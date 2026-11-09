#!/usr/bin/env python3
"""VIDEO_015 "Kessrah · Part 1" — real 2D psychological horror (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_015/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, kessrah, lin, mascot, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video015 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
FLUOR = '#E4ECF2'
CANDLE = '#FFB860'

THEO = dict(hair='#1A1A1A', hair_sh='#0A0A0A', shirt='#2E6A4A', shirt_sh='#22503A', skin='#8E5A3C', skin_sh='#6E432C')
HART = dict(long_hair=True, hair='#8A4A2A', hair_sh='#6A361E', shirt='#C9C2AE', shirt_sh='#A8A08C', glasses='#5A3A2A', skin='#F2C9A8',
            skin_sh='#D4A886')
KIDS = [dict(shirt=c1, shirt_sh=c2, hair=h1, hair_sh=h2, skin=sk, skin_sh=sks, long_hair=lh) for c1, c2, h1, h2, sk, sks, lh in (
    ('#7A4FA0', '#5C3A7A', '#2A1A10', '#1A100A', '#C98E66', '#A8704C', True), ('#2E8A6A', '#22684F', '#D9B06A', '#B38C4E', '#F2C29B', '#D99B76', False),
    ('#B03A3A', '#862C2C', '#4A2A1A', '#2E1A10', '#8E5A3C', '#6E432C', False), ('#3A6EB0', '#2C5486', '#1A1A1A', '#0A0A0A', '#F2C29B', '#D99B76', True),
    ('#C9A030', '#9E7C22', '#8A4A2A', '#6A361E', '#F5D0B0', '#D9AE8C', False), ('#556070', '#3E4652', '#C26A2A', '#9A521E', '#F2C29B', '#D99B76', True),
    ('#A0507A', '#7A3C5C', '#3A2A1A', '#24180E', '#A8704C', '#8A5A3A', False), ('#6A8A3A', '#506A2A', '#E0C080', '#C0A060', '#F5D0B0', '#D9AE8C', True))]


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


# ---------------------------------------------------------------- the classroom
def classroom(cv, t, lights=1.0, cold=False):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1C2228'))
    cv.drawRect(skia.Rect(0, 0, W, 1200), paint('#4A5258', shader=lin((0, 0), (0, 1200), [C('#3A4248'), C('#556066')])))
    for x in (180, 540, 900):
        a, b = (x - 150, 60), (x + 150, 90)
        cv.drawRect(skia.Rect(*a, *b), paint(C(FLUOR, 0.3 + 0.7 * lights)))
    cv.drawRect(skia.Rect(0, 1200, W, H), paint('#3A3632', shader=lin((0, 1200), (0, H), [C('#34302C'), C('#46403A')])))
    glow(cv, (540, 100), 1200, FLUOR, 0.18 * lights)
    if cold:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#4A6A8A', 0.12)))


def desk_row(cv, y, s):
    cv.drawRect(skia.Rect(0, y, W, y + 26 * s), paint('#B08A5A'))
    cv.drawRect(skia.Rect(0, y + 26 * s, W, y + 60 * s), paint('#8A6A42'))


def shot_STARE(cv, t):
    """The whole class turned round in their seats, staring at you with one smile. You in the middle, terrified.
    After the rub (t >= empty), this shot isn't used; before the ritual it's the hook; after the blink it's JS1 and after."""
    classroom(cv, t)
    staring = t < B['ritual'] or t >= B['blink1'] + 0.2
    rows = [(1000, 0.42, [100, 300, 780, 980]), (1240, 0.55, [120, 380, 700, 960]), (1520, 0.72, [80, 1000])]
    k = 0
    for y, s_, xs in rows:
        for x in xs:
            kid = KIDS[k % len(KIDS)]
            look_x = (540 - x) / 540
            if staring:
                pose = dict(look=(look_x * 0.9, 0.1), head_turn=look_x * 0.5, mouth='wide', brow=-0.2, pupil=0.55, lids=0.0,
                            head_tilt=6 * math.sin(k * 1.7))
            else:
                pose = dict(look=(0.0, -0.2), mouth='flat', brow=0.0, lids=0.15)
            mascot(cv, x, y + 520 * s_, s_, legs=False, light_side=1, rim=FLUOR, rim_a=0.2, **dict(kid, **pose))
            k += 1
        desk_row(cv, y + 330 * s_, s_)
    mascot(cv, 540, 1240 + 520 * 0.6, 0.6, legs=False, look=(0.0, 0.0), brow=1.0, mouth='o', pupil=0.55, sweat=True, light_side=1, rim=FLUOR,
           rim_a=0.4)
    desk_row(cv, 1240 + 330 * 0.6, 0.6)
    shade(cv, (540, 1100), 1250, 0.5)


def shot_EMPTY(cv, t):
    """The same classroom, empty. Backpacks still on the chairs. One light buzzing."""
    lt = flicker(t, 6, 6.0, 0.35)
    classroom(cv, t, lights=lt, cold=True)
    for y, s_ in ((1000, 0.42), (1240, 0.55), (1520, 0.72)):
        for x in (100, 300, 780, 980):
            cv.drawPath(blob([(x - 60 * s_, y + 200 * s_), (x + 60 * s_, y + 200 * s_), (x + 70 * s_, y + 330 * s_), (x - 70 * s_, y + 330 * s_)]),
                        paint('#2A3A4A'))
        desk_row(cv, y + 330 * s_, s_)
    shade(cv, (540, 1100), 1250, 0.6)


def shot_CLASS(cv, t):
    """Normal first period: Ms. Hart at the board, the class facing her (backs to us), you near the back."""
    classroom(cv, t)
    cv.drawRect(skia.Rect(160, 300, 920, 760), paint('#2A4A3A'))
    text(cv, 'ATTENDANCE', 540, 420, 60, '#D8D8D0', alpha=0.7, bold=False)
    mascot(cv, 540, 1250, 0.55, light_side=1, rim=FLUOR, rim_a=0.3, mouth='open' if talk(t, 'H01') else 'smile', mouth_open=talk(t, 'H01') * 0.6,
           look=(0.0, 0.3), **HART)
    k = 0
    for y, s_, xs in ((1300, 0.5, [120, 380, 700, 960]), (1600, 0.7, [100, 1000])):
        for x in xs:
            mascot(cv, x, y + 520 * s_, s_, view='back', legs=False, light_side=1, rim=FLUOR, rim_a=0.2, **KIDS[k % len(KIDS)])
            k += 1
    shade(cv, (540, 1000), 1250, 0.5)


def shot_HART(cv, t):
    classroom(cv, t)
    cv.drawRect(skia.Rect(0, 300, W, 900), paint('#2A4A3A'))
    m = talk(t, 'H01', 'H02')
    wrong = t >= B['h02'] - 0.1
    mascot(cv, 540, 2700, 1.95, light_side=1, rim=FLUOR, rim_a=0.4, look=(0.0, 0.0), brow=-0.1, pupil=0.6 if wrong else 0.9,
           mouth=('wide' if m == 0 else 'open') if wrong else ('smile' if m == 0 else 'open'), mouth_open=m * 0.6,
           head_tilt=10 if wrong else 0, void_eyes=wrong and int(t * 3) % 4 == 0, **HART)
    shade(cv, (540, 950), 1100, 0.55)


def shot_YOU(cv, t):
    """Your face, close — every emotion of the night. Background follows where you are."""
    if t < B['class_']:
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A4450'))
        for x in range(0, W, 110):
            cv.drawRect(skia.Rect(x + 6, 300, x + 104, 1300), paint('#4E6070'))
        glow(cv, (540, 0), 1100, FLUOR, 0.2)
        cold = False
    else:
        cold = t >= B['empty']
        classroom(cv, t, lights=flicker(t, 6, 6.0, 0.35) if cold else 1.0, cold=cold)
    m = talk(t, 'Y06', 'Y07', 'Y08', 'Y09', 'Y10', 'Y11')
    crying = t >= B['y08']
    begging = t >= B['y11']
    shake = 6 * math.sin(t * 47) if crying else 0
    mascot(cv, 540 + shake, 2700, 1.95, light_side=1, rim=FLUOR, rim_a=0.5, look=(0.0, 0.0) if not cold else (0.4 * math.sin(t * 1.7), 0.0),
           brow=1.0 if t >= B['y07'] else 0.5, mouth='open' if m > 0 else ('frown' if crying else 'o'), mouth_open=max(m, 0.15),
           pupil=0.5 if crying else 0.75, sweat=True, lids=0.3 if begging else 0.0)
    if crying:                                                                                  # tears
        for side in (-1, 1):
            y = 1330 + ((t * 260 + side * 40) % 260)
            cv.drawPath(blob([(540 + side * 145, y), (552 + side * 145, y + 30), (540 + side * 145, y + 46), (528 + side * 145, y + 30)]),
                        paint(C('#BFE3FF', 0.9)))
    if begging:                                                                                 # red, watering eyes
        for side in (-1, 1):
            cv.drawOval(skia.Rect(540 + side * 140 - 90, 820, 540 + side * 140 + 90, 1060), paint(C('#C83030', 0.18), blur=10))
    shade(cv, (540, 950), 1100, 0.55)


# ---------------------------------------------------------------- 3:33 AM
def bedroom(cv, t, candles=1.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A0B0E'))
    cv.drawRect(skia.Rect(0, 0, W, 1300), paint('#1A1C22'))
    cv.drawRect(skia.Rect(0, 1300, W, H), paint('#14161A'))
    if candles > 0:
        glow(cv, (540, 1500), 1100, CANDLE, 0.35 * candles * (0.9 + 0.1 * math.sin(t * 13)))


def candles_and_circle(cv, t, lit=1.0):
    cv.drawOval(skia.Rect(140, 1450, 940, 1800), paint('#E8E4DA', style='stroke', width=14))      # salt circle
    for k, x in enumerate((300, 540, 780)):
        y = 1600 if k != 1 else 1500
        cv.drawRect(skia.Rect(x - 22, y - 120, x + 22, y), paint('#E8E0D0'))
        if lit > 0:
            fl = 1 + 0.15 * math.sin(t * 17 + k)
            cv.drawPath(blob([(x, y - 190 * fl), (x + 16, y - 140), (x, y - 118), (x - 16, y - 140)]), paint(CANDLE))
            glow(cv, (x, y - 150), 120, CANDLE, 0.5 * lit)
        else:
            u = t - B['out']
            for j in range(4):                                                                   # smoke curls
                cv.drawCircle(x + 20 * math.sin(u * 3 + j), y - 140 - u * 120 - j * 40, 18 + j * 6, paint(C('#8A8A90', max(0.0, 0.4 - u * 0.2)), blur=10))


def shot_RITUAL(cv, t):
    bedroom(cv, t)
    cv.drawRect(skia.Rect(700, 300, 1000, 700), paint('#0E1626'))                                  # window, moon
    glow(cv, (850, 500), 200, '#9FB8D8', 0.25)
    mascot(cv, 540, 2080, 0.85, crouch=0.6, arm_l=(14, -75), arm_r=(14, -75), look=(0.0, 0.7), brow=0.6, mouth='open' if talk(t, 'Y02') else 'flat',
           mouth_open=talk(t, 'Y02') * 0.6, light_side=1, rim=CANDLE, rim_a=0.6)
    candles_and_circle(cv, t)
    cv.drawRect(skia.Rect(860, 1500, 960, 1680), paint('#101215'))                                 # phone playing the video
    cv.drawRect(skia.Rect(868, 1510, 952, 1670), paint('#BFE0FF'))
    text(cv, 'KESSRAH', 910, 1590, 22, '#C83030')
    shade(cv, (540, 1400), 1150, 0.6)


def shot_CANDLEFACE(cv, t):
    """Saying the name three times, lit from below by the candles."""
    bedroom(cv, t)
    n = 0
    for k in range(3):
        if t >= w_at('Y03', k):
            n = k + 1
    mascot(cv, 540, 2700, 1.95, light_side=1, rim=CANDLE, rim_a=0.7, look=(0.0, 0.0), brow=0.5 + 0.2 * n, mouth='open' if talk(t, 'Y03') else 'flat',
           mouth_open=talk(t, 'Y03') * 0.5, pupil=0.85 - 0.08 * n)
    glow(cv, (540, 1900), 1200, CANDLE, 0.4)
    shade(cv, (540, 1000), 1000, 0.65)


def w_at(line, k):
    ws = [x for x in WORDS if x['line'] == line]
    return ws[min(k, len(ws) - 1)]['start'] if ws else 0


def shot_CANDLES(cv, t):
    lit = 1.0 if t < B['out'] else 0.0
    bedroom(cv, t, candles=lit)
    candles_and_circle(cv, t, lit)
    shade(cv, (540, 1500), 1000, 0.55 if lit else 0.85)


def shot_DARKFACE(cv, t):
    """Lights out, only the moon. Your shaky laugh: 'Nothing happened.'"""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#08090C'))
    m = talk(t, 'Y04')
    mascot(cv, 540, 2700, 1.95, light_side=1, rim='#9FB8D8', rim_a=0.7, look=(0.5 * math.sin(t * 2), 0.0), brow=0.8, mouth='open' if m else 'smile',
           mouth_open=m * 0.5, sweat=True)
    dim(cv, 0.35)
    shade(cv, (700, 900), 1000, 0.6)


def shot_CORNER(cv, t):
    """The corner of your room in moonlight: clothes on a chair, a shelf... and in the dark gap, something blinks."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0E1016'))
    cv.drawPath(poly([(0, 0), (540, 500), (540, 1920), (0, 1920)]), paint('#1A1E28'))
    cv.drawPath(poly([(1080, 0), (540, 500), (540, 1920), (1080, 1920)]), paint('#151922'))
    cv.drawPath(poly([(700, 300), (1000, 380), (900, 1400), (640, 1300)]), paint(C('#9FB8D8', 0.10), blur=20))       # moonlight
    cv.drawRect(skia.Rect(140, 1100, 420, 1150), paint('#2A2420'))                                           # chair + clothes
    cv.drawRect(skia.Rect(160, 1150, 180, 1500), paint('#2A2420'))
    cv.drawRect(skia.Rect(380, 1150, 400, 1500), paint('#2A2420'))
    cv.drawPath(blob([(150, 1100), (300, 980), (420, 1100), (380, 1180), (200, 1180)]), paint('#3A3E4A'))
    cv.drawRect(skia.Rect(640, 900, 960, 930), paint('#2A2420'))                                             # shelf
    for k in range(4):
        cv.drawRect(skia.Rect(660 + k * 60, 820, 700 + k * 60, 900), paint(['#5A3A3A', '#3A4A5A', '#4A5A3A', '#5A5A3A'][k]))
    u = t - B['corner']
    op = 1.0 if 0.5 < u < 3.0 else 0.0
    if 1.3 < u < 1.5:
        op = 0.0                                                                                              # it blinks
    cv.drawPath(blob([(470, 1500), (480, 700), (540, 560), (600, 700), (610, 1500)]), paint(C('#030304', 0.85), blur=12))
    if op > 0:
        for side in (-1, 1):
            cv.drawOval(skia.Rect(540 + side * 46 - 26, 700 - 12, 540 + side * 46 + 26, 700 + 12), paint('#F2EEE6'))
            cv.drawCircle(540 + side * 46, 700, 9, paint('#B01212'))
            cv.drawCircle(540 + side * 46, 700, 40, paint(C('#B01212', 0.25), blur=14))
    shade(cv, (540, 800), 1000, 0.5)


def shot_RVIDEO(cv, t):
    """The video on your phone: the ritual instructions."""
    bedroom(cv, t)
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(200, 260, 880, 1560), 60, 60)), paint('#101215'))
    cv.drawRect(skia.Rect(230, 330, 850, 1490), paint('#0C0C0E'))
    text(cv, 'HOW TO SUMMON', 540, 470, 64, '#E8E4DA')
    text(cv, 'KESSRAH', 540, 580, 110, '#C83030')
    for k, ln in enumerate(('1. 3:33 AM', '2. SALT CIRCLE', '3. THREE CANDLES', '4. SAY HIS NAME 3 TIMES', "5. DON'T BLINK")):
        a = ease((t - B['ritual'] - 2.2 - k * 0.5) / 0.2)
        text(cv, ln, 280, 760 + k * 120, 54, C('#E8E4DA' if k < 4 else '#C83030', a), align='left')
    text(cv, '1.2M views  ·  "it actually worked??"', 540, 1420, 34, '#8A8F98')
    glow(cv, (540, 900), 700, '#BFE0FF', 0.15)
    for side in (-1, 1):
        hx = 540 + side * 360
        cv.drawPath(blob([(hx - 70, 1200), (hx + 70, 1180), (hx + 90, 1440), (hx - 60, 1500)]), paint('#F2C29B'))
    shade(cv, (540, 900), 1100, 0.5)


def shot_LOCKERS(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A4450'))
    for x in range(0, W, 110):
        cv.drawRect(skia.Rect(x + 6, 300, x + 104, 1500), paint('#4E6070'))
        for v in range(4):
            cv.drawRect(skia.Rect(x + 30, 340 + v * 18, x + 80, 346 + v * 18), paint('#3A4858'))
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#5A5650'))
    glow(cv, (540, 0), 1100, FLUOR, 0.25)
    m = talk(t, 'Y05')
    mascot(cv, 330, 1900, 0.8, light_side=1, rim=FLUOR, rim_a=0.3, look=(0.7, 0.0), head_turn=0.3, mouth='open' if m else 'smile', mouth_open=m * 0.6,
           brow=0.2, arm_r=(30, 60))
    mascot(cv, 770, 1900, 0.8, light_side=-1, rim=FLUOR, rim_a=0.3, look=(-0.7, 0.0), head_turn=-0.3, mouth='flat', brow=0.4 if t > B['school'] + 2 else 0.0,
           **THEO)
    shade(cv, (540, 1100), 1250, 0.45)


def shot_THEO(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A4450'))
    for x in range(0, W, 110):
        cv.drawRect(skia.Rect(x + 6, 300, x + 104, 1500), paint('#4E6070'))
    glow(cv, (540, 0), 1100, FLUOR, 0.2)
    m = talk(t, 'T01', 'T02')
    scared = t >= B['t02']
    mascot(cv, 540, 2700, 1.95, light_side=-1, rim=FLUOR, rim_a=0.5, look=(-0.4, 0.0), head_turn=-0.2, brow=1.0 if scared else 0.6,
           mouth='open' if m else 'frown', mouth_open=m * 0.7, pupil=0.65 if scared else 0.85, sweat=scared, **THEO)
    shade(cv, (540, 950), 1100, 0.5)


def shot_BOARD(cv, t):
    """The board: YOU CALLED. I CAME. DON'T BLINK. — written as you watch, no one holding the chalk."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1E2A24'))
    cv.drawRect(skia.Rect(40, 300, 1040, 1500), paint('#24382E'))
    cv.drawRect(skia.Rect(40, 300, 1040, 1500), paint('#6A4A2E', style='stroke', width=24))
    lines = ('YOU CALLED.', 'I CAME.', "DON'T BLINK.")
    u = t - B['board'] - 0.3
    total = sum(len(l) for l in lines)
    shown = int(max(0.0, u) * 9)
    y = 640
    for ln in lines:
        part = ln[:max(0, min(len(ln), shown))]
        shown -= len(ln)
        text(cv, part, 100, y, 150, '#E8E4DA', align='left', skew=-0.15, alpha=0.9)
        y += 300
    if 0 < shown + total < total + 4:
        pass
    glow(cv, (540, 900), 900, FLUOR, 0.1 * flicker(t, 6, 6.0, 0.35))
    shade(cv, (540, 900), 1100, 0.55)


def shot_BACK(cv, t):
    """The back of the empty classroom. In the last row, Kessrah stands up. On JS2, every eyelid opens."""
    shot_EMPTY(cv, t)
    u = max(0.0, t - B['k01'])
    rise = min(1.0, u / 2.0)
    op = 0.0 if t < B['js2'] else min(1.0, (t - B['js2']) / 0.12)
    ks = 0.62 if t < B['js2'] else 0.95
    kessrah(cv, 540, (1700 + (1 - rise) * 500) if t < B['js2'] else 780 + 2120 * ks, ks, open_=op, t=t, tilt=8 * math.sin(t * 1.5), reach=op * 0.6)
    shade(cv, (540, 900), 1100, 0.55)


def shot_EYE(cv, t):
    """Your eye, huge: red veins, watering, the lid trembling."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#E8B898'))
    cv.drawOval(skia.Rect(80, 560, 1000, 1360), paint('#F6F2EC'))
    cv.save(); cv.clipPath(skia.Path.Oval(skia.Rect(80, 560, 1000, 1360)), skia.ClipOp.kIntersect, True)
    for k in range(14):
        a = k * 0.45
        x0, y0 = 540 + math.cos(a) * 460, 960 + math.sin(a) * 400
        cv.drawLine(x0, y0, x0 + (540 - x0) * 0.4, y0 + (960 - y0) * 0.4 + 12 * math.sin(k), paint(C('#C83030', 0.6), style='stroke', width=4))
    jit = 6 * math.sin(t * 31)
    cv.drawCircle(540 + jit, 960, 230, paint('#5A3417'))
    cv.drawCircle(540 + jit, 960, 90, paint('#0A0604'))
    cv.drawCircle(600 + jit, 900, 30, paint('#FFFFFF'))
    lid = 0.12 + 0.06 * math.sin(t * 23)
    cv.drawRect(skia.Rect(0, 0, W, 560 + 800 * lid), paint('#E8B898'))
    cv.restore()
    cv.drawPath(skia.Path().addArc(skia.Rect(80, 560 + 800 * lid - 400, 1000, 560 + 800 * lid + 400), 0, 180), paint('#2A1A12', style='stroke', width=12))
    for k in range(3):                                                                              # a tear forming
        y = 1360 + ((t * 120 + k * 80) % 300)
        cv.drawPath(blob([(300, y), (316, y + 40), (300, y + 60), (284, y + 40)]), paint(C('#BFE3FF', 0.8)))
    shade(cv, (540, 960), 900, 0.5)


def shot_CREEP(cv, t):
    """The choice: the empty classroom; every time you blink, Kessrah is a row closer."""
    shot_EMPTY(cv, t)
    n = sum(1 for (bt, *_r) in E.BLINKS if B['choice'] <= bt <= t)
    dist = max(0.0, 1 - n * 0.22)
    s_ = 0.5 + (1 - dist) * 0.9
    kessrah(cv, 540, max(1600.0, 720 + 2120 * s_), s_, open_=0.35 + 0.65 * (1 - dist), t=t, tilt=10 * math.sin(t), reach=(1 - dist) * 0.5)
    shade(cv, (540, 900), 1100, 0.55)


def shot_SCARE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000'))
    u = t - B['js3']
    ks = 2.0 + u * 1.5
    kessrah(cv, 540, 900 + 2120 * ks, ks, open_=1.0, t=t, tilt=-6 + 14 * u)


SHOTS = {'RVIDEO': shot_RVIDEO, 'STARE': shot_STARE, 'EMPTY': shot_EMPTY, 'CLASS': shot_CLASS, 'HART': shot_HART, 'YOU': shot_YOU, 'RITUAL': shot_RITUAL,
         'CANDLEFACE': shot_CANDLEFACE, 'CANDLES': shot_CANDLES, 'DARKFACE': shot_DARKFACE, 'CORNER': shot_CORNER, 'LOCKERS': shot_LOCKERS,
         'THEO': shot_THEO, 'BOARD': shot_BOARD, 'BACK': shot_BACK, 'EYE': shot_EYE, 'CREEP': shot_CREEP, 'SCARE': shot_SCARE}


def needed():
    out = []
    for sgm in E.SEGMENTS:
        if 'rewind' in sgm:
            a, b = sgm['rewind']
            out += [(sgm['src'], f) for f in range(int(b * FPS), int(a * FPS) + 2)]
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
            if i % 300 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
