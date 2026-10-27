# CLAUDE.md – Frontend (Dominik Boch)

> Gedächtnis des Projekts für Claude Code. **Bei jeder Änderung aktualisieren** (Abschnitt "Arbeitslog" + ggf. "Stand"),
> damit die Arbeit auf jedem Rechner nahtlos weitergeht. Lies diese Datei zuerst, wenn du auf einem neuen Rechner startest.

## Projekt in drei Sätzen
Uni-Projekt (FOM, Modul "Projekt: Anwendungsentwicklung", Prof. Dr. Henning Ahlf, WS 2026/27), Team: Melanie Peitsch (MP),
Dominik Boch (DB), Stephanie Jayhooni (SJ), David Zöller (DZ). Wir bauen ein **Framework**, das aus einem ausgefüllten
Artefakt (`artefakt.yaml`: Ziel, Publikum, Spalten, KPIs, Branding) per Agenten-Pipeline mit lokalem LLM (Qwen3/Ollama)
eine `dashboard.json` erzeugt. Ein **generischer Streamlit-Runner** auf einem Raspberry Pi rendert sie – ohne LLM zur Laufzeit.
Leitbild: "Die Fabrik, nicht das Produkt" – Erfolgsmaßstab ist Generizität (zweites Dashboard ohne Codeänderung).

## Mein Teil: Frontend (Teilprojekt 6 im PSP)
| PSP | Arbeitspaket | Stories | Status |
|---|---|---|---|
| 6.1 | Streamlit-Eingabeoberfläche (Formular -> `artefakt.yaml`, Spaltenauswahl) | US-01, US-02 | offen |
| 6.2 | Upload & Branding (Logo-Prüfung mit Pillow, Farbcodes `#RRGGBB`) | US-03 | offen |
| 6.3 | Dashboard-Runner (liest `dashboard.json`, rendert Charts/Theme/Logo, Daten-Upload) | US-09, US-10 | offen |
| 6.4 | UI-Feinschliff & Usability-Check mit Testperson | – | offen |
| 5.5 | Pipeline-Schritt 3: Dashboard-Konfiguration (JSON-Schema-erzwungen) | US-06 | Phase 2 |
| 5.8 | Prompt-Vorlagen & Token-Optimierung | – | Phase 2 |
| 3.3 | Input-Artefakte definieren (Pydantic + `artefakt.yaml`), gemeinsam mit DZ | US-02 | offen |

Reihenfolge (Entscheidung): **Runner zuerst** (6.3) – ohne LLM testbar, liefert sichtbares Ergebnis; dann Upload, Formular, Branding.

## Repo & Struktur
- GitHub: https://github.com/hoangthanie/Anwendungsentwicklung (Branch `main`; unser Code liegt NUR im Ordner `frontend/`)
- Lokaler Klon (Dominiks Rechner): `C:\dev\Anwendungsentwicklung` (bewusst **außerhalb OneDrive**, weil `.git` + OneDrive-Sync Konflikte verursachen kann)
- Projektunterlagen (nur lesen): OneDrive "Anwendungsentwicklung - General" (PSP, Backlog, Spezifikation, Repository-Doc)
- `frontend/src/dashboard_framework/` – Paketname und Unterordner (`models/`, `eingabe/`, `runner/`) folgen dem Repository-Doc,
  damit später die gemeinsamen Teile von DZ/SJ ohne Umbau passen.
- `frontend/tests/` – pytest, Tests je Story nach Backlog (TF-IDs im Backlog nennen Dateien, z. B. `tests/stories/test_us09_10_runner.py`)
- `frontend/docs/` – Doku mit Erklärungen **was/warum** (Lernziel von Dominik, Teil der Abgabe)

## Verbindliche Schnittstellen (Repository-Doc, Anhang B – Auszug Frontend)
- `models/artefakt`: `Artefakt.aus_yaml(pfad)`, `aehnliche_spalte(name, bekannte)` (DB)
- `eingabe/formular`: `artefakt_aus_formular(daten)`, `spalten_vorschlag(df)` (DB)
- `runner/daten`: `lade_chart_daten(config)`, `uebernehmen(df, db, tabelle)` (DB)
- `runner/framework_lib`: `validate_against_schema(df, schema)` (DB)
- `runner/branding`: `pruefe_logo(pfad)` (DB)
- Chart-Typen erlaubt: `balken`, `linie`, `tabelle`, `kennzahl`. Spaltentypen: `datum`, `text`, `ganzzahl`, `dezimal`, `bool`.
- Streamlit-Dateien bleiben **dünn**; Fachlogik in testbaren Funktionen (Backlog-Hinweis US-01/US-09).

## Harte Regeln (aus Spezifikation/Risikoanalyse)
- Runner führt **nur lesendes SQL** aus (SELECT, genau 1 Statement, DB read-only öffnen) – US-09.2, R14.
- Uploads: Schema-Validierung **vor** dem Schreiben; Logo nur echte PNG/JPEG <= 1 MB, Prüfung per Pillow (nicht Dateiendung) – R15.
- Framework-Code enthält **keine** Sales-Begriffe (region, umsatz, ...) – Generizität, US-12.1.
- Nur synthetische Daten, keine Zugangsdaten ins Repo.
- **KI-Kennzeichnung:** Alles mit Claude Erzeugte muss ins Prompt-Verzeichnis (Repository-Doc Kap. 10, Verantw. MP). Eintrag-Vorlage in `docs/prompt-verzeichnis-entwurf.md` pflegen und an MP geben.
- Tests: pytest; Definition of Done = Testfälle bestanden + 2. Person prüft + Doku aktualisiert.

## Entscheidungen von Dominik (Gesprächsverlauf)
- Frontend zunächst **eigenständig mit Platzhalter-Modellen** (Pydantic nach Spec-Anhang A/B), später gegen die gemeinsamen Modelle von DZ/SJ tauschen (Risiko R07 Schnittstellenbruch). Das Code-Gerüst `dashboard-framework/` aus dem Repository-Doc war im Projektordner nicht auffindbar.
- Umfang inkl. PSP 5.5 und 5.8 (Phase 2).
- Doku-Sprache Deutsch; jede Entscheidung mit Begründung in `docs/`.

## Offene Punkte
- US-10 Upload: nur anhängen (Start-Annahme) oder auch überschreiben? Team muss klären (Spez. 4.7).
- Gemeinsames Code-Gerüst von DZ/SJ in die Repo bringen lassen.
- AP 7.1 (synthetische Daten) hat keine verantwortliche Person.
- ADR 0004 OpenCode vs. Mini-Harness (Spike DZ, bis 30.10.) – beeinflusst Frontend kaum.
- Repo-Doc spricht von "simuliertem Repo ohne GitHub"; PSP 4.1 sagt "GitHub aufgesetzt" – wir nutzen die echte Repo.

## Termine
M2 Fachkonzept 13./14.11.2026 · Coaching 10.11. · M3 Pipeline-Durchstich 18.12.2026 · M4 Feature Freeze 15.01.2027 · Abschluss 26.01.-02.02.2027.

## Setup auf neuem Rechner
```
git clone https://github.com/hoangthanie/Anwendungsentwicklung C:\dev\Anwendungsentwicklung
cd C:\dev\Anwendungsentwicklung\frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
streamlit run src/dashboard_framework/runner/app.py   # sobald vorhanden
```
Python 3.12 verwendet. git user.name/user.email lokal setzen (war auf dem ersten Rechner nicht konfiguriert).

## Arbeitslog (neueste oben)
- 2026-10-27 – Projektunterlagen gelesen, Repo geklont (leer), `frontend/`-Grundstruktur, CLAUDE.md, Doku-Gerüst angelegt. Noch kein Code, noch nichts gepusht.
