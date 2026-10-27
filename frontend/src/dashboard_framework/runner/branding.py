"""Firmen-Branding: Logo- und Farbprüfung (US-03, Risiko R15).

Ein Upload ist fremder Input. Wir vertrauen weder Dateiendung noch Dateiname, sondern prüfen den Inhalt mit Pillow,
und wir speichern nie die hochgeladenen Bytes selbst, sondern ein von Pillow neu erzeugtes PNG (bereinige_logo).
"""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from dashboard_framework.models.dashboard_config import ist_farbcode

MAX_LOGO_BYTES = 1024 * 1024  # 1 MB
MAX_LOGO_KANTE = 4000  # Pixel; schützt vor "Dekompressionsbomben" (winzige Datei, riesiges Bild im Speicher)
ANZEIGE_KANTE = 1024  # beim Speichern wird höchstens auf diese Kantenlänge verkleinert
ERLAUBTE_FORMATE = {"PNG", "JPEG"}  # bewusst kein SVG (kann Skripte enthalten), kein GIF/WebP/BMP
LOGO_DATEINAME = "logo.png"  # fester Name: kein vom Anwender bestimmter Dateiname, damit kein Pfad-Trick möglich ist


class BrandingFehler(ValueError):
    """Logo oder Farben sind nicht verwendbar. 'meldungen' enthält alle Gründe in verständlicher Form."""

    def __init__(self, meldungen: list[str] | str):
        self.meldungen = [meldungen] if isinstance(meldungen, str) else list(meldungen)
        super().__init__("; ".join(self.meldungen))


def pruefe_logo_bytes(inhalt: bytes) -> str:
    """Prüft Bild-Bytes und gibt das erkannte Format ('PNG' oder 'JPEG') zurück; sonst BrandingFehler."""
    if not inhalt:
        raise BrandingFehler("Die Logo-Datei ist leer")
    if len(inhalt) > MAX_LOGO_BYTES:
        raise BrandingFehler(f"Das Logo ist größer als {MAX_LOGO_BYTES // (1024 * 1024)} MB")
    try:
        with Image.open(io.BytesIO(inhalt)) as bild:
            bildformat = bild.format
            breite, hoehe = bild.size
            if bildformat not in ERLAUBTE_FORMATE:
                raise BrandingFehler(f"Nur PNG- oder JPEG-Bilder sind erlaubt (erkannt: {bildformat})")
            if max(breite, hoehe) > MAX_LOGO_KANTE:
                raise BrandingFehler(f"Das Logo ist zu groß ({breite}×{hoehe} Pixel, erlaubt sind höchstens {MAX_LOGO_KANTE} je Seite)")
            bild.verify()  # prüft die Struktur der Datei, ohne alle Pixel zu dekodieren
    except BrandingFehler:
        raise
    except Exception:
        # Pillow wirft je nach Defekt sehr verschiedene Typen (UnidentifiedImageError, OSError, SyntaxError, ...).
        # Für den Anwender zählt nur: keine gültige Bilddatei.
        raise BrandingFehler("Die Datei ist kein gültiges PNG- oder JPEG-Bild") from None
    return bildformat


def pruefe_logo(pfad: str | Path) -> str:
    """Wie pruefe_logo_bytes, für eine Datei auf der Platte. Die Größe wird geprüft, bevor die Datei gelesen wird."""
    datei = Path(pfad)
    try:
        if datei.stat().st_size > MAX_LOGO_BYTES:
            raise BrandingFehler(f"Das Logo ist größer als {MAX_LOGO_BYTES // (1024 * 1024)} MB")
        return pruefe_logo_bytes(datei.read_bytes())
    except FileNotFoundError:
        raise BrandingFehler("Die Logo-Datei wurde nicht gefunden") from None


def bereinige_logo(inhalt: bytes) -> bytes:
    """Prüft das Bild und erzeugt daraus ein NEUES PNG.

    Das Neu-Kodieren wirft alles weg, was nicht Bild ist: Metadaten (z. B. GPS in Fotos), angehängte Daten hinter dem Bildende
    und in Bilddateien versteckte Nutzlasten ("Polyglot"-Dateien). Gespeichert wird nur, was Pillow selbst geschrieben hat.
    """
    pruefe_logo_bytes(inhalt)
    with Image.open(io.BytesIO(inhalt)) as bild:
        bild.load()
        if bild.mode == "CMYK":
            bild = bild.convert("RGB")
        elif bild.mode not in ("RGB", "RGBA", "L", "LA"):
            bild = bild.convert("RGBA")  # z. B. Paletten-PNG mit Transparenz
        bild.thumbnail((ANZEIGE_KANTE, ANZEIGE_KANTE))
        ausgabe = io.BytesIO()
        bild.save(ausgabe, format="PNG")
    return ausgabe.getvalue()


def speichere_logo(inhalt: bytes, ordner: str | Path) -> str:
    """Speichert das bereinigte Logo als 'logo.png' im Ordner und gibt den Dateinamen zurück (für Branding.logo)."""
    sauber = bereinige_logo(inhalt)
    ziel = Path(ordner)
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / LOGO_DATEINAME).write_bytes(sauber)
    return LOGO_DATEINAME


def lade_logo(basis_ordner: str | Path, logo: str) -> bytes:
    """Liest das in der dashboard.json genannte Logo sicher: nur innerhalb des Konfigurationsordners und nur, wenn es ein gültiges Bild ist.

    Die dashboard.json ist Eingabe, die manipuliert sein könnte (Risiko R16). Ein Eintrag wie '../../geheim.png' darf nichts außerhalb lesen.
    """
    basis = Path(basis_ordner).resolve()
    ziel = (basis / logo).resolve()
    if not ziel.is_relative_to(basis):
        raise BrandingFehler("Der Logo-Pfad zeigt aus dem Dashboard-Ordner heraus und wird nicht geladen")
    pruefe_logo(ziel)
    return ziel.read_bytes()


def normalisiere_farben(farben: list[str]) -> list[str]:
    """Entfernt Leerzeichen, vereinheitlicht auf Großbuchstaben (#1f3864 -> #1F3864) und meldet alle ungültigen Codes gemeinsam."""
    eingaben = [f.strip() for f in farben if f.strip()]
    falsch = [f for f in eingaben if not ist_farbcode(f)]  # in der Meldung die Eingabe zeigen, wie sie getippt wurde
    if falsch:
        raise BrandingFehler(f"Ungültige Farbcodes: {', '.join(falsch)} (erwartet #RRGGBB, z. B. #1F3864)")
    return [f.upper() for f in eingaben]


def theme_css(farben: list[str]) -> str:
    """CSS für die Akzentfarbe (erste Firmenfarbe): aktiver Tab und Haupt-Button.

    Der Code wird als Text in HTML eingesetzt. Darum wird er hier nochmals streng geprüft, damit über die Konfiguration kein fremdes CSS/HTML eingeschleust werden kann.
    """
    if not farben or not ist_farbcode(farben[0]):
        return ""
    f = farben[0]
    return (
        # Streamlit ändert den Aufbau seiner Elemente zwischen Versionen; deshalb je Version ein Selektor (1.66: react-aria, älter: baseweb).
        f'.react-aria-SelectionIndicator, [data-baseweb="tab-highlight"] {{ background-color: {f} !important; }}'
        f'[role="tab"][aria-selected="true"], [data-baseweb="tab"][aria-selected="true"] {{ color: {f} !important; }}'
        f'button[kind="primary"], button[data-testid="stBaseButton-primary"] {{ background-color: {f} !important; border-color: {f} !important; }}'
    )
