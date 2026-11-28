"""Tests für Schritt 4 (PSP 5.6): Akzeptanzkriterien aus docs/stories/US-07 sowie die Arbeitsteilung Vorlage/Modell.

Das Sprachmodell wird durch FakeLLM ersetzt: keine GPU, reproduzierbar.
"""

import json
import sqlite3
from datetime import date

import pytest
from dashboard_framework.models.artefakt import Artefakt
from dashboard_framework.models.dashboard_config import Chart, DashboardConfig

from pipeline.harness.llm import LLMFehler
from pipeline.schritte.schritt4_doku import (
    OHNE_ERKLAERUNG,
    SCHRITT,
    VOM_MODELL,
    erzeuge_doku,
)

SQL = {
    "Umsatz nach Region": "SELECT region, SUM(umsatz) AS summe FROM absatz GROUP BY region",
    "Umsatzverlauf": "SELECT strftime('%Y-%m', datum) AS monat, SUM(umsatz) AS summe FROM absatz GROUP BY monat ORDER BY monat",
}


class FakeLLM:
    def __init__(self, antwort, modell="qwen3:8b", fallback_modell=None, url=None):
        self.antwort = antwort
        self.modell = modell
        self.fallback_modell = fallback_modell
        self.url = url
        self.aufrufe: list[dict] = []

    def antworte(self, prompt, schritt, json_schema=None, versuch=1, modell=None):
        self.aufrufe.append({"prompt": prompt, "schritt": schritt, "json_schema": json_schema})
        if isinstance(self.antwort, Exception):
            raise self.antwort
        return self.antwort if isinstance(self.antwort, str) else json.dumps(self.antwort)


def erklaert(*namen):
    return {"kpis": [{"kpi": n, "aussage": f"Aussage zu {n}.", "berechnung": f"Berechnung zu {n}."} for n in namen]}


@pytest.fixture
def artefakt():
    return Artefakt.aus_dict({
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
            {"name": "Umsatz nach Region", "beschreibung": "Summe von `umsatz` je `region`"},
            {"name": "Umsatzverlauf", "beschreibung": "Summe von `umsatz` je Monat aus `datum`"},
        ],
    })


@pytest.fixture
def db(tmp_path):
    pfad = tmp_path / "daten.db"
    verbindung = sqlite3.connect(pfad)
    verbindung.execute("CREATE TABLE absatz (datum TEXT, region TEXT, umsatz REAL)")
    verbindung.executemany(
        "INSERT INTO absatz VALUES (?, ?, ?)",
        [("2026-01-15", "Nord", 100), ("2026-02-15", "Nord", 50), ("2026-03-31", "Süd", 70)],
    )
    verbindung.commit()
    verbindung.close()
    return pfad


def doku(artefakt, llm, **zusatz):
    return erzeuge_doku(artefakt, SQL, llm, erstellt=date(2026, 11, 23), **zusatz)


# --- US-07.1 Jede KPI mit SQL ------------------------------------------------------------------------


def test_doku_enthaelt_jede_kpi_mit_sql(artefakt):
    text = doku(artefakt, FakeLLM(erklaert(*SQL)))

    for name, sql in SQL.items():
        assert f"### {list(SQL).index(name) + 1}. {name}" in text
        assert f"```sql\n{sql}\n```" in text


# --- US-07.2 Zweck und Zielgruppe -------------------------------------------------------------------


def test_doku_nennt_zweck_und_zielgruppe(artefakt):
    text = doku(artefakt, FakeLLM(erklaert(*SQL)))

    assert "**Zweck:** Umsatz nach Region und Zeit verstehen" in text
    assert "**Für wen:** Vertriebsleitung" in text


# --- Arbeitsteilung: Fakten aus der Vorlage, Erklärtexte vom Modell --------------------------------------


def test_erklaertexte_kommen_aus_einem_einzigen_modellaufruf(artefakt):
    llm = FakeLLM(erklaert(*SQL))

    text = doku(artefakt, llm)

    assert len(llm.aufrufe) == 1 and llm.aufrufe[0]["schritt"] == SCHRITT
    assert "**Was zeigt sie?** Aussage zu Umsatz nach Region." in text
    assert "**Wie wird sie berechnet?** Berechnung zu Umsatzverlauf." in text
    assert SQL["Umsatzverlauf"] in llm.aufrufe[0]["prompt"]  # das Modell erklärt das tatsächliche SQL


def test_vorgabe_und_darstellung_stammen_aus_artefakt_und_konfiguration(artefakt):
    config = DashboardConfig(
        name="sales", titel="Vertriebs-Dashboard", tabelle="absatz",
        charts=[Chart(titel=n, typ=t, sql=SQL[n]) for n, t in [("Umsatz nach Region", "balken"), ("Umsatzverlauf", "linie")]],
    )

    text = doku(artefakt, FakeLLM(erklaert(*SQL)), config=config)

    assert "**Ihre Vorgabe:** Summe von `umsatz` je `region`" in text
    assert "**Darstellung:** Balkendiagramm" in text
    assert "**Darstellung:** Liniendiagramm" in text


def test_datenbasis_nennt_datei_zeilen_und_zeitraum(artefakt, db):
    text = doku(artefakt, FakeLLM(erklaert(*SQL)), db_pfad=db, quelle="verkaeufe.csv")

    assert "Datei `verkaeufe.csv` mit 3 Zeilen aus dem Zeitraum 15.01.2026 bis 31.03.2026" in text
    assert "| `umsatz` | Dezimalzahl | Nettoumsatz in Euro |" in text


def test_entstehung_nennt_modell_und_fallback(artefakt):
    text = doku(artefakt, FakeLLM(erklaert(*SQL), fallback_modell="qwen3:14b"))

    assert "Sprachmodell (qwen3:8b)" in text
    assert "größeres Modell (qwen3:14b)" in text


# --- Ohne brauchbare Erklärung bleibt die Beschreibung vollständig ---------------------------------------


@pytest.mark.parametrize(
    "antwort",
    [
        LLMFehler("Ollama ist nicht erreichbar"),
        "kein JSON",
        {"kpis": "falsch"},
        {"kpis": [{"kpi": "Unbekannt", "aussage": "x", "berechnung": "y"}]},
    ],
)
def test_ohne_erklaerung_bleiben_alle_fakten_erhalten(artefakt, antwort):
    text = doku(artefakt, FakeLLM(antwort))

    assert text.count(OHNE_ERKLAERUNG) == 2
    for sql in SQL.values():
        assert sql in text
    assert "**Zweck:**" in text and "## Wie ist das Dashboard entstanden?" in text


def test_unbrauchbare_erklaerung_fehlt_nur_bei_dieser_kpi(artefakt):
    antwort = erklaert("Umsatz nach Region")
    antwort["kpis"].append({"kpi": "Umsatzverlauf", "aussage": "", "berechnung": "x" * 5000})

    text = doku(artefakt, FakeLLM(antwort))

    assert "Aussage zu Umsatz nach Region." in text
    assert text.count(OHNE_ERKLAERUNG) == 1


# --- Review zum PR für 5.6 und 5.7: Kennzeichnung und Ort des Modells ---------------------------------------------------


def test_erklaertexte_sind_als_vom_modell_formuliert_gekennzeichnet(artefakt):
    text = doku(artefakt, FakeLLM(erklaert("Umsatz nach Region")))

    assert text.count(VOM_MODELL) == 1  # nur bei der KPI, die eine Erklärung bekam
    assert text.index("Aussage zu Umsatz nach Region.") < text.index(VOM_MODELL)


@pytest.mark.parametrize("url", ["http://localhost:11434", "http://127.0.0.1:11434", "localhost:11434"])
def test_lokales_modell_kein_cloud_dienst(artefakt, url):
    text = doku(artefakt, FakeLLM(erklaert(*SQL), url=url))

    assert "lokal betriebenes Sprachmodell" in text
    assert "an keinen Cloud-Dienst übertragen" in text


def test_entferntes_modell_wird_ehrlich_benannt(artefakt):
    text = doku(artefakt, FakeLLM(erklaert(*SQL), url="https://gpu.example.org:11434"))

    assert "lokal betriebenes" not in text and "Cloud-Dienst" not in text
    assert "auf dem Rechner gpu.example.org" in text and "nicht die vollständigen Daten" in text


def test_ohne_adresse_keine_aussage_zum_ort(artefakt):
    text = doku(artefakt, FakeLLM(erklaert(*SQL)))

    assert "Cloud-Dienst" not in text and "auf dem Rechner" not in text
