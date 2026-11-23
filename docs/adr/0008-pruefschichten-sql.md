# ADR 0008: Prüfschichten für generiertes SQL

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 13.11.2026 · **Vorgeschlagen von:** DZ · **PSP:** 5.4 (DZ)

## Kontext
Schritt 2 lässt das Sprachmodell aus jeder KPI-Beschreibung ein SQL schreiben. Falsche Zahlen im Dashboard sind das Top-Risiko des Projekts (R01, US-05). Ein Prompt kann nichts erzwingen: Das Modell kann einen anderen SQL-Dialekt verwenden (z. B. `MONTH()` statt `strftime`), eine genannte Spalte ignorieren, eine fremde Tabelle erfinden oder falsch rechnen. Zu entscheiden war, wie das SQL geprüft wird, bevor es in die `dashboard.json` gelangt.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: SQL ungeprüft übernehmen, Fehler fallen im Dashboard auf | kein Aufwand | Fehler erst beim Anwender sichtbar; widerspricht R01 |
| B: nur Ausführung testen | einfach, findet Dialektfehler | übersieht SQL, das läuft, aber Falsches berechnet (ignorierte Spalte, fremde Tabelle) |
| C: mehrere Prüfschichten ohne Sprachmodell, Rückmeldung an das Modell (Reparaturschleife) | findet Fehler früh und meldet sie konkret; das Modell korrigiert sich mit der Fehlermeldung | mehr Code; Prüfregeln müssen gepflegt werden |
| D: ein zweites Modell prüft das SQL | kann inhaltliche Fehler finden | doppelte Laufzeit, selbst nicht verlässlich, nicht reproduzierbar |

## Entscheidung
Wir wählen **C**. Schichten in dieser Reihenfolge (`backend/src/pipeline/harness/validators.py`):
1. **Format:** JSON mit `sql` oder `ablehnung` (per JSON-Schema erzwungen).
2. **Nur lesend:** genau ein SELECT/WITH, nichts Schreibendes (gemeinsame Prüfung aus `runner/sicherheit.py`, US-14).
3. **Bekannt:** nur die Tabelle des Artefakts, nur Spalten aus dem Schema; eigene Aliase sind erlaubt (Zerlegung mit sqlglot, SQLite-Dialekt). Erlaubt sind alle Spalten der Tabelle, nicht nur die in der KPI genannten, weil z. B. „aktueller Monat“ die Datumsspalte braucht, auch wenn sie nicht in Backticks steht.
4. **Bedeutung:** Jede Spalte, die in der KPI in Backticks steht, kommt im SQL vor.
5. **Plausible Rechnung:** kein heutiges Datum (`'now'`, `CURRENT_DATE`, `CURRENT_TIME`, `CURRENT_TIMESTAMP`; siehe Zeitbezüge unten) und keine Division eines Ausdrucks durch sich selbst (Ergebnis wäre immer 1).
6. **Ausführbar:** läuft schreibgeschützt auf der Datenbank aus Schritt 1, liefert Zeilen, und der berechnete Wert (letzte Spalte) ist in keiner Zeile leer (NULL). Ist die erste Ergebnisspalte ein Zeitraum, muss sie aufsteigend sortiert sein, weil das Dashboard die Werte in dieser Reihenfolge zeichnet. Das ist die eigentliche Garantie für den SQLite-Dialekt.
7. **Testorakel:** Vergleich mit Referenzwerten, nur wenn welche vorliegen. In der Pipeline gibt es keine, deshalb greift die Schicht dort nicht; in den Tests weist sie nach, dass z. B. AVG statt SUM erkannt wird (US-05.3).

Scheitert eine Schicht, bekommt das Modell sein letztes SQL und die Meldung zurück; höchstens **3 Versuche** je KPI (wie Schritt 3). Scheitert das Hauptmodell dreimal, **eskaliert** Schritt 2 einmal an das Fallback-Modell (qwen3:14b), mit dem letzten SQL und der letzten Fehlermeldung. Damit gibt es zwei Arten von Fallback: technisch in `llm.py` (Antwort abgeschnitten oder kein gültiges JSON) und inhaltlich in Schritt 2 (an den Prüfschichten gescheitert). Ist kein Fallback eingestellt oder nicht installiert, bricht der Schritt nach drei Versuchen ab. Lehnt das Modell eine KPI begründet ab („mit diesen Daten nicht berechenbar“), gibt es keinen weiteren Versuch. Alle KPIs werden versucht, Probleme gemeinsam gemeldet. Ergänzend gibt der Prompt die Ergebnisspalten vor (zuerst Gruppierung, dann Wert), weil das Dashboard ohne Achsenangabe die erste Spalte als X-Achse und die zweite als Wert nimmt.

**Zeitbezüge beziehen sich auf die Daten, nicht auf den Kalender.** Im ersten Probelauf hat das Modell „aktueller Monat“ als heutiges Datum gelesen (`date('now')`). Das Ergebnis hing damit vom Kalender ab, wäre bei jedem Lauf anders gewesen und bei verspätet hochgeladenen Daten leer geblieben. Deshalb gilt: „aktuell“, „Vormonat“ usw. meinen den jüngsten Wert der Datumsspalte in den Daten (`MAX`). Die Regel im Prompt wird für jeden Datensatz aus den Spaltentypen des Artefakts erzeugt (Spalten vom Typ `datum`), nichts darin ist auf einen Datensatz zugeschnitten. Hat ein Datensatz keine Datumsspalte, sagt der Prompt das ausdrücklich, und eine KPI mit Zeitbezug wird begründet abgelehnt statt mit einer erfundenen Zahl beantwortet. Die Prüfschicht 5 garantiert, dass kein kalenderabhängiges SQL durchkommt, auch wenn das Modell die Regel übergeht. Nebeneffekt: Weil das SQL im Dashboard bei jedem Aufruf läuft, rückt „aktuell“ nach jedem Daten-Upload automatisch mit.

## Konsequenzen
- `temperature: 0` in `llm.py`: gleiche Eingabe ergibt praktisch dasselbe SQL, Ergebnisse sind wiederholbar. Gilt auch für Schritt 3.
- Je KPI im Normalfall ein Modellaufruf, im schlechtesten Fall drei (plus Fallback). Jeder Versuch steht mit Nummer im Run-Protokoll.
- Inhaltlich falsche, aber lauffähige SQL (z. B. falsche Aggregation ohne Referenzwerte) kann die Pipeline nicht sicher erkennen. Dagegen helfen nur Referenzwerte aus dem Testkonzept (AP 8.1) und die sichtbare Berechnung im Dashboard (KPI-Beschreibung in der Fußleiste).
- **Belegte Grenze (Probeläufe 4–6):** Versteht das Modell eine KPI inhaltlich falsch, findet es Varianten, die jede Prüfung über die Form des Ergebnisses bestehen (NULL durch 0 ersetzt, Jahres- statt Monatssumme). Das ist mit generischen Prüfungen nicht vollständig abzufangen; weitere Regeln verschieben das Problem nur. Gegenmittel, Entscheidung im Jour fixe: (1) solche KPIs im Artefakt eindeutig formulieren (z. B. „als eine Zahl: Summe im jüngsten Monat geteilt durch die Summe im Monat davor“), wie in Spezifikation 3.1 vorgesehen; (2) qwen3:14b als Hauptmodell für Schritt 2: nur eine Einstellung (MODELL), im Probelauf auf Anhieb richtig, rund 1,4 statt 0,7 Sekunden je KPI bei einem einmaligen Lauf zur Build-Time; (3) Ergebnis vor der Auslieferung sichten, die Berechnung steht in der Fußleiste jeder Kachel. **Stand nach den Probeläufen 7–10 (24.11.2026):** (1) allein genügt nicht, (2) ist nicht verlässlich, (3) bleibt nötig; neue Kandidaten siehe Nachtrag.
- **Bekannte Grenze:** Kennt sqlglot ein gültiges SQLite-Konstrukt nicht, wird korrektes SQL abgelehnt und erneut angefragt. Gängige Fälle (strftime, WITH, ORDER BY … LIMIT, Aliase) sind durch Tests abgedeckt.

## Belege
- User Story US-05, Spezifikation 3.2
- Tests `backend/tests/test_us05_sql.py` und `backend/tests/test_validators.py`
- Probelauf 1 mit dem Sales-Artefakt und qwen3:8b: „aktueller Monat“ als heutiges Datum gelesen (`date('now')`), deshalb Regel 7 und Prüfung auf Systemzeit
- Probelauf 2: Vormonat durch Vormonat geteilt (Ergebnis immer 1), deshalb Muster für Zeitraumvergleiche in Regel 7 und Prüfung auf Division durch sich selbst. Der Fall zeigt die Grenze aus „Konsequenzen“: Lauffähiges, aber falsch gerechnetes SQL finden die Prüfschichten nur, wenn eine Regel genau diesen Fehler beschreibt
- Probelauf 3: Vergleich zweier Zeiträume mit zusätzlichem WHERE, das den Vormonat ausschließt (Ergebnis NULL), und ein Verlauf absteigend sortiert. Deshalb prüft Schicht 6 auf ein nur leeres Ergebnis und auf aufsteigende Zeiträume
- Probelauf 4: je Monat gruppiert, Wert nur in einer Zeile gefüllt (11 von 12 Zeilen NULL), Ergebnis wieder 1,0. Alle Schichten bestanden, kein zweiter Versuch: ein stiller Fehler. Deshalb lehnt Schicht 6 jeden leeren Wert ab. Derselbe Prompt mit qwen3:14b: richtiges Ergebnis 1,228 im ersten Versuch (siehe Nachtrag in ADR 0006). Deshalb Eskalation an das Fallback-Modell
- Probelauf 5 (qwen3:8b mit Eskalation): Versuch 1 wegen NULL abgelehnt; Versuch 2 war dasselbe SQL mit COALESCE(..., 0), weil die Fehlermeldung COALESCE als Ausweg für gewollte Lücken nannte. Aus NULL wurde 0, die Prüfung war bestanden, der Fehler versteckt. Lehre: Fehlermeldungen an das Modell beschreiben nur das Problem und nennen keinen Weg, der die Prüfung umgeht. Hinweis entfernt
- Probelauf 6 (qwen3:8b): Versuch 1 wegen NULL abgelehnt; Versuch 2 teilt den Jahresumsatz durch den Vormonat (11,19 statt 1,23). Formal korrekt, alle Schichten bestanden. Wie vorab vereinbart, wird danach nicht weiter nachgeschärft (siehe Konsequenzen)
- Nebenbefund: Zwei Läufe mit qwen3:14b erzeugten exakt dieselben SQL-Abfragen; temperature 0 macht die Ergebnisse wiederholbar

## Nachtrag 24.11.2026: Probeläufe 7–10 mit der vollständigen Pipeline
Ablauf: `dashframe-run` mit dem Sales-Artefakt und den Demo-Daten (192 Zeilen, Seed 42), Prompt mit Regel 7 wie oben. Von Lauf zu Lauf geändert wurde nur das Modell oder der Wortlaut der KPI „Zielerreichung ggü. Vorperiode“; Daten, Prüfschichten und temperature 0 blieben gleich. Richtig wäre 123.873 / 100.863 = **1,23** (Dezember / November). Die Artefakt-Kopien liegen nur lokal unter `backend/runs/`, der Wortlaut steht hier, damit jeder die Läufe nachstellen kann.

| Lauf | Modell | Wortlaut der KPI | Versuche | Ergebnis des SQL | Kachel im Dashboard zeigt |
|---|---|---|---|---|---|
| 7 | qwen3:8b | „Summe von `umsatz` im aktuellen Monat geteilt durch die im Vormonat.“ (Original) | 2 | drei Spalten: Vormonat, Jahresumsatz, Quote 11,19 | 100.863 (erste Spalte) |
| 8 | qwen3:8b | „Summe von `umsatz` im jüngsten Monat von `datum` geteilt durch die Summe von `umsatz` im Monat davor. Ergebnis ist genau eine Zahl.“ | 1 | eine Spalte: 11,19 | 11,19 |
| 9 | qwen3:14b | wie Lauf 8 | 3 | kein gültiges SQL („no such column: umsatz“), ehrlicher Abbruch, kein Paket | – |
| 10 | qwen3:8b | wie Lauf 8, dazu: „Beispiel: Ist Dezember der jüngste Monat in den Daten, lautet die Rechnung Dezember / November. Dezember: x (Summe von `umsatz` im Dezember), November: y (Summe von `umsatz` im November), x / y = z“ | 1 | zwei Spalten: Jahresumsatz, Vormonat; keine Division | 1.128.186 |

Die übrigen drei KPIs des Artefakts waren in allen vier Läufen richtig und identisch. Lauf 7 dauerte 16 Sekunden für das ganze Paket (7 Modellaufrufe).

**Befunde**
- **Systematischer Fehler von qwen3:8b:** In den Läufen 7, 8 und 10 ist der Vormonat jeweils richtig gefiltert, der „jüngste Monat“ nie; der Zähler ist der Jahresumsatz. Das ist unabhängig vom Wortlaut. Die Annahme „präzise Eingabe genügt“ ist für Vergleiche zweier Zeiträume damit widerlegt, auch ein Beispiel in der Beschreibung hilft nicht. Positiv: Das Beispiel mit „Dezember“ wurde nicht als festes Datum ins SQL übernommen.
- **qwen3:14b** liefert mit dem heutigen Prompt und dem präzisen Wortlaut kein gültiges SQL, in Probelauf 4 (älterer Prompt) war es auf Anhieb richtig. Als Hauptmodell für Schritt 2 ist es damit nicht verlässlich besser. Die Prüfschichten haben das falsche SQL von 14b abgefangen: kein falsches Dashboard, sondern ein Abbruch mit Meldung.
- **Reparaturschleife und temperature 0:** In Lauf 9 sind Versuch 2 und 3 identisch (gleiche Token-Zahlen). Liefert das Modell dasselbe SQL noch einmal, ist der nächste Prompt Wort für Wort gleich und damit auch die Antwort; jeder weitere Versuch ist verschwendet.
- **Regel 4 wird nur erbeten, nicht geprüft:** Ein Einzelwert mit mehreren Spalten besteht alle Schichten; der Runner zeigt bei einer Kennzahl die erste Spalte. Daher die falschen Kacheln in den Läufen 7 und 10.
- Die Erklärtexte aus Schritt 4 beschreiben bei dieser KPI die Vorgabe statt des tatsächlichen SQL (siehe ADR 0009).
- Das SQL von Fehlversuchen steht nicht im Run-Protokoll, nur die Token-Zahlen; die Ursache eines Fehlversuchs lässt sich deshalb nachträglich nicht immer nachvollziehen.

**Folgerung, Entscheidung im Jour fixe:** Die Sichtung vor Auslieferung (3) bleibt in jedem Fall nötig. Neue Kandidaten, alle allgemein und ohne Bezug auf einen Datensatz:
- (a) Prüfung „Einzelwert = genau eine Spalte“: Eine Zeile mit mehreren Zahlenspalten wird abgelehnt. Die Läufe 7 und 10 wären abgewiesen worden; danach greifen Reparaturschleife und Eskalation.
- (b) Wiederholtes SQL erkennen und dem Modell ausdrücklich melden oder sofort eskalieren, statt Versuche zu verschwenden.
- (c) Selbstprüfung: Das Modell bekommt Vorgabe, SQL und Ergebnis und prüft, ob jede Teilsumme den richtigen Zeitraum abdeckt (ein Aufruf mehr je KPI).
- (d) Denkmodus nur bei der Eskalation (für die Masse ohne Nutzen, ADR 0006; für Einzelfälle ungetestet).
- (e) Quoten zerlegen: Zähler und Nenner als zwei einfache Abfragen, die Division übernimmt der Code (größter Umbau).

Vorschlag: (a) und (b) umsetzen, (c) testen.
