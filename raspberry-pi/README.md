# Raspberry-Pi-Betrieb (Planung)

**Stand:** 2026-10-27 · **Status:** Dateien geschrieben, **noch nicht auf einem Pi getestet** (auf dem Entwicklungsrechner ist kein Docker installiert).

## Zielbild
Der Pi zeigt nur an. Erzeugen (Eingabeformular, Pipeline, Ollama/Qwen3) passiert auf einem PC; der Pi bekommt den **Ausgabeordner** (`dashboard.json`, `daten.db`, `logo.png`).

| Rolle | Wo | Warum |
|---|---|---|
| Erzeugen | PC/Laptop | Das Modell braucht deutlich mehr RAM, als ein Pi 4 mit 2 GB hat |
| Anzeigen (Runner, Upload) | Raspberry Pi 4 (2 GB) | Der Runner braucht kein LLM, nur Streamlit, pandas, Plotly |

## Bausteine (Ordner `raspberry-pi/`, neben `frontend/`)
- `setup-pi.sh`: Ein-Befehl-Einrichtung (siehe unten).
- `docker/`: alles fuer den Container (Build-Kontext ist die Repo-Wurzel, weil der Runner-Code in `frontend/` liegt).
- `docker/Dockerfile`: schlankes Image (`python:3.12-slim`, arm64), nur Runner-Abhaengigkeiten (`requirements-runner.txt`, ohne pytest), Prozess als Nutzer `runner` (kein Root), Healthcheck.
- `docker/docker-compose.yml`: Neustart automatisch, Datenordner `/srv/dashboards/aktuell` wird nach `/daten` eingehaengt, **700 MB Speichergrenze** (2-GB-Pi), Dateisystem schreibgeschuetzt ausser `/tmp` und dem Datenordner.
- `docker/Dockerfile.dockerignore`: haelt Daten, Artefakte und Firmenlogos aus dem Image.

## Warum diese Entscheidungen
- **Docker trotz 2 GB:** Der Dienst selbst kostet wenig; die Speichergrenze verhindert, dass ein Fehler den Pi ausbremst. Wenn es zu eng wird, ist die Alternative ein venv plus `systemd`-Dienst (gleicher Befehl wie im `CMD`).
- **Daten als Volume, nicht im Image:** Upload-Anhaengen schreibt in `daten.db`; das muss einen Neustart ueberleben und darf keine Firmendaten ins Image bringen.
- **Nur LAN, spaeter Tailscale:** Port 8501 ist im Heimnetz erreichbar. Mit Tailscale kann man den Port spaeter an das Tailscale-Interface binden (`100.x.y.z:8501:8501`), dann ist nichts im Internet offen. Streamlit hat keine eigene Anmeldung; Tailscale uebernimmt die Zugriffskontrolle.

## Automatische Einrichtung (empfohlen)
1. Mit dem **Raspberry Pi Imager** "Raspberry Pi OS Lite (64-bit)" auf die SD-Karte schreiben. Im Imager unter *Einstellungen bearbeiten*: Hostname (z. B. `dashboard-pi`), Benutzer und Passwort, WLAN, **SSH aktivieren**, Zeitzone. Das ist die offizielle Stelle fuer die Grundeinstellungen.
2. Pi starten, per SSH anmelden und **einen** Befehl ausfuehren (`setup-pi.sh`, Aufruf steht im Skriptkopf). Es installiert Docker, holt den Code nach `/opt/dashboard-framework`, legt `/srv/dashboards/aktuell` an (beim ersten Mal mit dem synthetischen Sales-Beispiel) und startet den Runner. Danach laeuft er nach jedem Neustart von selbst.
3. Ein zweiter Lauf desselben Befehls aktualisiert den Code und startet neu; Daten bleiben erhalten.

Warum nicht komplett ohne SSH? Der Imager kann Hostname, WLAN und SSH vorbelegen, aber keine eigenen Skripte ausfuehren. Ein Skript beim ersten Start waere ueber `cloud-init` oder eine `firstrun`-Datei auf der Boot-Partition moeglich, das haengt von der Pi-OS-Version ab und ist fragil. Ein SSH-Befehl ist robuster. Voraussetzung: Das Repository ist fuer den Pi lesbar (oeffentlich oder per Zugangstoken in `REPO_URL`).

## Einrichtung von Hand (Kurzfassung)
1. Raspberry Pi OS Lite 64-bit, SSH an, `curl -fsSL https://get.docker.com | sh`, Nutzer in Gruppe `docker`.
2. Repo klonen (`frontend/`), Ausgabeordner nach `/srv/dashboards/aktuell` kopieren (z. B. `scp -r ausgabe/<name>/* pi@<ip>:/srv/dashboards/aktuell/`). Ordner dem Nutzer mit UID 1000 geben: `sudo chown -R 1000 /srv/dashboards`.
3. `docker compose -f raspberry-pi/docker/docker-compose.yml up -d --build` (im Repo-Hauptordner) (erster Build auf dem Pi dauert einige Minuten).
4. Browser: `http://<pi-ip>:8501`.

## Noch zu pruefen (auf dem Pi)
- Baut das Image auf arm64 ohne Compiler (Wheels fuer pandas/Pillow vorhanden)?
- Speicherbedarf und Antwortzeit mit dem Beispiel (Ziel: fluessig).
- Gibt es nach `read_only: true` Fehler beim Schreiben (Streamlit-Cache)? Falls ja, weiteres `tmpfs` ergaenzen.
- Mehrere Dashboards: derzeit ein Ordner = ein Dashboard. Mehrere brauchen mehrere Container/Ports.
- Abstimmung mit Stephanie (CI/Docker), damit nicht doppelt gebaut wird.
