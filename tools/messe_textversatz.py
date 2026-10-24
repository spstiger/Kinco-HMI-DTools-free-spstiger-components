#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
messe_textversatz.py  —  wertet einen Screenshot der Offline-Simulation mit der Testkomponente
_kalibrierung_textversatz aus (Bibliothek mit --kalibrierung bauen, Komponente bei x 0 / y 0 einfügen).
Gibt je Schriftgröße und dy den Versatz der Ziffern Zahl gegenüber statischem Text aus, in Panel-Pixeln
(Windows-Skalierung wird aus der Panelbreite 1024 px herausgerechnet).

  python tools/messe_textversatz.py screenshot.png
"""
import sys, xml.etree.ElementTree as ET
from PIL import Image
IMG = sys.argv[1]
im = Image.open(IMG).convert('L'); W, H = im.size
row = [im.getpixel((x, 300)) for x in range(W)]; xs = [x for x, v in enumerate(row) if v > 200]
col = [im.getpixel((400, y)) for y in range(H)]; ys = [y for y, v in enumerate(col) if v > 200]
x0, y0 = xs[0], ys[0]; s = (xs[-1] - x0 + 1) / 1024
import os
r = ET.parse(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'spstiger-free-DTools-components.pgl')).getroot()
g = [pg.find('Group') for pg in r.iter('PartGroup') if pg.get('PartGroupName').startswith('_kal')][0]
els = list(g.find('GParts'))
def box(e):
    if e.tag == 'draw': return [int(e.get(k)) for k in ('pos_sx', 'pos_sy', 'pos_ex', 'pos_ey')]
    p = e.find('Position'); return [int(p.findtext(k)) for k in ('Left', 'Top', 'Right', 'Bottom')]
def ink(a, b, c, d):
    A, B, C, D = round(x0 + a * s), round(y0 + b * s), round(x0 + c * s), round(y0 + d * s)
    cr = im.crop((A, B, C, D)); px = cr.load(); w, h = cr.size
    dk = [(x, y) for y in range(h) for x in range(w) if px[x, y] < 120]
    if not dk: return None
    return (b + min(y for x, y in dk) / s, b + max(y for x, y in dk) / s, a + min(x for x, y in dk) / s)
nis = [n for n in els if n.get('Type') == 'Number Input']
erg = []
for e in els:
    if e.tag == 'draw' and e.get('src') == '88':
        bt = box(e)
        ni = min((n for n in nis if box(n)[0] > bt[0] and abs(box(n)[1] - bt[1]) <= 3), key=lambda n: box(n)[0] - bt[0])
        bn = box(ni)
        it = ink(bt[0], bt[1] - 4, bn[0] - 1, bt[3] + 4)
        zn = ink(bn[0] + 1, min(bn[1], bt[1]) - 4, bn[0] + (bn[2] - bn[0]) * 0.42, max(bn[3], bt[3]) + 4)
        pt = int(e.get('VectorFontSize')); dy = bn[1] - bt[1]; size = ni.find('Font').findtext('Size')
        erg.append((pt, dy, size, it[1], zn[1], it[0], zn[0]))
        print(f"pt {pt:>2} dy {dy:+d} Size {size:>2} | Ziffern unten: Text {it[1]:6.1f}  Zahl {zn[1]:6.1f}  Diff {zn[1]-it[1]:+5.1f} | oben: Text {it[0]:6.1f} Zahl {zn[0]:6.1f} Diff {zn[0]-it[0]:+5.1f}")
# linker Rand: Text "888.8 MB" über Zahl
for e in els:
    if e.tag == 'draw' and e.get('src') == '888.8 MB':
        bt = box(e); ni = [n for n in nis if box(n)[0] == bt[0] and box(n)[1] > bt[1]][0]; bn = box(ni)
        it = ink(bt[0] - 2, bt[1], bt[2], bt[3]); zn = ink(bn[0] - 2, bn[1], bn[2], bn[3])
        print(f"links pt {e.get('VectorFontSize')}: Text x {it[2]:.1f}  Zahl x {zn[2]:.1f}  Diff {zn[2]-it[2]:+.1f}  (Box x {bt[0]})")
