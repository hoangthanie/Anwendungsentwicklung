# US-03 Firmenbranding hinterlegen

| Epic | PSP | Verantwortlich | Priorität (Entwurf AP 3.1) |
|---|---|---|---|
| E1 Artefakt erfassen | 6.2 | DB | Should |

> **Als** Fachanwender:in **möchte ich** Firmenfarben und Logo angeben, **damit** das Dashboard nach „unserem“ Dashboard aussieht.

## Akzeptanzkriterien

Status je Kriterium: siehe Backlog-Excel (Blatt „Akzeptanzkriterien“) bzw. Ergebnis der CI.

### US-03.1 Ungültige Farbcodes abweisen

- **Gegeben** eine Farbe ist nicht im Format #RRGGBB
- **Wenn** das Artefakt validiert wird
- **Dann** wird es abgelehnt
- **Test:** `test_models.py::test_ungueltige_farbe_wird_abgelehnt`

### US-03.2 Nur echte Bilder als Logo

- **Gegeben** eine Datei wird als Logo hochgeladen
- **Wenn** sie geprüft wird
- **Dann** werden nur echte PNG/JPEG-Bilder bis 1 MB akzeptiert – auch umbenannte Nicht-Bilder werden abgelehnt
- **Test:** `test_us02_03_artefakt.py::test_echtes_png_wird_akzeptiert, ::test_getarnte_datei_wird_abgelehnt, ::test_zu_grosses_logo_wird_abgelehnt`

## Schnittstelle (Vorschlag aus dem Testkonzept)

Modul: `frontend/src/ bzw. backend/src/ – dashboard_framework/runner/branding.py`

```python
pruefe_logo(pfad: str | Path) -> None   # wirft BrandingFehler
```

## Hinweise

Prüfung mit Pillow (Image.open + verify), nicht über die Dateiendung. Teil des Sicherheitskonzepts (AP 4.6).
