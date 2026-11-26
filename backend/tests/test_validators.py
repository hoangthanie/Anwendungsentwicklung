"""Tests für einzelne Prüfschichten (pipeline/harness/validators.py), wie im Testkonzept zu US-05 vorgesehen."""

import sqlite3

import pytest

from pipeline.harness.validators import (
    SqlPruefFehler,
    fuehre_aus,
    pruefe_anker,
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


# --- Anker: ein gleichnamiger Alias zählt nicht als Spalte (Hinweis 1 aus Review #15) ---------------


def test_alias_mit_name_der_ankerspalte_wird_abgelehnt():
    with pytest.raises(SqlPruefFehler, match="umsatz"):
        pruefe_anker("SELECT region, COUNT(*) AS umsatz FROM absatz GROUP BY region ORDER BY umsatz", ["umsatz"])


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT region, SUM(umsatz) AS umsatz FROM absatz GROUP BY region ORDER BY umsatz",  # Spalte im Ausdruck des Alias
        "SELECT region, SUM(absatz.umsatz) AS summe FROM absatz GROUP BY region",  # mit Tabellenname
        "WITH m AS (SELECT region, umsatz FROM absatz) SELECT region, SUM(umsatz) AS summe FROM m GROUP BY region",
    ],
)
def test_echte_verwendung_der_ankerspalte_besteht(sql):
    pruefe_anker(sql, ["umsatz"])


# --- Zeitlimit (Hinweis 4 aus Review #15) ----------------------------------------------------------


def test_endlose_abfrage_wird_nach_dem_zeitlimit_abgebrochen(db):
    endlos = "WITH RECURSIVE z(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM z) SELECT COUNT(*) FROM z"
    with pytest.raises(SqlPruefFehler, match="länger als 0.2 Sekunden"):
        fuehre_aus(endlos, db, zeitlimit_s=0.2)
