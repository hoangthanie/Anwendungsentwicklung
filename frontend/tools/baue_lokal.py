"""Entwicklungsskript: baut aus Artefakt + CSV ein lokales Dashboard unter ausgabe/<name>/ (daten.db, dashboard.json, Logo).

Es ersetzt NICHT die Pipeline (David, PSP 5.x), sondern lässt das Frontend schon jetzt mit eigenen Daten sehen:
  Schritt 1 (Schema/Daten laden): Daten werden mit dem Schema des Artefakts geprüft und umgewandelt und in SQLite geladen.
  Schritt 2 (SQL je KPI): kommt aus einer Datei (--sql), geschrieben von Hand bzw. von Claude. Jedes SQL wird auf "nur lesend" geprüft und ausgeführt.
  Schritt 3 (Dashboard-Konfiguration): derselbe Code wie in der Pipeline (harness/dashboard.py). Die Wahl des "Modells" kommt aus einer Datei (--wahl).

Aufruf (im Ordner frontend):
  python tools/baue_lokal.py artefakte/<name> <daten.csv>                      # nur laden und Profil zeigen
  python tools/baue_lokal.py artefakte/<name> <daten.csv> --sql s.json --wahl w.json
Die Ausgabe liegt in ausgabe/ (nicht im Git: enthält Daten und evtl. Firmenlogo).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from pathlib import Path

from dashboard_framework.harness.dashboard import erzeuge_config
from dashboard_framework.models.artefakt import Artefakt
from dashboard_framework.runner.framework_lib import bezeichner_zitieren, lese_csv, uebernehmen, validate_against_schema
from dashboard_framework.runner.sicherheit import pruefe_nur_lesend, verbinde_nur_lesend

SQL_TYPEN = {"datum": "TEXT", "text": "TEXT", "ganzzahl": "INTEGER", "dezimal": "REAL", "bool": "INTEGER"}


class AntwortAusDatei:
    """Gibt eine vorbereitete Modellantwort zurück (hier: von Claude geschrieben). Hat die Form des Modell-Zugangs der Pipeline."""

    def __init__(self, text: str):
        self.text, self.aufrufe = text, 0

    def antworte(self, prompt: str, schritt: str, json_schema: dict | None = None) -> str:
        self.aufrufe += 1
        return self.text


def lade_daten(artefakt: Artefakt, csv: Path, db: Path) -> int:
    daten = validate_against_schema(lese_csv(csv.read_bytes()), artefakt.spalten)  # wirft UploadFehler mit allen Gründen
    db.parent.mkdir(parents=True, exist_ok=True)
    db.unlink(missing_ok=True)
    spalten = ", ".join(f"{bezeichner_zitieren(s.name)} {SQL_TYPEN[s.typ]}" for s in artefakt.spalten)
    verbindung = sqlite3.connect(db)
    verbindung.execute(f"CREATE TABLE {bezeichner_zitieren(artefakt.tabelle)} ({spalten})")
    verbindung.commit()
    verbindung.close()
    return uebernehmen(daten, db, artefakt.tabelle)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("artefakt_ordner", type=Path)
    ap.add_argument("csv", type=Path)
    ap.add_argument("--sql", type=Path, help="JSON {KPI-Name: SQL}")
    ap.add_argument("--wahl", type=Path, help="JSON-Antwort für Schritt 3 (charts mit kpi, typ, ...)")
    ap.add_argument("--ausgabe", type=Path, default=Path("ausgabe"))
    a = ap.parse_args()

    artefakt = Artefakt.aus_yaml(a.artefakt_ordner / "artefakt.yaml")
    ziel = a.ausgabe / artefakt.name
    zeilen = lade_daten(artefakt, a.csv, ziel / "daten.db")
    print(f"Schritt 1: {zeilen} Zeilen in {ziel / 'daten.db'} geladen")

    if not (a.sql and a.wahl):
        verbindung = verbinde_nur_lesend(ziel / "daten.db")
        for s in artefakt.spalten:
            n = verbindung.execute(f"SELECT COUNT(DISTINCT {bezeichner_zitieren(s.name)}), MIN({bezeichner_zitieren(s.name)}), MAX({bezeichner_zitieren(s.name)}) FROM {bezeichner_zitieren(artefakt.tabelle)}").fetchone()
            print(f"  {s.name:18} {s.typ:9} verschiedene={n[0]:6} min={str(n[1])[:30]!r} max={str(n[2])[:30]!r}")
        return

    sql = json.loads(a.sql.read_text(encoding="utf-8"))
    verbindung = verbinde_nur_lesend(ziel / "daten.db")
    for name, anweisung in sql.items():
        pruefe_nur_lesend(anweisung)
        zeilen_sql = verbindung.execute(anweisung).fetchall()
        print(f"Schritt 2: '{name}' -> {len(zeilen_sql)} Zeilen, erste: {zeilen_sql[:3]}")
    verbindung.close()

    llm = AntwortAusDatei(a.wahl.read_text(encoding="utf-8"))
    config = erzeuge_config(artefakt, sql, llm, db_pfad="daten.db")
    config.speichern(ziel / "dashboard.json")
    print(f"Schritt 3: dashboard.json mit {len(config.charts)} Feldern ({llm.aufrufe} Modellaufruf)")
    logo = a.artefakt_ordner / (artefakt.branding.logo or "")
    if artefakt.branding.logo and logo.exists():
        shutil.copy(logo, ziel / artefakt.branding.logo)
    print(f"\nAnsehen:  DASHBOARD_CONFIG={ziel / 'dashboard.json'}  streamlit run src/dashboard_framework/runner/app.py")


if __name__ == "__main__":
    main()
