"""Erzeugt aus Chart-Konfiguration und Daten eine Plotly-Figur bzw. einen Kennzahl-Wert.

Der Runner kennt nur diese vier Typen (balken, linie, tabelle, kennzahl); welche Daten sie zeigen, steht in der Konfiguration.
Die Figuren folgen dem Gestaltungssystem "Formblatt": Haarlinien, keine Kästen, Schrift Barlow, deutsche Zahlenschreibweise.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from dashboard_framework.models.dashboard_config import Chart
from dashboard_framework.runner.daten import achsen, format_dezimal, format_ganz
from dashboard_framework.ui.theme import BLATT, HAARLINIE, LINIE_STARK, PRODUKT_AKZENT, TINTE, TINTE_2

STANDARD_FARBE = PRODUKT_AKZENT


def waehle_farbe(chart: Chart, firmenfarben: list[str]) -> str:
    """Chart-Farbe, sonst erste Firmenfarbe, sonst Produktfarbe."""
    if chart.farbe:
        return chart.farbe
    return firmenfarben[0] if firmenfarben else STANDARD_FARBE


def erstelle_figur(chart: Chart, df: pd.DataFrame, firmenfarben: list[str]) -> Figure:
    """Figur für die Typen 'balken' und 'linie'. Andere Typen werden anders dargestellt (siehe app.py)."""
    x, y = achsen(chart, df)
    farbe = waehle_farbe(chart, firmenfarben)
    if chart.typ == "balken":
        beschriften = len(df) <= 12 and pd.api.types.is_numeric_dtype(df[y])  # Werte an den Balken, damit man nichts am Gitter ablesen muss; bei vielen Balken wäre es zu eng
        fig = px.bar(df, x=x, y=y, text=y if beschriften else None, color_discrete_sequence=[farbe])
        fig.update_traces(marker_line_width=0)
        if beschriften:
            fig.update_traces(texttemplate="%{y:" + _zahlenformat(df[y]) + "}", textposition="outside", cliponaxis=False, textfont=dict(size=13, color=TINTE))
            if (df[y] >= 0).all() and df[y].max() > 0:
                fig.update_yaxes(range=[0, float(df[y].max()) * 1.15])  # Platz für die Beschriftung über dem höchsten Balken
    elif chart.typ == "linie":
        fig = px.line(df, x=x, y=y, markers=True, color_discrete_sequence=[farbe])
        fig.update_traces(line_width=2.5, marker_size=7)
    else:
        raise ValueError(f"Chart-Typ '{chart.typ}' hat keine Figur")
    achstitel = dict(size=13, color=TINTE_2)
    fig.update_layout(
        height=320,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor=BLATT,
        plot_bgcolor=BLATT,
        font=dict(family="Barlow, sans-serif", size=14, color=TINTE),
        separators=",.",  # deutsche Schreibweise: Dezimalkomma, Punkt als Tausendertrenner
        bargap=0.35,
        hoverlabel=dict(font_family="Barlow, sans-serif", bgcolor=BLATT, bordercolor=LINIE_STARK),
        xaxis=dict(showgrid=False, linecolor=LINIE_STARK, ticks="outside", tickcolor=LINIE_STARK, title=None),  # Rubriken erklären sich selbst
        yaxis=dict(gridcolor=HAARLINIE, zeroline=False, tickformat=",.0f", title_font=achstitel),
    )
    return fig


def _zahlenformat(serie: pd.Series) -> str:
    """d3-Format für Wertbeschriftungen: ganze Zahlen oder große Werte ohne Nachkommastellen, kleine Werte mit zwei."""
    ganz = bool((serie.dropna() % 1 == 0).all()) or float(serie.abs().max()) >= 1000
    return ",.0f" if ganz else ",.2f"


def kennzahl_wert(df: pd.DataFrame) -> str:
    """Erster Wert der ersten Zeile als lesbarer Text; 'n/a' bei leerem Ergebnis."""
    if df.empty:
        return "n/a"
    wert = df.iloc[0, 0]
    if hasattr(wert, "item"):  # numpy-Zahlentypen (z. B. int64) in normale Python-Typen umwandeln
        wert = wert.item()
    if isinstance(wert, float) and not wert.is_integer():
        return format_dezimal(wert, kuerzen=True)  # höchstens zwei Nachkommastellen, deutsche Schreibweise (103,2 statt 103.20)
    if isinstance(wert, (int, float)):
        return format_ganz(wert)
    return str(wert)
