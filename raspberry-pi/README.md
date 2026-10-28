# Raspberry-Pi-Betrieb (Planung)

**Stand:** 2026-10-27 · **Status:** Dateien geschrieben, **noch nicht auf einem Pi getestet** (auf dem Entwicklungsrechner ist kein Docker installiert).

## Hardware: Raspberry Pi 3 (1 GB RAM)
Das Zielgeraet ist ein Pi 3 (Modell B/B+, 1 GB). Das reicht fuer Runner und Eingabeformular, ist aber eng: je Container 300 MB Grenze, dazu 1 GB Auslagerungsspeicher (setzt `setup-pi.sh`), der Erst-Build dauert 15-30 Minuten, und die Seiten laden langsamer als auf einem Pi 4. Ein Pi 3A+ (512 MB) reicht nicht. Pruefen mit `free -h` (Zeile Mem: ca. 900 MB). Fuer das Dauerbetrieb-Ziel ist eine hochwertige SD-Karte wichtig (Swap beansprucht sie).

## Erster Test auf dem echten Pi (2026-10-28)
Pi 3 (905 MiB RAM), Raspberry Pi OS Lite 64-bit auf Debian 13 "trixie", Docker 29.
- `setup-pi.sh` lief durch (erster Lauf scheiterte an fehlendem Pillow fuer die Demo-Daten, danach behoben). **Der Erst-Build dauerte etwa 19 Minuten** (pip install ca. 7 Minuten, Image-Export ca. 10 Minuten).
- Beide Container starten, Adressen `:8501` und `:8502` werden ausgegeben.
- **Speicher:** `free -h` zeigt 376 MiB belegt, 528 MiB verfuegbar, Swap 904 MiB (kaum genutzt). Je Streamlit-Prozess etwa 170-180 MB (`ps`), zusammen rund 350 MB.
- **Speichergrenze:** Docker meldet "kernel does not support memory limit"; `docker stats` zeigt deshalb `0B / 0B`. Abhilfe: in `/boot/firmware/cmdline.txt` am Zeilenende `cgroup_enable=memory cgroup_memory=1` anhaengen und neu starten. Noch nicht eingebaut ins Skript.
- **Ladezeit im Browser (Erstaufruf):** Dashboard ca. 6-7 s, Eingabeformular ca. 5 s. Fuer den Projektzweck ausreichend, keine Optimierung noetig. Moegliche spaetere Stellschraube: `--server.fileWatcherType=none` (ungemessen).
- Noch offen: Speichern eines Artefakts ueber das Formular (`/srv/dashboards/artefakte`).

## Zielbild
Das **gesamte Frontend laeuft auf dem Pi**: Eingabeformular (Port 8502) und Dashboard-Runner (Port 8501). Beide sind von jedem Rechner im Netz im Browser erreichbar (`http://<pi>:8501` bzw. `:8502`). Nur das Sprachmodell (Ollama/Qwen3) laeuft nicht auf dem Pi.

| Rolle | Wo | Warum |
|---|---|---|
| Artefakt anlegen (Eingabeformular) | Raspberry Pi 3 (1 GB) | Das Formular ruft kein Modell auf, es prueft und speichert nur `artefakt.yaml` und Logo |
| Anzeigen (Runner, Upload) | Raspberry Pi 3 (1 GB) | Der Runner braucht kein LLM, nur Streamlit, pandas, Plotly |
| Pipeline mit Sprachmodell (Davids Schritte 1-4) | noch offen | Das Modell braucht deutlich mehr RAM, als ein Pi 3 mit 1 GB hat; siehe "Offener Punkt Pipeline" |

## Bausteine (Ordner `raspberry-pi/`, neben `frontend/`)
- `setup-pi.sh`: Ein-Befehl-Einrichtung (siehe unten).
- `docker/`: alles fuer den Container (Build-Kontext ist die Repo-Wurzel, weil der Runner-Code in `frontend/` liegt).
- `docker/Dockerfile`: ein schlankes Image (`python:3.12-slim`, arm64) fuer beide Apps, nur Frontend-Abhaengigkeiten (`requirements-runner.txt`, ohne pytest), Prozess als Nutzer `runner` (kein Root), Healthcheck.
- `docker/docker-compose.yml`: **zwei Container aus einem Image** (`runner` Port 8501, `eingabe` Port 8502), je 300 MB Speichergrenze, zwei Datenordner: `/srv/dashboards/aktuell` (fertiges Dashboard) und `/srv/dashboards/artefakte` (vom Formular gespeicherte Artefakte). Weitere Punkte: Neustart automatisch, Dateisystem schreibgeschuetzt ausser `/tmp` und den Datenordnern.
- `docker/Dockerfile.dockerignore`: haelt Daten, Artefakte und Firmenlogos aus dem Image.

## Warum diese Entscheidungen
- **Docker trotz 1 GB:** Der Dienst selbst kostet wenig; die Speichergrenze verhindert, dass ein Fehler den Pi ausbremst. Wenn es zu eng wird, ist die Alternative ein venv plus `systemd`-Dienst (gleicher Befehl wie im `CMD`).
- **Daten als Volume, nicht im Image:** Upload-Anhaengen schreibt in `daten.db`; das muss einen Neustart ueberleben und darf keine Firmendaten ins Image bringen.
- **Nur LAN, spaeter Tailscale:** Die Ports 8501 und 8502 sind im Heimnetz erreichbar. Mit Tailscale kann man den Port spaeter an das Tailscale-Interface binden (`100.x.y.z:8501:8501`, `100.x.y.z:8502:8502`), dann ist nichts im Internet offen. Streamlit hat keine eigene Anmeldung; Tailscale uebernimmt die Zugriffskontrolle.

## Automatische Einrichtung (empfohlen)
1. Mit dem **Raspberry Pi Imager** "Raspberry Pi OS Lite (64-bit)" auf die SD-Karte schreiben. Im Imager unter *Einstellungen bearbeiten*: Hostname (z. B. `dashboard-pi`), Benutzer und Passwort, WLAN, **SSH aktivieren**, Zeitzone. Das ist die offizielle Stelle fuer die Grundeinstellungen.
2. Pi starten, per SSH anmelden und **einen** Befehl ausfuehren (`setup-pi.sh`, Aufruf steht im Skriptkopf). Es installiert Docker, holt den Code nach `/opt/dashboard-framework`, legt `/srv/dashboards/aktuell` an (beim ersten Mal mit dem synthetischen Sales-Beispiel) und startet Runner und Eingabeformular. Danach laeuft er nach jedem Neustart von selbst.
3. Ein zweiter Lauf desselben Befehls aktualisiert den Code und startet neu; Daten bleiben erhalten.

Warum nicht komplett ohne SSH? Der Imager kann Hostname, WLAN und SSH vorbelegen, aber keine eigenen Skripte ausfuehren. Ein Skript beim ersten Start waere ueber `cloud-init` oder eine `firstrun`-Datei auf der Boot-Partition moeglich, das haengt von der Pi-OS-Version ab und ist fragil. Ein SSH-Befehl ist robuster. Voraussetzung: Das Repository ist fuer den Pi lesbar (oeffentlich oder per Zugangstoken in `REPO_URL`).

## Einrichtung von Hand (Kurzfassung)
1. Raspberry Pi OS Lite 64-bit, SSH an, `curl -fsSL https://get.docker.com | sh`, Nutzer in Gruppe `docker`.
2. Repo klonen (`frontend/`), Ausgabeordner nach `/srv/dashboards/aktuell` kopieren (z. B. `scp -r ausgabe/<name>/* pi@<ip>:/srv/dashboards/aktuell/`). Ordner dem Nutzer mit UID 1000 geben: `sudo chown -R 1000 /srv/dashboards`.
3. `docker compose -f raspberry-pi/docker/docker-compose.yml up -d --build` (im Repo-Hauptordner) (erster Build auf dem Pi dauert einige Minuten).
4. Browser (auch von jedem Rechner im Netz): Dashboard `http://<pi-ip>:8501`, Eingabeformular `http://<pi-ip>:8502`.

## Offener Punkt Pipeline
Das Formular legt das Artefakt auf dem Pi ab. Aus Artefakt + CSV macht erst die Pipeline (Schritte 1-4, Sprachmodell) das `dashboard.json`. Das Modell passt nicht auf einen Pi 3 mit 1 GB. Optionen, mit David abzustimmen: (a) Pipeline laeuft auf einem staerkeren Rechner im Netz und liest/schreibt die Pi-Ordner (Freigabe oder `rsync`), (b) Ollama auf einem anderen Rechner im Netz, Pipeline auf dem Pi ruft es per Netzwerk auf (`OLLAMA_HOST`), (c) kleineres Modell direkt auf dem Pi (Spike PSP 5.1 klaeren). Bis dahin: Dashboards wie bisher mit `tools/baue_lokal.py` bauen und nach `/srv/dashboards/aktuell` kopieren.

## Noch zu pruefen (auf dem Pi)
- Baut das Image auf arm64 ohne Compiler (Wheels fuer pandas/Pillow vorhanden)?
- Speicherbedarf und Antwortzeit mit dem Beispiel (Ziel: fluessig).
- Gibt es nach `read_only: true` Fehler beim Schreiben (Streamlit-Cache)? Falls ja, weiteres `tmpfs` ergaenzen.
- Mehrere Dashboards: derzeit ein Ordner = ein Dashboard. Mehrere brauchen mehrere Container/Ports.
- Abstimmung mit Stephanie (CI/Docker), damit nicht doppelt gebaut wird.
