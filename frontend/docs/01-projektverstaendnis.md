# 01 – Projektverständnis und Rolle des Frontends

## Das Projekt
Mittelständler brauchen individuelle Dashboards, haben aber kein Data-Engineering-Team und kein Budget für BI-Lizenzen.
Unser Framework löst das so: Der Nutzer füllt ein **Artefakt** aus, eine **Pipeline** mit lokalem Sprachmodell macht daraus
eine **Konfiguration**, und ein **generischer Runner** zeigt sie an. Kern der These: "Wir bauen die Fabrik, nicht das Produkt" –
das Sales-Dashboard ist nur eine austauschbare Instanz. Bewiesen wird das durch ein zweites Dashboard (z. B. Aktivitätsmonitor)
**ohne** Änderung am Framework-Code.

## Zwei Zeitpunkte: Build-Time und Runtime
| | Build-Time (Entwicklungsrechner) | Runtime (Raspberry Pi) |
|---|---|---|
| Was läuft | Eingabe-App, Pipeline mit Qwen3/Ollama | Docker-Container mit Runner |
| Eingabe | `artefakt.yaml` + Datendatei | `dashboard.json` + SQLite-DB (Volume) |
| LLM | ja (lokal) | **nein** |

Warum die Trennung? CPU-Inferenz auf dem Pi ist zu langsam; zusätzlich ist ein LLM-freier Runner deterministisch und leichter abzusichern.

## Datenfluss und mein Anteil
```
Eingabe-App (6.1, 6.2)  -> artefakt.yaml ->  Pipeline (DZ, DB: 5.x) -> dashboard.json + daten.db
                                                                              |
                                                       Runner (6.3) <---------+   (+ Upload neuer Daten, US-10)
```
Das Frontend besteht damit aus **zwei getrennten Streamlit-Anwendungen**:
1. **Eingabe-App** (Build-Time): erzeugt ein gültiges Artefakt, prüft früh (Fail-Fast), nimmt Logo und Farben entgegen.
2. **Runner** (Runtime): liest `dashboard.json`, führt pro Chart das hinterlegte SQL (nur lesend) aus, rendert Charts mit Theme und Logo,
   bietet Daten-Upload mit Schema-Prüfung.

## Gemeinsame Verträge
Zwei Dateiformate verbinden alle Teilprojekte: `artefakt.yaml` (Input) und `dashboard.json` (Output). Sie sind als
Pydantic-Modelle definiert (PSP 3.3 / 3.4). Beide Seiten müssen dasselbe Modell nutzen, sonst bricht die Schnittstelle (Risiko R07).
Solange die gemeinsamen Modelle nicht in der Repo liegen, arbeitet das Frontend mit eigenen Platzhaltern nach dem Beispiel in der Spezifikation
(siehe [02-entscheidungen.md](02-entscheidungen.md), E-02).
