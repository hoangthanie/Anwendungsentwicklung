"""Daten für den Runner: führt das in der dashboard.json hinterlegte SQL aus (US-09.1).

Reine Funktionen ohne Streamlit, damit sie ohne Browser testbar sind.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from dashboard_framework.models.dashboard_config import Chart, DashboardConfig
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
