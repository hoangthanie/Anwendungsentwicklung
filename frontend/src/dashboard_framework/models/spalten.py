"""Spaltenbeschreibung (Name + Typ), gemeinsam genutzt von Artefakt, Dashboard-Konfiguration und Upload-Prüfung."""
from __future__ import annotations

import difflib
from typing import Literal

from pydantic import BaseModel, Field

SpaltenTyp = Literal["datum", "text", "ganzzahl", "dezimal", "bool"]


class SpaltenDef(BaseModel):
    name: str = Field(min_length=1)
    typ: SpaltenTyp
    beschreibung: str = ""


def aehnliche_spalte(name: str, bekannte: list[str]) -> str | None:
    """Ähnlichster bekannter Spaltenname ("meinten Sie ...?") oder None.

    Groß-/Kleinschreibung wird ignoriert; der Vorschlag hat die Schreibweise aus 'bekannte'.
    """
    klein = {b.lower(): b for b in bekannte}
    treffer = difflib.get_close_matches(name.lower(), list(klein), n=1, cutoff=0.6)
    return klein[treffer[0]] if treffer else None
