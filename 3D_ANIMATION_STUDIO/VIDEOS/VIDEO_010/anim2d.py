#!/usr/bin/env python3
"""VIDEO_010 "Last Bus · Part 2" — real 2D (2dEDIT). Reuses the bus, passengers and driver from VIDEO_008.

    python3 VIDEOS/VIDEO_010/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
sys.path.insert(0, os.path.join(STUDIO, 'VIDEOS', 'VIDEO_008'))
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video010 as E  # noqa

_spec = importlib.util.spec_from_file_location('anim8', os.path.join(STUDIO, 'VIDEOS', 'VIDEO_008', 'anim2d.py'))
A8 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A8)

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
FOG = '#8A949E'
FOG_T = 1000.0                       # a VIDEO_008 time that is "foggy" (for reused drawing functions)


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


def fog_layers(cv, t, n=7, alpha=0.35, y0=300, dy=220):
    for k in range(n):
        x = ((t * 35 + k * 230) % 1500) - 250
        cv.drawOval(skia.Rect(x - 300, y0 + k * dy, x + 300, y0 + 240 + k * dy), paint(C('#C7CED6', alpha), blur=45))


def ghost(cv, x, y, s, base, alpha=0.6, **pose):
    """A passenger standing in the fog: pale, washed out."""
    cv.saveLayer(None, skia.Paint(Alphaf=alpha, ColorFilter=skia.ColorFilters.Blend(C('#AEB8C2', 0.5).toColor(), skia.BlendMode.kSrcATop)))
    P = dict(base)
    P.update(pose)
    mascot(cv, x, y, s, **P)
    cv.restore()


# ===================================================================== shots
def shot_SMASH(cv, t):
    """Inside the bus: the fogged window (faces outside). Your hammer swings; cracks; it explodes. (Also the loop's last shot.)"""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A2028'))
    wx0, wy0, wx1, wy1 = 70, 260, 1010, 1500
    broke = B['explodes'] <= t < B['loopback']
    cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), paint(FOG, shader=lin((0, wy0), (0, wy1), [C('#9AA4AE'), C('#6E7882')])))
    cv.save(); cv.clipRect(skia.Rect(wx0, wy0, wx1, wy1))
    for k, (sd, r, lk) in enumerate(A8.PASSENGERS[:9]):
        x = 140 + (k % 5) * 190 + (40 if k >= 5 else 0)
        y = 1650 + (k // 5) * 260 - (k % 2) * 40
        ghost(cv, x, y, 0.42 + (k // 5) * 0.12, lk, 0.5, look=(0.0, 0.0), mouth='flat', pupil=0.6,
              arm_r=(150 + 20 * math.sin(t * 5 + k), 20) if not broke else (3, 0))
    fog_layers(cv, t)
    cv.restore()
    # cracks spread from the impact point, then the pane is gone (fog pours in)
    ix, iy = 640, 820
    if B['swing'] - 0.1 <= t < B['loopback']:
        u = ease((t - B['swing']) / max(0.1, B['explodes'] - B['swing']))
        if not broke:
            for k in range(11):
                a = k * 2 * math.pi / 11 + 0.3
                ln = 80 + 520 * u * (0.6 + 0.4 * ((k * 0.37) % 1))
                cv.drawLine(ix, iy, ix + math.cos(a) * ln, iy + math.sin(a) * ln, paint(C('#FFFFFF', 0.85), style='stroke', width=5))
            cv.drawCircle(ix, iy, 30 + 40 * u, paint(C('#FFFFFF', 0.6), style='stroke', width=4))
        else:
            fu = t - B['explodes']
            for k in range(26):                                                    # shards flying
                a = k * 2.39
                r = 60 + fu * (500 + 40 * (k % 7))
                x, y = ix + math.cos(a) * r, iy + math.sin(a) * r + fu * fu * 600
                cv.save(); cv.rotate(fu * 300 + k * 20, x, y)
                cv.drawPath(poly([(x - 30, y), (x, y - 40), (x + 26, y + 10)]), paint(C('#DDE6F2', max(0.0, 0.9 - fu * 0.6))))
                cv.restore()
            fog_layers(cv, t * 2, 5, 0.25 + min(0.3, fu * 0.3), y0=400)
    cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), paint(C('#9FC3FF', 0.05)))
    cv.drawRect(skia.Rect(wx0, wy0, wx1, wy1), paint('#2A333E', style='stroke', width=36))
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#24496E'))
    # the emergency hammer in your hand: wind-up, swing, impact
    ang = keys(t, [(0.0, 4.0), (B['swing'] - 0.3, 14.0), (B['explodes'] - 0.1, 16.0), (B['explodes'], -32.0),
                   (B['explodes'] + 0.4, -26.0), (B['loopback'], -26.0), (B['loopback'] + 0.01, 4.0)])
    if B['mirror'] > t or t >= B['loopback']:
        cv.save()
        cv.translate(960, 1960)
        cv.rotate(ang)
        cv.drawPath(poly([(-60, 0), (60, 0), (40, -560), (-40, -560)]), paint('#F07A1A'))      # sleeve/arm
        cv.drawPath(blob([(-70, -560), (60, -580), (80, -700), (-60, -720)]), paint('#F2C29B'))
        cv.drawRect(skia.Rect(-14, -900, 14, -640), paint('#C8202A'))                          # red handle
        cv.drawPath(poly([(-90, -960), (60, -960), (90, -900), (-90, -880)]), paint('#3A3E46'))  # head
        cv.drawPath(poly([(60, -960), (120, -930), (90, -900)]), paint('#C9CED6'))             # point
        cv.restore()
    shade(cv, (540, 900), 1150, 0.5)


def shot_MIRROR(cv, t):
    """The faceless driver, in the mirror: 'That's not an exit.'"""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0B0F15'))
    A8.windshield(cv, FOG_T, 0, 900, W, H)
    cv.drawRect(skia.Rect(520, 0, 560, 520), paint('#15171B'))
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(80, 420, 1000, 860), 70, 70), paint('#15171B'))
    inner = skia.RRect.MakeRectXY(skia.Rect(110, 450, 970, 830), 54, 54)
    cv.save(); cv.clipRRect(inner, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1C242E'))
    mascot(cv, 560, 1270 + 6 * math.sin(t * 8) * (talk(t, 'D1') > 0), 0.62, faceless=True, head_tilt=-6, light_side=-1, rim='#FFF3D0',
           rim_a=0.4, **A8.DRIVER)
    cv.restore()
    cv.drawRRect(inner, paint(C('#FFFFFF', 0.06)))
    shade(cv, (540, 640), 1000, 0.55)


def fog_road(cv, cam, t, lights=0.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint(FOG, shader=lin((0, 0), (0, H), [C('#A2ACB6'), C('#5E6872')])))
    cv.drawPath(quad(cam, [(-3.0, 0, cam.z + 0.3), (3.0, 0, cam.z + 0.3), (3.0, 0, 60), (-3.0, 0, 60)]), paint('#3A4048'))
    for k in range(12):                                                                          # lane dashes
        z = 2 + k * 3.0
        a, b = cam.p(0, 0.001, z), cam.p(0, 0.001, z + 1.2)
        cv.drawLine(*a, *b, paint(C('#D9D2B0', 0.6), style='stroke', width=max(2, 30 / cam.d(z))))


def shot_ROAD(cv, t):
    """You drop onto the road; the bus keeps going; its tail lights fade into the fog."""
    cam = Cam(-2.0, eye=1.5, vy=900)
    fog_road(cv, cam, t)
    u = max(0.0, t - B['drop'])
    bz = 2.0 + u * 3.5                                                                           # bus pulling away
    if bz < 40:
        a = max(0.0, 1 - u / max(0.5, B['them'] - B['drop']))
        p0, p1 = cam.p(-1.25, 0.3, bz), cam.p(1.25, 3.0, bz)
        cv.drawRect(skia.Rect(p0[0], p1[1], p1[0], p0[1]), paint(C('#1E2833', a)))
        for sd in (-1, 1):
            q = cam.p(sd * 1.0, 0.8, bz)
            cv.drawCircle(*q, max(4, 120 / cam.d(bz)), paint(C('#FF3B2F', a)))
            glow(cv, q, max(20, 600 / cam.d(bz)), '#FF3B2F', 0.45 * a)
        text(cv, '13', *cam.p(0, 2.5, bz), max(10, 300 / cam.d(bz)), C('#FF9A2E', a))
    # you: drop, land, stand up (side view, small, foreground left)
    land = keys(t, [(B['climb'], -220.0), (B['drop'], -220.0), (B['drop'] + 0.35, 0.0)])
    cr = keys(t, [(B['drop'] + 0.3, 0.0), (B['drop'] + 0.4, 0.7), (B['drop'] + 1.2, 0.0)])
    mascot(cv, 300, 1820 + land, 0.6, crouch=cr, look=(0.6, -0.1), brow=1.0, mouth='o', pupil=0.6, sweat=True, light_side=1, rim='#FFFFFF',
           rim_a=0.3, head_turn=0.4)
    fog_layers(cv, t, 7, 0.35)
    shade(cv, (540, 900), 1300, 0.45)


def shot_FOG(cv, t):
    """The passengers, standing in the road. They stop waving. Heads tilt together. They walk towards you."""
    cam = Cam(0.0, eye=1.5, vy=900)
    fog_road(cv, cam, t)
    wave = t < B['stopped']
    tilt = keys(t, [(B['tilts'] - 0.05, 0.0), (B['tilts'] + 0.2, 22.0)])
    adv = max(0.0, t - B['walking'])
    for k, (sd, r, lk) in enumerate(A8.PASSENGERS[:11]):
        x = -2.0 + (k % 6) * 0.8 + (0.4 if k >= 6 else 0)
        z = 4.2 + (k // 6) * 1.4 + (k % 3) * 0.35 - adv * 0.9
        if z < 1.2:
            continue
        s_ = cam.scale(z, 1.65)
        fx, fy = cam.p(x, 0, z)
        ghost(cv, fx, fy, s_, lk, 0.75, look=(0.0, 0.0), mouth='flat', pupil=0.5, brow=-0.2, head_tilt=tilt * (1 if k % 2 else -1),
              arm_r=(150 + 20 * math.sin(t * 5 + k), 20) if wave else (3, 0), walk=((t * 0.9 + k * 0.13) % 1) if adv > 0 else None)
    fog_layers(cv, t, 7, 0.3)
    shade(cv, (540, 900), 1300, 0.45)


def shot_RUN(cv, t):
    """Side-scroll: you run through the fog; shapes keep pace behind you; a bus stop sign appears."""
    u = t - B['run']
    cv.drawRect(skia.Rect(0, 0, W, H), paint(FOG, shader=lin((0, 0), (0, H), [C('#A2ACB6'), C('#5E6872')])))
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#3A4048'))
    for k in range(8):                                                                          # passing lamp posts
        x = ((-u * 900 + k * 420) % 3200) - 400
        cv.drawRect(skia.Rect(x, 600, x + 22, 1500), paint(C('#2A3036', 0.7)))
        glow(cv, (x + 11, 620), 140, '#FFE6B0', 0.25)
    for k in range(3):                                                                          # the ones behind you
        x = 120 - k * 150 + 20 * math.sin(t * 2 + k)
        ghost(cv, x, 1560, 0.48, A8.PASSENGERS[k][2], 0.5, view='side', face=1, walk=((t * 1.4 + k * 0.3) % 1), look=(0.0, 0.0))
    mascot(cv, 620, 1600, 0.6, view='side', face=1, walk=(t * 2.6) % 1, run=True, brow=1.0, mouth='open', mouth_open=0.4, sweat=True,
           light_side=1, rim='#FFFFFF', rim_a=0.3)
    if t >= B['stop'] - 0.2:                                                                     # the stop slides in from the right
        sx = 1300 - 500 * ease((t - B['stop'] + 0.2) / 0.8)
        cv.drawRect(skia.Rect(sx, 700, sx + 16, 1500), paint('#2A3036'))
        cv.drawRect(skia.Rect(sx - 70, 620, sx + 90, 760), paint('#1E5AA8'))
        text(cv, 'BUS', sx + 10, 690, 50, '#FFFFFF')
        text(cv, '13', sx + 10, 745, 50, '#FFFFFF')
    fog_layers(cv, t * 3, 6, 0.3)
    shade(cv, (540, 1000), 1250, 0.45)


def shot_STOP(cv, t):
    """The bus shelter: ROUTE 13, and a MISSING poster with your face."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint(FOG, shader=lin((0, 0), (0, H), [C('#9AA4AE'), C('#5E6872')])))
    cv.drawRect(skia.Rect(60, 260, 1020, 1560), paint(C('#C7CED6', 0.25)))                      # shelter glass
    cv.drawRect(skia.Rect(60, 260, 1020, 1560), paint('#2A3036', style='stroke', width=24))
    cv.drawRect(skia.Rect(40, 220, 1040, 300), paint('#1E5AA8'))
    text(cv, 'ROUTE 13  ·  ELM ST', 540, 280, 60, '#FFFFFF')
    # the poster
    cv.save(); cv.rotate(3, 700, 900)
    cv.drawRect(skia.Rect(470, 480, 930, 1180), paint('#F2EEE2'))
    text(cv, 'MISSING', 700, 590, 100, '#C8202A')
    cv.save(); cv.clipRect(skia.Rect(520, 620, 880, 960))
    cv.drawRect(skia.Rect(520, 620, 880, 960), paint('#B8C2CC'))
    mascot(cv, 700, 1700, 0.9, look=(0.0, 0.0), mouth='smile')
    cv.restore()
    text(cv, 'LAST SEEN ON THE', 700, 1030, 40, '#2A2A2A')
    text(cv, 'ROUTE 13 NIGHT BUS', 700, 1080, 40, '#2A2A2A')
    text(cv, 'CALL IF SEEN', 700, 1140, 36, '#5A5A5A', bold=False)
    cv.restore()
    for k in range(3):                                                                           # old timetable
        cv.drawRect(skia.Rect(120, 520 + k * 60, 380, 550 + k * 60), paint(C('#2A3036', 0.5)))
    text(cv, 'NEXT BUS: 11:58 PM', 250, 760, 34, '#1A1F26')
    cv.drawRect(skia.Rect(0, 1560, W, H), paint('#3A4048'))
    fog_layers(cv, t, 5, 0.22, y0=1200)
    shade(cv, (600, 860), 1150, 0.5)


def shot_PHONE(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#5E6872'))
    fog_layers(cv, t, 7, 0.3)
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(200, 260, 880, 1560), 60, 60)), paint('#101215'))
    cv.drawRect(skia.Rect(230, 330, 850, 1490), paint('#0E1218'))
    text(cv, 'NOV 8, 2027' if t >= B['date'] + 0.3 else 'NOV 8, 2026', 540, 520, 64, '#FF3B2F' if t >= B['date'] + 0.3 else '#FFFFFF')
    text(cv, '12:00', 540, 700, 190, '#FFFFFF')
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(260, 860, 820, 1010), 30, 30)), paint('#1E2632'))
    text(cv, '47 MISSED CALLS', 540, 925, 50, '#FF3B2F')
    text(cv, 'Mom', 540, 985, 44, '#C9CED6', bold=False)
    if t >= B['phone'] + 1.2:
        cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(260, 1040, 820, 1190), 30, 30)), paint('#1E2632'))
        text(cv, 'Mom: please come home', 540, 1130, 40, '#FFFFFF', bold=False)
    buzz = 6 * math.sin(t * 60) if B['phone'] <= t < B['phone'] + 0.5 else 0
    for side in (-1, 1):
        hx = 540 + side * 360 + buzz
        cv.drawPath(blob([(hx - 70, 1200), (hx + 70, 1180), (hx + 90, 1440), (hx - 60, 1500)]), paint('#F2C29B'))
        cv.drawPath(poly([(hx - 80, 1440), (hx + 100, 1420), (hx + 160, H), (hx - 140, H)]), paint('#F07A1A' if side > 0 else '#C85A0C'))
    glow(cv, (540, 800), 700, '#BFE0FF', 0.15)
    shade(cv, (540, 900), 1100, 0.5)


def shot_ARRIVE(cv, t):
    """Two headlights in the fog; the bus front; the doors fold open; the faceless driver."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint(FOG, shader=lin((0, 0), (0, H), [C('#9AA4AE'), C('#4E5862')])))
    u = ease((t - B['lights']) / max(0.5, B['doors'] - B['lights']))
    sc = 0.35 + 0.65 * u
    cx, cy = 540, 1000
    cv.save(); cv.translate(cx, cy); cv.scale(sc, sc)
    cv.drawRect(skia.Rect(-520, -800, 520, 700), paint(C('#1E2833', 0.3 + 0.7 * u)))
    cv.drawRect(skia.Rect(-480, -760, 480, -200), paint(C('#2A3440', 0.5 + 0.5 * u)))                # windshield
    cv.drawRect(skia.Rect(-420, -880, 420, -790), paint('#0E0907'))
    text(cv, 'ROUTE 13 · NEXT STOP: YOU', 0, -815, 54, '#FF3B2F')
    door = ease((t - B['doors']) / 0.6)
    cv.drawRect(skia.Rect(60, -180, 340, 680), paint('#0B0F15'))                                    # door opening (lit inside)
    cv.drawRect(skia.Rect(60, -180, 340, 680), paint(C('#DDE6F2', 0.8 * door)))
    for k in (0, 1):
        x0 = 60 + k * 140
        wdt = 140 * (1 - door)
        cv.drawRect(skia.Rect(x0 + (140 - wdt) * k, -180, x0 + (140 - wdt) * k + wdt, 680), paint('#3A4652'))
    if t >= B['d2'] - 0.6:                                                                          # the driver, leaning into the doorway
        cv.save(); cv.clipRect(skia.Rect(60, -180, 340, 680))
        mascot(cv, 210, 900, 0.75, faceless=True, head_tilt=-14, light_side=-1, rim='#FFF3D0', rim_a=0.5, **A8.DRIVER)
        cv.restore()
    for sd in (-1, 1):                                                                              # headlights
        q = (sd * 420, 600)
        cv.drawCircle(*q, 60, paint('#FFF8E0'))
    cv.restore()
    for sd in (-1, 1):
        glow(cv, (cx + sd * 420 * sc, cy + 600 * sc), 700 * sc, '#FFF3D0', 0.55)
    fog_layers(cv, t, 6, 0.28, y0=500)
    shade(cv, (540, 1000), 1250, 0.4)


def shot_INSIDE(cv, t):
    """Through the doors: every passenger back in their seat, waving. And in YOUR seat... you."""
    A8.bus_interior(cv, FOG_T, 'all', 'stare', you_pose=dict(look=(0.0, 0.0), mouth='smirk', brow=-0.4, lids=0.3, arm_r=(150, 20)))
    # every passenger waves (painted hand flicks over the rows are enough at this size)
    shade(cv, (540, 900), 1300, 0.35)


SHOTS = {'SMASH': shot_SMASH, 'MIRROR': shot_MIRROR, 'ROAD': shot_ROAD, 'FOG': shot_FOG, 'RUN': shot_RUN, 'STOP': shot_STOP,
         'PHONE': shot_PHONE, 'ARRIVE': shot_ARRIVE, 'INSIDE': shot_INSIDE}


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
