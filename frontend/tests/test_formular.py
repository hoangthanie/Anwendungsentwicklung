"""Tests zu Tabellen-Umwandlung, Speichern und Laden im Eingabeformular sowie ein Rauchtest der Eingabe-App."""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard_framework.eingabe.formular import speichere_artefakt_ordner, vorhandene_artefakte, zeilen_aus_tabelle
from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler

APP = Path(__file__).resolve().parents[1] / "src" / "dashboard_framework" / "eingabe" / "app.py"
BEISPIEL = Path(__file__).resolve().parents[1] / "artefakte" / "sales" / "artefakt.yaml"


def test_zeilen_aus_tabelle_ersetzt_leere_zellen_und_verwirft_leere_zeilen():
    df = pd.DataFrame({"name": ["a", None, "", " b "], "typ": ["text", None, None, float("nan")]})
    assert zeilen_aus_tabelle(df, ["name", "typ", "beschreibung"]) == [
        {"name": "a", "typ": "text", "beschreibung": ""},
        {"name": "b", "typ": "", "beschreibung": ""},
    ]


def test_speichern_legt_ordner_an_und_schuetzt_vor_ueberschreiben(tmp_path):
    artefakt = Artefakt.aus_yaml(BEISPIEL)
    ziel = speichere_artefakt_ordner(artefakt, b"PNG-BYTES", tmp_path)
    assert ziel == (tmp_path / "sales").resolve()
    assert (ziel / "logo.png").read_bytes() == b"PNG-BYTES"
    assert Artefakt.aus_yaml(ziel / "artefakt.yaml") == artefakt
    with pytest.raises(ArtefaktFehler, match="schon ein Artefakt"):
        speichere_artefakt_ordner(artefakt, None, tmp_path)
    speichere_artefakt_ordner(artefakt, None, tmp_path, ueberschreiben=True)


def test_speichern_verlaesst_den_artefakt_ordner_nie(tmp_path):
    artefakt = Artefakt.aus_yaml(BEISPIEL).model_copy(update={"name": ".."})  # umgeht die Namensprüfung absichtlich
    with pytest.raises(ArtefaktFehler, match="außerhalb"):
        speichere_artefakt_ordner(artefakt, None, tmp_path / "artefakte")
    assert not (tmp_path / "artefakt.yaml").exists()


def test_vorhandene_artefakte(tmp_path):
    assert vorhandene_artefakte(tmp_path / "gibts_nicht") == []
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "artefakt.yaml").write_text("x")
    (tmp_path / "a").mkdir()  # ohne artefakt.yaml: zählt nicht
    assert vorhandene_artefakte(tmp_path) == ["b"]


def test_eingabe_app_startet_und_wartet_auf_eingaben():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    texte = " ".join(m.value for m in app.markdown)
    assert "Füllen Sie die Felder" in texte and "noch leer" in texte


def test_eingabe_app_meldet_fehler_sofort():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.session_state["f_name"] = "Falscher Name!"
    app.run()
    assert not app.exception
    texte = " ".join(m.value for m in app.markdown)
    assert "name:" in texte and "Pflichtfeld" in texte


def test_meldungen_zu_feld_ordnet_meldungen_dem_feld_zu():
    from dashboard_framework.eingabe.formular import meldungen_zu_feld

    meldungen = [
        "tabelle: erlaubt sind Buchstaben, Ziffern und _",
        "Pflichtfeld ist leer: ziel",
        "KPI 'A': unbekannte Spalte: x",
        "name: erlaubt sind Kleinbuchstaben",
    ]
    assert meldungen_zu_feld(meldungen, "tabelle") == [meldungen[0]]
    assert meldungen_zu_feld(meldungen, "ziel") == [meldungen[1]]
    assert meldungen_zu_feld(meldungen, "name") == [meldungen[3]]
    assert meldungen_zu_feld(meldungen, "titel") == []


def test_fuege_spalte_ein_haengt_am_ende_an_und_laesst_zum_weitertippen_platz():
    from dashboard_framework.eingabe.formular import fuege_spalte_ein

    assert fuege_spalte_ein("", "Location") == '"Location" '
    assert fuege_spalte_ein("Anzahl der Tickets je", "Location") == 'Anzahl der Tickets je "Location" '
    assert fuege_spalte_ein('Anzahl je "State" ', "Created") == 'Anzahl je "State" "Created" '  # kein doppeltes Leerzeichen


def test_eingabe_app_kpi_felder_und_geladene_kpis_erscheinen_mit_anfuehrungszeichen():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    # vollständig und strukturell gültig, nur die KPI nennt eine Spalte, die es nicht gibt (die Spaltenprüfung läuft erst nach der Strukturprüfung)
    for feld, wert in {"f_name": "t", "f_titel": "T", "f_ziel": "Z", "f_publikum": "P", "f_tabelle": "tab"}.items():
        app.session_state[feld] = wert
    app.session_state["spalten_df"] = pd.DataFrame([{"name": "vorhanden", "typ": "text", "beschreibung": ""}])
    app.session_state["kpi_name_0"] = "Test"
    app.session_state["kpi_text_0"] = 'Anzahl je "Gibts_nicht"'
    app.run()
    assert not app.exception
    texte = " ".join(m.value for m in app.markdown)
    assert "unbekannte Spalte: Gibts_nicht" in texte  # Anführungszeichen werden als Spaltenverweis geprüft


def test_eingabe_app_gueltiges_artefakt_mit_leeren_beschreibungen_zeigt_hinweis_statt_fehler():
    """Regression: Ergebnisfeld läuft durch (kein AttributeError) und zeigt einen Hinweis, das Artefakt bleibt gültig."""
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    for feld, wert in {"f_name": "t", "f_titel": "T", "f_ziel": "Z", "f_publikum": "P", "f_tabelle": "tab"}.items():
        app.session_state[feld] = wert
    app.session_state["spalten_df"] = pd.DataFrame([{"name": "a", "typ": "text", "beschreibung": ""}])
    app.session_state["kpi_name_0"] = "K"
    app.session_state["kpi_text_0"] = 'Anzahl je "a"'
    app.run()
    assert not app.exception
    texte = " ".join(m.value for m in app.markdown)
    assert "marke-gueltig" in texte and "Ohne Beschreibung: a" in texte and "raten" in texte


def test_ziel_kpi_ist_die_zuletzt_geaenderte():
    from dashboard_framework.eingabe.formular import finde_geaenderte_kpi, waehle_ziel_kpi

    ids = [0, 1, 2]
    vorher = {0: "Anzahl", 1: "Summe", 2: ""}
    jetzt = {0: "Anzahl", 1: "Summe je", 2: ""}  # in KPI 1 wurde getippt
    assert finde_geaenderte_kpi(ids, jetzt, vorher) == 1
    assert waehle_ziel_kpi(ids, jetzt, vorher, zuletzt=0) == 1  # Änderung schlägt "zuletzt benutzt"
    assert finde_geaenderte_kpi(ids, vorher, vorher) is None


def test_ziel_kpi_ohne_aenderung_zuletzt_benutzte_sonst_erste_leere_sonst_letzte():
    from dashboard_framework.eingabe.formular import waehle_ziel_kpi

    ids = [3, 4, 5]
    gleich = {3: "a", 4: "b", 5: "c"}
    assert waehle_ziel_kpi(ids, gleich, gleich, zuletzt=4) == 4
    assert waehle_ziel_kpi(ids, gleich, gleich, zuletzt=99) == 5  # unbekannt, keine leere -> letzte
    mit_leerer = {3: "a", 4: "", 5: "c"}
    assert waehle_ziel_kpi(ids, mit_leerer, mit_leerer, zuletzt=None) == 4  # erste leere Zeile
    assert waehle_ziel_kpi(ids, gleich, {}, zuletzt=3) == 3  # kein Vergleichsstand (z. B. nach dem Laden): kein falscher Treffer


def test_neue_kpi_zeile_wird_nicht_als_aenderung_gewertet_solange_sie_nicht_im_vergleichsstand_ist():
    from dashboard_framework.eingabe.formular import finde_geaenderte_kpi

    assert finde_geaenderte_kpi([0, 1], {0: "x", 1: "y"}, {0: "x"}) is None
