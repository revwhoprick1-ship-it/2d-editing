#!/usr/bin/env python3
"""VIDEO_019 "What If You Never Stopped?" — real 2D horror (2dEDIT), flat vector drawn with Skia.

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
import edit_video019 as E  # noqa

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


MONITOR = '#7FB8FF'
LAMP = '#FFC27A'


def room(cv, t, door_open=0.0, night=True):
    """Bedroom at night: blurred posters + shelf in the back, monitor glow, moonlit window, lamp pool. Depth, not a flat wall."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#1A1E2E'), C('#0E1018')])))
    with blurred(cv, 9):
        cv.drawRect(skia.Rect(0, 1250, W, H), paint('#000000', shader=lin((0, 1250), (0, H), [C('#2A2420'), C('#14100C')])))
        for x, y, w_, h_, c in ((90, 380, 230, 320, '#6A2A3A'), (760, 330, 220, 300, '#2A4A6A')):                 # posters
            cv.drawRect(skia.Rect(x, y, x + w_, y + h_), paint(c))
            cv.drawCircle(x + w_ / 2, y + h_ * 0.4, w_ * 0.25, paint(C('#E8D8B0', 0.5)))
        cv.drawRect(skia.Rect(380, 600, 700, 630), paint('#3A2A1E'))                                          # shelf + stuff
        for k in range(5):
            cv.drawRect(skia.Rect(400 + k * 60, 520 - (k % 2) * 30, 440 + k * 60, 600), paint(['#8A3A2A', '#2A6A8A', '#C8A040', '#4A8A4A', '#6A4A8A'][k]))
        cv.drawRoundRect(skia.Rect(860, 760, 1040, 1100), 10, 10, paint('#0A1830'))                          # window
        cv.drawCircle(950, 860, 30, paint('#EEF2F6'))
        glow(cv, (950, 930), 500, '#9FC0E0', 0.18)
        if door_open > 0:                                                                                   # hallway light spill
            cv.drawRect(skia.Rect(40, 500, 40 + 300 * door_open, 1500), paint(C('#FFE6B0', 0.9)))
    glow(cv, (200, 1100), 700, MONITOR, 0.22 + 0.05 * math.sin(t * 7))
    glow(cv, (540, 300), 900, LAMP, 0.12)


def bed(cv, t, shake=1.0, censor=True, P=None, sc=1.0, fire=0.0, cobweb=0.0):
    """Mascot sitting up in bed; the blanket bump jitters; a CENSORED bar covers it."""
    cv.drawRoundRect(skia.Rect(60, 820, 1020, 1300), 40, 40, paint('#000000', shader=lin((0, 820), (0, 1300), [C('#4A3426'), C('#2A1C14')])))   # headboard
    cv.drawRoundRect(skia.Rect(180, 980, 900, 1220), 80, 80, paint('#E8E2D6'))                                 # pillow
    mascot(cv, 540, 2230, 1.15 * sc, legs=False, light_side=-1, rim=MONITOR, rim_a=0.5, **(P or {}))
    j = shake * 10 * math.sin(t * 61)
    bl = blob([(0, 1500 + j), (300, 1440 + j), (540, 1380 + j * 1.6), (780, 1440 + j), (1080, 1500 + j), (1080, H), (0, H)])
    cv.drawPath(bl, paint('#000000', shader=lin((0, 1380), (0, H), [C('#3A6A9A'), C('#1E3A5A')])))
    for k in range(6):                                                                                        # blanket folds
        cv.drawLine(120 + k * 160, 1520 + j, 160 + k * 160, 1880, paint(C('#000000', 0.18), style='stroke', width=10, blur=4))
    cv.drawPath(bl, paint(C(MONITOR, 0.35), style='stroke', width=8, blur=4))
    if censor:
        cv.save(); cv.rotate(-6, 540, 1560 + j)
        cv.drawRect(skia.Rect(250, 1500 + j, 830, 1620 + j), paint('#0A0A0A'))
        text(cv, 'CENSORED', 540, 1585 + j, 80, '#FFFFFF')
        cv.restore()
    if fire > 0:
        for k in range(9):
            fx = 160 + k * 95
            h_ = (180 + 120 * math.sin(t * 13 + k * 1.7)) * fire
            cv.drawPath(blob([(fx - 60, 1560), (fx, 1560 - h_), (fx + 60, 1560)]), paint('#FF8A20'))
            cv.drawPath(blob([(fx - 30, 1560), (fx, 1560 - h_ * 0.6), (fx + 30, 1560)]), paint('#FFE060'))
        glow(cv, (540, 1450), 900, '#FF8A20', 0.4 * fire)
    if cobweb > 0:
        for k in range(7):
            cv.drawLine(0, 0, 300 * math.cos(k * 0.22), 300 * math.sin(k * 0.22), paint(C('#D8D8D8', 0.6 * cobweb), style='stroke', width=2))
        for r in (90, 170, 250):
            cv.drawArc(skia.Rect(-r, -r, r, r), 0, 90, False, paint(C('#D8D8D8', 0.5 * cobweb), style='stroke', width=2))


def strain(t, o=0.0):
    return dict(brow=1.0, mouth='o', mouth_open=0.2 + 0.15 * math.sin(t * 20), pupil=0.55, sweat=True, lids=0.15, look=(0.3, 0.0))


def shot_BED(cv, t):
    room(cv, t)
    bed(cv, t, P=strain(t))
    shade(cv, (540, 1000), 1200, 0.45)
    grain(cv, t)


def shot_COOKIE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=rad((540, 900), 1100, [C('#3A2A1E'), C('#100C08')])))
    with blurred(cv, 12):
        for k in range(10):
            cv.drawCircle((k * 263) % W, 300 + (k * 179) % 1300, 40 + (k * 31) % 60, paint(C(LAMP, 0.25)))
    u = t - B['N02']
    cv.save(); cv.translate(540, 900); cv.rotate(8 * math.sin(t * 2))
    ck = skia.Path(); ck.addCircle(0, 0, 330)
    if u > 1.6:                                                                                             # someone took a bite
        bite = skia.Path(); bite.addCircle(260, -200, 150)
        ck = skia.Op(ck, bite, skia.PathOp.kDifference_PathOp)
    cv.drawPath(ck, paint('#000000', shader=rad((-60, -60), 420, [C('#E8B060'), C('#B07830')])))
    for k in range(9):
        a = k * 2.2
        cv.drawPath(blob([(math.cos(a) * 180 * (k % 3) / 2 - 30, math.sin(a) * 180 * (k % 3) / 2), (math.cos(a) * 180 * (k % 3) / 2, math.sin(a) * 180 * (k % 3) / 2 - 30),
                          (math.cos(a) * 180 * (k % 3) / 2 + 30, math.sin(a) * 180 * (k % 3) / 2)]), paint('#4A2A14'))
    cv.restore()
    text(cv, '100 KCAL', 540, 1360, 110, '#FFFFFF')
    text(cv, '= ONE (1) COOKIE', 540, 1470, 70, '#E0342C')
    shade(cv, (540, 950), 1100, 0.4)
    grain(cv, t)


def shot_RAISIN(cv, t):
    room(cv, t)
    P = strain(t)
    P.update(skin='#8A5A6A', skin_sh='#6A3A4A', mouth='o', lids=0.4)
    bed(cv, t, P=P, sc=0.9)
    for k in range(6):                                                                                     # wrinkles
        cv.drawLine(400 + k * 40, 820 + (k % 2) * 30, 440 + k * 40, 840 + (k % 2) * 30, paint(C('#3A1A2A', 0.6), style='stroke', width=5))
    cv.drawRoundRect(skia.Rect(760, 600, 1020, 900), 20, 20, paint(C('#2A8AE0', 0.85)))                    # empty water bottle
    text(cv, '-2 L', 890, 780, 80, '#FFFFFF')
    shade(cv, (540, 1000), 1200, 0.45)
    grain(cv, t)


def shot_WRIST(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=lin((0, 0), (0, H), [C('#2A2E3A'), C('#14161E')])))
    with blurred(cv, 14):
        room(cv, t)
    skin, sh = '#F2C29B', '#D99B76'
    cv.save(); cv.rotate(-75, 420, 1150)                                                                      # arm lying sideways on the pillow
    cv.drawRoundRect(skia.Rect(260, 700, 560, 1700), 120, 120, paint(sh))                                   # forearm
    cv.drawRoundRect(skia.Rect(240, 1100, 580, 1320), 40, 40, paint('#F0ECE4'))                             # bandage
    for k in range(5):
        cv.drawLine(240, 1120 + k * 45, 580, 1140 + k * 45, paint(C('#B8B4AC', 0.8), style='stroke', width=4))
    cv.drawRoundRect(skia.Rect(200, 1000, 620, 1110), 50, 50, paint('#7AC8F0'))                             # ice pack
    text(cv, 'ICE', 410, 1075, 60, '#FFFFFF')
    cv.drawCircle(410, 640, 170, paint(skin))                                                                 # hand (limp)
    cv.restore()
    cv.save(); cv.rotate(6, 820, 1100)                                                                        # divorce papers
    cv.drawRect(skia.Rect(640, 760, 1020, 1300), paint('#F4F0E6'))
    text(cv, 'DIVORCE', 830, 860, 60, '#1A1A1A'); text(cv, 'PAPERS', 830, 930, 50, '#1A1A1A')
    for k in range(5):
        cv.drawLine(680, 1000 + k * 40, 980, 1000 + k * 40, paint('#A0A0A0', style='stroke', width=4))
    text(cv, 'signed: WRIST', 830, 1260, 34, '#C83030')
    cv.restore()
    shade(cv, (540, 950), 1100, 0.45)
    grain(cv, t)


def shot_FIRE(cv, t):
    room(cv, t)
    P = strain(t)
    P.update(mouth='open', mouth_open=0.8, brow=1.0, pupil=0.4)
    bed(cv, t, P=P, fire=1.0)
    u = t - B['N05']
    if u > 1.2:                                                                                             # fire extinguisher
        cv.drawRoundRect(skia.Rect(880, 900, 1000, 1300), 30, 30, paint('#C82020'))
        for k in range(30):
            a = -2.4 + (k % 7) * 0.08
            r = ((u - 1.2) * 900 + k * 37) % 700
            cv.drawCircle(880 + math.cos(a) * r, 1000 + math.sin(a) * r * 0.4 + 300, 30 + k % 4 * 10, paint(C('#F0F0F0', 0.7)))
    text(cv, 'FRICTION: 1', 540, 560, 80, '#FFFFFF'); text(cv, 'YOU: 0', 540, 660, 80, '#E0342C')
    shade(cv, (540, 1000), 1200, 0.4)
    grain(cv, t)


def shot_REBOOT(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#05070C'))
    cv.drawRoundRect(skia.Rect(120, 440, 960, 1500), 40, 40, paint('#000000', shader=lin((0, 440), (0, 1500), [C('#0C1830'), C('#060A14')])))
    text(cv, 'SYSTEM', 540, 640, 100, '#FFFFFF')
    text(cv, 'REBOOTING...', 540, 760, 90, '#FFFFFF')
    a = t * 360 % 360                                                                                         # spinner
    for k in range(8):
        ang = math.radians(a + k * 45)
        cv.drawCircle(540 + math.cos(ang) * 90, 960 + math.sin(ang) * 90, 18, paint(C('#7FB8FF', 0.2 + k * 0.1)))
    cv.drawRoundRect(skia.Rect(220, 1160, 860, 1220), 30, 30, paint('#1A2236'))
    cv.drawRoundRect(skia.Rect(220, 1160, 220 + 640 * 0.03, 1220), 30, 30, paint('#E0342C'))
    text(cv, '3%  ·  PLEASE WAIT 20 MIN', 540, 1320, 46, '#9AA8B8')
    glow(cv, (540, 950), 900, MONITOR, 0.15)
    grain(cv, t)


def shot_SIT(cv, t):
    room(cv, t)
    P = dict(brow=0.4, mouth='flat', lids=0.55, pupil=0.7, sweat=False, look=(0.0, 0.0))
    bed(cv, t, shake=0.0, P=P, cobweb=min(1.0, (t - B['N07']) / 1.5))
    for k in range(int(min(6, (t - B['N07']) * 4))):                                                         # dust motes
        x = 200 + (k * 151) % 700
        cv.drawCircle(x, 500 + (t * 40 + k * 90) % 900, 4, paint(C('#E8E0C8', 0.6)))
    shade(cv, (540, 1000), 1200, 0.5)
    grain(cv, t)


def shot_DOOR(cv, t):
    u = min(1.0, max(0.0, (t - B['door']) / 0.5))
    room(cv, t, door_open=u)
    P = strain(t) if t < B['freeze'] else dict(brow=1.0, mouth='open', mouth_open=1.0, pupil=0.25, sweat=True, look=(-1.0, 0.0))
    bed(cv, t, shake=1.0 if t < B['freeze'] else 0.0, P=P)
    if u > 0:                                                                                                # mom in the doorway (silhouette)
        mascot(cv, 150, 1650, 0.9, long_hair=True, hair='#0A0A0A', hair_sh='#000000', skin='#14100C', skin_sh='#0A0806',
               shirt='#14100C', shirt_sh='#0A0806', pants='#14100C', pants_sh='#0A0806', shoe='#0A0806', mouth='o', brow=1.0, light_side=1, rim=LAMP, rim_a=0.8 * u)
    if t >= B['freeze']:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#FFFFFF', 0.06)))
        text(cv, 'YEP.', 820, 560, 120, '#FFFFFF')
    shade(cv, (540, 1000), 1200, 0.4)
    grain(cv, t)


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
