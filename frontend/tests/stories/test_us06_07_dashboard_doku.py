"""Tests zu US-06 (Dashboard-Konfiguration erzeugen): TF-021 und TF-022, plus Prüf- und Sicherheitsfälle.

Hinweis: Diese Backlog-Datei enthält laut Backlog auch die Tests zu US-07 (Dokumentation, Melanie, AP 5.6). Sie werden bei Bedarf hier ergänzt.
"""
import json
from pathlib import Path

import pytest
from fakes import FakeLLM

from dashboard_framework.harness.dashboard import (
    DashboardFehler,
    baue_prompt,
    erzeuge_config,
    extrahiere_json,
    wahl_schema,
)
from dashboard_framework.models.artefakt import Artefakt
from dashboard_framework.models.dashboard_config import DashboardConfig
from dashboard_framework.runner.daten import lade_chart_daten

ARTEFAKT = Path(__file__).resolve().parents[2] / "artefakte" / "sales" / "artefakt.yaml"
BEISPIEL_JSON = Path(__file__).resolve().parents[2] / "examples" / "sales" / "dashboard.json"


@pytest.fixture
def artefakt():
    return Artefakt.aus_yaml(ARTEFAKT)


@pytest.fixture
def sql_je_kpi(artefakt):
    """Das SQL aus Schritt 2: hier das Beispiel-SQL des Referenzfalls, den KPIs des Artefakts der Reihe nach zugeordnet."""
    config = DashboardConfig.laden(BEISPIEL_JSON)
    return {kpi.name: chart.sql for kpi, chart in zip(artefakt.kpis, config.charts, strict=True)}


def wahl(artefakt, **je_kpi):
    """Baut eine vollständige gültige Modellantwort; je_kpi überschreibt einzelne Felder, z. B. wahl(a, **{'Top-Produkte': {'typ': 'tabelle'}})."""
    standard = {"Umsatz nach Region": "balken", "Umsatzverlauf": "linie", "Top-Produkte": "tabelle", "Zielerreichung ggü. Vorperiode": "kennzahl"}
    charts = []
    for kpi in artefakt.kpis:
        eintrag = {"kpi": kpi.name, "typ": standard[kpi.name]}
        eintrag.update(je_kpi.get(kpi.name, {}))
        charts.append(eintrag)
    return {"charts": charts}


def test_ungueltiges_json_fuehrt_zu_neuem_versuch(artefakt, sql_je_kpi):  # TF-021 / US-06.1
    llm = FakeLLM(["Das ist leider kein JSON.", wahl(artefakt)])
    config = erzeuge_config(artefakt, sql_je_kpi, llm)
    assert isinstance(config, DashboardConfig) and len(llm.aufrufe) == 2
    assert "Deine letzte Antwort war ungültig" in llm.aufrufe[1]["prompt"]
    assert "kein gültiges JSON" in llm.aufrufe[1]["prompt"]


def test_name_tabelle_und_firmenfarben_setzt_der_code(artefakt, sql_je_kpi):  # TF-022 / US-06.2
    # Das Modell versucht, Name und Tabelle zu bestimmen: Zusatzfelder sind verboten, die Antwort wird abgelehnt und ersetzt.
    uebergriffig = {**wahl(artefakt), "name": "anders", "tabelle": "fremd"}
    llm = FakeLLM([uebergriffig, wahl(artefakt)])
    config = erzeuge_config(artefakt, sql_je_kpi, llm)
    assert (config.name, config.tabelle) == ("sales", "absatz")
    assert config.branding.farben == ["#1F3864", "#ED7D31", "#70AD47"]
    assert config.titel == artefakt.titel and config.spalten == artefakt.spalten


def test_sql_kommt_immer_aus_schritt_2_nie_vom_modell(artefakt, sql_je_kpi):
    boese = wahl(artefakt)
    boese["charts"][0]["sql"] = "DELETE FROM absatz"
    llm = FakeLLM([boese, wahl(artefakt)])
    config = erzeuge_config(artefakt, sql_je_kpi, llm)
    assert [c.sql for c in config.charts] == [sql_je_kpi[k.name] for k in artefakt.kpis]
    assert len(llm.aufrufe) == 2  # erste Antwort wurde abgelehnt ...
    assert "charts.0.sql" in llm.aufrufe[1]["prompt"]  # ... und zwar genau wegen des verbotenen Felds 'sql'


def test_reihenfolge_bestimmt_das_artefakt_nicht_das_modell(artefakt, sql_je_kpi):
    antwort = wahl(artefakt)
    antwort["charts"].reverse()
    config = erzeuge_config(artefakt, sql_je_kpi, FakeLLM([antwort]))
    assert [c.titel for c in config.charts] == [k.name for k in artefakt.kpis]


def test_modellwahl_wird_uebernommen(artefakt, sql_je_kpi):
    antwort = wahl(artefakt, **{"Umsatz nach Region": {"typ": "balken", "farbe": "#ed7d31", "sortierung": "absteigend", "breite": "voll"}})
    config = erzeuge_config(artefakt, sql_je_kpi, FakeLLM([antwort]))
    erstes = config.charts[0]
    assert (erstes.farbe, erstes.sortierung, erstes.breite) == ("#ED7D31", "absteigend", "voll")


@pytest.mark.parametrize("fehler,erwartung", [
    ({"charts": [{"kpi": "Unbekannt", "typ": "balken"}]}, "unbekannte KPI"),
    ({"charts": []}, "es fehlen KPI"),
    ({"charts": [{"kpi": "Umsatz nach Region", "typ": "kreis3d"}]}, "Schema"),
    ({"zeug": 1}, "Schema"),
    ("[1, 2, 3]", "Schema"),
])
def test_ungueltige_antworten_werden_zurueckgemeldet(artefakt, sql_je_kpi, fehler, erwartung):
    llm = FakeLLM([fehler, wahl(artefakt)])
    erzeuge_config(artefakt, sql_je_kpi, llm)
    assert erwartung in llm.aufrufe[1]["prompt"]


def test_doppelte_kpi_und_fehlende_kpi_werden_gemeldet(artefakt, sql_je_kpi):
    antwort = wahl(artefakt)
    antwort["charts"].append(antwort["charts"][0])
    llm = FakeLLM([antwort, wahl(artefakt)])
    erzeuge_config(artefakt, sql_je_kpi, llm)
    assert "mehrfach genannt" in llm.aufrufe[1]["prompt"]


def test_farbe_ausserhalb_der_palette_wird_abgelehnt(artefakt, sql_je_kpi):
    llm = FakeLLM([wahl(artefakt, **{"Umsatzverlauf": {"farbe": "#FF0000"}}), wahl(artefakt)])
    erzeuge_config(artefakt, sql_je_kpi, llm)
    assert "nicht erlaubt" in llm.aufrufe[1]["prompt"]


def test_abbruch_nach_max_versuchen_mit_verstaendlicher_meldung(artefakt, sql_je_kpi):
    llm = FakeLLM(["Quatsch"] * 5)
    with pytest.raises(DashboardFehler) as fehler:
        erzeuge_config(artefakt, sql_je_kpi, llm, max_versuche=3)
    assert len(llm.aufrufe) == 3
    assert "nach 3 Versuchen" in fehler.value.meldungen[0] and "Letzter Fehler" in fehler.value.meldungen[1]


def test_json_im_codeblock_wird_akzeptiert(artefakt, sql_je_kpi):
    text = "Gern! Hier ist die Konfiguration:\n```json\n" + json.dumps(wahl(artefakt)) + "\n```\nViel Erfolg."
    llm = FakeLLM([text])
    erzeuge_config(artefakt, sql_je_kpi, llm)
    assert len(llm.aufrufe) == 1


def test_extrahiere_json_varianten():
    assert extrahiere_json('{"a": 1}') == {"a": 1}
    assert extrahiere_json('Text vorher {"a": 1} Text danach') == {"a": 1}
    with pytest.raises(ValueError):
        extrahiere_json("gar nichts")
    with pytest.raises(ValueError):
        extrahiere_json("{kaputt")


def test_sql_fehlt_oder_ist_unsicher_stoppt_vor_dem_modell(artefakt, sql_je_kpi):
    llm = FakeLLM([])
    unvollstaendig = {k: v for k, v in sql_je_kpi.items() if k != "Umsatzverlauf"}
    with pytest.raises(DashboardFehler, match="fehlt das SQL"):
        erzeuge_config(artefakt, unvollstaendig, llm)
    unsicher = {**sql_je_kpi, "Umsatzverlauf": "DROP TABLE absatz"}
    with pytest.raises(DashboardFehler, match="nicht erlaubt"):
        erzeuge_config(artefakt, unsicher, llm)
    assert llm.aufrufe == []


def test_schema_enthaelt_nur_erlaubte_werte(artefakt):
    schema = wahl_schema([k.name for k in artefakt.kpis], artefakt.branding.farben)
    props = schema["properties"]["charts"]["items"]["properties"]
    assert props["kpi"]["enum"] == [k.name for k in artefakt.kpis]
    assert props["typ"]["enum"] == ["balken", "linie", "tabelle", "kennzahl"]
    assert props["farbe"]["enum"] == artefakt.branding.farben
    assert schema["properties"]["charts"]["minItems"] == 4 and "sql" not in props
    ohne_farben = wahl_schema(["a"], [])
    assert "farbe" not in ohne_farben["properties"]["charts"]["items"]["properties"]


def test_schema_wird_dem_modell_uebergeben(artefakt, sql_je_kpi):
    llm = FakeLLM([wahl(artefakt)])
    erzeuge_config(artefakt, sql_je_kpi, llm)
    assert llm.aufrufe[0]["schritt"] == "dashboard"
    assert llm.aufrufe[0]["json_schema"] == wahl_schema([k.name for k in artefakt.kpis], artefakt.branding.farben)


def test_prompt_enthaelt_ziel_publikum_kpis_und_sql(artefakt, sql_je_kpi):
    prompt = baue_prompt(artefakt, sql_je_kpi)
    assert artefakt.ziel in prompt and artefakt.publikum in prompt
    for kpi in artefakt.kpis:
        assert kpi.name in prompt and sql_je_kpi[kpi.name] in prompt
    assert "#ED7D31" in prompt


def test_ergebnis_laeuft_im_runner(artefakt, sql_je_kpi, test_db):
    """Integration: Die erzeugte Konfiguration kann der Runner mit echten Daten anzeigen."""
    config = erzeuge_config(artefakt, sql_je_kpi, FakeLLM([wahl(artefakt)]))
    daten = lade_chart_daten(config, test_db)
    assert set(daten) == {k.name for k in artefakt.kpis}
    assert set(daten["Umsatz nach Region"]["region"]) == {"Nord", "Süd", "Ost"}


def test_ergebnis_ist_speicherbar_und_ladbar(artefakt, sql_je_kpi, tmp_path):
    config = erzeuge_config(artefakt, sql_je_kpi, FakeLLM([wahl(artefakt)]))
    config.speichern(tmp_path / "dashboard.json")
    assert DashboardConfig.laden(tmp_path / "dashboard.json") == config
