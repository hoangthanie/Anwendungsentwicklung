"""Zugriff auf das lokale Sprachmodell über Ollama: die Mini-Harness aus ADR 0004 (PSP 5.2).

Die Klasse LLM erfüllt das LLMProtokoll aus Schritt 3
(frontend/src/dashboard_framework/harness/dashboard.py): antworte(prompt, schritt, json_schema) -> str.

Was die Klasse tut, und nur das:
- ein Ollama-Aufruf je Anfrage, der Prompt ist die einzige Nachricht (kein eigener Systemprompt),
- Format per JSON-Schema erzwingen, wenn eines übergeben wird,
- Denkmodus ausdrücklich aus (think=False) und feste Ausgabegrenze (ADR 0006),
- optionaler Fallback: Ist die Antwort abgeschnitten oder kein gültiges JSON, einmal beim Fallback-Modell nachfragen,
- je Aufruf eine Zeile im Run-Protokoll runs/metrics.jsonl (US-08.3).

Ob der INHALT einer Antwort stimmt, prüft der jeweilige Schritt selbst und fragt bei Bedarf erneut nach.
Deshalb gibt es hier keine eigene Wiederholung.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path

import httpx
import ollama
from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[3]
STANDARD_PROTOKOLL = BACKEND / "runs" / "metrics.jsonl"
STANDARD_URL = "http://localhost:11434"

# Feste Werte aus der Messung (ADR 0006): Kontext 12.288 Tokens, Ausgabegrenze 4.096 Tokens.
# temperature 0: gleiche Eingabe ergibt (praktisch) dieselbe Antwort, die Ergebnisse sind nachvollziehbar (ADR 0008).
OPTIONEN = {"num_ctx": 12288, "num_predict": 4096, "temperature": 0}
TIMEOUT_S = 300  # hängt Ollama, bricht der Aufruf nach dieser Zeit ab, statt die Pipeline endlos warten zu lassen


class LLMFehler(RuntimeError):
    """Das Sprachmodell konnte nicht aufgerufen werden (z. B. Ollama läuft nicht oder Modell fehlt)."""


class LLM:
    """Mini-Harness für alle Pipeline-Schritte.

    Ohne Angaben kommen Modell, Fallback-Modell und Adresse aus backend/.env (MODELL, FALLBACK_MODELL, OLLAMA_URL).
    Ein leeres FALLBACK_MODELL schaltet den Fallback ab. client und protokoll lassen sich für Tests ersetzen.
    """

    def __init__(
        self,
        modell: str | None = None,
        fallback_modell: str | None = None,
        url: str | None = None,
        protokoll: str | Path = STANDARD_PROTOKOLL,
        client: object | None = None,
    ):
        load_dotenv(BACKEND / ".env")
        self.modell = modell or os.environ.get("MODELL", "")
        if not self.modell:
            raise LLMFehler("Kein Modell angegeben: MODELL in backend/.env setzen (siehe .env.example)")
        if fallback_modell is None:
            fallback_modell = os.environ.get("FALLBACK_MODELL", "")
        self.fallback_modell = fallback_modell.strip() or None
        self.protokoll = Path(protokoll)
        self.client = client or ollama.Client(host=url or os.environ.get("OLLAMA_URL", STANDARD_URL), timeout=TIMEOUT_S)

    def antworte(
        self,
        prompt: str,
        schritt: str,
        json_schema: dict | None = None,
        versuch: int = 1,
        modell: str | None = None,
    ) -> str:
        """Gibt den Antworttext des Modells zurück.

        versuch ist optional und landet nur im Run-Protokoll. Schritte mit Reparaturschleife können hier
        die Nummer des Versuchs übergeben; ohne Angabe steht 1 im Protokoll.
        modell ist optional: Ein Schritt kann gezielt ein anderes Modell anfragen, z. B. das Fallback-Modell, wenn das
        Hauptmodell an den Prüfschichten des Schritts gescheitert ist (inhaltlicher Fallback, ADR 0008). Ein solcher
        Aufruf zählt im Protokoll als Fallback und löst selbst keinen weiteren technischen Fallback aus.
        """
        ziel = modell or self.modell
        if ziel != self.modell:
            text, _ = self._rufe(ziel, prompt, schritt, json_schema, versuch, fallback=True)
            return text
        text, brauchbar = self._rufe(self.modell, prompt, schritt, json_schema, versuch, fallback=False)
        if json_schema is not None and not brauchbar and self.fallback_modell and self.fallback_modell != self.modell:
            try:
                text, _ = self._rufe(self.fallback_modell, prompt, schritt, json_schema, versuch, fallback=True)
            except LLMFehler:
                pass  # Fallback nicht verfügbar (z. B. Modell nicht installiert): die erste Antwort bleibt, der Fehler steht im Protokoll
        return text

    def _rufe(self, modell: str, prompt: str, schritt: str, json_schema: dict | None, versuch: int, fallback: bool):
        """Ein einzelner Aufruf. Liefert (Antworttext, brauchbar). brauchbar heißt: nicht abgeschnitten und,
        falls ein Schema verlangt war, gültiges JSON."""
        zeile = {
            "zeit": datetime.now().isoformat(timespec="seconds"),
            "schritt": schritt,
            "versuch": versuch,
            "modell": modell,
            "fallback": fallback,
        }
        start = time.perf_counter()
        try:
            antwort = self.client.chat(
                model=modell,
                messages=[{"role": "user", "content": prompt}],
                format=json_schema,
                think=False,
                options=OPTIONEN,
                stream=False,
            )
        except httpx.TimeoutException:
            self._protokolliere({**zeile, "dauer_s": round(time.perf_counter() - start, 2), "fehler": "Zeitüberschreitung"})
            raise LLMFehler(f"Ollama hat nicht innerhalb von {TIMEOUT_S} Sekunden geantwortet. Hängt Ollama oder ist der Rechner ausgelastet?") from None
        except ConnectionError:
            self._protokolliere({**zeile, "dauer_s": round(time.perf_counter() - start, 2), "fehler": "Ollama nicht erreichbar"})
            raise LLMFehler("Ollama ist nicht erreichbar. Läuft Ollama auf diesem Rechner (OLLAMA_URL in backend/.env)?") from None
        except ollama.ResponseError as fehler:
            self._protokolliere({**zeile, "dauer_s": round(time.perf_counter() - start, 2), "fehler": str(fehler)})
            raise LLMFehler(f"Ollama hat den Aufruf mit Modell '{modell}' abgelehnt: {fehler}") from None

        text = antwort.message.content or ""
        abgeschnitten = antwort.done_reason == "length"
        gueltiges_json = True
        if json_schema is not None:
            try:
                json.loads(text)
            except json.JSONDecodeError:
                gueltiges_json = False
        self._protokolliere({
            **zeile,
            "tokens_in": antwort.prompt_eval_count,
            "tokens_out": antwort.eval_count,
            "dauer_s": round((antwort.total_duration or 0) / 1e9, 2),
            "ladezeit_s": round((antwort.load_duration or 0) / 1e9, 2),
            "grenze_erreicht": abgeschnitten,
            "gueltiges_json": gueltiges_json if json_schema is not None else None,
        })
        return text, not abgeschnitten and gueltiges_json

    def _protokolliere(self, zeile: dict) -> None:
        self.protokoll.parent.mkdir(parents=True, exist_ok=True)
        with self.protokoll.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(zeile, ensure_ascii=False) + "\n")
