# ADR 0009: Schritt 4 und Pipeline-Lauf – Doku für den Anwender, ein Aufruf, keine halben Pakete

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 23.11.2026 · **Vorgeschlagen von:** DZ · **PSP:** 5.6, 5.7 (DZ)

## Kontext
Mit Schritt 4 (Dokumentation, US-07) und `run.py` (ein Aufruf erzeugt das Paket, US-08) ist die Pipeline vollständig. Zu entscheiden waren vier Fragen:
1. Wie entsteht eine Doku, die ein Anwender ohne Technikkenntnisse versteht und die trotzdem nichts Falsches über die Berechnung behauptet?
2. Wo sieht der Anwender diese Doku? Er sieht später nur das Dashboard, keine Dateien.
3. Wie startet der Anwender die Pipeline, und wie erfährt er von einem Fehlschlag? Er wird sie voraussichtlich per Knopf im Frontend starten und hat kein Terminal.
4. Was passiert mit dem Ausgabeordner, wenn ein Schritt scheitert?

Das Paketformat selbst stand schon fest: Es ist der Ordner, den der Runner lokal (`frontend/tools/baue_lokal.py`) und auf dem Pi (`/srv/dashboards/aktuell`) erwartet.

## Betrachtete Alternativen
| Frage | Alternative | Vorteile | Nachteile |
|---|---|---|---|
| Doku | A1: Modell schreibt die ganze Doku | flüssiger Text | Modell kann SQL, Spalten oder Zahlen falsch wiedergeben; nicht prüfbar |
| | **A2: Fakten aus einer Vorlage, nur Erklärtexte vom Modell** | Fakten stimmen immer; das Modell erklärt nur | Text etwas schematischer |
| Modellaufrufe | B1: ein Aufruf je KPI | kürzere Antworten | n-mal Ladezeit und Prompt-Kosten |
| | **B2: ein Aufruf für alle KPIs** | ein Aufruf je Lauf, Tokens sparen (ADR 0004) | eine unbrauchbare Antwort betrifft alle KPIs (abgefangen, siehe Entscheidung) |
| Vorlage | C1: Jinja-Vorlage (Vorschlag in US-07) | Text getrennt vom Code | zusätzliche Bibliothek für wenige Absätze |
| | **C2: Vorlage im Python-Code** | keine neue Abhängigkeit, mit den übrigen Tests prüfbar | Textänderungen im Code |
| Anzeige | D1: nur `README.md` im Paket | einfach | der Anwender öffnet keine Dateien |
| | **D2: Tab „Über dieses Dashboard“ (Feld `doku` der `dashboard.json`), `README.md` als Kopie** | der Anwender sieht die Doku dort, wo er arbeitet; in der Spezifikation 3.4 so vorgeschlagen, der Runner hatte den Tab schon | – |
| Start | E1: nur ein Terminalbefehl | einfach | für den Anwender ohne Terminal unbrauchbar |
| | **E2: Funktion `pipeline()` als Kern, Befehl `dashframe-run` als dünne Hülle** | ein Knopf im Frontend und das Terminal nutzen denselben Ablauf | Fehler müssen für beide Wege taugen (siehe Entscheidung) |
| Fehlschlag | F1: in den Zielordner schreiben, bei Fehler stehen lassen | einfach | halbes Paket, das der Runner trotzdem anzeigt; vorhandenes Dashboard kaputt |
| | **F2: Arbeitsordner, erst bei Erfolg an den Platz verschieben** | nie ein halbes Paket; vorhandenes Paket bleibt bei Fehlern unverändert | ein paar Zeilen mehr Code |

## Entscheidung
Wir wählen **A2, B2, C2, D2, E2 und F2**.
1. **Doku:** Die Vorlage schreibt Zweck, Zielgruppe, Datenbasis (Datei, Zeilen, Zeitraum), Spalten, je KPI die Vorgabe aus dem Artefakt, das SQL und die Darstellung sowie die Entstehung in vier Schritten und die Grenzen der Prüfungen. Das Modell liefert per JSON-Schema je KPI nur zwei Texte: „Was zeigt sie?“ und „Wie wird sie berechnet?“. Ist ein Text leer, zu lang oder einer falschen KPI zugeordnet, fehlt nur dieser Text, mit einem Hinweis. Scheitert der Aufruf ganz, entsteht die Doku ohne Erklärtexte. Der Lauf bricht wegen der Doku nie ab: Ein korrektes Dashboard soll nicht an einem Erklärtext scheitern.
2. **Start und Fehlerbild:** `pipeline(artefakt_ordner, csv, ausgabe, …)` führt die Schritte 1 bis 4 aus. Jeder Fehlschlag wird zu `PipelineFehler` mit drei Feldern: `schritt` (wo), `meldungen` (warum), `hinweis` (was der Anwender tun kann). Das ist dasselbe Muster wie bei `ArtefaktFehler`, das die Eingabe-App schon anzeigt. Vor jedem Schritt meldet ein optionaler Rückruf `fortschritt` den laufenden Schritt, weil Schritt 2 mehrere Minuten dauern kann. Alles, was ohne Modell prüfbar ist (Artefakt, Logo, Datendatei, vorhandenes Paket), wird geprüft, bevor das Modell rechnet. `dashframe-run` gibt dieselben Felder als Text aus und endet mit Exit-Code 1 (US-08.2).
3. **Keine halben Pakete:** Das Paket entsteht in einem versteckten Arbeitsordner im Ausgabeordner. Erst wenn alle Schritte erfolgreich waren, wird es an seinen Platz verschoben. Ein vorhandenes Paket wird nur mit ausdrücklichem Überschreiben ersetzt und erst, wenn das neue fertig ist.
4. **Lauf-Kennung:** Jede Zeile in `runs/metrics.jsonl` trägt das Feld `lauf` (z. B. `2026-11-23T21:50:12_sales`). Damit lässt sich je Dashboard auswerten, was es an Tokens und Zeit gekostet hat (Messreihe 8.3).

## Konsequenzen
- Code in `backend/src/pipeline/schritte/schritt4_doku.py` und `backend/src/pipeline/run.py`, Tests in `backend/tests/test_us07_doku.py`, `test_us08_12_pipeline.py` und `test_run.py`. Ein Ende-zu-Ende-Test liest das erzeugte Paket mit demselben Code, mit dem der Runner die Charts füllt.
- Das Paket läuft ohne Umbau lokal und auf dem Pi.
- **Folgeaufgabe (Frontend, DB):** Ein Knopf „Dashboard erzeugen“ in der Eingabe-App kann `pipeline()` direkt aufrufen. Dafür braucht die Frontend-Umgebung das Backend-Paket und Zugriff auf Ollama. Wie das eingerichtet wird, ist im Jour fixe zu klären.
- **Bekannte Grenze:** Die Erklärtexte formuliert das Modell. Sie können ungenau sein. Deshalb stehen Vorgabe und SQL immer direkt daneben, und die Doku sagt ausdrücklich, dass die Prüfungen die inhaltliche Richtigkeit nicht vollständig sicherstellen (siehe ADR 0008).
- **Bekannte Grenze:** Die Doku nennt, welche Modelle beteiligt sein konnten, aber nicht, ob bei einer KPI tatsächlich das Fallback-Modell gebraucht wurde. Das steht im Protokoll (`fallback` je Zeile).

## Belege
- User Stories US-07 und US-08; Technische Spezifikation 3.4 (Doku-Schritt, Tab „Über dieses Dashboard“ als Erweiterung)
- Tests: 102 Backend-Tests grün (vorher 74), darunter Fehlschlag in Schritt 2 ohne Paket und Überschreiben erst nach Erfolg
- Probelauf mit Ollama und Demo-Daten (192 Zeilen): wird nach dem Lauf ergänzt
