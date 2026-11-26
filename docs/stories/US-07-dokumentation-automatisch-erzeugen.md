# US-07 Dokumentation automatisch erzeugen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E2 Agenten-Pipeline | 5.6 | DZ | Should |

> **Als** Zielgruppe und Prüfer **möchte ich** nachlesen können, wie jede KPI berechnet wird und für wen das Dashboard gedacht ist, **damit** das Ergebnis nachvollziehbar ist (Modulvorgabe Dokumentation).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-07.1 Jede KPI mit SQL

- **Gegeben** eine Pipeline mit vier KPIs
- **Wenn** die Doku erzeugt wird
- **Dann** enthält sie jede KPI mit ihrem SQL-Statement
- **Test:** `backend/tests/test_us07_doku.py::test_doku_enthaelt_jede_kpi_mit_sql`

### US-07.2 Zweck und Zielgruppe

- **Gegeben** ein Artefakt mit Ziel und Publikum
- **Wenn** die Doku erzeugt wird
- **Dann** werden beide genannt
- **Test:** `backend/tests/test_us07_doku.py::test_doku_nennt_zweck_und_zielgruppe`

## Schnittstelle (umgesetzt)

Modul: `backend/src/pipeline/schritte/schritt4_doku.py`

```python
erzeuge_doku(artefakt, sql_je_kpi: dict[str, str], llm, config=None, db_pfad=None, quelle=None) -> str   # Markdown
```

Der Text erscheint im Dashboard im Tab „Über dieses Dashboard“ (Feld `doku` der `dashboard.json`) und liegt als `README.md` im Paket.

## Hinweise

Fakten (Zweck, Spalten, Datenbasis, Vorgaben, SQL, Darstellung, Ablauf) kommen aus der Vorlage im Code, nur die Erklärtexte in einfachen Worten vom LLM (ein Aufruf für alle KPIs) – so kann die Doku nichts Falsches über die Berechnung behaupten. Liefert das LLM keine brauchbare Erklärung, fehlt nur dieser Text; der Lauf bricht nicht ab.
