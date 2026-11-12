"""VIDEO_025 "The World Ends In 60 Seconds" — 2D layer of the hybrid render (3D plates + flat puppets + 2D sky/FX).

    python3 anim.py [--frames a,b] [--stills 0.2,5.0,...]     -> frames2d/ALL/####.jpg (1080x1920)

Route up the street (+Y, never resets): SH01 you at y=6 -> SH03 run to 15 (past the burning car) -> SH04 15..22 ->
SH05 23.5..25.5 (gravity blinks) -> SH06/08 26..33 (scare car lands at y=34) -> SH10 40..47 -> Mia's door -> ROOM.
Sky = DIRECTIONS (az/el) projected per plate, so the crack is in the same place of the sky in every shot.
"""
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'hybrid'))
sys.path.insert(0, HERE)
from comp import (C, H, W, View, actor, actor_head, blink, ease, grain, keys, load_plates, mascot, occlude, paint,  # noqa: E402
                  shade, sky_dir, talk, view_on, with_ink)
import timeline as TL  # noqa: E402

T, WORDS, FPS = TL.T, TL.WORDS, TL.FPS
OUT = os.path.join(HERE, 'frames2d', 'ALL')
PL = load_plates(os.path.join(HERE, 'plates'))
X0 = 100.0
HS = (X0 - 0.6, -0.25)            # beam / YOU
MS = (X0 - 0.95, -0.35)           # Mia next to him
TB = (X0 - 0.8, 0.72)             # under the table
TF = skia.Typeface.MakeFromFile(os.path.join(STUDIO, 'ASSETS', 'fonts', 'RobotoCondensed-Bold.ttf'))
MIA_H = 1.0                       # Mia is 7: a full head shorter than you
MIA = dict(long_hair=True, shirt='#E8B84A', shirt_sh='#B8862A', pants='#C8607A', pants_sh='#98445A', shoe='#E86A8A', shoe_sh='#B84A6A')
STREET_TINT, ROOM_TINT, BEAM_TINT = '#D2B8D0', '#E2CCD0', '#E8ECF8'
RIM_RED = dict(rim='#FF7A5A', rim_a=0.7, light_side=-1)
RIM_WHITE = dict(rim='#FFFFFF', rim_a=0.9, light_side=1)
RNG = np.random.default_rng(25)


def font(sz):
    return skia.Font(TF, sz)


def text(cv, s, x, y, sz, col, align='c'):
    f = font(sz)
    w = f.measureText(s)
    dx = -w / 2 if align == 'c' else (-w if align == 'r' else 0)
    cv.drawString(s, x + dx, y, f, paint(col))


# =============================================================================================== SKY (directions)
MAIN = [(-8, 2), (-3, 9), (-7, 15), (0, 22), (-4, 30), (3, 38), (-1, 47), (6, 56), (2, 66), (8, 76), (4, 86), (20, 89)]
CRACKS = [dict(p=MAIN, t0=-1, w=1.0),
          dict(p=[(0, 22), (14, 26), (22, 24), (31, 29), (40, 27)], t0=2.0, w=0.6),
          dict(p=[(-4, 30), (-16, 33), (-26, 31), (-38, 36), (-50, 34)], t0=5.0, w=0.6),
          dict(p=[(3, 38), (18, 44), (34, 42), (52, 50), (70, 47)], t0=9.0, w=0.55),
          dict(p=[(6, 56), (-12, 62), (-30, 58), (-52, 66), (-75, 63)], t0=13.0, w=0.55),
          dict(p=[(-60, 4), (-72, 12), (-66, 20), (-84, 30), (-80, 41), (-96, 52), (-90, 64)], t0=6.0, w=0.7),
          dict(p=[(64, 3), (76, 12), (70, 22), (88, 33), (82, 44), (98, 58)], t0=8.0, w=0.7),
          dict(p=[(172, 3), (180, 12), (174, 22), (188, 33), (180, 45), (194, 58), (186, 70)], t0=4.0, w=0.75),
          dict(p=[(-128, 5), (-138, 16), (-132, 28), (-146, 40)], t0=12.0, w=0.6),
          dict(p=[(130, 6), (140, 18), (134, 30), (150, 44)], t0=14.0, w=0.6),
          dict(p=[(20, 89), (60, 84), (100, 86), (140, 82), (180, 85), (220, 83), (260, 86), (300, 84), (340, 87)], t0=20.0, w=0.7),
          dict(p=[(-40, 70), (-60, 78), (-90, 76), (-120, 80)], t0=26.0, w=0.5)]
SHARDS = [dict(az=RNG.uniform(-60, 60) if k < 14 else RNG.uniform(-180, 180), el=RNG.uniform(20, 70), t0=RNG.uniform(-2, 50),
               v=RNG.uniform(6, 14), sz=RNG.uniform(0.6, 1.8), rot=RNG.uniform(-200, 200)) for k in range(26)]


def opening(t):
    return 0.55 + 0.45 * ease(t / T['rip']) + 0.9 * ease((t - T['rip']) / (TL.END - T['rip']))


def sky(cv, v, t, glow=1.0):
    """Gradient (horizon from the view's own horizon), the cracks (3 strokes: glow/mid/core), falling sky shards."""
    p = v.p
    fwd = p.R @ np.array([0, 0, -1.0])
    az = math.degrees(math.atan2(fwd[0], fwd[1]))
    hz = v.D(sky_dir(az, 0.0))
    fp = v.fpx
    yh = hz[1] if hz else H * 0.75
    g = skia.GradientShader.MakeLinear([(0, yh - 2.2 * fp), (0, yh)], [C('#0A0716'), C('#26123A'), C('#5A2030')], [0.0, 1.3 / 2.2, 1.0])
    cv.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=g))
    cv.drawRect(skia.Rect(0, yh - 0.25 * fp, W, yh + 0.1 * fp), paint(C('#8A3030', 0.35 * glow), blur=0.12 * fp))
    op = opening(t)
    fl = 0.85 + 0.15 * math.sin(t * 7.3) * math.sin(t * 2.1 + 1)
    rad = math.radians(1) * fp
    for c in CRACKS:
        if t < c['t0']:
            continue
        grow = min(1.0, (t - c['t0']) / 1.2) if c['t0'] > 0 else 1.0
        pts = c['p'][:max(2, int(len(c['p']) * grow + 0.999))]
        path, pen = skia.Path(), False
        for az_, el_ in pts:
            q = v.D(sky_dir(az_, el_))
            if q is None or abs(q[0]) > 6 * W or abs(q[1]) > 6 * H:
                pen = False
                continue
            if pen:
                path.lineTo(*q)
            else:
                path.moveTo(*q); pen = True
        k = c['w'] * op * glow
        for col, a, wd, bl in (('#FF3A22', 0.5 * fl, 1.5, 0.9), ('#FF8A3A', 0.85, 0.42, 0.25), ('#FFF2D8', 1.0, 0.12, 0.0)):
            pt = paint(C(col, min(1.0, a)), style='stroke', width=max(1.5, wd * k * rad), blur=bl * k * rad if bl else 0)
            pt.setStrokeJoin(skia.Paint.kRound_Join); pt.setStrokeCap(skia.Paint.kRound_Cap)
            cv.drawPath(path, pt)
    for sh in SHARDS:
        dt = t - sh['t0']
        if dt < 0:
            continue
        el = sh['el'] - sh['v'] * dt
        if el < -2:
            continue
        q = v.D(sky_dir(sh['az'], el))
        if q is None or not (-200 < q[0] < W + 200 and -200 < q[1] < H + 200):
            continue
        r = sh['sz'] * rad
        a = math.radians(sh['rot'] * dt)
        tri = [(q[0] + r * math.cos(a + k * 2.2), q[1] + r * math.sin(a + k * 2.2) * 0.8) for k in range(3)]
        path = skia.Path(); path.moveTo(*tri[0]); path.lineTo(*tri[1]); path.lineTo(*tri[2]); path.close()
        cv.drawPath(path, paint(C('#FF8A3A', 0.55), blur=r * 0.5))
        cv.drawPath(path, paint('#1A1028'))


def beam(cv, v, x, y, t, r0=1.6, a=1.0, z0=0.0):
    """A white column of light from the sky onto ground point (x, y): drawn additively (light), wider up high."""
    pts_l, pts_r = [], []
    for z in (z0, z0 + 2, z0 + 8, 30, 90, 260):
        q = v.P((x, y, z))
        if q is None:
            continue
        rr = (r0 + z * 0.025) * q[2]
        pts_l.append((q[0] - rr, q[1])); pts_r.append((q[0] + rr, q[1]))
    if len(pts_l) < 2:
        return
    path = skia.Path(); path.moveTo(*pts_l[0])
    for p_ in pts_l[1:]:
        path.lineTo(*p_)
    for p_ in reversed(pts_r):
        path.lineTo(*p_)
    path.close()
    fl = 0.9 + 0.1 * math.sin(t * 23 + x)
    mids = [((l[0] + r_[0]) / 2, (l[1] + r_[1]) / 2, (r_[0] - l[0]) / 2) for l, r_ in zip(pts_l, pts_r)]
    for wk, al, bk in ((2.4, 0.16, 0.9), (1.0, 0.24, 0.45), (0.32, 0.5, 0.25)):    # glow / body / core: a soft column of light
        path = skia.Path(); path.moveTo(mids[0][0] - mids[0][2] * wk, mids[0][1])
        for mx, my, hw in mids[1:]:
            path.lineTo(mx - hw * wk, my)
        for mx, my, hw in reversed(mids):
            path.lineTo(mx + hw * wk, my)
        path.close()
        yb, yt = mids[0][1], mids[-1][1]
        g = skia.GradientShader.MakeLinear([(0, yb), (0, yt)], [C('#F6FBFF', al * a * fl), C('#CFE6FF', al * a * 0.15)])
        cv.drawPath(path, skia.Paint(Shader=g, BlendMode=skia.BlendMode.kScreen,
                                     MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, max(2.0, mids[0][2] * wk * bk))))
    q = v.P((x, y, z0))
    if q:
        rx = r0 * 1.4 * q[2]
        cv.drawOval(skia.Rect(q[0] - rx, q[1] - rx * 0.3, q[0] + rx, q[1] + rx * 0.3),
                    paint(C('#EAF6FF', 0.5 * a), blur=rx * 0.3, blend=skia.BlendMode.kScreen))


def grade(cv, t, vign=0.55, g=0.06):
    shade(cv, (540, 900), 1150, vign)
    grain(cv, t, g)


def stage(cv, v, t, sky_on=True, blur=0.0):
    if sky_on:
        sky(cv, v, t)
    v.draw(cv, blur=blur)


# =============================================================================================== PROPS (flat, inked)
def car(cv, x, y, L, col, ang=0.0, burn=0.0, t=0.0, flip=1):
    """Flat side-view car centred on its wheels' ground line at (x, y), length L px."""
    def body():
        cv.save(); cv.translate(x, y); cv.rotate(ang); cv.scale(flip, 1)
        h = 0.3 * L
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-L / 2, -h - 0.08 * L, L / 2, -0.08 * L), 0.06 * L, 0.06 * L), paint(col))
        cab = skia.Path(); cab.moveTo(-0.28 * L, -h - 0.07 * L); cab.lineTo(-0.16 * L, -h - 0.26 * L); cab.lineTo(0.16 * L, -h - 0.26 * L)
        cab.lineTo(0.3 * L, -h - 0.07 * L); cab.close()
        cv.drawPath(cab, paint(col))
        for a_, b_ in ((-0.24, -0.02), (0.02, 0.25)):
            win = skia.Path(); win.moveTo(a_ * L, -h - 0.09 * L); win.lineTo(a_ * L + 0.07 * L * (a_ < 0), -h - 0.22 * L)
            win.lineTo(b_ * L - 0.07 * L * (b_ > 0.1), -h - 0.22 * L); win.lineTo(b_ * L, -h - 0.09 * L); win.close()
            cv.drawPath(win, paint('#2A3448'))
        cv.drawRect(skia.Rect(-L / 2, -0.2 * L, L / 2, -0.17 * L), paint(C('#000000', 0.25)))
        cv.drawRect(skia.Rect(L / 2 - 0.05 * L, -0.25 * L, L / 2, -0.19 * L), paint('#FFE08A'))
        cv.drawRect(skia.Rect(-L / 2, -0.25 * L, -L / 2 + 0.04 * L, -0.19 * L), paint('#C8302A'))
        for wx in (-0.3, 0.3):
            cv.drawCircle(wx * L, -0.08 * L, 0.11 * L, paint('#141218'))
            cv.drawCircle(wx * L, -0.08 * L, 0.05 * L, paint('#8A8A96'))
        cv.restore()
    with_ink(cv, max(2.5, L * 0.012), body)
    if burn > 0:
        fire(cv, x, y - 0.42 * L, 0.55 * L * burn, t)


def fire(cv, x, y, s, t):
    cv.drawCircle(x, y, s * 0.9, paint(C('#FF7A2A', 0.35), blur=s * 0.6, blend=skia.BlendMode.kScreen))
    for k in range(6):
        ph = t * (5 + k) + k * 1.7
        fx = x + (k - 2.5) * s * 0.22 + math.sin(ph) * s * 0.05
        hh = s * (0.5 + 0.35 * abs(math.sin(ph * 1.3))) * (1.2 if 1 < k < 4 else 0.8)
        fl = skia.Path(); fl.moveTo(fx - s * 0.13, y); fl.quadTo(fx - s * 0.12, y - hh * 0.6, fx + math.sin(ph) * s * 0.06, y - hh)
        fl.quadTo(fx + s * 0.12, y - hh * 0.6, fx + s * 0.13, y); fl.close()
        cv.drawPath(fl, paint(C('#FF9A2A', 0.95)))
        cv.save(); cv.translate(fx, y); cv.scale(0.55, 0.6); cv.translate(-fx, -y)
        cv.drawPath(fl, paint('#FFE27A'))
        cv.restore()
    for k in range(5):                                                         # smoke
        u = ((t * 0.35 + k / 5) % 1.0)
        cv.drawCircle(x + math.sin(k * 2 + t) * s * 0.3 + u * s * 0.4, y - s * (0.6 + 2.2 * u), s * (0.25 + 0.4 * u),
                      paint(C('#1A1420', 0.45 * (1 - u)), blur=s * 0.15))


def sparks(cv, x, y, s, dt, n=26, seed=3):
    if dt < 0 or dt > 0.9:
        return
    rng = np.random.default_rng(seed)
    for k in range(n):
        a = rng.uniform(-math.pi, 0)
        sp = rng.uniform(0.6, 1.6) * s
        px, py = x + math.cos(a) * sp * dt * 2.2, y + math.sin(a) * sp * dt * 2.2 + 1.8 * s * dt * dt
        cv.drawLine(px, py, px - math.cos(a) * s * 0.06, py - math.sin(a) * s * 0.06,
                    paint(C('#FFD27A', max(0.0, 1 - dt / 0.9)), style='stroke', width=max(2, s * 0.012)))


def dust(cv, t, n=40, seed=5, col='#E8DCC8', a=0.35, fall=True):
    rng = np.random.default_rng(seed)
    for k in range(n):
        x0, sp, sz = rng.uniform(0, W), rng.uniform(60, 220), rng.uniform(2, 6)
        y = (rng.uniform(0, H) + (sp * t if fall else -sp * t)) % H
        cv.drawCircle(x0 + math.sin(t * 1.3 + k) * 12, y, sz, paint(C(col, a)))


def rising(cv, x0, x1, t, n=30, seed=9, a=0.8):
    """Light motes rising up the beam."""
    rng = np.random.default_rng(seed)
    for k in range(n):
        x = rng.uniform(x0, x1); sp = rng.uniform(150, 420); y = (rng.uniform(0, H) - sp * t) % H
        r = rng.uniform(2.5, 7)
        cv.drawCircle(x + math.sin(t * 2 + k) * 8, y, r, paint(C('#FFFFFF', a * rng.uniform(0.4, 1)), blur=r * 0.6, blend=skia.BlendMode.kScreen))


def embers(cv, t, n=26, seed=11):
    rng = np.random.default_rng(seed)
    for k in range(n):
        x, sp = rng.uniform(0, W), rng.uniform(40, 140)
        y = (rng.uniform(0, H) - sp * t) % H
        cv.drawCircle(x + math.sin(t * 1.7 + k) * 30, y, rng.uniform(2, 4.5), paint(C('#FF9A4A', rng.uniform(0.4, 0.9)), blend=skia.BlendMode.kScreen))


def phone_small(cv, hx, hy, s, ang=-15, col='#FF4A3A'):
    def body():
        cv.save(); cv.translate(hx, hy); cv.rotate(ang)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-34 * s, -70 * s, 34 * s, 62 * s), 10 * s, 10 * s), paint('#16141C'))
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-28 * s, -62 * s, 28 * s, 54 * s), 6 * s, 6 * s), paint(col))
        cv.restore()
    with_ink(cv, max(2, 3 * s), body)
    cv.drawCircle(hx, hy, 120 * s, paint(C(col, 0.25), blur=60 * s, blend=skia.BlendMode.kScreen))


def teddy(cv, x, y, s, ang=0):
    def body():
        cv.save(); cv.translate(x, y); cv.rotate(ang)
        cv.drawOval(skia.Rect(-80 * s, -110 * s, 80 * s, 90 * s), paint('#8A5A3A'))
        cv.drawOval(skia.Rect(-45 * s, -60 * s, 45 * s, 60 * s), paint('#B88A5A'))
        for sx in (-1, 1):
            cv.drawCircle(sx * 62 * s, -205 * s, 28 * s, paint('#8A5A3A'))
            cv.drawCircle(sx * 62 * s, -205 * s, 14 * s, paint('#B88A5A'))
        cv.drawCircle(0, -160 * s, 70 * s, paint('#8A5A3A'))
        cv.drawOval(skia.Rect(-30 * s, -150 * s, 30 * s, -112 * s), paint('#C8A07A'))
        cv.drawCircle(0, -140 * s, 9 * s, paint('#1A1010'))
        for sx in (-1, 1):
            cv.drawCircle(sx * 26 * s, -175 * s, 8 * s, paint('#1A1010'))
        cv.restore()
    with_ink(cv, max(2, 4 * s), body)


def tears(cv, head, s, t, turn=0.0, a=1.0, flow=1.0):
    hx, hy = head
    for side in (-1, 1):
        ex, ey = hx + (side * 72 + turn * 60) * s, hy + 40 * s
        u = (t * 0.9 * flow + (0.37 if side > 0 else 0)) % 1.0
        cv.drawPath(skia.Path().moveTo(ex, ey).lineTo(ex + side * 4 * s, ey + 120 * s * u),
                    paint(C('#BFE3FF', 0.55 * a), style='stroke', width=7 * s))
        dy = ey + 125 * s * u
        cv.drawOval(skia.Rect(ex - 9 * s, dy - 12 * s, ex + 9 * s, dy + 12 * s), paint(C('#D8F0FF', 0.9 * a)))


def extra(cv, v, p3, t, col, face=1, view='side', run=True, ph=0.0):
    return actor(cv, v, p3, 1.6, tint=STREET_TINT, view=view, face=face, walk=(t * 2.6 + ph) % 1.0, run=run,
                 shirt=col[0], shirt_sh=col[1], hair=col[2], pants=col[3], pants_sh=col[3], arm_l=(30, 70), arm_r=(30, 70), **RIM_RED)


def _ear_pose():
    best = None
    for a in range(90, 181, 5):
        for b in range(60, 181, 10):
            hx, hy = mascot(skia.Surface(16, 16).getCanvas(), 0, 0, 1.0, view='front', arm_r=(a, b))['hand_r']
            d = (hx - 168) ** 2 + (hy + 860) ** 2
            if best is None or d < best[0]:
                best = (d, a, b)
    return best[1], best[2]


EAR = _ear_pose()


def run_arms(t, k=2.6):
    a = math.sin(2 * math.pi * t * k)
    return dict(arm_l=(25 + 25 * a, 75), arm_r=(25 - 25 * a, 75))


# =============================================================================================== SHOTS
def sh01(cv, t):
    p = PL['ST_LOW']
    you = (0.35, 3.4, 0.0)
    v = view_on(p, t, 0, T['phone1'], 1.12, 1.25, p.project((0.1, 6.0, 2.6))[:2], p.project((0.3, 3.4, 1.9))[:2])
    stage(cv, v, t)
    beam(cv, v, you[0], you[1], t, r0=0.5, a=0.10)                                          # hidden detail: the light is already on you
    u = min(1.0, t / T['crash'])
    if t < T['crash']:
        cp = (-6 + 3.4 * u, 16 - 1.5 * u, 22 * (1 - u * u))
        q = v.P(cp)
        if q:
            car(cv, q[0], q[1], 4.2 * q[2], '#5A6A8A', ang=-160 * u, burn=1.0, t=t)
    for k, (x0, y0, x1, y1, col) in enumerate(((-3.2, 22, -3.0, 28, ('#3A7A6A', '#2A5A4A', '#2A1A14', '#2E3A5A')),
                                                 (2.8, 25, 2.2, 31, ('#8A4A8A', '#6A3A6A', '#C8A060', '#3A3A44')))):
        e = (t * 0.25 + k * 0.3) % 1.0
        extra(cv, v, (x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, 0), t, col, view='back', ph=k * 0.4)
    if t >= T['crash']:
        dt = t - T['crash']
        z = max(0.0, 0.7 * math.sin(min(math.pi, dt * 9)) * math.exp(-dt * 3))
        q = v.P((-2.6, 14.5, z))
        car(cv, q[0], q[1], 4.2 * q[2], '#5A6A8A', ang=-168 + 10 * math.exp(-dt * 4), burn=1.0, t=t)
        sparks(cv, q[0], q[1], 4.2 * q[2], dt)
    flinch = keys(t, [(T['crash'], 0.0), (T['crash'] + 0.12, 1.0), (T['crash'] + 0.8, 0.3), (T['phone1'], 0.2)])
    look = keys(t, [(0, (0.0, -0.9)), (T['crash'], (0.0, -0.9)), (T['crash'] + 0.1, (-0.9, -0.1))])
    r = actor(cv, v, you, tint=STREET_TINT, view='front', look=look, brow=1.0, mouth='open', mouth_open=0.35 + 0.2 * flinch,
              head_turn=-0.35 * flinch, body_lean=-4 * flinch + math.sin(t * 6) * 0.8, crouch=0.1 * flinch,
              arm_r=(35, 115), arm_l=(12 + 25 * flinch, 30), sweat=True, lids=blink(t, 2.3), **RIM_RED)
    if r:
        phone_small(cv, r['hand_r'][0], r['hand_r'][1], r['s'], ang=-10 + 3 * math.sin(t * 40))
    embers(cv, t)
    grade(cv, t)


def phone_screen(cv, rect, t, kind):
    x0, y0, x1, y1 = rect
    cw = x1 - x0
    cx = (x0 + x1) / 2
    if kind in ('alert1', 'alert2'):
        g = skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [C('#3A0A10'), C('#120408')]) if kind == 'alert1' else \
            skia.GradientShader.MakeLinear([(0, y0), (0, y1)], [C('#E8F2FF'), C('#9AB8E0')])
        cv.drawRect(skia.Rect(x0, y0, x1, y1), skia.Paint(Shader=g))
    else:
        cv.drawRect(skia.Rect(x0, y0, x1, y1), paint('#14121C'))
    dark = kind == 'alert2'
    fg = '#14121C' if dark else '#FFFFFF'
    text(cv, '11:59', x0 + 40, y0 + 52, 34, fg, 'l')
    text(cv, '5G  41%', x1 - 40, y0 + 52, 30, fg, 'r')
    if kind == 'alert1':
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + 30, y0 + 100, x1 - 30, y0 + 190), 18, 18), paint('#D8282A'))
        text(cv, 'EMERGENCY ALERT', cx, y0 + 162, 52, '#FFFFFF')
        a1 = min(1.0, max(0.0, (t - T['phone1'] - 0.15) / 0.2))
        text(cv, 'THE WORLD ENDS IN', cx, y0 + 330, 58, C('#FFFFFF', a1))
        text(cv, TL.clock(t), cx, y0 + 560, 210, C('#FF5A4A', a1))
        a2 = min(1.0, max(0.0, (t - TL.w_at('A01', 'this', T['phone1'] + 1.8)) / 0.2))
        text(cv, 'THIS IS NOT A TEST.', cx, y0 + 700, 56, C('#FFFFFF', a2))
        text(cv, 'Selection in progress... 8,118,000,004 scanned', cx, y1 - 70, 24, C('#A88A90', 0.9))
    elif kind == 'mom':
        cv.drawCircle(cx, y0 + 330, 120, paint('#C8A0A8'))
        hp = skia.Path(); hx_, hy_ = cx, y0 + 300
        hp.moveTo(hx_, hy_ + 70); hp.cubicTo(hx_ - 120, hy_ - 10, hx_ - 60, hy_ - 90, hx_, hy_ - 30)
        hp.cubicTo(hx_ + 60, hy_ - 90, hx_ + 120, hy_ - 10, hx_, hy_ + 70); hp.close()
        cv.drawPath(hp, paint('#E84A5A'))
        text(cv, 'MOM', cx, y0 + 560, 96, '#FFFFFF')
        text(cv, 'incoming call', cx, y0 + 620, 36, '#A8A0B0')
        for k, col in ((-1, '#E83A3A'), (1, '#3AC85A')):
            cv.drawCircle(cx + k * 150, y1 - 170, 62, paint(col))
    elif kind == 'fail':
        text(cv, 'MOM', cx, y0 + 420, 90, '#FFFFFF')
        text(cv, 'CALL FAILED', cx, y0 + 540, 70, '#FF4A3A')
        text(cv, 'No network', cx, y0 + 600, 36, '#A8A0B0')
    else:                                                                       # alert2: selection complete -> KEPT: YOU
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(x0 + 30, y0 + 100, x1 - 30, y0 + 190), 18, 18), paint('#14121C'))
        text(cv, 'SELECTION COMPLETE', cx, y0 + 162, 50, '#FFFFFF')
        text(cv, '1 HUMAN', cx, y0 + 370, 120, '#14121C')
        text(cv, 'WILL BE KEPT', cx, y0 + 460, 64, '#14121C')
        if t >= T['kept']:
            k = min(1.0, (t - T['kept']) / 0.12)
            gl = 14 * math.sin(t * 90) if t - T['kept'] < 0.4 else 0
            text(cv, 'KEPT:', cx + gl, y0 + 640, 60, C('#14121C', k))
            text(cv, 'YOU', cx - gl, y0 + 830, 200, C('#D8282A', k))


def phone_insert(cv, t, kind, bg_plate, bg_center3=None, a0=0.0):
    p = PL[bg_plate]
    v = View(p, 1.2, *(p.project(bg_center3)[:2] if bg_center3 else (None, None)))
    stage(cv, v, t, sky_on=True, blur=18)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.35)))
    buzz = (math.sin(t * 95) * 6 if kind in ('alert1', 'alert2', 'mom') else 0.0)
    rise = ease((t - a0) / 0.25, 'out')
    ox, oy = 540 + buzz, 1000 + (1 - rise) * 300
    scr = {'alert1': '#FF3A2A', 'alert2': '#DDEEFF', 'mom': '#6A6AFF', 'fail': '#FF3A2A'}[kind]
    cv.drawCircle(ox, oy - 100, 620, paint(C(scr, 0.25), blur=200, blend=skia.BlendMode.kScreen))

    def palm():                                                                  # behind the phone: sleeve + palm
        cv.save(); cv.translate(ox + 330, oy + 900); cv.rotate(-24)
        cv.drawRoundRect(skia.Rect(-190, -40, 190, 1100), 150, 150, paint('#E87A20'))
        cv.restore()
        cv.drawOval(skia.Rect(ox - 120, oy + 330, ox + 420, oy + 820), paint('#F2C29B'))
    with_ink(cv, 6, palm)

    def body():
        cv.save(); cv.translate(ox, oy); cv.rotate(-4)
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(-330, -640, 330, 640), 70, 70), paint('#18161E'))
        cv.restore()
    with_ink(cv, 6, body)
    cv.save(); cv.translate(ox, oy); cv.rotate(-4)
    cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect(-300, -610, 300, 610), 52, 52), True)
    phone_screen(cv, (-300, -610, 300, 610), t, kind)
    cv.restore()

    def fingers():                                                               # fingers round the left edge, thumb on the right edge
        cv.save(); cv.translate(ox, oy); cv.rotate(-4)
        for k in range(4):
            cv.drawRoundRect(skia.Rect(-395, 130 + k * 100, -262, 212 + k * 100), 40, 40, paint('#F2C29B' if k % 2 == 0 else '#EDBA92'))
        cv.save(); cv.translate(300, 300); cv.rotate(-28)
        cv.drawRoundRect(skia.Rect(-58, -170, 58, 120), 56, 56, paint('#F2C29B'))
        cv.restore()
        cv.restore()
    with_ink(cv, 6, fingers)
    grade(cv, t, 0.5, 0.05)


def ph1(cv, t):
    phone_insert(cv, t, 'alert1', 'ST_LOW', (0.0, 30, 12), T['phone1'])


def ph_mom(cv, t):
    phone_insert(cv, t, 'mom', 'ST_FRONT', (0.0, 20, 6), T['call'])


def ph_fail(cv, t):
    phone_insert(cv, t, 'fail', 'ST_FRONT', (0.0, 20, 6), T['fail'])


def ph2(cv, t):
    phone_insert(cv, t, 'alert2', 'LR_OPEN_UP', None, T['phone2'])
    if t >= T['kept']:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#FFFFFF', max(0.0, 0.5 - (t - T['kept']) * 2))))


def burning_car(cv, v, t, pos=(-2.6, 14.5, 0.0), ang=-168):
    q = v.P(pos)
    if q:
        car(cv, q[0], q[1], 4.2 * q[2], '#5A6A8A', ang=ang, burn=1.0, t=t)


def sh03(cv, t):
    p = PL['ST_LOW']
    u = (t - T['run']) / (T['pano'] - T['run'])
    y = 3.4 + 12.1 * ease(u, 'lin')
    pos = (0.35 - 0.25 * u, y, 0.0)
    hc = p.project((pos[0], pos[1], 1.6))
    v = View(p, 1.12 + 0.12 * ease(u), hc[0], hc[1] - 120)
    stage(cv, v, t)
    turning = t - T['run'] < 0.22
    burning_car(cv, v, t)
    pose = dict(view='front' if turning else 'back', walk=None if turning else (t * 2.7) % 1.0, run=True, look=(-0.8, 0),
                body_lean=4 if not turning else -3, **({} if turning else run_arms(t)))
    if y < 14.5:
        actor(cv, v, pos, tint=STREET_TINT, sweat=True, brow=1.0, mouth='open', **pose, **RIM_RED)
    if y >= 14.5:
        actor(cv, v, pos, tint=STREET_TINT, **pose, **RIM_RED)
    embers(cv, t)
    grade(cv, t)


def sh04(cv, t):
    p = PL['ST_PANO']
    u = (t - T['pano']) / (T['grav'] - T['pano'])
    pos = (-0.6, 15.0 + 7.0 * u, 0.0)
    q = p.project((pos[0], pos[1], 1.2))
    v = View(p, 1.0, q[0] + 120, q[1])
    stage(cv, v, t)
    for k, (y0, col) in enumerate(((21.5, ('#3A6A9A', '#2A4A6A', '#1A1410', '#3A3A4A')), (24.0, ('#9A6A3A', '#6A4A2A', '#5A3A1A', '#2A2A3A')))):
        extra(cv, v, (-5.2, y0 - 3.5 * u * (1 + k * 0.3), 0.0), t, col, face=-1, ph=k * 0.5)
    sh = T['pano'] + 0.45
    if t > sh - 0.25:                                                           # a burning piece of sky hits the sidewalk behind you
        e = min(1.0, (t - (sh - 0.25)) / 0.25)
        z = 18 * (1 - e * e)
        q2 = v.P((-4.6, 21.0 + 1.5 * e, z))
        if q2:
            rr = 0.6 * q2[2]
            cv.drawCircle(q2[0], q2[1], rr * 1.6, paint(C('#FF6A2A', 0.6), blur=rr, blend=skia.BlendMode.kScreen))
            cv.drawPath(skia.Path().addPoly([(q2[0] - rr, q2[1]), (q2[0], q2[1] - rr * 1.3), (q2[0] + rr * 0.8, q2[1] + rr * 0.3)], True),
                        paint('#2A1830'))
            sparks(cv, q2[0], q2[1], 3 * q2[2], t - sh)
    r = actor(cv, v, pos, tint=STREET_TINT, view='side', face=1, walk=(t * 2.9) % 1.0, run=True, arm_l=(40, 80), arm_r=(40, 80),
              body_lean=8, **RIM_RED)
    for k in range(9):                                                          # speed lines
        yy = 300 + k * 170 + 40 * math.sin(k * 3.1)
        xx = (k * 233 - t * 2600) % (W + 600) - 300
        cv.drawLine(xx, yy, xx + 260, yy, paint(C('#FFFFFF', 0.18), style='stroke', width=3))
    embers(cv, t)
    grade(cv, t)
    return r


FLOATERS = [dict(kind='car', p=(-2.6, 30.0), col='#7A4A4A', h=1.4, rot=25), dict(kind='car', p=(2.7, 34.0), col='#4A6A5A', h=2.1, rot=-35),
            dict(kind='bin', p=(-3.6, 27.0), h=1.8, rot=160), dict(kind='bin', p=(3.4, 25.5), h=1.2, rot=-90),
            dict(kind='ball', p=(1.6, 24.0), h=1.6, rot=0)] + \
           [dict(kind='paper', p=(RNG.uniform(-3, 3), RNG.uniform(22, 30)), h=RNG.uniform(0.8, 3.0), rot=RNG.uniform(-300, 300)) for _ in range(10)]


def gravity_z(t, h):
    if t < T['lift']:
        return 0.0
    if t < T['slam']:
        return h * ease((t - T['lift']) / 0.9, 'out') + 0.08 * h * math.sin((t - T['lift']) * 4)
    dt = t - T['slam']
    return max(0.0, h * (1 - dt / 0.06)) if dt < 0.06 else 0.35 * max(0.0, math.sin(dt * 14)) * math.exp(-dt * 6)


def sh05(cv, t):
    p = PL['ST_MID']
    run_u = min(1.0, (t - T['grav']) / (T['lift'] - T['grav']))
    pos_y = 23.5 + 1.2 * run_u + (0.8 * ease((t - T['lift']) / 1.5) if t > T['lift'] else 0)
    zy = gravity_z(t, 1.25)
    pos = (0.1, pos_y, zy)
    v = view_on(p, t, T['grav'], T['front'], 1.05, 1.18, None, p.project((0.1, 25.0, 1.4))[:2])
    stage(cv, v, t)
    items = []
    for f in FLOATERS:
        z = gravity_z(t, f['h'])
        q = v.P((f['p'][0], f['p'][1], z))
        if q:
            items.append((-q[2], f, q, z))
    for _, f, q, z in sorted(items, key=lambda a: a[0]):
        rot = f['rot'] * min(1.0, z / max(0.1, f['h'])) if t < T['slam'] + 0.1 else 0
        if f['kind'] == 'car':
            car(cv, q[0], q[1], 4.2 * q[2], f['col'], ang=rot, t=t)
        elif f['kind'] == 'bin':
            def bn(q=q, rot=rot):
                cv.save(); cv.translate(q[0], q[1]); cv.rotate(rot)
                cv.drawRoundRect(skia.Rect(-0.3 * q[2], -0.85 * q[2], 0.3 * q[2], 0), 8, 8, paint('#4A5A6A'))
                cv.drawRect(skia.Rect(-0.34 * q[2], -0.92 * q[2], 0.34 * q[2], -0.8 * q[2]), paint('#3A4A5A'))
                cv.restore()
            with_ink(cv, 3, bn)
        elif f['kind'] == 'ball':
            with_ink(cv, 3, lambda q=q: cv.drawCircle(q[0], q[1] - 0.12 * q[2], 0.12 * q[2], paint('#D8702A')))
        else:
            cv.save(); cv.translate(q[0], q[1] - 0.2 * q[2]); cv.rotate(rot + t * 40)
            cv.drawRect(skia.Rect(-0.1 * q[2], -0.07 * q[2], 0.1 * q[2], 0.07 * q[2]), paint(C('#EDE6DA', 0.9)))
            cv.restore()
    floating = T['lift'] <= t < T['slam']
    landed = T['slam'] <= t < T['slam'] + 0.55
    pose = dict(view='back', run=True)
    if floating:
        pose.update(walk=(t * 0.8) % 1.0, arm_l=(70 + 25 * math.sin(t * 9), 35), arm_r=(70 + 25 * math.sin(t * 9 + 1.5), 35),
                    body_lean=8 * math.sin(t * 3))
    elif landed:
        pose.update(crouch=0.55 * (1 - (t - T['slam']) / 0.55), arm_l=(40, 30), arm_r=(40, 30))
    else:
        pose.update(walk=(t * 2.7) % 1.0, **run_arms(t))
    q = v.P((pos[0], pos[1], 0))
    if q and zy > 0.02:                                                          # his shadow stays on the road
        rx = 0.35 * q[2] * (1 - min(0.6, zy / 3))
        cv.drawOval(skia.Rect(q[0] - rx, q[1] - rx * 0.2, q[0] + rx, q[1] + rx * 0.2), paint(C('#000000', 0.35), blur=8))
    actor(cv, v, pos, tint=STREET_TINT, **pose, **RIM_RED)
    if T['slam'] <= t < T['slam'] + 0.8:
        dt = t - T['slam']
        for k in range(14):
            a = k / 14 * math.pi
            r = (200 + 700 * dt) * (0.7 + 0.3 * math.sin(k * 7))
            cv.drawCircle(540 + math.cos(a) * r * 1.4, 1500 - math.sin(a) * r * 0.25, 60 + 160 * dt,
                          paint(C('#8A7A8A', 0.35 * (1 - dt / 0.8)), blur=30))
    embers(cv, t)
    grade(cv, t)


SCARE_CAR = (1.9, 34.0)


def sh06_08(cv, t, close=False):
    p = PL['ST_FRONT']
    if t < T['call']:                                                            # 14.6-16.3 run, the car drops, dive
        u = (t - T['front']) / (T['call'] - T['front'])
        dive = keys(t, [(T['scare'] + 0.05, 0.0), (T['scare'] + 0.2, 1.0), (T['scare'] + 0.7, 0.4), (T['call'], 0.0)])
        pos = (-0.4 - 0.9 * ease((t - T['scare']) / 0.3), 26.0 + 2.6 * u, 0.0)
        pose = dict(view='front', walk=(t * 2.7) % 1.0 if dive < 0.3 else None, run=True, crouch=0.35 * dive, body_lean=-14 * dive,
                    brow=1.0, mouth='open', mouth_open=0.4 + 0.5 * dive, look=(0.7 * dive, -0.2), **run_arms(t))
        hc = p.project((pos[0], pos[1], 1.3))
        v = View(p, 1.05 + 0.1 * u, hc[0] + 120, hc[1] - 80)
    elif not close:                                                              # 16.9-20.0 running at camera, phone at the ear
        u = (t - T['run2']) / (T['close'] - T['run2'])
        pos = (-0.9, 30.6 + 3.0 * u, 0.0)
        pose = dict(view='front', walk=(t * 2.5) % 1.0, run=True, brow=1.0, arm_r=EAR, arm_l=(25 + 25 * math.sin(t * 16), 75),
                    mouth_open=talk(t, WORDS, {'M01', 'M02'}), mouth='o', look=(0.2, 0.0), lids=blink(t, 2.7))
        hc = p.project((pos[0], pos[1], 1.2))
        v = View(p, 1.45 + 0.25 * u, hc[0] + 60, hc[1] + 40)
    else:                                                                        # 20.0-22.2 face close-up while running
        u = (t - T['close']) / (T['fail'] - T['close'])
        pos = (-0.9, 33.6 + 0.8 * u, 0.0)
        pose = dict(view='front', walk=(t * 2.0) % 1.0, run=False, brow=1.0, arm_r=EAR, arm_l=(20, 40),
                    mouth_open=talk(t, WORDS, {'M02'}), mouth='frown' if talk(t, WORDS, {'M02'}) == 0 else 'o', look=(0.15, 0.1),
                    lids=blink(t, 2.9, 0.4), head_tilt=math.sin(t * 5) * 2)
        hc = p.project((pos[0], pos[1], 1.3))
        v = View(p, 3.4 + 0.25 * u, hc[0], hc[1] + 30)
    stage(cv, v, t)
    landed = t >= T['scare']
    if landed:
        dt = t - T['scare']
        q = v.P((SCARE_CAR[0], SCARE_CAR[1], 0.0))
    r = actor(cv, v, pos, tint=STREET_TINT, sweat=True, **pose, **RIM_RED)
    if r and pose.get('arm_r') == EAR:
        phone_small(cv, r['hand_r'][0] - 10 * r['s'], r['hand_r'][1], r['s'] * 0.9, ang=8, col='#6A6AFF')
    if close and r:
        tears(cv, r['head'], r['s'], t, a=0.9)
    if T['scare'] - 0.08 <= t:                                                   # the car from the sky (closer than you: drawn after)
        e = min(1.0, (t - (T['scare'] - 0.08)) / 0.08)
        z = 14 * (1 - e) if t < T['scare'] else 0.0
        q = v.P((SCARE_CAR[0], SCARE_CAR[1], z))
        if q:
            car(cv, q[0], q[1], 4.2 * q[2], '#6A4A6A', ang=-14 if landed else -40, burn=min(1.0, max(0.0, (t - T['scare']) / 0.6)), t=t, flip=-1)
            if landed:
                sparks(cv, q[0], q[1], 4.2 * q[2], t - T['scare'], n=40)
    embers(cv, t)
    grade(cv, t)


def sh10(cv, t):
    p = PL['ST_HIGH']
    u = (t - T['high']) / (T['door'] - T['high'])
    you = (0.2, 40.0 + 7.0 * u, 0.0)
    v = view_on(p, t, T['high'], T['door'], 1.0, 1.15, None, p.project((0.0, 46.0, 0.0))[:2])
    stage(cv, v, t)
    actor(cv, v, you, tint=STREET_TINT, view='back', walk=(t * 2.7) % 1.0, run=True, **run_arms(t), **RIM_RED)
    paths = [((-12, 70), (8, 56), 0.0), ((18, 48), (-14, 64), 0.4), ((-30, 40), (-6, 30), 0.9), ((30, 90), (6, 72), 1.4)]
    for k, (a, b, d) in enumerate(paths):
        e = ease((t - T['high'] - d) / 3.2)
        if t < T['high'] + d:
            continue
        beam(cv, v, a[0] + (b[0] - a[0]) * e, a[1] + (b[1] - a[1]) * e, t, r0=2.2, a=min(1.0, (t - T['high'] - d) / 0.4))
    sw = T['sweep']                                                               # one beam sweeps the street, stops ON you, moves on
    bx = keys(t, [(sw - 1.4, -12.0), (sw - 0.15, you[0]), (sw + 0.35, you[0]), (sw + 1.3, 14.0)])
    by = keys(t, [(sw - 1.4, 44.0), (sw - 0.15, you[1]), (sw + 0.35, you[1]), (sw + 1.3, 50.0)])
    if sw - 1.4 <= t <= sw + 1.3:
        beam(cv, v, bx, by, t, r0=1.8, a=1.0)
    embers(cv, t)
    grade(cv, t)


def room_flicker(t):
    return 0.45 if any(a <= t < a + 0.07 for a in (T['door'] + 0.6, T['door'] + 0.9, T['rumble'] + 0.05, T['rumble'] + 0.3, T['rumble'] + 0.42)) else 0.0


def sh11(cv, t):
    p = PL['LR_DOOR']
    u = min(1.0, (t - T['door']) / 1.2)
    pos = (X0 + 1.5 - 0.8 * ease(u), 3.3 - 3.1 * ease(u, 'out'), 0.0)
    v = view_on(p, t, T['door'], T['table'], 1.15, 1.32, p.project((X0 + 1.4, 2.4, 1.2))[:2], p.project((X0 + 0.8, 0.4, 1.1))[:2])
    stage(cv, v, t)
    looking = t > T['door'] + 1.2
    turn = math.sin((t - T['door'] - 1.2) * 5) * 0.6 if looking else 0
    actor(cv, v, pos, tint=ROOM_TINT, view='front', walk=None if looking else (t * 2.7) % 1.0, run=True, brow=1.0, mouth='open',
          mouth_open=0.6 if looking else 0.4, head_turn=turn, look=(turn, 0),
          arm_l=(20, 30) if looking else run_arms(t)['arm_l'], arm_r=(20, 30) if looking else run_arms(t)['arm_r'], sweat=True,
          rim='#FF7A5A', rim_a=0.6, light_side=1)
    dust(cv, t, 50, col='#D8CCC0', a=0.3)
    if room_flicker(t):
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', room_flicker(t))))
    grade(cv, t)


def sh12(cv, t):
    p = PL['LR_TABLE']
    v = view_on(p, t, T['table'], T['hug'], 1.0, 1.1, None, p.project((TB[0], TB[1], 0.45))[:2])
    stage(cv, v, t)
    m = talk(t, WORDS, {'S01'})
    smile = t > TL.LINES.get('S01', (29.5, 29.9))[1] + 0.1
    r = actor(cv, v, (TB[0], TB[1], 0.0), 0.95, tint=ROOM_TINT, view='front', crouch=1.0, look=(0.55, -0.55), brow=0.8,
              mouth='smile' if smile and m == 0 else 'o', mouth_open=m, head_tilt=-6, arm_l=(22, -115), arm_r=(22, -115),
              lids=blink(t, 2.6, 0.5), rim='#FFB870', rim_a=0.5, light_side=1, **MIA)
    if r:
        teddy(cv, r['x'], r['y'] - 300 * r['s'], r['s'] * 0.95, ang=-6)
        hx, hy = r['hand_r']
        for px in (hx, 2 * r['x'] - hx):
            with_ink(cv, 3, lambda px=px: cv.drawCircle(px, hy, 34 * r['s'], paint('#E8BC9C')))
        tears(cv, r['head'], r['s'], t, a=0.8, flow=0.6)
    tx0, tx1, fy = TB[0] - 0.76, TB[0] + 0.76, TB[1] - 0.51                       # the table's front edge + front legs stay IN FRONT of her
    occlude(cv, v, [[(tx0, fy, 0.6), (tx1, fy, 0.6), (tx1, fy, 0.79), (tx0, fy, 0.79)]] +
            [[(TB[0] + dx - 0.035, TB[1] - 0.41, 0.0), (TB[0] + dx + 0.035, TB[1] - 0.41, 0.0), (TB[0] + dx + 0.035, TB[1] - 0.41, 0.74),
              (TB[0] + dx - 0.035, TB[1] - 0.41, 0.74)] for dx in (-0.62, 0.62)])
    dust(cv, t, 25, col='#D8CCC0', a=0.25)
    grade(cv, t)


def sh13(cv, t):
    p = PL['LR_HUG']
    rip = t >= T['rip']
    up = keys(t, [(T['rumble'], 0.0), (T['rumble'] + 0.3, 1.0)])
    v = view_on(p, t, T['hug'], T['open'], 1.0, 1.08, p.project((X0 - 0.5, -0.2, 0.95))[:2], p.project((X0 - 0.48, -0.2, 0.9))[:2])
    stage(cv, v, t)
    you = (X0 - 0.3, -0.1, 0.0)
    mia = (X0 - 0.63, -0.3, 0.0)                                                 # a side hug: both faces to camera
    mq = v.P(mia)
    ms = mq[2] * MIA_H / 1150
    target = (mq[0] - 10 * ms, mq[1] - 520 * ms)                               # his arm goes round her: the hand hides behind her back
    yq = v.P(you)
    ys = yq[2] * 1.6 / 1150
    best = None
    for ang in range(10, 100, 5):
        for elb in range(-80, 61, 10):
            hx, hy = mascot(_SCR, yq[0], yq[1], ys, view='front', arm_r=(ang, elb))['hand_r']
            d = ((2 * yq[0] - hx) - target[0]) ** 2 + (hy - target[1]) ** 2
            if best is None or d < best[0]:
                best = (d, ang, elb)
    r = actor(cv, v, you, tint=ROOM_TINT, view='front', mirror=True, arm_r=(best[1], best[2]), arm_l=(10, 10),
              lids=0.0 if up > 0.5 else 1.0, look=(0, -1.0 * up), brow=0.9, mouth='frown' if up < 0.5 else 'o',
              head_tilt=-9 * (1 - up), rim='#FFB870', rim_a=0.5, light_side=1, body_lean=-2 + math.sin(t * 1.4) * 1.0)
    mr = actor(cv, v, mia, MIA_H, tint=ROOM_TINT, view='front', arm_r=(62, 40), arm_l=(12, 20), lids=0.0 if up > 0.5 else 1.0,
               look=(0, -1.0 * up), brow=0.7, mouth='smile' if up < 0.5 else 'o', head_tilt=10 * (1 - up), rim='#FFB870', rim_a=0.4,
               light_side=1, **MIA)
    if r and mr:
        if up < 0.5:
            tears(cv, r['head'], r['s'], t, a=0.6, flow=0.5)
    if t >= T['rumble']:
        dust(cv, t, 70, col='#D8CCC0', a=0.45)
    if room_flicker(t):
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', room_flicker(t))))
    if rip:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#FFFFFF', max(0.0, 1 - (t - T['rip']) / 0.25))))
    grade(cv, t)


CHUNKS = [dict(p=(X0 + RNG.uniform(-2.5, 2.5), RNG.uniform(-2, 2), 2.8), v=RNG.uniform(5, 12), dx=RNG.uniform(-2, 2), sz=RNG.uniform(0.2, 0.7),
               rot=RNG.uniform(-400, 400), col=['#6E6280', '#9A8296', '#6A4A3E', '#D8CCD8'][k % 4]) for k in range(16)]


def debris(cv, v, t, t0):
    dt = t - t0
    if dt < 0:
        return
    for c in CHUNKS:
        z = c['p'][2] + c['v'] * dt + 2 * dt * dt
        q = v.P((c['p'][0] + c['dx'] * dt, c['p'][1], z))
        if q is None:
            continue
        r = c['sz'] * q[2] * 0.5
        if r < 1 or not (-300 < q[0] < W + 300 and -300 < q[1] < H + 300):
            continue
        def ch(q=q, r=r, c=c):
            cv.save(); cv.translate(q[0], q[1]); cv.rotate(c['rot'] * dt)
            cv.drawPath(skia.Path().addPoly([(-r, -r * 0.4), (r * 0.8, -r * 0.6), (r, r * 0.5), (-r * 0.6, r * 0.6)], True), paint(c['col']))
            cv.restore()
        with_ink(cv, 3, ch)


def floating_you(t):
    if t < T['lock']:
        return 0.0
    z = 0.45 * ease((t - T['lock']) / 1.8, 'out')
    if t > T['wide']:
        z = 0.45 + 0.12 * ease((t - T['wide']) / 4)
    if t > T['choice']:
        z = 0.57 + 0.38 * ease((t - T['choice']) / 3.0, 'in')
    return z + 0.03 * math.sin(t * 2.4)


def pair(cv, v, t, tint, light=None, reach=1.0, mia_view='front'):
    """YOU (mirrored: his reaching hand is screen-left) in the beam + Mia holding that hand."""
    z = floating_you(t)
    yp = v.P((HS[0], HS[1], z))
    mp_ = v.P((MS[0], MS[1], 0.0))
    if yp is None or mp_ is None:
        return None, None
    look_up = T['go'] <= t < T['her']
    you = actor(cv, v, (HS[0], HS[1], z), tint=tint, top_light=light, mirror=True, view='front', arm_r=(28 + 10 * reach, 10),
                arm_l=(35 + 6 * math.sin(t * 2), 20), brow=1.0, look=(0.6, 0.5) if not look_up else (0.0, -1.0),
                mouth='o' if t > T['lock'] else 'open', mouth_open=talk(t, WORDS, {'M03'}) or 0.2, lids=blink(t, 3.3, 1.1),
                **RIM_WHITE)
    if you is None:
        return None, None
    hx, hy = you['hand_r']
    ms = mp_[2] * MIA_H / 1150
    best = None
    for ang in range(100, 181, 5):                                               # Mia's arm aims at his hand
        for elb in (0, 10, 20, 30):
            px, py = mascot(_SCR, mp_[0], mp_[1], ms, view='front', arm_r=(ang, elb))['hand_r']
            d = (px - hx) ** 2 + (py - hy) ** 2
            if best is None or d < best[0]:
                best = (d, ang, elb)
    tip = 1.0 if t > T['wide'] else 0.0
    mia = actor(cv, v, (MS[0], MS[1], 0.04 * tip), MIA_H, tint=tint, top_light=light, view=mia_view, arm_r=(best[1], best[2]),
                arm_l=(25, 30), look=(0.5, -0.9), brow=1.0, head_tilt=-6, mouth='o', mouth_open=talk(t, WORDS, {'S01', 'S02', 'S03', 'S04'}),
                lids=blink(t, 2.9, 0.3), rim='#FFFFFF', rim_a=0.8, light_side=1, **MIA)
    with_ink(cv, 4, lambda: cv.drawCircle(hx, hy, 40 * you['s'], paint('#F2C29B')))
    return you, mia


_SCR = skia.Surface(16, 16).getCanvas()


def sh14_16(cv, t):
    p = PL['LR_OPEN_UP']
    locked = t >= T['lock']
    v = view_on(p, t, T['open'], T['cmia'], 1.05, 1.2, p.project((X0 - 0.75, -0.3, 1.5))[:2], p.project((X0 - 0.7, -0.3, 1.3))[:2])
    stage(cv, v, t)
    for k, (bx, by) in enumerate(((X0 - 40, 60), (X0 + 35, 80), (X0 - 70, 20))):
        beam(cv, v, bx + 6 * math.sin(t * 0.7 + k), by, t, r0=3.0, a=0.6)
    if locked:
        beam(cv, v, HS[0], HS[1], t, r0=0.55, a=min(1.0, (t - T['lock']) / 0.15))
    debris(cv, v, t, T['rip'] + 0.1)
    if not locked:
        z, look = 0.0, (0.0, -1.0)
        you = actor(cv, v, (HS[0], HS[1], 0.0), tint=BEAM_TINT, mirror=True, view='front', arm_r=(32, 20), arm_l=(15, 20), look=look,
                    brow=1.0, mouth='open', mouth_open=0.4, **RIM_RED)
        actor(cv, v, (MS[0], MS[1], 0.0), MIA_H, tint=BEAM_TINT, view='front', arm_r=(160, 10), arm_l=(20, 20), look=(0.3, -1.0), brow=1.0,
              mouth='o', **RIM_RED, **MIA)
        if you:
            with_ink(cv, 4, lambda: cv.drawCircle(you['hand_r'][0], you['hand_r'][1], 36 * you['s'], paint('#F2C29B')))
    else:
        pair(cv, v, t, BEAM_TINT, light=('#FFFFFF', 0.55), reach=min(1.0, (t - T['lock']) / 0.4))
        q = v.P((HS[0], HS[1], 1.0))
        rising(cv, q[0] - 200, q[0] + 200, t, 30)
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#FFFFFF', max(0.0, 0.9 - (t - T['lock']) / 0.35))))
    grade(cv, t)


def close_mia(cv, t, t0, t1, z0, z1, lines):
    p = PL['LR_CLOSE_MIA']
    head = (MS[0], MS[1], 0.8)
    hc = p.project(head)
    v = view_on(p, t, t0, t1, z0, z1, (hc[0], hc[1] + 120), (hc[0], hc[1] + 60))
    stage(cv, v, t, sky_on=False)
    beam(cv, v, HS[0], HS[1], t, r0=0.55, a=0.8)
    m = talk(t, WORDS, lines)
    smile = 'S03' in lines and TL.LINES.get('S03', (0, 0))[0] + 0.5 < t and m < 0.05
    r = actor_head(cv, v, head, MIA_H, tint=BEAM_TINT, top_light=('#FFFFFF', 0.4), view='front', look=(0.25, -1.0), brow=1.0,
                   head_tilt=-7, mouth='smile' if smile else 'o', mouth_open=m, arm_r=(165, 5), arm_l=(20, 25),
                   lids=blink(t, 3.1, 0.7), rim='#FFFFFF', rim_a=0.9, light_side=1, **MIA)
    if r:
        tears(cv, r['head'], r['s'], t, a=1.0, flow=0.7)
    rising(cv, 0, W, t, 40, a=0.6)
    grade(cv, t, 0.5)


def close_you(cv, t, t0, t1, z0, z1, look_up=False):
    p = PL['LR_CLOSE_YOU']
    z = floating_you(t)
    head = (HS[0], HS[1], z + 0.15 + 1.6 * (900 / 1150))
    hc = p.project(head)
    v = view_on(p, t, t0, t1, z0, z1, (hc[0], hc[1] - 80), (hc[0], hc[1] - 40))
    stage(cv, v, t)
    beam(cv, v, HS[0], HS[1], t, r0=0.55, a=1.0)
    m = talk(t, WORDS, {'M03'})
    r = actor_head(cv, v, head, 1.6, tint=BEAM_TINT, top_light=('#FFFFFF', 0.5), view='front', mirror=True,
                   look=(0.0, -1.0) if look_up else (-0.2, 0.9), brow=1.0, mouth='open' if m > 0 else 'frown', mouth_open=m,
                   arm_r=(30, 10), arm_l=(40, 20), lids=blink(t, 3.4, 0.2), head_tilt=-4 if look_up else 5, **RIM_WHITE)
    if r:
        tears(cv, r['head'], r['s'], t, a=0.9)
    rising(cv, 0, W, t, 40, a=0.7)
    grade(cv, t, 0.5)


def wide(cv, t, t0, t1, z0, z1):
    p = PL['LR_OPEN_WIDE']
    c = p.project((X0 - 0.75, -0.3, 1.05))[:2]
    v = view_on(p, t, t0, t1, z0, z1, c, c)
    stage(cv, v, t)
    for k, (bx, by) in enumerate(((X0 - 40, 60), (X0 - 60, -10), (X0 - 25, 110))):
        beam(cv, v, bx + 5 * math.sin(t * 0.6 + k), by, t, r0=3.0, a=0.55)
    beam(cv, v, HS[0], HS[1], t, r0=0.55, a=1.0)
    debris(cv, v, t, T['rip'] + 0.1)
    pair(cv, v, t, BEAM_TINT, light=('#FFFFFF', 0.5))
    q = v.P((HS[0], HS[1], 1.0))
    if q:
        rising(cv, q[0] - 160, q[0] + 160, t, 26)
    grade(cv, t)


def hands(cv, t):
    """'Or I could stay.' His hand (from the light, top-right) still holding hers (bottom-left). His grip slowly slips."""
    p = PL['LR_CLOSE_MIA']
    v = View(p, 1.3)
    stage(cv, v, t, sky_on=False, blur=22)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.3)))
    cv.drawCircle(820, 260, 760, paint(C('#EAF6FF', 0.38), blur=260, blend=skia.BlendMode.kScreen))
    slip = 46 * ease((t - (T['choice'] - 1.0)) / 0.8)
    tr = math.sin(t * 31) * 3
    SK, SK2, SKH, SKH2 = '#F2C8A8', '#E2B090', '#F2C29B', '#E0A880'
    cv.save(); cv.translate(540 + tr, 1000); cv.rotate(-38); cv.scale(1.45, 1.45)

    def her_arm():
        cv.drawRoundRect(skia.Rect(-1150, -52, -140, 52), 52, 52, paint(SK))
        cv.drawRoundRect(skia.Rect(-1150, -66, -470, 66), 60, 60, paint('#E8B84A'))

    def his_fingers():
        for k in range(4):
            x = -150 + k * 52 + slip
            cv.drawRoundRect(skia.Rect(x, -20, x + 44, 128 - abs(k - 1.5) * 10), 22, 22, paint(SKH2 if k % 2 else SKH))

    def her_hand():
        cv.drawRoundRect(skia.Rect(-190, -78, 40, 78), 60, 60, paint(SK))
        cv.drawRoundRect(skia.Rect(-80, -112, 22, -52), 30, 30, paint(SK2))

    def his_arm():
        cv.drawRoundRect(skia.Rect(60 + slip, -70, 1350, 70), 66, 66, paint(SKH))
        cv.drawRoundRect(skia.Rect(540 + slip, -90, 1350, 90), 80, 80, paint('#E87A20'))
        cv.drawRoundRect(skia.Rect(-40 + slip, -100, 210 + slip, 100), 80, 80, paint(SKH))
        cv.drawRoundRect(skia.Rect(-120 + slip, -130, 60 + slip, -72), 30, 30, paint(SKH2))
    for fn in (her_arm, his_fingers, her_hand, his_arm):
        with_ink(cv, 7, fn)
    cv.restore()
    rising(cv, 150, 930, t, 50, a=0.8)
    grade(cv, t, 0.5)


def sh22(cv, t):
    wide(cv, t, T['choice'], TL.END, 1.3, 1.4)
    if t >= T['white']:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#FFFFFF', min(1.0, (t - T['white']) / 0.25))))


SHOT_FN = {
    'SH01': sh01, 'PH1': ph1, 'SH03': sh03, 'SH04': sh04, 'SH05': sh05, 'SH06': sh06_08, 'PH_MOM': ph_mom, 'SH08': sh06_08,
    'SH08B': lambda cv, t: sh06_08(cv, t, close=True), 'PH_FAIL': ph_fail, 'SH10': sh10, 'SH11': sh11, 'SH12': sh12, 'SH13': sh13,
    'SH14': sh14_16, 'PH2': ph2, 'SH16': sh14_16,
    'SH17': lambda cv, t: close_mia(cv, t, T['cmia'], T['cyou'], 1.0, 1.1, {'S02', 'S03'}),
    'SH18': lambda cv, t: close_you(cv, t, T['cyou'], T['cmia2'], 1.0, 1.1),
    'SH19': lambda cv, t: close_mia(cv, t, T['cmia2'], T['wide'], 1.05, 1.18, {'S04'}),
    'SH20': lambda cv, t: wide(cv, t, T['wide'], T['go'], 1.2, 1.3),
    'SH20B': lambda cv, t: close_you(cv, t, T['go'], T['her'], 1.0, 1.08, look_up=True),
    'SH20C': lambda cv, t: close_mia(cv, t, T['her'], T['hands'], 1.08, 1.16, set()),
    'HANDS': hands, 'SH22': sh22}


def draw(f):
    p = os.path.join(OUT, f'{f:04d}.jpg')
    if os.path.exists(p):
        return
    t = f / FPS
    name, _, _ = TL.shot_at(t)
    srf = skia.Surface(W, H)
    cv = srf.getCanvas()
    cv.clear(skia.ColorBLACK)
    SHOT_FN[name](cv, t)
    os.makedirs(OUT, exist_ok=True)
    srf.makeImageSnapshot().save(p, skia.kJPEG, 92)


if __name__ == '__main__':
    if '--stills' in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
        d = os.path.join(HERE, 'stills'); os.makedirs(d, exist_ok=True)
        for t in ts:
            srf = skia.Surface(W, H); cv = srf.getCanvas(); cv.clear(skia.ColorBLACK)
            SHOT_FN[TL.shot_at(t)[0]](cv, t)
            srf.makeImageSnapshot().save(os.path.join(d, f'{t:05.2f}.jpg'), skia.kJPEG, 85)
        print('STILLS_OK', len(ts))
        sys.exit(0)
    a, b = 0, int(TL.END * FPS) - 1
    if '--frames' in sys.argv:
        a, b = (int(x) for x in sys.argv[sys.argv.index('--frames') + 1].split(','))
    with Pool(4) as pool:
        pool.map(draw, range(a, b + 1), chunksize=8)
    print('ANIM_OK', b - a + 1)
