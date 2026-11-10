#!/usr/bin/env python3
"""VIDEO_020 "Testicular Pressure Syndrome" — real 2D horror (2dEDIT), flat vector drawn with Skia.

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
import edit_video020 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS, JS, s, e = E.B, E.LS, E.WORDS, E.JS, E.s, E.e
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


WARM, COOL, RED = '#FFD9A0', '#9FC8E8', '#E0342C'
MOAN = E.MOAN
SUIT = {'doc': dict(shirt='#D8E4EC', shirt_sh='#B4C4D0'), 'office': dict(shirt='#2A3A5A', shirt_sh='#1C2840'),
        'wedding': dict(shirt='#1A1A1E', shirt_sh='#0E0E12'), 'home': dict(shirt='#E87A20', shirt_sh='#C0601A')}


def place(t):
    if t < B['office']:
        return 'doc'
    if t < B['wedding']:
        return 'office'
    if t < B['phone']:
        return 'wedding'
    return 'home'


def moaning(t):
    return any(a <= t < b for a, b in MOAN)


def face_pose(who, t):
    P = dict(CAST.get(who, {}))
    P['mouth_open'] = talk(t, who)
    if who == 'M':
        P.update(SUIT[place(t)])
        P.update(brow=0.8, mouth='o', pupil=0.6, sweat=True, look=(0.0, 0.0))
        if moaning(t):
            P.update(lids=0.75, brow=1.0, mouth='o', blush=0.9, head_tilt=-10 + 6 * math.sin(t * 9))
        if B['alarm'] <= t < s('M06'):
            P.update(brow=1.0, mouth='open', mouth_open=1.0, pupil=0.25)
        if t >= s('M08') - 0.3:
            P.update(brow=0.2, mouth='smile', lids=0.35, blush=0.6)
    else:
        P.update(brow=0.2, mouth='flat', pupil=1.0)
    if P['mouth_open'] > 0 and P.get('mouth') in ('flat', 'smile', 'o'):
        P['mouth'] = 'open'
    P['lids'] = max(P.get('lids', 0.0), blink(t, [k * 3.3 + len(who) for k in range(40)]))
    return P


def hospital(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#C8D8DC'), C('#8AA0A6')])))
    with blurred(cv, 10):
        for k in range(6):                                                                     # window blinds light stripes
            cv.drawRect(skia.Rect(700, 300 + k * 70, 1080, 330 + k * 70), paint(C('#FFFFFF', 0.6)))
        cv.drawRect(skia.Rect(60, 400, 360, 900), paint('#E8ECEE'))                           # cabinet
        for k in range(3):
            cv.drawRect(skia.Rect(80, 420 + k * 160, 340, 560 + k * 160), paint('#C8D0D4', style='stroke', width=6))
        cv.drawRect(skia.Rect(0, 1300, W, H), paint('#7A8A90'))
        cv.drawCircle(540, 260, 60, paint(C('#FFFFFF', 0.8)))
    glow(cv, (540, 260), 1200, '#FFFFFF', 0.2)
    cv.drawRect(skia.Rect(0, 0, W, 330), paint('#000000', shader=lin((0, 0), (0, 330), [C('#0A1418', 0.75), C('#0A1418', 0.0)])))   # dark band so the HUD reads


def office(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#3A4A5A'), C('#1E2630')])))
    with blurred(cv, 11):
        for k in range(4):                                                                     # city window at night
            for j in range(9):
                if (k * 7 + j * 3) % 4:
                    cv.drawRect(skia.Rect(80 + j * 105, 300 + k * 150, 140 + j * 105, 380 + k * 150), paint(C('#FFD890', 0.5)))
        cv.drawRect(skia.Rect(0, 900, W, 960), paint('#2A2E36'))
        cv.drawRect(skia.Rect(880, 600, 1000, 950), paint('#2A6A3A'))                         # plant
    glow(cv, (540, 300), 1100, WARM, 0.15)


def wedding(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#3A2A2E'), C('#1A1216')])))
    with blurred(cv, 12):
        for k in range(26):                                                                    # string lights bokeh
            x = (k * 83) % W
            y = 260 + 60 * math.sin(k * 0.6) + (k % 3) * 40
            cv.drawCircle(x, y, 26, paint(C('#FFD890', 0.8)))
        cv.drawRect(skia.Rect(0, 1100, W, H), paint('#2A1E22'))
        for k in range(7):                                                                     # guests at tables
            cv.drawCircle(80 + k * 160, 1050, 50, paint(C('#4A3A3E', 0.9)))
        for x in (120, 960):
            cv.drawCircle(x, 760, 120, paint(C('#E8B8C8', 0.7)))                              # flowers
    glow(cv, (540, 350), 1200, WARM, 0.25)


def apartment(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#2E2A3A'), C('#14121C')])))
    with blurred(cv, 10):
        cv.drawRect(skia.Rect(700, 380, 1000, 760), paint('#0A1830')); cv.drawCircle(850, 470, 28, paint('#EEF2F6'))
        for k in range(12):                                                                    # tissue boxes everywhere
            x, y = (k * 171) % 1000 + 40, 1150 + (k * 97) % 400
            cv.drawRect(skia.Rect(x, y, x + 110, y + 70), paint('#E8E8F0'))
    glow(cv, (300, 500), 900, WARM, 0.2)


def bg(cv, t):
    {'doc': hospital, 'office': office, 'wedding': wedding, 'home': apartment}[place(t)](cv, t)


def make_cu(who):
    def shot(cv, t):
        bg(cv, t)
        P = face_pose(who, t)
        j = 6 * math.sin(t * 47) if (who == 'M' and (moaning(t) or B['alarm'] <= t < s('M06'))) else 0
        mascot(cv, 540 + j, 2760, 2.0, light_side=1, rim=WARM, rim_a=0.45, **P)
        shade(cv, (540, 950), 1100, 0.45)
        grain(cv, t)
    return shot


def shot_CU_A(cv, t):
    office(cv, t)
    P = face_pose('A', t)
    P.update(long_hair=True, hair='#2A1A10', hair_sh='#1A0E08', shirt='#5A2A3A', shirt_sh='#401E2A', skin='#E8C0A0', skin_sh='#C89A7A',
             glasses='#1A1A1A', brow=0.7 if t >= s('A02') else 0.1, mouth='o' if t >= s('A02') else 'flat')
    if P['mouth_open'] > 0:
        P['mouth'] = 'open'
    mascot(cv, 540, 2760, 2.0, light_side=-1, rim=WARM, rim_a=0.4, **P)
    shade(cv, (540, 950), 1100, 0.45)
    grain(cv, t)


def shot_XRAY(cv, t):
    hospital(cv, t)
    cv.drawRoundRect(skia.Rect(140, 420, 940, 1260), 20, 20, paint('#1A1E22'))
    cv.drawRect(skia.Rect(180, 460, 900, 1220), paint('#000000', shader=rad((540, 840), 520, [C('#C8E8FF'), C('#5A7A9A')])))
    p = 1.0 + 0.04 * math.sin(t * 14)                                                              # two round shapes, pulsing
    for x in (430, 650):
        cv.drawCircle(x, 860, 140 * p, paint(C('#FFFFFF', 0.85)))
        cv.drawCircle(x, 860, 140 * p, paint('#2A3A4A', style='stroke', width=6))
        for k in range(4):
            a = k * 1.4 + (x / 100)
            cv.drawLine(x + math.cos(a) * 40, 860 + math.sin(a) * 40, x + math.cos(a) * 130, 860 + math.sin(a) * 130, paint('#2A3A4A', style='stroke', width=5))
    text(cv, 'PRESSURE: CRITICAL', 540, 560, 54, '#E0342C')
    text(cv, 'DO NOT STOP', 540, 1170, 60, '#1A1A1A')
    shade(cv, (540, 900), 1100, 0.35)
    grain(cv, t)


def shot_DOC(cv, t):
    hospital(cv, t)
    P = dict(skin='#C89A7A', skin_sh='#A87A5A', hair='#D8D8D8', hair_sh='#B0B0B0', shirt='#F4F4F4', shirt_sh='#D0D0D0', glasses='#1A1A1A',
             mustache=True, brow=-0.2, mouth='flat', mouth_open=talk(t, 'C'), lids=0.3)
    if P['mouth_open'] > 0:
        P['mouth'] = 'open'
    mascot(cv, 330, 2300, 1.25, legs=False, light_side=1, rim=COOL, rim_a=0.3, **P)
    cv.drawRoundRect(skia.Rect(160, 1500, 420, 1820), 14, 14, paint('#8A5A2A'))                     # clipboard
    cv.drawRect(skia.Rect(180, 1530, 400, 1800), paint('#F4F0E6'))
    text(cv, 'TPS', 290, 1620, 54, '#E0342C')
    Pm = face_pose('M', t)
    mascot(cv, 800, 2350, 1.15, legs=False, light_side=-1, rim=COOL, rim_a=0.3, **Pm)
    cv.drawRect(skia.Rect(560, 1700, 1080, H), paint('#E8ECEE'))                                     # exam table sheet
    shade(cv, (540, 950), 1100, 0.4)
    grain(cv, t)


def desk_shake(t):
    return (5 * math.sin(t * 53)) if not (B['stop'] <= t < s('M06')) else 0.0


def shot_OFFICE(cv, t):
    office(cv, t)
    P = face_pose('M', t)
    mascot(cv, 540, 2250, 1.2, legs=False, light_side=1, rim=WARM, rim_a=0.4, **P)
    j = desk_shake(t) * (2.2 if moaning(t) else 1.0)
    cv.drawRect(skia.Rect(0, 1450 + j, W, 1530 + j), paint('#000000', shader=lin((0, 1450), (0, 1530), [C('#8A5A3A'), C('#5A3A22')])))
    cv.drawRect(skia.Rect(40, 1530 + j, W - 40, H), paint('#000000', shader=lin((0, 1530), (0, H), [C('#5A3A22'), C('#2A1A10')])))
    cx = 820                                                                                          # coffee cup, ripples
    cv.drawRoundRect(skia.Rect(cx - 70, 1300 + j, cx + 70, 1460 + j), 16, 16, paint('#F0F0F0'))
    cv.drawOval(skia.Rect(cx - 62, 1295 + j, cx + 62, 1325 + j), paint('#4A2A14'))
    for r in range(3):
        rr = (t * 90 + r * 20) % 60
        cv.drawOval(skia.Rect(cx - rr, 1306 + j - rr * 0.2, cx + rr, 1314 + j + rr * 0.2), paint(C('#C8A080', 0.6), style='stroke', width=2))
    cv.drawRect(skia.Rect(200, 1380 + j, 560, 1450 + j), paint('#E8E4DC'))                          # resume
    text(cv, 'RESUME', 380, 1430 + j, 40, '#1A1A1A')
    shade(cv, (540, 950), 1150, 0.4)
    grain(cv, t)


def shot_WEDDING(cv, t):
    wedding(cv, t)
    P = face_pose('M', t)
    mascot(cv, 540, 2300, 1.25, legs=False, light_side=1, rim=WARM, rim_a=0.5, **P)
    j = desk_shake(t) * (2.5 if moaning(t) else 1.0)
    cv.drawPath(poly([(270, 1500 + j), (810, 1500 + j), (760, H), (320, H)]), paint('#000000', shader=lin((0, 1500), (0, H), [C('#8A6A4A'), C('#4A3420')])))
    cv.drawRect(skia.Rect(250, 1470 + j, 830, 1520 + j), paint('#A88A62'))
    cv.drawCircle(540, 1640 + j, 70, paint(C('#E8D8B0', 0.8)))                                       # podium crest
    cv.drawLine(620, 1470 + j, 690, 1180, paint('#2A2A2A', style='stroke', width=10))                 # mic on stand
    cv.drawOval(skia.Rect(670, 1130, 720, 1200), paint('#3A3A3A'))
    Pb = dict(CAST['B'], shirt='#1A1A1E', shirt_sh='#0E0E12', brow=0.9 if t < s('M06') else -0.3, mouth='flat', mouth_open=talk(t, 'B'))
    if Pb['mouth_open'] > 0:
        Pb['mouth'] = 'open'
    if t >= s('M06') + 1.4:
        Pb.update(mouth='smile')
    mascot(cv, 950, 2150, 0.85, legs=False, light_side=-1, rim=WARM, rim_a=0.4, **Pb)
    shade(cv, (540, 950), 1150, 0.4)
    grain(cv, t)


def shot_ALARM(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120606'))
    cv.drawCircle(540, 900, 380, paint('#000000', shader=rad((540, 900), 380, [C('#F4F0E6'), C('#C8C0B0')])))
    cv.drawCircle(540, 900, 380, paint('#3A3A3A', style='stroke', width=26))
    for k in range(11):
        a = math.radians(-210 + k * 24)
        cv.drawLine(540 + math.cos(a) * 300, 900 + math.sin(a) * 300, 540 + math.cos(a) * 350, 900 + math.sin(a) * 350,
                    paint('#E0342C' if k > 7 else '#1A1A1A', style='stroke', width=10))
    a = math.radians(-210 + 240 * min(1.0, 0.85 + (t - B['alarm']) * 0.4) + 4 * math.sin(t * 60))
    cv.drawLine(540, 900, 540 + math.cos(a) * 320, 900 + math.sin(a) * 320, paint('#E0342C', style='stroke', width=16))
    cv.drawCircle(540, 900, 34, paint('#1A1A1A'))
    text(cv, 'BALL PRESSURE', 540, 1120, 56, '#1A1A1A')
    if int(t * 6) % 2 == 0:
        text(cv, 'WARNING', 540, 1500, 130, '#E0342C')
    glow(cv, (540, 900), 1000, RED, 0.25)
    grain(cv, t)


def shot_PHONE(cv, t):
    apartment(cv, t)
    P = face_pose('M', t)
    mascot(cv, 540, 2600, 1.75, legs=False, light_side=1, rim=WARM, rim_a=0.45, **P)
    cv.drawRoundRect(skia.Rect(780, 700, 900, 1000), 20, 20, paint('#1A1A1E'))                    # phone at his ear
    cv.drawRoundRect(skia.Rect(790, 715, 890, 985), 14, 14, paint(C('#7FB8FF', 0.7)))
    cv.drawRect(skia.Rect(0, 1700, W, H), paint('#000000', shader=lin((0, 1700), (0, H), [C('#3A3A6A'), C('#1E1E3A')])))  # blanket
    j = 8 * math.sin(t * 50)
    cv.save(); cv.rotate(-5, 540, 1790 + j)
    cv.drawRect(skia.Rect(270, 1730 + j, 810, 1840 + j), paint('#0A0A0A'))
    text(cv, 'CENSORED', 540, 1810 + j, 72, '#FFFFFF')
    cv.restore()
    text(cv, 'DAY 1,095', 540, 560, 64, '#FFFFFF')
    shade(cv, (540, 950), 1150, 0.4)
    grain(cv, t)


SHOTS = {k[5:]: v for k, v in dict(globals()).items() if k.startswith('shot_')}
SHOTS['CU_M'] = make_cu('M')


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
