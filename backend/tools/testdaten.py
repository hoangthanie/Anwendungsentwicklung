"""Synthetische Testdaten für Probeläufe und Messungen: immer dieselben Zeilen dank festem Zufalls-Seed.

- demo_sales.csv      192 Zeilen, Sales-Artefakt (frontend/artefakte/sales), gleiche Werte wie
                      frontend/examples/sales/make_demo_db.py (Seed 42)
- demo_aktivitaet.csv Aktivitäten eines Teams von Januar bis Juni 2026, Artefakt frontend/artefakte/aktivitaet (Seed 7)

Format wie ein Export aus deutschem Excel: Semikolon, Datum TT.MM.JJJJ, Dezimalkomma. Keine echten Personen oder
Unternehmensdaten, die Namen sind ausgedacht.

Aufruf (aus dem Ordner backend, venv aktiv):
    python tools/testdaten.py            schreibt beide Dateien nach runs/
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

RUNS = Path(__file__).resolve().parent.parent / "runs"


def sales_zeilen() -> list[tuple]:
    """(datum, region, produktkategorie, menge, umsatz), 12 Monate × 4 Regionen × 4 Produkte."""
    regionen = {"Nord": 1.3, "Süd": 1.0, "Ost": 0.7, "West": 0.9}
    produkte = {"Antrieb": 120.0, "Lager": 45.0, "Dichtung": 12.0, "Steuerung": 210.0}
    zufall = random.Random(42)
    zeilen = []
    for monat in range(1, 13):
        for region, faktor in regionen.items():
            for produkt, preis in produkte.items():
                menge = int(zufall.randint(20, 80) * faktor * (1 + monat / 24))
                zeilen.append((date(2026, monat, 15), region, produkt, menge, round(menge * preis, 2)))
    return zeilen


def aktivitaet_zeilen() -> list[tuple]:
    """(zeitpunkt, person, aktion, dauer_min) an Werktagen von Januar bis Juni 2026.

    Die Aktionen sind unterschiedlich häufig gewichtet, damit eine Rangliste eindeutig ist (keine Gleichstände).
    """
    personen = ["Anna", "Ben", "Clara", "Deniz", "Emil"]
    aktionen = {"Telefonat": 30, "E-Mail": 22, "Meeting": 16, "Angebot": 11, "Recherche": 7, "Dokumentation": 4}
    zufall = random.Random(7)
    zeilen = []
    tag = date(2026, 1, 1)
    while tag <= date(2026, 6, 30):
        if tag.weekday() < 5:
            for _ in range(zufall.randint(2, 6)):
                aktion = zufall.choices(list(aktionen), weights=list(aktionen.values()))[0]
                zeilen.append((tag, zufall.choice(personen), aktion, zufall.randint(5, 120)))
        tag += timedelta(days=1)
    return zeilen


def _text(wert: object) -> str:
    if isinstance(wert, date):
        return f"{wert:%d.%m.%Y}"
    if isinstance(wert, float):
        return str(wert).replace(".", ",")
    return str(wert)


def schreibe_csv(pfad: Path, kopf: list[str], zeilen: list[tuple]) -> Path:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("w", encoding="utf-8", newline="") as datei:
        schreiber = csv.writer(datei, delimiter=";")
        schreiber.writerow(kopf)
        schreiber.writerows([_text(w) for w in zeile] for zeile in zeilen)
    return pfad


def schreibe_alle(ordner: Path = RUNS) -> dict[str, Path]:
    """Schreibt beide Dateien und liefert {Datensatz: Pfad}."""
    return {
        "sales": schreibe_csv(
            ordner / "demo_sales.csv", ["datum", "region", "produktkategorie", "menge", "umsatz"], sales_zeilen()
        ),
        "aktivitaet": schreibe_csv(
            ordner / "demo_aktivitaet.csv", ["zeitpunkt", "person", "aktion", "dauer_min"], aktivitaet_zeilen()
        ),
    }


if __name__ == "__main__":
    for name, pfad in schreibe_alle().items():
        print(f"{name}: {pfad}")
