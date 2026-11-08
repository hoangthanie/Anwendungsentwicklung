"""Vergleich: dieselben 3 Aufgaben über OpenCode statt direkt über Ollama (Referenz: qwen3:8b mit Denken).

Aufgaben, Anweisung und Prüfung kommen unverändert aus messung_modellwahl.py.
Tokens aus `opencode run --format json` (Summe über alle step_finish), Laufzeit = Gesamtdauer des Aufrufs.
Vor jedem Aufruf wird das Modell entladen: sonst zählt Ollama nur den nicht zwischengespeicherten Teil
des Prompts. Die Laufzeit enthält deshalb das Laden des Modells.
Ergebnis: backend/runs/opencode.csv (bleibt lokal, siehe .gitignore).

Aufruf (aus dem Ordner backend, venv aktiv):
    python tools/messung_opencode.py
"""

import csv
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import urllib.request

from messung_modellwahl import AUFGABEN, OLLAMA_URL, SYSTEM, pruefe

OPENCODE = os.environ.get(
    "OPENCODE_EXE",
    r"C:\Users\Administrator\AppData\Local\Programs\ai.opencode.desktop\resources\opencode-cli.exe",
)
MODELL = "ollama/qwen3:8b"
ARBEITSORDNER = Path(r"C:\Temp\opencode-messung")  # leer, außerhalb des Repos
ZIEL = Path(__file__).resolve().parent.parent / "runs" / "opencode.csv"


def entlade_modell() -> None:
    """Modell aus dem Speicher nehmen, damit Ollama den ganzen Prompt neu verarbeitet und zählt."""
    nutzlast = {"model": MODELL.split("/", 1)[1], "keep_alive": 0}
    anfrage = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(nutzlast).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(anfrage, timeout=60) as antwort:
        antwort.read()


def frage_opencode(frage: str) -> tuple[list[dict], float]:
    nachricht = f"{SYSTEM}\n\nFrage: {frage}"
    start = time.perf_counter()
    lauf = subprocess.run(
        [OPENCODE, "run", "--format", "json", "--title", "messung", "-m", MODELL, nachricht],
        cwd=ARBEITSORDNER,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    dauer = time.perf_counter() - start
    ereignisse = [json.loads(z.lstrip("\ufeff")) for z in lauf.stdout.splitlines() if z.strip()]
    if not ereignisse:
        raise RuntimeError(f"keine Ausgabe, Rückgabecode {lauf.returncode}: {lauf.stderr[:200]}")
    return ereignisse, dauer


def lies_json(text: str) -> dict:
    """OpenCode erzwingt kein Format: erstes {...} aus dem Antworttext nehmen."""
    return json.loads(text[text.index("{"): text.rindex("}") + 1])


def main() -> None:
    ARBEITSORDNER.mkdir(parents=True, exist_ok=True)
    ZIEL.parent.mkdir(exist_ok=True)
    spalten = [
        "zeit", "modell", "aufgabe", "richtig", "eingabe_tokens", "ausgabe_tokens",
        "laufzeit_s", "schritte", "antwort", "fehler",
    ]
    with ZIEL.open("w", newline="", encoding="utf-8") as datei:
        schreiber = csv.DictWriter(datei, fieldnames=spalten, delimiter=";")
        schreiber.writeheader()
        for name, frage, referenz in AUFGABEN:
            zeile = {"zeit": datetime.now().isoformat(timespec="seconds"), "modell": MODELL, "aufgabe": name}
            try:
                entlade_modell()
                ereignisse, dauer = frage_opencode(frage)
                schritte = [e["part"] for e in ereignisse if e.get("type") == "step_finish"]
                text = "".join(e["part"].get("text", "") for e in ereignisse if e.get("type") == "text")
                try:
                    richtig = pruefe(lies_json(text), referenz)
                except ValueError:  # kein JSON im Text (JSONDecodeError ist ein ValueError)
                    richtig = False
                zeile.update(
                    richtig="ja" if richtig else "nein",
                    eingabe_tokens=sum(s["tokens"]["input"] for s in schritte),
                    ausgabe_tokens=sum(s["tokens"]["output"] for s in schritte),
                    laufzeit_s=round(dauer, 2),
                    schritte=len(schritte),
                    antwort=text.replace("\n", " ")[:300],
                )
            except Exception as fehler:  # ein Fehler stoppt nicht den ganzen Lauf
                zeile.update(richtig="nein", fehler=str(fehler)[:300])
            schreiber.writerow(zeile)
            datei.flush()
            print(f"{MODELL:<18} {name:<12} richtig={zeile['richtig']} tokens={zeile.get('eingabe_tokens', '-')}")
    print(f"Fertig -> {ZIEL}")


if __name__ == "__main__":
    main()
