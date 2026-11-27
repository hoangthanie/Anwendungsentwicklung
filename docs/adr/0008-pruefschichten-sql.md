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

## Nachtrag 27.11.2026: umgesetzte Folgerungen
Aus den Probeläufen 7–10 und dem Review zum PR für 5.6 und 5.7 sind umgesetzt:
- **(a) Einzelwert = genau eine Spalte** (Schicht 5): Liefert die äußerste Abfrage ohne GROUP BY nur Aggregate in mehreren Spalten, wird sie abgelehnt. Die Läufe 7 und 10 wären damit in die Reparaturschleife und danach in die Eskalation gegangen. Gruppierte Ergebnisse und Bezeichnung plus Wert betrifft die Regel nicht.
- **(b) Wiederholtes SQL:** Liefert das Modell ein SQL, das schon einmal abgelehnt wurde, steht das ausdrücklich im nächsten Prompt. Damit ändert sich der Prompt, und mit temperature 0 kann sich auch die Antwort ändern.
- **Protokoll:** Jeder geprüfte Versuch steht mit SQL, Ergebnis und Meldung im Run-Protokoll (`"art": "pruefung"`). Fehlversuche lassen sich so nachträglich nachvollziehen (Messreihe 8.3).

## Nachtrag 27.11.2026: Messung mit dem Testset (Messung 1)
Mit `tools/messung_sql.py` liefen 15 KPIs mit Referenzwerten (9 Sales, 6 Aktivitätsmonitor; 7 einfach, 5 mittel, 3 schwer, davon eine nicht berechenbar) durch Schritt 2, je Modell einmal, temperature 0, Stand der Prüfschichten nach dem ersten Nachtrag vom 27.11.

| Modell | richtig | einfach | mittel | schwer | falsch | Abbruch | Tokens rein / raus |
|---|---|---|---|---|---|---|---|
| qwen3:8b | 10/15 | 7/7 | 3/5 | 0/3 | 5 | 0 | 16.950 / 1.261 |
| qwen3:14b | 9/15 | 7/7 | 2/5 | 0/3 | 4 | 2 | 20.140 / 1.842 |
| qwen3:30b-a3b | 12/15 | 7/7 | 4/5 | 1/3 | 2 | 1 | 17.051 / 1.523 |
| qwen3.5:35b-a3b | 14/15 | 7/7 | 5/5 | 2/3 | 1 | 0 | 11.600 / 936 |
| qwen3:8b, Eskalation an qwen3.5:35b-a3b | 10/15 | 7/7 | 3/5 | 0/3 | 5 | 0 | 16.950 / 1.261 |

**Befunde**
- **Eskalation hilft nicht gegen stille Fehler.** Die letzte Zeile ist identisch mit der ersten: Alle Fehler von qwen3:8b bestanden sämtliche Schichten, eskaliert wird aber nur, wenn alle Versuche scheitern.
- **qwen3.5:35b-a3b** löst am meisten und braucht die wenigsten Tokens, weil es fast nie einen zweiten Versuch braucht; je KPI rund 1,5–2 s statt 0,7–1 s bei qwen3:8b (Modellwahl: siehe ADR 0010).
- **Fehlerarten** (alle 22 Fehlschläge, SQL aus dem Run-Protokoll):

| Fehlerart | Modelle | durch Prüfung abfangbar? |
|---|---|---|
| äußere Abfrage ohne `FROM` („no such column“, 3 Abbrüche; die Logik war sonst richtig) | 14b | ja, Schicht „FROM“ (unten) |
| Beschriftung als zusätzliche Spalte (`'Anteil Region Nord' AS kpi`), die Kachel zeigt den Text | 14b | ja, Einzelwert-Schicht erweitert |
| Division zweier ganzer Zahlen (`COUNT(…) / COUNT(…)` = 0) | 8b, 14b | ja, Schicht „Ganzzahl“ |
| Selbstdivision mit Faktor (`SUM(x) * 1.0 / SUM(x) * 1.0` = 1) | 30b | ja, Selbstdivision erkennt Faktoren |
| Ersatzspalte statt Ablehnung (`AVG(umsatz)` für die Kundenzufriedenheit) – ausgelöst durch die eigene Meldung, die alle erlaubten Spalten aufzählte | 8b, 30b | ja, Meldung verlangt jetzt Ablehnung |
| falscher Zeitraum oder falsche Körnung (Quartal als Monat oder Woche, „jüngster Monat“ als ganze Reihe) | 8b, 14b, 35b | nein, Verständnisfehler |
| Zähler und Nenner vertauscht | 8b | nein, Verständnisfehler |
| ungefragte Aufschlüsselung (Anteil je Monat statt gesamt) | 8b | nein, Verständnisfehler |
| ungültiges SQL (Unterabfrage mitten im CASE) | 30b | ehrlicher Abbruch |

**Umgesetzt (Commit nach Messung 1):** Schichten „FROM vorhanden“ und „keine Division zweier ganzer Zahlen“; Einzelwert zählt feste Werte wie Beschriftungen mit; die Selbstdivision erkennt Faktoren wie `* 1.0`; die Meldung zu unbekannten Spalten verlangt, die KPI abzulehnen statt eine andere Spalte zu nehmen. Alle richtigen SQL aus Messung 1 bestehen die neuen Schichten weiterhin, alle Referenzen aus dem Testset ebenso (Test). Die Verständnisfehler bleiben; sie sind das Thema von ADR 0010.

**Einordnung:** ein Lauf je Modell auf einem selbst gebauten Testset mit 15 KPIs. Mit temperature 0 reproduzierbar, aber keine breite Stichprobe.

## Nachtrag 28.11.2026: Messung 2 nach den neuen Schichten
Gleiches Testset, gleiche Modelle, gleiche Bedingungen, nur mit den Schichten aus dem vorigen Nachtrag.

| Modell | richtig M1 → M2 | stille Fehler M1 → M2 | Abbruch M1 → M2 | Tokens M2 rein / raus |
|---|---|---|---|---|
| qwen3:8b | 10 → 11 | 5 → 4 | 0 → 0 | 19.155 / 1.534 |
| qwen3:14b | 9 → 14 | 4 → 1 | 2 → 0 | 20.147 / 1.755 |
| qwen3:30b-a3b | 12 → 12 | 2 → 1 | 1 → 2 | 19.157 / 1.801 |
| qwen3.5:35b-a3b | 14 → 14 | 1 → 1 | 0 → 0 | 11.600 / 936 |
| qwen3:8b, Eskalation an qwen3.5:35b-a3b | 10 → 11 | 5 → 4 | 0 → 0 | wie qwen3:8b |

Stille Fehler (geprüftes, aber falsches SQL, das im Dashboard landen würde) insgesamt: 12 → 7. Keine richtige Antwort wurde durch die neuen Schichten abgelehnt.

**Wirkung im Einzelnen (aus dem Run-Protokoll):**
- qwen3:14b: Die FROM-Meldung führte zweimal zur richtigen Korrektur (Zielerreichung, Quartalsvergleich), die Beschriftungs-Prüfung zweimal (Anteil Region Nord, Anteil Meetings), FROM und Ganzzahl nacheinander bei „Aktivität ggü. Vormonat“.
- qwen3:8b: Die Ganzzahl-Prüfung führte bei „Aktivität ggü. Vormonat“ zum richtigen Ergebnis.
- qwen3:30b-a3b: Die Selbstdivision mit Faktor wurde erkannt; danach lieferte das Modell ungültiges SQL. Aus einem stillen Fehler (Ergebnis 1,0) wurde ein ehrlicher Abbruch.
- qwen3.5:35b-a3b: unverändert, keine seiner Antworten war betroffen.
- Die Eskalation griff wieder nie: Es gab keinen Fall, in dem qwen3:8b dreimal an den Schichten scheiterte.

**Neuer Befund und Folgerung:** qwen3:8b verlangte bei der Kundenzufriedenheit zweimal die fehlende Spalte. Im dritten Versuch stand im Prompt der Hinweis auf das wiederholte SQL („Schreibe eine andere Abfrage“), und das Modell nahm eine Ersatzspalte (`AVG(umsatz)`). Umgesetzt: Verlangt das Modell zweimal dieselbe Spalte, die es nicht gibt und die keiner vorhandenen ähnelt (also kein Tippfehler), wird die KPI als nicht berechenbar abgelehnt. Die Regel kennt keinen Datensatz, sie prüft nur gegen das Schema des jeweiligen Artefakts. Gegenprobe am 28.11.: qwen3:8b lehnt die Kundenzufriedenheit jetzt nach zwei Aufrufen als nicht berechenbar ab (Ergebnis richtig). Eine Übersetzung einzelner Meldungen von sqlglot (z. B. zu unvollständigem CASE) wurde bewusst nicht umgesetzt: Sie hinge am Wortlaut der Bibliothek und behöbe nur einen einzelnen beobachteten Fall.

**Was bleibt:** Die verbleibenden stillen Fehler sind Verständnisfehler: Zähler und Nenner vertauscht (8b), Quartal als Monat bzw. Woche (8b, 35b), Einzelwert als Monatsreihe (14b), ungefragte Aufschlüsselung (8b), Ersatzgröße ohne vorherige Nachfrage (30b). Prüfschichten ohne Wissen über die Absicht können sie nicht erkennen (siehe ADR 0010).

**Folgerung für die Modellwahl (Entscheidung im Jour fixe):** qwen3:14b und qwen3.5:35b-a3b lösen beide 14 von 15. qwen3:14b passt vollständig in 12 GB Grafikspeicher und ist als Fallback ohnehin installiert; qwen3.5:35b-a3b braucht rund 40 % weniger Tokens, lehnt nicht berechenbare KPIs direkt ab und setzt beim Kunden mindestens 32 GB Arbeitsspeicher voraus. Weil die Eskalation stille Fehler nicht abfängt, entscheidet das Hauptmodell für Schritt 2 über die Qualität, nicht das Fallback-Modell.

**Einschränkung – Überanpassung:** Die neuen Schichten sind allgemein formuliert, wurden aber auf genau diesem Testset gefunden und auf denselben 15 KPIs nachgemessen. Die Verbesserung ist deshalb ein Hinweis, kein Beleg. Belastbar wird sie erst mit einem zweiten, unabhängigen Testset, an dem nichts mehr angepasst wird (geplant vor dem Jour fixe).
