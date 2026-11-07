"""Zugriff auf das lokale Sprachmodell über Ollama (PSP 5.2).

Noch nicht umgesetzt. Schritt 3 (frontend/src/dashboard_framework/harness/dashboard.py) erwartet
eine Klasse mit dieser Methode (LLMProtokoll):

    def antworte(self, prompt: str, schritt: str, json_schema: dict | None = None) -> str: ...

Geplant: Format erzwingen (JSON-Schema über Ollama), Wiederholung bei Parse-Fehlern,
Protokoll je Aufruf in runs/metrics.jsonl (Tokens, Laufzeit, Modell, Schritt).
"""
