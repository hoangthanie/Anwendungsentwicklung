"""Simuliertes Sprachmodell für Tests: keine GPU, keine Wartezeit, reproduzierbar (Repository-Doc Kap. 7)."""
import json


class FakeLLM:
    """Liefert vorbereitete Antworten der Reihe nach und merkt sich jeden Aufruf.

    Eine Antwort ist ein Text (wird unverändert geliefert, auch kaputtes JSON) oder ein dict/list (wird zu JSON).
    Passt zum Aufruf-Muster antworte(prompt, schritt, json_schema) der geplanten Klasse harness/llm.LLM.
    """

    def __init__(self, antworten):
        self.antworten = list(antworten)
        self.aufrufe: list[dict] = []

    def antworte(self, prompt, schritt, json_schema=None):
        self.aufrufe.append({"prompt": prompt, "schritt": schritt, "json_schema": json_schema})
        if not self.antworten:
            raise AssertionError("FakeLLM: keine vorbereitete Antwort mehr (der Code fragt öfter nach als erwartet)")
        antwort = self.antworten.pop(0)
        return antwort if isinstance(antwort, str) else json.dumps(antwort)
