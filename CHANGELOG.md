# Änderungen

Neue Einträge oben. Die Überschrift muss genau `## <Version>` lauten – der Release-Workflow
übernimmt diesen Abschnitt als Text des GitHub-Releases.

> Hinweis für alle Versionen: Komponenten, die schon in einem Projekt eingefügt sind, ändern sich
> durch ein Update der Bibliothek nicht. Wer die neue Fassung möchte, fügt die Komponente neu ein.

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
