"""Eingabe-App (Streamlit). Aktueller Stand: Abschnitt Branding (PSP 6.2). Ziel, Publikum, Spalten und KPIs folgen mit PSP 6.1.

Start:  streamlit run src/dashboard_framework/eingabe/app.py
"""
from __future__ import annotations

import streamlit as st

from dashboard_framework.eingabe.branding_form import baue_branding
from dashboard_framework.runner.branding import BrandingFehler, MAX_LOGO_BYTES

STANDARD_FARBEN = "#1F3864, #ED7D31, #70AD47"


def _farbfelder(farben: list[str]) -> str:
    # Die Codes sind bereits als #RRGGBB geprüft (normalisiere_farben), daher unkritisch im HTML.
    felder = "".join(
        f'<span style="display:inline-block;width:56px;height:56px;margin-right:8px;border-radius:8px;background:{f};'
        f'border:1px solid #8884" title="{f}"></span>'
        for f in farben
    )
    return f"<div>{felder}</div>"


def main() -> None:
    st.set_page_config(page_title="Dashboard-Eingabe", layout="centered")
    st.title("Dashboard-Eingabe")
    st.caption("Entwurf: bisher nur der Abschnitt Branding. Ziel, Publikum, Spalten und KPIs folgen (PSP 6.1).")

    st.header("Branding")
    firmenname = st.text_input("Firmenname", value="Muster GmbH", max_chars=120)
    farben_text = st.text_input(
        "Firmenfarben", value=STANDARD_FARBEN,
        help="Farbcodes im Format #RRGGBB, getrennt durch Komma. Die erste Farbe ist die Hauptfarbe des Dashboards.",
    )
    logo_datei = st.file_uploader(
        f"Logo (PNG oder JPEG, höchstens {MAX_LOGO_BYTES // (1024 * 1024)} MB)", type=["png", "jpg", "jpeg"]
    )

    try:
        branding, logo = baue_branding(firmenname, farben_text, logo_datei.getvalue() if logo_datei else None)
    except BrandingFehler as fehler:
        st.error("Das Branding kann so nicht übernommen werden:")
        for text in fehler.meldungen:
            st.markdown(f"- {text}")
        return

    st.subheader("Vorschau")
    if branding.farben:
        st.markdown(_farbfelder(branding.farben), unsafe_allow_html=True)
    if logo:
        st.image(logo, width=120, caption="So wird das Logo gespeichert (neu erzeugtes PNG)")
    st.json(branding.model_dump())


if __name__ == "__main__":
    main()
