# US-04 Datenstruktur automatisch auslesen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E2 Agenten-Pipeline | 5.3 | DZ | Must |

> **Als** Pipeline **möchte ich** Spalten, Typen und Beispielwerte direkt aus der Datenbank lesen, **damit** das LLM nichts über die Datenstruktur raten muss und Abweichungen zum Artefakt auffallen.

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-04.1 Schema aus der DB lesen

- **Gegeben** eine SQLite-Tabelle absatz
- **Wenn** lese_schema() aufgerufen wird
- **Dann** liefert es alle Spalten in Reihenfolge mit SQLite-Typ
- **Test:** `test_us04_schema.py::test_schema_wird_aus_db_gelesen`

### US-04.2 Abgleich Artefakt ↔ Daten

- **Gegeben** Artefakt und tatsächliche Daten unterscheiden sich
- **Wenn** abgleich() aufgerufen wird
- **Dann** nennt je Abweichung eine verständliche Meldung; bei Übereinstimmung ist die Liste leer
- **Test:** `test_us04_schema.py::test_abweichung_artefakt_vs_daten_wird_gemeldet, ::test_passendes_schema_ohne_meldung`

### US-04.3 Beispielwerte begrenzen

- **Gegeben** eine Tabelle mit vielen Zeilen
- **Wenn** das Schema gelesen wird
- **Dann** enthält jede Spalte 1–3 Beispielwerte (Token sparen)
- **Test:** `test_us04_schema.py::test_hoechstens_drei_beispielwerte`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/harness/schema.py`

```python
lese_schema(db_pfad, tabelle) -> list[SpaltenInfo]
abgleich(artefakt: Artefakt, schema: list[SpaltenInfo]) -> list[str]
```

## Hinweise

Rein deterministisch, kein LLM-Aufruf (Spez. 3.1). DB read-only öffnen (validators.verbinde_nur_lesend).
