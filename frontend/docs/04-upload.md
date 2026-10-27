# 04 – Daten-Upload (PSP 6.3, US-10)

**Stand:** 2026-10-27 · **Status:** Variante "nur anhängen" fertig und im Browser getestet · **Offen:** Teamentscheidung anhängen/überschreiben

## Wofür?
Ein Dashboard bleibt nur nützlich, wenn neue Daten (z. B. die Monatszahlen) hineinkommen. Der Anwender lädt dazu eine CSV-Datei hoch.
Die Pipeline mit dem Sprachmodell muss dafür **nicht** erneut laufen, weil das SQL der Charts allgemein formuliert ist (`GROUP BY ...`) und
automatisch mit neuen Zeilen arbeitet (Spezifikation 4.2).

## Ablauf (so sieht es der Anwender)
1. Tab **Daten aktualisieren** öffnen, CSV auswählen.
2. Die App prüft sofort. Bei Fehlern erscheint eine Liste (was fehlt, welche Spalte, welcher Wert in welcher Zeile). Es wird nichts geschrieben.
3. Bei gültiger Datei: Meldung "n Zeilen sind gültig", Vorschau der ersten 10 Zeilen (so wie sie gespeichert würden), ggf. Warnung vor Doppel-Upload.
4. Erst der Klick auf **Übernehmen** schreibt. Danach ist das Upload-Feld wieder leer und das Dashboard zeigt die neuen Werte.

## Dateien und Funktionen (`runner/framework_lib.py`)
| Funktion | Aufgabe |
|---|---|
| `lese_csv(bytes)` | Größe prüfen (5 MB), UTF-8 prüfen, Trennzeichen automatisch erkennen (`,` oder `;`), alles zunächst als **Text** lesen |
| `validate_against_schema(df, schema)` | Spalten abgleichen, jede Spalte in den Zieltyp umwandeln, **alle** Fehler sammeln, bereinigten DataFrame liefern |
| `zaehle_vorhandene_zeilen(df, db, tabelle)` | Wie viele Zeilen gibt es schon genau so? (Warnung vor Doppel-Upload) |
| `uebernehmen(df, db, tabelle)` | Zeilen in **einer Transaktion** anhängen, Anzahl zurückgeben |
| `UploadFehler` | Eine Ausnahme mit Liste verständlicher Meldungen |
| `models/spalten.py` | `SpaltenDef` (Name, Typ) und `aehnliche_spalte` ("meinten Sie ...?", auch für das Formular US-02.3) |

Das Schema kommt aus der `dashboard.json` (neues Feld `spalten`). Gibt es keins, wird der Tab nicht angezeigt.

## Entscheidungen und Begründung

### "Nur anhängen" als Startvariante
Die Spezifikation (4.7) lässt offen, ob auch überschrieben werden darf. Anhängen ist die sichere Variante: Der Upload kann bestehende Daten nicht beschädigen,
und es braucht keine Regel, *welche* Zeilen ersetzt werden (dafür bräuchte jede Tabelle einen Schlüssel, den unser generisches Schema nicht kennt).
Preis: Eine fehlerhaft hochgeladene Monatsdatei lässt sich nicht aus der App korrigieren. Dafür ist die Warnung vor Doppel-Uploads da.
**Für das Team:** Wollen wir das? Alternative wäre ein zusätzlicher Modus "Monat ersetzen" mit Schlüsselspalte. Entscheidung im Jour fixe.

### Erst prüfen und umwandeln, dann schreiben (Fail-Fast)
Fehler werden vor dem Schreiben abgefangen und erreichen nie die Datenbank. Das ist das Prinzip des ganzen Projekts (Fehler früh statt erst in der Demo)
und die Gegenmaßnahme zu Risiko R15 (fehlerhafte Uploads).

### CSV zunächst komplett als Text lesen
Liest man mit automatischer Typerkennung, "rät" pandas (z. B. `007` -> `7`, Datum -> Text oder Zahl). Wir lesen alles als Text und entscheiden **allein anhand des Schemas**.
Damit ist das Ergebnis vorhersehbar und für jedes Dashboard gleich.

### Alle Fehler gemeinsam melden
Wer eine Datei dreimal hochlädt, weil jedes Mal nur der erste Fehler gemeldet wird, ärgert sich. Wir sammeln alle Meldungen: fehlende Spalten, unbekannte Spalten
(mit Hinweis "meinten Sie `umsatz`?", wenn nur die Schreibweise abweicht) und Typfehler mit Beispielwert und Zeile (Zeilennummer wie in Excel, Kopfzeile = 1).

### Typen strikt, aber alltagstauglich
| Typ | akzeptiert | wird gespeichert als |
|---|---|---|
| `ganzzahl` | `7`, `7.0` | ganze Zahl (`1.5` wird abgelehnt) |
| `dezimal` | `1.5`, `1,5` | Kommazahl; `1.234,5` ist mehrdeutig und wird abgelehnt |
| `datum` | `2026-12-31`, `31.12.2026` | Text `YYYY-MM-DD` (sortierbar, mit `strftime` in SQLite nutzbar) |
| `bool` | `ja/nein`, `true/false`, `1/0` | `1`/`0` |
| `text` | alles | Text (leer = leer/NULL) |
Leere Werte sind bei allen Typen außer `text` verboten, weil eine leere Zahl sonst im Diagramm still als Lücke oder 0 endet.
Unbekannte zusätzliche Spalten werden abgelehnt statt ignoriert: lieber eine klare Rückmeldung als Daten, die stillschweigend fehlen.

### Atomares Schreiben
`uebernehmen` schreibt alle Zeilen in einer Transaktion (`with verbindung:`). Scheitert eine Zeile, wird **nichts** übernommen. Ein Test erzwingt das mit einer `NOT NULL`-Spalte.
Die Datenbank wird mit `mode=rw` geöffnet: existiert die Datei nicht, gibt es einen Fehler, statt dass SQLite stillschweigend eine neue leere anlegt.

### Schreiben nur hier, nur nach Prüfung
Die Anzeige-Funktionen öffnen die DB nur lesend (siehe 03-runner). Der Upload ist der **einzige** Schreibpfad. Tabellen- und Spaltennamen werden nie blind in SQL eingesetzt:
Die Tabelle muss in `sqlite_master` existieren, die Spalten müssen in der Tabelle vorkommen, Namen werden zusätzlich in Anführungszeichen gesetzt (Schutz vor SQL-Injection; Test mit
bösartigem Tabellennamen). Werte gehen immer als Parameter (`?`) in die Abfrage.

### Größenlimit zweifach
`MAX_UPLOAD_BYTES = 5 MB` in Code **und** `.streamlit/config.toml` (`maxUploadSize = 5`). Streamlit erlaubt sonst 200 MB. Das Limit im Server greift, bevor die Datei im Speicher liegt.

### Warnung vor Doppel-Upload (statt Sperre)
Wer dieselbe Datei zweimal hochlädt, verdoppelt seine Umsätze. Wir zählen Zeilen, die **vollständig identisch** schon existieren, und warnen. Wir sperren nicht, weil identische
Zeilen legitim sein können (zwei gleiche Verkäufe am selben Tag).

### Nach dem Übernehmen: neues Upload-Feld
Streamlit behält die ausgewählte Datei über Neuladen hinweg. Ohne Gegenmaßnahme würde sie nach "Übernehmen" erneut geprüft und könnte versehentlich ein zweites Mal übernommen werden.
Deshalb bekommt das Upload-Feld nach Erfolg einen neuen Schlüssel (`upload_nr` + 1) und ist wieder leer.

## Tests
`tests/test_framework_lib.py` (TF-035 bis TF-037 plus Typen, Fehlersammlung, CSV, Atomarität, SQL-Injection, Doppel-Erkennung),
`tests/stories/test_us09_10_runner.py` (TF-034 Upload wird angehängt, falscher Upload ändert nichts), `tests/stories/test_us02_03_artefakt.py` (TF-006).
Zusätzlich im Browser geprüft (Demo-DB): fehlerhafte CSV -> Fehlerliste mit Hinweis; gültige CSV (Semikolon, `15.01.2027`, `12000,50`) -> Vorschau mit `2027-01-15` / `12000.5`,
nach "Übernehmen" 192 -> 194 Zeilen und der neue Monat erscheint im Verlauf **ohne manuelles Neuladen des Caches** (US-10.3).

## Lernnotizen aus dem Test
- **Paket nicht gefunden:** Die App startete im Browser nicht (`No module named 'dashboard_framework'`), obwohl `pytest` grün war. `pytest` hatte `src/` selbst in den Suchpfad gelegt (`pyproject.toml`),
  `streamlit run` nicht. Lösung: Das Paket wird mit `pip install -e .` installiert (steht jetzt in `requirements.txt`). Lehre: Rauchtests im echten Start ergänzen Unit-Tests.
- **Server-Neustart:** Streamlit lädt geänderte Module aus einem installierten Paket nicht immer neu; nach Änderungen an Nicht-App-Dateien den Server neu starten.
- **Fehlermeldungen:** pandas liefert englische Fehlertexte ("Unable to parse string ..."). Die zeigen wir bewusst nicht an, sondern formulieren eigene.

## Offen
- Teamentscheidung anhängen/überschreiben (siehe oben), ggf. Schlüsselspalte im Schema.
- Datensicherung vor dem Schreiben (z. B. Kopie `daten.db.bak`)? Gehört zu David (Deployment, Risiko R11); hier nur als Hinweis.
- Mehrere Personen gleichzeitig: SQLite wartet bis zu 10 s auf eine Sperre; für den Referenzfall (ein Anwender) ausreichend.
