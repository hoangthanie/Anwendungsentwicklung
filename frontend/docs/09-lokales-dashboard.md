# 09 – Ein eigenes Artefakt als Dashboard ansehen (Entwicklungsskript)

**Stand:** 2026-10-27 · **Werkzeug:** `tools/baue_lokal.py` · **Wichtig:** Das ersetzt die Pipeline **nicht**; es lässt das Frontend schon jetzt mit eigenen Daten sehen.

## Wozu?
Die Pipeline (Davids Schritte 1, 2, 4 und die Modell-Anbindung) gibt es noch nicht durchgängig. Um ein selbst angelegtes Artefakt (z. B. `artefakte/tickets_am/`) trotzdem als Dashboard zu sehen, baut dieses Skript die fehlenden Teile von Hand nach.

## Was das Skript tut
| Schritt | Pipeline-Schritt (Spezifikation) | Hier |
|---|---|---|
| 1. Daten laden | Schema auslesen (deterministisch, David PSP 5.3) | CSV wird mit dem **Schema des Artefakts** geprüft und umgewandelt (`validate_against_schema`) und in SQLite geladen (`daten.db`) |
| 2. SQL je KPI | Query-Schritt mit Sprachmodell (David PSP 5.4) | SQL kommt aus einer **Datei** (`--sql`), jedes SQL wird auf "nur lesend" geprüft und ausgeführt |
| 3. Dashboard-Konfiguration | Schritt 3 (Dominik PSP 5.5) | **Derselbe Code** wie in der Pipeline (`harness/dashboard.py`: Schema, Prüfung, Zusammensetzen). Nur die Antwort des "Modells" kommt aus einer Datei (`--wahl`) |
| 4. Dokumentation | Schritt 4 (Melanie PSP 5.6) | nicht enthalten |

Ausgabe: `ausgabe/<name>/` mit `daten.db`, `dashboard.json`, Logo. Der Ordner steht in `.gitignore`, weil er Daten und evtl. Firmenlogos enthält.

## Wer war das "Sprachmodell"? (KI-Kennzeichnung)
Beim Beispiel `tickets_am` hat **Claude (nicht das lokale Qwen3)** das SQL je KPI geschrieben und die Darstellung gewählt (Balken, Linie, Kennzahl, Tabelle). Auf diesem Rechner läuft zwar Ollama mit `qwen3:8b`; auf Wunsch von Dominik wurde es **nicht** verwendet. Folgen:
- Das Ergebnis sagt **nichts** darüber, wie gut Qwen3 diese Aufgabe löst. Das bleibt Aufgabe des Spikes (PSP 5.1) und der Messreihe (PSP 8.3).
- Die Prüfungen sind echt: SQL nur lesend, Antwort gegen Schema und Inhalt (jede KPI genau einmal), Zusammensetzen aus Artefakt. Hier lief die Antwort beim ersten Versuch durch.
- Eingetragen im Prompt-Verzeichnis (KI-Einsatz bei PSP 5.5/5.4-Ersatz).

## Aufruf
```
python tools/baue_lokal.py artefakte/<name> <daten.csv>                      # nur laden und Profil der Spalten anzeigen
python tools/baue_lokal.py artefakte/<name> <daten.csv> --sql sql.json --wahl wahl.json
DASHBOARD_CONFIG=ausgabe/<name>/dashboard.json streamlit run src/dashboard_framework/runner/app.py
```
`sql.json`: `{"KPI-Name": "SELECT ..."}`; `wahl.json`: `{"charts": [{"kpi": "...", "typ": "balken|linie|tabelle|kennzahl", "sortierung": "...", "breite": "halb|voll"}, ...]}`.

## Was das Beispiel gezeigt hat (Funde fürs Team)
- **Echte Daten brauchen Datum mit Uhrzeit:** `Created`/`Closed` (z. B. `27.10.2026 11:20:10`). Der Typ `datum` wurde dafür erweitert (E-16).
- **Anführungszeichen statt Backticks** in KPI-Texten und nicht gepaarte Zeichen als Fehler (E-15).
- **Die Kennzahl hat keine Einheit:** "214,8" steht allein; erst die Fußleiste ("in Stunden") erklärt es. Ein Feld `einheit` im `dashboard.json`-Vertrag wäre sinnvoll (mit David abstimmen).
- **Tabellenwerte ohne Tausenderpunkt** (2516 statt 2.516): `st.dataframe` formatiert nicht deutsch; ließe sich per Spaltenformat lösen.
- **Mittelwerte können täuschen:** Die mittlere Bearbeitungsdauer (214,8 Stunden) ist stark von sehr langen Tickets geprägt (Closed Skipped im Mittel 872 Stunden, Closed Complete 159 Stunden). Median oder Auswertung je Status wäre aussagekräftiger. Das ist eine fachliche Frage an den Anwender, nicht an das Framework.
- **Echte Firmendaten:** Die Ticket-Datei sieht nach echten Unternehmensdaten aus. Die Projektregel (Repository-Doc 5.6) sagt: nur synthetische Daten. Die Daten liegen nur lokal (`ausgabe/` ist ignoriert), nichts ging ins Git. Vor Abgabe/Demo besser eine synthetische Variante verwenden.
