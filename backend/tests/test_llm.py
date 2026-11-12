"""Tests für die Mini-Harness (PSP 5.2, ADR 0004/0006). Ollama wird durch einen Fake ersetzt: keine GPU, keine Wartezeit."""

import json
from pathlib import Path
from types import SimpleNamespace

import ollama
import pytest
from dashboard_framework.harness.dashboard import erzeuge_config
from dashboard_framework.models.artefakt import Artefakt

from pipeline.harness.llm import LLM, LLMFehler

SCHEMA = {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}


class FakeOllama:
    """Liefert vorbereitete Antworten der Reihe nach und merkt sich jeden Aufruf von chat()."""

    def __init__(self, *antworten):
        self.antworten = list(antworten)
        self.aufrufe: list[dict] = []

    def chat(self, **kwargs):
        self.aufrufe.append(kwargs)
        antwort = self.antworten.pop(0)
        if isinstance(antwort, Exception):
            raise antwort
        return antwort


def antwort(text, done_reason="stop"):
    return SimpleNamespace(
        message=SimpleNamespace(content=text),
        done_reason=done_reason,
        prompt_eval_count=190,
        eval_count=27,
        total_duration=400_000_000,
        load_duration=0,
    )


def zeilen(pfad: Path) -> list[dict]:
    return [json.loads(z) for z in pfad.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def protokoll(tmp_path):
    return tmp_path / "metrics.jsonl"


def test_sendet_schema_ohne_denkmodus_mit_ausgabegrenze(protokoll):
    fake = FakeOllama(antwort('{"sql": "SELECT 1"}'))
    llm = LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=fake)

    assert llm.antworte("Frage", "query", SCHEMA) == '{"sql": "SELECT 1"}'

    aufruf = fake.aufrufe[0]
    assert aufruf["model"] == "qwen3:8b"
    assert aufruf["messages"] == [{"role": "user", "content": "Frage"}]  # kein eigener Systemprompt
    assert aufruf["format"] == SCHEMA
    assert aufruf["think"] is False  # ADR 0006: Denkmodus ausdrücklich aus
    assert aufruf["options"]["num_predict"] == 4096


def test_ohne_schema_kein_format(protokoll):
    fake = FakeOllama(antwort("freier Text"))
    llm = LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=fake)

    assert llm.antworte("Erkläre", "doku") == "freier Text"
    assert fake.aufrufe[0]["format"] is None


def test_jeder_aufruf_wird_protokolliert(protokoll):  # US-08.3
    fake = FakeOllama(antwort('{"sql": "SELECT 1"}'))
    llm = LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=fake)

    llm.antworte("Frage", "query", SCHEMA, versuch=2)

    zeile = zeilen(protokoll)[0]
    assert zeile["schritt"] == "query"
    assert zeile["versuch"] == 2
    assert zeile["modell"] == "qwen3:8b"
    assert zeile["tokens_in"] == 190
    assert zeile["tokens_out"] == 27
    assert zeile["dauer_s"] == 0.4
    assert zeile["fallback"] is False
    assert "zeit" in zeile


@pytest.mark.parametrize("erste", [antwort('{"sql": "SELE', done_reason="length"), antwort("kein JSON")])
def test_fallback_bei_abgeschnittener_oder_ungueltiger_antwort(protokoll, erste):
    fake = FakeOllama(erste, antwort('{"sql": "SELECT 1"}'))
    llm = LLM(modell="qwen3:8b", fallback_modell="qwen3:14b", protokoll=protokoll, client=fake)

    assert llm.antworte("Frage", "query", SCHEMA) == '{"sql": "SELECT 1"}'

    assert [a["model"] for a in fake.aufrufe] == ["qwen3:8b", "qwen3:14b"]
    assert [z["fallback"] for z in zeilen(protokoll)] == [False, True]


def test_hoechstens_ein_fallback(protokoll):
    fake = FakeOllama(antwort("kein JSON"), antwort("auch kein JSON"))
    llm = LLM(modell="qwen3:8b", fallback_modell="qwen3:14b", protokoll=protokoll, client=fake)

    assert llm.antworte("Frage", "query", SCHEMA) == "auch kein JSON"  # der Schritt merkt den Fehler und fragt selbst nach
    assert len(fake.aufrufe) == 2


def test_kein_fallback_wenn_abgeschaltet_oder_ohne_schema(protokoll):
    ohne_fallback = FakeOllama(antwort("kein JSON"))
    LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=ohne_fallback).antworte("Frage", "query", SCHEMA)
    assert len(ohne_fallback.aufrufe) == 1

    ohne_schema = FakeOllama(antwort("freier Text"))
    LLM(modell="qwen3:8b", fallback_modell="qwen3:14b", protokoll=protokoll, client=ohne_schema).antworte("Erkläre", "doku")
    assert len(ohne_schema.aufrufe) == 1


def test_verstaendliche_meldung_wenn_ollama_nicht_laeuft(protokoll):
    fake = FakeOllama(ConnectionError("Failed to connect"))
    llm = LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=fake)

    with pytest.raises(LLMFehler, match="Läuft Ollama"):
        llm.antworte("Frage", "query", SCHEMA)
    assert zeilen(protokoll)[0]["fehler"] == "Ollama nicht erreichbar"


def test_verstaendliche_meldung_wenn_modell_fehlt(protokoll):
    fake = FakeOllama(ollama.ResponseError("model 'qwen3:8b' not found", 404))
    llm = LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=fake)

    with pytest.raises(LLMFehler, match="qwen3:8b"):
        llm.antworte("Frage", "query", SCHEMA)


def test_schritt3_von_dominik_laeuft_mit_dieser_klasse(protokoll):
    """Nachweis für die Schnittstelle: Schritt 3 (frontend, LLMProtokoll) nutzt die echte Klasse LLM ohne Änderung."""
    artefakt = Artefakt.aus_yaml(Path(__file__).resolve().parents[2] / "frontend" / "artefakte" / "sales" / "artefakt.yaml")
    sql_je_kpi = {kpi.name: "SELECT 1 AS wert" for kpi in artefakt.kpis}
    wahl = {"charts": [{"kpi": kpi.name, "typ": "kennzahl"} for kpi in artefakt.kpis]}
    fake = FakeOllama(antwort(json.dumps(wahl)))
    llm = LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=fake)

    config = erzeuge_config(artefakt, sql_je_kpi, llm)

    assert [c.titel for c in config.charts] == [kpi.name for kpi in artefakt.kpis]
    assert fake.aufrufe[0]["format"] is not None  # Schritt 3 übergibt sein Schema, die Harness reicht es an Ollama weiter
    assert zeilen(protokoll)[0]["schritt"] == "dashboard"
