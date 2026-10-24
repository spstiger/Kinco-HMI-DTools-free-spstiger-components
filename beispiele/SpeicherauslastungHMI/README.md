# Beispielprojekt Speicherauslastung

DTools-V4-Projekt für ein **MK070E** mit allen Speicheranzeigen der Bibliothek
(`ram_64`, `ram_128`, `ram_256`, `flash_128`, `flash_256`) im Hauptfenster.

Öffnen: `SpeicherauslastungHMI.dpj` in Kinco DTools V4. Für ein anderes Gerät in DTools den HMI-Typ
umstellen und die passende Anzeige für die Speichergröße des Geräts behalten.

Beim Öffnen, Speichern und Kompilieren legt DTools `temp/`, `tar/`, `.bak` und `.pkgx` an. Diese
Dateien sind per `.gitignore` ausgeschlossen und gehören nicht ins Repository.

Aufbau und Systemregister: [docs/speicheranzeige.md](../../docs/speicheranzeige.md)
