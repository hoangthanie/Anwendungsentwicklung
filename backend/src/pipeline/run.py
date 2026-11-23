"""Ein Aufruf erzeugt aus Artefakt und CSV das vollständige Dashboard-Paket (PSP 5.7, US-08).

Zwei Wege, derselbe Ablauf:
- im Programm, z. B. hinter einem Knopf im Frontend:  pipeline(artefakt_ordner, csv_pfad, ausgabe) -> Ordner des Pakets
- im Terminal:  dashframe-run <artefakt_ordner> <daten.csv> [--ausgabe ausgabe] [--ueberschreiben]

Das Paket ist der Ordner, den der Runner braucht (lokal und auf dem Raspberry Pi unter /srv/dashboards/aktuell):
  <ausgabe>/<name>/dashboard.json   Konfiguration, enthält auch die Beschreibung für den Tab "Über dieses Dashboard"
  <ausgabe>/<name>/daten.db         die geprüften Daten
  <ausgabe>/<name>/README.md        dieselbe Beschreibung als Datei
  <ausgabe>/<name>/<logo>           falls im Artefakt hinterlegt

Keine halben Pakete: Das Paket entsteht in einem Arbeitsordner und wird erst ganz am Ende an seinen Platz verschoben.
Scheitert ein Schritt, bleibt nichts Halbfertiges liegen, und ein vorhandenes Paket ist unverändert.
Jeder Fehler wird zu PipelineFehler: welcher Schritt, welche Gründe, was der Anwender tun kann.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from dashboard_framework.harness.dashboard import DashboardFehler, erzeuge_config
from dashboard_framework.models.artefakt import Artefakt, ArtefaktFehler

from pipeline.harness.llm import LLM, LLMFehler
from pipeline.schritte import schritt1_datenmodell, schritt2_query
from pipeline.schritte.schritt1_datenmodell import SchemaFehler
from pipeline.schritte.schritt2_query import SqlFehler
from pipeline.schritte.schritt4_doku import erzeuge_doku

DB_NAME = "daten.db"
SCHRITTE = 4

# Was der Anwender je nach fehlgeschlagenem Schritt tun kann
HINWEIS_ARTEFAKT = "Korrigieren Sie die Angaben im Eingabeformular, speichern Sie das Artefakt und starten Sie erneut."
HINWEIS_DATEN = "Die Datei passt nicht zur Spaltenbeschreibung im Artefakt. Korrigieren Sie die Datei oder die Spalten und starten Sie erneut."
HINWEIS_SQL = (
    "Formulieren Sie die genannte(n) Kennzahl(en) eindeutiger: welche Spalte, welcher Zeitraum, welche Rechnung. "
    "Starten Sie dann erneut."
)
HINWEIS_DASHBOARD = "Starten Sie erneut. Tritt der Fehler wieder auf, vereinfachen Sie die Kennzahlen."
HINWEIS_MODELL = "Prüfen Sie, ob Ollama läuft und die Modelle installiert sind, und starten Sie erneut."


class PipelineFehler(RuntimeError):
    """Die Pipeline hat kein Paket erzeugt.

    schritt:   welcher Schritt gescheitert ist, in Worten (z. B. "Schritt 2 von 4: Kennzahlen berechnen")
    meldungen: alle Gründe, jeder verständlich formuliert
    hinweis:   was der Anwender tun kann
    Ein Frontend zeigt die drei Felder in seiner Gestaltung an; das Terminal gibt als_text() aus.
    """

    def __init__(self, schritt: str, meldungen: list[str] | str, hinweis: str = ""):
        self.schritt = schritt
        self.meldungen = [meldungen] if isinstance(meldungen, str) else list(meldungen)
        self.hinweis = hinweis
        super().__init__(f"{schritt}: " + "; ".join(self.meldungen))

    def als_text(self) -> str:
        zeilen = ["Es wurde kein Dashboard erzeugt.", f"Fehlgeschlagen: {self.schritt}"]
        zeilen += [f"  - {m}" for m in self.meldungen]
        if self.hinweis:
            zeilen.append(f"Was tun: {self.hinweis}")
        return "\n".join(zeilen)


def _schritt(nr: int, name: str) -> str:
    return f"Schritt {nr} von {SCHRITTE}: {name}"


def lauf_kennung(name: str, zeit: datetime | None = None) -> str:
    """Kennung eines Laufs für das Run-Protokoll, z. B. 2026-11-23T21:50:12_sales."""
    return f"{(zeit or datetime.now()):%Y-%m-%dT%H:%M:%S}_{name}"


def pipeline(
    artefakt_ordner: str | Path,
    csv_pfad: str | Path,
    ausgabe: str | Path = "ausgabe",
    llm=None,
    ueberschreiben: bool = False,
    fortschritt: Callable[[str], None] | None = None,
) -> Path:
    """US-08.1: Führt die Schritte 1 bis 4 aus und liefert den Ordner des fertigen Pakets (<ausgabe>/<name>).

    artefakt_ordner: Ordner mit artefakt.yaml und ggf. Logo (so speichert ihn die Eingabe-App).
    llm:             ohne Angabe LLM() mit den Einstellungen aus backend/.env; für Tests ein Fake.
    ueberschreiben:  ein vorhandenes Paket gleichen Namens ersetzen (erst, wenn das neue fertig ist).
    fortschritt:     wird vor jedem Schritt mit einem kurzen Text aufgerufen, z. B. für eine Statusanzeige.
    Wirft PipelineFehler; es entsteht dann kein Paket, und ein vorhandenes bleibt unverändert.
    """
    melde = fortschritt or (lambda text: None)
    ordner, csv, ausgabe = Path(artefakt_ordner), Path(csv_pfad), Path(ausgabe)

    # Alles, was ohne Sprachmodell prüfbar ist, zuerst: Ein Fehler hier kostet keine Minute Rechenzeit (US-08.2).
    try:
        artefakt = Artefakt.aus_yaml(ordner / "artefakt.yaml")
    except ArtefaktFehler as fehler:
        raise PipelineFehler("Artefakt prüfen", fehler.meldungen, HINWEIS_ARTEFAKT) from None
    logo = ordner / artefakt.branding.logo if artefakt.branding.logo else None
    if logo and Path(artefakt.branding.logo).name != artefakt.branding.logo:  # nur ein Dateiname, kein Pfad (US-13)
        raise PipelineFehler("Artefakt prüfen", "Das Logo muss als Dateiname ohne Ordner angegeben sein", HINWEIS_ARTEFAKT)
    if logo and not logo.is_file():
        raise PipelineFehler("Artefakt prüfen", f"Die Logo-Datei {logo.name} fehlt im Ordner {ordner}", HINWEIS_ARTEFAKT)
    if not csv.is_file():
        raise PipelineFehler(_schritt(1, "Daten prüfen und laden"), f"Datendatei nicht gefunden: {csv}", "Prüfen Sie den Pfad zur Datei.")
    ziel = ausgabe / artefakt.name
    if ziel.exists() and not ueberschreiben:
        raise PipelineFehler(
            "Paket speichern",
            f"Es gibt bereits ein Dashboard-Paket in {ziel}",
            "Bestätigen Sie das Überschreiben (im Terminal: --ueberschreiben) oder wählen Sie einen anderen Ausgabeordner.",
        )
    if llm is None:
        try:
            llm = LLM()
        except LLMFehler as fehler:
            raise PipelineFehler("Sprachmodell", str(fehler), HINWEIS_MODELL) from None
    if hasattr(llm, "lauf"):
        llm.lauf = lauf_kennung(artefakt.name)  # alle Protokollzeilen dieses Laufs tragen dieselbe Kennung

    ausgabe.mkdir(parents=True, exist_ok=True)
    arbeit = Path(tempfile.mkdtemp(prefix=f".{artefakt.name}_entsteht_", dir=ausgabe))  # gleiches Laufwerk: Verschieben ist sofort fertig
    db = arbeit / DB_NAME
    schritt = "Vorbereitung"
    try:
        schritt = _schritt(1, "Daten prüfen und laden")
        melde(schritt)
        schema = schritt1_datenmodell.ausfuehren(artefakt, csv, db)

        schritt = _schritt(2, "Kennzahlen berechnen")
        melde(f"{schritt} (Sprachmodell, kann einige Minuten dauern)")
        sql_je_kpi = schritt2_query.ausfuehren(artefakt, schema, db, llm)

        schritt = _schritt(3, "Darstellung wählen")
        melde(schritt)
        config = erzeuge_config(artefakt, sql_je_kpi, llm, db_pfad=DB_NAME)
        if logo:
            shutil.copy2(logo, arbeit / artefakt.branding.logo)

        schritt = _schritt(4, "Beschreibung erstellen")
        melde(schritt)
        doku = erzeuge_doku(artefakt, sql_je_kpi, llm, config=config, db_pfad=db, quelle=csv.name)
        config = config.model_copy(update={"doku": doku})  # erscheint im Dashboard im Tab "Über dieses Dashboard"
        config.speichern(arbeit / "dashboard.json")
        (arbeit / "README.md").write_text(doku, encoding="utf-8")

        _einsetzen(arbeit, ziel)
    except SchemaFehler as fehler:
        raise PipelineFehler(schritt, fehler.meldungen, HINWEIS_DATEN) from None
    except SqlFehler as fehler:
        raise PipelineFehler(schritt, fehler.meldungen, HINWEIS_SQL) from None
    except DashboardFehler as fehler:
        raise PipelineFehler(schritt, fehler.meldungen, HINWEIS_DASHBOARD) from None
    except LLMFehler as fehler:
        raise PipelineFehler(f"{schritt} (Sprachmodell)", str(fehler), HINWEIS_MODELL) from None
    finally:
        shutil.rmtree(arbeit, ignore_errors=True)  # nach Erfolg schon verschoben; nach einem Fehler: Reste weg
    melde(f"Fertig: {ziel}")
    return ziel


def _einsetzen(arbeit: Path, ziel: Path) -> None:
    """Setzt das fertige Paket an seinen Platz. Ein altes Paket wird erst zur Seite gelegt und nach Erfolg gelöscht."""
    alt = ziel.with_name(f".{ziel.name}_alt")
    shutil.rmtree(alt, ignore_errors=True)
    if ziel.exists():
        ziel.rename(alt)
    try:
        arbeit.rename(ziel)
    except OSError:
        if alt.exists():
            alt.rename(ziel)  # zurück: das alte Paket bleibt erhalten
        raise
    shutil.rmtree(alt, ignore_errors=True)


def main(argv: list[str] | None = None, llm=None) -> int:
    """Befehl dashframe-run (US-08.2). Rückgabe 0 = Paket erzeugt, 1 = Fehler (Meldung auf stderr)."""
    parser = argparse.ArgumentParser(
        prog="dashframe-run",
        description="Erzeugt aus Artefakt und CSV ein fertiges Dashboard-Paket (dashboard.json, daten.db, README.md).",
    )
    parser.add_argument("artefakt_ordner", type=Path, help="Ordner mit artefakt.yaml, z. B. ../frontend/artefakte/sales")
    parser.add_argument("csv", type=Path, help="Datendatei (CSV)")
    parser.add_argument("--ausgabe", type=Path, default=Path("ausgabe"), help="Zielordner, darin entsteht <name>/ (Standard: ausgabe)")
    parser.add_argument("--ueberschreiben", action="store_true", help="vorhandenes Paket gleichen Namens ersetzen")
    argumente = parser.parse_args(argv)
    try:
        ziel = pipeline(
            argumente.artefakt_ordner,
            argumente.csv,
            argumente.ausgabe,
            llm=llm,
            ueberschreiben=argumente.ueberschreiben,
            fortschritt=lambda text: print(text, flush=True),
        )
    except PipelineFehler as fehler:
        print(fehler.als_text(), file=sys.stderr)
        return 1
    print(f"\nAnsehen (im Ordner frontend):\n  DASHBOARD_CONFIG={(ziel / 'dashboard.json').resolve()} streamlit run src/dashboard_framework/runner/app.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
