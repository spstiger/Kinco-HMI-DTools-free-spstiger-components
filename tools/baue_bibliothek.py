#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
baue_bibliothek.py  —  erzeugt die spstiger-Komponentenbibliothek für Kinco DTools V4 im spstiger-Design.

Ergebnis (überschreibt):
  spstiger-free-DTools-components.pgl   Bibliothek
  vg/  image/                           Grafiken (werden komplett neu erzeugt)
  docs/bilder/komponenten-uebersicht.png  grobe Vorschau aller Komponenten (1:1)

Vorlagen:
  tools/vorlagen/bibliothek_v1.pgl      von DTools erzeugte Bauteile (Text, Zahl, Balken, Bitmap, Tasten,
                                        Schieberegler, Timer, Moving) – werden kopiert und angepasst
  tools/vorlagen/logo-original.png      Logo mit Claim, aus dem spstiger-Design-System (Farbwelt Standard)
  tools/vorlagen/logo-standard.png      Logo ohne Claim (für Größe S), ebenso
  tools/vorlagen/tigerkopf-orange.png   Tigerkopf, ebenso

Regeln aus dem DTools-Skill (regelwerk.md, belegt):
  - Farben im XML BGR; Schriftfarbe hex ohne 0x und ohne führende Nullen
  - Schrift in pt, Box-Höhe 1,53 × pt + 2 (+ 4 px Gerätereserve), Text steht links oben in seiner Box
  - Box-Breite = Textbreite + 7 + 4 px + 4 % (Gerätereserve G100E2)
  - Gruppen zeichnen umgekehrt: erstes Kind liegt oben
  - Zahlenanzeigen 1 px tiefer als statischer Text (ZAHL_DY, gemessen 24.10.2026)
  - Balken-Direction ist die Wachstumsrichtung ("Right" = vom linken Rand nach rechts, belegt am G100E2)
  - Bilder exakt in Bauteilgröße (DTools skaliert unschön)
Design (spstiger-Design-System, Kanal HMI abgeleitet wie spstiger_hmi.py):
  - nur Palettenfarben, Text Shark / Davys Grey, Akzentlinie Cathams Blue, Orange nur als Signal
  - Schrift Arial statt Inter (benannte Abweichung: Inter ist auf dem Panel nicht verfügbar)

  python tools/baue_bibliothek.py                  # Release-Stand
  python tools/baue_bibliothek.py --kalibrierung   # zusätzlich Testkomponente _kalibrierung_textversatz
"""
import copy
import math
import os
import re
import shutil
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VORLAGEN = os.path.join(ROOT, "tools", "vorlagen")
NAME = "spstiger-free-DTools-components"

# --------------------------------------------------------------------------------------------- Farben
F = {
    "nile_blue": "#12354F", "cathams_blue": "#194B6F", "pale_cerulean": "#A9C6D9", "orange": "#FF8300",
    "gruen": "#009846", "shark": "#242628", "davys_grey": "#525558", "silver_chalice": "#B3B5B7",
    "mercury": "#E2E3E4", "black_haze": "#F6F7F8",
}
KARTE, RAND, AKZENT = F["black_haze"], F["mercury"], F["cathams_blue"]
TEXT, TEXT2 = F["shark"], F["davys_grey"]


def bgr(rgb):
    """'#RRGGBB' -> '0xbbggrr' (Element-/Rechteckfarben)."""
    v = rgb.lstrip("#")
    return "0x" + (v[4:6] + v[2:4] + v[0:2]).lower()


def bgr_int(rgb):
    """'#RRGGBB' -> BGR als Dezimalzahl (CustomVG LineColor/FillColor)."""
    return str(int(bgr(rgb), 16))


def font_color(rgb):
    """'#RRGGBB' -> VectorFontColor: BGR hex ohne 0x und ohne führende Nullen."""
    return format(int(bgr(rgb), 16), "x")


def rgba(c, a=255):
    v = c.lstrip("#")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), a)


# --------------------------------------------------------------------------------------------- Schrift
RESERVE_W, RESERVE_W_PCT, RESERVE_H, BOX_EXTRA, BOLD_EXTRA = 4, 0.04, 4, 7, 0.09
_FONTS = {}


def _ttf(pt, bold=False):
    key = (pt, bold)
    if key not in _FONTS:
        datei = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "arialbd.ttf" if bold else "arial.ttf")
        _FONTS[key] = ImageFont.truetype(datei, round(pt * 4 / 3))
    return _FONTS[key]


def line_height(pt):
    return round(1.53 * pt) + 2 + RESERVE_H


def text_width(text, pt, bold=False):
    return _ttf(pt, bold).getlength(text) + (len(text) * BOLD_EXTRA * pt if bold else 0)


def box_width(text, pt, bold=False):
    tw = text_width(text, pt, bold)
    return math.ceil(tw) + BOX_EXTRA + RESERVE_W + math.ceil(RESERVE_W_PCT * tw)


# --------------------------------------------------------------------------------------------- Größen
GROESSEN = {
    #     Breite × Höhe, Innenabstand, Titel, Text, Balken, Legende
    "S": dict(w=256, h=64, pad=12, titel_y=8, titel_pt=11, text_pt=11, bar_y=36, bar_h=16, leg_y=None),
    "M": dict(w=384, h=96, pad=16, titel_y=10, titel_pt=14, text_pt=10, bar_y=42, bar_h=20, leg_y=66),
    "L": dict(w=512, h=128, pad=20, titel_y=14, titel_pt=18, text_pt=14, bar_y=56, bar_h=28, leg_y=92),
}
AKZENT_W = 4          # Akzentlinie links (Signaturelement)
RADIUS = 6
SS = 4                # Supersampling für Grafiken
WARN_PROZENT = 10     # Balken „frei“ wird orange unter diesem Anteil

# Zahlenanzeigen zeichnen ihre Ziffern 1 px höher als statischer Text mit gleicher Box-Oberkante – unabhängig
# von Schriftgröße (10/11/14/18 pt) und alter Pixelschrift-Größe <Size>; waagerecht kein Versatz.
# Gemessen 24.10.2026 mit _kalibrierung_textversatz: Simulation 4.4 pixelgenau, G100E2 per Foto gleichsinnig.
ZAHL_DY = 1

# Systemregister: Adresse -> Index, den DTools in NI#SysRegRIndex usw. einträgt (aus bibliothek_v1.pgl)
SYSREG = {9134: "39", 9136: "40", 9036: "17", 9140: "41"}


# --------------------------------------------------------------------------------------------- Vorlagen
class Vorlagen:
    def __init__(self, pfad):
        self.root = ET.parse(pfad).getroot()
        self.gruppen = {g.get("PartGroupName"): g.find("Group") for g in self.root.iter("PartGroup")}

    def teil(self, gruppe, name):
        for el in self.gruppen[gruppe].find("GParts"):
            if el.get("Name", el.get("name")) == name:
                return copy.deepcopy(el)
        raise KeyError(f"{gruppe}/{name}")


def _umbenennen(el, prefix, neu):
    """Name setzen und die namensabhängigen Attribute (z. B. NI1SysRegRIndex) mitziehen."""
    alt = el.get("Name")
    for k in list(el.attrib):
        if alt and k.startswith(alt) and k != alt:
            el.set(neu + k[len(alt):], el.attrib.pop(k))
    el.set("Name", neu)


def _position(el, x, y, w, h):
    p = el.find("Position")
    for tag, val in (("Left", x), ("Top", y), ("Right", x + w - 1), ("Bottom", y + h - 1)):
        p.find(tag).text = str(val)


def _adresse(el, funktion, wert, worte):
    for a in el.findall("Address"):
        if a.get("Function") == funktion:
            ra = a.find("RegAddr")
            ra.set("MasterValue", str(wert)); ra.set("WordCount", str(worte))
            av = ra.find("AddressValue")
            av.text = str(wert); av.set("Length", str(worte))
            return
    raise KeyError(funktion)


# --------------------------------------------------------------------------------------------- Bauen
class Bibliothek:
    def __init__(self):
        self.v = Vorlagen(os.path.join(VORLAGEN, "bibliothek_v1.pgl"))
        self.gruppen = []          # (Name, Group-Element)
        self.grafiken = {}         # Name -> (Liste PIL-Bilder, Typ 'bmp') oder (vg-Text, 'vector')
        self.zaehler = {}
        self.vorschau = []         # (Name, Größe, Zeichenfunktion)

    def _name(self, prefix):
        n = self.zaehler.get(prefix, 0)
        self.zaehler[prefix] = n + 1
        return f"{prefix}{n}"

    # ---- Bauteile -----------------------------------------------------------------------------
    def text(self, x, y, text, pt, farbe=TEXT, fett=False):
        x, y = round(x), round(y)
        el = self.v.teil("ram_64", "TXT0")
        w, h = box_width(text, pt, fett), line_height(pt)
        el.set("name", self._name("TXT"))
        for k, val in (("pos_sx", x), ("pos_sy", y), ("pos_ex", x + w - 1), ("pos_ey", y + h - 1)):
            el.set(k, str(val))
        el.set("VectorFontSize", str(pt)); el.set("VectorFontColor", font_color(farbe))
        el.set("VectorFontBold", "1" if fett else "0"); el.set("src", text)
        return el, x + math.ceil(text_width(text, pt, fett))

    def zahl(self, x, y, register, worte, max_roh, max_anzeige, stellen, nachkomma, einheit, pt, farbe=TEXT,
             groesse=None, rahmen=None, korrektur=True):
        """Zahlenanzeige (Number Input ohne Eingabe), Text links oben in der Box wie bei statischem Text.
        korrektur: um ZAHL_DY tiefer setzen, damit die Ziffern auf einer Linie mit statischem Text gleicher
        Box-Oberkante stehen."""
        x, y = round(x), round(y) + (ZAHL_DY if korrektur else 0)
        el = self.v.teil("ram_64", "NI1")
        _umbenennen(el, "NI", self._name("NI"))
        idx = SYSREG[register]
        for k in list(el.attrib):
            if k.endswith("SysRegRIndex") or k.endswith("SysRegWIndex"):
                el.set(k, idx)
        el.set("EnableInput", "0")
        _adresse(el, "Read", register, worte); _adresse(el, "Write", register, worte)
        ds = el.find("DataSet")
        ds.find("MaxValue").text = str(max_roh); ds.find("MinValue").text = "0"
        ds.find("IntgerCount").text = str(stellen); ds.find("DecimalCount").text = str(nachkomma)
        ds.find("ConvertMaxValueTo").text = str(max_anzeige); ds.find("ConvertMinValueTo").text = "0"
        el.find("aLabSetting").set("rightLab", "$SPACE_DRUG$" + einheit)
        f = el.find("Font")
        f.set("VectorFontSize", str(pt)); f.set("VectorFontColor", font_color(farbe)); f.set("VectorFontBold", "0")
        f.set("VectorFontAlign", "0"); f.find("Left").text = "0"; f.find("Top").text = "0"
        if groesse:                                    # alte Pixelschrift-Größe (nur Kalibrierung)
            f.find("Size").text = str(groesse)
        for b in el.iter("BorderProperties"):          # kein sichtbarer Rahmen: Linie und Fläche in Kartenfarbe
            b.set("LineColor", bgr_int(rahmen or KARTE)); b.set("FillColor", bgr_int(KARTE))
        muster = ("8" * stellen) + ("." + "8" * nachkomma if nachkomma else "") + " " + einheit
        w, h = box_width(muster, pt), line_height(pt)
        _position(el, x, y, w, h)
        return el, x + w

    def balken(self, x, y, w, h, register, max_roh, richtung, farbe, warnung=False):
        """richtung = Wachstumsrichtung (belegt am G100E2, 24.10.2026): "Right" wächst vom linken Rand nach rechts,
        "Left" vom rechten Rand nach links."""
        el = self.v.teil("ram_64", "BR0")
        _umbenennen(el, "BR", self._name("BR"))
        for k in list(el.attrib):
            if k.endswith("SysRegRIndex"):
                el.set(k, SYSREG[register])
        _adresse(el, "Read", register, 2)
        el.find("Direction").text = richtung
        el.find("MaxValue").text = str(max_roh); el.find("MinValue").text = "0"
        el.set("AlarmSwitch", "On" if warnung else "Off")
        el.find("AlarmMinValue").text = str(max_roh * WARN_PROZENT // 100 if warnung else 0)
        el.find("AlarmMaxValue").text = str(max_roh)
        cs = el.find("ColorSetting")
        cs.find("BarColor").text = bgr(farbe)
        cs.find("AlarmColor").text = bgr(F["orange"])       # unter AlarmMinValue (in DTools zu prüfen)
        cs.find("AlarmUpColor").text = bgr(farbe)            # über AlarmMaxValue: nie erreicht
        cs.find("BakgroundColor").text = bgr(KARTE)
        el.set("bBKColor", "0"); el.set("bBorderColor", "0")
        _position(el, x, y, w, h)
        return el

    def bitmap(self, x, y, grafik):
        el = self.v.teil("ram_64", "BG0")
        el.set("Name", self._name("BG"))
        el.find("Shape").set("URL", f".\\vg\\{grafik}.bg")
        w, h = self.grafiken[grafik][0][0].size
        _position(el, x, y, w, h)
        return el

    def gruppe(self, name, w, h, teile):
        """teile von oben nach unten (erstes liegt oben)."""
        g = ET.Element("Group", {"DrawLevel": str(len(teile) + 1), "name": str(len(self.gruppen))})
        p = ET.SubElement(g, "Position")
        for tag, val in (("Left", 0), ("Top", 0), ("Right", w - 1), ("Bottom", h - 1), ("lock_status", 0)):
            ET.SubElement(p, tag).text = str(val)
        gp = ET.SubElement(g, "GParts")
        for i, t in enumerate(teile):
            t.set("DrawLevel", str(len(teile) - i))
            t.set("isgroupmember", "yes")
            gp.append(t)
        self.gruppen.append((name, g))

    # ---- Grafiken ---------------------------------------------------------------------------------
    def grafik(self, name, bilder):
        self.grafiken[name] = (bilder, "bmp")
        return name

    @staticmethod
    def karte(w, h, spuren=(), quadrate=()):
        """Kartenhintergrund: Black Haze, Rand Mercury, Akzentlinie links. spuren/quadrate: (x, y, w, h, farbe[, rand])."""
        W, H = w * SS, h * SS
        maske = Image.new("L", (W, H), 0)
        ImageDraw.Draw(maske).rounded_rectangle((0, 0, W - 1, H - 1), RADIUS * SS, fill=255)
        im = Image.new("RGBA", (W, H), rgba(KARTE))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, AKZENT_W * SS - 1, H - 1), fill=rgba(AKZENT))
        for x, y, ww, hh, c, *rand in list(spuren) + list(quadrate):
            d.rectangle((x * SS, y * SS, (x + ww) * SS - 1, (y + hh) * SS - 1), fill=rgba(c),
                        outline=rgba(rand[0]) if rand else None, width=SS if rand else 0)
        rahmen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(rahmen).rounded_rectangle((0, 0, W - 1, H - 1), RADIUS * SS, outline=rgba(RAND), width=SS)
        im.alpha_composite(rahmen)
        out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out.paste(im, (0, 0), maske)
        return [out.resize((w, h), Image.LANCZOS)]

    @staticmethod
    def taste(w, h, symbol):
        """Sekundärtaste [normal, gedrückt]: Black Haze, Rand Cathams Blue, gedrückt Pale Cerulean; Symbol − / +."""
        out = []
        for gedrueckt in (False, True):
            W, H = w * SS, h * SS
            im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            box = (SS, SS, W - SS - 1, H - SS - 1)
            d.rounded_rectangle(box, RADIUS * SS, fill=rgba(F["pale_cerulean"] if gedrueckt else F["black_haze"]),
                                outline=rgba(F["nile_blue"] if gedrueckt else F["cathams_blue"]), width=2 * SS)
            s, t = min(W, H) * 0.32, max(2, round(min(w, h) / 14)) * SS
            cx, cy = W / 2, H / 2
            d.rectangle((cx - s, cy - t / 2, cx + s, cy + t / 2), fill=rgba(F["cathams_blue"]))
            if symbol == "+":
                d.rectangle((cx - t / 2, cy - s, cx + t / 2, cy + s), fill=rgba(F["cathams_blue"]))
            out.append(im.resize((w, h), Image.LANCZOS))
        return out

    @staticmethod
    def logo(datei, breite=None, hoehe=None):
        im = Image.open(os.path.join(VORLAGEN, datei)).convert("RGBA")
        if hoehe:
            breite = round(im.width * hoehe / im.height)
        else:
            hoehe = round(im.height * breite / im.width)
        return [im.resize((breite, hoehe), Image.LANCZOS)]

    def vg(self, name, text):
        self.grafiken[name] = (text, "vector")
        return name

    # ---- Komponenten ------------------------------------------------------------------------------
    def speicher(self, art, mb, gr):
        """art 'ram' oder 'flash'. RAM: [Projekt | System | frei], Flash: [belegt | frei]."""
        g = GROESSEN[gr]
        w, h, pad = g["w"], g["h"], g["pad"]
        x0, x1 = AKZENT_W + pad, w - pad
        roh = mb * 1024 * 1024
        stellen = len(str(mb))
        frei_reg = 9134 if art == "ram" else 9036
        titel = "RAM" if art == "ram" else "Flash"

        teile, spuren, quadrate = [], [], []
        # Kopfzeile: Titel + Kapazität
        t, x = self.text(x0, g["titel_y"], titel, g["titel_pt"], TEXT, fett=True)
        teile.append(t)
        teile.append(self.text(x + round(g["titel_pt"] * 0.6), g["titel_y"], f"{mb} MB", g["titel_pt"], TEXT2)[0])

        # Balken: Spur in der Karte, darüber die Bauteile
        bw = x1 - x0
        spur = F["pale_cerulean"] if art == "ram" else F["cathams_blue"]
        spuren.append((x0, g["bar_y"], bw, g["bar_h"], spur))
        balken = []
        if art == "ram":
            balken.append(self.balken(x0, g["bar_y"], bw, g["bar_h"], 9136, roh, "Right", F["cathams_blue"]))
        balken.append(self.balken(x0, g["bar_y"], bw, g["bar_h"], frei_reg, roh, "Left", F["mercury"], warnung=True))

        zahl = dict(worte=2, max_roh=roh, max_anzeige=mb, stellen=stellen, nachkomma=1, einheit="MB")
        if g["leg_y"] is None:
            # S: „frei“ rechts in der Kopfzeile
            pt = g["text_pt"]
            breite = math.ceil(text_width("frei", pt)) + round(pt * 0.5) + box_width("8" * stellen + ".8 MB", pt)
            xf = x1 - breite
            t, x = self.text(xf, g["titel_y"], "frei", pt, TEXT2)
            teile.insert(0, t)
            teile.insert(0, self.zahl(x + round(pt * 0.5), g["titel_y"], frei_reg, pt=pt, **zahl)[0])
        else:
            pt = g["text_pt"]
            q = round(pt * 4 / 3 * 0.8)
            qy = g["leg_y"] + round((round(1.53 * pt) + 2 - q) / 2)
            luecke = round(pt * 0.5)
            eintraege = ([("Projekt", F["cathams_blue"], None, 9136), ("System", F["pale_cerulean"], None, None),
                          ("frei", F["mercury"], F["silver_chalice"], frei_reg)] if art == "ram" else
                         [("belegt", F["cathams_blue"], None, None), ("frei", F["mercury"], F["silver_chalice"], frei_reg)])
            muster = "8" * stellen + ".8 MB"
            breiten = [q + luecke + math.ceil(text_width(lab, pt)) + (luecke + box_width(muster, pt) if reg else 0)
                       for lab, _, _, reg in eintraege]
            abstand = (bw - sum(breiten)) / (len(eintraege) - 1)
            if abstand < 2 * luecke:
                raise ValueError(f"{art}_{mb}_{gr}: Legende passt nicht ({abstand:.1f} px Abstand)")
            x = x0
            for (lab, c, rand, reg), bwid in zip(eintraege, breiten):
                x = round(x)
                quadrate.append((x, qy, q, q, c, rand) if rand else (x, qy, q, q, c))
                t, xe = self.text(x + q + luecke, g["leg_y"], lab, pt, TEXT2)
                teile.insert(0, t)
                if reg:
                    teile.insert(0, self.zahl(xe + luecke, g["leg_y"], reg, pt=pt, **zahl)[0])
                x += bwid + abstand

        hg = self.grafik(f"sp_{art}_{mb}_{gr}", self.karte(w, h, spuren, quadrate))
        teile += balken[::-1] + [self.bitmap(0, 0, hg)]
        self.gruppe(f"{art}_{mb}_{gr}", w, h, teile)

    def helligkeit(self, gr):
        g = GROESSEN[gr]
        w, h, pad = g["w"], g["h"], g["pad"]
        x0, x1 = AKZENT_W + pad, w - pad
        teile = []
        if gr == "S":
            ty, tg = (h - 44) // 2, 44
        else:
            t, x = self.text(x0, g["titel_y"], "Helligkeit", g["titel_pt"], TEXT, fett=True)
            teile.append(t)
            teile.append(self.zahl(x + round(g["titel_pt"] * 0.6), g["titel_y"], 9140, worte=1, max_roh=32,
                                   max_anzeige=100, stellen=3, nachkomma=0, einheit="%", pt=g["titel_pt"],
                                   farbe=TEXT2)[0])
            tg = 48 if gr == "M" else 56
            ty = h - pad + 4 - tg
        minus = self.grafik(f"sp_taste_minus_{tg}", self.taste(tg, tg, "-"))
        plus = self.grafik(f"sp_taste_plus_{tg}", self.taste(tg, tg, "+"))
        sub = self.v.teil("brightness", "SWD1")
        add = self.v.teil("brightness", "SWD0")
        for el, x, grafik in ((sub, x0, minus), (add, x1 - tg, plus)):
            _umbenennen(el, "SWD", self._name("SWD"))
            el.find("Shape").set("Type", "Bitmap"); el.find("Shape").set("URL", f".\\vg\\{grafik}.bg")
            for c in list(el.find("CustomVG")):
                el.find("CustomVG").remove(c)
            _position(el, x, ty, tg, tg)
        scr = self.v.teil("brightness", "SCR0")
        _umbenennen(scr, "SCR", self._name("SCR"))
        scr.find("BarShape").set("URL", ".\\vg\\sp_regler_spur.vg")
        scr.find("ThumbShape").set("URL", ".\\vg\\sp_regler_knopf.vg")
        _position(scr, x0 + tg + 8, ty, (x1 - tg - 8) - (x0 + tg + 8), tg)
        karte = self.grafik(f"sp_helligkeit_{gr}", self.karte(w, h))
        teile = [add, sub, scr] + teile + [self.bitmap(0, 0, karte)]
        # Texte und Zahl liegen oben: an den Anfang
        teile = [t for t in teile if t.tag == "draw" or t.get("Type") == "Number Input"] + \
                [t for t in teile if not (t.tag == "draw" or t.get("Type") == "Number Input")]
        self.gruppe(f"brightness_{gr}", w, h, teile)

    def logo_komponente(self, gr):
        breite = {"S": 160, "M": 240, "L": 320}[gr]
        # S ohne Claim: „WWW.SPSTIGER.DE“ wäre bei 160 px nicht mehr lesbar (Design-System: logo-standard)
        datei = "logo-standard.png" if gr == "S" else "logo-original.png"
        lg = self.grafik(f"sp_logo_{gr}", self.logo(datei, breite=breite))
        w, h = self.grafiken[lg][0][0].size
        self.gruppe(f"spstiger_logo_{gr}", w, h, [self.bitmap(0, 0, lg)])

    def bildschirmschoner(self, gr):
        hoehe = {"S": 96, "M": 137, "L": 192}[gr]
        kopf = self.grafik(f"sp_tigerkopf_{gr}", self.logo("tigerkopf-orange.png", hoehe=hoehe))
        w, h = self.grafiken[kopf][0][0].size
        tm0, tm1 = self.v.teil("screen_saver_logo", "TM0"), self.v.teil("screen_saver_logo", "TM1")
        mv = self.v.teil("screen_saver_logo", "MV0")
        for el, p in ((tm0, "TM"), (tm1, "TM"), (mv, "MV")):
            _umbenennen(el, p, self._name(p))
        _position(tm0, 0, 0, 50, 50); _position(tm1, 0, 56, 50, 50)
        mv.find("Shape").set("URL", f".\\vg\\{kopf}.bg")
        _position(mv, 60, 0, w, h)
        self.gruppe(f"screen_saver_logo_{gr}", 60 + w, max(h, 106), [tm1, tm0, mv])

    def kalibrierung(self):
        """Testkomponente für den Versatz zwischen statischem Text und Zahlenanzeige (nicht für das Release).
        Je Schriftgröße: statisch „88“ direkt vor einer Zahlenanzeige, diese um dy = −3 … +3 px verschoben.
        Zeile „Size“: alte Pixelschrift-Größe 8/16/24/32 bei 14 pt. Unten: Text über Zahl für den linken Rand.
        Zahlenanzeigen mit sichtbarem Rahmen (Silver Chalice), damit ihre Box im Screenshot erkennbar ist."""
        teile = []
        zahl = dict(register=9134, worte=2, max_roh=256 * 1024 * 1024, max_anzeige=256, stellen=3, nachkomma=1,
                    einheit="MB", rahmen=F["silver_chalice"])
        x0, dx_spalte = 70, 126
        for i, dy in enumerate(range(-3, 4)):
            teile.append(self.text(x0 + i * dx_spalte, 4, f"dy {dy:+d}", 9, TEXT2)[0])
        y = 30
        for pt in (10, 11, 14, 18):
            teile.append(self.text(6, y, f"{pt} pt", 9, TEXT2)[0])
            for i, dy in enumerate(range(-3, 4)):
                t, xe = self.text(x0 + i * dx_spalte, y, "88", pt)
                teile.append(t)
                teile.append(self.zahl(xe + 3, y + dy, pt=pt, korrektur=False, **zahl)[0])
            y += line_height(pt) + 18
        teile.append(self.text(6, y, "Size", 9, TEXT2)[0])
        for i, groesse in enumerate((8, 16, 24, 32)):
            t, xe = self.text(x0 + i * dx_spalte, y, "88", 14)
            teile.append(t)
            teile.append(self.zahl(xe + 3, y, pt=14, groesse=groesse, korrektur=False, **zahl)[0])
            teile.append(self.text(x0 + i * dx_spalte, y + line_height(14), f"Size {groesse}", 9, TEXT2)[0])
        y += line_height(14) + 34
        teile.append(self.text(6, y, "links", 9, TEXT2)[0])
        for i, pt in enumerate((10, 11, 14, 18)):
            teile.append(self.text(x0 + i * 2 * dx_spalte, y, "888.8 MB", pt)[0])
            teile.append(self.zahl(x0 + i * 2 * dx_spalte, y + line_height(pt), pt=pt, korrektur=False, **zahl)[0])
        y += 2 * line_height(18) + 8
        hg = self.grafik("sp_kalibrierung", [Image.new("RGBA", (1000, y), rgba(F["black_haze"]))])
        self.gruppe("_kalibrierung_textversatz", 1000, y, teile + [self.bitmap(0, 0, hg)])

    # ---- Schreiben --------------------------------------------------------------------------------
    def schreiben(self):
        for sub in ("vg", "image"):
            ziel = os.path.join(ROOT, sub)
            if os.path.isdir(ziel):
                shutil.rmtree(ziel)
            os.makedirs(ziel)
        for name, (inhalt, typ) in self.grafiken.items():
            if typ == "vector":
                _schreibe(os.path.join(ROOT, "vg", name + ".vg"), inhalt)
                continue
            dateien = []
            for i, im in enumerate(inhalt):
                fn = f"{name}_{i:02d}.png"
                im.save(os.path.join(ROOT, "image", fn), optimize=True)
                dateien.append(fn)
            w, h = inhalt[0].size
            _schreibe(os.path.join(ROOT, "vg", name + ".bg"), bg_xml(name, w, h, dateien))

        lib = ET.Element("EVPartGroupLib")
        pgs = ET.SubElement(lib, "PartGroups")
        for name, g in self.gruppen:
            ET.SubElement(pgs, "PartGroup", {"PartGroupName": name}).append(g)
        vgs = ET.SubElement(lib, "VectorGraphs")
        for name, (_, typ) in self.grafiken.items():
            ET.SubElement(vgs, "VectorGraph", {"URL": f".\\vg\\{name}.{'vg' if typ == 'vector' else 'bg'}"})
        for tag in ("TextObjects", "MacroObjs", "SubMacroObjs"):
            ET.SubElement(lib, tag)
        _schreibe(os.path.join(ROOT, NAME + ".pgl"), ET.tostring(lib, encoding="unicode"))


def _schreibe(pfad, text):
    if not text.startswith("<?xml"):
        text = '<?xml version="1.0" encoding="utf-8"?>\n' + text
    with open(pfad, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)


def bg_xml(name, w, h, bilder):
    """.bg wie in bg_grafik.py (DTools-Skill): Zustände absteigend, je Zustand ein Bild in Bauteilgröße."""
    draw = ('<draw name="" type="image" pos_sx="0" pos_sy="0" pos_ex="{ex}" pos_ey="{ey}" penwidth="1" '
            'penstyle="6" DOFlag="0" pencolor="0xeeeeaf" fillcolor="0xfae6e6" fill="color" GradientFill="false" '
            'BackgroundColor="0xfae6e6" ForegroundColor="0x0" lock_status="0" isgroupmember="no" '
            'src="..\\image\\{src}" UseExtImage="false" ExtImageFileName="" ExtImageMemType="0">'
            '<DynamicGraph flag="0"/><ViewCtrl EnableReg="0" CtrlMode="0"/></draw>')
    states = "".join(f'<state id="{i}">' + draw.format(ex=w - 1, ey=h - 1, src=src) + "</state>"
                     for i, src in reversed(list(enumerate(bilder))))
    return (f'<vg ver="1" name="{name}.bg" type="bmp" width="{w}" height="{h}" discription="" '
            f'color="0xffffff" transparent="no">{states}</vg>')


def vg_rechtecke(name, rechtecke):
    """Vektorgrafik 100 × 100 aus Rechtecken (x0, y0, x1, y1, farbe); erstes Rechteck liegt oben."""
    draws = "".join(
        f'<draw name="RCT{len(rechtecke) - 1 - i}" type="rect" pos_sx="{a}" pos_sy="{b}" pos_ex="{c}" pos_ey="{d}" '
        f'penwidth="1" penstyle="6" DOFlag="0" DrawLevel="{len(rechtecke) - 1 - i}" pencolor="none" '
        f'fillcolor="{bgr(f)}" fill="color" GradientFill="false" BackgroundColor="{bgr(f)}" ForegroundColor="0x0" '
        f'lock_status="0" isgroupmember="yes"><DynamicGraph flag="0"/><ViewCtrl EnableReg="0" CtrlMode="0"/></draw>'
        for i, (a, b, c, d, f) in enumerate(rechtecke))
    return (f'<vg ver="1" name="{name}.vg" type="vector" width="100" height="100" discription="" color="0xffffff" '
            f'transparent="no"><state id="0"><Group DrawLevel="{len(rechtecke)}" name="GROUP0"><Position><Left>0</Left>'
            f'<Top>0</Top><Right>99</Right><Bottom>99</Bottom><lock_status>0</lock_status></Position><GParts>{draws}'
            f'</GParts></Group></state></vg>')


def pruefen():
    """Prüft die geschriebene Bibliothek: eindeutige Namen, Namensattribute, Lage in der Gruppe,
    Bitmap-Bauteile pixelgleich mit ihren Bildern (sonst skaliert DTools unschön)."""
    root = ET.parse(os.path.join(ROOT, NAME + ".pgl")).getroot()
    namen, fehler = {}, []

    def datei(url):
        return os.path.join(ROOT, *url.lstrip(".").strip("\\").split("\\"))

    for pg in root.iter("PartGroup"):
        komp, g = pg.get("PartGroupName"), pg.find("Group")
        gp = g.find("Position")
        gw, gh = int(gp.findtext("Right")) + 1, int(gp.findtext("Bottom")) + 1
        for el in g.find("GParts"):
            n = el.get("Name") or el.get("name")
            namen[n] = namen.get(n, 0) + 1
            for k in el.attrib:
                m = re.match(r"([A-Z]+\d+)Sys", k)
                if m and m.group(1) != n:
                    fehler.append(f"{komp}/{n}: Attribut {k} passt nicht zum Namen")
            if el.find("Position") is not None:
                p = [int(el.find("Position").findtext(k)) for k in ("Left", "Top", "Right", "Bottom")]
            else:
                p = [int(el.get(k)) for k in ("pos_sx", "pos_sy", "pos_ex", "pos_ey")]
            if p[0] < 0 or p[1] < 0 or p[2] >= gw or p[3] >= gh:
                fehler.append(f"{komp}/{n}: {p} liegt außerhalb der Gruppe {gw}×{gh}")
            sh = el.find("Shape")
            if sh is not None and sh.get("Type") == "Bitmap":
                t = open(datei(sh.get("URL")), encoding="utf-8").read()
                w, h = map(int, re.search(r'width="(\d+)" height="(\d+)"', t).groups())
                if (p[2] - p[0] + 1, p[3] - p[1] + 1) != (w, h):
                    fehler.append(f"{komp}/{n}: Bauteil {p[2] - p[0] + 1}×{p[3] - p[1] + 1} ≠ Grafik {w}×{h}")
                for src in re.findall(r'src="([^"]+)"', t):
                    pfad = os.path.join(ROOT, "image", src.split("\\")[-1])
                    if Image.open(pfad).size != (w, h):
                        fehler.append(f"{src}: Bildgröße ≠ {w}×{h}")
    fehler += [f"Name {n} kommt {c}× vor" for n, c in namen.items() if c > 1]
    if fehler:
        raise SystemExit("FEHLER:\n  " + "\n  ".join(fehler))
    print(f"Prüfung ok: {sum(namen.values())} Bauteile, Namen eindeutig, Grafiken pixelgleich")


def main(kalibrierung=False):
    b = Bibliothek()
    for art, groessen in (("ram", (64, 128, 256)), ("flash", (128, 256))):
        for mb in groessen:
            for gr in "SML":
                b.speicher(art, mb, gr)
    b.vg("sp_regler_spur", vg_rechtecke("sp_regler_spur", [(0, 42, 99, 57, F["mercury"]), (0, 0, 99, 99, KARTE)]))
    b.vg("sp_regler_knopf", vg_rechtecke("sp_regler_knopf", [(44, 25, 55, 74, F["black_haze"]),
                                                              (0, 0, 99, 99, F["cathams_blue"])]))
    for gr in "SML":
        b.helligkeit(gr)
    for gr in "SML":
        b.logo_komponente(gr)
    for gr in "SML":
        b.bildschirmschoner(gr)
    if kalibrierung:
        b.kalibrierung()
    b.schreiben()
    print(f"{len(b.gruppen)} Komponenten, {len(b.grafiken)} Grafiken -> {NAME}.pgl")
    pruefen()
    return b


if __name__ == "__main__":
    import sys
    main(kalibrierung="--kalibrierung" in sys.argv)
