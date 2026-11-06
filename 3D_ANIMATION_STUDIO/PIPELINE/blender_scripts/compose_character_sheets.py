#!/usr/bin/env python3
"""Compose CHARACTER/mascot_reference_sheet.png and mascot_expressions.png from the
renders made by render_character_sheets.py (system python + Pillow)."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
CH = os.path.join(STUDIO, 'CHARACTER')
RS = os.path.join(CH, 'reference_sheets')
EX = os.path.join(CH, 'expressions')
FB = os.path.join(STUDIO, 'ASSETS', 'fonts', 'Montserrat-800.ttf')
FS = os.path.join(STUDIO, 'ASSETS', 'fonts', 'Montserrat-600.ttf')

import importlib.util
spec = importlib.util.spec_from_file_location('cfg', os.path.join(HERE, 'studio_lib', 'mascot_config.py'))
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)

NAMES = ['happy', 'surprised', 'shocked', 'confused', 'curious', 'angry', 'scared', 'sad', 'disgusted', 'excited',
         'thinking', 'laughing']


def font(path, size):
    return ImageFont.truetype(path, size)


def expressions_sheet():
    tile = 420
    W = 4 * tile
    H = 3 * (tile + 50) + 110
    s = Image.new('RGB', (W, H), (22, 24, 29))
    d = ImageDraw.Draw(s)
    d.text((30, 28), 'MASCOT — EXPRESSION LIBRARY', font=font(FB, 44), fill=(255, 255, 255))
    for k, n in enumerate(NAMES):
        im = Image.open(os.path.join(EX, f'exp_{n}.png')).convert('RGB').resize((tile, tile), Image.LANCZOS)
        x, y = (k % 4) * tile, 110 + (k // 4) * (tile + 50)
        s.paste(im, (x, y + 50))
        d.text((x + 16, y + 8), f'{k + 1:02d}  {n.upper()}', font=font(FB, 30), fill=(255, 176, 60))
    s.save(os.path.join(CH, 'mascot_expressions.png'))


def reference_sheet():
    views = ['front', 'three_quarter', 'side', 'back']
    vw, vh = 540, 960
    W = vw * 4
    H = 130 + vh + 60 + 360 + 40
    s = Image.new('RGB', (W, H), (22, 24, 29))
    d = ImageDraw.Draw(s)
    d.text((30, 26), 'MASCOT — MODEL REFERENCE SHEET', font=font(FB, 56), fill=(255, 255, 255))
    d.text((30, 92), 'Permanent protagonist · stylised 3D · height ≈1.35 m (≈4 heads incl. hair) · Blender 5.2 · CHARACTER/mascot_rig.blend',
           font=font(FS, 24), fill=(190, 196, 205))
    for i, v in enumerate(views):
        im = Image.open(os.path.join(RS, f'mascot_{v}.png')).convert('RGB').resize((vw, vh), Image.LANCZOS)
        s.paste(im, (i * vw, 130))
        d.text((i * vw + 18, 140), v.replace('_', ' ').upper(), font=font(FB, 30), fill=(255, 176, 60))
    y0 = 130 + vh + 30
    # palette
    d.text((30, y0), 'IDENTITY PALETTE', font=font(FB, 30), fill=(255, 255, 255))
    keys = ['skin', 'hair', 'brow', 'iris', 'sclera', 'shirt', 'jeans', 'shoe', 'lip']
    for i, k in enumerate(keys):
        x = 30 + i * 150
        hx = cfg.COLORS[k]
        d.rounded_rectangle((x, y0 + 50, x + 120, y0 + 150), 14, fill=hx, outline=(80, 80, 90), width=2)
        d.text((x, y0 + 160), k, font=font(FS, 22), fill=(220, 220, 225))
        d.text((x, y0 + 188), hx, font=font(FS, 20), fill=(160, 165, 175))
    # face close-ups
    fx = 30 + len(keys) * 150 + 20
    for j, n in enumerate(['neutral', 'happy', 'surprised']):
        im = Image.open(os.path.join(EX, f'exp_{n}.png')).convert('RGB').resize((230, 230), Image.LANCZOS)
        s.paste(im, (fx + j * 240, y0 + 40))
    notes = ('Locks: voluminous side-swept brown hair · warm skin · large dark-brown eyes with catchlights · '
             'dark expressive brows · ORANGE tee · blue jeans · white sneakers. Never substitute or restyle.')
    d.text((30, y0 + 240), notes, font=font(FS, 22), fill=(255, 210, 150))
    d.text((30, y0 + 275), 'Rig: 70+ bones, leg IK, optional arm IK, eye tracking target, jaw, lids, 3 brow bones/side, '
           '18 facial shape keys, 12 visemes, 12 expressions.', font=font(FS, 22), fill=(190, 196, 205))
    s.save(os.path.join(CH, 'mascot_reference_sheet.png'))
    for v in ('front', 'side', 'back'):
        Image.open(os.path.join(RS, f'mascot_{v}.png')).save(os.path.join(CH, f'mascot_{v}.png'))


if __name__ == '__main__':
    expressions_sheet()
    reference_sheet()
    print('SHEETS_COMPOSED')
