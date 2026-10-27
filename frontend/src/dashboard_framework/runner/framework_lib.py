"""Upload neuer Daten (US-10): CSV lesen, gegen das Schema prüfen, an die Tabelle anhängen.

Geteilte, von Hand geschriebene Bibliothek (nicht generiert): Das Schema kommt als Parameter, deshalb funktioniert sie für jedes Dashboard.
Reihenfolge ist Absicht: erst vollständig prüfen und umwandeln (validate_against_schema), dann schreiben (uebernehmen).
Fehlerhafte Daten erreichen die Datenbank nie.
"""
from __future__ import annotations

import io
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from dashboard_framework.models.spalten import SpaltenDef, aehnliche_spalte
from dashboard_framework.runner.sicherheit import verbinde_nur_lesend

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # Größenlimit gegen versehentlich riesige oder missbräuchliche Dateien (Risiko R15)

_WAHR = {"true", "wahr", "ja", "yes", "y", "1"}
_FALSCH = {"false", "falsch", "nein", "no", "n", "0"}


class UploadFehler(ValueError):
    """Upload ist nicht übernehmbar. 'meldungen' enthält alle Gründe, jeder verständlich formuliert."""

    def __init__(self, meldungen: list[str] | str):
        self.meldungen = [meldungen] if isinstance(meldungen, str) else list(meldungen)
        super().__init__("; ".join(self.meldungen))


def lese_csv(inhalt: bytes) -> pd.DataFrame:
    """CSV-Bytes in einen DataFrame lesen. Alles wird zunächst als Text gelesen; die Typen bestimmt allein das Schema."""
    if len(inhalt) > MAX_UPLOAD_BYTES:
        raise UploadFehler(f"Die Datei ist größer als {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    if not inhalt.strip():
        raise UploadFehler("Die Datei ist leer")
    try:
        text = inhalt.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise UploadFehler("Die Datei ist nicht UTF-8-codiert (in Excel als 'CSV UTF-8' speichern)") from None
    try:
        # sep=None: Trennzeichen (Komma oder Semikolon, z. B. aus deutschem Excel) wird automatisch erkannt
        df = pd.read_csv(io.StringIO(text), sep=None, engine="python", dtype=str, keep_default_na=False)
    except Exception:
        raise UploadFehler("Die Datei konnte nicht als CSV gelesen werden") from None
    df.columns = [str(spalte).strip() for spalte in df.columns]
    return df


def _text_bereinigen(serie: pd.Series) -> pd.Series:
    return serie.where(serie.notna(), "").astype(str).str.strip()


def konvertiere_spalte(serie: pd.Series, typ: str) -> pd.Series:
    """Wandelt eine Spalte in den Zieltyp um; wirft ValueError, wenn ein Wert nicht passt."""
    s = _text_bereinigen(serie)
    if typ == "text":
        return s.where(s != "", None)
    if (s == "").any():
        raise ValueError("leere Werte")
    if typ == "ganzzahl":
        zahl = pd.to_numeric(s, errors="raise")
        if (zahl % 1 != 0).any() or not np.isfinite(zahl.astype(float)).all():
            raise ValueError("keine ganze Zahl")
        return zahl.astype("int64")
    if typ == "dezimal":
        # "1,5" (deutsch) wird zu 1.5, sofern kein Punkt vorkommt; "1.234,5" bleibt mehrdeutig und wird abgelehnt
        s = s.where(s.str.contains(".", regex=False), s.str.replace(",", ".", regex=False))
        zahl = pd.to_numeric(s, errors="raise").astype(float)
        if not np.isfinite(zahl).all():
            raise ValueError("keine endliche Zahl")
        return zahl
    if typ == "datum":
        try:
            datum = pd.to_datetime(s, format="ISO8601", errors="raise")
        except ValueError:
            datum = pd.to_datetime(s, format="%d.%m.%Y", errors="raise")
        return datum.dt.strftime("%Y-%m-%d")  # als Text in ISO-Form: sortierbar und mit strftime in SQLite nutzbar
    if typ == "bool":
        klein = s.str.lower()
        if not klein.isin(_WAHR | _FALSCH).all():
            raise ValueError("kein Wahrheitswert")
        return klein.isin(_WAHR).astype("int64")
    raise ValueError(f"unbekannter Typ {typ}")


def _erster_fehlerwert(serie: pd.Series, typ: str) -> str:
    for position, wert in enumerate(serie.tolist()):
        try:
            konvertiere_spalte(pd.Series([wert]), typ)
        except ValueError:
            return f"'{wert}' in Zeile {position + 2}"  # +2: Kopfzeile und 1-basierte Zählung wie in Excel
    return "?"


def validate_against_schema(df: pd.DataFrame, schema: list[SpaltenDef | dict]) -> pd.DataFrame:
    """Prüft df gegen das Schema und gibt eine bereinigte Kopie in Schema-Reihenfolge und Zieltypen zurück.

    Sammelt alle Fehler und meldet sie gemeinsam (UploadFehler), statt beim ersten aufzugeben: Der Anwender sieht, was er korrigieren muss.
    """
    spalten = [s if isinstance(s, SpaltenDef) else SpaltenDef(**s) for s in schema]
    soll = [s.name for s in spalten]
    ist = list(df.columns)
    meldungen: list[str] = []

    fehlend = [n for n in soll if n not in ist]
    if fehlend:
        meldungen.append("fehlende Spalte(n): " + ", ".join(fehlend))
    unbekannt = [n for n in ist if n not in soll]
    for name in unbekannt:
        vorschlag = aehnliche_spalte(name, fehlend or soll)
        hinweis = f" – meinten Sie `{vorschlag}`?" if vorschlag else ""
        meldungen.append(f"unbekannte Spalte: {name}{hinweis}")
    if len(df) == 0:
        meldungen.append("Die Datei enthält keine Datenzeilen")

    ergebnis: dict[str, pd.Series] = {}
    for spalte in spalten:
        if spalte.name not in ist or len(df) == 0:
            continue
        try:
            ergebnis[spalte.name] = konvertiere_spalte(df[spalte.name], spalte.typ)
        except ValueError as grund:
            # Bewusst nicht str(grund) ausgeben: pandas-Texte sind englisch und für Fachanwender unverständlich.
            if str(grund) == "leere Werte":
                meldungen.append(f"Spalte {spalte.name} ist nicht vom Typ {spalte.typ}: leere Werte sind hier nicht erlaubt")
            else:
                beispiel = _erster_fehlerwert(df[spalte.name], spalte.typ)
                meldungen.append(f"Spalte {spalte.name} ist nicht vom Typ {spalte.typ} (z. B. {beispiel})")
    if meldungen:
        raise UploadFehler(meldungen)
    return pd.DataFrame(ergebnis, columns=soll)


def bezeichner_zitieren(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _tabellenspalten(verbindung: sqlite3.Connection, tabelle: str) -> list[str]:
    vorhanden = verbindung.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (tabelle,)).fetchone()
    if not vorhanden:
        raise UploadFehler(f"Die Tabelle '{tabelle}' existiert in der Datenbank nicht")
    return [zeile[1] for zeile in verbindung.execute(f"PRAGMA table_info({bezeichner_zitieren(tabelle)})")]


def zaehle_vorhandene_zeilen(df: pd.DataFrame, db_pfad: str | Path, tabelle: str) -> int:
    """Wie viele Zeilen von df gibt es (vollständig identisch) schon in der Tabelle? Dient der Warnung vor Doppel-Uploads."""
    verbindung = verbinde_nur_lesend(db_pfad)
    try:
        spalten = _tabellenspalten(verbindung, tabelle)
        if not set(df.columns) <= set(spalten):
            return 0
        auswahl = ", ".join(bezeichner_zitieren(c) for c in df.columns)
        bestehend = pd.read_sql_query(f"SELECT DISTINCT {auswahl} FROM {bezeichner_zitieren(tabelle)}", verbindung)
    finally:
        verbindung.close()
    if bestehend.empty:
        return 0
    markiert = df.merge(bestehend, how="left", on=list(df.columns), indicator=True)
    return int((markiert["_merge"] == "both").sum())


def _python_wert(wert):
    if wert is None or (isinstance(wert, float) and np.isnan(wert)):
        return None
    return wert.item() if hasattr(wert, "item") else wert


def uebernehmen(df: pd.DataFrame, db_pfad: str | Path, tabelle: str) -> int:
    """Hängt die (bereits geprüften) Zeilen an die bestehende Tabelle an und gibt die Anzahl zurück.

    Atomar: Alle Zeilen werden in einer Transaktion geschrieben, bei einem Fehler wird nichts übernommen.
    Die Datenbank wird nur geöffnet, nie neu angelegt (mode=rw), und die Tabelle muss schon existieren.
    """
    pfad = Path(db_pfad).resolve()
    verbindung = sqlite3.connect(f"{pfad.as_uri()}?mode=rw", uri=True, timeout=10)
    try:
        spalten = _tabellenspalten(verbindung, tabelle)
        fremd = [c for c in df.columns if c not in spalten]
        if fremd:
            raise UploadFehler("Spalten nicht in der Tabelle vorhanden: " + ", ".join(fremd))
        sql = (
            f"INSERT INTO {bezeichner_zitieren(tabelle)} ({', '.join(bezeichner_zitieren(c) for c in df.columns)}) "
            f"VALUES ({', '.join('?' for _ in df.columns)})"
        )
        zeilen = [tuple(_python_wert(w) for w in zeile) for zeile in df.itertuples(index=False, name=None)]
        with verbindung:  # Transaktion: commit bei Erfolg, rollback bei Ausnahme
            verbindung.executemany(sql, zeilen)
    finally:
        verbindung.close()
    return len(df)
