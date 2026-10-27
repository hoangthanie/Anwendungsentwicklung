# Dokumentation Frontend

Diese Doku erklärt **was** gebaut wurde, **warum** so und **wie** es funktioniert. Sie wächst mit dem Code
und ist Grundlage für das Begleitdokument (Kapitel technische Dokumentation / Design-Entscheidungen).

| Datei | Inhalt |
|---|---|
| [01-projektverstaendnis.md](01-projektverstaendnis.md) | Worum geht es im Projekt, wo sitzt das Frontend, wie hängen die Teile zusammen |
| [02-entscheidungen.md](02-entscheidungen.md) | Entscheidungslog (ADR-artig) mit Alternativen und Begründung |
| [03-runner.md](03-runner.md) | Dashboard-Runner: Aufbau, Sicherheit, Entscheidungen (US-09) |
| [04-upload.md](04-upload.md) | Daten-Upload: Ablauf, Prüfregeln, Entscheidungen (US-10) |
| [05-branding.md](05-branding.md) | Logo- und Farbprüfung, Sicherheit, Anzeige (US-03) |
| [06-eingabe.md](06-eingabe.md) | Eingabeformular, Artefakt-Modell, Fail-Fast-Prüfung (US-01, US-02) |
| [07-dashboard-schritt.md](07-dashboard-schritt.md) | Pipeline-Schritt 3: Dashboard-Konfiguration mit Sprachmodell, Prüfung, Reparaturschleife (US-06) |
| [08-gestaltung.md](08-gestaltung.md) | Gestaltungssystem "Formblatt": Vorgehen mit dem Impeccable-Skill, Entscheidungen, Review |
| [09-lokales-dashboard.md](09-lokales-dashboard.md) | Eigenes Artefakt als Dashboard ansehen: Entwicklungsskript, was echt und was von Hand war |
| [raspberry-pi/README.md](../../raspberry-pi/README.md) | Betrieb auf dem Raspberry Pi 4 (2 GB): Docker, Datenordner, LAN/Tailscale |
| [prompt-verzeichnis-entwurf.md](prompt-verzeichnis-entwurf.md) | KI-Kennzeichnung (Modulvorgabe), geht an MP |

Konvention: Jede neue Funktion/Modul bekommt einen Abschnitt "Was / Warum / Wie" in der passenden Datei
(ab Implementierungsbeginn: `03-runner.md`, `04-eingabe.md`, `05-branding-upload.md`).
