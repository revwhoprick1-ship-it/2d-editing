#!/usr/bin/env python3
"""VIDEO_026 "Two Bobs" renderer — draws the 1,680 frames (1080x1920 @ 30 fps) with multiprocessing.

    python3 studio/renderer.py [--frames a,b] [--stills 0.0,1.2,...]      -> frames2d/ALL/####.jpg

Per frame: shot (sets.py plate cropped by a 2D camera + what moves + puppets.py) -> vignette/grain -> pop-up labels -> HUD ->
choice card -> colour strobes -> VHS glitch pass (compositor.py). Captions / watermark / the POV blink are added by the EDL.
Fast: static sets are cached plates, ink outlines are the stamped filter (no Dilate), big blurs are cached low-res copies.
"""
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import timeline as TL  # noqa: E402
import compositor as CP  # noqa: E402
from puppets import (BOB, FAKE, INKC, SKIN_M, SKIN_M_SH, C, H, W, _tendril, draw_bob_mimic_puppet, lit_puppet, long_hand, mascot,  # noqa: E402
                     paint, palm_on_glass, phone_in_hand, poly, seated, side_light, stroke, under_light, with_ink)
from sets import (GAP_B, GAP_T, R, cam_scene, draw_plate, hallway, pov_backrest, rain, rr, ui_call, ui_lock, ui_thread)  # noqa: E402
from comp import blink, ease, glow, keys, talk  # noqa: E402
from kit import Cam, text  # noqa: E402

F, T, FPS, NF, WORDS = TL.F, TL.T, TL.FPS, TL.NF, TL.WORDS
OUT = os.path.join(VIDEO, 'frames2d', 'ALL')
YOU_X, BOB_X, PS, HIP_Y, FLOOR_Y = 332, 698, 0.78, 1392, 1700
CYAN = '#37BEFF'
REST = dict(arm_l=(4, -14), arm_r=(4, -14))
YOU_POSE = dict(arm_l=(8, -38), arm_r=(8, -38), light_side=-1, rim='#9FC3FF', rim_a=0.5)
PHONE0 = dict(cx=540.0, cy=990.0, s=1.0, tilt=-5.0)                          # the frame-0 pose = the loop target


def rnd(k):
    return (math.sin(k * 12.9898 + 4.1414) * 43758.5453) % 1.0


def tv_flicker(t):
    k = int(t * 11)
    u = t * 11 - k
    return 0.72 + 0.28 * (rnd(k) + (rnd(k + 1) - rnd(k)) * u)


def shake(f, f0, n, amp):
    if not (f0 <= f < f0 + n):
        return (0.0, 0.0)
    k = 1 - (f - f0) / n
    return ((rnd(f * 3.1) * 2 - 1) * amp * k, (rnd(f * 7.7 + 2) * 2 - 1) * amp * k)


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def sway(t, a=1.0):
    return (a * (6 * math.sin(t * 1.3) + 3 * math.sin(t * 2.9)), a * (5 * math.sin(t * 1.7 + 1)), a * 0.25 * math.sin(t * 0.9))


class View:
    """2D camera on a set drawn in 1080x1920 world coords."""
    def __init__(self, z=1.0, cx=540.0, cy=960.0, sw=(0.0, 0.0, 0.0), sh=(0.0, 0.0)):
        self.z, self.cx, self.cy, self.rot, self.sh = z, cx + sw[0] / z, cy + sw[1] / z, sw[2], sh

    def begin(self, cv):
        cv.save(); cv.translate(540 + self.sh[0], 960 + self.sh[1]); cv.rotate(self.rot); cv.scale(self.z, self.z); cv.translate(-self.cx, -self.cy)

    def end(self, cv):
        cv.restore()

    def pt(self, x, y):
        return (540 + (x - self.cx) * self.z + self.sh[0], 960 + (y - self.cy) * self.z + self.sh[1])

    def rect(self, l, t, r, b):
        a, c = self.pt(l, t), self.pt(r, b)
        return (a[0], a[1], c[0], c[1])


def whip(cv, u, draw_a, draw_b, direction=1):
    """Whip-pan: A flies out, B flies in, smeared with horizontal motion blur. direction +1 = the camera pans right."""
    e = ease(u)
    cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(95 * math.sin(math.pi * u) + 0.01, 0.01)))
    cv.save(); cv.translate(-direction * e * 1400, 0); draw_a(); cv.restore()
    cv.save(); cv.translate(direction * (1 - e) * 1400, 0); draw_b(); cv.restore()
    cv.restore()
    for k in range(10):
        y = 120 + k * 185 + 60 * math.sin(k * 2.7)
        cv.drawLine(0, y, W, y, stroke('#FFFFFF', 3, 0.10 * math.sin(math.pi * u)))


# =============================================================================================== the living room (front)
def living_scene(cv, f, t, you=None, bob=None, tv_col='#AFC0FF', tv_a=1.0, bg_blur=0, dots=0.0, dent=False, phone_glow=1.0):
    draw_plate(cv, 'living', blur=bg_blur)
    rain(cv, (690, 440, 910, 890), t)
    if int(t * 1.5) % 2 == 0:                                                 # the security camera's LED
        cv.drawCircle(938, 329, 4.5, paint('#FF3B30')); glow(cv, 938, 329, 26, '#FF3B30', 0.5)
    fl = tv_flicker(t)
    glow(cv, 60, 1560, 1250, tv_col, 0.20 * fl * tv_a)                         # the TV, off-screen front-left
    if dent:                                                                  # where the copy sat
        cv.drawOval(R(BOB_X - 120, 1356, BOB_X + 120, 1432), paint(C('#28315A', 0.8), blur=10))
        cv.drawOval(R(BOB_X - 96, 1130, BOB_X + 96, 1300), paint(C('#28315A', 0.45), blur=14))
    if you is not None:                                                       # hidden detail #2: YOUR shadow on the couch. It has none.
        sx, sy = YOU_X + 128, HIP_Y - 470 * PS - 14
        cv.save(); cv.clipRect(R(110, 300, 900, 1342))
        sp = paint(C('#04040C', 0.66 + 0.12 * fl), blur=9)
        cv.drawCircle(sx, sy, 172 * PS, sp)
        cv.drawRoundRect(R(sx - 132 * PS, sy + 108 * PS, sx + 132 * PS, sy + 520 * PS), 60 * PS, 60 * PS, sp)
        cv.restore()
    if dots > 0:                                                              # it rises behind the couch, right behind your shoulder
        cx_, top = 522, 1094 - 104 * dots
        cv.save(); cv.clipRect(R(110, 300, 970, 1081))
        dome = R(cx_ - 64, top, cx_ + 64, top + 220)
        cv.drawOval(dome, paint('#05050B')); cv.drawOval(dome, stroke(INKC, 4))
        for sd in (-1, 1):
            cv.drawPath(poly([(cx_ + sd * 40, top + 30), (cx_ + sd * 92, top + 4), (cx_ + sd * 60, top + 70)]), paint('#05050B'))
        for k, (dx, dy) in enumerate(((-15, 60), (15, 60), (-12, 88), (12, 88))):
            ex, ey = cx_ + dx + 1.5 * math.sin(f * 0.23 + k), top + dy
            cv.drawCircle(ex, ey, 13, paint(C('#FF1A1A', 0.8 * dots), blur=7)); cv.drawCircle(ex, ey, 4.5, paint(C('#FF3A2A', dots)))
        cv.restore()
    if bob is not None:
        draw_bob_mimic_puppet(cv, BOB_X, 0, PS, bob.get('g', 0.0), bob.get('jd', 0.0), bob.get('td', 0.0), bob.get('crack', 0.0), bob.get('glitch', 0),
                              frame=f, hip_y=HIP_Y, floor_y=FLOOR_Y, pose=bob.get('pose', REST), look=bob.get('look', (0.0, 0.0)),
                              eye_roll=bob.get('roll', 0.0), under=0.42 * phone_glow, rim=0.55 * fl, head_tilt=bob.get('tilt', 0.0))
    if you is not None:
        lights = [under_light(YOU_X, HIP_Y + 60, HIP_Y - 700 * PS, 0.5 * phone_glow)]
        seated(cv, YOU_X, HIP_Y, PS, FLOOR_Y, '#C6C2E2', lights=lights, phone=(0, 6, 0), **you)
        glow(cv, YOU_X, HIP_Y - 10, 330, CYAN, 0.30 * phone_glow)


# =============================================================================================== SHOT 1A / 7B: the phone held up to the lens
def phone_comp(cv, f, t, bg=1.0, screen=None, pose=None, trem=1.0, red=0.22):
    cv.save(); cv.translate(540, 960); cv.scale(1.5, 1.5); cv.translate(-420, -1150)
    draw_plate(cv, 'living', blur=10)
    cv.restore()
    cv.drawRect(R(0, 0, W, H), paint(C('#05050E', 1 - 0.5 * bg)))
    p = dict(PHONE0); p.update(pose or {})
    tx = trem * (4.5 * math.sin(t * 2 * math.pi * 8.5) + 2 * math.sin(t * 2 * math.pi * 13))
    ty = trem * 3.5 * math.sin(t * 2 * math.pi * 7.3 + 1)
    if red > 0:
        glow(cv, p['cx'], p['cy'] - 80, 900 * p['s'], '#E8283A', red)
    phone_in_hand(cv, p['cx'] + tx, p['cy'] + ty, p['s'], p['tilt'] + trem * 0.6 * math.sin(t * 40), screen or (lambda c: ui_lock(c, t)), tremble=4 * trem)


def bob_cu(cv, f, t):
    z = keys(f, [(F['whip1'], 1.86), (F['s1b'], 2.0)])
    v = View(z, BOB_X + 22, 1105, sw=sway(t, 0.6))
    v.begin(cv)
    living_scene(cv, f, t, you=dict(YOU_POSE, look=(0.0, 0.6), brow=0.6), bob={})
    v.end(cv)


def s1a(cv, f, t):
    if f < F['whip1']:
        phone_comp(cv, f, t, bg=min(1.0, f / 6.0))
    elif f < F['whip1_end']:
        whip(cv, (f - F['whip1'] + 1) / (F['whip1_end'] - F['whip1'] + 1), lambda: phone_comp(cv, f, t), lambda: bob_cu(cv, f, t), 1)
    else:
        bob_cu(cv, f, t)
    return []


def s1b(cv, f, t):
    u = (f - F['s1b']) / (F['s2a'] - F['s1b'])
    v = View(1.05 + 0.17 * ease(u), 556, 1085 - 25 * u, sw=sway(t))
    turn = keys(f, [(F['s1b'] + 4, 0.0), (F['s1b'] + 46, 0.85)])
    you = dict(YOU_POSE, head_turn=turn, look=(0.95 * turn, 0.05), brow=0.9, mouth='o' if f > 82 else 'flat', sweat=f > 86,
               lids=blink(t, 2.9, 0.4), body_lean=-2.5 * turn)
    v.begin(cv)
    living_scene(cv, f, t, you=you, bob={})
    v.end(cv)
    tg = v.rect(BOB_X - 112, 1140, BOB_X + 112, 1330)
    return [dict(f0=F['label_dist'], f1=F['s2a'], txt='DISTANCE: 0.4 M — PULSE: 0 BPM', at=(600, tg[1] - 380), target=tg, leader=False)]


# =============================================================================================== SHOT 2A / 2B: the photo
def s2(cv, f, t):
    a = F['s2a']
    if f < F['s2b']:
        u = (f - a) / (F['s2b'] - a)
        s, cx, cy, tilt = 1.22 + 0.4 * ease(u), 540.0, 1085 - 40 * u, -3 * (1 - ease(u))
        L = None
    else:
        u = (f - F['s2b']) / (F['s3a'] - F['s2b'])
        s = 1.62 + 1.75 * ease(u, 'out')
        L = (-103 + 20 * ease(u), -164)                                       # the thing's head inside the photo (phone-local)
        k = ease(min(1.0, u * 2.4))
        cx, cy, tilt = 540 * (1 - k) + (540 - L[0] * s) * k, 1045 * (1 - k) + (900 - L[1] * s) * k, 0.0
    load = keys(f, [(a + 9, 0.0), (a + 15, 0.45), (a + 23, 0.88), (a + 29, 1.0)], 'lin')
    sharp = keys(f, [(a + 29, 0.0), (F['unblur'], 1.0)])
    ang = keys(f, [(F['live_turn'], 0.0), (F['live_turn'] + 7, 84.0)], 'out')
    flare = 1.0 + (1.2 if F['live_turn'] <= f < F['live_turn'] + 6 else 0.0)
    show = ease((f - (a + 3)) / 5.0, 'out')

    def screen(c):
        ui_thread(c, t, f, load=load, sharp=sharp, thing_ang=ang, pin=flare, show=show)
    phone_comp(cv, f, t, bg=0.7, screen=screen, pose=dict(cx=cx, cy=cy, s=s, tilt=tilt), trem=0.5 if L is None else 0.15, red=0.0)
    glow(cv, 540, 900, 900, '#7FE8A8' if sharp > 0.5 else '#9FB4FF', 0.10)
    if L is not None:
        hx, hy = cx + L[0] * s, cy + L[1] * s
        r = 46 * s
        return [dict(f0=F['label_ir'], f1=F['s3a'], txt='SPECTRUM IR: NECK ROTATION 94°', at=(540, hy + r + 96), target=(hx - r, hy - r, hx + r, hy + r))]
    return []


# =============================================================================================== SHOT 3A: you test it
def s3a(cv, f, t):
    u = (f - F['s3a']) / (F['s3b'] - F['s3a'])
    v = View(2.0 + 0.15 * u, YOU_X + 74 - 20 * u, 1085, sw=sway(t, 0.7))
    m = talk(t, WORDS, {'M01'})
    reach = ease((f - F['fingers']) / 30.0)
    you = dict(YOU_POSE, look=(0.25, 0.9), brow=1.0, mouth='o' if m > 0 else 'flat', mouth_open=m, sweat=True, body_lean=-3.5 * u, head_tilt=-3,
               lids=blink(t, 2.3, 0.1))
    you['arm_l'] = (8 + 30 * u, -38 + 22 * u)                                  # your free hand feels for the armrest
    bob = dict(pose=dict(arm_l=(4 + 48 * reach, -14 + 36 * reach), arm_r=(4, -14)), tilt=-5 * reach, look=(-0.9 * reach, 0.2 * reach))
    v.begin(cv)
    living_scene(cv, f, t, you=you, bob=bob)
    v.end(cv)
    return [dict(f0=F['fingers'] + 8, f1=F['s3b'], txt='DISTANCE: 0.2 M', at=(790, 640), target=None)]


# =============================================================================================== SHOT 3B: the head snap
def s3b(cv, f, t):
    snap = f >= F['snap']
    u = (f - F['s3b']) / (F['s4a'] - F['s3b'])
    v = View(1.0 + 0.08 * u + (0.07 if snap else 0.0), 540, 960, sw=sway(t, 0.5), sh=shake(f, F['snap'], 13, 25))
    HX, HY, S = 520.0, 800.0, 2.3
    fl = tv_flicker(t)
    said = talk(t, WORDS, {'B01'})
    v.begin(cv)
    draw_plate(cv, 'rightwall')
    glow(cv, 1180, 900, 1150, '#FF3040' if snap else '#AFC0FF', 0.17 * fl)       # the TV, off to the right
    glow(cv, 300, 1900, 900, CYAN, 0.16)                                       # your phone, below the lens
    thr = TL.w_at('N07', 'throat', T['s3b'] + 1.2)
    if not snap:
        x, y = HX - 26 * S, HY + 900 * S

        def throat():                                                         # the throat moves. The lips do not.
            if t >= thr:
                for k in range(3):
                    ph = ((t - thr) * 3.2 + k / 3.0) % 1.0
                    rad = (36 + 150 * ph) * 1.0
                    cv.drawArc(R(HX + 60 - rad, HY + 215 * S / 2.3 * 2.3 - rad, HX + 60 + rad, HY + 215 * S / 2.3 * 2.3 + rad), -42, 84, False,
                               stroke('#FFFFFF', 7, 0.55 * (1 - ph)))
        lit_puppet(cv, x, y, S, tint='#B4B1DC', lights=[side_light(HX + 520, HX - 60, 0.28, (175, 192, 255)), under_light(0, HY + 900, HY - 200, 0.38)],
                   ink_w=9, post=throat, **dict(FAKE, view='side', face=1, glasses='#17151F', lens=C('#D6F1FF', 0.22), mouth='flat', brow=0.0,
                                                look=(0.3, 0.0), arm_l=(3, 0), arm_r=(3, 0), legs=False))
    else:
        k = f - F['snap']
        g = 0.15 + 0.07 * said + 0.03 * math.sin(f * 0.9)
        draw_bob_mimic_puppet(cv, HX, HY + 900 * S, S, g, 0.0, 0.0, 0.35, 14 if k < 7 else 0, frame=f, eye_roll=1.0, pose=REST,
                              under=0.55, rim=1.0, tint='#B4B1DC', ink_w=9, age=0.5)
        for j in range(3):                                                    # the voice comes out of the neck
            ph = (t * 3.0 + j / 3.0) % 1.0
            rad = 60 + 260 * ph
            for sd in (-1, 1):
                cv.drawArc(R(HX - rad, HY + 500 - rad, HX + rad, HY + 500 + rad), -28 if sd > 0 else 152, 56, False, stroke('#FFFFFF', 7, 0.5 * (1 - ph) * (0.35 + said)))
    v.end(cv)
    tg = v.rect(HX - 120, HY + 215, HX + 120, HY + 305)
    return [dict(f0=F['snap'] + 12, f1=F['s4a'], txt='LIPS: CLOSED — VOICE SOURCE: THROAT', at=(540, 330), target=tg)]


# =============================================================================================== SHOT 4A: the hallway / front door
def hall_shot(cv, f, t, z, open_=0.0, bob_door=0.0, flash=0.0, hands=(0.0, 0.0), shud=0.0, sil=0.0, handle=0.0, fl=1500.0, sh=(0.0, 0.0)):
    sw = sway(t, 0.8)
    cam = Cam(z, eye=1.38, vx=540 + sw[0], vy=920 + sw[1], x=0.0, f=fl)
    cv.save(); cv.translate(*sh)
    hallway(cv, cam, t, door_open=open_, flash=flash, hands=hands, shudder=shud, handle=handle, sil=sil, bob_door=bob_door)
    cv.restore()


def s4a(cv, f, t):
    a = F['s4a']
    knocks = (F['knock1'], F['knock2'], F['knock3'])
    shud = max([max(0.0, 1 - (f - k) / 8.0) for k in knocks if f >= k] + [0.0])
    sh = (0.0, 0.0)
    for k in knocks:
        sh = add(sh, shake(f, k, 8, 16))
    hands = (min(1.0, max(0.0, (f - F['knock2'] - 1) / 2.0)), min(1.0, max(0.0, (f - F['knock3'] - 1) / 2.0)))
    flash = max(0.0, 1 - (f - F['lightning']) / 7.0) if f >= F['lightning'] else 0.0
    sil = 0.0 if f < F['lightning'] else 0.9
    handle = 26 * math.sin(f * 2.4) if F['handle'] <= f < F['handle'] + 24 else 0.0
    z = keys(f, [(a, -2.4), (F['s4b'], 1.6)], 'out')

    def hall():
        hall_shot(cv, f, t, z, flash=flash, hands=hands, shud=shud, sil=sil, handle=handle, sh=sh)
    if f < a + 7:
        whip(cv, (f - a + 1) / 8.0, lambda: s3b(cv, a - 1, (a - 1) / FPS), hall, -1)
    else:
        hall()
    return []


# =============================================================================================== SHOT 4B: the real Bob behind the glass
def s4b(cv, f, t):
    a, note = F['s4b'], F['note']
    if f < note:
        z, cx, cy = 1.0 + 0.1 * (f - a) / (note - a), 540.0, 880.0
    else:
        k, u2 = ease((f - note) / 5.0, 'out'), (f - note) / (F['s5a'] - note)
        z, cx, cy = 1.1 + 0.42 * k + 0.12 * u2, 540.0, 880 + 250 * k            # the note sits ABOVE the captions (Y=1240)
    pounds = (a + 5, a + 19, note)
    sh = (0.0, 0.0)
    for k_ in pounds:
        sh = add(sh, shake(f, k_, 7, 10))
    v = View(z, cx, cy, sw=sway(t, 0.6), sh=sh)
    breath = 0.5 + 0.5 * math.sin(t * 2 * math.pi * 0.9)
    v.begin(cv)
    cv.drawPaint(paint('#201A32'))
    for box in ((-60, 1490, 1140, 2100), (-60, -200, 1140, 200)):
        rr(cv, box[0], box[1], box[2], box[3], 8, '#1A1528', 4)
    rr(cv, 150, 260, 930, 1420, 10, '#3A3E72', 5)
    glass = R(180, 290, 900, 1390)
    cv.save(); cv.clipRect(glass)
    cv.drawRect(glass, paint('#000000', shader=skia.GradientShader.MakeLinear([(180, 290), (900, 1390)], [C('#8FA2C8').toColor(), C('#46547C').toColor()])))
    glow(cv, 840, 360, 640, '#FFE2B0', 0.45)                                    # porch light
    cv.saveLayer(glass, skia.Paint(ImageFilter=skia.ImageFilters.Blur(12, 12)))  # frosted: the real Bob is a blur. Warm skin. No glasses.
    by = 700 + 900 * 0.95
    mascot(cv, 540 + 6 * math.sin(t * 2.1), by, 0.95, legs=False, **dict(BOB, view='front', brow=1.0, mouth='o', mouth_open=0.25 + 0.25 * breath,
                                                                         look=(0.0, 0.1), arm_l=(52, -8), arm_r=(52, -8) if f < note else (30, -60)))
    for k_ in range(3):                                                        # the scrape on his forehead
        cv.drawLine(585 + k_ * 16, 578 + k_ * 5, 640 + k_ * 12, 610 + k_ * 9, stroke('#8A1A1E', 9, 0.9))
    cv.restore()
    cv.drawRect(glass, paint(C('#9FB0D8', 0.24)))
    glow(cv, 540, 840, 140 + 60 * breath, '#FFFFFF', 0.30 + 0.25 * breath)        # his breath fogs the glass
    rain(cv, (180, 290, 900, 1390), t, n=22, a=0.4)
    pop = [1 + 0.12 * max(0.0, 1 - (f - k_) / 5.0) if f >= k_ else 1.0 for k_ in pounds]
    palm_on_glass(cv, 262, 1060, 1.3 * max(pop[0], pop[1]), flip=1, blood=1.0)
    if f < note:
        palm_on_glass(cv, 822, 1050, 1.3 * max(pop[0], pop[1]), flip=-1, blood=1.0)
    else:                                                                     # he presses his phone flat against the glass
        k = min(1.0, (f - note + 1) / 3.0)
        cv.save(); cv.translate(545, 1010); cv.scale(1.3 - 0.3 * k, 1.3 - 0.3 * k); cv.rotate(-3)
        rr(cv, -135, -240, 135, 240, 34, '#0E0E16', 6)
        rr(cv, -120, -222, 120, 222, 22, '#16161E')
        for i, (ln, col) in enumerate((('HOLD YOUR', '#FFFFFF'), ('BREATH.', '#FFFFFF'), ('IT HUNTS', '#FFFFFF'), ('BY SOUND.', '#FF5A50'))):
            text(cv, ln, 0, -112 + i * 70 + (22 if i >= 2 else 0), 54, col)
        for i in range(4):                                                    # fingertips pressed white around it
            cv.drawOval(R(118, -150 + i * 78, 172, -96 + i * 78), paint(C('#F2DDD0', 0.92)))
        cv.drawOval(R(-176, 40, -118, 104), paint(C('#F2DDD0', 0.92)))
        cv.restore()
        if f < note + 3:
            cv.drawRect(glass, paint(C('#FFFFFF', 0.4 - 0.13 * (f - note))))
    cv.restore()
    cv.drawRect(glass, stroke('#454B8A', 16)); cv.drawRect(glass, stroke(INKC, 5))
    v.end(cv)
    tg = v.rect(380, 500, 700, 880)
    return [dict(f0=F['label_out'], f1=note - 2, txt='OUTSIDE: REAL BOB — INSIDE: UNKNOWN ENTITY', at=(540, 360), target=tg)]


# =============================================================================================== SHOT 5A / 5B: the TV feed (5 s late)
def s5(cv, f, t):
    if f < F['s5b']:
        u = (f - F['s5a']) / (F['s5b'] - F['s5a'])
        z, cx, cy = 1.2 + 0.45 * ease(u), 540.0, 867 - 30 * u
    else:
        u = (f - F['s5b']) / (F['s5c'] - F['s5b'])
        e = ease(min(1.0, u * 1.7))
        z, cx, cy = 1.65 + 0.75 * e, 540 + 160 * e, 837 + 23 * e
    v = View(z, cx, cy, sw=sway(t, 0.5), sh=shake(f, F['s5a'], 8, 12))
    v.begin(cv)
    draw_plate(cv, 'tvwall')
    cv.save(); cv.translate(140, 612); cv.clipRect(R(0, 0, 800, 450))
    if f < F['feed']:
        cv.drawRect(R(0, 0, 800, 450), paint('#0A0A0E'))
        rng = np.random.default_rng(f)
        for _ in range(1400):
            x, y = rng.uniform(0, 800), rng.uniform(0, 450)
            cv.drawRect(R(x, y, x + rng.uniform(3, 30), y + 3), paint(C('#FFFFFF', rng.uniform(0.2, 1.0))))
    else:
        cam_scene(cv, t, f, mode='tv', u=t - T['climb'], you_ang=58 if t < 32.2 else None, badge=1.0 if f >= F['s5b'] else 0.0,
                  static=max(0.0, 1 - (f - F['feed']) / 6.0))
    cv.restore()
    glow(cv, 540, 837, 950, '#FFFFFF' if f < F['feed'] else '#3AE87A', 0.22 if f < F['feed'] else 0.11)
    v.end(cv)
    e2 = ease((f - F['s5b']) / 24.0) if f >= F['s5b'] else 0.0                 # you, watching (over your shoulder)
    ox, oy = -140 * e2 + 5 * math.sin(t * 1.9), 520 * e2 + 4 * math.sin(t * 2.6)
    cv.drawRoundRect(R(-120 + ox, 1700 + oy, 700 + ox, 2300 + oy), 150, 150, paint('#0A0A14'))
    cv.drawCircle(290 + ox, 1590 + oy, 215, paint('#0A0A14'))
    cv.drawPath(poly([(140 + ox, 1440 + oy), (200 + ox, 1330 + oy), (300 + ox, 1372 + oy), (420 + ox, 1350 + oy), (470 + ox, 1470 + oy)]), paint('#0A0A14'))
    cv.drawArc(R(75 + ox, 1375 + oy, 505 + ox, 1805 + oy), -78, 96, False, stroke('#FFFFFF' if f < F['feed'] else '#4AE88A', 9, 0.5))
    if f >= F['label_5s']:
        x = 305 + 187 * 1.0
        tg = v.rect(140 + x - 70, 612 + 384, 140 + x + 70, 612 + 450)
        return [dict(f0=F['label_5s'], f1=F['s5c'], txt='5 SECONDS AGO: IT CRAWLED BEHIND YOU', at=(540, 660), target=tg)]
    return []


def s5c(cv, f, t):
    u = (f - F['s5c']) / (F['s6a'] - F['s5c'])
    v = View(1.55 + 0.17 * u, 470, 1125, sw=sway(t, 0.8))
    lk = keys(f, [(F['s5c'], 0.0), (F['s5c'] + 12, 0.95)])
    you = dict(YOU_POSE, look=(lk, 0.0), brow=1.0, mouth='o', sweat=True, head_turn=0.25 * lk)
    v.begin(cv)
    living_scene(cv, f, t, you=you, bob=None, dent=True, dots=ease((f - F['dots']) / 30.0), tv_col='#6AE89A')
    v.end(cv)
    return []


# =============================================================================================== SHOT 6A: the ankle
def s6a(cv, f, t):
    ring, yank = f >= F['ring'], ease((f - F['yank']) / 9.0, 'out')
    u = (f - F['s6a']) / (F['s6b'] - F['s6a'])
    sh = add(shake(f, F['ring'], 12, 30), shake(f, F['yank'], 9, 16))
    v = View(1.02 + 0.08 * u, 540, 960 + 20 * u, sw=sway(t, 0.5), sh=sh)
    v.begin(cv)
    draw_plate(cv, 'floor')
    glow(cv, 900, 300, 1100, CYAN, (0.34 + 0.16 * math.sin(t * 2 * math.pi * 5)) if ring else 0.10)        # the phone in your hand
    # what waits in the gap: four red pinpricks, listening
    ex = (300 + 70 * math.sin(t * 0.9)) if not ring else 842.0
    for k, (dx, dy) in enumerate(((-16, -12), (16, -12), (-13, 14), (13, 14))):
        cv.drawCircle(ex + dx + 1.2 * math.sin(f * 0.3 + k), 962 + dy, 13, paint(C('#FF1A1A', 0.7), blur=7))
        cv.drawCircle(ex + dx, 962 + dy, 4.2, paint('#FF3A2A'))
    if f >= F['yank']:                                                         # ink creeps out along the floor
        for i, (x0, dxe) in enumerate(((200, 120), (420, -90), (560, 60), (880, -150))):
            k = min(1.0, (f - F['yank']) / 16.0)
            o = 14 * math.sin(f * 0.35 + i)
            _tendril(cv, [(x0, GAP_B - 30), (x0 + 30 + o, GAP_B + 90 * k), (x0 + dxe * 0.5 - o, GAP_B + 150 * k), (x0 + dxe * k, GAP_B + 230 * k)], 15)

    def legs():
        for i, x in enumerate((400.0, 640.0)):
            ox, oy = ((34 * yank, -96 * yank) if i == 1 else (0.0, 0.0))
            trem = 2.5 * math.sin(t * 38 + i) * (1.0 if ring else 0.35)
            cv.drawRoundRect(R(x - 78 + ox + trem, -260, x + 78 + ox + trem, 1108 + oy), 40, 40, paint('#3557A6' if i == 0 else '#2C4A8E'))
            cv.drawRect(R(x - 82 + ox + trem, 1050 + oy, x + 82 + ox + trem, 1108 + oy), paint('#26407E'))
            shoe = R(x - 118 + ox, 1092 + oy, x + 118 + ox, 1262 + oy)
            cv.drawRoundRect(shoe, 70, 70, paint('#F4F4F4' if i == 0 else '#DCDDE6'))
            cv.drawRoundRect(R(x - 118 + ox, 1226 + oy, x + 118 + ox, 1262 + oy), 18, 18, paint('#8E90A0'))
            for j in range(3):
                cv.drawLine(x - 44 + ox, 1128 + j * 26 + oy, x + 44 + ox, 1128 + j * 26 + oy, stroke('#9A9CB0', 6))
    with_ink(cv, 6, legs)
    if ring:                                                                  # the hand: out of the dark, onto your ankle
        k = min(1.0, (f - F['ring'] + 1) / 2.0)
        gx, gy = 742 + 34 * yank, 1096 - 96 * yank
        joints = [(1010, 948), (930 - 40 * (1 - k), 1022), (842, 952)]
        grip = (joints[-1][0] + (gx - joints[-1][0]) * k, joints[-1][1] + (gy - joints[-1][1]) * k)
        long_hand(cv, joints, grip, 1.45, t, wrap=k)
        if k < 1:
            for j in range(6):
                cv.drawLine(1010, 930 + j * 12, grip[0] + 40, grip[1] - 30 + j * 12, stroke('#FFFFFF', 3, 0.25))

    def hanging():                                                            # your hand, hanging by your knee, still holding the phone
        jx = 6 * math.sin(t * 2 * math.pi * 11) if ring else 0.0
        cv.drawRoundRect(R(858 + jx, -300, 962 + jx, 250), 50, 50, paint('#E87A20'))
        cv.drawRoundRect(R(872 + jx, 200, 948 + jx, 330), 36, 36, paint('#F2C29B'))
        cv.save(); cv.translate(910 + jx, 420); cv.rotate(6)
        cv.drawRoundRect(R(-72, -140, 72, 140), 18, 18, paint('#17151D'))
        cv.clipRRect(skia.RRect.MakeRectXY(R(-64, -132, 64, 132), 12, 12), True)
        cv.scale(0.214, 0.214)
        if ring:
            ui_call(cv, t)
        else:
            cv.drawRect(R(-300, -620, 300, 620), paint('#0B0C18'))
        cv.restore()
        for j in range(4):
            cv.drawRoundRect(R(826 + jx, 312 + j * 34, 876 + jx, 340 + j * 34), 14, 14, paint('#F2C29B'))
    with_ink(cv, 5, hanging, bounds=R(800, -320, 1010, 600))
    if ring:                                                                  # the ring, drawn as sound: it hunts by sound
        for j in range(3):
            ph = ((t - T['ring']) * 2.6 + j / 3.0) % 1.0
            rad = 90 + 520 * ph
            cv.drawArc(R(910 - rad, 420 - rad, 910 + rad, 420 + rad), 95, 150, False, stroke('#BFF0FF', 7, 0.6 * (1 - ph)))
    v.end(cv)
    out = [dict(f0=F['ring'], f1=F['s6b'], txt='INCOMING CALL: BOB', at=(560, 420), target=v.rect(826, 270, 994, 570))]
    return out


# =============================================================================================== SHOTS 6B / 7A / 7B: it rises, it unzips
def mimic_state(f, t):
    said = talk(t, WORDS, {'D01'})
    if f < F['unzip']:
        return dict(g=0.15 + 0.02 * math.sin(f * 0.5), jd=0.0, td=0.0, crack=0.35, glitch=0, eye_k=1.0)
    k = min(1.0, (f - F['unzip'] + 1) / 4.0)
    jd = 0.95 * k
    if f >= F['s7a']:
        jd = (0.5 + 0.5 * said) if (TL.LINES.get('D01', (46.3, 50.3))[0] - 0.1 <= t <= TL.LINES.get('D01', (46.3, 50.3))[1] + 0.1) else 0.82 + 0.06 * math.sin(f * 0.21)
    if f >= F['s7b']:
        jd = 0.95 + 0.35 * ease((f - F['s7b']) / 60.0)
    flare = F['box3'] <= f < F['box3'] + 5
    return dict(g=0.15 + 0.85 * k + 0.02 * math.sin(f * 0.33), jd=jd, td=k, crack=0.35 + 0.65 * k,
                glitch=18 if f < F['unzip'] + 6 else (22 if flare else 0), eye_k=2.3 if flare else 1.0)


def pov(cv, f, t, z, cx, cy, hy, s, st, look=(0.0, 0.0), tilt=0.0, sh=(0.0, 0.0), tug=0.0, fingers=1.0, blur=0, red=0.0):
    v = View(z, cx, cy + tug, sw=sway(t, 0.9), sh=sh)
    v.begin(cv)
    draw_plate(cv, 'pov', blur=blur)
    rain(cv, (730, 330, 1010, 1080), t)
    if int(t * 1.5) % 2 == 0:
        cv.drawCircle(1034, 201, 6, paint('#FF3B30')); glow(cv, 1034, 201, 34, '#FF3B30', 0.5)
    fl = tv_flicker(t)
    glow(cv, 200, 1900, 1500, '#FF2838' if red > 0 else '#6AE89A', (0.26 * red + 0.10) * fl)      # the TV behind you
    glow(cv, 620, 1750, 900, CYAN, 0.22)                                                         # your phone
    draw_bob_mimic_puppet(cv, 540, hy + 900 * s, s, st['g'], st['jd'], st['td'], st['crack'], st['glitch'], frame=f, pose=dict(arm_l=(10, -6), arm_r=(24, 4)),
                          look=look, eye_roll=1.0, head_tilt=tilt, under=1.0, rim=0.35 + 0.35 * red, eye_k=st['eye_k'], ink_w=7)
    pov_backrest(cv)
    if fingers > 0:                                                           # one hand hooks over the backrest (the other holds your ankle)
        def fing():
            for k in range(4):
                a = min(1.0, max(0.0, fingers * 4 - k))
                if a <= 0:
                    continue
                x = 322 + k * 46
                cv.drawRoundRect(R(x - 17, 1500 - 46 * a, x + 17, 1500 + 66 * a), 17, 17, paint(SKIN_M if k % 2 == 0 else SKIN_M_SH))
                cv.drawRoundRect(R(x - 12, 1500 + 40 * a, x + 12, 1500 + 66 * a), 8, 8, paint('#2A2238'))
        with_ink(cv, 5, fing, bounds=R(280, 1430, 500, 1590))
    v.end(cv)
    return v


def edge_tendrils(cv, f, amp):
    """Ink tendrils creep in from the frame edges like a living vignette."""
    if amp <= 0.01:
        return
    spec = [((-30, 420), (190, 80), (90, 330), (250, 400)), ((-30, 1350), (200, -60), (110, -300), (270, -330)),
            ((1110, 520), (-200, 70), (-100, 310), (-260, 380)), ((1110, 1420), (-190, -40), (-120, -270), (-280, -300)),
            ((260, -30), (60, 190), (-80, 130), (40, 300)), ((820, -30), (-70, 180), (80, 140), (-30, 310)),
            ((-30, 880), (150, -30), (150, 110), (300, 60)), ((1110, 960), (-150, 40), (-160, -100), (-310, -50))]
    for i, (p0, c1, c2, p3) in enumerate(spec):
        o = math.sin(f * 0.35 + i) * 24.0 * amp
        o2 = math.cos(f * 0.27 + i * 1.3) * 16.0 * amp
        _tendril(cv, [p0, (p0[0] + c1[0] * amp + o * 0.4, p0[1] + c1[1] * amp), (p0[0] + c2[0] * amp - o, p0[1] + c2[1] * amp + o2),
                      (p0[0] + p3[0] * amp + o, p0[1] + p3[1] * amp - o2)], 26)


def s6b(cv, f, t):
    a = F['s6b']
    u = (f - a) / (F['s7a'] - a)
    st = mimic_state(f, t)
    tug = sum(40 * math.exp(-(f - f0) / 5.0) for f0 in (a + 12, a + 40) if f >= f0)
    sh = add(shake(f, a + 12, 8, 10), add(shake(f, a + 40, 8, 10), shake(f, F['unzip'], 16, 38)))
    hy = keys(f, [(a, 1660.0), (a + 68, 1020.0)], 'out')
    red = 1.0 if f >= F['unzip'] else 0.0
    pov(cv, f, t, 1.15 + 0.55 * ease(u), 540, 1000 - 60 * u, hy, 1.25, st, look=(0.0, 0.6), tilt=3 * math.sin(t * 1.1), sh=sh, tug=tug,
        fingers=min(1.0, (f - a) / 14.0), red=red)
    return []


def lunge_pov(cv, f, t):
    """7A (and the base of 7B): its face, inches from the lens."""
    st = mimic_state(f, t)
    if f < F['s7b']:
        u = (f - F['s7a']) / (F['s7b'] - F['s7a'])
        z, s, hy = 1.70 + 0.75 * ease(u), 1.25 + 0.2 * u, 1020 - 30 * u
    else:
        u = (f - F['s7b']) / (NF - F['s7b'])
        z, s, hy = 2.45 + 0.85 * ease(u, 'in'), 1.45 + 0.25 * u, 990 - 40 * u
    lk = (0.25 * math.sin(t * 2.3), 0.5 + 0.2 * math.sin(t * 1.7))
    if F['peek_end'] <= f < F['peek_end'] + 12:                                # all four eyes come back to you
        lk = (-0.9 + 0.9 * ease((f - F['peek_end']) / 10.0), 0.5)
    pov(cv, f, t, z, 540, hy + 40, hy, s, st, look=lk, tilt=4 * math.sin(t * 0.9), sh=shake(f, F['box3'], 6, 14), fingers=0.0, blur=6, red=1.0)
    edge_tendrils(cv, f, ease((f - (F['s7a'] + 36)) / 40.0))
    drip = f - (F['s7a'] + 88)                                                 # a drop of ink falls from its maw onto the lens
    if 0 <= drip < 60 and f < F['peek']:
        k = min(1.0, drip / 8.0)
        y = 1130 + 620 * ease(drip / 14.0, 'in')
        if drip < 14:
            cv.drawOval(R(520, y - 60 * k, 560, y + 30), paint('#030206'))
        else:
            cv.drawOval(R(540 - 160 * min(1.0, (drip - 14) / 6.0), 1700, 540 + 160 * min(1.0, (drip - 14) / 6.0), 1990), paint('#030206'))


def peek(cv, f, t):
    """50.5 s: the real Bob kicks the front door open. One half of its face turns to the noise. Bob has a long shadow."""
    k = f - F['kick']
    op = ease((k - 3) / 6.0, 'out')
    flash = max(0.0, 1 - (k - 3) / 9.0) if k >= 3 else 0.0
    hall_shot(cv, f, t, 1.5, open_=op, bob_door=min(1.0, max(0.0, (k - 6) / 3.0)), flash=0.0, fl=1300.0, sh=shake(f, F['kick'] + 3, 10, 22))
    if flash > 0:
        cv.drawRect(R(0, 0, W, H), paint(C('#DCE6FF', 0.55 * flash), blend=skia.BlendMode.kScreen))
    st = mimic_state(f, t)
    draw_bob_mimic_puppet(cv, 1215, 880 + 900 * 2.2, 2.2, st['g'], 0.7, 1.0, 1.0, 0, frame=f, body=False, look=(-1.0, 0.1), eye_roll=1.0, head_tilt=-12,
                          under=0.8, rim=0.0, ink_w=10, mess=0.35)
    glow(cv, 620, 1750, 900, CYAN, 0.18)


def s7a(cv, f, t):
    if F['peek'] <= f < F['peek_end']:
        a, b = F['peek'], F['peek_end']
        if f < a + 6:
            whip(cv, (f - a + 1) / 7.0, lambda: lunge_pov(cv, f, t), lambda: peek(cv, f, t), -1)
        elif f >= b - 6:
            whip(cv, (f - (b - 6) + 1) / 7.0, lambda: peek(cv, f, t), lambda: lunge_pov(cv, f, t), 1)
        else:
            peek(cv, f, t)
    else:
        lunge_pov(cv, f, t)
    return []


def s7b(cv, f, t):
    lunge_pov(cv, f, t)
    if f >= F['hand']:                                                        # your hand lifts the phone into the frame-0 pose = the loop
        k = ease((f - F['hand']) / (NF - 1 - F['hand']), 'out')
        dark = ease((f - (NF - 14)) / 13.0)
        cv.drawRect(R(0, 0, W, H), paint(C('#05050E', 0.94 * dark)))
        phone_comp_only(cv, f, t, dy=1500 * (1 - k))
    return []


def phone_comp_only(cv, f, t, dy=0.0):
    p = dict(PHONE0)
    tx = 4.5 * math.sin(t * 2 * math.pi * 8.5) + 2 * math.sin(t * 2 * math.pi * 13)
    ty = 3.5 * math.sin(t * 2 * math.pi * 7.3 + 1)
    glow(cv, p['cx'], p['cy'] - 80 + dy, 900, '#E8283A', 0.22 * (1 - dy / 1500.0))
    phone_in_hand(cv, p['cx'] + tx, p['cy'] + ty + dy, p['s'], p['tilt'] + 0.6 * math.sin(t * 40), lambda c: ui_lock(c, t), tremble=4)


SHOT_FN = {'S1A': s1a, 'S1B': s1b, 'S2A': s2, 'S2B': s2, 'S3A': s3a, 'S3B': s3b, 'S4A': s4a, 'S4B': s4b, 'S5A': s5, 'S5B': s5, 'S5C': s5c,
           'S6A': s6a, 'S6B': s6b, 'S7A': s7a, 'S7B': s7b}
VIGN = {'S2A': 0.4, 'S2B': 0.4, 'S4B': 0.5, 'S5A': 0.5, 'S5B': 0.5}


def frame_image(f):
    t = f / FPS
    name, _, _ = TL.shot_at(f)
    srf = skia.Surface(W, H)
    cv = srf.getCanvas()
    cv.clear(skia.ColorBLACK)
    labels = SHOT_FN[name](cv, f, t) or []
    CP.grade(cv, t, vign=VIGN.get(name, 0.58))
    for lb in labels:
        CP.label(cv, f, lb['f0'], lb['f1'], lb['txt'], lb['at'], lb.get('target'), leader=lb.get('leader', True))
    CP.hud(cv, f, t)
    CP.choice_card(cv, f)
    CP.strobe(cv, f)
    CP.glitch_pass(srf, cv, f)
    return srf.makeImageSnapshot()


def draw(f):
    p = os.path.join(OUT, f'{f:04d}.jpg')
    if os.path.exists(p):
        return
    os.makedirs(OUT, exist_ok=True)
    frame_image(f).save(p, skia.kJPEG, 93)


if __name__ == '__main__':
    if '--stills' in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
        d = os.path.join(VIDEO, 'stills'); os.makedirs(d, exist_ok=True)
        for tt in ts:
            frame_image(int(round(tt * FPS))).save(os.path.join(d, f'{tt:06.2f}.jpg'), skia.kJPEG, 88)
        print('STILLS_OK', len(ts))
        sys.exit(0)
    a, b = 0, NF - 1
    if '--frames' in sys.argv:
        a, b = (int(x) for x in sys.argv[sys.argv.index('--frames') + 1].split(','))
    with Pool(4) as pool:
        pool.map(draw, range(a, b + 1), chunksize=6)
    print('RENDER_OK', b - a + 1)
