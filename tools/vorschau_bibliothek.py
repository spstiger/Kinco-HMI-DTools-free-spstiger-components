#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vorschau_bibliothek.py  —  grobe Vorschau aller Komponenten einer DTools-Bibliothek (.pgl), 1:1 in Pixeln.

Rendert direkt aus dem XML: Bitmaps (Zustand 0), Balken mit Beispielwerten, Zahlenanzeigen mit Beispielwert,
Texte (Arial, links oben in der Box), Tasten, Schieberegler, Moving. Timer sind unsichtbar.
Ersetzt nicht den Test in DTools – zeigt aber Lage, Größen, Farben und abgeschnittene Texte.

  python tools/vorschau_bibliothek.py [ausgabe.png]   # alle Komponenten (docs/bilder/komponenten-uebersicht.png)
  python tools/vorschau_bibliothek.py --readme         # README-Bilder (Panel, Größenvergleich)
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PGL = os.path.join(ROOT, "spstiger-free-DTools-components.pgl")
BEISPIEL = {9136: 0.20, 9134: 0.35, 9036: 0.70, 9140: 0.75}      # Anteil am Maximalwert
SEITE = (246, 247, 248)


def farbe_bgr(v):
    v = int(str(v).replace("0x", ""), 16)
    return (v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF)


def ttf(pt, bold=False):
    d = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arialbd.ttf" if bold else "arial.ttf")
    return ImageFont.truetype(d, round(int(pt) * 4 / 3))


def pos(el):
    p = el.find("Position")
    return [int(p.findtext(k)) for k in ("Left", "Top", "Right", "Bottom")]


def bg_bild(url, zustand=0):
    pfad = os.path.join(ROOT, url.lstrip(".\\").replace("\\", os.sep))
    t = open(pfad, encoding="utf-8").read()
    st = re.findall(r'<state id="(\d+)">.*?src="([^"]+)"', t)
    src = dict(st).get(str(zustand), st[-1][1])
    return Image.open(os.path.join(ROOT, src.replace("..\\", "").replace("\\", os.sep))).convert("RGBA")


def vg_zeichnen(d, url, box):
    pfad = os.path.join(ROOT, url.lstrip(".\\").replace("\\", os.sep))
    t = open(pfad, encoding="utf-8").read()
    x0, y0, x1, y1 = box
    sx, sy = (x1 - x0 + 1) / 100, (y1 - y0 + 1) / 100
    rects = re.findall(r'type="rect" pos_sx="(\d+)" pos_sy="(\d+)" pos_ex="(\d+)" pos_ey="(\d+)".*?fillcolor="(0x[0-9a-f]+)"', t)
    for a, b, c, e, f in reversed(rects):          # erstes Rechteck liegt oben
        d.rectangle((x0 + int(a) * sx, y0 + int(b) * sy, x0 + (int(c) + 1) * sx - 1, y0 + (int(e) + 1) * sy - 1),
                    fill=farbe_bgr(f))


def register(el):
    for a in el.findall("Address"):
        if a.get("Function") == "Read":
            return int(a.find("RegAddr").get("MasterValue"))


def gruppe_rendern(g, warnung=False):
    gp = pos(g)
    im = Image.new("RGBA", (gp[2] + 1, gp[3] + 1), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for el in reversed(list(g.find("GParts"))):     # letztes Kind liegt unten
        typ = el.get("Type") or el.get("type")
        if typ in ("Bitmap", "Moving"):
            x0, y0, x1, y1 = pos(el)
            im.alpha_composite(bg_bild(el.find("Shape").get("URL")).resize((x1 - x0 + 1, y1 - y0 + 1)), (x0, y0))
        elif typ == "Word Set":
            x0, y0, x1, y1 = pos(el)
            im.alpha_composite(bg_bild(el.find("Shape").get("URL")), (x0, y0))
        elif typ == "Scroll Bar":
            box = pos(el)
            vg_zeichnen(d, el.find("BarShape").get("URL"), box)
            x0, y0, x1, y1 = box
            k = (y1 - y0 + 1) // 2
            kx = x0 + round((x1 - x0 + 1 - k) * BEISPIEL[9140])
            vg_zeichnen(d, el.find("ThumbShape").get("URL"), (kx, y0, kx + k - 1, y1))
        elif typ == "Bar":
            x0, y0, x1, y1 = pos(el)
            reg = register(el)
            anteil = 0.06 if (warnung and reg in (9134, 9036)) else BEISPIEL[reg]
            maxv = int(el.findtext("MaxValue"))
            cs = el.find("ColorSetting")
            c = cs.findtext("BarColor")
            if el.get("AlarmSwitch") == "On" and anteil * maxv < int(el.findtext("AlarmMinValue")):
                c = cs.findtext("AlarmColor")
            bw = round((x1 - x0 + 1) * anteil)
            if el.findtext("Direction") == "Left":          # Wachstumsrichtung: "Left" = von rechts verankert
                d.rectangle((x1 - bw + 1, y0, x1, y1), fill=farbe_bgr(c))
            else:
                d.rectangle((x0, y0, x0 + bw - 1, y1), fill=farbe_bgr(c))
        elif typ == "Number Input":
            x0, y0, x1, y1 = pos(el)
            reg = register(el)
            ds = el.find("DataSet")
            wert = int(ds.findtext("ConvertMaxValueTo")) * (0.06 if (warnung and reg in (9134, 9036)) else BEISPIEL[reg])
            nk = int(ds.findtext("DecimalCount"))
            f = el.find("Font")
            einheit = el.find("aLabSetting").get("rightLab").replace("$SPACE_DRUG$", " ")
            text = f"{wert:.{nk}f}{einheit}"
            schicht = Image.new("RGBA", (x1 - x0 + 1, y1 - y0 + 1), (0, 0, 0, 0))
            # DTools zeichnet Zahlen 1 px höher als statischen Text (gemessen 24.10.2026, siehe ZAHL_DY)
            ImageDraw.Draw(schicht).text((int(f.findtext("Left")), int(f.findtext("Top")) - 1), text,
                                         font=ttf(f.get("VectorFontSize"), f.get("VectorFontBold") == "1"),
                                         fill=farbe_bgr(f.get("VectorFontColor")))
            im.alpha_composite(schicht, (x0, y0))       # an der Box abgeschnitten wie in DTools
        elif typ == "text":
            x0, y0, x1, y1 = (int(el.get(k)) for k in ("pos_sx", "pos_sy", "pos_ex", "pos_ey"))
            schicht = Image.new("RGBA", (x1 - x0 + 1, y1 - y0 + 1), (0, 0, 0, 0))
            ImageDraw.Draw(schicht).text((0, 0), el.get("src"),
                                         font=ttf(el.get("VectorFontSize"), el.get("VectorFontBold") == "1"),
                                         fill=farbe_bgr(el.get("VectorFontColor")))
            im.alpha_composite(schicht, (x0, y0))
    return im


def main(ausgabe):
    root = ET.parse(PGL).getroot()
    gruppen = [(pg.get("PartGroupName"), pg.find("Group")) for pg in root.iter("PartGroup")]
    gruppen.append(("ram_256_M (unter 10 % frei)", dict(gruppen)["ram_256_M"]))
    bilder = [(n, gruppe_rendern(g, warnung="unter" in n)) for n, g in gruppen]
    breite, rand, zeile, x, y, zh = 1100, 24, [], 24, 24, 0
    plaetze = []
    for n, im in bilder:
        if x + im.width > breite - rand:
            x, y = rand, y + zh + 40
            zh = 0
        plaetze.append((n, im, x, y))
        x += im.width + rand
        zh = max(zh, im.height)
    out = Image.new("RGB", (breite, y + zh + 40), SEITE)
    d = ImageDraw.Draw(out)
    for n, im, x, y in plaetze:
        out.paste(im, (x, y + 16), im)
        d.text((x, y), n, font=ttf(9), fill=(82, 85, 88))
    out.save(ausgabe, optimize=True)
    print(f"{len(bilder)} Komponenten -> {ausgabe} ({out.width} × {out.height})")


def readme_bilder():
    """Bilder für die README: Panel 1024 × 600 mit Diagnoseseite und Größenvergleich S/M/L."""
    root = ET.parse(PGL).getroot()
    gruppen = {pg.get("PartGroupName"): pg.find("Group") for pg in root.iter("PartGroup")}
    bilder = os.path.join(ROOT, "docs", "bilder")

    # Panel mit Rahmen: links Größe L, rechts Größe M und Logo
    rand, panel = 18, Image.new("RGBA", (1024, 600), SEITE + (255,))
    for name, x, y in (("ram_256_L", 24, 24), ("flash_256_L", 24, 168), ("brightness_L", 24, 312),
                       ("ram_128_M", 576, 24), ("flash_128_M", 576, 136), ("brightness_M", 576, 248),
                       ("spstiger_logo_M", 648, 420)):
        panel.alpha_composite(gruppe_rendern(gruppen[name]), (x, y))
    geraet = Image.new("RGBA", (1024 + 2 * rand, 600 + 2 * rand), (0, 0, 0, 0))
    ImageDraw.Draw(geraet).rounded_rectangle((0, 0, geraet.width - 1, geraet.height - 1), 16, fill=(36, 38, 40, 255))
    geraet.alpha_composite(panel, (rand, rand))
    geraet.save(os.path.join(bilder, "readme-panel.png"), optimize=True)

    # Größenvergleich RAM 256 und Helligkeit in S/M/L
    reihen = [["ram_256_S", "ram_256_M", "ram_256_L"], ["brightness_S", "brightness_M", "brightness_L"]]
    zellen = [[gruppe_rendern(gruppen[n]) for n in r] for r in reihen]
    luecke, kopf = 24, 22
    breite = luecke + sum(im.width for im in zellen[0]) + luecke * 3
    hoehe = luecke + sum(max(im.height for im in z) + kopf + luecke for z in zellen)
    out = Image.new("RGBA", (breite, hoehe), SEITE + (255,))
    d = ImageDraw.Draw(out)
    y = luecke
    for r, z in zip(reihen, zellen):
        x = luecke
        for n, im in zip(r, z):
            gr = n.rsplit("_", 1)[1]
            d.text((x, y), f"{gr} · {im.width} × {im.height} px", font=ttf(10), fill=(82, 85, 88))
            out.alpha_composite(im, (x, y + kopf))
            x += im.width + luecke
        y += max(im.height for im in z) + kopf + luecke
    out.save(os.path.join(bilder, "readme-groessen.png"), optimize=True)
    print("README-Bilder: readme-panel.png, readme-groessen.png")


if __name__ == "__main__":
    if "--readme" in sys.argv:
        readme_bilder()
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "bilder", "komponenten-uebersicht.png"))
