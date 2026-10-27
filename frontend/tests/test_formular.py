"""Tests zu Tabellen-Umwandlung, Speichern und Laden im Eingabeformular sowie ein Rauchtest der Eingabe-App."""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard_framework.eingabe.formular import speichere_artefakt_ordner, vorhandene_artefakte, zeilen_aus_tabelle
from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler

APP = Path(__file__).resolve().parents[1] / "src" / "dashboard_framework" / "eingabe" / "app.py"
BEISPIEL = Path(__file__).resolve().parents[1] / "artefakte" / "sales" / "artefakt.yaml"


def test_zeilen_aus_tabelle_ersetzt_leere_zellen_und_verwirft_leere_zeilen():
    df = pd.DataFrame({"name": ["a", None, "", " b "], "typ": ["text", None, None, float("nan")]})
    assert zeilen_aus_tabelle(df, ["name", "typ", "beschreibung"]) == [
        {"name": "a", "typ": "text", "beschreibung": ""},
        {"name": "b", "typ": "", "beschreibung": ""},
    ]


def test_speichern_legt_ordner_an_und_schuetzt_vor_ueberschreiben(tmp_path):
    artefakt = Artefakt.aus_yaml(BEISPIEL)
    ziel = speichere_artefakt_ordner(artefakt, b"PNG-BYTES", tmp_path)
    assert ziel == (tmp_path / "sales").resolve()
    assert (ziel / "logo.png").read_bytes() == b"PNG-BYTES"
    assert Artefakt.aus_yaml(ziel / "artefakt.yaml") == artefakt
    with pytest.raises(ArtefaktFehler, match="schon ein Artefakt"):
        speichere_artefakt_ordner(artefakt, None, tmp_path)
    speichere_artefakt_ordner(artefakt, None, tmp_path, ueberschreiben=True)


def test_speichern_verlaesst_den_artefakt_ordner_nie(tmp_path):
    artefakt = Artefakt.aus_yaml(BEISPIEL).model_copy(update={"name": ".."})  # umgeht die Namensprüfung absichtlich
    with pytest.raises(ArtefaktFehler, match="außerhalb"):
        speichere_artefakt_ordner(artefakt, None, tmp_path / "artefakte")
    assert not (tmp_path / "artefakt.yaml").exists()


def test_vorhandene_artefakte(tmp_path):
    assert vorhandene_artefakte(tmp_path / "gibts_nicht") == []
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "artefakt.yaml").write_text("x")
    (tmp_path / "a").mkdir()  # ohne artefakt.yaml: zählt nicht
    assert vorhandene_artefakte(tmp_path) == ["b"]


def test_eingabe_app_startet_und_wartet_auf_eingaben():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    assert any("Füllen Sie die Felder" in i.value for i in app.info)


def test_eingabe_app_meldet_fehler_sofort():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    app.session_state["f_name"] = "Falscher Name!"
    app.run()
    assert not app.exception
    texte = " ".join(m.value for m in app.markdown)
    assert "name:" in texte and "Pflichtfeld" in texte
