"""Testset für die Messung von Schritt 2: KPI-Beschreibungen mit bekanntem richtigem Ergebnis.

Jeder Fall hat eine Referenz-Abfrage, die von Hand geschrieben und geprüft ist. Sie liefert auf den Testdaten aus
tools/testdaten.py das richtige Ergebnis (das Testorakel aus ADR 0008, Schicht 7). Die Referenz muss nicht allgemein
gültig sein, nur auf diesen Daten stimmen. referenz None heißt: Die KPI ist mit den Spalten nicht berechenbar und
muss begründet abgelehnt werden.

Die Fälle reichen von einfach (Summe je Gruppe) bis schwer (Vergleich zweier Zeiträume). Die Beschreibungen sind so
präzise formuliert, wie es ein Anwender im Formular tun sollte; gemessen wird das Modell, nicht die Formulierung.
Erweitern: einfach einen Fall anhängen. Ein Datensatz hat höchstens 12 KPIs (Grenze des Artefakts).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fall:
    datensatz: str  # "sales" oder "aktivitaet": Artefakt in frontend/artefakte/<datensatz>, Daten aus testdaten.py
    name: str
    beschreibung: str
    referenz: str | None
    reihenfolge: bool = False  # True: Reihenfolge der Zeilen zählt (Verlauf, Rangliste)
    schwierigkeit: str = "einfach"  # einfach, mittel, schwer – nur für die Auswertung


TESTSET: list[Fall] = [
    # --- Sales (Tabelle absatz, 192 Zeilen, Januar bis Dezember 2026) ---
    Fall(
        "sales", "Umsatz nach Region", "Summe von `umsatz`, gruppiert nach `region`.",
        "SELECT region, SUM(umsatz) FROM absatz GROUP BY region",
    ),
    Fall(
        "sales", "Umsatzverlauf", "Summe von `umsatz` je Monat aus `datum`.",
        "SELECT strftime('%Y-%m', datum) AS m, SUM(umsatz) FROM absatz GROUP BY m ORDER BY m",
        reihenfolge=True,
    ),
    Fall(
        "sales", "Top-Produkte", "Die fünf `produktkategorie`-Werte mit der höchsten Summe von `menge`.",
        "SELECT produktkategorie, SUM(menge) AS s FROM absatz GROUP BY produktkategorie ORDER BY s DESC LIMIT 5",
        reihenfolge=True,
    ),
    Fall(
        "sales", "Durchschnittspreis je Produkt",
        "Summe von `umsatz` geteilt durch die Summe von `menge`, je `produktkategorie`.",
        "SELECT produktkategorie, SUM(umsatz) / SUM(menge) FROM absatz GROUP BY produktkategorie",
        schwierigkeit="mittel",
    ),
    Fall(
        "sales", "Umsatz im jüngsten Monat", "Summe von `umsatz` im jüngsten Monat von `datum`.",
        "SELECT SUM(umsatz) FROM absatz WHERE strftime('%Y-%m', datum) = '2026-12'",
        schwierigkeit="mittel",
    ),
    Fall(
        "sales", "Anteil Region Nord", "Anteil der `region` Nord an der Summe von `umsatz`, in Prozent.",
        "SELECT 100.0 * SUM(CASE WHEN region = 'Nord' THEN umsatz END) / SUM(umsatz) FROM absatz",
        schwierigkeit="mittel",
    ),
    Fall(
        "sales", "Zielerreichung ggü. Vorperiode",
        "Summe von `umsatz` im jüngsten Monat von `datum` geteilt durch die Summe von `umsatz` im Monat davor. "
        "Ergebnis ist genau eine Zahl.",
        "SELECT SUM(CASE WHEN strftime('%Y-%m', datum) = '2026-12' THEN umsatz END)"
        " / SUM(CASE WHEN strftime('%Y-%m', datum) = '2026-11' THEN umsatz END) FROM absatz",
        schwierigkeit="schwer",
    ),
    Fall(
        "sales", "Quartalsvergleich",
        "Summe von `umsatz` im jüngsten Quartal von `datum` geteilt durch die Summe von `umsatz` im Quartal davor. "
        "Ergebnis ist genau eine Zahl.",
        "SELECT SUM(CASE WHEN strftime('%m', datum) >= '10' THEN umsatz END)"
        " / SUM(CASE WHEN strftime('%m', datum) BETWEEN '07' AND '09' THEN umsatz END) FROM absatz",
        schwierigkeit="schwer",
    ),
    Fall(
        "sales", "Kundenzufriedenheit", "Durchschnittliche Kundenzufriedenheit je `region`.",
        None,  # keine Spalte dafür: begründet ablehnen
        schwierigkeit="mittel",
    ),
    # --- Aktivitätsmonitor (Tabelle aktivitaeten, 495 Zeilen, Januar bis Juni 2026) ---
    Fall(
        "aktivitaet", "Aktivitäten je Person", "Anzahl der Einträge je `person`.",
        "SELECT person, COUNT(*) FROM aktivitaeten GROUP BY person",
    ),
    Fall(
        "aktivitaet", "Dauer im Zeitverlauf", "Summe von `dauer_min` je Monat aus `zeitpunkt`.",
        "SELECT strftime('%Y-%m', zeitpunkt) AS m, SUM(dauer_min) FROM aktivitaeten GROUP BY m ORDER BY m",
        reihenfolge=True,
    ),
    Fall(
        "aktivitaet", "Häufigste Aktionen", "Die fünf `aktion`-Werte mit den meisten Einträgen.",
        "SELECT aktion, COUNT(*) AS n FROM aktivitaeten GROUP BY aktion ORDER BY n DESC LIMIT 5",
        reihenfolge=True,
    ),
    Fall(
        "aktivitaet", "Durchschnittliche Dauer je Aktion", "Durchschnitt von `dauer_min` je `aktion`.",
        "SELECT aktion, AVG(dauer_min) FROM aktivitaeten GROUP BY aktion",
    ),
    Fall(
        "aktivitaet", "Anteil Meetings an der Arbeitszeit",
        "Anteil der `aktion` Meeting an der Summe von `dauer_min`, in Prozent.",
        "SELECT 100.0 * SUM(CASE WHEN aktion = 'Meeting' THEN dauer_min END) / SUM(dauer_min) FROM aktivitaeten",
        schwierigkeit="mittel",
    ),
    Fall(
        "aktivitaet", "Aktivität ggü. Vormonat",
        "Anzahl der Einträge im jüngsten Monat von `zeitpunkt` geteilt durch die Anzahl der Einträge im Monat davor. "
        "Ergebnis ist genau eine Zahl.",
        "SELECT 1.0 * SUM(strftime('%Y-%m', zeitpunkt) = '2026-06') / SUM(strftime('%Y-%m', zeitpunkt) = '2026-05')"
        " FROM aktivitaeten",
        schwierigkeit="schwer",
    ),
]
