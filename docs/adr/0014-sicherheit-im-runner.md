# ADR 0014: Sicherheit im Runner: nur lesendes SQL, geprüftes und neu kodiertes Logo, escaptes HTML

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 27.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 6.2, 6.3 (DB), AP 4.6, US-14

## Kontext
Der Runner zeigt Inhalte an, die aus Dateien kommen: SQL aus der `dashboard.json`, Logo und Farben aus dem Branding, Namen und Texte aus Artefakt und Daten. Er läuft im Netzwerk ohne Anmeldung (ADR 0017). Ein manipulierter oder fehlerhafter Eintrag darf weder Daten ändern noch Code oder Skripte in die Seite bringen. Ein Logo, das als Bild durchgeht, kann zusätzlich angehängte Daten oder Metadaten enthalten.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: SQL aus der Konfiguration ausführen, wie es kommt | einfach | ein schreibendes oder zerstörerisches Statement würde ausgeführt |
| **B: SQL nur nach Prüfung (`pruefe_nur_lesend`) und über eine nur lesende Verbindung** (`mode=ro`, `PRAGMA query_only`) | zwei unabhängige Sperren, auch wenn eine Prüfung eine Lücke hat | Lesen mit Sonderfällen muss geprüft werden |
| C: Logo speichern, wenn die Prüfung besteht | schnell, Original bleibt | bestanden heißt nicht, dass die Datei nur ein Bild ist |
| **D: Logo prüfen (Pillow, PNG oder JPEG, höchstens 1 MB, höchstens 4000 Pixel je Seite), dann mit Pillow neu kodieren und immer als `logo.png` speichern (höchstens 1024 Pixel)** | nur selbst erzeugte Bytes werden gespeichert, Dateiendung und Inhalt sind sicher | Original geht verloren, Qualität begrenzt |
| E: Texte unverändert in HTML einsetzen | einfach | Skripteinschleusung über Namen oder Beschreibungen möglich |
| **F: alles mit `html.escape` einsetzen, Akzentfarbe nur als `#RRGGBB`** | keine fremden Tags oder Styles | Texte erscheinen buchstäblich |

## Entscheidung
Wir wählen **B, D und F**. SQL wird mit `pruefe_nur_lesend` geprüft und nur über eine nur lesende SQLite-Verbindung ausgeführt. Logos prüft Pillow auf Inhalt (nicht auf Dateiendung) und kodiert sie neu. Alle in HTML eingesetzten Texte laufen durch `html.escape`; Farben sind nur als `#RRGGBB` erlaubt, alles andere fällt auf die Produktfarbe zurück. Ordner- und Dateiauflösung (`lade_logo`) bleibt innerhalb des Ordners der `dashboard.json`. Die Bezeichner-Regeln aus ADR 0010 gelten zusätzlich.

## Konsequenzen
- Fehlerhafte Konfiguration führt zu einer verständlichen Meldung statt eines Stacktrace; unerlaubtes SQL wird nicht ausgeführt.
- Das Logo wird immer neu erzeugt, ein getarntes oder zu großes Bild wird abgelehnt (Testdateien in `frontend/examples/testdateien/`).
- Die Absicherung ersetzt kein Anmeldesystem. Wer den Runner im Netz erreicht, kann ihn weiter nutzen (ADR 0017).
- Gilt nur für den Runner im Frontend. Die Prüfschichten für das **erzeugte** SQL in der Pipeline stehen in ADR 0008.

## Belege
- `frontend/docs/02-entscheidungen.md` (E-08), `frontend/docs/03-runner.md`, `frontend/docs/05-branding.md`
- `frontend/src/dashboard_framework/runner/sicherheit.py`, `branding.py`, `frontend/tests/test_sicherheit.py`, `frontend/tests/test_branding.py`
