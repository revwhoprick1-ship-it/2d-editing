#!/usr/bin/env python3
"""VIDEO_014 "Don't Touch The Vase · Part 2" — real 2D horror (2dEDIT). Re-uses Part 1's monster + recap shots (VIDEO_012).

    python3 VIDEOS/VIDEO_014/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
sys.path.insert(0, os.path.join(STUDIO, 'VIDEOS', 'VIDEO_012'))
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video014 as E  # noqa

_spec = importlib.util.spec_from_file_location('anim12', os.path.join(STUDIO, 'VIDEOS', 'VIDEO_012', 'anim2d.py'))
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
B12 = A.B

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
LAMP, MOON = A.LAMP, A.MOON
GMA = dict(hair='#D8D8D8', hair_sh='#B0B0B0', glasses='#3A3A3A', shirt='#6A4A5A', shirt_sh='#4E3644', skin='#EBC6A8', skin_sh='#C9A084',
           pants='#3A3A40', pants_sh='#2A2A30', shoe='#3A2A20', shoe_sh='#2A1A10')
ROSE = dict(long_hair=True, hair='#6A3E1F', hair_sh='#4A2912', shirt='#8A3A3A', shirt_sh='#6A2A2A')
ELI = dict(hair='#4A2A1A', hair_sh='#2E1A10', shirt='#3A5A8A', shirt_sh='#2A4466')
MOTHER = dict(long_hair=True, hair='#2A1A10', hair_sh='#1A100A', shirt='#8A8A80', shirt_sh='#6A6A60', skin='#EBC6A8', skin_sh='#C9A084')


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


def rain(cv, t, n=60, alpha=0.35):
    for k in range(n):
        x = (k * 97 + t * 900) % (W + 100) - 50
        y = (k * 211 + t * 2000) % H
        cv.drawLine(x, y, x - 12, y + 60, paint(C('#9FB8D8', alpha), style='stroke', width=3))


def sack(cv, x, y, s=1.0, swing=0.0):
    """The pillowcase full of broken porcelain, hanging from its knot at (x, y) (put that in the hand)."""
    cv.save(); cv.translate(x, y); cv.rotate(swing); cv.translate(-x, -y)
    cv.drawRect(skia.Rect(x - 14 * s, y - 10 * s, x + 14 * s, y + 40 * s), paint('#D8D2C4'))
    y = y + 90 * s
    cv.drawPath(blob([(x - 70 * s, y - 40 * s), (x + 60 * s, y - 50 * s), (x + 90 * s, y + 90 * s), (x, y + 140 * s), (x - 90 * s, y + 90 * s)]),
                paint('#E8E4DA'))
    cv.drawLine(x - 20 * s, y + 20 * s, x + 30 * s, y + 70 * s, paint(C('#2A4A9A', 0.6), style='stroke', width=6 * s))
    cv.restore()


# ---------------------------------------------------------------- recap (Part 1 shots)
def shot_R_VASE(cv, t):
    A.shot_VASE(cv, B12['crash'] + 0.15 + (t - B['recap']) * 0.5)


def shot_R_MOM(cv, t):
    A.shot_MOM(cv, B12['mom'] + 2.2)


def shot_R_DAD(cv, t):
    A.shot_DAD(cv, B12['js1'] + 0.1 + (t - B['r3']) * 0.3)


def shot_R_MIRROR(cv, t):
    A.shot_MIRROR(cv, B12['js2'] + 0.15)


# ---------------------------------------------------------------- outside
def shot_PEEPOUT(cv, t):
    """Grandma's front door in the rain. In the peephole, an old eye. (Frame 0.) Later: you blink; the door opens."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A0C10'))
    cv.drawRect(skia.Rect(0, 0, W, 1600), paint('#2A2420', shader=lin((0, 0), (0, 1600), [C('#1E1A16'), C('#3A3028')])))
    opened = keys(t, [(B['opens'], 0.0), (B['opens'] + 0.6, 1.0)]) if t >= B['door'] else 0.0
    dx0, dx1 = 300, 780
    cv.drawRect(skia.Rect(dx0, 300, dx1, 1600), paint('#FFD9A0' if opened > 0 else '#3A2618'))
    if opened > 0:                                                                                # Grandma in the warm doorway
        glow(cv, (540, 900), 900, LAMP, 0.4 * opened)
        mascot(cv, 560, 1750, 0.9, light_side=-1, rim=LAMP, rim_a=0.5, look=(0.0, 0.2), brow=0.6, mouth='frown', **GMA)
    dw = (dx1 - dx0) * (1 - opened * 0.85)
    cv.drawRect(skia.Rect(dx0, 300, dx0 + dw, 1600), paint('#4A3020'))
    if opened < 0.1:
        for r in range(3):
            cv.drawRect(skia.Rect(dx0 + 60, 420 + r * 380, dx1 - 60, 700 + r * 380), paint('#3E281A', style='stroke', width=10))
        cv.drawCircle(540, 820, 70, paint('#15100C'))                                              # peephole + the eye inside
        cv.save(); cv.clipPath(skia.Path.Circle(540, 820, 56), skia.ClipOp.kIntersect, True)
        cv.drawRect(skia.Rect(470, 750, 610, 890), paint('#E8E0D0'))
        look = 0.25 * math.sin(t * 1.3)
        cv.drawCircle(540 + 18 * look, 822, 28, paint('#5A6E7A'))
        cv.drawCircle(540 + 18 * look, 822, 13, paint('#0A0A0A'))
        lid = 1.0 if (B['door'] <= t and abs(t - B['blinkyou']) < 0.12) else 0.0
        cv.drawRect(skia.Rect(470, 750, 610, 750 + 140 * lid), paint('#C9A084'))
        cv.restore()
        cv.drawCircle(700, 1000, 22, paint('#B9A27A'))
    glow(cv, (540, 230), 300, LAMP, 0.5)                                                           # porch light
    cv.drawRect(skia.Rect(500, 210, 580, 250), paint('#FFE2A8'))
    cv.drawRect(skia.Rect(0, 1600, W, H), paint('#2A2622'))
    o = mascot(cv, 320, 2550, 1.2, view='back', light_side=1, rim=LAMP, rim_a=0.5, arm_r=(20, 10))   # you, soaked, with the sack
    hx, hy = o['hand_r']
    sack(cv, hx, hy, 1.2)
    rain(cv, t)
    shade(cv, (540, 900), 1150, 0.55)


def street(cv, t, scroll):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#070A10', shader=lin((0, 0), (0, 1500), [C('#05070C'), C('#141A26')])))
    for k in range(-1, 6):                                                                       # houses, dark
        x = ((k * 330 - scroll) % 2000) - 300
        cv.drawRect(skia.Rect(x, 700, x + 300, 1500), paint('#0E1218'))
        cv.drawPath(poly([(x - 20, 700), (x + 150, 540), (x + 320, 700)]), paint('#0A0D12'))
        cv.drawRect(skia.Rect(x + 60, 860, x + 130, 960), paint('#151B24'))
        cv.drawRect(skia.Rect(x + 170, 860, x + 240, 960), paint('#151B24'))
    for k in range(4):
        x = ((k * 520 - scroll * 1.2) % 2100) - 300
        cv.drawRect(skia.Rect(x, 820, x + 14, 1500), paint('#1A1E26'))
        glow(cv, (x + 7, 830), 160, '#FFE6B0', 0.3)
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#141820'))
    for k in range(8):                                                                            # wet reflections
        x = ((k * 260 - scroll * 1.5) % 2100) - 300
        cv.drawRect(skia.Rect(x, 1560, x + 90, 1580), paint(C('#FFE6B0', 0.12)))


def shot_RUN(cv, t):
    u = t - B['card']
    street(cv, t, u * 700)
    o = mascot(cv, 520, 1760, 0.62, view='side', face=1, walk=(t * 2.6) % 1, run=True, arm_r=(35, 70), brow=1.0, mouth='open', mouth_open=0.4, sweat=True,
           light_side=1, rim=MOON, rim_a=0.5)
    hx, hy = o['hand_r']
    sack(cv, hx, hy, 0.55, swing=12 * math.sin(t * 2.6 * 2 * math.pi))
    rain(cv, t)
    shade(cv, (540, 1100), 1250, 0.5)


def shot_FRONT(cv, t):
    """Running straight at camera down the wet street; far behind, something on all fours keeps pace."""
    cam = Cam(0.0, eye=1.3, vy=900)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#070A10'))
    cv.drawPath(quad(cam, [(-3, 0, 1), (3, 0, 1), (3, 0, 40), (-3, 0, 40)]), paint('#141820'))
    for side in (-1, 1):
        for k in range(6):
            z = max(0.5, 4 + k * 5 - (t * 6) % 5)
            p0, p1 = cam.p(side * 4, 0, z), cam.p(side * 4, 4.5, z)
            cv.drawRect(skia.Rect(min(p0[0], p1[0]) - 120 / z * 10, p1[1], max(p0[0], p1[0]) + 120 / z * 10, p0[1]), paint('#0E1218'))
    far = cam.p(0.2, 0, 22)
    A.crawler(cv, far[0], far[1], 0.08, t)
    o = mascot(cv, 540, 1900, 0.9, walk=(t * 2.6) % 1, run=True, arm_r=(22, 15), brow=1.0, mouth='open', mouth_open=0.4, pupil=0.6, sweat=True, light_side=1,
           rim=MOON, rim_a=0.5)
    hx, hy = o['hand_r']
    sack(cv, hx, hy, 0.8, swing=8 * math.sin(t * 2.6 * 2 * math.pi))
    rain(cv, t)
    shade(cv, (540, 1000), 1200, 0.5)


def shot_YOUFACE(cv, t):
    """Your own voice behind you says 'Don't let her in.' Your mouth never moves."""
    street(cv, t, t * 200)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.4)))
    mascot(cv, 540, 2700, 1.95, look=(-0.7, 0.0), head_turn=-0.3, brow=1.0, mouth='flat', pupil=0.5, sweat=True, light_side=1, rim=MOON, rim_a=0.6)
    rain(cv, t, 40, 0.25)
    shade(cv, (540, 950), 1100, 0.6)


def shot_ROOF(cv, t):
    """Lightning: rooftops against a white sky — and it, on the nearest roof edge, keeping up."""
    u = t - B['lightning']
    strike = (u < 0.12) or (0.22 < u < 0.3)
    sky = '#D8E2F0' if strike else '#0A0E16'
    cv.drawRect(skia.Rect(0, 0, W, H), paint(sky))
    for k in range(5):
        x = k * 260 - 60
        cv.drawPath(poly([(x, 1300), (x + 130, 1050 - (k % 2) * 80), (x + 260, 1300)]), paint('#05070A'))
        cv.drawRect(skia.Rect(x, 1300, x + 260, H), paint('#05070A'))
    if strike or u < 0.6:
        A.crawler(cv, 700, 980, 0.75, t)
    else:
        A.crawler(cv, 700 + (u - 0.6) * 300, 980, 0.75, t)
    rain(cv, t, 50, 0.3 if not strike else 0.6)
    if not strike:
        shade(cv, (540, 900), 1100, 0.5)


# ---------------------------------------------------------------- Grandma's
def kitchen(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2018'))
    cv.drawRect(skia.Rect(0, 0, W, 1300), paint('#5A4A3A', shader=lin((0, 0), (0, 1300), [C('#3E3226'), C('#6A5642')])))
    for x in range(0, W, 120):                                                                   # old floral wallpaper
        for y in range(80, 1300, 160):
            cv.drawCircle(x + (60 if (y // 160) % 2 else 0), y, 16, paint(C('#7A6450', 0.6)))
    cv.drawRect(skia.Rect(700, 300, 1000, 700), paint('#0E1626'))                                  # window with the storm
    flash_ = int(t * 1.3) % 7 == 0
    cv.drawRect(skia.Rect(710, 310, 990, 690), paint('#C8D4E8' if flash_ else '#0E1626'))
    for x in (700, 850, 1000):
        cv.drawRect(skia.Rect(x - 8, 300, x + 8, 700), paint('#3A2E22'))
    cv.drawLine(540, 0, 540, 220, paint('#1A1410', style='stroke', width=6))
    cv.drawPath(poly([(440, 220), (640, 220), (690, 300), (390, 300)]), paint('#C99A4E'))
    glow(cv, (540, 330), 1000, LAMP, 0.35)
    rain(cv, t, 20, 0.15)


def shot_KITCHEN(cv, t):
    kitchen(cv, t)
    pale = t >= B['pale']
    mascot(cv, 380, 1760, 0.8, legs=False, light_side=1, rim=LAMP, rim_a=0.4, look=(0.2, 0.8), brow=1.0 if pale else 0.4,
           mouth='o' if pale else 'flat', mouth_open=talk(t, 'G2') * 0.6, arm_l=(30, -100), arm_r=(30, -100), **GMA)
    mascot(cv, 860, 1840, 0.7, legs=False, light_side=-1, rim=LAMP, rim_a=0.4, look=(-0.6, 0.6), brow=1.0, mouth='o', sweat=True)
    cv.drawRect(skia.Rect(0, 1380, W, 1460), paint('#6A4A2E'))
    cv.drawRect(skia.Rect(0, 1460, W, H), paint('#3A2A1C'))
    for k in range(23):                                                                          # the pieces laid out
        a = k * 0.27
        x, y = 540 + math.cos(a) * 200, 1410 + math.sin(a) * 30 - 10
        cv.drawPath(poly([(x - 20, y), (x, y - 16), (x + 18, y + 4)]), paint('#EEF0F2' if k % 3 else '#2A4A9A'))
    shade(cv, (540, 1000), 1200, 0.5)


def shot_GMA(cv, t):
    kitchen(cv, t)
    m = talk(t, 'G3', 'G4', 'G5')
    scared = t >= B['n13'] - 0.2
    mascot(cv, 540, 2700, 1.95, light_side=1, rim=LAMP if not scared else MOON, rim_a=0.5, look=(0.0, 0.0) if not scared else (-0.7, 0.0),
           brow=1.0 if (scared or t < B['g4']) else 0.5, mouth='open' if m > 0 else ('o' if scared else 'frown'), mouth_open=m * 0.7,
           pupil=0.6 if scared else 0.9, sweat=scared, lids=0.2 if (B['g4'] <= t < B['knock'] and not scared) else 0.0, **GMA)
    shade(cv, (540, 950), 1100, 0.55)


def shot_TABLE(cv, t):
    """Top-down: twenty-three pieces fitted together into the vase... and a face-shaped hole."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A2A1C'))
    for k in range(9):
        cv.drawLine(0, 140 + k * 220, W, 120 + k * 220, paint(C('#2A1C12', 0.8), style='stroke', width=6))
    v = blob([(380, 1550), (300, 1200), (330, 760), (400, 480), (680, 480), (750, 760), (780, 1200), (700, 1550)])
    cv.drawPath(v, paint('#EEF0F2'))
    cv.save(); cv.clipPath(v, skia.ClipOp.kIntersect, True)
    for k in range(6):
        cv.drawPath(skia.Path().addArc(skia.Rect(260 + k * 30, 520 + k * 160, 640 + k * 30, 760 + k * 160), 200, 160),
                    paint('#2A4A9A', style='stroke', width=10))
    for k in range(12):                                                                            # crack lines between the pieces
        y = 540 + k * 85
        cv.drawLine(300, y + (k % 3) * 20, 780, y - (k % 2) * 30, paint('#3A3A40', style='stroke', width=4))
    hole = blob([(430, 900), (540, 820), (650, 900), (630, 1060), (540, 1110), (450, 1060)])
    cv.drawPath(hole, paint('#3A2A1C'))                                                              # the missing face piece
    cv.restore()
    a = ease((t - B['missing'] - 0.6) / 0.3)
    cv.drawPath(hole, paint(C('#C8202A', 0.8 * a), style='stroke', width=8))
    text(cv, '23 / 24', 540, 1760, 90, C('#C8202A', a))
    glow(cv, (540, 1000), 900, LAMP, 0.15)
    shade(cv, (540, 1000), 1050, 0.65)


# ---------------------------------------------------------------- 1968 (lore flashback, faded)
def old_house(cv, t):
    A.living_room(cv, t, lamp=0.6)


def shot_F_TWINS(cv, t):
    """1968, the same living room: Rose and her twin Eli. Eli has stopped blinking; he stares at the crack in the wall."""
    old_house(cv, t)
    cv.drawPath(poly([(900, 1300), (920, 1150), (905, 1000), (930, 860), (915, 700)], closed=False), paint('#1A1410', style='stroke', width=10))
    mascot(cv, 330, 1880, 0.62, look=(0.8, 0.0), brow=1.0, mouth='o', light_side=1, rim=LAMP, rim_a=0.4, **ROSE)
    mascot(cv, 700, 1880, 0.62, look=(0.9, -0.2), head_turn=0.4, brow=0.0, lids=0.0, pupil=0.45, mouth='flat', light_side=1, rim=LAMP,
           rim_a=0.4, **ELI)
    shade(cv, (540, 1100), 1150, 0.6)


def shot_F_PAINT(cv, t):
    """Their mother paints every room of the house onto the vase."""
    old_house(cv, t)
    cv.drawRect(skia.Rect(0, 1380, W, 1460), paint('#6A4A2E'))
    mascot(cv, 330, 1800, 0.7, legs=False, look=(0.8, 0.6), brow=-0.2, lids=0.3, mouth='flat', arm_r=(50, -80), light_side=1, rim=LAMP, rim_a=0.4,
           item='pen', **MOTHER)
    cv.save(); cv.translate(760, 1380)
    v = blob([(-60, 0), (-110, -160), (-80, -330), (-50, -400), (50, -400), (80, -330), (110, -160), (60, 0)])
    cv.drawPath(v, paint('#EEF0F2'))
    cv.save(); cv.clipPath(v, skia.ClipOp.kIntersect, True)
    rooms = int(min(6, (t - B['mother']) * 3))
    for k in range(rooms):                                                                         # little painted rooms: doors, windows
        y = -360 + k * 60
        cv.drawRect(skia.Rect(-70, y, -20, y + 40), paint('#2A4A9A', style='stroke', width=5))
        cv.drawRect(skia.Rect(10, y + 5, 60, y + 40), paint('#2A4A9A', style='stroke', width=5))
    cv.restore(); cv.restore()
    cv.drawRect(skia.Rect(0, 1460, W, H), paint('#3A2A1C'))
    shade(cv, (600, 1100), 1150, 0.6)


def shot_F_SEAL(cv, t):
    """Black wax pressed onto the vase's mouth; the last of the smoke curling in."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A1410'))
    v = blob([(300, 1900), (220, 1300), (330, 820), (420, 620), (660, 620), (750, 820), (860, 1300), (780, 1900)])
    cv.drawPath(v, paint('#EEF0F2'))
    cv.save(); cv.clipPath(v, skia.ClipOp.kIntersect, True)
    for k in range(7):                                                                             # the painted rooms
        y = 860 + k * 150
        for x in (320, 470, 620):
            cv.drawRect(skia.Rect(x, y, x + 100, y + 90), paint('#2A4A9A', style='stroke', width=8))
    cv.restore()
    u = t - B['so']
    for k in range(6):                                                                             # smoke being sucked in
        a = k * 1.05 + u * 2
        r = max(0.0, 300 - u * 160)
        cv.drawOval(skia.Rect(540 + math.cos(a) * r - 90, 560 + math.sin(a) * r * 0.5 - 50, 540 + math.cos(a) * r + 90, 560 + math.sin(a) * r * 0.5 + 50),
                    paint(C('#050506', 0.7), blur=20))
    press = ease((u - 0.6) / 0.5)
    if press > 0:
        cv.drawOval(skia.Rect(420, 540 - 60 * (1 - press), 660, 680), paint('#0A0A0C'))              # the wax seal
        for side in (-1, 1):                                                                       # hands pressing
            cv.drawPath(blob([(540 + side * 160, 420 + 80 * press), (540 + side * 40, 450 + 80 * press), (540 + side * 60, 560), (540 + side * 200, 540)]),
                        paint('#EBC6A8'))
    glow(cv, (540, 700), 800, LAMP, 0.2)
    shade(cv, (540, 900), 1100, 0.6)


def hallway(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A1410'))
    cv.drawRect(skia.Rect(0, 0, W, 1600), paint('#3E3226'))
    for x in range(0, W, 120):
        for y in range(80, 1600, 160):
            cv.drawCircle(x + (60 if (y // 160) % 2 else 0), y, 16, paint(C('#4E4030', 0.7)))
    jolt = 0
    for k in range(3):
        k0 = B['knock'] + 0.9 + k * 0.6
        if k0 <= t < k0 + 0.12:
            jolt = 8
    if t >= B['js2'] + 0.55:                                                                       # after the scare: knocking continues, harder
        if int((t - B['js2']) * 2.2) % 2 == 0 and (t * 10) % 5 < 1:
            jolt = 10
    cv.drawRect(skia.Rect(320 + jolt, 300, 760 + jolt, 1600), paint('#4A3020'))
    cv.drawCircle(540 + jolt, 760, 22, paint('#15100C'))
    cv.drawCircle(700 + jolt, 1000, 22, paint('#B9A27A'))
    cv.drawRect(skia.Rect(330, 1590, 750, 1605), paint('#FFE2A8'))                                  # porch light under the door
    if t >= B['e1'] - 0.4:                                                                        # small feet
        for x in (480, 570):
            cv.drawRect(skia.Rect(x, 1590, x + 40, 1605), paint('#000000'))
    cv.drawRect(skia.Rect(0, 1600, W, H), paint('#2A2018'))


def shot_HALL(cv, t):
    hallway(cv, t)
    late = t >= B['js2']
    mascot(cv, 230, 2350, 1.05, view='back', light_side=1, rim=LAMP, rim_a=0.4, **GMA)
    mascot(cv, 860, 2450, 1.05, view='back', light_side=-1, rim=LAMP, rim_a=0.4)
    if late:                                                                                       # escalation under the choice
        turn = (t - B['js2'] - 0.55) * 8
        cv.save(); cv.translate(700, 1000); cv.rotate(-min(60.0, turn))
        cv.drawRect(skia.Rect(-10, -10, 80, 10), paint('#B9A27A'))
        cv.restore()
        n = int((t - B['js2']) / 1.5)
        for k in range(min(n, 5)):
            cv.drawCircle(80 + (k * 53) % 140, 500 + k * 170, 7, paint('#FF2A1A'))
            cv.drawCircle(116 + (k * 53) % 140, 500 + k * 170, 7, paint('#FF2A1A'))
    shade(cv, (540, 1000), 1150, 0.55)


def shot_PEEP(cv, t):
    """Through the peephole (fisheye): a twelve-year-old's porcelain face, pressed right against the glass."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000'))
    cv.save(); cv.clipPath(skia.Path.Circle(540, 900, 470), skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2420'))
    glow(cv, (540, 400), 600, LAMP, 0.4)
    u = t - B['js2']
    for k in range(6):                                                                             # boy's hair (smoke-black)
        a = k * 1.0
        cv.drawOval(skia.Rect(540 + math.cos(a) * 200 - 180, 700 + math.sin(a) * 120 - 160, 540 + math.cos(a) * 200 + 180, 700 + math.sin(a) * 120 + 60),
                    paint('#2E1A10', blur=18))
    A.porcelain_face(cv, 540, 950, 1.7 + u * 1.2, jaw=min(1.0, 0.2 + u * 2), tilt=-10)
    cv.restore()
    cv.drawCircle(540, 900, 470, paint('#000000', style='stroke', width=60, blur=20))


def shot_SCARE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000'))
    u = t - B['js3']
    A.porcelain_face(cv, 540, 980, 1.6 + u * 2.4, jaw=min(1.0, 0.3 + u * 2), tilt=-8 + 20 * u)
    glow(cv, (540, 900), 900, '#FF2A1A', 0.12)


SHOTS = {'PEEPOUT': shot_PEEPOUT, 'R_VASE': shot_R_VASE, 'R_MOM': shot_R_MOM, 'R_DAD': shot_R_DAD, 'R_MIRROR': shot_R_MIRROR,
         'RUN': shot_RUN, 'FRONT': shot_FRONT, 'YOUFACE': shot_YOUFACE, 'ROOF': shot_ROOF, 'KITCHEN': shot_KITCHEN, 'GMA': shot_GMA,
         'TABLE': shot_TABLE, 'F_TWINS': shot_F_TWINS, 'F_PAINT': shot_F_PAINT, 'F_SEAL': shot_F_SEAL, 'HALL': shot_HALL, 'PEEP': shot_PEEP,
         'SCARE': shot_SCARE}


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
