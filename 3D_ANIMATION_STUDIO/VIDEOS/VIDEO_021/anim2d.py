#!/usr/bin/env python3
"""VIDEO_021 "My Mother Isn't Real" — real 2D horror (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_016/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]

House: one fixed layout (hallway / kitchen / basement) reused by every shot so the map never changes.
"""
import argparse
import math
import os
import sys
from multiprocessing import Pool

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'twod'))
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, lin, mascot, purser, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video021 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS, JS, s, e = E.B, E.LS, E.WORDS, E.JS, E.s, E.e
MOON = '#9FD0C8'          # blue-green moonlight
TUNG = '#FFC27A'          # weak tungsten

CAST = {
    'M': dict(),
    'O': dict(long_hair=True, hair='#5A3A24', hair_sh='#3E2616', shirt='#B07A8A', shirt_sh='#8A5A6A', skin='#F0C8A8', skin_sh='#D0A486',
              pants='#3A3A4A', pants_sh='#2A2A36'),
    'P': dict(long_hair=True, hair='#3E2A1C', hair_sh='#24180E', shirt='#7A7470', shirt_sh='#5A5450', skin='#D8B094', skin_sh='#B08A70',
              pants='#3A3A4A', pants_sh='#2A2A36'),
}


def talk(t, who):
    return mouth_open(t, WORDS, [l['id'] for l in E._T['lines'] if l['id'][0] == who])


# ===================================================================== depth toolkit
import numpy as np  # noqa: E402

NIGHT, RED, WARM, SCREEN = '#7A9AD8', '#E0342C', '#FFD9A0', '#7FB8FF'
_rng = np.random.default_rng(18)
_g = (_rng.normal(128, 40, (512, 512))).clip(0, 255).astype(np.uint8)
GRAIN = skia.Image.fromarray(np.dstack([_g, _g, _g, np.full_like(_g, 255)]))


def grain(cv, t, a=0.07):
    p = skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kOverlay)
    ox, oy = int(t * 997) % 512, int(t * 613) % 512
    for x in range(-ox, W, 512):
        for y in range(-oy, H, 512):
            cv.drawImage(GRAIN, x, y, skia.SamplingOptions(), p)


class blurred:
    """with blurred(cv, 8): ... -> everything drawn inside is out of focus (depth of field)."""
    def __init__(self, cv, s):
        self.cv, self.s = cv, s

    def __enter__(self):
        self.cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(self.s, self.s)))

    def __exit__(self, *a):
        self.cv.restore()


MOON, DAY, TORCH, HALLWARM = '#7A9AD8', '#FFE2B8', '#E8F0FF', '#FFC27A'
GOLD = '#E8C050'


def blur_rect(cv, r, col, s_=6):
    with blurred(cv, s_):
        cv.drawRect(r, paint(col))


def ring(cv, x, y, sc=1.0):
    """The wedding ring (hidden detail): a small gold band with a glint."""
    cv.drawCircle(x, y, 13 * sc, paint(GOLD, style='stroke', width=7 * sc))
    cv.drawCircle(x - 5 * sc, y - 6 * sc, 3 * sc, paint('#FFFFFF'))


def clock(cv, x, y, r, col='#F4F0E6'):
    """Every clock in this house says 11:47 (hidden detail)."""
    cv.drawCircle(x, y, r, paint(col))
    cv.drawCircle(x, y, r, paint('#2A2420', style='stroke', width=r * 0.08))
    for k in range(12):
        a = math.radians(k * 30)
        cv.drawLine(x + math.sin(a) * r * 0.8, y - math.cos(a) * r * 0.8, x + math.sin(a) * r * 0.9, y - math.cos(a) * r * 0.9, paint('#2A2420', style='stroke', width=r * 0.04))
    ah, am = math.radians(11 * 30 + 47 * 0.5), math.radians(47 * 6)
    cv.drawLine(x, y, x + math.sin(ah) * r * 0.5, y - math.cos(ah) * r * 0.5, paint('#1A1410', style='stroke', width=r * 0.08))
    cv.drawLine(x, y, x + math.sin(am) * r * 0.75, y - math.cos(am) * r * 0.75, paint('#1A1410', style='stroke', width=r * 0.05))


def wood(cv, q, cam, a, b, n, col0, col1):
    """Floor planks between z=a..b (perspective lines) clipped to quad q."""
    cv.save(); cv.clipPath(q, skia.ClipOp.kIntersect, True)
    cv.drawPath(q, paint('#000000', shader=lin((0, H), cam.p(0, 0, b), [C(col0), C(col1)])))
    for k in range(n + 1):
        x = -1.2 + 2.4 * k / n
        p0, p1 = cam.p(x, 0, a), cam.p(x, 0, b)
        cv.drawLine(p0[0], p0[1], p1[0], p1[1], paint(C('#000000', 0.25), style='stroke', width=3))
    for z in range(int(a), int(b)):
        for k in range(n):
            if (k + z) % 3 == 0:
                x = -1.2 + 2.4 * k / n
                p0, p1 = cam.p(x, 0, z + 0.5 * (k % 2)), cam.p(x + 2.4 / n, 0, z + 0.5 * (k % 2))
                cv.drawLine(p0[0], p0[1], p1[0], p1[1], paint(C('#000000', 0.2), style='stroke', width=2))
    cv.restore()


def wallpaper(cv, q, col0, col1, seed=0):
    cv.save(); cv.clipPath(q, skia.ClipOp.kIntersect, True)
    r = q.getBounds()
    cv.drawRect(r, paint('#000000', shader=lin((r.left(), 0), (r.right(), 0), [C(col0), C(col1)])))
    for x in range(int(r.left()), int(r.right()), 36):                               # faint vertical stripes + damask dots
        cv.drawLine(x, r.top(), x, r.bottom(), paint(C('#000000', 0.06), style='stroke', width=8))
    cv.restore()


# ===================================================================== HALLWAY (night) — fixed layout
HALL_DOOR = (2.6, 3.5)          # basement door on the right wall, z range
STAIRS_Z = (4.0, 8.0)           # stairs going up along the right wall


def hall(cv, t, cam=None, door_light=0.0, door_open=0.0):
    cam = cam or Cam(0.2, eye=1.45, vy=840, x=0.05, f=880)
    q = lambda pts: quad(cam, pts)  # noqa
    Z1 = 9.0
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#05070C'))
    cv.drawPath(q([(-1.2, 2.6, 0.3), (1.2, 2.6, 0.3), (1.2, 2.6, Z1), (-1.2, 2.6, Z1)]), paint('#000000', shader=lin((0, 0), cam.p(0, 2.6, Z1), [C('#0A0C14'), C('#1A1E2C')])))
    lw = q([(-1.2, 0, 0.3), (-1.2, 2.6, 0.3), (-1.2, 2.6, Z1), (-1.2, 0, Z1)])
    rw = q([(1.2, 0, 0.3), (1.2, 2.6, 0.3), (1.2, 2.6, Z1), (1.2, 0, Z1)])
    wallpaper(cv, lw, '#1A2232', '#2A3448')
    wallpaper(cv, rw, '#2A3448', '#161C2A')
    fl = q([(-1.2, 0, 0.3), (1.2, 0, 0.3), (1.2, 0, Z1), (-1.2, 0, Z1)])
    wood(cv, fl, cam, 0.3, Z1, 8, '#2A1E16', '#4A3626')
    cv.drawPath(q([(-0.55, 0.003, 0.6), (0.55, 0.003, 0.6), (0.55, 0.003, 7.5), (-0.55, 0.003, 7.5)]), paint('#4A2228'))          # runner rug
    cv.drawPath(q([(-0.45, 0.004, 0.8), (0.45, 0.004, 0.8), (0.45, 0.004, 7.3), (-0.45, 0.004, 7.3)]), paint(C('#C8A060', 0.25), style='stroke', width=4))
    for side in (-1, 1):                                                                  # skirting boards
        cv.drawPath(q([(side * 1.199, 0, 0.3), (side * 1.199, 0.14, 0.3), (side * 1.199, 0.14, Z1), (side * 1.199, 0, Z1)]), paint('#C8C0B0'))
    # end wall + kitchen doorway (dark at night)
    cv.drawPath(q([(-1.2, 0, Z1), (1.2, 0, Z1), (1.2, 2.6, Z1), (-1.2, 2.6, Z1)]), paint('#1E2636'))
    cv.drawPath(q([(-0.5, 0, Z1 - 0.01), (0.5, 0, Z1 - 0.01), (0.5, 2.1, Z1 - 0.01), (-0.5, 2.1, Z1 - 0.01)]), paint('#07080C'))
    # left wall: window with moon, family photos, side table with a lamp + phone, night-light
    cv.drawPath(q([(-1.19, 1.1, 6.6), (-1.19, 2.0, 6.6), (-1.19, 2.0, 7.4), (-1.19, 1.1, 7.4)]), paint('#0E1A34'))
    cv.drawPath(q([(-1.19, 1.1, 6.6), (-1.19, 2.0, 6.6), (-1.19, 2.0, 7.4), (-1.19, 1.1, 7.4)]), paint('#C8C0B0', style='stroke', width=6))
    wx, wy = cam.p(-1.2, 1.6, 7.0)
    glow(cv, (wx, wy), 380, MOON, 0.35)
    cv.drawPath(q([(-1.2, 0.002, 6.4), (-0.3, 0.002, 7.1), (-0.2, 0.002, 8.0), (-1.2, 0.002, 7.6)]), paint(C(MOON, 0.12)))   # moonlight on the floor
    for (z0, z1, h0, h1, kind) in ((2.0, 2.9, 1.3, 1.95, 'family'), (3.5, 4.0, 1.45, 1.85, 'small'), (4.6, 5.1, 1.4, 1.9, 'small')):
        fr = q([(-1.19, h0, z0), (-1.19, h1, z0), (-1.19, h1, z1), (-1.19, h0, z1)])
        cv.drawPath(fr, paint('#6A4A2A'))
        inner = q([(-1.188, h0 + 0.06, z0 + 0.06), (-1.188, h1 - 0.06, z0 + 0.06), (-1.188, h1 - 0.06, z1 - 0.06), (-1.188, h0 + 0.06, z1 - 0.06)])
        cv.drawPath(inner, paint('#8A9AA8'))
        if kind == 'family':                                                             # mom + you in the photo; mom's face scratched out
            for k, (zz, col) in enumerate(((z0 + 0.3, '#B07A8A'), (z0 + 0.62, '#E87A20'))):
                hx, hy = cam.p(-1.188, h0 + 0.38, zz)
                rr = cam.scale(zz, 0.09) * 1150
                cv.drawCircle(hx, hy, rr, paint('#F0C8A8'))
                cv.drawRect(skia.Rect(hx - rr, hy + rr, hx + rr, hy + rr * 2.4), paint(col))
                if k == 0:
                    for j in range(5):
                        cv.drawLine(hx - rr, hy - rr + j * rr * 0.4, hx + rr, hy - rr * 0.6 + j * rr * 0.4, paint('#1A1410', style='stroke', width=3))
    for z0 in (5.8,):
        cv.drawPath(q([(-1.2, 0.8, z0), (-0.85, 0.8, z0), (-0.85, 0.8, z0 + 0.6), (-1.2, 0.8, z0 + 0.6)]), paint('#5A3A22'))
        cv.drawPath(q([(-0.85, 0, z0), (-0.85, 0.8, z0), (-0.85, 0.8, z0 + 0.6), (-0.85, 0, z0 + 0.6)]), paint('#3A2414'))
        lx, ly = cam.p(-1.0, 1.1, z0 + 0.3)
        cv.drawPath(poly([(lx - 22, ly), (lx + 22, ly), (lx + 32, ly + 34), (lx - 32, ly + 34)]), paint('#C8B8A0'))
    nx, ny = cam.p(-1.19, 0.3, 4.4)
    glow(cv, (nx, ny), 90, '#9FE0B0', 0.5)                                                # night-light
    cv.drawCircle(nx, ny, 6, paint('#CFF0D8'))
    # stairs up along the right wall (beyond the basement door)
    z0, z1 = STAIRS_Z
    n = 13
    for k in range(n, -1, -1):
        za = z0 + (z1 - z0) * k / n
        hh = 2.6 * k / n
        cv.drawPath(q([(0.35, hh, za), (1.2, hh, za), (1.2, hh, za + (z1 - z0) / n), (0.35, hh, za + (z1 - z0) / n)]), paint('#5A3E28' if k % 2 else '#4E3422'))
        cv.drawPath(q([(0.35, hh - 2.6 / n, za), (1.2, hh - 2.6 / n, za), (1.2, hh, za), (0.35, hh, za)]), paint('#2E2016'))
    cv.drawPath(q([(0.35, 0, z0), (0.35, 0, z1), (0.35, 2.6, z1)]), paint('#24180F'))       # stair side panel
    for k in range(9):                                                                     # banister + spindles
        za = z0 + (z1 - z0) * k / 8
        a0, a1 = cam.p(0.36, 2.6 * k / 8 + 0.02, za), cam.p(0.36, 2.6 * k / 8 + 0.95, za)
        cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint('#D8D0C0', style='stroke', width=max(2, cam.scale(za, 0.03) * 1150)))
    b0, b1 = cam.p(0.36, 0.95, z0), cam.p(0.36, 2.6 + 0.95, z1)
    cv.drawLine(b0[0], b0[1], b1[0], b1[1], paint('#6A4A2A', style='stroke', width=14))
    np_ = cam.p(0.36, 1.1, z0)
    cv.drawRect(skia.Rect(np_[0] - 14, np_[1], np_[0] + 14, cam.p(0.36, 0, z0)[1]), paint('#6A4A2A'))          # newel post
    # the basement door (right wall)
    d0, d1 = HALL_DOOR
    frame = q([(1.19, 0, d0 - 0.08), (1.19, 2.15, d0 - 0.08), (1.19, 2.15, d1 + 0.08), (1.19, 0, d1 + 0.08)])
    cv.drawPath(frame, paint('#D8D0C0'))
    door = q([(1.188, 0, d0), (1.188, 2.05, d0), (1.188, 2.05, d1), (1.188, 0, d1)])
    cv.drawPath(door, paint('#000000', shader=lin(cam.p(1.2, 1, d0), cam.p(1.2, 1, d1), [C('#E8E2D6'), C('#B8B0A4')])))
    for (h0, h1) in ((0.2, 0.95), (1.1, 1.85)):
        cv.drawPath(q([(1.186, h0, d0 + 0.12), (1.186, h1, d0 + 0.12), (1.186, h1, d1 - 0.12), (1.186, h0, d1 - 0.12)]), paint(C('#8A8478', 0.6), style='stroke', width=4))
    if door_open > 0:
        cv.drawPath(q([(1.186, 0, d0), (1.186, 2.05, d0), (1.186, 2.05, d0 + (d1 - d0) * door_open), (1.186, 0, d0 + (d1 - d0) * door_open)]), paint('#030304'))
    kx, ky = cam.p(1.185, 1.0, d1 - 0.1)
    cv.drawCircle(kx, ky, max(6, cam.scale(d1, 0.04) * 1150), paint('#C8A050'))
    if door_light > 0:                                                                     # light under the basement door
        a0, a1 = cam.p(1.18, 0.01, d0), cam.p(1.18, 0.01, d1)
        cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C('#FFE6B0', 0.9 * door_light), style='stroke', width=5))
        glow(cv, ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2), 160, HALLWARM, 0.35 * door_light)
    with blurred(cv, 8):                                                                  # haze toward the kitchen
        vx, vy = cam.p(0, 1.2, Z1)
        cv.drawCircle(vx, vy, 500, paint('#000000', shader=rad((vx, vy), 500, [C('#3A4A6A', 0.35), C('#000000', 0.0)])))
    return cam


def hall_people(cv, t, cam, mom_z=None, you=True, reach=True):
    if mom_z is not None:                                                                  # Mom in the dark hallway, smiling
        mx, my = cam.p(-0.25, 0, mom_z)
        P = dict(CAST['O'], mouth='smile', brow=0.0, lids=0.15, pupil=0.6, look=(0.6, 0.0), mouth_open=talk(t, 'O'))
        if P['mouth_open'] > 0:
            P['mouth'] = 'open'
        mascot(cv, mx, my, cam.scale(mom_z, 1.65), light_side=-1, rim=MOON, rim_a=0.5, **P)
        dim_ = paint(C('#05070C', 0.45))
        cv.drawCircle(mx, my - cam.scale(mom_z, 1.65) * 900, cam.scale(mom_z, 1.65) * 420, paint(C('#000000', 0.0)))
    if you:
        yx, yy = cam.p(0.72, 0, 2.2)
        P = dict(view='back', arm_r=(62, 18) if reach else (3, 0), light_side=1, rim=MOON, rim_a=0.4)
        mascot(cv, yx, yy, cam.scale(2.2, 1.45), **P)


# ===================================================================== KITCHEN (morning) — fixed layout
def kitchen(cv, t, mom=True, mom_t=None):
    cam = Cam(0.0, eye=1.25, vy=900, f=820)
    q = lambda pts: quad(cam, pts)  # noqa
    Z1 = 4.6
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2420'))
    cv.drawPath(q([(-2.2, 2.7, 0.2), (2.2, 2.7, 0.2), (2.2, 2.7, Z1), (-2.2, 2.7, Z1)]), paint('#000000', shader=lin((0, 0), (0, 500), [C('#C8BCA8'), C('#E8DCC8')])))
    for side, cols in ((-1, ('#C8B898', '#E0D2B4')), (1, ('#E0D2B4', '#C0B090'))):
        cv.drawPath(q([(side * 2.2, 0, 0.2), (side * 2.2, 2.7, 0.2), (side * 2.2, 2.7, Z1), (side * 2.2, 0, Z1)]),
                    paint('#000000', shader=lin(cam.p(side * 2.2, 1, 0.4), cam.p(side * 2.2, 1, Z1), [C(cols[0]), C(cols[1])])))
    fl = q([(-2.2, 0, 0.2), (2.2, 0, 0.2), (2.2, 0, Z1), (-2.2, 0, Z1)])
    cv.save(); cv.clipPath(fl, skia.ClipOp.kIntersect, True)                                # checker tiles
    cv.drawPath(fl, paint('#D8D0C0'))
    for i in range(-6, 6):
        for z in range(0, 10):
            if (i + z) % 2 == 0:
                cv.drawPath(q([(i * 0.4, 0.001, 0.2 + z * 0.45), ((i + 1) * 0.4, 0.001, 0.2 + z * 0.45), ((i + 1) * 0.4, 0.001, 0.65 + z * 0.45), (i * 0.4, 0.001, 0.65 + z * 0.45)]), paint('#6A6A70'))
    cv.restore()
    bw = q([(-2.2, 0, Z1), (2.2, 0, Z1), (2.2, 2.7, Z1), (-2.2, 2.7, Z1)])
    cv.drawPath(bw, paint('#E6D8BC'))
    tiles = q([(-2.2, 0.9, Z1 - 0.01), (2.2, 0.9, Z1 - 0.01), (2.2, 1.5, Z1 - 0.01), (-2.2, 1.5, Z1 - 0.01)])
    cv.save(); cv.clipPath(tiles, skia.ClipOp.kIntersect, True)
    cv.drawPath(tiles, paint('#E8EEF0'))
    for k in range(-30, 30):
        a0, a1 = cam.p(k * 0.15, 0.9, Z1 - 0.01), cam.p(k * 0.15, 1.5, Z1 - 0.01)
        cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint('#B8C4C8', style='stroke', width=2))
    for hh in (1.05, 1.2, 1.35):
        a0, a1 = cam.p(-2.2, hh, Z1 - 0.01), cam.p(2.2, hh, Z1 - 0.01)
        cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint('#B8C4C8', style='stroke', width=2))
    cv.restore()
    for x0 in (-2.2, -1.4, -0.6, 0.9, 1.6):                                                   # upper cabinets
        if -0.6 <= x0 < 0.9:
            continue
        cv.drawPath(q([(x0 + 0.03, 1.75, Z1 - 0.3), (x0 + 0.72, 1.75, Z1 - 0.3), (x0 + 0.72, 2.6, Z1 - 0.3), (x0 + 0.03, 2.6, Z1 - 0.3)]), paint('#6A8A7A'))
        cv.drawPath(q([(x0 + 0.08, 1.8, Z1 - 0.31), (x0 + 0.67, 1.8, Z1 - 0.31), (x0 + 0.67, 2.55, Z1 - 0.31), (x0 + 0.08, 2.55, Z1 - 0.31)]), paint('#4A6A5A', style='stroke', width=4))
    cv.drawPath(q([(-2.2, 0, Z1 - 0.6), (2.2, 0, Z1 - 0.6), (2.2, 0.9, Z1 - 0.6), (-2.2, 0.9, Z1 - 0.6)]), paint('#5A7A6A'))   # lower cabinets
    cv.drawPath(q([(-2.2, 0.9, Z1 - 0.6), (2.2, 0.9, Z1 - 0.6), (2.2, 0.9, Z1), (-2.2, 0.9, Z1)]), paint('#C8C0B4'))         # counter top
    for x0 in (-2.0, -1.3, 0.2, 0.9, 1.5):
        cv.drawPath(q([(x0, 0.1, Z1 - 0.61), (x0 + 0.6, 0.1, Z1 - 0.61), (x0 + 0.6, 0.8, Z1 - 0.61), (x0, 0.8, Z1 - 0.61)]), paint('#3E5A4A', style='stroke', width=3))
    cv.drawPath(q([(-0.6, 0, Z1 - 0.62), (0.3, 0, Z1 - 0.62), (0.3, 0.9, Z1 - 0.62), (-0.6, 0.9, Z1 - 0.62)]), paint('#2A2A2E'))   # stove
    cv.drawPath(q([(-0.5, 0.15, Z1 - 0.63), (0.2, 0.15, Z1 - 0.63), (0.2, 0.7, Z1 - 0.63), (-0.5, 0.7, Z1 - 0.63)]), paint('#0E0E10'))
    cv.drawPath(q([(-0.6, 1.75, Z1 - 0.35), (0.3, 1.75, Z1 - 0.35), (0.2, 2.2, Z1 - 0.2), (-0.5, 2.2, Z1 - 0.2)]), paint('#8A8A90'))  # hood
    # window over the sink (right), morning light; reflection of Mom staring (hidden detail)
    wq = q([(0.7, 1.15, Z1 - 0.01), (1.9, 1.15, Z1 - 0.01), (1.9, 2.3, Z1 - 0.01), (0.7, 2.3, Z1 - 0.01)])
    cv.drawPath(wq, paint('#000000', shader=lin(cam.p(0, 2.3, Z1), cam.p(0, 1.15, Z1), [C('#BFE0F4'), C('#FFF0D8')])))
    cv.save(); cv.clipPath(wq, skia.ClipOp.kIntersect, True)
    rx, ry = cam.p(1.0, 1.15, Z1)
    P = dict(CAST['O'], mouth='flat', brow=-0.4, pupil=0.4, look=(0.0, 0.0))
    mascot(cv, rx + 30, ry + 120, cam.scale(Z1, 1.5) * 0.9, light_side=1, **P)
    cv.drawRect(wq.getBounds(), paint(C('#FFFFFF', 0.55)))
    cv.restore()
    cv.drawPath(wq, paint('#F4F0E6', style='stroke', width=10))
    c0, c1 = cam.p(1.3, 1.15, Z1), cam.p(1.3, 2.3, Z1)
    cv.drawLine(c0[0], c0[1], c1[0], c1[1], paint('#F4F0E6', style='stroke', width=6))
    glow(cv, cam.p(1.3, 1.7, Z1), 700, DAY, 0.35)
    cv.drawPath(q([(0.5, 0.002, 1.0), (1.9, 0.002, 1.6), (1.6, 0.002, 3.8), (0.6, 0.002, 3.6)]), paint(C(DAY, 0.18)))    # sun patch on the floor
    clock(cv, *cam.p(-1.6, 2.35, Z1), cam.scale(Z1, 0.22) * 1150)                              # wall clock 11:47
    mw = q([(-2.15, 1.05, Z1 - 0.15), (-1.45, 1.05, Z1 - 0.15), (-1.45, 1.45, Z1 - 0.15), (-2.15, 1.45, Z1 - 0.15)])            # microwave 11:47
    cv.drawPath(mw, paint('#3A3A40'))
    mx_, my_ = cam.p(-1.6, 1.25, Z1 - 0.16)
    text(cv, '11:47', mx_, my_ + 12, cam.scale(Z1, 0.12) * 1150, '#7AF07A')
    cv.drawPath(q([(2.2, 0, 1.6), (2.2, 2.0, 1.6), (2.2, 2.0, 2.6), (2.2, 0, 2.6)]), paint('#E8E8EC'))              # fridge on the right wall
    for k, (zz, hh, col) in enumerate(((1.8, 1.5, '#E8B040'), (2.2, 1.2, '#7AB0E0'), (2.0, 0.9, '#E07A7A'))):        # drawings on the fridge
        cv.drawPath(q([(2.19, hh, zz), (2.19, hh + 0.3, zz), (2.19, hh + 0.3, zz + 0.25), (2.19, hh, zz + 0.25)]), paint(col))
    # Mom at the stove, back to us, flipping a pancake (the same flip, every morning)
    if mom:
        tt = mom_t if mom_t is not None else t
        mx, my = cam.p(-0.15, 0, Z1 - 0.95)
        flip = (tt * 0.8) % 1.0
        P = dict(CAST['O'], view='back', arm_r=(55 + 25 * math.sin(flip * 2 * math.pi), 40), light_side=1, rim=DAY, rim_a=0.3)
        o = mascot(cv, mx, my, cam.scale(Z1 - 0.95, 1.65), **P)
        hx, hy = o['hand_r']
        cv.drawLine(hx, hy, hx + 40, hy - 70, paint('#3A3A3A', style='stroke', width=10))                         # spatula
        pz = max(0.0, math.sin(flip * math.pi)) * 160
        cv.drawOval(skia.Rect(hx + 10, hy - 110 - pz, hx + 110, hy - 80 - pz), paint('#D8A050'))
    # foreground: the table, your plate of pancakes, orange juice
    cv.drawRect(skia.Rect(0, 1560, W, H), paint('#000000', shader=lin((0, 1560), (0, H), [C('#8A5A36'), C('#5A3A22')])))
    cv.drawOval(skia.Rect(250, 1620, 750, 1800), paint('#F4F0E6'))
    for k in range(3):
        cv.drawOval(skia.Rect(330, 1640 - k * 26, 670, 1740 - k * 26), paint('#D8A050' if k % 2 == 0 else '#C89040'))
    cv.drawRect(skia.Rect(470, 1560, 540, 1610), paint('#F0E0A0'))
    cv.drawRoundRect(skia.Rect(820, 1500, 920, 1720), 14, 14, paint(C('#F8A030', 0.85)))
    glow(cv, (540, 500), 1300, DAY, 0.18)
    shade(cv, (540, 1000), 1300, 0.35)
    return cam


def kitchen_blur(cv, t):
    with blurred(cv, 16):
        kitchen(cv, t, mom=False)


def hall_blur(cv, t):
    with blurred(cv, 14):
        hall(cv, t)


# ===================================================================== BASEMENT — fixed layout
def basement(cv, t, torch=(540, 1100), mom=True, mom_up=0.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#1A1C1E'), C('#0A0B0C')])))
    with blurred(cv, 3):
        cv.drawRect(skia.Rect(0, 1350, W, H), paint('#000000', shader=lin((0, 1350), (0, H), [C('#2A2A28'), C('#121210')])))   # concrete floor
        for k in range(6):                                                                  # water stains on the wall
            x = 80 + k * 180
            cv.drawPath(blob([(x, 300), (x + 60, 320), (x + 40, 700 + (k % 3) * 120), (x + 10, 640)]), paint(C('#0A0A08', 0.4)))
        for y in (150, 210):                                                                # pipes along the ceiling
            cv.drawRect(skia.Rect(0, y, W, y + 34), paint('#4A4440'))
            for x in range(60, W, 260):
                cv.drawRect(skia.Rect(x, y - 6, x + 26, y + 40), paint('#3A3430'))
        cv.drawRect(skia.Rect(40, 700, 300, 1360), paint('#3A2A1E'))                        # shelves with paint cans + boxes
        for k in range(4):
            cv.drawRect(skia.Rect(40, 800 + k * 150, 300, 820 + k * 150), paint('#5A4030'))
            for j in range(3):
                cv.drawRect(skia.Rect(60 + j * 76, 730 + k * 150, 120 + j * 76, 800 + k * 150), paint(['#6A6A70', '#8A5A3A', '#4A6A8A'][(j + k) % 3]))
        cv.drawRoundRect(skia.Rect(820, 760, 1000, 1360), 80, 80, paint('#5A5E62'))           # water heater
        cv.drawLine(910, 760, 910, 230, paint('#4A4440', style='stroke', width=16))
        cv.drawLine(540, 0, 540, 260, paint('#1A1A1A', style='stroke', width=4))            # dead bulb
        cv.drawCircle(540, 280, 26, paint('#3A3A36'))
    mx, my = 560, 1560
    if mom:
        # her shadow on the wall: fingers too long (hidden detail)
        with blurred(cv, 6):
            sx, sy = mx + 140, 1050
            cv.drawPath(blob([(sx - 140, sy + 300), (sx - 120, sy - 120), (sx, sy - 220), (sx + 120, sy - 120), (sx + 150, sy + 300)]), paint(C('#000000', 0.55)))
            for f in range(4):
                cv.drawLine(sx + 150, sy + 40 + f * 22, sx + 360 + f * 30, sy - 60 + f * 50, paint(C('#000000', 0.55), style='stroke', width=14))
        cv.drawLine(900, 760, mx + 90, my - 120, paint('#6A6A6A', style='stroke', width=8))   # chain to the pipe
        for k in range(14):
            a = k / 14
            cv.drawCircle(900 + (mx + 90 - 900) * a, 760 + (my - 120 - 760) * a, 9, paint('#7A7A7A', style='stroke', width=4))
        P = dict(CAST['P'], crouch=1.0, brow=1.0, mouth='o', lids=0.35, pupil=0.5, sweat=True, mouth_open=talk(t, 'P'),
                 look=(0.0, -0.3 * mom_up), head_tilt=-6 + 6 * mom_up)
        if P['mouth_open'] > 0:
            P['mouth'] = 'open'
        o = mascot(cv, mx, my, 1.0, light_side=1, rim=TORCH, rim_a=0.4, **P)
        hx, hy = o['head']
        cv.drawLine(hx - 60, hy - 120, hx + 10, hy - 90, paint('#8A2020', style='stroke', width=7))   # the scar from the crash
        rx, ry = o['hand_r']
        ring(cv, rx, ry - 6, 1.1)
    # flashlight: everything outside the beam is near black
    tx, ty = torch
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=rad((tx, ty), 700, [C('#000000', 0.0), C('#000000', 0.55), C('#000000', 0.92)], [0, 0.55, 1])))
    glow(cv, (tx, ty), 420, TORCH, 0.18)


# ===================================================================== shots
def shot_HOOK(cv, t):
    cam = hall(cv, t)
    mz = 8.6 if t < s('O01') else 3.9                       # first: in the kitchen doorway. On "Sweetie": right behind you.
    hall_people(cv, t, cam, mom_z=mz)
    shade(cv, (540, 950), 1150, 0.45)
    grain(cv, t, 0.09)


def shot_HALL(cv, t):
    cam = hall(cv, t, door_light=1.0 if t >= s('P01') - 0.2 else 0.0)
    shade(cv, (540, 950), 1150, 0.5)
    grain(cv, t, 0.09)


def shot_KITCHEN(cv, t):
    kitchen(cv, t)
    grain(cv, t)


def shot_MONTAGE(cv, t):
    k = 0
    for i, m in enumerate(B['montage']):
        if t >= m:
            k = i
    kitchen(cv, t, mom_t=0.55 + (t - B['montage'][k]))       # every morning: the exact same flip at the exact same second
    grain(cv, t)


def make_cu(who, bgf, lightc):
    def shot(cv, t):
        bgf(cv, t)
        P = dict(CAST.get(who, {}))
        P['mouth_open'] = talk(t, who)
        if who == 'M':
            P.update(brow=0.8, mouth='o' if P['mouth_open'] == 0 else 'open', pupil=0.65, sweat=True, look=(0.2, 0.0))
        elif who == 'O':
            P.update(brow=0.0, mouth='smile' if P['mouth_open'] == 0 else 'open', lids=0.12, pupil=0.75, look=(0.0, 0.0))
        P['lids'] = max(P.get('lids', 0.0), blink(t, [k * 3.1 + len(who) for k in range(40)]) if who != 'O' else 0.0)   # she never blinks
        if who == 'O':
            P['arm_r'] = (35, 95)
        o = mascot(cv, 540, 2760, 2.0, light_side=1, rim=lightc, rim_a=0.5, **P)
        if who == 'O':                                                                   # spatula, and NO ring (hidden detail)
            hx, hy = o['hand_r']
            cv.drawLine(hx, hy, hx + 30, hy - 260, paint('#3A3A3A', style='stroke', width=22))
            cv.drawRoundRect(skia.Rect(hx - 10, hy - 380, hx + 90, hy - 250), 14, 14, paint('#4A4A4E'))
        shade(cv, (540, 950), 1100, 0.45)
        grain(cv, t)
    return shot


def bg_upstairs_light(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#3A2A1E'), C('#0A0806')])))
    with blurred(cv, 14):
        cv.drawRect(skia.Rect(200, 0, 880, 1300), paint(C(HALLWARM, 0.55)))                  # the doorway behind her
        cv.drawRect(skia.Rect(0, 1300, W, H), paint('#1A120C'))


def shot_CU_OS(cv, t):
    bg_upstairs_light(cv, t)
    P = dict(CAST['O'], mouth='smile', brow=0.0, lids=0.1, pupil=0.6, look=(0.0, 0.2), mouth_open=talk(t, 'O'), arm_r=(20, 30))
    if P['mouth_open'] > 0:
        P['mouth'] = 'open'
    mascot(cv, 540, 2760, 2.0, light_side=1, rim=HALLWARM, rim_a=0.8, **P)
    dim(cv, 0.35)
    glow(cv, (540, 1700), 900, TORCH, 0.15)                                               # your flashlight from below
    shade(cv, (540, 950), 1000, 0.5)
    grain(cv, t, 0.09)


def shot_CU_P(cv, t):
    with blurred(cv, 10):
        basement(cv, t, mom=False)
    with blurred(cv, 5):                                                                  # the long-fingered shadow behind her
        for f in range(4):
            cv.drawLine(860, 520 + f * 40, 1060, 380 + f * 70, paint(C('#000000', 0.7), style='stroke', width=26))
    P = dict(CAST['P'], brow=1.0, mouth='o', lids=0.35, pupil=0.5, sweat=True, mouth_open=talk(t, 'P'), look=(0.0, -0.2), arm_r=(40, 120))
    if P['mouth_open'] > 0:
        P['mouth'] = 'open'
    o = mascot(cv, 540, 2760, 2.0, light_side=1, rim=TORCH, rim_a=0.6, **P)
    hx, hy = o['head']
    cv.drawLine(hx - 120, hy - 240, hx + 20, hy - 180, paint('#8A2020', style='stroke', width=12))   # scar
    rx, ry = o['hand_r']
    ring(cv, rx, ry - 10, 2.2)                                                            # she still wears the ring
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=rad((540, 1000), 900, [C('#000000', 0.0), C('#000000', 0.75)])))
    grain(cv, t, 0.1)


def shot_CAR(cv, t):
    """The crash, 2 years ago, 11:47 PM: from the back seat. Blurry, rain, Mom turning around."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#04060A'))
    with blurred(cv, 6):
        cv.drawRect(skia.Rect(0, 350, W, 1150), paint('#000000', shader=lin((0, 350), (0, 1150), [C('#0A1020'), C('#1A1A24')])))   # windshield
        for k in range(40):                                                                # rain streaks
            x = (k * 97 + int(t * 900)) % W
            y = 380 + (k * 53 + int(t * 1400)) % 760
            cv.drawLine(x, y, x - 10, y + 50, paint(C('#9AB0D0', 0.5), style='stroke', width=3))
        glow(cv, (540, 900), 500, '#FFF0C8', 0.5)                                          # headlights on the road
        glow(cv, (300, 700), 260, '#E0342C', 0.4)
    wa = math.radians(-40 + 70 * abs(math.sin(t * 2.4)))                                  # wiper
    cv.drawLine(200, 1150, 200 + math.cos(wa) * 700, 1150 - math.sin(wa) * 700, paint('#0A0A0A', style='stroke', width=14))
    cv.drawRect(skia.Rect(0, 1150, W, 1360), paint('#141418'))                               # dashboard
    cv.drawRoundRect(skia.Rect(640, 1190, 860, 1270), 10, 10, paint('#0A0E0A'))
    text(cv, '11:47', 750, 1250, 66, '#7AF07A')
    P = dict(CAST['O'], head_turn=-0.6, look=(-0.6, 0.1), brow=0.9, mouth='open' if talk(t, 'Q') > 0 else 'o', mouth_open=talk(t, 'Q'),
             pupil=0.6, sweat=True)
    mascot(cv, 330, 2500, 1.5, legs=False, light_side=1, rim='#E0342C', rim_a=0.5, **P)
    cv.drawRoundRect(skia.Rect(-60, 1450, 420, H), 120, 120, paint('#1E1E24'))                # driver seat back
    cv.drawRoundRect(skia.Rect(660, 1450, 1140, H), 120, 120, paint('#1E1E24'))               # passenger seat back
    cv.drawCircle(560, 1370, 160, paint('#1A1A1E', style='stroke', width=26))                 # steering wheel + her hand with the ring
    cv.drawCircle(445, 1300, 30, paint(CAST['O']['skin']))
    ring(cv, 452, 1292, 1.4)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#2A0A10', 0.25)))
    grain(cv, t, 0.14)


def shot_FLOOR(cv, t):
    """Floorboards, close. Something knocks from underneath; dust jumps; light through the cracks."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A120C'))
    j = 0
    for k0 in B['knocks']:
        if k0 <= t < k0 + 0.12:
            j = 10
    for k in range(9):
        y = 200 + k * 200
        cv.drawRect(skia.Rect(-20, y + j * (k % 2), W + 20, y + 190 + j * (k % 2)), paint('#000000', shader=lin((0, y), (0, y + 190), [C('#4A3424'), C('#2E2016')])))
        for g in range(3):
            cv.drawLine(80 + g * 340 + k * 37, y + 40, 260 + g * 340 + k * 37, y + 60, paint(C('#1A120C', 0.6), style='stroke', width=3))
        cv.drawLine(0, y + 190, W, y + 190, paint(C('#FFE6B0', 0.35 if t >= s('P01') - 0.2 else 0.05), style='stroke', width=4))
    for k0 in B['knocks']:
        u = t - k0
        if 0 <= u < 0.8:
            for d in range(10):
                cv.drawCircle(300 + d * 60, 1000 - u * 400 + 30 * math.sin(d), 5, paint(C('#C8B898', 0.8 * (1 - u))))
    glow(cv, (540, 1000), 900, MOON, 0.08)
    shade(cv, (540, 1000), 1000, 0.6)
    grain(cv, t, 0.1)


def shot_CU_MN(cv, t):
    hall_blur(cv, t)
    P = dict(brow=1.0, mouth='o' if talk(t, 'M') == 0 else 'open', mouth_open=talk(t, 'M'), pupil=0.5, sweat=True, look=(0.0, 0.5))
    mascot(cv, 540, 2760, 2.0, light_side=-1, rim=MOON, rim_a=0.6, **P)
    shade(cv, (540, 950), 1050, 0.55)
    grain(cv, t, 0.09)


def shot_DOOR(cv, t):
    """The basement door, close. It opens; stairs + a faint light below."""
    cam = Cam(0.0, eye=1.2, vy=900, x=0.0, f=900)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#141A26'))
    wq = quad(cam, [(-1.6, 0, 1.6), (1.6, 0, 1.6), (1.6, 2.6, 1.6), (-1.6, 2.6, 1.6)])
    wallpaper(cv, wq, '#2A3448', '#1E2636')
    op = min(1.0, max(0.0, (t - B['door']) / 1.2))
    cv.drawPath(quad(cam, [(-0.55, 0, 1.59), (0.55, 0, 1.59), (0.55, 2.15, 1.59), (-0.55, 2.15, 1.59)]), paint('#D8D0C0'))
    cv.drawPath(quad(cam, [(-0.48, 0, 1.58), (0.48, 0, 1.58), (0.48, 2.08, 1.58), (-0.48, 2.08, 1.58)]), paint('#040404'))
    if op > 0:                                                                             # stairs going down + faint light
        for k in range(5):
            y0 = cam.p(0, 0, 1.6)[1] + k * 50
            cv.drawRect(skia.Rect(cam.p(-0.4, 0, 1.6)[0] + k * 6, y0, cam.p(0.4, 0, 1.6)[0] - k * 6, y0 + 20), paint(C('#5A4030', 0.7 - k * 0.12)))
        glow(cv, cam.p(0, 0.3, 1.6), 300, HALLWARM, 0.25 * op)
    dw = 0.96 * (1 - 0.85 * op)                                                            # the door swinging inward
    door = quad(cam, [(-0.48, 0, 1.58), (-0.48 + dw, 0, 1.58 + 0.6 * op), (-0.48 + dw, 2.08, 1.58 + 0.6 * op), (-0.48, 2.08, 1.58)])
    cv.drawPath(door, paint('#000000', shader=lin(cam.p(-0.48, 1, 1.58), cam.p(0.48, 1, 1.58), [C('#E8E2D6'), C('#A8A094')])))
    kx, ky = cam.p(-0.48 + dw * 0.88, 1.0, 1.58 + 0.6 * op * 0.88)
    cv.drawCircle(kx, ky, 20, paint('#C8A050'))
    for k in range(6):                                                                     # old scratches on the door
        sx = cam.p(-0.4 + dw * 0.1 * k, 0.3, 1.58)[0]
        cv.drawLine(sx, ky + 200, sx + 30, ky + 330, paint(C('#5A5048', 0.5), style='stroke', width=3))
    if t < B['door'] + 0.2:
        a0, a1 = cam.p(-0.48, 0.01, 1.58), cam.p(0.48, 0.01, 1.58)
        cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C('#FFE6B0', 0.8), style='stroke', width=6))
    glow(cv, (540, 300), 900, MOON, 0.12)
    shade(cv, (540, 950), 1100, 0.5)
    grain(cv, t, 0.09)


def stairs_down(cv, t, n_vis=13):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#030303'))
    for k in range(n_vis, -1, -1):                                                         # far (bottom) first
        f = k / n_vis
        w_ = 820 - 560 * f
        y = 1820 - 1250 * f ** 0.8
        hgt = 120 - 70 * f
        cv.drawRect(skia.Rect(540 - w_ / 2, y - hgt, 540 + w_ / 2, y), paint('#000000', shader=lin((0, y - hgt), (0, y), [C('#6A4A30'), C('#3A2818')])))
        cv.drawRect(skia.Rect(540 - w_ / 2, y, 540 + w_ / 2, y + hgt * 0.35), paint('#120C08'))
    for side in (-1, 1):                                                                    # brick side walls
        cv.drawPath(poly([(540 + side * 410, 1920), (540 + side * 560, 1920), (540 + side * 560, 0), (540 + side * 150, 300)]), paint('#2A1E18'))
        for r in range(26):
            y = 80 + r * 70
            cv.drawLine(540 + side * 300, y, 540 + side * 560, y - 20, paint(C('#000000', 0.35), style='stroke', width=4))


def shot_STAIRS(cv, t):
    stairs_down(cv, t)
    u = t - B['door']
    tx, ty = 540 + 60 * math.sin(t * 1.3), 1300 - 40 * math.sin(t * 0.9)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=rad((tx, ty), 650, [C('#000000', 0.0), C('#000000', 0.6), C('#000000', 0.95)], [0, 0.5, 1])))
    glow(cv, (tx, ty), 380, TORCH, 0.16)
    grain(cv, t, 0.1)


def shot_GRAB(cv, t):
    """On 'thirteen': a grey hand shoots out between the steps and grabs your ankle."""
    u = t - B['js2']
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#050404'))
    cv.drawRect(skia.Rect(0, 900, W, 1100), paint('#5A4030'))                                   # the step you're standing on
    cv.drawRect(skia.Rect(0, 1100, W, 1180), paint('#000000'))                                  # the gap under it
    cv.drawRoundRect(skia.Rect(380, 640, 640, 1000), 60, 60, paint('#2E4A7A'))                  # your jeans
    cv.drawRoundRect(skia.Rect(330, 940, 720, 1060), 50, 50, paint('#E8E8EC'))                  # sneaker
    rr = min(1.0, u / 0.08)
    for f in range(5):                                                                          # long grey fingers
        cv.drawLine(560, 1180, 420 + f * 50, 1180 - 260 * rr - (f % 2) * 30, paint('#B8B0A8', style='stroke', width=26))
    cv.drawRect(skia.Rect(470, 1140, 650, 1300), paint('#A8A098'))
    glow(cv, (540, 1000), 600, TORCH, 0.25)
    grain(cv, t, 0.15)


def shot_BASEMENT(cv, t):
    up = min(1.0, max(0.0, (t - s('P03')) / 0.6))
    tx = 300 + min(1.0, (t - B['basement']) / 0.8) * 260                                     # the beam finds her
    basement(cv, t, torch=(tx, 1250), mom=True, mom_up=up)
    grain(cv, t, 0.1)


def shot_UPSTAIRS(cv, t):
    """From the bottom of the stairs: the doorway at the top, Mom standing in the light."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#040303'))
    for k in range(13):
        f = k / 13
        y0 = 1900 - 1400 * f
        w_ = 900 - 500 * f
        cv.drawRect(skia.Rect(540 - w_ / 2, y0 - 70 + 40 * f, 540 + w_ / 2, y0), paint('#000000', shader=lin((0, y0 - 70), (0, y0), [C('#4A3424'), C('#24180F')])))
    cv.drawRect(skia.Rect(370, 160, 710, 560), paint(HALLWARM))                                 # the doorway, bright
    glow(cv, (540, 360), 700, HALLWARM, 0.45)
    P = dict(CAST['O'], mouth='smile' if talk(t, 'O') == 0 else 'open', mouth_open=talk(t, 'O'), look=(0.0, 0.4))
    mascot(cv, 540, 560, 0.33, light_side=1, rim=HALLWARM, rim_a=1.0, **P)
    cv.drawRect(skia.Rect(370, 160, 710, 560), paint(C('#000000', 0.0)))
    for side in (-1, 1):
        cv.drawPath(poly([(540 + side * 460, 1920), (540 + side * 560, 1920), (540 + side * 560, 0), (540 + side * 200, 140)]), paint('#1A120E'))
    shade(cv, (540, 700), 1100, 0.5)
    grain(cv, t, 0.1)


def true_face(cv, x, y, sc, who='O', t=0.0):
    P = dict(CAST[who], void_eyes=True, mouth='wide', mouth_open=0.0, stretch=0.3, brow=-0.6, head_tilt=8 * math.sin(t * 40),
             skin='#C8C0B8', skin_sh='#9A9088')
    mascot(cv, x, y, sc, light_side=1, rim='#E0342C', rim_a=0.9, **P)


def shot_TRUEFACE(cv, t):
    kitchen_blur(cv, t)
    true_face(cv, 540, 2900, 2.3, 'O', t)
    dim(cv, 0.25, '#3A0404')
    grain(cv, t, 0.18)


def shot_BOTH(cv, t):
    """From the basement: stairs + doorway (copy) at the top-left, real Mom chained on the floor right, you in between."""
    basement(cv, t, torch=(700, 1350), mom=True, mom_up=1.0)
    cv.drawPath(poly([(60, 0), (420, 0), (420, 780), (60, 980)]), paint('#0A0806'))            # stair well, top-left
    for k in range(8):
        y = 900 - k * 110
        cv.drawRect(skia.Rect(80 + k * 22, y - 40, 400, y), paint('#3A2A1C'))
    cv.drawRect(skia.Rect(200, 40, 400, 250), paint(HALLWARM))
    glow(cv, (300, 150), 400, HALLWARM, 0.4)
    lean = min(1.0, max(0.0, (t - B['pick'] + 0.3) / 0.4))
    P = dict(CAST['O'], mouth='smile' if talk(t, 'X') == 0 else 'open', mouth_open=talk(t, 'X'), look=(0.3, 0.4), head_tilt=12 * lean)
    mascot(cv, 300, 250, 0.2 + 0.04 * lean, light_side=1, rim=HALLWARM, rim_a=1.0, **P)
    mascot(cv, 520, 2300, 1.0, view='back', item='flashlight', arm_r=(40, 30), light_side=1, rim=TORCH, rim_a=0.4)
    grain(cv, t, 0.1)


def shot_LUNGE(cv, t):
    """Mid-card: the lights die, and both of them are in your face."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#080202'))
    u = t - B['js3']
    sc = 1.7 + u * 1.6
    true_face(cv, 300, 2500 + u * 400, sc, 'O', t)
    true_face(cv, 800, 2600 + u * 400, sc, 'P', t + 0.3)
    dim(cv, 0.2, '#3A0404')
    grain(cv, t, 0.2)


SHOTS = {k[5:]: v for k, v in dict(globals()).items() if k.startswith('shot_')}
SHOTS['CU_O'] = make_cu('O', kitchen_blur, DAY)
SHOTS['CU_M'] = make_cu('M', kitchen_blur, DAY)


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
    cv = surf.getCanvas()
    SHOTS[job](cv, f / FPS)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    surf.makeImageSnapshot().save(p, skia.kPNG)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', default='')
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--still', nargs='*', default=None)
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    OUT = a.out
    if a.still:
        todo = [(x.split(':')[0], int(x.split(':')[1])) for x in a.still]
    else:
        todo = needed()
        if a.jobs:
            js = set(a.jobs.split(','))
            todo = [x for x in todo if x[0] in js]
    with Pool(a.procs) as pool:
        for i, _ in enumerate(pool.imap_unordered(draw, todo, chunksize=4)):
            if i % 400 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
