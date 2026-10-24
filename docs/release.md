# Neue Version veröffentlichen (für spstiger)

## Komponenten bearbeiten

Am einfachsten arbeitet man direkt im Git-Klon im `usrlib`-Ordner
(siehe [Installation, Weg C](installation.md#weg-c--github-desktop-für-entwickler)):

1. In DTools die Komponente bauen, gruppieren und über **Eigene Komponenten speichern** in die
   Bibliothek **spstiger-free-dtools-components** speichern. DTools ändert dabei direkt die
   `.pgl` und legt neue Grafiken in `vg/` und `image/` ab.
2. DTools schließen.
3. In GitHub Desktop die Änderungen prüfen. Nur Dateien der Bibliothek (`.pgl`, `vg/`, `image/`)
   und ggf. Doku committen.

Komponentennamen nicht nachträglich umbenennen – Kunden suchen sie unter dem bekannten Namen.

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
