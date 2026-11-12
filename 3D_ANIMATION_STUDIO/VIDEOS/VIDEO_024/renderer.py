#!/usr/bin/env python3
"""VIDEO_024 "The Taxi" renderer (blueprint section 2). Skia, 1080x1920, 30 fps. One fixed taxi interior, two camera setups:
  A = from the front, looking BACK at you on the back seat (rear window behind you): shots CAB_BACK, TUNNEL.
  B = from the back seat, looking FORWARD (driver's head left, dashboard, meter, vent + ID card, clock 11:47, mirror): METER,
      IDCARD, DRIVER, CTA.
Camera moves are vector transforms (zoom about a focus point) so x2.5 stays sharp. Hidden details: dash clock 11:47; Bob's
crumpled MISSING poster on the back-seat floor (setup A).

    python3 VIDEOS/VIDEO_024/renderer.py [--still JOB:frame ...] [--out DIR] [--procs 4]"""
import argparse
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'twod'))
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
from kit import blink, mouth_open, text  # noqa
import edit_video024 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, s, e = E.B, E.s, E.e
BASE = '#0A080E'                      # skia.Color(10, 8, 14)
STREET = '#F5781E'                    # skia.Color(245, 120, 30)
METER_RED, SICK = '#FF0000', '#32CD32'
DRIVER = dict(cap='#2A2A30', hair='#2A2420', hair_sh='#1A1410', shirt='#3A3A44', shirt_sh='#2A2A32', skin='#C8A088', skin_sh='#A88068')


def talk(t, who):
    return mouth_open(t, E.WORDS, [l['id'] for l in E._T['lines'] if l['id'][0] == who])


_g = (np.random.default_rng(24).normal(128, 40, (512, 512))).clip(0, 255).astype(np.uint8)
GRAIN = skia.Image.fromarray(np.dstack([_g, _g, _g, np.full_like(_g, 255)]))


def grain(cv, t, a=0.07):
    p = skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kOverlay)
    for x in range(-(int(t * 997) % 512), W, 512):
        for y in range(-(int(t * 613) % 512), H, 512):
            cv.drawImage(GRAIN, x, y, skia.SamplingOptions(), p)


class inked:
    def __init__(self, cv, w=5):
        self.cv, self.w = cv, w

    def __enter__(self):
        f = skia.ImageFilters.Merge([skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(14, 12, 26), skia.BlendMode.kSrcIn),
                                                                   skia.ImageFilters.Dilate(self.w, self.w)), None])
        self.cv.saveLayer(None, skia.Paint(ImageFilter=f))

    def __exit__(self, *a):
        self.cv.restore()


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def zoom(cv, sc, fx, fy, center=True):
    """Push in by sc about focus (fx, fy); with center=True the focus also drifts to the frame centre as we push."""
    p = min(1.0, (sc - 1.0) / 1.5) if center else 0.0
    cv.translate(540, 960); cv.scale(sc, sc)
    cv.translate(-(540 + (fx - 540) * p), -(960 + (fy - 960) * p))


def car_shake(cv, t, amp=5.0):
    cv.translate(0, math.sin(t * 20) * amp)                                                   # blueprint: sin(t*20)*5 on Y


# ===================================================================== setup A: looking back at you
def outside_rear(cv, t, r):
    """Through the rear window: night street receding (streetlights rushing away) or, after 29 s, the concrete tunnel."""
    cv.save(); cv.clipRect(r)
    cx, cy = r.centerX(), r.top() + r.height() * 0.45
    if t < B['tunnel']:
        cv.drawRect(r, paint('#000000', shader=lin((0, r.top()), (0, r.bottom()), [C('#0E0A1A'), C('#2A1A2A')])))
        cv.drawPath(poly([(cx - 30, cy), (cx + 30, cy), (r.right(), r.bottom()), (r.left(), r.bottom())]), paint('#1A1820'))
        for k in range(6):                                                                    # streetlights rushing AWAY (shrinking)
            ph = (t * 0.66 + k / 6) % 1.0
            d = 1 - ph
            for side in (-1, 1):
                x = cx + side * (40 + 420 * d)
                y = cy - 30 - 260 * d
                glow(cv, (x, y), 30 + 160 * d, STREET, 0.7 * d)
                cv.drawCircle(x, y, 4 + 14 * d, paint('#FFE6C0'))
    else:
        tunnel(cv, t, r, cx, cy, away=True)
    cv.restore()


def tunnel(cv, t, r, cx, cy, away=False):
    """Concrete tunnel: grey walls + horizontal motion-blurred streaks racing toward the vanishing point (no lights, no exit)."""
    cv.drawRect(r, paint('#2A2A2E'))
    cv.drawCircle(cx, cy, 60, paint('#050506'))                                               # no light at the end
    for k in range(26):
        ph = (t * 1.8 + k / 26) % 1.0
        d = (1 - ph) if away else ph
        ang = k * 2.39
        r0 = 40 + 700 * d * d
        r1 = r0 + 120 + 600 * d
        x0, y0 = cx + math.cos(ang) * r0, cy + math.sin(ang) * r0 * 0.7
        x1, y1 = cx + math.cos(ang) * r1, cy + math.sin(ang) * r1 * 0.7
        cv.drawLine(x0, y0, x1, y1, paint(C('#9A9AA0', 0.6), style='stroke', width=10 + 30 * d, blur=8))


def cab_back(cv, t, arms=False):
    cv.drawRect(skia.Rect(0, 0, W, H), paint(BASE))
    rear = skia.Rect(200, 380, 880, 900)
    outside_rear(cv, t, rear)
    with inked(cv, 5):
        roof = skia.Path(); roof.addRect(skia.Rect(0, 0, W, 900)); roof.addRoundRect(rear, 60, 60)
        roof.setFillType(skia.PathFillType.kEvenOdd)
        cv.drawPath(roof, paint('#16121C'))                                                    # cab roof + C-pillars around the window
        for side in (-1, 1):                                                                    # side windows with passing light
            x0 = 0 if side < 0 else 960
            cv.drawRect(skia.Rect(x0, 420, x0 + 120, 880), paint('#120E18'))
        cv.drawRoundRect(skia.Rect(60, 880, 1020, 1720), 60, 60, paint('#2A2226'))            # back bench
        for x in (300, 780):
            cv.drawRoundRect(skia.Rect(x - 110, 820, x + 110, 960), 40, 40, paint('#342A2E'))  # headrests
        cv.drawRect(skia.Rect(60, 1500, 1020, 1720), paint('#221C20'))                         # seat cushion front
    you = dict(brow=1.0, mouth='o', pupil=0.55, sweat=True, look=(0.0, 0.0), mouth_open=talk(t, 'M'))
    you['lids'] = blink(t, [k * 0.55 + 0.2 for k in range(120)], dur=0.1)                        # rapid blinking
    if arms:
        you.update(arm_r=(150, 70), arm_l=(150, 70), brow=1.0, mouth='open', mouth_open=0.4 + talk(t, 'M'))
    sway = 10 * math.sin(t * 2.3)
    with inked(cv, 7):
        mascot(cv, 540 + sway, 2020, 1.05, legs=False, light_side=-1, rim=STREET, rim_a=0.3, **you)
    cv.drawRect(skia.Rect(0, 1720, W, H), paint('#141016'))                                    # floor
    cv.save(); cv.translate(700, 1810); cv.rotate(-12)                                          # Bob's crumpled MISSING poster (hidden)
    cv.drawPath(blob([(-110, -70), (0, -90), (110, -60), (120, 70), (10, 90), (-115, 75)]), paint('#D8D0C0'))
    text(cv, 'MISSING', 0, -40, 30, '#8A1A1A')
    cv.drawCircle(0, 10, 26, paint('#F2C29B'))
    cv.drawRoundRect(skia.Rect(-26, -2, -4, 14), 4, 4, paint('#1A1A1A', style='stroke', width=3))
    cv.drawRoundRect(skia.Rect(4, -2, 26, 14), 4, 4, paint('#1A1A1A', style='stroke', width=3))
    cv.drawRect(skia.Rect(-30, 36, 30, 70), paint('#2A7A7A'))                                     # teal shirt
    text(cv, 'BOB', 0, 84, 22, '#1A1A1A')
    cv.restore()


def streetlight_pool(cv, t):
    """Every 1.5 s a wide orange light pool sweeps horizontally across your face (passing streetlights)."""
    ph = (t % 1.5) / 1.5
    x = -500 + ph * 2100
    cv.drawOval(skia.Rect(x - 520, 300, x + 520, 1500), paint(C(STREET, 80 / 255), blur=60, blend=skia.BlendMode.kScreen))


def shot_CAB_BACK(cv, t):
    cv.save(); car_shake(cv, t)
    cab_back(cv, t)
    cv.restore()
    streetlight_pool(cv, t)
    shade(cv, (540, 1000), 1100, 0.5)
    grain(cv, t)


def shot_TUNNEL(cv, t):
    """Snap back to the wide back-seat shot: no more streetlights, only the tunnel in the rear window; arms up, defensive."""
    cv.save(); car_shake(cv, t, 7)
    cab_back(cv, t, arms=True)
    cv.restore()
    for k in range(3):                                                                           # grey tunnel strobes across the cab
        ph = (t * 1.8 + k / 3) % 1.0
        cv.drawRect(skia.Rect(-200 + ph * 1500, 0, -60 + ph * 1500, H), paint(C('#C8C8D0', 0.06), blur=30))
    shade(cv, (540, 1000), 1100, 0.55)
    grain(cv, t)


# ===================================================================== setup B: looking forward
DRV_HEAD = (250, 820)          # driver's head (seated, left); his seat back covers him below the shoulders
DRV_S = 0.9
METER_XY = (580, 1060)         # taxi meter on the dash, in the gap between the front seats
VENT_XY = (580, 1222)          # centre air vent with the ID card clipped to it
CLOCK_XY = (880, 1045)         # dash clock 11:47 (hidden detail), above the passenger seat


def windshield(cv, t, r):
    cv.save(); cv.clipRect(r)
    cx, cy = r.centerX() + 40, r.top() + r.height() * 0.48
    if t < B['tunnel']:
        cv.drawRect(r, paint('#000000', shader=lin((0, r.top()), (0, r.bottom()), [C('#0A0814'), C('#1E1626')])))
        cv.drawPath(poly([(cx - 20, cy), (cx + 20, cy), (r.right() + 300, r.bottom()), (r.left() - 300, r.bottom())]), paint('#1E1C24'))
        for k in range(8):                                                                       # lane dashes rushing at us
            ph = (t * 1.5 + k / 8) % 1.0
            y0 = cy + (r.bottom() - cy) * ph * ph
            y1 = cy + (r.bottom() - cy) * min(1.0, (ph + 0.05)) ** 2
            cv.drawLine(cx + (y0 - cy) * 0.15, y0, cx + (y1 - cy) * 0.15, y1, paint('#E8D8A0', style='stroke', width=2 + 18 * ph))
        for k in range(5):                                                                       # streetlights coming at us
            ph = (t * 0.66 + k / 5) % 1.0
            for side in (-1, 1):
                x = cx + side * (30 + 620 * ph * ph)
                y = cy - 20 - 380 * ph * ph
                glow(cv, (x, y), 20 + 200 * ph, STREET, 0.8 * ph)
    else:
        tunnel(cv, t, r, cx, cy)
    cv.restore()


def cab_front(cv, t, monster=0.0, flash_white=0.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint(BASE))
    ws = skia.Rect(60, 230, 1020, 1000)
    windshield(cv, t, ws)
    with inked(cv, 5):
        pth = skia.Path(); pth.addRect(skia.Rect(0, 0, W, 1000)); pth.addRoundRect(ws, 40, 40)
        pth.setFillType(skia.PathFillType.kEvenOdd)
        cv.drawPath(pth, paint('#141018'))
        cv.drawRoundRect(skia.Rect(440, 270, 640, 360), 14, 14, paint('#2A2A30'))                # rear-view mirror
        cv.drawRoundRect(skia.Rect(452, 280, 628, 350), 10, 10, paint('#1A1622'))
        cv.drawRect(skia.Rect(0, 980, W, 1400), paint('#000000', shader=lin((0, 980), (0, 1400), [C('#24202A'), C('#141018')])))   # dashboard
        cv.drawRoundRect(skia.Rect(METER_XY[0] - 130, METER_XY[1] - 55, METER_XY[0] + 130, METER_XY[1] + 55), 12, 12, paint('#0A0A0C'))
        cv.drawRoundRect(skia.Rect(VENT_XY[0] - 100, VENT_XY[1] - 55, VENT_XY[0] + 100, VENT_XY[1] + 55), 10, 10, paint('#1A1A20'))
        for k in range(5):
            cv.drawLine(VENT_XY[0] - 90, VENT_XY[1] - 40 + k * 20, VENT_XY[0] + 90, VENT_XY[1] - 40 + k * 20, paint('#3A3A44', style='stroke', width=5))
        cv.drawRoundRect(skia.Rect(CLOCK_XY[0] - 80, CLOCK_XY[1] - 32, CLOCK_XY[0] + 80, CLOCK_XY[1] + 32), 8, 8, paint('#0A100A'))
    if monster < 0.5:                                                                             # the mirror: your eyes (until he turns)
        for side in (-1, 1):
            cv.drawCircle(540 + side * 30, 315, 12, paint('#F4F0E6')); cv.drawCircle(540 + side * 30, 317, 6, paint('#1A1410'))
    remaining = max(0, int(56 - t))                                                               # meter: counting DOWN
    text(cv, f'00:00:{remaining:02d}', METER_XY[0], METER_XY[1] + 22, 62, METER_RED)
    glow(cv, METER_XY, 240, METER_RED, 100 / 255)
    text(cv, '11:47', CLOCK_XY[0], CLOCK_XY[1] + 14, 40, '#7AF07A')                               # hidden detail
    id_card(cv, t)
    driver(cv, t, monster)
    with inked(cv, 5):                                                                            # the front seats (in front of his body)
        cv.drawRoundRect(skia.Rect(20, 1010, 450, 2100), 70, 70, paint('#2A2226'))                # driver seat back
        cv.drawRoundRect(skia.Rect(720, 1080, 1100, 2100), 70, 70, paint('#2A2226'))              # passenger seat back
        cv.drawRoundRect(skia.Rect(790, 990, 1010, 1130), 40, 40, paint('#342A2E'))               # passenger headrest (empty)
    if monster < 0.5:
        glow(cv, (DRV_HEAD[0] + 120, DRV_HEAD[1] + 160), 380, METER_RED, 0.22)                     # red under-light from the meter
    if flash_white > 0:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#F0F4FF', 0.65 * flash_white)))


def id_card(cv, t):
    """Laminated ID clipped to the vent: TAXI LICENSE, NAME: YOU, and a small, corrupted picture of you."""
    x, y = VENT_XY[0], VENT_XY[1] + 10
    cv.save(); cv.translate(x, y); cv.rotate(-4)
    with inked(cv, 3):
        cv.drawRoundRect(skia.Rect(-85, -52, 85, 62), 8, 8, paint('#E8ECF0'))
    cv.drawRect(skia.Rect(-85, -52, 85, -32), paint('#E8B020'))
    text(cv, 'TAXI LICENSE', 0, -37, 15, '#1A1A1A')
    cv.save(); cv.clipRect(skia.Rect(-77, -28, -25, 42))
    mascot(cv, -51, 100, 0.12, brow=1.0, mouth='o', pupil=0.6)                                   # your face...
    for k in range(4):                                                                             # ...corrupted (glitch slices)
        yy = -22 + k * 16
        cv.drawRect(skia.Rect(-77 + (k % 2) * 6, yy, -25 + (k % 2) * 6, yy + 5), paint(C(['#E0342C', '#2A7AE0'][k % 2], 0.6)))
    cv.restore()
    text(cv, 'NAME:', 24, -8, 14, '#5A5A5A'); text(cv, 'YOU', 28, 16, 26, '#C8302A')
    text(cv, '#1147', 28, 42, 14, '#5A5A5A')
    cv.drawRect(skia.Rect(-14, -62, 14, -48), paint('#8A8A94'))                                   # the clip
    cv.restore()


def driver(cv, t, monster):
    """Driver, SEATED, seen from behind: back of head + cap + shoulders (his seat back is drawn over the rest).
    monster=1: the head is turned COMPLETELY backwards and upside down (the back-of-head is not drawn at all)."""
    hx, hy = DRV_HEAD
    under = METER_RED if monster < 0.5 else SICK
    cv.save()
    if monster > 0.5:
        cv.clipRect(skia.Rect(0, hy + 190 * DRV_S, W, H))                                         # body only: no back-of-head
    with inked(cv, 6):
        mascot(cv, hx, hy + DRV_S * 900, DRV_S, view='back', legs=False, light_side=1, rim=under, rim_a=0.7, **DRIVER)
    cv.restore()
    if monster > 0.5:
        cv.save(); cv.clipPath(skia.Path.Circle(hx, hy - 10 * DRV_S, 245 * DRV_S), skia.ClipOp.kIntersect, True)   # head only
        cv.rotate(180, hx, hy)
        with inked(cv, 6):
            mascot(cv, hx, hy + DRV_S * 900, DRV_S, void_eyes=True, mouth='wide', brow=-0.9, legs=False, light_side=1, rim=SICK, rim_a=0.9,
                   **dict(DRIVER, cap=None, skin='#9AA48E', skin_sh='#76806A'))
        cv.restore()
        for k in range(4):                                                                          # twisted, broken neck
            yy = hy + 210 * DRV_S + k * 16
            cv.drawLine(hx - 70, yy, hx + 70, yy - 24, paint(C('#3A1414', 0.85), style='stroke', width=6))
        glow(cv, (hx, hy + 260), 520, SICK, 0.35)                                                    # sickly green under-light


def popup(cv, t, t0, x, y, txt, tip=None):
    k = min(1.0, max(0.0, (t - t0) * 6))
    if k <= 0:
        return
    if tip:
        cv.drawLine(x, y + 40, tip[0], tip[1], paint('#F4F0E6', style='stroke', width=5))
    cv.save(); cv.translate(x, y); cv.scale(k, k); cv.rotate(-3)
    cv.drawRoundRect(skia.Rect(-250, -48, 250, 48), 10, 10, paint('#F4F0E6'))
    cv.drawRoundRect(skia.Rect(-250, -48, 250, 48), 10, 10, paint('#0E0C1A', style='stroke', width=5))
    text(cv, txt, 0, 18, 44, '#C8302A')
    cv.restore()


def shot_METER(cv, t):
    """Slow dolly-in 1.0 -> 1.4 on the meter + the back of the driver's head; label at 11.0 s."""
    u = ease((t - B['meter']) / (B['idcard'] - B['meter']))
    sc = 1.0 + 0.4 * u
    cv.save(); car_shake(cv, t, 3)
    zoom(cv, sc, (DRV_HEAD[0] + METER_XY[0]) / 2, (DRV_HEAD[1] + METER_XY[1]) / 2 + 40)
    cab_front(cv, t)
    remaining = max(0, int(56 - t))
    popup(cv, t, 11.0, METER_XY[0] - 60, METER_XY[1] - 230, f'COUNTDOWN: 00:00:{remaining:02d}', tip=(METER_XY[0], METER_XY[1] - 60))
    cv.restore()
    shade(cv, (540, 960), 1100, 0.5)
    grain(cv, t)


def shot_IDCARD(cv, t):
    """Pan slightly left + push 1.4 -> 2.0 on the vent; a harsh cold-white flash (passing car) lights the ID on N07."""
    u = ease((t - B['idcard']) / 4.0)
    sc = 1.4 + 0.6 * u
    fx = VENT_XY[0] + 60 - 80 * u
    fl = max(0.0, 1 - abs(t - B['flash'] - 0.15) / 0.35)
    cv.save(); car_shake(cv, t, 3)
    zoom(cv, sc, fx, VENT_XY[1])
    cab_front(cv, t, flash_white=fl * 0.6)
    cv.restore()
    shade(cv, (540, 960), 1100, 0.45)
    grain(cv, t)


def shot_DRIVER(cv, t):
    """Extreme dolly-in 1.0 -> 2.5 on the driver; at 42.5 s exactly: the head is backwards + upside down; green under-light."""
    u = ease((t - B['driver']) / (B['snap'] - B['driver'] + 2.0))
    sc = 1.0 + 1.5 * u
    m = 1.0 if t >= B['snap'] else 0.0
    cv.save(); car_shake(cv, t, 4)
    zoom(cv, sc, DRV_HEAD[0], DRV_HEAD[1] + 40)
    cab_front(cv, t, monster=m)
    cv.restore()
    if m:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C(SICK, 0.08)))
    shade(cv, (540, 960), 1000, 0.55)
    grain(cv, t, 0.09)


def shot_CTA(cv, t):
    """3-second micro-CTA: the monster lunges; the card slams in; each box lights up on 'One', 'Two', 'Three'."""
    u = t - B['cta']
    sc = 2.5 + 0.35 * ease(u / 2.5)
    cv.save(); car_shake(cv, t, 4)
    zoom(cv, sc, DRV_HEAD[0], DRV_HEAD[1] + 40)
    cab_front(cv, t, monster=1.0)
    cv.restore()
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.35)))
    k = min(1.0, u / 0.12)
    cv.save(); cv.translate(540, 980); cv.scale(1.3 - 0.3 * k, 1.3 - 0.3 * k)
    text(cv, 'WHAT DO YOU DO?', 0, -330, 64, '#FFFFFF')
    for i, (lab, tw) in enumerate((('JUMP', B['one']), ('GRAB WHEEL', B['two']), ('CLOSE EYES', B['three']))):
        y = -230 + i * 170
        lit = t >= tw - 0.05
        cv.drawRoundRect(skia.Rect(-420, y, 420, y + 140), 18, 18, paint('#C8302A' if lit else C('#141018', 0.9)))
        cv.drawRoundRect(skia.Rect(-420, y, 420, y + 140), 18, 18, paint('#F4F0E6', style='stroke', width=6))
        cv.drawRoundRect(skia.Rect(-400, y + 20, -300, y + 120), 14, 14, paint('#F4F0E6'))
        text(cv, str(i + 1), -350, y + 100, 80, '#C8302A')
        text(cv, lab, 60, y + 98, 76, '#FFFFFF')
    text(cv, 'COMMENT NOW  ·  FOLLOW FOR PART 2', 0, 300, 40, '#F4F0E6')
    cv.restore()
    grain(cv, t, 0.08)


SHOTS = {k[5:]: v for k, v in dict(globals()).items() if k.startswith('shot_')}


def needed():
    out = []
    for sg in E.SEGMENTS:
        f0, f1 = int(round(sg['t0'] * FPS)), int(round(sg['t1'] * FPS))
        out += [(sg['src'], f) for f in range(f0, f1 + 1)]
    return sorted(set(out))


def draw(job_frame):
    job, f = job_frame
    p = os.path.join(OUT, job, f'{f:04d}.png')
    if os.path.exists(p):
        return
    surf = skia.Surface(W, H)
    SHOTS[job](surf.getCanvas(), f / FPS)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    surf.makeImageSnapshot().save(p, skia.kPNG)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--still', nargs='*', default=None)
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    OUT = a.out
    todo = [(x.split(':')[0], int(x.split(':')[1])) for x in a.still] if a.still else needed()
    with Pool(a.procs) as pool:
        for i, _ in enumerate(pool.imap_unordered(draw, todo, chunksize=4)):
            if i % 400 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
