# ADR 0013: Daten-Upload im Runner: zunächst nur anhängen, geprüft und atomar

- **Status:** vorgeschlagen (Beschluss im Jour fixe, Ersetzen offen)
- **Datum:** 27.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 6.3 (DB), US-10

## Kontext
Der Runner soll neue Daten aufnehmen können (US-10). Die technische Spezifikation (4.7) lässt offen, ob der Upload Daten anhängen oder überschreiben soll. Das Schema ist generisch, es gibt keine feste Schlüsselspalte. Fehlerhafte Uploads dürfen bestehende Daten nicht beschädigen. Die Datenbank soll ansonsten nur lesend geöffnet werden (US-14, ADR 0014).

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| **A: nur anhängen** | sicher (bestehende Daten bleiben unangetastet), einfach, braucht keine Schlüsselspalte | fehlerhafte oder doppelte Uploads sind aus der App nicht korrigierbar |
| B: zusätzlich „Monat ersetzen“ über eine Schlüsselspalte | korrigierbar, kein Doppelt-Eintrag | Schlüsselspalte im Schema nötig, riskanter (löscht Daten) |
| C: komplett überschreiben | einfachste Logik für „aktueller Stand“ | Datenverlust bei Fehlbedienung |

## Entscheidung
Wir starten mit **A** (Auftrag von Dominik). Die Entscheidung für B bleibt im Team offen. Die Datei wird **vor dem Schreiben** gegen das Schema geprüft (Spalten, Typen, leere Werte, fremde Spalten); das Schreiben passiert in **einer Transaktion** (alles oder nichts) über eine eigene, schreibende Verbindung. Das Limit liegt bei 5 MB (Streamlit-Einstellung und eigene Prüfung). Der Anwender sieht vorher eine Vorschau und eine Warnung vor Doppel-Upload.

## Konsequenzen
- Bestehende Daten bleiben bei jedem Fehler unverändert. Ein fehlerhafter, aber gültiger Upload lässt sich aber nur außerhalb der App beheben.
- Der Runner liest die Datenbank sonst nur lesend (`mode=ro`, `PRAGMA query_only`); nur der Upload öffnet sie kurz schreibend.
- Offene Teamfrage: Soll „Monat ersetzen“ nachgerüstet werden? Dafür braucht das Artefakt eine Schlüsselspalte.

## Belege
- `frontend/docs/02-entscheidungen.md` (E-06), `frontend/docs/04-upload.md`
- `frontend/src/dashboard_framework/runner/framework_lib.py` (`validate_against_schema`, `uebernehmen`), `frontend/tests/stories/test_us09_10_runner.py`
