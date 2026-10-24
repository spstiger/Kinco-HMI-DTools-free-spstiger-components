# Komponenten ändern und neue Version veröffentlichen (für spstiger)

## Komponenten bearbeiten

Seit Version 2.0 erzeugt [`tools/baue_bibliothek.py`](../tools/baue_bibliothek.py) die komplette
Bibliothek: `.pgl`, `vg/` und `image/`. **Nicht in DTools in der Bibliothek speichern** – der nächste
Lauf überschreibt das. Größen, Abstände, Farben und neue Komponenten kommen ins Skript.

```
python tools/baue_bibliothek.py
python tools/vorschau_bibliothek.py
python tools/vorschau_bibliothek.py --readme
```

1. Skript ändern und ausführen. Es prüft am Ende Namen, Lage der Bauteile und Bildgrößen.
2. `docs/bilder/komponenten-uebersicht.png` ansehen (grobe Vorschau aus dem XML). Bei Änderungen am
   Aussehen auch die README-Bilder neu erzeugen.
3. In DTools testen. Über den Git-Klon oder die Junction in `usrlib` sieht DTools die neue Fassung
   sofort, es lädt die Bibliothek bei jedem Aufruf von **Eigene Komponenten nutzen** neu.
4. Auf dem Gerät prüfen. Simulation und Gerät rendern Text unterschiedlich breit.

Voraussetzung: Python 3 mit Pillow (`pip install pillow`) unter Windows, das Skript misst Texte mit
der Arial aus `C:\Windows\Fonts`. Bauvorlagen für die DTools-Bauteile liegen in `tools/vorlagen/`.

**Textversatz neu messen** (andere DTools-Version oder anderes Gerät):
`python tools/baue_bibliothek.py --kalibrierung` erzeugt zusätzlich die Komponente
`_kalibrierung_textversatz`. Sie bei x 0 / y 0 einfügen, die Simulation starten, einen Screenshot
machen und mit `python tools/messe_textversatz.py screenshot.png` auswerten. Das Ergebnis kommt nach
`ZAHL_DY`. Vor dem Release ohne `--kalibrierung` neu bauen.

Komponentennamen nicht nachträglich umbenennen – Kunden suchen sie unter dem bekannten Namen.

## Beispielprojekt öffnen

Wer das Beispiel unter `beispiele/` in DTools öffnet, sieht danach Änderungen an
`SpeicherauslastungHMI.dpj` und `PLCGEDefaultProperties.xml` – DTools schreibt beide schon beim
Öffnen neu. Nur angesehen oder getestet → **verwerfen**. Bewusst geändert und gespeichert → alle
geänderten Projektdateien zusammen committen. Details:
[beispiele/SpeicherauslastungHMI/README.md](../beispiele/SpeicherauslastungHMI/README.md#änderungen-durch-bloßes-öffnen)

## Version erhöhen

In [`VERSION`](../VERSION) die Versionsnummer setzen:

| Änderung | Beispiel |
|---|---|
| Fehler behoben, Optik angepasst | 1.0.0 → 1.0.1 |
| Neue Komponente | 1.0.1 → 1.1.0 |
| Komponente entfernt oder umbenannt | 1.1.0 → 2.0.0 |

In [`CHANGELOG.md`](../CHANGELOG.md) oben einen Abschnitt `## <Version>` ergänzen. Dieser Text wird
der Release-Text auf GitHub.

Vorher lokal prüfen (optional):

```
pwsh tools\Build-Release.ps1
```

Das Skript prüft, ob alle Grafiken vorhanden sind und der Changelog-Abschnitt existiert, und legt
die ZIP-Dateien in `dist\` ab (`dist\` wird nicht committet).

## Veröffentlichen

1. Commit nach `main` pushen. Der Workflow prüft die Bibliothek (Reiter **Actions** auf GitHub).
2. Tag anlegen und pushen – in GitHub Desktop: **History** → Rechtsklick auf den Commit →
   **Create Tag…** → `v1.1.0` → **Push origin**. Oder auf der Kommandozeile:
   ```
   git tag v1.1.0
   git push origin v1.1.0
   ```
3. Der Workflow baut die ZIP-Dateien und legt das Release an. Der Tag muss zu `VERSION` passen,
   sonst bricht er ab.

Der Download-Link für Kunden bleibt immer gleich und zeigt auf das neueste Release:

- Bibliothek: `https://github.com/spstiger/Kinco-HMI-DTools-free-spstiger-components/releases/latest/download/spstiger-free-DTools-components.zip`
- Update-Skript: `https://github.com/spstiger/Kinco-HMI-DTools-free-spstiger-components/releases/latest/download/spstiger-Bibliothek-Updater.zip`

## Kunden informieren

- Auf GitHub können Kunden unter **Watch → Custom → Releases** neue Versionen abonnieren.
- Kunden ohne GitHub-Konto über Newsletter oder Produktseiten im Shop informieren und auf den
  festen Download-Link verweisen.
- Im Changelog darauf hinweisen, dass bereits eingefügte Komponenten neu eingefügt werden müssen,
  wenn man die neue Fassung möchte.
