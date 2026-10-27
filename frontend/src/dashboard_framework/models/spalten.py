"""Spaltenbeschreibung (Name + Typ), gemeinsam genutzt von Artefakt, Dashboard-Konfiguration und Upload-Prüfung."""
from __future__ import annotations

import difflib
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SpaltenTyp = Literal["datum", "text", "ganzzahl", "dezimal", "bool"]

# Buchstabe oder _ am Anfang, danach Buchstaben/Ziffern/_ (Unicode erlaubt, z. B. Umlaute). Keine Leerzeichen, keine Sonderzeichen.
# Spaltennamen landen später in SQL-Abfragen und in KPI-Texten zwischen Backticks; diese strenge Form verhindert Mehrdeutigkeit und SQL-Einschleusung.
BEZEICHNER = re.compile(r"^[^\W\d]\w{0,63}$")


def ist_bezeichner(wert: str) -> bool:
    return bool(BEZEICHNER.match(wert))


class SpaltenDef(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1)
    typ: SpaltenTyp
    beschreibung: str = ""

    @field_validator("name")
    @classmethod
    def _name_pruefen(cls, wert: str) -> str:
        if not ist_bezeichner(wert):
            raise ValueError(
                f"Spaltenname '{wert}' ist ungültig: erlaubt sind Buchstaben, Ziffern und _ "
                "(keine Leerzeichen, nicht mit einer Ziffer beginnen, höchstens 64 Zeichen). "
                "Bitte die Spalte auch in der Datendatei so umbenennen."
            )
        return wert


def aehnliche_spalte(name: str, bekannte: list[str]) -> str | None:
    """Ähnlichster bekannter Spaltenname ("meinten Sie ...?") oder None.

    Groß-/Kleinschreibung wird ignoriert; der Vorschlag hat die Schreibweise aus 'bekannte'.
    """
    klein = {b.lower(): b for b in bekannte}
    treffer = difflib.get_close_matches(name.lower(), list(klein), n=1, cutoff=0.6)
    return klein[treffer[0]] if treffer else None
