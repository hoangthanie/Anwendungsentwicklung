"""Tests für run.py (PSP 5.7): Akzeptanzkriterien US-08.1 und US-08.3 sowie "keine halben Pakete".

Ende zu Ende über alle vier Schritte, das Sprachmodell wird ersetzt: keine GPU, reproduzierbar.
"""

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from dashboard_framework.models.artefakt import Artefakt
from dashboard_framework.models.dashboard_config import DashboardConfig
from dashboard_framework.runner.daten import lade_chart_daten

from pipeline.harness.llm import LLM, LLMFehler
from pipeline.run import PipelineFehler, pipeline

LOGO = Path(__file__).resolve().parents[2] / "frontend" / "examples" / "sales" / "logo.png"
SQL_REGION = "SELECT region, SUM(umsatz) AS summe FROM absatz GROUP BY region ORDER BY region"
SQL_VERLAUF = "SELECT strftime('%Y-%m', datum) AS monat, SUM(umsatz) AS summe FROM absatz GROUP BY monat ORDER BY monat"
KPIS = ["Umsatz nach Region", "Umsatzverlauf"]

ANTWORTEN = {
    "query": [{"sql": SQL_REGION, "ablehnung": ""}, {"sql": SQL_VERLAUF, "ablehnung": ""}],
    "dashboard": [{"charts": [{"kpi": KPIS[0], "typ": "balken"}, {"kpi": KPIS[1], "typ": "linie", "breite": "voll"}]}],
    "doku": [{"kpis": [{"kpi": k, "aussage": f"Zeigt {k}.", "berechnung": f"Rechnet {k}."} for k in KPIS]}],
}


class FakeLLM:
    """Antwortet je Schritt der Reihe nach mit vorbereiteten Antworten; eine Exception wird geworfen."""

    def __init__(self, antworten, modell="qwen3:8b", fallback_modell=None):
        self.antworten = {schritt: list(liste) for schritt, liste in antworten.items()}
        self.modell, self.fallback_modell, self.lauf = modell, fallback_modell, None
        self.aufrufe: list[str] = []

    def antworte(self, prompt, schritt, json_schema=None, versuch=1, modell=None):
        self.aufrufe.append(schritt)
        if not self.antworten.get(schritt):
            raise AssertionError(f"FakeLLM: keine Antwort mehr für Schritt {schritt}")
        antwort = self.antworten[schritt].pop(0)
        if isinstance(antwort, Exception):
            raise antwort
        return json.dumps(antwort)


@pytest.fixture
def artefakt_ordner(tmp_path):
    ordner = tmp_path / "artefakte" / "sales"
    Artefakt.aus_dict({
        "name": "sales",
        "titel": "Vertriebs-Dashboard",
        "ziel": "Umsatz nach Region und Zeit verstehen",
        "publikum": "Vertriebsleitung",
        "tabelle": "absatz",
        "spalten": [
            {"name": "datum", "typ": "datum", "beschreibung": "Verkaufstag"},
            {"name": "region", "typ": "text", "beschreibung": "Vertriebsregion"},
            {"name": "umsatz", "typ": "dezimal", "beschreibung": "Nettoumsatz in Euro"},
        ],
        "kpis": [
            {"name": KPIS[0], "beschreibung": "Summe von `umsatz` je `region`"},
            {"name": KPIS[1], "beschreibung": "Summe von `umsatz` je Monat aus `datum`"},
        ],
        "branding": {"firmenname": "Muster GmbH", "farben": ["#1F3864"], "logo": "logo.png"},
    }).speichern(ordner / "artefakt.yaml")
    shutil.copy(LOGO, ordner / "logo.png")
    return ordner


@pytest.fixture
def csv(tmp_path):
    pfad = tmp_path / "verkaeufe.csv"
    pfad.write_text(
        "datum;region;umsatz\n15.01.2026;Nord;100\n15.02.2026;Nord;50\n15.01.2026;Süd;70\n15.02.2026;Ost;30\n",
        encoding="utf-8",
    )
    return pfad


def reste(ausgabe: Path) -> list[str]:
    """Versteckte Arbeitsordner, die nach einem Lauf nicht mehr da sein dürfen."""
    return [p.name for p in ausgabe.iterdir() if p.name.startswith(".")] if ausgabe.exists() else []


# --- US-08.1 Paket wird erzeugt -------------------------------------------------------------------------


def test_pipeline_erzeugt_config_und_readme(artefakt_ordner, csv, tmp_path):
    ausgabe = tmp_path / "ausgabe"
    llm = FakeLLM(ANTWORTEN)

    ziel = pipeline(artefakt_ordner, csv, ausgabe, llm=llm)

    assert ziel == ausgabe / "sales"
    assert sorted(p.name for p in ziel.iterdir()) == ["README.md", "dashboard.json", "daten.db", "logo.png"]
    assert llm.aufrufe == ["query", "query", "dashboard", "doku"]
    config = DashboardConfig.laden(ziel / "dashboard.json")
    assert config.db_pfad == "daten.db"  # relativ: der Ordner läuft so, wie er ist, lokal und auf dem Pi
    assert [c.sql for c in config.charts] == [SQL_REGION, SQL_VERLAUF]
    readme = (ziel / "README.md").read_text(encoding="utf-8")
    assert config.doku == readme  # derselbe Text im Tab "Über dieses Dashboard"
    assert "Datei `verkaeufe.csv` mit 4 Zeilen" in readme and "Zeigt Umsatz nach Region." in readme
    assert reste(ausgabe) == []


def test_paket_laeuft_im_runner(artefakt_ordner, csv, tmp_path):
    ziel = pipeline(artefakt_ordner, csv, tmp_path / "ausgabe", llm=FakeLLM(ANTWORTEN))

    config = DashboardConfig.laden(ziel / "dashboard.json")
    daten = lade_chart_daten(config, ziel / config.db_pfad)  # derselbe Code, mit dem der Runner die Charts füllt

    assert daten[KPIS[0]].values.tolist() == [["Nord", 150.0], ["Ost", 30.0], ["Süd", 70.0]]
    assert daten[KPIS[1]]["monat"].tolist() == ["2026-01", "2026-02"]


def test_fortschritt_meldet_jeden_schritt(artefakt_ordner, csv, tmp_path):
    meldungen: list[str] = []

    pipeline(artefakt_ordner, csv, tmp_path / "ausgabe", llm=FakeLLM(ANTWORTEN), fortschritt=meldungen.append)

    assert [m[:17] for m in meldungen[:4]] == [f"Schritt {n} von 4: " for n in range(1, 5)]
    assert meldungen[-1].startswith("Fertig:")


# --- US-08.3 Jeder LLM-Aufruf wird protokolliert ------------------------------------------------------------


def test_jeder_llm_aufruf_wird_protokolliert(artefakt_ordner, csv, tmp_path):
    class FakeOllama:  # Ollama-Antworten im Format der Bibliothek, damit die echte Klasse LLM protokolliert
        def __init__(self):
            self.antworten = [json.dumps(a) for schritt in ("query", "dashboard", "doku") for a in ANTWORTEN[schritt]]

        def chat(self, **kwargs):
            return SimpleNamespace(
                message=SimpleNamespace(content=self.antworten.pop(0)), done_reason="stop",
                prompt_eval_count=200, eval_count=30, total_duration=500_000_000, load_duration=0,
            )

    protokoll = tmp_path / "metrics.jsonl"
    llm = LLM(modell="qwen3:8b", fallback_modell="", protokoll=protokoll, client=FakeOllama())

    pipeline(artefakt_ordner, csv, tmp_path / "ausgabe", llm=llm)

    alle = [json.loads(z) for z in protokoll.read_text(encoding="utf-8").splitlines()]
    zeilen = [z for z in alle if z["art"] == "aufruf"]
    assert [z["schritt"] for z in zeilen] == ["query", "query", "dashboard", "doku"]
    pruefungen = [z for z in alle if z["art"] == "pruefung"]  # je geprüftem SQL eine Zeile, mit dem SQL selbst
    assert [(z["ergebnis"], z["sql"]) for z in pruefungen] == [("bestanden", SQL_REGION), ("bestanden", SQL_VERLAUF)]
    assert len({z["lauf"] for z in alle}) == 1
    for zeile in zeilen:
        assert {"zeit", "lauf", "schritt", "versuch", "tokens_in", "tokens_out", "dauer_s"} <= zeile.keys()
    assert len({z["lauf"] for z in zeilen}) == 1 and zeilen[0]["lauf"].endswith("_sales")


# --- Keine halben Pakete -----------------------------------------------------------------------------------


def test_fehlschlag_in_schritt2_hinterlaesst_kein_paket(artefakt_ordner, csv, tmp_path):
    antworten = {**ANTWORTEN, "query": [{"sql": "", "ablehnung": "Es gibt keine Spalte für Kosten"}, ANTWORTEN["query"][1]]}
    ausgabe = tmp_path / "ausgabe"

    with pytest.raises(PipelineFehler) as fehler:
        pipeline(artefakt_ordner, csv, ausgabe, llm=FakeLLM(antworten))

    assert fehler.value.schritt == "Schritt 2 von 4: Kennzahlen berechnen"
    assert "keine Spalte für Kosten" in fehler.value.meldungen[0]
    assert "eindeutiger" in fehler.value.hinweis
    assert not (ausgabe / "sales").exists() and reste(ausgabe) == []


def test_vorhandenes_paket_bleibt_ohne_ueberschreiben_unberuehrt(artefakt_ordner, csv, tmp_path):
    vorhanden = tmp_path / "ausgabe" / "sales"
    vorhanden.mkdir(parents=True)
    (vorhanden / "dashboard.json").write_text("alt", encoding="utf-8")
    llm = FakeLLM(ANTWORTEN)

    with pytest.raises(PipelineFehler, match="bereits ein Dashboard-Paket"):
        pipeline(artefakt_ordner, csv, tmp_path / "ausgabe", llm=llm)

    assert llm.aufrufe == []  # geprüft, bevor das Modell rechnet
    assert (vorhanden / "dashboard.json").read_text(encoding="utf-8") == "alt"


def test_ueberschreiben_ersetzt_das_paket_erst_wenn_das_neue_fertig_ist(artefakt_ordner, csv, tmp_path):
    ausgabe = tmp_path / "ausgabe"
    vorhanden = ausgabe / "sales"
    vorhanden.mkdir(parents=True)
    (vorhanden / "dashboard.json").write_text("alt", encoding="utf-8")
    fehlschlag = {**ANTWORTEN, "dashboard": [{"charts": []}] * 3}  # Schritt 3 scheitert dreimal

    with pytest.raises(PipelineFehler, match="Schritt 3 von 4"):
        pipeline(artefakt_ordner, csv, ausgabe, llm=FakeLLM(fehlschlag), ueberschreiben=True)
    assert (vorhanden / "dashboard.json").read_text(encoding="utf-8") == "alt"

    pipeline(artefakt_ordner, csv, ausgabe, llm=FakeLLM(ANTWORTEN), ueberschreiben=True)
    assert DashboardConfig.laden(vorhanden / "dashboard.json").name == "sales"
    assert reste(ausgabe) == []


def test_ollama_nicht_erreichbar_wird_verstaendlich_gemeldet(artefakt_ordner, csv, tmp_path):
    llm = FakeLLM({"query": [LLMFehler("Ollama ist nicht erreichbar. Läuft Ollama auf diesem Rechner?")]})

    with pytest.raises(PipelineFehler) as fehler:
        pipeline(artefakt_ordner, csv, tmp_path / "ausgabe", llm=llm)

    assert fehler.value.schritt == "Schritt 2 von 4: Kennzahlen berechnen (Sprachmodell)"
    assert "Ollama ist nicht erreichbar" in fehler.value.als_text()


def test_fehlende_datendatei_wird_vor_dem_modell_gemeldet(artefakt_ordner, tmp_path):
    llm = FakeLLM(ANTWORTEN)

    with pytest.raises(PipelineFehler, match="Datendatei nicht gefunden"):
        pipeline(artefakt_ordner, tmp_path / "gibtsnicht.csv", tmp_path / "ausgabe", llm=llm)
    assert llm.aufrufe == []


def test_gesperrtes_paket_wird_verstaendlich_gemeldet(artefakt_ordner, csv, tmp_path, monkeypatch):
    def gesperrt(arbeit, ziel):  # wie unter Windows, wenn ein laufendes Dashboard eine Datei offen hält
        raise PermissionError("[WinError 32] Die Datei wird von einem anderen Prozess verwendet")

    monkeypatch.setattr("pipeline.run._einsetzen", gesperrt)
    ausgabe = tmp_path / "ausgabe"

    with pytest.raises(PipelineFehler) as fehler:
        pipeline(artefakt_ordner, csv, ausgabe, llm=FakeLLM(ANTWORTEN))

    assert fehler.value.schritt == "Paket speichern"
    assert "WinError 32" in fehler.value.meldungen[0] and "laufendes Dashboard" in fehler.value.hinweis
    assert reste(ausgabe) == []  # Arbeitsordner aufgeräumt
