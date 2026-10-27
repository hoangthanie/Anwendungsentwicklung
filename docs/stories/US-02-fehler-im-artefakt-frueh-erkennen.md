# US-02 Fehler im Artefakt früh erkennen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E1 Artefakt erfassen | 3.3 | DB | Must |

> **Als** Fachanwender:in **möchte ich** sofort erfahren, wenn eine KPI eine Spalte verwendet, die es nicht gibt, **damit** Fehler nicht erst als falsches Dashboard sichtbar werden (Fail-Fast).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-02.1 Unbekannte Spalte wird abgelehnt

- **Gegeben** eine KPI referenziert `region`, im Artefakt heißt die Spalte `Region`
- **Wenn** das Artefakt validiert wird
- **Dann** wird es abgelehnt und die Meldung nennt die unbekannte Spalte
- **Test:** `test_models.py::test_unbekannte_spalte_wird_abgelehnt`

### US-02.2 KPI ohne Spaltenanker wird abgelehnt

- **Gegeben** eine KPI-Beschreibung enthält keine Spalte in `Backticks`
- **Wenn** das Artefakt validiert wird
- **Dann** wird es mit Hinweis auf die Backtick-Schreibweise abgelehnt
- **Test:** `test_models.py::test_kpi_ohne_spaltenanker_wird_abgelehnt`

### US-02.3 Ähnliche Spalte vorschlagen

- **Gegeben** eine KPI referenziert `region`, bekannt ist `Region`
- **Wenn** die Fehlermeldung erzeugt wird
- **Dann** schlägt sie „meinten Sie `Region`?“ vor
- **Test:** `test_us02_03_artefakt.py::test_aehnliche_spalte_wird_vorgeschlagen`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/models/artefakt.py`

```python
aehnliche_spalte(name: str, bekannte: list[str]) -> str | None
```

## Hinweise

US-02.1 und US-02.2 sind bereits umgesetzt. Für US-02.3 reicht difflib aus der Standardbibliothek.
