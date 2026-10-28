#!/usr/bin/env bash
# Richtet einen frischen Raspberry Pi (Raspberry Pi OS Lite, 64-bit) komplett fuer das Frontend ein:
# Dashboard-Runner (Port 8501) und Eingabeformular (Port 8502), beide aus dem Netz erreichbar.
# Aufruf auf dem Pi (einmal):
#   curl -fsSL https://raw.githubusercontent.com/hoangthanie/Anwendungsentwicklung/main/raspberry-pi/setup-pi.sh | sudo bash
# Das Skript ist wiederholbar: ein zweiter Lauf aktualisiert den Code und startet neu, loescht aber keine Daten.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/hoangthanie/Anwendungsentwicklung.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="/opt/dashboard-framework"
DATEN_DIR="/srv/dashboards/aktuell"
ARTEFAKT_DIR="/srv/dashboards/artefakte"

[ "$(id -u)" -eq 0 ] || { echo "Bitte mit sudo ausfuehren."; exit 1; }

echo "==> 1/5 Pakete (git, python3 fuer die Demo-Daten)"
apt-get update -qq
apt-get install -y -qq git python3 curl ca-certificates

echo "==> Auslagerungsspeicher auf 1 GB (Pi mit 1 GB RAM: Docker-Build und zwei Apps brauchen Reserve)"
if [ -f /etc/dphys-swapfile ] && ! grep -q '^CONF_SWAPSIZE=1024' /etc/dphys-swapfile; then
  sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
  dphys-swapfile swapoff || true
  dphys-swapfile setup && dphys-swapfile swapon
fi

echo "==> 2/5 Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

echo "==> 3/5 Code holen nach ${APP_DIR}"
if [ -d "${APP_DIR}/.git" ]; then
  git -C "${APP_DIR}" fetch --depth 1 origin "${BRANCH}" && git -C "${APP_DIR}" reset --hard "origin/${BRANCH}"
else
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
fi

echo "==> 4/5 Datenordner ${DATEN_DIR}"
mkdir -p "${DATEN_DIR}" "${ARTEFAKT_DIR}"
if [ ! -f "${DATEN_DIR}/dashboard.json" ]; then
  # Erster Start: synthetisches Beispiel, damit der Runner sofort etwas zeigt. Eigene Dashboards einfach darueber kopieren.
  python3 "${APP_DIR}/frontend/examples/sales/make_demo_db.py"
  cp "${APP_DIR}/frontend/examples/sales/dashboard.json" "${APP_DIR}/frontend/examples/sales/daten.db" \
     "${APP_DIR}/frontend/examples/sales/logo.png" "${DATEN_DIR}/"
fi
chown -R 1000:1000 /srv/dashboards   # UID des Container-Nutzers "runner"

echo "==> 5/5 Runner und Eingabeformular starten (Neustart nach Reboot automatisch)"
docker compose -f "${APP_DIR}/raspberry-pi/docker/docker-compose.yml" up -d --build

IP="$(hostname -I | awk '{print $1}')"
echo "Fertig. Dashboard: http://${IP}:8501   Eingabeformular: http://${IP}:8502"
