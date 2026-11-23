# US-08 Ein Befehl erzeugt das vollständige Paket

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E2 Agenten-Pipeline | 5.2, 5.7 | DZ | Must |

> **Als** Entwickler:in im Team **möchte ich** mit einem Befehl aus einem Artefakt das komplette Dashboard-Paket erzeugen, **damit** neue Dashboards reproduzierbar und messbar entstehen (M3).

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-08.1 Paket wird erzeugt

- **Gegeben** ein gültiges Artefakt und eine Datendatei (CSV)
- **Wenn** pipeline() bzw. dashframe-run läuft
- **Dann** liegen dashboard.json und README.md im Ausgabeordner
- **Test:** `backend/tests/test_us08_12_pipeline.py::test_pipeline_erzeugt_config_und_readme`

### US-08.2 Ungültiges Artefakt stoppt sofort

- **Gegeben** ein ungültiges Artefakt
- **Wenn** dashframe-run läuft
- **Dann** endet es mit Exit-Code 1 und verständlicher Meldung
- **Test:** `backend/tests/test_run.py::test_cli_prueft_artefakt, ::test_cli_meldet_ungueltiges_artefakt`

### US-08.3 Jeder LLM-Aufruf wird protokolliert

- **Gegeben** ein Pipeline-Lauf
- **Wenn** das Modell aufgerufen wird
- **Dann** steht je Aufruf eine Zeile mit Schritt, Tokens, Dauer, Versuch und Zeitstempel in metrics.jsonl
- **Test:** `backend/tests/test_us08_12_pipeline.py::test_jeder_llm_aufruf_wird_protokolliert`

## Schnittstelle (umgesetzt)

Module: `backend/src/pipeline/run.py`, `backend/src/pipeline/harness/llm.py`

```python
pipeline(artefakt_ordner, csv_pfad, ausgabe="ausgabe", llm=None, ueberschreiben=False, fortschritt=None) -> Path
# Fehler: PipelineFehler mit schritt, meldungen, hinweis
```

Befehl: `dashframe-run <artefakt_ordner> <daten.csv> [--ausgabe ausgabe] [--ueberschreiben]`. Das Protokoll schreibt die Klasse `LLM` selbst (eine Zeile je Aufruf, mit Lauf-Kennung), ein eigener `MetrikLogger` ist nicht nötig.

## Hinweise

metrics.jsonl ist die Datengrundlage für die Token-/Laufzeit-Messreihe (AP 8.3, SJ).
