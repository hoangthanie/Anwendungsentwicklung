# US-06 Dashboard-Konfiguration erzeugen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E2 Agenten-Pipeline | 5.5 | DB | Must |

> **Als** Pipeline **möchte ich** aus den SQL-Statements eine schemakonforme dashboard.json erzeugen, **damit** der generische Runner jedes Dashboard ohne neuen Code anzeigen kann.

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-06.1 Immer schemakonformes JSON

- **Gegeben** das Modell liefert zuerst ungültiges JSON
- **Wenn** erzeuge_config() läuft
- **Dann** wird einmal mit Fehlermeldung nachgefragt und eine gültige DashboardConfig geliefert
- **Test:** `test_us06_07_dashboard_doku.py::test_ungueltiges_json_fuehrt_zu_neuem_versuch`

### US-06.2 Feste Werte setzt der Code

- **Gegeben** ein Artefakt mit Name, Tabelle und Firmenfarben
- **Wenn** die Konfiguration erzeugt wird
- **Dann** stammen Name, Tabelle und Farben aus dem Artefakt – nicht vom Modell
- **Test:** `test_us06_07_dashboard_doku.py::test_name_tabelle_und_firmenfarben_setzt_der_code`

### US-06.3 Nur erlaubte Chart-Typen

- **Gegeben** ein Chart-Typ außerhalb von balken/linie/tabelle/kennzahl
- **Wenn** die Konfiguration validiert wird
- **Dann** wird sie abgelehnt
- **Test:** `test_us06_07_dashboard_doku.py::test_nur_erlaubte_chart_typen · test_models.py::test_dashboard_config_roundtrip`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/harness/dashboard.py`

```python
erzeuge_config(artefakt, sql_je_kpi: dict[str, str], llm, max_versuche=2) -> DashboardConfig
```

## Hinweise

JSON-Schema für den Ollama-format-Parameter: models.dashboard_config.json_schema().
