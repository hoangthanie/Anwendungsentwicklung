# ADR 0007: Schritt 1 deterministisch, Daten über die gemeinsamen Bausteine laden

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 11.11.2026 · **Vorgeschlagen von:** DZ · **PSP:** 5.3 (DZ)

## Kontext
Schritt 1 (Datenmodell) bekommt das Artefakt und die CSV des Anwenders und liefert Schritt 2 ein bestätigtes Schema. Laut Spezifikation 3.1 ist das Artefakt „behauptetes Wissen“, die Daten sind die Wahrheit; ein unbemerkter Unterschied fiele sonst erst in Schritt 2 oder 3 auf. US-04 verlangt: Schema aus der Datenbank lesen, mit dem Artefakt abgleichen, höchstens drei Beispielwerte je Spalte. Zu entscheiden war, wie die Daten in die Datenbank kommen und ob ein Sprachmodell beteiligt ist.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: Laden mit den gemeinsamen Bausteinen aus `runner/framework_lib.py` (dieselben wie beim Upload im Dashboard) | dieselben Regeln beim Bauen und beim späteren Upload (Datumsformate, Dezimalkomma, ja/nein); kaum neuer Code; Prüfung schon getestet | Backend hängt an Frontend-Code (war es über Datenmodelle und Schritt 3 ohnehin) |
| B: eigene Lade- und Prüflogik im Backend | Backend unabhängig von Änderungen im Frontend | rund 100 Zeilen doppelter Code; zwei Regelwerke können auseinanderlaufen, dann lädt die Pipeline Daten, die das Dashboard beim Upload ablehnt (oder umgekehrt) |
| C: Sprachmodell formuliert Fehlermeldungen (in Spezifikation 3.1 als Option genannt) | freier formulierte Meldungen | GPU-Aufruf für einen deterministischen Schritt; Ergebnis nicht reproduzierbar; „meinten Sie …?“ liefert die Ähnlichkeitssuche bereits ohne Modell |

## Entscheidung
Wir wählen **A ohne C**: Schritt 1 arbeitet vollständig ohne Sprachmodell.
1. CSV mit `lese_csv` und `validate_against_schema` prüfen und umwandeln, in eine **neue** SQLite-Datei laden (`uebernehmen`).
2. Schema **aus der Datenbank** lesen (nur lesend über `verbinde_nur_lesend`): Spalten, SQLite-Typ, bis zu drei verschiedene Beispielwerte, sortiert, Texte auf 50 Zeichen gekürzt. Sortiert, damit jeder Lauf dasselbe Ergebnis liefert.
3. Abgleich mit dem Artefakt. **Jede** Abweichung stoppt die Pipeline mit allen Meldungen auf einmal (Fail-Fast). Einen erneuten Versuch gibt es nicht, weil der Schritt bei gleicher Eingabe immer gleich entscheidet.

## Konsequenzen
- Code in `backend/src/pipeline/schritte/schritt1_datenmodell.py`, Tests in `backend/tests/test_us04_schema.py`. Fehler kommen als Liste verständlicher Sätze (`SchemaFehler.meldungen`, gleiches Muster wie `ArtefaktFehler` und `UploadFehler`), damit ein Frontend sie später ohne Umbau anzeigen kann.
- Eine vorhandene Datenbank wird nur mit ausdrücklichem `ueberschreiben=True` ersetzt, damit nie versehentlich eine Dashboard-Datenbank verloren geht (US-13).
- Ändert sich die gemeinsame Prüfung im Frontend, laufen die Backend-Tests in der CI mit; ein Bruch wird im PR sichtbar.
- **Bekannte Grenze:** `lese_csv` lehnt Dateien über 5 MB ab (Schutz beim Upload, Risiko R15). Für die synthetischen Projektdaten reicht das. Bei größeren Daten erhält `lese_csv` einen optionalen Parameter für die Grenze (Abstimmung mit DB).
- **Bekannte Grenze:** SQLite unterscheidet `datum`/`text` (beide `TEXT`) und `bool`/`ganzzahl` (beide `INTEGER`) nicht. Der Abgleich erkennt diese Verwechslungen daher nicht. Unkritisch, weil Schritt 1 die Datenbank selbst aus streng geprüften Daten baut; relevant wäre es nur bei einer fremd gelieferten Datenbank.

## Belege
- Spezifikation 3.1 (Datenmodell-Schritt), User Story US-04
- Probelauf mit `frontend/examples/testdateien/`: gültige Datei liefert das Schema, fehlerhafte Datei stoppt mit „fehlende Spalte(n): umsatz“, „unbekannte Spalte: Umsatz – meinten Sie `umsatz`?“ und „Spalte menge ist nicht vom Typ ganzzahl (z. B. 'viele' in Zeile 2)“
