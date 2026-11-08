#!/usr/bin/env python3
"""VIDEO_012 "Don't Touch The Vase · Part 1" — real 2D horror (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_012/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
import edit_video012 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
LAMP = '#FFC88A'
MOON = '#9FB8D8'
PHONE = '#E8F2FF'

MOM = dict(long_hair=True, hair='#5A3A1A', hair_sh='#3A2410', shirt='#7A4FA0', shirt_sh='#5C3A7A', skin='#F5D0B0', skin_sh='#D9AE8C')
DAD = dict(hair='#2A1A10', hair_sh='#1A100A', shirt='#3A6EB0', shirt_sh='#2C5486', mustache='#2A1A10', belly=1.2, glasses='#22262C')
SIS = dict(long_hair=True, hair='#C26A2A', hair_sh='#9A521E', shirt='#E07AA0', shirt_sh='#B85C80')


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


# ===================================================================== the thing from the vase
def porcelain_face(cv, cx, cy, s, jaw=0.6, glow_eyes=1.0, tilt=0.0):
    """Cracked white porcelain face (blue vase painting on it), hollow black eyes with red pinpoints, a mouth that opens too far."""
    cv.save(); cv.translate(cx, cy); cv.rotate(tilt); cv.scale(s, s)
    for k in range(10):                                                      # black smoke hair
        a = k * 0.62
        cv.drawOval(skia.Rect(math.cos(a) * 180 - 160, math.sin(a) * 160 - 260, math.cos(a) * 180 + 160, math.sin(a) * 160 + 40),
                    paint(C('#050506', 0.85), blur=30))
    face = blob([(-170, -60), (-150, -230), (0, -290), (150, -230), (170, -60), (130, 150), (0, 230 + 160 * jaw), (-130, 150)])
    cv.drawPath(face, paint('#E8EAEC'))
    cv.save(); cv.clipPath(face, skia.ClipOp.kIntersect, True)
    cv.drawOval(skia.Rect(-260, -320, -60, 320), paint(C('#AEB6C0', 0.9), blur=30))
    for k in range(4):                                                       # blue vase painting
        cv.drawPath(skia.Path().addArc(skia.Rect(-120 + k * 50, -250 + k * 30, 40 + k * 50, -90 + k * 30), 200, 160),
                    paint(C('#2A4A9A', 0.7), style='stroke', width=8))
    for pts in (((-20, -290), (10, -180), (-30, -90), (20, 20)), ((150, -100), (90, -60), (110, 40)), ((-160, 40), (-90, 70), (-110, 150))):
        cv.drawPath(poly(pts, closed=False), paint('#3A3A40', style='stroke', width=6))
    cv.restore()
    for side in (-1, 1):
        ex, ey = side * 70, -90
        cv.drawPath(blob([(ex - 50, ey), (ex, ey - 46), (ex + 50, ey), (ex + 6, ey + 70)]), paint('#000000'))
        if glow_eyes > 0:
            cv.drawCircle(ex, ey + 10, 9, paint(C('#FF2A1A', glow_eyes)))
            cv.drawCircle(ex, ey + 10, 30, paint(C('#FF2A1A', 0.35 * glow_eyes), blur=12))
    mouth = blob([(-110, 60), (0, 40), (110, 60), (70, 60 + 170 * jaw), (0, 80 + 210 * jaw), (-70, 60 + 170 * jaw)])
    cv.drawPath(mouth, paint('#000000'))
    for k in range(9):
        tx = -96 + k * 24
        cv.drawPath(poly([(tx, 52), (tx + 12, 52 + 50 + 20 * jaw), (tx + 24, 52)]), paint('#D8D2C0'))
        cv.drawPath(poly([(tx, 70 + 180 * jaw), (tx + 12, 30 + 150 * jaw), (tx + 24, 70 + 180 * jaw)]), paint('#D8D2C0'))
    cv.restore()


def crawler(cv, x, y, s, t, face_up=1.0):
    """The thing on all fours on the stairs: long black limbs, porcelain face tilted up at you."""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    for side in (-1, 1):
        ph = math.sin(t * 5 + (0 if side < 0 else math.pi))
        _limbs = [(side * 120, -200), (side * (320 + 40 * ph), -360), (side * (420 + 30 * ph), -60), (side * (460 + 30 * ph), 0)]
        cv.drawPath(poly(_limbs, closed=False), paint('#050506', style='stroke', width=34))
        _legs = [(side * 90, 60), (side * (300 - 30 * ph), 180), (side * (360 - 30 * ph), 420)]
        cv.drawPath(poly(_legs, closed=False), paint('#050506', style='stroke', width=40))
        for f in range(4):
            cv.drawLine(side * (460 + 30 * ph), 0, side * (460 + 30 * ph) + side * (f * 16 - 20), 70, paint('#050506', style='stroke', width=10))
    cv.drawOval(skia.Rect(-170, -260, 170, 160), paint('#050506'))
    cv.restore()
    porcelain_face(cv, x, y - 260 * s, 0.75 * s, jaw=0.2 + 0.2 * face_up, glow_eyes=1.0, tilt=12 * math.sin(t * 2))


# ===================================================================== sets
def living_room(cv, t, lamp=1.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2420'))
    cv.drawRect(skia.Rect(0, 0, W, 1400), paint('#4A3A30', shader=lin((0, 0), (0, 1400), [C('#3A2E26'), C('#5A483A')])))
    for x in range(0, W, 90):
        cv.drawRect(skia.Rect(x, 0, x + 6, 1400), paint(C('#3E3028', 0.6)))
    cv.drawRect(skia.Rect(0, 1400, W, H), paint('#3A2A20'))
    cv.drawRect(skia.Rect(80, 380, 420, 760), paint('#2A2420'))                                  # an old portrait (grandpa)
    cv.drawRect(skia.Rect(100, 400, 400, 740), paint('#6A5A48'))
    cv.save(); cv.clipRect(skia.Rect(100, 400, 400, 740))
    mascot(cv, 250, 1080, 0.36, mustache='#BDBDBD', hair='#BDBDBD', hair_sh='#9A9A9A', shirt='#2A2A2A', shirt_sh='#1A1A1A', mouth='frown')
    cv.restore()
    glow(cv, (850, 300), 900, LAMP, 0.3 * lamp)


def shelf_vase(cv, t):
    """The shelf and the vase. Frame 0: it is already rocking on the edge; it falls and shatters on 'broke'."""
    cv.drawRect(skia.Rect(430, 1030, 1080, 1070), paint('#5A3A22'))
    fall = max(0.0, t - (B['crash'] - 0.45))
    if t < B['crash']:
        rock = 9 * math.sin(t * 7) * (0.6 + 0.4 * min(1.0, t / 1.5)) if fall <= 0 else 9 + fall * 140
        vx, vy = 760 + (fall * 80 if fall > 0 else 0), 1030 + (fall * fall * 2600 if fall > 0 else 0)
        cv.save(); cv.translate(vx, vy); cv.rotate(rock)
        v = blob([(-60, 0), (-110, -160), (-80, -330), (-50, -400), (50, -400), (80, -330), (110, -160), (60, 0)])
        cv.drawPath(v, paint('#EEF0F2'))
        cv.save(); cv.clipPath(v, skia.ClipOp.kIntersect, True)
        for k in range(5):
            cv.drawPath(skia.Path().addArc(skia.Rect(-120 + k * 30, -330 + k * 50, 60 + k * 30, -200 + k * 50), 200, 170),
                        paint('#2A4A9A', style='stroke', width=10))
        cv.drawRect(skia.Rect(-120, -60, 120, -40), paint('#2A4A9A'))
        cv.drawRect(skia.Rect(-120, -360, 120, -350), paint('#2A4A9A'))
        cv.drawOval(skia.Rect(-200, -420, -40, 20), paint(C('#9AA2AC', 0.6), blur=20))
        cv.restore()
        cv.drawRect(skia.Rect(-26, -432, 26, -400), paint('#1A1A1E'))                         # wax seal
        cv.restore()
    else:                                                                                       # shards + black smoke
        u = t - B['crash']
        for k in range(18):
            a = k * 2.1
            r = min(1.0, u * 3) * (80 + (k % 5) * 70)
            x, y = 760 + math.cos(a) * r * 1.6, 1700 + math.sin(a) * r * 0.25
            cv.save(); cv.rotate(k * 37 + u * 40 * (1 - min(1, u)), x, y)
            cv.drawPath(poly([(x - 34, y), (x, y - 26 - k % 3 * 10), (x + 30, y + 6)]), paint('#EEF0F2' if k % 3 else '#2A4A9A'))
            cv.restore()


def shot_VASE(cv, t):
    living_room(cv, t)
    shelf_vase(cv, t)
    # you: backing into the shelf, phone up (side view, facing away from the shelf)
    turned = t >= B['crash'] - 0.3
    mascot(cv, 420, 1880, 0.95, view='side', face=-1 if not turned else 1, arm_r=(80, 40) if not turned else (60, 60),
           item=None, look=(0.6 if turned else 0.0, 0.4), brow=1.0 if turned else 0.0, mouth='o' if turned else 'smile', light_side=1,
           rim=LAMP, rim_a=0.5)
    if t >= B['crash']:
        u = t - B['crash']
        for k in range(7):                                                                      # smoke rising
            cv.drawOval(skia.Rect(700 + 40 * math.sin(u * 3 + k) - 120, 1650 - u * 300 - k * 60, 820 + 40 * math.sin(u * 3 + k) + 120,
                                  1800 - u * 300 - k * 60), paint(C('#050506', 0.6), blur=30))
    shade(cv, (700, 1200), 1200, 0.6)


def shot_SCARE(cv, t):
    """Full-frame face: the 3-frame subliminal flash and the final lunge."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000'))
    if t < B['dinner']:
        porcelain_face(cv, 540, 900, 2.4, jaw=0.4)
    else:
        u = t - B['js3']
        porcelain_face(cv, 540, 980, 1.6 + u * 2.4, jaw=min(1.0, 0.3 + u * 2), tilt=-8 + 20 * u)
    glow(cv, (540, 900), 900, '#FF2A1A', 0.12)


def shot_SMOKE(cv, t):
    """Shards on the floor; the black thing crawls off the floor and slides into a crack in the wall."""
    living_room(cv, t, lamp=0.7)
    cv.drawRect(skia.Rect(0, 1300, W, H), paint('#3A2A20'))
    u = t - B['smoke']
    for k in range(18):
        a = k * 2.1
        x, y = 400 + math.cos(a) * (60 + k % 5 * 60) * 1.6, 1650 + math.sin(a) * (60 + k % 5 * 60) * 0.25
        cv.drawPath(poly([(x - 34, y), (x, y - 26 - k % 3 * 10), (x + 30, y + 6)]), paint('#EEF0F2' if k % 3 else '#2A4A9A'))
    cv.drawPath(poly([(900, 1300), (920, 1150), (905, 1000), (930, 860), (915, 700)], closed=False), paint('#1A1410', style='stroke', width=10))  # wall crack
    for k in range(9):                                                                          # the tendril
        v = min(1.0, max(0.0, u * 0.4 - k * 0.03))
        x = 400 + (910 - 400) * v + 30 * math.sin(u * 4 + k)
        y = 1650 - (1650 - (1250 - k * 40)) * v
        cv.drawOval(skia.Rect(x - 70 + k * 4, y - 40, x + 70 - k * 4, y + 40), paint(C('#030304', 0.85), blur=16))
    if u > 1.2:                                                                                 # the crack glows red as it slips in
        glow(cv, (912, 1000), 260, '#FF2A1A', 0.25 * min(1.0, (u - 1.2)))
    shade(cv, (600, 1200), 1150, 0.6)


def dining(cv, t, lamp=1.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A2018'))
    cv.drawRect(skia.Rect(0, 0, W, 1250), paint('#4A3A2E', shader=lin((0, 0), (0, 1250), [C('#3A2C22'), C('#544232')])))
    cv.drawLine(540, 0, 540, 260, paint('#1A1410', style='stroke', width=6))
    cv.drawPath(poly([(430, 260), (650, 260), (700, 340), (380, 340)]), paint('#C99A4E'))
    glow(cv, (540, 360), 1000, LAMP, 0.35 * lamp)


def table_front(cv):
    cv.drawRect(skia.Rect(0, 1380, W, 1460), paint('#6A4A2E'))
    cv.drawRect(skia.Rect(0, 1460, W, H), paint('#3A2A1C'))
    for x in (220, 540, 860):
        cv.drawOval(skia.Rect(x - 110, 1360, x + 110, 1410), paint('#EDE6D6'))


def shot_DINNER(cv, t):
    dining(cv, t)
    after = t >= B['js1']
    for x, who, pose in ((220, MOM, dict(mouth='smile', look=(0.2, 0.6))), (540, DAD, dict(mouth='flat', look=(0.0, 0.8), head_tilt=6)),
                         (860, SIS, dict(mouth='flat', look=(-0.2, 0.7)))):
        sc = 0.62 if who is not SIS else 0.5
        mascot(cv, x, 1720 if who is not SIS else 1640, sc, legs=False, light_side=1, rim=LAMP, rim_a=0.3,
               arm_l=(30, -100), arm_r=(30, -100), **dict(who, **pose))
    table_front(cv)
    mascot(cv, 540, 2700, 1.1, view='back', light_side=1, rim=LAMP, rim_a=0.4)                 # you, foreground
    if after:
        shade(cv, (540, 900), 1100, 0.65)
    else:
        shade(cv, (540, 900), 1250, 0.5)


def shot_MOM(cv, t):
    dining(cv, t)
    u = t - B['mom']
    mascot(cv, 540, 2700, 1.95, light_side=1, rim=LAMP, rim_a=0.4, look=(0.0, 0.0), pupil=0.75, lids=0.0,
           mouth='smile' if u < 1.6 else 'wide', head_tilt=min(10.0, u * 4), **MOM)
    shade(cv, (540, 950), 1100, 0.55)


def shot_SISTER(cv, t):
    dining(cv, t)
    if t < B['dad'] - 0.8:                                                                      # chewing at an empty plate
        chew = abs(math.sin(t * 7))
        mascot(cv, 540, 2600, 1.5, light_side=1, rim=LAMP, rim_a=0.4, look=(0.0, 0.9), mouth='o', mouth_open=0.2 + 0.5 * chew,
               arm_r=(40, -110), **SIS)
    else:
        cv.drawRect(skia.Rect(0, 1000, W, H), paint('#6A4A2E'))
    cv.drawOval(skia.Rect(200, 1450, 880, 1700), paint('#EDE6D6'))                              # the empty plate
    cv.drawOval(skia.Rect(290, 1490, 790, 1660), paint('#D8D0BE'))
    fx_ = 600 + 120 * math.sin(t * 3)
    cv.drawLine(fx_, 1580, fx_ + 140, 1380, paint('#B8BEC6', style='stroke', width=14))         # fork scraping
    shade(cv, (540, 1100), 1100, 0.55)


def shot_DAD(cv, t):
    dining(cv, t, lamp=0.85)
    up = keys(t, [(B['dad'], 0.0), (B['d1'], 1.0)])
    if t < B['js1']:
        mascot(cv, 540, 2700, 1.95, light_side=1, rim=LAMP, rim_a=0.4, look=(0.0, 0.9 - 0.9 * up), head_tilt=14 * (1 - up), pupil=0.7,
               mouth='flat' if talk(t, 'D1') == 0 else 'o', mouth_open=talk(t, 'D1') * 0.5, brow=-0.3, **DAD)
    else:                                                                                       # JUMPSCARE 1
        u = t - B['js1']
        mascot(cv, 540, 2700 + 300 * u, 1.95 + 1.6 * u, light_side=1, rim='#FF2A1A', rim_a=0.8, void_eyes=True, stretch=0.35 + u,
               mouth='open', mouth_open=1.0, **dict(DAD, glasses=None))
    shade(cv, (540, 950), 1100, 0.6)


def bedroom(cv, t, phone_light=True, lamp=0.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#08090C'))
    cv.drawRect(skia.Rect(620, 300, 1000, 800), paint('#0E1626'))                                 # window
    glow(cv, (810, 550), 300, MOON, 0.25)
    for x in (620, 810, 1000):
        cv.drawRect(skia.Rect(x - 8, 300, x + 8, 800), paint('#1A1E26'))
    cv.drawRect(skia.Rect(620, 542, 1000, 558), paint('#1A1E26'))
    cv.drawPath(poly([(620, 800), (1000, 800), (900, 1500), (360, 1500)]), paint(C(MOON, 0.07), blur=12))
    cv.drawRect(skia.Rect(0, 1400, 600, 1700), paint('#1A1E2A'))                                  # bed
    cv.drawRect(skia.Rect(0, 1320, 300, 1420), paint('#2A3040'))


def shot_ROOM(cv, t):
    """2:13 AM. The lamp clicks off — the whole house goes dark. Then your phone light."""
    bedroom(cv, t)
    lit = t < B['out']
    if lit:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C(LAMP, 0.12)))
        glow(cv, (160, 1200), 700, LAMP, 0.35)
    mascot(cv, 330, 1700, 0.75, legs=False, look=(0.6, -0.3) if not lit else (0.0, 0.6), brow=1.0 if not lit else 0.0, mouth='o' if not lit else 'flat',
           pupil=0.6, light_side=1, rim=MOON, rim_a=0.6)
    if not lit:
        dim(cv, keys(t, [(B['out'], 0.95), (B['out'] + 0.8, 0.95), (B['out'] + 1.1, 0.4)]))
        if t > B['out'] + 0.8:
            glow(cv, (450, 1250), 500, PHONE, 0.35)
    shade(cv, (540, 1000), 1100, 0.6)


def shot_PHONE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#050608'))
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(200, 260, 880, 1560), 60, 60)), paint('#101215'))
    cv.drawRect(skia.Rect(230, 330, 850, 1490), paint('#0E1218'))
    cv.drawRect(skia.Rect(560, 380, 820, 470), paint('#2A2E36', style='stroke', width=8))
    cv.drawRect(skia.Rect(568, 388, 568 + 252 * 0.04 * 4, 462), paint('#FF3B2F'))
    text(cv, '4%', 540, 445, 64, '#FF3B2F', align='right')
    text(cv, '2:13', 540, 760, 200, '#FFFFFF')
    text(cv, 'NO SERVICE', 540, 860, 50, '#8A8F98')
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(260, 960, 820, 1110), 30, 30)), paint('#1E2632'))
    text(cv, 'Mom: working late, home by 6am', 540, 1050, 38, '#FFFFFF', bold=False)
    glow(cv, (540, 800), 700, PHONE, 0.2)
    for side in (-1, 1):
        hx = 540 + side * 360
        cv.drawPath(blob([(hx - 70, 1200), (hx + 70, 1180), (hx + 90, 1440), (hx - 60, 1500)]), paint('#F2C29B'))
        cv.drawPath(poly([(hx - 80, 1440), (hx + 100, 1420), (hx + 160, H), (hx - 140, H)]), paint('#F07A1A' if side > 0 else '#C85A0C'))
    shade(cv, (540, 900), 1100, 0.5)


def stairs_view(cv, t, beam=1.0):
    """Top of the stairs, looking down into the dark; your phone light is the only light."""
    cam = Cam(0.0, eye=2.9, vy=560)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#050506'))
    for k in range(12):                                                                          # steps going down (away)
        z0, z1 = 0.6 + k * 0.32, 0.6 + (k + 1) * 0.32
        h = 2.5 - k * 0.2
        cv.drawPath(quad(cam, [(-0.6, h, z0), (0.6, h, z0), (0.6, h, z1), (-0.6, h, z1)]), paint('#2A2420' if k % 2 else '#241E1A'))
        cv.drawPath(quad(cam, [(-0.6, h, z1), (0.6, h, z1), (0.6, h - 0.2, z1), (-0.6, h - 0.2, z1)]), paint('#1A1410'))
    for x in (-0.6, 0.6):
        cv.drawPath(quad(cam, [(x, 0, 0.6), (x, 0, 5), (x, 3.5, 5), (x, 3.5, 0.6)]), paint('#15120F'))
    cv.drawPath(poly([(540, 1900), (300, 900), (780, 900)]), paint(C(PHONE, 0.12 * beam), blur=30))
    glow(cv, (540, 1100), 600, PHONE, 0.22 * beam)


def shot_HALL(cv, t):
    stairs_view(cv, t)
    shade(cv, (540, 1000), 1000, 0.6)


def shot_WINDOW(cv, t):
    """Out of the window: the driveway, in the rain. Lightning. No car."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#08090C'))
    strike = (B['car'] - 0.1 <= t < B['car'] + 0.05) or (B['car'] + 0.2 <= t < B['car'] + 0.28)
    sky = '#C8D4E8' if strike else '#0E1626'
    cv.drawRect(skia.Rect(120, 260, 960, 1500), paint(sky))
    cv.drawRect(skia.Rect(120, 1000, 960, 1500), paint('#2A2E36' if strike else '#0A0C10'))
    cv.drawPath(poly([(420, 1500), (660, 1500), (600, 1000), (480, 1000)]), paint('#4A4E56' if strike else '#12141A'))
    text(cv, 'EMPTY', 540, 1300, 60, '#8A8F98' if strike else '#1A1E26')
    for k in range(40):                                                                          # rain
        x = (k * 97 + t * 900) % 840 + 120
        y = (k * 211 + t * 1800) % 1240 + 260
        cv.drawLine(x, y, x - 10, y + 50, paint(C('#9FB8D8', 0.35), style='stroke', width=3))
    for x in (120, 540, 960):
        cv.drawRect(skia.Rect(x - 12, 260, x + 12, 1500), paint('#1A1E26'))
    cv.drawRect(skia.Rect(120, 868, 960, 892), paint('#1A1E26'))
    shade(cv, (540, 900), 1000, 0.55)


def shot_STAIRS(cv, t):
    stairs_view(cv, t)
    u = t - B['stairs']
    z = max(1.2, 4.6 - u * 1.0)                                                                  # it climbs towards you
    cam = Cam(0.0, eye=2.9, vy=560)
    k = (z - 0.6) / 0.32
    h = 2.5 - k * 0.2
    p = cam.p(0.0, h, z)
    crawler(cv, p[0], p[1], 0.9 / z * 1.4, t)
    shade(cv, (540, 1000), 1000, 0.55)


def shot_BATH(cv, t):
    """Inside the bathroom: you lock the door. A shadow fills the gap under it. Then nothing."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0C0E10'))
    for r in range(14):
        for c_ in range(10):
            cv.drawRect(skia.Rect(c_ * 110 + 4, r * 110 + 4, c_ * 110 + 106, r * 110 + 106), paint('#1A1E22'))
    cv.drawRect(skia.Rect(260, 360, 820, 1700), paint('#3A2E24'))
    gap = '#E8F2FF' if t < B['lock'] + 1.0 else '#0A0A0A'
    cv.drawRect(skia.Rect(270, 1690, 810, 1710), paint(gap))
    if t >= B['lock'] + 1.0:                                                                     # it is right outside
        for x in (380, 560, 700):
            cv.drawRect(skia.Rect(x, 1690, x + 70, 1710), paint('#000000'))
    turn = keys(t, [(B['lock'] - 0.1, 0.0), (B['lock'] + 0.15, 90.0)])
    cv.save(); cv.translate(720, 1050); cv.rotate(turn)
    cv.drawRect(skia.Rect(-40, -12, 40, 12), paint('#B9A27A'))
    cv.restore()
    cv.drawCircle(720, 1050, 26, paint('#8E7A56'))
    glow(cv, (540, 1300), 700, PHONE, 0.2)
    shade(cv, (540, 1100), 1100, 0.6)


def shot_MIRROR(cv, t):
    """The mirror. Your reflection, lit by your phone from below. A beat. Then it is right behind you."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0C0E10'))
    cv.drawRect(skia.Rect(80, 260, 1000, 1500), paint('#15191E'))
    cv.save(); cv.clipRect(skia.Rect(100, 280, 980, 1480))
    cv.drawRect(skia.Rect(100, 280, 980, 1480), paint('#0A0C10'))
    if t >= B['js2']:
        porcelain_face(cv, 760, 760, 1.25 + (t - B['js2']) * 1.5, jaw=min(1.0, 0.4 + (t - B['js2']) * 2), tilt=14)
    mascot(cv, 470, 2300, 1.6, look=(0.0, -0.1), brow=1.0, mouth='o', pupil=0.6, sweat=True, light_side=1, rim=PHONE, rim_a=0.6)
    glow(cv, (470, 1500), 800, PHONE, 0.3)
    cv.restore()
    cv.drawRect(skia.Rect(80, 260, 1000, 1500), paint('#3A3E46', style='stroke', width=30))
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#D8D8D0'))                                       # sink
    shade(cv, (540, 900), 1000, 0.55)


def shot_BLACK(cv, t):
    """Phone dies. Darkness. At 'whispers', a faint profile of you — and, right beside your ear, two red points open."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000'))
    if t < B['dies'] + 0.3:
        cv.drawRect(skia.Rect(300, 600, 780, 1400), paint(C(PHONE, max(0.0, 0.3 - (t - B['dies']) * 1.0))))
    if t >= B['whisper']:
        a = min(1.0, (t - B['whisper']) / 1.0)
        cv.saveLayer(None, skia.Paint(Alphaf=0.35 * a))
        mascot(cv, 380, 2500, 1.6, view='side', face=1, look=(0.6, 0.0), brow=1.0, mouth='o', pupil=0.5, light_side=1, rim=MOON, rim_a=0.9)
        cv.restore()
        if t >= B['d3'] - 0.3:                                                                    # eyes beside your ear
            for side in (-1, 1):
                cv.drawCircle(160 + side * 50, 980, 9, paint('#FF2A1A'))
                cv.drawCircle(160 + side * 50, 980, 30, paint(C('#FF2A1A', 0.35), blur=12))
    shade(cv, (540, 1000), 1000, 0.4)


def shot_FLOOR(cv, t):
    """Your bedroom floor in the moonlight: the pieces of the vase (the choice). It keeps escalating so the card never sits still:
    the shards twitch, a shape rises outside the window, red eyes open in the dark corner one pair at a time."""
    bedroom(cv, t)
    u = t - B['choice']
    rise = min(1.0, u / 8.0)
    cv.save(); cv.clipRect(skia.Rect(620, 300, 1000, 800))                                       # a shape outside the window
    cv.drawPath(blob([(740, 820), (750, 820 - 420 * rise), (810, 760 - 460 * rise), (870, 820 - 420 * rise), (880, 820)]), paint(C('#020203', 0.9)))
    if u > 6.0:
        for side in (-1, 1):
            cv.drawCircle(810 + side * 22, 500 - 120 * rise + 160, 6, paint('#FF2A1A'))
    cv.restore()
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#14161C'))
    for k in range(16):
        a = k * 2.3
        jit = min(1.0, u / 6.0) * 6 * math.sin(t * 40 + k * 3)
        x, y = 540 + math.cos(a) * (60 + k % 5 * 60) * 1.4 + jit, 1700 + math.sin(a) * (40 + k % 5 * 40) * 0.4
        cv.drawPath(poly([(x - 34, y), (x, y - 26 - k % 3 * 10), (x + 30, y + 6)]), paint('#C8CCD2' if k % 3 else '#2A4A9A'))
    cv.drawPath(poly([(380, 1500), (700, 1500), (900, 1920), (180, 1920)]), paint(C(MOON, 0.08), blur=14))
    shade(cv, (540, 1300), 1100, 0.55)
    n = int(u / 1.4)                                                                              # eyes opening in the corner
    for k in range(min(n, 7)):
        x, y = 90 + (k * 37) % 160, 380 + k * 150
        cv.drawCircle(x - 18, y, 7, paint('#FF2A1A'))
        cv.drawCircle(x + 18, y, 7, paint('#FF2A1A'))
        cv.drawCircle(x, y, 40, paint(C('#FF2A1A', 0.15), blur=14))


SHOTS = {'VASE': shot_VASE, 'SCARE': shot_SCARE, 'SMOKE': shot_SMOKE, 'DINNER': shot_DINNER, 'MOM': shot_MOM, 'SISTER': shot_SISTER,
         'DAD': shot_DAD, 'ROOM': shot_ROOM, 'PHONE': shot_PHONE, 'HALL': shot_HALL, 'WINDOW': shot_WINDOW, 'STAIRS': shot_STAIRS,
         'BATH': shot_BATH, 'MIRROR': shot_MIRROR, 'BLACK': shot_BLACK, 'FLOOR': shot_FLOOR}


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
