"""Tests für Schritt 1 (PSP 5.3): Akzeptanzkriterien aus docs/stories/US-04 sowie Laden der CSV (Spezifikation 3.1)."""

import sqlite3

import pytest
from dashboard_framework.models.artefakt import Artefakt

from pipeline.schritte.schritt1_datenmodell import (
    SchemaFehler,
    SpaltenInfo,
    abgleich,
    ausfuehren,
    lade_daten,
    lese_schema,
)


@pytest.fixture
def artefakt():
    return Artefakt.aus_dict({
        "name": "sales",
        "titel": "Test",
        "ziel": "Umsatz verstehen",
        "publikum": "Vertrieb",
        "tabelle": "absatz",
        "spalten": [
            {"name": "datum", "typ": "datum"},
            {"name": "region", "typ": "text"},
            {"name": "menge", "typ": "ganzzahl"},
            {"name": "umsatz", "typ": "dezimal"},
        ],
        "kpis": [{"name": "Umsatz nach Region", "beschreibung": "Summe von `umsatz` je `region`"}],
    })


@pytest.fixture
def csv(tmp_path):
    pfad = tmp_path / "daten.csv"
    pfad.write_text(
        "datum;region;menge;umsatz\n"
        "15.01.2026;Nord;10;100,5\n"
        "16.01.2026;Süd;7;70\n"
        "17.01.2026;Nord;5;50\n"
        "18.01.2026;Ost;3;30\n"
        "19.01.2026;West;1;10\n",
        encoding="utf-8",
    )
    return pfad


@pytest.fixture
def db(tmp_path, artefakt, csv):
    pfad = tmp_path / "daten.db"
    lade_daten(artefakt, csv, pfad)
    return pfad


# --- US-04.1 Schema aus der DB lesen ------------------------------------------------------------


def test_schema_wird_aus_db_gelesen(db):
    schema = lese_schema(db, "absatz")
    assert [(s.name, s.typ) for s in schema] == [
        ("datum", "TEXT"),
        ("region", "TEXT"),
        ("menge", "INTEGER"),
        ("umsatz", "REAL"),
    ]


def test_fehlende_tabelle_wird_verstaendlich_gemeldet(db):
    with pytest.raises(SchemaFehler, match="Tabelle 'gibtsnicht' existiert"):
        lese_schema(db, "gibtsnicht")


# --- US-04.2 Abgleich Artefakt ↔ Daten ----------------------------------------------------------


def test_passendes_schema_ohne_meldung(artefakt, db):
    assert abgleich(artefakt, lese_schema(db, "absatz")) == []


def test_abweichung_artefakt_vs_daten_wird_gemeldet(artefakt, tmp_path):
    pfad = tmp_path / "fremd.db"
    verbindung = sqlite3.connect(pfad)
    # Tippfehler 'regoin', 'menge' als Text statt Zahl, zusätzliche Spalte 'notiz'
    verbindung.execute("CREATE TABLE absatz (datum TEXT, regoin TEXT, menge TEXT, umsatz REAL, notiz TEXT)")
    verbindung.close()

    meldungen = abgleich(artefakt, lese_schema(pfad, "absatz"))

    assert len(meldungen) == 4
    assert any("'region'" in m and "meinten Sie `regoin`" in m for m in meldungen)
    assert any("'menge'" in m and "INTEGER" in m for m in meldungen)
    assert any("'regoin'" in m and "nicht im Artefakt" in m for m in meldungen)
    assert any("'notiz'" in m and "nicht im Artefakt" in m for m in meldungen)


# --- US-04.3 Beispielwerte begrenzen ------------------------------------------------------------


def test_hoechstens_drei_beispielwerte(db):
    schema = {s.name: s for s in lese_schema(db, "absatz")}
    assert all(1 <= len(s.beispiele) <= 3 for s in schema.values())
    assert schema["region"].beispiele == ("Nord", "Ost", "Süd")  # verschieden und sortiert: jeder Lauf liefert dasselbe
    assert schema["datum"].beispiele[0] == "2026-01-15"  # ISO-Form, so wie das SQL später darauf zugreift


def test_lange_texte_werden_gekuerzt(tmp_path):
    pfad = tmp_path / "lang.db"
    verbindung = sqlite3.connect(pfad)
    verbindung.execute("CREATE TABLE t (text TEXT)")
    verbindung.execute("INSERT INTO t VALUES (?)", ("x" * 200,))
    verbindung.commit()
    verbindung.close()

    (spalte,) = lese_schema(pfad, "t")
    assert len(spalte.beispiele[0]) == 50


# --- Laden der CSV (Spezifikation 3.1) und Gesamtablauf ------------------------------------------


def test_csv_wird_geprueft_und_geladen(artefakt, csv, tmp_path):
    assert lade_daten(artefakt, csv, tmp_path / "neu.db") == 5


def test_fehlerhafte_csv_stoppt_mit_allen_meldungen(artefakt, tmp_path):
    kaputt = tmp_path / "kaputt.csv"
    kaputt.write_text("datum;region;menge;Umsatz\n15.01.2026;Nord;viele;10\n", encoding="utf-8")

    with pytest.raises(SchemaFehler) as fehler:
        lade_daten(artefakt, kaputt, tmp_path / "neu.db")

    text = " ".join(fehler.value.meldungen)
    assert "umsatz" in text  # fehlende Spalte
    assert "meinten Sie `umsatz`" in text  # Tippfehler in der Groß-/Kleinschreibung
    assert "menge" in text  # 'viele' ist keine ganze Zahl
    assert not (tmp_path / "neu.db").exists()  # fehlerhafte Daten erreichen nie eine Datenbank


def test_vorhandene_datenbank_wird_nicht_ueberschrieben(artefakt, csv, db):
    with pytest.raises(SchemaFehler, match="existiert bereits"):
        lade_daten(artefakt, csv, db)
    assert lade_daten(artefakt, csv, db, ueberschreiben=True) == 5


def test_fehlende_datendatei_wird_verstaendlich_gemeldet(artefakt, tmp_path):
    with pytest.raises(SchemaFehler, match="nicht gefunden"):
        lade_daten(artefakt, tmp_path / "gibtsnicht.csv", tmp_path / "neu.db")


def test_ausfuehren_liefert_bestaetigtes_schema(artefakt, csv, tmp_path):
    schema = ausfuehren(artefakt, csv, tmp_path / "neu.db")
    assert [s.name for s in schema] == ["datum", "region", "menge", "umsatz"]
    assert isinstance(schema[0], SpaltenInfo)
    assert schema[0].als_dict()["typ"] == "TEXT"
