"""Streamlit-Oberfläche des Dashboard-Runners (bewusst dünn: Logik liegt in daten.py, charts.py, sicherheit.py).

Start:  streamlit run src/dashboard_framework/runner/app.py
Konfiguration über Umgebungsvariablen:
  DASHBOARD_CONFIG  Pfad zur dashboard.json (Standard: examples/sales/dashboard.json)
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import streamlit as st

from dashboard_framework.models.dashboard_config import DashboardConfig
from dashboard_framework.runner.charts import erstelle_figur, kennzahl_wert, waehle_farbe
from dashboard_framework.runner.daten import lade_chart_daten, layout_zeilen
from dashboard_framework.runner.framework_lib import (
    UploadFehler,
    lese_csv,
    uebernehmen,
    validate_against_schema,
    zaehle_vorhandene_zeilen,
)
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


def _upload_bereich(config: DashboardConfig, db_datei: Path) -> None:
    """Daten-Upload (US-10): CSV wählen -> automatisch prüfen -> Vorschau -> erst nach Klick auf 'Übernehmen' schreiben."""
    st.markdown(
        "Neue Datenzeilen als CSV-Datei hochladen. Sie werden an die bestehende Tabelle **angehängt**; "
        "vorhandene Daten werden weder geändert noch überschrieben."
    )
    st.caption("Erwartete Spalten: " + ", ".join(f"`{s.name}` ({s.typ})" for s in config.spalten))
    meldung = st.session_state.pop("upload_meldung", None)
    if meldung:
        st.success(meldung)
    nummer = st.session_state.setdefault("upload_nr", 0)  # neuer Schlüssel = leeres Upload-Feld nach erfolgreicher Übernahme
    datei = st.file_uploader("CSV-Datei", type=["csv"], key=f"upload_{nummer}")
    if datei is None:
        return
    try:
        geprueft = validate_against_schema(lese_csv(datei.getvalue()), config.spalten)
    except UploadFehler as fehler:
        st.error("Die Datei kann nicht übernommen werden:")
        for text in fehler.meldungen:
            st.markdown(f"- {text}")
        return
    st.success(f"{len(geprueft)} Zeilen sind gültig.")
    doppelt = zaehle_vorhandene_zeilen(geprueft, db_datei, config.tabelle)
    if doppelt:
        st.warning(
            f"{doppelt} dieser Zeilen gibt es bereits genau so in den Daten. "
            "Wenn Sie die Datei schon einmal hochgeladen haben, würden die Werte doppelt gezählt."
        )
    st.dataframe(geprueft.head(10), hide_index=True, use_container_width=True)
    if len(geprueft) > 10:
        st.caption(f"Vorschau: erste 10 von {len(geprueft)} Zeilen")
    if st.button("Übernehmen", type="primary"):
        try:
            anzahl = uebernehmen(geprueft, db_datei, config.tabelle)
        except (UploadFehler, sqlite3.Error) as fehler:
            st.error(f"Übernahme fehlgeschlagen, es wurde nichts geschrieben: {fehler}")
            return
        st.session_state["upload_meldung"] = f"{anzahl} Zeilen wurden übernommen."
        st.session_state["upload_nr"] = nummer + 1
        st.rerun()


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
    logo = config_pfad.parent / config.branding.logo if config.branding.logo else None
    if logo and logo.exists():
        kopf_logo, kopf_text = st.columns([1, 6])  # Logo-Spalte nur, wenn es ein Logo gibt (sonst bliebe sie leer)
        kopf_logo.image(str(logo), width=96)
    else:
        kopf_text = st.container()
    kopf_text.title(config.titel)
    if config.branding.firmenname:
        kopf_text.caption(config.branding.firmenname)

    tab_namen = ["Dashboard", "Über dieses Dashboard"] + (["Daten aktualisieren"] if config.spalten else [])
    tabs = st.tabs(tab_namen)
    with tabs[0]:
        for zeile in layout_zeilen(config.charts):
            spalten = st.columns(len(zeile))
            for spalte, chart in zip(spalten, zeile):
                with spalte:
                    _zeige_chart(chart, daten[chart.titel], farben)
    with tabs[1]:
        st.markdown(config.doku or "Für dieses Dashboard liegt noch keine Dokumentation vor.")
    if config.spalten:
        with tabs[2]:
            _upload_bereich(config, db_datei)


if __name__ == "__main__":
    main()
