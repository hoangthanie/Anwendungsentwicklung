# ADR 0004: Agent-Harness: eigene Mini-Harness statt OpenCode

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 08.11.2026 · **Vorgeschlagen von:** DZ · **PSP:** 5.1 (DZ)

## Kontext
Die Spezifikation sah OpenCode als Agent-Harness vor, der PSP plant eine eigene Mini-Harness (`llm.py`, `run.py`). Die Pipeline-Schritte 1, 2 und 4 rufen das lokale Modell mit fest vorgegebenen Aufgaben auf und erwarten je Aufruf genau eine strukturierte Antwort (JSON). Rahmen: lokales Modell über Ollama (ADR 0001), RTX 4070 Super mit 12 GB, Kontext 12.288 Tokens.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: OpenCode (v2.2.6) als Harness | Agentenschleife, Werkzeuge und Sitzungen fertig vorhanden | ca. 4.900 Tokens Systemprompt und Werkzeugbeschreibungen je Aufruf; Antwortformat nicht erzwingbar; bringt Datei- und Shell-Zugriff mit; eigene Installation (im ersten Benchmark nach 323 Aufgaben nicht mehr startfähig) |
| B: Mini-Harness (direkter Aufruf der Ollama-API) | nur die Aufgabe im Prompt; Format per JSON-Schema erzwungen; Tokens und Zeiten direkt aus jeder Antwort; kein Werkzeugzugriff | Wiederholung bei Fehlern, Protokoll und Prüfschichten selbst bauen |

## Entscheidung
Wir wählen **B: eigene Mini-Harness**.

Gemessen mit qwen3:8b, drei Aufgaben im Stil von Schritt 2 (Gesamtumsatz, Umsatz je Region, nicht beantwortbare Frage), identische Anweisung. Denkmodus an, weil qwen3 über die von OpenCode genutzte Schnittstelle standardmäßig denkt; so wird gleich mit gleich verglichen.

| Mittelwert je Aufruf | Direkt (Ollama) | Über OpenCode | Faktor |
|---|---|---|---|
| Eingabe-Tokens | 191 | 5.057 | × 26 |
| Ausgabe-Tokens | 239 | 557 | × 2,3 |
| Laufzeit | 3,0 s (+ ca. 4,4 s Laden) | 10,5 s (inkl. Laden) | × 1,4 |
| Richtig gelöst | 3 / 3 | 2 / 3 | – |

Rund 96 % der Eingabe über OpenCode sind Overhead, der für fest vorgegebene Pipeline-Schritte keinen Nutzen hat und ca. 40 % des Kontexts belegt, bevor die Aufgabe beginnt. Da je Dashboard mehrere Aufrufe anfallen (Schema, SQL je KPI, Doku), vervielfacht sich das. Die Mini-Harness erzwingt zudem das Antwortformat: Alle 21 direkten Aufrufe der Modellmessung (ADR 0006) lieferten gültiges JSON.

**Abweichung vom Plan:** Vorgesehen waren ≥ 3 Läufe je Variante, gemessen wurde je ein Lauf. Begründung: Systemprompt und Aufgabe sind bei jedem Aufruf gleich groß, die Eingabe-Tokens als Hauptargument schwanken daher nicht. Der Faktor 26 liegt weit über jeder Streuung. Die Trefferquote 2 / 3 ist eine Momentaufnahme und nicht Grundlage der Entscheidung.

## Konsequenzen
- `backend/src/pipeline/harness/llm.py` setzt die Mini-Harness um: ein Ollama-Aufruf je Schritt über die Schnittstelle `LLMProtokoll` (`antworte(prompt, schritt, json_schema)`), Format per JSON-Schema, Run-Protokoll (`runs/metrics.jsonl`) mit Tokens und Laufzeit je Aufruf.
- Wiederholung bei ungültiger Antwort und Prüfschichten (z. B. SQL nur lesend) bauen wir selbst.
- OpenCode wird für die Pipeline weder installiert noch vorausgesetzt. Das Modell erhält keinen Datei- oder Shell-Zugriff (passt zu US-14).
- Wird später eine echte Agentenschleife nötig (Modell entscheidet selbst über Werkzeuge), ist diese Entscheidung neu zu prüfen.

## Belege
- Begleitdokument `docs/docs_melanie/Modellwahl_und_Harness.docx`, Abschnitte 3 und 4
- Messskripte `backend/tools/messung_modellwahl.py` und `backend/tools/messung_opencode.py` (Messung vom 08.11.2026, PR #3)
- Messhinweis: Vor jedem OpenCode-Aufruf wurde das Modell entladen, sonst zählt Ollama nur den nicht zwischengespeicherten Teil des Prompts.
