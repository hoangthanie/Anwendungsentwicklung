# Backend – Pipeline und Agent-Harness

Verantwortlich: David Zöller

Hier liegen die Pipeline-Schritte 1, 2 und 4, der Agent-Harness (Anbindung an das lokale Sprachmodell über Ollama) und `run.py`, das die ganze Pipeline in einem Aufruf ausführt.

```
artefakt.yaml + CSV ──► Schritt 1 Datenmodell ──► Schritt 2 SQL je KPI ──► Schritt 3 Dashboard-Konfiguration ──► dashboard.json
                                                                       └──► Schritt 4 Dokumentation
```

Schritt 3 liegt nicht hier, sondern bei Dominik unter `frontend/src/dashboard_framework/harness/dashboard.py`.

## Ordner

| Pfad | Inhalt | PSP |
|---|---|---|
| `src/pipeline/harness/llm.py` | Zugriff auf das Sprachmodell (Ollama), Format-Erzwingung, Wiederholung bei Fehlern, Run-Protokoll | 5.2 |
| `src/pipeline/schritte/schritt1_datenmodell.py` | CSV prüfen und in SQLite laden, Schema (Spalten, Typ, Beispielwerte) aus der Datenbank lesen und gegen das Artefakt abgleichen, ohne Sprachmodell (ADR 0007) | 5.3 |
| `src/pipeline/schritte/schritt2_query.py` | KPI-Beschreibung in geprüftes SQL übersetzen | 5.4 |
| `src/pipeline/schritte/schritt4_doku.py` | Dokumentation aus den Ergebnissen der anderen Schritte erzeugen | 5.6 |
| `src/pipeline/run.py` | ein Befehl erzeugt das vollständige Paket | 5.7 |
| `runs/` | lokales Run-Protokoll (`metrics.jsonl`), wird nicht eingecheckt | 5.2 |
| `tests/` | Tests für das Backend | – |

Die PSP-Nummern für Schritt 1, 2, 4 und `run.py` sind vorläufig, bitte mit dem PSP abgleichen.

## Einrichtung

Voraussetzung: Python 3.11 oder neuer.

Mac:
```
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Windows (Git Bash):
```
cd backend
py -3.12 -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
pytest
```

`requirements.txt` installiert das gemeinsame Paket `dashboard_framework` aus `../frontend` mit. Daraus kommen die Datenmodelle (`models/artefakt.py`, `models/dashboard_config.py`) und Schritt 3.

## Einstellungen

Vorlage kopieren und bei Bedarf anpassen:
```
cp .env.example .env
```
Die `.env` bleibt lokal und wird nicht eingecheckt.
