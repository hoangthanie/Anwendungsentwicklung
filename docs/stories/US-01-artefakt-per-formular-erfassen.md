# US-01 Artefakt per Formular erfassen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E1 Artefakt erfassen | 6.1 | DB | Must |

> **Als** Fachanwender:in (Vertriebsleitung) **möchte ich** Ziel, Zielgruppe, Spalten und KPIs in einem Formular eintragen, **damit** ohne Data-Engineering-Team ein gültiges Artefakt entsteht.

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-01.1 Formular erzeugt gültiges Artefakt

- **Gegeben** alle Pflichtfelder sind ausgefüllt
- **Wenn** ich speichere
- **Dann** entsteht ein Artefakt, das gegen das Artefakt-Modell gültig ist (artefakt.yaml)
- **Test:** `test_us01_formular.py::test_formular_erzeugt_gueltiges_artefakt`

### US-01.2 Spalten aus der Datei vorschlagen

- **Gegeben** ich lade eine CSV-/Excel-Datei hoch
- **Wenn** das Formular die Spalten anzeigt
- **Dann** werden Name und Typ jeder Spalte vorgeschlagen (datum, text, ganzzahl, dezimal, bool)
- **Test:** `test_us01_formular.py::test_spaltenvorschlag_aus_hochgeladener_datei`

### US-01.3 Fehlende Pflichtfelder melden

- **Gegeben** ein Pflichtfeld (z. B. Ziel) ist leer
- **Wenn** ich speichere
- **Dann** erhalte ich eine Meldung mit dem Feldnamen und es wird keine Datei geschrieben
- **Test:** `test_us01_formular.py::test_fehlendes_pflichtfeld_wird_mit_feldname_gemeldet`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/eingabe/formular.py`

```python
artefakt_aus_formular(daten: dict) -> Artefakt
spalten_vorschlag(df: pd.DataFrame) -> list[dict[str, str]]
```

## Hinweise

Die Streamlit-Oberfläche selbst ruft nur diese Funktionen auf – UI-Logik bleibt dünn und die Fachlogik testbar.
