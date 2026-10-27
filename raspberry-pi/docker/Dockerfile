# Frontend-Image fuer den Raspberry Pi (arm64): enthaelt Runner UND Eingabeformular, kein LLM.
# Standard-Start ist der Runner; das Eingabeformular startet docker-compose.yml mit eigenem Befehl.
# Bauen im Repo-Wurzelordner:  docker build -f raspberry-pi/docker/Dockerfile -t dashboard-runner .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app
# Abhaengigkeiten zuerst: bleibt beim Code-Aenderungen im Docker-Cache
COPY raspberry-pi/docker/requirements-runner.txt .
RUN pip install -r requirements-runner.txt

COPY frontend/pyproject.toml ./
COPY frontend/src ./src
COPY frontend/.streamlit ./.streamlit
RUN pip install --no-deps .

# Kein Root: der Prozess bekommt nur Schreibrechte auf den Datenordner
RUN useradd --create-home --uid 1000 runner && mkdir -p /daten && chown runner /daten
USER runner

ENV DASHBOARD_CONFIG=/daten/dashboard.json
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8501/_stcore/health', timeout=4)"

CMD ["streamlit", "run", "src/dashboard_framework/runner/app.py", \
     "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
