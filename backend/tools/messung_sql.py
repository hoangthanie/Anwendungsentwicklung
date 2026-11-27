"""Messung von Schritt 2: Wie viele KPIs aus dem Testset löst ein Modell richtig, mit welchem Aufwand?

Für jede KPI aus tools/testset_sql.py läuft Schritt 2 genau wie in der Pipeline (Prompt, Prüfschichten,
Reparaturschleife, auf Wunsch Eskalation). Das geprüfte SQL wird danach auf den Testdaten ausgeführt und mit der
Referenz verglichen. So lassen sich Modelle und spätere Varianten (z. B. Intent Layer) auf denselben Fällen
vergleichen, statt einzelne Probeläufe von Hand auszuwerten.

Ergebnis je KPI:
  richtig    Ergebnis stimmt mit der Referenz überein (bzw. nicht berechenbare KPI begründet abgelehnt)
  falsch     geprüftes SQL, aber anderes Ergebnis als die Referenz: der gefährliche Fall, er erreicht das Dashboard
  abbruch    kein gültiges SQL nach allen Versuchen: ehrlich, es entsteht kein falsches Dashboard
  abgelehnt  das Modell hält eine berechenbare KPI für nicht berechenbar

Ausgabe: Zusammenfassung im Terminal, je KPI eine Zeile in runs/messung_sql.csv (wird angehängt),
alle Modellaufrufe und Prüfungen in runs/messung_sql.jsonl. Beides bleibt lokal (runs/ ist in .gitignore).

Aufruf (aus dem Ordner backend, venv aktiv, Ollama läuft):
    python tools/messung_sql.py --modell qwen3:8b
    python tools/messung_sql.py --modell qwen3:8b --fallback qwen3:14b     mit Eskalation wie in der Pipeline
    python tools/messung_sql.py --modell qwen3:8b --fall Zielerreichung    nur Fälle, deren Name das enthält
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import testdaten
import yaml
from dashboard_framework.models.artefakt import Artefakt
from testset_sql import TESTSET, Fall

from pipeline.harness.llm import LLM, LLMFehler
from pipeline.harness.validators import fuehre_aus
from pipeline.schritte import schritt1_datenmodell
from pipeline.schritte.schritt2_query import SqlFehler, erzeuge_sql

BACKEND = Path(__file__).resolve().parent.parent
ARTEFAKTE = BACKEND.parent / "frontend" / "artefakte"
RUNS = BACKEND / "runs"
ERGEBNIS_CSV = RUNS / "messung_sql.csv"
PROTOKOLL = RUNS / "messung_sql.jsonl"
TOLERANZ_ABS, TOLERANZ_REL = 0.01, 0.005  # gerundete Ergebnisse (z. B. ROUND(x, 2)) zählen als richtig
SPALTEN_CSV = [
    "zeit", "lauf", "modell", "fallback", "datensatz", "kpi", "schwierigkeit", "ergebnis", "versuche", "eskaliert",
    "tokens_in", "tokens_out", "dauer_s", "sql", "fehler", "ist",
]


def _gleich(ist: object, soll: object) -> bool:
    zahlen = (int, float)
    if isinstance(ist, zahlen) and isinstance(soll, zahlen) and not isinstance(ist, bool):
        return abs(ist - soll) <= TOLERANZ_ABS + TOLERANZ_REL * abs(soll)
    return str(ist).strip() == str(soll).strip()


def vergleiche(ist: list[tuple], soll: list[tuple], reihenfolge: bool = False) -> bool:
    """Gleiches Ergebnis? Spaltennamen zählen nicht, Zahlen mit kleiner Toleranz, Zeilenreihenfolge nur auf Wunsch."""
    if len(ist) != len(soll) or any(len(a) != len(b) for a, b in zip(ist, soll, strict=False)):
        return False
    if not reihenfolge:
        def schluessel(zeile: tuple) -> tuple:
            return tuple(str(w) for w in zeile if isinstance(w, str))

        ist, soll = sorted(ist, key=schluessel), sorted(soll, key=schluessel)
    return all(_gleich(a, b) for zeile_ist, zeile_soll in zip(ist, soll, strict=True) for a, b in zip(zeile_ist, zeile_soll, strict=True))


def _artefakt(datensatz: str, faelle: list[Fall]) -> Artefakt:
    """Das echte Artefakt des Datensatzes, aber mit den KPIs aus dem Testset."""
    daten = yaml.safe_load((ARTEFAKTE / datensatz / "artefakt.yaml").read_text(encoding="utf-8"))
    daten["kpis"] = [{"name": f.name, "beschreibung": f.beschreibung} for f in faelle]
    return Artefakt.aus_dict(daten)


def _neue_zeilen(protokoll: Path, ab: int) -> list[dict]:
    if not protokoll.exists():
        return []
    return [json.loads(z) for z in protokoll.read_text(encoding="utf-8").splitlines()[ab:] if z.strip()]


def _anzahl_zeilen(protokoll: Path) -> int:
    return len(protokoll.read_text(encoding="utf-8").splitlines()) if protokoll.exists() else 0


def messe(llm, faelle: list[Fall], ordner: Path, protokoll: Path = PROTOKOLL, ausgabe=print) -> list[dict]:
    """Misst alle Fälle mit dem übergebenen llm und liefert je Fall ein Ergebnis-Dict (Spalten wie SPALTEN_CSV)."""
    daten = testdaten.schreibe_alle(ordner)
    ergebnisse: list[dict] = []
    for datensatz in dict.fromkeys(f.datensatz for f in faelle):  # Reihenfolge wie im Testset
        eigene = [f for f in faelle if f.datensatz == datensatz]
        artefakt = _artefakt(datensatz, eigene)
        db = ordner / f"{datensatz}.db"
        schema = schritt1_datenmodell.ausfuehren(artefakt, daten[datensatz], db, ueberschreiben=True)
        beschreibungen = {s.name: s.typ + (f", {s.beschreibung}" if s.beschreibung else "") for s in artefakt.spalten}
        datumsspalten = [s.name for s in artefakt.spalten if s.typ == "datum"]
        for fall, kpi in zip(eigene, artefakt.kpis, strict=True):
            vorher = _anzahl_zeilen(protokoll)
            start = time.perf_counter()
            sql, fehler, ist = "", "", ""
            try:
                sql = erzeuge_sql(
                    kpi, schema, artefakt.tabelle, llm, db, beschreibungen=beschreibungen, datumsspalten=datumsspalten
                )
                _, zeilen = fuehre_aus(sql, db)
                ist = str(zeilen[:3])[:200]
                if fall.referenz is None:
                    ergebnis, fehler = "falsch", "nicht berechenbar, hätte abgelehnt werden müssen"
                else:
                    ergebnis = "richtig" if vergleiche(zeilen, fuehre_aus(fall.referenz, db)[1], fall.reihenfolge) else "falsch"
            except SqlFehler as f:
                fehler = "; ".join(f.meldungen)
                abgelehnt = "nicht berechenbar" in fehler
                ergebnis = ("richtig" if fall.referenz is None else "abgelehnt") if abgelehnt else "abbruch"
            except LLMFehler as f:
                ergebnis, fehler = "abbruch", str(f)
            aufrufe = [z for z in _neue_zeilen(protokoll, vorher) if z.get("art") == "aufruf"]
            ergebnisse.append({
                "zeit": datetime.now().isoformat(timespec="seconds"),
                "lauf": getattr(llm, "lauf", None),
                "modell": getattr(llm, "modell", None),
                "fallback": getattr(llm, "fallback_modell", None) or "",
                "datensatz": datensatz,
                "kpi": fall.name,
                "schwierigkeit": fall.schwierigkeit,
                "ergebnis": ergebnis,
                "versuche": len(aufrufe),
                "eskaliert": any(z.get("fallback") for z in aufrufe),
                "tokens_in": sum(z.get("tokens_in") or 0 for z in aufrufe),
                "tokens_out": sum(z.get("tokens_out") or 0 for z in aufrufe),
                "dauer_s": round(time.perf_counter() - start, 1),
                "sql": sql,
                "fehler": fehler,
                "ist": ist,
            })
            ausgabe(f"  {ergebnis:<9} {fall.name}  ({len(aufrufe)} Aufruf(e), {ergebnisse[-1]['dauer_s']} s)")
    return ergebnisse


def zusammenfassung(ergebnisse: list[dict]) -> str:
    gesamt = Counter(e["ergebnis"] for e in ergebnisse)
    je_stufe = {
        stufe: (sum(1 for e in ergebnisse if e["schwierigkeit"] == stufe and e["ergebnis"] == "richtig"),
                sum(1 for e in ergebnisse if e["schwierigkeit"] == stufe))
        for stufe in ("einfach", "mittel", "schwer")
    }
    stufen = ", ".join(f"{s} {r}/{n}" for s, (r, n) in je_stufe.items() if n)
    rein = f"{sum(e['tokens_in'] for e in ergebnisse):,}".replace(",", ".")
    raus = f"{sum(e['tokens_out'] for e in ergebnisse):,}".replace(",", ".")
    return (
        f"{gesamt['richtig']} von {len(ergebnisse)} richtig ({stufen}); "
        f"falsch {gesamt['falsch']}, Abbruch {gesamt['abbruch']}, fälschlich abgelehnt {gesamt['abgelehnt']}; "
        f"Tokens {rein} rein / {raus} raus; {sum(e['dauer_s'] for e in ergebnisse):.0f} s"
    )


def speichere(ergebnisse: list[dict], ziel: Path = ERGEBNIS_CSV) -> None:
    neu = not ziel.exists()
    ziel.parent.mkdir(parents=True, exist_ok=True)
    with ziel.open("a", encoding="utf-8", newline="") as datei:
        schreiber = csv.DictWriter(datei, fieldnames=SPALTEN_CSV, delimiter=";")
        if neu:
            schreiber.writeheader()
        schreiber.writerows(ergebnisse)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Misst Schritt 2 auf dem Testset (tools/testset_sql.py).")
    parser.add_argument("--modell", required=True, help="Hauptmodell, z. B. qwen3:8b")
    parser.add_argument("--fallback", default="", help="Fallback-Modell für die Eskalation; ohne Angabe: keine Eskalation")
    parser.add_argument("--fall", default="", help="nur Fälle, deren Name diesen Text enthält")
    argumente = parser.parse_args(argv)
    faelle = [f for f in TESTSET if argumente.fall.lower() in f.name.lower()]
    if not faelle:
        print(f"Kein Fall enthält '{argumente.fall}'.", file=sys.stderr)
        return 1
    kennung = f"{datetime.now():%Y-%m-%dT%H:%M:%S}_messung_{argumente.modell}"
    try:
        llm = LLM(modell=argumente.modell, fallback_modell=argumente.fallback, protokoll=PROTOKOLL, lauf=kennung)
    except LLMFehler as fehler:
        print(fehler, file=sys.stderr)
        return 1
    eskalation = f", Eskalation an {argumente.fallback}" if argumente.fallback else ", ohne Eskalation"
    print(f"Messung {kennung}: {len(faelle)} Fälle mit {argumente.modell}{eskalation}")
    ergebnisse = messe(llm, faelle, RUNS / "messung")
    speichere(ergebnisse)
    print(f"\n{argumente.modell}: {zusammenfassung(ergebnisse)}")
    print(f"Details: {ERGEBNIS_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
