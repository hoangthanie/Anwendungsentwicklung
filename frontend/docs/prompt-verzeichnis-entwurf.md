# Prompt-Verzeichnis – Entwurf Dominik Boch

Modulvorgabe: Alle mit generativer KI erzeugten Inhalte kennzeichnen. Diese Liste an Melanie (AP 9.4) geben, Format wie Repository-Doc Kap. 10.

| Datum | PSP | Tool | Zweck / Ergebnis | Prüfung |
|---|---|---|---|---|
| 2026-10-27 | 6.3 | Claude Code | Dashboard-Runner (Config-Modell, SQL-Sicherheit, Charts, App), Tests, docs/03 | Code gelesen, 36 Tests, im Browser geprüft |
| 2026-10-27 | 6.3 | Claude Code | Daten-Upload (US-10): Validierung, Übernehmen, UI, Tests, docs/04 | 61 Tests, Browser-Test mit fehlerhafter und gültiger CSV |
| 2026-10-27 | 6.2 | Claude Code | Branding: Logo-/Farbprüfung, Anzeige, Eingabe-Entwurfsseite, Tests, docs/05 | 83 Tests, Browser-Test mit Skript-Datei, PNG und falschen Farben |
| 2026-10-27 | 6.1, 3.3 | Claude Code | Artefakt-Modell mit Fail-Fast-Prüfung, Formularlogik, Eingabe-App, Beispiel-Artefakte (sales, aktivitaet-Entwurf), Tests, docs/06 | 125 Tests, Browser-Test (Laden, CSV, "meinten Sie") |
| 2026-10-27 | 5.5 | Claude Code | Pipeline-Schritt 3 (harness/dashboard.py): Schema, Prompt-Vorlage, Antwortprüfung, Reparaturschleife, FakeLLM, Tests, docs/07 | 146 Tests; Prompt-Text und Wirkung mit echtem Modell noch ungeprüft (Spike David) |
| 2026-10-27 | 6.4 | Claude Code mit Impeccable-Skill (github.com/pbakaus/impeccable v4.8.0) | Gestaltungssystem "Formblatt" für beide Streamlit-Apps: PRODUCT.md, DESIGN.md, Gestaltungsvertrag, ui/-Paket, Schriften (Barlow, OFL), unabhängiges Review (Agent) und dessen Korrekturen, docs/08 | 172 Tests, Browser-Prüfung (Desktop, Handy), Kontraste gemessen; Review-Agent ersetzt den im Skill vorgesehenen Review-Agenten |
| 2026-10-27 | 5.4 (Ersatz), 5.5 | Claude Code (Claude als "Sprachmodell", nicht Qwen3) | SQL je KPI und Darstellungswahl für das Artefakt tickets_am von Claude geschrieben; Entwicklungsskript tools/baue_lokal.py; docs/09 | SQL auf "nur lesend" geprüft und ausgeführt, Antwort durch dieselbe Prüfung wie in Schritt 3; Ergebnis im Browser angesehen |
| 2026-10-27 | 6.x | Claude Code | Projektunterlagen eingelesen, frontend/-Grundstruktur, CLAUDE.md, Doku-Gerüst | Inhalte gelesen, Struktur im Team abstimmen |
