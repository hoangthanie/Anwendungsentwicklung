# Risiken – Kurzfassung

Vollständige Analyse: `Risikoanalyse_Massnahmen.docx` (AP 1.2.3, SJ) in der Projektablage (Team-Ordner). Review wöchentlich im Jour fixe.

| ID | Top-Risiko (Risikozahl ≥ 15) | RZ | Verantw. | Wichtigste Maßnahme im Repo |
|---|---|---|---|---|
| R01 | Fachlich falsche SQL-Queries trotz gültiger Syntax | 20 | DZ | Prüfschichten in `harness/validators.py`, Testorakel mit erwarteten KPI-Werten |
| R19 | Terminverzug durch unterschätzte Aufwände | 16 | MP | Issues mit Meilensteinen, wöchentliche PSP-Pflege |
| R06 | Generizitätsnachweis scheitert | 15 | DZ | CI-Job `generizitaet`, zweites Artefakt `artefakte/aktivitaet` |
| R18 | Unvollständige KI-Kennzeichnung | 15 | MP | PR-Checkbox + `docs/prompt-verzeichnis.md` |
| R28 | Live-Demo scheitert in der Präsentation | 15 | SJ | eingefrorener Release-Tag, Fallback-Video, lokaler Container |

Weitere im Repo umgesetzte Maßnahmen: Nur-Lese-SQL + read-only DB (R14), gitleaks (R17), Vertrags-Tests (R07),
DB-Backup im Deploy-Skript (R11).
