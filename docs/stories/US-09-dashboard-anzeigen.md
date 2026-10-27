# US-09 Dashboard anzeigen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E3 Dashboard zur Laufzeit | 6.3 | DB | Must |

> **Als** Fachanwender:in **möchte ich** mein Dashboard im Browser sehen, **damit** ich Umsatz nach Region, Verlauf und Top-Produkte im Blick habe.

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-09.1 Jedes Chart bekommt seine Daten

- **Gegeben** eine dashboard.json mit mehreren Charts
- **Wenn** der Runner startet
- **Dann** wird für jedes Chart das hinterlegte SQL ausgeführt
- **Test:** `test_us09_10_runner.py::test_jedes_chart_bekommt_seine_daten`

### US-09.2 Kein schreibendes SQL zur Laufzeit

- **Gegeben** eine manipulierte dashboard.json mit DELETE
- **Wenn** der Runner sie lädt
- **Dann** wird das SQL abgewiesen, die DB bleibt unverändert
- **Test:** `test_us09_10_runner.py::test_runner_fuehrt_kein_schreibendes_sql_aus`

### US-09.3 Tab „Über dieses Dashboard“ [manuell]

- **Gegeben** ein erzeugtes Dashboard mit Doku
- **Wenn** ich den Tab öffne
- **Dann** sehe ich die automatisch erzeugte Dokumentation
- **Test:** manuell – Testprotokoll AP 8.4

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/runner/daten.py`

```python
lade_chart_daten(config: DashboardConfig) -> dict[str, pd.DataFrame]
```

## Hinweise

app.py (Streamlit) bleibt dünn und nutzt nur daten.py – so ist die Logik ohne Browser testbar.
