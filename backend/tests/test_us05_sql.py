"""Tests für Schritt 2 (PSP 5.4): Akzeptanzkriterien aus docs/stories/US-05 sowie die Prüfschichten aus ADR 0008.

Das Sprachmodell wird durch FakeLLM ersetzt: keine GPU, reproduzierbar.
"""

import json
import sqlite3

import pytest
from dashboard_framework.harness.dashboard import erzeuge_config
from dashboard_framework.models.artefakt import Artefakt

from pipeline.harness.llm import LLMFehler
from pipeline.harness.validators import (
    SqlPruefFehler,
    pruefe_ausfuehrbar,
    pruefe_bedeutung,
    pruefe_keine_selbstdivision,
    pruefe_ohne_systemzeit,
    pruefe_plausibilitaet,
    pruefe_zeitreihe_aufsteigend,
)
from pipeline.schritte.schritt1_datenmodell import lese_schema
from pipeline.schritte.schritt2_query import (
    SqlFehler,
    ausfuehren,
    baue_prompt,
    erzeuge_sql,
    regel_zeitbezug,
)

RICHTIG = "SELECT region, SUM(umsatz) AS summe FROM absatz GROUP BY region"


class FakeLLM:
    """Liefert vorbereitete Antworten der Reihe nach und merkt sich jeden Aufruf (wie frontend/tests/fakes.py, plus versuch)."""

    def __init__(self, *antworten, modell="qwen3:8b", fallback_modell=None):
        self.antworten = list(antworten)
        self.aufrufe: list[dict] = []
        self.modell = modell
        self.fallback_modell = fallback_modell

    def antworte(self, prompt, schritt, json_schema=None, versuch=1, modell=None):
        self.aufrufe.append(
            {"prompt": prompt, "schritt": schritt, "json_schema": json_schema, "versuch": versuch, "modell": modell}
        )
        if not self.antworten:
            raise AssertionError("FakeLLM: keine vorbereitete Antwort mehr")
        antwort = self.antworten.pop(0)
        if isinstance(antwort, Exception):
            raise antwort
        return antwort if isinstance(antwort, str) else json.dumps(antwort)


def sql(text):
    return {"sql": text, "ablehnung": ""}


@pytest.fixture
def artefakt():
    return Artefakt.aus_dict({
        "name": "sales",
        "titel": "Test",
        "ziel": "Umsatz verstehen",
        "publikum": "Vertrieb",
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
    """Testdaten mit bekannten Referenzwerten (US-05.3): Summe Nord = 150, Süd = 70, Ost = 30."""
    pfad = tmp_path / "daten.db"
    verbindung = sqlite3.connect(pfad)
    verbindung.execute("CREATE TABLE absatz (datum TEXT, region TEXT, umsatz REAL)")
    verbindung.executemany(
        "INSERT INTO absatz VALUES (?, ?, ?)",
        [("2026-01-15", "Nord", 100), ("2026-02-15", "Nord", 50), ("2026-01-15", "Süd", 70),
         ("2026-01-15", "Ost", 10), ("2026-02-15", "Ost", 20)],
    )
    verbindung.commit()
    verbindung.close()
    return pfad


@pytest.fixture
def schema(db):
    return lese_schema(db, "absatz")


@pytest.fixture
def kpi(artefakt):
    return artefakt.kpis[0]


# --- US-05.1 Ein lesendes SQL je KPI ------------------------------------------------------------


def test_ein_geprueftes_select_je_kpi(kpi, schema, db):
    llm = FakeLLM(sql(RICHTIG))

    assert erzeuge_sql(kpi, schema, "absatz", llm, db) == RICHTIG
    assert len(llm.aufrufe) == 1
    assert llm.aufrufe[0]["schritt"] == "query"
    assert llm.aufrufe[0]["json_schema"]["required"] == ["sql", "ablehnung"]


# --- US-05.2 Schicht Bedeutung ------------------------------------------------------------------


def test_unbekannte_spalte_im_sql_wird_abgelehnt():
    with pytest.raises(SqlPruefFehler, match="regoin"):
        pruefe_bedeutung("SELECT regoin, SUM(umsatz) FROM absatz GROUP BY regoin", {"datum", "region", "umsatz"})


def test_eigene_aliase_sind_keine_unbekannten_spalten():
    pruefe_bedeutung(
        "WITH m AS (SELECT strftime('%Y-%m', datum) AS monat, SUM(umsatz) AS summe FROM absatz GROUP BY monat) "
        "SELECT monat, summe FROM m ORDER BY summe DESC LIMIT 3",
        {"datum", "region", "umsatz"},
    )


# --- US-05.3 Schicht Plausibilität (Testorakel) -------------------------------------------------


def test_plausibilitaet_gegen_testorakel(db):
    referenz = {"Nord": 150, "Süd": 70, "Ost": 30}
    pruefe_plausibilitaet(RICHTIG, db, referenz)
    with pytest.raises(SqlPruefFehler, match="Nord: 75"):
        pruefe_plausibilitaet("SELECT region, AVG(umsatz) FROM absatz GROUP BY region", db, referenz)


def test_orakel_greift_auch_in_der_reparaturschleife(kpi, schema, db):
    llm = FakeLLM(sql("SELECT region, AVG(umsatz) AS summe FROM absatz GROUP BY region"), sql(RICHTIG))

    assert erzeuge_sql(kpi, schema, "absatz", llm, db, erwartet={"Nord": 150, "Süd": 70, "Ost": 30}) == RICHTIG
    assert "Referenzwerte" in llm.aufrufe[1]["prompt"]


# --- US-05.4 Reparaturschleife ------------------------------------------------------------------


def test_reparaturschleife_korrigiert_fehler(artefakt, schema, db):
    verlauf = artefakt.kpis[1]
    falsch = "SELECT MONTH(datum) AS monat, SUM(umsatz) AS summe FROM absatz GROUP BY monat"
    richtig = "SELECT strftime('%Y-%m', datum) AS monat, SUM(umsatz) AS summe FROM absatz GROUP BY monat"
    llm = FakeLLM(sql(falsch), sql(richtig))

    assert erzeuge_sql(verlauf, schema, "absatz", llm, db) == richtig
    zweiter = llm.aufrufe[1]
    assert zweiter["versuch"] == 2  # landet im Run-Protokoll
    assert falsch in zweiter["prompt"]  # das Modell sieht sein letztes SQL ...
    assert "MONTH" in zweiter["prompt"] and "SQLite meldet" in zweiter["prompt"]  # ... und die Meldung von SQLite


def test_abbruch_nach_max_versuchen(kpi, schema, db):
    llm = FakeLLM(*[sql("SELECT regoin, SUM(umsatz) FROM absatz GROUP BY regoin")] * 3)

    with pytest.raises(SqlFehler, match="nach 3 Versuchen") as fehler:
        erzeuge_sql(kpi, schema, "absatz", llm, db)
    assert "Umsatz nach Region" in fehler.value.meldungen[0]
    assert len(llm.aufrufe) == 3


# --- weitere Prüfschichten (ADR 0008) -----------------------------------------------------------


@pytest.mark.parametrize(
    ("antwort", "meldung"),
    [
        ("DELETE FROM absatz", "Nicht erlaubt"),
        ("SELECT region, SUM(umsatz) FROM kunden GROUP BY region", "Unbekannte Tabelle"),
        ("SELECT region, COUNT(*) AS anzahl FROM absatz GROUP BY region", "umsatz"),  # Anker `umsatz` ignoriert
        ("SELECT region, SUM(umsatz) FROM absatz WHERE region = 'Nirgendwo' GROUP BY region", "keine Zeilen"),
        ("kein JSON", "kein gültiges JSON"),
    ],
)
def test_pruefschicht_meldet_fehler_an_das_modell(kpi, schema, db, antwort, meldung):
    llm = FakeLLM(antwort if antwort == "kein JSON" else sql(antwort), sql(RICHTIG))

    assert erzeuge_sql(kpi, schema, "absatz", llm, db) == RICHTIG
    assert meldung in llm.aufrufe[1]["prompt"]


def test_ablehnung_bricht_ohne_weiteren_versuch_ab(kpi, schema, db):
    llm = FakeLLM({"sql": "", "ablehnung": "Es gibt keine Spalte zur Kundenzufriedenheit"})

    with pytest.raises(SqlFehler, match="nicht berechenbar: Es gibt keine Spalte"):
        erzeuge_sql(kpi, schema, "absatz", llm, db)
    assert len(llm.aufrufe) == 1


def test_prompt_nennt_beispielwerte_und_sqlite_regeln(kpi, schema):
    prompt = baue_prompt(kpi, schema, "absatz", {"region": "text, Vertriebsregion"})
    assert "'Nord'" in prompt and "'2026-01-15'" in prompt
    assert "Vertriebsregion" in prompt
    assert "strftime('%Y-%m', spalte)" in prompt
    assert "zuerst die Gruppierung" in prompt  # Dashboard nimmt erste Spalte als X-Achse, zweite als Wert


# --- Schritt komplett und Übergabe an Schritt 3 -------------------------------------------------


def test_ausfuehren_sammelt_probleme_aller_kpis(artefakt, schema, db):
    llm = FakeLLM({"sql": "", "ablehnung": "zu unklar"}, {"sql": "", "ablehnung": "auch unklar"})

    with pytest.raises(SqlFehler) as fehler:
        ausfuehren(artefakt, schema, db, llm)
    assert len(fehler.value.meldungen) == 2  # beide KPIs werden gemeldet, nicht nur die erste


def test_ergebnis_passt_zu_schritt3(artefakt, schema, db):
    verlauf = "SELECT strftime('%Y-%m', datum) AS monat, SUM(umsatz) AS summe FROM absatz GROUP BY monat"
    llm = FakeLLM(sql(RICHTIG), sql(verlauf))

    sql_je_kpi = ausfuehren(artefakt, schema, db, llm)
    wahl = {"charts": [{"kpi": k.name, "typ": "balken"} for k in artefakt.kpis]}
    config = erzeuge_config(artefakt, sql_je_kpi, FakeLLM(wahl))

    assert [c.sql for c in config.charts] == [RICHTIG, verlauf]


# --- Zeitbezug: Daten statt Kalender (ADR 0008) -------------------------------------------------


@pytest.mark.parametrize(
    "falsch",
    [
        "SELECT SUM(umsatz) AS s FROM absatz WHERE strftime('%Y-%m', datum) = strftime('%Y-%m', date('now'))",
        "SELECT SUM(umsatz) AS s FROM absatz WHERE datum <= CURRENT_DATE",
        "SELECT SUM(umsatz) AS s FROM absatz WHERE datum <= CURRENT_TIMESTAMP",
        "SELECT julianday('now') - julianday(MAX(datum)) AS tage FROM absatz",
    ],
)
def test_heutiges_datum_wird_abgelehnt(falsch):
    with pytest.raises(SqlPruefFehler, match="heutige Datum"):
        pruefe_ohne_systemzeit(falsch)


def test_juengster_monat_aus_den_daten_ist_erlaubt():
    pruefe_ohne_systemzeit(
        "SELECT SUM(umsatz) AS s FROM absatz WHERE strftime('%Y-%m', datum) = strftime('%Y-%m', (SELECT MAX(datum) FROM absatz))"
    )


def test_systemzeit_landet_in_der_reparaturschleife(artefakt, schema, db):
    kpi = artefakt.kpis[0]
    mit_now = "SELECT region, SUM(umsatz) AS summe FROM absatz WHERE datum <= date('now') GROUP BY region"
    llm = FakeLLM(sql(mit_now), sql(RICHTIG))

    assert erzeuge_sql(kpi, schema, "absatz", llm, db) == RICHTIG
    assert "heutige Datum" in llm.aufrufe[1]["prompt"]


def test_regel_zeitbezug_nennt_die_datumsspalte_aus_dem_artefakt():
    regel = regel_zeitbezug("tab", ["erfasst_am"])
    assert "MAX(erfasst_am) FROM tab" in regel
    assert "nie auf das heutige Datum" in regel


def test_regel_zeitbezug_ohne_datumsspalte_verlangt_ablehnung():
    regel = regel_zeitbezug("tab", [])
    assert "keine Datumsspalte" in regel and "ablehnung" in regel
    assert "MAX(" not in regel


def test_regel_zeitbezug_bei_mehreren_datumsspalten():
    regel = regel_zeitbezug("tab", ["bestellt_am", "geliefert_am"])
    assert "die die KPI nennt" in regel and "geliefert_am" in regel


def test_ausfuehren_gibt_datumsspalten_aus_dem_artefakt_weiter(artefakt, schema, db):
    verlauf = "SELECT strftime('%Y-%m', datum) AS monat, SUM(umsatz) AS summe FROM absatz GROUP BY monat"
    llm = FakeLLM(sql(RICHTIG), sql(verlauf))

    ausfuehren(artefakt, schema, db, llm)
    assert "MAX(datum) FROM absatz" in llm.aufrufe[0]["prompt"]


# --- Division durch sich selbst (zweiter Probelauf, ADR 0008) -----------------------------------


@pytest.mark.parametrize(
    "falsch",
    [
        "SELECT SUM(umsatz) / SUM(umsatz) AS q FROM absatz",
        "SELECT SUM(umsatz) / NULLIF(SUM(umsatz), 0) AS q FROM absatz",
        "SELECT (SUM(umsatz)) / CAST(SUM(umsatz) AS REAL) AS q FROM absatz",
    ],
)
def test_division_durch_sich_selbst_wird_abgelehnt(falsch):
    with pytest.raises(SqlPruefFehler, match="durch sich selbst"):
        pruefe_keine_selbstdivision(falsch)


def test_vergleich_zweier_zeitraeume_ist_erlaubt(db):
    richtig = (
        "SELECT SUM(CASE WHEN strftime('%Y-%m', datum) = '2026-02' THEN umsatz END)"
        " / SUM(CASE WHEN strftime('%Y-%m', datum) = '2026-01' THEN umsatz END) AS q FROM absatz"
    )
    pruefe_keine_selbstdivision(richtig)


def test_regel_zeitbezug_zeigt_muster_fuer_zeitraumvergleich():
    regel = regel_zeitbezug("tab", ["erfasst_am"])
    assert "SUM(CASE WHEN strftime('%Y-%m', erfasst_am)" in regel
    assert "Kein WHERE, das nur einen der beiden Zeiträume übrig lässt" in regel


def test_selbstdivision_landet_in_der_reparaturschleife(artefakt, schema, db):
    kpi = artefakt.kpis[0]
    falsch = "SELECT region, SUM(umsatz) / NULLIF(SUM(umsatz), 0) AS q FROM absatz GROUP BY region"
    llm = FakeLLM(sql(falsch), sql(RICHTIG))

    assert erzeuge_sql(kpi, schema, "absatz", llm, db) == RICHTIG
    assert "durch sich selbst" in llm.aufrufe[1]["prompt"]


# --- Leeres Ergebnis und Reihenfolge von Zeitreihen (dritter Probelauf, ADR 0008) --------------


def test_ergebnis_nur_null_wird_abgelehnt(artefakt, schema, db):
    kpi = artefakt.kpis[0]
    nur_null = (
        "SELECT SUM(CASE WHEN strftime('%Y-%m', datum) = '2026-01' THEN umsatz END) AS q "
        "FROM absatz WHERE strftime('%Y-%m', datum) = '2026-02' AND region = 'Süd'"
    )
    llm = FakeLLM(sql(nur_null), sql(RICHTIG))

    assert erzeuge_sql(kpi, schema, "absatz", llm, db) == RICHTIG
    assert "leer (NULL)" in llm.aufrufe[1]["prompt"]


def test_zeitreihe_absteigend_wird_abgelehnt():
    with pytest.raises(SqlPruefFehler, match="nicht aufsteigend"):
        pruefe_zeitreihe_aufsteigend(["monat", "summe"], [("2026-02", 2.0), ("2026-01", 1.0)])


@pytest.mark.parametrize(
    "zeilen",
    [
        [("2026-01", 1.0), ("2026-02", 2.0)],  # Zeitreihe aufsteigend
        [("2026-01-15 08:00:00", 1.0), ("2026-01-15 09:30:00", 2.0)],  # mit Uhrzeit
        [("Steuerung", 9.0), ("Antrieb", 5.0)],  # Rangliste: keine Zeitspalte, Reihenfolge frei
        [("2026-01", 1.0)],  # nur ein Wert
    ],
)
def test_erlaubte_reihenfolgen(zeilen):
    pruefe_zeitreihe_aufsteigend(["a", "b"], zeilen)


def test_regel_4_verlangt_aufsteigende_zeitraeume(kpi, schema):
    assert "aufsteigend nach dem Zeitraum" in baue_prompt(kpi, schema, "absatz")


def test_teilweise_leerer_wert_wird_abgelehnt(db):
    """Vierter Probelauf: je Monat gruppiert, Wert nur in einer Zeile gefüllt, sonst NULL."""
    with pytest.raises(SqlPruefFehler, match="in 1 von 2 Zeilen leer"):
        pruefe_ausfuehrbar(
            "SELECT strftime('%Y-%m', datum) AS monat, "
            "SUM(CASE WHEN strftime('%Y-%m', datum) = '2026-01' THEN umsatz END) AS wert FROM absatz GROUP BY monat",
            db,
        )


# --- Eskalation an das Fallback-Modell (ADR 0008) ------------------------------------------------

FALSCH = sql("SELECT regoin, SUM(umsatz) FROM absatz GROUP BY regoin")


def test_eskalation_an_fallback_modell_nach_drei_fehlversuchen(kpi, schema, db):
    llm = FakeLLM(FALSCH, FALSCH, FALSCH, sql(RICHTIG), fallback_modell="qwen3:14b")

    assert erzeuge_sql(kpi, schema, "absatz", llm, db) == RICHTIG
    assert [a["modell"] for a in llm.aufrufe] == [None, None, None, "qwen3:14b"]
    vierter = llm.aufrufe[3]
    assert vierter["versuch"] == 4
    assert "regoin" in vierter["prompt"] and "Unbekannte Spalte" in vierter["prompt"]  # Aufgabe samt letztem Fehler


def test_keine_eskalation_ohne_fallback_modell(kpi, schema, db):
    llm = FakeLLM(FALSCH, FALSCH, FALSCH)

    with pytest.raises(SqlFehler, match="nach 3 Versuchen. Letzter Fehler"):
        erzeuge_sql(kpi, schema, "absatz", llm, db)
    assert len(llm.aufrufe) == 3


def test_abbruch_wenn_auch_das_fallback_modell_scheitert(kpi, schema, db):
    llm = FakeLLM(FALSCH, FALSCH, FALSCH, FALSCH, fallback_modell="qwen3:14b")

    with pytest.raises(SqlFehler, match="auch nicht mit dem Fallback-Modell qwen3:14b"):
        erzeuge_sql(kpi, schema, "absatz", llm, db)
    assert len(llm.aufrufe) == 4


def test_fehlendes_fallback_modell_bricht_sauber_ab(kpi, schema, db):
    llm = FakeLLM(FALSCH, FALSCH, FALSCH, LLMFehler("Modell nicht installiert"), fallback_modell="qwen3:14b")

    with pytest.raises(SqlFehler, match="Unbekannte Spalte"):  # Meldung zum eigentlichen Problem, kein Absturz
        erzeuge_sql(kpi, schema, "absatz", llm, db)
