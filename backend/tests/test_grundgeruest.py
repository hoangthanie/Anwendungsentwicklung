"""Prüft nur, dass das Backend-Paket installiert und importierbar ist."""

import importlib

import pytest


@pytest.mark.parametrize("modul", ["pipeline.harness.llm", "pipeline.run"])
def test_modul_ist_importierbar(modul):
    importlib.import_module(modul)
