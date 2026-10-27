from pathlib import Path

import pytest
from pydantic import ValidationError

from dashboard_framework.models.dashboard_config import Chart, DashboardConfig

BEISPIEL = Path(__file__).resolve().parents[1] / "examples" / "sales" / "dashboard.json"


def test_beispiel_dashboard_json_ist_gueltig():
    config = DashboardConfig.laden(BEISPIEL)
    assert len(config.charts) == 4


def test_nur_erlaubte_chart_typen():  # TF-023 / US-06.3
    with pytest.raises(ValidationError):
        Chart(titel="x", typ="kreis3d", sql="SELECT 1")


def test_roundtrip(tmp_path):  # TF-024
    config = DashboardConfig.laden(BEISPIEL)
    ziel = tmp_path / "d.json"
    config.speichern(ziel)
    assert DashboardConfig.laden(ziel) == config


def test_ungueltige_farbe_wird_abgelehnt():
    with pytest.raises(ValidationError):
        Chart(titel="x", typ="balken", sql="SELECT 1", farbe="blau")


def test_doppelte_chart_titel_werden_abgelehnt():
    c = Chart(titel="x", typ="tabelle", sql="SELECT 1")
    with pytest.raises(ValidationError):
        DashboardConfig(name="n", titel="t", tabelle="a", charts=[c, c])


def test_json_schema_enthaelt_chart_typen():
    assert "balken" in str(DashboardConfig.json_schema())


def test_framework_code_ohne_dashboard_begriffe():  # TF-041 / US-12.1 (Vorabversion fürs Frontend)
    src = Path(__file__).resolve().parents[1] / "src"
    verboten = ["umsatz", "region", "produktkategorie", "absatz"]
    for datei in src.rglob("*.py"):
        text = datei.read_text(encoding="utf-8").lower()
        for wort in verboten:
            assert wort not in text, f"'{wort}' in {datei.name}: Framework-Code muss generisch bleiben"
