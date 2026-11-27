"""Prüfschichten für generiertes SQL (US-05, ADR 0008). Alle ohne Sprachmodell.

Jede Prüfung wirft bei einem Problem SqlPruefFehler mit einer Meldung, die verständlich genug ist, um sie dem Modell
in der Reparaturschleife zurückzugeben. Die Reihenfolge der Anwendung legt Schritt 2 fest.
"""

from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path

import sqlglot
from dashboard_framework.models.spalten import aehnliche_spalte
from dashboard_framework.runner.sicherheit import verbinde_nur_lesend
from sqlglot import exp

ZEITLIMIT_S = 10  # so lange darf ein SQL bei der Prüfung höchstens laufen; schützt vor Abfragen, die nie fertig werden


class SqlPruefFehler(ValueError):
    """Das SQL besteht eine Prüfschicht nicht. Der Text wird dem Modell als Fehlermeldung zurückgegeben."""


def zerlege(sql: str) -> exp.Expression:
    """Zerlegt das SQL im SQLite-Dialekt. Nicht lesbares SQL ist ein Fehler."""
    try:
        baum = sqlglot.parse_one(sql, read="sqlite")
    except sqlglot.errors.ParseError as fehler:
        erste_zeile = str(fehler).splitlines()[0] if str(fehler) else "unbekannter Fehler"
        raise SqlPruefFehler(f"Das SQL ist kein gültiges SQLite: {erste_zeile}") from None
    if baum is None:
        raise SqlPruefFehler("Das SQL ist leer")
    return baum


def _eigene_namen(baum: exp.Expression) -> set[str]:
    """Namen, die das SQL selbst vergibt (Spaltenaliase mit AS, Namen von WITH-Teilabfragen). Sie sind keine Tabellenspalten."""
    namen = {a.alias.lower() for a in baum.find_all(exp.Alias) if a.alias}
    namen |= {c.alias.lower() for c in baum.find_all(exp.CTE) if c.alias}
    return namen


def verwendete_spalten(baum: exp.Expression) -> set[str]:
    """Alle Spaltennamen, auf die das SQL zugreift (kleingeschrieben). Kann eigene Aliase enthalten, z. B. in ORDER BY."""
    return {c.name.lower() for c in baum.find_all(exp.Column) if c.name}


def pruefe_tabelle(baum: exp.Expression, tabelle: str) -> None:
    """Nur die Tabelle des Artefakts darf vorkommen (WITH-Teilabfragen zählen nicht als Tabelle)."""
    teilabfragen = {c.alias.lower() for c in baum.find_all(exp.CTE) if c.alias}
    fremd = sorted({t.name for t in baum.find_all(exp.Table) if t.name and t.name.lower() not in teilabfragen | {tabelle.lower()}})
    if fremd:
        raise SqlPruefFehler(f"Unbekannte Tabelle(n): {', '.join(fremd)} – erlaubt ist nur die Tabelle {tabelle}")


def pruefe_bedeutung(sql: str, erlaubte_spalten: set[str]) -> None:
    """US-05.2: Das SQL verwendet nur bekannte Spalten. Eine unbekannte Spalte wird mit ihrem Namen gemeldet."""
    erlaubt = {s.lower() for s in erlaubte_spalten}
    baum = zerlege(sql)
    # Eigene Aliase (z. B. "ORDER BY summe" nach "SUM(x) AS summe") sind keine Tabellenspalten und deshalb erlaubt.
    unbekannt = sorted(verwendete_spalten(baum) - erlaubt - _eigene_namen(baum))
    if unbekannt:
        hinweise = []
        for name in unbekannt:
            vorschlag = aehnliche_spalte(name, sorted(erlaubte_spalten))
            hinweise.append(f"{name} (meinten Sie `{vorschlag}`?)" if vorschlag else name)
        raise SqlPruefFehler(
            f"Unbekannte Spalte(n): {', '.join(hinweise)} – erlaubt sind: {', '.join(sorted(erlaubte_spalten))}"
        )


def _ist_alias_verweis(spalte: exp.Column) -> bool:
    """True, wenn der Name nur auf einen Alias derselben Abfrage zeigt, z. B. 'umsatz' in
    'SELECT COUNT(*) AS umsatz ... ORDER BY umsatz'. Steht der Name im Ausdruck eines Alias selbst
    ('SUM(umsatz) AS umsatz'), ist es die echte Tabellenspalte."""
    if spalte.table:
        return False  # absatz.umsatz ist immer die Tabellenspalte
    naechstes = spalte.find_ancestor(exp.Alias, exp.Select)
    if not isinstance(naechstes, exp.Select):
        return False  # liegt im Ausdruck eines Alias (oder außerhalb einer Abfrage)
    aliase = {a.alias.lower() for a in naechstes.expressions if isinstance(a, exp.Alias) and a.alias}
    return spalte.name.lower() in aliase


def echte_spalten(baum: exp.Expression) -> set[str]:
    """Spaltennamen, die wirklich aus der Tabelle gelesen werden (kleingeschrieben), ohne bloße Verweise auf eigene Aliase."""
    return {c.name.lower() for c in baum.find_all(exp.Column) if c.name and not _ist_alias_verweis(c)}


def pruefe_anker(sql: str, anker: list[str]) -> None:
    """Die Spalten, die in der KPI-Beschreibung in Backticks stehen, müssen im SQL vorkommen.
    Fängt den Fall ab, dass das Modell die genannte Spalte ignoriert und etwas anderes berechnet.
    Ein Alias mit demselben Namen zählt nicht ('COUNT(*) AS umsatz ... ORDER BY umsatz' liest umsatz nie)."""
    verwendet = echte_spalten(zerlege(sql))
    fehlend = [a for a in anker if a.lower() not in verwendet]
    if fehlend:
        raise SqlPruefFehler(f"Die KPI beruht auf der Spalte bzw. den Spalten {', '.join(fehlend)}, das SQL verwendet sie nicht")


def _kern(ausdruck: exp.Expression) -> str:
    """Normalisiert einen Ausdruck für den Vergleich: Klammern, CAST(... AS ...) und NULLIF(..., 0) zählen nicht."""
    while isinstance(ausdruck, (exp.Paren, exp.Cast, exp.Nullif)):
        ausdruck = ausdruck.this
    return ausdruck.sql(dialect="sqlite").lower()


def pruefe_keine_selbstdivision(sql: str) -> None:
    """Zähler und Nenner einer Division dürfen nicht derselbe Ausdruck sein: das Ergebnis wäre immer 1.

    Fängt einen typischen Denkfehler bei Vergleichen zweier Zeiträume ab (z. B. Vormonat geteilt durch Vormonat).
    Andere inhaltliche Rechenfehler findet diese Prüfung nicht (ADR 0008).
    """
    for division in zerlege(sql).find_all(exp.Div):
        if _kern(division.left) == _kern(division.right):
            raise SqlPruefFehler(
                f"Das SQL teilt einen Ausdruck durch sich selbst ({division.left.sql(dialect='sqlite')}), das Ergebnis ist immer 1. "
                "Bei einem Vergleich zweier Zeiträume müssen Zähler und Nenner verschiedene Zeiträume abdecken (siehe Regel 7)"
            )


_SYSTEMZEIT = (exp.CurrentDate, exp.CurrentTime, exp.CurrentTimestamp)


def pruefe_einzelwert(sql: str) -> None:
    """Ein einzelner Wert (äußerste Abfrage ohne GROUP BY, nur Aggregate) hat genau eine Ergebnisspalte.

    Der Runner zeigt bei einer Kennzahl die erste Spalte. Liefert die Abfrage zusätzlich Hilfswerte, etwa den Umsatz
    des Vormonats vor der eigentlichen Quote, stünde der falsche Wert im Dashboard (Probeläufe 7 und 10, ADR 0008).
    Abfragen mit Gruppierung oder mit Spalten ohne Aggregat (z. B. Bezeichnung plus Wert) betrifft das nicht.
    """
    baum = zerlege(sql)
    if not isinstance(baum, exp.Select) or baum.args.get("group") or len(baum.expressions) < 2:
        return
    if all(ausdruck.find(exp.AggFunc) for ausdruck in baum.expressions):
        namen = ", ".join(a.alias_or_name or a.sql(dialect="sqlite") for a in baum.expressions)
        raise SqlPruefFehler(
            f"Die Abfrage berechnet einen einzelnen Wert, liefert aber {len(baum.expressions)} Spalten ({namen}). "
            "Das Dashboard zeigt davon nur die erste. Gib genau eine Spalte zurück: den Wert, den die KPI beschreibt"
        )


def pruefe_ohne_systemzeit(sql: str) -> None:
    """Das SQL darf das heutige Datum nicht verwenden ('now', CURRENT_DATE, CURRENT_TIME, CURRENT_TIMESTAMP).

    Sonst hinge das Ergebnis vom Kalender ab statt von den Daten: nicht wiederholbar, und bei verspätet hochgeladenen
    Daten bliebe die Kachel leer. Zeitbezüge wie "aktuell" oder "Vormonat" beziehen sich auf die Daten (ADR 0008).
    """
    baum = zerlege(sql)
    systemzeit = any(isinstance(knoten, _SYSTEMZEIT) for knoten in baum.walk())
    now = any(lit.is_string and lit.this.strip().lower() == "now" for lit in baum.find_all(exp.Literal))
    if systemzeit or now:
        raise SqlPruefFehler(
            "Das SQL verwendet das heutige Datum ('now' bzw. CURRENT_DATE/CURRENT_TIMESTAMP). Zeitbezüge wie 'aktuell' "
            "oder 'Vormonat' müssen sich auf den jüngsten Wert der Datumsspalte in den Daten beziehen (siehe Regel 7)"
        )


def fuehre_aus(sql: str, db_pfad: str | Path, zeitlimit_s: float = ZEITLIMIT_S) -> tuple[list[str], list[tuple]]:
    """Führt das SQL schreibgeschützt aus und liefert (Spaltennamen, Zeilen). Fehler von SQLite werden zur Meldung.

    Läuft das SQL länger als zeitlimit_s, bricht SQLite es ab (z. B. eine Teilabfrage ohne Ende oder eine
    Verknüpfung der Tabelle mit sich selbst). Sonst bliebe die Pipeline an dieser Stelle hängen.
    """
    verbindung = verbinde_nur_lesend(db_pfad)
    ende = time.monotonic() + zeitlimit_s
    verbindung.set_progress_handler(lambda: 1 if time.monotonic() > ende else 0, 10_000)  # 1 = abbrechen
    try:
        cursor = verbindung.execute(sql)
        spalten = [d[0] for d in cursor.description or []]
        return spalten, cursor.fetchall()
    except sqlite3.Error as fehler:
        if time.monotonic() > ende:
            raise SqlPruefFehler(
                f"Das SQL lief länger als {zeitlimit_s:g} Sekunden und wurde abgebrochen. Schreibe eine einfachere Abfrage "
                "ohne Verknüpfung der Tabelle mit sich selbst und ohne rekursive Teilabfrage"
            ) from None
        raise SqlPruefFehler(f"SQLite meldet beim Ausführen: {fehler}") from None
    finally:
        verbindung.close()


def pruefe_ausfuehrbar(sql: str, db_pfad: str | Path) -> tuple[list[str], list[tuple]]:
    """Das SQL läuft auf den echten Daten und liefert mindestens eine Zeile."""
    spalten, zeilen = fuehre_aus(sql, db_pfad)
    if not spalten:
        raise SqlPruefFehler("Das SQL liefert keine Ergebnisspalten")
    if not zeilen:
        raise SqlPruefFehler("Das SQL liefert keine Zeilen – prüfe Filter und Bedingungen")
    leer = sum(1 for zeile in zeilen if zeile[-1] is None)
    if leer:
        raise SqlPruefFehler(
            f"Der berechnete Wert (letzte Spalte) ist in {leer} von {len(zeilen)} Zeilen leer (NULL). Prüfe, ob sich "
            "Bedingungen gegenseitig ausschließen, z. B. ein WHERE oder GROUP BY auf einen Zeitraum und ein CASE auf "
            "einen anderen. Berechne die KPI so, dass jede Zeile einen echten Wert hat"
        )
    return spalten, zeilen


# Zeiträume, wie Schritt 1 sie speichert und strftime sie liefert: JJJJ, JJJJ-MM, JJJJ-MM-TT, optional mit Uhrzeit
_ZEITRAUM = re.compile(r"^\d{4}(-\d{2}(-\d{2}( \d{2}:\d{2}(:\d{2})?)?)?)?$")


def pruefe_zeitreihe_aufsteigend(spalten: list[str], zeilen: list[tuple]) -> None:
    """Ist die erste Ergebnisspalte ein Zeitraum, muss sie aufsteigend sortiert sein (ältester zuerst).

    Das Dashboard zeichnet die Werte in der gelieferten Reihenfolge; absteigend liefe ein Verlauf rückwärts.
    Ergebnisse, deren erste Spalte kein Zeitraum ist (z. B. Ranglisten), betrifft das nicht.
    """
    erste = [zeile[0] for zeile in zeilen]
    if len(erste) < 2 or not all(isinstance(w, str) and _ZEITRAUM.match(w) for w in erste):
        return
    if erste != sorted(erste):
        raise SqlPruefFehler(
            f"Die Zeiträume in der ersten Spalte ({spalten[0]}) sind nicht aufsteigend sortiert. "
            "Verläufe über die Zeit müssen mit dem ältesten Zeitraum beginnen (ORDER BY ... ASC)"
        )


def pruefe_plausibilitaet(sql: str, db_pfad: str | Path, erwartet: dict[str, float], toleranz: float = 0.01) -> None:
    """US-05.3 (Testorakel): Vergleicht das Ergebnis mit bekannten Referenzwerten.

    Zeilen mit zwei oder mehr Spalten werden als {erste Spalte: zweite Spalte} gelesen. Ein Ergebnis aus genau einer
    Zahl hat den Schlüssel "wert". toleranz ist relativ (0.01 = 1 %). In der Pipeline gibt es keine Referenzwerte;
    die Prüfung greift dort nur, wenn welche übergeben werden.
    """
    spalten, zeilen = fuehre_aus(sql, db_pfad)
    if len(spalten) == 1 and len(zeilen) == 1:
        ist = {"wert": zeilen[0][0]}
    else:
        ist = {str(z[0]): z[1] for z in zeilen if len(z) >= 2}
    abweichungen = []
    for schluessel, soll in erwartet.items():
        wert = ist.get(schluessel)
        if wert is None:
            abweichungen.append(f"{schluessel} fehlt im Ergebnis")
        elif not isinstance(wert, (int, float)):
            abweichungen.append(f"{schluessel}: '{wert}' ist keine Zahl")
        elif abs(wert - soll) > toleranz * max(abs(soll), 1e-9):
            abweichungen.append(f"{schluessel}: {wert} statt erwartet {soll}")
    if abweichungen:
        raise SqlPruefFehler("Das Ergebnis passt nicht zu den Referenzwerten: " + "; ".join(abweichungen))
