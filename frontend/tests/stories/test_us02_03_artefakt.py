"""Tests zu US-02 (Fehler früh erkennen) und US-03 (Branding). Wächst mit AP 3.3 und 6.2."""
from dashboard_framework.models.spalten import aehnliche_spalte


def test_aehnliche_spalte_wird_vorgeschlagen():  # TF-006 / US-02.3
    bekannte = ["Region", "umsatz", "datum"]
    assert aehnliche_spalte("region", bekannte) == "Region"
    assert aehnliche_spalte("xyz", bekannte) is None
