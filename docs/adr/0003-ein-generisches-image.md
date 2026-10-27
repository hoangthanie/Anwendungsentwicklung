# ADR 0003: Ein generisches Image + Konfiguration statt generiertem Code

- **Status:** angenommen
- **Datum:** 2026 · **Quelle:** Technische Spezifikation, Kap. 9

## Kontext
Ein Image pro Dashboard bedeutet unnötige Build- und Transferzeit; generierter Python-Code ist schwer abzusichern.

## Entscheidung
Der Dashboard-Schritt erzeugt nur eine dashboard.json (Konfigurationssprache mittlerer Reichhaltigkeit). Ein einmal gebautes Runner-Image rendert jede Konfiguration; DB und Konfiguration per Volume.

## Konsequenzen
Kleineres, vorhersehbares Testproblem; neue Dashboards ohne Image-Build. Weniger gestalterische Freiheit pro Dashboard.
