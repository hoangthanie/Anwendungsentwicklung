# US-05 KPI-Beschreibung in geprüftes SQL übersetzen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E2 Agenten-Pipeline | 5.4 | DZ | Must |

> **Als** Pipeline **möchte ich** aus jeder KPI-Beschreibung genau ein geprüftes SQL-Statement erzeugen, **damit** das Dashboard korrekte Zahlen zeigt (Top-Risiko R01).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-05.1 Ein lesendes SQL je KPI

- **Gegeben** eine gültige KPI und das Schema
- **Wenn** erzeuge_sql() aufgerufen wird
- **Dann** entsteht genau ein SELECT, das alle Prüfschichten besteht
- **Test:** `test_us05_sql.py::test_ein_geprueftes_select_je_kpi`

### US-05.2 Schicht Bedeutung

- **Gegeben** das LLM verwendet eine Spalte, die nicht referenziert/bekannt ist
- **Wenn** das SQL geprüft wird
- **Dann** wird es mit dem Spaltennamen in der Meldung abgelehnt
- **Test:** `test_us05_sql.py::test_unbekannte_spalte_im_sql_wird_abgelehnt · test_validators.py::test_unbekannte_spalte_ist_nicht_ausfuehrbar`

### US-05.3 Schicht Plausibilität (Testorakel)

- **Gegeben** Referenzwerte für eine KPI (Nord = 150, Süd = 70, Ost = 30)
- **Wenn** das SQL gegen die Test-DB ausgeführt wird
- **Dann** wird ein falsch rechnendes SQL (z. B. AVG statt SUM) erkannt
- **Test:** `test_us05_sql.py::test_plausibilitaet_gegen_testorakel`

### US-05.4 Reparaturschleife

- **Gegeben** der erste Versuch ist ungültig
- **Wenn** die Prüfung fehlschlägt
- **Dann** wird die Fehlermeldung an das Modell zurückgegeben; nach max_versuche bricht es mit verständlicher Meldung ab
- **Test:** `test_us05_sql.py::test_reparaturschleife_korrigiert_fehler, ::test_abbruch_nach_max_versuchen`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/harness/sql.py, harness/validators.py`

```python
erzeuge_sql(kpi, schema, tabelle, llm, db_pfad, max_versuche=3) -> str
pruefe_bedeutung(sql, erlaubte_spalten: set[str]) -> None
pruefe_plausibilitaet(sql, db_pfad, erwartet: dict[str, float], toleranz=0.01) -> None
```

## Hinweise

Tests nutzen FakeLLM (tests/fakes.py) – keine GPU nötig. Referenzwerte für den echten Sales-Datensatz liefert das Testkonzept (AP 8.1, SJ).
