# ADR 0011: Spaltenverweise in KPI-Texten in Anführungszeichen, gespeichert mit Backticks; Datum mit Uhrzeit

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 27.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 6.1, 3.3 (DB, gemeinsam mit DZ)

## Kontext
In KPI-Beschreibungen sollen Fachanwender Spalten benennen („Summe von `betrag`, gruppiert nach `region`“). Die Pipeline erwartet die Spaltennamen in Backticks, damit sie sicher gefunden und geprüft werden können. Beim Test mit einer echten Ticket-Datei zeigte sich: Backticks sind für Fachanwender nicht zumutbar (Tastenkombination, nicht sichtbar), und ein ungepaarter Backtick wurde stillschweigend überlesen. Außerdem enthielt die Ticket-Datei Zeitstempel wie `27.10.2026 11:20:10`, der Typ `datum` kannte nur Datumsangaben, deshalb schlug das Formular „text“ vor.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: Backticks beibehalten, besser erklären | Vertrag mit der Pipeline bleibt | Anwender scheitern weiter daran |
| B: nur noch Anführungszeichen (Vertrag ändern) | gewohnt | Vertrag und alte Artefakte ändern sich, Pipeline muss angepasst werden |
| **C: Anführungszeichen und Backticks erlaubt, gespeichert wird mit Backticks** | Anwender tippt Gewohntes, `artefakt.yaml` und die Pipeline bleiben unverändert | zwei Schreibweisen im Eingabeweg, Umwandlung nötig |

Für das Datum: (A) nur Datum, (B) Datum und Uhrzeit, ISO und deutsch, nur wenn die Daten eine Uhrzeit enthalten.

## Entscheidung
Wir wählen **C**. Der Anwender setzt Spaltennamen in Anführungszeichen („…“ oder "…"); beim Speichern wandelt das Modell sie in Backticks um. Nicht gepaarte Anführungszeichen oder Backticks sind ein Fehler mit klarer Meldung. Das Formular zeigt die vorhandenen Spalten zum Anklicken. Der Typ `datum` akzeptiert ISO und deutsche Schreibweise, jeweils mit oder ohne Uhrzeit; gespeichert wird `JJJJ-MM-TT` bzw. `JJJJ-MM-TT HH:MM:SS`. Gemischte Formate in einer Spalte bleiben ein Fehler.

## Konsequenzen
- Der Vertrag `artefakt.yaml` bleibt für David unverändert: Backticks kommen weiterhin aus dem Artefakt an.
- **Mit David abstimmen**, falls Schritt 2 oder 3 Backticks auch aus freiem Rohtext erwartet und nicht nur aus dem gespeicherten Artefakt.
- Die Spaltenauswahl ist eine Leiste unten im KPI-Feld und fügt in die zuletzt bearbeitete KPI ein (am Textende, die genaue Cursorposition kennt Streamlit nicht).
- Zeitstempel funktionieren: Datum-Typ-Erkennung, Anzeige und Sortierung im Runner behandeln die Uhrzeit mit.

## Belege
- `frontend/docs/02-entscheidungen.md` (E-15, E-16), `frontend/docs/06-eingabe.md`
- `frontend/src/dashboard_framework/models/artefakt.py` (`anfuehrungszeichen_zu_backticks`), `frontend/src/dashboard_framework/eingabe/formular.py`
