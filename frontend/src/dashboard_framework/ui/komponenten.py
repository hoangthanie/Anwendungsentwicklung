"""Bausteine als HTML-Text: Schriftfeld, Feldkopf, Fußleiste, Zustandsmarke, Kennzahl.

Alle Texte von außen (Kundenname, Titel, Dateinamen) werden mit html.escape entschärft, bevor sie in HTML stehen.
Das HTML steht bewusst in EINER Zeile ohne Einrückung: Streamlit liest Markdown, und eingerückte oder durch Leerzeilen getrennte Zeilen würden als Codeblock oder neuer Textabschnitt missverstanden.
"""
from __future__ import annotations

import html
import re
from collections.abc import Sequence

from dashboard_framework.ui.theme import ZUSTAENDE

_LOGO_URI = re.compile(r"^data:image/(png|jpeg);base64,[A-Za-z0-9+/=]+$")
MAX_ZELLEN = 8

Zelle = tuple[str, str] | tuple[str, str, str]  # (Beschriftung, Wert) oder (Beschriftung, Wert, Zustandsart)


def esc(text: object) -> str:
    return html.escape(str(text), quote=True)


def zahl(wert: int) -> str:
    """Ganze Zahl mit Punkt als Tausendertrenner (1234 -> 1.234), wie in den Diagrammen."""
    return f"{int(wert):,}".replace(",", ".")


def marke(text: str, art: str) -> str:
    """Zustandsmarke mit Form und Text. art: offen, gueltig, fehler, uebernommen, hinweis."""
    if art not in ZUSTAENDE:
        raise ValueError(f"Unbekannte Zustandsart '{art}'")
    return f'<span class="marke marke-{art}">{esc(text)}</span>'


def schriftfeld(titel: str, zellen: Sequence[Zelle], logo_uri: str | None = None) -> str:
    """Kopfzeile der Oberfläche, nach dem Vorbild eines Zeichnungs-Schriftfelds.

    Die erste Zelle trägt den Titel (ohne Beschriftung darüber) und optional das Logo; weitere Zellen haben Beschriftung und Wert.
    """
    if len(zellen) + 1 > MAX_ZELLEN:
        raise ValueError(f"Höchstens {MAX_ZELLEN} Zellen im Schriftfeld")
    logo = ""
    if logo_uri:
        if not _LOGO_URI.match(logo_uri):
            raise ValueError("Logo muss als data:image/png oder data:image/jpeg (base64) übergeben werden")
        logo = f'<img class="sf-logo" alt="" src="{logo_uri}">'
    teile = [f'<div class="sf sf-n{len(zellen) + 1}">', f'<div class="sf-zelle sf-titel">{logo}<span class="sf-wert">{esc(titel)}</span></div>']
    for zelle in zellen:
        label, wert = zelle[0], zelle[1]
        inhalt = marke(wert, zelle[2]) if len(zelle) == 3 else esc(wert)
        teile.append(f'<div class="sf-zelle"><span class="sf-label">{esc(label)}</span><span class="sf-wert">{inhalt}</span></div>')
    teile.append("</div>")
    return "".join(teile)


def feldkopf(titel: str, nummer: int | None = None) -> str:
    """Titelzeile eines Felds, optional mit Feldnummer (z. B. zum Nachfragen: "Feld 3 stimmt nicht")."""
    nr = f'<span class="fb-nr">{int(nummer)}</span>' if nummer is not None else ""
    return f'<div class="fb-kopf">{nr}<span class="fb-titel">{esc(titel)}</span></div>'


def fussleiste(paare: Sequence[tuple[str, str]], breit_erste: bool = False) -> str:
    """Fußleiste eines Felds. breit_erste: die erste Zelle (z. B. die Berechnung) bekommt mehr Platz, weil ihr Text länger ist."""
    zellen = []
    for i, (label, wert) in enumerate(paare):
        klasse = ' class="breit"' if breit_erste and i == 0 else ""
        zellen.append(f'<div{klasse}><span class="sf-label">{esc(label)}</span><span class="sf-wert">{esc(wert)}</span></div>')
    return f'<div class="fb-fuss">{"".join(zellen)}</div>'


def kennzahl(wert: str) -> str:
    return f'<div class="fb-kennzahl">{esc(wert)}</div>'
