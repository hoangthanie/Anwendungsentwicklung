"""Tests für einzelne Prüfschichten (pipeline/harness/validators.py), wie im Testkonzept zu US-05 vorgesehen."""

import sqlite3

import pytest

from pipeline.harness.validators import (
    SqlPruefFehler,
    fuehre_aus,
    pruefe_anker,
    pruefe_ausfuehrbar,
    pruefe_bedeutung,
    pruefe_einzelwert,
    pruefe_from,
    pruefe_ganzzahl_division,
    pruefe_keine_selbstdivision,
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


# --- Einzelwert = genau eine Spalte (Probeläufe 7 und 10, ADR 0008) ----------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        # Lauf 7: Vormonat, Jahresumsatz und Quote nebeneinander; die Kachel zeigte die erste Spalte
        (
            "SELECT SUM(CASE WHEN region = 'Nord' THEN umsatz END) AS vormonat, SUM(umsatz) AS gesamt, "
            "SUM(umsatz) / SUM(CASE WHEN region = 'Nord' THEN umsatz END) AS quote FROM absatz"
        ),
        # Lauf 10: zwei Summen, keine Quote
        "SELECT SUM(umsatz) AS aktuell, SUM(CASE WHEN region = 'Nord' THEN umsatz END) AS vorher FROM absatz",
    ],
)
def test_einzelwert_mit_mehreren_spalten_wird_abgelehnt(sql):
    with pytest.raises(SqlPruefFehler, match="genau eine Spalte"):
        pruefe_einzelwert(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT SUM(umsatz) / (SELECT SUM(umsatz) FROM absatz WHERE region = 'Nord') AS quote FROM absatz",  # Lauf 12
        "SELECT region, SUM(umsatz) AS summe FROM absatz GROUP BY region",  # gruppiert, auch wenn nur eine Gruppe
        "SELECT region, umsatz FROM absatz ORDER BY umsatz DESC LIMIT 1",  # Bezeichnung plus Wert, kein Aggregat
        "WITH t AS (SELECT region, SUM(umsatz) AS s FROM absatz GROUP BY region) SELECT region, s FROM t",
    ],
)
def test_andere_ergebnisformen_bestehen(sql):
    pruefe_einzelwert(sql)



# --- Messung 27.11.: Fehler, die alle Schichten bestanden oder unverständlich gemeldet wurden ------------------


def test_beschriftung_neben_dem_einzelwert_wird_abgelehnt():  # qwen3:14b, „Anteil Region Nord“
    sql = "SELECT 'Anteil Region Nord' AS kpi, SUM(CASE WHEN region = 'Nord' THEN umsatz ELSE 0 END) * 100.0 / SUM(umsatz) FROM absatz"
    with pytest.raises(SqlPruefFehler, match="ohne Beschriftung"):
        pruefe_einzelwert(sql)


def test_fehlendes_from_wird_klar_benannt():  # qwen3:14b, dreimal „no such column: umsatz“
    sql = (
        "SELECT (SUM(CASE WHEN datum = (SELECT MAX(datum) FROM absatz) THEN umsatz END)"
        " / SUM(CASE WHEN datum < (SELECT MAX(datum) FROM absatz) THEN umsatz END)) AS quote"
    )
    with pytest.raises(SqlPruefFehler, match="fehlt FROM absatz.*Spalte umsatz"):
        pruefe_from(sql, "absatz")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT region, SUM(umsatz) FROM absatz GROUP BY region",
        "SELECT (SELECT SUM(umsatz) FROM absatz) / (SELECT COUNT(*) FROM absatz) AS schnitt",  # nur Unterabfragen
        "SELECT 1",
    ],
)
def test_from_ist_vorhanden_oder_nicht_noetig(sql):
    pruefe_from(sql, "absatz")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT COUNT(CASE WHEN region = 'Nord' THEN 1 END) / COUNT(*) FROM absatz",  # qwen3:14b
        "SELECT (SELECT COUNT(*) FROM absatz WHERE region = 'Nord') / (SELECT COUNT(*) FROM absatz) AS quote",  # qwen3:8b
        "SELECT SUM(menge) / SUM(CASE WHEN region = 'Nord' THEN menge END) FROM absatz",  # Ganzzahl-Spalte
    ],
)
def test_division_zweier_ganzer_zahlen_wird_abgelehnt(sql):
    with pytest.raises(SqlPruefFehler, match="zwei ganze Zahlen"):
        pruefe_ganzzahl_division(sql, {"menge"})


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1.0 * COUNT(CASE WHEN region = 'Nord' THEN 1 END) / COUNT(*) FROM absatz",
        "SELECT SUM(umsatz) / SUM(menge) FROM absatz",  # umsatz ist eine Dezimalzahl
        "SELECT CAST(COUNT(*) AS REAL) / COUNT(DISTINCT region) FROM absatz",
    ],
)
def test_division_mit_kommazahl_besteht(sql):
    pruefe_ganzzahl_division(sql, {"menge"})


def test_selbstdivision_mit_faktor_wird_erkannt():  # qwen3:30b-a3b, Ergebnis immer 1,0
    sql = "SELECT SUM(CASE WHEN region = 'Nord' THEN 1 ELSE 0 END) * 1.0 / SUM(CASE WHEN region = 'Nord' THEN 1 ELSE 0 END) * 1.0 FROM absatz"
    with pytest.raises(SqlPruefFehler, match="durch sich selbst"):
        pruefe_keine_selbstdivision(sql)


def test_unbekannte_spalte_verlangt_ablehnung_statt_ersatz():  # qwen3:8b nahm AVG(umsatz) für die Kundenzufriedenheit
    with pytest.raises(SqlPruefFehler, match="ersetze sie nicht durch eine andere, sondern lehne die KPI ab"):
        pruefe_bedeutung("SELECT region, AVG(kundenzufriedenheit) FROM absatz GROUP BY region", {"region", "umsatz"})
