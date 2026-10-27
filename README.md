# Framework für die agentengestützte Entwicklung maßgeschneiderter self-hosted Dashboards

FOM-Projekt Anwendungsentwicklung. Aus einer Beschreibung (Ziel, Publikum, Spalten, KPIs, Branding) und einer CSV-Datei erzeugt eine Agenten-Pipeline mit lokalem Sprachmodell (Qwen3 über Ollama) eine `dashboard.json`. Ein generischer Streamlit-Runner zeigt sie an, ohne Sprachmodell zur Laufzeit. Betrieben wird alles self-hosted auf einem Raspberry Pi.

```
Eingabeformular ──► artefakt.yaml + CSV ──► Pipeline (Schritte 1-4) ──► dashboard.json + daten.db ──► Runner (Dashboard)
```

## Ordner

| Ordner | Inhalt | Verantwortlich |
|---|---|---|
| [`frontend/`](frontend/) | Eingabeformular, Dashboard-Runner mit Daten-Upload und Branding, Pipeline-Schritt 3 (Dashboard-Konfiguration), Tests, Doku | Dominik Boch |
| [`raspberry-pi/`](raspberry-pi/) | Betrieb auf dem Raspberry Pi: Docker-Setup und Einrichtungsskript für Runner und Eingabeformular | Dominik Boch |
| `backend/` *(Platzhalter)* | Pipeline-Schritte 1, 2 und 4, Harness, Anbindung an Ollama | David Zöller |
| `ci/` oder `.github/` *(Platzhalter)* | CI, Tests, Repo-Regeln | Stephanie Jayhooni |
| `docs/` *(Platzhalter)* | Projektdokumentation, Prompt-Verzeichnis | Melanie Peitsch |

Die Platzhalter-Zeilen können angepasst, umbenannt oder gelöscht werden, sobald die Ordner existieren.

## Schnellstart (Frontend lokal)

Details und Einrichtung auf einem neuen Rechner: [`frontend/README.md`](frontend/README.md) und [`frontend/CLAUDE.md`](frontend/CLAUDE.md).

## Betrieb auf dem Raspberry Pi

Eingabeformular (Port 8502) und Dashboard (Port 8501) laufen auf dem Pi und sind aus dem Netzwerk erreichbar. Einrichtung: [`raspberry-pi/README.md`](raspberry-pi/README.md).

## Für David (Backend / Pipeline)

*Platzhalter: Schnittstellen, Aufruf der Pipeline, Hinweise zu Ollama und Modell.*

## Für Stephanie (Repo / CI / Tests)

*Platzhalter: Branch-Regeln, CI-Ablauf, Hinweise zum Testen.*

## Für Melanie (Dokumentation)

*Platzhalter: Verweise auf Projektdokumente und Prompt-Verzeichnis.*

## Regeln

- Nur synthetische Daten, keine echten Unternehmensdaten und keine Firmenlogos im Repository.
- Zugangsdaten und `.env`-Dateien gehören nicht ins Repository.
