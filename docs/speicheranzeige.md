# Speicheranzeige RAM und Flash

Die Komponenten `ram_*` und `flash_*` zeigen die Speicherauslastung eines Kinco-HMIs. Sie lesen nur
Systemregister und funktionieren in jedem Projekt ohne SPS.

![RAM 256 MB in den Größen S, M und L](bilder/readme-groessen.png)

## Varianten

| RAM | Flash | Größen |
|---|---|---|
| `ram_64_*`, `ram_128_*`, `ram_256_*`, `ram_512_*` | `flash_128_*`, `flash_256_*`, `flash_4096_*` | `_S` 256 × 64, `_M` 384 × 96, `_L` 512 × 128, `_XL` 896 × 224 px |

Welche Speichergröße euer Gerät hat, steht im Datenblatt. Die Variante muss dazu passen, denn
Balkenlänge und Stellenzahl richten sich danach. Ist sie zu klein, zeigt die Zahl `**.*`.

`flash_4096_*` ist für Geräte mit 4 GB Flash (z. B. GT2156E). Das Register LW9036 ist 32 Bit breit und
zählt höchstens 4 294 967 295 Byte, 1 Byte weniger als 4 GB. Darum endet der Balken bei diesem Wert,
der freie Speicher wird weiter in MB angezeigt.

## RAM-Anzeige

Der Balken zeigt drei Bereiche:

| Farbe | Bereich | Quelle |
|---|---|---|
| Cathams Blue `#194B6F` | **Projekt**: vom Projekt belegter RAM | LW9136–9137 (2 Words, Byte) |
| Pale Cerulean `#A9C6D9` | **System**: der Rest dazwischen | ergibt sich aus Gesamt − Projekt − frei |
| Mercury `#E2E3E4` | **frei** | LW9134–9135 (2 Words, Byte) |

Aufbau in DTools: Eine Bitmap bildet die Karte und den Balkenhintergrund in der System-Farbe. Darüber
liegen zwei Balken-Bauteile: „Projekt“ wächst vom linken Rand nach rechts, „frei“ vom rechten Rand
nach links. Was dazwischen sichtbar bleibt, ist der vom System belegte Bereich.

Die Zahlenanzeigen rechnen Byte in MB um (Wertebereich 0 … RAM in Byte → 0 … RAM in MB, eine
Nachkommastelle) und sind reine Anzeigen ohne Eingabe.

### Was belegt RAM?

Beim Start lädt das HMI alle Ressourcen in den Arbeitsspeicher, damit die Darstellung flüssig bleibt.

| Elementtyp | Einfluss auf RAM |
|---|---|
| Bilder und Bitmaps (Hintergründe, Icons, Logos) | hoch – werden vollständig geladen |
| Tabellen, Rezepte, Parameterlisten | mittel bis hoch |
| Schriften (jede Schrift und Größe) | mittel |
| Balken, Zeiger, Trends | mittel |
| Makros und Skripte | gering bis mittel |
| Kommunikationsvariablen | gering, summiert sich bei vielen |

## Flash-Anzeige

Im Flash gibt es keinen eigenen Systemanteil, Betriebssystem und Runtime nutzen ihn nur zum Speichern
und Laden von Dateien. Darum zeigt die Anzeige zwei Bereiche:

| Farbe | Bereich | Quelle |
|---|---|---|
| Cathams Blue | **belegt** | Gesamt − frei |
| Mercury | **frei** | LW9036–9037 (2 Words, Byte) |

## Warnung bei wenig Speicher

Fällt der freie Speicher unter 10 %, färbt sich der freie Teil des Balkens orange. Umgesetzt ist das
über die untere Alarmgrenze des Balkens (`AlarmMinValue`). Orange ist im spstiger-Design die
Signalfarbe und kommt in den Komponenten sonst nicht vor.

## Design

- Farben aus der spstiger-Palette, Akzentlinie links in Cathams Blue, Karte in Black Haze
- Schrift Arial: Inter, die spstiger-Hausschrift, ist auf dem Panel nicht verfügbar
- Zahlen stehen auf einer Linie mit dem Text davor. DTools zeichnet Zahlenanzeigen 1 px höher als
  statischen Text, die Komponenten gleichen das aus (gemessen in Simulation und auf dem G100E2).

Erzeugt werden die Komponenten von [tools/baue_bibliothek.py](../tools/baue_bibliothek.py). Größen,
Abstände und Farben stehen dort. Änderungen in DTools würden beim nächsten Lauf überschrieben.
