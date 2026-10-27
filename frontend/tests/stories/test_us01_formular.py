"""Tests zu US-01 (Artefakt per Formular erfassen): TF-001 bis TF-003, plus Typ-Erkennung."""
import pandas as pd
import pytest

from dashboard_framework.eingabe.formular import artefakt_aus_formular, spalten_vorschlag
from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler

FORMULAR = {
    "name": "sales",
    "titel": "Vertriebs-Dashboard",
    "ziel": "Transparenz über Umsatz",
    "publikum": "Vertriebsleitung",
    "tabelle": "absatz",
    "spalten": [{"name": "region", "typ": "text"}, {"name": "umsatz", "typ": "dezimal"}],
    "kpis": [{"name": "Umsatz nach Region", "beschreibung": "Summe von `umsatz`, gruppiert nach `region`."}],
}


def test_formular_erzeugt_gueltiges_artefakt(tmp_path):  # TF-001 / US-01.1
    ziel = tmp_path / "artefakt.yaml"
    artefakt = artefakt_aus_formular(FORMULAR, ziel_pfad=ziel)
    assert artefakt.name == "sales" and len(artefakt.kpis) == 1
    assert Artefakt.aus_yaml(ziel) == artefakt  # die geschriebene Datei ist wieder ladbar und gleich


def test_spaltenvorschlag_aus_hochgeladener_datei():  # TF-002 / US-01.2
    df = pd.DataFrame({
        "datum": pd.to_datetime(["2026-01-05"]), "region": ["Nord"], "menge": [3], "umsatz": [9.5],
    })
    vorschlag = spalten_vorschlag(df)
    assert [(s["name"], s["typ"]) for s in vorschlag] == [
        ("datum", "datum"), ("region", "text"), ("menge", "ganzzahl"), ("umsatz", "dezimal"),
    ]


def test_fehlendes_pflichtfeld_wird_mit_feldname_gemeldet(tmp_path):  # TF-003 / US-01.3
    daten = {k: v for k, v in FORMULAR.items() if k != "ziel"}
    ziel = tmp_path / "artefakt.yaml"
    with pytest.raises(ArtefaktFehler, match="ziel"):
        artefakt_aus_formular(daten, ziel_pfad=ziel)
    assert not ziel.exists()  # keine Datei bei Fehlern


def test_spaltenvorschlag_erkennt_typen_auch_aus_csv_text():
    # So kommen die Daten aus lese_csv: alles ist zunächst Text.
    df = pd.DataFrame({
        "a": ["1", "2"], "b": ["1,5", "2"], "c": ["2026-01-05", "2026-12-31"], "h": ["05.01.2026", "31.12.2026"],
        "d": ["ja", "nein"], "e": ["x", "y"], "f": ["1", "x"], "g": ["", ""],
        "gemischt": ["2026-01-05", "31.12.2026"],  # zwei Datumsformate in einer Spalte: unklar, daher nur Text
    })
    typen = {s["name"]: s["typ"] for s in spalten_vorschlag(df)}
    assert typen == {
        "a": "ganzzahl", "b": "dezimal", "c": "datum", "h": "datum", "d": "bool",
        "e": "text", "f": "text", "g": "text", "gemischt": "text",
    }


def test_spaltenvorschlag_ignoriert_leere_zellen_bei_der_typerkennung():
    df = pd.DataFrame({"zahl": ["1", "", "3"]})
    assert spalten_vorschlag(df)[0]["typ"] == "ganzzahl"


def test_ungueltiger_dateispaltenname_wird_vorgeschlagen_und_dann_von_der_pruefung_gemeldet():
    df = pd.DataFrame({"Umsatz netto": ["1"]})
    vorschlag = spalten_vorschlag(df)
    assert vorschlag[0]["name"] == "Umsatz netto"
    daten = {**FORMULAR, "spalten": vorschlag, "kpis": [{"name": "K", "beschreibung": "`x`"}]}
    with pytest.raises(ArtefaktFehler, match="ungültig"):
        artefakt_aus_formular(daten)
