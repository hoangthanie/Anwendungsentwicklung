"""Tests zu US-02 (Fehler früh erkennen) und US-03 (Branding): TF-006 sowie TF-008 bis TF-010."""
import os

import pytest
from PIL import Image

from dashboard_framework.models.spalten import aehnliche_spalte
from dashboard_framework.runner.branding import MAX_LOGO_BYTES, BrandingFehler, pruefe_logo


def _bild_bytes(pfad, groesse=(1, 1), format="PNG", rauschen=False):
    if rauschen:  # zufällige Pixel lassen sich nicht komprimieren: so wird die Datei sicher groß
        bild = Image.frombytes("RGB", groesse, os.urandom(groesse[0] * groesse[1] * 3))
    else:
        bild = Image.new("RGB", groesse, "#1F3864")
    bild.save(pfad, format=format)
    return pfad


def test_aehnliche_spalte_wird_vorgeschlagen():  # TF-006 / US-02.3
    bekannte = ["Region", "umsatz", "datum"]
    assert aehnliche_spalte("region", bekannte) == "Region"
    assert aehnliche_spalte("xyz", bekannte) is None


def test_echtes_png_wird_akzeptiert(tmp_path):  # TF-008 / US-03.2
    assert pruefe_logo(_bild_bytes(tmp_path / "logo.png")) == "PNG"


def test_getarnte_datei_wird_abgelehnt(tmp_path):  # TF-009 / US-03.2
    falsch = tmp_path / "logo.png"
    falsch.write_text("<script>alert('hallo')</script>", encoding="utf-8")
    with pytest.raises(BrandingFehler, match="kein gültiges PNG"):
        pruefe_logo(falsch)


def test_zu_grosses_logo_wird_abgelehnt(tmp_path):  # TF-010 / US-03.2
    gross = _bild_bytes(tmp_path / "gross.png", groesse=(700, 700), rauschen=True)
    assert gross.stat().st_size > MAX_LOGO_BYTES
    with pytest.raises(BrandingFehler, match="1 MB"):
        pruefe_logo(gross)
