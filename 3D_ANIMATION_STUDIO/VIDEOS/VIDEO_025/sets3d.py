"""VIDEO_025 "The World Ends In 60 Seconds" — 3D sets + plates (hybrid FAST mode, see PIPELINE/hybrid/kit3d.py).

    blender -b --factory-startup --python VIDEOS/VIDEO_025/sets3d.py -- [--only ST_LOW,LR_DOOR] [--samples 12]

Two FIXED sets in one scene (same coordinates in every shot):
  STREET  (origin): suburban street along +Y, houses both sides, lamps, trees, fences, far city skyline. The sky is
          transparent: comp draws the cracked sky + beams behind / over it.
  ROOM    (X0 = 100): Mia's living room. Front door in the back wall (y=+2.5, open), window in the left wall (x=X0-3),
          dining table with a cloth (Mia hides under it), sofa, lamp, toys, the wall clock at 11:59.
          Collections: CEIL (roof on) / BROKEN (roof ripped off: splintered wall tops) / BEAM (the white beam light).
Key spots (used by comp.py): YOU+MIA hug / beam spot H=(X0-0.6,-0.25), Mia under the table (X0-0.8,0.75).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'PIPELINE', 'hybrid'))
from kit3d import (OPT, box, ball, collection, cyl, finish, holdout, light, plate, prism, setup, show, toon)  # noqa

OUT = os.path.join(HERE, 'plates')
os.makedirs(OUT, exist_ok=True)
X0 = 100.0
setup(samples=12, transparent=True, ambient='#1C1230', ambient_strength=1.3)

# =============================================================================================== STREET
ROAD, WALK, CURB, LAWN = '#2E2C40', '#6A6880', '#8A88A0', '#2F4A3C'
box('ground', (0, 150, -0.12), (600, 600, 0.2), '#1E1A2C', w=0)
box('road', (0, 35, -0.02), (8, 120, 0.04), ROAD, w=0)
for k in range(24):
    box(f'dash{k}', (0, -18 + k * 5, 0.005), (0.15, 2.2, 0.02), '#9A8A5A', w=0)
for s in (-1, 1):
    box(f'walk{s}', (s * 5.25, 35, 0.07), (2.5, 120, 0.15), WALK, w=0.01)
    box(f'curb{s}', (s * 4.05, 35, 0.08), (0.12, 120, 0.17), CURB, w=0)
    box(f'lawn{s}', (s * 11.75, 35, 0.03), (10.5, 120, 0.08), LAWN, w=0)
WALLS = ['#8A7A9E', '#7A8AA6', '#A08A7A', '#8E9A8A', '#9A7A86', '#7E8E9E']
ROOFS = ['#4A3A4E', '#3E3E5A', '#4E3A3A']
for s in (-1, 1):
    for i, y in enumerate((-10, 2, 14, 26, 38, 50, 62, 74)):
        k = (i * 2 + (s > 0)) % len(WALLS)
        hx = s * 13.5
        box(f'house{s}{i}', (hx, y, 2.0), (7, 8, 4.0), WALLS[k], w=0.03)
        prism(f'roof{s}{i}', (hx, y, 4.0), (7.8, 8.8, 2.3), ROOFS[(i + (s > 0)) % 3], axis='y', w=0.03)
        fx = s * 9.98
        for dy in (-2.3, 2.3):
            lit = (i + int(dy > 0) + (s > 0)) % 3 != 0
            box(f'win{s}{i}{dy}', (fx, y + dy, 2.4), (0.06, 1.25, 1.3), '#F2B870' if lit else '#262238', w=0.02,
                **({'emit': 1.6} if lit else {}))
            box(f'wfr{s}{i}{dy}', (fx + s * 0.02, y + dy, 2.4), (0.04, 1.45, 1.5), '#D8D0E0', w=0)
        box(f'door{s}{i}', (fx, y, 1.1), (0.08, 1.0, 2.1), ['#5A3A44', '#3A4A5A', '#6A5A3A'][i % 3], w=0.02)
        box(f'step{s}{i}', (fx - s * 0.5, y, 0.12), (1.0, 1.6, 0.24), '#7A7488', w=0.02)
        if i % 2 == 0:
            box(f'chim{s}{i}', (hx + s * 1.5, y + 2.5, 5.6), (0.6, 0.6, 1.6), '#6A4A44', w=0.02)
        for dy in (-3.4, 3.4):                                                     # picket fence along the walk
            box(f'fence{s}{i}{dy}', (s * 6.7, y + dy * 0.6, 0.4), (0.05, 3.0, 0.7), '#C9C2D6', w=0.015)
        if i % 2 == 1:                                                             # trees between houses
            cyl(f'trunk{s}{i}', (s * 8.4, y + 6, 1.1), 0.16, 2.2, '#4A3A34', w=0.02)
            ball(f'crown{s}{i}', (s * 8.4, y + 6, 3.2), (1.6, 1.6, 1.9), '#33503F', w=0.03)
        if i % 3 == 0:
            cyl(f'bin{s}{i}', (s * 4.5, y + 3.2, 0.55), 0.3, 0.8, '#4A5A6A', w=0.02)
        box(f'mailpost{s}{i}', (s * 6.4, y - 2.0, 0.5), (0.08, 0.08, 1.0), '#4A4050', w=0.01)
        box(f'mailbox{s}{i}', (s * 6.4, y - 2.0, 1.05), (0.25, 0.45, 0.25), '#3A4A6A', w=0.015)
cyl('hydrant', (4.45, 9.0, 0.35), 0.13, 0.7, '#A83A34', w=0.02)
for s, ys in ((-1, (0, 24, 48)), (1, (12, 36, 60))):                              # street lamps
    for y in ys:
        cyl(f'pole{s}{y}', (s * 4.6, y, 2.3), 0.07, 4.6, '#3A3848', w=0.015)
        box(f'arm{s}{y}', (s * 4.15, y, 4.55), (0.9, 0.1, 0.1), '#3A3848', w=0.015)
        box(f'lamp{s}{y}', (s * 3.75, y, 4.45), (0.45, 0.3, 0.16), '#FFD49A', emit=4.0, w=0.01)
        light('POINT', (s * 3.75, y, 4.2), '#FFC27A', 260, size=0.3)
for k in range(14):                                                                # far skyline (blurs into depth)
    x = -150 + k * 22 + (k % 3) * 5
    h = 25 + (k * 37) % 55
    box(f'tower{k}', (x, 260 + (k % 4) * 30, h / 2), (16, 16, h), '#2A2440', w=0)
    for j in range(int(h // 12)):
        box(f'twin{k}{j}', (x, 252 + (k % 4) * 30 - 0.05, 6 + j * 12), (10, 0.2, 1.2), '#E8A868' if (k + j) % 3 else '#3A3050',
            w=0, **({'emit': 1.2} if (k + j) % 3 else {}))
light('SUN', (0, 60, 40), '#FF6A4A', 3.2, target=(0, 0, 0))                      # the cracked sky, up the street
light('SUN', (20, -40, 30), '#5A5AC0', 0.7, target=(0, 0, 0))                   # cool fill

# =============================================================================================== ROOM (X0 = 100)
WALLP, TRIM, FLOOR = '#9A8296', '#D8CCD8', '#7A5A4C'
box('lr_floor', (X0, 0, -0.05), (6, 5, 0.1), FLOOR, w=0)
for k in range(11):
    box(f'lr_seam{k}', (X0 - 2.75 + k * 0.55, 0, 0.002), (0.012, 5, 0.004), '#5A3E36', w=0)
box('lr_rug', (X0 - 0.4, 0.1, 0.008), (2.8, 2.2, 0.014), '#6A4A6A', w=0.01)
box('lr_rug2', (X0 - 0.4, 0.1, 0.012), (2.4, 1.8, 0.01), '#8A5A70', w=0)
# back wall (y=+2.5) with the doorway x X0+1.0..X0+2.0
box('lr_back_l', (X0 - 1.0, 2.5, 1.35), (4.0, 0.12, 2.7), WALLP, w=0.02)
box('lr_back_r', (X0 + 2.5, 2.5, 1.35), (1.0, 0.12, 2.7), WALLP, w=0.02)
box('lr_back_top', (X0 + 1.5, 2.5, 2.4), (1.0, 0.12, 0.6), WALLP, w=0.02)
box('lr_doorframe', (X0 + 1.5, 2.48, 2.12), (1.12, 0.14, 0.06), TRIM, w=0.01)
door = box('lr_door', (X0 + 1.0 - 0.09, 2.5 - 0.5, 1.05), (0.06, 1.0, 2.1), '#6A4A5A', rot=(0, 0, math.radians(10)), w=0.02)
ball('lr_knob', (X0 + 0.98, 1.65, 1.0), (0.04, 0.04, 0.04), '#E8C060', w=0.005)
# left wall (x=X0-3) with the window y -0.3..1.1, z 1.0..2.2
L = X0 - 3.0
box('lr_left_a', (L, -1.4, 1.35), (0.12, 2.2, 2.7), WALLP, w=0.02)
box('lr_left_b', (L, 1.8, 1.35), (0.12, 1.4, 2.7), WALLP, w=0.02)
box('lr_left_low', (L, 0.4, 0.5), (0.12, 1.4, 1.0), WALLP, w=0.02)
box('lr_left_top', (L, 0.4, 2.45), (0.12, 1.4, 0.5), WALLP, w=0.02)
box('lr_glass', (L, 0.4, 1.6), (0.02, 1.4, 1.2), '#000000', mat=holdout(), w=0)
for nm, loc, size in (('sill', (L + 0.08, 0.4, 0.98), (0.2, 1.6, 0.06)), ('wtop', (L + 0.04, 0.4, 2.22), (0.1, 1.6, 0.06)),
                      ('wl', (L + 0.04, -0.33, 1.6), (0.1, 0.06, 1.3)), ('wr', (L + 0.04, 1.13, 1.6), (0.1, 0.06, 1.3)),
                      ('wmid', (L + 0.04, 0.4, 1.6), (0.06, 0.05, 1.2)), ('wbar', (L + 0.04, 0.4, 1.6), (0.06, 1.4, 0.05))):
    box('lr_' + nm, loc, size, TRIM, w=0.01)
box('lr_curtain_l', (L + 0.12, -0.55, 1.5), (0.06, 0.35, 1.9), '#7A3A4A', w=0.015)
box('lr_curtain_r', (L + 0.12, 1.35, 1.5), (0.06, 0.35, 1.9), '#7A3A4A', w=0.015)
box('lr_right', (X0 + 3.0, 0, 1.35), (0.12, 5, 2.7), '#8E7A92', w=0.02)
box('lr_front', (X0, -2.5, 1.35), (6, 0.12, 2.7), WALLP, w=0.02)
for nm, x, y, sx, sy in (('skb', X0 - 1.0, 2.43, 4.0, 0.02), ('skr', X0 + 2.93, 0, 0.02, 5), ('skf', X0, -2.43, 6, 0.02), ('skl', L + 0.07, 0, 0.02, 5)):
    box('lr_' + nm, (x, y, 0.06), (sx, sy, 0.12), TRIM, w=0)
# the dining table (Mia hides under it): cloth hangs on the back + sides, open at the front (y-)
TX, TY = X0 - 0.8, 0.75
box('lr_ttop', (TX, TY, 0.76), (1.5, 1.0, 0.05), '#B8656A', w=0.02)
for dx in (-0.62, 0.62):
    for dy in (-0.38, 0.38):
        box(f'lr_tleg{dx}{dy}', (TX + dx, TY + dy, 0.37), (0.06, 0.06, 0.74), '#4A3238', w=0.01)
box('lr_cloth_b', (TX, TY + 0.5, 0.58), (1.5, 0.02, 0.36), '#A85A60', w=0.01)
box('lr_cloth_l', (TX - 0.75, TY, 0.58), (0.02, 1.0, 0.36), '#A85A60', w=0.01)
box('lr_cloth_r', (TX + 0.75, TY, 0.58), (0.02, 1.0, 0.36), '#A85A60', w=0.01)
box('lr_cloth_f', (TX, TY - 0.5, 0.68), (1.5, 0.02, 0.16), '#A85A60', w=0.01)
for k, (dx, dy, r) in enumerate(((-0.45, 0.85, 0), (0.45, 0.85, 0), (1.05, 0.0, 90))):
    box(f'lr_chair{k}', (TX + dx, TY + dy - 0.1 * (k < 2), 0.45), (0.45, 0.45, 0.06), '#5A3A40', w=0.015)
    box(f'lr_chairb{k}', (TX + dx, TY + dy + 0.12, 0.75), (0.45, 0.05, 0.6), '#5A3A40', rot=(0, 0, math.radians(r)), w=0.015)
# sofa along the right wall, facing -x; lamp; shelf; photos; clock 11:59; toys
SX = X0 + 2.45
box('lr_sofa', (SX, 0.0, 0.25), (0.9, 2.1, 0.5), '#5A6A8A', w=0.02)
box('lr_sofab', (SX + 0.38, 0.0, 0.65), (0.22, 2.1, 0.6), '#4E5E7E', w=0.02)
for dy in (-1.05, 1.05):
    box(f'lr_sofaa{dy}', (SX, dy, 0.45), (0.9, 0.2, 0.45), '#4E5E7E', w=0.02)
for dy, c in ((-0.5, '#C8A060'), (0.5, '#A06A7A')):
    box(f'lr_pillow{dy}', (SX + 0.2, dy, 0.6), (0.15, 0.45, 0.35), c, w=0.015)
box('lr_ctable', (X0 + 1.45, 0.0, 0.22), (0.6, 1.0, 0.06), '#6A4A3E', w=0.015)
cyl('lr_lamp_pole', (X0 + 2.6, 2.1, 0.8), 0.03, 1.6, '#3A3440', w=0.01)
cyl('lr_lamp_shade', (X0 + 2.6, 2.1, 1.65), 0.22, 0.3, '#F0B070', emit=1.3, w=0.01)
box('lr_shelf', (X0 - 2.0, 2.3, 0.9), (1.2, 0.3, 1.8), '#5A4040', w=0.02)
for j in range(3):
    box(f'lr_shelfb{j}', (X0 - 2.0, 2.16, 0.4 + j * 0.55), (1.1, 0.02, 0.04), '#3A2A2A', w=0)
    for b in range(6):
        box(f'lr_book{j}{b}', (X0 - 2.45 + b * 0.17, 2.25, 0.55 + j * 0.55), (0.1, 0.2, 0.26 - 0.03 * (b % 3)),
            ['#B85A4A', '#4A6A9A', '#C8A04A', '#5A8A5A', '#8A5A8A', '#D8D0C0'][(b + j) % 6], w=0.006)
for k, (y, z, wd, ht, c) in enumerate(((-1.2, 1.7, 0.5, 0.4, '#C88A7A'), (-0.4, 1.8, 0.4, 0.5, '#7A9AC8'), (0.5, 1.65, 0.7, 0.5, '#E8C8A0'))):
    box(f'lr_frame{k}', (X0 + 2.93, y, z), (0.03, wd, ht), '#C8A060', w=0.01)
    box(f'lr_photo{k}', (X0 + 2.91, y, z), (0.01, wd - 0.08, ht - 0.08), c, w=0)
cyl('lr_clock', (X0 - 0.6, 2.43, 2.15), 0.2, 0.04, '#F0E8D8', rot=(math.radians(90), 0, 0), w=0.015)
box('lr_clock_h', (X0 - 0.6, 2.4, 2.21), (0.02, 0.01, 0.12), '#1A1414', w=0)                 # hour hand ~12
box('lr_clock_m', (X0 - 0.618, 2.4, 2.24), (0.018, 0.01, 0.17), '#1A1414', rot=(0, math.radians(6), 0), w=0)  # 59 min
ball('lr_toyball', (X0 + 0.5, -0.6, 0.12), (0.12, 0.12, 0.12), '#C84A3A', w=0.01)
for k, (dx, dy, c) in enumerate(((0.1, -0.9, '#E8C04A'), (0.25, -0.95, '#4A7AC8'), (0.18, -0.78, '#5AA05A'))):
    box(f'lr_block{k}', (X0 + dx, dy, 0.05), (0.1, 0.1, 0.1), c, rot=(0, 0, k * 0.4), w=0.006)
box('lr_drawing', (X0 + 0.9, -1.2, 0.006), (0.4, 0.3, 0.004), '#F4F0E6', rot=(0, 0, 0.3), w=0.004)
box('lr_coat', (X0 + 2.2, 2.35, 1.4), (0.35, 0.08, 0.8), '#4A5A4A', w=0.015)
# outside the front door (seen through the doorway)
box('lr_porch', (X0 + 1.5, 3.6, -0.05), (2.5, 2.0, 0.1), '#5A5060', w=0)
box('lr_out_lawn', (X0, 16, -0.08), (60, 24, 0.1), '#2F4A3C', w=0)
box('lr_out_road', (X0, 12, -0.04), (60, 6, 0.06), ROAD, w=0)
for k in range(3):
    box(f'lr_out_house{k}', (X0 - 8 + k * 9, 21, 2.0), (7, 6, 4.0), WALLS[k], w=0.03)
    prism(f'lr_out_roof{k}', (X0 - 8 + k * 9, 21, 4.0), (7.8, 6.8, 2.2), ROOFS[k], axis='x', w=0.03)
light('POINT', (X0 + 2.6, 2.1, 1.6), '#FFB870', 140, size=0.15)                               # the lamp
light('AREA', (L - 1.2, 0.4, 1.7), '#FF5A3A', 420, size=1.2, target=(X0, 0.2, 0.6))            # red sky through the window
# --- roof on / roof ripped off / the beam
cc = collection('CEIL')
box('lr_ceiling', (X0, 0, 2.75), (6.2, 5.2, 0.1), '#6E6280', w=0.02, coll=cc)
cyl('lr_ceil_lamp', (X0 - 0.4, 0.2, 2.6), 0.25, 0.12, '#F8E0B0', emit=1.5, w=0.01, coll=cc)
cb = collection('BROKEN')
for k, (x, y, z, sx, sy, sz, rx, ry) in enumerate(((X0 - 2.2, 2.5, 2.85, 1.2, 0.12, 0.5, 0, 18), (X0 + 0.4, 2.5, 2.8, 0.9, 0.12, 0.4, 0, -25),
                                                   (X0 - 3.0, -1.6, 2.85, 0.12, 1.0, 0.5, 20, 0), (X0 + 3.0, 1.0, 2.8, 0.12, 1.4, 0.45, -15, 0),
                                                   (X0 - 1.2, -2.5, 2.8, 1.1, 0.12, 0.4, 0, 22))):
    box(f'lr_shard{k}', (x, y, z), (sx, sy, sz), WALLP, rot=(math.radians(rx), math.radians(ry), 0), w=0.02, coll=cb)
for k, (x, y, ang) in enumerate(((X0 - 1.5, 2.3, 35), (X0 + 1.8, -2.2, -40), (X0 - 2.8, 0.0, 60))):
    box(f'lr_beam{k}', (x, y, 2.9), (2.2, 0.12, 0.14), '#6A4A3E', rot=(math.radians(ang * 0.3), math.radians(ang), math.radians(ang)), w=0.015, coll=cb)
cl = collection('BEAM')
H = (X0 - 0.6, -0.25)
light('SPOT', (H[0], H[1], 9.0), '#DDEEFF', 2600, size=0.2, target=(H[0], H[1], 0), coll=cl, spot=16)
light('SUN', (X0, 0, 20), '#FF7A5A', 1.6, target=(X0 + 0.5, 0.5, 0), coll=cl)


def roof(on, beam=False):
    show('CEIL', on); show('BROKEN', not on); show('BEAM', beam)


# =============================================================================================== PLATES
P = dict(out_dir=OUT)
street = lambda: roof(True)  # noqa: E731  (the room's ceiling also blocks the street's sky light inside the room)
plate('ST_LOW', (1.0, 0.0, 0.32), (-0.3, 30, 6.5), lens=15, K=1.25, focus=(0.4, 6.0, 1.0), fstop=5.6, setup_fn=street, **P)
plate('ST_PANO', (3.6, 18.5, 1.15), (-10, 18.5, 2.4), lens=22, K=1.0, res=(3240, 1920), focus=(-0.6, 18.5, 1.0), fstop=4, setup_fn=street, **P)
plate('ST_MID', (1.2, 20.5, 1.1), (0.6, 48, 3.2), lens=18, K=1.2, focus=(0, 25, 1.0), fstop=4, setup_fn=street, **P)
plate('ST_FRONT', (0.4, 42.0, 1.0), (-0.2, 20, 1.7), lens=20, K=1.3, focus=(0, 33, 1.0), fstop=3.5, setup_fn=street, **P)
plate('ST_HIGH', (9.0, 22.0, 15.0), (-1, 56, 0), lens=18, K=1.2, setup_fn=street, **P)
plate('LR_DOOR', (X0 - 1.6, -2.2, 1.5), (X0 + 1.3, 2.5, 1.0), lens=20, K=1.2, focus=(X0 + 1.5, 2.0, 1.0), fstop=4, setup_fn=lambda: roof(True), **P)
plate('LR_TABLE', (X0 - 0.8, -1.0, 0.3), (X0 - 0.8, 0.8, 0.36), lens=26, K=1.15, focus=(X0 - 0.8, 0.7, 0.35), fstop=2.0, setup_fn=lambda: roof(True), **P)
plate('LR_HUG', (X0 + 0.8, -1.5, 0.95), (X0 - 0.6, 0.0, 0.7), lens=28, K=1.15, focus=(X0 - 0.6, -0.2, 0.7), fstop=2.2, setup_fn=lambda: roof(True), **P)
plate('LR_OPEN_UP', (X0 + 0.9, -2.0, 0.25), (X0 - 0.5, 0.0, 2.2), lens=15, K=1.25, focus=(X0 - 0.6, -0.25, 1.2), fstop=4, setup_fn=lambda: roof(False, True), **P)
plate('LR_OPEN_WIDE', (X0 + 2.6, -2.2, 1.3), (X0 - 0.8, 0.5, 2.0), lens=15, K=1.2, focus=(X0 - 0.6, -0.25, 1.2), fstop=4, setup_fn=lambda: roof(False, True), **P)
plate('LR_CLOSE_YOU', (X0 - 0.55, -1.25, 1.0), (X0 - 0.6, -0.25, 2.1), lens=30, K=1.1, focus=(X0 - 0.6, -0.25, 1.9), fstop=1.6, setup_fn=lambda: roof(False, True), **P)
plate('LR_CLOSE_MIA', (X0 - 0.9, -1.25, 1.75), (X0 - 0.95, -0.35, 0.9), lens=30, K=1.1, focus=(X0 - 0.95, -0.35, 0.95), fstop=1.6, setup_fn=lambda: roof(False, True), **P)
finish(OUT)
if '--save' in OPT:
    import bpy
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'sets3d.blend'))
