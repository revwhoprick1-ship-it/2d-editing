#!/usr/bin/env python3
"""VIDEO_022 "Don't Touch The Vase" remake — 2.5D ink style (see VIDEOS/STYLE_REFS.md): ink outlines on sets + puppets,
indigo/lavender night with warm lamp pools, camera moves drawn IN the scene (parallax). ONE fixed bedroom layout:
back wall z=5 (shelf + vase on the left, window on the right), door on the left wall (z 1.0-2.0), bed along the right wall."""
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
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade, tenant  # noqa
from kit import Cam, blink, dim, flicker, keys, mouth_open, quad, text  # noqa
import edit_video022 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS, JS, s, e = E.B, E.LS, E.WORDS, E.JS, E.s, E.e
IND, IND2, LAV, WARM, INK = '#5A5AA0', '#40407A', '#A8A4E0', '#FFB870', '#0E0C1A'
BLUE, POR = '#2A4A9A', '#ECE8DE'


def talk(t, who):
    return mouth_open(t, WORDS, [l['id'] for l in E._T['lines'] if l['id'][0] == who])


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


# ===================================================================== the vase
def vase(cv, x, y, sc, rot=0.0, face_detail=True):
    """Grandma's vase: blue-and-white porcelain, painted with tiny rooms; a black wax seal on top."""
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(sc, sc)
    body = blob([(-60, -340), (60, -340), (70, -300), (150, -200), (170, -60), (120, 0), (-120, 0), (-170, -60), (-150, -200), (-70, -300)])
    with inked(cv, 5):
        cv.drawPath(body, paint(POR))
        cv.save(); cv.clipPath(body, skia.ClipOp.kIntersect, True)
        cv.drawRect(skia.Rect(40, -360, 200, 10), paint(C('#B8B2A6', 0.6)))
        for k in range(3):                                                                    # painted rooms band
            cv.drawLine(-170, -230 + k * 70, 170, -230 + k * 70, paint(BLUE, style='stroke', width=6))
            for j in range(4):
                wx = -110 + j * 60 + (k % 2) * 20
                cv.drawRect(skia.Rect(wx, -215 + k * 70, wx + 24, -180 + k * 70), paint(BLUE, style='stroke', width=4))
        if face_detail:                                                                       # a tiny painted face (Eli) - hidden detail
            cv.drawCircle(0, -105, 16, paint(BLUE, style='stroke', width=4))
            cv.drawCircle(-5, -108, 3, paint(BLUE)); cv.drawCircle(5, -108, 3, paint(BLUE))
        cv.restore()
        cv.drawRect(skia.Rect(-62, -370, 62, -335), paint('#141018'))                         # black wax seal
        cv.drawPath(blob([(-30, -340), (-18, -340), (-22, -300), (-26, -296)]), paint('#141018'))
    cv.restore()


# ===================================================================== bedroom (fixed layout)
Z1 = 5.0


def room(cv, cam, t, lamp=1.0, door_light=0.0, vase_on=True, under_bed_smoke=0.0):
    q = lambda p: quad(cam, p)  # noqa
    cv.drawRect(skia.Rect(0, 0, W, H), paint(INK))
    with inked(cv, 4):
        cv.drawPath(q([(-1.8, 2.6, 0.1), (1.8, 2.6, 0.1), (1.8, 2.6, Z1), (-1.8, 2.6, Z1)]), paint('#000000', shader=lin((0, 0), (0, 600), [C(IND2), C(IND)])))
        cv.drawPath(q([(-1.8, 0, 0.1), (-1.8, 2.6, 0.1), (-1.8, 2.6, Z1), (-1.8, 0, Z1)]), paint('#000000', shader=lin((0, 0), (540, 0), [C(IND2), C('#6A6AAE')])))
        cv.drawPath(q([(1.8, 0, 0.1), (1.8, 2.6, 0.1), (1.8, 2.6, Z1), (1.8, 0, Z1)]), paint('#000000', shader=lin((W, 0), (540, 0), [C(IND2), C('#62629E')])))
        cv.drawPath(q([(-1.8, 0, 0.1), (1.8, 0, 0.1), (1.8, 0, Z1), (-1.8, 0, Z1)]), paint('#000000', shader=lin((0, H), (0, 900), [C('#6A5A86'), C('#4A4070')])))
        cv.drawPath(q([(-1.8, 0, Z1), (1.8, 0, Z1), (1.8, 2.6, Z1), (-1.8, 2.6, Z1)]), paint('#55559A'))
        for z in range(1, 5):                                                                   # floorboard lines
            a0, a1 = cam.p(-1.8, 0, z), cam.p(1.8, 0, z)
            cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C(INK, 0.3), style='stroke', width=3))
        cv.drawPath(q([(-0.9, 0.005, 1.6), (0.5, 0.005, 1.6), (0.5, 0.005, 3.6), (-0.9, 0.005, 3.6)]), paint('#7A4A6A'))     # rug
        cv.drawPath(q([(-0.75, 0.006, 1.8), (0.35, 0.006, 1.8), (0.35, 0.006, 3.4), (-0.75, 0.006, 3.4)]), paint(C('#C8A0B0', 0.5), style='stroke', width=5))
        # back wall: posters, the shelf (left) with the vase, the window (right)
        cv.drawPath(q([(-0.2, 1.3, Z1 - 0.01), (0.35, 1.3, Z1 - 0.01), (0.35, 2.1, Z1 - 0.01), (-0.2, 2.1, Z1 - 0.01)]), paint('#8A3A4A'))
        cv.drawPath(q([(-1.6, 1.4, Z1 - 0.3), (-0.5, 1.4, Z1 - 0.3), (-0.5, 1.4, Z1), (-1.6, 1.4, Z1)]), paint('#8A6A4A'))         # shelf top
        cv.drawPath(q([(-1.6, 1.33, Z1 - 0.3), (-0.5, 1.33, Z1 - 0.3), (-0.5, 1.4, Z1 - 0.3), (-1.6, 1.4, Z1 - 0.3)]), paint('#5A4030'))
        wq = q([(0.6, 0.9, Z1 - 0.01), (1.5, 0.9, Z1 - 0.01), (1.5, 2.1, Z1 - 0.01), (0.6, 2.1, Z1 - 0.01)])
        cv.drawPath(wq, paint('#000000', shader=lin(cam.p(0, 2.1, Z1), cam.p(0, 0.9, Z1), [C('#1A2A5A'), C('#3A4A7A')])))
        c0, c1 = cam.p(1.05, 0.9, Z1), cam.p(1.05, 2.1, Z1)
        cv.drawLine(c0[0], c0[1], c1[0], c1[1], paint('#C8C0D8', style='stroke', width=6))
        # left wall: the door (near camera)
        cv.drawPath(q([(-1.79, 0, 1.0), (-1.79, 2.1, 1.0), (-1.79, 2.1, 2.0), (-1.79, 0, 2.0)]), paint('#000000', shader=lin(cam.p(-1.8, 1, 1.0), cam.p(-1.8, 1, 2.0), [C('#9A9AD0'), C('#7676B2')])))
        kx, ky = cam.p(-1.78, 1.0, 1.85)
        cv.drawCircle(kx, ky, max(6.0, cam.scale(1.85, 0.05) * 1150), paint('#E8C060'))
        # right wall: the bed (dark gap under it) + nightstand with a lamp
        cv.drawPath(q([(0.6, 0.0, 2.4), (1.8, 0.0, 2.4), (1.8, 0.15, 2.4), (0.6, 0.15, 2.4)]), paint('#05040A'))
        cv.drawPath(q([(0.6, 0.15, 2.4), (1.8, 0.15, 2.4), (1.8, 0.55, 2.4), (0.6, 0.55, 2.4)]), paint('#3A4A8A'))
        cv.drawPath(q([(0.6, 0.55, 2.4), (1.8, 0.55, 2.4), (1.8, 0.55, 4.8), (0.6, 0.55, 4.8)]), paint('#4A5AA0'))
        cv.drawPath(q([(0.7, 0.56, 4.1), (1.7, 0.56, 4.1), (1.7, 0.7, 4.7), (0.7, 0.7, 4.7)]), paint('#E8E4F0'))                    # pillow
        cv.drawPath(q([(0.6, 0.0, 2.4), (0.6, 0.55, 2.4), (0.6, 0.55, 4.8), (0.6, 0.0, 4.8)]), paint('#34408A'))                    # bed side
        cv.drawPath(q([(0.6, 0.0, 2.45), (0.6, 0.14, 2.45), (0.6, 0.14, 4.75), (0.6, 0.0, 4.75)]), paint('#05040A'))               # dark under the bed
        cv.drawPath(q([(1.3, 0, 1.6), (1.79, 0, 1.6), (1.79, 0.6, 1.6), (1.3, 0.6, 1.6)]), paint('#6A5A82'))                        # nightstand
        lx, ly = cam.p(1.55, 0.85, 1.9)
        sz = cam.scale(1.9, 0.25) * 1150
        cv.drawPath(poly([(lx - sz * 0.4, ly), (lx + sz * 0.4, ly), (lx + sz * 0.6, ly + sz * 0.6), (lx - sz * 0.6, ly + sz * 0.6)]), paint('#FFD8A0'))
    if vase_on:
        vx, vy = cam.p(-1.05, 1.4, Z1 - 0.15)
        vase(cv, vx, vy, cam.scale(Z1 - 0.15, 0.5) * 1150 / 370)
    wx, wy = cam.p(1.05, 1.5, Z1)                                                                # night outside the window
    glow(cv, (wx, wy), 300, LAV, 0.3)
    beam(cv, [cam.p(0.6, 2.1, Z1), cam.p(1.5, 2.1, Z1), cam.p(0.9, 0, 2.5), cam.p(-0.2, 0, 2.8)], LAV, 0.16)
    glow(cv, cam.p(1.55, 0.9, 1.9), 600, WARM, 0.45 * lamp)                                       # lamp pool
    if door_light > 0:
        a0, a1 = cam.p(-1.78, 0.01, 1.0), cam.p(-1.78, 0.01, 2.0)
        cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C(WARM, 0.9 * door_light), style='stroke', width=6))
    if under_bed_smoke > 0:
        for k in range(6):
            p0 = cam.p(0.6 - 0.3 * (1 - under_bed_smoke) - k * 0.08, 0.05, 3.0 + k * 0.25)
            cv.drawCircle(p0[0], p0[1], 50 + k * 10, paint(C('#05030A', 0.7), blur=20))


def you(cv, cam, z, x=0.0, **P):
    yx, yy = cam.p(x, 0, z)
    with inked(cv, 6):
        return mascot(cv, yx, yy, cam.scale(z, 1.4), light_side=-1, rim=LAV, rim_a=0.5, **P)


# ===================================================================== shots
def shot_HOOK(cv, t):
    """Low dolly toward the shelf; you knock the vase; it falls in slow motion (rotating), then CRASH (cut)."""
    u = min(1.0, t / max(0.5, B['crash']))
    cam = Cam(0.2 + 1.2 * u, eye=0.9, vy=1050, x=-0.5, f=880)
    room(cv, cam, t, vase_on=False)
    you(cv, cam, 3.8, x=-0.8, view='back', arm_r=(80, 10))
    fall = max(0.0, (t - 0.6) / max(0.4, B['crash'] - 0.6))                                    # the fall
    h = 1.4 - 1.4 * fall ** 2
    vx, vy = cam.p(-1.05 + 0.2 * fall, h, Z1 - 0.15 - 0.6 * fall)
    vase(cv, vx, vy, cam.scale(Z1 - 0.15 - 0.6 * fall, 0.5) * 1150 / 370, rot=-140 * fall)
    shade(cv, (540, 960), 1150, 0.5)
    grain(cv, t)


def shot_SHATTER(cv, t):
    u = t - B['crash']
    cam = Cam(1.4, eye=0.45, vy=1100, x=-0.5, f=880)
    room(cv, cam, t, vase_on=False)
    cx, cy = cam.p(-0.85, 0.0, 4.1)
    for k in range(24):                                                                          # pieces burst across the floor
        a = k * 0.27 + 0.3
        r = min(1.0, u * 3) * (180 + (k * 53) % 260)
        px, py = cx + math.cos(a) * r * 1.6, cy + abs(math.sin(a)) * r * 0.4
        sz = 18 + (k * 7) % 22
        with inked(cv, 3):
            cv.drawPath(poly([(px - sz, py), (px + sz * 0.6, py - sz * 0.7), (px + sz, py + sz * 0.4)]), paint(POR if k % 3 else '#C8C4BC'))
    for k in range(8):                                                                           # black smoke
        cv.drawCircle(cx + (k - 4) * 40, cy - min(1.0, u * 2) * (80 + k * 30), 90 + k * 12, paint(C('#05030A', 0.55), blur=30))
    shade(cv, (540, 1000), 1100, 0.5)
    grain(cv, t, 0.08)


def shot_SMOKE(cv, t):
    """Floor level: the black thing slides across the rug and under the bed."""
    u = min(1.0, (t - s('N03')) / max(1.0, e('N03') - s('N03')))
    cam = Cam(0.6, eye=0.35, vy=1150, x=0.3, f=880)
    room(cv, cam, t, vase_on=False, under_bed_smoke=u)
    for k in range(10):
        p0 = cam.p(-0.6 + 1.2 * u - k * 0.07, 0.03, 3.4 - 0.3 * u + k * 0.04)
        cv.drawCircle(p0[0], p0[1], 60 - k * 3, paint(C('#05030A', 0.75), blur=14))
    shade(cv, (540, 1100), 1100, 0.55)
    grain(cv, t)


def shot_NOTE(cv, t):
    """Grandma's note, rules appearing as she 'says' them (rule card from the flow ref); a 4th rule torn off."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2A4A'))
    cv.save(); cv.rotate(-3, 540, 960)
    with inked(cv, 5):
        cv.drawRect(skia.Rect(120, 420, 960, 1520), paint('#000000', shader=lin((0, 420), (0, 1520), [C('#F4ECD8'), C('#D8CCB0')])))
    text(cv, 'IF IT BREAKS:', 540, 560, 70, '#1A1A2A')
    rules = ["1. DON'T BLINK WHEN IT'S", "    IN THE ROOM", "2. DON'T ANSWER", "    WHEN I CALL YOU", "3. COUNT THE PIECES"]
    show = [0, 0, 1, 1, 2]
    for i, r in enumerate(rules):
        k = show[i]
        if k < len(B['rules']) and t >= B['rules'][k] - 0.1:
            text(cv, r, 180, 700 + i * 110, 54, '#2A2A3A', align='left')
    text(cv, '4. IF IT ASKS FOR ITS FA', 180, 1400, 40, C('#2A2A3A', 0.35), align='left')            # hidden: the torn 4th rule
    cv.drawPath(poly([(120, 1440), (300, 1470), (520, 1430), (760, 1480), (960, 1440), (960, 1530), (120, 1530)]), paint('#2A2A4A'))
    cv.restore()
    glow(cv, (540, 900), 900, WARM, 0.15)
    shade(cv, (540, 960), 1100, 0.45)
    grain(cv, t)


def shot_PIECES(cv, t):
    """Top-down: the pieces laid out on the rug in a grid, counted one by one; one slot is empty: FACE."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#5A3A5A'))
    for k in range(12):
        cv.drawLine(0, k * 170, W, k * 170 + 20, paint(C('#4A2A4A', 0.6), style='stroke', width=4))
    n = min(24, int((t - B['count']) / 0.06) + 1)
    for k in range(24):
        cx, cy = 200 + (k % 6) * 136, 520 + (k // 6) * 190
        if k == 14:                                                                              # the empty slot
            cv.drawCircle(cx, cy, 50, paint('#F4F0E6', style='stroke', width=5))
            if t > B['count'] + 1.4:
                text(cv, 'FACE?', cx, cy + 15, 40, '#E0342C')
            continue
        if k < n:
            with inked(cv, 3):
                cv.drawPath(poly([(cx - 46, cy + 20), (cx - 10, cy - 44), (cx + 44, cy - 10), (cx + 30, cy + 36)]), paint(POR))
            cv.drawLine(cx - 30, cy, cx + 30, cy - 6, paint(BLUE, style='stroke', width=5))
    with inked(cv, 6):                                                                           # your fist at the edge (hidden detail)
        cv.drawRoundRect(skia.Rect(860, 1440, 1100, 1700), 60, 60, paint('#E87A20'))
        cv.drawCircle(900, 1440, 80, paint('#F2C29B'))
    cv.drawPath(poly([(870, 1400), (900, 1385), (915, 1410)]), paint(POR))                         # a corner of porcelain between your fingers
    text(cv, f'{min(23, max(0, n - (1 if n > 14 else 0)))} / 24', 540, 380, 110, '#FFFFFF')
    glow(cv, (540, 900), 900, WARM, 0.15)
    shade(cv, (540, 960), 1100, 0.45)
    grain(cv, t)


def shot_DOOR(cv, t):
    """The bedroom door from inside. First: Mom calls from downstairs. Later: feet shadows right outside, handle turning."""
    cam = Cam(0.0, eye=1.2, vy=930, x=-1.0, f=880)
    room(cv, cam, t, door_light=1.0)
    if t >= B['feet']:
        a0 = cam.p(-1.78, 0.01, 1.3)
        a1 = cam.p(-1.78, 0.01, 1.7)
        cv.drawLine(a0[0], a0[1], a0[0] + (a1[0] - a0[0]) * 0.3, a0[1] + (a1[1] - a0[1]) * 0.3, paint('#05040A', style='stroke', width=8))
        cv.drawLine(a0[0] + (a1[0] - a0[0]) * 0.6, a0[1] + (a1[1] - a0[1]) * 0.6, a1[0], a1[1], paint('#05040A', style='stroke', width=8))
    shade(cv, (500, 960), 1100, 0.5)
    grain(cv, t)


def shot_WINDOW(cv, t):
    """Out the window: the driveway, the streetlight... and no car."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#55559A'))
    with inked(cv, 5):
        cv.drawRect(skia.Rect(120, 300, 960, 1550), paint('#8A86C0'))
        cv.drawRect(skia.Rect(150, 330, 930, 1520), paint('#000000', shader=lin((0, 330), (0, 1520), [C('#141C40'), C('#2A345A')])))
        cv.drawRect(skia.Rect(150, 1150, 930, 1520), paint('#3A3A4A'))                          # driveway
        cv.drawLine(500, 1150, 420, 1520, paint(C('#F4F0E6', 0.5), style='stroke', width=8))
        cv.drawRect(skia.Rect(760, 600, 780, 1150), paint('#2A2A34'))                            # streetlight
        cv.drawPath(poly([(740, 600), (820, 600), (800, 640), (760, 640)]), paint('#4A4A54'))
    cv.drawPath(poly([(760, 640), (800, 640), (900, 1150), (640, 1150)]), paint(C(WARM, 0.25), blur=14))
    cv.drawRect(skia.Rect(150, 330, 930, 1520), paint(C('#FFFFFF', 0.05)))
    s_ = min(1.0, (t - s('N08')) * 4)
    cv.save(); cv.translate(540, 1300); cv.scale(s_, s_); cv.rotate(-3)
    cv.drawRoundRect(skia.Rect(-230, -50, 230, 50), 10, 10, paint('#F4F0E6'))
    text(cv, "MOM'S CAR: GONE", 0, 18, 52, '#C8302A')
    cv.restore()
    shade(cv, (540, 960), 1100, 0.45)
    grain(cv, t)


def cu(cv, t, P, bgcam_x=0.0):
    cam = Cam(0.5, eye=1.2, vy=900, x=bgcam_x, f=880)
    room(cv, cam, t, vase_on=False)
    dim(cv, 0.25)
    with inked(cv, 8):
        o = mascot(cv, 540, 2760, 2.0, light_side=-1, rim=LAV, rim_a=0.7, **P)
    return o


def shot_PHONE(cv, t):
    P = dict(brow=1.0, mouth='o', pupil=0.6, sweat=True, look=(0.4, 0.0), mouth_open=talk(t, 'M'), arm_r=(150, 150))
    cu(cv, t, P)
    with inked(cv, 6):
        cv.drawRoundRect(skia.Rect(760, 620, 900, 960), 20, 20, paint('#1A1A24'))
    cv.drawRoundRect(skia.Rect(772, 635, 888, 945), 14, 14, paint(C('#9FC8FF', 0.8)))
    if t < s('G01'):
        text(cv, 'GRANDMA', 830, 800, 26, '#1A1A24')
    glow(cv, (830, 790), 300, '#9FC8FF', 0.3)
    shade(cv, (540, 950), 1100, 0.45)
    grain(cv, t)


def shot_EYES(cv, t):
    """Extreme close-up of your eyes: red, watering, refusing to blink."""
    u = min(1.0, (t - B['eyes']) / 3.5)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2A4A'))
    with inked(cv, 10):
        mascot(cv, 540, 4300, 4.2, brow=1.0, mouth='o', pupil=0.35 - 0.1 * u, sweat=True, look=(0.0, 0.0), mouth_open=talk(t, 'M'),
               light_side=-1, rim=LAV, rim_a=0.7, skin='#E8C0B0', skin_sh='#C09A90')
    for side in (-1, 1):                                                                        # red veins + tears
        cx = 540 + side * 190
        for k in range(6):
            a = k * 1.05
            cv.drawLine(cx + math.cos(a) * 60, 760 + math.sin(a) * 60, cx + math.cos(a) * (110 + 20 * u), 760 + math.sin(a) * (110 + 20 * u),
                        paint(C('#C82020', 0.3 + 0.5 * u), style='stroke', width=4))
        ty = 860 + (t * 300) % 400
        cv.drawPath(blob([(cx + 70, ty), (cx + 85, ty + 40), (cx + 70, ty + 60), (cx + 55, ty + 40)]), paint(C('#BFE3FF', 0.8)))
    shade(cv, (540, 800), 900, 0.45)
    grain(cv, t)


def shot_FACE(cv, t):
    """It is RIGHT THERE (on the blink / at the end)."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A1430'))
    tenant(cv, 540, 4900, 2.6, t=t, mouth=1.0, eyes_open=1.0, look=(0.0, 0.1), tilt=-8, rim='#E0342C', rim_a=0.8)
    shade(cv, (540, 960), 900, 0.45)
    grain(cv, t, 0.12)


def shot_REVEAL(cv, t):
    """Wide: the room, the lamp flickering, IT standing by the bed. Pieces of it still clicking into place."""
    cam = Cam(0.3 + 0.2 * math.sin(t * 0.3), eye=1.25, vy=900, x=-0.3, f=880)
    room(cv, cam, t, vase_on=False, lamp=flicker(t, 4, 7.0, 0.3))
    tx, ty = cam.p(0.35, 0, 3.4)
    a = min(1.0, 0.85 + (t - B['js1'] - JS) * 0.3)
    with inked(cv, 6):
        tenant(cv, tx, ty, cam.scale(3.4, 2.3) * 1150 / 2400, t=t, assemble=a, mouth=talk(t, 'X') * 0.8, reach=0.3, eyes_open=0.6,
               look=(-0.4, 0.2), tilt=-12, rim=LAV, rim_a=0.6, ink=False)
    you(cv, cam, 1.6, x=-0.9, view='back')
    shade(cv, (540, 960), 1150, 0.5)
    grain(cv, t)


def shot_HAND(cv, t):
    """Your fist opens: the face piece. A child's face is painted on it."""
    u = min(1.0, (t - s('N10')) / 1.0)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2A4A'))
    glow(cv, (540, 900), 700, WARM, 0.25)
    with inked(cv, 8):
        cv.drawRoundRect(skia.Rect(380, 1150, 700, 1920), 120, 120, paint('#E87A20'))
        cv.drawCircle(540, 1000, 260, paint('#F2C29B'))
        cv.drawPath(blob([(400, 900), (540, 820), (690, 900), (680, 1080), (540, 1140), (400, 1080)]), paint(POR))
        for k in range(4):                                                                     # fingers opening
            fx = 360 + k * 110
            cv.drawRoundRect(skia.Rect(fx, 760 - 200 * u, fx + 90, 960 - 120 * u), 45, 45, paint('#F2C29B'))
    cv.drawCircle(500, 960, 16, paint(BLUE)); cv.drawCircle(580, 960, 16, paint(BLUE))          # the painted child's face
    q = skia.Path(); q.moveTo(490, 1040); q.quadTo(540, 1070, 590, 1040)
    cv.drawPath(q, paint(BLUE, style='stroke', width=7))
    cv.drawLine(450, 880, 520, 1100, paint('#141018', style='stroke', width=6))
    shade(cv, (540, 950), 1000, 0.45)
    grain(cv, t)


def shot_CHOICE(cv, t):
    """Wide again: with every line it is closer; mouth slowly opening."""
    u = min(1.0, max(0.0, (t - B['choice']) / max(1.0, B['js2'] - B['choice'])))
    cam = Cam(0.3, eye=1.25, vy=900, x=-0.3, f=880)
    room(cv, cam, t, vase_on=False, lamp=flicker(t, 6, 9.0, 0.2))
    z = 3.4 - 1.6 * u
    tx, ty = cam.p(0.2 - 0.3 * u, 0, z)
    with inked(cv, 6):
        tenant(cv, tx, ty, cam.scale(z, 2.3) * 1150 / 2400, t=t, mouth=0.3 + 0.6 * u, reach=0.3 + 0.6 * u, eyes_open=1.0, look=(-0.3, 0.3),
               tilt=-10 - 10 * u, rim='#E0342C', rim_a=0.5 + 0.3 * u)
    shade(cv, (540, 960), 1100, 0.55)
    grain(cv, t, 0.08)


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
