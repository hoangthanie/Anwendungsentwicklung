# 10 – Raspberry-Pi-Betrieb (Planung)

**Stand:** 2026-10-27 · **Status:** Dateien geschrieben, **noch nicht auf einem Pi getestet** (auf dem Entwicklungsrechner ist kein Docker installiert).

## Zielbild
Der Pi zeigt nur an. Erzeugen (Eingabeformular, Pipeline, Ollama/Qwen3) passiert auf einem PC; der Pi bekommt den **Ausgabeordner** (`dashboard.json`, `daten.db`, `logo.png`).

| Rolle | Wo | Warum |
|---|---|---|
| Erzeugen | PC/Laptop | Das Modell braucht deutlich mehr RAM, als ein Pi 4 mit 2 GB hat |
| Anzeigen (Runner, Upload) | Raspberry Pi 4 (2 GB) | Der Runner braucht kein LLM, nur Streamlit, pandas, Plotly |

## Bausteine (Ordner `deploy/`)
- `Dockerfile`: schlankes Image (`python:3.12-slim`, arm64), nur Runner-Abhaengigkeiten (`requirements-runner.txt`, ohne pytest), Prozess als Nutzer `runner` (kein Root), Healthcheck.
- `docker-compose.yml`: Neustart automatisch, Datenordner `/srv/dashboards/aktuell` wird nach `/daten` eingehaengt, **700 MB Speichergrenze** (2-GB-Pi), Dateisystem schreibgeschuetzt ausser `/tmp` und dem Datenordner.
- `.dockerignore`: haelt Daten, Artefakte und Firmenlogos aus dem Image.

## Warum diese Entscheidungen
- **Docker trotz 2 GB:** Der Dienst selbst kostet wenig; die Speichergrenze verhindert, dass ein Fehler den Pi ausbremst. Wenn es zu eng wird, ist die Alternative ein venv plus `systemd`-Dienst (gleicher Befehl wie im `CMD`).
- **Daten als Volume, nicht im Image:** Upload-Anhaengen schreibt in `daten.db`; das muss einen Neustart ueberleben und darf keine Firmendaten ins Image bringen.
- **Nur LAN, spaeter Tailscale:** Port 8501 ist im Heimnetz erreichbar. Mit Tailscale kann man den Port spaeter an das Tailscale-Interface binden (`100.x.y.z:8501:8501`), dann ist nichts im Internet offen. Streamlit hat keine eigene Anmeldung; Tailscale uebernimmt die Zugriffskontrolle.

## Einrichtung auf dem Pi (Kurzfassung)
1. Raspberry Pi OS Lite 64-bit, SSH an, `curl -fsSL https://get.docker.com | sh`, Nutzer in Gruppe `docker`.
2. Repo klonen (`frontend/`), Ausgabeordner nach `/srv/dashboards/aktuell` kopieren (z. B. `scp -r ausgabe/<name>/* pi@<ip>:/srv/dashboards/aktuell/`). Ordner dem Nutzer mit UID 1000 geben: `sudo chown -R 1000 /srv/dashboards`.
3. `docker compose -f deploy/docker-compose.yml up -d --build` (erster Build auf dem Pi dauert einige Minuten).
4. Browser: `http://<pi-ip>:8501`.

## Noch zu pruefen (auf dem Pi)
- Baut das Image auf arm64 ohne Compiler (Wheels fuer pandas/Pillow vorhanden)?
- Speicherbedarf und Antwortzeit mit dem Beispiel (Ziel: fluessig).
- Gibt es nach `read_only: true` Fehler beim Schreiben (Streamlit-Cache)? Falls ja, weiteres `tmpfs` ergaenzen.
- Mehrere Dashboards: derzeit ein Ordner = ein Dashboard. Mehrere brauchen mehrere Container/Ports.
- Abstimmung mit Stephanie (CI/Docker), damit nicht doppelt gebaut wird.
