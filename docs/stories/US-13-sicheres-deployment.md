# US-13 Sicheres Deployment

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E4 Betrieb | 7.3, 4.3 | DZ | Should |

> **Als** Betreiber:in **möchte ich** Updates einspielen, ohne Daten zu verlieren, **damit** per Upload ergänzte Daten erhalten bleiben (Risiko R11).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-13.1 Datenbank wird nie überschrieben [manuell]

- **Gegeben** ein Dashboard mit per Upload ergänzten Daten
- **Wenn** ein neues Release deployt wird
- **Dann** ist die Zeilenanzahl unverändert und ein Backup vorhanden
- **Test:** manuell – Release-Checkliste

### US-13.2 Rollback möglich [manuell]

- **Gegeben** ein fehlerhaftes Release
- **Wenn** der Healthcheck fehlschlägt
- **Dann** kann das vorherige Image-Tag gestartet werden
- **Test:** manuell – Release-Checkliste

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `deploy/`

```python
deploy / deploy.sh
```

## Hinweise

Kandidat für späteren automatisierten Test in release.yml.
