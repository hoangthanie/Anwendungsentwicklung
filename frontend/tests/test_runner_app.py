"""Rauchtest der Streamlit-Oberfläche ohne Browser (streamlit.testing): die App läuft mit dem Beispiel durch."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

WURZEL = Path(__file__).resolve().parents[1]
APP = WURZEL / "src" / "dashboard_framework" / "runner" / "app.py"
BEISPIEL = WURZEL / "examples" / "sales"


@pytest.fixture
def demo_db():
    db = BEISPIEL / "daten.db"
    if not db.exists():
        subprocess.run([sys.executable, str(BEISPIEL / "make_demo_db.py")], check=True)
    return db


def test_app_zeigt_beispiel_dashboard(demo_db, monkeypatch):
    monkeypatch.setenv("DASHBOARD_CONFIG", str(BEISPIEL / "dashboard.json"))
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert not app.error
    texte = " ".join(m.value for m in app.markdown)
    assert "Vertriebs-Dashboard" in texte and "Muster GmbH" in texte  # Schriftfeld mit Titel und Kunde
    assert "nur lesend" in texte and "fb-kennzahl" in texte  # Datenzugriff im Kopf, Kennzahl als Feld
    assert "--akzent:#1F3864" in texte  # erste Kundenfarbe ist der Akzent
    assert len(app.tabs) == 3  # Dashboard, Über dieses Dashboard, Daten aktualisieren


def test_app_meldet_fehlende_konfiguration_verstaendlich(monkeypatch, tmp_path):
    monkeypatch.setenv("DASHBOARD_CONFIG", str(tmp_path / "gibt_es_nicht.json"))
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert len(app.error) == 1
