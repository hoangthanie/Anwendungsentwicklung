"""Eingabe-App (Streamlit, PSP 6.1 und 6.2) im Gestaltungssystem "Formblatt": erfasst Ziel, Publikum, Spalten, KPIs und Branding
und erzeugt eine geprüfte artefakt.yaml.

Die Seite ist bewusst dünn: Prüfung und Speichern liegen in formular.py, branding_form.py und models/artefakt.py (dort testbar ohne Browser);
das Aussehen liegt in ui/. Fünf nummerierte Felder bilden die Reihenfolge ab, in der man ein Artefakt ausfüllt.

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
    fuege_spalte_ein,
    meldungen_zu_feld,
    speichere_artefakt_ordner,
    spalten_vorschlag,
    vorhandene_artefakte,
    zeilen_aus_tabelle,
)
from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler, backticks_zu_anfuehrungszeichen
from dashboard_framework.models.spalten import SpaltenTyp
from dashboard_framework.runner.branding import MAX_LOGO_BYTES, BrandingFehler
from dashboard_framework.runner.framework_lib import UploadFehler, lese_csv
from dashboard_framework.ui.komponenten import esc, feldkopf, marke, schriftfeld
from dashboard_framework.ui.theme import wende_an

ARTEFAKT_ORDNER = Path(os.environ.get("ARTEFAKT_ORDNER", Path(__file__).resolve().parents[3] / "artefakte"))
TYPEN = list(get_args(SpaltenTyp))
SPALTEN_FELDER = ["name", "typ", "beschreibung"]
KPI_FELDER = ["name", "beschreibung"]
TEXTFELDER = ("f_name", "f_titel", "f_ziel", "f_publikum", "f_tabelle")


def _leere_tabelle(felder: list[str]) -> pd.DataFrame:
    return pd.DataFrame({f: pd.Series([], dtype="object") for f in felder})


def _starte() -> None:
    st.session_state.setdefault("spalten_df", _leere_tabelle(SPALTEN_FELDER))
    st.session_state.setdefault("kpi_ids", [0])  # eine Zeile je KPI; die Nummer bleibt stabil, auch wenn Zeilen wegfallen
    st.session_state.setdefault("kpi_naechste_id", 1)
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
        editor_nr=st.session_state["editor_nr"] + 1,
    )
    start = st.session_state["kpi_naechste_id"]
    ids = list(range(start, start + len(artefakt.kpis)))
    for kid, kpi in zip(ids, artefakt.kpis):
        st.session_state[f"kpi_name_{kid}"] = kpi.name
        st.session_state[f"kpi_text_{kid}"] = backticks_zu_anfuehrungszeichen(kpi.beschreibung)  # im Formular Anführungszeichen
    st.session_state["kpi_ids"], st.session_state["kpi_naechste_id"] = ids, start + len(ids)
    st.session_state.pop("lade_fehler", None)


def _neue_kpi() -> None:
    kid = st.session_state["kpi_naechste_id"]
    st.session_state["kpi_naechste_id"] = kid + 1
    st.session_state["kpi_ids"] = [*st.session_state["kpi_ids"], kid]


def _entferne_kpi(kid: int) -> None:
    rest = [i for i in st.session_state["kpi_ids"] if i != kid]
    if not rest:  # mindestens eine (leere) Zeile bleibt stehen
        rest = [st.session_state["kpi_naechste_id"]]
        st.session_state["kpi_naechste_id"] += 1
    st.session_state["kpi_ids"] = rest


def _fuege_spalte_ein(kid: int) -> None:
    """Callback der Spalten-Knöpfe: hängt den gewählten Spaltennamen an den Text dieser KPI an und setzt die Auswahl zurück."""
    wahl = st.session_state.get(f"kpi_pill_{kid}")
    if wahl:
        schluessel = f"kpi_text_{kid}"
        st.session_state[schluessel] = fuege_spalte_ein(st.session_state.get(schluessel, ""), wahl)
    st.session_state[f"kpi_pill_{kid}"] = None


def _farbfelder(farben: list[str]) -> str:
    # Die Codes sind bereits als #RRGGBB geprüft (normalisiere_farben), daher unkritisch im HTML.
    felder = "".join(
        f'<span style="display:inline-block;width:40px;height:40px;margin-right:8px;border-radius:2px;background:{f};'
        f'border:1px solid #7C8791" title="{esc(f)}"></span>'
        for f in farben
    )
    return f"<div>{felder}</div>"


def _kopf(artefakt_name: str, spalten: int, kpis: int, pruefung: tuple[str, str]) -> str:
    return schriftfeld(
        "Dashboard-Eingabe",
        [
            ("Artefakt", artefakt_name or "–"),
            ("Spalten", str(spalten)),
            ("KPIs", str(kpis)),
            ("Prüfung", pruefung[0], pruefung[1]),
            ("Speicherort", "artefakte/"),
        ],
    )


def main() -> None:
    st.set_page_config(page_title="Dashboard-Eingabe", layout="wide")
    _starte()
    wende_an()  # Produktfarbe als Akzent: in der Eingabe gibt es noch keinen Kunden
    kopf = st.container()  # wird am Ende gefüllt, steht aber oben: der Stand ist immer sichtbar
    st.caption(
        "Beschreiben Sie Ihr Dashboard. Fehler werden angezeigt, bevor etwas erzeugt wird. "
        "Ein Textfeld übernimmt Ihre Eingabe erst mit Enter oder wenn Sie das Feld verlassen."
    )

    vorhanden = vorhandene_artefakte(ARTEFAKT_ORDNER)
    if vorhanden:
        spalte_a, spalte_b = st.columns([3, 1], vertical_alignment="bottom")
        auswahl = spalte_a.selectbox("Gespeichertes Artefakt laden", vorhanden)
        spalte_b.button("Laden", on_click=_lade_vorhandenes, args=(auswahl,))
        if "lade_fehler" in st.session_state:
            st.markdown(marke("fehlerhaft", "fehler"), unsafe_allow_html=True)
            for text in st.session_state["lade_fehler"]:
                st.markdown(f"- {text}")

    nr = st.session_state["editor_nr"]
    feld_platz = {}  # je Feld ein Platz direkt darunter für dessen Fehlermeldungen (gefüllt, sobald die Prüfung gelaufen ist)

    with st.container(border=True, key="feld_grunddaten"):
        st.markdown(feldkopf("Grunddaten", 1), unsafe_allow_html=True)
        links, rechts = st.columns(2, gap="medium")
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

    with st.container(border=True, key="feld_spalten"):
        st.markdown(feldkopf("Daten und Spalten", 2), unsafe_allow_html=True)
        csv = st.file_uploader("Beispieldatei (CSV) hochladen: Spalten und Typen werden vorgeschlagen", type=["csv"])
        if csv is not None and st.session_state.get("csv_marke") != (csv.name, csv.size):
            try:
                vorschlag = spalten_vorschlag(lese_csv(csv.getvalue()))
            except UploadFehler as fehler:
                st.markdown(marke("fehlerhaft", "fehler"), unsafe_allow_html=True)
                for text in fehler.meldungen:
                    st.markdown(f"- {text}")
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
            st.session_state["spalten_df"], key=f"spalten_{nr}", num_rows="dynamic", hide_index=True, width="stretch",
            column_config={
                "name": st.column_config.TextColumn("Name", required=True),
                "typ": st.column_config.SelectboxColumn("Typ", options=TYPEN, required=True),
                "beschreibung": st.column_config.TextColumn("Beschreibung (Bedeutung der Spalte)"),
            },
        )
        spalten = zeilen_aus_tabelle(spalten_df, SPALTEN_FELDER)
        ohne_text = [s["name"] for s in spalten if s["name"] and not s["beschreibung"]]
        if ohne_text:  # Hinweis, keine Pflicht: leere Beschreibungen sind erlaubt
            st.markdown(marke("Hinweis", "hinweis") + f" Ohne Beschreibung: {esc(', '.join(ohne_text))}. Das Artefakt bleibt gültig, aber das Sprachmodell muss dann raten, was diese Spalte(n) bedeuten. Aus den Werten allein lässt sich das nicht zuverlässig ableiten.", unsafe_allow_html=True)

    with st.container(border=True, key="feld_kpis"):
        st.markdown(feldkopf("Kennzahlen (KPIs)", 3), unsafe_allow_html=True)
        namen = [s["name"] for s in spalten if s["name"]]
        st.caption(
            'Beschreiben Sie jede Kennzahl in einem Satz und setzen Sie jeden Spaltennamen in Anführungszeichen, '
            'z. B. Summe von "spalte_a", gruppiert nach "spalte_b". Einfacher: Tippen Sie den Satz und klicken Sie die Spalte '
            'darunter an, der Name wird dann richtig am Ende eingefügt. So prüft das System vorab, ob die Spalten existieren.'
        )
        if not namen:
            st.caption("Die Spalten erscheinen hier zum Anklicken, sobald sie oben (Feld 2) eingetragen sind.")
        for kid in st.session_state["kpi_ids"]:
            spalte_n, spalte_t, spalte_x = st.columns([1.3, 3, 0.7], gap="small", vertical_alignment="bottom")
            spalte_n.text_input("Name der KPI", key=f"kpi_name_{kid}", placeholder="z. B. Tickets je Standort")
            spalte_t.text_input("Berechnung", key=f"kpi_text_{kid}", placeholder='z. B. Anzahl der Tickets je "Spalte"')
            spalte_x.button("Entfernen", key=f"kpi_weg_{kid}", on_click=_entferne_kpi, args=(kid,))
            if namen:
                st.pills("Spalte einfügen", namen, selection_mode="single", key=f"kpi_pill_{kid}",
                         on_change=_fuege_spalte_ein, args=(kid,))
        st.button("KPI hinzufügen", key="kpi_neu", on_click=_neue_kpi)
        kpis = [
            {"name": st.session_state.get(f"kpi_name_{kid}", "").strip(), "beschreibung": st.session_state.get(f"kpi_text_{kid}", "").strip()}
            for kid in st.session_state["kpi_ids"]
        ]
        kpis = [k for k in kpis if k["name"] or k["beschreibung"]]  # ganz leere Zeilen zählen nicht

    with st.container(border=True, key="feld_branding"):
        st.markdown(feldkopf("Branding", 4), unsafe_allow_html=True)
        links, rechts = st.columns(2, gap="medium")
        links.text_input("Firmenname", key="f_firmenname")
        rechts.text_input(
            "Firmenfarben", key="f_farben", placeholder="#1F3864, #ED7D31",
            help="Farbcodes im Format #RRGGBB, durch Komma getrennt. Die erste Farbe ist die Hauptfarbe.",
        )
        logo_datei = st.file_uploader(
            f"Logo (PNG oder JPEG, höchstens {MAX_LOGO_BYTES // (1024 * 1024)} MB)", type=["png", "jpg", "jpeg"]
        )

    felder = {f.removeprefix("f_"): st.session_state[f].strip() for f in TEXTFELDER}
    name_text = felder["name"]
    nichts_eingegeben = not any(felder.values()) and not spalten and not kpis

    meldungen: list[str] = []
    branding, logo, artefakt = None, None, None
    if not nichts_eingegeben:
        try:
            branding, logo = baue_branding(
                st.session_state["f_firmenname"], st.session_state["f_farben"], logo_datei.getvalue() if logo_datei else None
            )
        except BrandingFehler as fehler:
            meldungen.extend(fehler.meldungen)
        try:
            artefakt = artefakt_aus_formular({**felder, "spalten": spalten, "kpis": kpis, "branding": branding.model_dump() if branding else {}})
        except ArtefaktFehler as fehler:
            meldungen.extend(fehler.meldungen)

    # Zustand des Ganzen: leer (offen), fehlerhaft oder gültig. Er steht oben im Schriftfeld und unten im Ergebnisfeld.
    if nichts_eingegeben:
        pruefung = ("noch leer", "offen")
    elif meldungen or artefakt is None:
        pruefung = (f"{len(meldungen)} offen", "fehler")
    else:
        pruefung = ("gültig", "gueltig")
    with kopf:
        st.markdown(_kopf(name_text, len(spalten), len(kpis), pruefung), unsafe_allow_html=True)

    with st.container(border=True, key="feld_ergebnis"):
        st.markdown(feldkopf("Prüfung und Ergebnis", 5), unsafe_allow_html=True)
        if nichts_eingegeben:
            st.markdown(marke("noch leer", "offen"), unsafe_allow_html=True)
            st.markdown("Füllen Sie die Felder aus. Die Prüfung läuft dabei laufend mit. Das Ergebnis erscheint hier, sobald alle Angaben gültig sind.")
            return
        if meldungen or artefakt is None:
            st.markdown(marke(f"{len(meldungen)} Punkt(e) offen", "fehler"), unsafe_allow_html=True)
            for text in meldungen:
                st.markdown(f"- {text}")
            for feld, platz in feld_platz.items():  # dieselben Meldungen zusätzlich direkt unter dem betroffenen Feld
                with platz:
                    for text in meldungen_zu_feld(meldungen, feld):
                        if not text.startswith("Pflichtfeld"):  # "noch leer" nicht rot unter jedes unberührte Feld
                            st.markdown(marke("Fehler", "fehler") + f" {esc(text)}", unsafe_allow_html=True)
            return

        st.markdown(marke("gültig", "gueltig"), unsafe_allow_html=True)
        if artefakt.spalten_ohne_beschreibung:
            st.markdown(
                marke("Hinweis", "hinweis") + f" Ohne Beschreibung: {esc(', '.join(artefakt.spalten_ohne_beschreibung))}. Das Artefakt bleibt gültig, aber das Sprachmodell muss dann raten, was diese Spalte(n) bedeuten. Aus den Werten allein lässt sich das nicht zuverlässig ableiten.",
                unsafe_allow_html=True,
            )
        if branding.farben:
            st.markdown(_farbfelder(branding.farben), unsafe_allow_html=True)
        if logo:
            st.image(logo, width=160)  # Breite statt 96 px: breite Wortmarken sind sonst kaum zu erkennen
            st.caption("So wird das Logo gespeichert (neu erzeugtes PNG).")  # eigene Zeile: in der schmalen Bildspalte brach die Unterschrift in sechs Zeilen um
        st.code(artefakt.zu_yaml(), language="yaml")
        st.download_button("artefakt.yaml herunterladen", data=artefakt.zu_yaml(), file_name="artefakt.yaml", mime="text/yaml")
        ueberschreiben = False
        if artefakt.name in vorhanden:
            ueberschreiben = st.checkbox(f"Vorhandenes Artefakt '{artefakt.name}' überschreiben")
        if st.button(f"In Ordner artefakte/{artefakt.name}/ speichern", type="primary"):
            try:
                ziel = speichere_artefakt_ordner(artefakt, logo, ARTEFAKT_ORDNER, ueberschreiben)
            except ArtefaktFehler as fehler:
                st.markdown(marke("fehlerhaft", "fehler"), unsafe_allow_html=True)
                for text in fehler.meldungen:
                    st.markdown(f"- {text}")
            else:
                st.markdown(marke("übernommen", "uebernommen"), unsafe_allow_html=True)
                st.markdown(f"Gespeichert: `{ziel}`")


if __name__ == "__main__":
    main()
