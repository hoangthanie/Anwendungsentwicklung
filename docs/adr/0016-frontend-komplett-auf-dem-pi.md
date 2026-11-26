# ADR 0016: Das gesamte Frontend läuft auf dem Raspberry Pi, die Pipeline mit Sprachmodell nicht

- **Status:** vorgeschlagen (Beschluss im Jour fixe, Ort der Pipeline offen)
- **Datum:** 28.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 6.1, 6.3 (DB); berührt 7.3 und 8.4 (DZ), US-11

## Kontext
ADR 0002 legt fest: Build-Time (Pipeline mit Sprachmodell) auf dem Entwicklungsrechner, Runtime auf dem Raspberry Pi. Zuerst gingen wir davon aus, dass nur der Runner auf dem Pi läuft und das Eingabeformular auf einem anderen Rechner. Dominik will beide Oberflächen auf dem Pi, aus dem Netzwerk von jedem Rechner im Browser erreichbar. Zielgerät ist ein **Raspberry Pi 3 mit 1 GB RAM** (zunächst war ein Pi 4 mit 2 GB angenommen). Das Eingabeformular ruft kein Sprachmodell auf; es prüft und speichert nur `artefakt.yaml` und das Logo.

## Betrachtete Alternativen
| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: nur der Runner auf dem Pi, Formular auf dem Entwicklungsrechner | Pi sehr leicht | Formular nur an einem Rechner, Anwender müssen Artefakte zum Pi kopieren |
| **B: Runner und Eingabeformular auf dem Pi** | eine Adresse für alles, Artefakte liegen direkt auf dem Pi, vom Netzwerk erreichbar | Pi trägt zwei Streamlit-Prozesse |
| C: auch die Pipeline mit Qwen3 auf dem Pi | alles an einem Ort | `qwen3:8b` passt nicht in 1 GB RAM, Modell zu langsam |

## Entscheidung
Wir wählen **B**. Eingabeformular (Port 8502) und Dashboard-Runner (Port 8501) laufen auf dem Pi und sind aus dem Netzwerk erreichbar. Das Sprachmodell und die Pipeline-Schritte 1 bis 4 laufen **nicht** auf dem Pi.

## Konsequenzen
- **Gemessen auf dem echten Pi 3** (28.10.2026): beide Apps zusammen etwa 350 MB (Runner 178 MB, Eingabeformular 170 MB), 528 MiB verfügbar, Swap 904 MiB kaum genutzt. Erster Seitenaufruf: Dashboard etwa 6 bis 7 Sekunden, Eingabeformular etwa 5 Sekunden. Für den Projektzweck ausreichend. Ein Pi 3A+ (512 MB) würde nicht reichen.
- **Offener Punkt:** Aus Artefakt und CSV macht erst Davids Pipeline mit dem Modell die `dashboard.json`. Optionen, mit David abzustimmen: (a) Pipeline läuft auf einem stärkeren Rechner im Netz und liest/schreibt die Pi-Ordner (Freigabe oder `rsync`), (b) Ollama auf einem anderen Rechner im Netz, Pipeline ruft es per Netzwerk auf, (c) ein kleineres Modell direkt auf dem Pi (Spike PSP 5.1). Bis dahin bauen wir Dashboards mit `tools/baue_lokal.py` und kopieren sie auf den Pi.
- Ein Container zeigt genau ein Dashboard. Mehrere Dashboards bräuchten mehrere Container und Ports.
- Ergänzt ADR 0002 und ADR 0003, ersetzt sie nicht.
- US-11 (Betrieb auf dem Pi) liegt bei David (PSP 7.3, 8.4). Wir haben die Pi-Seite des Frontends vorweggenommen; die Release-Checkliste und das Testprotokoll (US-11.1 Neustart in höchstens 2 Minuten, US-11.2 Erreichbarkeit im Tailnet) sind noch nicht durchgeführt. Tailscale ist auf dem Pi eingerichtet, ein formaler Test fehlt.

## Belege
- `raspberry-pi/README.md`
- Messung auf dem Pi (`free -h`, `ps`), Ladezeiten vom 28.10.2026
