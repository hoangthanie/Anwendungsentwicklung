# ADR 0001: Lokales LLM statt Cloud-API

- **Status:** angenommen
- **Datum:** 12.09.2026 · **Quelle:** Concept Paper, Kap. 4

## Kontext
Bei einer Cloud-API würden zumindest Schema-Metadaten das eigene System verlassen. Zielgruppe sind KMU mit Anspruch auf Datenhoheit.

## Entscheidung
Inferenz lokal mit Qwen3 über Ollama auf dem Entwicklungsrechner (RTX 4070 Super, aktuell qwen3:14b).

## Konsequenzen
Datenschutz-Spannungsfeld aufgelöst; dafür begrenzte Modellqualität und VRAM (Risiken R01–R03). Self-hosted CI-Runner nötig.
