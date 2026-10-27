---
version: 1
slug: "src-dashboard-framework-runner-app-py"
primary_target: "src/dashboard_framework/runner/app.py"
related_targets: ["src/dashboard_framework/eingabe/app.py"]
---

# Surface brief: Eingabe-App und Dashboard-Runner

Scope und Modus: Operate. Zwei Streamlit-Oberflächen desselben Frameworks: die Eingabe-App (Formular, erzeugt artefakt.yaml) und der Dashboard-Runner (Anzeige, Dokumentation, Daten-Upload).

Zielgruppe, Aufgabe, Beweise: Fachanwender ohne IT-Wissen am Büro-Laptop oder im Pi-Browser (Referenz: Vertriebsleitung eines mittelständischen Herstellers). Aufgabe Eingabe-App: Dashboard beschreiben und Fehler früh verstehen. Aufgabe Runner: Zahlen lesen, Herkunft nachvollziehen, neue CSV sicher einspielen. Echter Inhalt: Demo-Dashboard (Muster GmbH, synthetische Daten), Beispiel-Artefakte.

Grenzen: Streamlit (Theme, CSS, HTML-Blöcke, keine eigenen JS-Komponenten). Schriften lokal ausliefern (Pi ohne Internet). Deutsche Texte, Funktionen, Reihenfolge der Abschnitte und Meldungen bleiben. Kundenfarbe nur Akzent im Runner.

Gewählte Richtung: Formblatt (DIN-Schriftfeld und Formblattwesen), Wurf seed:40228cf084939b81. Unvollständig entschieden: genaue Schriftdateien, wie weit sich Streamlit-Widgets stylen lassen (Inspektion am gerenderten Ergebnis).

## Direction contract

THESIS: Jede Oberfläche ist ein geprüftes Formblatt: beschriftete, nummerierte Felder mit Haarlinien und ein Schriftfeld als Kopf. Verweigert wird das graue Standard-Streamlit mit Farbakzent und verspielten Karten.

OWN-WORLD: Zeichenpapier (#F1F3F5) mit weißen Blättern, Graphit-Tinte (#1C2227), Haarlinien (#AEB7BF, #DDE2E6), Zustandsfarben Grün/Rot/Bernstein nur mit Bedeutung. Eine Schriftfamilie (Barlow) plus Barlow Condensed für Feldbezeichnungen in Versalien, Feldtitel und große Kennzahlen; tabellarische Ziffern. Kundenfarbe reserviert: aktiver Tab, Hauptaktion, Datenebene.

STORY: Die Anwenderin sieht sofort, was das Blatt ist (Kunde, Datenstand, Zeilen, nur lesend), liest die Felder der Reihe nach und erkennt an festen Zustandsmarken, ob etwas offen, gültig, fehlerhaft oder übernommen ist.

FIRST VIEWPORT: Oben ein Schriftfeld über die volle Breite (Logo, Dashboard, Kunde, Datenstand, Zeilen, Datenzugriff, Prüfstatus), darunter die Tabs, darunter zwei Spalten nummerierter Felder (1 bis 4) mit Titelzeile, Diagramm und Fußzeile (Darstellung, Ergebnis). Hauptaktion rechts unten im Feld, in der Kundenfarbe.

FORM: Formblatt/DIN-Schriftfeld, Platz 3 meiner geordneten Liste, seed:40228cf084939b81.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
