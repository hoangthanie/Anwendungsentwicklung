"""Erzeugt aus Chart-Konfiguration und Daten eine Plotly-Figur bzw. einen Kennzahl-Wert.

Der Runner kennt nur diese vier Typen (balken, linie, tabelle, kennzahl); welche Daten sie zeigen, steht in der Konfiguration.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from dashboard_framework.models.dashboard_config import Chart
from dashboard_framework.runner.daten import achsen

STANDARD_FARBE = "#1F77B4"


def waehle_farbe(chart: Chart, firmenfarben: list[str]) -> str:
    """Chart-Farbe, sonst erste Firmenfarbe, sonst neutrale Standardfarbe."""
    if chart.farbe:
        return chart.farbe
    return firmenfarben[0] if firmenfarben else STANDARD_FARBE


def erstelle_figur(chart: Chart, df: pd.DataFrame, firmenfarben: list[str]) -> Figure:
    """Figur für die Typen 'balken' und 'linie'. Andere Typen werden anders dargestellt (siehe app.py)."""
    x, y = achsen(chart, df)
    farbe = waehle_farbe(chart, firmenfarben)
    if chart.typ == "balken":
        fig = px.bar(df, x=x, y=y, color_discrete_sequence=[farbe])
    elif chart.typ == "linie":
        fig = px.line(df, x=x, y=y, markers=True, color_discrete_sequence=[farbe])
    else:
        raise ValueError(f"Chart-Typ '{chart.typ}' hat keine Figur")
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=320)
    return fig


def kennzahl_wert(df: pd.DataFrame) -> str:
    """Erster Wert der ersten Zeile als lesbarer Text; 'n/a' bei leerem Ergebnis."""
    if df.empty:
        return "n/a"
    wert = df.iloc[0, 0]
    if hasattr(wert, "item"):  # numpy-Zahlentypen (z. B. int64) in normale Python-Typen umwandeln
        wert = wert.item()
    if isinstance(wert, float) and not wert.is_integer():
        return f"{wert:,.2f}".replace(",", " ")
    if isinstance(wert, (int, float)):
        return f"{int(wert):,}".replace(",", " ")
    return str(wert)
