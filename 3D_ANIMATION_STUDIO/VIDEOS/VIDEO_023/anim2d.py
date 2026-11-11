#!/usr/bin/env python3
"""VIDEO_023 "The Last Two Humans" — 2.5D ink style, MOVEMENT FIRST: every shot has someone running, vaulting, sliding,
crouching, breathing or shaking, and the camera tracks the action (side-scroll with 4 parallax layers, dollies).

    python3 VIDEOS/VIDEO_023/anim2d.py [--still JOB:frame ...] [--out DIR] [--procs 4]

Places (fixed layouts): STREET (burning orange dusk) -> STORE (grocery store, green fluorescent; the roll-up gate at the
front, aisle 7, the walk-in freezer at the back) -> FREEZER (icy blue, frosted door window, EXIT door at the back)."""
import argparse
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'twod'))
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, flicker, mouth_open, quad, text  # noqa
import edit_video023 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS, JS, s, e = E.B, E.LS, E.WORDS, E.JS, E.s, E.e
INK, FIRE, SMOKE, FLUO, ICE, LAV = '#0E0C1A', '#FF7A30', '#2A1E2A', '#B8F0C0', '#BFE4FF', '#A8A4E0'

MIKA = dict(long_hair=True, hair='#1A1414', hair_sh='#0A0808', shirt='#C83A4A', shirt_sh='#9A2A38', skin='#E8B890', skin_sh='#C89470',
            pants='#2A2A3A', pants_sh='#1A1A26')
TARA = dict(long_hair=True, hair='#C8642A', hair_sh='#9A4A1E', shirt='#3A6A4A', shirt_sh='#2A4E36', skin='#F4D0B8', skin_sh='#D4AE94',
            pants='#3A4A6A', pants_sh='#2A3650')
ZSHIRTS = [('#5A5048', '#40382F'), ('#3A4A6A', '#28344E'), ('#6A3A3A', '#4E2A2A'), ('#4A5A3A', '#36422A'), ('#7A7A80', '#5A5A60')]


def zomb(k=0):
    sh = ZSHIRTS[k % len(ZSHIRTS)]
    return dict(zombie=True, skin=['#9AA494', '#8E9A8A', '#A4A898'][k % 3], skin_sh='#76806E', iris='#D8E0E4', pupil_col='#A8B0B4',
                shirt=sh[0], shirt_sh=sh[1], pants='#2E2E34', pants_sh='#202024', hair=['#3A2A1A', '#1A1A1A', '#6A4A2A', '#8A8A8A'][k % 4],
                hair_sh='#100C08', mouth='wide', brow=-0.7)


def talk(t, who):
    return mouth_open(t, WORDS, [l['id'] for l in E._T['lines'] if l['id'][0] == who])


_g = (np.random.default_rng(23).normal(128, 40, (512, 512))).clip(0, 255).astype(np.uint8)
GRAIN = skia.Image.fromarray(np.dstack([_g, _g, _g, np.full_like(_g, 255)]))


def grain(cv, t, a=0.07):
    p = skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kOverlay)
    for x in range(-(int(t * 997) % 512), W, 512):
        for y in range(-(int(t * 613) % 512), H, 512):
            cv.drawImage(GRAIN, x, y, skia.SamplingOptions(), p)


class inked:
    def __init__(self, cv, w=5):
        self.cv, self.w = cv, w

    def __enter__(self):
        f = skia.ImageFilters.Merge([skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(14, 12, 26), skia.BlendMode.kSrcIn),
                                                                   skia.ImageFilters.Dilate(self.w, self.w)), None])
        self.cv.saveLayer(None, skia.Paint(ImageFilter=f))

    def __exit__(self, *a):
        self.cv.restore()


class blurred:
    def __init__(self, cv, s_):
        self.cv, self.s = cv, s_

    def __enter__(self):
        self.cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(self.s, self.s)))

    def __exit__(self, *a):
        self.cv.restore()


def label(cv, x, y, txt, t0, t, col='#C8302A', size=48):
    k = min(1.0, max(0.0, (t - t0) * 5))
    if k <= 0:
        return
    cv.save(); cv.translate(x, y); cv.scale(k, k); cv.rotate(-3)
    w_ = len(txt) * size * 0.32 + 40
    cv.drawRoundRect(skia.Rect(-w_, -size * 0.85, w_, size * 0.85), 10, 10, paint('#F4F0E6'))
    cv.drawRoundRect(skia.Rect(-w_, -size * 0.85, w_, size * 0.85), 10, 10, paint(INK, style='stroke', width=5))
    text(cv, txt, 0, size * 0.35, size, col)
    cv.restore()


def breath(cv, x, y, t, sc=1.0, seed=0, on=True):
    """Cold breath puffs (the clue: Tara's stop)."""
    if not on:
        return
    for k in range(3):
        ph = (t * 0.7 + k / 3 + seed * 0.13) % 1.0
        cv.drawCircle(x + ph * 90 * sc, y - ph * 120 * sc, (20 + 50 * ph) * sc, paint(C('#FFFFFF', 0.35 * (1 - ph)), blur=10))


# ===================================================================== STREET (side-scroll, 4 parallax layers)
def street(cv, t, speed=900.0):
    cam_x = t * speed
    cv.drawRect(skia.Rect(0, 0, W, 1200), paint('#000000', shader=lin((0, 0), (0, 1200), [C('#3A1420'), C('#C8462A'), C('#FF9A50')], [0, 0.6, 1])))
    glow(cv, (300, 1050), 700, FIRE, 0.45)
    for k in range(5):                                                                       # smoke columns
        x = (k * 300 - cam_x * 0.05) % 1500 - 200
        cv.drawPath(blob([(x, 1100), (x + 60, 700), (x + 160, 300), (x + 260, 0), (x + 120, 0), (x + 20, 350), (x - 60, 750)]), paint(C(SMOKE, 0.55), blur=24))
    for k in range(9):                                                                       # far skyline (0.1x)
        x = (k * 170 - cam_x * 0.1) % 1530 - 220
        h_ = 300 + (k * 97) % 260
        cv.drawRect(skia.Rect(x, 1150 - h_, x + 150, 1150), paint('#2A1828'))
    with inked(cv, 4):
        for k in range(6):                                                                   # mid buildings (0.4x), windows on fire
            x = (k * 280 - cam_x * 0.4) % 1680 - 300
            h_ = 520 + (k * 131) % 240
            cv.drawRect(skia.Rect(x, 1260 - h_, x + 250, 1260), paint(['#5A3A3A', '#4A3A4A', '#6A4A3A'][k % 3]))
            for j in range(4):
                for i in range(3):
                    wy = 1260 - h_ + 60 + j * 110
                    lit = (k + i + j) % 4 == 0
                    cv.drawRect(skia.Rect(x + 30 + i * 72, wy, x + 80 + i * 72, wy + 70), paint(FIRE if lit else '#1A1018'))
        cv.drawRect(skia.Rect(0, 1260, W, 1380), paint('#6A5A5A'))                            # sidewalk
        cv.drawRect(skia.Rect(0, 1380, W, H), paint('#3A3238'))                               # road
        for k in range(6):
            x = (k * 260 - cam_x) % 1560 - 200
            cv.drawRect(skia.Rect(x, 1640, x + 140, 1660), paint('#E8D8A0'))                    # lane marks (1x)
            cv.drawLine(x + 60, 1260, x + 60, 1380, paint(C(INK, 0.4), style='stroke', width=3))
        for k in range(3):                                                                   # lamp posts (1x)
            x = (k * 620 - cam_x) % 1860 - 300
            cv.drawRect(skia.Rect(x, 700, x + 18, 1380), paint('#2A2A30'))
            cv.drawRect(skia.Rect(x - 40, 690, x + 50, 712), paint('#2A2A30'))


def car(cv, x, y, sc=1.0, col='#4A6A8A', burning=False):
    with inked(cv, 4):
        cv.drawRoundRect(skia.Rect(x, y - 130 * sc, x + 420 * sc, y - 30 * sc), 30, 30, paint(col))
        cv.drawPath(poly([(x + 80 * sc, y - 130 * sc), (x + 140 * sc, y - 210 * sc), (x + 300 * sc, y - 210 * sc), (x + 360 * sc, y - 130 * sc)]), paint(col))
        cv.drawPath(poly([(x + 100 * sc, y - 135 * sc), (x + 150 * sc, y - 195 * sc), (x + 290 * sc, y - 195 * sc), (x + 340 * sc, y - 135 * sc)]), paint('#1A2030'))
        for wx in (x + 90 * sc, x + 330 * sc):
            cv.drawCircle(wx, y - 30 * sc, 46 * sc, paint('#141418'))
    if burning:
        for k in range(5):
            fx = x + 100 * sc + k * 50 * sc
            h_ = (90 + 50 * math.sin(k * 2.1 + x)) * sc
            cv.drawPath(blob([(fx - 30, y - 200 * sc), (fx, y - 200 * sc - h_), (fx + 30, y - 200 * sc)]), paint(FIRE))


def runner(cv, x, y, sc, ph, P, face=1, lean=0.0, ink_w=6):
    with inked(cv, ink_w):
        mascot(cv, x, y, sc, view='side', face=face, walk=ph % 1.0, run=True, body_lean=lean, light_side=-1, rim=FIRE, rim_a=0.5, **P)


def shot_CHASE(cv, t):
    """Frame 0: already running. The two girls sprint right; the horde pours in behind, gaining; Tara vaults a car."""
    street(cv, t)
    cam_x = t * 900
    cx = 1700 - (cam_x % 2400)                                                               # a wrecked car Tara vaults over
    if -500 < cx < 1200:
        car(cv, cx, 1520, 1.0, burning=True)
    # the horde: 9 zombies, sprinting faster than they should, arms out
    for k in range(9):
        zx = -260 + k * 70 + 140 * math.sin(t * 0.9 + k) + min(1.0, t / 5) * 120
        zy = 1640 + (k % 3) * 40
        runner(cv, zx, zy, 0.48 + (k % 3) * 0.04, t * 2.6 + k * 0.37, dict(zomb(k), arm_r=(85, 10), arm_l=(80, 15)), lean=18, ink_w=4)
    # Tara: vaults the car around B['vault']
    u = (t - B['vault']) / 0.6
    jump = max(0.0, math.sin(min(1.0, max(0.0, u)) * math.pi)) * 260
    P = dict(TARA, brow=1.0, mouth='open', mouth_open=0.5, sweat=True, pupil=0.6)
    if 0 < u < 1:
        P.update(arm_r=(150, 20), arm_l=(140, 30))
    runner(cv, 520, 1680 - jump, 0.62, t * 2.4 + 0.4, P, lean=12)
    # Mika (you), closest to camera
    P = dict(MIKA, brow=1.0, mouth='open', mouth_open=0.35 + 0.3 * abs(math.sin(t * 7)), sweat=True, pupil=0.55, look=(-0.6, 0.0))
    runner(cv, 760, 1760, 0.7, t * 2.4, P, lean=12)
    shade(cv, (600, 1100), 1250, 0.45)
    grain(cv, t)


def gate_store_bg(cv, t, inside=True):
    """Store front from INSIDE: the roll-up gate (grating), dusk fire glow outside, the checkout counter."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A3A30'))
    with blurred(cv, 4):
        cv.drawRect(skia.Rect(80, 380, 1000, 1500), paint('#000000', shader=lin((0, 380), (0, 1500), [C('#C8462A'), C('#FF9A50')])))
    glow(cv, (540, 1100), 900, FIRE, 0.35)


def grating(cv, y_bottom):
    with inked(cv, 3):
        cv.drawRect(skia.Rect(80, 380, 1000, y_bottom), paint(C('#5A5A62', 0.0)))
        for x in range(90, 1000, 46):
            cv.drawLine(x, 380, x, y_bottom, paint('#7A7A84', style='stroke', width=8))
        for y in range(400, int(y_bottom), 46):
            cv.drawLine(80, y, 1000, y, paint('#7A7A84', style='stroke', width=6))
        cv.drawRect(skia.Rect(80, y_bottom - 24, 1000, y_bottom), paint('#9A9AA4'))


def shot_GATE(cv, t):
    """The girls slide under the closing gate; it slams; the horde hits it."""
    u = t - B['gate']
    gate_store_bg(cv, t)
    yb = 380 + min(1.0, u / 0.7) * 1120                                                       # gate rolls down
    for k in range(6):                                                                        # zombies racing at the gate (outside)
        zx = 1300 - min(1.0, u / 0.9) * (700 - k * 60) + k * 40
        runner(cv, zx, 1500, 0.42, t * 2.6 + k * 0.3, dict(zomb(k), arm_r=(85, 10)), face=-1, lean=18, ink_w=3)
    grating(cv, yb)
    sx = -200 + min(1.0, u / 0.45) * 760                                                        # Mika slides in, under the gate
    with inked(cv, 6):
        mascot(cv, sx, 1820, 0.62, view='side', face=1, crouch=0.8, body_lean=-35, light_side=-1, rim=FIRE, rim_a=0.5,
               **dict(MIKA, brow=1.0, mouth='open', mouth_open=0.6, sweat=True))
        tx = -420 + min(1.0, max(0.0, (u - 0.15) / 0.45)) * 700
        mascot(cv, tx, 1840, 0.6, view='side', face=1, crouch=0.8, body_lean=-35, light_side=-1, rim=FIRE, rim_a=0.5,
               **dict(TARA, brow=1.0, mouth='open', mouth_open=0.6, sweat=True))
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#000000', shader=lin((0, 1500), (0, H), [C('#3A4A40'), C('#1A221E')])))
    with inked(cv, 6):                                                                         # redraw girls over the floor
        mascot(cv, sx, 1820, 0.62, view='side', face=1, crouch=0.8, body_lean=-35, light_side=-1, rim=FIRE, rim_a=0.5,
               **dict(MIKA, brow=1.0, mouth='open', mouth_open=0.6, sweat=True))
        mascot(cv, tx, 1840, 0.6, view='side', face=1, crouch=0.8, body_lean=-35, light_side=-1, rim=FIRE, rim_a=0.5,
               **dict(TARA, brow=1.0, mouth='open', mouth_open=0.6, sweat=True))
    shade(cv, (540, 1000), 1150, 0.45)
    grain(cv, t)


def shot_GATEFACE(cv, t):
    """Close: a zombie presses its face to the grating and talks. Calm. Polite. More of them behind, shifting."""
    gate_store_bg(cv, t)
    for k in range(5):
        with blurred(cv, 6):
            mascot(cv, 120 + k * 220, 2000 + (k % 2) * 80, 1.0, light_side=1, rim=FIRE, rim_a=0.3, **dict(zomb(k + 2), mouth='flat', brow=0.0))
    P = dict(zomb(0), mouth='smile' if talk(t, 'Z') == 0 else 'open', mouth_open=talk(t, 'Z'), brow=0.2, look=(0.0, 0.1))
    with inked(cv, 8):
        mascot(cv, 540 + 10 * math.sin(t * 1.3), 2700, 1.8, light_side=1, rim=FIRE, rim_a=0.6, head_tilt=-8 + 5 * math.sin(t * 0.8), **P)
    for x in range(90, 1000, 46):
        cv.drawLine(x, 380, x, 1500, paint('#7A7A84', style='stroke', width=10))
    for y in range(400, 1500, 46):
        cv.drawLine(80, y, 1000, y, paint('#7A7A84', style='stroke', width=7))
    shade(cv, (540, 960), 1100, 0.45)
    grain(cv, t)


def shot_DRONE(cv, t):
    """Outside, night roofs: a police drone rises, red/blue lights, a searchlight sweeping the store roof."""
    u = t - B['drone']
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#140A18'), C('#5A2030')])))
    with inked(cv, 4):
        cv.drawRect(skia.Rect(-20, 1300, W + 20, H), paint('#2A2A34'))                        # store roof
        cv.drawRect(skia.Rect(150, 1180, 930, 1300), paint('#3A3A44'))
        text(cv, 'GROCERY', 540, 1270, 90, '#B8F0C0')
    dy = 1500 - min(1.0, u / 1.2) * 900                                                        # rising
    dx = 540 + 120 * math.sin(t * 0.9)
    sweep = math.sin(t * 1.4) * 260
    cv.drawPath(poly([(dx - 20, dy + 30), (dx + 20, dy + 30), (dx + sweep + 220, 1400), (dx + sweep - 220, 1400)]), paint(C('#FFFFFF', 0.14), blur=16))
    with inked(cv, 5):
        cv.drawRoundRect(skia.Rect(dx - 90, dy - 30, dx + 90, dy + 30), 16, 16, paint('#2A2A30'))
        for side in (-1, 1):
            cv.drawLine(dx + side * 90, dy - 10, dx + side * 180, dy - 50, paint('#2A2A30', style='stroke', width=12))
            ang = t * 60
            cv.drawLine(dx + side * 180 - 70 * math.cos(ang), dy - 54, dx + side * 180 + 70 * math.cos(ang), dy - 54, paint('#8A8A94', style='stroke', width=6))
    on = int(t * 6) % 2
    glow(cv, (dx - 40, dy), 140, '#E0342C' if on else '#3A6AFF', 0.7)
    glow(cv, (dx + 40, dy), 140, '#3A6AFF' if on else '#E0342C', 0.7)
    for k in range(6):                                                                         # zombies on the street pointing up
        zx = 120 + k * 170
        with inked(cv, 3):
            mascot(cv, zx, 1920, 0.42, light_side=1, rim=FIRE, rim_a=0.4, arm_r=(150, 10), **dict(zomb(k), mouth='flat', look=(0.0, -1.0)))
    shade(cv, (540, 900), 1150, 0.45)
    grain(cv, t)


def thermal_body(cv, x, y, sc, heat=1.0, crouch=0.6):
    col = [C('#FFF0A0', heat), C('#FF7A20', heat), C('#C82020', heat * 0.8), C('#3A2AA0', 0.0)]
    cv.drawCircle(x, y - 330 * sc, 90 * sc, paint('#000000', shader=rad((x, y - 330 * sc), 140 * sc, col)))
    cv.drawOval(skia.Rect(x - 120 * sc, y - 260 * sc, x + 120 * sc, y), paint('#000000', shader=rad((x, y - 130 * sc), 200 * sc, col)))


def shot_THERMAL(cv, t):
    """Drone thermal camera: the store in cold blue wireframe; warm bodies glow. D01: two (one already fading: hidden).
    D02: the freezer box, ONE warm body... and one shape the same blue as the meat."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A0A3A'))
    for k in range(6):                                                                          # shelves, top-down
        x = 120 + k * 150
        cv.drawRect(skia.Rect(x, 360, x + 70, 1500), paint('#1A2A7A'))
        cv.drawRect(skia.Rect(x, 360, x + 70, 1500), paint('#3A5AC8', style='stroke', width=3))
    cv.drawRect(skia.Rect(700, 1560, 1000, 1820), paint('#0A1460'))                             # freezer box (cold)
    cv.drawRect(skia.Rect(700, 1560, 1000, 1820), paint('#5A7AFF', style='stroke', width=4))
    text(cv, 'FREEZER', 850, 1600, 34, '#8AA0FF')
    phase2 = t >= s('D02') - 0.2
    if not phase2:                                                                              # aisle 7: two shapes, crouched
        thermal_body(cv, 520, 1000, 0.9, 1.0)
        thermal_body(cv, 620, 1010, 0.85, 0.55 + 0.1 * math.sin(t * 3))                             # Tara is already cooler
        label(cv, 570, 1180, 'AISLE 7', s('D01'), t, col='#E0342C', size=40)
    else:
        thermal_body(cv, 800, 1760, 0.55, 1.0)                                                   # Mika
        thermal_body(cv, 900, 1765, 0.52, 0.08)                                                  # Tara: as cold as the meat
        label(cv, 850, 1480, '1 WARM BODY', s('D02'), t, col='#E0342C', size=40)
    for y in range(0, H, 6):
        cv.drawLine(0, y, W, y, paint(C('#000000', 0.12), style='stroke', width=2))               # scanlines
    text(cv, 'THERMAL  ·  REC', 230, 300, 40, '#E0342C')
    cv.drawRect(skia.Rect(60, 260, 1020, 1860), paint('#E0E0FF', style='stroke', width=3))
    grain(cv, t, 0.1)


def store_aisle(cv, cam, t):
    """Grocery aisle in perspective: shelves of products both sides, flickering fluorescent tubes, aisle sign 7."""
    q = lambda p: quad(cam, p)  # noqa
    lp = flicker(t, 3, 8.0, 0.55)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#141E18'))
    with inked(cv, 3):
        cv.drawPath(q([(-1.6, 3.0, 0.2), (1.6, 3.0, 0.2), (1.6, 3.0, 20), (-1.6, 3.0, 20)]), paint('#1E2A24'))
        cv.drawPath(q([(-1.6, 0, 0.2), (1.6, 0, 0.2), (1.6, 0, 20), (-1.6, 0, 20)]), paint('#000000', shader=lin((0, H), cam.p(0, 0, 20), [C('#C8D0C0'), C('#5A6A60')])))
        for side in (-1, 1):
            cv.drawPath(q([(side * 1.0, 0, 0.2), (side * 1.0, 2.2, 0.2), (side * 1.0, 2.2, 20), (side * 1.0, 0, 20)]), paint('#3A4A42'))
            for k in range(5):                                                                    # shelf boards + products
                h_ = 0.2 + k * 0.45
                a0, a1 = cam.p(side * 1.0, h_, 0.3), cam.p(side * 1.0, h_, 20)
                cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint('#8A9A90', style='stroke', width=6))
                for z in range(1, 19):
                    p0 = cam.p(side * 0.99, h_ + 0.05, z)
                    p1 = cam.p(side * 0.99, h_ + 0.35, z + 0.4)
                    cv.drawRect(skia.Rect(min(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[0], p1[0]), max(p0[1], p1[1])),
                                paint(['#E05A3A', '#E8C040', '#3A8AD0', '#6AC05A', '#E8E8E8'][(z + k + (side > 0)) % 5]))
    for z in range(2, 20, 3):                                                                    # fluorescent tubes
        a0, a1 = cam.p(-0.3, 2.95, z), cam.p(0.3, 2.95, z)
        cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C(FLUO, lp), style='stroke', width=8))
        glow(cv, ((a0[0] + a1[0]) / 2, a0[1]), 200, FLUO, 0.15 * lp)
    sx, sy = cam.p(0, 2.6, 4)
    with inked(cv, 4):
        cv.drawRoundRect(skia.Rect(sx - 70, sy - 50, sx + 70, sy + 50), 10, 10, paint('#2A6AC8'))
    text(cv, '7', sx, sy + 26, 70, '#FFFFFF')


def shot_AISLE(cv, t):
    """Running full speed down aisle 7 toward the freezer; the camera runs backward in front of them."""
    u = t - B['aisle']
    cam = Cam(u * 2.4, eye=1.4, vy=900, x=0.0, f=860)
    store_aisle(cv, cam, t)
    for k, (P, xo, zo) in enumerate(((TARA, -0.35, 2.6), (MIKA, 0.25, 2.1))):
        z = cam.z + zo
        px, py = cam.p(xo, 0, z)
        PP = dict(P, brow=1.0, mouth='open', mouth_open=talk(t, 'K') if P is MIKA else 0.5, sweat=True, pupil=0.6, look=(0.0, 0.0))
        with inked(cv, 6):
            mascot(cv, px, py + 12 * abs(math.sin(t * 9 + k)), cam.scale(z, 1.55), walk=(t * 2.6 + k * 0.5) % 1, run=True, light_side=1,
                   rim=FLUO, rim_a=0.4, **PP)
    shade(cv, (540, 900), 1150, 0.45)
    grain(cv, t)


def freezer_room(cv, t, door_x=540):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#5A7A9A'), C('#2A3A54')])))
    with inked(cv, 4):
        for side in (-1, 1):                                                                      # steel shelves with frosted boxes
            x0 = 540 + side * 380
            cv.drawRect(skia.Rect(min(x0, x0 + side * 200), 300, max(x0, x0 + side * 200), 1500), paint('#7A8A9A'))
            for k in range(5):
                y = 400 + k * 230
                cv.drawRect(skia.Rect(min(x0, x0 + side * 200), y, max(x0, x0 + side * 200), y + 14), paint('#B8C8D8'))
                cv.drawRect(skia.Rect(min(x0, x0 + side * 200) + 20, y - 90, max(x0, x0 + side * 200) - 30, y), paint('#D8E8F0'))
        cv.drawRect(skia.Rect(320, 260, 760, 1500), paint('#6A7A8C'))                            # the back wall + EXIT door
        cv.drawRect(skia.Rect(420, 700, 660, 1500), paint('#8A9AAC'))
        cv.drawRoundRect(skia.Rect(470, 640, 610, 690), 8, 8, paint('#3AA05A'))
    text(cv, 'EXIT', 540, 680, 40, '#FFFFFF')
    cv.drawLine(420, 1100, 660, 1060, paint('#C8C8D0', style='stroke', width=10))                  # chain on the EXIT (choice 3 risk)
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#000000', shader=lin((0, 1500), (0, H), [C('#8A9AAC'), C('#4A5A6C')])))
    for k in range(40):                                                                            # frost specks
        cv.drawCircle((k * 137) % W, (k * 211) % 1500, 3, paint(C('#FFFFFF', 0.5)))
    glow(cv, (540, 300), 900, ICE, 0.25)


def shot_FREEZER(cv, t):
    """Inside the walk-in freezer: both crouched, shaking with cold; Mika's breath fogs... Tara's does not (hidden detail).
    Tara's ankle bleeds through her jeans (bitten at the gate)."""
    freezer_room(cv, t)
    u = t - B['freezer']
    slam = max(0.0, 1 - u / 0.3)
    shiver = 6 * math.sin(t * 40)
    with inked(cv, 6):
        mascot(cv, 330 + shiver, 1900, 0.95, crouch=1.0, light_side=1, rim=ICE, rim_a=0.6,
               **dict(MIKA, brow=1.0, mouth='o', mouth_open=talk(t, 'K'), sweat=False, pupil=0.6, look=(0.6 if t > s('K05') else 0.0, 0.0)))
        tara_cold = min(1.0, max(0.0, (t - B['freezer']) / 4.0))
        mascot(cv, 760, 1910, 0.92, crouch=1.0, light_side=1, rim=ICE, rim_a=0.6, head_tilt=-6,
               **dict(TARA, skin='#E8D0C8', skin_sh='#B8A8B0', brow=0.6, mouth='o', lids=0.3 + 0.2 * tara_cold, pupil=0.5,
                      pupil_col='#3A3030', sweat=False))
    cv.drawPath(blob([(690, 1830), (760, 1820), (770, 1880), (700, 1890)]), paint('#8A1414'))       # blood at her ankle
    breath(cv, 410, 1310, t, 1.0, 0)                                                                # Mika's breath
    breath(cv, 840, 1330, t, 1.0, 2, on=t < B['freezer'] + 1.0)                                     # Tara's stops early
    if slam > 0:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#FFFFFF', 0.25 * slam)))
    shade(cv, (540, 1100), 1150, 0.45)
    grain(cv, t)


def shot_CU_T(cv, t):
    """Tara close: veins creeping up her neck, eyes clouding as she talks; she stands up (camera follows her up)."""
    freezer_room(cv, t)
    dim(cv, 0.2)
    k = min(1.0, max(0.0, (t - s('T01')) / max(1.0, e('T02') - s('T01'))))
    rise = max(0.0, (t - s('T02')) / 0.8)
    P = dict(TARA, skin='#E0C8C0', skin_sh='#B0A0A8', brow=1.0, mouth='o' if talk(t, 'T') == 0 else 'open', mouth_open=talk(t, 'T'),
             pupil=0.55, iris='#8A7A70' if k < 0.5 else '#B8C0C4', pupil_col='#2A2020' if k < 0.7 else '#6A7074', look=(0.3, 0.0),
             head_tilt=-4 + 3 * math.sin(t * 1.7))
    with inked(cv, 8):
        o = mascot(cv, 540 + 4 * math.sin(t * 30), 2800 - 200 * min(1.0, rise), 2.0, light_side=1, rim=ICE, rim_a=0.6, **P)
    hx, hy = o['head']
    for j in range(5):                                                                              # veins
        x0 = hx - 120 + j * 55
        cv.drawPath(poly([(x0, hy + 520), (x0 + 15, hy + 420 - 120 * k), (x0 - 10, hy + 330 - 160 * k)], closed=False),
                    paint(C('#3A4A6A', 0.3 + 0.6 * k), style='stroke', width=6))
    shade(cv, (540, 950), 1050, 0.45)
    grain(cv, t)


def shot_DOORLOCK(cv, t):
    """Freezer door from inside: Tara steps out (silhouette through the small frosted window), Mika slams the latch."""
    u = t - B['lock']
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#4A5A6C'))
    with inked(cv, 6):
        cv.drawRect(skia.Rect(200, 260, 880, 1700), paint('#9AAABA'))
        cv.drawRect(skia.Rect(380, 520, 700, 900), paint('#C8D8E4'))                                  # frosted window
    with blurred(cv, 10):
        sx = 540 + min(1.0, u / 0.8) * 260
        mascot(cv, sx, 1500, 0.65, view='back', **dict(TARA, skin='#5A6070', skin_sh='#4A5060', shirt='#3A4A44', hair='#6A3A1E'))
    lx = 250 + min(1.0, max(0.0, (u - 0.5) / 0.2)) * 200                                               # latch slams across
    with inked(cv, 5):
        cv.drawRect(skia.Rect(240, 1080, 700, 1120), paint('#5A6A7A'))
        cv.drawRoundRect(skia.Rect(lx, 1060, lx + 120, 1140), 12, 12, paint('#D8D8E0'))
        cv.drawCircle(lx - 30, 1180, 70, paint(MIKA['skin']))                                        # your hand on it
    shade(cv, (540, 950), 1100, 0.45)
    grain(cv, t)


def shot_STORE(cv, t):
    """Tara runs out into the store yelling, waving; the gate bursts; the horde floods in, sprinting at her. Camera tracks her."""
    u = t - B['out']
    cam = Cam(2.0 + u * 0.8, eye=1.5, vy=880, x=-0.2 + u * 0.3, f=860)
    store_aisle(cv, cam, t)
    tz = cam.z + 3.0
    tx, ty = cam.p(0.1 + 0.15 * math.sin(t * 3), 0, tz)
    with inked(cv, 6):
        mascot(cv, tx, ty, cam.scale(tz, 1.55), view='back', walk=(t * 2.6) % 1, run=True, arm_r=(160, 10), arm_l=(150, 20),
               light_side=1, rim=FLUO, rim_a=0.4, **TARA)
    for k in range(10):                                                                             # horde sprinting toward her
        zz = cam.z + 9.0 - min(1.0, u / 1.5) * 5.0 + (k % 4) * 0.6
        zx, zy = cam.p(-0.7 + (k % 5) * 0.35, 0, zz)
        with inked(cv, 3):
            mascot(cv, zx, zy, cam.scale(zz, 1.6), walk=(t * 3 + k * 0.29) % 1, run=True, arm_r=(85, 10), arm_l=(80, 15),
                   light_side=1, rim=FLUO, rim_a=0.3, **zomb(k))
    shade(cv, (540, 900), 1150, 0.45)
    grain(cv, t)


def shot_SWARM(cv, t):
    """JS1: they leap. Zombies fly at the camera over her, mid-air, arms out."""
    u = t - B['js1']
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A0A0A'))
    for k in range(5):
        sc = 0.9 + u * 2.4 + k * 0.25
        x = 540 + (k - 2) * 260 * (1 + u)
        y = 2600 - k * 120 + u * 300
        with inked(cv, 8):
            mascot(cv, x, y, sc, arm_r=(150, 10), arm_l=(150, 10), **dict(zomb(k), mouth='wide', brow=-1.0))
    dim(cv, 0.2, '#3A0404')
    grain(cv, t, 0.14)


def glass_door(cv, t, blood=0.0, shadow=None, knocks=None):
    """From inside the freezer: the steel door, the small frosted window, what moves behind it."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A4A5C'))
    with inked(cv, 6):
        cv.drawRect(skia.Rect(140, 200, 940, 1800), paint('#8A9AAA'))
    jolt = 0
    for k0 in (knocks or []):
        if k0 <= t < k0 + 0.1:
            jolt = 10
    win = skia.Rect(300 + jolt, 420, 780 + jolt, 1020)
    cv.drawRect(win, paint('#C8D8E4'))
    cv.save(); cv.clipRect(win)
    if shadow:
        shadow(cv, t)
    if blood > 0:                                                                                  # blood hits the glass, runs down
        for k in range(7):
            bx = 360 + k * 60
            cv.drawCircle(bx, 600 + (k * 37) % 120, 30 + (k % 3) * 18, paint(C('#8A0A0A', 0.9 * blood)))
            cv.drawRect(skia.Rect(bx - 6, 600, bx + 6, 600 + 380 * blood * (0.4 + (k % 3) * 0.3)), paint(C('#8A0A0A', 0.85 * blood)))
    cv.drawRect(win, paint(C('#E8F0F8', 0.35)))                                                    # frost
    cv.restore()
    with inked(cv, 4):
        cv.drawRect(skia.Rect(win.left() - 14, 1080, win.left() + 460, 1120), paint('#5A6A7A'))      # the latch (locked)
        cv.drawRoundRect(skia.Rect(450, 1060, 570, 1140), 12, 12, paint('#D8D8E0'))
    glow(cv, (540, 300), 800, ICE, 0.2)


def shot_GLASS(cv, t):
    def sil(cv, t):
        if t < s('K06') + 0.5:                                                                      # shapes thrashing, then still
            for k in range(4):
                x = 400 + k * 110 + 60 * math.sin(t * 9 + k)
                with blurred(cv, 14):
                    cv.drawCircle(x, 760 + 40 * math.sin(t * 7 + k), 120, paint(C('#1A1010', 0.8)))
        elif t >= B['knock'] - 0.4:                                                                  # ONE shape steps up to the window
            with blurred(cv, 12):
                mascot(cv, 540, 1500, 0.9, **dict(TARA, skin='#2A3038', skin_sh='#1A2028', shirt='#1A2420', hair='#2A1A10', head_tilt=-14))
    b = min(1.0, max(0.0, (t - B['glass'] - 0.3) / 0.4))
    glass_door(cv, t, blood=b, shadow=sil, knocks=B['knocks'])
    shade(cv, (540, 900), 1100, 0.45)
    grain(cv, t)


def shot_GLASSCU(cv, t):
    """Extreme close-up of the window: your breath fogs YOUR side... her face is right there, and no fog on hers."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#8A9AAA'))
    with blurred(cv, 6):
        with inked(cv, 6):
            mascot(cv, 540, 2600, 1.9, **dict(TARA, skin='#B8C0C0', skin_sh='#8A9294', iris='#D0D8DC', pupil_col='#9AA2A6', mouth='smile',
                                             brow=0.0, head_tilt=-12, look=(0.0, 0.0)))
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#E8F0F8', 0.3)))
    for k in range(5):                                                                               # blood streaks still on the glass
        cv.drawRect(skia.Rect(150 + k * 190, 0, 165 + k * 190, 600 + k * 90), paint(C('#7A0A0A', 0.7)))
    ph = (t * 0.6) % 1.0                                                                              # YOUR breath fogging the glass
    cv.drawCircle(540, 1500, 260 + 120 * ph, paint(C('#FFFFFF', 0.4 * (1 - ph)), blur=40))
    grain(cv, t)


def shot_CHOICE(cv, t):
    """Back against the EXIT door, the window with her shape, the handle starting to turn."""
    def sil(cv, t):
        with blurred(cv, 10):
            mascot(cv, 540, 1500, 0.9, **dict(TARA, skin='#2A3038', skin_sh='#1A2028', shirt='#1A2420', hair='#2A1A10', head_tilt=-14 + 6 * math.sin(t * 2)))
    glass_door(cv, t, blood=1.0, shadow=sil)
    with inked(cv, 7):                                                                                 # you, in the foreground, backing away
        mascot(cv, 860, 2200, 1.15, view='back', light_side=1, rim=ICE, rim_a=0.6, **MIKA)
    breath(cv, 760, 1180, t, 1.2, 0)
    shade(cv, (540, 950), 1100, 0.5)
    grain(cv, t)


def shot_SLAM(cv, t):
    """JS2: Tara's turned face SLAMS the glass, mouth open, milky eyes."""
    u = t - B['js2']
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A3A4C'))
    with inked(cv, 10):
        mascot(cv, 540, 3400 - 200 * min(1.0, u / 0.1), 2.8, **dict(TARA, skin='#A8B0AC', skin_sh='#808886', iris='#E0E8EC', pupil_col='#B0B8BC',
                                                                    mouth='wide', brow=-1.0, head_tilt=8))
    for k in range(6):
        cv.drawLine(540, 900, 540 + math.cos(k) * 900, 900 + math.sin(k) * 900, paint(C('#FFFFFF', 0.6), style='stroke', width=4))   # cracks
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#E8F0F8', 0.15)))
    grain(cv, t, 0.15)


SHOTS = {k[5:]: v for k, v in dict(globals()).items() if k.startswith('shot_')}


def needed():
    out = []
    for sgm in E.SEGMENTS:
        if sgm['src'] is None:
            continue
        f0, f1 = int(round(sgm['t0'] * FPS)), int(round(sgm['t1'] * FPS))
        out += [(sgm['src'], f) for f in range(f0, f1 + 1)]
    return sorted(set(out))


def draw(job_frame):
    job, f = job_frame
    p = os.path.join(OUT, job, f'{f:04d}.png')
    if os.path.exists(p):
        return
    surf = skia.Surface(W, H)
    SHOTS[job](surf.getCanvas(), f / FPS)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    surf.makeImageSnapshot().save(p, skia.kPNG)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--still', nargs='*', default=None)
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    OUT = a.out
    todo = [(x.split(':')[0], int(x.split(':')[1])) for x in a.still] if a.still else needed()
    with Pool(a.procs) as pool:
        for i, _ in enumerate(pool.imap_unordered(draw, todo, chunksize=4)):
            if i % 400 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
