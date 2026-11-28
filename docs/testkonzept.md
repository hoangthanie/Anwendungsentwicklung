# Testkonzept

**AP 8.1 – Testkonzept & Testfälle** · verantwortlich: Stephanie Jayhooni (SJ) · Mitwirkende: alle
Stand: 28.11.2026 · Status: Entwurf, Freigabe im Jour fixe

Dieses Dokument legt fest, **was** wir testen, **womit**, **wann** und **woran wir erkennen, dass es reicht**. Es bündelt, was im Repository schon existiert (User Stories, pytest-Tests, CI, Messwerkzeug), damit alle dieselbe Grundlage haben.

---

## 1. Ziel und Abnahmekriterium

Abnahmekriterium von AP 8.1 laut PSP: **Jede Must-Anforderung hat mindestens einen Testfall.**

Darüber hinaus soll das Testkonzept das Top-Risiko des Projekts absichern: **falsche Zahlen im Dashboard** (R01, siehe `docs/risiken.md` und ADR 0008).

## 2. Was getestet wird – und was nicht

| Im Umfang | Nicht im Umfang |
|---|---|
| Eingabe-App und Artefakt-Prüfung (Frontend) | Lasttests mit vielen gleichzeitigen Nutzern |
| Pipeline-Schritte 1–4 und `run.py` (Backend) | Tests mit echten Unternehmensdaten |
| Prüfschichten für generiertes SQL | Penetrationstests |
| Qualität des Sprachmodells in Schritt 2 (Messung) | Andere Modelle als die in ADR 0006 betrachteten |
| Dashboard-Runner und Paketformat | Browser-Kompatibilität über Chrome/Safari hinaus |
| Betrieb auf dem Raspberry Pi (manuell) | |

## 3. Teststufen

| Stufe | Was | Wo | Wer | Wann |
|---|---|---|---|---|
| **Unit-Tests** | einzelne Funktionen: Validatoren, Pydantic-Modelle, Prüfschichten, Harness | `frontend/tests/`, `backend/tests/` | Entwickler des Codes | mit jedem PR |
| **Story-Tests** | je Akzeptanzkriterium `US-xx.y` ein Test, Marker `@pytest.mark.story(...)` | `frontend/tests/stories/`, `backend/tests/test_usXX_*.py` | Entwickler, Vorlage SJ | mit jedem PR |
| **Integrationstests** | Zusammenspiel der Schritte mit Fake-Modell, z. B. Schritt 3 mit echter `LLM`-Klasse, Pipeline Ende zu Ende | `backend/tests/test_us08_12_pipeline.py`, `test_run.py` | DZ | mit jedem PR |
| **Modell-Messung** | Schritt 2 mit echtem Modell auf 15 Referenz-KPIs (Abschnitt 6) | `backend/tools/messung_sql.py` | SJ / DZ | bei Modell- oder Prompt-Änderung, vor Meilensteinen |
| **E2E-Test auf dem Pi** | Formular → Paket → Dashboard auf dem Raspberry Pi | manuell, Protokoll (AP 8.4) | SJ | vor M4 Feature Freeze |
| **Abnahme** | Anforderungen gegen Ergebnis prüfen | Abnahmeprotokoll (AP 8.5) | SJ, alle | vor M4 |

**Grundsatz:** Alle automatischen Tests laufen **ohne GPU und ohne Ollama**. Das Sprachmodell wird durch Fakes ersetzt (`FakeOllama`, `FakeLLM`, `frontend/tests/fakes.py`). So sind die Tests schnell, wiederholbar und laufen in der CI. Das echte Modell wird nur in der Messung (Abschnitt 6) und im E2E-Test verwendet.

## 4. Werkzeuge und Ablauf

- **pytest** für alle automatischen Tests, **ruff** für den Code-Stil.
- **GitHub Actions** (`.github/workflows/ci.yml`, ADR 0005) führt bei jedem Push und PR aus:

| Check | Inhalt | Pflicht für `main` |
|---|---|---|
| Frontend – Tests | `pytest` im Ordner `frontend` | ja |
| Backend – Tests | `pytest` und `ruff check` im Ordner `backend` | ja |
| Sicherheit – keine Zugangsdaten im Repo | gitleaks | ja |
| Frontend – Code-Stil (Hinweis) | ruff, blockiert nicht | nein |

- Das **Ruleset „main schützen“** verlangt: PR mit mindestens einer Freigabe, alle Pflicht-Checks grün, kein Force-Push, kein Löschen von `main`.
- **Offene Story-Tests:** Noch nicht umgesetzte Kriterien tragen `@pytest.mark.offen("x.y")` und gelten als erwarteter Fehlschlag. Wird ein solcher Test grün, schlägt die CI absichtlich fehl, bis der Marker entfernt ist. So wird Fortschritt sichtbar.

## 5. Testdaten

- **Nur synthetische Daten**, keine echten Unternehmensdaten (Datenschutz, R-Liste).
- `backend/tools/testdaten.py` erzeugt die Daten mit **festem Seed**, also bei jedem Lauf identisch:
  - **Sales** (Tabelle `absatz`): 192 Zeilen, Januar bis Dezember 2026
  - **Aktivitätsmonitor** (Tabelle `aktivitaeten`): 495 Zeilen, Januar bis Juni 2026, ausgedachte Namen. Dient auch als zweites Dashboard für den Generizitätsnachweis (AP 7.4, US-12).
- Kleine Testdaten direkt in den Tests (z. B. 5 Zeilen mit bekannten Summen Nord = 150, Süd = 70, Ost = 30) für Unit- und Story-Tests.
- Fehlerhafte Beispieldateien unter `frontend/examples/testdateien/` für die Prüfung der Uploads (falsche Spalten, Tippfehler, falsche Typen).

## 6. Referenz-KPIs und Testorakel (Schritt 2)

Die Prüfschichten (ADR 0008) stellen sicher, dass ein SQL **technisch** korrekt ist. Ob es **inhaltlich** das Richtige berechnet, lässt sich nur mit bekannten richtigen Ergebnissen prüfen (Testorakel, ADR 0008 Schicht 7). Dafür gibt es ein festes Testset.

**Quelle:** `backend/tools/testset_sql.py` (DZ). Jede KPI hat eine von Hand geschriebene Referenz-Abfrage, die auf den Testdaten das richtige Ergebnis liefert. Der Test `backend/tests/test_messung_sql.py` stellt sicher, dass **jede Referenz alle Prüfschichten besteht**. Die Prüfungen lehnen also keine richtige Antwort fälschlich ab.

| Nr. | Datensatz | KPI | Schwierigkeit | Was sie testet |
|---|---|---|---|---|
| R01 | Sales | Umsatz nach Region | einfach | Summe je Gruppe |
| R02 | Sales | Umsatzverlauf | einfach | Monatsbildung mit `strftime`, aufsteigende Reihenfolge |
| R03 | Sales | Top-Produkte | einfach | Rangliste mit `LIMIT`, Reihenfolge |
| R04 | Sales | Durchschnittspreis je Produkt | mittel | Quotient zweier Summen je Gruppe |
| R05 | Sales | Umsatz im jüngsten Monat | mittel | Zeitbezug aus den Daten statt Kalender |
| R06 | Sales | Anteil Region Nord | mittel | Prozentanteil, Einzelwert |
| R07 | Sales | Zielerreichung ggü. Vorperiode | schwer | Vergleich zweier Zeiträume (bekannte Schwachstelle von qwen3:8b) |
| R08 | Sales | Quartalsvergleich | schwer | Vergleich zweier Quartale |
| R09 | Sales | Kundenzufriedenheit | mittel | **muss begründet abgelehnt werden** (keine passende Spalte) |
| R10 | Aktivität | Aktivitäten je Person | einfach | Anzahl je Gruppe |
| R11 | Aktivität | Dauer im Zeitverlauf | einfach | Zeitreihe auf zweitem Datensatz |
| R12 | Aktivität | Häufigste Aktionen | einfach | Rangliste nach Anzahl |
| R13 | Aktivität | Durchschnittliche Dauer je Aktion | einfach | Durchschnitt je Gruppe |
| R14 | Aktivität | Anteil Meetings an der Arbeitszeit | mittel | Prozentanteil |
| R15 | Aktivität | Aktivität ggü. Vormonat | schwer | Zeitraumvergleich mit Anzahlen, Ganzzahl-Division |

**Neue Fälle** kommen als weiterer Eintrag in `tools/testset_sql.py` dazu. Der Test oben prüft automatisch, ob die Referenz zu Daten und Prüfschichten passt.

## 7. Messreihe Schritt 2 (Verbindung zu AP 8.3)

**Werkzeug:** `backend/tools/messung_sql.py`. Es lässt Schritt 2 für alle Referenz-KPIs genau wie in der Pipeline laufen und vergleicht das Ergebnis mit der Referenz.

```
python tools/messung_sql.py --modell qwen3:8b
python tools/messung_sql.py --modell qwen3:8b --fallback qwen3:14b
```

**Ergebnis je KPI:**

| Ergebnis | Bedeutung | Bewertung |
|---|---|---|
| `richtig` | stimmt mit der Referenz überein (bzw. R09 begründet abgelehnt) | gut |
| `falsch` | SQL hat alle Prüfungen bestanden, rechnet aber falsch | **kritisch**: erreicht das Dashboard |
| `abbruch` | kein gültiges SQL nach allen Versuchen | akzeptabel: ehrlicher Abbruch, kein falsches Dashboard |
| `abgelehnt` | berechenbare KPI fälschlich abgelehnt | unerwünscht |

**Auswertung für 8.3:**

- Mindestens **3 Läufe je Variante** (Abnahmekriterium 8.3). Dank `temperature 0` sind Läufe mit gleichem Modell und Prompt praktisch identisch. Unterschiede entstehen durch Modell, Prompt oder Eskalation.
- Kennzahlen je Variante: Anteil `richtig` / `falsch` / `abbruch` / `abgelehnt`, Versuche je KPI, Tokens (Eingabe/Ausgabe), Dauer.
- **Token-Auswertung nur über Zeilen mit `"art": "aufruf"`** in `runs/metrics.jsonl`. Zeilen mit `"art": "pruefung"` enthalten SQL und Fehlermeldung je Versuch und dienen der Ursachenanalyse.
- Einzelne Pipeline-Läufe lassen sich über das Feld `lauf` abgrenzen.
- Rohdaten bleiben lokal unter `runs/` (nicht im Repo). Die Auswertung kommt ins Begleitdokument (Token-Kapitel) und in ADR 0010.

**Zielwerte (Vorschlag, Freigabe im Jour fixe):**

| Kriterium | Ziel |
|---|---|
| `falsch` | **0** bei allen einfachen und mittleren KPIs |
| `richtig` | ≥ 12 von 15 mit der gewählten Standard-Konfiguration |
| R09 | wird immer begründet abgelehnt |

## 8. Rückverfolgbarkeit: Anforderung → Test

Jede User Story unter `docs/stories/` hat Akzeptanzkriterien `US-xx.y`. Die Tests tragen denselben Bezeichner im Testnamen oder als Marker. Kriterien mit `[manuell]` werden im E2E-Protokoll (8.4) oder in der Abnahme (8.5) nachgewiesen.

| Story | Prio | Testort | Art des Nachweises |
|---|---|---|---|
| US-01 Artefakt per Formular erfassen | Must | `frontend/tests/test_formular.py`, `test_ui.py`, `tests/stories/` | automatisch |
| US-02 Fehler im Artefakt früh erkennen | Must | `frontend/tests/test_models.py`, `tests/stories/` | automatisch |
| US-03 Firmenbranding hinterlegen | Should | `frontend/tests/test_branding.py`, `test_models.py` | automatisch |
| US-04 Datenstruktur automatisch auslesen | Must | `backend/tests/test_us04_schema.py` | automatisch, **umgesetzt** (PR #14) |
| US-05 KPI-Beschreibung in geprüftes SQL übersetzen | Must | `backend/tests/test_us05_sql.py`, `test_validators.py`, `test_messung_sql.py` | automatisch + Messung (Abschnitt 7), **umgesetzt** (PR #15–#17) |
| US-06 Dashboard-Konfiguration erzeugen | Must | `frontend/tests/test_dashboard_config.py`, `backend/tests/test_llm.py` (Schnittstelle) | automatisch |
| US-07 Dokumentation automatisch erzeugen | Should | `backend/tests/test_us07_doku.py` | automatisch, **umgesetzt** (PR #16/#17) |
| US-08 Ein Befehl erzeugt das vollständige Paket | Must | `backend/tests/test_us08_12_pipeline.py`, `test_run.py` | automatisch, **umgesetzt** (PR #16/#17) |
| US-09 Dashboard anzeigen | Must | `frontend/tests/test_runner_app.py` + E2E | automatisch + manuell (8.4) |
| US-10 Neue Daten hochladen | Should | `frontend/tests/test_framework_lib.py` | automatisch |
| US-11 Betrieb auf dem Raspberry Pi | Must | E2E-Protokoll | manuell (8.4) |
| US-12 Generizität: zweites Dashboard | Must | `backend/tests/test_us08_12_pipeline.py` + Aktivitätsmonitor | automatisch + manuell (7.4) |
| US-13 Sicheres Deployment | Should | E2E-Protokoll, Release-Checkliste | manuell |
| US-14 Nur lesender Datenzugriff | Must | `frontend/tests/test_sicherheit.py`, `backend/tests/test_validators.py` | automatisch |

**Ergebnis:** Alle **Must**-Stories haben mindestens einen Testort, damit ist das Abnahmekriterium von AP 8.1 erfüllt. Der genaue Status je Kriterium (grün / offen / manuell) ergibt sich aus der CI und wird in der Backlog-Excel gepflegt.

## 9. Testfälle für Randfälle und ungültige Eingaben

Laut PSP soll das Testkonzept ausdrücklich ungültige Artefakte und Randfälle abdecken. Diese Fälle sind bereits durch Tests belegt:

| Bereich | Randfall | erwartetes Verhalten |
|---|---|---|
| Artefakt | Pflichtfeld fehlt, ungültiger Farbcode, Logo mit Pfad statt Dateiname | verständliche Meldung, Pipeline startet nicht |
| Daten (Schritt 1) | Spalte fehlt, Tippfehler in Spaltenname, falscher Typ (z. B. „viele“ statt Zahl) | alle Meldungen auf einmal, „meinten Sie …?“, keine Datenbank entsteht |
| Daten (Schritt 1) | vorhandene Datenbank | wird nie ohne ausdrückliches Überschreiben ersetzt (US-13) |
| SQL (Schritt 2) | schreibendes SQL (`DELETE`), fremde Tabelle, unbekannte Spalte | abgelehnt, Reparaturschleife |
| SQL (Schritt 2) | heutiges Datum (`now`), Division durch sich selbst, Ganzzahl-Division, mehrere Spalten bei Einzelwert, fehlendes `FROM` | abgelehnt, Reparaturschleife |
| SQL (Schritt 2) | leeres Ergebnis, NULL-Werte, absteigende Zeitreihe, Abfrage läuft länger als 10 s | abgelehnt, Reparaturschleife |
| SQL (Schritt 2) | KPI ohne passende Spalte | begründete Ablehnung statt erfundener Zahl |
| Modell | Ollama nicht erreichbar, Modell nicht installiert, Zeitüberschreitung, Fallback-Modell fehlt | verständliche Meldung, keine verlorene Antwort |
| Paket (run.py) | Fehler in einem Schritt, vorhandenes Paket, Datei gesperrt (Windows) | kein halbes Paket, altes Paket bleibt erhalten, Hinweis was zu tun ist |

## 10. Bekannte Grenzen

- **Inhaltlich falsche, aber lauffähige SQL** erkennen die Prüfschichten nur, wenn eine Regel genau diesen Fehler beschreibt. Sicher erkannt werden solche Fehler nur in der Messung mit Referenzwerten, nicht in der Pipeline selbst (ADR 0008).
- **qwen3:8b** löst Vergleiche zweier Zeiträume (R07, R08, R15) systematisch falsch (Probeläufe 7–10). Gegenmaßnahmen werden im Jour fixe entschieden.
- Deshalb bleibt die **Sichtung vor der Auslieferung** Pflicht: Vorgabe, SQL und Erklärung stehen im Tab „Über dieses Dashboard“.
- Erklärtexte in Schritt 4 formuliert das Modell. Sie sind gekennzeichnet und werden nicht automatisch auf Richtigkeit geprüft.

## 11. Definition of Done (Testsicht)

Ein PR ist fertig, wenn:

1. alle Pflicht-Checks grün sind,
2. neuer Code durch Tests abgedeckt ist, bei Story-Code mit dem passenden `US-xx.y`,
3. erledigte Kriterien ihren `offen`-Marker verloren haben,
4. bei Änderungen an Prompt, Modell oder Prüfschichten die Messung (Abschnitt 7) erneut gelaufen ist und das Ergebnis im PR steht,
5. eine zweite Person freigegeben hat.

## 12. Offene Punkte für den Jour fixe

- Zielwerte für die Messung (Abschnitt 7) freigeben.
- Wer führt die Messläufe für 8.3 durch (Rechner mit GPU nötig)?
- Termin für den E2E-Test auf dem Pi (8.4), abhängig von AP 7.3.
