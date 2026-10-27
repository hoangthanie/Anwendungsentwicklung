# US-12 Generizität: zweites Dashboard ohne Codeänderung

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E4 Betrieb | 7.4 | DZ | Must |

> **Als** Projektteam / Prüfer **möchte ich** belegen, dass dieselbe Pipeline mit einem anderen Artefakt ein anderes Dashboard erzeugt, **damit** die Kernthese „Fabrik statt Produkt“ bewiesen ist (Top-Risiko R06).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-12.1 Keine Dashboard-Begriffe im Framework-Code

- **Gegeben** Spalten- und Tabellennamen aller Artefakte
- **Wenn** der Framework-Code durchsucht wird
- **Dann** kommt keiner davon im Code unter src/ vor
- **Test:** `test_us08_12_pipeline.py::test_framework_code_ohne_dashboard_begriffe (+ CI-Job generizitaet)`

### US-12.2 Alle Artefakte sind gültig

- **Gegeben** die Artefakte sales und aktivitaet
- **Wenn** sie validiert werden
- **Dann** sind beide gültig
- **Test:** `test_models.py::test_alle_artefakte_im_repo_sind_gueltig`

### US-12.3 Zweites Dashboard entsteht

- **Gegeben** das Artefakt aktivitaet und passende Daten
- **Wenn** die unveränderte Pipeline läuft
- **Dann** entsteht eine gültige dashboard.json für den Aktivitätsmonitor
- **Test:** `test_us08_12_pipeline.py::test_zweites_dashboard_ohne_codeaenderung`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `artefakte/aktivitaet/`

```python
– (nutzt pipeline())
```

## Hinweise

Im echten LLM-Lauf zusätzlich über die Matrix in pipeline-e2e.yml belegt.
