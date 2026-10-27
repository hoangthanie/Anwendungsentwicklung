"""Tests zum Gestaltungssystem: Kontrast, sichere HTML-Bausteine, CSS, Schriftdateien, Kopfdaten."""
import hashlib
import tomllib
from pathlib import Path

import pytest

from dashboard_framework.models.spalten import SpaltenDef
from dashboard_framework.runner.daten import Kopfdaten, formatiere_datum, lade_kopfdaten
from dashboard_framework.ui.komponenten import esc, feldkopf, fussleiste, kennzahl, marke, schriftfeld, zahl
from dashboard_framework.ui.theme import (
    BLATT,
    LINIE_STARK,
    PRODUKT_AKZENT,
    TINTE,
    TINTE_2,
    ZUSTAENDE,
    akzent_als_text,
    akzent_pruefen,
    baue_css,
    kontrast,
    text_auf_akzent,
)

WURZEL = Path(__file__).resolve().parents[1]
RUNNER_STATIC = WURZEL / "src" / "dashboard_framework" / "runner" / "static"
EINGABE_STATIC = WURZEL / "src" / "dashboard_framework" / "eingabe" / "static"


def test_kontrast_bekannte_werte():
    assert kontrast("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert kontrast("#FFFFFF", "#FFFFFF") == pytest.approx(1.0)


def test_gestaltungswerte_erfuellen_wcag_kontrast():
    assert kontrast(TINTE, BLATT) >= 7
    assert kontrast(TINTE_2, BLATT) >= 4.5
    assert kontrast(LINIE_STARK, BLATT) >= 3  # Rand von Bedienelementen
    assert kontrast(PRODUKT_AKZENT, BLATT) >= 4.5
    for art, (text, grund) in ZUSTAENDE.items():
        assert kontrast(text, grund) >= 4.5, f"Zustand {art}: Text auf Hintergrund zu schwach"


def test_helle_kundenfarbe_wird_nie_als_text_verwendet():
    gelb = "#FFD600"
    assert akzent_als_text(gelb) == TINTE  # zu hell für Text auf Weiß
    assert text_auf_akzent(gelb) == TINTE  # auf Gelb liest man dunkle Schrift
    marine = "#1F3864"
    assert akzent_als_text(marine) == marine
    assert text_auf_akzent(marine) == BLATT


def test_akzent_pruefen_faellt_auf_die_produktfarbe_zurueck():
    assert akzent_pruefen("#1f3864") == "#1F3864"
    for ungueltig in [None, "", "blau", "#12345", "red; } body { display:none"]:
        assert akzent_pruefen(ungueltig) == PRODUKT_AKZENT


def test_css_enthaelt_nur_geprueften_akzent():
    css = baue_css("#ED7D31")
    assert "--akzent:#ED7D31" in css
    boese = baue_css("red; } body { display:none")
    assert "red;" not in boese and "body { display:none" not in boese  # das eingeschleuste Stück kommt nirgends vor
    assert f"--akzent:{PRODUKT_AKZENT}" in boese  # stattdessen gilt die Produktfarbe


def test_css_themt_die_browserflaechen():
    css = baue_css()
    for baustein in ["::selection", "caret-color", ":focus-visible", "scrollbar-color"]:
        assert baustein in css


def test_schriftfeld_maskiert_fremde_texte():
    html = schriftfeld('<script>alert(1)</script>', [("Kunde", '<img src=x onerror=alert(1)>')])
    assert "<script>" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html


def test_schriftfeld_ist_eine_einzige_zeile_ohne_einrueckung():
    html = schriftfeld("Titel", [("A", "1"), ("B", "2", "gueltig")])
    assert "\n" not in html  # Streamlit liest Markdown: Zeilenumbrüche mit Einrückung würden zum Codeblock
    assert "sf-n3" in html and "marke-gueltig" in html


def test_logo_nur_als_data_uri_von_png_oder_jpeg():
    ok = "data:image/png;base64,iVBORw0KGgo="
    assert ok in schriftfeld("T", [], logo_uri=ok)
    for boese in ["https://example.com/x.png", 'data:image/png;base64,AAA" onerror="x', "javascript:alert(1)", "data:image/svg+xml;base64,AAAA"]:
        with pytest.raises(ValueError):
            schriftfeld("T", [], logo_uri=boese)


def test_zu_viele_zellen_und_unbekannte_zustandsart():
    with pytest.raises(ValueError):
        schriftfeld("T", [("a", "b")] * 8)
    with pytest.raises(ValueError):
        marke("x", "knallbunt")


def test_marke_traegt_text_und_art():
    assert marke("gültig", "gueltig") == '<span class="marke marke-gueltig">gültig</span>'


def test_feldkopf_fussleiste_kennzahl():
    assert 'class="fb-nr">3<' in feldkopf("Titel", 3)
    assert "fb-nr" not in feldkopf("Titel")
    assert "&amp;" in fussleiste([("Darstellung", "A & B")])
    assert "103,2" in kennzahl("103,2")


def test_zahl_und_esc():
    assert zahl(1234567) == "1.234.567" and zahl(192) == "192"
    assert esc('"<&>') == "&quot;&lt;&amp;&gt;"


def test_schriftdateien_in_beiden_apps_gleich_und_in_der_config_eingetragen():
    config = tomllib.loads((WURZEL / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    dateien = [Path(f["url"]).name for f in config["theme"]["fontFaces"]]
    assert len(dateien) == 6
    for name in dateien:
        runner, eingabe = RUNNER_STATIC / name, EINGABE_STATIC / name
        assert runner.exists() and eingabe.exists(), f"{name} fehlt in runner/static oder eingabe/static"
        assert hashlib.sha256(runner.read_bytes()).digest() == hashlib.sha256(eingabe.read_bytes()).digest()
    assert (RUNNER_STATIC / "LIZENZ-Barlow.txt").exists() and (EINGABE_STATIC / "LIZENZ-Barlow.txt").exists()


def test_formatiere_datum():
    assert formatiere_datum("2026-12-31") == "31.12.2026"
    assert formatiere_datum("2026-12-31 10:00:00") == "31.12.2026 10:00"
    assert formatiere_datum("kein Datum") == "kein Datum"
    assert formatiere_datum(None) is None and formatiere_datum("  ") is None


def test_kopfdaten_aus_der_datenbank(config_region, test_db):
    config = config_region.model_copy(update={"spalten": [SpaltenDef(name="datum", typ="datum")]})
    assert lade_kopfdaten(config, test_db) == Kopfdaten(zeilen=4, stand="15.02.2026")


def test_kopfdaten_ohne_datumsspalte_oder_tabelle(config_region, test_db):
    assert lade_kopfdaten(config_region, test_db) == Kopfdaten(zeilen=4, stand=None)
    fremd = config_region.model_copy(update={"tabelle": "gibt_es_nicht"})
    assert lade_kopfdaten(fremd, test_db) == Kopfdaten(zeilen=None, stand=None)


def test_kopfdaten_tabellenname_wird_nicht_als_sql_ausgefuehrt(config_region, test_db):
    boese = config_region.model_copy(update={"tabelle": 'absatz"; DROP TABLE absatz; --'})
    assert lade_kopfdaten(boese, test_db).zeilen is None
    assert lade_kopfdaten(config_region, test_db).zeilen == 4


def test_fussleiste_breite_erste_zelle():
    assert 'class="breit"' in fussleiste([("Berechnung", "Summe von x"), ("Ergebnis", "4 Zeilen")], breit_erste=True)
    assert "breit" not in fussleiste([("Ergebnis", "4 Zeilen")])


def test_css_haarlinie_unter_den_tabs_und_hauptaktion_rechts():
    css = baue_css()
    assert '[role="tablist"]::after{height:1px' in css  # Streamlits 2px-Linie wird zur Haarlinie
    assert "align-self:flex-end" in css and "st-key-feld_upload_uebernahme" in css
    assert "max-width:760px" in css  # Tabs auf schmalen Bildschirmen enger


def test_formatiere_vorschau_deutsche_schreibweise():
    import pandas as pd

    from dashboard_framework.models.spalten import SpaltenDef
    from dashboard_framework.runner.daten import formatiere_vorschau

    spalten = [SpaltenDef(name="d", typ="datum"), SpaltenDef(name="z", typ="dezimal"), SpaltenDef(name="n", typ="ganzzahl"),
               SpaltenDef(name="b", typ="bool"), SpaltenDef(name="t", typ="text")]
    df = pd.DataFrame({"d": ["2026-12-15"], "z": [12000.5], "n": [1234567], "b": [1], "t": ["Nord"]})
    zeile = formatiere_vorschau(df, spalten).iloc[0].tolist()
    assert zeile == ["15.12.2026", "12.000,50", "1.234.567", "ja", "Nord"]
    assert df.iloc[0]["d"] == "2026-12-15"  # das Original bleibt unverändert (gespeichert wird ISO)


def test_formatiere_datum_mit_uhrzeit():
    assert formatiere_datum("2026-10-27 11:20:10") == "27.10.2026 11:20"
