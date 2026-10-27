# 08 – Gestaltung: das Formblatt-System (beide Streamlit-Oberflächen)

**Stand:** 2026-10-27 · **Werkzeug:** Impeccable-Skill (github.com/pbakaus/impeccable, Version 4.8.0) · **Status:** umgesetzt, im Browser geprüft, unabhängig begutachtet (siehe Abschnitt "Review")

## Was wurde gemacht?
Beide Oberflächen (Eingabe-App und Dashboard-Runner) sehen jetzt wie ein Produkt aus einem Guss aus, statt wie Standard-Streamlit mit einer Akzentfarbe. Funktionen, Texte und Reihenfolge der Abschnitte sind unverändert.

## Wie ist der Skill vorgegangen? (der Ablauf, den er verlangt)
1. **Kontext:** Der Skill lädt PRODUCT.md. Es fehlte, also lief zuerst `init`: Nutzer, Zweck, Einsatzort, Grenzen wurden aus den Projektunterlagen zusammengestellt und von dir bestätigt (`frontend/PRODUCT.md`).
2. **Modus:** Beide Oberflächen sind *Operate* (der Nutzer erledigt eine Aufgabe). Dort zählen Übersicht und Bekanntheit mehr als Ausdruck; die "Welt" darf nur Schrift, Farbe, Dichte und **ein** Erkennungsmerkmal liefern, nie Navigation oder Bedienelemente.
3. **Richtung finden:** Ich habe sieben Kandidaten aus der Welt der Zielgruppe (deutscher Mittelstand, Controlling, Formulare, Normen) entwickelt. Ein Würfel im Skill hat bestimmt, welche davon gebaut wird (damit nicht jeder Lauf bei der naheliegenden Standardlösung landet), und sechs Katalog-Welten dienten als Gegenkandidaten. Du hast auf einer Auswahlseite entschieden: **Formblatt**.
4. **Vertrag:** Die Entscheidung steht als "Direction contract" in `.impeccable/surfaces/src-dashboard-framework-runner-app-py.md` (These, eigene Welt, Geschichte, erster Bildschirm, Form).
5. **Qualitätsboden:** Vor dem Bauen liest der Skill eine Liste von Mindestanforderungen und Verboten (`craft-floor.md`); daraus folgen etwa die Kontrastwerte und der Verzicht auf bestimmte Dekorationen.
6. **Bauen, prüfen, begutachten, dokumentieren:** siehe unten.

## Die Gestaltungsidee: Formblatt
Vorbild ist das **Schriftfeld technischer Zeichnungen** (DIN) und das Formblattwesen: alles ist beschriftet, nummeriert, in Haarlinien gefasst.
- **Erkennungsmerkmal (das eine Signaturmerkmal):** das **Schriftfeld** als Kopfzeile. Im Runner enthält es Titel (mit Kundenlogo), Kunde, Datenstand, Zeilenzahl, Datenzugriff "nur lesend" und den Prüfstand. In der Eingabe-App zeigt es Artefakt, Spalten, KPIs und den Prüfstand der Eingaben. So sieht man in jedem Moment, "was für ein Blatt" man vor sich hat.
- **Felder:** Jeder Abschnitt ist ein weißes Blatt mit Titelzeile und Feldnummer; im Runner trägt es unten eine Fußleiste (Darstellung, Sortierung, Ergebnis), in der Eingabe-App sind die Felder die fünf Schritte des Ausfüllens.
- **Zustandsmarken:** *offen, gültig, fehlerhaft, übernommen, Hinweis*. Jede hat eine **Form und einen Text**, nie nur eine Farbe (z. B. Raute für Fehler, leeres Quadrat für offen), damit sie auch bei Farbschwäche lesbar sind.

## Entscheidungen und Begründung
| Thema | Entscheidung | Warum |
|---|---|---|
| Hell/Dunkel | fest hell | Einsatz am Büro-Laptop bei Tageslicht; Kundenfarben sind für helle Flächen gestaltet (E-09) |
| Schrift | **Barlow** (Text, Ziffern) und **Barlow Condensed** (Beschriftungen, Titel, große Kennzahl) | DIN-nah und gut lesbar, tabellarische Ziffern für Zahlen; freie OFL-Lizenz |
| Schriften lokal | Dateien liegen in `runner/static` und `eingabe/static` | Der Raspberry Pi hat kein Internet; Streamlit liefert statische Dateien nur **neben dem Startskript** aus, deshalb in beiden Ordnern |
| Farbe | Papier `#F1F3F5`, Tinte `#1C2227`, Haarlinien, Zustandsfarben nur mit Bedeutung | Ruhige Oberfläche; Farbe soll Aufgaben erledigen, nicht dekorieren |
| Kundenfarbe | nur aktiver Tab, Hauptknopf und Diagrammfarbe | Der Kunde ist Gast, das Framework Gastgeber (Produktprinzip 4); ist die Kundenfarbe zu hell für Text, bleibt die Schrift dunkel (`akzent_als_text`, Kontrast ≥ 4,5:1) |
| Kontrast | Textstufen ≥ 4,5:1, Ränder von Bedienelementen ≥ 3:1 | Lesbarkeit (WCAG); als Test festgeschrieben |
| Kein farbiger Seitenstreifen an Meldungen | stattdessen Zustandsmarke mit Text | Verbot im Qualitätsboden; außerdem robuster für Farbschwäche |
| Keine Zeilenüberschrift über Titeln | Im Schriftfeld steht der Titel ohne Beschriftung darüber | Verbot im Qualitätsboden ("Kicker") |
| Feldnummern | bleiben | In Formularen sind sie Verweise ("Feld 3 stimmt nicht") und in der Eingabe die Reihenfolge des Ausfüllens |
| Diagramme | Haarlinien, deutsche Zahlen (Dezimalkomma, Punkt als Tausendertrenner), keine Werkzeugleiste | weniger Ablenkung, vertraute Schreibweise |
| Eingebettete Texte | alles Fremde wird mit `html.escape` maskiert, Logo nur als `data:image/png|jpeg;base64`, Akzent nur als `#RRGGBB` | Kunde und Anwender liefern die Texte; sonst wäre Einschleusen von HTML/CSS möglich (Tests) |
| Gemeinsamer Code | Paket `dashboard_framework/ui/` (`theme.py`, `komponenten.py`) | beide Apps nutzen dieselben Bausteine, damit sie gleich bleiben |

## Wo liegt was?
- `.streamlit/config.toml`: Streamlit-Theme (Farben, Schriften, Radius, ausgeblendeter Deploy-Knopf).
- `ui/theme.py`: Farben, Kontrastberechnung, das globale CSS (`baue_css`), `wende_an`.
- `ui/komponenten.py`: `schriftfeld`, `feldkopf`, `fussleiste`, `marke`, `kennzahl`, `zahl`, `esc`.
- `runner/app.py`, `eingabe/app.py`: die Seiten (weiterhin dünn).
- `runner/charts.py`: Plotly im selben Stil.
- `runner/daten.py`: `lade_kopfdaten` (Zeilenzahl und Datenstand fürs Schriftfeld, nur lesend).

## Was Streamlit nicht zulässt
- Die Tabellen (`st.dataframe`, `st.data_editor`) werden auf einer Zeichenfläche gemalt; CSS erreicht sie kaum. Ihre Kopfzeilen bleiben im Streamlit-Grau.
- Die Texte im Datei-Upload ("Upload", "5MB per file") sind fest englisch.
- Die Akzentfarbe des Kunden wirkt über CSS auf Streamlits interne Elemente. Die Namen dieser Elemente ändern sich zwischen Streamlit-Versionen; nach einem Update ist eine Sichtprüfung nötig (so ging es schon beim ersten Versuch).

## Lernnotizen aus dem Bauen
- Die Auswahlseite des Skills zählt Skizzen nur, wenn sie **nach** ihrem Start geschrieben wurden; meine waren vorher fertig, deshalb zeigte sie "Sketching" (Datei neu geschrieben, dann ging es).
- Streamlit gibt jedem Markdown-Block unten **-16 px** Außenabstand. Eigene HTML-Blöcke ragten dadurch 16 px über ihre Hülle; die Messung im Browser (nicht das Auge) hat das gezeigt. Lehre: Abstände messen, nicht schätzen.
- Streamlit legt über Bildunterschriften 60 % Deckkraft; sie fielen unter 4,5:1 Kontrast und wurden korrigiert.
- Meine Tests mussten nachgezogen werden, weil Titel und Kennzahl jetzt HTML sind und nicht mehr `st.title`/`st.metric` (der Test prüft jetzt den sichtbaren Text).
- `kennzahl_wert` formatiert jetzt deutsch (103,2 statt 103.20).

## Review (unabhängig) und was daraus wurde
Ein frischer Agent ohne meinen Gesprächsverlauf hat die Oberflächen gegen den Gestaltungsvertrag geprüft (Urteil: **fix**, acht Punkte). Der Skill sieht dafür einen eigenen Review-Agenten vor, der in dieser Sitzung nicht registriert war; deshalb lief die Prüfung mit der mitgelieferten Review-Anleitung des Skills (`reference/degraded/finish-reviewer.md`) in einem normalen Agenten.

| # | Fund | Entscheidung |
|---|---|---|
| 1 | Hauptaktion "Übernehmen" links statt rechts unten im Feld (Vertragsverstoß) | behoben (CSS `align-self:flex-end`, auch für "Speichern" in der Eingabe-App); im Browser gemessen: 17 px vom Rand |
| 2 | Hinweis "Erwartete Spalten" zu blass und klein | behoben (normaler Text statt Bildunterschrift, Code-Chips in Tinte) |
| 3 | Fußleiste "Darstellung: Balken" ohne Aussage; Herkunft der Zahl fehlt | behoben: Fußleiste zeigt jetzt die **Berechnung** in Worten. Dafür gibt es ein neues, **optionales** Feld `Chart.beschreibung` (siehe unten) |
| 4 | Achsentitel sind rohe Spaltennamen; keine Werte an den Balken | x-Titel entfernt, Werte an den Balken (bis 12 Balken, nur bei Zahlen) |
| 5 | Zwei Datenfarben für dieselbe Aussage (Balken blau, Linie orange) | behoben im Beispiel (`farbe` entfernt); die Möglichkeit, einem Chart eine eigene Farbe zu geben, bleibt |
| 6 | Vorschau-Tabelle mit ISO-Datum und Punkt-Dezimalzahl | Vorschau in deutscher Schreibweise; ein Satz erklärt, was gespeichert wird (ISO-Datum, Punkt) |
| 7 | Dritter Tab auf dem Handy abgeschnitten | engere Abstände auf kleinen Bildschirmen; der Tab-Streifen scrollt weiterhin, wenn es nicht reicht |
| 8 | "Konfiguration: geprüft" kann nie rot werden, ist also Dekoration | Zelle entfernt; stattdessen trägt **"Datenzugriff: nur lesend"** die Marke, weil diese Prüfung tatsächlich stattgefunden hat |

Zusätzlich gefunden (nicht vom Review): Streamlit zeichnet unter den Tabs eine eigene 2-Pixel-Linie neben meiner; beide sind zu einer Haarlinie zusammengelegt.

**Nicht übernommen / bewusst anders:** Die Feldnummern bleiben (der Review nennt sie "akzeptabel, nicht lobenswert": im Runner sind sie Verweise, in der Eingabe-App die Reihenfolge). Streamlit-eigene englische Texte im Datei-Upload bleiben.

**Neues Feld im gemeinsamen Vertrag:** `Chart.beschreibung` (optional). Der Pipeline-Schritt 3 setzt es aus der KPI-Beschreibung des Artefakts (nicht vom Sprachmodell). Es ist abwärtskompatibel, aber Teil des Vertrags `dashboard.json`: bitte mit David (PSP 3.4) abstimmen.

**Was der Skill nicht prüfen konnte:** Der mechanische Detektor (`impeccable detect`) liest nur HTML/CSS-Dateien; mein CSS steht in Python-Texten. Sein leeres Ergebnis ist deshalb ein schwaches Signal. Das Review konnte nur Bildschirmfotos beurteilen (800 px breit), keine berechneten Kontrastwerte; die habe ich selbst gemessen (Tests in `tests/test_ui.py`).

## Auf einem neuen Rechner
Der Skill liegt nicht im Repo, sondern in `~/.claude/skills/impeccable` (installiert aus github.com/pbakaus/impeccable, Ordner `.claude/skills/impeccable`). Auf einem neuen Rechner neu installieren; die Engine-Datei lädt er beim ersten Start selbst (sie ist für die Gestaltungsarbeit nötig, nicht für das Ausführen der Apps). Im Repo liegen `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json` und `.impeccable/surfaces/` (der Gestaltungsvertrag).
