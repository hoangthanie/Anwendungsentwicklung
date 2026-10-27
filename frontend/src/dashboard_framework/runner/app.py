"""Streamlit-Oberfläche des Dashboard-Runners im Gestaltungssystem "Formblatt".

Bewusst dünn: Daten und Prüfungen liegen in daten.py, charts.py, framework_lib.py, branding.py; das Aussehen in ui/.

Start:  streamlit run src/dashboard_framework/runner/app.py
Konfiguration über Umgebungsvariablen:
  DASHBOARD_CONFIG  Pfad zur dashboard.json (Standard: examples/sales/dashboard.json)
"""
from __future__ import annotations

import base64
import os
import sqlite3
from pathlib import Path

import streamlit as st

from dashboard_framework.models.dashboard_config import Chart, DashboardConfig
from dashboard_framework.runner.branding import BrandingFehler, lade_logo, pruefe_logo_bytes
from dashboard_framework.runner.charts import erstelle_figur, kennzahl_wert
from dashboard_framework.runner.daten import Kopfdaten, formatiere_vorschau, lade_chart_daten, lade_kopfdaten, layout_zeilen
from dashboard_framework.runner.framework_lib import (
    UploadFehler,
    lese_csv,
    uebernehmen,
    validate_against_schema,
    zaehle_vorhandene_zeilen,
)
from dashboard_framework.runner.sicherheit import UnsicheresSql
from dashboard_framework.ui.komponenten import esc, feldkopf, fussleiste, kennzahl, marke, schriftfeld, zahl
from dashboard_framework.ui.theme import akzent_pruefen, wende_an

STANDARD_CONFIG = Path(__file__).resolve().parents[3] / "examples" / "sales" / "dashboard.json"
DARSTELLUNG = {"balken": "Balken", "linie": "Linie", "tabelle": "Tabelle", "kennzahl": "Kennzahl"}
PLOTLY_CONFIG = {"displayModeBar": False}  # Zoom- und Export-Leiste würde nur ablenken


@st.cache_data(show_spinner=False)
def _lade(config_pfad: str, db_stand: float, config_stand: float):
    """Konfiguration, Diagrammdaten und Kopfdaten laden. db_stand und config_stand (Änderungszeiten von Datenbank und dashboard.json)
    sind Teil des Cache-Schlüssels: ändert sich eine der beiden Dateien, wird automatisch neu geladen."""
    config = DashboardConfig.laden(config_pfad)
    db_pfad = Path(config_pfad).parent / config.db_pfad
    return config, lade_chart_daten(config, db_pfad), lade_kopfdaten(config, db_pfad)


def _logo_uri(config_pfad: Path, config: DashboardConfig) -> str | None:
    """Das Logo als data-URI fürs Schriftfeld. Es wurde vorher als echtes PNG/JPEG geprüft; bei Problemen gibt es eine kleine Warnung."""
    if not config.branding.logo:
        return None
    try:
        inhalt = lade_logo(config_pfad.parent, config.branding.logo)
        mime = "image/png" if pruefe_logo_bytes(inhalt) == "PNG" else "image/jpeg"
    except BrandingFehler as fehler:
        st.warning(f"Das Logo wird nicht angezeigt: {fehler}")
        return None
    return f"data:{mime};base64,{base64.b64encode(inhalt).decode('ascii')}"


def _kopf(config: DashboardConfig, kopf: Kopfdaten, logo_uri: str | None) -> str:
    zellen = []
    if config.branding.firmenname:
        zellen.append(("Kunde", config.branding.firmenname))
    if kopf.stand:
        zellen.append(("Datenstand", kopf.stand))
    if kopf.zeilen is not None:
        zellen.append(("Zeilen", zahl(kopf.zeilen)))
    # Jede Abfrage der Konfiguration wurde vor dem Laden als reines SELECT geprüft (lade_chart_daten) und läuft über eine schreibgeschützte Verbindung.
    zellen.append(("Datenzugriff", "nur lesend", "gueltig"))
    return schriftfeld(config.titel, zellen, logo_uri)


def _feld(nummer: int, chart: Chart, df, farben: list[str]) -> None:
    with st.container(border=True, key=f"feld_{nummer}"):
        st.markdown(feldkopf(chart.titel, nummer), unsafe_allow_html=True)
        if chart.typ == "tabelle":
            st.dataframe(df, hide_index=True, width="stretch")
        elif chart.typ == "kennzahl":
            st.markdown(kennzahl(kennzahl_wert(df)), unsafe_allow_html=True)
        else:
            st.plotly_chart(erstelle_figur(chart, df, farben), width="stretch", config=PLOTLY_CONFIG)
        angaben = []
        if chart.beschreibung:  # Herkunft der Zahl in Worten; die Backticks sind nur Spaltenanker für die Prüfung
            angaben.append(("Berechnung", chart.beschreibung.replace("`", "")))
        if chart.sortierung != "keine":
            angaben.append(("Sortierung", chart.sortierung))
        angaben.append(("Ergebnis", f"{zahl(len(df))} Zeilen" if len(df) != 1 else "1 Zeile"))
        st.markdown(fussleiste(angaben, breit_erste=bool(chart.beschreibung)), unsafe_allow_html=True)


def _upload_bereich(config: DashboardConfig, db_datei: Path) -> None:
    """Daten-Upload (US-10) als drei Felder: Datei wählen, Prüfung, Vorschau und Übernahme. Erst der Klick auf 'Übernehmen' schreibt."""
    meldung = st.session_state.pop("upload_meldung", None)
    nummer = st.session_state.setdefault("upload_nr", 0)  # neuer Schlüssel = leeres Upload-Feld nach erfolgreicher Übernahme

    with st.container(border=True, key="feld_upload_datei"):
        st.markdown(feldkopf("Datei wählen", 1), unsafe_allow_html=True)
        st.markdown(
            "Neue Datenzeilen als CSV-Datei hochladen. Sie werden an die bestehende Tabelle **angehängt**; "
            "vorhandene Daten werden weder geändert noch überschrieben."
        )
        st.markdown("**Erwartete Spalten:** " + ", ".join(f"`{s.name}` ({s.typ})" for s in config.spalten))
        datei = st.file_uploader("CSV-Datei", type=["csv"], key=f"upload_{nummer}")

    geprueft, fehler = None, []
    if datei is not None:
        try:
            geprueft = validate_against_schema(lese_csv(datei.getvalue()), config.spalten)
        except UploadFehler as problem:
            fehler = problem.meldungen

    with st.container(border=True, key="feld_upload_pruefung"):
        st.markdown(feldkopf("Prüfung", 2), unsafe_allow_html=True)
        if meldung:
            st.markdown(marke("übernommen", "uebernommen"), unsafe_allow_html=True)
            st.markdown(meldung)
        elif datei is None:
            st.markdown(marke("keine Datei", "offen"), unsafe_allow_html=True)
        elif fehler:
            st.markdown(marke("fehlerhaft", "fehler"), unsafe_allow_html=True)
            st.markdown("Die Datei kann nicht übernommen werden:")
            for text in fehler:
                st.markdown(f"- {text}")
        else:
            st.markdown(marke("gültig", "gueltig"), unsafe_allow_html=True)
            st.markdown(f"{zahl(len(geprueft))} Zeilen sind gültig.")
            doppelt = zaehle_vorhandene_zeilen(geprueft, db_datei, config.tabelle)
            if doppelt:
                st.markdown(marke("Hinweis", "hinweis"), unsafe_allow_html=True)
                st.markdown(
                    f"{doppelt} dieser Zeilen gibt es bereits genau so in den Daten. "
                    "Wenn Sie die Datei schon einmal hochgeladen haben, würden die Werte doppelt gezählt."
                )

    if geprueft is not None:
        with st.container(border=True, key="feld_upload_uebernahme"):
            st.markdown(feldkopf("Vorschau und Übernahme", 3), unsafe_allow_html=True)
            st.dataframe(formatiere_vorschau(geprueft.head(10), config.spalten), hide_index=True, width="stretch")
            st.caption(
                "Anzeige in deutscher Schreibweise; gespeichert werden Datum als JJJJ-MM-TT und Zahlen mit Punkt."
                + (f" Vorschau: erste 10 von {zahl(len(geprueft))} Zeilen." if len(geprueft) > 10 else "")
            )
            if st.button("Übernehmen", type="primary"):
                try:
                    anzahl = uebernehmen(geprueft, db_datei, config.tabelle)
                except (UploadFehler, sqlite3.Error) as problem:
                    st.markdown(marke("fehlerhaft", "fehler"), unsafe_allow_html=True)
                    st.markdown(f"Übernahme fehlgeschlagen, es wurde nichts geschrieben: {esc(problem)}")
                    return
                st.session_state["upload_meldung"] = f"{zahl(anzahl)} Zeilen wurden übernommen."
                st.session_state["upload_nr"] = nummer + 1
                st.rerun()


def main() -> None:
    config_pfad = Path(os.environ.get("DASHBOARD_CONFIG", STANDARD_CONFIG))
    st.set_page_config(page_title="Dashboard", layout="wide")
    try:
        config_roh = DashboardConfig.laden(config_pfad)
        db_datei = config_pfad.parent / config_roh.db_pfad
        config, daten, kopf = _lade(str(config_pfad), db_datei.stat().st_mtime, config_pfad.stat().st_mtime)
    except FileNotFoundError as fehler:
        wende_an()
        st.error(f"Datei nicht gefunden: {fehler.filename}")
        return
    except UnsicheresSql as fehler:
        wende_an()
        st.error(f"Die Konfiguration enthält unerlaubtes SQL und wurde nicht ausgeführt: {fehler}")
        return
    except Exception as fehler:  # ungültige Konfiguration, kaputte DB: verständliche Meldung statt Stacktrace
        wende_an()
        st.error(f"Das Dashboard kann nicht angezeigt werden: {fehler}")
        return

    farben = config.branding.farben
    wende_an(farben[0] if farben else None)  # erste Kundenfarbe = Akzent (aktiver Tab, Hauptaktion); ungültig -> Produktfarbe
    st.markdown(_kopf(config, kopf, _logo_uri(config_pfad, config)), unsafe_allow_html=True)

    tab_namen = ["Dashboard", "Über dieses Dashboard"] + (["Daten aktualisieren"] if config.spalten else [])
    tabs = st.tabs(tab_namen)
    with tabs[0]:
        nummer = 0
        for zeile in layout_zeilen(config.charts):
            for spalte, chart in zip(st.columns(len(zeile), gap="medium"), zeile):
                nummer += 1
                with spalte:
                    _feld(nummer, chart, daten[chart.titel], farben)
    with tabs[1]:
        with st.container(key="lesetext"):
            st.markdown(config.doku or "Für dieses Dashboard liegt noch keine Dokumentation vor.")
    if config.spalten:
        with tabs[2]:
            _upload_bereich(config, db_datei)


if __name__ == "__main__":
    main()
