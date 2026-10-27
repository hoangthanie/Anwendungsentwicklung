"""Fachlogik des Eingabeformulars (ohne Streamlit, damit testbar): Formulardaten -> geprüftes Artefakt, Spaltenvorschlag aus einer Datei."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler
from dashboard_framework.runner.branding import LOGO_DATEINAME
from dashboard_framework.runner.framework_lib import konvertiere_spalte

# Reihenfolge ist wichtig: spezifische Typen zuerst. "7" soll ganzzahl sein, nicht dezimal oder bool.
_TYPEN_DER_REIHE_NACH = ("ganzzahl", "dezimal", "datum", "bool")


def artefakt_aus_formular(daten: dict, ziel_pfad: str | Path | None = None) -> Artefakt:
    """Prüft die Formulardaten und liefert das Artefakt. Bei Fehlern gibt es eine ArtefaktFehler mit ALLEN Meldungen.

    Nur wenn alles gültig ist UND ein ziel_pfad angegeben wurde, wird die artefakt.yaml geschrieben
    (bei Fehlern entsteht nie eine halbfertige Datei).
    """
    artefakt = Artefakt.aus_dict(daten)
    if ziel_pfad is not None:
        artefakt.speichern(ziel_pfad)
    return artefakt


def zeilen_aus_tabelle(df: pd.DataFrame, felder: list[str]) -> list[dict]:
    """Wandelt eine im Formular bearbeitete Tabelle in Dicts um: leere Zellen (NaN/None) werden zu '', komplett leere Zeilen entfallen."""
    zeilen = []
    for _, zeile in df.iterrows():
        werte = {f: ("" if f not in zeile or pd.isna(zeile[f]) else str(zeile[f]).strip()) for f in felder}
        if any(werte.values()):
            zeilen.append(werte)
    return zeilen


def vorhandene_artefakte(basis: str | Path) -> list[str]:
    """Namen der Unterordner von 'basis', die eine artefakt.yaml enthalten."""
    ordner = Path(basis)
    if not ordner.is_dir():
        return []
    return sorted(p.parent.name for p in ordner.glob("*/artefakt.yaml"))


def speichere_artefakt_ordner(artefakt: Artefakt, logo: bytes | None, basis: str | Path, ueberschreiben: bool = False) -> Path:
    """Schreibt artefakt.yaml (und logo.png) nach <basis>/<artefakt.name>/ und gibt den Ordner zurück.

    Ein vorhandenes Artefakt wird nur mit ausdrücklicher Erlaubnis überschrieben. Der Ordnername kommt vom (geprüften) Namen; zusätzlich wird
    kontrolliert, dass das Ziel wirklich innerhalb von 'basis' liegt.
    """
    wurzel = Path(basis).resolve()
    ziel = (wurzel / artefakt.name).resolve()
    if not ziel.is_relative_to(wurzel) or ziel == wurzel:
        raise ArtefaktFehler("Der Zielordner liegt außerhalb des Artefakt-Ordners")
    if (ziel / "artefakt.yaml").exists() and not ueberschreiben:
        raise ArtefaktFehler(f"Es gibt schon ein Artefakt '{artefakt.name}'. Zum Ersetzen bitte das Überschreiben bestätigen")
    artefakt.speichern(ziel / "artefakt.yaml")
    if logo:
        (ziel / LOGO_DATEINAME).write_bytes(logo)
    return ziel


def _typ_fuer(serie: pd.Series) -> str:
    dtype = serie.dtype
    if pd.api.types.is_bool_dtype(dtype):
        return "bool"
    if pd.api.types.is_integer_dtype(dtype):
        return "ganzzahl"
    if pd.api.types.is_float_dtype(dtype):
        return "dezimal"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "datum"
    werte = serie.dropna().astype(str).str.strip()
    werte = werte[werte != ""]
    if werte.empty:
        return "text"
    for typ in _TYPEN_DER_REIHE_NACH:
        try:
            konvertiere_spalte(werte, typ)
            return typ
        except (ValueError, TypeError):
            continue
    return "text"


def spalten_vorschlag(df: pd.DataFrame) -> list[dict]:
    """Schlägt für jede Spalte der Datei Name und Typ vor (Reihenfolge wie in der Datei), als Liste von {name, typ, beschreibung}.

    Es ist nur ein Vorschlag: Die Bedeutung einer Spalte (Beschreibung) kann man aus den Werten nicht zuverlässig ableiten und bleibt Pflicht des Anwenders.
    Namen werden unverändert übernommen. Ungültige Namen (z. B. mit Leerzeichen) meldet erst die Prüfung des Artefakts, mit Hinweis.
    """
    return [{"name": str(name), "typ": _typ_fuer(df[name]), "beschreibung": ""} for name in df.columns]
