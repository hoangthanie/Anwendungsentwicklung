# ADR 0015: Gestaltungssystem „Formblatt“: fester heller Stil, Kundenfarbe nur als Akzent

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 27.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 6.4 (DB)

## Kontext
Die beiden Streamlit-Oberflächen (Eingabeformular und Dashboard) sollten über das Standardaussehen hinaus gestaltet werden, soweit Streamlit das erlaubt. Es gibt keine verbindliche Marke für das Produkt. Die Oberflächen sind Arbeitswerkzeuge (Büro-Laptop oder Browser am Raspberry Pi). Kunden bringen eigene Firmenfarben mit, die für helle Hintergründe gedacht sind; auf einem dunklen Theme war Marineblau kaum lesbar.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: Streamlit-Standard belassen | kein Aufwand | austauschbares Aussehen, kein Wiedererkennen |
| B: Theme folgt der Einstellung des Betrachters (hell/dunkel) | vertraut | Firmenfarben nicht zuverlässig lesbar |
| **C: fest helles Theme, eigene Gestaltung „Formblatt“** (Schriftfeld, nummerierte Felder, Zustandsmarken, Barlow/Barlow Condensed) | eigener, ruhiger Stil für Arbeitswerkzeuge, Kontraste prüfbar | Theme folgt nicht der Betrachtereinstellung, mehr Pflegeaufwand für CSS |
| D: Kundenfarbe als Hauptfarbe der Oberfläche | stark markentreu | Lesbarkeit und Kontrast hängen vom Kunden ab |
| **E: Kundenfarbe nur als Akzent** (aktiver Reiter, Hauptaktion, Datenfarbe), Produktfarbe sonst | Kontrast bleibt gesichert, Branding sichtbar | Marke weniger dominant |

## Entscheidung
Wir wählen **C und E**. Das Produkt hat ein festes helles Theme und ein eigenes Gestaltungssystem „Formblatt“ (`DESIGN.md`, `docs/08-gestaltung.md`): Schriftfeld als Kopf, nummerierte Felder, Zustandsmarken, die Schriften Barlow und Barlow Condensed (selbst gehostet, ohne externe Anfrage), keine Schatten und Verläufe. Die erste Kundenfarbe wird nur als Akzent verwendet; ein zu heller oder nicht lesbarer Wert fällt auf die Produktfarbe zurück (Kontrastprüfung `kontrast`, `akzent_als_text`, `text_auf_akzent`). Die Gestaltung wurde mit dem Impeccable-Werkzeug umgesetzt (Operate-Modus).

## Konsequenzen
- Das Theme folgt nicht der Einstellung des Betrachters.
- Schriften liegen in `runner/static` und `eingabe/static` (Streamlit liefert statische Dateien nur neben dem Startskript aus); das funktioniert ohne Internet, wichtig für den Pi.
- Streamlit setzt Grenzen (Abstände, Reiterlinie, Beschriftungen); sie sind im CSS ausgeglichen und in `docs/08-gestaltung.md` beschrieben. Bei einem Streamlit-Update ist die Darstellung zu prüfen.
- KI-Einsatz: Gestaltungsentscheidung und Umsetzung mit Claude Code; im Prompt-Verzeichnis zu erfassen.
- Usability-Test mit einer Testperson (PSP 6.4) steht aus.

## Belege
- `frontend/docs/02-entscheidungen.md` (E-09), `frontend/docs/08-gestaltung.md`, `frontend/DESIGN.md`, `frontend/PRODUCT.md`
- `frontend/src/dashboard_framework/ui/theme.py`, `frontend/tests/test_ui.py`
