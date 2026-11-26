# Architecture Decision Records (ADR)

Jede wichtige Entscheidung bekommt eine kurze Datei – das ist der Nachweis für die im Modul geforderte
**Begründung der getroffenen Entscheidungen** im Begleitdokument.

Neue Entscheidung: `0000-vorlage.md` kopieren, nächste Nummer vergeben, als PR einreichen, im Jour fixe beschließen.

| Nr. | Entscheidung | Status |
|---|---|---|
| [0001](0001-lokales-llm.md) | Lokales LLM (Qwen3 über Ollama) statt Cloud-API | angenommen |
| [0002](0002-build-time-runtime-split.md) | Build-Time auf Entwicklungsrechner, Runtime auf Raspberry Pi | angenommen |
| [0003](0003-ein-generisches-image.md) | Ein generisches Runner-Image + Konfiguration statt generiertem Code | angenommen |
| [0004](0004-harness.md) | Agent-Harness: eigene Mini-Harness statt OpenCode | vorgeschlagen |
| [0005](0005-github-actions.md) | GitHub + GitHub Actions für Repo und CI/CD | angenommen |
| [0006](0006-modellwahl.md) | Modellwahl: qwen3:8b ohne Denkmodus | vorgeschlagen |
| [0007](0007-schritt1-deterministisch.md) | Schritt 1 deterministisch, Daten über die gemeinsamen Bausteine laden | vorgeschlagen |
| [0008](0008-pruefschichten-sql.md) | Prüfschichten für generiertes SQL | vorgeschlagen |
| [0009](0009-fachlogik-getrennt-von-streamlit.md) | Fachlogik in reinen Funktionen, Streamlit dünn, Frontend als installierbares Paket | vorgeschlagen |
| [0010](0010-pruefung-im-artefakt-modell.md) | Prüfregeln im Artefakt-Modell, strenge Bezeichner, sicheres YAML-Laden | vorgeschlagen |
| [0011](0011-spaltenverweise-in-anfuehrungszeichen.md) | Spaltenverweise in Anführungszeichen (gespeichert mit Backticks), Datum mit Uhrzeit | vorgeschlagen |
| [0012](0012-schritt3-modell-waehlt-nur-darstellung.md) | Schritt 3: Modell wählt nur die Darstellung, Abbruch statt Ersatzkonfiguration | vorgeschlagen |
| [0013](0013-upload-nur-anhaengen.md) | Daten-Upload im Runner: zunächst nur anhängen, geprüft und atomar | vorgeschlagen |
| [0014](0014-sicherheit-im-runner.md) | Sicherheit im Runner: nur lesendes SQL, neu kodiertes Logo, escaptes HTML | vorgeschlagen |
| [0015](0015-gestaltungssystem-formblatt.md) | Gestaltungssystem „Formblatt“: festes helles Theme, Kundenfarbe nur als Akzent | vorgeschlagen |
| [0016](0016-frontend-komplett-auf-dem-pi.md) | Gesamtes Frontend auf dem Raspberry Pi, Pipeline mit Modell nicht | vorgeschlagen |
| [0017](0017-docker-einrichtung-und-netzwerkzugriff-pi.md) | Docker (zwei Container), Einrichtung per Skript, Zugriff über LAN und Tailscale | vorgeschlagen |
