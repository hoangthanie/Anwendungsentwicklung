# ADR 0002: Build-Time/Runtime-Split

- **Status:** angenommen
- **Datum:** 12.09.2026 · **Quelle:** Concept Paper, Kap. 3.6

## Kontext
CPU-Inferenz auf einem Raspberry Pi ist für mehrstufige Agentenläufe zu langsam.

## Entscheidung
Agenten und LLM laufen nur zur Build-Time auf dem Entwicklungsrechner; der Pi führt ausschließlich den generischen Runner aus – ohne LLM.

## Konsequenzen
Minimale Hardwarekosten zur Laufzeit, keine Inferenz-Latenz; zwei getrennte Umgebungen in CI/CD.
