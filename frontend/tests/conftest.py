"""Gemeinsame Test-Hilfen: kleine Test-DB mit bekannten Werten (Testorakel: Nord=150, Süd=70, Ost=30)."""
import sqlite3

import pytest

from dashboard_framework.models.dashboard_config import Branding, Chart, DashboardConfig


@pytest.fixture
def test_db(tmp_path):
    pfad = tmp_path / "daten.db"
    verbindung = sqlite3.connect(pfad)
    verbindung.execute("CREATE TABLE absatz (datum TEXT, region TEXT, produktkategorie TEXT, menge INTEGER, umsatz REAL)")
    verbindung.executemany(
        "INSERT INTO absatz VALUES (?, ?, ?, ?, ?)",
        [
            ("2026-01-10", "Nord", "A", 10, 100.0),
            ("2026-02-10", "Nord", "B", 5, 50.0),
            ("2026-01-12", "Süd", "A", 7, 70.0),
            ("2026-02-15", "Ost", "B", 3, 30.0),
        ],
    )
    verbindung.commit()
    verbindung.close()
    return pfad


@pytest.fixture
def config_region():
    return DashboardConfig(
        name="sales",
        titel="Test",
        tabelle="absatz",
        charts=[
            Chart(titel="Umsatz nach Region", typ="balken", sql="SELECT region, SUM(umsatz) AS umsatz FROM absatz GROUP BY region"),
        ],
        branding=Branding(firmenname="Muster", farben=["#1F3864"]),
    )
