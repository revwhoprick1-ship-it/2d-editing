#!/usr/bin/env python3
"""VIDEO_017 "Flight 404" — real 2D horror (2dEDIT), flat vector drawn with Skia.

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
import edit_video017 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS, JS, s = E.B, E.LS, E.WORDS, E.JS, E.s
MOON = '#9FD0C8'          # blue-green moonlight
TUNG = '#FFC27A'          # weak tungsten

CAST = {
    'M': dict(),
    'B': dict(glasses='#22262C', hair='#3A2A1A', hair_sh='#24180E', shirt='#2A7A7A', shirt_sh='#1E5C5C'),
    'L': dict(hair='#1A1A1A', hair_sh='#0A0A0A', shirt='#6A4A8A', shirt_sh='#50366A', skin='#8E5A3C', skin_sh='#6E432C'),
    'X': dict(hair='#E8C060', hair_sh='#C09A40', shirt='#D8B020', shirt_sh='#A88618', skin='#F5D0B0', skin_sh='#D9AE8C', blush=0.3),
    'J': dict(belly=1.35, hair='#1A1A1A', hair_sh='#0A0A0A', shirt='#3E5A3E', shirt_sh='#2C422C', skin='#6E4A30', skin_sh='#543622'),
}
SPEAK = {'M': ('M',), 'B': ('B',), 'L': ('L',), 'K': ('K',), 'J': ('J',)}


def talk(t, who):
    return mouth_open(t, WORDS, [l['id'] for l in E._T['lines'] if l['id'][0] == who])


def mood(t):
    if t < B['feet']:
        return 'calm'
    if t < B['click2']:
        return 'scared'
    if t < B['land']:
        return 'terror'
    if t < B['window']:
        return 'calm'
    return 'scared'


def face_pose(who, t):
    m = mood(t)
    P = dict(CAST[who])
    o = talk(t, who)
    P['mouth_open'] = o
    if m == 'calm':
        P.update(brow={'L': 0.3, 'B': 0.2, 'M': 0.1}[who], mouth='smile' if who == 'L' else 'flat')
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


# ===================================================================== cabin
NIGHT, RED, WARM = '#6A8AC8', '#E0342C', '#FFD9A0'


def light(t):
    """'night' -> 'red' (after Lawrence) -> 'warm' (landed) -> 'red' again at the very end."""
    if t < B['js2']:
        return 'night'
    if t < B['land']:
        return 'red'
    if t < B['open_']:
        return 'warm'
    return 'red'


def tint(cv, t):
    L_ = light(t)
    if L_ == 'night':
        dim(cv, 0.28, '#050A18')
    elif L_ == 'red':
        dim(cv, 0.30 * flicker(t, 3, 4.0, 0.7), '#3A0404')
    else:
        glow(cv, (540, 300), 1400, WARM, 0.12)


def sign(cv, x, y, sc, on, t):
    """Seatbelt sign panel: on = lit (amber), off = dark."""
    cv.drawRoundRect(skia.Rect(x - 150 * sc, y - 55 * sc, x + 150 * sc, y + 55 * sc), 18 * sc, 18 * sc, paint('#2A2E36'))
    col = '#FFB23A' if on else '#4A4E56'
    if on:
        glow(cv, (x, y), 260 * sc, '#FFB23A', 0.35)
    cv.drawCircle(x - 70 * sc, y - 18 * sc, 14 * sc, paint(col))
    cv.drawRoundRect(skia.Rect(x - 92 * sc, y - 2 * sc, x - 48 * sc, y + 40 * sc), 8 * sc, 8 * sc, paint(col))
    cv.drawRect(skia.Rect(x - 110 * sc, y + 12 * sc, x - 30 * sc, y + 20 * sc), paint(col))
    text(cv, 'FASTEN', x + 50 * sc, y + 14 * sc, 30 * sc, col)


def row_front(cv, t, who='BML', belts=True, people=True, lights_=None, unbuckle=0.0):
    """Front view of our row: window (Bob) / middle (you) / aisle (Lawrence). Bins + seatbelt sign above."""
    lt = lights_ or light(t)
    wall = {'night': '#1C2230', 'red': '#2A1414', 'warm': '#D8CDBA'}[lt]
    cv.drawRect(skia.Rect(0, 0, W, H), paint(wall))
    cv.drawRect(skia.Rect(0, 0, W, 520), paint({'night': '#2A3142', 'red': '#3A1A1A', 'warm': '#ECE4D6'}[lt]))       # bins
    for x in (0, 360, 720):
        cv.drawRect(skia.Rect(x + 10, 60, x + 350, 500), paint(C('#000000', 0.12), style='stroke', width=6))
        cv.drawRect(skia.Rect(x + 140, 440, x + 220, 470), paint(C('#000000', 0.25)))
    sign(cv, 540, 590, 1.0, lt != 'warm' or t < B['land'] + 1.0, t)
    for x in (300, 780):                                                                   # reading lights
        cv.drawCircle(x, 600, 22, paint('#FFF2D0' if lt == 'night' else '#6A6A6A'))
        if lt == 'night':
            cv.drawPath(poly([(x - 20, 600), (x + 20, 600), (x + 160, 1500), (x - 160, 1500)]), paint(C('#FFE6B0', 0.06)))
    cv.drawRoundRect(skia.Rect(-40, 700, 130, 1000), 60, 60, paint('#0A0E18'))             # the window by Bob
    cv.drawRoundRect(skia.Rect(-20, 720, 110, 980), 50, 50, paint('#101A30' if lt != 'warm' else '#8AB8E0'))
    for i, who in enumerate('BML'):
        x = (220, 540, 860)[i]
        cv.drawRoundRect(skia.Rect(x - 165, 760, x + 165, 1900), 60, 60, paint('#22314E'))            # seat back
        cv.drawRoundRect(skia.Rect(x - 120, 780, x + 120, 900), 30, 30, paint('#E6E2DA'))              # headrest cover
        if people and who in who_list(who, t):
            P = face_pose(who, t)
            if t >= B['land'] and t < B['window'] and who == 'B':
                P.update(mouth='smile', brow=-0.2)
            mascot(cv, x, 1960, 0.78, legs=False, light_side=1, rim=RED if lt == 'red' else NIGHT, rim_a=0.35, **P)
        if belts:
            cv.drawRect(skia.Rect(x - 150, 1700, x + 150, 1730), paint('#3A3A40'))
            op = unbuckle if who in 'BM' else 0.0
            cv.save(); cv.rotate(-35 * op, x, 1715)
            cv.drawRoundRect(skia.Rect(x - 40, 1695, x + 40, 1735), 6, 6, paint('#B8BCC4'))
            cv.restore()
    for x in (60, 380, 700, 1020):                                                         # armrests
        cv.drawRoundRect(skia.Rect(x - 25, 1560, x + 25, 1920), 20, 20, paint('#2A2E36'))
    tint(cv, t)
    shade(cv, (540, 1100), 1300, 0.45)


def who_list(who, t):
    return 'BM' if t >= B['js2'] else 'BML'


def cabin(cv, cam, t, rows=14, heads=True, staring=0.0, bins_moving=0.0, masks=0.0, z0=1.0):
    """Down-the-aisle perspective: seat rows both sides, passenger heads, bins above, windows."""
    lt = light(t)
    base = {'night': ('#121826', '#1C2434', '#262E40'), 'red': ('#1E0A0A', '#2E1212', '#3A1818'), 'warm': ('#B8AE9C', '#D8CEBA', '#ECE4D6')}[lt]
    cv.drawRect(skia.Rect(0, 0, W, H), paint(base[0]))
    cv.drawPath(quad(cam, [(-2.0, 0, z0), (2.0, 0, z0), (2.0, 0, 30), (-2.0, 0, 30)]), paint(base[1]))
    cv.drawPath(quad(cam, [(-0.35, 0.001, z0), (0.35, 0.001, z0), (0.35, 0.001, 30), (-0.35, 0.001, 30)]), paint('#3A1E2A' if lt != 'warm' else '#6A3A4A'))
    cv.drawPath(quad(cam, [(-2.0, 2.4, z0), (2.0, 2.4, z0), (2.0, 2.4, 30), (-2.0, 2.4, 30)]), paint(base[2]))
    for side in (-1, 1):
        cv.drawPath(quad(cam, [(side * 2.0, 0, z0), (side * 2.0, 2.4, z0), (side * 2.0, 2.4, 30), (side * 2.0, 0, 30)]), paint(base[0]))
        for k in range(rows + 2, 0, -1):                                                         # far rows first
            z = z0 + k * 1.0
            bump = bins_moving * max(0.0, math.sin(t * 9 + k * 1.7 + side)) * 0.08
            cv.drawPath(quad(cam, [(side * 0.4, 1.75 - bump, z), (side * 2.0, 1.75 - bump, z), (side * 2.0, 2.3, z), (side * 0.4, 2.3, z)]),
                        paint(base[2]))
            cv.drawPath(quad(cam, [(side * 0.4, 1.75 - bump, z), (side * 2.0, 1.75 - bump, z), (side * 2.0, 1.75 - bump, z + 0.98),
                                   (side * 0.4, 1.75 - bump, z + 0.98)]), paint(C('#000000', 0.25)))
            wx, wy = cam.p(side * 1.98, 1.35, z + 0.5)
            r_ = cam.scale(z + 0.5, 0.25) * 1150 / 2
            cv.drawOval(skia.Rect(wx - r_ * 0.5, wy - r_, wx + r_ * 0.5, wy + r_), paint('#0A1020' if lt != 'warm' else '#8AB8E0'))
            for s_ in range(3):
                x = side * (0.55 + s_ * 0.48)
                cv.drawPath(quad(cam, [(x - 0.2, 0.45, z), (x + 0.2, 0.45, z), (x + 0.2, 1.2, z), (x - 0.2, 1.2, z)]), paint('#22314E'))
                if heads and not (k == 4 and side == -1):
                    hx, hy = cam.p(x, 1.28, z + 0.3)
                    hr = cam.scale(z + 0.3, 0.28) * 1150 / 2
                    seed = (k * 7 + s_ * 3 + side) % 5
                    cv.drawCircle(hx, hy, hr, paint(['#2A1A12', '#1A1A1A', '#6A4A2A', '#D8B060', '#3A2A1A'][seed]))
                    if staring > 0:
                        cv.drawCircle(hx, hy + hr * 0.15, hr * 0.85, paint(C(['#F2C29B', '#8E5A3C', '#D99B76', '#F5D0B0', '#6E4A30'][seed], staring)))
                        for e_ in (-1, 1):
                            cv.drawCircle(hx + e_ * hr * 0.35, hy + hr * 0.1, hr * 0.2, paint(C('#FFFFFF', staring)))
                            cv.drawCircle(hx + e_ * hr * 0.35, hy + hr * 0.1, hr * 0.08, paint(C('#000000', staring)))
            if masks > 0:
                for s_ in range(3):
                    mx, my_ = cam.p(side * (0.55 + s_ * 0.48), 1.75 - 0.5 * masks + 0.05 * math.sin(t * 5 + k + s_), z + 0.4)
                    mr = cam.scale(z + 0.4, 0.12) * 1150 / 2
                    tx, ty = cam.p(side * (0.55 + s_ * 0.48), 1.75, z + 0.4)
                    cv.drawLine(tx, ty, mx, my_, paint('#D8D0C0', style='stroke', width=max(1.0, mr * 0.15)))
                    cv.drawCircle(mx, my_, mr, paint('#E6C23A'))
    if lt == 'red':
        for k in range(1, rows, 2):
            p = cam.p(0, 0.02, z0 + k)
            glow(cv, p, cam.scale(z0 + k, 0.6) * 600, RED, 0.25)


def make_cu(who):
    def shot(cv, t):
        lt = light(t)
        cv.drawRect(skia.Rect(0, 0, W, H), paint({'night': '#1C2230', 'red': '#2A1414', 'warm': '#D8CDBA'}[lt]))
        cv.drawRoundRect(skia.Rect(140, 500, 940, 2400), 120, 120, paint('#22314E'))
        cv.drawRoundRect(skia.Rect(230, 540, 850, 860), 60, 60, paint('#E6E2DA'))
        P = face_pose(who, t)
        if t >= B['land'] and t < B['window'] and who == 'B':
            P.update(mouth='smile', brow=-0.2)
        if who == 'B' and B['tray'] <= t < B['land']:                                     # blood on Bob's face/glasses
            P['sweat'] = True
        shake_ = 5 * math.sin(t * 41) if mood(t) == 'terror' else 0
        mascot(cv, 540 + shake_, 2760, 2.0, light_side=1, rim=RED if lt == 'red' else NIGHT, rim_a=0.5,
               look=(0.3 * math.sin(t * 0.8 + len(who)), 0.0), **P)
        if who == 'B' and B['tray'] <= t < B['land']:
            for bx, by in ((420, 760), (650, 900), (560, 1180)):
                cv.drawPath(blob([(bx - 18, by), (bx, by - 22), (bx + 18, by), (bx + 4, by + 50)]), paint(C('#7A0E0E', 0.9)))
        tint(cv, t)
        shade(cv, (540, 950), 1100, 0.5)
    return shot


def shot_ROW(cv, t):
    row_front(cv, t)
    if t < 0.4:                                                                            # the DING: the sign blazes
        glow(cv, (540, 590), 700, '#FFB23A', 0.5 * (1 - t / 0.4))


def shot_MAP(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#05070C'))
    cv.drawRoundRect(skia.Rect(60, 420, 1020, 1500), 30, 30, paint('#0C2A44'))
    for k in range(8):                                                                      # the loops it has flown
        r = 260 + k * 6
        cv.drawCircle(540, 960, r, paint(C('#E8E8E8', 0.12 + 0.05 * k), style='stroke', width=4))
    a = t * 0.9
    px, py = 540 + math.cos(a) * 300, 960 + math.sin(a) * 300
    cv.save(); cv.translate(px, py); cv.rotate(math.degrees(a) + 180)
    cv.drawPath(poly([(0, -40), (12, 10), (40, 20), (12, 22), (8, 40), (-8, 40), (-12, 22), (-40, 20), (-12, 10)]), paint('#FFFFFF'))
    cv.restore()
    text(cv, 'FLIGHT 404', 540, 540, 54, '#E8E8E8')
    text(cv, 'TIME TO DESTINATION', 540, 1360, 40, '#9AA8B8')
    text(cv, '--:--', 540, 1440, 64, '#E0342C')
    text(cv, 'OCEAN', 540, 970, 34, '#3A5A78')


def shot_ROW14(cv, t):
    row_front(cv, t, people=False)
    glow(cv, (540, 1640), 120, '#9FC8FF', 0.5)
    cv.drawRoundRect(skia.Rect(500, 1600, 580, 1680), 10, 10, paint('#9FC8FF'))           # a phone still lit on the seat
    text(cv, 'ROW 14', 540, 700, 60, '#C8C8C8')


def shot_AISLE(cv, t):
    cam = Cam(0.0, eye=1.4, vy=860)
    cabin(cv, cam, t)
    z = max(1.5, 6.0 - (t - B['cart']) * 2.2)                                              # the cart comes down the aisle
    fx, fy = cam.p(0, 0, z + 0.6)
    purser(cv, fx, fy, cam.scale(z + 0.6, 2.4) * 1150 / 2400, t=t, rim=WARM, rim_a=0.3)
    cv.drawPath(quad(cam, [(-0.3, 0, z), (0.3, 0, z), (0.3, 1.0, z), (-0.3, 1.0, z)]), paint('#B8BCC4'))
    cv.drawPath(quad(cam, [(-0.3, 1.0, z), (0.3, 1.0, z), (0.3, 1.0, z + 0.5), (-0.3, 1.0, z + 0.5)]), paint('#D8DCE4'))
    tint(cv, t)
    shade(cv, (540, 900), 1200, 0.45)


def shot_FEET(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#141A28'))
    cv.drawRect(skia.Rect(0, 1100, W, H), paint('#3A1E2A'))
    cv.drawRect(skia.Rect(600, 600, 1080, 1700), paint('#B8BCC4'))                          # the cart
    cv.drawCircle(700, 1720, 40, paint('#2A2A2A')); cv.drawCircle(980, 1720, 40, paint('#2A2A2A'))
    purser(cv, 320, 1800, 1.45, t=t, wrong=1.0, rim=WARM, rim_a=0.3)
    tint(cv, t)
    shade(cv, (400, 1500), 900, 0.5)


def shot_TURN(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1C2230'))
    mk = 1.0 if t >= B['js1'] else 0.0
    nk = min(1.0, max(0.0, (t - B['js1']) * 4)) * 0.25
    purser(cv, 540, 4300 + nk * 400, 1.6, t=t, mask=mk, neck=nk, blood_=mk, rim=WARM, rim_a=0.5)
    if t >= B['js1'] + JS:
        dim(cv, min(0.9, (t - B['js1'] - JS) * 2))
    tint(cv, t)
    shade(cv, (540, 900), 1100, 0.5)


def shot_HEADS(cv, t):
    cam = Cam(0.0, eye=1.75, vy=780)
    st = min(1.0, max(0.0, (t - B['heads']) / 0.5))
    cabin(cv, cam, t, staring=st)
    tint(cv, t)
    shade(cv, (540, 900), 1200, 0.4)


def shot_BIN(cv, t):
    cam = Cam(0.0, eye=1.4, vy=860)
    cabin(cv, cam, t, staring=1.0)
    op = min(1.0, max(0.0, (t - B['bin']) / 1.5))
    cv.drawRect(skia.Rect(560, 0, 1080, 420), paint('#262E40'))                              # the bin right above him
    cv.save(); cv.rotate(-60 * op, 560, 0)
    cv.drawRect(skia.Rect(560, 330, 1080, 420), paint('#323A4E'))
    cv.restore()
    if op > 0:
        cv.drawRect(skia.Rect(570, 330, 1070, 330 + 80 * op), paint('#000000'))
        for f in range(4):                                                                   # grey fingers spilling out
            x = 640 + f * 110
            cv.drawLine(x, 380, x + 10 * math.sin(t * 6 + f), 380 + 260 * op, paint('#D8CFC6', style='stroke', width=16))
    P = face_pose('L', t)
    P.update(look=(0.0, -0.6 * op))
    mascot(cv, 760, 2300, 1.15, view='front', light_side=1, rim=NIGHT, rim_a=0.4, **P)
    tint(cv, t)
    shade(cv, (600, 900), 1200, 0.45)


def shot_GRAB(cv, t):
    u = t - B['js2']
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120606'))
    cv.drawRect(skia.Rect(0, 0, W, 520), paint('#2A1010'))
    cv.drawRect(skia.Rect(100, 420, 980, 520), paint('#000000'))
    yy = 2100 - min(1.0, u / 0.35) * 1400                                                    # yanked up into the bin
    P = dict(CAST['L'], brow=1.0, mouth='open', mouth_open=1.0, pupil=0.4, sweat=True)
    mascot(cv, 540 + 30 * math.sin(u * 40), yy, 1.0, walk=(u * 6) % 1, light_side=1, rim=RED, rim_a=0.5, **P)
    for k in range(3):
        purser_arm = [(300 + k * 240, 420), (380 + k * 160, 700 + 200 * k), (540, yy - 700)]
        cv.drawPath(poly(purser_arm, closed=False), paint('#D8CFC6', style='stroke', width=34))
    if u > 0.2:
        for k in range(22):                                                                  # blood spray
            a = k * 0.29
            r = (u - 0.2) * 1800
            cv.drawCircle(540 + math.cos(a) * r * (0.4 + (k % 3) * 0.3), 600 + math.sin(a) * r * 0.5, 14 + (k % 4) * 6, paint('#7A0A0A'))
    cv.drawRect(skia.Rect(0, 0, W, 430), paint('#2A1010'))


def shot_TRAY(cv, t):
    u = t - B['tray']
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1E0C0C'))
    cv.drawRect(skia.Rect(0, 0, W, 300), paint('#3A1818'))
    cv.drawLine(0, 300, W, 300, paint('#000000', style='stroke', width=10))                  # the bin seam
    P = dict(CAST['L'])
    hx = 420
    cv.drawRect(skia.Rect(hx - 34, 300, hx + 34, 760), paint(P['skin_sh']))                   # Lawrence's arm hanging out, limp
    cv.drawCircle(hx, 790, 60, paint(P['skin']))
    for k in range(4):
        cv.drawLine(hx - 36 + k * 24, 800, hx - 40 + k * 26, 880 + 6 * math.sin(t * 2 + k), paint(P['skin'], style='stroke', width=18))
    cv.drawRect(skia.Rect(80, 1300, 1000, 1360), paint('#5A5E66'))                           # tray table
    cv.drawRect(skia.Rect(80, 1360, 1000, 1400), paint('#3A3E46'))
    fill = min(1.0, u / 2.4)
    cv.drawRect(skia.Rect(560, 1080, 720, 1300), paint(C('#E8E8F0', 0.5)))                   # Bob's cup filling red
    cv.drawRect(skia.Rect(566, 1300 - 210 * fill, 714, 1296), paint('#8A0A0A'))
    for k in range(10):                                                                      # drips: from the seam, and from his fingers
        for src_x, sy, sp in ((640, 300, 1.0), (hx, 900, 1.3)):
            ph = (u * sp + k * 0.31) % 1.0
            y = sy + ph * (1300 - sy)
            cv.drawPath(blob([(src_x - 10, y), (src_x, y - 22), (src_x + 10, y), (src_x, y + 18)]), paint('#8A0A0A'))
    cv.drawRect(skia.Rect(620, 300, 660, 300 + 40 + 10 * math.sin(t * 3)), paint('#8A0A0A'))
    sy = min(1220.0, 300 + max(0.0, u - 1.1) * 2600)                                         # his sneaker drops onto the tray
    if u > 1.1:
        cv.drawPath(blob([(180, sy), (360, sy - 10), (380, sy + 60), (170, sy + 70)]), paint('#E8E8E8'))
        cv.drawRect(skia.Rect(170, sy + 60, 385, sy + 80), paint('#C83030'))
    shade(cv, (540, 1000), 1100, 0.45)


def shot_BINS(cv, t):
    cam = Cam(0.0, eye=1.4, vy=860)
    cabin(cv, cam, t, heads=True, bins_moving=1.0)
    tint(cv, t)
    shade(cv, (540, 900), 1200, 0.45)


def shot_REVEAL(cv, t):
    cam = Cam(0.0, eye=1.2, vy=900)
    cabin(cv, cam, t, bins_moving=0.4)
    u = min(1.0, max(0.0, (t - B['reveal']) / 1.8))
    fx, fy = cam.p(0, 0, 3.2)
    sc = cam.scale(3.2, 2.4) * 1150 / 2400
    purser(cv, fx, fy - (1 - u) * 900, sc, t=t, neck=0.15 + 0.55 * u, mask=1.0 if u > 0.6 else 0.0, reach=0.5 * u, blood_=1.0,
           wrong=1.0, rim=RED, rim_a=0.7)
    tint(cv, t)
    shade(cv, (540, 900), 1100, 0.45)


def shot_BELT(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1E1414'))
    cv.drawRect(skia.Rect(0, 900, W, 1000), paint('#3A3A40'))
    pop = 1.0 if t >= s('B05') + 0.3 else 0.0
    cv.save(); cv.rotate(-55 * pop, 540, 950)
    cv.drawRoundRect(skia.Rect(400, 880, 680, 1020), 16, 16, paint('#B8BCC4'))
    cv.drawRoundRect(skia.Rect(440, 910, 640, 990), 8, 8, paint('#8A8E96'))
    cv.restore()
    for side in (-1, 1):
        cv.drawRoundRect(skia.Rect(540 + side * 20 - 240, 1300, 540 + side * 20 + 240, 1900), 80, 80, paint(CAST['B']['shirt_sh']))
    tint(cv, t)
    shade(cv, (540, 950), 900, 0.5)


def shot_CEILING(cv, t):
    cam = Cam(0.0, eye=1.0, vy=1250)
    cabin(cv, cam, t, masks=1.0)
    u = t - B['ceiling']
    z = max(1.4, 5.5 - u * 3.0)                                                              # crawling along the ceiling at us
    fx, fy = cam.p(0, 2.4, z)
    sc = cam.scale(z, 2.4) * 1150 / 2400
    cv.save(); cv.translate(fx, fy); cv.rotate(180)
    purser(cv, 0, 0, sc, t=t, neck=0.4, mask=1.0, reach=1.0, blood_=1.0, wrong=1.0, crawl=True, rim=RED, rim_a=0.7)
    cv.restore()
    tint(cv, t)
    shade(cv, (540, 1100), 1200, 0.45)


def shot_FACE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120606'))
    cv.save(); cv.translate(540, 1000); cv.rotate(180)
    purser(cv, 0, 5600, 2.5, t=t, neck=0.0, mask=1.0, blood_=1.0, rim=RED, rim_a=0.8)
    cv.restore()
    tint(cv, t)
    shade(cv, (540, 1000), 900, 0.4)


def shot_LAND(cv, t):
    row_front(cv, t, unbuckle=min(1.0, max(0.0, (t - s('B06')) / 0.3)))


def shot_WINDOW(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#D8CDBA' if light(t) == 'warm' else '#2A1414'))
    cv.drawRoundRect(skia.Rect(190, 420, 890, 1500), 300, 300, paint('#8A8478'))
    win = skia.Path(); win.addRoundRect(skia.Rect(240, 470, 840, 1450), 270, 270)
    cv.save(); cv.clipPath(win, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A1428', shader=lin((0, 470), (0, 1450), [C('#060C1C'), C('#1A2A48')])))
    cv.drawCircle(700, 620, 60, paint('#EEF2F6'))
    for k in range(7):                                                                       # clouds far below, sliding past
        x = (k * 260 - t * 120) % 1400 - 200
        cv.drawOval(skia.Rect(x, 1180 + (k % 3) * 40, x + 360, 1300 + (k % 3) * 40), paint(C('#8A98B0', 0.7)))
    cv.drawPath(poly([(240, 1000), (840, 900), (840, 960), (240, 1110)]), paint('#B8BCC4'))   # the wing: still flying
    cv.drawCircle(830, 920, 10, paint('#E0342C'))
    cv.restore()
    if t >= B['open_'] - 0.6:                                                                # the bin above Bob creaks open
        u = min(1.0, (t - B['open_'] + 0.6) / 0.6)
        cv.drawRect(skia.Rect(0, 0, W, 160 * u), paint('#000000'))
        for f in range(4):
            x = 200 + f * 70
            cv.drawLine(x, 0, x + 8, 260 * u, paint('#D8CFC6', style='stroke', width=14))
    tint(cv, t)
    shade(cv, (540, 950), 1000, 0.4)


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
