# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Bestehende Codebasis: Python mit Streamlit (zwei getrennte Streamlit-Apps im Paket `dashboard_framework`). Die Oberfläche bleibt Streamlit; Gestaltung geschieht über Theme-Einstellungen (`.streamlit/config.toml`), eingebettetes CSS und Streamlit-eigene Komponenten.

## Users

- **Fachanwender ohne IT-Wissen** (Referenzfall: Vertriebsleitung eines mittelständischen Herstellers). Sie beschreiben ihr Dashboard im Eingabeformular und lesen später das fertige Dashboard. Sie arbeiten am Büro-Laptop oder im Browser auf dem Raspberry Pi und haben kein Data-Engineering-Team.
- Zweitnutzer: das Projektteam (Studierende, FOM Modul "Projekt: Anwendungsentwicklung"), das die Seiten entwickelt, testet und vorführt. [Aus den Projektunterlagen abgeleitet]

## Product Purpose

Ein Framework für die agentengestützte Entwicklung maßgeschneiderter, selbst gehosteter Dashboards. Aus einem ausgefüllten Artefakt (Ziel, Publikum, Spalten, KPIs, Branding) erzeugt eine Pipeline mit lokalem Sprachmodell eine `dashboard.json`; ein generischer Runner zeigt sie an. Erfolg heißt: Ein Fachanwender kommt ohne Hilfe vom Formular zum laufenden Dashboard, und dieselbe Pipeline erzeugt mit anderem Artefakt ein anderes Dashboard ohne Codeänderung.

Dieses Dokument betrifft nur die zwei Oberflächen des Frontends:
1. **Eingabe-App** (Build-Time): Formular, das eine geprüfte `artefakt.yaml` erzeugt.
2. **Dashboard-Runner** (Laufzeit): zeigt das Dashboard, die Dokumentation und erlaubt den Upload neuer Daten.

## Positioning

"Die Fabrik, nicht das Produkt": Kein einzelnes fertiges Dashboard, sondern ein Rahmen, der aus ausfüllbaren Vorlagen individuelle Dashboards macht, ohne dass Daten oder Schema-Informationen das eigene Netz verlassen (lokales Sprachmodell, Betrieb auf eigener Hardware).

## Operating Context

Büro-Laptop und Browser auf dem Raspberry Pi (Tailscale-Netz). Nicht primär Beamer-Präsentation (Nutzerantwort: "Nur Büro-Laptop/Pi-Browser"). Fachanwender sind Gelegenheitsnutzer: Das Formular wird selten, das Dashboard regelmäßig geöffnet. Daten kommen als CSV (häufig aus deutschem Excel: Semikolon, Dezimalkomma).

## Capabilities and Constraints

- Eingabe-App: Grunddaten, Spalten und KPIs in Tabellen, CSV-Spaltenvorschlag, Branding (Logo, Firmenfarben), laufende Fail-Fast-Prüfung mit Meldungen am Feld und oben, Laden/Speichern/Download der `artefakt.yaml`.
- Runner: vier Darstellungen (Balken, Linie, Tabelle, Kennzahl), Tabs "Dashboard", "Über dieses Dashboard", "Daten aktualisieren" (CSV-Upload, nur anhängen, Vorschau, Warnung vor Doppel-Upload).
- Technische Grenzen: Streamlit-Komponenten; keine eigenen JavaScript-Komponenten vorgesehen; Gestaltung über Theme, CSS und Markdown/HTML-Blöcke.
- Sprache der Oberfläche: Deutsch, einfache Wörter, keine Fachbegriffe aus der IT ohne Erklärung.
- Fehlermeldungen müssen verständlich sein und das betroffene Feld nennen (Projektregel Fail-Fast).
- Die Firmenfarben des Kunden sind Eingabe und für helle Hintergründe gestaltet; die erste Farbe dient im Runner als Akzent. Inhalt, Reihenfolge der Abschnitte und Funktionen sind getestet und bleiben erhalten.
- Nur synthetische Daten, keine echten Unternehmensdaten.

## Brand Commitments

Keine verbindlichen Vorgaben für die Oberfläche selbst (Nutzerantwort: "Keine, frei gestalten"). Die Produktidentität des Frameworks ist frei zu gestalten; die Kundenfarbe bleibt Akzent im Dashboard.

## Evidence on Hand

- Demo-Dashboard "Vertriebs-Dashboard" mit synthetischen Absatzdaten (`examples/sales/`), Beispiel-Artefakte `artefakte/sales`, `artefakte/aktivitaet`.
- Testdateien für Upload und Logo unter `examples/testdateien/`.
- Keine echten Kundenlogos, Kundenzitate oder Kennzahlen; keine erfinden.

## Product Principles

1. **Fehler früh und am richtigen Ort zeigen.** Meldungen stehen beim Feld, in einfacher Sprache, mit Hinweis, was zu tun ist.
2. **Vertrauen durch Klarheit.** Der Anwender sieht, was passiert und was gespeichert wird (Vorschau, Bestätigung, nur lesender Datenzugriff).
3. **Das Werkzeug verschwindet in der Aufgabe.** Bekannte Bedienmuster, ruhige Oberfläche, die Daten stehen im Vordergrund.
4. **Kundenmarke ist Gast, Framework ist Gastgeber.** Die Kundenfarbe taucht gezielt als Akzent im Dashboard auf, die App-Oberfläche hat eine eigene, stabile Identität.
