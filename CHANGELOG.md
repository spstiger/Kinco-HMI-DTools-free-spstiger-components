# Änderungen

Neue Einträge oben. Die Überschrift muss genau `## <Version>` lauten – der Release-Workflow
übernimmt diesen Abschnitt als Text des GitHub-Releases.

> Hinweis für alle Versionen: Komponenten, die schon in einem Projekt eingefügt sind, ändern sich
> durch ein Update der Bibliothek nicht. Wer die neue Fassung möchte, fügt die Komponente neu ein.

## 2.0.0

Alle Komponenten neu im spstiger-Design und in drei Größen. Die bisherigen Komponenten sind ersetzt.

- **Neue Namen mit Größe:** `ram_64_S/M/L`, `ram_128_*`, `ram_256_*`, `flash_128_*`, `flash_256_*`,
  `brightness_*`, `spstiger_logo_*`, `screen_saver_logo_*` – S 256 × 64, M 384 × 96, L 512 × 128 px.
  24 Komponenten statt 8.
- **Entfallen:** `ram_64`, `ram_128`, `ram_256`, `flash_128`, `flash_256`, `brightness`,
  `spstiger Logo`, `screen_saver_logo`. Bereits eingefügte alte Komponenten laufen in euren Projekten
  unverändert weiter.
- **Design:** Karten mit spstiger-Farben, deutlich größere Schrift (vorher 5 pt), RAM-Balken mit
  Projekt / System / frei und Legende ab Größe M.
- **Warnung:** Unter 10 % freiem Speicher wird der freie Teil des Balkens orange.
- **Helligkeitsregler** mit großen −/+-Tasten (44–56 px) und Prozentanzeige ab Größe M.
- **Logos** aus dem aktuellen spstiger-Design-System, Größe S ohne Claim.
- **Ausrichtung:** Zahlen stehen auf einer Linie mit dem Text davor. DTools zeichnet Zahlenanzeigen
  1 px höher als Text, die Komponenten gleichen das aus.
- Für spstiger: Die Bibliothek wird jetzt von `tools/baue_bibliothek.py` erzeugt, nicht mehr in
  DTools gepflegt (siehe `docs/release.md`).
- Das Beispielprojekt zeigt noch das Design von Version 1.

## 1.0.1

Bibliothek unverändert – nur der Updater und die Anleitung wurden verbessert.

- Updater-ZIP enthält jetzt `LIESMICH.txt`: was der Updater tut, dass er für spätere Updates einfach
  erneut gestartet wird, und wie man die Windows-Warnung „Unbekannter Herausgeber“ vermeidet
- Updater weist am Ende darauf hin, dass er immer die neueste Version holt
- Anleitung: Abschnitt zur Windows-Warnung und zum Freigeben der ZIP („Zulassen“)

## 1.0.0

Erste versionierte Veröffentlichung.

- Komponenten: `ram_64`, `ram_128`, `ram_256`, `flash_128`, `flash_256`, `spstiger Logo`,
  `brightness`, `screen_saver_logo`
- Lizenz: MIT
- Release-ZIP mit nur der Bibliothek und Update-Skript für alle installierten DTools-V4-Versionen
- Repository aufgeräumt: Beispielprojekt nach `beispiele/`, Anleitungen nach `docs/`,
  von DTools erzeugte Dateien (`temp/`, `tar/`, `.pkgx` …) entfernt
