---
name: Dashboard-Framework Frontend
description: Formblatt-System für Eingabe-App und Dashboard-Runner: beschriftete, nummerierte Felder in Haarlinien unter einem Schriftfeld.
colors:
  papier: "#F1F3F5"
  blatt: "#FFFFFF"
  tinte: "#1C2227"
  tinte-2: "#4A545D"
  linie: "#AEB7BF"
  haarlinie: "#DDE2E6"
  linie-stark: "#7C8791"
  produktfarbe: "#23579F"
  gueltig: "#1F6B40"
  gueltig-grund: "#E6F2EB"
  fehler: "#A3201A"
  fehler-grund: "#FBE9E7"
  hinweis: "#7A4E00"
  hinweis-grund: "#FFF4D6"
  offen-grund: "#EEF1F3"
typography:
  titel:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "26px"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "0.01em"
  feldtitel:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "21px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "0.01em"
  wert:
    fontFamily: "Barlow, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.25
  body:
    fontFamily: "Barlow, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.09em"
  kennzahl:
    fontFamily: "Barlow Condensed, Barlow, sans-serif"
    fontSize: "76px"
    fontWeight: 600
    lineHeight: 1
rounded:
  kante: "2px"
spacing:
  feld-innen: "16px"
  feld-abstand: "14px"
  schriftfeld-zelle: "10px 14px 12px"
components:
  schriftfeld:
    backgroundColor: "{colors.blatt}"
    textColor: "{colors.tinte}"
    rounded: "{rounded.kante}"
    padding: "{spacing.schriftfeld-zelle}"
  feld:
    backgroundColor: "{colors.blatt}"
    textColor: "{colors.tinte}"
    rounded: "{rounded.kante}"
    padding: "0 16px 16px"
  feldnummer:
    backgroundColor: "{colors.tinte}"
    textColor: "{colors.blatt}"
    typography: "{typography.label}"
    rounded: "1px"
    padding: "4px 7px 3px"
  marke-gueltig:
    backgroundColor: "{colors.gueltig-grund}"
    textColor: "{colors.gueltig}"
    typography: "{typography.label}"
    rounded: "{rounded.kante}"
    padding: "2px 9px 3px"
  marke-fehler:
    backgroundColor: "{colors.fehler-grund}"
    textColor: "{colors.fehler}"
    typography: "{typography.label}"
    rounded: "{rounded.kante}"
    padding: "2px 9px 3px"
  button-primary:
    backgroundColor: "{colors.produktfarbe}"
    textColor: "{colors.blatt}"
    rounded: "{rounded.kante}"
  button-secondary:
    backgroundColor: "{colors.blatt}"
    textColor: "{colors.tinte}"
    rounded: "{rounded.kante}"
---

# Design System: Dashboard-Framework Frontend

## Overview

**Creative North Star: "Das geprüfte Formblatt"**

Jede Oberfläche ist ein Blatt, das jemand geprüft hat: oben ein Schriftfeld, das sagt, was für ein Blatt das ist (Kunde, Datenstand, Zeilen, Datenzugriff, Prüfstand), darunter beschriftete, nummerierte Felder in Haarlinien. Das System ist ruhig und genau. Es lehnt sich an das Schriftfeld technischer Zeichnungen und an Formblätter an, ohne deren Papier nachzuahmen: keine Texturen, keine Schatten, keine Verläufe.

Dichte und Ton sind die eines Werkzeugs für Gelegenheitsnutzer ohne IT-Wissen. Die Oberfläche tritt hinter die Aufgabe zurück: bekannte Bedienelemente (Tabs, Eingabefelder, Knöpfe, Tabellen), klare Reihenfolge, Zustände mit Form und Text. Die Kundenfarbe ist Gast: Sie erscheint nur dort, wo der Kunde etwas "gehört" (aktiver Tab, Hauptaktion, Daten).

**Key Characteristics:**
- Schriftfeld als Kopf jeder Oberfläche, Felder mit Nummer und Haarlinien
- Eine Schriftfamilie (Barlow) plus Barlow Condensed für Beschriftungen, Titel und große Zahlen
- Fester heller Grund: Papier mit weißen Blättern
- Zustände immer mit Form und Text, nie nur Farbe
- Kundenfarbe reserviert: aktiver Tab, Hauptaktion, Datenebene

## Colors

Eine zurückhaltende, kühl getönte Palette aus Papier, Tinte und Haarlinien. Farbe erledigt Aufgaben: Zustand, Auswahl, Daten.

### Primary
- **Produktfarbe Bleistiftblau** (#23579F): Akzent der Eingabe-App und Rückfall im Runner, wenn der Kunde keine (gültige) Farbe angibt. Aktiver Tab, Hauptknopf, Fokusring.
- **Kundenfarbe** (Eingabe des Kunden, im Beispiel #1F3864): im Runner an Stelle der Produktfarbe. Als Textfarbe nur, wenn sie auf Weiß mindestens 4,5:1 erreicht; sonst bleibt die Schrift in Tinte und nur der Strich unter dem Tab trägt die Farbe.

### Neutral
- **Zeichenpapier** (#F1F3F5): Grund der Seite.
- **Blatt** (#FFFFFF): Schriftfeld, Felder, Eingabefelder.
- **Graphit-Tinte** (#1C2227): Text, Schriftfeld-Rahmen, Feldnummern.
- **Zweite Tintenstufe** (#4A545D): Beschriftungen, Bildunterschriften (7,9:1 auf Weiß).
- **Blattrand** (#AEB7BF) und **Haarlinie** (#DDE2E6): Rahmen von Feldern und Trennlinien, dekorativ.
- **Bedienelement-Linie** (#7C8791): Ränder von Eingabefeldern und Knöpfen (mindestens 3:1 gegen Weiß).

### Zustände
- **Gültig** (#1F6B40 auf #E6F2EB), **Fehler** (#A3201A auf #FBE9E7), **Hinweis** (#7A4E00 auf #FFF4D6), **Offen** (#4A545D auf #EEF1F3), **Übernommen** (wie gültig).

### Named Rules
**The Gast-Farbe Rule.** Die Kundenfarbe taucht nur im aktiven Tab, in der Hauptaktion und in der Datenebene auf. Nie als Fläche der Oberfläche.
**The Form-und-Text Rule.** Jeder Zustand hat Form (leeres Quadrat, volles Quadrat, Raute) und Text. Farbe allein trägt nie eine Aussage.

## Typography

**Display Font:** Barlow Condensed (mit Barlow, sans-serif)
**Body Font:** Barlow (mit sans-serif)

**Character:** Eine DIN-nahe, nüchterne Familie. Condensed in Versalien für Beschriftungen, sonst Condensed für Titel und die große Kennzahl; Zahlen immer tabellarisch.

### Hierarchy
- **Titel** (600, 26px, 1.15): Titel im Schriftfeld.
- **Feldtitel** (600, 21px, 1.1): Titelzeile jedes Felds.
- **Wert** (600, 18px, 1.25): Werte im Schriftfeld und in der Fußleiste.
- **Body** (400, 16 bis 17px, 1.5 bis 1.6): Fließtext; der Lesetext im Tab "Über dieses Dashboard" steht in höchstens 65 Zeichen Breite.
- **Label** (600, 12px, 0.09em, Versalien): Beschriftung über Werten im Schriftfeld und in der Fußleiste, nie über Überschriften.
- **Kennzahl** (600, 76px, 1): die eine große Zahl eines Felds.

### Named Rules
**The Eine-Skala Rule.** Hierarchie entsteht aus Größe und Gewicht innerhalb einer Familie, nicht aus zusätzlichen Schriften.

## Layout

Ein Blatt in höchstens 1280px Breite, 40px Seitenrand (14px auf dem Handy). Oben das Schriftfeld über die ganze Breite, darunter Tabs, darunter die Felder in zwei Spalten (Runner) oder untereinander (Eingabe). Felder halten 16px Innenabstand und 14px Abstand zwischen ihren Elementen; Titelzeile und Fußleiste laufen von Rand zu Rand. Auf schmalen Bildschirmen wird das Schriftfeld zweispaltig (der Titel über die volle Breite), die Felder stapeln sich, die Tabs scrollen.

## Elevation & Depth

Flach. Tiefe entsteht durch Papier-Grund gegen weiße Blätter und durch Linien, nie durch Schatten. Der Fokus bekommt einen 2px-Ring in der Akzentfarbe.

### Named Rules
**The Flach-Immer Rule.** Keine Schatten, keine Verläufe, kein Glas.

## Shapes

Fast eckig: 2px Eckenradius für Felder, Eingabefelder, Knöpfe und Marken; Feldnummern 1px. Rahmen sind Haarlinien (1px); nur das Schriftfeld trägt einen kräftigeren Rahmen (1,5px, Tinte).

## Components

### Schriftfeld
Gitter aus Zellen mit Trennlinien; erste Zelle trägt Titel (und Logo), die übrigen Beschriftung über Wert. Im Runner: Kunde, Datenstand, Zeilen, Datenzugriff ("nur lesend" als Zustandsmarke). In der Eingabe-App: Artefakt, Spalten, KPIs, Prüfung, Speicherort.

### Felder
- **Aufbau:** Titelzeile mit schwarzer Feldnummer und Feldtitel, Inhalt, optional Fußleiste (Berechnung, Sortierung, Ergebnis), die bündig mit dem unteren Rand abschließt.
- **Hauptaktion:** rechts unten im Feld.

### Buttons
- **Primary:** Akzentfarbe, Schrift in Weiß oder Tinte (nach Kontrast), 2px Radius; bei Hover 7 % dunkler (150ms).
- **Secondary:** weiß mit Linie in #7C8791.

### Zustandsmarke
Kleines Feld in Condensed-Versalien mit Rand in Textfarbe und gezeichneter Form: *offen* leeres Quadrat, *gültig/übernommen* volles Quadrat, *fehler* Raute, *hinweis* volles Quadrat auf Bernstein.

### Inputs / Fields
Weiß, Rand #7C8791, 2px Radius; Fokus: Rand und Ring in der Akzentfarbe. Fehlermeldungen stehen direkt unter dem Feld und gesammelt im Feld "Prüfung und Ergebnis".

### Navigation
Streamlit-Tabs: Condensed 18px, aktiver Tab in Akzentfarbe (Text nur bei ausreichendem Kontrast) mit 3px Strich, darunter eine 1px-Linie über die ganze Breite.

### Diagramme
Plotly auf Weiß: Haarlinien-Gitter, Balken und Linien in der Kundenfarbe, Werte an den Balken (bis 12 Balken), keine Werkzeugleiste, deutsche Zahlen.

## Do's and Don'ts

### Do:
- **Do** jede neue Oberfläche mit einem Schriftfeld beginnen und in nummerierte Felder gliedern, wenn die Reihenfolge oder ein Verweis ("Feld 3") Information trägt.
- **Do** Meldungen am betroffenen Feld und gesammelt zeigen, in einfachen Wörtern, mit Hinweis auf das, was zu tun ist.
- **Do** Zahlen deutsch schreiben (103,2; 300.000) und tabellarische Ziffern nutzen.
- **Do** Kontrast messen: Text mindestens 4,5:1, Ränder von Bedienelementen mindestens 3:1.

### Don't:
- **Don't** Streamlits Grau-mit-Farbakzent als Gestaltung gelten lassen.
- **Don't** farbige Seitenstreifen an Meldungen, Schatten, Verläufe oder Piktogramm-Zeichen als Icons verwenden.
- **Don't** eine Beschriftung über eine Überschrift setzen.
- **Don't** zwei Datenfarben für dieselbe Aussage verwenden: eine Kundenfarbe für alle Diagramme, außer ein Diagramm bekommt bewusst eine eigene.
- **Don't** fremde Texte ungeprüft in HTML oder CSS einsetzen (immer maskieren, Farben als #RRGGBB prüfen).
