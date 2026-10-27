"""Farben, Kontrastberechnung und das globale CSS des Gestaltungssystems "Formblatt".

Was wohin gehört:
- .streamlit/config.toml: Grundfarben, Schriften und Eckenradius, die Streamlit selbst versteht.
- Dieses Modul: alles, was Streamlit nicht einstellen lässt (Linienführung, Tabs, Zustandsmarken, Schriftfeld). Die Akzentfarbe ist
  ein Parameter: im Runner die Farbe des Kunden, in der Eingabe-App die Produktfarbe.
Die Kundenfarbe ist Eingabe von außen und wird als Text in CSS eingesetzt. Sie wird deshalb streng als #RRGGBB geprüft.
"""
from __future__ import annotations

import streamlit as st

from dashboard_framework.models.dashboard_config import ist_farbcode

PAPIER = "#F1F3F5"
BLATT = "#FFFFFF"
TINTE = "#1C2227"
TINTE_2 = "#4A545D"  # zweite Textstufe, auf Weiß 7,9:1
LINIE = "#AEB7BF"  # Blattränder und Trennlinien (dekorativ)
HAARLINIE = "#DDE2E6"
LINIE_STARK = "#7C8791"  # Rand von Eingabefeldern und Bedienelementen, mind. 3:1 gegen Weiß
PRODUKT_AKZENT = "#23579F"

ZUSTAENDE = {
    # art: (Text, Hintergrund) jeweils mit mindestens 4,5:1
    "offen": (TINTE_2, "#EEF1F3"),
    "gueltig": ("#1F6B40", "#E6F2EB"),
    "fehler": ("#A3201A", "#FBE9E7"),
    "uebernommen": ("#1F6B40", "#E6F2EB"),
    "hinweis": ("#7A4E00", "#FFF4D6"),
}


def _kanal(wert: int) -> float:
    s = wert / 255
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def _luminanz(farbe: str) -> float:
    r, g, b = (int(farbe[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _kanal(r) + 0.7152 * _kanal(g) + 0.0722 * _kanal(b)


def kontrast(farbe_a: str, farbe_b: str) -> float:
    """Kontrastverhältnis nach WCAG (1 bis 21) zwischen zwei Farben im Format #RRGGBB."""
    hell, dunkel = sorted((_luminanz(farbe_a), _luminanz(farbe_b)), reverse=True)
    return (hell + 0.05) / (dunkel + 0.05)


def akzent_pruefen(akzent: str | None) -> str:
    """Gibt die Farbe normalisiert zurück, wenn sie gültig ist, sonst die Produktfarbe."""
    if akzent and ist_farbcode(akzent):
        return akzent.upper()
    return PRODUKT_AKZENT


def akzent_als_text(akzent: str) -> str:
    """Akzent als Textfarbe auf weißem Blatt: nur wenn lesbar (4,5:1), sonst Tinte. Der Strich unter dem Tab bleibt in der Akzentfarbe."""
    return akzent if kontrast(akzent, BLATT) >= 4.5 else TINTE


def text_auf_akzent(akzent: str) -> str:
    """Schriftfarbe auf einer Fläche in Akzentfarbe: Weiß oder Tinte, je nachdem, was besser lesbar ist."""
    return BLATT if kontrast(akzent, BLATT) >= kontrast(akzent, TINTE) else TINTE


def _schriftfeld_spalten() -> str:
    # Die erste Zelle (Titel) ist breiter als die übrigen. Klassen statt Inline-Stil, weil Streamlit Inline-Stile in HTML-Blöcken nicht überall zulässt.
    return "".join(
        f".sf-n{n}{{grid-template-columns:minmax(0,1.7fr) repeat({n - 1},minmax(0,1fr))}}" for n in range(2, 9)
    )


def baue_css(akzent: str | None = None) -> str:
    farbe = akzent_pruefen(akzent)
    wurzel = (
        ":root{"
        f"--papier:{PAPIER};--blatt:{BLATT};--tinte:{TINTE};--tinte-2:{TINTE_2};--linie:{LINIE};--haar:{HAARLINIE};--stark:{LINIE_STARK};"
        f"--akzent:{farbe};--akzent-text:{akzent_als_text(farbe)};--auf-akzent:{text_auf_akzent(farbe)};--r:2px;"
        "}"
    )
    marken = "".join(
        f".marke-{art}{{color:{text};background:{grund};border-color:{text}}}" for art, (text, grund) in ZUSTAENDE.items()
    )
    return wurzel + _schriftfeld_spalten() + marken + _STATISCH


_STATISCH = """
.stApp{background:var(--papier);color:var(--tinte)}
[data-testid="stHeader"]{background:transparent}
[data-testid="stDecoration"],footer{display:none}
[data-testid="stMainBlockContainer"]{max-width:1280px;padding:28px 40px 72px}
@media (max-width:760px){[data-testid="stMainBlockContainer"]{padding:16px 14px 48px}}
html{scrollbar-color:var(--stark) var(--papier)}
::selection{background:var(--akzent);color:var(--auf-akzent)}
input,textarea{caret-color:var(--akzent)}
:focus-visible{outline:2px solid var(--akzent);outline-offset:2px}
body,.stApp{font-variant-numeric:tabular-nums}
h1,h2,h3,h4{font-family:'Barlow Condensed',Barlow,sans-serif;font-weight:600;letter-spacing:.01em;color:var(--tinte)}

/* Schriftfeld: der Kopf jeder Oberfläche */
/* Streamlit gibt jedem Markdown-Block unten -16px Außenabstand; die eigenen HTML-Blöcke gleichen das mit +16px aus */
.sf{display:grid;border:1.5px solid var(--tinte);background:var(--blatt);margin:0 0 36px}
.sf-zelle{padding:10px 14px 12px;border-right:1px solid var(--linie);min-width:0}
.sf-zelle:last-child{border-right:0}
.sf-label{display:block;font:600 12px/1 'Barlow Condensed',sans-serif;letter-spacing:.09em;text-transform:uppercase;color:var(--tinte-2);margin-bottom:7px}
.sf-wert{display:block;font:600 18px/1.25 Barlow,sans-serif;color:var(--tinte);overflow-wrap:anywhere}
.sf-titel{display:flex;align-items:center;gap:14px}
.sf-titel .sf-wert{font:600 26px/1.15 'Barlow Condensed',sans-serif;letter-spacing:.01em}
.sf-logo{width:46px;height:46px;object-fit:contain;flex:none}
@media (max-width:900px){.sf{grid-template-columns:1fr 1fr!important}.sf-titel{grid-column:1/-1;border-right:0;border-bottom:1px solid var(--linie)}.sf-zelle{border-bottom:1px solid var(--haar)}}

/* Zustandsmarke: Form UND Text, nie nur Farbe */
.marke{display:inline-flex;align-items:center;gap:8px;padding:2px 9px 3px;border:1px solid;border-radius:var(--r);font:600 14px/1.3 'Barlow Condensed',sans-serif;letter-spacing:.06em;text-transform:uppercase}
.marke::before{content:"";width:8px;height:8px;background:currentColor;flex:none}
.marke-offen::before{background:transparent;border:1.5px solid currentColor}
.marke-fehler::before{transform:rotate(45deg)}
.sf-wert .marke{margin-top:1px}

/* Feld: ein beschrifteter Bereich des Blatts */
div[class*="st-key-feld"]{background:var(--blatt);border:1px solid var(--linie);border-radius:var(--r);padding:0 16px 16px;gap:14px}
.fb-kopf{display:flex;align-items:center;gap:12px;padding:12px 16px 10px;border-bottom:1px solid var(--haar);margin:0 -16px 16px}
.fb-nr{font:600 13px/1 'Barlow Condensed',sans-serif;letter-spacing:.06em;background:var(--tinte);color:var(--blatt);padding:4px 7px 3px;border-radius:1px}
.fb-titel{font:600 21px/1.1 'Barlow Condensed',sans-serif;letter-spacing:.01em;color:var(--tinte)}
div[class*="st-key-feld"]:has(.fb-fuss){padding-bottom:0}
.fb-fuss{display:flex;border-top:1px solid var(--haar);margin:0 -16px 16px}
.fb-fuss>div{flex:1;padding:8px 16px 10px;border-right:1px solid var(--haar);min-width:0}
.fb-fuss>div:last-child{border-right:0}
.fb-fuss .sf-wert{font:500 15px/1.3 Barlow,sans-serif}
.fb-kennzahl{font:600 76px/1 'Barlow Condensed',sans-serif;color:var(--tinte);padding:18px 0 14px;margin-bottom:16px;font-variant-numeric:tabular-nums}
div[class*="st-key-lesetext"]{max-width:65ch;padding:8px 0}
div[class*="st-key-lesetext"] p,div[class*="st-key-lesetext"] li{font-size:17px;line-height:1.6}

/* Streamlit-Bedienelemente im Formblatt-Vokabular */
[data-testid="stTabs"] [role="tablist"]{gap:28px;border-bottom:0}
[data-testid="stTabs"] [role="tablist"]::after{height:1px;background:var(--linie)}  /* Streamlits eigene Linie (2px, grau) durch eine Haarlinie ersetzen */
@media (max-width:760px){[data-testid="stTabs"] [role="tablist"]{gap:16px}[data-testid="stTab"] p{font-size:16px;letter-spacing:.01em}}
[data-testid="stTab"]{padding:0 2px 10px;height:auto}
[data-testid="stTab"] p{font:600 18px/1.2 'Barlow Condensed',sans-serif;letter-spacing:.03em;color:var(--tinte-2)}
[data-testid="stTab"][aria-selected="true"] p{color:var(--akzent-text)}
.react-aria-SelectionIndicator{background:var(--akzent)!important;height:3px!important}
button[data-testid="stBaseButton-primary"]{background:var(--akzent);border:1px solid var(--akzent);color:var(--auf-akzent);border-radius:var(--r);transition:filter 150ms}
button[data-testid="stBaseButton-primary"] p{color:var(--auf-akzent);font-weight:600}
button[data-testid="stBaseButton-secondary"]{background:var(--blatt);border:1px solid var(--stark);color:var(--tinte);border-radius:var(--r);transition:filter 150ms}
button[data-testid="stBaseButton-primary"]:hover,button[data-testid="stBaseButton-secondary"]:hover{filter:brightness(.93)}
[data-testid="stWidgetLabel"] p{font:600 15px/1.3 Barlow,sans-serif;color:var(--tinte)}
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"]>div{background:var(--blatt);border-radius:var(--r)}
[data-baseweb="input"]:focus-within,[data-baseweb="textarea"]:focus-within{border-color:var(--akzent);box-shadow:0 0 0 1px var(--akzent)}
[data-testid="stFileUploaderDropzone"]{background:var(--blatt);border:1px dashed var(--stark);border-radius:var(--r)}
[data-testid="stAlert"]{border-radius:var(--r)}
[data-testid="stDataFrame"]{border:1px solid var(--linie);border-radius:var(--r)}
[data-testid="stCaptionContainer"]{opacity:1}  /* Streamlit blendet Bildunterschriften auf 60 % aus: Kontrast dann unter 4,5:1 */
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] *{color:var(--tinte-2)}
[data-testid="stCaptionContainer"] p{font-size:14px;line-height:1.45}
[data-testid="stCaptionContainer"] code,[data-testid="stMarkdownContainer"] code{color:var(--tinte);background:#E8ECEF;font-size:.92em;padding:1px 5px;border-radius:var(--r)}
/* Hauptaktion rechts unten im Feld (Gestaltungsvertrag, erster Bildschirm) */
div[class*="st-key-feld_upload_uebernahme"] [data-testid="stElementContainer"]:has([data-testid="stButton"]),div[class*="st-key-feld_ergebnis"] [data-testid="stElementContainer"]:has([data-testid="stButton"]){align-self:flex-end}
.fb-fuss>div.breit{flex:2.2}
"""


def wende_an(akzent: str | None = None) -> None:
    """Fügt das globale CSS in die aktuelle Streamlit-Seite ein. Aufruf einmal pro Lauf, vor den sichtbaren Elementen."""
    st.markdown(f"<style>{baue_css(akzent)}</style>", unsafe_allow_html=True)
