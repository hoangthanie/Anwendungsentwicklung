"""Schritt 2 (PSP 5.4, US-05): aus jeder KPI-Beschreibung genau ein geprüftes SQL erzeugen. Entscheidungen in ADR 0008.

Arbeitsteilung: Das MODELL schreibt das SQL. Der CODE prüft es, bevor es weitergegeben wird, in dieser Reihenfolge:
  a) Format     – gültiges JSON mit "sql" oder "ablehnung"
  b) nur lesend – genau ein SELECT/WITH, nichts Schreibendes (US-14)
  c) bekannt    – nur die Tabelle des Artefakts und nur bekannte Spalten (US-05.2)
  d) Bedeutung  – die Spalten aus der KPI-Beschreibung (in Backticks) kommen im SQL vor
  d2) Zeitbezug – kein heutiges Datum ('now', CURRENT_DATE): "aktuell" bezieht sich auf die Daten, nicht auf den Kalender
  d3) Division  – Zähler und Nenner sind nicht derselbe Ausdruck (Ergebnis wäre immer 1)
  d4) Einzelwert – eine einzelne Zahl hat genau eine Ergebnisspalte (der Runner zeigt die erste)
  d5) Ganzzahl   – keine Division zweier ganzer Zahlen (SQLite schneidet die Nachkommastellen ab)
  e) ausführbar – läuft auf den echten Daten, liefert Zeilen und nicht nur NULL; Zeitreihen aufsteigend
  f) Orakel     – nur wenn Referenzwerte übergeben werden (in den Tests, US-05.3)
Scheitert eine Schicht, bekommt das Modell die Meldung zurück und versucht es erneut (Reparaturschleife, US-05.4).
Liefert es ein SQL, das schon einmal gescheitert ist, erfährt es das ausdrücklich: Mit temperature 0 wäre der nächste
Prompt sonst Wort für Wort derselbe und damit auch die Antwort (Probelauf 9, ADR 0008). Verlangt es zweimal dieselbe
Spalte, die es nicht gibt (und die keiner vorhandenen ähnelt), wird die KPI als nicht berechenbar abgelehnt, statt im
nächsten Versuch eine Ersatzspalte zu riskieren (Messung 2, ADR 0008).
Jeder geprüfte Versuch steht mit SQL und Meldung im Run-Protokoll, wenn das llm das anbietet (protokolliere_pruefung).
Lehnt das Modell eine KPI begründet ab, gibt es keinen weiteren Versuch: das ist eine Antwort, kein Fehler.
Scheitert das Hauptmodell max_versuche-mal, bekommt einmal das Fallback-Modell (z. B. qwen3:14b) die Aufgabe mit dem
letzten SQL und der letzten Fehlermeldung (Eskalation, ADR 0008). Erst wenn auch das scheitert, bricht der Schritt ab.

Eingabe laut Spezifikation 3.2 nur Schema und KPI; Ziel und Publikum gehören zu Schritt 3.
"""

from __future__ import annotations

from pathlib import Path

from dashboard_framework.harness.dashboard import extrahiere_json
from dashboard_framework.models.artefakt import Artefakt, Kpi
from dashboard_framework.runner.sicherheit import UnsicheresSql, pruefe_nur_lesend

from pipeline.harness.llm import LLMFehler
from pipeline.harness.validators import (
    SqlPruefFehler,
    UnbekannteSpalten,
    pruefe_anker,
    pruefe_ausfuehrbar,
    pruefe_bedeutung,
    pruefe_einzelwert,
    pruefe_from,
    pruefe_ganzzahl_division,
    pruefe_keine_selbstdivision,
    pruefe_ohne_systemzeit,
    pruefe_plausibilitaet,
    pruefe_tabelle,
    pruefe_zeitreihe_aufsteigend,
    zerlege,
)
from pipeline.schritte.schritt1_datenmodell import SpaltenInfo

SCHRITT = "query"
STANDARD_MAX_VERSUCHE = 3
ANTWORT_SCHEMA = {
    "type": "object",
    "properties": {"sql": {"type": "string"}, "ablehnung": {"type": "string"}},
    "required": ["sql", "ablehnung"],
}


class SqlFehler(ValueError):
    """Für mindestens eine KPI gibt es kein geprüftes SQL. 'meldungen' nennt jede KPI mit Grund."""

    def __init__(self, meldungen: list[str] | str):
        self.meldungen = [meldungen] if isinstance(meldungen, str) else list(meldungen)
        super().__init__("; ".join(self.meldungen))


def _wert(wert: object) -> str:
    return f"'{wert}'" if isinstance(wert, str) else str(wert)


def regel_zeitbezug(tabelle: str, datumsspalten: list[str] | None) -> str:
    """Regel 7 des Prompts, abgeleitet aus den Spaltentypen des Artefakts. Nichts darin ist auf einen Datensatz zugeschnitten.

    datumsspalten None = unbekannt (Aufruf ohne Artefakt), [] = der Datensatz hat keine Datumsspalte.
    """
    verbot = "Das heutige Datum ('now', date('now'), CURRENT_DATE, CURRENT_TIMESTAMP) ist verboten."
    if datumsspalten is None:
        return (
            "7. Zeitbezüge wie 'aktuell', 'Vormonat' oder 'letzte 30 Tage' beziehen sich immer auf den jüngsten Wert der "
            f"Datumsspalte in den Daten (MAX), nie auf das heutige Datum. {verbot}"
        )
    if not datumsspalten:
        return (
            "7. Die Tabelle hat keine Datumsspalte. Eine KPI mit Zeitbezug (z. B. 'aktuell', 'Vormonat', 'je Monat', "
            f"'im Zeitverlauf') ist deshalb nicht berechenbar: \"sql\" leer lassen und in \"ablehnung\" begründen. {verbot}"
        )
    d = datumsspalten[0]
    welche = (
        f"der Datumsspalte {d}"
        if len(datumsspalten) == 1
        else f"der Datumsspalte, die die KPI nennt (Datumsspalten: {', '.join(datumsspalten)})"
    )
    return (
        f"7. Zeitbezüge wie 'aktuell', 'Vormonat' oder 'letzte 30 Tage' beziehen sich immer auf den jüngsten Wert {welche} "
        f"in den Daten, nie auf das heutige Datum. {verbot} Beispiele: jüngster Monat = "
        f"strftime('%Y-%m', (SELECT MAX({d}) FROM {tabelle})); Monat davor = "
        f"strftime('%Y-%m', date((SELECT MAX({d}) FROM {tabelle}), 'start of month', '-1 month'))."
        " Vergleich zweier Zeiträume (z. B. aktueller Monat gegenüber Vormonat): beide Werte getrennt in derselben Abfrage"
        " berechnen und dann teilen, etwa"
        f" SUM(CASE WHEN strftime('%Y-%m', {d}) = <jüngster Monat> THEN wert END)"
        f" / SUM(CASE WHEN strftime('%Y-%m', {d}) = <Monat davor> THEN wert END),"
        " wobei wert die zu verrechnende Spalte ist. Kein WHERE, das nur einen der beiden Zeiträume übrig lässt."
    )


def baue_prompt(
    kpi: Kpi,
    schema: list[SpaltenInfo],
    tabelle: str,
    beschreibungen: dict[str, str] | None = None,
    datumsspalten: list[str] | None = None,
) -> str:
    beschreibungen = beschreibungen or {}
    zeilen = [
        "Du schreibst genau eine SQLite-Abfrage für eine Kennzahl (KPI) eines Dashboards.",
        "",
        f"Tabelle: {tabelle}",
        "Spalten (Name, Typ, Bedeutung, Beispielwerte):",
    ]
    for spalte in schema:
        bedeutung = f"; {beschreibungen[spalte.name]}" if beschreibungen.get(spalte.name) else ""
        beispiele = ", ".join(_wert(w) for w in spalte.beispiele) or "keine"
        zeilen.append(f"- {spalte.name} ({spalte.typ}{bedeutung}) – Beispielwerte: {beispiele}")
    zeilen += [
        "",
        f"KPI: {kpi.name}",
        f"Beschreibung: {kpi.beschreibung}",
        "Spaltennamen in Backticks sind die Spalten, auf denen die KPI beruht.",
        "",
        "Regeln:",
        (
            "1. Nur SQLite. Datumswerte sind Text im Format JJJJ-MM-TT (mit Uhrzeit: JJJJ-MM-TT HH:MM:SS). Teile davon mit strftime, z. B. Monat: strftime('%Y-%m', spalte),"
            " Jahr: strftime('%Y', spalte). MONTH(), YEAR(), DATE_TRUNC oder EXTRACT gibt es in SQLite nicht."
        ),
        "2. Genau eine lesende Abfrage (SELECT oder WITH), ohne Semikolon.",
        f"3. Nur die Tabelle {tabelle} und nur die oben genannten Spalten.",
        (
            "4. Ergebnisspalten: zuerst die Gruppierung (z. B. Kategorie oder Zeitraum), danach der berechnete Wert."
            " Ist das Ergebnis eine einzelne Zahl (z. B. Verhältnis oder Gesamtsumme): genau eine Spalte und eine Zeile,"
            " ohne zusätzliche Spalte für Zeitraum oder Bezeichnung."
            " Ergebnisse über die Zeit aufsteigend nach dem Zeitraum sortieren (ältester zuerst)."
        ),
        "5. Gib berechneten Spalten mit AS einen kurzen Namen.",
        '6. Ist die KPI mit diesen Spalten nicht berechenbar: "sql" leer lassen und in "ablehnung" kurz begründen.',
        regel_zeitbezug(tabelle, datumsspalten),
        "",
        'Antworte nur mit JSON: {"sql": "...", "ablehnung": ""}',
    ]
    return "\n".join(zeilen)


def pruefe_sql(
    sql: str,
    kpi: Kpi,
    schema: list[SpaltenInfo],
    tabelle: str,
    db_pfad: str | Path,
    erwartet: dict[str, float] | None = None,
) -> None:
    """Prüfschichten b) bis f). Wirft SqlPruefFehler mit einer Meldung für das Modell."""
    try:
        pruefe_nur_lesend(sql)
    except UnsicheresSql as fehler:
        raise SqlPruefFehler(f"Nicht erlaubt: {fehler}") from None
    pruefe_tabelle(zerlege(sql), tabelle)
    pruefe_from(sql, tabelle)
    pruefe_bedeutung(sql, {s.name for s in schema})
    pruefe_anker(sql, kpi.referenzierte_spalten)
    pruefe_ohne_systemzeit(sql)
    pruefe_keine_selbstdivision(sql)
    pruefe_ganzzahl_division(sql, {s.name for s in schema if s.typ.upper() == "INTEGER"})
    pruefe_einzelwert(sql)
    spalten, zeilen = pruefe_ausfuehrbar(sql, db_pfad)
    pruefe_zeitreihe_aufsteigend(spalten, zeilen)
    if erwartet:
        pruefe_plausibilitaet(sql, db_pfad, erwartet)


def erzeuge_sql(
    kpi: Kpi,
    schema: list[SpaltenInfo],
    tabelle: str,
    llm,
    db_pfad: str | Path,
    max_versuche: int = STANDARD_MAX_VERSUCHE,
    beschreibungen: dict[str, str] | None = None,
    erwartet: dict[str, float] | None = None,
    datumsspalten: list[str] | None = None,
) -> str:
    """US-05.1: Liefert genau ein geprüftes SELECT für die KPI oder wirft SqlFehler.

    llm braucht antworte(prompt, schritt, json_schema, versuch=...) wie pipeline.harness.llm.LLM.
    """
    bekannt = {s.name for s in schema}
    fehlend = [a for a in kpi.referenzierte_spalten if a not in bekannt]
    if fehlend:  # Vorprüfung ohne Modell (Spezifikation 3.2)
        raise SqlFehler(f"KPI '{kpi.name}': Spalte(n) {', '.join(fehlend)} gibt es in den Daten nicht")

    basis = baue_prompt(kpi, schema, tabelle, beschreibungen, datumsspalten)
    prompt = basis
    versuche = max(1, max_versuche)
    letzter_fehler = ""
    fallback = getattr(llm, "fallback_modell", None)
    if fallback == getattr(llm, "modell", None):
        fallback = None
    fallback_fehler = ""  # gesetzt, wenn das Fallback-Modell gar nicht antworten konnte (z. B. nicht installiert)
    gescheitert: set[str] = set()  # bereits abgelehnte SQL (normalisiert), um Wiederholungen zu erkennen
    fehlende: dict[str, int] = {}  # wie oft das Modell eine Spalte verlangt hat, die es in den Daten nicht gibt
    notiere = getattr(llm, "protokolliere_pruefung", None)  # Fakes in Tests müssen das nicht anbieten
    plan = [(nr, None) for nr in range(1, versuche + 1)]
    if fallback:
        plan.append((versuche + 1, fallback))  # Eskalation: Aufgabe samt letztem Fehler an das größere Modell
    for versuch, modell in plan:
        if modell is None:
            text = llm.antworte(prompt, SCHRITT, ANTWORT_SCHEMA, versuch=versuch)
        else:
            try:
                text = llm.antworte(prompt, SCHRITT, ANTWORT_SCHEMA, versuch=versuch, modell=modell)
            except LLMFehler as fehler:
                fallback_fehler = str(fehler)
                break  # Fallback-Modell nicht verfügbar: es bleibt beim Abbruch mit dem letzten Fehler des Hauptmodells
        sql = ""
        try:
            daten = extrahiere_json(text)
            if not isinstance(daten, dict):
                raise SqlPruefFehler('Die Antwort muss ein JSON-Objekt mit "sql" und "ablehnung" sein')
            sql = str(daten.get("sql") or "").strip().rstrip(";").strip()
            ablehnung = str(daten.get("ablehnung") or "").strip()
            if not sql and ablehnung:
                raise SqlFehler(f"KPI '{kpi.name}' ist mit den vorhandenen Daten nicht berechenbar: {ablehnung}")
            if not sql:
                raise SqlPruefFehler('Weder "sql" noch "ablehnung" ist ausgefüllt')
            pruefe_sql(sql, kpi, schema, tabelle, db_pfad, erwartet)
            if notiere:
                notiere(SCHRITT, versuch, sql, modell=modell)
            return sql
        except (SqlPruefFehler, ValueError) as fehler:
            if isinstance(fehler, SqlFehler):
                raise
            letzter_fehler = str(fehler)
            if notiere:
                notiere(SCHRITT, versuch, sql, fehler=letzter_fehler, modell=modell)
            if isinstance(fehler, UnbekannteSpalten):
                for name in fehler.ohne_vorschlag:
                    fehlende[name] = fehlende.get(name, 0) + 1
                beharrlich = sorted(name for name, anzahl in fehlende.items() if anzahl >= 2)
                if beharrlich:
                    # Zweimal dieselbe Spalte, die es nicht gibt (kein Tippfehler): Die KPI braucht offenbar Daten, die
                    # fehlen. Ehrlich ablehnen, statt im nächsten Versuch eine Ersatzspalte zu riskieren (Messung 2).
                    raise SqlFehler(
                        f"KPI '{kpi.name}' ist mit den vorhandenen Daten nicht berechenbar: Sie braucht "
                        f"{', '.join(beharrlich)}, das gibt es in den Daten nicht"
                    ) from None
            normal = " ".join(sql.lower().split())
            wiederholt = bool(sql) and normal in gescheitert
            gescheitert.add(normal)
            vorher = f"Dein letztes SQL war:\n{sql}\n" if sql else ""
            hinweis = (
                "Dieses SQL hast du schon in einem früheren Versuch geliefert, es ist weiterhin ungültig. "
                "Schreibe eine andere Abfrage.\n"
                if wiederholt
                else ""
            )
            prompt = (
                f"{basis}\n\n{vorher}Es ist ungültig: {letzter_fehler}\n{hinweis}"
                "Korrigiere es und antworte erneut nur mit JSON."
            )
    if fallback_fehler:
        zusatz = f". Das Fallback-Modell {fallback} konnte nicht helfen, weil es nicht verfügbar war: {fallback_fehler}"
    elif fallback:
        zusatz = f", auch nicht mit dem Fallback-Modell {fallback}"
    else:
        zusatz = ""
    raise SqlFehler(f"KPI '{kpi.name}': kein gültiges SQL nach {versuche} Versuchen{zusatz}. Letzter Fehler: {letzter_fehler}")


def ausfuehren(
    artefakt: Artefakt,
    schema: list[SpaltenInfo],
    db_pfad: str | Path,
    llm,
    max_versuche: int = STANDARD_MAX_VERSUCHE,
) -> dict[str, str]:
    """Schritt 2 komplett: {KPI-Name: geprüftes SQL} für Schritt 3.
    Alle KPIs werden versucht; Probleme werden gesammelt und gemeinsam gemeldet."""
    beschreibungen = {s.name: s.typ + (f", {s.beschreibung}" if s.beschreibung else "") for s in artefakt.spalten}
    datumsspalten = [s.name for s in artefakt.spalten if s.typ == "datum"]  # aus dem Artefakt, für jeden Datensatz gleich ermittelt
    ergebnis: dict[str, str] = {}
    meldungen: list[str] = []
    for kpi in artefakt.kpis:
        try:
            ergebnis[kpi.name] = erzeuge_sql(
                kpi,
                schema,
                artefakt.tabelle,
                llm,
                db_pfad,
                max_versuche=max_versuche,
                beschreibungen=beschreibungen,
                datumsspalten=datumsspalten,
            )
        except SqlFehler as fehler:
            meldungen += fehler.meldungen
    if meldungen:
        raise SqlFehler(meldungen)
    return ergebnis
