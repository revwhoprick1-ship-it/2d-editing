#!/usr/bin/env python3
"""STYLE TEST (10 s): "2.5D ink" look = toon 3D-ish sets with black ink outlines + our flat 2D puppet (also inked),
indigo/purple moonlight with warm lamp/flashlight pools, slow camera dolly + pan with real parallax (drawn per frame),
extreme close-up, pop-up object label. 3 shots: HALL dolly -> FACE close-up -> DOOR push-in."""
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'twod'))
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
from kit import Cam, quad, text  # noqa

FPS, OUT = 30, os.path.join(HERE, 'frames2d')
T1, T2, END = 4.2, 7.2, 10.0
# palette: indigo shadows, lavender lights, warm lamp/flashlight, ink
IND, IND2, LAV, WARM, INK = '#5A5AA0', '#40407A', '#A8A4E0', '#FFB870', '#0E0C1A'

_g = (np.random.default_rng(7).normal(128, 40, (512, 512))).clip(0, 255).astype(np.uint8)
GRAIN = skia.Image.fromarray(np.dstack([_g, _g, _g, np.full_like(_g, 255)]))


def grain(cv, t, a=0.06):
    p = skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kOverlay)
    for x in range(-(int(t * 997) % 512), W, 512):
        for y in range(-(int(t * 613) % 512), H, 512):
            cv.drawImage(GRAIN, x, y, skia.SamplingOptions(), p)


class inked:
    """with inked(cv, w): ... -> everything drawn inside gets a black ink outline (the 3D-toon look)."""
    def __init__(self, cv, w=5):
        self.cv, self.w = cv, w

    def __enter__(self):
        f = skia.ImageFilters.Merge([skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(14, 12, 26), skia.BlendMode.kSrcIn),
                                                                   skia.ImageFilters.Dilate(self.w, self.w)), None])
        self.cv.saveLayer(None, skia.Paint(ImageFilter=f))

    def __exit__(self, *a):
        self.cv.restore()


def beam(cv, pts, col, a):
    cv.drawPath(poly(pts), paint(C(col, a), blur=18))


def hall(cv, cam, t, door_label=0.0):
    q = lambda p: quad(cam, p)  # noqa
    Z1 = 10.0
    cv.drawRect(skia.Rect(0, 0, W, H), paint(INK))
    with inked(cv, 4):
        cv.drawPath(q([(-1.3, 2.7, 0.2), (1.3, 2.7, 0.2), (1.3, 2.7, Z1), (-1.3, 2.7, Z1)]), paint('#000000', shader=lin((0, 0), (0, 700), [C(IND2), C(IND)])))
        cv.drawPath(q([(-1.3, 0, 0.2), (-1.3, 2.7, 0.2), (-1.3, 2.7, Z1), (-1.3, 0, Z1)]), paint('#000000', shader=lin((0, 0), (540, 0), [C(IND2), C('#6A6AAE')])))
        cv.drawPath(q([(1.3, 0, 0.2), (1.3, 2.7, 0.2), (1.3, 2.7, Z1), (1.3, 0, Z1)]), paint('#000000', shader=lin((W, 0), (540, 0), [C(IND2), C('#62629E')])))
        cv.drawPath(q([(-1.3, 0, 0.2), (1.3, 0, 0.2), (1.3, 0, Z1), (-1.3, 0, Z1)]), paint('#000000', shader=lin((0, H), (0, 900), [C('#6A5A86'), C('#4A4070')])))
        for z in range(1, int(Z1)):                                                         # floorboards + wall panel seams
            for x in (-1.3, 1.3):
                a0, a1 = cam.p(x, 0, z), cam.p(x, 2.7, z)
                cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C(INK, 0.5), style='stroke', width=3))
            a0, a1 = cam.p(-1.3, 0, z), cam.p(1.3, 0, z)
            cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C(INK, 0.35), style='stroke', width=3))
        cv.drawPath(q([(-1.3, 0, Z1), (1.3, 0, Z1), (1.3, 2.7, Z1), (-1.3, 2.7, Z1)]), paint('#55559A'))
        cv.drawPath(q([(-1.29, 1.0, 6.0), (-1.29, 2.1, 6.0), (-1.29, 2.1, 7.2), (-1.29, 1.0, 7.2)]), paint('#4A5AA8'))   # window
        cv.drawPath(q([(-1.29, 1.3, 2.0), (-1.29, 1.9, 2.0), (-1.29, 1.9, 2.8), (-1.29, 1.3, 2.8)]), paint('#C8A060'))   # framed photo
        cv.drawPath(q([(-1.28, 1.36, 2.07), (-1.28, 1.84, 2.07), (-1.28, 1.84, 2.73), (-1.28, 1.36, 2.73)]), paint('#7A88B8'))
        cv.drawPath(q([(-1.3, 0, 4.0), (-0.9, 0, 4.0), (-0.9, 0.8, 4.0), (-1.3, 0.8, 4.0)]), paint('#6A5A82'))          # side table
        cv.drawPath(q([(-1.3, 0.8, 4.0), (-0.9, 0.8, 4.0), (-0.9, 0.8, 4.6), (-1.3, 0.8, 4.6)]), paint('#6A5A7A'))
        lx, ly = cam.p(-1.1, 1.15, 4.3)
        cv.drawPath(poly([(lx - 30, ly), (lx + 30, ly), (lx + 44, ly + 50), (lx - 44, ly + 50)]), paint('#FFD8A0'))     # lamp shade
        d0, d1 = 3.0, 4.0                                                                     # the basement door (right wall)
        cv.drawPath(q([(1.29, 0, d0 - 0.1), (1.29, 2.2, d0 - 0.1), (1.29, 2.2, d1 + 0.1), (1.29, 0, d1 + 0.1)]), paint('#5A4A6A'))
        cv.drawPath(q([(1.285, 0, d0), (1.285, 2.1, d0), (1.285, 2.1, d1), (1.285, 0, d1)]), paint('#000000', shader=lin(cam.p(1.3, 1, d0), cam.p(1.3, 1, d1), [C('#9A9AD0'), C('#7676B2')])))
        kx, ky = cam.p(1.28, 1.0, d1 - 0.12)
        cv.drawCircle(kx, ky, max(6.0, cam.scale(d1, 0.05) * 1150), paint('#E8C060'))
    # light: lamp pool (warm), moon beam from the window (lavender), light under the door
    glow(cv, cam.p(-1.1, 1.2, 4.3), 520, WARM, 0.45)
    beam(cv, [cam.p(-1.3, 2.1, 6.0), cam.p(-1.3, 1.0, 7.2), cam.p(0.6, 0, 8.2), cam.p(0.9, 0, 6.6)], LAV, 0.22)
    a0, a1 = cam.p(1.28, 0.01, 3.0), cam.p(1.28, 0.01, 4.0)
    cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C(WARM, 0.9), style='stroke', width=6))
    glow(cv, ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2), 200, WARM, 0.4)
    if door_label > 0:                                                                        # pop-up label (flow ref style)
        lx, ly = cam.p(1.25, 2.35, 3.5)
        s_ = min(1.0, door_label * 4)
        cv.save(); cv.translate(lx - 150, ly); cv.scale(s_, s_); cv.rotate(-3)
        cv.drawRoundRect(skia.Rect(-170, -48, 170, 48), 10, 10, paint('#F4F0E6'))
        cv.drawRoundRect(skia.Rect(-170, -48, 170, 48), 10, 10, paint(INK, style='stroke', width=5))
        text(cv, 'DO NOT OPEN', 0, 18, 50, '#C8302A')
        cv.restore()


def shot_HALL(cv, t):
    """Slow dolly in + slight pan + dutch tilt: real parallax because the camera moves in the scene."""
    u = t / T1
    e = u * u * (3 - 2 * u)
    cam = Cam(-0.6 + 1.6 * e, eye=1.35 - 0.15 * e, vy=900, x=-0.2 + 0.35 * e, f=860)
    cv.save(); cv.rotate(-3 + 2 * e, 540, 960)
    cv.scale(1.06, 1.06)
    hall(cv, cam, t, door_label=max(0.0, t - 2.4))
    yx, yy = cam.p(0.55, 0, 2.6)                                                              # you, in front of the door
    with inked(cv, 6):
        mascot(cv, yx, yy, cam.scale(2.6, 1.4), view='back', arm_r=(55, 15), light_side=-1, rim=LAV, rim_a=0.6)
    cv.restore()
    shade(cv, (540, 960), 1150, 0.55)
    grain(cv, t)


def shot_FACE(cv, t):
    """Extreme close-up, low angle; a warm flashlight sweep crosses the indigo face."""
    u = (t - T1) / (T2 - T1)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#6A6AAE'), C(IND2)])))
    with inked(cv, 9):
        cv.save(); cv.rotate(4, 540, 960)
        mascot(cv, 520 + 30 * u, 2900 - 60 * u, 2.6, brow=1.0, mouth='o', mouth_open=0.15, pupil=0.45, sweat=True, look=(0.7, 0.1),
               light_side=-1, rim=LAV, rim_a=0.8, skin='#C8A8C8', skin_sh='#8A7AA8', shirt='#3A3A78', shirt_sh='#24244E')
        cv.restore()
    fx = -300 + 1700 * u                                                                      # flashlight sweeping left -> right
    cv.drawCircle(fx, 900, 380, paint(C(WARM, 0.35), blur=60, blend=skia.BlendMode.kScreen))
    shade(cv, (540, 900), 1000, 0.5)
    grain(cv, t, 0.08)


def shot_DOOR(cv, t):
    """Push-in on the door + key in your hand, light leaking under it."""
    u = (t - T2) / (END - T2)
    cam = Cam(0.6 + 0.9 * u, eye=1.1, vy=980, x=0.55, f=900)
    hall(cv, cam, t, door_label=1.0)
    with inked(cv, 6):                                                                         # the key, held up
        cv.save(); cv.translate(380, 1450 - 40 * u); cv.rotate(-25)
        cv.drawCircle(0, 0, 70, paint('#E8C060')); cv.drawCircle(0, 0, 32, paint('#6A5A3A'))
        cv.drawRect(skia.Rect(60, -14, 300, 14), paint('#E8C060'))
        cv.drawRect(skia.Rect(240, 14, 262, 56), paint('#E8C060')); cv.drawRect(skia.Rect(280, 14, 300, 46), paint('#E8C060'))
        cv.restore()
        cv.drawRoundRect(skia.Rect(170, 1560, 330, 1920), 40, 40, paint('#E87A20'))                # sleeve
        cv.drawCircle(300, 1470, 95, paint('#F2C29B'))                                          # fist holding the key
    glow(cv, (380, 1450), 300, WARM, 0.3)
    shade(cv, (600, 900), 1050, 0.55)
    grain(cv, t)


SHOTS = {'HALL': shot_HALL, 'FACE': shot_FACE, 'DOOR': shot_DOOR}


def job(t):
    return 'HALL' if t < T1 else ('FACE' if t < T2 else 'DOOR')


def draw(f):
    t = f / FPS
    p = os.path.join(OUT, job(t), f'{f:04d}.png')
    if os.path.exists(p):
        return
    s = skia.Surface(W, H)
    SHOTS[job(t)](s.getCanvas(), t)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    s.makeImageSnapshot().save(p, skia.kPNG)


if __name__ == '__main__':
    fr = [int(a) for a in sys.argv[1:]] or list(range(int(END * FPS) + 1))
    with Pool(4) as pool:
        list(pool.imap_unordered(draw, fr, chunksize=4))
    print('DRAW_OK', len(fr))
