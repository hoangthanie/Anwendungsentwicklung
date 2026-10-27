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
| [`.github/`](.github/) | CI-Pipeline, PR- und Issue-Vorlagen, Repo-Regeln | Stephanie Jayhooni |
| [`docs/`](docs/) | Projektdokumentation, Prompt-Verzeichnis (Melanie) · [Vorgehen](docs/VORGEHEN.md), [User Stories](docs/stories/README.md), [Entscheidungen (ADR)](docs/adr/README.md), [Risiken](docs/risiken.md) (Stephanie) | Melanie Peitsch, Stephanie Jayhooni |

Die Platzhalter-Zeilen können angepasst, umbenannt oder gelöscht werden, sobald die Ordner existieren.

## Schnellstart (Frontend lokal)

Details und Einrichtung auf einem neuen Rechner: [`frontend/README.md`](frontend/README.md) und [`frontend/CLAUDE.md`](frontend/CLAUDE.md).

## Betrieb auf dem Raspberry Pi

Eingabeformular (Port 8502) und Dashboard (Port 8501) laufen auf dem Pi und sind aus dem Netzwerk erreichbar. Einrichtung: [`raspberry-pi/README.md`](raspberry-pi/README.md).

## Für David (Backend / Pipeline)

*Platzhalter: Schnittstellen, Aufruf der Pipeline, Hinweise zu Ollama und Modell.*

## Für Stephanie (Repo / CI / Tests)

- **Regeln für die Zusammenarbeit:** [CONTRIBUTING.md](CONTRIBUTING.md) – Branches, Commit-Nachrichten, Pull Requests, Definition of Done.
- **Wie geht es weiter?** [docs/VORGEHEN.md](docs/VORGEHEN.md) – Meilensteine und Aufgaben je Person.
- **Was heißt „fertig“?** [docs/stories/](docs/stories/README.md) – User Stories mit Akzeptanzkriterien; jedes Kriterium ist mit einem Test verknüpft (`@pytest.mark.story("US-xx.y")`).
- **CI-Pipeline:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) läuft bei jedem Push und Pull Request: Frontend-Tests (`pytest` in `frontend/`), Code-Stil als Hinweis (ruff) und Suche nach versehentlich eingecheckten Zugangsdaten. Ergebnis unter *Actions*. Backend-Tests werden ergänzt, sobald `backend/` existiert.
- **Pull Requests:** Vorlage mit Checkliste (inkl. KI-Kennzeichnung) erscheint automatisch; Issues über die Vorlagen *Arbeitspaket* oder *Fehler melden*.

## Für Melanie (Dokumentation)

*Platzhalter: Verweise auf Projektdokumente und Prompt-Verzeichnis.*

## Regeln

- Nur synthetische Daten, keine echten Unternehmensdaten und keine Firmenlogos im Repository.
- Zugangsdaten und `.env`-Dateien gehören nicht ins Repository.
