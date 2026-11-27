"""Tests für den Befehl dashframe-run (PSP 5.7): Akzeptanzkriterium US-08.2."""

import pytest

from pipeline.run import main


@pytest.fixture
def csv(tmp_path):
    pfad = tmp_path / "daten.csv"
    pfad.write_text("datum;region;umsatz\n15.01.2026;Nord;100\n", encoding="utf-8")
    return pfad


class KeinModell:
    """Darf nie aufgerufen werden: Ein ungültiges Artefakt muss vorher auffallen."""

    modell, fallback_modell, lauf = "qwen3:8b", None, None

    def antworte(self, *args, **kwargs):
        raise AssertionError("Das Modell wurde trotz ungültigem Artefakt aufgerufen")


def test_cli_prueft_artefakt(tmp_path, csv):
    ordner = tmp_path / "kaputt"
    ordner.mkdir()
    (ordner / "artefakt.yaml").write_text("name: kaputt\ntitel: Test\n", encoding="utf-8")  # Ziel, Publikum, ... fehlen

    code = main([str(ordner), str(csv), "--ausgabe", str(tmp_path / "ausgabe")], llm=KeinModell())

    assert code == 1
    assert not (tmp_path / "ausgabe").exists()  # nichts angelegt, kein Modellaufruf


def test_cli_meldet_ungueltiges_artefakt(tmp_path, csv, capsys):
    ordner = tmp_path / "leer"
    ordner.mkdir()

    code = main([str(ordner), str(csv)], llm=KeinModell())

    fehler = capsys.readouterr().err
    assert code == 1
    assert "Es wurde kein Dashboard erzeugt." in fehler
    assert "Fehlgeschlagen: Artefakt prüfen" in fehler
    assert "artefakt.yaml" in fehler  # sagt, was fehlt
    assert "Was tun:" in fehler


def test_falscher_artefakt_pfad_nennt_den_ordner(tmp_path, csv, capsys):
    code = main([str(tmp_path / "gibtsnicht"), str(csv)], llm=KeinModell())

    fehler = capsys.readouterr().err
    assert code == 1
    assert f"Im Ordner {(tmp_path / 'gibtsnicht').resolve()} gibt es keine artefakt.yaml" in fehler
    assert "Prüfen Sie den Pfad zum Artefakt-Ordner" in fehler
