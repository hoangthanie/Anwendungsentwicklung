# 05 – Branding: Logo und Farben (PSP 6.2, US-03)

**Stand:** 2026-10-27 · **Status:** Prüfung, Speichern und Anzeige fertig und im Browser getestet · **Offen:** Einbindung in das vollständige Eingabeformular (PSP 6.1)

## Wofür?
Das Dashboard soll nach "unserem" Dashboard aussehen: Firmenname, Logo, Firmenfarben. Der Anwender liefert diese Angaben in der Eingabe-App, der Runner zeigt sie an.
Ein Logo-Upload ist fremder Input aus dem Browser und deshalb ein Sicherheitsthema (Risiko R15, Teil des Sicherheitskonzepts AP 4.6).

## Dateien und Funktionen
| Datei | Funktion | Aufgabe |
|---|---|---|
| `runner/branding.py` | `pruefe_logo(pfad)` / `pruefe_logo_bytes(bytes)` | Prüft den **Inhalt** (nicht die Endung): echtes PNG/JPEG, höchstens 1 MB, höchstens 4000 px je Seite |
| | `bereinige_logo(bytes)` | Erzeugt aus dem Bild ein **neues PNG** (höchstens 1024 px), alles Fremde fällt weg |
| | `speichere_logo(bytes, ordner)` | Speichert als festen Dateinamen `logo.png`, gibt den Namen für `Branding.logo` zurück |
| | `lade_logo(ordner, name)` | Liest das Logo für die Anzeige, nur innerhalb des Dashboard-Ordners und nur wenn es ein gültiges Bild ist |
| | `normalisiere_farben(liste)` | Prüft `#RRGGBB`, vereinheitlicht auf Großbuchstaben, meldet alle falschen Codes gemeinsam |
| | `theme_css(farben)` | CSS für die Akzentfarbe (aktiver Tab, Haupt-Button) |
| `eingabe/branding_form.py` | `baue_branding(name, farben_text, logo)` | Fachlogik des Formularabschnitts: prüft alles, sammelt alle Fehler, liefert `Branding` + bereinigtes Logo |
| `eingabe/app.py` | `main()` | Dünne Streamlit-Seite (bisher nur Branding) mit Farbfeldern und Logo-Vorschau |

## Entscheidungen und Begründung

### Inhalt prüfen, nicht Dateiname
Eine Textdatei mit Skript, umbenannt in `logo.png`, trägt die Endung eines Bildes, ist aber keins. Pillow öffnet die Bytes und stellt das **tatsächliche Format** fest; `verify()` prüft die Struktur.
Test: `test_getarnte_datei_wird_abgelehnt` (TF-009) und im Browser mit einer Skript-Datei bestätigt.

### Nur PNG und JPEG (Whitelist)
SVG ist ein Textformat und kann Skripte enthalten, GIF/WebP/BMP brauchen wir nicht. Eine **Erlaubnisliste** ist sicherer als eine Verbotsliste, weil unbekannte Formate automatisch abgelehnt werden.

### Drei Grenzen: Bytes, Pixel, Format
- **1 MB** (Backlog US-03.2): Größe wird geprüft, **bevor** gelesen wird (`pruefe_logo`).
- **4000 px je Seite**: Eine kleine Datei kann ein riesiges Bild enthalten (einfarbig komprimiert sich extrem). Beim Dekodieren würde das Gigabytes Speicher fressen ("Dekompressionsbombe").
  Pillow liest dazu zuerst nur den Kopf der Datei; erst danach wird entschieden. Test: ein 5000×1-Pixel-Bild ist winzig, wird aber abgelehnt.
- **Format** wie oben.

### Neu kodieren statt Original speichern
Eine Datei kann gleichzeitig ein gültiges Bild **und** etwas anderes sein (angehängte Daten hinter dem Bildende, Metadaten wie GPS-Position in Fotos, "Polyglot"-Dateien).
`bereinige_logo` liest die Pixel und schreibt ein neues PNG; gespeichert wird ausschließlich, was Pillow selbst erzeugt hat. Test: Ein PNG mit angehängtem `<script>` besteht die Prüfung als Bild,
das gespeicherte Ergebnis enthält das Skript nicht mehr. Nebeneffekt: Alles ist danach PNG (einheitlich, auch Transparenz bleibt erhalten) und höchstens 1024 px (reicht für die Anzeige mit 96 px).

### Fester Dateiname `logo.png`
Der vom Anwender gewählte Dateiname wird **nie** übernommen. So gibt es keine Pfadtricks (`../../x`), keine Namenskollisionen und keine merkwürdigen Zeichen.

### Das Logo beim Anzeigen nochmals prüfen
Die `dashboard.json` ist Eingabe und könnte manipuliert sein (Risiko R16). Ein Logo-Eintrag wie `../../geheim.png` darf nichts außerhalb des Dashboard-Ordners lesen:
`lade_logo` löst den Pfad vollständig auf (`resolve`) und verlangt `is_relative_to(Ordner)`. Zusätzlich wird der Inhalt wieder als Bild geprüft. Bei einem Fehler zeigt der Runner eine kleine Warnung, das Dashboard selbst läuft weiter.

### Farben: streng `#RRGGBB`
Wie im Backlog (TF-007). Kurzformen wie `#FFF` und Namen wie `blau` werden abgelehnt, damit überall dasselbe Format gilt. Eingaben werden bereinigt (`#1f3864` -> `#1F3864`).
Die Fehlermeldung zeigt den Text so, wie er getippt wurde (nicht in Großbuchstaben umgewandelt). Dieser Punkt fiel erst im Test auf: `blau` erschien als `BLAU`.
Die Farben werden an drei Stellen verwendet (Charts, Kopf, CSS) und gehen deshalb nirgendwo ungeprüft in HTML/CSS: `theme_css` prüft sie nochmals. Test: `red; } body { display:none` ergibt leeres CSS.

### Helles Theme fest eingestellt
Firmenfarben sind für **helle** Hintergründe entworfen. Auf einem dunklen Betriebssystem-Theme war das Marineblau (`#1F3864`) kaum zu erkennen. `.streamlit/config.toml` setzt deshalb `base = "light"`.
Das ist eine Entscheidung gegen die Gewohnheit "Theme des Betrachters übernehmen" zugunsten verlässlicher Lesbarkeit.

### Akzentfarbe per CSS
Streamlit erlaubt pro Seite keine dynamische Designfarbe. Wir setzen die **erste Firmenfarbe** per CSS auf den aktiven Tab und den Haupt-Button. Das ist eine Notlösung, die von Streamlits internem Aufbau abhängt:
In Version 1.66 hieß der Tab-Streifen anders als im ersten Entwurf (`react-aria-SelectionIndicator` statt `baseweb`). Darum enthält die CSS mehrere Selektoren; bei einem Streamlit-Update ist hier ein Kontrollblick nötig.

### Diagramm-Farben
Reihenfolge der Farbwahl: Farbe des einzelnen Charts, sonst erste Firmenfarbe, sonst neutrales Blau (`runner/charts.py`).

## Tests
`tests/stories/test_us02_03_artefakt.py`: TF-008 (echtes PNG), TF-009 (getarnte Datei), TF-010 (zu groß). `tests/test_branding.py`: JPEG, GIF/BMP/WebP, SVG, leere/abgeschnittene Datei, Pixelgrenze,
Bereinigung (angehängte Daten, JPEG zu PNG, Verkleinern, Paletten-Transparenz), fester Dateiname, Pfad außerhalb, Farben, CSS-Einschleusung, Formularlogik mit gesammelten Fehlern.
Im Browser: Runner mit Logo und Akzentfarbe, Eingabe-Seite mit Skript-Datei (abgelehnt), echtem PNG (Vorschau) und falschen Farben (Fehlermeldung).

## Lernnotizen
- Meine ersten CSS-Selektoren passten nicht zur installierten Streamlit-Version; erst die Untersuchung der Seite im Browser (Elemente auslesen) zeigte den richtigen Namen. Unit-Tests können das nicht erkennen.
- Der Test für die Fehlermeldung deckte eine kleine Unfreundlichkeit auf (Großbuchstaben in der Meldung). Gute Tests prüfen auch den Text, den der Anwender sieht.

## Offen
- Die Eingabe-Seite ist ein Entwurf: In PSP 6.1 kommen Ziel, Publikum, Spalten, KPIs hinzu; der Branding-Abschnitt wird dort eingebunden und das Ergebnis (`logo.png` + `Branding`) neben die `artefakt.yaml` geschrieben.
- Das Artefakt-Modell (PSP 3.3, gemeinsam mit David) muss die Branding-Felder übernehmen (Spec Anhang A: `firmenname`, `farben`); `Branding.logo` ist unser Zusatz.
