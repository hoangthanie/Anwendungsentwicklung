# Architecture Decision Records (ADR)

Jede wichtige Entscheidung bekommt eine kurze Datei – das ist der Nachweis für die im Modul geforderte
**Begründung der getroffenen Entscheidungen** im Begleitdokument.

Neue Entscheidung: `0000-vorlage.md` kopieren, nächste Nummer vergeben, als PR einreichen, im Jour fixe beschließen.

| Nr. | Entscheidung | Status |
|---|---|---|
| [0001](0001-lokales-llm.md) | Lokales LLM (Qwen3 über Ollama) statt Cloud-API | angenommen |
| [0002](0002-build-time-runtime-split.md) | Build-Time auf Entwicklungsrechner, Runtime auf Raspberry Pi | angenommen |
| [0003](0003-ein-generisches-image.md) | Ein generisches Runner-Image + Konfiguration statt generiertem Code | angenommen |
| [0004](0004-harness.md) | Agent-Harness: OpenCode vs. Mini-Harness | **offen** – Spike AP 5.1 bis 30.10. |
| [0005](0005-github-actions.md) | GitHub + GitHub Actions für Repo und CI/CD | angenommen |
