# ADR 0010: Prüfregeln im Artefakt-Modell, strenge Bezeichner, sicheres YAML-Laden

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 27.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 6.1, 3.3 (DB, gemeinsam mit DZ)

## Kontext
Das Artefakt (`artefakt.yaml`) ist die Eingabe der gesamten Pipeline. Fehler darin sollen früh auffallen (Fail-Fast, US-02), bevor ein Sprachmodell Zeit verbraucht. Das Artefakt entsteht auf mehreren Wegen: über das Formular, von Hand editiert oder durch die Pipeline. Ordner- und Dateinamen sowie Tabellen- und Spaltennamen landen später in Pfaden und SQL.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: Prüfung nur im Formular | Meldungen direkt am Feld | von Hand editierte YAML-Dateien umgehen die Prüfung |
| **B: Prüfung im Pydantic-Modell (`model_validator`)** | jeder Weg zum Artefakt läuft durch dieselbe Prüfung | Meldungen müssen vom Formular den Feldern zugeordnet werden (`meldungen_zu_feld`) |
| C: freie Namen (Leerzeichen, Sonderzeichen erlaubt) | Dateien aus Excel passen ohne Umbenennen | Namen werden Ordnernamen und SQL, Risiko für Fehler und Einschleusung |
| **D: strenge Bezeichner** (Buchstaben, Ziffern, `_`; unbekannte YAML-Felder sind Fehler; höchstens 12 KPIs) | Tippfehler in Feldnamen werden nicht still ignoriert, sichere Namen für Pfad und SQL | CSV-Dateien mit Leerzeichen in Spaltennamen müssen umbenannt werden |
| E: `yaml.load` | kennt mehr YAML-Funktionen | kann Code ausführen |
| **F: `yaml.safe_load` mit Größenlimit (1 MB)** | führt keinen Code aus | keine Spezial-Tags |

## Entscheidung
Wir wählen **B, D und F**. Alle Prüfregeln stehen im Artefakt-Modell (`models/artefakt.py`), das Formular zeigt nur deren Meldungen an der passenden Stelle. `name`, `tabelle` und Spaltennamen sind nur Buchstaben, Ziffern und `_` erlaubt. Unbekannte Felder sind Fehler (`extra="forbid"`). Die Referenzprüfungen (existieren die Spalten, die eine KPI nennt?) laufen erst, wenn die Struktur gültig ist. YAML wird nur mit `safe_load` gelesen.

## Konsequenzen
- Fail-Fast ist nicht zu umgehen: Formular, Handbearbeitung und Pipeline nutzen dieselbe Prüfung.
- **Preis:** Dateien mit Leerzeichen in Spaltennamen müssen umbenannt werden. Die Meldung erklärt das. **Mit David abstimmen**, ob seine Schritte dieselben Regeln voraussetzen (Schritt 1 lädt Daten über dieselben Bausteine, ADR 0007).
- Teil des Sicherheitskonzepts (AP 4.6): kein Code aus YAML, nur geprüfte Namen in Pfaden und SQL.

## Belege
- `frontend/docs/02-entscheidungen.md` (E-10, E-11, E-12), `frontend/docs/06-eingabe.md`
- `frontend/src/dashboard_framework/models/artefakt.py`, `frontend/tests/stories/test_us02_03_artefakt.py`
