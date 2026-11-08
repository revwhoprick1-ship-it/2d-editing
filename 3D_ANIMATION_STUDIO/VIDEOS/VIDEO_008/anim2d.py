#!/usr/bin/env python3
"""VIDEO_008 "Last Bus · Part 1" — real 2D animation (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_008/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
import edit_video008 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
MOON = '#9FC3FF'
BUSLIGHT = '#DDE6F2'

DRIVER = dict(shirt='#3A4A3A', shirt_sh='#2A362A', pants='#1E2433', pants_sh='#151A25', shoe='#1A1A1A', shoe_sh='#111111',
              hair='#2A2A2A', hair_sh='#1A1A1A', cap='#2A362A', belly=1.2, skin='#D9A784', skin_sh='#B88866')
PASSENGERS = [  # (side, row, look)
    (-1, 3, dict(shirt='#7A4FA0', shirt_sh='#5C3A7A', hair='#2A1A10', hair_sh='#1A100A', skin='#C98E66', skin_sh='#A8704C')),
    (1, 0, dict(shirt='#2E8A6A', shirt_sh='#22684F', hair='#D9B06A', hair_sh='#B38C4E')),
    (1, 1, dict(shirt='#B03A3A', shirt_sh='#862C2C', hair='#4A2A1A', hair_sh='#2E1A10', skin='#8E5A3C', skin_sh='#6E432C')),
    (-1, 2, dict(shirt='#3A6EB0', shirt_sh='#2C5486', hair='#1A1A1A', hair_sh='#0A0A0A')),
    (1, 2, dict(shirt='#C9A030', shirt_sh='#9E7C22', hair='#8A4A2A', hair_sh='#6A361E')),
    (1, 3, dict(shirt='#556070', shirt_sh='#3E4652', hair='#BDBDBD', hair_sh='#9A9A9A', mustache='#9A9A9A')),
    (-1, 4, dict(shirt='#A0507A', shirt_sh='#7A3C5C', hair='#C26A2A', hair_sh='#9A521E')),
    (1, 4, dict(shirt='#2A5A5A', shirt_sh='#1E4444', hair='#3A2A1A', hair_sh='#24180E', skin='#A8704C', skin_sh='#8A5A3A')),
    (-1, 5, dict(shirt='#6A8A3A', shirt_sh='#506A2A', hair='#1A1A1A', hair_sh='#0A0A0A', cap='#B03A3A')),
    (1, 5, dict(shirt='#8A6A4A', shirt_sh='#6A5038', hair='#E0C080', hair_sh='#C0A060')),
    (-1, 6, dict(shirt='#4A4A8A', shirt_sh='#36366A', hair='#5A3A1A', hair_sh='#3A2410')),
    (1, 6, dict(shirt='#B07A3A', shirt_sh='#8A5C2A', hair='#1A1A1A', hair_sh='#0A0A0A', skin='#8E5A3C', skin_sh='#6E432C')),
    (-1, 7, dict(shirt='#3A3A3A', shirt_sh='#2A2A2A', hair='#7A4A2A', hair_sh='#5A341E')),
]
YOU_ROW = 0                     # you sit left, row 1


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


def beam(cv, x0, y0, x1, y1, width, alpha=0.35, col='#FFF3D0'):
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang), math.cos(ang)
    p = poly([(x0 + nx * 10, y0 + ny * 10), (x1 + nx * width, y1 + ny * width), (x1 - nx * width, y1 - ny * width), (x0 - nx * 10, y0 - ny * 10)])
    cv.drawPath(p, paint(C(col, alpha), blur=18, shader=lin((x0, y0), (x1, y1), [C(col, alpha), C(col, 0.0)]), blend=skia.BlendMode.kPlus))


def foggy(t):
    return t >= B['window'] - 0.3


# ===================================================================== the bus interior (camera at the front, looking back)
BW, BH = 1.25, 2.3
ROW_Z0, ROW_DZ = 1.9, 0.95


def outside_window(cv, cam, side, z0, z1, t):
    """What is outside the side windows: passing city lights, or fog (and faces, later)."""
    x = side * BW
    win = quad(cam, [(x, 1.0, z0), (x, 1.0, z1), (x, 1.95, z1), (x, 1.95, z0)])
    cv.save()
    cv.clipPath(win, skia.ClipOp.kIntersect, True)
    if not foggy(t):
        cv.drawPath(win, paint('#0A0F1A'))
        for k in range(8):                                       # streetlights rushing past (towards the camera)
            z = z1 - ((t * 9 + k * 1.37) % (z1 - z0))
            p = cam.p(x * 1.02, 1.6 + 0.15 * (k % 3), z)
            r = 70 / max(cam.d(z), 0.4)
            glow(cv, p, r * 3, '#FFC870' if k % 2 else '#9FC3FF', 0.5)
    else:
        cv.drawPath(win, paint('#7C8794'))
        for k in range(5):
            z = z1 - ((t * 0.7 + k * 1.9) % (z1 - z0))
            glow(cv, cam.p(x * 1.02, 1.4, z), 160 / max(cam.d(z), 0.4), '#C7CED6', 0.5)
    cv.restore()
    cv.drawPath(win, paint(C('#9FC3FF', 0.06)))


def seat(cv, cam, x0, x1, z):
    """A forward-facing double seat (we see its front: cushion + back)."""
    cv.drawPath(quad(cam, [(x0, 0.45, z), (x1, 0.45, z), (x1, 1.15, z + 0.12), (x0, 1.15, z + 0.12)]), paint('#24496E'))
    cv.drawPath(quad(cam, [(x0, 1.1, z + 0.11), (x1, 1.1, z + 0.11), (x1, 1.17, z + 0.12), (x0, 1.17, z + 0.12)]), paint('#8E99A6'))
    cv.drawPath(quad(cam, [(x0, 0.0, z - 0.25), (x1, 0.0, z - 0.25), (x1, 0.45, z - 0.25), (x0, 0.45, z - 0.25)]), paint('#1A2F45'))
    cv.drawPath(quad(cam, [(x0, 0.45, z - 0.3), (x1, 0.45, z - 0.3), (x1, 0.45, z), (x0, 0.45, z)]), paint('#2C5A84'))
    for k in range(3):                                            # seat fabric pattern
        a, b = cam.p(x0 + 0.1 + k * 0.3, 0.6, z + 0.03), cam.p(x0 + 0.1 + k * 0.3, 1.0, z + 0.09)
        cv.drawLine(*a, *b, paint(C('#3B6E9E', 0.6), style='stroke', width=max(1, 30 / cam.d(z))))


def passenger(cv, cam, x, z, look, t, mode):
    """Sitting passenger, front view. mode: 'phone' (looking down at a lit phone) / 'stare' (looking at you) / 'turn'."""
    s = cam.scale(z, 1.6)
    fx, fy = cam.p(x, 0, z)
    drop = 200 * s
    P = dict(look)
    if mode == 'phone':
        P.update(look=(0.0, 0.9), lids=0.35, head_tilt=8, mouth='flat', arm_l=(18, -95), arm_r=(18, -95))
    else:
        P.update(look=(0.0, 0.0), lids=0.0, mouth='flat', brow=-0.2, pupil=0.75, arm_l=(3, 0), arm_r=(3, 0))
    mascot(cv, fx, fy + drop, s, legs=False, light_side=1, rim=BUSLIGHT, rim_a=0.25, **P)
    if mode == 'phone':
        px, py = fx, fy + drop - 560 * s
        cv.drawRect(skia.Rect(px - 50 * s, py - 70 * s, px + 50 * s, py + 70 * s), paint('#BFE0FF'))
        glow(cv, (px, py - 300 * s), 260 * s, '#BFE0FF', 0.35)


def bus_interior(cv, t, who='all', mode='phone', you_pose=None, stand=None, lights=1.0):
    cam = Cam(0.0, eye=2.05, vy=760)
    zf = 9.4
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0B0F15'))
    cv.drawPath(quad(cam, [(-BW, 0, zf), (BW, 0, zf), (BW, BH, zf), (-BW, BH, zf)]), paint('#1E2833'))
    rw = quad(cam, [(-0.9, 1.0, zf), (0.9, 1.0, zf), (0.9, 1.9, zf), (-0.9, 1.9, zf)])            # rear window
    cv.drawPath(rw, paint('#7C8794' if foggy(t) else '#0A0F1A'))
    for side in (-1, 1):
        x = side * BW
        cv.drawPath(quad(cam, [(x, 0, 0.3), (x, 0, zf), (x, BH, zf), (x, BH, 0.3)]), paint('#26313D' if side < 0 else '#222C37'))
        for k in range(4):
            outside_window(cv, cam, side, 0.6 + k * 2.2, 0.6 + k * 2.2 + 2.0, t)
    cv.drawPath(quad(cam, [(-BW, BH, 0.3), (BW, BH, 0.3), (BW, BH, zf), (-BW, BH, zf)]), paint('#151B22'))
    cv.drawPath(quad(cam, [(-BW, 0, 0.3), (BW, 0, 0.3), (BW, 0, zf), (-BW, 0, zf)]), paint('#2A2622'))
    cv.drawPath(quad(cam, [(-0.3, 0.002, 0.3), (0.3, 0.002, 0.3), (0.3, 0.002, zf), (-0.3, 0.002, zf)]), paint('#3A332C'))
    for side in (-1, 1):                                                                            # ceiling light strips
        a, b = cam.p(side * 0.6, BH - 0.02, 0.6), cam.p(side * 0.6, BH - 0.02, zf - 0.3)
        cv.drawLine(*a, *b, paint(C(BUSLIGHT, 0.25 + 0.75 * lights), style='stroke', width=14))
        cv.drawPath(quad(cam, [(side * BW, 2.0, 0.3), (side * BW, 2.0, zf), (side * BW, 2.04, zf), (side * BW, 2.04, 0.3)]),
                    paint('#C93A2E' if t >= B['slam'] and t < B['back'] else '#4A2420'))           # stop-request strip
    # rows, far -> near (each nearer seat hides the lower half of the passenger behind it)
    occupants = {(sd, r): lk for sd, r, lk in PASSENGERS}
    for r in range(7, -1, -1):
        z = ROW_Z0 + r * ROW_DZ
        for sd in (-1, 1):
            x0, x1 = (-BW + 0.08, -0.35) if sd < 0 else (0.35, BW - 0.08)
            seat(cv, cam, x0, x1, z + 0.25)
            if (sd, r) == (-1, YOU_ROW) and you_pose is not None and stand is None:
                s_ = cam.scale(z, 1.55)
                fx, fy = cam.p(-0.78, 0, z)
                mascot(cv, fx, fy + 200 * s_, s_, legs=False, light_side=1, rim=BUSLIGHT, rim_a=0.3, **you_pose)
            elif (sd, r) in occupants and who == 'all':
                passenger(cv, cam, sd * 0.78, z, occupants[(sd, r)], t, mode)
            elif (sd, r) in occupants and who == 'empty' and (r + sd) % 3 == 0:                    # left-behind phones
                p = cam.p(sd * 0.7, 0.47, z - 0.1)
                cv.drawRect(skia.Rect(p[0] - 14, p[1] - 6, p[0] + 14, p[1] + 6), paint('#BFE0FF'))
                glow(cv, p, 90, '#BFE0FF', 0.35)
        for sd in ((-1, 1) if r % 3 == 1 else ()):                                                 # yellow poles
            a, b = cam.p(sd * 0.33, 0, z - 0.4), cam.p(sd * 0.33, BH, z - 0.4)
            cv.drawLine(*a, *b, paint('#B8962E', style='stroke', width=max(3, 24 / cam.d(z - 0.4))))
    if stand is not None:                                                                           # you, standing in the aisle
        z = stand
        mascot(cv, *cam.p(0.0, 0, z), cam.scale(z, 1.55), light_side=1, rim=BUSLIGHT, rim_a=0.4, **(you_pose or {}))
    glow(cv, (540, 300), 1100, BUSLIGHT, 0.15 * lights)
    shade(cv, (540, 900), 1250, 0.6)
    dim(cv, (1 - lights) * 0.85)


def shot_BUS(cv, t):
    if t < B['blink']:
        bus_interior(cv, t, 'all', 'phone', you_pose=dict(look=(0.4, 0.6), lids=0.45, mouth='flat'))
    elif t < B['blink'] + 0.1:                                                                       # the blink
        cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000'))
    elif t < B['choice']:
        bus_interior(cv, t, 'empty', you_pose=dict(look=(0.6, 0.0), brow=1.0, mouth='o', pupil=0.6, head_turn=0.3, sweat=True))
    elif t < B['back']:                                                                              # standing in the aisle, the bus empty
        bus_interior(cv, t, 'empty', you_pose=dict(look=(0.0, 0.0), brow=1.0, mouth='o', pupil=0.55, sweat=True,
                                                   arm_r=(40, 30), arm_l=(10, 10)), stand=3.0)
    else:                                                                                            # flicker: everyone is back. staring.
        u = t - B['back']
        lt = 0.15 if (u < 0.12 or 0.24 < u < 0.33) else 1.0
        bus_interior(cv, t, 'all', 'stare', you_pose=dict(look=(0.0, 0.0), brow=1.0, mouth='o', pupil=0.5, sweat=True), stand=3.0,
                     lights=lt)


def shot_EMPTY(cv, t):
    """CU: an empty seat — a lit phone, a coffee still steaming, a bag."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0E141B'))
    cv.drawRect(skia.Rect(60, 200, 1020, 1100), paint('#24496E'))
    for k in range(6):
        cv.drawRect(skia.Rect(60 + k * 160, 200, 80 + k * 160, 1100), paint(C('#3B6E9E', 0.5)))
    cv.drawRect(skia.Rect(60, 180, 1020, 230), paint('#8E99A6'))
    cv.drawRect(skia.Rect(0, 1100, W, 1560), paint('#2C5A84'))
    cv.drawRect(skia.Rect(0, 1560, W, H), paint('#1A2F45'))
    cv.save(); cv.rotate(-12, 420, 1320)
    cv.drawRect(skia.Rect(300, 1260, 560, 1390), paint('#101215'))
    cv.drawRect(skia.Rect(312, 1270, 548, 1380), paint('#BFE0FF'))
    text(cv, '1 NEW MESSAGE', 430, 1310, 26, '#1A2A3A')
    text(cv, "where are you??", 430, 1350, 26, '#1A2A3A', bold=False)
    cv.restore()
    glow(cv, (430, 1320), 300, '#BFE0FF', 0.35)
    cv.drawPath(poly([(720, 1440), (840, 1440), (820, 1220), (740, 1220)]), paint('#E9DCC6'))      # coffee cup
    cv.drawRect(skia.Rect(732, 1200, 828, 1230), paint('#3A2A1E'))
    for k in range(3):
        ph = (t * 0.5 + k / 3) % 1
        x = 780 + 20 * math.sin(t * 3 + k * 2)
        cv.drawCircle(x, 1180 - ph * 280, 26 + ph * 30, paint(C('#FFFFFF', 0.18 * (1 - ph)), blur=12))
    cv.drawPath(blob([(860, 1500), (1000, 1420), (1080, 1520), (980, 1600)]), paint('#4A3A5A'))
    glow(cv, (540, 0), 1100, BUSLIGHT, 0.18)
    shade(cv, (540, 1200), 1100, 0.65)


def shot_PHONE(cv, t):
    """You hold the phone; it plays a video from one minute ago: everyone turns at once."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0B0F15'))
    glow(cv, (540, 900), 900, '#BFE0FF', 0.15)
    px0, py0, pw, ph = 250, 380, 580, 1140
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(px0 - 30, py0 - 60, px0 + pw + 30, py0 + ph + 80), 60, 60)), paint('#101215'))
    surf = skia.Surface(W, H)
    c2 = surf.getCanvas()
    if t < B['play']:
        c2.drawRect(skia.Rect(0, 0, W, H), paint('#1A1F26'))
        c2.drawCircle(540, 960, 160, paint(C('#FFFFFF', 0.85)))
        c2.drawPath(poly([(500, 880), (500, 1040), (620, 960)]), paint('#1A1F26'))
        text(c2, 'REC · 11:57 PM', 540, 1300, 70, '#FFFFFF')
    elif t < B['ends']:
        mode = 'stare' if t >= B['turn'] else 'phone'
        bus_interior(c2, t - 60, 'all', mode, you_pose=dict(look=(0.4, 0.6), lids=0.45, mouth='flat') if mode == 'phone'
                     else dict(look=(0.6, 0.0), brow=1.0, mouth='o', pupil=0.6))
        text(c2, '● REC  11:57:42 PM', 60, 200, 60, '#FF4A3A', align='left')
    else:
        c2.drawRect(skia.Rect(0, 0, W, H), paint('#000000'))
        text(c2, 'VIDEO ENDED', 540, 980, 90, '#FFFFFF', alpha=0.7)
    cv.drawImageRect(surf.makeImageSnapshot(), skia.Rect(px0, py0, px0 + pw, py0 + ph), skia.SamplingOptions(skia.FilterMode.kLinear))
    for side in (-1, 1):                                                                         # your hands
        hx = 540 + side * 330
        cv.drawPath(blob([(hx - 70, 1300), (hx + 70, 1280), (hx + 90, 1500), (hx - 60, 1560)]), paint('#F2C29B'))
        cv.drawPath(poly([(hx - 80, 1500), (hx + 100, 1480), (hx + 160, H), (hx - 140, H)]), paint('#F07A1A' if side > 0 else '#C85A0C'))
    glow(cv, (540, 950), 700, '#BFE0FF', 0.2)
    shade(cv, (540, 950), 1100, 0.6)


def bus_bg(cv, t, lights=1.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#141C26', shader=lin((0, 0), (0, H), [C('#1E2833'), C('#0B0F15')])))
    for k in range(3):
        x = 80 + k * 340
        cv.drawRect(skia.Rect(x, 360, x + 280, 900), paint('#7C8794' if foggy(t) else '#0A0F1A'))
        if not foggy(t):
            for j in range(2):
                gx = x + ((t * 800 + j * 500 + k * 90) % 400) - 60
                glow(cv, (gx, 600), 120, '#FFC870', 0.4)
    cv.drawRect(skia.Rect(0, 1150, W, H), paint('#24496E'))
    glow(cv, (540, 0), 1100, BUSLIGHT, 0.2 * lights)


def shot_FACE(cv, t):
    bus_bg(cv, t)
    talking = talk(t, 'D1', 'D3')
    angry = t >= LS['D3'][0]
    mascot(cv, 540, 2700, 1.95, look=(0.5, -0.1), head_turn=0.35, brow=0.4 if angry else 1.0, mouth='open' if talking else 'o',
           mouth_open=talking, pupil=0.7, sweat=True, light_side=1, rim=BUSLIGHT, rim_a=0.5, lids=blink(t, [B['face'] + 0.7]))
    shade(cv, (540, 950), 1100, 0.55)


def windshield(cv, t, x0, y0, x1, y1):
    cv.drawRect(skia.Rect(x0, y0, x1, y1), paint('#05080D'))
    cv.save(); cv.clipRect(skia.Rect(x0, y0, x1, y1))
    vx, vy = (x0 + x1) / 2, y0 + (y1 - y0) * 0.55
    cv.drawPath(poly([(vx - 20, vy), (vx + 20, vy), (x1 + 200, y1), (x0 - 200, y1)]), paint('#15181C'))
    for k in range(6):                                                                         # lane dashes rushing in
        u = (t * 1.6 + k / 6) % 1
        yy = vy + (y1 - vy) * u * u
        cv.drawRect(skia.Rect(vx - 4 - 30 * u, yy, vx + 4 + 30 * u, yy + 10 + 60 * u * u), paint(C('#D9D2B0', 0.7)))
    glow(cv, (vx, vy + 150), 500, '#FFF3D0', 0.25)                                             # headlights
    if foggy(t):
        cv.drawRect(skia.Rect(x0, y0, x1, y1), paint(C('#8A949E', 0.75)))
    cv.restore()


def route_screen(cv, x, y, w_, h_, t, size):
    cv.drawRect(skia.Rect(x, y, x + w_, y + h_), paint('#0E0907'))
    msg = 'NEXT STOP: ELM ST' if t < B['you'] - 0.1 else 'NEXT STOP: YOU'
    col = '#FF9A2E' if t < B['you'] - 0.1 else '#FF3B2F'
    text(cv, msg, x + w_ / 2, y + h_ * 0.72, size, col)
    glow(cv, (x + w_ / 2, y + h_ / 2), w_ * 0.6, col, 0.15)


def shot_DRIVER(cv, t):
    """Behind the driver: he never turns round. Windshield, wheel, route screen."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#10151B'))
    windshield(cv, t, 0, 300, W, 1250)
    route_screen(cv, 260, 220, 560, 90, t, 50)
    cv.drawRect(skia.Rect(0, 1250, W, H), paint('#1A1E24'))
    mascot(cv, 470, 2350, 1.55, view='back', light_side=1, rim='#FFF3D0', rim_a=0.4, talk=0, **DRIVER)
    cv.drawOval(skia.Rect(560, 1180, 1060, 1330), paint('#15171B', style='stroke', width=44))    # steering wheel
    glow(cv, (540, 1300), 900, '#FFF3D0', 0.1)
    shade(cv, (540, 800), 1150, 0.55)


def shot_ROUTE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#141A20'))
    route_screen(cv, 40, 640, 1000, 300, t, 96)
    for i in range(0, 300, 6):
        cv.drawLine(40, 640 + i, 1040, 640 + i, paint(C('#000000', 0.3), style='stroke', width=2))
    if t >= B['you'] - 0.1 and int(t * 8) % 2 == 0:
        glow(cv, (540, 790), 600, '#FF3B2F', 0.15)
    shade(cv, (540, 800), 1000, 0.6)


def shot_WINDOW(cv, t):
    """The side window: fog, and in the fog, every passenger, perfectly still, waving."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A2028'))
    wx0, wy0, wx1, wy1 = 70, 260, 1010, 1500
    cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), paint('#8A949E', shader=lin((0, wy0), (0, wy1), [C('#9AA4AE'), C('#6E7882')])))
    cv.save(); cv.clipRect(skia.Rect(wx0, wy0, wx1, wy1))
    appear = ease((t - B['faces']) / 0.8)
    wave = t >= B['waving']
    for k, (sd, r, lk) in enumerate(PASSENGERS[:9]):
        x = 140 + (k % 5) * 190 + (40 if k >= 5 else 0)
        y = 1650 + (k // 5) * 260 - (k % 2) * 40
        s_ = 0.42 + (k // 5) * 0.12
        drift = -((t * 60) % 0) if False else 0
        cv.saveLayer(None, skia.Paint(Alphaf=0.55 * appear, ColorFilter=skia.ColorFilters.Blend(C('#AEB8C2', 0.55).toColor(), skia.BlendMode.kSrcATop)))
        arm = (150 + 20 * math.sin(t * 5 + k), 20) if wave else (3, 0)
        mascot(cv, x, y, s_, look=(0.0, 0.0), mouth='flat', brow=-0.1, pupil=0.6, arm_r=arm, **lk)
        cv.restore()
    for k in range(6):                                                                          # drifting fog layers
        x = ((t * 40 + k * 230) % 1400) - 200
        cv.drawOval(skia.Rect(x - 260, 300 + k * 200, x + 260, 520 + k * 200), paint(C('#C7CED6', 0.35), blur=40))
    cv.restore()
    cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), paint('#2A333E', style='stroke', width=36))
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#24496E'))
    cv.saveLayer(None, skia.Paint(Alphaf=0.12))                                                 # your faint reflection
    mascot(cv, 900, 2300, 1.1, look=(-0.6, 0.0), brow=1.0, mouth='o', pupil=0.6)
    cv.restore()
    shade(cv, (540, 900), 1100, 0.5)


def shot_BUTTON(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#141C26'))
    cv.drawRect(skia.Rect(470, 0, 610, H), paint('#D9B23A'))                                   # pole
    cv.drawRect(skia.Rect(470, 0, 500, H), paint('#F0CE5A'))
    lit = t >= B['slam']
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(380, 760, 700, 1080), 40, 40)), paint('#C9CED6'))
    cv.drawCircle(540, 920, 110, paint('#FF3B2F' if lit else '#8A1E18'))
    text(cv, 'STOP', 540, 945, 64, '#FFFFFF')
    if lit:
        glow(cv, (540, 920), 400, '#FF3B2F', 0.4)
    push = keys(t, [(B['button'], 0.0), (B['slam'] - 0.15, 0.6), (B['slam'], 1.0), (B['slam'] + 0.4, 0.8)])
    hx, hy = 1250 - 560 * push, 1000 - 60 * push
    cv.drawPath(blob([(hx - 120, hy - 60), (hx + 30, hy - 80), (hx + 60, hy + 70), (hx - 100, hy + 80)]), paint('#F2C29B'))
    cv.drawPath(poly([(hx + 20, hy - 90), (1300, hy - 160), (1300, hy + 160), (hx + 40, hy + 90)]), paint('#F07A1A'))
    text(cv, 'STOP REQUESTED', 540, 360, 84, '#FF3B2F' if lit else '#3A1A18')
    shade(cv, (540, 900), 1100, 0.55)


def shot_TICKET(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0E141B'))
    cv.save(); cv.rotate(-6, 540, 900)
    cv.drawRect(skia.Rect(150, 560, 930, 1280), paint('#EDE4CC'))
    cv.drawRect(skia.Rect(150, 560, 930, 680), paint('#B03A3A'))
    text(cv, 'CITY NIGHT TRANSIT', 540, 645, 64, '#FFFFFF')
    text(cv, 'ROUTE 13', 210, 790, 54, '#2A2A2A', align='left')
    text(cv, 'FROM:  ELM ST', 210, 900, 54, '#2A2A2A', align='left')
    text(cv, 'TO:  ———', 210, 1000, 54, '#2A2A2A', align='left')
    a = ease((t - B['oneway']) / 0.15)
    text(cv, 'ONE WAY', 540, 1190, 120, C('#B03A3A', 0.35 + 0.65 * a))
    cv.drawCircle(860, 760, 34, paint('#0E141B'))
    cv.restore()
    for k in range(4):
        cv.drawPath(poly([(300 + k * 40, 1400), (330 + k * 44, 1250)], closed=False), paint('#E3B08A', style='stroke', width=52))
    cv.drawPath(blob([(200, 1400), (520, 1380), (560, 1700), (180, 1760)]), paint('#F2C29B'))
    cv.drawPath(poly([(160, 1650), (560, 1620), (600, H), (100, H)]), paint('#F07A1A'))
    glow(cv, (540, 300), 1000, BUSLIGHT, 0.18)
    shade(cv, (540, 900), 1100, 0.6)


def shot_MIRROR(cv, t):
    """The rear-view mirror: the driver looks at you... no face."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0B0F15'))
    windshield(cv, t, 0, 900, W, H)
    cv.drawRect(skia.Rect(520, 0, 560, 520), paint('#15171B'))
    mr = skia.RRect.MakeRectXY(skia.Rect(80, 420, 1000, 860), 70, 70)
    cv.drawRRect(mr, paint('#15171B'))
    inner = skia.RRect.MakeRectXY(skia.Rect(110, 450, 970, 830), 54, 54)
    cv.save(); cv.clipRRect(inner, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1C242E'))
    u = keys(t, [(B['mirror'], 0.0), (B['noface'] - 0.4, 0.0), (B['noface'], 1.0)])
    mascot(cv, 520 + 40 * u, 1270, 0.62, faceless=True, head_turn=0.0, head_tilt=-4 * u, light_side=-1, rim='#FFF3D0', rim_a=0.4, **DRIVER)
    cv.restore()
    cv.drawRRect(inner, paint(C('#FFFFFF', 0.06)))
    cv.drawPath(poly([(140, 460), (360, 460), (180, 820)]), paint(C('#FFFFFF', 0.05)))
    shade(cv, (540, 640), 1000, 0.55)


def shot_FACE3(cv, t):
    bus_bg(cv, t, lights=flicker(t, 4, 9.0, 0.3))
    mascot(cv, 540, 2700, 1.95, look=(0.0, 0.0), brow=1.0, mouth='open', mouth_open=0.5, pupil=0.4, sweat=True, light_side=1,
           rim='#FF3B2F', rim_a=0.6)
    glow(cv, (540, 1900), 900, '#FF3B2F', 0.18)
    shade(cv, (540, 950), 1100, 0.6)


SHOTS = {'BUS': shot_BUS, 'EMPTY': shot_EMPTY, 'PHONE': shot_PHONE, 'FACE': shot_FACE, 'DRIVER': shot_DRIVER, 'ROUTE': shot_ROUTE,
         'WINDOW': shot_WINDOW, 'BUTTON': shot_BUTTON, 'TICKET': shot_TICKET, 'MIRROR': shot_MIRROR, 'FACE3': shot_FACE3}


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
            if i % 300 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
