"""Schritt 4 (PSP 5.6, US-07): Beschreibung des Dashboards für den Anwender.

Ziel: Wer das Dashboard nutzt, soll ohne Technikkenntnisse nachlesen können, was es zeigt, auf welchen Daten es beruht,
wie jede Kennzahl berechnet wird und wie das Dashboard entstanden ist. Der Text erscheint im Dashboard im Tab
"Über dieses Dashboard" (Feld doku der dashboard.json) und liegt zusätzlich als README.md im Paket.

Arbeitsteilung wie in US-07 vorgesehen:
- Die VORLAGE (dieser Code) schreibt alle Fakten: Zweck, Zielgruppe, Spalten, Zeilenzahl, Zeitraum, die Vorgabe jeder
  Kennzahl, ihr SQL, die Darstellung und den Ablauf der Erstellung. Diese Angaben kommen direkt aus Artefakt, Datenbank
  und Konfiguration, das Modell kann sie also nicht verfälschen.
- Das MODELL schreibt nur die Erklärtexte in einfachen Worten, für alle Kennzahlen in einem einzigen Aufruf.
Scheitert der Aufruf oder ist eine Erklärung unbrauchbar, fehlt nur dieser Text: Die Beschreibung bleibt vollständig
und richtig, der Lauf bricht deswegen nicht ab.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from dashboard_framework.harness.dashboard import extrahiere_json
from dashboard_framework.models.artefakt import Artefakt
from dashboard_framework.models.dashboard_config import DashboardConfig
from dashboard_framework.runner.framework_lib import bezeichner_zitieren
from dashboard_framework.runner.sicherheit import verbinde_nur_lesend

from pipeline.harness.llm import LLMFehler

SCHRITT = "doku"
MAX_ZEICHEN = 600  # je Erklärtext; längere Antworten sind eher Geschwätz als Erklärung und werden verworfen

SPALTEN_ART = {"datum": "Datum", "text": "Text", "ganzzahl": "ganze Zahl", "dezimal": "Dezimalzahl", "bool": "Ja/Nein"}
DARSTELLUNG = {
    "balken": "Balkendiagramm",
    "linie": "Liniendiagramm (Verlauf über die Zeit)",
    "tabelle": "Tabelle",
    "kennzahl": "einzelne Zahl",
}
OHNE_ERKLAERUNG = "*Für diese Kennzahl liegt keine Erklärung in einfachen Worten vor. Maßgeblich sind Ihre Vorgabe und die Abfrage.*"


def antwort_schema(kpi_namen: list[str]) -> dict:
    """JSON-Schema für das Modell: je Kennzahl genau ein Eintrag mit zwei Texten, sonst nichts."""
    return {
        "type": "object",
        "properties": {
            "kpis": {
                "type": "array",
                "minItems": len(kpi_namen),
                "maxItems": len(kpi_namen),
                "items": {
                    "type": "object",
                    "properties": {
                        "kpi": {"enum": list(kpi_namen)},
                        "aussage": {"type": "string"},
                        "berechnung": {"type": "string"},
                    },
                    "required": ["kpi", "aussage", "berechnung"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["kpis"],
        "additionalProperties": False,
    }


def baue_prompt(artefakt: Artefakt, sql_je_kpi: dict[str, str]) -> str:
    zeilen = [
        "Du erklärst die Kennzahlen eines Dashboards für Leser ohne Technikkenntnisse.",
        "",
        f"Zweck des Dashboards: {artefakt.ziel}",
        f"Leser: {artefakt.publikum}",
        "",
        "Spalten der Daten (Name: Bedeutung):",
    ]
    zeilen += [f"- {s.name}: {s.beschreibung or SPALTEN_ART[s.typ]}" for s in artefakt.spalten]
    zeilen += ["", "Kennzahlen (Name | Vorgabe | SQL-Abfrage, die die Zahl tatsächlich berechnet):"]
    zeilen += [f"{nr}. {k.name} | {k.beschreibung} | {sql_je_kpi[k.name]}" for nr, k in enumerate(artefakt.kpis, start=1)]
    zeilen += [
        "",
        "Schreibe für jede Kennzahl:",
        '- "aussage": ein bis zwei Sätze, was die Zahl zeigt und wobei sie den Lesern hilft.',
        (
            '- "berechnung": ein bis zwei Sätze, wie die Zahl aus den Daten berechnet wird. Beschreibe genau das, was die '
            "SQL-Abfrage tut, nicht mehr und nicht weniger. Verwende keine SQL-Begriffe (SELECT, GROUP BY, CASE ...) und "
            "statt Spaltennamen deren Bedeutung."
        ),
        "Sachlich, auf Deutsch, ohne Anrede. Nenne keine Zahlenwerte, die nicht in der Vorgabe oder im SQL stehen.",
        "",
        'Antworte nur mit JSON: {"kpis": [{"kpi": "<Name genau wie oben>", "aussage": "...", "berechnung": "..."}]}',
        "Jede Kennzahl kommt genau einmal vor.",
    ]
    return "\n".join(zeilen)


def erklaerungen(artefakt: Artefakt, sql_je_kpi: dict[str, str], llm) -> dict[str, tuple[str, str]]:
    """Ein Modellaufruf für alle Kennzahlen. Liefert {KPI-Name: (aussage, berechnung)} nur für brauchbare Einträge.

    Nichts hier wirft einen Fehler weiter: Ohne Erklärtexte ist die Beschreibung immer noch vollständig und richtig.
    """
    namen = [k.name for k in artefakt.kpis]
    try:
        daten = extrahiere_json(llm.antworte(baue_prompt(artefakt, sql_je_kpi), SCHRITT, antwort_schema(namen)))
    except (LLMFehler, ValueError):
        return {}
    eintraege = daten.get("kpis") if isinstance(daten, dict) else None
    if not isinstance(eintraege, list):
        return {}
    gefunden: dict[str, tuple[str, str]] = {}
    for eintrag in eintraege:
        if not isinstance(eintrag, dict) or eintrag.get("kpi") not in namen or eintrag["kpi"] in gefunden:
            continue
        aussage, berechnung = (str(eintrag.get(f) or "").strip() for f in ("aussage", "berechnung"))
        if aussage and berechnung and len(aussage) <= MAX_ZEICHEN and len(berechnung) <= MAX_ZEICHEN:
            gefunden[eintrag["kpi"]] = (aussage, berechnung)
    return gefunden


def datenbasis(db_pfad: str | Path, artefakt: Artefakt) -> tuple[int, list[tuple[str, str, str]]]:
    """Zeilenzahl und je Datumsspalte (Name, ältester, jüngster Wert), nur lesend aus der Datenbank."""
    t = bezeichner_zitieren(artefakt.tabelle)
    verbindung = verbinde_nur_lesend(db_pfad)
    try:
        zeilen = verbindung.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        zeitraeume = []
        for spalte in (s for s in artefakt.spalten if s.typ == "datum"):
            s = bezeichner_zitieren(spalte.name)
            von, bis = verbindung.execute(f"SELECT MIN({s}), MAX({s}) FROM {t}").fetchone()
            if von and bis:
                zeitraeume.append((spalte.name, str(von), str(bis)))
        return zeilen, zeitraeume
    finally:
        verbindung.close()


def _datum(wert: str) -> str:
    """2026-01-15 -> 15.01.2026; andere Formate bleiben, wie sie sind."""
    teile = wert[:10].split("-")
    if len(teile) == 3 and all(t.isdigit() for t in teile):
        return f"{teile[2]}.{teile[1]}.{teile[0]}"
    return wert


def _zelle(text: str) -> str:
    """Text für eine Markdown-Tabellenzelle: kein senkrechter Strich, keine Zeilenumbrüche."""
    return " ".join(text.replace("|", "/").split()) or "–"


def _zahl(wert: int) -> str:
    return f"{wert:,}".replace(",", ".")


def erzeuge_doku(
    artefakt: Artefakt,
    sql_je_kpi: dict[str, str],
    llm,
    config: DashboardConfig | None = None,
    db_pfad: str | Path | None = None,
    quelle: str | None = None,
    erstellt: date | None = None,
) -> str:
    """US-07: Beschreibung des Dashboards als Markdown.

    config (aus Schritt 3) liefert die Darstellung je Kennzahl, db_pfad die Zeilenzahl und den Zeitraum, quelle den Namen
    der Datendatei. Alle drei sind optional; fehlt eine Angabe, fehlt nur der zugehörige Satz.
    """
    erstellt = erstellt or date.today()
    texte = erklaerungen(artefakt, sql_je_kpi, llm)
    darstellung = {c.titel: c.typ for c in config.charts} if config else {}
    modell = getattr(llm, "modell", None)
    fallback = getattr(llm, "fallback_modell", None)

    z = [
        f"# {artefakt.titel}",
        "",
        f"*Beschreibung dieses Dashboards, automatisch erstellt am {erstellt:%d.%m.%Y}.*",
        "",
        "## Wofür ist dieses Dashboard?",
        "",
        f"**Zweck:** {artefakt.ziel}",
        "",
        f"**Für wen:** {artefakt.publikum}",
        "",
        "## Welche Daten stecken darin?",
        "",
    ]
    satz = f"Grundlage ist die Datei `{quelle}`" if quelle else "Grundlage sind Ihre hochgeladenen Daten"
    if db_pfad:
        zeilen, zeitraeume = datenbasis(db_pfad, artefakt)
        satz += f" mit {_zahl(zeilen)} Zeilen"
        if len(zeitraeume) == 1:
            satz += f" aus dem Zeitraum {_datum(zeitraeume[0][1])} bis {_datum(zeitraeume[0][2])}"
        satz += "."
        satz += "".join(f" Spalte {n}: {_datum(v)} bis {_datum(b)}." for n, v, b in zeitraeume if len(zeitraeume) > 1)
    else:
        satz += "."
    z += [
        f"{satz} Im Dashboard liegen die Daten als Tabelle `{artefakt.tabelle}` mit diesen Spalten:",
        "",
        "| Spalte | Art | Bedeutung |",
        "|---|---|---|",
    ]
    z += [f"| `{s.name}` | {SPALTEN_ART[s.typ]} | {_zelle(s.beschreibung)} |" for s in artefakt.spalten]
    z += ["", "## Die Kennzahlen", ""]

    for nr, kpi in enumerate(artefakt.kpis, start=1):
        z += [f"### {nr}. {kpi.name}", ""]
        if kpi.name in texte:
            aussage, berechnung = texte[kpi.name]
            z += [f"**Was zeigt sie?** {aussage}", "", f"**Wie wird sie berechnet?** {berechnung}", ""]
        else:
            z += [OHNE_ERKLAERUNG, ""]
        z += [f"**Ihre Vorgabe:** {kpi.beschreibung}", ""]
        if kpi.name in darstellung:
            z += [f"**Darstellung:** {DARSTELLUNG[darstellung[kpi.name]]}", ""]
        z += ["Abfrage an die Datenbank (SQL), zum Nachprüfen für Fachleute:", "", "```sql", sql_je_kpi[kpi.name], "```", ""]

    wer = f"Ein lokal betriebenes Sprachmodell ({modell})" if modell else "Ein lokal betriebenes Sprachmodell"
    eskalation = (
        f" Gelang das nach drei Versuchen nicht, hat ein größeres Modell ({fallback}) die Aufgabe übernommen." if fallback else ""
    )
    z += [
        "## Wie ist das Dashboard entstanden?",
        "",
        "Das Dashboard wurde aus Ihren Angaben (Zweck, Spalten, Kennzahlen) automatisch in vier Schritten erstellt:",
        "",
        (
            "1. **Daten prüfen und laden.** Die Datei wurde mit Ihrer Spaltenbeschreibung abgeglichen (Spalten vorhanden, Werte passen "
            "zur Art der Spalte) und in eine Datenbank geladen. Hier war kein Sprachmodell beteiligt."
        ),
        (
            f"2. **Kennzahlen berechnen.** {wer} hat für jede Kennzahl eine Abfrage an die Datenbank geschrieben. Übernommen wurde "
            "eine Abfrage nur, wenn sie alle automatischen Prüfungen bestanden hat: Sie liest nur und verändert nichts, verwendet "
            "nur Ihre Tabelle und Spalten, nutzt die Spalten, die in der Vorgabe genannt sind, hängt nicht vom heutigen Datum ab, "
            "läuft auf Ihren Daten fehlerfrei und liefert für jede Zeile einen Wert. Verläufe sind vom ältesten zum jüngsten "
            "Zeitraum sortiert. Fiel eine Prüfung durch, bekam das Modell die Fehlermeldung zurück und hat die Abfrage "
            f"korrigiert.{eskalation}"
        ),
        (
            "3. **Darstellung wählen.** Das Sprachmodell hat je Kennzahl die Diagrammart gewählt. Die geprüften Abfragen konnte es "
            "dabei nicht mehr verändern."
        ),
        (
            "4. **Diese Beschreibung.** Alle Fakten (Daten, Spalten, Vorgaben, Abfragen, Diagrammarten) stammen direkt aus dem "
            "System. Nur die Erklärtexte in einfachen Worten hat das Sprachmodell formuliert."
        ),
        "",
        (
            "Das Sprachmodell lief auf dem Rechner, auf dem das Dashboard erstellt wurde. Ihre Daten wurden an keinen "
            "Cloud-Dienst übertragen."
        ),
        "",
        "## Gut zu wissen",
        "",
        (
            "Die Prüfungen stellen sicher, dass jede Abfrage technisch korrekt läuft und die genannten Spalten verwendet. Ob sie "
            "inhaltlich genau das berechnet, was Sie gemeint haben, kann ein Programm nicht vollständig prüfen."
        ),
        "",
        (
            "Kommt Ihnen eine Zahl ungewöhnlich vor, vergleichen Sie die Abfrage mit Ihrer Vorgabe oder rechnen Sie eine Stichprobe "
            "mit Ihrer Ausgangsdatei nach (z. B. in Excel). Ist eine Vorgabe mehrdeutig, formulieren Sie sie genauer (welche Spalte, "
            "welcher Zeitraum, welche Rechnung) und lassen Sie das Dashboard neu erstellen."
        ),
    ]
    return "\n".join(z) + "\n"
