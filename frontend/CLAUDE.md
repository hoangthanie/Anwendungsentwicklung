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
| 6.1 | Streamlit-Eingabeoberfläche (Formular -> `artefakt.yaml`, Spaltenauswahl) | US-01, US-02 | fertig (125 Tests, im Browser geprüft); Usability-Test mit Testperson = 6.4 |
| 6.2 | Upload & Branding (Logo-Prüfung mit Pillow, Farbcodes `#RRGGBB`) | US-03 | fertig (83 Tests grün, im Browser geprüft); Einbindung ins Gesamtformular mit 6.1 |
| 6.3 | Dashboard-Runner (liest `dashboard.json`, rendert Charts/Theme/Logo, Daten-Upload) | US-09, US-10 | US-09 fertig, US-10 Upload "nur anhängen" fertig (61 Tests grün, im Browser geprüft); Team muss anhängen/überschreiben klären |
| 6.4 | UI-Feinschliff & Usability-Check mit Testperson | – | offen |
| 5.5 | Pipeline-Schritt 3: Dashboard-Konfiguration (JSON-Schema-erzwungen) | US-06 | Logik fertig, mit FakeLLM getestet (146 Tests); echtes Modell ungetestet (Spike David) |
| 5.8 | Prompt-Vorlagen & Token-Optimierung | – | Phase 2 |
| 3.3 | Input-Artefakte definieren (Pydantic + `artefakt.yaml`), gemeinsam mit DZ | US-02 | Platzhalter-Modell fertig (`models/artefakt.py`), Abstimmung mit DZ offen |

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
- `Artefakt`-Modell (Platzhalter) mit David abstimmen (PSP 3.3/3.4, R07): Feldnamen, Grenzen (12 KPIs), strenge Bezeichner (keine Leerzeichen in Spaltennamen), `Branding.logo`; `artefakte/aktivitaet/` gehört fachlich zu AP 7.4 (David).
- Nächste Frontend-Schritte: PSP 6.4 Usability-Check mit Testperson; PSP 5.8 Prompt-Vorlagen & Token-Optimierung (braucht das echte Modell, Ollama bei David eingerichtet).
- Schritt 3 mit David abstimmen: schmales Modell-Schema statt `DashboardConfig.json_schema()` (E-13), Schnittstelle `LLM.antworte(prompt, schritt, json_schema)`, `harness/__init__.py` (Konfliktgefahr).
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
- `runner/branding.py`: `pruefe_logo(_bytes)`, `bereinige_logo` (neu kodiertes PNG), `speichere_logo` (fester Name `logo.png`), `lade_logo` (nur im Ordner), `normalisiere_farben`, `theme_css`, `BrandingFehler`. Details: docs/05-branding.md.
- `models/artefakt.py`: `Artefakt`, `Kpi`, `ArtefaktFehler` (Fail-Fast im `model_validator`: KPI-Spalten in Backticks gegen Spalten, strenge Bezeichner, `extra=forbid`, YAML `safe_load`). Details: docs/06-eingabe.md.
- `eingabe/formular.py`: `artefakt_aus_formular`, `spalten_vorschlag`, `zeilen_aus_tabelle`, `speichere_artefakt_ordner`, `vorhandene_artefakte`. `eingabe/branding_form.py`: `baue_branding`.
- `eingabe/app.py`: vollständiges Formular (Grunddaten, Spalten-/KPI-Editor, Branding, laufende Prüfung, Download/Speichern nach `frontend/artefakte/<name>/`; Env `ARTEFAKT_ORDNER`). Start: `streamlit run src/dashboard_framework/eingabe/app.py`.
- `harness/dashboard.py` (Schritt 3, PSP 5.5): `erzeuge_config(artefakt, sql_je_kpi, llm, max_versuche)`; Modell wählt nur typ/farbe/sortierung/breite (Schema `wahl_schema`), SQL/Name/Tabelle/Branding setzt der Code; Prüfung + Reparaturschleife; `LLMProtokoll` = `antworte(prompt, schritt, json_schema)` (Annahme zu Davids `harness/llm.py`). Tests mit `tests/fakes.py:FakeLLM`. Details: docs/07-dashboard-schritt.md.
- `artefakte/sales/` (Referenzfall) und `artefakte/aktivitaet/` (Entwurf fürs 2. Dashboard, mit David abstimmen); Test `test_alle_artefakte_im_repo_sind_gueltig` prüft alle.
- Gestaltung: `DESIGN.md` (Gestaltungssystem), `PRODUCT.md`, `.impeccable/design.json`, `ui/theme.py` (globales CSS, Kontrastfunktionen), `ui/komponenten.py` (Schriftfeld, Feldkopf, Fußleiste, Marke, Kennzahl). Neue Seiten im selben System bauen (siehe docs/08-gestaltung.md). Schriften liegen doppelt (runner/static, eingabe/static), weil Streamlit nur neben dem Startskript ausliefert; Test prüft Gleichheit.
- `.streamlit/config.toml`: `maxUploadSize = 5` (MB), festes helles Theme, lokale Schriften. App immer aus dem Ordner `frontend` starten, damit sie gelesen wird.
- Nach Änderungen an Modulen (nicht nur app.py) den Streamlit-Server neu starten. Port-Freigabe notfalls per PowerShell (`Get-NetTCPConnection -LocalPort 8511`).
- `examples/sales/`: Beispiel-`dashboard.json` und `make_demo_db.py` (erzeugt `daten.db`, gitignored).
- Tests: `python -m pytest` im Ordner `frontend` (venv: `.venv`). Starten der App siehe docs/03-runner.md.
- Arbeitsweise: Streamlit-Dateien dünn, Logik in reinen Funktionen; neue Funktion = Eintrag in docs/.
- Hinweis Tooling: Die automatische Befehlsprüfung der Claude-App fiel oft aus; Schreibvorgänge einfach wiederholen.

## Arbeitslog (neueste oben)
- 2026-10-27 – Raspberry-Pi-Plan (docs/10-raspberry-pi.md): Pi 4 mit 2 GB zeigt nur den Runner, Erzeugen/Ollama bleibt auf dem PC. Neu `deploy/` (Dockerfile, docker-compose.yml mit 700-MB-Grenze, requirements-runner.txt) + `.dockerignore`. Zugriff erst LAN, spaeter Tailscale. NICHT getestet (kein Docker auf dem Entwicklungsrechner). Docker-Setup macht Dominik auch, mit Stephanie (CI) abstimmen.
- 2026-10-27 – KPI-Spaltenauswahl: nur noch **eine** Leiste unten in Feld 3 statt je KPI. Ziel = KPI, in die zuletzt getippt wurde (serverseitig aus geändertem Text erkannt, `waehle_ziel_kpi`/`finde_geaenderte_kpi` in `eingabe/formular.py`; Anzeige "Spalte einfügen in: …"). Einfügen an der echten Cursorposition geht in Streamlit nicht (nur mit eingebettetem Skript, anfällig), daher Ende des Textes. 193 Tests grün, im Browser geprüft (Port 8512). Lokal committet, nicht gepusht.
- 2026-10-27 – **Erster Push nach GitHub** (hoangthanie/Anwendungsentwicklung, Branch `main`, 13 Commits, Ordner `frontend/`). Anmeldung über Git Credential Manager (Browserfenster beim ersten Push, keine CLI-Anmeldung nötig). Nicht im Git (gitignored): `ausgabe/`, `artefakte/tickets_am/`, `artefakte/*/logo.png`, `examples/sales/kundenlogo.png` (Firmendaten/Firmenlogo). Lokal mit `git update-index --skip-worktree` ausgeblendet: `artefakte/sales/artefakt.yaml` und `examples/sales/dashboard.json` (eigene Logo-Einträge); rückgängig mit `git update-index --no-skip-worktree <Datei>`. Frühere Log-Zeilen mit "Noch nicht gepusht" sind damit überholt.
- 2026-10-27 – Artefakt `tickets_am` (eigene Ticket-CSV, 17.421 Zeilen) als Dashboard gebaut mit `tools/baue_lokal.py` (docs/09-lokales-dashboard.md): Daten per Schema geladen, SQL und Darstellungswahl von Claude geschrieben (bewusst OHNE Ollama/Qwen3 auf Wunsch von Dominik), Schritt 3 mit echtem Code geprüft. Ausgabe in `ausgabe/` (gitignored: Daten und Firmenlogo). Neu: Hinweis (keine Pflicht) bei leeren Spaltenbeschreibungen (`Artefakt.spalten_ohne_beschreibung`), Logo-Vorschau-Layout, Datum mit Uhrzeit, Anführungszeichen statt Backticks. 189 Tests grün. Laufendes Beispiel: Port 8513. Offene Funde: Kennzahl ohne Einheit, Tabellen ohne Tausenderpunkt. Noch nicht gepusht.
- 2026-10-27 – Gemeinsamer Test der Eingabe-App mit echter Datei (`test_tickets.csv`, 17.421 Zeilen, Semikolon, Datum mit Uhrzeit). Funde: (1) Typ `datum` kannte keine Uhrzeit -> erweitert (E-16, `framework_lib.konvertiere_spalte`); (2) Anwender tippt Spaltennamen ohne Backticks; ungepaarter Backtick wurde stillschweigend überlesen -> Anführungszeichen ("Name" oder „Name“) als Spaltenverweis, gespeichert wird weiter `Name` mit Backticks, nicht gepaarte Zeichen = Fehler, KPI-Eingabe als Einzelfelder mit anklickbaren Spalten (`st.pills`, hängt am Ende an) (E-15). 188 Tests grün, im Browser geprüft. Noch nicht gepusht.
- 2026-10-27 – Neugestaltung beider Apps mit dem Impeccable-Skill (github.com/pbakaus/impeccable, lokal in ~/.claude/skills/impeccable): PRODUCT.md, Richtungsauswahl (Wurf "Formblatt"), Gestaltungsvertrag (.impeccable/surfaces), gemeinsames Paket `ui/` (theme.py, komponenten.py), lokale Schriften Barlow in runner/static und eingabe/static, Schriftfeld + nummerierte Felder + Zustandsmarken, Kundenfarbe nur als Akzent. Unabhängiges Review (8 Funde, alle umgesetzt oder begründet abgelehnt), DESIGN.md + .impeccable/design.json. Neues optionales Feld `Chart.beschreibung` (mit David abstimmen). 172 Tests grün, im Browser gemessen. docs/08-gestaltung.md. Noch nicht gepusht.
- 2026-10-27 – Fund aus Dominiks Browser-Test (B3): Fehlermeldung zum Tabellennamen stand nur ganz unten, Feld wurde nach Verlassen wieder normal. Fix: Status-Box oben + Meldung direkt unter dem betroffenen Feld (`meldungen_zu_feld`), leere Pflichtfelder nur oben (nicht rot unter jedem unberührten Feld); leeres `name`/`tabelle` meldet jetzt "Pflichtfeld ist leer" wie die anderen. Hinweis zu Streamlit: Textfelder übernehmen Eingaben erst bei Enter/Verlassen (roter Rand = "noch nicht übernommen"). Testdateien für Handtests unter `examples/testdateien/`. 149 Tests grün. Noch nicht gepusht (6 Commits + dieser).
- 2026-10-27 – Phase 2, PSP 5.5 / US-06: Pipeline-Schritt 3 `harness/dashboard.py` (schmales Modell-Schema mit Enums, Prompt, Antwortprüfung auf Format und Inhalt, Reparaturschleife mit Fehlertext, JSON aus Codeblöcken retten, SQL-Vorprüfung, Abbruch statt Ersatz), `tests/fakes.py:FakeLLM`, 21 neue Tests (146 gesamt grün), Integration mit Runner. Entscheidungen E-13/E-14, docs/07. Tests nachgeschärft (schwache Assertion, Fixture). Mit echtem Modell NICHT getestet. Noch nicht gepusht (5 Commits + dieser).
- 2026-10-27 – Eingabeformular (PSP 6.1/3.3, US-01/02): `Artefakt`-Modell mit Fail-Fast (KPI-Spalten in Backticks, "meinten Sie", strenge Bezeichner gegen SQL-/Pfad-Einschleusung, `extra=forbid`, `safe_load`), Formularlogik, vollständige Eingabe-App (Tabellen-Editor, CSV-Spaltenvorschlag, laufende Prüfung, Laden/Speichern/Download), Beispiel-Artefakte sales + aktivitaet (Entwurf). 125 Tests grün; Browser: Artefakt laden, CSV mit `Person` -> "meinten Sie `Person`?". Entscheidungen E-10 bis E-12, docs/06-eingabe.md. Noch nicht gepusht (4 Commits + dieser).
- 2026-10-27 – Branding (PSP 6.2 / US-03): Logo-Prüfung (Inhalt statt Endung, nur PNG/JPEG, 1 MB, 4000 px, Neu-Kodierung zu `logo.png`), sicheres Laden (kein Pfad aus dem Ordner), Farben `#RRGGBB`, Akzentfarbe per CSS, festes helles Theme, Eingabe-Entwurfsseite. 83 Tests grün; Browser: Runner mit Logo, Eingabe mit Skript-Datei/PNG/falschen Farben. Gefunden/gefixt: CSS-Selektoren passten nicht zu Streamlit 1.66; Fehlermeldung zeigte Farben in Großbuchstaben. Entscheidungen E-08/E-09, docs/05-branding.md. Noch nicht gepusht (3 Commits + dieser).
- 2026-10-27 – Daten-Upload (US-10) "nur anhängen": Schema-Validierung mit Typumwandlung, Fehlerliste, Vorschau, Doppel-Upload-Warnung, atomares Schreiben, 5-MB-Limit. 61 Tests grün. Im Browser geprüft (fehlerhafte und gültige CSV; DB 192 -> 194 Zeilen, Chart aktualisiert sich). Gefunden/gefixt: App startete im Browser nicht (Paket nicht installiert, nur pytest hatte den Pfad) -> `pip install -e .` in requirements.txt; leere Logo-Spalte im Kopf; englische pandas-Fehlertexte in Meldungen. Entscheidungen E-06/E-07, docs/04-upload.md. Noch nicht gepusht.
- 2026-10-27 – Runner-Grundversion (PSP 6.3 / US-09): Config-Modell, SQL-Sicherheit, Datenladen, Charts, Streamlit-App, Beispiel + Demo-DB, 36 Tests grün (inkl. AppTest-Rauchtest), docs/03-runner.md. Visuelle Browser-Prüfung steht noch aus. Bug gefunden/gefixt: numpy.int64 in kennzahl_wert. Noch nicht gepusht (Dominik wollte erst den Runner).
- 2026-10-27 – Projektunterlagen gelesen, Repo geklont (leer), `frontend/`-Grundstruktur, CLAUDE.md, Doku-Gerüst angelegt. Noch kein Code, noch nichts gepusht.
