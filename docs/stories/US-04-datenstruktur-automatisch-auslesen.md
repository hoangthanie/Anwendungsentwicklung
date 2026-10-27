# Qualitäts-Gate für jeden Push und Pull Request – PSP AP 4.3 (Stephanie Jayhooni)
# Abnahmekriterium AP 4.3: „Pipeline läuft bei jedem PR grün/rot“.
# Läuft auf GitHub-Servern, ohne Sprachmodell, nur mit synthetischen Testdaten.
# Weitere Teile (backend/, docs/) werden ergänzt, sobald die Ordner existieren.
name: ci

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  frontend-tests:
    name: Frontend – Tests
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: frontend/requirements.txt
      - name: Abhängigkeiten installieren
        run: pip install -r requirements.txt
      - name: Tests ausführen (pytest)
        run: pytest -q

  frontend-lint:
    name: Frontend – Code-Stil (Hinweis)
    runs-on: ubuntu-latest
    continue-on-error: true   # zunächst nur Hinweis, blockiert nichts
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff
      - name: ruff
        run: ruff check src tests --output-format=github

  secrets-scan:
    name: Sicherheit – keine Zugangsdaten im Repo
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
