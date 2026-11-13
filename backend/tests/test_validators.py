"""Tests für einzelne Prüfschichten (pipeline/harness/validators.py), wie im Testkonzept zu US-05 vorgesehen."""

import sqlite3

import pytest

from pipeline.harness.validators import (
    SqlPruefFehler,
    pruefe_ausfuehrbar,
    pruefe_tabelle,
    zerlege,
)


@pytest.fixture
def db(tmp_path):
    pfad = tmp_path / "daten.db"
    verbindung = sqlite3.connect(pfad)
    verbindung.execute("CREATE TABLE t (a TEXT, b REAL)")
    verbindung.execute("INSERT INTO t VALUES ('x', 1.0)")
    verbindung.commit()
    verbindung.close()
    return pfad


def test_unbekannte_spalte_ist_nicht_ausfuehrbar(db):
    with pytest.raises(SqlPruefFehler, match="no such column"):
        pruefe_ausfuehrbar("SELECT c FROM t", db)


def test_ausfuehrbares_sql_liefert_spalten_und_zeilen(db):
    spalten, zeilen = pruefe_ausfuehrbar("SELECT a, SUM(b) AS summe FROM t GROUP BY a", db)
    assert spalten == ["a", "summe"]
    assert zeilen == [("x", 1.0)]


def test_teilabfrage_mit_with_ist_keine_fremde_tabelle():
    pruefe_tabelle(zerlege("WITH m AS (SELECT a FROM t) SELECT a FROM m"), "t")


def test_unlesbares_sql_wird_gemeldet():
    with pytest.raises(SqlPruefFehler, match="kein gültiges SQLite"):
        zerlege("SELECT FROM WHERE")
