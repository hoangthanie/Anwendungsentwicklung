"""Platzhalter-Modell für dashboard.json (Output der Pipeline, Input des Runners).

Wird später gegen das gemeinsame Modell von DZ/DB (PSP 3.4) getauscht. Feld- und Typnamen folgen
dem Repository-Doc (Anhang B) und der Spezifikation Kap. 9.3: Chart-Typ plus Farbe, Sortierung, Titel, Größe/Position.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from dashboard_framework.models.spalten import SpaltenDef

ChartTyp = Literal["balken", "linie", "tabelle", "kennzahl"]
Sortierung = Literal["keine", "aufsteigend", "absteigend"]
Breite = Literal["halb", "voll"]

_FARBE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def ist_farbcode(wert: str) -> bool:
    """True, wenn wert genau dem Format #RRGGBB entspricht."""
    return bool(_FARBE.match(wert))


class Chart(BaseModel):
    """Ein Diagramm bzw. eine Kachel: Titel, Typ und das fest hinterlegte SQL (einmalig zur Build-Time erzeugt)."""

    titel: str = Field(min_length=1)
    typ: ChartTyp
    sql: str = Field(min_length=1)
    x: str | None = None  # Spalte der X-Achse; None = erste Ergebnisspalte
    y: str | None = None  # Spalte der Y-Achse; None = zweite Ergebnisspalte
    farbe: str | None = None  # None = erste Firmenfarbe
    sortierung: Sortierung = "keine"
    breite: Breite = "halb"
    beschreibung: str | None = Field(default=None, max_length=1000)  # Berechnung in Worten (aus der KPI); der Runner zeigt sie in der Fußleiste

    @field_validator("farbe")
    @classmethod
    def _farbe_pruefen(cls, wert: str | None) -> str | None:
        if wert is not None and not ist_farbcode(wert):
            raise ValueError(f"Ungültiger Farbcode '{wert}' (erwartet #RRGGBB)")
        return wert


class Branding(BaseModel):
    firmenname: str = ""
    farben: list[str] = Field(default_factory=list)
    logo: str | None = None  # Dateipfad relativ zur dashboard.json

    @field_validator("farben")
    @classmethod
    def _farben_pruefen(cls, werte: list[str]) -> list[str]:
        falsche = [f for f in werte if not ist_farbcode(f)]
        if falsche:
            raise ValueError(f"Ungültige Farbcodes {falsche} (erwartet #RRGGBB)")
        return werte


class DashboardConfig(BaseModel):
    name: str = Field(min_length=1)
    titel: str = Field(min_length=1)
    tabelle: str = Field(min_length=1)
    db_pfad: str = "data/daten.db"  # relativ zur dashboard.json
    spalten: list[SpaltenDef] = Field(default_factory=list)  # Schema der Tabelle; Voraussetzung für den Daten-Upload
    charts: list[Chart] = Field(min_length=1)
    branding: Branding = Field(default_factory=Branding)
    doku: str | None = None  # Text für den Tab "Über dieses Dashboard"

    @model_validator(mode="after")
    def _titel_eindeutig(self) -> "DashboardConfig":
        titel = [c.titel for c in self.charts]
        doppelt = sorted({t for t in titel if titel.count(t) > 1})
        if doppelt:
            raise ValueError(f"Chart-Titel müssen eindeutig sein, doppelt: {doppelt}")
        return self

    @classmethod
    def laden(cls, pfad: str | Path) -> "DashboardConfig":
        return cls.model_validate(json.loads(Path(pfad).read_text(encoding="utf-8")))

    def speichern(self, pfad: str | Path) -> None:
        Path(pfad).write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def json_schema(cls) -> dict:
        """JSON-Schema, z. B. für den Ollama-format-Parameter (Pipeline-Schritt 3)."""
        return cls.model_json_schema()
