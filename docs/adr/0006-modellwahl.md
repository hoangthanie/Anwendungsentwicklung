# ADR 0006: Modellwahl: qwen3:8b ohne Denkmodus

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 08.11.2026 · **Entschieden von:** Team im Jour fixe · **PSP:** 5.1 (DZ)

## Kontext
ADR 0001 legt lokale Inferenz mit Qwen3 über Ollama fest, das konkrete Modell war offen (bisher qwen3:14b). Auf der RTX 4070 Super (12 GB) laufen mehrere Kandidaten. Qwen3-Modelle haben einen Denkmodus, in dem sie vor der Antwort Zwischenschritte ausgeben. Gesucht ist das Modell, das die Pipeline-Aufgaben zuverlässig löst und dabei am wenigsten Tokens und Zeit braucht.

## Betrachtete Alternativen
Gemessen: drei Aufgaben im Stil von Schritt 2 (Gesamtumsatz, Umsatz je Region, nicht beantwortbare Frage) auf synthetischen Verkaufsdaten, je ein Lauf, direkt über die Ollama-API mit JSON-Schema.

| Modell | Denkmodus | Richtig | Ausgabe-Tokens Ø | Laufzeit Ø |
|---|---|---|---|---|
| **qwen3:8b** | **aus** | **3 / 3** | **27** | **0,4 s** |
| qwen3.5:9b | aus | 2 / 3 | 24 | 0,5 s |
| qwen3:14b | aus | 3 / 3 | 29 | 0,9 s |
| qwen2.5-coder:14b | – | 3 / 3 | 35 | 1,0 s |
| qwen3:8b | an | 3 / 3 | 239 | 3,0 s |
| qwen3:14b | an | 3 / 3 | 185 | 5,4 s |
| qwen3.5:9b | an | 3 / 3 | 493 | 8,2 s |

Eingabe bei allen rund 190 Tokens. Laufzeit ohne einmaliges Laden des Modells.

## Entscheidung
Wir wählen **qwen3:8b ohne Denkmodus**, weil es
- alle Aufgaben richtig löst, wie die größeren Modelle,
- am schnellsten ist (gut doppelt so schnell wie qwen3:14b, rund 8-mal so schnell wie mit Denkmodus),
- unter den fehlerfreien Modellen die wenigsten Ausgabe-Tokens erzeugt,
- weniger Grafikspeicher belegt (rund 5 statt rund 9 GB) und so mehr Platz für längere Eingaben lässt.

Der Denkmodus brachte bei keinem Modell einen Genauigkeitsgewinn, kostete aber 6- bis 20-mal so viele Ausgabe-Tokens.

## Konsequenzen
- Die Harness (ADR 0004) sendet `think: false` und setzt eine Ausgabegrenze (`num_predict`). qwen3:8b mit Denkmodus geriet in einem früheren Versuch in eine Endlosschleife.
- Das Modell ist eine Einstellung (`MODELL` in `backend/.env`), kein Code. `backend/.env.example` steht jetzt auf `qwen3:8b`, ein Wechsel braucht keine Codeänderung.
- **Offen für den Jour fixe:** qwen3:14b ohne Denkmodus als Fallback in der Harness, z. B. wenn qwen3:8b keine gültige Antwort liefert. In der Messung ebenfalls 3 / 3, rund doppelt so langsam.
- Grenze der Messung: Die Aufgaben sind bewusst einfach, einen Qualitätsunterschied zwischen 8b und 14b zeigen sie nicht. Scheitert qwen3:8b an schwierigeren KPIs, messen wir mit dem vorhandenen Skript neu.

## Belege
- Begleitdokument `docs/docs_melanie/Modellwahl_und_Harness.docx`, Abschnitte 1 und 2
- Messskript `backend/tools/messung_modellwahl.py` (Messung vom 08.11.2026, PR #3; Kontext 12.288, Ausgabegrenze 4.096, RTX 4070 Super)
