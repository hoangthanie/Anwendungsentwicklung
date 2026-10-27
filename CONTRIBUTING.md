# Zusammenarbeit im Projekt (CONTRIBUTING)

Dieses Dokument ist das Ergebnis von **PSP-AP 4.2 „Entwicklungsprozess & Konventionen“** (verantwortlich: SJ).
Abnahmekriterium: *von allen angewendet*. Änderungen an diesen Regeln besprechen wir im Jour fixe.

---

## 1. Der Ablauf in 7 Schritten

```
Issue auf dem Board ─▶ Branch ─▶ Commits ─▶ Pull Request ─▶ CI grün + Review ─▶ Merge ─▶ PSP pflegen
```

1. **Story lesen** – In [docs/stories/](docs/stories/README.md) und in der Backlog-Excel steht zu jeder Aufgabe, was fertig bedeutet (Akzeptanzkriterien + vorbereitete Tests).
1. **Issue wählen** – Jede Aufgabe ist ein Issue auf dem Kanban-Board und trägt den PSP-Code im Titel, z. B. `[5.4] SQL je KPI mit Prüfschichten`. Zieh es nach *In Arbeit* und weise es dir zu.
2. **Branch anlegen** – immer von aktuellem `main`:
   `git switch main && git pull && git switch -c feature/42-sql-pruefschichten`
3. **Klein committen** – nach Conventional Commits (siehe 3.).
4. **Pull Request öffnen** – spätestens, wenn die Arbeit sichtbar wird (Draft-PR ist erwünscht). Die PR-Vorlage ausfüllen.
5. **CI + Review** – alle Checks grün, mindestens **1 Review** einer anderen Person.
6. **Merge** – per *Squash and merge*. Branch wird automatisch gelöscht.
7. **PSP pflegen** – Ist-Stunden, Status und Fortschritt im `PSP_Arbeitsdokument.xlsx` aktualisieren (wöchentlich, AP 1.2.4).

## 2. Branches

| Präfix | Wofür | Beispiel |
|---|---|---|
| `feature/` | neue Funktion | `feature/42-sql-pruefschichten` |
| `fix/` | Fehlerbehebung | `fix/57-json-retry` |
| `artefakt/` | neues oder geändertes Artefakt | `artefakt/aktivitaet` |
| `docs/` | nur Dokumentation | `docs/adr-0004-harness` |
| `ci/` | Workflows, Tooling | `ci/release-workflow` |

- `main` ist geschützt: kein direkter Push, nur über PR.
- Branches leben kurz (Ziel: < 1 Woche). Lieber zwei kleine PRs als einen großen.

## 3. Commit-Nachrichten (Conventional Commits)

```
<typ>(<bereich>): <was, im Imperativ>      ← max. 72 Zeichen

Optional: warum, nicht wie.
Refs #42
```

Typen: `feat`, `fix`, `test`, `docs`, `refactor`, `ci`, `chore`.
Bereiche: `models`, `harness`, `runner`, `deploy`, `data`, `artefakt`.

Beispiele:
`feat(harness): Plausibilitätsprüfung für SQL-Ergebnisse ergänzen` ·
`test(models): ungültige Artefakte ohne KPI ablehnen` ·
`ci: Generizitäts-Check in ci.yml aufnehmen`

## 4. Pull Requests & Reviews

- PR-Titel wie Commit-Nachricht, PSP-Code in der Beschreibung.
- **Reviewer:in**: eine andere Person aus dem Team (bei Code möglichst die Verantwortliche des Ordners laut README); spätestens nach **2 Werktagen** reagieren.
- Review-Fokus: Ist das Ergebnis korrekt und nachvollziehbar? Gibt es Tests? **Keine Sonderfälle für Sales** im Framework-Code (Generizität!)? KI-Einsatz dokumentiert?
- Kommentare sind Vorschläge, kein Urteil. „Nit:“ markiert Kleinigkeiten, die den Merge nicht blockieren.

## 5. Definition of Done

Ein Issue ist **erledigt**, wenn:

- [ ] alle CI-Checks grün sind („Frontend – Tests“, „Sicherheit – keine Zugangsdaten im Repo“)
- [ ] die zugehörigen Akzeptanzkriterien (`US-xx.y`) grün sind und der Marker `@pytest.mark.offen` entfernt ist
- [ ] mindestens 1 Review erfolgt ist
- [ ] neue Logik durch Tests abgedeckt ist (Testfälle aus dem Testkonzept, AP 8.1)
- [ ] README / Doku / ADR aktualisiert sind, falls sich Verhalten oder Entscheidungen ändern
- [ ] KI-Einsatz im [Prompt-Verzeichnis](docs/prompt-verzeichnis.md) eingetragen ist (Modulpflicht)
- [ ] das Issue auf dem Board in *Done* liegt und der PSP-Status gepflegt ist

## 6. Kanban-Board

| Spalte | Bedeutung | PSP-Status |
|---|---|---|
| Backlog | geplant, noch nicht bereit | Offen |
| Ready | beschrieben, Abnahmekriterium klar | Offen |
| In Arbeit | jemand arbeitet daran (max. 2 Issues pro Person) | In Arbeit |
| In Review | PR offen | In Review |
| Done | DoD erfüllt | Abgeschlossen |
| Blockiert | wartet auf etwas – im Jour fixe ansprechen | Blockiert |

## 7. KI-Nutzung (Modulvorgabe)

Alle mit generativer KI erzeugten Inhalte (Code, Texte, Diagramme) werden gekennzeichnet:

1. Eintrag im [Prompt-Verzeichnis](docs/prompt-verzeichnis.md) (Datum, Tool, Zweck, Prompt, Prüfung).
2. Im PR die Checkbox „KI-Einsatz dokumentiert“ setzen.
3. KI-Ergebnisse immer selbst prüfen – „kritisch reflektierend“ ist Teil der Bewertung.

## 8. Sicherheit

- Keine Secrets im Repo. `.env` bleibt lokal (Vorlage: `.env.example`), Zugangsdaten nur als GitHub Secrets.
- Generiertes SQL läuft ausschließlich gegen read-only geöffnete Datenbanken.
- Keine echten Unternehmensdaten im Repo – nur synthetische Daten.

## 9. Termine & Regeln im Zeitverlauf

- **Jour fixe** wöchentlich (Moderation MP): Board durchgehen, Blocker lösen, Top-Risiken prüfen.
- **Coachings** Prof. Ahlf: 10.11., 15.12.2026, 12.01.2027 – Fragen vorher im Issue „Coaching-Fragen“ sammeln.
- **Feature Freeze ab 15.01.2027 (M4)**: nur noch `fix/`- und `docs/`-Branches.
