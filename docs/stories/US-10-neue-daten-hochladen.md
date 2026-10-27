# US-10 Neue Daten hochladen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E3 Dashboard zur Laufzeit | 6.3 | DB | Should |

> **Als** Fachanwender:in **möchte ich** neue Monatsdaten per Upload ergänzen, **damit** das Dashboard aktuell bleibt, ohne dass die Pipeline neu läuft.

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-10.1 Gültige Daten werden angehängt

- **Gegeben** eine CSV mit passendem Schema
- **Wenn** ich „Übernehmen“ klicke
- **Dann** werden die Zeilen an die Tabelle angehängt
- **Test:** `test_us09_10_runner.py::test_upload_wird_angehaengt`

### US-10.2 Falsches Schema wird vor dem Schreiben abgelehnt

- **Gegeben** eine CSV mit fehlender Spalte oder falschem Typ
- **Wenn** sie hochgeladen wird
- **Dann** erscheint eine Meldung mit Spaltenname, es wird nichts geschrieben
- **Test:** `test_framework_lib.py::test_gueltiger_upload, ::test_fehlende_spalte, ::test_falscher_typ`

### US-10.3 Dashboard zeigt neue Daten sofort [manuell]

- **Gegeben** Daten wurden übernommen
- **Wenn** die Seite neu lädt
- **Dann** sind die neuen Werte sichtbar (Cache geleert)
- **Test:** manuell – Testprotokoll AP 8.4

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/runner/daten.py`

```python
uebernehmen(df, db_pfad, tabelle) -> int
```

## Hinweise

Offene Designfrage (Spez. 4.7): nur anhängen oder auch überschreiben? Vor der Umsetzung im Team klären.
