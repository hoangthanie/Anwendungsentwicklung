"""Tests zur Upload-Prüfung (US-10.2, TF-035 bis TF-037) und zu Lesen/Übernehmen (US-10.1)."""
import sqlite3

import pandas as pd
import pytest

from dashboard_framework.runner.framework_lib import (
    MAX_UPLOAD_BYTES,
    UploadFehler,
    lese_csv,
    uebernehmen,
    validate_against_schema,
    zaehle_vorhandene_zeilen,
)

SCHEMA = [{"name": "datum", "typ": "datum"}, {"name": "wert", "typ": "dezimal"}]


def test_gueltiger_upload():  # TF-035
    df = pd.DataFrame({"datum": ["2026-01-05"], "wert": ["1.5"]})
    sauber = validate_against_schema(df, SCHEMA)
    assert sauber["wert"].tolist() == [1.5]
    assert sauber["datum"].tolist() == ["2026-01-05"]


def test_fehlende_spalte():  # TF-036
    df = pd.DataFrame({"datum": ["2026-01-05"]})
    with pytest.raises(UploadFehler, match=r"fehlende Spalte\(n\): wert"):
        validate_against_schema(df, SCHEMA)


def test_falscher_typ():  # TF-037
    df = pd.DataFrame({"datum": ["2026-01-05"], "wert": ["abc"]})
    with pytest.raises(UploadFehler, match="Spalte wert ist nicht vom Typ dezimal"):
        validate_against_schema(df, SCHEMA)


def test_alle_fehler_werden_gemeinsam_gemeldet():
    df = pd.DataFrame({"datum": ["kein Datum"], "unbekannt": ["x"]})
    with pytest.raises(UploadFehler) as fehler:
        validate_against_schema(df, SCHEMA)
    text = " | ".join(fehler.value.meldungen)
    assert "fehlende Spalte(n): wert" in text
    assert "unbekannte Spalte: unbekannt" in text
    assert "Spalte datum ist nicht vom Typ datum" in text


def test_aehnliche_spalte_wird_als_hinweis_genannt():
    df = pd.DataFrame({"datum": ["2026-01-05"], "Wert": ["1"]})
    with pytest.raises(UploadFehler, match="meinten Sie `wert`"):
        validate_against_schema(df, SCHEMA)


def test_deutsche_schreibweisen_werden_akzeptiert():
    schema = [{"name": "d", "typ": "datum"}, {"name": "w", "typ": "dezimal"}, {"name": "b", "typ": "bool"}, {"name": "n", "typ": "ganzzahl"}]
    df = pd.DataFrame({"d": ["31.12.2026"], "w": ["1,5"], "b": ["Ja"], "n": ["7"]})
    sauber = validate_against_schema(df, schema)
    assert sauber.iloc[0].tolist() == ["2026-12-31", 1.5, 1, 7]


@pytest.mark.parametrize("typ,wert", [
    ("ganzzahl", "1.5"), ("ganzzahl", "x"), ("dezimal", "1.234,5"), ("dezimal", "inf"),
    ("datum", "2026-13-40"), ("bool", "vielleicht"), ("datum", ""),
])
def test_ungueltige_werte_je_typ(typ, wert):
    with pytest.raises(UploadFehler):
        validate_against_schema(pd.DataFrame({"c": [wert]}), [{"name": "c", "typ": typ}])


def test_leere_datei_ohne_zeilen_wird_abgelehnt():
    with pytest.raises(UploadFehler, match="keine Datenzeilen"):
        validate_against_schema(pd.DataFrame({"datum": [], "wert": []}), SCHEMA)


def test_csv_mit_semikolon_und_bom():
    inhalt = "﻿datum;wert\n2026-01-05;1,5\n".encode("utf-8")
    df = lese_csv(inhalt)
    assert list(df.columns) == ["datum", "wert"]
    assert validate_against_schema(df, SCHEMA)["wert"].tolist() == [1.5]


def test_csv_zu_gross_oder_leer_oder_falsch_codiert():
    with pytest.raises(UploadFehler, match="größer"):
        lese_csv(b"a\n" + b"x" * MAX_UPLOAD_BYTES)
    with pytest.raises(UploadFehler, match="leer"):
        lese_csv(b"   \n")
    with pytest.raises(UploadFehler, match="UTF-8"):
        lese_csv("datum;wert\nä;1".encode("latin-1"))


def _anzahl(db):
    verbindung = sqlite3.connect(db)
    anzahl = verbindung.execute("SELECT COUNT(*) FROM absatz").fetchone()[0]
    verbindung.close()
    return anzahl


def test_uebernehmen_haengt_an(test_db):
    ok = pd.DataFrame({"datum": ["2026-03-01"], "menge": [1], "umsatz": [1.0]})
    assert uebernehmen(ok, test_db, "absatz") == 1
    assert _anzahl(test_db) == 5


def test_uebernehmen_ist_atomar(tmp_path):
    """Scheitert die zweite Zeile (NOT NULL), darf auch die erste nicht in der Datenbank landen."""
    db = tmp_path / "t.db"
    verbindung = sqlite3.connect(db)
    verbindung.execute("CREATE TABLE t (a INTEGER NOT NULL)")
    verbindung.commit()
    verbindung.close()
    with pytest.raises(sqlite3.IntegrityError):
        uebernehmen(pd.DataFrame({"a": [1, None]}), db, "t")
    verbindung = sqlite3.connect(db)
    assert verbindung.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0
    verbindung.close()


def test_uebernehmen_lehnt_fremde_spalten_ab(test_db):
    fremd = pd.DataFrame({"datum": ["2026-03-01"], "gibts_nicht": [1]})
    with pytest.raises(UploadFehler, match="gibts_nicht"):
        uebernehmen(fremd, test_db, "absatz")
    assert _anzahl(test_db) == 4


def test_uebernehmen_verlangt_existierende_tabelle_und_db(test_db, tmp_path):
    df = pd.DataFrame({"datum": ["2026-03-01"]})
    with pytest.raises(UploadFehler, match="existiert in der Datenbank nicht"):
        uebernehmen(df, test_db, "andere_tabelle")
    with pytest.raises(sqlite3.OperationalError):
        uebernehmen(df, tmp_path / "neu.db", "absatz")
    assert not (tmp_path / "neu.db").exists()


def test_uebernehmen_gegen_sql_injection_im_tabellennamen(test_db):
    df = pd.DataFrame({"datum": ["2026-03-01"]})
    with pytest.raises(UploadFehler):
        uebernehmen(df, test_db, 'absatz"; DROP TABLE absatz; --')
    assert _anzahl(test_db) == 4


def test_vorhandene_zeilen_werden_gezaehlt(test_db):
    df = pd.DataFrame({
        "datum": ["2026-01-10", "2026-05-05"], "region": ["Nord", "Nord"],
        "produktkategorie": ["A", "A"], "menge": [10, 1], "umsatz": [100.0, 1.0],
    })
    assert zaehle_vorhandene_zeilen(df, test_db, "absatz") == 1


def test_datum_mit_uhrzeit_deutsch_und_iso():
    schema = [{"name": "t", "typ": "datum"}]
    deutsch = validate_against_schema(pd.DataFrame({"t": ["27.10.2026 11:20:10", "26.10.2026 23:14:38"]}), schema)
    assert deutsch["t"].tolist() == ["2026-10-27 11:20:10", "2026-10-26 23:14:38"]  # mit Uhrzeit gespeichert, sortierbar
    iso = validate_against_schema(pd.DataFrame({"t": ["2026-10-27 11:20:10"]}), schema)
    assert iso["t"].tolist() == ["2026-10-27 11:20:10"]
    ohne = validate_against_schema(pd.DataFrame({"t": ["27.10.2026", "01.01.2027"]}), schema)
    assert ohne["t"].tolist() == ["2026-10-27", "2027-01-01"]  # ohne Uhrzeit in den Daten wird auch keine erfunden
    kurz = validate_against_schema(pd.DataFrame({"t": ["27.10.2026 11:20"]}), schema)
    assert kurz["t"].tolist() == ["2026-10-27 11:20:00"]


def test_datum_mit_gemischten_formaten_wird_abgelehnt():
    with pytest.raises(UploadFehler, match="nicht vom Typ datum"):
        validate_against_schema(pd.DataFrame({"t": ["27.10.2026 11:20:10", "2026-10-27"]}), [{"name": "t", "typ": "datum"}])
