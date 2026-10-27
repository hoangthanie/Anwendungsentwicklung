"""Tests zu US-09 (Dashboard anzeigen), Testfälle TF-031 und TF-032 aus dem Backlog, plus Hilfsfunktionen des Runners."""
import sqlite3

import pandas as pd
import pytest

from dashboard_framework.models.dashboard_config import Chart, DashboardConfig
from dashboard_framework.runner.charts import erstelle_figur, kennzahl_wert, waehle_farbe
from dashboard_framework.runner.daten import achsen, lade_chart_daten, layout_zeilen
from dashboard_framework.runner.framework_lib import UploadFehler, uebernehmen, validate_against_schema
from dashboard_framework.runner.sicherheit import UnsicheresSql


def test_jedes_chart_bekommt_seine_daten(config_region, test_db):  # TF-031 / US-09.1
    daten = lade_chart_daten(config_region, test_db)
    df = daten["Umsatz nach Region"]
    assert set(df["region"]) == {"Nord", "Süd", "Ost"}
    assert df.set_index("region")["umsatz"].to_dict() == {"Nord": 150.0, "Süd": 70.0, "Ost": 30.0}


def test_runner_fuehrt_kein_schreibendes_sql_aus(test_db):  # TF-032 / US-09.2
    boese = DashboardConfig(
        name="x", titel="x", tabelle="absatz",
        charts=[
            Chart(titel="ok", typ="tabelle", sql="SELECT * FROM absatz"),
            Chart(titel="boese", typ="tabelle", sql="DELETE FROM absatz"),
        ],
    )
    with pytest.raises(UnsicheresSql):
        lade_chart_daten(boese, test_db)
    verbindung = sqlite3.connect(test_db)
    assert verbindung.execute("SELECT COUNT(*) FROM absatz").fetchone()[0] == 4
    verbindung.close()


def test_upload_wird_angehaengt(test_db):  # TF-034 / US-10.1
    schema = [
        {"name": "datum", "typ": "datum"}, {"name": "region", "typ": "text"}, {"name": "produktkategorie", "typ": "text"},
        {"name": "menge", "typ": "ganzzahl"}, {"name": "umsatz", "typ": "dezimal"},
    ]
    upload = pd.DataFrame({
        "datum": ["2026-03-01"], "region": ["West"], "produktkategorie": ["C"], "menge": ["4"], "umsatz": ["40,5"],
    })
    sauber = validate_against_schema(upload, schema)
    assert uebernehmen(sauber, test_db, "absatz") == 1
    verbindung = sqlite3.connect(test_db)
    assert verbindung.execute("SELECT COUNT(*) FROM absatz").fetchone()[0] == 5
    assert verbindung.execute("SELECT region, menge, umsatz FROM absatz WHERE datum = '2026-03-01'").fetchone() == ("West", 4, 40.5)
    verbindung.close()


def test_falscher_upload_aendert_die_datenbank_nicht(test_db):  # US-10.2: nichts wird geschrieben
    upload = pd.DataFrame({"datum": ["2026-03-01"], "menge": ["viele"]})
    schema = [{"name": "datum", "typ": "datum"}, {"name": "menge", "typ": "ganzzahl"}]
    with pytest.raises(UploadFehler):
        validate_against_schema(upload, schema)
    verbindung = sqlite3.connect(test_db)
    assert verbindung.execute("SELECT COUNT(*) FROM absatz").fetchone()[0] == 4
    verbindung.close()


def test_sortierung_absteigend(config_region, test_db):
    chart = config_region.charts[0].model_copy(update={"sortierung": "absteigend"})
    config = config_region.model_copy(update={"charts": [chart]})
    df = lade_chart_daten(config, test_db)["Umsatz nach Region"]
    assert list(df["region"]) == ["Nord", "Süd", "Ost"]


def test_achsen_default_ist_erste_und_zweite_spalte(test_db, config_region):
    df = lade_chart_daten(config_region, test_db)["Umsatz nach Region"]
    assert achsen(config_region.charts[0], df) == ("region", "umsatz")


def test_layout_halb_paarweise_voll_allein():
    def c(titel, breite):
        return Chart(titel=titel, typ="tabelle", sql="SELECT 1", breite=breite)

    zeilen = layout_zeilen([c("a", "halb"), c("b", "halb"), c("c", "voll"), c("d", "halb")])
    assert [[x.titel for x in z] for z in zeilen] == [["a", "b"], ["c"], ["d"]]


def test_figur_nutzt_chart_farbe_vor_firmenfarbe(config_region, test_db):
    chart = config_region.charts[0].model_copy(update={"farbe": "#ED7D31"})
    df = lade_chart_daten(config_region, test_db)["Umsatz nach Region"]
    assert waehle_farbe(chart, ["#1F3864"]) == "#ED7D31"
    assert erstelle_figur(chart, df, ["#1F3864"]).data[0].marker.color == "#ED7D31"


def test_kennzahl_formatierung():
    assert kennzahl_wert(pd.DataFrame({"v": [1234567]})) == "1 234 567"
    assert kennzahl_wert(pd.DataFrame({"v": [12.5]})) == "12.50"
    assert kennzahl_wert(pd.DataFrame({"v": []})) == "n/a"
