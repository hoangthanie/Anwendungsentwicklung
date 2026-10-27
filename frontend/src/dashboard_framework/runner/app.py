"""Streamlit-Oberfläche des Dashboard-Runners (bewusst dünn: Logik liegt in daten.py, charts.py, sicherheit.py).

Start:  streamlit run src/dashboard_framework/runner/app.py
Konfiguration über Umgebungsvariablen:
  DASHBOARD_CONFIG  Pfad zur dashboard.json (Standard: examples/sales/dashboard.json)
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from dashboard_framework.models.dashboard_config import DashboardConfig
from dashboard_framework.runner.charts import erstelle_figur, kennzahl_wert, waehle_farbe
from dashboard_framework.runner.daten import lade_chart_daten, layout_zeilen
from dashboard_framework.runner.sicherheit import UnsicheresSql

STANDARD_CONFIG = Path(__file__).resolve().parents[3] / "examples" / "sales" / "dashboard.json"


@st.cache_data(show_spinner=False)
def _lade(config_pfad: str, db_stand: float):
    """Konfiguration und Daten laden. db_stand (Änderungszeit der DB) ist Teil des Cache-Schlüssels:
    ändert sich die Datenbank, wird automatisch neu geladen."""
    config = DashboardConfig.laden(config_pfad)
    db_pfad = Path(config_pfad).parent / config.db_pfad
    return config, lade_chart_daten(config, db_pfad)


def _zeige_chart(chart, df, firmenfarben) -> None:
    st.subheader(chart.titel)
    if chart.typ == "tabelle":
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif chart.typ == "kennzahl":
        st.metric(label=chart.titel, value=kennzahl_wert(df))
    else:
        st.plotly_chart(erstelle_figur(chart, df, firmenfarben), use_container_width=True)


def main() -> None:
    config_pfad = Path(os.environ.get("DASHBOARD_CONFIG", STANDARD_CONFIG))
    st.set_page_config(page_title="Dashboard", layout="wide")
    try:
        config_roh = DashboardConfig.laden(config_pfad)
        db_datei = config_pfad.parent / config_roh.db_pfad
        config, daten = _lade(str(config_pfad), db_datei.stat().st_mtime)
    except FileNotFoundError as fehler:
        st.error(f"Datei nicht gefunden: {fehler.filename}")
        return
    except UnsicheresSql as fehler:
        st.error(f"Die Konfiguration enthält unerlaubtes SQL und wurde nicht ausgeführt: {fehler}")
        return
    except Exception as fehler:  # ungültige Konfiguration, kaputte DB: verständliche Meldung statt Stacktrace
        st.error(f"Das Dashboard kann nicht angezeigt werden: {fehler}")
        return

    farben = config.branding.farben
    kopf_logo, kopf_text = st.columns([1, 6])
    if config.branding.logo:
        logo = config_pfad.parent / config.branding.logo
        if logo.exists():
            kopf_logo.image(str(logo), width=96)
    kopf_text.title(config.titel)
    if config.branding.firmenname:
        kopf_text.caption(config.branding.firmenname)

    tab_dashboard, tab_doku = st.tabs(["Dashboard", "Über dieses Dashboard"])
    with tab_dashboard:
        for zeile in layout_zeilen(config.charts):
            spalten = st.columns(len(zeile))
            for spalte, chart in zip(spalten, zeile):
                with spalte:
                    _zeige_chart(chart, daten[chart.titel], farben)
    with tab_doku:
        st.markdown(config.doku or "Für dieses Dashboard liegt noch keine Dokumentation vor.")


if __name__ == "__main__":
    main()
