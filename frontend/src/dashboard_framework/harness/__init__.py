"""Pipeline-Schritt 3 (PSP 5.5, Dominik): Dashboard-Konfiguration.

Die übrigen Pipeline-Schritte (1, 2, 4), `harness/llm.py` und `run.py` liegen nicht hier, sondern im Ordner `backend/` (Paket `pipeline`, David, PSP 5.2 bis 5.7).
Die Klasse in `llm.py` hält sich an das `LLMProtokoll` aus `dashboard.py` (`antworte(prompt, schritt, json_schema)`); Schritt 3 kann sie deshalb direkt nutzen.
"""
