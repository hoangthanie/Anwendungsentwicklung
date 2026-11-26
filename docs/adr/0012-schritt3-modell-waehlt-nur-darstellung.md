# ADR 0012: Schritt 3: Das Modell wählt nur die Darstellung, nie SQL oder Namen; Abbruch statt Ersatzkonfiguration

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 27.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 5.5 (DB)

## Kontext
Schritt 3 der Pipeline erzeugt die `dashboard.json`. Das Backlog nennt als Hinweis, das Modell gegen `DashboardConfig.json_schema()` die komplette Konfiguration schreiben zu lassen. Das geprüfte SQL aus Schritt 2 (ADR 0008) darf aber nicht mehr verändert werden. Name, Tabelle und Branding stehen laut US-06 bereits im Artefakt. Es bleibt nur zu entscheiden, wie jede KPI dargestellt wird.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: Modell erzeugt die komplette `dashboard.json` | entspricht dem Backlog-Hinweis, eine Aufgabe | langes Ergebnis (mehr Tokens, mehr Fehler), Modell könnte SQL oder Farben verändern |
| **B: Modell wählt je KPI nur Typ, Farbe, Sortierung und Breite; der Code setzt alles Übrige** | kurzes Schema (`wahl_schema`), geprüftes SQL bleibt unverändert, Name/Tabelle/Branding kommen sicher aus dem Artefakt | weicht vom Backlog-Hinweis ab, braucht zusätzlichen Zusammenbau im Code |
| C: nach gescheiterten Versuchen eine Standardkonfiguration verwenden | Pipeline liefert immer ein Dashboard | versteckt ein untaugliches Modell oder einen schlechten Prompt |
| **D: nach `max_versuche` ungültigen Antworten Abbruch mit `DashboardFehler`** | Fail-Fast, Fehler sind sichtbar und messbar | kein Dashboard in diesem Lauf |

## Entscheidung
Wir wählen **B und D**. Das Modell antwortet nur mit einem schmalen JSON-Schema (Typ, Farbe, Sortierung, Breite je KPI). Der Code setzt Name, Titel, Tabelle, Branding, Spalten, SQL und Beschreibung aus dem Artefakt und dem Ergebnis von Schritt 2. Die Endprüfung macht `DashboardConfig`. Antworten werden bis zu `max_versuche` mit Reparaturschleife neu angefragt, danach folgt ein `DashboardFehler`, keine Ersatzkonfiguration.

## Konsequenzen
- Das Modell kann das geprüfte SQL nicht ändern; weniger Ausgabe bedeutet weniger Fehler und Tokens.
- Das Feld `beschreibung` je Chart kommt aus dem Artefakt (KPI-Beschreibung) und ist ein zusätzliches Feld im Vertrag `dashboard.json`. **Mit David abstimmen** (PSP 3.4).
- Die Anbindung an das Modell läuft über `LLMProtokoll.antworte(prompt, schritt, json_schema)`. Davids `llm.py` hält sich an dieses Protokoll, Schritt 3 kann sie direkt nutzen.
- Bisher nur mit FakeLLM getestet (146 Tests zum Zeitpunkt der Entscheidung); der Lauf mit dem echten Modell steht aus.
- Ein expliziter Ersatzmodus wäre später möglich, wenn das Team ihn will.

## Belege
- `frontend/docs/02-entscheidungen.md` (E-13, E-14), `frontend/docs/07-dashboard-schritt.md`
- `frontend/src/dashboard_framework/harness/dashboard.py`, `frontend/tests/stories/test_us06_07_dashboard_doku.py`
