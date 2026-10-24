# Beispielprojekt Speicherauslastung

DTools-V4-Projekt für ein **MK070E** mit allen Speicheranzeigen der Bibliothek
(`ram_64`, `ram_128`, `ram_256`, `flash_128`, `flash_256`) im Hauptfenster.

> Das Projekt zeigt noch das Design von **Version 1** der Bibliothek. Die aktuellen Komponenten im
> spstiger-Design (Größen S/M/L) fügt ihr aus der Bibliothek ein, siehe [README](../../README.md).

Öffnen: `SpeicherauslastungHMI.dpj` in Kinco DTools V4. Für ein anderes Gerät in DTools den HMI-Typ
umstellen und die passende Anzeige für die Speichergröße des Geräts behalten.

Beim Öffnen, Speichern und Kompilieren legt DTools `temp/`, `tar/`, `.bak` und `.pkgx` an. Diese
Dateien sind per `.gitignore` ausgeschlossen und gehören nicht ins Repository.

## Änderungen durch bloßes Öffnen

Schon beim Öffnen schreibt DTools zwei Dateien neu, auch wenn man nichts ändert:

- `SpeicherauslastungHMI.dpj` – wird unverschlüsselt gespeichert (vorher verschlüsselt)
- `PLCGEDefaultProperties.xml` – Standardvorlagen für neue Elemente werden durch die der
  DTools-Installation ersetzt (meist leer); wirkt nicht auf vorhandene Elemente oder das HMI

Regel für Git:

- **Nur angesehen oder getestet** → Änderungen verwerfen
  (GitHub Desktop: Rechtsklick → **Discard changes**).
- **Bewusst etwas geändert und gespeichert** → alles zusammen committen: `.dpj`, geänderte
  `HMI0/*.whe`, `PLCGEDefaultProperties.xml` und neue Grafiken in `image/` bzw. `vg/`.

Aufbau und Systemregister: [docs/speicheranzeige.md](../../docs/speicheranzeige.md)
