"""Schritt 1 (PSP 5.3, US-04): Datenstruktur – CSV prüfen und in SQLite laden, Schema aus der Datenbank lesen, mit dem Artefakt abgleichen.

Deterministisch, ohne Sprachmodell (Spezifikation 3.1, ADR 0007). Die Datenbank ist die Wahrheit, das Artefakt ist behauptetes Wissen.

Ablauf:
1. lade_daten:  CSV mit denselben Regeln prüfen und umwandeln wie der Upload im Dashboard (gemeinsame Bausteine aus
                dashboard_framework.runner.framework_lib), dann in eine neue SQLite-Datei laden.
2. lese_schema: Spalten, SQLite-Typ und bis zu drei Beispielwerte je Spalte nur lesend aus der Datenbank holen (US-04.1, US-04.3).
3. abgleich:    Artefakt und Datenbank vergleichen; jede Abweichung wird eine verständliche Meldung (US-04.2).
ausfuehren() verbindet alles und bricht bei der ersten Stufe mit Meldungen ab (Fail-Fast). Ein erneuter Versuch ist hier
sinnlos, weil der Schritt bei gleicher Eingabe immer gleich entscheidet.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from dashboard_framework.models.artefakt import Artefakt
from dashboard_framework.models.spalten import aehnliche_spalte
from dashboard_framework.runner.framework_lib import (
    UploadFehler,
    bezeichner_zitieren,
    lese_csv,
    uebernehmen,
    validate_against_schema,
)
from dashboard_framework.runner.sicherheit import verbinde_nur_lesend

# Typ im Artefakt -> SQLite-Typ der Tabelle (wie frontend/tools/baue_lokal.py)
SQL_TYPEN = {"datum": "TEXT", "text": "TEXT", "ganzzahl": "INTEGER", "dezimal": "REAL", "bool": "INTEGER"}
MAX_BEISPIELE = 3  # US-04.3: Token sparen
MAX_ZEICHEN = 50  # lange Texte in Beispielwerten werden gekürzt


class SchemaFehler(ValueError):
    """Schritt 1 kann nicht fortfahren. 'meldungen' enthält alle Gründe, jeder verständlich formuliert."""

    def __init__(self, meldungen: list[str] | str):
        self.meldungen = [meldungen] if isinstance(meldungen, str) else list(meldungen)
        super().__init__("; ".join(self.meldungen))


@dataclass(frozen=True)
class SpaltenInfo:
    """Eine Spalte, wie sie tatsächlich in der Datenbank steht."""

    name: str
    typ: str  # SQLite-Typ laut Tabellendefinition, z. B. TEXT, INTEGER, REAL
    beispiele: tuple = ()

    def als_dict(self) -> dict:
        return {"name": self.name, "typ": self.typ, "beispiele": list(self.beispiele)}


def lade_daten(artefakt: Artefakt, csv_pfad: str | Path, db_pfad: str | Path, ueberschreiben: bool = False) -> int:
    """Prüft die CSV gegen die Spalten des Artefakts und lädt sie in eine neue SQLite-Datei. Gibt die Zeilenzahl zurück.

    Eine vorhandene Datenbank wird nur mit ueberschreiben=True ersetzt: Schritt 1 baut die Datenbank für einen
    Pipeline-Lauf neu und darf nie versehentlich eine bestehende Dashboard-Datenbank löschen (US-13).
    """
    csv = Path(csv_pfad)
    db = Path(db_pfad)
    if db.exists() and not ueberschreiben:
        raise SchemaFehler(f"Die Datenbank {db.name} existiert bereits und wird nicht überschrieben")
    try:
        daten = validate_against_schema(lese_csv(csv.read_bytes()), artefakt.spalten)
    except FileNotFoundError:
        raise SchemaFehler(f"Datendatei nicht gefunden: {csv.name}") from None
    except UploadFehler as fehler:
        raise SchemaFehler(fehler.meldungen) from None

    db.parent.mkdir(parents=True, exist_ok=True)
    db.unlink(missing_ok=True)
    spalten = ", ".join(f"{bezeichner_zitieren(s.name)} {SQL_TYPEN[s.typ]}" for s in artefakt.spalten)
    verbindung = sqlite3.connect(db)
    try:
        verbindung.execute(f"CREATE TABLE {bezeichner_zitieren(artefakt.tabelle)} ({spalten})")
        verbindung.commit()
    finally:
        verbindung.close()
    return uebernehmen(daten, db, artefakt.tabelle)


def _kuerzen(wert: object) -> object:
    if isinstance(wert, str) and len(wert) > MAX_ZEICHEN:
        return wert[: MAX_ZEICHEN - 1] + "…"
    return wert


def lese_schema(db_pfad: str | Path, tabelle: str) -> list[SpaltenInfo]:
    """Liest Spalten in Tabellenreihenfolge mit SQLite-Typ und bis zu drei Beispielwerten (verschieden, ohne leere, sortiert)."""
    if not Path(db_pfad).exists():
        raise SchemaFehler(f"Datenbank nicht gefunden: {Path(db_pfad).name}")
    verbindung = verbinde_nur_lesend(db_pfad)
    try:
        vorhanden = verbindung.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (tabelle,)
        ).fetchone()
        if not vorhanden:
            raise SchemaFehler(f"Die Tabelle '{tabelle}' existiert in der Datenbank nicht")
        t = bezeichner_zitieren(tabelle)
        schema = []
        for _, name, typ, *_ in verbindung.execute(f"PRAGMA table_info({t})").fetchall():
            s = bezeichner_zitieren(name)
            werte = verbindung.execute(
                f"SELECT DISTINCT {s} FROM {t} WHERE {s} IS NOT NULL ORDER BY {s} LIMIT ?", (MAX_BEISPIELE,)
            ).fetchall()
            schema.append(SpaltenInfo(name=name, typ=typ.upper(), beispiele=tuple(_kuerzen(w[0]) for w in werte)))
        return schema
    finally:
        verbindung.close()


def abgleich(artefakt: Artefakt, schema: list[SpaltenInfo]) -> list[str]:
    """Vergleicht Artefakt und Datenbank. Leere Liste = alles passt; sonst eine verständliche Meldung je Abweichung."""
    ist = {s.name: s.typ for s in schema}
    soll = [s.name for s in artefakt.spalten]
    meldungen: list[str] = []
    for spalte in artefakt.spalten:
        if spalte.name not in ist:
            vorschlag = aehnliche_spalte(spalte.name, [n for n in ist if n not in soll])
            hinweis = f" – meinten Sie `{vorschlag}`?" if vorschlag else ""
            meldungen.append(f"Spalte '{spalte.name}' aus dem Artefakt fehlt in der Datenbank{hinweis}")
        elif ist[spalte.name] != SQL_TYPEN[spalte.typ]:
            meldungen.append(
                f"Spalte '{spalte.name}' hat in der Datenbank den Typ {ist[spalte.name]}, "
                f"laut Artefakt ({spalte.typ}) wäre {SQL_TYPEN[spalte.typ]} richtig"
            )
    for name in ist:
        if name not in soll:
            meldungen.append(f"Spalte '{name}' steht in der Datenbank, aber nicht im Artefakt")
    return meldungen


def ausfuehren(artefakt: Artefakt, csv_pfad: str | Path, db_pfad: str | Path, ueberschreiben: bool = False) -> list[SpaltenInfo]:
    """Schritt 1 komplett: laden, Schema lesen, abgleichen. Liefert das bestätigte Schema für Schritt 2 oder wirft SchemaFehler."""
    lade_daten(artefakt, csv_pfad, db_pfad, ueberschreiben=ueberschreiben)
    schema = lese_schema(db_pfad, artefakt.tabelle)
    meldungen = abgleich(artefakt, schema)
    if meldungen:
        raise SchemaFehler(meldungen)
    return schema
