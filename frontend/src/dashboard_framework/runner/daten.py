"""Daten für den Runner: führt das in der dashboard.json hinterlegte SQL aus (US-09.1).

Reine Funktionen ohne Streamlit, damit sie ohne Browser testbar sind.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from dashboard_framework.models.dashboard_config import Chart, DashboardConfig
from dashboard_framework.runner.framework_lib import bezeichner_zitieren
from dashboard_framework.runner.sicherheit import pruefe_nur_lesend, verbinde_nur_lesend


def achsen(chart: Chart, df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Bestimmt X- und Y-Spalte: explizit aus dem Chart, sonst erste bzw. zweite Ergebnisspalte."""
    spalten = list(df.columns)
    x = chart.x if chart.x else (spalten[0] if spalten else None)
    y = chart.y if chart.y else (spalten[1] if len(spalten) > 1 else x)
    return x, y


def sortiere(chart: Chart, df: pd.DataFrame) -> pd.DataFrame:
    """Wendet die in der Konfiguration gewählte Sortierung auf die Y-Werte an."""
    if chart.sortierung == "keine" or df.empty:
        return df
    _, y = achsen(chart, df)
    return df.sort_values(y, ascending=(chart.sortierung == "aufsteigend"), ignore_index=True)


def lade_chart_daten(config: DashboardConfig, db_pfad: str | Path) -> dict[str, pd.DataFrame]:
    """Führt das SQL jedes Charts aus und liefert {Chart-Titel: DataFrame}.

    Jedes SQL wird zuerst geprüft (nur lesend) und läuft dann über eine schreibgeschützte Verbindung.
    Schlägt eine Prüfung fehl, wird nichts ausgeführt: es gibt keine Teilergebnisse.
    """
    for chart in config.charts:
        pruefe_nur_lesend(chart.sql)
    ergebnis: dict[str, pd.DataFrame] = {}
    verbindung = verbinde_nur_lesend(db_pfad)
    try:
        for chart in config.charts:
            ergebnis[chart.titel] = sortiere(chart, pd.read_sql_query(chart.sql, verbindung))
    finally:
        verbindung.close()
    return ergebnis


@dataclass(frozen=True)
class Kopfdaten:
    """Angaben für das Schriftfeld: wie viele Zeilen hat die Tabelle, und wie aktuell sind die Daten?"""

    zeilen: int | None  # None: Tabelle nicht gefunden
    stand: str | None  # jüngstes Datum der ersten Datumsspalte, als TT.MM.JJJJ; None ohne Datumsspalte


def _deutsch(text: str) -> str:
    """Tauscht englische gegen deutsche Trennzeichen: 1,234.5 -> 1.234,5 (Punkt = Tausender, Komma = Dezimal)."""
    return text.translate(str.maketrans(",.", ".,"))


def format_ganz(wert: object) -> str:
    return _deutsch(f"{int(wert):,}")


def format_dezimal(wert: float, kuerzen: bool = False) -> str:
    """Zwei Nachkommastellen; mit kuerzen entfallen überflüssige Nullen (103,2 statt 103,20)."""
    text = f"{wert:,.2f}"
    if kuerzen:
        text = text.rstrip("0").rstrip(".")
    return _deutsch(text)


def formatiere_vorschau(df: pd.DataFrame, spalten: list) -> pd.DataFrame:
    """Macht aus den geprüften Upload-Daten eine Anzeige in deutscher Schreibweise (nur für die Vorschau; gespeichert wird weiterhin ISO-Datum und Punkt)."""
    typ = {s.name: s.typ for s in spalten}
    anzeige = df.astype(object).copy()
    for name in df.columns:
        art = typ.get(name, "text")
        if art == "datum":
            anzeige[name] = df[name].map(lambda v: formatiere_datum(v) or "")
        elif art == "dezimal":
            anzeige[name] = df[name].map(lambda v: format_dezimal(float(v)))
        elif art == "ganzzahl":
            anzeige[name] = df[name].map(format_ganz)
        elif art == "bool":
            anzeige[name] = df[name].map(lambda v: "ja" if int(v) else "nein")
    return anzeige.astype(str)


def formatiere_datum(wert: object) -> str | None:
    """'2026-12-31' -> '31.12.2026'; mit Uhrzeit '2026-12-31 11:20:10' -> '31.12.2026 11:20'. Alles andere bleibt Text; leer wird None."""
    if wert is None or str(wert).strip() == "":
        return None
    text = str(wert).strip()
    try:
        if len(text) > 10 and ":" in text:
            return datetime.strptime(text[:16], "%Y-%m-%d %H:%M").strftime("%d.%m.%Y %H:%M")
        return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return text


def lade_kopfdaten(config: DashboardConfig, db_pfad: str | Path) -> Kopfdaten:
    """Zeilenzahl und Datenstand für das Schriftfeld. Nur lesend; Tabellen- und Spaltennamen werden vorab gegen die Datenbank geprüft."""
    verbindung = verbinde_nur_lesend(db_pfad)
    try:
        vorhanden = verbindung.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (config.tabelle,)
        ).fetchone()
        if not vorhanden:
            return Kopfdaten(None, None)
        tabelle = bezeichner_zitieren(config.tabelle)
        zeilen = verbindung.execute(f"SELECT COUNT(*) FROM {tabelle}").fetchone()[0]
        datumsspalte = next((s.name for s in config.spalten if s.typ == "datum"), None)
        stand = None
        if datumsspalte:
            in_db = {zeile[1] for zeile in verbindung.execute(f"PRAGMA table_info({tabelle})")}
            if datumsspalte in in_db:
                spalte = bezeichner_zitieren(datumsspalte)
                stand = formatiere_datum(verbindung.execute(f"SELECT MAX({spalte}) FROM {tabelle}").fetchone()[0])
        return Kopfdaten(int(zeilen), stand)
    finally:
        verbindung.close()


def layout_zeilen(charts: list[Chart]) -> list[list[Chart]]:
    """Ordnet Charts in Zeilen: 'voll' belegt eine Zeile allein, 'halb' wird paarweise nebeneinander gesetzt."""
    zeilen: list[list[Chart]] = []
    offen: list[Chart] = []
    for chart in charts:
        if chart.breite == "voll":
            if offen:
                zeilen.append(offen)
                offen = []
            zeilen.append([chart])
        else:
            offen.append(chart)
            if len(offen) == 2:
                zeilen.append(offen)
                offen = []
    if offen:
        zeilen.append(offen)
    return zeilen
