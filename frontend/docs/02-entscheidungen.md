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

## E-05 – Reihenfolge: Runner zuerst (2026-10-27)
- **Warum:** Der Runner braucht kein LLM, nur eine Beispiel-`dashboard.json` und eine Test-DB. Er ist früh sichtbar (Demo-fähig) und prägt das Format, das die Pipeline erzeugen muss. Danach Upload, Formular, Branding.
