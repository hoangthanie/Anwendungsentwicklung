"""Fachlogik des Branding-Abschnitts der Eingabe-App (ohne Streamlit, damit testbar)."""
from __future__ import annotations

import re

from dashboard_framework.models.dashboard_config import Branding
from dashboard_framework.runner.branding import (
    LOGO_DATEINAME,
    BrandingFehler,
    bereinige_logo,
    normalisiere_farben,
)

MAX_FIRMENNAME = 80


def farben_aus_text(text: str) -> list[str]:
    """Zerlegt eine Eingabe wie '#1F3864, #ED7D31 #70AD47' in einzelne Farbangaben (Trenner: Komma, Semikolon, Leerzeichen)."""
    return [teil for teil in re.split(r"[,;\s]+", text) if teil]


def baue_branding(firmenname: str, farben_text: str, logo_inhalt: bytes | None) -> tuple[Branding, bytes | None]:
    """Prüft alle Branding-Eingaben und liefert das Branding-Modell plus das bereinigte Logo (PNG-Bytes) oder None.

    Alle Fehler werden gesammelt und gemeinsam gemeldet (BrandingFehler), nicht nur der erste.
    """
    meldungen: list[str] = []
    name = firmenname.strip()
    if len(name) > MAX_FIRMENNAME:
        meldungen.append(f"Der Firmenname ist zu lang (höchstens {MAX_FIRMENNAME} Zeichen)")

    farben: list[str] = []
    try:
        farben = normalisiere_farben(farben_aus_text(farben_text))
    except BrandingFehler as fehler:
        meldungen.extend(fehler.meldungen)

    logo: bytes | None = None
    if logo_inhalt:
        try:
            logo = bereinige_logo(logo_inhalt)
        except BrandingFehler as fehler:
            meldungen.extend(fehler.meldungen)

    if meldungen:
        raise BrandingFehler(meldungen)
    return Branding(firmenname=name, farben=farben, logo=LOGO_DATEINAME if logo else None), logo
