# US-14 Nur lesender Datenzugriff

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E5 Sicherheit | 4.6 | DZ | Must |

> **Als** Unternehmen (Datenhoheit) **möchte ich** sicher sein, dass generiertes SQL keine Daten verändert, **damit** Fehler oder Manipulationen keinen Schaden anrichten (Risiko R14).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-14.1 Nur SELECT erlaubt

- **Gegeben** ein SQL mit INSERT/UPDATE/DELETE/DROP …
- **Wenn** es geprüft wird
- **Dann** wird es abgelehnt
- **Test:** `test_validators.py::test_erlaubte_abfragen, ::test_schreibende_oder_mehrfache_abfragen_werden_abgelehnt`

### US-14.2 Genau ein Statement

- **Gegeben** mehrere Statements mit Semikolon
- **Wenn** sie geprüft werden
- **Dann** werden sie abgelehnt
- **Test:** `test_validators.py::test_schreibende_oder_mehrfache_abfragen_werden_abgelehnt`

### US-14.3 DB technisch schreibgeschützt

- **Gegeben** eine read-only geöffnete Verbindung
- **Wenn** ein Schreibversuch erfolgt
- **Dann** schlägt er auf Datenbankebene fehl
- **Test:** `test_validators.py::test_db_ist_technisch_schreibgeschuetzt`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/harness/validators.py`

```python
pruefe_nur_lesend(sql) -> str
verbinde_nur_lesend(db_pfad) -> sqlite3.Connection
```

## Hinweise

Bereits umgesetzt – Beispiel für den Zielzustand aller Stories.
