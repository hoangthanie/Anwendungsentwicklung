"""Zusätzliche Tests zum Branding: Angriffs- und Randfälle, Bereinigung, sicheres Laden, Farben, Formularlogik."""
import io

import pytest
from PIL import Image

from dashboard_framework.eingabe.branding_form import baue_branding, farben_aus_text
from dashboard_framework.runner.branding import (
    LOGO_DATEINAME,
    BrandingFehler,
    bereinige_logo,
    lade_logo,
    normalisiere_farben,
    pruefe_logo_bytes,
    speichere_logo,
    theme_css,
)


def _bytes(format="PNG", groesse=(8, 8), modus="RGB"):
    ausgabe = io.BytesIO()
    Image.new(modus, groesse, "#ED7D31" if modus != "L" else 128).save(ausgabe, format=format)
    return ausgabe.getvalue()


def test_jpeg_wird_akzeptiert():
    assert pruefe_logo_bytes(_bytes("JPEG")) == "JPEG"


@pytest.mark.parametrize("format", ["GIF", "BMP", "WEBP"])
def test_andere_bildformate_werden_abgelehnt(format):
    with pytest.raises(BrandingFehler, match="Nur PNG- oder JPEG"):
        pruefe_logo_bytes(_bytes(format))


def test_svg_wird_abgelehnt():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    with pytest.raises(BrandingFehler):
        pruefe_logo_bytes(svg)


def test_leere_und_abgeschnittene_datei_werden_abgelehnt():
    with pytest.raises(BrandingFehler, match="leer"):
        pruefe_logo_bytes(b"")
    with pytest.raises(BrandingFehler):
        pruefe_logo_bytes(_bytes()[:30])


def test_riesige_pixelmaße_werden_abgelehnt():
    # kleine Datei (einfarbig, gut komprimiert), aber 5000 x 1 Pixel breit: über der erlaubten Kantenlänge
    with pytest.raises(BrandingFehler, match="zu groß"):
        pruefe_logo_bytes(_bytes(groesse=(5000, 1)))


def test_bereinigen_entfernt_angehaengte_daten_und_metadaten():
    original = _bytes() + b"<script>alert('versteckt')</script>"
    assert pruefe_logo_bytes(original) == "PNG"  # als Bild gültig
    sauber = bereinige_logo(original)
    assert b"<script>" not in sauber
    with Image.open(io.BytesIO(sauber)) as bild:
        assert bild.format == "PNG"


def test_bereinigen_wandelt_jpeg_in_png_und_verkleinert():
    sauber = bereinige_logo(_bytes("JPEG", groesse=(3000, 1500)))
    with Image.open(io.BytesIO(sauber)) as bild:
        assert bild.format == "PNG"
        assert max(bild.size) <= 1024


def test_bereinigen_behaelt_transparenz_von_paletten_png():
    palette = Image.new("P", (4, 4))
    palette.info["transparency"] = 0
    ausgabe = io.BytesIO()
    palette.save(ausgabe, format="PNG", transparency=0)
    with Image.open(io.BytesIO(bereinige_logo(ausgabe.getvalue()))) as bild:
        assert bild.mode in ("RGBA", "LA")


def test_speichern_nutzt_festen_dateinamen(tmp_path):
    name = speichere_logo(_bytes("JPEG"), tmp_path / "ausgabe")
    assert name == LOGO_DATEINAME
    assert (tmp_path / "ausgabe" / LOGO_DATEINAME).exists()


def test_lade_logo_nur_innerhalb_des_ordners(tmp_path):
    ordner = tmp_path / "dash"
    ordner.mkdir()
    (tmp_path / "geheim.png").write_bytes(_bytes())
    speichere_logo(_bytes(), ordner)
    assert lade_logo(ordner, "logo.png")
    with pytest.raises(BrandingFehler, match="heraus"):
        lade_logo(ordner, "../geheim.png")
    with pytest.raises(BrandingFehler, match="nicht gefunden"):
        lade_logo(ordner, "gibt_es_nicht.png")


def test_lade_logo_verweigert_kein_bild(tmp_path):
    (tmp_path / "logo.png").write_text("kein Bild")
    with pytest.raises(BrandingFehler):
        lade_logo(tmp_path, "logo.png")


def test_farben_werden_normalisiert_und_ungueltige_gemeinsam_gemeldet():
    assert normalisiere_farben([" #1f3864 ", "#ed7d31", ""]) == ["#1F3864", "#ED7D31"]
    with pytest.raises(BrandingFehler) as fehler:
        normalisiere_farben(["blau", "#12345", "#GGGGGG", "#1F3864"])
    assert "blau" in str(fehler.value) and "#12345" in str(fehler.value) and "#GGGGGG" in str(fehler.value)


def test_theme_css_nur_mit_gueltiger_farbe():
    assert "#1F3864" in theme_css(["#1F3864"])
    assert theme_css([]) == ""
    assert theme_css(["red; } body { display:none"]) == ""  # eingeschleustes CSS wird nicht ausgegeben


def test_farben_aus_text():
    assert farben_aus_text("#1F3864, #ED7D31;#70AD47  #000000") == ["#1F3864", "#ED7D31", "#70AD47", "#000000"]


def test_formular_baut_branding_und_bereinigtes_logo():
    branding, logo = baue_branding("  Muster GmbH ", "#1f3864, #ED7D31", _bytes("JPEG"))
    assert branding.firmenname == "Muster GmbH"
    assert branding.farben == ["#1F3864", "#ED7D31"]
    assert branding.logo == LOGO_DATEINAME
    assert logo.startswith(b"\x89PNG")


def test_formular_ohne_logo():
    branding, logo = baue_branding("X", "#000000", None)
    assert branding.logo is None and logo is None


def test_formular_meldet_alle_fehler_gemeinsam():
    with pytest.raises(BrandingFehler) as fehler:
        baue_branding("A" * 81, "blau", b"kein bild")
    assert len(fehler.value.meldungen) == 3
