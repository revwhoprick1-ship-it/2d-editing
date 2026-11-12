"""TEST_3D hybrid compositor (FAST mode): 3D plates (Blender, plates/*.png) + FLAT 2D mascot (Skia puppet).

The look of the reference reels: the WORLD is a real 3D render (perspective, depth of field), the CHARACTERS are flat 2D
cut-outs. Speed rule (CPU-only cloud): Blender renders ONE overscanned still per shot (scene3d.py --plates 1, ~3 min);
everything that moves is 2D here: the camera push/pan (crop of the plate), handheld wobble, the door handle turning,
the lamp flicker, the character. plates.json gives the 3D->plate projection of the feet / head / handle.

    python3 comp2d.py [--frames a,b]      -> frames2d/ALL/####.png  (1080x1920)
"""
import json
import math
import os
import sys
from multiprocessing import Pool

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'twod'))
from flat import C, H, W, mascot, paint, shade  # noqa

FPS, F_B, F_C, F_END = 30, 126, 216, 300
OUT = os.path.join(HERE, 'frames2d', 'ALL')
PL = json.load(open(os.path.join(HERE, 'plates', 'plates.json')))
LAV, WARM, INK, GOLD = '#A8A4E0', '#FFB870', '#0E0C1A', '#E8C060'
HEIGHT_M = 1.6                         # the puppet stands 1.6 m tall in the 3D set
_g = (np.random.default_rng(7).normal(128, 40, (512, 512))).clip(0, 255).astype(np.uint8)
GRAIN = skia.Image.fromarray(np.dstack([_g, _g, _g, np.full_like(_g, 255)]))
_scratch = skia.Surface(16, 16).getCanvas()
_img = {}


def plate(key):
    if key not in _img:
        _img[key] = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(os.path.join(HERE, 'plates', f'{key}.png'))).withDefaultMipmaps()
    return _img[key]


def grain(cv, t, a=0.06):
    p = skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kOverlay)
    for x in range(-(int(t * 997) % 512), W, 512):
        for y in range(-(int(t * 613) % 512), H, 512):
            cv.drawImage(GRAIN, x, y, skia.SamplingOptions(), p)


def ease(u, out=False):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3 if out else u * u * (3 - 2 * u)


def keys(f, pts):
    """Eased piecewise value from [(frame, value), ...] (floats or tuples)."""
    if f <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f <= f1:
            e = ease((f - f0) / max(1, f1 - f0))
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * e for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * e
    return pts[-1][1]


HEAD_OFF = {v: tuple(mascot(_scratch, 0, 0, 1.0, view=v)['head']) for v in ('front', 'back')}

# 2D camera per shot: zoom 1 -> K (the plate is K x overscanned), crop centre plate-centre -> end point (plate px)
SHOT = {'A': (0, F_B, (1290, 2050), True), 'B': (F_B, F_C, (605, 1240), False), 'C': (F_C, F_END, (795, 1683), False)}


def view(f):
    key = 'A' if f < F_B else ('B' if f < F_C else 'C')
    m = PL[key]
    f0, f1, end, out = SHOT[key]
    u = ease((f - f0) / (f1 - 1 - f0), out)
    z = 1 + (m['K'] - 1) * u
    cw, ch = m['W'] / z, m['H'] / z
    cx = m['W'] / 2 + (end[0] - m['W'] / 2) * u
    cy = m['H'] / 2 + (end[1] - m['H'] / 2) * u
    sc = W / cw
    cx += (6 * math.sin(f * 0.37) + 3 * math.sin(f * 0.91)) / sc                  # handheld
    cy += (5 * math.sin(f * 0.53 + 1)) / sc
    cx = min(max(cx, cw / 2), m['W'] - cw / 2)
    cy = min(max(cy, ch / 2), m['H'] - ch / 2)
    x0, y0 = cx - cw / 2, cy - ch / 2

    def mp(pt):                         # plate point -> output (x, y, px per metre)
        return (pt[0] - x0) * sc, (pt[1] - y0) * sc, pt[3] * sc
    return key, skia.Rect.MakeXYWH(x0, y0, cw, ch), mp


def blink(f, at):
    return max([max(0.0, 1 - abs(f - b) / 3.0) for b in at] + [0.0])


def pose(f, key, mp):
    t = f / FPS
    m = PL[key]
    common = dict(light_side=-1, rim=LAV, rim_a=0.7)
    if key == 'A':                                                                # back to us, reaching for the handle
        fx, fy, pxm = mp(m['feet'])
        s = pxm * HEIGHT_M / 1150 * (1 + 0.006 * math.sin(t * 5.5))
        e = ease(f / 110)
        P = dict(view='back', arm_r=(12 + 50 * e + 2 * math.sin(t * 23), 22 * e), arm_l=(6, 4), body_lean=-2 * e + 1.2 * math.sin(t * 1.9), **common)
        return fx, fy, s, P, 0.0, pxm
    if key == 'B':                                                                # face close-up (camera at the door)
        hx, hy, pxm = mp(m['head'])
        s = pxm * HEIGHT_M / 1150 * 0.92
        ox, oy = HEAD_OFF['front']
        snap = keys(f, [(F_B + 50, 0.0), (F_B + 55, 1.0)])
        P = dict(view='front', brow=keys(f, [(F_B, 0.4), (F_B + 34, 1.0)]),
                 look=keys(f, [(F_B, (0.15, -0.05)), (F_B + 30, (0.15, -0.05)), (F_B + 36, (-0.85, 0.05)), (F_B + 50, (-0.85, 0.05)), (F_B + 56, (-1.0, 0.1))]),
                 lids=blink(f, (F_B + 22, F_B + 74)), mouth='open' if snap > 0.5 else 'o', mouth_open=0.15 + 0.5 * snap,
                 head_turn=-0.55 * snap, head_tilt=-4 * snap + 1.5 * math.sin(t * 2.2), sweat=True, **common)
        warm = keys(f, [(F_B, 0.18), (F_B + 8, 0.42), (F_B + 30, 0.28), (F_B + 55, 0.5), (F_C, 0.4)])
        return hx - ox * s + 2.5 * math.sin(t * 41), hy - oy * s, s, P, warm, None
    kx, ky, kpm = mp(m['knob'])                                                   # C: over his shoulder, key to the keyhole
    s = kpm * HEIGHT_M / 1150 * 1.05
    target = (kx - 10, ky + 0.09 * kpm)
    hx_o, hy_o = mascot(_scratch, 0, 0, s, view='back', arm_r=(78, 28))['hand_r']   # body placed so the final pose lands on the keyhole
    fx, fy = target[0] - hx_o, target[1] - hy_o
    reach = ease((f - F_C) / 40)
    ang = 10 + 68 * reach + 3 * math.sin(t * 31) * reach
    best = (0, 0, 28)
    P = dict(view='back', arm_r=(ang, best[2] * reach), arm_l=(5, 0), item='keys', **common)
    return fx, fy, s, P, 0.25, None


def lever(cv, key, mp, f):
    """The door handle, drawn in 2D on the plate (it turns by itself from the other side in shot C)."""
    m = PL[key]
    a = keys(f, [(0, 0), (F_C + 40, 0), (F_C + 43, 28), (F_C + 47, 4), (F_C + 51, 34), (F_C + 56, 6), (F_C + 60, 40), (F_END, 42)]) / 42
    px, py, pm = mp(m['knob'])
    t0, t1 = mp(m['tip0']), mp(m['tip42'])
    v0, v1 = (t0[0] - px, t0[1] - py), (t1[0] - px, t1[1] - py)
    a0, a1 = math.atan2(v0[1], v0[0]), math.atan2(v1[1], v1[0])
    da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    ln = math.hypot(*v0) + (math.hypot(*v1) - math.hypot(*v0)) * a
    ang = a0 + da * a
    w = max(3, 0.032 * pm)
    lp = paint(GOLD, style='stroke', width=w)
    lp.setStrokeCap(skia.Paint.kRound_Cap)
    with_ink(cv, max(2, w * 0.18), lambda: (
        cv.drawLine(px, py, px + ln * math.cos(ang), py + ln * math.sin(ang), lp),
        cv.drawCircle(px, py, w * 0.75, paint('#C8A048'))))


def with_ink(cv, w, fn):
    ink = skia.ImageFilters.Merge([skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(14, 12, 26), skia.BlendMode.kSrcIn),
                                                                 skia.ImageFilters.Dilate(w, w)), None])
    cv.saveLayer(None, skia.Paint(ImageFilter=ink))
    fn()
    cv.restore()


def draw(f):
    p = os.path.join(OUT, f'{f:04d}.png')
    if os.path.exists(p):
        return
    t = f / FPS
    srf = skia.Surface(W, H)
    cv = srf.getCanvas()
    key, src, mp = view(f)
    cv.drawImageRect(plate(key), src, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    if key in ('A', 'C'):
        lever(cv, key, mp, f)
    fx, fy, s, P, warm, shadow_pxm = pose(f, key, mp)
    if shadow_pxm:                                                                # contact shadow on the 3D floor
        rx = 0.32 * shadow_pxm
        cv.drawOval(skia.Rect(fx - rx, fy - rx * 0.18, fx + rx, fy + rx * 0.18), paint(C(INK, 0.5), blur=max(4, rx * 0.15)))
    flick = F_B + 41 <= f <= F_B + 43 or F_B + 47 <= f <= F_B + 48                # the lamp flickers

    def puppet():
        cv.saveLayer(None, None)
        mascot(cv, fx, fy, s, **P)
        cv.drawPaint(skia.Paint(Color=C('#BEBAE4'), BlendMode=skia.BlendMode.kModulate))
        if warm > 0:                                                              # warm leak from under the door
            g = skia.GradientShader.MakeLinear([(0, H), (0, H * 0.35)], [C(WARM, warm), C(WARM, 0.0)])
            cv.drawPaint(skia.Paint(Shader=g, BlendMode=skia.BlendMode.kSrcATop))
        cv.restore()
    with_ink(cv, max(4, min(12, 3.2 * s)), puppet)
    if flick:
        cv.drawPaint(skia.Paint(Color=C('#4A4870'), BlendMode=skia.BlendMode.kModulate))
    shade(cv, (540, 900), 1150, 0.5)
    grain(cv, t, 0.06)
    os.makedirs(OUT, exist_ok=True)
    srf.makeImageSnapshot().save(p, skia.kPNG)


if __name__ == '__main__':
    a, b = 0, F_END - 1
    if '--frames' in sys.argv:
        a, b = (int(v) for v in sys.argv[sys.argv.index('--frames') + 1].split(','))
    with Pool(4) as pool:
        pool.map(draw, range(a, b + 1), chunksize=6)
    print('COMP_OK', b - a + 1)
