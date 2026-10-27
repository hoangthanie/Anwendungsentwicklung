# Vorgehen: Wie geht es weiter?

Stand: 27.10.2026 · Quelle: `PSP_Arbeitsdokument.xlsx` · Pflege: SJ (Prozesse) / MP (PSP)

## 1. Wo stehen wir?

- **Erledigt:** Projektinitialisierung bis M1 (Concept Paper, Pitch, Projektangebot), PSP, Entwicklungsrechner mit Ollama, Raspberry Pi mit Docker + Tailscale.
- **Fortschritt:** ca. 3 % von 332 h Soll · Termintreue-Index 0,63 → wir liegen leicht hinter dem Plan.
- **Wichtigste offene Entscheidung:** OpenCode vs. Mini-Harness (Spike AP 5.1, Entscheidung bis **30.10.**).

## 2. Meilensteine

| Meilenstein | Datum | Was muss stehen? | CI/CD-Stand |
|---|---|---|---|
| **M2** Fachkonzept & Artefakt-Verträge | 13.11.2026 | Anforderungen (MoSCoW), BPMN, Pydantic-Modelle für Input/Output, Business Model Canvas | `ci.yml` läuft bei jedem PR |
| **M3** Pipeline-Durchstich | 18.12.2026 | `run.py` erzeugt aus `artefakt.yaml` eine vollständige `dashboard.json` | `pipeline-e2e.yml` für Sales + Aktivitätsmonitor |
| **M4** Feature Freeze | 15.01.2027 | Runner, Docker-Image, Deployment auf dem Pi, zweites Dashboard, Tests | `release.yml` deployt auf den Pi |
| **M5** Abschlusspräsentation | 26.01.2027* | Präsentation + Demo + Begleitdokument | Demo-Release eingefroren |

\* unter Vorbehalt, alternativ 01./02.02.2027

## 3. Die nächsten 4 Wochen (bis M2)

### Diese Woche (KW 42/43)
| Wer | Aufgabe | PSP | bis |
|---|---|---|---|
| SJ | ✔ GitHub-Repo angelegt (27.10.); offen: Branch-Schutz für `main`, Team einladen | 4.1 | 30.10. |
| alle | Repo klonen, Setup aus `frontend/README.md` ausführen, `pytest` grün | 4.1 | 30.10. |
| alle | CONTRIBUTING.md lesen, Einwände im Jour fixe | 4.2 | 23.10. |
| MP | Dokumentenablage & Kanäle festlegen, Zeitplan abstimmen | 1.3.1, 1.2.2 | 23.10. |
| DZ + DB | Machbarkeits-Spike OpenCode vs. Mini-Harness starten, Messkriterien festlegen | 5.1 | 30.10. |
| SJ (+MP) | Anforderungen erheben & priorisieren (MoSCoW) | 3.1 | 30.10. |
| MP | Literaturrecherche starten – jede Person liefert Quellen zu ihrem Thema | 2.1 | laufend |

### KW 44 (26.–30.10.)
| Wer | Aufgabe | PSP |
|---|---|---|
| DZ | **Spike abschließen → ADR 0004 schreiben** (Entscheidung im Jour fixe) | 5.1 |
| SJ | Risikoanalyse im Team bestätigen, Top-Risiken-Verantwortliche festlegen | 1.2.3 |
| SJ | CONTRIBUTING.md final, Board-Workflow aktiv | 4.2 |
| DB (+DZ) | `models/artefakt.py` ausbauen, Beispiel-YAMLs gültig/ungültig | 3.3 |
| MP | Gliederung Begleitdokument, Kapitelverantwortliche | 9.1 |
| **offen** | **AP 7.1 (synthetische Daten) braucht eine verantwortliche Person** | 7.1 |

### KW 45–46 (02.–13.11.)
| Wer | Aufgabe | PSP |
|---|---|---|
| SJ | `ci.yml` erweitern (Backend-Tests, Story-Abdeckung), sobald `backend/` existiert → Required Checks | 4.3 |
| SJ | Testkonzept: Stories & Tests in `docs/stories/` im Team freigeben, Referenzwerte (Testorakel) für Sales berechnen | 8.1 |
| SJ (+MP) | BPMN & Use Cases (Vorlage: `CICD_Prozess_Vorlagen.drawio`, Seite 06) | 3.2 |
| SJ (+MP) | Business Model Canvas | 3.5 |
| DZ (+DB) | `models/dashboard_config.py` + JSON-Schema (Output-Vertrag) | 3.4 |
| DZ | `harness/llm.py` + Run-Protokoll `runs/metrics.jsonl` | 5.2 |
| DZ | Sicherheitskonzept (Nur-Lese-SQL, Upload-Prüfung, Tailnet) | 4.6 |
| alle | **10.11. Coaching** – Fragen im Issue „Coaching-Fragen“ sammeln | 1.3.3 |
| alle | **13.11. M2-Review** im Jour fixe | 3.6 |

## 4. Danach (Überblick)

| Zeitraum | Schwerpunkt | Wer |
|---|---|---|
| 09.11.–18.12. | Pipeline-Schritte 1–4, `run.py`, Prompt-Optimierung | DZ, DB, MP (Doku-Schritt) |
| 09.11.–04.12. | Streamlit-Eingabeformular | DB |
| 23.11.–18.12. | Unit-Tests, Token-/Laufzeit-Messreihe | SJ |
| 07.12.–08.01. | Dashboard-Runner, Docker-Image | DB, DZ |
| 04.–15.01. | Deployment Pi, zweites Dashboard, E2E-Test, Abnahme | DZ, SJ |
| 04.–25.01. | Präsentation, Generalprobe, Begleitdokument | MP + alle |

## 5. Regeln, die alle kennen müssen

0. Vor dem Programmieren die passende **User Story** in `docs/stories/` lesen – die Tests dort definieren, was fertig ist.

1. Jede Aufgabe = ein Issue mit PSP-Code. Kein Code ohne Issue.
2. Nichts direkt auf `main` – immer PR, CI grün, 1 Review.
3. Framework-Code kennt **keine** Sales-Begriffe (die CI prüft das).
4. KI-Einsatz sofort im Prompt-Verzeichnis eintragen, nicht erst am Ende.
5. Entscheidungen mit Begründung als ADR festhalten – das braucht das Begleitdokument.
6. Ist-Stunden und Status im PSP wöchentlich pflegen.
