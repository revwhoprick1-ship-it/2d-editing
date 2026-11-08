#!/usr/bin/env python3
"""VIDEO_013 "Benched · Part 2" — real 2D (2dEDIT). Re-uses Part 1's characters and recap shots from VIDEO_011.

    python3 VIDEOS/VIDEO_013/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
"""
import argparse
import importlib.util
import math
import os
import sys
from multiprocessing import Pool

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'twod'))
sys.path.insert(0, os.path.join(STUDIO, 'VIDEOS', 'VIDEO_011'))
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video013 as E  # noqa

_spec = importlib.util.spec_from_file_location('anim11', os.path.join(STUDIO, 'VIDEOS', 'VIDEO_011', 'anim2d.py'))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
B11 = A.B

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
ARENA = A.ARENA
OPP = dict(shirt='#2A4A8A', shirt_sh='#1E3666', pants='#2A4A8A', pants_sh='#1E3666', shorts=True, sleeveless=True, number=10,
           hair='#1A1A1A', hair_sh='#0A0A0A', skin='#8E5A3C', skin_sh='#6E432C')
SCOUT = dict(shirt='#7A1E2A', shirt_sh='#5A1620', pants='#2A2E36', pants_sh='#1E2228', hair='#BDBDBD', hair_sh='#9A9A9A', cap='#7A1E2A',
             belly=1.15, glasses='#22262C')


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


# ---------------------------------------------------------------- recap shots: Part 1 frames, re-timed
def recap(fn, t11_start, seg_start):
    return lambda cv, t: fn(cv, t11_start + (t - seg_start))


def shot_R_BENCH(cv, t):
    A.shot_BENCH(cv, B11['bench'] + 0.5 + (t - B['recap']))


def shot_R_TRYOUT(cv, t):
    A.shot_TRYOUT(cv, B11['laugh'] + 0.3 + (t - B['mates']))


def shot_R_NIGHT(cv, t):
    A.shot_NIGHT(cv, B11['shots'] + 1.0 + (t - B['night']))


def shot_R_VIEWS(cv, t):
    A.shot_VIEWS(cv, B11['views'] + 1.8 + (t - B['viral']))


def shot_R_CROWD(cv, t):
    A.shot_CROWD(cv, B11['number'] + 0.5 + (t - B['chant']))


def shot_R_COACH(cv, t):
    A.shot_COACH(cv, B11['c2'] + 0.1 + (t - B['until']))


def shot_R_COACHF(cv, t):
    """Coach, frozen, watching the ball (present day: mouth shut)."""
    A.shot_COACH(cv, B11['turn'] + 1.7)


def shot_R_TYLERF(cv, t):
    A.shot_TYLER(cv, B11['t2'] + 1.2)


# ---------------------------------------------------------------- the play
def hoop(cv, x, y, s=1.0, net_swish=0.0):
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    cv.drawRect(skia.Rect(60, -200, 80, 900), paint('#3A3E46'))
    cv.drawRect(skia.Rect(-40, -260, 110, -130), paint('#E8E8E8', style='stroke', width=8))
    cv.drawLine(-100, -100, 40, -100, paint('#E0501E', style='stroke', width=10))
    sway = 10 * math.sin(net_swish * 20) * max(0.0, 1 - net_swish)
    for k in range(6):
        cv.drawLine(-95 + k * 26, -95, -88 + k * 22 + sway, -10, paint(C('#FFFFFF', 0.75), style='stroke', width=3))
    cv.restore()


def shot_AIR(cv, t):
    """Frame 0: the release — he's in the air, the ball at the top of its arc, the defender's hand an inch too late."""
    A.arena(cv, t, lit=0.7, signs=True, stand=0.6)
    cv.drawPath(poly([(330, 0), (390, 0), (620, 1800), (100, 1800)]), paint(C(ARENA, 0.12), blur=20))
    mascot(cv, 260, 1460, 0.7, view='side', face=1, arm_r=(150, -15), arm_l=(140, -10), light_side=1, rim=ARENA, rim_a=0.8, brow=-0.3,
           look=(0.5, -0.6), **A.YOU)
    mascot(cv, 700, 1760, 0.72, view='side', face=-1, arm_r=(150, -10), arm_l=(30, 20), light_side=-1, rim=ARENA, rim_a=0.5,
           brow=-0.6, mouth='o', **OPP)
    A.ball(cv, 640 + 6 * math.sin(t * 2), 520, 44)
    hoop(cv, 900, 900, 0.9)
    shade(cv, (540, 1000), 1250, 0.45)


def shot_PLAY(cv, t):
    """Inbound, dribble, step back (side view, the defender pressing)."""
    A.arena(cv, t, lit=0.7, signs=True, stand=0.8)
    u = t - B['ball']
    step = t >= B['step']
    youx = 300 - (90 * ease((t - B['step']) / 0.25) if step else 0)
    dribble = abs(math.sin(t * 7)) if t < B['step'] else 0
    if t < B['ball'] + 0.5:                                                                     # inbound pass
        v = min(1.0, u / 0.5)
        A.ball(cv, 1100 - (1100 - youx - 90) * v, 900 + 400 * v - 120 * math.sin(math.pi * v), 30)
    else:
        A.ball(cv, youx + 110, 1500 - 300 * (1 - dribble) if not (t >= B['go'] - 0.4) else 1000, 30)
    shooting = t >= B['go'] - 0.4
    mascot(cv, youx, 1780, 0.75, view='side', face=1, walk=None, arm_r=(150, -15) if shooting else (40, 40), arm_l=(140, -10) if shooting else (20, 30),
           light_side=1, rim=ARENA, rim_a=0.7, brow=-0.4, lids=0.15, **A.YOU)
    mascot(cv, 800 - (40 if step else 0), 1800, 0.78, view='side', face=-1, arm_r=(110, 0) if shooting else (60, 20), arm_l=(70, 10),
           light_side=-1, rim=ARENA, rim_a=0.5, brow=-0.6, mouth='smirk' if t < B['step'] else 'o', **OPP)
    shade(cv, (540, 1200), 1250, 0.45)


def shot_DEFENDER(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120F0C'))
    A.crowd(cv, t, 200, 1100, lit=0.4, stand=0.6, signs=True)
    m = talk(t, 'D1')
    mascot(cv, 540, 2700, 1.95, look=(-0.5, 0.0), head_turn=-0.25, brow=-0.6, lids=0.2, mouth='smirk' if m == 0 else 'open', mouth_open=m,
           sweat=True, light_side=-1, rim=ARENA, rim_a=0.5, **OPP)
    shade(cv, (540, 950), 1100, 0.5)


def shot_SLOW(cv, t):
    """Slow motion: the ball's long arc across a hushed gym; the clock hits 0:00 while it's still in the air."""
    A.arena(cv, t, lit=0.4, signs=True, stand=0.0)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.25)))
    u = min(1.0, max(0.0, (t - B['go']) / max(0.5, B['slow_end'] - B['go'])))
    bx = 150 + (860 - 150) * u
    by = 1400 * (1 - u) + 640 * u - 900 * math.sin(math.pi * u)
    for k in range(6):                                                                          # motion trail
        uu = max(0.0, u - k * 0.012)
        tx = 150 + (860 - 150) * uu
        ty = 1400 * (1 - uu) + 640 * uu - 900 * math.sin(math.pi * uu)
        cv.drawCircle(tx, ty, 40 - k * 4, paint(C('#E0701E', 0.15)))
    A.ball(cv, bx, by, 44)
    hoop(cv, 900, 900, 1.0)
    text(cv, '0:00' if t >= B['go'] + 0.4 else '0:01', 540, 360, 110, '#FF4A36', alpha=0.85)
    shade(cv, (540, 900), 1100, 0.5)


def shot_RIM(cv, t):
    """Close on the rim: it hits... bounces up... rolls... drops in. Swish."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0E0C0A'))
    A.crowd(cv, t, 1200, 1920, lit=0.3, stand=1.0 if t >= B['drops'] + 0.15 else 0.0, signs=t >= B['drops'] + 0.15)
    cv.drawRect(skia.Rect(160, 260, 1000, 900), paint('#E8E8E8', style='stroke', width=16))       # backboard
    cv.drawRect(skia.Rect(450, 560, 710, 740), paint('#E8E8E8', style='stroke', width=10))
    cv.drawLine(300, 900, 780, 900, paint('#E0501E', style='stroke', width=22))
    u = t - B['slow_end']
    t_in = B['drops'] + 0.15
    if t < B['clang']:
        bx, by = 900 - 300 * min(1.0, u / 0.6), 640 + 220 * min(1.0, u / 0.6)
    elif t < t_in:                                                                               # bounce up, roll on the rim
        v = (t - B['clang']) / max(0.1, t_in - B['clang'])
        bx = 600 - 60 * v + 20 * math.sin(v * 9)
        by = 840 - 260 * math.sin(math.pi * min(1.0, v * 1.4)) * (1 - v * 0.6)
    else:
        v = min(1.0, (t - t_in) / 0.35)
        bx, by = 540, 860 + 300 * v
    sw = (t - t_in) if t >= t_in else 0.0
    for k in range(9):
        sway = 14 * math.sin(sw * 18 + k) * max(0.0, 1 - sw)
        cv.drawLine(310 + k * 58, 905, 340 + k * 50 + sway, 1150, paint(C('#FFFFFF', 0.8), style='stroke', width=5))
    A.ball(cv, bx, by, 80)
    if t >= t_in:
        glow(cv, (540, 1000), 900, ARENA, 0.25 * max(0.0, 1 - sw))
    shade(cv, (540, 900), 1100, 0.45)


def shot_CELEB(cv, t):
    """The gym explodes: scoreboard FINAL 61-60, confetti, everyone on the court; you lifted up."""
    A.arena(cv, t, lit=0.9, signs=True, stand=1.0)
    cv.drawRect(skia.Rect(240, 280, 840, 640), paint('#0E0B0A'))
    cv.drawRect(skia.Rect(240, 280, 840, 640), paint('#3A342E', style='stroke', width=10))
    text(cv, 'HOME 61', 540, 410, 100, '#FF4A36')
    text(cv, 'AWAY 60', 540, 520, 80, '#FFB23A')
    text(cv, 'FINAL', 540, 610, 50, '#FFB23A')
    for k, m in enumerate(A.MATES):
        mascot(cv, 220 + k * 320, 1900, 0.7, light_side=1, rim=ARENA, rim_a=0.4, mouth='grin', brow=0.6, arm_r=(160, 0), arm_l=(160, 0),
               head_tilt=8 * math.sin(t * 8 + k), **m)
    lift = 60 * abs(math.sin(t * 3))
    mascot(cv, 540, 1720 - lift, 0.8, light_side=1, rim=ARENA, rim_a=0.7, mouth='grin', brow=0.5, arm_r=(165, 0), arm_l=(165, 0), **A.YOU)
    for k in range(70):                                                                          # confetti
        x = (k * 157 + t * 60 * (1 + k % 3)) % W
        y = (k * 211 + t * 300 * (1 + k % 4) * 0.5) % H
        cv.save(); cv.rotate(t * 200 + k * 30, x, y)
        cv.drawRect(skia.Rect(x - 10, y - 5, x + 10, y + 5), paint(['#F07A1A', '#FFFFFF', '#FFB23A', '#C83030'][k % 4]))
        cv.restore()
    shade(cv, (540, 1100), 1300, 0.35)


def shot_JANITOR(cv, t):
    """The janitor at the side door, phone still up, wiping his eyes."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120F0C'))
    A.crowd(cv, t, 200, 1100, lit=0.6, stand=1.0, signs=True)
    mascot(cv, 540, 2700, 1.95, look=(0.4, -0.2), brow=1.0, lids=0.35, mouth='smile', sweat=True, light_side=1, rim=ARENA, rim_a=0.6,
           arm_r=(150, -40), **A.JANITOR)
    for side in (-1, 1):                                                                          # tears
        y = 1320 + ((t * 300) % 200)
        cv.drawPath(blob([(540 + side * 160, y), (552 + side * 160, y + 30), (540 + side * 160, y + 44), (528 + side * 160, y + 30)]), paint('#BFE3FF'))
    shade(cv, (540, 950), 1100, 0.5)


def shot_COACH2(cv, t):
    """Coach walks over, holding out a water bottle: 'Kid... I think this one's yours.'"""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120F0C'))
    A.crowd(cv, t, 200, 1100, lit=0.6, stand=0.6, signs=True)
    m = talk(t, 'D2')
    mascot(cv, 470, 2700, 1.95, look=(0.6, 0.1), brow=0.6, lids=0.25, mouth='smile' if m == 0 else 'open', mouth_open=m * 0.7,
           arm_r=(80, -20), light_side=-1, rim=ARENA, rim_a=0.5, **A.COACH)
    bx = 930 - 40 * ease((t - B['d2']) / 0.6)
    cv.drawRect(skia.Rect(bx - 50, 1180, bx + 50, 1420), paint('#7FB8E0'))
    cv.drawRect(skia.Rect(bx - 30, 1140, bx + 30, 1180), paint('#C83030'))
    shade(cv, (540, 950), 1100, 0.5)


def shot_SCOUT(cv, t):
    """In the stands: a man in a college jacket, phone at his ear, eyes on #23."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120F0C'))
    A.crowd(cv, t, 150, 1920, lit=0.4, stand=1.0, signs=False)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.45)))
    mascot(cv, 540, 2500, 1.5, look=(0.7, 0.0), brow=-0.3, lids=0.2, mouth='smirk', arm_r=(150, -80), light_side=1, rim=ARENA, rim_a=0.6, **SCOUT)
    cv.drawRect(skia.Rect(690, 940, 760, 1080), paint('#101215'))
    text(cv, 'STATE U', 540, 1720, 70, '#F4E9D0')
    text(cv, 'BASKETBALL', 540, 1790, 46, '#F4E9D0')
    shade(cv, (540, 1000), 1100, 0.45)


SHOTS = {'AIR': shot_AIR, 'R_BENCH': shot_R_BENCH, 'R_TRYOUT': shot_R_TRYOUT, 'R_NIGHT': shot_R_NIGHT, 'R_VIEWS': shot_R_VIEWS,
         'R_CROWD': shot_R_CROWD, 'R_COACH': shot_R_COACH, 'R_COACHF': shot_R_COACHF, 'R_TYLERF': shot_R_TYLERF, 'PLAY': shot_PLAY,
         'DEFENDER': shot_DEFENDER, 'SLOW': shot_SLOW, 'RIM': shot_RIM, 'CELEB': shot_CELEB, 'JANITOR': shot_JANITOR,
         'COACH2': shot_COACH2, 'SCOUT': shot_SCOUT}


def needed():
    out = []
    for sgm in E.SEGMENTS:
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
            if i % 300 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
