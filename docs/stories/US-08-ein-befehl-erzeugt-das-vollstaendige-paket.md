# US-08 Ein Befehl erzeugt das vollständige Paket

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E2 Agenten-Pipeline | 5.2, 5.7 | DZ | Must |

> **Als** Entwickler:in im Team **möchte ich** mit einem Befehl aus einem Artefakt das komplette Dashboard-Paket erzeugen, **damit** neue Dashboards reproduzierbar und messbar entstehen (M3).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-08.1 Paket wird erzeugt

- **Gegeben** ein gültiges Artefakt und eine Datenbank
- **Wenn** pipeline() bzw. dashframe-run läuft
- **Dann** liegen dashboard.json und README.md im Ausgabeordner
- **Test:** `test_us08_12_pipeline.py::test_pipeline_erzeugt_config_und_readme`

### US-08.2 Ungültiges Artefakt stoppt sofort

- **Gegeben** ein ungültiges Artefakt
- **Wenn** dashframe-run läuft
- **Dann** endet es mit Exit-Code 1 und verständlicher Meldung
- **Test:** `test_run.py::test_cli_prueft_artefakt, ::test_cli_meldet_ungueltiges_artefakt`

### US-08.3 Jeder LLM-Aufruf wird protokolliert

- **Gegeben** ein Pipeline-Lauf
- **Wenn** das Modell aufgerufen wird
- **Dann** steht je Aufruf eine Zeile mit Schritt, Tokens, Dauer, Versuch und Zeitstempel in metrics.jsonl
- **Test:** `test_us08_12_pipeline.py::test_jeder_llm_aufruf_wird_protokolliert`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/harness/run.py, harness/llm.py`

```python
pipeline(artefakt, db_pfad, out_dir, llm) -> Path
MetrikLogger(pfad).schreibe(schritt=, tokens_in=, tokens_out=, dauer_s=, versuch=1)
```

## Hinweise

metrics.jsonl ist die Datengrundlage für die Token-/Laufzeit-Messreihe (AP 8.3, SJ).
