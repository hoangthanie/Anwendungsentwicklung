# 03 – Dashboard-Runner (PSP 6.3, US-09)

**Stand:** 2026-10-27 · **Status:** Grundversion lauffähig, 36 Tests grün (inkl. App-Rauchtest ohne Browser) · **Offen:** Daten-Upload (US-10), Logo-Prüfung (6.2), Docker/Pi (DZ)

## Was ist der Runner?
Eine Streamlit-Anwendung, die **jede** `dashboard.json` anzeigen kann. Sie weiß nichts über Umsatz, Regionen oder Produkte.
Alles Fachliche steht in der Konfiguration: welche Charts, welches SQL, welche Farben. Das ist die technische Umsetzung von
"Fabrik statt Produkt" (ADR 0003: ein generisches Image + Konfiguration statt generiertem Code).

## Ablauf in einem Satz
`dashboard.json` laden -> pro Chart das SQL prüfen -> SQL über eine schreibgeschützte Verbindung ausführen -> Ergebnis als Balken, Linie, Tabelle oder Kennzahl zeichnen.

## Dateien und ihre Aufgabe
| Datei | Aufgabe | Warum separat? |
|---|---|---|
| `models/dashboard_config.py` | Pydantic-Modell von `dashboard.json` (`DashboardConfig`, `Chart`, `Branding`) | Gemeinsamer Vertrag zwischen Pipeline (schreibt) und Runner (liest). Validiert beim Laden: erlaubte Chart-Typen, Farbformat `#RRGGBB`, eindeutige Titel. |
| `runner/sicherheit.py` | `pruefe_nur_lesend(sql)`, `verbinde_nur_lesend(db)` | Sicherheit an einer Stelle, einzeln testbar. |
| `runner/daten.py` | `lade_chart_daten`, `sortiere`, `achsen`, `layout_zeilen` | Reine Funktionen ohne Streamlit: testbar ohne Browser. |
| `runner/charts.py` | `erstelle_figur`, `waehle_farbe`, `kennzahl_wert` | Darstellung getrennt von Datenbeschaffung. |
| `runner/app.py` | Dünne Streamlit-Oberfläche | Nur Anordnung und Fehlermeldungen; keine Fachlogik (E-04). |
| `examples/sales/` | Beispiel-`dashboard.json` + Skript für eine Demo-DB | Zum Ausprobieren, solange die Pipeline noch keine echte Datei liefert. |

## Wichtige Entscheidungen (Begründung)

### Zwei Sicherheitsschichten für SQL ("Defense in Depth")
Das SQL in der `dashboard.json` wurde vom LLM erzeugt – oder könnte von jemandem manipuliert worden sein. Der Runner vertraut ihm nicht.
1. **Textprüfung** (`pruefe_nur_lesend`): erlaubt nur ein einziges `SELECT`/`WITH`-Statement. Kommentare und Textliterale werden vorher entfernt, damit
   `SELECT 'DROP TABLE x'` nicht fälschlich auffällt und `-- DELETE` im Kommentar niemanden täuscht. Wortgrenzen (`\b`) sorgen dafür, dass eine
   Spalte `update_datum` nicht blockiert wird.
2. **Schreibgeschützte Verbindung** (`mode=ro` + `PRAGMA query_only`): selbst wenn eine Textprüfung etwas übersieht, lehnt SQLite jeden Schreibzugriff ab.
Eine Blacklist an Schlüsselwörtern ist nie vollständig; deshalb ist die zweite, technische Schicht entscheidend.

### Alles-oder-nichts beim Laden
`lade_chart_daten` prüft **zuerst alle** SQL-Statements und führt erst dann das erste aus. Ein manipuliertes Chart führt also nicht dazu,
dass die anderen noch laufen und ein halbes Dashboard erscheint (Fail-Fast).

### Chart-Konfiguration: "mittlere Stufe"
Gemäß Spezifikation 9.3 kennt `Chart` genau: Typ (`balken`, `linie`, `tabelle`, `kennzahl`), Titel, SQL, Farbe, Sortierung und Breite (`halb`/`voll`).
Mehr Freiheit (eigene Chart-Grammatik) würde den Runner viel aufwendiger machen, weniger wirkte zu generisch.

### Achsen ohne Spaltennamen
`x`/`y` sind optional: Standard ist die erste bzw. zweite Spalte des SQL-Ergebnisses. So bleibt der Runner generisch und die Pipeline muss nur das SQL
passend schreiben. Ist es ausnahmsweise anders, kann sie `x`/`y` setzen.

### Automatisch aktuelle Daten (Cache)
Streamlit cached Funktionsergebnisse. Der Cache-Schlüssel enthält die Änderungszeit der Datenbank (`st_mtime`). Wird die DB geändert (später durch den
Upload), lädt der Runner automatisch neu. Das erfüllt US-10.3 ("neue Werte sofort sichtbar"), ohne dass man den Cache manuell leeren muss.

### Verständliche Fehler statt Stacktrace
`app.py` fängt fehlende Dateien, unerlaubtes SQL und ungültige Konfigurationen ab und zeigt eine Meldung. Wichtig für die Zielgruppe (kein IT-Team).

### Generizität ist testbar
`test_framework_code_ohne_dashboard_begriffe` sucht im gesamten `src/`-Code nach Sales-Begriffen (`umsatz`, `region`, ...). Sobald jemand eines
hart einbaut, schlägt der Test fehl. Das ist die Vorstufe zu US-12.1.

## Ausprobieren
```
cd C:\dev\Anwendungsentwicklung\frontend
.venv\Scripts\activate
python examples/sales/make_demo_db.py      # erzeugt examples/sales/daten.db
streamlit run src/dashboard_framework/runner/app.py
```
Eine andere Konfiguration: `set DASHBOARD_CONFIG=C:\pfad\zur\dashboard.json` vor dem Start. Die DB wird relativ zur JSON-Datei über `db_pfad` gefunden.

## Tests
`pytest` im Ordner `frontend`. Zuordnung zum Backlog: TF-031 (`test_jedes_chart_bekommt_seine_daten`), TF-032 (`test_runner_fuehrt_kein_schreibendes_sql_aus`),
TF-023/024 (Chart-Typen, Roundtrip), plus eigene Tests zur SQL-Prüfung. Testorakel: Die Test-DB enthält Nord = 150, Süd = 70, Ost = 30.

## Lernnotiz: ein Bug auf dem Weg
Beim ersten Testlauf scheiterte die Zahlenformatierung: pandas liefert `numpy.int64`, und das ist kein Python-`int`, `isinstance(wert, int)` war also falsch.
Lösung: `wert.item()` wandelt numpy-Zahlen in normale Python-Zahlen um. Genau dafür sind die Tests da.

## Offen / nächste Schritte
- Upload neuer Daten mit `validate_against_schema` (US-10) – hängt an der Designfrage "nur anhängen oder auch überschreiben".
- Logo anzeigen ist vorbereitet (`branding.logo`), die Prüfung mit Pillow (`pruefe_logo`) kommt in 6.2.
- Das Modell `DashboardConfig` ist ein Platzhalter bis zur Abstimmung mit DZ (PSP 3.4, Risiko R07).
- Docker-Image und Pi-Deployment: David (PSP 7.2/7.3).
