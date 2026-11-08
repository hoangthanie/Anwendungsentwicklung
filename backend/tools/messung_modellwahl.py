"""Tokenmessung und Modellwahl: jedes Modell mit und ohne Denken gegen die Ollama-API.

Misst je Aufruf: Eingabe-Tokens, Ausgabe-Tokens, Laufzeit, Aufgabe richtig/falsch.
Ergebnis: backend/runs/modellwahl.csv (bleibt lokal, siehe .gitignore).

Aufruf (aus dem Ordner backend, venv aktiv):
    python tools/messung_modellwahl.py
"""

import csv
import json
import os
import random
import sqlite3
import urllib.request
from datetime import date, datetime
from pathlib import Path

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
ZIEL = Path(__file__).resolve().parent.parent / "runs" / "modellwahl.csv"

# Fest im Skript, unabhängig von OLLAMA_CONTEXT_LENGTH
OPTIONEN = {"num_ctx": 12288, "num_predict": 4096}

# (Modell, Denken). None = Modell hat keinen Denkmodus, Parameter wird nicht gesendet.
VARIANTEN = [
    ("qwen3:14b", True),
    ("qwen3:14b", False),
    ("qwen3:8b", True),
    ("qwen3:8b", False),
    ("qwen3.5:9b", True),
    ("qwen3.5:9b", False),
    ("qwen2.5-coder:14b", None),
]

SYSTEM = (
    "Du übersetzt Fragen in SQLite-SQL.\n"
    "Es gibt genau eine Tabelle `absatz` mit diesen Spalten:\n"
    "- datum (TEXT, ISO-Datum JJJJ-MM-TT): Verkaufstag\n"
    "- region (TEXT): Vertriebsregion\n"
    "- produktkategorie (TEXT): Produktgruppe\n"
    "- menge (INTEGER): verkaufte Stückzahl\n"
    "- umsatz (REAL): Nettoumsatz in Euro\n"
    "Antworte nur mit JSON der Form {\"sql\": \"...\", \"ablehnung\": \"...\"}.\n"
    "Ist die Frage mit diesen Spalten beantwortbar: eine SELECT-Abfrage in sql, ablehnung leer.\n"
    "Ist sie nicht beantwortbar: sql leer, in ablehnung eine kurze Begründung."
)

SCHEMA = {
    "type": "object",
    "properties": {"sql": {"type": "string"}, "ablehnung": {"type": "string"}},
    "required": ["sql", "ablehnung"],
}

# (Name, Frage, Referenz-SQL). Referenz None = Frage muss abgelehnt werden.
AUFGABEN = [
    ("einfach", "Wie hoch ist der gesamte Umsatz?", "SELECT SUM(umsatz) FROM absatz"),
    (
        "gruppierung",
        "Wie hoch ist der Umsatz je Region?",
        "SELECT region, SUM(umsatz) FROM absatz GROUP BY region",
    ),
    ("ablehnung", "Wie hoch ist die durchschnittliche Kundenzufriedenheit je Region?", None),
]


def baue_datenbank() -> sqlite3.Connection:
    """Gleiche Daten wie frontend/examples/sales/make_demo_db.py (Seed 42), nur im Arbeitsspeicher."""
    regionen = {"Nord": 1.3, "Süd": 1.0, "Ost": 0.7, "West": 0.9}
    produkte = {"Antrieb": 120.0, "Lager": 45.0, "Dichtung": 12.0, "Steuerung": 210.0}
    zufall = random.Random(42)
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE absatz (datum TEXT, region TEXT, produktkategorie TEXT, menge INTEGER, umsatz REAL)")
    zeilen = []
    for monat in range(1, 13):
        for region, faktor in regionen.items():
            for produkt, preis in produkte.items():
                menge = int(zufall.randint(20, 80) * faktor * (1 + monat / 24))
                zeilen.append((date(2026, monat, 15).isoformat(), region, produkt, menge, round(menge * preis, 2)))
    db.executemany("INSERT INTO absatz VALUES (?, ?, ?, ?, ?)", zeilen)
    return db


def normiere(zeilen: list) -> list:
    """Reihenfolge von Zeilen und Spalten egal, Zahlen auf 2 Stellen gerundet."""
    def wert(v):
        return f"{v:.2f}" if isinstance(v, (int, float)) else str(v)
    return sorted(tuple(sorted(wert(v) for v in zeile)) for zeile in zeilen)


def pruefe(antwort: dict, referenz: str | None) -> bool:
    sql = (antwort.get("sql") or "").strip()
    ablehnung = (antwort.get("ablehnung") or "").strip()
    if referenz is None:
        return not sql and bool(ablehnung)
    if not sql or not sql.lower().startswith(("select", "with")):
        return False
    db = baue_datenbank()  # frisch je Prüfung, damit nichts übrig bleibt
    try:
        return normiere(db.execute(sql).fetchall()) == normiere(db.execute(referenz).fetchall())
    except sqlite3.Error:
        return False
    finally:
        db.close()


def frage_ollama(modell: str, denken: bool | None, frage: str) -> dict:
    nutzlast = {
        "model": modell,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": frage}],
        "format": SCHEMA,
        "stream": False,
        "options": OPTIONEN,
    }
    if denken is not None:
        nutzlast["think"] = denken
    anfrage = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(nutzlast).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(anfrage, timeout=900) as antwort:
        return json.loads(antwort.read())


def main() -> None:
    ZIEL.parent.mkdir(exist_ok=True)
    spalten = [
        "zeit", "modell", "denken", "aufgabe", "richtig", "eingabe_tokens", "ausgabe_tokens",
        "laufzeit_s", "ladezeit_s", "grenze_erreicht", "antwort", "fehler",
    ]
    with ZIEL.open("w", newline="", encoding="utf-8") as datei:
        schreiber = csv.DictWriter(datei, fieldnames=spalten, delimiter=";")
        schreiber.writeheader()
        for modell, denken in VARIANTEN:
            for name, frage, referenz in AUFGABEN:
                zeile = {
                    "zeit": datetime.now().isoformat(timespec="seconds"),
                    "modell": modell,
                    "denken": {True: "ja", False: "nein", None: "-"}[denken],
                    "aufgabe": name,
                }
                try:
                    r = frage_ollama(modell, denken, frage)
                    text = r["message"]["content"]
                    try:
                        richtig = pruefe(json.loads(text), referenz)
                    except json.JSONDecodeError:
                        richtig = False
                    zeile.update(
                        richtig="ja" if richtig else "nein",
                        eingabe_tokens=r.get("prompt_eval_count", ""),
                        ausgabe_tokens=r.get("eval_count", ""),
                        laufzeit_s=round(r.get("total_duration", 0) / 1e9, 2),
                        ladezeit_s=round(r.get("load_duration", 0) / 1e9, 2),
                        grenze_erreicht="ja" if r.get("done_reason") == "length" else "nein",
                        antwort=text.replace("\n", " ")[:300],
                    )
                except Exception as fehler:  # ein Fehler stoppt nicht den ganzen Lauf
                    zeile.update(richtig="nein", fehler=str(fehler)[:300])
                schreiber.writerow(zeile)
                datei.flush()  # Zwischenstand bleibt bei Abbruch erhalten
                print(f"{zeile['modell']:<20} denken={zeile['denken']:<4} {name:<12} richtig={zeile['richtig']}")
    print(f"Fertig -> {ZIEL}")


if __name__ == "__main__":
    main()
