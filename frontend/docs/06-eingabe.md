# 06 – Eingabeformular und Artefakt-Modell (PSP 6.1 und 3.3, US-01 und US-02)

**Stand:** 2026-10-27 · **Status:** Modell, Prüfung, Formularlogik und Oberfläche fertig, im Browser geprüft · **Offen:** Abstimmung des Modells mit David (gemeinsamer Vertrag, Risiko R07)

## Wofür?
Der Anwender (z. B. die Vertriebsleitung) beschreibt sein Dashboard in einem Formular: Ziel, Publikum, Datenspalten, Kennzahlen, Branding. Heraus kommt eine Datei `artefakt.yaml`.
Sie ist der **Eingang der Agenten-Pipeline** und ein "strukturierter, wiederverwendbarer Prompt-Container" (Konzeptpapier, Kap. 2). Wichtig dabei: Fehler müssen **vor** dem Sprachmodell auffallen (Fail-Fast),
sonst entsteht erst in der Demo ein falsches Dashboard.

## Aufbau des Artefakts (`artefakt.yaml`)
```
name, titel, ziel, publikum, tabelle,
spalten: [ {name, typ, beschreibung}, ... ]     typ: datum | text | ganzzahl | dezimal | bool
kpis:    [ {name, beschreibung}, ... ]          Spaltennamen in der Beschreibung stehen in `Backticks`
branding: { firmenname, farben: [#RRGGBB, ...], logo }
```
Beispiele liegen unter `artefakte/sales/` (Referenzfall) und `artefakte/aktivitaet/` (Entwurf für den Generizitäts-Nachweis, mit David abzustimmen).

## Dateien und Funktionen
| Datei | Funktion | Aufgabe |
|---|---|---|
| `models/artefakt.py` | `Artefakt`, `Kpi`, `ArtefaktFehler` | Das Modell samt **allen** Prüfungen; `aus_dict`, `aus_yaml`, `zu_yaml`, `speichern` |
| | `Kpi.referenzierte_spalten` | Liest die Spaltennamen zwischen Backticks aus der KPI-Beschreibung |
| | `Artefakt.benoetigte_spalten` | Alle von KPIs verwendeten Spalten |
| `models/spalten.py` | `SpaltenDef`, `aehnliche_spalte` | Spalte (Name, Typ, Beschreibung); "meinten Sie ...?" |
| `eingabe/formular.py` | `artefakt_aus_formular(daten, ziel_pfad)` | Formulardaten -> geprüftes Artefakt; schreibt nur bei Erfolg |
| | `spalten_vorschlag(df)` | Name und Typ aus einer hochgeladenen Datei vorschlagen |
| | `zeilen_aus_tabelle`, `speichere_artefakt_ordner`, `vorhandene_artefakte` | Tabelle -> Daten, sicheres Speichern, Laden vorhandener Artefakte |
| `eingabe/app.py` | `main()` | Die Streamlit-Seite (dünn): Grunddaten, Spalten, KPIs, Branding, laufende Prüfung, Ergebnis |

## Die Fail-Fast-Prüfung (US-02)
Geprüft wird, bevor irgendetwas erzeugt wird:
| Regel | Beispielmeldung |
|---|---|
| Pflichtfelder vorhanden und nicht leer | `Pflichtfeld fehlt: ziel` / `Pflichtfeld ist leer: ziel` |
| KPI nennt eine Spalte, die es nicht gibt | `KPI 'X': unbekannte Spalte: region – meinten Sie `Region`?` |
| KPI nennt gar keine Spalte (Backticks vergessen) | `KPI 'X' referenziert keine Spalte – bitte Backticks setzen (z. B. `spalte`)` |
| Doppelte Spalten (auch bei anderer Groß-/Kleinschreibung) oder doppelte KPI-Namen | `Spalte 'Region' kommt doppelt vor (...)` |
| Spalten- und Tabellennamen sind einfache Bezeichner | `Spaltenname 'Umsatz netto' ist ungültig ...` |
| Name nur Kleinbuchstaben, Ziffern, `_` | `name: erlaubt sind Kleinbuchstaben ...` |
| Farbcodes `#RRGGBB` | `Ungültige Farbcodes: blau (erwartet #RRGGBB ...)` |
| Unbekannte Felder (Tippfehler wie `kpi:` statt `kpis:`) | `Unbekanntes Feld: kpi` |
| Mindestens 1 Spalte, 1 bis 12 KPIs | `kpis: höchstens 12 Einträge erlaubt` |

## Entscheidungen und Begründung

### Die Prüfung steckt im Modell, nicht im Formular
Die KPI-Spalten-Prüfung ist ein `model_validator` des `Artefakt`. Damit gilt sie für **jeden**, der ein Artefakt baut: Formular, YAML-Datei von Hand geschrieben, später die Pipeline (David).
Würde sie nur im Formular stehen, könnte eine von Hand editierte YAML-Datei die Prüfung umgehen. Prinzip: Prüfregeln gehören an die Stelle, wo die Daten definiert werden.

### Backtick-Anker für KPI-Spalten
Die KPI bleibt **Freitext** (flexibel), aber Spaltennamen stehen in Backticks. Das ist der feste Ankerpunkt für die automatische Prüfung (Konzeptpapier Kap. 5, Architekturentscheidung "Freitext mit Spalten-Anker").
Ohne Anker kann ein Programm nicht sicher erkennen, welches Wort eine Spalte ist.

### Anführungszeichen statt Backticks, Spalten zum Anklicken (aus dem ersten Test mit einer echten Datei)
Beim Test mit einer Ticket-Datei hat ein Anwender (Dominik) die Spaltennamen ohne Backticks getippt; Backticks sind für Fachanwender kaum zu schreiben (auf der deutschen Tastatur ist `` ` `` eine "Tottaste"). Außerdem fiel eine Lücke auf: War ein Backtick *nicht gepaart*, wurde der zugehörige Spaltenname **stillschweigend überlesen** (die KPI sah gültig aus). Daraus folgen drei Änderungen:
1. **Anführungszeichen:** `"Location"` (gerade) und „Location“ (deutsch) gelten als Spaltenverweis, genau wie Backticks. Die Umwandlung geschieht im Modell (`Kpi`-Validator): Gespeichert wird weiterhin `` `Location` ``, damit die `artefakt.yaml` für die Pipeline (David) unverändert bleibt und alle älteren Artefakte gültig sind. Im Formular sieht der Anwender nur Anführungszeichen (`backticks_zu_anfuehrungszeichen` beim Laden).
2. **Nicht gepaarte Zeichen sind ein Fehler:** "KPI 'x': Anführungszeichen nicht paarig – jeder Spaltenname braucht ein öffnendes und ein schließendes Anführungszeichen". Das gilt auch für Backticks.
3. **Spalten zum Anklicken:** Unter jedem KPI-Feld stehen die Spalten als Auswahl (`st.pills`). Ein Klick hängt `"Name" ` an das **Ende** des Textes an (`fuege_spalte_ein`). Eine Einfügestelle mitten im Text kennt Streamlit nicht; deshalb ist es Ende-Anhängen (Satz tippen, Spalte anklicken, weitertippen). Dafür ersetzt je ein Eingabefeld pro KPI die frühere Tabelle, denn in eine Tabellenzelle lässt sich nichts einfügen. KPIs werden mit "KPI hinzufügen" und "Entfernen" verwaltet.
**Abwägung:** Ein normales Anführungszeichen im KPI-Text (z. B. `die "aktiven" Tickets`) gilt jetzt als Spaltenverweis und wird als "unbekannte Spalte" gemeldet. Das ist Absicht (Fail-Fast); es ist selten und die Meldung nennt das Wort.

### Alle Fehler gemeinsam, aber in zwei Stufen
Der Anwender bekommt alle Meldungen auf einmal. Einschränkung: Zuerst wird die **Struktur** geprüft (Pflichtfelder, Typen, Namen), danach die **Zusammenhänge** (KPI gegen Spalten).
Ist die Struktur kaputt, lässt sich der Zusammenhang nicht sinnvoll prüfen (z. B. fehlt die Spaltenliste). Test `test_alle_fehler_gemeinsam` dokumentiert das Verhalten.

### Strikte Bezeichner statt freier Namen
`name` wird Ordner- und Dateiname, `tabelle` und Spaltennamen landen in SQL. Deshalb sind nur Buchstaben, Ziffern und `_` erlaubt, keine Leerzeichen, nicht mit Ziffer beginnend (Unicode wie Umlaute ist ok).
Das verhindert Pfadtricks (`../x`) und SQL-Einschleusung (`absatz; DROP TABLE x`) schon an der Quelle; Tests prüfen beides.
Preis: Eine Datei mit der Spalte "Umsatz netto" muss vorher umbenannt werden. Die Fehlermeldung sagt das ausdrücklich ("auch in der Datendatei umbenennen"), weil Artefakt und Datei sonst nicht mehr zusammenpassen
(der Upload vergleicht Spaltennamen exakt).

### `extra = "forbid"`: unbekannte Felder sind Fehler
Ein Tippfehler im Feldnamen würde sonst **still ignoriert**, und die KPIs fehlten ohne Hinweis. Lieber laut ablehnen.

### YAML nur mit `safe_load`, mit Größenlimit
`yaml.load` kann beliebige Python-Objekte erzeugen und damit Code ausführen. `safe_load` kann nur einfache Daten. Test: Eine YAML-Datei mit `!!python/object/apply:os.system` wird abgelehnt.
Dazu ein Limit von 1 MB (Risiko R15).

### Typ-Vorschlag aus der Datei: Vorschlag, kein Urteil
`spalten_vorschlag` nutzt **dieselbe** Umwandlungslogik wie der spätere Upload (`konvertiere_spalte`). So wird nur ein Typ vorgeschlagen, den der Upload später auch akzeptiert.
Reihenfolge: ganzzahl, dezimal, datum, bool, sonst text (spezifisch vor allgemein: "7" ist eine ganze Zahl, nicht "dezimal"). Leere Zellen werden bei der Erkennung ignoriert.
Spalten mit **gemischten** Datumsformaten gelten als Text (unklar). Die **Bedeutung** einer Spalte kann das System nicht raten; sie bleibt Pflicht des Anwenders (Spezifikation 3.1).

### Laufende Prüfung statt "Prüfen"-Knopf
Die Fehler erscheinen während der Eingabe. Solange noch nichts eingegeben ist, steht nur ein Hinweis da (sonst wäre die Seite beim Start voller Pflichtfeld-Fehler).

### Speichern: nur in `artefakte/<name>/`, nie überschreiben ohne Nachfrage
`speichere_artefakt_ordner` prüft zusätzlich, dass das Ziel wirklich **innerhalb** des Artefakt-Ordners liegt (Test mit absichtlich umgangener Namensprüfung, Name `..`).
Ein vorhandenes Artefakt wird nur nach ausdrücklicher Bestätigung ersetzt. Alternativ gibt es den Download der `artefakt.yaml`, damit es auch ohne Schreibzugriff auf den Ordner geht.
Das Logo wird als bereinigtes `logo.png` daneben gespeichert (siehe docs/05-branding.md).

### Tabellen-Editor (`st.data_editor`) mit Typ-Auswahl
Spalten und KPIs sind Tabellen: Zeilen lassen sich hinzufügen und löschen, der Typ ist eine Auswahlliste (kein Tippfehler möglich).
Technik: Der Editor bekommt einen Schlüssel mit Zähler (`editor_nr`). Nach "Laden" oder CSV-Vorschlag steigt der Zähler, dadurch startet der Editor mit den neuen Daten. Ohne das würde Streamlit
die alten Änderungen des Nutzers über die neuen Daten legen.

## Tests
- `tests/test_models.py`: TF-004 (unbekannte Spalte), TF-005 (kein Anker), TF-007 (Farbe), TF-042 (alle Artefakte im Repo gültig, inklusive Ordnername = Artefaktname), "meinten Sie", Pflichtfelder, ungültige Namen/Tabellen (SQL, Pfad),
  doppelte Spalten/KPIs, unbekannte Felder, Grenzen, YAML-Roundtrip, kaputtes YAML, `!!python/object`, Größenlimit.
- `tests/stories/test_us01_formular.py`: TF-001 (Formular erzeugt gültiges Artefakt), TF-002 (Spaltenvorschlag), TF-003 (Pflichtfeld, keine Datei bei Fehlern) plus Typ-Erkennung aus Text.
- `tests/test_formular.py`: Tabellen-Umwandlung, Speichern/Überschreiben/Ordnergrenze, Rauchtests der Eingabe-App.
- Zusätzlich im Browser: Artefakt laden (gültig, YAML sichtbar), CSV mit `Person` hochladen -> Spalten übernommen, KPI `person` -> "meinten Sie `Person`?".

## Lernnotizen
- Mein erster Test mischte zwei Datumsformate in einer Spalte und schlug fehl. Der Fehler lag im Test: Das System lehnt gemischte Formate **mit Absicht** ab, weil `01.02.` mehrdeutig sein kann. Tests müssen realistische Daten verwenden.
- Pydantic liefert englische Fehlertexte. `_uebersetze` wandelt sie in deutsche Meldungen um, die den Feldnamen nennen (`spalten[2].typ`, gezählt ab 1 wie ein Mensch).

## Offen / für das Team
- **Mit David abstimmen (PSP 3.3/3.4, Risiko R07):** Das Modell ist ein Platzhalter. Zu klären: Feldnamen, Grenzen (12 KPIs, 64 Zeichen), strenge Bezeichner, `Branding.logo` als Zusatzfeld.
- `artefakte/aktivitaet/` ist von mir als Entwurf angelegt; Inhalt und Beispieldaten gehören zu AP 7.4 (David).
- Die KPI-Zeile akzeptiert jeden Text; ob eine KPI **berechenbar** ist, prüft erst der Query-Schritt der Pipeline (Plausibilitätsprüfung, US-05).
