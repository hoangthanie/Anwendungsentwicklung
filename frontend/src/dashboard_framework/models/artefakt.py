"""Artefakt-Modell (Platzhalter bis zur Abstimmung mit DZ, PSP 3.3): der gemeinsame Vertrag für artefakt.yaml.

Das Artefakt ist das ausgefüllte Formular des Anwenders. Alles, was die Pipeline später braucht, steht hier: Ziel, Publikum, Datenstruktur, KPIs, Branding.
Fail-Fast (US-02): Fehler werden gefunden, BEVOR das Sprachmodell läuft, vor allem KPIs, die eine nicht existierende Spalte verwenden.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from dashboard_framework.models.dashboard_config import Branding
from dashboard_framework.models.spalten import SpaltenDef, aehnliche_spalte, ist_bezeichner

MAX_YAML_BYTES = 1024 * 1024
MAX_KPIS = 12  # mehr KPIs sprengen das Kontextfenster des lokalen Modells und die Übersicht des Dashboards

_NAME = re.compile(r"^[a-z][a-z0-9_]{0,39}$")
_ANKER = re.compile(r"`([^`]+)`")
# Anwender schreiben Spaltennamen in Anführungszeichen ("Name" oder „Name“); gespeichert werden sie als `Name` (Spaltenanker der Pipeline).
_ZITAT = re.compile(r'["„“”]([^"„“”`]+)["„“”]')
_ZITATZEICHEN = re.compile(r'["„“”]')


def anfuehrungszeichen_zu_backticks(text: str) -> str:
    """"Location" und „Location“ -> `Location`. Nicht gepaarte Zeichen bleiben stehen und werden von der Prüfung gemeldet."""
    return _ZITAT.sub(r"`\1`", text)


def backticks_zu_anfuehrungszeichen(text: str) -> str:
    """`Location` -> "Location" (Anzeige im Formular)."""
    return _ANKER.sub(r'"\1"', text)


class ArtefaktFehler(ValueError):
    """Das Artefakt ist nicht gültig. 'meldungen' enthält alle Gründe, jeder verständlich formuliert."""

    def __init__(self, meldungen: list[str] | str):
        self.meldungen = [meldungen] if isinstance(meldungen, str) else list(meldungen)
        super().__init__("; ".join(self.meldungen))


class Kpi(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    beschreibung: str = Field(min_length=1, max_length=1000)

    @field_validator("beschreibung")
    @classmethod
    def _zitate_zu_ankern(cls, wert: str) -> str:
        return anfuehrungszeichen_zu_backticks(wert)

    @property
    def referenzierte_spalten(self) -> list[str]:
        """Spaltennamen, die in der Beschreibung zwischen Backticks stehen (in Reihenfolge, ohne Doppelte)."""
        return list(dict.fromkeys(_ANKER.findall(self.beschreibung)))


class Artefakt(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str
    titel: str = Field(min_length=1, max_length=80)
    ziel: str = Field(min_length=1, max_length=500)
    publikum: str = Field(min_length=1, max_length=200)
    tabelle: str
    spalten: list[SpaltenDef] = Field(min_length=1, max_length=100)
    kpis: list[Kpi] = Field(min_length=1, max_length=MAX_KPIS)
    branding: Branding = Field(default_factory=Branding)

    @field_validator("name")
    @classmethod
    def _name_pruefen(cls, wert: str) -> str:
        # 'name' wird später Ordner- und Dateiname (artefakte/<name>/): deshalb nur harmlose Zeichen.
        if not wert:
            raise ValueError("Pflichtfeld ist leer: name")  # gleiche Meldung wie bei den anderen Pflichtfeldern
        if not _NAME.match(wert):
            raise ValueError(
                "name: erlaubt sind Kleinbuchstaben, Ziffern und _ (muss mit einem Buchstaben beginnen, höchstens 40 Zeichen)"
            )
        return wert

    @field_validator("tabelle")
    @classmethod
    def _tabelle_pruefen(cls, wert: str) -> str:
        # 'tabelle' wird in SQL eingesetzt: nur ein einfacher Bezeichner.
        if not wert:
            raise ValueError("Pflichtfeld ist leer: tabelle")
        if not ist_bezeichner(wert):
            raise ValueError(
                "tabelle: erlaubt sind Buchstaben, Ziffern und _ (keine Leerzeichen, nicht mit einer Ziffer beginnen)"
            )
        return wert

    @model_validator(mode="after")
    def _zusammenhaenge_pruefen(self) -> "Artefakt":
        meldungen: list[str] = []

        namen = [s.name for s in self.spalten]
        sichtbar: dict[str, str] = {}
        for n in namen:
            if n.lower() in sichtbar:
                meldungen.append(
                    f"Spalte '{n}' kommt doppelt vor"
                    + ("" if sichtbar[n.lower()] == n else f" (Groß-/Kleinschreibung zählt in SQLite nicht: '{sichtbar[n.lower()]}')")
                )
            sichtbar.setdefault(n.lower(), n)

        kpi_namen = [k.name for k in self.kpis]
        for n in dict.fromkeys(kpi_namen):
            if kpi_namen.count(n) > 1:
                meldungen.append(f"KPI '{n}' kommt doppelt vor")

        for kpi in self.kpis:
            if kpi.beschreibung.count("`") % 2 == 1 or _ZITATZEICHEN.search(kpi.beschreibung):
                # ein Zeichen ohne Gegenstück: sonst würde der zugehörige Spaltenname stillschweigend überlesen
                meldungen.append(
                    f"KPI '{kpi.name}': Anführungszeichen nicht paarig – jeder Spaltenname braucht ein öffnendes und ein schließendes Anführungszeichen"
                )
                continue
            anker = kpi.referenzierte_spalten
            if not anker:
                meldungen.append(
                    f"KPI '{kpi.name}' referenziert keine Spalte – bitte Spaltennamen in Anführungszeichen setzen "
                    '(z. B. "spalte") oder die Spalte unter dem Eingabefeld anklicken'
                )
            for spalte in anker:
                if spalte not in namen:
                    vorschlag = aehnliche_spalte(spalte, namen)
                    hinweis = f" – meinten Sie `{vorschlag}`?" if vorschlag else ""
                    meldungen.append(f"KPI '{kpi.name}': unbekannte Spalte: {spalte}{hinweis}")

        if meldungen:
            raise ValueError("\n".join(meldungen))
        return self

    @property
    def spalten_ohne_beschreibung(self) -> list[str]:
        """Spalten ohne Beschreibung. Das ist KEIN Fehler (Entscheidung: Hinweis statt Pflicht), aber das Sprachmodell muss dann raten,
        was die Spalte bedeutet; aus den Werten lässt sich das nicht zuverlässig ableiten (Spezifikation 3.1)."""
        return [s.name for s in self.spalten if not s.beschreibung.strip()]

    @property
    def benoetigte_spalten(self) -> list[str]:
        """Alle von KPIs verwendeten Spalten (ohne Doppelte, in Reihenfolge des Auftretens)."""
        return list(dict.fromkeys(s for k in self.kpis for s in k.referenzierte_spalten))

    # --- Laden und Speichern -------------------------------------------------------------------------

    @classmethod
    def aus_dict(cls, daten: object) -> "Artefakt":
        if not isinstance(daten, dict):
            raise ArtefaktFehler("Das Artefakt muss aus Feldern bestehen (name, titel, ziel, ...)")
        try:
            return cls.model_validate(daten)
        except ValidationError as fehler:
            raise ArtefaktFehler(_uebersetze(fehler)) from None

    @classmethod
    def aus_yaml(cls, pfad: str | Path) -> "Artefakt":
        datei = Path(pfad)
        try:
            if datei.stat().st_size > MAX_YAML_BYTES:
                raise ArtefaktFehler("Die Artefakt-Datei ist größer als 1 MB")
            text = datei.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise ArtefaktFehler(f"Datei nicht gefunden: {datei.name}") from None
        except UnicodeDecodeError:
            raise ArtefaktFehler("Die Artefakt-Datei ist nicht UTF-8-codiert") from None
        try:
            daten = yaml.safe_load(text)  # safe_load: erzeugt nur einfache Daten, nie Python-Objekte (yaml.load wäre unsicher)
        except yaml.YAMLError as fehler:
            marke = getattr(fehler, "problem_mark", None)
            ort = f" (Zeile {marke.line + 1})" if marke else ""
            raise ArtefaktFehler(f"Die Datei ist kein gültiges YAML{ort}") from None
        return cls.aus_dict(daten)

    def zu_yaml(self) -> str:
        return yaml.safe_dump(self.model_dump(exclude_none=True), allow_unicode=True, sort_keys=False)

    def speichern(self, pfad: str | Path) -> None:
        ziel = Path(pfad)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(self.zu_yaml(), encoding="utf-8")


def _feldname(ort: tuple) -> str:
    """('spalten', 0, 'name') -> 'spalten[1].name' (Zählung ab 1, wie ein Mensch zählt)."""
    text = ""
    for teil in ort:
        if isinstance(teil, int):
            text += f"[{teil + 1}]"
        else:
            text += ("." if text else "") + str(teil)
    return text


def _uebersetze(fehler: ValidationError) -> list[str]:
    """Wandelt die (englischen) Pydantic-Fehler in verständliche deutsche Meldungen um."""
    meldungen: list[str] = []
    for f in fehler.errors():
        feld = _feldname(f["loc"]) or "Artefakt"
        art = f["type"]
        ctx = f.get("ctx", {})
        if art == "missing":
            text = f"Pflichtfeld fehlt: {feld}"
        elif art == "string_too_short":
            text = f"Pflichtfeld ist leer: {feld}"
        elif art == "string_too_long":
            text = f"{feld}: zu lang (höchstens {ctx.get('max_length')} Zeichen)"
        elif art == "too_short":
            text = f"{feld}: mindestens {ctx.get('min_length')} Eintrag erforderlich"
        elif art == "too_long":
            text = f"{feld}: höchstens {ctx.get('max_length')} Einträge erlaubt"
        elif art == "extra_forbidden":
            text = f"Unbekanntes Feld: {feld}"
        elif art == "literal_error":
            text = f"{feld}: ungültiger Wert '{f.get('input')}' (erlaubt: {ctx.get('expected')})"
        elif art == "value_error":
            text = str(ctx.get("error", f["msg"]))  # unsere eigenen deutschen Texte, ggf. mehrzeilig
            meldungen.extend(zeile for zeile in text.split("\n") if zeile)
            continue
        else:
            text = f"{feld}: ungültige Angabe"
        meldungen.append(text)
    return meldungen
