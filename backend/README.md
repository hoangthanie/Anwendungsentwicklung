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
| `src/pipeline/harness/llm.py` | Mini-Harness (ADR 0004): Zugriff auf das Sprachmodell über Ollama, Format-Erzwingung per JSON-Schema, Denkmodus aus, optionaler Fallback, Run-Protokoll | 5.2 |
| `src/pipeline/schritte/schritt1_datenmodell.py` | Datenstruktur aus der CSV lesen und gegen das Artefakt prüfen | 5.3 |
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

| Variable | Bedeutung |
|---|---|
| `OLLAMA_URL` | Adresse des Ollama-Servers |
| `MODELL` | Standardmodell, laut ADR 0006 `qwen3:8b` |
| `FALLBACK_MODELL` | Ausweichmodell, wenn die Antwort abgeschnitten oder kein gültiges JSON ist; leer = kein Fallback |

Jeder Modellaufruf schreibt eine Zeile nach `runs/metrics.jsonl` (Schritt, Versuch, Modell, Tokens, Dauer, Fallback ja/nein).
