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
| 6.3 | Dashboard-Runner (liest `dashboard.json`, rendert Charts/Theme/Logo, Daten-Upload) | US-09, US-10 | US-09 fertig, US-10 Upload "nur anhängen" fertig (61 Tests grün, im Browser geprüft); Team muss anhängen/überschreiben klären |
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
- US-10 Upload: umgesetzt ist "nur anhängen". Soll es zusätzlich Überschreiben/"Monat ersetzen" geben (braucht Schlüsselspalte im Schema)? Team muss klären (Spez. 4.7).
- `DashboardConfig.spalten` (neu) mit David abstimmen: Das gemeinsame Modell (PSP 3.4) muss das Schema für den Upload enthalten.
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

## Code-Stand (Kurzüberblick)
- `models/dashboard_config.py`: Platzhalter-Modell `DashboardConfig`/`Chart`/`Branding` (Chart-Typen, Farbformat, eindeutige Titel).
- `runner/sicherheit.py`: `pruefe_nur_lesend`, `verbinde_nur_lesend` (2 Schichten, siehe docs/03-runner.md).
- `runner/daten.py`: `lade_chart_daten`, `sortiere`, `achsen`, `layout_zeilen`. `runner/charts.py`: Plotly-Figuren, Kennzahl. `runner/app.py`: dünne Streamlit-UI.
- `models/spalten.py`: `SpaltenDef`, `aehnliche_spalte` ("meinten Sie ...?"). `DashboardConfig.spalten` = Schema; Upload-Tab erscheint nur, wenn es gesetzt ist.
- `runner/framework_lib.py`: `lese_csv`, `validate_against_schema`, `zaehle_vorhandene_zeilen`, `uebernehmen` (atomar, einziger Schreibpfad), `UploadFehler`. Details: docs/04-upload.md.
- `.streamlit/config.toml`: `maxUploadSize = 5` (MB). App immer aus dem Ordner `frontend` starten, damit sie gelesen wird.
- `examples/sales/`: Beispiel-`dashboard.json` und `make_demo_db.py` (erzeugt `daten.db`, gitignored).
- Tests: `python -m pytest` im Ordner `frontend` (venv: `.venv`). Starten der App siehe docs/03-runner.md.
- Arbeitsweise: Streamlit-Dateien dünn, Logik in reinen Funktionen; neue Funktion = Eintrag in docs/.
- Hinweis Tooling: Die automatische Befehlsprüfung der Claude-App fiel oft aus; Schreibvorgänge einfach wiederholen.

## Arbeitslog (neueste oben)
- 2026-10-27 – Daten-Upload (US-10) "nur anhängen": Schema-Validierung mit Typumwandlung, Fehlerliste, Vorschau, Doppel-Upload-Warnung, atomares Schreiben, 5-MB-Limit. 61 Tests grün. Im Browser geprüft (fehlerhafte und gültige CSV; DB 192 -> 194 Zeilen, Chart aktualisiert sich). Gefunden/gefixt: App startete im Browser nicht (Paket nicht installiert, nur pytest hatte den Pfad) -> `pip install -e .` in requirements.txt; leere Logo-Spalte im Kopf; englische pandas-Fehlertexte in Meldungen. Entscheidungen E-06/E-07, docs/04-upload.md. Noch nicht gepusht.
- 2026-10-27 – Runner-Grundversion (PSP 6.3 / US-09): Config-Modell, SQL-Sicherheit, Datenladen, Charts, Streamlit-App, Beispiel + Demo-DB, 36 Tests grün (inkl. AppTest-Rauchtest), docs/03-runner.md. Visuelle Browser-Prüfung steht noch aus. Bug gefunden/gefixt: numpy.int64 in kennzahl_wert. Noch nicht gepusht (Dominik wollte erst den Runner).
- 2026-10-27 – Projektunterlagen gelesen, Repo geklont (leer), `frontend/`-Grundstruktur, CLAUDE.md, Doku-Gerüst angelegt. Noch kein Code, noch nichts gepusht.
