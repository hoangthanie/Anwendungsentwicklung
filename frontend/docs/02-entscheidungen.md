# 02 – Entscheidungslog Frontend

Format: Kontext – Alternativen – Entscheidung – Konsequenz. Neueste Einträge unten anhängen.

## E-01 – Lokaler Klon außerhalb von OneDrive (2026-10-27)
- **Kontext:** Repo soll lokal liegen; der Uni-Ordner liegt in OneDrive.
- **Alternativen:** (A) Klon in OneDrive, (B) Klon unter `C:\dev`.
- **Entscheidung:** B, `C:\dev\Anwendungsentwicklung`.
- **Warum:** OneDrive synchronisiert viele kleine Dateien im `.git`-Ordner und kann sie sperren oder Konflikte/Korruption erzeugen. Die Versionskontrolle läuft ohnehin über GitHub, ein Backup durch OneDrive ist unnötig.
- **Konsequenz:** Auf einem neuen Rechner einfach neu klonen; Kontext steht in `frontend/CLAUDE.md`.

## E-02 – Platzhalter-Modelle statt gemeinsamer Verträge (2026-10-27)
- **Kontext:** Das im Repository-Doc erwähnte Gerüst `dashboard-framework/` (Pydantic-Modelle) ist nicht auffindbar.
- **Alternativen:** (A) warten, (B) eigenständig mit Platzhaltern starten.
- **Entscheidung:** B – eigene schlanke Pydantic-Modelle nach Spec Anhang A/B.
- **Warum:** Sonst blockiert das Frontend monatelang. Die Modelle sind klein und werden später gegen die gemeinsamen getauscht.
- **Konsequenz:** Risiko R07 (Schnittstellenbruch). Gegenmaßnahme: Feldnamen exakt aus Anhang A übernehmen, Vertrags-Tests schreiben.

## E-03 – Paketstruktur wie im Repository-Doc (2026-10-27)
- **Entscheidung:** `frontend/src/dashboard_framework/{models,eingabe,runner}` und `frontend/tests`.
- **Warum:** Gleiche Pfade und Modulnamen wie Anhang B, damit Testfälle (TF-IDs nennen Dateien) und spätere Zusammenführung ohne Umbenennen funktionieren. `src/`-Layout verhindert, dass Tests versehentlich nicht installierten Code importieren.

## E-04 – Dünne Streamlit-Dateien, Fachlogik in reinen Funktionen (2026-10-27)
- **Warum:** Streamlit-Code ist schwer automatisiert zu testen. Liegt die Logik (Validierung, Datenladen, Upload-Prüfung) in normalen Funktionen, genügt `pytest` ohne Browser. Das fordert auch das Backlog (Hinweise zu US-01 und US-09).

## E-06 – Upload zunächst "nur anhängen" (2026-10-27)
- **Kontext:** Spezifikation 4.7 lässt offen, ob der Upload anhängen oder überschreiben soll.
- **Alternativen:** (A) nur anhängen, (B) zusätzlich "Monat ersetzen" über eine Schlüsselspalte.
- **Entscheidung:** A als Startvariante (Auftrag von Dominik), Entscheidung für B im Team offen.
- **Warum:** Sicher (keine Beschädigung bestehender Daten), einfach, kommt ohne Schlüsselspalte im generischen Schema aus.
- **Konsequenz:** Fehlerhafte Uploads sind aus der App nicht korrigierbar; Mitigation: Vorschau, Warnung vor Doppel-Upload, atomares Schreiben. Details: docs/04-upload.md.

## E-07 – Paket per `pip install -e .` statt Pfad-Trick (2026-10-27)
- **Kontext:** App startete im Browser nicht, obwohl pytest grün war (Importpfad nur in pytest gesetzt).
- **Entscheidung:** Das Frontend ist ein installierbares Paket (`pyproject.toml`, `-e .` in `requirements.txt`).
- **Warum:** Ein einheitlicher, offizieller Weg für Tests, `streamlit run` und später das Docker-Image; kein `sys.path`-Hack und keine Umgebungsvariable `PYTHONPATH`.

## E-08 – Logo wird neu kodiert und unter festem Namen gespeichert (2026-10-27)
- **Alternativen:** (A) Original speichern, wenn die Prüfung besteht, (B) mit Pillow neues PNG erzeugen.
- **Entscheidung:** B, immer als `logo.png`, höchstens 1024 px.
- **Warum:** Eine bestandene Prüfung garantiert nicht, dass die Datei *nur* ein Bild ist (angehängte Daten, Metadaten). Nur selbst erzeugte Bytes werden gespeichert. Details: docs/05-branding.md.

## E-09 – Festes helles Theme (2026-10-27)
- **Warum:** Firmenfarben sind für helle Hintergründe gestaltet; auf dunklem Theme war Marineblau kaum lesbar. Preis: Das Theme folgt nicht der Einstellung des Betrachters.

## E-10 – Prüfregeln im Artefakt-Modell statt im Formular (2026-10-27)
- **Alternativen:** (A) Prüfung nur im Formular, (B) im Modell (`model_validator`).
- **Entscheidung:** B.
- **Warum:** Jeder Weg zum Artefakt (Formular, von Hand editierte YAML, Pipeline) läuft durch dieselbe Prüfung; sonst ließe sich Fail-Fast umgehen. Details: docs/06-eingabe.md.

## E-11 – Strenge Bezeichner und `extra="forbid"` (2026-10-27)
- **Entscheidung:** `name`, `tabelle` und Spaltennamen nur Buchstaben/Ziffern/`_` (kein Leerzeichen); unbekannte YAML-Felder sind Fehler; höchstens 12 KPIs.
- **Warum:** Diese Werte werden Ordnernamen und SQL; Tippfehler in Feldnamen würden sonst still ignoriert. **Preis:** Dateien mit Leerzeichen in Spaltennamen müssen umbenannt werden (Meldung erklärt das). Mit David abstimmen.

## E-12 – YAML mit `safe_load` und Größenlimit (2026-10-27)
- **Warum:** `yaml.load` kann Code ausführen; `safe_load` nicht. Teil des Sicherheitskonzepts (AP 4.6).

## E-13 – Schritt 3: Modell wählt nur Darstellung, nie SQL (2026-10-27)
- **Alternativen:** (A) Modell erzeugt die komplette `dashboard.json` (Backlog-Hinweis: `DashboardConfig.json_schema()`), (B) Modell wählt nur Typ/Farbe/Sortierung/Breite, der Code setzt alles Übrige.
- **Entscheidung:** B, mit schmalem Schema (`wahl_schema`) und Endprüfung durch `DashboardConfig`.
- **Warum:** Das geprüfte SQL aus Schritt 2 kann nicht verändert werden; weniger Ausgabe = weniger Fehler und Tokens; Name/Tabelle/Farben kommen laut US-06.2 aus dem Artefakt. Mit David abstimmen. Details: docs/07-dashboard-schritt.md.

## E-14 – Abbruch statt stiller Ersatzkonfiguration (2026-10-27)
- **Entscheidung:** Nach `max_versuche` ungültiger Antworten gibt es einen `DashboardFehler`, keine Standard-Konfiguration.
- **Warum:** Fail-Fast: Ein Ersatz würde ein untaugliches Modell/Prompt verstecken. Ein expliziter Ersatzmodus wäre später möglich.

## E-15 – Spaltenverweise in Anführungszeichen, Speicherung mit Backticks (2026-10-27)
- **Kontext:** Test mit echter Ticket-Datei: Backticks sind für Fachanwender nicht zumutbar; ein ungepaarter Backtick wurde stillschweigend überlesen.
- **Alternativen:** (A) Backticks beibehalten und besser erklären, (B) nur noch Anführungszeichen (Vertrag mit der Pipeline ändern), (C) Anführungszeichen **und** Backticks erlaubt, gespeichert wird Backtick.
- **Entscheidung:** C, dazu Fehlermeldung bei nicht gepaarten Zeichen und anklickbare Spalten.
- **Warum:** Der Anwender tippt Gewohntes; der Vertrag `artefakt.yaml` und alte Dateien bleiben unverändert. Mit David abstimmen, falls seine Pipeline Backticks nicht nur aus dem Artefakt, sondern auch aus Rohtext erwartet. Details: docs/06-eingabe.md.

## E-16 – Datum mit Uhrzeit (2026-10-27)
- **Kontext:** Ticket-CSV mit `27.10.2026 11:20:10`; der Typ `datum` kannte nur Datumsangaben und schlug "text" vor.
- **Entscheidung:** `datum` akzeptiert ISO und deutsche Schreibweise, jeweils mit oder ohne Uhrzeit. Gespeichert wird `JJJJ-MM-TT` bzw. `JJJJ-MM-TT HH:MM:SS` (nur wenn die Daten eine Uhrzeit enthalten). Gemischte Formate in einer Spalte bleiben ein Fehler.

## E-05 – Reihenfolge: Runner zuerst (2026-10-27)
- **Warum:** Der Runner braucht kein LLM, nur eine Beispiel-`dashboard.json` und eine Test-DB. Er ist früh sichtbar (Demo-fähig) und prägt das Format, das die Pipeline erzeugen muss. Danach Upload, Formular, Branding.
