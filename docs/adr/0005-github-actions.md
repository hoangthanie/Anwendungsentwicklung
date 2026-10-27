# ADR 0005: GitHub und GitHub Actions

- **Status:** angenommen
- **Datum:** 17.10.2026 · **Quelle:** PSP AP 4.1 / 4.3

## Kontext
Das Modul verlangt Kollaborationstools (Git mit Branching, Kanban-Boards). CI/CD soll Linting, Tests und Build bei jedem Push ausführen.

## Entscheidung
Privates GitHub-Repository mit Projects-Board und GitHub Actions: ci.yml (GitHub-hosted), pipeline-e2e.yml (self-hosted, lokales LLM), release.yml (Deploy per Tailscale).

## Konsequenzen
Keine eigene CI-Infrastruktur nötig; LLM-Läufe bleiben lokal. Self-hosted Runner muss abgesichert werden (Risiko R16).
