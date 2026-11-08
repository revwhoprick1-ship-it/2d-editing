#!/usr/bin/env python3
"""VIDEO_011 "Benched · Part 1" — real 2D animation (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_011/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video011 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
ARENA = '#FFE9C0'                       # warm arena light

TEAM = dict(shirt='#F07A1A', shirt_sh='#C85A0C', pants='#F07A1A', pants_sh='#C85A0C', shorts=True, sleeveless=True)
YOU = dict(TEAM, number=23)
YOU_TRYOUT = dict(shirt='#8A8A8A', shirt_sh='#6A6A6A', pants='#3A3A3A', pants_sh='#2A2A2A', shorts=True, sleeveless=True, number='00',
                  shoe='#7A5A3A', shoe_sh='#5A4028', belly=1.15)
TYLER = dict(TEAM, number=1, hair='#E0C080', hair_sh='#C0A060')
MATES = [dict(TEAM, number=n, hair=h, hair_sh=hs, skin=sk, skin_sh=sks) for n, h, hs, sk, sks in (
    (4, '#1A1A1A', '#0A0A0A', '#8E5A3C', '#6E432C'), (11, '#5A3A1A', '#3A2410', '#F2C29B', '#D99B76'),
    (32, '#2A1A10', '#1A100A', '#C98E66', '#A8704C'))]
COACH = dict(shirt='#4A4F58', shirt_sh='#363A42', pants='#2A2E36', pants_sh='#1E2228', shoe='#1A1A1A', shoe_sh='#111111', belly=1.35,
             hair='#6A6A6A', hair_sh='#4A4A4A', cap='#C85A0C', mustache='#5A5A5A', skin='#E3AE86', skin_sh='#C48E68')
JANITOR = dict(shirt='#5A6A5A', shirt_sh='#465446', pants='#3A443A', pants_sh='#2A322A', shoe='#1A1A1A', shoe_sh='#111111',
               hair='#BDBDBD', hair_sh='#9A9A9A', skin='#8E5A3C', skin_sh='#6E432C', mustache='#DADADA')


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


def flashback(t):
    return B['flash'] <= t < B['night']


def ball(cv, x, y, r):
    cv.drawCircle(x, y, r, paint('#E0701E'))
    cv.drawCircle(x, y, r, paint('#3A1E0A', style='stroke', width=max(1, r * 0.08)))
    cv.drawLine(x - r, y, x + r, y, paint('#3A1E0A', style='stroke', width=max(1, r * 0.07)))
    cv.drawArc(skia.Rect(x - r * 0.5, y - r, x + r * 0.5, y + r), 90, 180, False, paint('#3A1E0A', style='stroke', width=max(1, r * 0.07)))


def crowd(cv, t, y0=260, y1=1100, lit=0.5, signs=False, stand=0.0, phones=False):
    """Bleachers: rows of heads (simple dots + shoulders), bouncing when they chant."""
    cv.drawRect(skia.Rect(0, y0 - 60, W, y1), paint('#1A1614'))
    rows = 7
    for r in range(rows):
        y = y0 + r * (y1 - y0) / rows
        cv.drawRect(skia.Rect(0, y + 60, W, y + 70), paint(C('#2E2620', 0.9)))
        for k in range(16):
            x = (k + 0.5 * (r % 2)) * 72
            bob_ = -abs(math.sin(t * 6.3 + k * 0.7 + r)) * 18 * stand
            col = ['#C85A0C', '#2A2E36', '#8A6A4A', '#4A4A8A', '#6A8A3A', '#B03A3A'][(k * 3 + r) % 6]
            cv.drawCircle(x, y + 40 + bob_, 24, paint(C(col, 0.55 + 0.35 * lit)))
            cv.drawCircle(x, y + bob_, 17, paint(C(['#F2C29B', '#8E5A3C', '#C98E66', '#E3AE86'][(k + r) % 4], 0.5 + 0.4 * lit)))
            if phones and (k * 7 + r) % 5 == 0:
                cv.drawRect(skia.Rect(x - 8, y - 40 + bob_, x + 8, y - 14 + bob_), paint('#BFE0FF'))
                glow(cv, (x, y - 27 + bob_), 40, '#BFE0FF', 0.3)
            if signs and (k * 5 + r) % 7 == 0 and r < 5:
                cv.save(); cv.rotate(6 * math.sin(t * 6 + k), x, y - 50)
                cv.drawRect(skia.Rect(x - 50, y - 100 + bob_, x + 50, y - 30 + bob_), paint('#F4F0E0'))
                text(cv, '23', x, y - 44 + bob_, 56, '#C83030')
                cv.restore()


def court(cv, y0=1100, lights=1.0):
    cv.drawRect(skia.Rect(0, y0, W, H), paint('#B07A44', shader=lin((0, y0), (0, H), [C('#8A5A30'), C('#C28A50')])))
    for k in range(12):
        cv.drawLine(k * 110 - 200, y0, k * 140 - 500, H, paint(C('#9A6A3A', 0.6), style='stroke', width=3))
    cv.drawLine(0, y0 + 260, W, y0 + 230, paint(C('#FFFFFF', 0.8), style='stroke', width=8))


def arena(cv, t, **kw):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0E0C0A'))
    crowd(cv, t, **kw)
    court(cv)
    for x in (200, 880):
        cv.drawPath(poly([(x - 30, 0), (x + 30, 0), (x + 260, 1500), (x - 260, 1500)]), paint(C(ARENA, 0.06), blur=20))
    glow(cv, (540, 1250), 800, ARENA, 0.2)


# ===================================================================== shots
def shot_SCORE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A0908'))
    crowd(cv, t, 1300, 1920, lit=0.25)
    cv.drawRect(skia.Rect(40, 420, 1040, 1180), paint('#0E0B0A'))
    cv.drawRect(skia.Rect(40, 420, 1040, 1180), paint('#3A342E', style='stroke', width=14))
    text(cv, 'HOME', 270, 540, 70, '#FFB23A')
    text(cv, 'AWAY', 810, 540, 70, '#FFB23A')
    text(cv, '58', 270, 760, 230, '#FF4A36')
    text(cv, '60', 810, 760, 230, '#FF4A36')
    blinkc = (int(t * 2) % 2 == 0) or t < 0.6
    text(cv, '0:03', 540, 1000, 200, '#FF4A36' if blinkc else '#5A1A12')
    text(cv, 'Q4', 540, 1120, 60, '#FFB23A')
    text(cv, 'BONUS', 180, 1120, 46, '#FFB23A', alpha=0.7)
    for i in range(0, 760, 7):
        cv.drawLine(40, 420 + i, 1040, 420 + i, paint(C('#000000', 0.25), style='stroke', width=2))
    glow(cv, (540, 800), 700, '#FF4A36', 0.15)
    shade(cv, (540, 800), 1150, 0.55)


def shot_BENCH(cv, t):
    arena(cv, t, lit=0.5)
    for k, m in enumerate(MATES):                                                       # teammates at the court edge
        mascot(cv, 520 + k * 190, 1420, 0.48, view='back', light_side=1, rim=ARENA, rim_a=0.4, **m)
    cv.drawRect(skia.Rect(0, 1560, W, 1620), paint('#2A2E36'))                         # the bench
    cv.drawRect(skia.Rect(0, 1620, W, 1920), paint(C('#000000', 0.55)))
    mascot(cv, 230, 2050, 0.7, legs=False, look=(0.6, -0.1), brow=-0.1, lids=0.25, head_turn=0.3, light_side=1, rim=ARENA, rim_a=0.6, **YOU)
    cv.drawPath(blob([(110, 1500), (230, 1540), (350, 1500), (340, 1600), (230, 1580), (120, 1600)]), paint('#E8E4DA'))     # towel on the shoulders
    for k in range(4):                                                                  # crate of water bottles
        cv.drawRect(skia.Rect(400 + k * 40, 1500, 430 + k * 40, 1600), paint('#7FB8E0'))
    cv.drawRect(skia.Rect(390, 1550, 560, 1640), paint('#C83030'))
    shade(cv, (600, 1200), 1250, 0.55)


def shot_FACE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120F0C'))
    crowd(cv, t, 200, 1100, lit=0.25)
    glow(cv, (1000, 700), 900, ARENA, 0.25)
    mascot(cv, 540, 2700, 1.95, look=(0.0, 0.0), brow=-0.25, lids=0.22, mouth='flat', light_side=1, rim=ARENA, rim_a=0.7, **YOU)
    shade(cv, (540, 950), 1100, 0.6)


def gym_day(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A3632'))
    for k in range(6):
        cv.drawRect(skia.Rect(0, 200 + k * 80, W, 230 + k * 80), paint(C('#2E2A26', 0.8)))
    text(cv, 'TRYOUTS', 540, 300, 90, '#E8E0D0', alpha=0.6)
    court(cv, 1150)
    glow(cv, (540, 0), 1200, '#FFFFFF', 0.15)


def shot_TRYOUT(cv, t):
    gym_day(cv, t)
    laughing = t >= B['laugh']
    mascot(cv, 540, 1430, 0.42, light_side=1, mouth='grin' if laughing else 'flat', brow=-0.2, arm_r=(40, -60), **COACH)   # coach, clipboard
    cv.drawRect(skia.Rect(600, 1060, 660, 1140), paint('#C9C2AE'))
    for k, m in enumerate([TYLER] + MATES):
        x = 640 + k * 130
        mascot(cv, x, 1700 - (k % 2) * 40, 0.5, light_side=-1, mouth='grin' if laughing or k == 0 else 'smile', brow=-0.3,
               look=(-0.8, 0.0), head_tilt=8 * math.sin(t * 9 + k) if laughing else 0, **m)
    mascot(cv, 230, 1830, 0.62, look=(0.6, 0.1), brow=0.8 if laughing else 0.2, mouth='frown' if laughing else 'flat', light_side=1, rim='#FFFFFF',
           rim_a=0.3, **YOU_TRYOUT)
    shade(cv, (540, 1100), 1250, 0.45)


def shot_TYLER(cv, t):
    past = flashback(t)
    if past:
        gym_day(cv, t)
    else:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#120F0C'))
        crowd(cv, t, 200, 1100, lit=0.3)
    m = talk(t, 'T1', 'T2')
    mascot(cv, 540, 2700, 1.95, look=(0.5, 0.0), head_turn=0.25, brow=-0.5, lids=0.2, mouth='grin' if m == 0 else 'open', mouth_open=m,
           sweat=not past, light_side=-1, rim=ARENA, rim_a=0.5, **TYLER)
    shade(cv, (540, 950), 1100, 0.5)


def shot_COACH(cv, t):
    past = flashback(t)
    if past:
        gym_day(cv, t)
    else:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#120F0C'))
        crowd(cv, t, 200, 1100, lit=0.5, stand=1.0, signs=True)
    m = talk(t, 'C1', 'C2')
    turn = 0.0 if past else keys(t, [(B['turn'], 0.9), (B['turn'] + 0.9, 0.9), (B['turn'] + 1.6, 0.0)])
    point = (not past) and t >= B['c2']
    mascot(cv, 540, 2700, 1.95, look=(0.9 * turn, 0.0), head_turn=turn, brow=-0.6, lids=0.15, mouth='frown' if m == 0 else 'open', mouth_open=m,
           arm_r=(95, 0) if point else (3, 0), light_side=-1, rim=ARENA, rim_a=0.5, **COACH)
    shade(cv, (540, 950), 1100, 0.5)


def shot_NIGHT(cv, t):
    """The empty gym at night: one light over the hoop; you shoot, again and again. A counter climbs to 500."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#08090B'))
    court(cv, 1300)
    cv.drawRect(skia.Rect(0, 1300, W, H), paint(C('#000000', 0.65)))
    cv.drawPath(poly([(840, 0), (900, 0), (1150, 1700), (560, 1700)]), paint(C(ARENA, 0.10), blur=25))
    glow(cv, (870, 1500), 500, ARENA, 0.25)
    cv.drawRect(skia.Rect(960, 560, 980, 1500), paint('#3A3E46'))                        # hoop
    cv.drawRect(skia.Rect(860, 520, 1010, 640), paint('#E8E8E8', style='stroke', width=8))
    cv.drawLine(800, 700, 900, 700, paint('#E0501E', style='stroke', width=10))
    for k in range(5):
        cv.drawLine(805 + k * 22, 705, 815 + k * 18, 790, paint(C('#FFFFFF', 0.7), style='stroke', width=3))
    period = 1.6 if t < B['shots'] else 0.75
    t0 = B['night'] if t < B['shots'] else B['shots']
    u = ((t - t0) % period) / period
    jump = math.sin(math.pi * min(1.0, max(0.0, (u - 0.15) / 0.4))) * 120
    up = u > 0.15
    mascot(cv, 340, 1560 - jump, 0.55, view='side', face=1, crouch=0.0, arm_r=(150, -15) if up else (95, 60), arm_l=(140, -10) if up else (85, 70),
           light_side=1, rim=ARENA, rim_a=0.6, brow=-0.2, lids=0.3 if t >= B['shots'] + 2.0 else 0.0, **YOU)
    if u > 0.35:                                                                           # the ball's arc -> swish
        v = min(1.0, (u - 0.35) / 0.5)
        bx = 400 + (850 - 400) * v
        by = (1560 - 120 - 560) * (1 - v) + 690 * v - 520 * math.sin(math.pi * v)
        ball(cv, bx, by, 34)
    else:
        ball(cv, 470, 1560 - jump - 600, 34)
    n = int((t - B['night']) / 1.6) + 1 if t < B['shots'] else min(500, 3 + int(((t - B['shots']) / max(0.1, B['janitor'] - B['shots'])) ** 1.5 * 497))
    text(cv, f'SHOT {n}', 300, 520, 90, '#FFB23A', alpha=0.85)
    shade(cv, (700, 1100), 1150, 0.55)


def shot_JANITOR(cv, t):
    shot_NIGHT(cv, t)
    cv.drawRect(skia.Rect(0, 0, 330, H), paint('#05060A'))                                # doorway
    mascot(cv, 120, 2500, 1.2, view='back', light_side=1, rim=ARENA, rim_a=0.4, **JANITOR)
    if t >= B['record'] - 0.5:                                                            # phone raised, recording
        cv.drawRect(skia.Rect(150, 760, 330, 1080), paint('#101215'))
        cv.drawRect(skia.Rect(160, 772, 320, 1068), paint('#1E2833'))
        ball(cv, 260, 880, 12)
        if int(t * 2) % 2 == 0:
            cv.drawCircle(185, 800, 9, paint('#FF3B2F'))
        glow(cv, (240, 920), 260, '#BFE0FF', 0.3)
    if B['record'] - 0.2 <= t:
        text(cv, '20 IN A ROW', 700, 400, 80, '#FFFFFF', alpha=0.9)


def shot_VIEWS(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0E0C0A'))
    crowd(cv, t, 200, 1900, lit=0.3, phones=True)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.45)))
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(160, 260, 920, 1640), 60, 60)), paint('#101215'))
    cv.drawRect(skia.Rect(190, 330, 890, 1570), paint('#F4F4F4'))
    cv.drawRect(skia.Rect(190, 330, 890, 720), paint('#08090B'))                           # the video
    glow(cv, (700, 500), 300, ARENA, 0.3)
    mascot(cv, 380, 700, 0.3, view='side', face=1, arm_r=(140, 25), arm_l=(128, 35), **YOU)
    ball(cv, 640, 420, 16)
    text(cv, 'kid hits 20 threes in a row at 11pm', 220, 790, 40, '#1A1A1A', align='left')
    v = int(2104388 * ease((t - B['views']) / 2.2))
    text(cv, f'{v:,} views', 220, 850, 40, '#E62828', align='left')
    for k, (u, c_) in enumerate((('@hoopsdaily', 'WHO IS #23??'), ('@jaylen_04', 'coach is blind fr'), ('@mrs.hart', 'START HIM.'),
                                 ('@west_high', 'he fills the water bottles??'))):
        if t >= B['views'] + 0.6 + k * 0.4:
            y = 940 + k * 150
            cv.drawCircle(250, y + 40, 32, paint(['#6AAAC8', '#C86A6A', '#6AC88A', '#C8A86A'][k]))
            text(cv, u, 300, y + 30, 32, '#6A6A6A', align='left', bold=False)
            text(cv, c_, 300, y + 80, 44, '#1A1A1A', align='left')
    shade(cv, (540, 950), 1150, 0.4)


def shot_SIDELINE(cv, t):
    """Coach, oblivious, reading his clipboard; behind him, the crowd watching the video on their phones."""
    arena(cv, t, lit=0.4, phones=True)
    mascot(cv, 540, 2200, 1.05, look=(0.0, 0.9), head_tilt=6, brow=-0.4, mouth='frown', arm_r=(40, -70), arm_l=(40, -70), light_side=-1,
           rim=ARENA, rim_a=0.5, **COACH)
    cv.drawRect(skia.Rect(440, 1500, 640, 1650), paint('#C9C2AE'))
    shade(cv, (540, 1100), 1200, 0.5)


def shot_CROWD(cv, t):
    """Tyler fouls out (whistle, towel over his head); the crowd stands and chants: 23."""
    stand = keys(t, [(B['fouls'], 0.0), (B['number'], 1.0)])
    arena(cv, t, lit=0.6, signs=t >= B['number'] - 0.3, stand=stand)
    mascot(cv, 780, 1900, 0.75, view='back', light_side=1, rim=ARENA, rim_a=0.4, head_tilt=-10, **TYLER)    # walking off
    if t >= B['fouls']:
        cv.drawPath(blob([(660, 1150), (780, 1110), (900, 1150), (880, 1260), (680, 1260)]), paint('#E8E4DA'))
        text(cv, 'FOULED OUT', 780, 1000, 60, '#FF4A36')
    shade(cv, (540, 1100), 1250, 0.45)


def shot_WALK(cv, t):
    """You stand up, drop the towel, and walk onto the court. A spotlight finds you. The ball comes to you."""
    arena(cv, t, lit=0.7, signs=True, stand=1.0)
    u = t - B['walk']
    x = 160 + min(1.0, u / 2.2) * 420
    ph = ((u * 1.1) % 1) if u < 2.2 else None
    cv.drawPath(poly([(x - 30, 0), (x + 30, 0), (x + 260, 1800), (x - 260, 1800)]), paint(C(ARENA, 0.12), blur=20))
    glow(cv, (x, 1750), 400, ARENA, 0.3)
    mascot(cv, x, 1780, 0.75, view='side', face=1, walk=ph, light_side=1, rim=ARENA, rim_a=0.8, brow=-0.3, lids=0.15,
           arm_r=(-70, -40) if u > 2.6 else (3, 0), **YOU)
    if u > 2.2:                                                                              # the inbound pass
        v = min(1.0, (u - 2.2) / 0.4)
        ball(cv, 1100 - (1100 - x - 120) * v, 1100 - 140 * math.sin(math.pi * v) + 120 * v, 30)
    shade(cv, (x, 1300), 1150, 0.5)


SHOTS = {'SCORE': shot_SCORE, 'BENCH': shot_BENCH, 'FACE': shot_FACE, 'TRYOUT': shot_TRYOUT, 'TYLER': shot_TYLER, 'COACH': shot_COACH,
         'NIGHT': shot_NIGHT, 'JANITOR': shot_JANITOR, 'VIEWS': shot_VIEWS, 'SIDELINE': shot_SIDELINE, 'CROWD': shot_CROWD, 'WALK': shot_WALK}


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
