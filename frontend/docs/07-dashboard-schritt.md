# 07 – Pipeline-Schritt 3: Dashboard-Konfiguration (PSP 5.5, US-06)

**Stand:** 2026-10-27 · **Status:** Logik fertig und mit simuliertem Sprachmodell getestet (146 Tests grün) · **Nicht getestet:** mit dem echten Qwen3-Modell (das gehört in den Spike von David, PSP 5.1)

## Was macht dieser Schritt?
Die Pipeline hat vier Schritte (Spezifikation Kap. 3). Dies ist **Schritt 3**:
1. Schema auslesen (David, deterministisch)
2. SQL je KPI erzeugen (David, mit Sprachmodell)
3. **Dashboard-Konfiguration erzeugen (hier)**: aus Artefakt und SQL entsteht die `dashboard.json`, die der Runner anzeigt
4. Dokumentation erzeugen (Melanie)

Der Schritt beantwortet die Frage: *Welche KPI zeigen wir wie?* (Balken, Linie, Tabelle, Kennzahl; Farbe, Sortierung, Breite.) Das ist die einzige Entscheidung, bei der ein Sprachmodell sinnvoll hilft,
denn sie hängt vom Sinn der KPI ab ("Verlauf über Zeit" -> Linie).

## Datei und Funktionen (`harness/dashboard.py`)
| Funktion | Aufgabe |
|---|---|
| `erzeuge_config(artefakt, sql_je_kpi, llm, max_versuche=3)` | Der Schritt selbst (Schnittstelle laut Repository-Doc Anhang B) |
| `wahl_schema(kpi_namen, farben)` | JSON-Schema für das Modell (Aufzählungen der erlaubten Werte) |
| `baue_prompt(artefakt, sql_je_kpi)` | Der Text, den das Modell bekommt |
| `pruefe_antwort(text, kpi_namen, farben)` | Prüft die Antwort auf Format **und** Inhalt |
| `extrahiere_json(text)` | Holt JSON auch aus Codeblöcken oder Text drumherum |
| `ChartWahl`, `Antwort` | Pydantic-Modelle der erwarteten Antwort (kein SQL, keine Zusatzfelder) |
| `DashboardFehler` | Fehler mit verständlicher Meldungsliste |
| `LLMProtokoll` | Was der Schritt vom Modell-Zugang erwartet: `antworte(prompt, schritt, json_schema) -> str` |

## Ablauf in `erzeuge_config`
1. **Vorprüfung ohne Modell:** Gibt es zu jeder KPI ein SQL? Ist jedes SQL nur lesend? Wenn nicht: Abbruch, das Modell wird gar nicht gefragt.
2. **Prompt und Schema** bauen (aus Artefakt und SQL).
3. **Modell fragen**, Antwort prüfen. Ist sie ungültig: derselbe Prompt plus "Deine letzte Antwort war ungültig: <konkreter Fehler>" und nochmal (bis `max_versuche`).
4. **Zusammensetzen:** Der Code baut die Konfiguration aus den Wahlen des Modells **und** den festen Werten (Name, Titel, Tabelle, Branding, Spalten, SQL).
5. **Abschlussprüfung** durch das volle Modell `DashboardConfig` (Typen, Farbformat, eindeutige Titel).
Nach `max_versuche` ohne gültige Antwort: `DashboardFehler` mit dem letzten Fehler. Es gibt nie eine stillschweigend schlechte Konfiguration.

## Entscheidungen und Begründung

### Das Modell darf wenig entscheiden (und kein SQL)
Das Modell wählt je KPI nur `typ`, `farbe`, `sortierung`, `breite`. **Alles andere setzt der Code:** Name, Titel, Tabelle, Branding, Spalten und das SQL.
Gründe:
- **Sicherheit:** Das SQL wurde in Schritt 2 mit mehreren Prüfschichten validiert. Würde das Modell es hier nochmal "mitschreiben", könnte es das geprüfte SQL verändern oder durch ein anderes ersetzen.
  Zusatzfelder sind per Schema verboten (`extra="forbid"`). Test: Schreibt das Modell `"sql": "DELETE ..."` in die Antwort, wird sie abgelehnt und das ursprüngliche SQL bleibt.
- **Zuverlässigkeit:** Je weniger das Modell erzeugen muss, desto seltener macht es Fehler (Konzept: Format-Zuverlässigkeit, Spezifikation Kap. 5).
- **Spezifikation 3.2/6.1 (US-06.2):** "Name, Tabelle und Farben stammen aus dem Artefakt, nicht vom Modell."
Das Backlog erwähnt `DashboardConfig.json_schema()` für das Modell. Ich verwende stattdessen das **schmalere** Schema `wahl_schema`; das volle Schema bleibt für die Endprüfung. Mit David klären, ob das so passt.

### Das Schema begrenzt die Auswahl auf erlaubte Werte
`wahl_schema` zählt die erlaubten Werte auf (`enum`): die KPI-Namen **dieses** Artefakts, die vier Chart-Typen, die Farben **aus der Firmenpalette**. Bei Ollama (Parameter `format`) kann das Modell dann syntaktisch gar keinen anderen Wert erzeugen.
Zwei Sicherheitsnetze, die sich ergänzen (Spezifikation Kap. 5): (1) das Schema erzwingt die Form, (2) `pruefe_antwort` prüft den **Inhalt** (jede KPI genau einmal, Farbe wirklich aus der Palette), weil gültiges JSON trotzdem inhaltlich falsch sein kann.
Die Prüfung steht im Code und nicht nur im Schema, weil nicht jeder Modell-Zugang das Schema erzwingt (und die Tests laufen ohne Modell).

### Reparaturschleife mit konkreter Fehlermeldung
Bei einer ungültigen Antwort fragt der Schritt mit dem **genauen Fehler** nochmal ("es fehlen KPI(s): ...", "Farbe #FF0000 bei KPI 'x' ist nicht erlaubt ..."). Das Modell kann so gezielt korrigieren statt zu raten.
Die Zahl der Versuche ist begrenzt (Standard 3), damit ein hartnäckig falsches Modell die Pipeline nicht endlos blockiert.

### JSON auch aus Codeblöcken retten
Kleine lokale Modelle packen JSON gern in Markdown-Codeblöcke oder schreiben einen Satz davor (Spezifikation Kap. 5). `extrahiere_json` probiert: reiner Text, Inhalt eines Codeblocks, Text von der ersten `{` bis zur letzten `}`.
Das spart Wiederholungen (Token und Zeit), ohne die Prüfung aufzuweichen: Das gerettete JSON muss weiterhin Schema und Inhaltsprüfung bestehen.

### Reihenfolge und Titel bestimmt das Artefakt
Die Charts erscheinen in der Reihenfolge der KPIs im Artefakt, der Titel ist der KPI-Name. Das Modell könnte beides sonst unvorhersehbar ändern; so bleibt das Dashboard so, wie der Anwender es geordnet hat.

### Bewusst kein Standard-Ersatz bei Fehlschlag
Es wäre möglich, nach `max_versuche` automatisch "alles als Tabelle" auszugeben. Das würde aber einen Fehler verstecken (Fail-Fast-Prinzip). Der Abbruch mit Meldung zeigt dem Team, dass das Modell oder der Prompt nicht taugt.
Falls das Team später robusteres Verhalten möchte, wäre ein expliziter Parameter `ersatz_bei_fehler=True` der saubere Weg.

### Zusätzliche Absicherung des SQL
Obwohl Schritt 2 schon prüft, kontrolliert dieser Schritt das SQL nochmals mit `pruefe_nur_lesend` (dieselbe Funktion wie im Runner). Eine fertige Konfiguration soll nie unsicheres SQL enthalten, auch wenn ein anderer Schritt einen Fehler hätte.

### Das Schema der Daten wandert mit
Die Konfiguration enthält `spalten` aus dem Artefakt. Dadurch zeigt der Runner automatisch den Upload-Tab (docs/04-upload.md) mit der richtigen Prüfung, ohne dass jemand das Schema nochmal angeben muss.

## Der Prompt (Beispiel Referenzfall, ca. 1750 Zeichen)
```
Du wählst für jede KPI eines Dashboards die passende Darstellung.

Ziel des Dashboards: <ziel aus dem Artefakt>
Publikum: <publikum>

KPIs (Name | Beschreibung | SQL):
1. <KPI-Name> | <Beschreibung> | <SQL aus Schritt 2>
...
Darstellungen (typ):
- balken: Vergleich einzelner Kategorien
- linie: Verlauf über die Zeit
- tabelle: Rangliste oder Detailwerte mit mehreren Spalten
- kennzahl: genau eine einzelne Zahl

Weitere Angaben je KPI (optional):
- farbe: genau eine dieser Farben: #1F3864, #ED7D31, #70AD47
- sortierung: keine | aufsteigend | absteigend ...
- breite: halb | voll ...

Antworte ausschließlich mit JSON in dieser Form, ohne Erklärung:
{"charts": [{"kpi": "<Name der KPI genau wie oben>", "typ": "balken"}]}
Jede KPI kommt genau einmal vor.
```
Warum diese Bestandteile: **Ziel und Publikum** helfen bei der Wahl ("Vertriebsleitung" -> wenige, klare Charts). **SQL** zeigt dem Modell, was die KPI liefert (Zeitreihe oder eine Zahl).
**Erklärung der Typen** steht drin, damit das Modell sie nicht raten muss. Das Beispiel-JSON zeigt die Form. Optimierung auf weniger Token ist PSP 5.8 (Phase 2, Prompt-Vorlagen), Messung mit dem echten Modell fehlt noch.

## Tests (`tests/stories/test_us06_07_dashboard_doku.py`, `tests/fakes.py`)
`FakeLLM` ersetzt das Modell: liefert vorbereitete Antworten der Reihe nach und merkt sich jeden Aufruf (Prompt, Schritt, Schema). So lässt sich genau prüfen, **was** gefragt wurde und **wie oft**.
- TF-021: erst Text statt JSON, dann gültig -> 2 Aufrufe, Fehlermeldung im zweiten Prompt
- TF-022: Name, Tabelle, Farben aus dem Artefakt, selbst wenn das Modell Zusatzfelder liefert
- weitere: SQL nie vom Modell, Reihenfolge, Modellwahl wird übernommen, fünf Arten ungültiger Antworten, doppelte/fehlende KPI, Farbe außerhalb der Palette, Abbruch nach 3 Versuchen (genau 3 Aufrufe),
  JSON im Codeblock, SQL fehlt/unsicher (Modell wird gar nicht gefragt), Schema-Inhalt, Prompt-Inhalt
- Integration: Die erzeugte Konfiguration lädt im **Runner** mit echten Testdaten alle vier Charts; Speichern und Laden ergibt dieselbe Konfiguration.
`pyproject.toml` enthält jetzt `pythonpath = ["src", "tests"]`, damit `import fakes` in allen Testordnern geht.

## Grenzen und offene Punkte
- **Nicht mit dem echten Modell getestet.** Ob Qwen3:14b zuverlässig gültiges JSON liefert und sinnvolle Typen wählt, zeigt erst der Spike (PSP 5.1) und die Messreihe (PSP 8.3). Erst dann sind `max_versuche` und der Prompt sinnvoll eingestellt.
- **`LLMProtokoll` ist eine Annahme:** David baut `harness/llm.py` (PSP 5.2). Die Methode `antworte(prompt, schritt, json_schema)` ist aus dem Repository-Doc (Anhang B) abgeleitet; bei Abweichung genügt ein kleiner Adapter.
- **`harness/__init__.py`** habe ich angelegt, damit das Paket importierbar ist. Kommt David mit eigenen Dateien dazu, beim Zusammenführen auf Konflikt achten.
- **Qualität der Wahl:** Es gibt (noch) keine Prüfung, ob z. B. `kennzahl` zu einem SQL mit vielen Zeilen passt. Das wäre eine mögliche Erweiterung (Ergebnisform des SQL gegen die Wahl prüfen), setzt Zugriff auf die Datenbank voraus.
