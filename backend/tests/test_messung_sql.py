"""Tests für das Messwerkzeug (tools/messung_sql.py) und sein Testset.

Wichtigster Test: Jede Referenz-Abfrage besteht alle Prüfschichten aus Schritt 2. Damit ist belegt, dass die
Prüfungen richtige Antworten nicht fälschlich ablehnen, und dass das Testset zu den Testdaten passt.
"""

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import messung_sql
import testdaten
from testset_sql import TESTSET

from pipeline.harness.validators import fuehre_aus


class ReferenzLLM:
    """Antwortet je KPI mit der Referenz-Abfrage aus dem Testset, bei nicht berechenbaren KPIs mit einer Ablehnung."""

    modell, fallback_modell, lauf = "referenz", None, "test"

    def antworte(self, prompt, schritt, json_schema=None, versuch=1, modell=None):
        name = re.search(r"^KPI: (.+)$", prompt, re.MULTILINE).group(1)
        fall = next(f for f in TESTSET if f.name == name)
        if fall.referenz is None:
            return json.dumps({"sql": "", "ablehnung": "Dafür gibt es keine Spalte"})
        return json.dumps({"sql": fall.referenz, "ablehnung": ""})


def test_referenzen_bestehen_alle_pruefschichten_und_gelten_als_richtig(tmp_path):
    ergebnisse = messung_sql.messe(ReferenzLLM(), TESTSET, tmp_path, protokoll=tmp_path / "p.jsonl", ausgabe=lambda t: None)

    assert {e["kpi"]: e["ergebnis"] for e in ergebnisse} == {f.name: "richtig" for f in TESTSET}


def test_testdaten_passen_zu_den_erwarteten_werten(tmp_path):
    messung_sql.messe(ReferenzLLM(), TESTSET, tmp_path, protokoll=tmp_path / "p.jsonl", ausgabe=lambda t: None)
    ziel = next(f for f in TESTSET if f.name == "Zielerreichung ggü. Vorperiode")
    rangliste = next(f for f in TESTSET if f.name == "Häufigste Aktionen")

    assert fuehre_aus(ziel.referenz, tmp_path / "sales.db")[1][0][0] == pytest.approx(1.2281, abs=1e-4)  # wie Probelauf 12
    anzahlen = [n for _, n in fuehre_aus(rangliste.referenz, tmp_path / "aktivitaet.db")[1]]
    assert len(set(anzahlen)) == len(anzahlen)  # keine Gleichstände, die Rangliste ist eindeutig


def test_testdaten_sind_reproduzierbar():
    assert testdaten.sales_zeilen() == testdaten.sales_zeilen()
    assert len(testdaten.sales_zeilen()) == 192 and len(testdaten.aktivitaet_zeilen()) == 495


@pytest.mark.parametrize(
    ("ist", "soll", "reihenfolge", "gleich"),
    [
        ([("Nord", 10.0), ("Süd", 5.0)], [("Süd", 5.0), ("Nord", 10.0)], False, True),  # Reihenfolge egal
        ([("Nord", 10.0), ("Süd", 5.0)], [("Süd", 5.0), ("Nord", 10.0)], True, False),  # Reihenfolge zählt
        ([(1.23,)], [(1.2281,)], False, True),  # auf zwei Stellen gerundet
        ([(11.19,)], [(1.2281,)], False, False),  # Probelauf 8
        ([(100863.0, 1.23)], [(1.2281,)], False, False),  # zusätzliche Spalte
        ([], [(1.0,)], False, False),
    ],
)
def test_vergleich(ist, soll, reihenfolge, gleich):
    assert messung_sql.vergleiche(ist, soll, reihenfolge) is gleich


def test_zusammenfassung_zaehlt_je_schwierigkeit():
    ergebnisse = [
        {"ergebnis": "richtig", "schwierigkeit": "einfach", "tokens_in": 800, "tokens_out": 40, "dauer_s": 1.0},
        {"ergebnis": "falsch", "schwierigkeit": "schwer", "tokens_in": 900, "tokens_out": 90, "dauer_s": 2.0},
    ]

    text = messung_sql.zusammenfassung(ergebnisse)

    assert text.startswith("1 von 2 richtig (einfach 1/1, schwer 0/1); falsch 1")
    assert "Tokens 1.700 rein / 130 raus" in text
