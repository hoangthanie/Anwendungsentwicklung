# US-07 Dokumentation automatisch erzeugen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E2 Agenten-Pipeline | 5.6 | MP | Should |

> **Als** Zielgruppe und Prüfer **möchte ich** nachlesen können, wie jede KPI berechnet wird und für wen das Dashboard gedacht ist, **damit** das Ergebnis nachvollziehbar ist (Modulvorgabe Dokumentation).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-07.1 Jede KPI mit SQL

- **Gegeben** eine Pipeline mit vier KPIs
- **Wenn** die Doku erzeugt wird
- **Dann** enthält sie jede KPI mit ihrem SQL-Statement
- **Test:** `test_us06_07_dashboard_doku.py::test_doku_enthaelt_jede_kpi_mit_sql`

### US-07.2 Zweck und Zielgruppe

- **Gegeben** ein Artefakt mit Ziel und Publikum
- **Wenn** die Doku erzeugt wird
- **Dann** werden beide genannt
- **Test:** `test_us06_07_dashboard_doku.py::test_doku_nennt_zweck_und_zielgruppe`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/harness/docs.py`

```python
erzeuge_doku(artefakt, sql_je_kpi: dict[str, str], llm) -> str   # Markdown
```

## Hinweise

Fakten (SQL, Spalten) kommen aus der Jinja-Vorlage, nur Erklärtexte vom LLM – so kann die Doku nichts Falsches über die Berechnung behaupten.
