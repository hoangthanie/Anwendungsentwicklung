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
| `src/pipeline/harness/llm.py` | Mini-Harness (ADR 0004): Zugriff auf das Sprachmodell über Ollama, Format-Erzwingung per JSON-Schema, Denkmodus aus, temperature 0, Timeout 300 s, optionaler Fallback, Run-Protokoll | 5.2 |
| `src/pipeline/harness/validators.py` | Prüfschichten für generiertes SQL (ADR 0008); jedes SQL läuft bei der Prüfung höchstens 10 Sekunden | 5.4 |
| `src/pipeline/schritte/schritt1_datenmodell.py` | CSV prüfen und in SQLite laden, Schema (Spalten, Typ, Beispielwerte) aus der Datenbank lesen und gegen das Artefakt abgleichen, ohne Sprachmodell (ADR 0007) | 5.3 |
| `src/pipeline/schritte/schritt2_query.py` | je KPI ein SQL vom Sprachmodell, geprüft durch die Prüfschichten, mit Reparaturschleife (höchstens 3 Versuche, danach einmal das Fallback-Modell) | 5.4 |
| `src/pipeline/schritte/schritt4_doku.py` | Beschreibung des Dashboards für den Anwender (Tab „Über dieses Dashboard“ und `README.md` im Paket): Fakten aus der Vorlage, nur die Erklärtexte vom Sprachmodell (ein Aufruf) | 5.6 |
| `src/pipeline/run.py` | ein Aufruf erzeugt das vollständige Paket: `pipeline()` für das Frontend, Befehl `dashframe-run` für das Terminal | 5.7 |
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
| `FALLBACK_MODELL` | Ausweichmodell, wenn die Antwort abgeschnitten oder kein gültiges JSON ist; leer = kein Fallback. Das Modell muss installiert sein (`ollama pull qwen3:14b`); fehlt es, bleibt die erste Antwort erhalten |

Jeder Modellaufruf schreibt eine Zeile nach `runs/metrics.jsonl` (Lauf, Schritt, Versuch, Modell, Tokens, Dauer, Fallback ja/nein). Das Feld `lauf` (z. B. `2026-11-23T21:50:12_sales`) ist bei allen Aufrufen eines Pipeline-Laufs gleich. So lässt sich auswerten, was ein einzelnes Dashboard gekostet hat.

## Dashboard erzeugen

Voraussetzung: Ollama läuft, die Modelle aus der `.env` sind installiert (`ollama pull qwen3:8b`, `ollama pull qwen3:14b`).

Im Terminal (Git Bash), im Ordner `backend` mit aktivem venv:
```
pip install -r requirements.txt
dashframe-run ../frontend/artefakte/sales pfad/zu/daten.csv
```
`pip install` ist nur einmal nötig, es richtet den Befehl `dashframe-run` ein. Ohne den Befehl geht es auch mit `python -m pipeline.run …`.

Der Befehl zeigt an, welcher Schritt gerade läuft. Am Ende liegt das Paket in `ausgabe/sales/`:

| Datei | Inhalt |
|---|---|
| `dashboard.json` | Konfiguration für den Runner, mit der Beschreibung für den Tab „Über dieses Dashboard“ |
| `daten.db` | die geprüften Daten |
| `README.md` | dieselbe Beschreibung als Datei |
| Logo | falls im Artefakt hinterlegt |

Der Ordner läuft so, wie er ist: lokal mit dem Runner oder auf dem Raspberry Pi, dort den Inhalt nach `/srv/dashboards/aktuell` kopieren.
Ein vorhandenes Paket wird nur mit `--ueberschreiben` ersetzt, und erst dann, wenn das neue fertig ist. Scheitert ein Schritt, entsteht kein Paket. Der Befehl nennt den Schritt, die Gründe und was zu tun ist, und endet mit Exit-Code 1.

Lokal ansehen (im Ordner `frontend` mit dessen venv):
```
DASHBOARD_CONFIG=../backend/ausgabe/sales/dashboard.json streamlit run src/dashboard_framework/runner/app.py
```

Aus dem Frontend (z. B. hinter einem Knopf) läuft derselbe Ablauf über eine Funktion:
```python
from pipeline.run import PipelineFehler, pipeline

try:
    paket = pipeline(artefakt_ordner, csv_pfad, ausgabe, fortschritt=anzeige)  # anzeige(text) zeigt den laufenden Schritt
except PipelineFehler as fehler:
    ...  # fehler.schritt, fehler.meldungen, fehler.hinweis anzeigen
```
