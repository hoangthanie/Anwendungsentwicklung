"""Tests zum Artefakt-Modell (PSP 3.3): TF-004, TF-005, TF-007, TF-042 sowie gültige und ungültige Beispiele."""
import copy
from pathlib import Path

import pytest

from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler

ARTEFAKTE = Path(__file__).resolve().parents[1] / "artefakte"

GUELTIG = {
    "name": "sales",
    "titel": "Vertriebs-Dashboard",
    "ziel": "Transparenz über Umsatz",
    "publikum": "Vertriebsleitung",
    "tabelle": "absatz",
    "spalten": [
        {"name": "region", "typ": "text"},
        {"name": "umsatz", "typ": "dezimal"},
        {"name": "datum", "typ": "datum"},
    ],
    "kpis": [{"name": "Umsatz nach Region", "beschreibung": "Summe von `umsatz`, gruppiert nach `region`."}],
    "branding": {"firmenname": "Muster GmbH", "farben": ["#1F3864"]},
}


def mit(**aenderungen):
    daten = copy.deepcopy(GUELTIG)
    daten.update(aenderungen)
    return daten


def meldungen(daten) -> str:
    with pytest.raises(ArtefaktFehler) as fehler:
        Artefakt.aus_dict(daten)
    return " | ".join(fehler.value.meldungen)


def test_leere_spaltenbeschreibung_ist_ein_hinweis_kein_fehler():
    ohne = Artefakt.aus_dict(mit(spalten=[{"name": "region", "typ": "text"}, {"name": "umsatz", "typ": "dezimal", "beschreibung": "Euro"}]))
    assert ohne.spalten_ohne_beschreibung == ["region"]  # gültig, aber als Hinweis auffindbar
    mit_text = Artefakt.aus_dict(mit(spalten=[{"name": "region", "typ": "text", "beschreibung": "Vertriebsregion"}, {"name": "umsatz", "typ": "dezimal", "beschreibung": " "}]))
    assert mit_text.spalten_ohne_beschreibung == ["umsatz"]  # nur Leerzeichen zählt als leer


def test_gueltiges_artefakt():
    artefakt = Artefakt.aus_dict(GUELTIG)
    assert artefakt.benoetigte_spalten == ["umsatz", "region"]


def test_unbekannte_spalte_wird_abgelehnt():  # TF-004 / US-02.1
    daten = mit(spalten=[{"name": "Region", "typ": "text"}, {"name": "umsatz", "typ": "dezimal"}])
    assert "unbekannte Spalte: region" in meldungen(daten)


def test_kpi_ohne_spaltenanker_wird_abgelehnt():  # TF-005 / US-02.2
    daten = mit(kpis=[{"name": "Gesamt", "beschreibung": "Der gesamte Umsatz des Jahres"}])
    assert "referenziert keine Spalte – bitte Spaltennamen in Anführungszeichen" in meldungen(daten)


def test_ungueltige_farbe_wird_abgelehnt():  # TF-007 / US-03.1
    assert "Ungültige Farbcodes" in meldungen(mit(branding={"firmenname": "X", "farben": ["blau"]}))


def test_alle_artefakte_im_repo_sind_gueltig():  # TF-042 / US-12.2
    dateien = sorted(ARTEFAKTE.glob("*/artefakt.yaml"))
    assert len(dateien) >= 2
    for datei in dateien:
        assert Artefakt.aus_yaml(datei).name == datei.parent.name


def test_aehnliche_spalte_steht_in_der_meldung():  # US-02.3
    daten = mit(spalten=[{"name": "Region", "typ": "text"}, {"name": "umsatz", "typ": "dezimal"}])
    assert "meinten Sie `Region`" in meldungen(daten)


def test_alle_fehler_gemeinsam():
    daten = mit(
        ziel="",
        kpis=[
            {"name": "A", "beschreibung": "ohne Anker"},
            {"name": "B", "beschreibung": "Summe von `gibtsnicht`"},
        ],
    )
    # Struktur-Fehler (leeres Ziel) werden zuerst gemeldet; Zusammenhangsfehler folgen, sobald die Struktur stimmt.
    assert "Pflichtfeld ist leer: ziel" in meldungen(daten)
    ok = mit(kpis=daten["kpis"])
    text = meldungen(ok)
    assert "KPI 'A' referenziert keine Spalte" in text and "KPI 'B': unbekannte Spalte: gibtsnicht" in text


def test_pflichtfelder_fehlen():
    daten = copy.deepcopy(GUELTIG)
    del daten["ziel"], daten["publikum"]
    text = meldungen(daten)
    assert "Pflichtfeld fehlt: ziel" in text and "Pflichtfeld fehlt: publikum" in text


@pytest.mark.parametrize("name", ["Sales", "mit leerzeichen", "../hack", "1abc", "a" * 41, "sales/x", ""])
def test_ungueltige_namen_werden_abgelehnt(name):
    meldungen(mit(name=name))


@pytest.mark.parametrize("tabelle", ["absatz; DROP TABLE x", "mit leerzeichen", '"x"', "1x", "a-b"])
def test_ungueltige_tabellennamen_werden_abgelehnt(tabelle):
    assert "tabelle:" in meldungen(mit(tabelle=tabelle))


def test_spaltenname_mit_leerzeichen_wird_abgelehnt_mit_hinweis():
    assert "in der Datendatei" in meldungen(mit(spalten=[{"name": "Umsatz netto", "typ": "dezimal"}]))


def test_doppelte_spalten_auch_bei_anderer_schreibweise():
    daten = mit(spalten=[{"name": "region", "typ": "text"}, {"name": "Region", "typ": "text"}])
    assert "doppelt" in meldungen(daten)


def test_doppelte_kpi_namen():
    kpi = {"name": "A", "beschreibung": "Summe von `umsatz`"}
    assert "KPI 'A' kommt doppelt vor" in meldungen(mit(kpis=[kpi, kpi]))


def test_unbekannter_typ_und_unbekanntes_feld():
    assert "ungültiger Wert 'zahl'" in meldungen(mit(spalten=[{"name": "umsatz", "typ": "zahl"}]))
    assert "Unbekanntes Feld: kpi" in meldungen({**GUELTIG, "kpi": []})


def test_mindestens_eine_spalte_und_ein_kpi_und_begrenzung():
    assert "mindestens 1 Eintrag" in meldungen(mit(spalten=[]))
    assert "mindestens 1 Eintrag" in meldungen(mit(kpis=[]))
    viele = [{"name": f"K{i}", "beschreibung": "`umsatz`"} for i in range(13)]
    assert "höchstens 12 Einträge" in meldungen(mit(kpis=viele))


def test_nur_leerzeichen_zaehlt_als_leer():
    assert "Pflichtfeld ist leer: ziel" in meldungen(mit(ziel="   "))


def test_yaml_roundtrip(tmp_path):
    artefakt = Artefakt.aus_dict(GUELTIG)
    ziel = tmp_path / "a" / "artefakt.yaml"
    artefakt.speichern(ziel)
    assert Artefakt.aus_yaml(ziel) == artefakt


def test_yaml_fehler_sind_verstaendlich(tmp_path):
    kaputt = tmp_path / "k.yaml"
    kaputt.write_text("name: [unvollstaendig\n", encoding="utf-8")
    with pytest.raises(ArtefaktFehler, match="kein gültiges YAML"):
        Artefakt.aus_yaml(kaputt)
    liste = tmp_path / "l.yaml"
    liste.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ArtefaktFehler, match="aus Feldern"):
        Artefakt.aus_yaml(liste)
    with pytest.raises(ArtefaktFehler, match="nicht gefunden"):
        Artefakt.aus_yaml(tmp_path / "gibt_es_nicht.yaml")


def test_yaml_kann_keine_python_objekte_erzeugen(tmp_path):
    boese = tmp_path / "b.yaml"
    boese.write_text("name: !!python/object/apply:os.system ['echo gefaehrlich']\n", encoding="utf-8")
    with pytest.raises(ArtefaktFehler):
        Artefakt.aus_yaml(boese)


def test_zu_grosse_yaml_wird_abgelehnt(tmp_path):
    gross = tmp_path / "g.yaml"
    gross.write_text("a: " + "x" * (1024 * 1024 + 1), encoding="utf-8")
    with pytest.raises(ArtefaktFehler, match="größer als 1 MB"):
        Artefakt.aus_yaml(gross)


@pytest.mark.parametrize("feld", ["name", "tabelle"])
def test_leeres_name_oder_tabellenfeld_wird_wie_ein_leeres_pflichtfeld_gemeldet(feld):
    assert f"Pflichtfeld ist leer: {feld}" in meldungen(mit(**{feld: ""}))


# --- Anführungszeichen statt Backticks (Anwender tippen "Name", gespeichert wird `Name`) ---

def kpi(text):
    return mit(kpis=[{"name": "K", "beschreibung": text}])


@pytest.mark.parametrize("text", [
    'Summe von "umsatz", gruppiert nach "region".',
    "Summe von „umsatz“, gruppiert nach „region“.",
    "Summe von \u201cumsatz\u201d, gruppiert nach \u201cregion\u201d.",
    "Summe von `umsatz`, gruppiert nach `region`.",
    'Summe von "umsatz", gruppiert nach `region`.',
])
def test_anfuehrungszeichen_und_backticks_sind_gleichwertig(text):
    artefakt = Artefakt.aus_dict(kpi(text))
    assert artefakt.kpis[0].referenzierte_spalten == ["umsatz", "region"]
    assert "`umsatz`" in artefakt.kpis[0].beschreibung and '"' not in artefakt.kpis[0].beschreibung  # gespeichert wird mit Backticks


def test_yaml_enthaelt_backticks_auch_wenn_mit_anfuehrungszeichen_getippt(tmp_path):
    artefakt = Artefakt.aus_dict(kpi('Summe von "umsatz"'))
    ziel = tmp_path / "a.yaml"
    artefakt.speichern(ziel)
    assert "`umsatz`" in ziel.read_text(encoding="utf-8")  # Vertrag mit der Pipeline bleibt unverändert


def test_unbekannte_spalte_in_anfuehrungszeichen_wird_gemeldet():
    text = meldungen(kpi('Anzahl je "location"'))
    assert "unbekannte Spalte: location" in text


@pytest.mark.parametrize("text", [
    'Zeit zwischen "umsatz" und "region in Stunden',  # schließendes Zeichen fehlt
    'Zeit zwischen "umsatz und region" in Stunden "',  # ein Zeichen zu viel
    "Zeit zwischen `umsatz` und `region in Stunden",  # auch bei Backticks
])
def test_nicht_gepaarte_anfuehrungszeichen_werden_gemeldet_statt_still_uebersehen(text):
    assert "Anführungszeichen nicht paarig" in meldungen(kpi(text))


def test_backticks_zu_anfuehrungszeichen_fuer_die_anzeige():
    from dashboard_framework.models.artefakt import backticks_zu_anfuehrungszeichen

    assert backticks_zu_anfuehrungszeichen("Summe von `umsatz` je `region`") == 'Summe von "umsatz" je "region"'
