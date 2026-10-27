"""Eingabe-App (Streamlit, PSP 6.1 und 6.2): erfasst Ziel, Publikum, Spalten, KPIs und Branding und erzeugt eine geprüfte artefakt.yaml.

Die Seite ist bewusst dünn: Prüfung und Speichern liegen in formular.py, branding_form.py und models/artefakt.py (dort testbar ohne Browser).

Start:  streamlit run src/dashboard_framework/eingabe/app.py
Umgebungsvariable ARTEFAKT_ORDNER: Zielordner für gespeicherte Artefakte (Standard: frontend/artefakte)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import get_args

import pandas as pd
import streamlit as st

from dashboard_framework.eingabe.branding_form import baue_branding
from dashboard_framework.eingabe.formular import (
    artefakt_aus_formular,
    meldungen_zu_feld,
    speichere_artefakt_ordner,
    spalten_vorschlag,
    vorhandene_artefakte,
    zeilen_aus_tabelle,
)
from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler
from dashboard_framework.models.spalten import SpaltenTyp
from dashboard_framework.runner.branding import MAX_LOGO_BYTES, BrandingFehler
from dashboard_framework.runner.framework_lib import UploadFehler, lese_csv

ARTEFAKT_ORDNER = Path(os.environ.get("ARTEFAKT_ORDNER", Path(__file__).resolve().parents[3] / "artefakte"))
TYPEN = list(get_args(SpaltenTyp))
SPALTEN_FELDER = ["name", "typ", "beschreibung"]
KPI_FELDER = ["name", "beschreibung"]
TEXTFELDER = ("f_name", "f_titel", "f_ziel", "f_publikum", "f_tabelle")


def _leere_tabelle(felder: list[str]) -> pd.DataFrame:
    return pd.DataFrame({f: pd.Series([], dtype="object") for f in felder})


def _starte() -> None:
    st.session_state.setdefault("spalten_df", _leere_tabelle(SPALTEN_FELDER))
    st.session_state.setdefault("kpi_df", _leere_tabelle(KPI_FELDER))
    st.session_state.setdefault("editor_nr", 0)  # neuer Wert = Tabellen-Editoren starten mit den neuen Daten
    for feld in TEXTFELDER:
        st.session_state.setdefault(feld, "")
    st.session_state.setdefault("f_firmenname", "")
    st.session_state.setdefault("f_farben", "")


def _lade_vorhandenes(name: str) -> None:
    """Callback: füllt das Formular aus einem gespeicherten Artefakt."""
    try:
        artefakt = Artefakt.aus_yaml(ARTEFAKT_ORDNER / name / "artefakt.yaml")
    except ArtefaktFehler as fehler:
        st.session_state["lade_fehler"] = fehler.meldungen
        return
    st.session_state.update(
        f_name=artefakt.name, f_titel=artefakt.titel, f_ziel=artefakt.ziel, f_publikum=artefakt.publikum,
        f_tabelle=artefakt.tabelle, f_firmenname=artefakt.branding.firmenname, f_farben=", ".join(artefakt.branding.farben),
        spalten_df=pd.DataFrame([s.model_dump() for s in artefakt.spalten], columns=SPALTEN_FELDER),
        kpi_df=pd.DataFrame([k.model_dump() for k in artefakt.kpis], columns=KPI_FELDER),
        editor_nr=st.session_state["editor_nr"] + 1,
    )
    st.session_state.pop("lade_fehler", None)


def _farbfelder(farben: list[str]) -> str:
    # Die Codes sind bereits als #RRGGBB geprüft (normalisiere_farben), daher unkritisch im HTML.
    felder = "".join(
        f'<span style="display:inline-block;width:40px;height:40px;margin-right:8px;border-radius:8px;background:{f};'
        f'border:1px solid #8884" title="{f}"></span>'
        for f in farben
    )
    return f"<div>{felder}</div>"


def _zeige_meldungen(titel: str, meldungen: list[str]) -> None:
    st.error(titel)
    for text in meldungen:
        st.markdown(f"- {text}")


def main() -> None:
    st.set_page_config(page_title="Dashboard-Eingabe", layout="wide")
    _starte()
    st.title("Dashboard-Eingabe")
    st.caption(
        "Beschreiben Sie Ihr Dashboard. Fehler werden angezeigt, bevor etwas erzeugt wird. "
        "Hinweis: Ein Textfeld übernimmt Ihre Eingabe erst mit Enter oder wenn Sie das Feld verlassen."
    )
    status = st.container()  # wird am Ende gefüllt; steht oben, damit der Stand immer sichtbar ist

    vorhanden = vorhandene_artefakte(ARTEFAKT_ORDNER)
    if vorhanden:
        spalte_a, spalte_b = st.columns([3, 1], vertical_alignment="bottom")
        auswahl = spalte_a.selectbox("Gespeichertes Artefakt laden", vorhanden)
        spalte_b.button("Laden", on_click=_lade_vorhandenes, args=(auswahl,))
        if "lade_fehler" in st.session_state:
            _zeige_meldungen("Das Artefakt konnte nicht geladen werden:", st.session_state["lade_fehler"])

    nr = st.session_state["editor_nr"]

    st.header("1. Grunddaten")
    links, rechts = st.columns(2)
    feld_platz = {}  # je Feld ein Platz direkt darunter für dessen Fehlermeldungen (gefüllt, sobald die Prüfung gelaufen ist)
    links.text_input("Name (Ordner- und Dateiname)", key="f_name", placeholder="mein_dashboard",
                     help="Kleinbuchstaben, Ziffern und _; muss mit einem Buchstaben beginnen.")
    feld_platz["name"] = links.container()
    rechts.text_input("Titel des Dashboards", key="f_titel", placeholder="Mein Dashboard")
    feld_platz["titel"] = rechts.container()
    links.text_area("Ziel: Wozu dient das Dashboard?", key="f_ziel", height=100)
    feld_platz["ziel"] = links.container()
    rechts.text_area("Publikum: Wer nutzt es?", key="f_publikum", height=100, placeholder="z. B. Geschäftsleitung")
    feld_platz["publikum"] = rechts.container()
    links.text_input("Tabellenname in der Datenbank", key="f_tabelle", placeholder="meine_tabelle")
    feld_platz["tabelle"] = links.container()

    st.header("2. Daten und Spalten")
    csv = st.file_uploader("Beispieldatei (CSV) hochladen: Spalten und Typen werden vorgeschlagen", type=["csv"])
    if csv is not None and st.session_state.get("csv_marke") != (csv.name, csv.size):
        try:
            vorschlag = spalten_vorschlag(lese_csv(csv.getvalue()))
        except UploadFehler as fehler:
            _zeige_meldungen("Die Datei kann nicht gelesen werden:", fehler.meldungen)
        else:
            st.session_state.update(
                spalten_df=pd.DataFrame(vorschlag, columns=SPALTEN_FELDER), csv_marke=(csv.name, csv.size), editor_nr=nr + 1
            )
            st.rerun()
    st.caption(
        "Typ und Bedeutung jeder Spalte. Der Typ ist nur ein Vorschlag aus den Werten; die Bedeutung (Beschreibung) kennen nur Sie. "
        "Spaltennamen ohne Leerzeichen."
    )
    spalten_df = st.data_editor(
        st.session_state["spalten_df"], key=f"spalten_{nr}", num_rows="dynamic", hide_index=True, use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Name", required=True),
            "typ": st.column_config.SelectboxColumn("Typ", options=TYPEN, required=True),
            "beschreibung": st.column_config.TextColumn("Beschreibung (Bedeutung der Spalte)"),
        },
    )
    spalten = zeilen_aus_tabelle(spalten_df, SPALTEN_FELDER)

    st.header("3. Kennzahlen (KPIs)")
    namen = [s["name"] for s in spalten if s["name"]]
    st.caption(
        "Beschreiben Sie jede Kennzahl in einem Satz. **Setzen Sie jeden Spaltennamen in Backticks**, z. B. Summe von `spalte_a`, gruppiert nach `spalte_b`. "
        "So prüft das System vorab, ob die Spalten existieren."
    )
    if namen:
        st.caption("Verfügbare Spalten: " + ", ".join(f"`{n}`" for n in namen))
    kpi_df = st.data_editor(
        st.session_state["kpi_df"], key=f"kpis_{nr}", num_rows="dynamic", hide_index=True, use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Name der KPI", required=True),
            "beschreibung": st.column_config.TextColumn("Berechnung (Spalten in Backticks)", required=True, width="large"),
        },
    )
    kpis = zeilen_aus_tabelle(kpi_df, KPI_FELDER)

    st.header("4. Branding")
    links, rechts = st.columns(2)
    links.text_input("Firmenname", key="f_firmenname")
    rechts.text_input(
        "Firmenfarben", key="f_farben", placeholder="#1F3864, #ED7D31",
        help="Farbcodes im Format #RRGGBB, durch Komma getrennt. Die erste Farbe ist die Hauptfarbe.",
    )
    logo_datei = st.file_uploader(
        f"Logo (PNG oder JPEG, höchstens {MAX_LOGO_BYTES // (1024 * 1024)} MB)", type=["png", "jpg", "jpeg"]
    )

    st.header("5. Prüfung und Ergebnis")
    felder = {f.removeprefix("f_"): st.session_state[f].strip() for f in TEXTFELDER}
    nichts_eingegeben = not any(felder.values()) and not spalten and not kpis
    if nichts_eingegeben:
        with status:
            st.info("Füllen Sie die Felder aus. Die Prüfung läuft dabei laufend mit.")
        st.info("Das Ergebnis erscheint hier, sobald alle Angaben gültig sind.")
        return

    meldungen: list[str] = []
    branding, logo = None, None
    try:
        branding, logo = baue_branding(
            st.session_state["f_firmenname"], st.session_state["f_farben"], logo_datei.getvalue() if logo_datei else None
        )
    except BrandingFehler as fehler:
        meldungen.extend(fehler.meldungen)
    artefakt = None
    try:
        artefakt = artefakt_aus_formular({**felder, "spalten": spalten, "kpis": kpis, "branding": branding.model_dump() if branding else {}})
    except ArtefaktFehler as fehler:
        meldungen.extend(fehler.meldungen)

    if meldungen or artefakt is None:
        with status:
            _zeige_meldungen(f"{len(meldungen)} Punkt(e) müssen noch korrigiert werden:", meldungen)
        for feld, platz in feld_platz.items():  # dieselben Meldungen zusätzlich direkt unter dem betroffenen Feld
            with platz:
                for text in meldungen_zu_feld(meldungen, feld):
                    if not text.startswith("Pflichtfeld"):  # "noch leer" nicht rot unter jedes unberührte Feld; steht in der Status-Box oben
                        st.error(text)
        st.warning("Solange Punkte offen sind, wird kein Ergebnis angezeigt. Die Meldungen stehen oben und unter den Feldern.")
        return

    with status:
        st.success("Das Artefakt ist gültig. Das Ergebnis steht unten unter 5.")
    st.success("Das Artefakt ist gültig.")
    if branding.farben:
        st.markdown(_farbfelder(branding.farben), unsafe_allow_html=True)
    if logo:
        st.image(logo, width=96, caption="So wird das Logo gespeichert (neu erzeugtes PNG)")
    st.code(artefakt.zu_yaml(), language="yaml")
    st.download_button("artefakt.yaml herunterladen", data=artefakt.zu_yaml(), file_name="artefakt.yaml", mime="text/yaml")

    ueberschreiben = False
    if artefakt.name in vorhanden:
        ueberschreiben = st.checkbox(f"Vorhandenes Artefakt '{artefakt.name}' überschreiben")
    if st.button(f"In Ordner artefakte/{artefakt.name}/ speichern", type="primary"):
        try:
            ziel = speichere_artefakt_ordner(artefakt, logo, ARTEFAKT_ORDNER, ueberschreiben)
        except ArtefaktFehler as fehler:
            _zeige_meldungen("Speichern nicht möglich:", fehler.meldungen)
        else:
            st.success(f"Gespeichert: {ziel}")


if __name__ == "__main__":
    main()
