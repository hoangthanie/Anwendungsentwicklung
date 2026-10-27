# User Stories & Akzeptanzkriterien

Ergebnis von **AP 3.1** (Anforderungen) und **AP 8.1** (Testkonzept) – verantwortlich SJ. Priorisierung nach MoSCoW ist ein **Entwurf** und wird im Team freigegeben.

## So arbeitest du mit den Stories

1. **Story lesen** – jede Datei beschreibt *wer* *was* *wozu* braucht, die Akzeptanzkriterien (Gegeben/Wenn/Dann) und die vorgeschlagene Schnittstelle.
2. **Tests ansehen** – zu jedem Kriterium gibt es bereits einen Test in `tests/stories/` (oder `tests/`). Er beschreibt genau, was fertig bedeutet.
3. **Implementieren**, bis der Test grün ist. Noch offene Tests tragen `@pytest.mark.offen("x.y")` und gelten als *erwarteter Fehlschlag* (CI bleibt grün).
4. **Marker `offen` entfernen.** Ein Test, der grün wird, aber noch `offen` trägt, lässt die CI absichtlich fehlschlagen (XPASS strict) – so vergisst niemand, den Fortschritt sichtbar zu machen.
5. **Neue Anforderung?** Erst Story + Kriterium (`US-xx.y`) hier ergänzen, dann Test mit `@pytest.mark.story("US-xx.y")`, dann Code.

Die Tests liegen bei den jeweiligen Teilen: `frontend/tests/` (US-01, 02, 03, 06, 09, 10) und künftig `backend/tests/` (US-04, 05, 07, 08, 12, 14). Status und Ergebnisse pflegen wir in der Backlog-Excel (Projektablage).

## Übersicht

| Story | Titel | Epic | PSP | Verantw. | Prio |
|---|---|---|---|---|---|
| [US-01](US-01-artefakt-per-formular-erfassen.md) | Artefakt per Formular erfassen | E1 Artefakt erfassen | 6.1 | DB | Must |
| [US-02](US-02-fehler-im-artefakt-frueh-erkennen.md) | Fehler im Artefakt früh erkennen | E1 Artefakt erfassen | 3.3 | DB | Must |
| [US-03](US-03-firmenbranding-hinterlegen.md) | Firmenbranding hinterlegen | E1 Artefakt erfassen | 6.2 | DB | Should |
| [US-04](US-04-datenstruktur-automatisch-auslesen.md) | Datenstruktur automatisch auslesen | E2 Agenten-Pipeline | 5.3 | DZ | Must |
| [US-05](US-05-kpi-beschreibung-in-geprueftes-sql-uebersetzen.md) | KPI-Beschreibung in geprüftes SQL übersetzen | E2 Agenten-Pipeline | 5.4 | DZ | Must |
| [US-06](US-06-dashboard-konfiguration-erzeugen.md) | Dashboard-Konfiguration erzeugen | E2 Agenten-Pipeline | 5.5 | DB | Must |
| [US-07](US-07-dokumentation-automatisch-erzeugen.md) | Dokumentation automatisch erzeugen | E2 Agenten-Pipeline | 5.6 | MP | Should |
| [US-08](US-08-ein-befehl-erzeugt-das-vollstaendige-paket.md) | Ein Befehl erzeugt das vollständige Paket | E2 Agenten-Pipeline | 5.2, 5.7 | DZ | Must |
| [US-09](US-09-dashboard-anzeigen.md) | Dashboard anzeigen | E3 Dashboard zur Laufzeit | 6.3 | DB | Must |
| [US-10](US-10-neue-daten-hochladen.md) | Neue Daten hochladen | E3 Dashboard zur Laufzeit | 6.3 | DB | Should |
| [US-11](US-11-betrieb-auf-dem-raspberry-pi.md) | Betrieb auf dem Raspberry Pi | E4 Betrieb | 7.3, 8.4 | DZ | Must |
| [US-12](US-12-generizitaet-zweites-dashboard-ohne-codeaenderung.md) | Generizität: zweites Dashboard ohne Codeänderung | E4 Betrieb | 7.4 | DZ | Must |
| [US-13](US-13-sicheres-deployment.md) | Sicheres Deployment | E4 Betrieb | 7.3, 4.3 | DZ | Should |
| [US-14](US-14-nur-lesender-datenzugriff.md) | Nur lesender Datenzugriff | E5 Sicherheit | 4.6 | DZ | Must |

Kriterien mit `[manuell]` werden im Testprotokoll (AP 8.4) bzw. in der Release-Checkliste nachgewiesen.
