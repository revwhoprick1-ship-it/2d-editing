#!/usr/bin/env python3
"""VIDEO_007 "After Hours · Part 1" — real 2D animation (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_007/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
from flat import C, H, W, blob, glow, lin, mascot, monster, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video007 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS

GUARD = dict(shirt='#2B3A55', shirt_sh='#1E2A40', pants='#1E2433', pants_sh='#151A25', shoe='#1A1A1A', shoe_sh='#111111',
             hair='#8A8A8A', hair_sh='#6A6A6A', cap='#1E2A40', mustache='#7A7A7A', belly=1.35, skin='#E3AE86', skin_sh='#C48E68')
MOON = '#9FC3FF'


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


def floor_persp(cv, y0, y1, c0, c1):
    cv.drawRect(skia.Rect(0, y0, W, y1), paint(c0, shader=lin((0, y0), (0, y1), [C(c0), C(c1)])))


def beam(cv, x0, y0, x1, y1, width, alpha=0.35, col='#FFF3D0'):
    """Flashlight cone from (x0, y0) towards (x1, y1)."""
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang), math.cos(ang)
    p = poly([(x0 + nx * 10, y0 + ny * 10), (x1 + nx * width, y1 + ny * width), (x1 - nx * width, y1 - ny * width), (x0 - nx * 10, y0 - ny * 10)])
    cv.drawPath(p, paint(C(col, alpha), blur=18, shader=lin((x0, y0), (x1, y1), [C(col, alpha), C(col, 0.0)]), blend=skia.BlendMode.kPlus))
    glow(cv, (x1, y1), width * 1.3, col, alpha * 0.8)


def dust(cv, t, n=30, alpha=0.3, seed=0):
    for k in range(n):
        x = ((k * 0.618 + seed * 0.13) % 1) * W
        y = ((k * 0.381 + t * 0.012 * (1 + k % 3)) % 1) * H
        cv.drawCircle(x + 6 * math.sin(t + k), y, 2 + k % 3, paint(C('#FFF1D8', alpha)))


# ===================================================================== HIDE: under the teacher's desk (hook + ending)
def door_feet(t):
    """Feet shadows under the door: hook (something is right outside) and after 'the footsteps stop'."""
    return t < B['rewind0'] or t >= B['stop']


def shot_HIDE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0C1016'))
    # back wall + door across the room
    cv.drawRect(skia.Rect(0, 300, W, 1430), paint('#1B232C', shader=lin((0, 300), (0, 1430), [C('#151B22'), C('#222C36')])))
    floor_persp(cv, 1430, H, '#1A1714', '#2A231D')
    dx0, dx1, dy0, dy1 = 560, 900, 560, 1430
    cv.drawRect(skia.Rect(dx0 - 20, dy0 - 20, dx1 + 20, dy1), paint('#2B2018'))
    cv.drawRect(skia.Rect(dx0, dy0, dx1, dy1), paint('#3A2A1E'))
    cv.drawRect(skia.Rect(dx0 + 50, dy0 + 50, dx1 - 50, dy0 + 330), paint('#6E7F8E', shader=lin((0, dy0 + 50), (0, dy0 + 330), [C('#8796A6'), C('#56626E')])))
    cv.save()
    cv.translate(dx0 + 50 + (dx1 - dx0 - 100), 0)
    cv.scale(-1, 1)                                         # lettering seen from inside: mirrored
    text(cv, "TEACHERS'", (dx1 - dx0 - 100) / 2, dy0 + 170, 52, '#C9A45C')
    text(cv, 'OFFICE', (dx1 - dx0 - 100) / 2, dy0 + 230, 52, '#C9A45C')
    cv.restore()
    # light under the door (hallway) + feet shadows
    cv.drawRect(skia.Rect(dx0 + 6, dy1 - 10, dx1 - 6, dy1), paint('#FFE9B8'))
    glow(cv, ((dx0 + dx1) / 2, dy1), 260, '#FFD58A', 0.3)
    if door_feet(t):
        for fx in (660, 790):
            cv.drawRect(skia.Rect(fx - 40, dy1 - 12, fx + 40, dy1 + 2), paint('#050505'))
        # a tall shadow behind the frosted glass
        sx = keys(t, [(0.0, 700), (B['rewind0'], 720)]) if t < B['rewind0'] else 720
        cv.drawPath(blob([(sx - 60, dy0 + 330), (sx - 50, dy0 + 120), (sx, dy0 + 60), (sx + 50, dy0 + 120), (sx + 60, dy0 + 330)]),
                    paint(C('#0A0C10', 0.8), blur=14))
    # door handle (turns slowly in the hook)
    hang = keys(t, [(0, 0), (s_('N02'), 0), (s_('N02') + 1.2, -24), (B['rewind0'], -24)]) if t < B['rewind0'] else 0
    cv.save()
    cv.translate(dx0 + 40, 1010)
    cv.rotate(hang)
    cv.drawRect(skia.Rect(-8, -12, 80, 12), paint('#B9A27A'))
    cv.restore()
    cv.drawCircle(dx0 + 40, 1010, 18, paint('#8E7A56'))
    # moonlight from a window on the left
    cv.drawPath(poly([(0, 1450), (380, 1450), (560, 1920), (0, 1920)]), paint(C(MOON, 0.10), blur=12))
    # him, crouched under the desk, hugging his knees
    dive = keys(t, [(B['dive'], 0.0), (B['dive'] + 0.55, 1.0)]) if t >= B['dive'] else 1.0
    x = 340 + (1 - dive) * 500
    breathe = 6 * math.sin(t * 2 * math.pi * 1.6)
    look_door = 0.9
    mascot(cv, x, 1900 + breathe, 1.15, crouch=0.6 + 0.4 * dive, arm_l=(14, -75), arm_r=(14, -75), look=(look_door, 0.1),
           brow=1.0, mouth='o' if t > B['dive'] or t < 0.2 else 'flat', mouth_open=0.0, pupil=0.62, sweat=True,
           light_side=1, rim=MOON, rim_a=0.6, head_turn=0.25, lids=blink(t, [1.4, 3.8, B['dive'] + 2.5, B['dive'] + 6.0]))
    # the desk we hide under (frame): underside, side panel
    cv.drawRect(skia.Rect(0, 0, W, 330), paint('#2A1B12', shader=lin((0, 0), (0, 330), [C('#140D08'), C('#3A271A')])))
    cv.drawRect(skia.Rect(0, 300, W, 340), paint('#4A3222'))
    cv.drawRect(skia.Rect(0, 300, 70, H), paint('#22160F'))
    cv.drawRect(skia.Rect(70, 300, 92, H), paint('#3A271A'))
    dust(cv, t, 25, 0.22)
    shade(cv, (620, 1200), 1250, 0.7)


def s_(i):
    return LS[i][0]


# ===================================================================== the guard booth
def booth_bg(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1C2228'))
    cv.drawRect(skia.Rect(0, 0, W, 1450), paint('#2C3036', shader=lin((0, 0), (0, 1450), [C('#22262B'), C('#33373D')])))
    cv.drawRect(skia.Rect(80, 220, 640, 700), paint('#0A1220'))                        # window: night outside
    glow(cv, (520, 330), 120, '#DDE8FF', 0.4)
    cv.drawCircle(520, 330, 42, paint('#E8EEF8'))
    cv.drawPath(poly([(80, 700), (180, 560), (300, 600), (420, 520), (640, 590), (640, 700)]), paint('#05080D'))
    for x in range(80, 641, 140):
        cv.drawRect(skia.Rect(x - 6, 220, x + 6, 700), paint('#3A3F46'))
    cv.drawRect(skia.Rect(80, 452, 640, 466), paint('#3A3F46'))
    floor_persp(cv, 1450, H, '#25221E', '#38322B')
    text(cv, 'SECURITY', 860, 330, 64, '#C9A45C', alpha=0.8)
    # CCTV monitors (right)
    for i in range(4):
        x0, y0 = 700 + (i % 2) * 180, 450 + (i // 2) * 150
        cv.drawRect(skia.Rect(x0, y0, x0 + 160, y0 + 130), paint('#101215'))
        cv.drawRect(skia.Rect(x0 + 10, y0 + 10, x0 + 150, y0 + 120), paint('#5E7A8A' if i != 3 else '#3A4A55'))
        for k in range(6):
            yy = y0 + 18 + k * 17
            cv.drawLine(x0 + 12, yy, x0 + 148, yy, paint(C('#FFFFFF', 0.1 + 0.08 * math.sin(t * 20 + k + i)), style='stroke', width=3))
        glow(cv, (x0 + 80, y0 + 65), 160, '#8FB4CC', 0.18)
    cv.drawRect(skia.Rect(660, 760, 1080, 820), paint('#3A2C20'))                    # desk
    cv.drawRect(skia.Rect(660, 820, 1080, 1450), paint('#2E2219'))
    cv.drawPath(poly([(760, 760), (800, 640), (840, 640), (820, 760)]), paint('#2B2B30'))  # lamp
    cv.drawPath(poly([(770, 640), (870, 640), (900, 690), (740, 690)]), paint('#C99A4E'))
    glow(cv, (820, 700), 520, '#FFC070', 0.35)


def shot_BOOTH(cv, t):
    booth_bg(cv, t)
    # chair back
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(160, 640, 560, 1300), 40, 40)), paint('#1A1C20'))
    snore = math.sin(t * 2 * math.pi * 0.35)
    out = mascot(cv, 360, 1720, 0.95, crouch=0.55, lids=1.0, mouth='o', mouth_open=0.25 + 0.2 * max(0, snore), head_tilt=16,
                 arm_l=(18, 40), arm_r=(18, 40), light_side=1, rim='#FFC070', rim_a=0.3, **GUARD)
    # keys on the belt (right hip)
    kx, ky = 470, 1390
    cv.drawCircle(kx, ky, 22, paint('#C9A45C', style='stroke', width=7))
    for k in range(4):
        cv.drawLine(kx - 14 + k * 10, ky + 16, kx - 22 + k * 14, ky + 74, paint('#D9C27A' if k % 2 else '#B8BEC6', style='stroke', width=10))
    glow(cv, (kx, ky + 40), 80, '#FFE6A0', 0.25 + 0.1 * math.sin(t * 3))
    for i in range(3):                                                            # Zzz
        ph = (t * 0.5 + i / 3) % 1.0
        text(cv, 'z', 470 + ph * 120 + i * 10, 760 - ph * 220, 50 + i * 14, '#FFFFFF', alpha=0.6 * (1 - ph))
    shade(cv, (600, 1000), 1250, 0.6)


def shot_KEYS(cv, t):
    """CU: the key ring on the sleeping guard's belt; your hand slides it off."""
    breathe = 14 * math.sin(t * 2 * math.pi * 0.35)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1E2A40'))
    cv.drawPath(blob([(-200, 300 + breathe), (540, 220 + breathe), (1280, 300 + breathe), (1280, 1300), (-200, 1300)]), paint('#2B3A55'))
    for y in (520, 760):
        cv.drawCircle(540, y + breathe, 16, paint('#1A2333'))
    cv.drawRect(skia.Rect(0, 1120, W, 1250), paint('#15171B'))                       # belt
    cv.drawRect(skia.Rect(380, 1105, 560, 1265), paint('#B9A27A', style='stroke', width=16))
    cv.drawRect(skia.Rect(0, 1250, W, H), paint('#1E2433'))                           # trousers
    cv.drawRect(skia.Rect(740, 1110, 790, 1265), paint('#101215'))                    # belt loop
    # hand: enters, grips, lifts the ring off the loop slowly; freezes on the snort
    hx = keys(t, [(B['keys'], 1300), (s_('N05'), 830), (s_('N05') + 0.9, 790), (B['snort'] - 0.4, 820), (B['snort'], 1000)])
    hy = keys(t, [(B['keys'], 1420), (s_('N05'), 1290), (s_('N05') + 0.9, 1270), (B['snort'] - 0.4, 1150), (B['snort'], 1120)])
    held = t >= s_('N05') + 0.9
    rx, ry = (hx - 30, hy - 40) if held else (765, 1260)
    cv.drawCircle(rx, ry, 46, paint('#C9A45C', style='stroke', width=12))
    for k, (col, ln) in enumerate((('#D9C27A', 210), ('#B8BEC6', 180), ('#C9A45C', 230), ('#B8BEC6', 160))):
        a = math.radians(-20 + k * 14 + (6 * math.sin(t * 9 + k) if held else 0))
        x2, y2 = rx + math.sin(a) * ln, ry + 40 + math.cos(a) * ln
        cv.drawLine(rx, ry + 40, x2, y2, paint(col, style='stroke', width=22))
        cv.drawRect(skia.Rect(x2 - 12, y2 - 30, x2 + 12, y2), paint(col))
    glow(cv, (rx, ry + 120), 260, '#FFE6A0', 0.2)
    cv.drawPath(poly([(hx + 60, hy - 50), (1300, hy - 120), (1300, hy + 140), (hx + 60, hy + 60)]), paint('#F07A1A'))
    cv.drawPath(blob([(hx - 70, hy - 40), (hx + 70, hy - 60), (hx + 90, hy + 40), (hx - 40, hy + 70), (hx - 110, hy + 10)]), paint('#F2C29B'))
    for k in range(4):
        cv.drawPath(poly([(hx - 70 + k * 10, hy - 30 + k * 22), (hx - 150 + k * 6, hy - 10 + k * 26)], closed=False), paint('#E3B08A', style='stroke', width=26))
    glow(cv, (300, 200), 900, '#FFC070', 0.15)
    shade(cv, (650, 1200), 1100, 0.7)


def shot_GUARDCU(cv, t):
    booth_bg(cv, t)
    u = t - B['snort']
    jerk = 10 * math.exp(-u * 5) * math.sin(u * 40)
    mascot(cv, 540, 2850, 2.0, crouch=0.0, lids=1.0, mouth='open' if u < 0.35 else 'o', mouth_open=0.4, head_tilt=12 + jerk,
           brow=-0.5 if u < 0.5 else 0.0, arm_l=(3, 0), arm_r=(3, 0), light_side=1, rim='#FFC070', rim_a=0.4, **GUARD)
    shade(cv, (540, 900), 1150, 0.6)


# ===================================================================== outside, the corridor, the office door
def shot_EXT(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#070B16', shader=lin((0, 0), (0, 1300), [C('#04060D'), C('#14203A')])))
    for k in range(60):
        cv.drawCircle((k * 197) % W, (k * 113) % 900, 1.5 + k % 2, paint(C('#FFFFFF', 0.4 + 0.3 * math.sin(t * 2 + k))))
    glow(cv, (800, 300), 260, '#DDE8FF', 0.45)
    cv.drawCircle(800, 300, 78, paint('#E9EEF6'))
    cv.drawPath(blob([(560, 340), (700, 300), (860, 330), (980, 320), (900, 370), (640, 380)]), paint(C('#1A2238', 0.9)))
    # the school: Building C
    cv.drawRect(skia.Rect(-20, 820, 1100, 1420), paint('#141A26'))
    cv.drawPath(poly([(-20, 820), (540, 640), (1100, 820)]), paint('#10151F'))
    for r in range(3):
        for c in range(7):
            x, y = 40 + c * 150, 900 + r * 160
            lit = (r, c) == (1, 5)
            cv.drawRect(skia.Rect(x, y, x + 90, y + 110), paint('#E9C77A' if lit else '#0A0E16'))
            if lit:
                glow(cv, (x + 45, y + 55), 120, '#FFC86A', 0.3)
    cv.drawRect(skia.Rect(440, 690, 640, 780), paint('#0A0E16'))
    text(cv, 'C', 540, 770, 90, '#C9A45C')
    cv.drawRect(skia.Rect(470, 1240, 610, 1420), paint('#07090E'))                 # entrance
    floor_persp(cv, 1420, H, '#0E1410', '#1A231A')
    for x in range(-40, W + 60, 64):                                                  # fence (foreground)
        cv.drawRect(skia.Rect(x, 1560, x + 10, 1920), paint('#05070A'))
    cv.drawRect(skia.Rect(0, 1600, W, 1614), paint('#05070A'))
    cv.drawRect(skia.Rect(0, 1760, W, 1774), paint('#05070A'))
    # you, running to the entrance (side view, right -> left), keys in hand
    u = (t - B['ext']) / max(0.1, B['corr'] - B['ext'])
    x = 1150 - 700 * ease(min(1.0, u * 1.1))
    mascot(cv, x, 1500, 0.32, view='side', face=-1, walk=(t * 2.4) % 1, run=True, item='keys', light_side=1, rim=MOON, rim_a=0.6)
    shade(cv, (540, 1000), 1300, 0.55)


def shot_CORR(cv, t):
    """Side-scrolling corridor: lockers, doors, moonlit windows. You walk right with the flashlight."""
    u = t - B['corr']
    scroll = u * 260
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0B0F15'))
    cv.drawRect(skia.Rect(0, 380, W, 1420), paint('#18202A'))
    cv.save()
    cv.translate(-scroll, 0)
    for i in range(-1, 12):
        x = i * 360
        if i % 4 == 2:                                                               # classroom door
            cv.drawRect(skia.Rect(x + 40, 760, x + 300, 1420), paint('#2B2018'))
            cv.drawRect(skia.Rect(x + 120, 830, x + 220, 1000), paint('#3E4D5A'))
            text(cv, f'C2{i:02d}', x + 170, 740, 40, '#7D8895')
        else:                                                                         # lockers
            for k in range(4):
                lx = x + k * 90
                cv.drawRect(skia.Rect(lx + 4, 820, lx + 86, 1420), paint('#2E3D4E' if k % 2 else '#2A3848'))
                for v in range(4):
                    cv.drawRect(skia.Rect(lx + 22, 860 + v * 16, lx + 68, 866 + v * 16), paint('#1C2632'))
                cv.drawRect(skia.Rect(lx + 64, 1080, lx + 74, 1130), paint('#8E99A6'))
        # high windows with moonlight
        cv.drawRect(skia.Rect(x + 60, 430, x + 300, 640), paint('#0F1A2C'))
        glow(cv, (x + 180, 535), 120, MOON, 0.18)
        cv.drawPath(poly([(x + 60, 1420), (x + 300, 1420), (x + 380, 1700), (x + 140, 1700)]), paint(C(MOON, 0.08), blur=10))
    cv.restore()
    floor_persp(cv, 1420, H, '#1C1A18', '#2A2622')
    cv.drawRect(skia.Rect(0, 1416, W, 1424), paint('#0E0C0A'))
    ph = (u * 1.25) % 1
    out = mascot(cv, 420, 1700, 0.42, view='side', face=1, walk=ph, arm_r=(-70, 0), item='flashlight', light_side=1, rim=MOON, rim_a=0.4,
                 brow=0.8, look=(0.3, 0.0))
    hx, hy = out.get('hand_r', (560, 1300))
    beam(cv, hx + 40, hy + 10, 1060, 1500, 170, 0.35)
    for x in (900, 1050):                                                            # flickering tube far right
        pass
    shade(cv, (480, 1300), 1150, 0.72)


def shot_DOOR(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2B2018'))
    cv.drawRect(skia.Rect(140, 0, 940, H), paint('#3A2A1E'))
    cv.drawRect(skia.Rect(220, 160, 860, 900), paint('#7F8D99', shader=lin((0, 160), (0, 900), [C('#8D9BA8'), C('#5A6670')])))
    text(cv, "TEACHERS'", 540, 480, 104, '#C9A45C')
    text(cv, 'OFFICE', 540, 600, 104, '#C9A45C')
    cv.drawRect(skia.Rect(620, 1080, 820, 1460), paint('#B9A27A'))                  # lock plate
    cv.drawCircle(720, 1350, 34, paint('#1A1410'))
    # the keys: three tries, the third turns
    tries = [(B['door'], B['door'] + 0.9), (B['door'] + 1.0, B['key_turn'] - 0.2), (B['key_turn'] - 0.15, 99)]
    k = 0
    for i, (a, b) in enumerate(tries):
        if a <= t < b:
            k = i
    rot = 0.0
    if k == 2:
        rot = keys(t, [(B['key_turn'], 0.0), (B['key_turn'] + 0.25, 80.0)])
    else:
        rot = 8 * math.sin(t * 30) if (t - tries[k][0]) > 0.3 else 0
    cv.save()
    cv.translate(720, 1350)
    cv.rotate(rot)
    cv.drawRect(skia.Rect(-12, -80, 12, 0), paint(['#B8BEC6', '#D9C27A', '#C9A45C'][k]))
    cv.drawCircle(0, -110, 44, paint(['#B8BEC6', '#D9C27A', '#C9A45C'][k]))
    cv.drawCircle(0, -110, 16, paint('#3A2A1E'))
    cv.restore()
    cv.drawPath(poly([(790, 1250), (1100, 1180), (1100, 1420), (790, 1330)]), paint('#F07A1A'))
    cv.drawPath(blob([(700, 1220), (800, 1200), (820, 1300), (720, 1320)]), paint('#F2C29B'))
    beam(cv, 1100, 1700, 640, 900, 260, 0.32)
    if t > B['key_turn'] + 0.4:                                                       # door swings in: darkness behind
        o = ease((t - B['key_turn'] - 0.4) / 0.8)
        cv.drawRect(skia.Rect(140, 0, 140 + 800 * o * 0.35, H), paint('#050608'))
    shade(cv, (600, 1000), 1100, 0.65)


# ===================================================================== the office
def office_bg(cv, t, lit=1.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#10151B'))
    cv.drawRect(skia.Rect(0, 260, W, 1430), paint('#1C242C', shader=lin((0, 260), (0, 1430), [C('#151B21'), C('#232C35')])))
    floor_persp(cv, 1430, H, '#1E1A16', '#2C251E')
    cv.drawRect(skia.Rect(90, 420, 470, 860), paint('#0B1424'))                       # barred window
    glow(cv, (300, 560), 200, '#DDE8FF', 0.3)
    cv.drawCircle(330, 540, 46, paint('#E6ECF6'))
    for x in range(90, 471, 76):
        cv.drawRect(skia.Rect(x - 5, 420, x + 5, 860), paint('#2A3038'))
    cv.drawPath(poly([(90, 1430), (470, 1430), (700, 1920), (180, 1920)]), paint(C(MOON, 0.07), blur=12))
    for i in range(3):                                                                 # filing cabinets
        x0 = 600 + i * 150
        cv.drawRect(skia.Rect(x0, 640, x0 + 140, 1430), paint('#58626C' if i != 1 else '#5E6872'))
        for d in range(4):
            y0 = 660 + d * 190
            cv.drawRect(skia.Rect(x0 + 10, y0, x0 + 130, y0 + 175), paint('#4A535C'))
            cv.drawRect(skia.Rect(x0 + 45, y0 + 20, x0 + 95, y0 + 44), paint('#D8D2C0'))
            cv.drawRect(skia.Rect(x0 + 50, y0 + 70, x0 + 90, y0 + 82), paint('#2A3038'))
    text(cv, 'STAFF ONLY', 760, 600, 40, '#C93A2E', alpha=0.8)
    for k in range(4):                                                                 # pinned papers
        cv.drawRect(skia.Rect(110 + k * 90, 960 + (k % 2) * 30, 180 + k * 90, 1050 + (k % 2) * 30), paint('#C9C2AE'))


def shot_OFFICE(cv, t):
    office_bg(cv, t)
    pull = keys(t, [(B['office'], 0.0), (B['office'] + 1.2, 1.0)])
    x0, y0 = 750, 850                                                                  # 2nd drawer of the middle cabinet pulls out
    cv.drawRect(skia.Rect(x0 - 4, y0 + 20 - 50 * pull, x0 + 144, y0 + 175 + 40 * pull), paint('#6A747E'))
    for f in range(6):
        cv.drawRect(skia.Rect(x0 + 8 + f * 22, y0 + 10 - 50 * pull - 30, x0 + 26 + f * 22, y0 + 60 - 50 * pull), paint('#D9C690' if f % 2 else '#C9B47A'))
    out = mascot(cv, 470, 1700, 0.62, view='side', face=1, arm_r=(-60, -10), item='flashlight', light_side=1, rim=MOON, rim_a=0.5,
                 brow=0.6, look=(0.4, 0.4), arm_l=(-30, -40))
    hx, hy = out.get('hand_r', (600, 1100))
    beam(cv, hx + 30, hy, 820, 900, 120, 0.4)
    dust(cv, t, 20, 0.2, 2)
    shade(cv, (650, 1100), 1150, 0.7)


def portrait(cv, x, y, s, look):
    """Small ID photo of a student (puppet head, varied colours)."""
    cv.drawRect(skia.Rect(x, y, x + 150 * s, y + 190 * s), paint('#B8C2CC'))
    cv.save()
    cv.clipRect(skia.Rect(x, y, x + 150 * s, y + 190 * s))
    mascot(cv, x + 75 * s, y + 520 * s, 0.38 * s, **look)
    cv.restore()


STUDENTS = [
    ('1987', dict(shirt='#7A4FA0', shirt_sh='#5C3A7A', hair='#2A1A10', hair_sh='#1A100A', skin='#C98E66', skin_sh='#A8704C')),
    ('1994', dict(shirt='#2E8A6A', shirt_sh='#22684F', hair='#D9B06A', hair_sh='#B38C4E')),
    ('2003', dict(shirt='#B03A3A', shirt_sh='#862C2C', hair='#4A2A1A', hair_sh='#2E1A10', skin='#8E5A3C', skin_sh='#6E432C')),
    ('2011', dict(shirt='#3A6EB0', shirt_sh='#2C5486', hair='#1A1A1A', hair_sh='#0A0A0A')),
    ('2019', dict(shirt='#C9A030', shirt_sh='#9E7C22', hair='#8A4A2A', hair_sh='#6A361E')),
]


def stamp(cv, x, y, size, a, rot=-12):
    cv.save()
    cv.translate(x, y)
    cv.rotate(rot)
    cv.scale(1 + (1 - a) * 0.8, 1 + (1 - a) * 0.8)
    w = size * 2.6
    cv.drawRect(skia.Rect(-w / 2, -size * 0.7, w / 2, size * 0.5), paint(C('#C8202A', 0.9 * a), style='stroke', width=size * 0.09))
    text(cv, 'KEPT', 0, size * 0.32, size, C('#C8202A', 0.9 * a))
    cv.restore()


def shot_FILES(cv, t):
    """Top-down under the flashlight: the files that aren't tests."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1B120C'))
    for k in range(9):
        cv.drawLine(0, 120 + k * 220, W, 100 + k * 220, paint(C('#2A1C12', 0.8), style='stroke', width=6))
    cv.drawRect(skia.Rect(60, 260, 1020, 1700), paint('#C9A86A'))                    # open folder
    cv.drawRect(skia.Rect(60, 260, 1020, 300), paint('#B8975A'))
    text(cv, 'STUDENT RECORDS · NIGHT PROGRAM', 540, 360, 44, '#5A4020')
    n_show = 5
    for i, (yr, look) in enumerate(STUDENTS):
        appear = ease((t - B['files'] - 0.4 - i * 0.35) / 0.25)
        if appear <= 0:
            continue
        y = 420 + i * 245 + (1 - appear) * 60
        cv.drawRect(skia.Rect(110, y, 970, y + 225), paint(C('#EFE8D6', appear)))
        portrait(cv, 130, y + 18, 1.0, dict(look, look=(0.0, 0.0), mouth='flat', brow=0.2))
        for r in range(3):
            cv.drawRect(skia.Rect(310, y + 40 + r * 48, 310 + [420, 300, 360][r], y + 64 + r * 48), paint(C('#4A4A4A', 0.6 * appear)))
        text(cv, f'ENROLLED {yr}', 310, y + 200, 34, C('#3A3A3A', appear), align='left')
        sa = ease((t - B['stamps'] - 0.25 - i * 0.28) / 0.12)
        if sa > 0:
            stamp(cv, 820, y + 120, 64, sa)
    # the newest file: YOUR photo, stamp box still empty, the note
    if t >= B['note']:
        a = ease((t - B['note']) / 0.4)
        y = 520 + (1 - a) * 300
        cv.save()
        cv.rotate(-4, 540, y)
        cv.drawRect(skia.Rect(150, y, 1000, y + 330), paint('#F4EEDC'))
        portrait(cv, 175, y + 30, 1.35, dict(look=(0.0, 0.0), mouth='flat', brow=0.4))
        for r in range(3):
            cv.drawRect(skia.Rect(400, y + 60 + r * 52, 400 + [360, 260, 300][r], y + 86 + r * 52), paint(C('#4A4A4A', 0.6)))
        text(cv, 'ENROLLED THIS YEAR', 400, y + 290, 38, '#3A3A3A', align='left')
        cv.drawRect(skia.Rect(780, y + 200, 960, y + 300), paint(C('#C8202A', 0.6), style='stroke', width=4))
        cv.restore()
        na = ease((t - B['note'] - 0.6) / 0.3)
        if na > 0:
            cv.save()
            cv.rotate(6, 640, 1150)
            cv.drawRect(skia.Rect(380, 940, 960, 1380), paint(C('#F3DC5A', na)))
            for k2, ln in enumerate(('HE COMES BACK', 'FOR THE ONES', 'WHO CHEAT.')):
                text(cv, ln, 670, 1060 + k2 * 100, 76, C('#1A1A30', na), skew=-0.25)
            cv.restore()
    if B['kept'] <= t < B['note']:                                                       # the word, huge
        stamp(cv, 540, 980, 210, ease((t - B['kept']) / 0.1), rot=-10)
    # flashlight pool
    glow(cv, (560, 1000), 900, '#FFF3D0', 0.12)
    shade(cv, (560, 1000), 1050, 0.8)


def face_cu(cv, t, bg, **pose):
    bg(cv, t)
    mascot(cv, 540, 2700, 1.95, **pose)


def uplight(cv, alpha=0.4):
    """Flashlight from below (horror): warm glow from the bottom of frame."""
    glow(cv, (540, 1900), 1300, '#FFE6B8', alpha)


def shot_FACE(cv, t):
    def bg(c, tt):
        c.drawRect(skia.Rect(0, 0, W, H), paint('#0B0E12'))
    face_cu(cv, t, bg, look=(keys(t, [(B['face'], -0.6), (s_('D1'), 0.4), (e_('D1') - 0.3, -0.5)]), 0.3), brow=1.0, mouth='frown',
            mouth_open=talk(t, 'D1'), pupil=0.7, sweat=True, light_side=-1, rim=MOON, rim_a=0.5, lids=blink(t, [B['face'] + 0.4]))
    uplight(cv, 0.35)
    shade(cv, (540, 1100), 1100, 0.7)


def e_(i):
    return LS[i][1]


def shot_TEST(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1B120C'))
    cv.save()
    cv.rotate(-3, 540, 960)
    cv.drawRect(skia.Rect(110, 220, 980, 1720), paint('#F2EEE2'))
    text(cv, 'WESTBROOK HIGH', 545, 330, 54, '#2A2A2A')
    text(cv, 'BIOLOGY · UNIT TEST 4', 545, 400, 40, '#4A4A4A')
    text(cv, 'NAME:', 170, 520, 40, '#2A2A2A', align='left')
    cv.drawLine(290, 528, 700, 528, paint('#2A2A2A', style='stroke', width=3))
    text(cv, 'CLASS: 10-B', 760, 520, 40, '#2A2A2A', align='left')
    for r in range(9):
        y = 640 + r * 110
        text(cv, f'{r + 1}.', 170, y, 36, '#3A3A3A', align='left')
        cv.drawLine(230, y + 8, 900, y + 8, paint('#B8B2A2', style='stroke', width=3))
        mark = '#D02A2A'
        if r in (0, 2, 3, 5, 6, 8):
            cv.drawLine(860, y - 30, 920, y + 10, paint(mark, style='stroke', width=8))
            cv.drawLine(920, y - 30, 860, y + 10, paint(mark, style='stroke', width=8))
    # the score
    cv.drawCircle(760, 1560, 120, paint('#D02A2A', style='stroke', width=10))
    text(cv, '/100', 840, 1590, 46, '#D02A2A', align='left')
    digit_x = 690
    text(cv, '38', digit_x + 60, 1600, 130, '#D02A2A', align='right')
    # the pen turns the 3 into an 8: an extra loop drawn over the left half
    u = ease((t - B['becomes']) / 0.9)
    if u > 0:
        p = skia.Path()
        p.addArc(skia.Rect(628, 1478, 686, 1540), 90, 180 * u)
        p2 = skia.Path()
        p2.addArc(skia.Rect(624, 1532, 690, 1600), 90, 180 * max(0, u * 2 - 1))
        cv.drawPath(p, paint('#D02A2A', style='stroke', width=13))
        cv.drawPath(p2, paint('#D02A2A', style='stroke', width=13))
    text(cv, 'F', 220, 1640, 180, '#D02A2A', alpha=1.0)
    cv.restore()
    # pen + hand
    pen_t = keys(t, [(B['test'], 0.0), (B['pen'], 0.0), (B['becomes'], 1.0), (B['becomes'] + 0.9, 1.15), (B['bang'], 1.2)])
    px = 1250 - 590 * min(1, pen_t) + (30 * math.sin(t * 10) if 1 < pen_t < 1.15 else 0)
    py = 1900 - 360 * min(1, pen_t)
    cv.drawLine(px, py, px + 160, py + 240, paint('#C8202A', style='stroke', width=28))
    cv.drawLine(px, py, px + 22, py + 33, paint('#2A2A2A', style='stroke', width=14))
    cv.drawPath(blob([(px + 90, py + 150), (px + 230, py + 140), (px + 260, py + 260), (px + 120, py + 290)]), paint('#F2C29B'))
    cv.drawPath(poly([(px + 200, py + 200), (1300, py + 120), (1300, py + 420), (px + 220, py + 320)]), paint('#F07A1A'))
    glow(cv, (620, 1300), 900, '#FFF3D0', 0.12)
    shade(cv, (600, 1200), 1100, 0.75)


def shot_BANG(cv, t):
    office_bg(cv, t)
    u = t - B['bang']
    jump = max(0.0, 1 - u * 2.5) * 90
    cv.drawRect(skia.Rect(80, 1250, 1000, 1310), paint('#3A2A1E'))                   # his desk
    cv.drawRect(skia.Rect(110, 1310, 970, 1600), paint('#2E2219'))
    mascot(cv, 540, 1540 - jump, 0.8, look=(-0.9, -0.1), brow=1.0, mouth='o', pupil=0.55, arm_l=(60, 60), arm_r=(60, 60),
           head_turn=-0.5, sweat=True, light_side=-1, rim=MOON, rim_a=0.5, legs=False)
    cv.drawRect(skia.Rect(80, 1250, 1000, 1310), paint('#3A2A1E'))
    cv.drawRect(skia.Rect(110, 1310, 970, 1600), paint('#2E2219'))
    for k in range(10):                                                                 # papers flying
        if u < 1.5:
            x = 300 + k * 60 + u * (k - 5) * 160
            y = 1230 - u * 420 + u * u * 300 + k * 6
            cv.save(); cv.rotate(u * 200 * (k - 5) / 5, x, y)
            cv.drawRect(skia.Rect(x - 40, y - 28, x + 40, y + 28), paint('#EFE8D6'))
            cv.restore()
    beam(cv, 700, 1260, 1000, 1150, 90, 0.3)
    shade(cv, (540, 1100), 1150, 0.7)


def shot_FACE2(cv, t):
    def bg(c, tt):
        office_bg(c, tt)
    face_cu(cv, t, bg, look=(-0.9, 0.0), head_turn=-0.55, brow=1.0, mouth='o', mouth_open=talk(t, 'D2'), pupil=0.6, sweat=True,
            light_side=-1, rim=MOON, rim_a=0.6)
    uplight(cv, 0.25)
    shade(cv, (500, 1000), 1100, 0.7)


def shot_PEEK(cv, t):
    """Inside the dark office: the door opens a crack; a blade of hallway light."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#07090C'))
    gap = keys(t, [(B['peek'], 0.0), (B['peek'] + 1.0, 60.0), (B['pov'], 90.0)])
    x = 520
    cv.drawRect(skia.Rect(x, 220, x + gap, 1700), paint('#FFE2A8'))
    glow(cv, (x + gap / 2, 960), 500, '#FFD58A', 0.25)
    cv.drawPath(poly([(x, 1700), (x + gap, 1700), (x + gap * 6 + 300, H), (x - 200, H)]), paint(C('#FFD58A', 0.18), blur=14))
    cv.drawRect(skia.Rect(x - 380, 220, x, 1700), paint('#120E0A'))
    cv.drawRect(skia.Rect(x + gap, 220, x + gap + 300, 1700), paint('#120E0A'))
    mascot(cv, 860, 2450, 1.5, view='side', face=-1, look=(0.4, 0.0), brow=1.0, light_side=-1, rim='#FFD58A', rim_a=0.9)
    shade(cv, (540, 960), 1100, 0.6)


def school_hall(cv, cam, t, light_last=1.0):
    """One-point school corridor (lockers both sides); ceiling tubes; the last one flickers."""
    HW, HH, ZE = 1.4, 2.7, 16.0
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#06080B'))
    z0 = cam.z + 0.2
    cv.drawPath(quad(cam, [(-HW, 0, ZE), (HW, 0, ZE), (HW, HH, ZE), (-HW, HH, ZE)]), paint('#151A20'))
    for x, c0 in ((-HW, '#1E2A36'), (HW, '#1B2632')):
        cv.drawPath(quad(cam, [(x, 0, z0), (x, 0, ZE), (x, HH, ZE), (x, HH, z0)]), paint(c0))
        z = 1.0
        while z < ZE:
            p0, p1 = cam.p(x, 0.1, z), cam.p(x, 1.9, z)
            cv.drawLine(*p0, *p1, paint(C('#0E141A', 0.9), style='stroke', width=max(1.0, 30 / cam.d(z))))
            z += 0.45
        cv.drawPath(quad(cam, [(x, 1.9, z0), (x, 1.9, ZE), (x, 2.0, ZE), (x, 2.0, z0)]), paint('#10161C'))
    cv.drawPath(quad(cam, [(-HW, HH, z0), (HW, HH, z0), (HW, HH, ZE), (-HW, HH, ZE)]), paint('#0A0C0F'))
    cv.drawPath(quad(cam, [(-HW, 0, z0), (HW, 0, z0), (HW, 0, ZE), (-HW, 0, ZE)]), paint('#16191C'))
    for i, zl in enumerate((2.5, 5.0, 7.0, 8.6)):
        on = (light_last if i == 3 else 0.25)
        a, b = cam.p(-0.3, HH - 0.02, zl), cam.p(0.3, HH - 0.02, zl)
        cv.drawLine(*a, *b, paint(C('#F4F0E0', 0.2 + 0.8 * on), style='stroke', width=max(2, 60 / cam.d(zl))))
        if on > 0.5:
            glow(cv, cam.p(0, HH - 0.2, zl), 2200 / cam.d(zl), '#F4EAD0', 0.35 * on)
            cv.drawPath(quad(cam, [(-1.0, 0.002, zl - 0.9), (1.0, 0.002, zl - 0.9), (1.0, 0.002, zl + 0.9), (-1.0, 0.002, zl + 0.9)]),
                        paint(C('#F4EAD0', 0.12 * on), blur=6))


def shot_POV(cv, t):
    cam = Cam(0.0, eye=1.45, vy=900)
    lt = flicker(t, 3, 7.0, 0.1)
    school_hall(cv, cam, t, lt)
    z = 8.9
    s = cam.scale(z, 2.4) * 1150 / 2300
    fx, fy = cam.p(0.1, 0, z)
    monster(cv, fx, fy, s, head_tilt=35, look=(0, 0), eye_glow=0.0 if t < B['looks'] else 1.0)
    fl = cam.p(0.35, 0.95, z)                                                            # its flashlight, pointing at the floor
    beam(cv, fl[0], fl[1], fl[0] + 10, cam.p(0.4, 0, z - 1.2)[1], 30, 0.4)
    cp = cam.p(-0.4, 0, z - 0.7)                                                         # the guard's cap on the floor
    cv.drawOval(skia.Rect(cp[0] - 14, cp[1] - 6, cp[0] + 14, cp[1] + 4), paint('#1E2A40'))
    dim(cv, (1 - lt) * 0.5)
    # the door crack (we look through it)
    gap = keys(t, [(B['pov'], 300.0), (B['hand'], 340.0)])
    cv.drawRect(skia.Rect(0, 0, 540 - gap / 2, H), paint('#050608'))
    cv.drawRect(skia.Rect(540 + gap / 2, 0, W, H), paint('#050608'))
    shade(cv, (540, 960), 1000, 0.5)


def shot_HANDCU(cv, t):
    cam = Cam(10.5, eye=0.9, vy=760)
    school_hall(cv, cam, t, flicker(t, 3, 7.0, 0.1))
    # long fingers around the guard's flashlight, beam on the floor; the cap in the light
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.35)))
    cv.drawPath(poly([(380, -40), (470, -40), (520, 560), (450, 560)]), paint('#0B0C0F'))           # forearm
    cv.save(); cv.translate(500, 640); cv.rotate(-18)
    cv.drawRect(skia.Rect(-40, -60, 40, 330), paint('#2B2B30'))
    cv.drawRect(skia.Rect(-52, 300, 52, 380), paint('#45464E'))
    text(cv, 'SECURITY', 0, 140, 34, '#C9A45C')
    cv.restore()
    for k in range(5):
        a = math.radians(-60 + k * 30)
        fp = poly([(480, 600), (480 + math.cos(a) * 160, 600 + math.sin(a) * 60 + 90), (500 + math.cos(a) * 120, 760)], closed=False)
        cv.drawPath(fp, paint(C('#9FB4CC', 0.55), style='stroke', width=30, blur=3))
        cv.drawPath(fp, paint('#0B0C0F', style='stroke', width=22))
    beam(cv, 610, 980, 720, 1650, 260, 0.45)
    cv.drawPath(blob([(560, 1560), (700, 1500), (860, 1540), (880, 1620), (700, 1660), (560, 1630)]), paint('#1E2A40'))   # the cap
    cv.drawPath(blob([(600, 1620), (760, 1660), (900, 1640), (860, 1690), (640, 1690)]), paint('#151A24'))
    cv.drawCircle(720, 1540, 18, paint('#C9A45C'))
    shade(cv, (650, 1300), 1000, 0.65)


def shot_TURN(cv, t):
    lt = flicker(t, 5, 8.0, 0.2)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A0C10', shader=lin((0, 0), (0, H), [C('#5A6068'), C('#2A3038'), C('#0A0C10')], [0, 0.45, 1])))
    for x in (120, 960):                                                     # lockers behind it
        cv.drawRect(skia.Rect(x - 120, 300, x + 120, H), paint(C('#1E2A36', 0.9)))
    glow(cv, (540, 0), 1300, '#F4EAD0', 0.45 * lt)
    u = keys(t, [(B['turn'], 0.0), (B['looks'] - 0.35, 0.15), (B['looks'], 1.0)])
    tilt = 70 - 58 * u
    monster(cv, 540, 3950, 1.6, head_tilt=tilt, look=(0, 0), eye_glow=1.0 if t >= B['looks'] else 0.0, jaw=0.25 if t > B['looks'] + 0.5 else 0.0,
            flashlight=False)
    if t >= B['looks']:
        glow(cv, (540, 700), 700, '#E9F2FF', 0.12)
    dim(cv, (1 - lt) * 0.4)
    shade(cv, (540, 800), 1000, 0.6)


def shot_FACE3(cv, t):
    def bg(c, tt):
        c.drawRect(skia.Rect(0, 0, W, H), paint('#0B0E12'))
        c.drawRect(skia.Rect(0, 0, 180, H), paint(C('#FFE2A8', 0.12)))
    back = keys(t, [(B['face3'], 0.0), (B['dive'], 1.0)])
    cv.save()
    cv.translate(540, 900)
    cv.scale(1 - 0.12 * back, 1 - 0.12 * back)
    cv.translate(-540, -900)
    face_cu(cv, t, bg, look=(-0.7, 0.0), brow=1.0, mouth='open', mouth_open=max(0.5, talk(t, 'D3')), pupil=0.4, sweat=True,
            head_tilt=-6 * back, light_side=-1, rim='#FFE2A8', rim_a=0.8)
    cv.restore()
    shade(cv, (500, 1000), 1100, 0.7)


SHOTS = {'HIDE': shot_HIDE, 'BOOTH': shot_BOOTH, 'KEYS': shot_KEYS, 'GUARDCU': shot_GUARDCU, 'EXT': shot_EXT, 'CORR': shot_CORR,
         'DOOR': shot_DOOR, 'OFFICE': shot_OFFICE, 'FILES': shot_FILES, 'FACE': shot_FACE, 'TEST': shot_TEST, 'BANG': shot_BANG,
         'FACE2': shot_FACE2, 'PEEK': shot_PEEK, 'POV': shot_POV, 'HANDCU': shot_HANDCU, 'TURN': shot_TURN, 'FACE3': shot_FACE3}


def needed():
    out = []
    for sgm in E.SEGMENTS:
        if sgm['src'] is None:
            continue
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
            if i % 200 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
