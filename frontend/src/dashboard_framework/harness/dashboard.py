"""Pipeline-Schritt 3 (PSP 5.5, US-06): erzeugt aus Artefakt und SQL je KPI die dashboard.json.

Arbeitsteilung zwischen Code und Sprachmodell, mit Absicht eng gehalten:
- Das MODELL wählt nur Darstellungsdetails je KPI: Chart-Typ, Farbe (aus der Firmenpalette), Sortierung, Breite.
- Der CODE setzt alles Feststehende: Name, Titel, Tabelle, Branding, Spalten und vor allem das SQL. Das SQL stammt aus Schritt 2 (bereits geprüft)
  und wird nie vom Modell neu geschrieben oder verändert.
Die Antwort des Modells wird nie blind übernommen: Format erzwingen (JSON-Schema), Inhalt prüfen, bei Fehlern mit Fehlermeldung nachfragen, nach max_versuche abbrechen.
"""
from __future__ import annotations

import json
import re
from typing import Protocol, get_args

from pydantic import BaseModel, ConfigDict, ValidationError

from dashboard_framework.models.artefakt import Artefakt
from dashboard_framework.models.dashboard_config import Breite, Chart, ChartTyp, DashboardConfig, Sortierung
from dashboard_framework.runner.sicherheit import UnsicheresSql, pruefe_nur_lesend

SCHRITT = "dashboard"
STANDARD_MAX_VERSUCHE = 3


class LLMProtokoll(Protocol):
    """Was dieser Schritt vom Sprachmodell erwartet. Passt zur geplanten Klasse harness/llm.LLM (PSP 5.2, David); zum Testen genügt ein Fake."""

    def antworte(self, prompt: str, schritt: str, json_schema: dict | None = None) -> str: ...


class DashboardFehler(ValueError):
    """Die Dashboard-Konfiguration konnte nicht erzeugt werden. 'meldungen' nennt die Gründe."""

    def __init__(self, meldungen: list[str] | str):
        self.meldungen = [meldungen] if isinstance(meldungen, str) else list(meldungen)
        super().__init__("; ".join(self.meldungen))


class ChartWahl(BaseModel):
    """Die Wahl des Modells für eine KPI. Weitere Felder (z. B. ein eigenes SQL) sind verboten und werden abgelehnt."""

    model_config = ConfigDict(extra="forbid")

    kpi: str
    typ: ChartTyp
    farbe: str | None = None
    sortierung: Sortierung = "keine"
    breite: Breite = "halb"


class Antwort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    charts: list[ChartWahl]


# --- Schema und Prompt ------------------------------------------------------------------------------


def wahl_schema(kpi_namen: list[str], farben: list[str]) -> dict:
    """JSON-Schema für das Modell (z. B. Ollama-Parameter 'format'). Erlaubte Werte stehen als Aufzählung fest,
    das Modell kann also keinen unbekannten KPI-Namen, Chart-Typ oder Farbwert mehr erzeugen.

    Bewusst schmaler als DashboardConfig.json_schema(): kein SQL, keine Namen, kein Branding. Weniger Tokens, weniger Fehlerquellen,
    und das geprüfte SQL kann nicht verändert werden. Die fertige Konfiguration wird zusätzlich vom vollen Modell DashboardConfig geprüft.
    """
    eigenschaften: dict = {
        "kpi": {"enum": list(kpi_namen)},
        "typ": {"enum": list(get_args(ChartTyp))},
        "sortierung": {"enum": list(get_args(Sortierung))},
        "breite": {"enum": list(get_args(Breite))},
    }
    if farben:
        eigenschaften["farbe"] = {"enum": list(farben)}
    return {
        "type": "object",
        "properties": {
            "charts": {
                "type": "array",
                "minItems": len(kpi_namen),
                "maxItems": len(kpi_namen),
                "items": {
                    "type": "object",
                    "properties": eigenschaften,
                    "required": ["kpi", "typ"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["charts"],
        "additionalProperties": False,
    }


def baue_prompt(artefakt: Artefakt, sql_je_kpi: dict[str, str]) -> str:
    zeilen = [
        "Du wählst für jede KPI eines Dashboards die passende Darstellung.",
        "",
        f"Ziel des Dashboards: {artefakt.ziel}",
        f"Publikum: {artefakt.publikum}",
        "",
        "KPIs (Name | Beschreibung | SQL):",
    ]
    for nr, kpi in enumerate(artefakt.kpis, start=1):
        zeilen.append(f"{nr}. {kpi.name} | {kpi.beschreibung} | {sql_je_kpi[kpi.name]}")
    zeilen += [
        "",
        "Darstellungen (typ):",
        "- balken: Vergleich einzelner Kategorien",
        "- linie: Verlauf über die Zeit",
        "- tabelle: Rangliste oder Detailwerte mit mehreren Spalten",
        "- kennzahl: genau eine einzelne Zahl",
        "",
        "Weitere Angaben je KPI (optional):",
    ]
    if artefakt.branding.farben:
        zeilen.append(f"- farbe: genau eine dieser Farben: {', '.join(artefakt.branding.farben)}")
    zeilen += [
        "- sortierung: keine | aufsteigend | absteigend (nach dem Wert; sinnvoll bei balken und tabelle)",
        "- breite: halb | voll (voll für Verläufe mit vielen Punkten)",
        "",
        "Antworte ausschließlich mit JSON in dieser Form, ohne Erklärung:",
        '{"charts": [{"kpi": "<Name der KPI genau wie oben>", "typ": "balken"}]}',
        "Jede KPI kommt genau einmal vor.",
    ]
    return "\n".join(zeilen)


# --- Antwort prüfen -----------------------------------------------------------------------------------

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extrahiere_json(text: str) -> object:
    """Holt JSON aus der Modellantwort. Kleine Modelle verpacken es gern in Markdown-Codeblöcke oder schreiben Text davor.

    Reihenfolge: reiner JSON-Text, Inhalt eines Codeblocks, zuletzt das Stück von der ersten '{' bis zur letzten '}'.
    """
    kandidaten = [text.strip()]
    kandidaten += [m.strip() for m in _FENCE.findall(text)]
    anfang, ende = text.find("{"), text.rfind("}")
    if 0 <= anfang < ende:
        kandidaten.append(text[anfang : ende + 1])
    for kandidat in kandidaten:
        try:
            return json.loads(kandidat)
        except json.JSONDecodeError:
            continue
    raise ValueError("Die Antwort enthält kein gültiges JSON")


def pruefe_antwort(text: str, kpi_namen: list[str], farben: list[str]) -> list[ChartWahl]:
    """Prüft die Modellantwort auf Format UND Inhalt. Bei einem Problem: ValueError mit einer Meldung, die dem Modell zurückgegeben werden kann."""
    daten = extrahiere_json(text)
    try:
        antwort = Antwort.model_validate(daten)
    except ValidationError as fehler:
        einzelne = [f"{'.'.join(str(t) for t in e['loc'])}: {e['msg']}" for e in fehler.errors()[:5]]
        raise ValueError("Die Antwort entspricht nicht dem Schema: " + "; ".join(einzelne)) from None

    genannt = [w.kpi for w in antwort.charts]
    unbekannt = [k for k in dict.fromkeys(genannt) if k not in kpi_namen]
    fehlend = [k for k in kpi_namen if k not in genannt]
    doppelt = [k for k in dict.fromkeys(genannt) if genannt.count(k) > 1]
    probleme = []
    if unbekannt:
        probleme.append(f"unbekannte KPI(s): {', '.join(unbekannt)}")
    if fehlend:
        probleme.append(f"es fehlen KPI(s): {', '.join(fehlend)}")
    if doppelt:
        probleme.append(f"KPI(s) mehrfach genannt: {', '.join(doppelt)}")
    erlaubt = {f.upper() for f in farben}
    for w in antwort.charts:
        if w.farbe is not None and w.farbe.upper() not in erlaubt:
            wohin = f"erlaubt sind: {', '.join(farben)}" if farben else "es gibt keine Farbpalette, 'farbe' weglassen"
            probleme.append(f"Farbe {w.farbe} bei KPI '{w.kpi}' ist nicht erlaubt ({wohin})")
    if probleme:
        raise ValueError("Die Antwort ist inhaltlich falsch: " + "; ".join(probleme))
    return antwort.charts


# --- Der Schritt ------------------------------------------------------------------------------------------


def erzeuge_config(
    artefakt: Artefakt,
    sql_je_kpi: dict[str, str],
    llm: LLMProtokoll,
    max_versuche: int = STANDARD_MAX_VERSUCHE,
    db_pfad: str = "daten.db",
) -> DashboardConfig:
    """Erzeugt die dashboard.json-Konfiguration. Wirft DashboardFehler, wenn das Modell nach max_versuche keine gültige Antwort liefert.

    sql_je_kpi: {KPI-Name: SQL} aus Schritt 2 (Query-Schritt). Es muss zu jeder KPI des Artefakts genau ein SQL geben.
    """
    kpi_namen = [k.name for k in artefakt.kpis]
    fehlt = [n for n in kpi_namen if n not in sql_je_kpi]
    if fehlt:
        raise DashboardFehler(f"Für diese KPI(s) fehlt das SQL aus dem Query-Schritt: {', '.join(fehlt)}")
    for name in kpi_namen:
        try:
            pruefe_nur_lesend(sql_je_kpi[name])  # zweite Absicherung: Schritt 2 prüft schon, aber die Konfiguration soll nie unsicheres SQL enthalten
        except UnsicheresSql as fehler:
            raise DashboardFehler(f"Das SQL der KPI '{name}' ist nicht erlaubt: {fehler}") from None

    farben = list(artefakt.branding.farben)
    schema = wahl_schema(kpi_namen, farben)
    basis_prompt = baue_prompt(artefakt, sql_je_kpi)

    prompt = basis_prompt
    letzter_fehler = ""
    wahl: list[ChartWahl] | None = None
    for _ in range(max(1, max_versuche)):
        antwort = llm.antworte(prompt, SCHRITT, schema)
        try:
            wahl = pruefe_antwort(antwort, kpi_namen, farben)
            break
        except ValueError as fehler:
            letzter_fehler = str(fehler)
            # Reparaturschleife: dieselbe Aufgabe nochmals, ergänzt um den konkreten Fehler der letzten Antwort.
            prompt = f"{basis_prompt}\n\nDeine letzte Antwort war ungültig: {letzter_fehler}\nAntworte erneut, nur mit korrektem JSON."
    if wahl is None:
        raise DashboardFehler(
            [f"Die Dashboard-Konfiguration konnte nach {max(1, max_versuche)} Versuchen nicht erzeugt werden.", f"Letzter Fehler: {letzter_fehler}"]
        )

    nach_name = {w.kpi: w for w in wahl}
    charts = []
    for kpi in artefakt.kpis:  # Reihenfolge bestimmt das Artefakt, nicht das Modell
        w = nach_name[kpi.name]
        charts.append(
            Chart(
                titel=kpi.name,
                typ=w.typ,
                sql=sql_je_kpi[kpi.name],
                farbe=w.farbe.upper() if w.farbe else None,
                sortierung=w.sortierung,
                breite=w.breite,
                beschreibung=kpi.beschreibung,  # vom Code gesetzt, nicht vom Modell: so bleibt die Herkunft der Zahl nachvollziehbar
            )
        )
    return DashboardConfig(
        name=artefakt.name,
        titel=artefakt.titel,
        tabelle=artefakt.tabelle,
        db_pfad=db_pfad,
        spalten=artefakt.spalten,
        charts=charts,
        branding=artefakt.branding,
    )
