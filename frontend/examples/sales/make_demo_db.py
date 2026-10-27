"""Erzeugt eine kleine synthetische Demo-Datenbank (daten.db) neben dieser Datei.

Nur zum lokalen Ausprobieren des Runners. Die offiziellen synthetischen Sales-Daten (PSP 7.1) kommen separat.
Aufruf:  python examples/sales/make_demo_db.py
"""
import random
import sqlite3
from datetime import date
from pathlib import Path

ZIEL = Path(__file__).with_name("daten.db")
REGIONEN = {"Nord": 1.3, "Süd": 1.0, "Ost": 0.7, "West": 0.9}
PRODUKTE = {"Antrieb": 120.0, "Lager": 45.0, "Dichtung": 12.0, "Steuerung": 210.0}


def main() -> None:
    zufall = random.Random(42)  # fester Seed: reproduzierbare Daten
    ZIEL.unlink(missing_ok=True)
    verbindung = sqlite3.connect(ZIEL)
    verbindung.execute(
        "CREATE TABLE absatz (datum TEXT, region TEXT, produktkategorie TEXT, menge INTEGER, umsatz REAL)"
    )
    zeilen = []
    for monat in range(1, 13):
        for region, faktor in REGIONEN.items():
            for produkt, preis in PRODUKTE.items():
                menge = int(zufall.randint(20, 80) * faktor * (1 + monat / 24))
                zeilen.append((date(2026, monat, 15).isoformat(), region, produkt, menge, round(menge * preis, 2)))
    verbindung.executemany("INSERT INTO absatz VALUES (?, ?, ?, ?, ?)", zeilen)
    verbindung.commit()
    verbindung.close()
    print(f"{len(zeilen)} Zeilen -> {ZIEL}")


if __name__ == "__main__":
    main()
