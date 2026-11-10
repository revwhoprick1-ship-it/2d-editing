#!/usr/bin/env python3
"""VIDEO_018 "The Extra Passenger" — real 2D horror (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_016/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]

Cabin light: night blue + warm reading lights; after Lawrence: red emergency light; landing: warm full light.
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
import edit_video018 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS, JS, s = E.B, E.LS, E.WORDS, E.JS, E.s
MOON = '#9FD0C8'          # blue-green moonlight
TUNG = '#FFC27A'          # weak tungsten

CAST = {
    'M': dict(),
    'B': dict(glasses='#22262C', hair='#3A2A1A', hair_sh='#24180E', shirt='#2A7A7A', shirt_sh='#1E5C5C'),
    'L': dict(hair='#1A1A1A', hair_sh='#0A0A0A', shirt='#6A4A8A', shirt_sh='#50366A', skin='#8E5A3C', skin_sh='#6E432C'),
    'G': dict(long_hair=True, hair='#2A1A10', hair_sh='#1A0E08', shirt='#C8C8D8', shirt_sh='#A0A0B4', blush=0.2),
    'Q': dict(skin='#B8B0A8', skin_sh='#948C84', hair='#5A5A5A', hair_sh='#3A3A3A', shirt='#4A4A52', shirt_sh='#34343A'),
    'X': dict(hair='#E8C060', hair_sh='#C09A40', shirt='#D8B020', shirt_sh='#A88618', skin='#F5D0B0', skin_sh='#D9AE8C', blush=0.3),
    'J': dict(belly=1.35, hair='#1A1A1A', hair_sh='#0A0A0A', shirt='#3E5A3E', shirt_sh='#2C422C', skin='#6E4A30', skin_sh='#543622'),
}
SPEAK = {'M': ('M',), 'B': ('B',), 'L': ('L',), 'K': ('K',), 'J': ('J',)}


def talk(t, who):
    return mouth_open(t, WORDS, [l['id'] for l in E._T['lines'] if l['id'][0] == who])


def mood(t):
    if t < B['a02']:
        return 'calm'
    if t < B['dark']:
        return 'scared'
    return 'terror'


def face_pose(who, t):
    m = mood(t)
    P = dict(CAST[who])
    o = talk(t, who)
    P['mouth_open'] = o
    if m == 'calm':
        P.update(brow={'L': 0.3, 'B': 0.2, 'M': 0.1, 'G': 0.0}.get(who, 0.0), mouth='smile' if who == 'L' else 'flat')
    elif m == 'scared':
        P.update(brow=1.0, mouth='o', pupil=0.75, sweat=True)
    elif m == 'terror':
        P.update(brow=1.0, mouth='open', pupil=0.5, sweat=True)
    else:
        P.update(brow=0.6, mouth='o', lids=0.25, sweat=True)
    if o > 0 and P.get('mouth') in ('flat', 'smile', 'o'):
        P['mouth'] = 'open'
    P['lids'] = max(P.get('lids', 0.0), blink(t, [k * 3.7 + hash(who) % 3 for k in range(60)]))
    return P


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


def state(t):
    if B['dark'] <= t < s('A03') - 0.1:
        return 'dark'
    if t >= B['choice']:
        return 'red'
    return 'night'


def lamp(t):
    """Cabin light level: steady, then nervous flicker after the blackout."""
    st = state(t)
    if st == 'dark':
        return 0.0
    if t >= s('A03') - 0.1:
        return flicker(t, 7, 6.0, 0.55)
    return 1.0


def cone(cv, x, y, w0, w1, h, col, a):
    """Volumetric reading-light cone: soft gradient wedge."""
    pth = poly([(x - w0, y), (x + w0, y), (x + w1, y + h), (x - w1, y + h)])
    cv.drawPath(pth, paint('#000', shader=lin((x, y), (x, y + h), [C(col, a), C(col, 0.0)]), blur=10))
    cv.drawCircle(x, y, w0 * 1.3, paint(C(col, min(1.0, a * 3))))
    glow(cv, (x, y), w0 * 6, col, a * 0.8)


def fabric(cv, rect, base, t=0.0):
    """Seat fabric: vertical gradient + small woven dots + soft inner shadow (not a flat fill)."""
    x0, y0, x1, y1 = rect
    rr = skia.Rect(x0, y0, x1, y1)
    cv.drawRoundRect(rr, (x1 - x0) * 0.2, (x1 - x0) * 0.2, paint(base, shader=lin((0, y0), (0, y1), [C('#2E4470'), C('#16223C')])))
    cv.save(); pth = skia.Path(); pth.addRoundRect(rr, (x1 - x0) * 0.2, (x1 - x0) * 0.2); cv.clipPath(pth, skia.ClipOp.kIntersect, True)
    step = max(10, int((x1 - x0) / 16))
    dot = paint(C('#5A78B0', 0.18))
    for yy in range(int(y0), int(y1), step):
        for xx in range(int(x0) + (yy // step % 2) * step // 2, int(x1), step):
            cv.drawCircle(xx, yy, step * 0.12, dot)
    cv.drawRect(skia.Rect(x0, y0, x1, y1), paint('#000', shader=lin((x0, 0), (x1, 0), [C('#000000', 0.35), C('#000000', 0.0), C('#000000', 0.0), C('#000000', 0.4)], [0, 0.25, 0.75, 1])))
    cv.restore()


def cabin(cv, cam, t, near_sharp=3.0, blur_far=5.0, heads=True, staring=0.0, extra_heads=0, z_max=24):
    """Down-the-aisle perspective with depth: far rows blurred + hazed, light strips, window glow, seat-back screens."""
    st, lp = state(t), lamp(t)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#05070C'))
    vx, vy = cam.p(0, 1.2, 60)
    # ceiling + walls + floor as gradients toward the vanishing point
    cv.drawPath(quad(cam, [(-2.0, 2.4, 0.3), (2.0, 2.4, 0.3), (2.0, 2.4, 60), (-2.0, 2.4, 60)]),
                paint('#000', shader=lin((0, 0), (vx, vy), [C('#0C1220'), C('#1E2A44' if st != 'red' else '#3A1414')])))
    for side in (-1, 1):
        cv.drawPath(quad(cam, [(side * 2.0, 0, 0.3), (side * 2.0, 2.4, 0.3), (side * 2.0, 2.4, 60), (side * 2.0, 0, 60)]),
                    paint('#000', shader=lin(cam.p(side * 2.0, 1.2, 0.5), (vx, vy), [C('#0A0E18'), C('#1A2438' if st != 'red' else '#2E1010')])))
    cv.drawPath(quad(cam, [(-2.0, 0, 0.3), (2.0, 0, 0.3), (2.0, 0, 60), (-2.0, 0, 60)]),
                paint('#000', shader=lin((0, H), (vx, vy), [C('#141824'), C('#262E44')])))
    cv.drawPath(quad(cam, [(-0.38, 0.002, 0.3), (0.38, 0.002, 0.3), (0.38, 0.002, 60), (-0.38, 0.002, 60)]),
                paint('#000', shader=lin((0, H), (vx, vy), [C('#3A2030'), C('#24182A')])))
    for k in range(0, 60, 2):                                                                 # carpet pattern stripes
        cv.drawPath(quad(cam, [(-0.38, 0.003, k), (0.38, 0.003, k), (0.38, 0.003, k + 0.25), (-0.38, 0.003, k + 0.25)]), paint(C('#000000', 0.18)))
    if st == 'dark':                                                                          # emergency floor path lights
        for k in range(1, 40):
            for side in (-1, 1):
                p = cam.p(side * 0.36, 0.0, k * 0.8)
                cv.drawCircle(p[0], p[1], max(1.5, cam.scale(k * 0.8, 0.03) * 575), paint('#FF5A40'))
    else:
        for side in (-1, 1):                                                                  # ceiling light strips
            a0, a1 = cam.p(side * 0.7, 2.38, 0.5), cam.p(side * 0.7, 2.38, 60)
            col = WARM if st != 'red' else RED
            cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C(col, 0.5 * lp), style='stroke', width=14, blur=14))
            cv.drawLine(a0[0], a0[1], a1[0], a1[1], paint(C('#FFF4E0', 0.7 * lp), style='stroke', width=3))

    def row(k, side):
        z = k * 0.95
        bump = 0
        cv.drawPath(quad(cam, [(side * 0.42, 1.78, z), (side * 2.0, 1.78, z), (side * 2.0, 2.32, z), (side * 0.42, 2.32, z)]), paint('#2A3550'))
        cv.drawPath(quad(cam, [(side * 0.42, 1.78, z), (side * 2.0, 1.78, z), (side * 2.0, 1.78, z + 0.93), (side * 0.42, 1.78, z + 0.93)]),
                    paint(C('#000000', 0.35)))
        wx, wy = cam.p(side * 1.99, 1.35, z + 0.45)
        rr = cam.scale(z + 0.45, 0.24) * 575
        cv.drawOval(skia.Rect(wx - rr * 0.55, wy - rr, wx + rr * 0.55, wy + rr), paint('#0E1830'))
        if st != 'dark':
            glow(cv, (wx, wy), rr * 2.2, NIGHT, 0.12)
        for s_ in range(3):
            x = side * (0.62 + s_ * 0.46)
            q = quad(cam, [(x - 0.21, 0.45, z), (x + 0.21, 0.45, z), (x + 0.19, 1.22, z), (x - 0.19, 1.22, z)])
            cv.drawPath(q, paint('#22314E'))
            hx, hy = cam.p(x, 1.06, z - 0.01)
            sr = cam.scale(z, 0.11) * 575
            if st != 'dark':                                                                   # seat-back screen glow
                cv.drawRect(skia.Rect(hx - sr, hy - sr * 0.7, hx + sr, hy + sr * 0.7), paint(C(SCREEN, 0.6 * lp)))
                glow(cv, (hx, hy), sr * 3, SCREEN, 0.08 * lp)
            if heads:
                hx, hy = cam.p(x, 1.36, z + 0.25)
                hr = cam.scale(z + 0.25, 0.26) * 575
                seed = (k * 7 + s_ * 3 + side) % 5
                cv.drawCircle(hx, hy, hr, paint(['#2A1A12', '#1A1A1A', '#6A4A2A', '#C8A050', '#3A2A1A'][seed]))
                if staring > 0:
                    cv.drawCircle(hx, hy + hr * 0.12, hr * 0.84, paint(C(['#F2C29B', '#8E5A3C', '#D99B76', '#F5D0B0', '#6E4A30'][seed], staring)))
                    for e_ in (-1, 1):
                        cv.drawCircle(hx + e_ * hr * 0.33, hy + hr * 0.08, hr * 0.18, paint(C('#FFFFFF', staring)))
                        cv.drawCircle(hx + e_ * hr * 0.33, hy + hr * 0.08, hr * 0.07, paint(C('#000000', staring)))
        cv.drawPath(quad(cam, [(side * 0.42, 0, z + 0.05), (side * 2.0, 0, z + 0.05), (side * 2.0, 0, z + 0.5), (side * 0.42, 0, z + 0.5)]),
                    paint(C('#000000', 0.35), blur=6))                                             # contact shadow under the seats

    far = [k for k in range(z_max, 0, -1) if k * 0.95 > near_sharp]
    near = [k for k in range(z_max, 0, -1) if k * 0.95 <= near_sharp]
    with blurred(cv, blur_far):
        for k in far:
            for side in (-1, 1):
                row(k, side)
        cv.drawCircle(vx, vy, 900, paint('#000', shader=rad((vx, vy), 900, [C('#3A4A6A' if st != 'red' else '#4A1818', 0.55), C('#000000', 0.0)])))
    for k in near:
        for side in (-1, 1):
            row(k, side)
    if st == 'red':
        dim(cv, 0.25 * flicker(t, 3, 4.0, 0.6), '#3A0404')
    if st == 'dark':
        dim(cv, 0.55)


def bokeh(cv, t, n=14, seed=3, col=None):
    """Out-of-focus light discs behind close-ups (window glows, reading lights)."""
    lp = lamp(t)
    for k in range(n):
        x = (k * 397 + seed * 131) % W
        y = 300 + (k * 211 + seed * 71) % 1100
        r = 30 + (k * 37) % 70
        cv.drawCircle(x, y, r, paint(C(col or [WARM, SCREEN, NIGHT][k % 3], 0.18 * lp), blur=6))


def cu_bg(cv, t, who):
    cam = Cam(0.0, eye=1.25, vy=860, facing=1)
    with blurred(cv, 18):
        cabin(cv, cam, t, near_sharp=-1, blur_far=0.1)
    bokeh(cv, t, seed=len(who))
    fabric(cv, (150, 520, 930, 2400), '#22314E')
    cv.drawRoundRect(skia.Rect(240, 560, 840, 860), 60, 60, paint('#E6E2DA', shader=lin((0, 560), (0, 860), [C('#F0ECE4'), C('#C8C4BC')])))


def lit(cv, t, x, y, r=1100, a=0.3):
    """Key light from a reading lamp above + rim from the window: makes the puppet sit IN the scene."""
    if state(t) != 'dark':
        glow(cv, (x, y), r, WARM, a * lamp(t))


def make_cu(who):
    def shot(cv, t):
        cu_bg(cv, t, who)
        P = face_pose(who, t)
        if who == 'L' and t >= B['lsmile']:
            P.update(mouth='smile', pupil=0.35, brow=-0.2)
        shake_ = 4 * math.sin(t * 41) if mood(t) == 'terror' else 0
        mascot(cv, 540 + shake_, 2760, 2.0, light_side=1, rim=NIGHT if state(t) != 'red' else RED, rim_a=0.55,
               look=(0.3 * math.sin(t * 0.8 + len(who)), 0.0), **P)
        lit(cv, t, 760, 300, 1300, 0.22)
        shade(cv, (540, 950), 1100, 0.5)
        grain(cv, t)
    return shot


def attendant(cv, x, y, s_, t, P=None):
    P = dict(long_hair=True, hair='#3A2418', hair_sh='#24160E', shirt='#1E2A44', shirt_sh='#141C30', skin='#E8C0A0', skin_sh='#C89A7A',
             **(P or {}))
    mascot(cv, x, y, s_, light_side=1, rim=WARM, rim_a=0.5, **P)
    cv.drawPath(poly([(x - 60 * s_, y - 520 * s_), (x, y - 420 * s_), (x + 60 * s_, y - 520 * s_), (x + 30 * s_, y - 400 * s_), (x - 30 * s_, y - 400 * s_)]),
                paint('#9A1E24'))                                                                   # scarf


def clicker(cv, x, y, sc, n, t):
    cv.drawRoundRect(skia.Rect(x - 120 * sc, y - 80 * sc, x + 120 * sc, y + 120 * sc), 40 * sc, 40 * sc, paint('#B8BCC4', shader=lin((0, y - 80 * sc), (0, y + 120 * sc), [C('#D8DCE4'), C('#8A8E96')])))
    cv.drawRoundRect(skia.Rect(x - 90 * sc, y - 50 * sc, x + 90 * sc, y + 20 * sc), 10 * sc, 10 * sc, paint('#101410'))
    text(cv, f'{n:03d}', x, y + 5 * sc, 62 * sc, '#E0342C' if n > 212 else '#C8F0C8')
    cv.drawCircle(x, y + 70 * sc, 26 * sc, paint('#3A3E46'))


def count_now(t):
    n = 211
    for k, c in enumerate(B['counts'][:3]):
        if t >= c:
            n = 211 + k
    if t >= B['counts'][0] and t < B['counts'][1]:
        n = 211
    if t >= B['counts'][1]:
        n = 212
    if t >= B['counts'][2]:
        n = 213
    if t >= s('A03'):
        n = 214
    if t >= B['choice'] + 2.0:
        n = 215
    if t >= B['choice'] + 3.5:
        n = 216
    return n


def shot_COUNT(cv, t):
    cam = Cam(0.0, eye=1.5, vy=820)
    with blurred(cv, 10):
        cabin(cv, cam, t, near_sharp=-1, blur_far=0.1)
    bokeh(cv, t, seed=9)
    P = dict(brow=0.9 if t > s('A02') else 0.3, mouth='o' if t > s('A02') else 'flat', mouth_open=talk(t, 'A'), pupil=0.6 if t > s('A02') else 1.0,
             sweat=t > s('A02'), look=(0.0, 0.0))
    if P['mouth_open'] > 0:
        P['mouth'] = 'open'
    attendant(cv, 540, 2850, 2.0, t, P)
    lit(cv, t, 540, 200, 1200, 0.3)
    clicker(cv, 760, 1560, 1.3, count_now(t), t)
    shade(cv, (540, 950), 1100, 0.5)
    grain(cv, t)


def row_front(cv, t, who='BML', faceless=False, dark_=False):
    """Our row seen from the row in front: background cabin out of focus, the three of us sharp."""
    cam = Cam(0.0, eye=1.3, vy=700)
    with blurred(cv, 8):
        cabin(cv, cam, t, near_sharp=-1, blur_far=0.1, staring=0.0)
    cv.drawRect(skia.Rect(0, 0, W, 360), paint('#000', shader=lin((0, 0), (0, 360), [C('#1A2236'), C('#2A3550')])))     # bins above
    cv.drawRect(skia.Rect(0, 340, W, 380), paint('#000', shader=lin((0, 340), (0, 380), [C('#000000', 0.5), C('#000000', 0.0)])))
    for i, w_ in enumerate(who):
        x = (220, 540, 860)[i]
        fabric(cv, (x - 165, 720, x + 165, 1950), '#22314E')
        cv.drawRoundRect(skia.Rect(x - 120, 740, x + 120, 880), 30, 30, paint('#E6E2DA', shader=lin((0, 740), (0, 880), [C('#F2EEE6'), C('#C0BCB4')])))
        if state(t) != 'dark':
            cone(cv, x, 400, 18, 230, 1500, WARM, 0.10 * lamp(t))
        P = face_pose(w_, t)
        mascot(cv, x, 1990, 0.8, legs=False, light_side=1, rim=NIGHT, rim_a=0.4, **P)
    if faceless:
        mascot(cv, 380, 1990, 0.86, legs=False, faceless=True, skin='#8A8480', skin_sh='#5A5450', shirt='#1A1A1A', shirt_sh='#0A0A0A',
               hair='#0A0A0A', hair_sh='#000000', light_side=1, rim=RED, rim_a=0.7)
    for x in (60, 380, 700, 1020):
        cv.drawRoundRect(skia.Rect(x - 25, 1560, x + 25, 1920), 20, 20, paint('#2A2E36', shader=lin((x - 25, 0), (x + 25, 0), [C('#3A3E48'), C('#1A1E26')])))
    cv.drawRect(skia.Rect(0, 1840, W, H), paint('#000', shader=lin((0, 1840), (0, H), [C('#000000', 0.0), C('#000000', 0.6)])))
    if dark_ or state(t) == 'dark':
        dim(cv, 0.7)


def shot_ROW(cv, t):
    row_front(cv, t)
    shade(cv, (540, 1100), 1300, 0.45)
    grain(cv, t)


def shot_AISLE(cv, t):
    cam = Cam(-0.5 + (t - B['aisle']) * 0.12, eye=1.25, vy=880)
    cabin(cv, cam, t, near_sharp=3.0, blur_far=5.0)
    shade(cv, (540, 950), 1200, 0.45)
    grain(cv, t)


def seat_closeup(cv, t, x, y, sc, flip=False, window=True):
    """One window seat filling the frame, the cabin behind out of focus."""
    cam = Cam(0.0, eye=1.25, vy=820)
    with blurred(cv, 14):
        cabin(cv, cam, t, near_sharp=-1, blur_far=0.1)
    if window:
        wx = 140 if not flip else 940
        cv.drawRoundRect(skia.Rect(wx - 110, 500, wx + 110, 900), 100, 100, paint('#1A2034'))
        cv.drawRoundRect(skia.Rect(wx - 90, 520, wx + 90, 880), 85, 85, paint('#000', shader=lin((0, 520), (0, 880), [C('#04060E'), C('#101C34')])))
    fabric(cv, (x - 260 * sc, y - 1300 * sc, x + 260 * sc, y + 100), '#22314E')
    cv.drawRoundRect(skia.Rect(x - 190 * sc, y - 1270 * sc, x + 190 * sc, y - 1060 * sc), 40, 40, paint('#E6E2DA'))


def shot_MAN(cv, t):
    seat_closeup(cv, t, 540, 1950, 1.0, flip=True)
    eyes = 1.0 if (s('B02') + 1.0 <= t < s('B02') + 1.07) else 0.0                       # 2 frames: his eyes are open
    P = dict(CAST['Q'], lids=1.0 - eyes, brow=0.0, mouth='o', mouth_open=0.15, head_tilt=-14, pupil=0.3, look=(0.0, 0.0))
    mascot(cv, 540, 2650, 1.55, legs=False, light_side=1, rim=NIGHT, rim_a=0.35, **P)
    lit(cv, t, 300, 300, 1100, 0.15)
    text(cv, '22C', 900, 700, 46, '#C8C8C8', alpha=0.8)
    shade(cv, (540, 950), 1100, 0.5)
    grain(cv, t)


def shot_MANTURN(cv, t):
    seat_closeup(cv, t, 540, 1950, 1.0, flip=True)
    P = dict(CAST['Q'], void_eyes=True, mouth='wide', mouth_open=0.0, head_tilt=24, brow=-0.4)
    mascot(cv, 540 + 6 * math.sin(t * 50), 2650, 1.75, legs=False, light_side=1, rim=RED, rim_a=0.7, **P)
    dim(cv, 0.2, '#3A0404')
    shade(cv, (540, 950), 1000, 0.55)
    grain(cv, t, 0.1)


def girl(cv, t, x, y, sc, P_extra=None):
    P = face_pose('G', t) if 'G' in CAST else {}
    P.update(CAST['G'])
    P['mouth_open'] = talk(t, 'G')
    P.update(brow=0.0, mouth='smile' if P['mouth_open'] == 0 else 'open', sweat=False, pupil=0.7)
    P.update(P_extra or {})
    mascot(cv, x, y, sc, legs=False, light_side=1, rim=NIGHT, rim_a=0.45, **P)


def shot_GIRL(cv, t):
    seat_closeup(cv, t, 540, 1950, 1.0)
    girl(cv, t, 540, 2350, 1.25, dict(look=(0.0, 0.5 if t < s('G01') else 0.0)))
    cv.drawRect(skia.Rect(120, 1650, 960, 1700), paint('#5A5E66'))                            # tray + pad + crayon
    cv.drawRect(skia.Rect(300, 1560, 780, 1660), paint('#F4F0E6'))
    cx = 560 + 80 * math.sin(t * 7)
    cv.drawLine(cx, 1600, cx + 40, 1520, paint('#C83030', style='stroke', width=14))
    text(cv, '23A', 900, 700, 46, '#C8C8C8', alpha=0.8)
    lit(cv, t, 700, 300, 1100, 0.18)
    shade(cv, (540, 950), 1100, 0.5)
    grain(cv, t)


def figure(cv, x, y, sc, col='#2A2A6A', face=True):
    cv.drawCircle(x, y, 22 * sc, paint(col, style='stroke', width=5 * sc))
    if face:
        cv.drawCircle(x - 7 * sc, y - 4 * sc, 3 * sc, paint(col)); cv.drawCircle(x + 7 * sc, y - 4 * sc, 3 * sc, paint(col))
    else:
        cv.drawCircle(x, y, 20 * sc, paint('#101010'))
    cv.drawLine(x, y + 22 * sc, x, y + 80 * sc, paint(col, style='stroke', width=5 * sc))
    cv.drawLine(x - 30 * sc, y + 45 * sc, x + 30 * sc, y + 45 * sc, paint(col, style='stroke', width=5 * sc))


def paper(cv):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2E36'))
    cv.save(); cv.rotate(-3, 540, 960)
    cv.drawRect(skia.Rect(80, 380, 1000, 1560), paint('#F4F0E6', shader=lin((0, 380), (0, 1560), [C('#FAF6EC'), C('#E4DED0')])))
    for k in range(30):
        cv.drawLine(80, 420 + k * 38, 1000, 420 + k * 38, paint(C('#A0B8D8', 0.25), style='stroke', width=2))


def shot_DRAWING(cv, t):
    paper(cv)
    for r in range(4):
        for c in range(9):
            figure(cv, 160 + c * 95, 520 + r * 190, 0.8, ['#2A2A6A', '#2A6A2A', '#6A2A2A'][(r + c) % 3])
    u = t - B['drawing']
    if u > 0.4:                                                                                # the one between us: no face
        cv.drawRect(skia.Rect(330, 1290, 760, 1500), paint(C('#F4F0E6', 1.0)))
        figure(cv, 400, 1340, 1.3, '#2A6A2A'); figure(cv, 690, 1340, 1.3, '#2A2A6A')
        figure(cv, 545, 1330, 1.5, '#101010', face=False)
        text(cv, 'ME', 400, 1500, 34, '#2A6A2A'); text(cv, 'BOB', 690, 1500, 34, '#2A2A6A')
    text(cv, '213', 880, 470, 70, '#C83030')
    cv.restore()
    dim(cv, 0.15)
    shade(cv, (540, 950), 1000, 0.45)
    grain(cv, t)


def shot_DARK(cv, t):
    row_front(cv, t, dark_=True)
    if t > B['dark'] + 0.25 and int(t * 12) % 7 == 0:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#FFFFFF', 0.05)))
    shade(cv, (540, 1100), 1100, 0.6)
    grain(cv, t, 0.1)


def shot_FACELESS(cv, t):
    if t < B['choice']:
        row_front(cv, t, faceless=True)
        dim(cv, 0.35)
    else:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A0404'))
        mascot(cv, 540, 3300, 2.6, faceless=True, skin='#8A8480', skin_sh='#5A5450', shirt='#1A1A1A', shirt_sh='#0A0A0A',
               hair='#0A0A0A', hair_sh='#000000', light_side=1, rim=RED, rim_a=0.8)
    shade(cv, (540, 1000), 1000, 0.5)
    grain(cv, t, 0.12)


def shot_TICKETS(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A3E46', shader=lin((0, 0), (0, H), [C('#4A4E58'), C('#24262E')])))
    for i, (seat, name) in enumerate((('22A', 'BOB'), ('22B', 'YOU'))):
        y = 620 + i * 560
        cv.save(); cv.rotate(-4 + i * 7, 540, y + 200)
        cv.drawRoundRect(skia.Rect(140, y, 940, y + 420), 20, 20, paint('#F4F0E6', shader=lin((0, y), (0, y + 420), [C('#FFFFFF'), C('#E2DCD0')])))
        cv.drawRect(skia.Rect(140, y, 940, y + 90), paint('#1E2A44'))
        text(cv, 'BOARDING PASS · FLIGHT 1213', 540, y + 60, 40, '#F4F0E6')
        text(cv, 'PASSENGER', 280, y + 170, 30, '#6A6A6A'); text(cv, name, 280, y + 240, 70, '#1A1A1A')
        text(cv, 'SEAT', 760, y + 170, 30, '#6A6A6A'); text(cv, seat, 760, y + 260, 110, '#C83030')
        cv.restore()
    glow(cv, (540, 300), 900, WARM, 0.2)
    shade(cv, (540, 950), 1000, 0.45)
    grain(cv, t)


def shot_LSMILE(cv, t):
    cu_bg(cv, t, 'L')
    dim(cv, 0.6)
    P = face_pose('L', t)
    P.update(mouth='smile', pupil=0.35, brow=-0.3)
    mascot(cv, 540, 2760, 2.0, light_side=1, rim=SCREEN, rim_a=0.6, look=(0.0, 0.0), **P)
    glow(cv, (540, 1900), 900, SCREEN, 0.35)                                                   # lit from below by a screen
    shade(cv, (540, 950), 1000, 0.55)
    grain(cv, t, 0.1)


def shot_GIRL2(cv, t):
    seat_closeup(cv, t, 540, 1950, 1.0)
    girl(cv, t, 540, 2350, 1.25, dict(look=(0.0, 0.0)))
    cv.save(); cv.rotate(-5, 540, 1500)                                                       # she holds the drawing up
    cv.drawRect(skia.Rect(180, 1180, 900, 1760), paint('#F4F0E6'))
    for k, (x, lab, col) in enumerate(((300, '1', '#4A4A52'), (540, '2', '#C83030'), (780, '3', '#6A4A8A'))):
        figure(cv, x, 1360, 1.4, col)
        text(cv, lab, x, 1660, 60, col)
    cv.drawCircle(540, 1360, 120, paint('#C83030', style='stroke', width=6))
    cv.restore()
    lit(cv, t, 700, 300, 1100, 0.18)
    shade(cv, (540, 950), 1100, 0.5)
    grain(cv, t)


def shot_CHOICE(cv, t):
    cam = Cam(0.0, eye=1.3, vy=820)
    st = min(1.0, max(0.0, (t - B['choice']) / 1.0))
    cabin(cv, cam, t, near_sharp=2.5, blur_far=6.0, staring=st)
    shade(cv, (540, 950), 1100, 0.55)
    grain(cv, t, 0.1)


SHOTS = {k[5:]: v for k, v in dict(globals()).items() if k.startswith('shot_')}
for _w in 'MBL':
    SHOTS['CU_' + _w] = make_cu(_w)


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
