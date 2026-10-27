"""Nur lesender Datenzugriff im Runner (US-09.2, Risiko R14).

Zwei unabhängige Schichten ("Defense in Depth"):
1. pruefe_nur_lesend: Textprüfung des SQL (nur ein SELECT/WITH-Statement, keine Schreib-Schlüsselwörter).
2. verbinde_nur_lesend: Die Datenbankverbindung selbst ist schreibgeschützt. Selbst wenn Schicht 1 etwas übersieht,
   lehnt SQLite jeden Schreibversuch ab.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path


class UnsicheresSql(ValueError):
    """SQL ist nicht erlaubt (schreibend, mehrfach, leer)."""


_VERBOTEN = (
    "insert", "update", "delete", "drop", "alter", "create", "attach", "detach",
    "pragma", "vacuum", "reindex", "truncate", "grant", "revoke",
)
_VERBOTEN_RE = re.compile(r"\b(" + "|".join(_VERBOTEN) + r")\b", re.IGNORECASE)
_STRING_RE = re.compile(r"'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\"")
_KOMMENTAR_RE = re.compile(r"--[^\n]*|/\*.*?\*/", re.DOTALL)


def _bereinigen(sql: str) -> str:
    """Entfernt Kommentare und String-Inhalte, damit sie weder täuschen noch falschen Alarm auslösen."""
    ohne_strings = _STRING_RE.sub("''", sql)
    return _KOMMENTAR_RE.sub(" ", ohne_strings).strip()


def pruefe_nur_lesend(sql: str) -> str:
    """Gibt das SQL unverändert zurück, wenn es erlaubt ist; sonst UnsicheresSql."""
    if not sql or not sql.strip():
        raise UnsicheresSql("Leeres SQL")
    kern = _bereinigen(sql).rstrip(";").strip()
    if not kern:
        raise UnsicheresSql("Leeres SQL")
    if ";" in kern:
        raise UnsicheresSql("Nur genau ein Statement erlaubt")
    if not re.match(r"(select|with)\b", kern, re.IGNORECASE):
        raise UnsicheresSql("Nur SELECT-Abfragen sind erlaubt")
    treffer = _VERBOTEN_RE.search(kern)
    if treffer:
        raise UnsicheresSql(f"Schreibender Befehl nicht erlaubt: {treffer.group(1).upper()}")
    return sql


def verbinde_nur_lesend(db_pfad: str | Path) -> sqlite3.Connection:
    """Öffnet die SQLite-Datei schreibgeschützt (mode=ro). Existiert sie nicht, gibt es einen Fehler statt einer neuen leeren DB."""
    pfad = Path(db_pfad).resolve()
    verbindung = sqlite3.connect(f"{pfad.as_uri()}?mode=ro", uri=True)
    verbindung.execute("PRAGMA query_only = ON")
    return verbindung
