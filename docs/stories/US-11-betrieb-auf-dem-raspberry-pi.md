# US-11 Betrieb auf dem Raspberry Pi

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E4 Betrieb | 7.3, 8.4 | DZ | Must |

> **Als** Betreiber:in im KMU **möchte ich** dass das Dashboard ohne technisches Zutun läuft, **damit** kein IT-Team nötig ist.

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-11.1 Dashboard überlebt Neustart [manuell]

- **Gegeben** ein deploytes Dashboard
- **Wenn** der Pi neu gestartet wird
- **Dann** ist das Dashboard nach spätestens 2 Minuten wieder erreichbar
- **Test:** manuell – Release-Checkliste (AP 7.3)

### US-11.2 Erreichbar im Tailnet [manuell]

- **Gegeben** ein Gerät im Tailscale-Netz
- **Wenn** ich die Dashboard-Adresse aufrufe
- **Dann** lädt das Dashboard vollständig
- **Test:** manuell – Testprotokoll AP 8.4

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `deploy/`

```python
deploy/systemd/dashboard@.service, deploy/deploy.sh
```

## Hinweise

Wird automatisiert in release.yml (Healthcheck) und zusätzlich manuell protokolliert.
