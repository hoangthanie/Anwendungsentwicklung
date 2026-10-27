import sqlite3

import pytest

from dashboard_framework.runner.sicherheit import UnsicheresSql, pruefe_nur_lesend, verbinde_nur_lesend


@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "select region, sum(umsatz) from absatz group by region;",
    "WITH m AS (SELECT 1 AS a) SELECT a FROM m",
    "SELECT 1 -- DELETE kommt nur im Kommentar vor",
    "SELECT 'DROP TABLE x' AS text",
    "SELECT update_datum FROM absatz",
])
def test_erlaubte_abfragen(sql):
    assert pruefe_nur_lesend(sql) == sql


@pytest.mark.parametrize("sql", [
    "DELETE FROM absatz",
    "DROP TABLE absatz",
    "SELECT 1; DELETE FROM absatz",
    "UPDATE absatz SET umsatz = 0",
    "INSERT INTO absatz VALUES (1)",
    "SELECT 1 /* x */; DROP TABLE absatz",
    "ATTACH DATABASE 'x.db' AS x",
    "PRAGMA writable_schema = 1",
    "WITH x AS (SELECT 1) DELETE FROM absatz",
    "",
    "   ",
    "-- nur Kommentar",
])
def test_unerlaubte_abfragen(sql):
    with pytest.raises(UnsicheresSql):
        pruefe_nur_lesend(sql)


def test_verbindung_ist_technisch_schreibgeschuetzt(tmp_path):
    pfad = tmp_path / "t.db"
    v = sqlite3.connect(pfad)
    v.execute("CREATE TABLE t (a INTEGER)")
    v.commit()
    v.close()
    ro = verbinde_nur_lesend(pfad)
    with pytest.raises(sqlite3.OperationalError):
        ro.execute("INSERT INTO t VALUES (1)")
    ro.close()


def test_fehlende_db_wird_nicht_neu_angelegt(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        verbinde_nur_lesend(tmp_path / "gibt_es_nicht.db")
    assert not (tmp_path / "gibt_es_nicht.db").exists()
