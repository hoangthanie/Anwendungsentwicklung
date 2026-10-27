# Frontend – Dashboard-Framework

Frontend-Teil des Uni-Projekts "Framework für die agentengestützte Entwicklung maßgeschneiderter self-hosted Dashboards".

- **Eingabe-App** (Streamlit): Formular für Ziel, Publikum, Spalten, KPIs, Branding -> `artefakt.yaml`
- **Dashboard-Runner** (Streamlit): rendert eine `dashboard.json` generisch, inkl. Daten-Upload

Einstieg für Entwickler: [CLAUDE.md](CLAUDE.md). Erklärungen und Entscheidungen: [docs/](docs/README.md).

## Schnellstart
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
```
