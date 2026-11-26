# ADR 0009: Fachlogik in reinen Funktionen, Streamlit-Dateien dünn, Frontend als installierbares Paket

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 27.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 6.1, 6.3 (DB)

## Kontext
Streamlit-Code lässt sich nur schwer automatisiert testen: Jede Eingabe läuft über die Oberfläche, und Fehler zeigen sich erst im Browser. Das Backlog (US-01, US-09) verlangt Tests je Story. Außerdem startete die App im Browser nicht, obwohl `pytest` grün war: Der Importpfad war nur in `pytest` gesetzt, nicht beim Start mit `streamlit run`.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: Logik direkt in den Streamlit-Skripten | wenig Dateien, schnell geschrieben | nur über `AppTest` oder Browser testbar, schwer zu lesen |
| **B: Fachlogik in reinen Funktionen (`formular.py`, `daten.py`, `framework_lib.py`), Streamlit-Dateien nur Oberfläche** | `pytest` genügt ohne Browser, Logik ist wiederverwendbar (auch für Davids Pipeline) | mehr Dateien, Oberfläche und Logik müssen sauber getrennt bleiben |
| C: Importpfad über `sys.path`-Trick oder `PYTHONPATH` | kein Paket nötig | fragil, drei Startwege (pytest, Streamlit, Docker) mit je eigener Einstellung |
| **D: installierbares Paket (`pip install -e .`, `src/`-Layout)** | ein einheitlicher Weg für Tests, `streamlit run` und das Docker-Image | einmaliger Installationsschritt pro Rechner |

## Entscheidung
Wir wählen **B und D**: Die Streamlit-Dateien (`eingabe/app.py`, `runner/app.py`) enthalten nur die Oberfläche. Validierung, Datenladen, Upload-Prüfung und Formatierung liegen in normalen Funktionen. Das Frontend ist ein Paket `dashboard_framework` mit `src/`-Layout und wird mit `pip install -e .` (in `requirements.txt` als `-e .`) installiert. Die Ordnernamen (`models/`, `eingabe/`, `runner/`) folgen dem Repository-Dokument, damit Testfälle und die spätere Zusammenführung ohne Umbenennen funktionieren.

## Konsequenzen
- Die meisten Tests laufen schnell und ohne Browser (193 Tests, rund 30 Sekunden). Die Oberfläche selbst prüfen zusätzliche `AppTest`-Fälle und die Sichtprüfung im Browser.
- Davids Backend bindet das Frontend als Paket ein (`-e ../frontend`) und nutzt dieselben Modelle und Prüfungen.
- Das `src/`-Layout verhindert, dass Tests versehentlich nicht installierten Code importieren.
- Änderungen an Modulen brauchen einen Neustart des Streamlit-Servers (Lernpunkt aus einem Fehler im Eingabeformular).

## Belege
- `frontend/docs/02-entscheidungen.md` (E-03, E-04, E-07)
- `frontend/pyproject.toml`, `frontend/tests/`
