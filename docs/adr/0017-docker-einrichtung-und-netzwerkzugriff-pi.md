# ADR 0017: Docker (zwei Container, ein Image), Einrichtung per Skript, Zugriff über LAN und Tailscale

- **Status:** vorgeschlagen (Beschluss im Jour fixe)
- **Datum:** 28.10.2026 · **Vorgeschlagen von:** DB · **PSP:** 7.3, 8.4 (DZ) berührt; Vorschlag von DB, Abstimmung mit DZ und SJ nötig · **Stories:** US-11, US-13

## Kontext
Der Pi 3 mit 1 GB RAM soll beide Oberflächen (ADR 0016) dauerhaft betreiben, sich nach einem Neustart selbst starten und aus dem Netzwerk erreichbar sein. Neue Einrichtungen sollen ohne Handarbeit gelingen. Die Stories US-11 und US-13 (DZ, PSP 7.3) sehen als Schnittstelle `deploy/systemd/dashboard@.service` und `deploy/deploy.sh` vor, dazu Backup, Healthcheck und Rollback. Streamlit hat keine eigene Anmeldung.

## Betrachtete Alternativen
**Betrieb:**

| Alternative | Vorteile | Nachteile |
|---|---|---|
| A: virtuelle Umgebung plus `systemd`-Dienst (so im Testkonzept der Stories vorgesehen) | weniger Speicher, kein Docker | Abhängigkeiten und Versionen je Rechner, kein sauberes Zurücksetzen |
| **B: Docker, ein Image, zwei Container** (`runner`, `eingabe`) | identischer Stand für alle, Neustart automatisch, Dateisystem schreibgeschützt, Datenordner als Volume | mehr Speicher (Docker-Dienst), Erst-Build auf dem Pi lang |

**Einrichtung:** (A) Schritte von Hand, (B) ein wiederholbares Skript `setup-pi.sh` auf frischem Raspberry Pi OS Lite.

**Zugriff:** (A) nur LAN, (B) LAN und Tailscale, keine Anmeldung, (C) zusätzlich Reverse Proxy mit Anmeldung (später möglich).

## Entscheidung
Wir wählen **Docker mit zwei Containern aus einem Image** (`raspberry-pi/docker/`), das Skript **`setup-pi.sh`** (installiert Docker, holt den Code, setzt 1 GB Swap, legt `/srv/dashboards/aktuell` und `/srv/dashboards/artefakte` an, startet beide Container, wiederholbar) und den Zugriff **über das LAN-Kabel, WLAN abgeschaltet, dazu Tailscale**. Die Container laufen ohne Root mit schreibgeschütztem Dateisystem (nur `/tmp` und die Datenordner beschreibbar), `no-new-privileges` und Neustart `unless-stopped`. Im Router wird die Adresse des Pi fest reserviert.

## Konsequenzen
- **Gemessen:** Der Erst-Build dauerte auf dem Pi 3 rund 19 Minuten. Das Skript lief nach einem Fix (Pillow für die Demo-Daten) durch.
- Die Speichergrenze je Container (300 MB) wird vom Pi-Kernel derzeit verworfen (kein Memory-Cgroup), `docker stats` zeigt `0B / 0B`. Abhilfe: Kernel-Parameter `cgroup_enable=memory cgroup_memory=1` in `/boot/firmware/cmdline.txt`, noch nicht ins Skript übernommen.
- Das Skript holt den Code von GitHub; das Repository muss für den Pi lesbar sein.
- **Keine Anmeldung:** Wer das Netzwerk (LAN oder Tailscale) erreicht, kann Dashboard und Eingabeformular nutzen. Das Formular legt Artefakte an. Die Freigabe im Tailscale-Netz ist klein zu halten. Möglicher späterer Schritt: Ports nur an die Tailscale-Adresse binden oder einen Reverse Proxy mit Anmeldung (Caddy) davorsetzen.
- Eine Optimierung der Ladezeit (z. B. `--server.fileWatcherType=none`) ist nicht nötig, aber vorbereitet.
- **Nicht abgedeckt, Sache von David (PSP 7.3):** Backup der Datenbank vor einem Update, Healthcheck mit Rollback auf das vorherige Image-Tag, Release-Workflow (US-13). Das Skript `setup-pi.sh` aktualisiert den Code bei einem zweiten Lauf, sichert aber keine Daten außerhalb des Volumes und kennt kein Rollback. Der Neustart nach höchstens 2 Minuten (US-11.1) ist noch nicht gemessen.
- **Abstimmung nötig:** Wenn David das Deployment anders plant (`systemd`, `deploy.sh`, `release.yml`), ersetzt oder ergänzt sein Entwurf diese ADR. Auch mit Stephanie (CI/Docker) klären, damit nicht doppelt gebaut wird.

## Belege
- `raspberry-pi/README.md`, `raspberry-pi/setup-pi.sh`, `raspberry-pi/docker/`
- Testlauf auf dem Pi 3 am 28.10.2026
