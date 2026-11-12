"""TEST_3D hybrid compositor: 3D set (Blender, frames3d/BG) + FLAT 2D mascot (Skia puppet) glued to the 3D camera.

The look of the reference reels: the WORLD is a real 3D render (perspective, parallax, depth of field), the CHARACTERS
are flat 2D cut-outs (ink outline, flat fill, one shadow tone) standing in it. track.json (written by scene3d.py --bg 1)
says where the character's feet / head / the door handle land on screen every frame and how many px one metre is there.

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
BG = os.path.join(HERE, 'frames3d', 'BG')
OUT = os.path.join(HERE, 'frames2d', 'ALL')
TRACK = {r['f']: r for r in json.load(open(os.path.join(HERE, 'track.json')))}
LAV, WARM, INK = '#A8A4E0', '#FFB870', '#0E0C1A'
HEIGHT_M = 1.6                         # the puppet stands 1.6 m tall in the 3D set
_g = (np.random.default_rng(7).normal(128, 40, (512, 512))).clip(0, 255).astype(np.uint8)
GRAIN = skia.Image.fromarray(np.dstack([_g, _g, _g, np.full_like(_g, 255)]))
_scratch = skia.Surface(16, 16).getCanvas()


def grain(cv, t, a=0.06):
    p = skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kOverlay)
    for x in range(-(int(t * 997) % 512), W, 512):
        for y in range(-(int(t * 613) % 512), H, 512):
            cv.drawImage(GRAIN, x, y, skia.SamplingOptions(), p)


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def keys(f, pts):
    """Piecewise-linear (eased) value from [(frame, value), ...]."""
    if f <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f <= f1:
            e = ease((f - f0) / max(1, f1 - f0))
            if isinstance(v0, tuple):
                return tuple(a + (b - a) * e for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * e
    return pts[-1][1]


def head_offset(view):
    r = mascot(_scratch, 0, 0, 1.0, view=view)
    hx, hy = r['head']
    return hx, hy


HEAD_OFF = {v: head_offset(v) for v in ('front', 'back')}


def blink(f, at):
    return max([max(0.0, 1 - abs(f - b) / 3.0) for b in at] + [0.0])


def pose(f):
    """-> (view, feet_x, feet_y, s, pose dict, tint, warm glow alpha, shadow?)"""
    tr = TRACK[f]
    t = f / FPS
    common = dict(light_side=-1, rim=LAV, rim_a=0.7)
    if f < F_B:                                                                   # A: back to us, reaching for the knob
        fx, fy, _, pxm = tr['feet']
        s = pxm * HEIGHT_M / 1150 * (1 + 0.006 * math.sin(t * 5.5))
        e = ease(f / 110)
        P = dict(view='back', arm_r=(12 + 50 * e + 2 * math.sin(t * 23), 22 * e), arm_l=(6, 4), body_lean=-2 * e + 1.2 * math.sin(t * 1.9), **common)
        return fx, fy, s, P, 0.0, True
    if f < F_C:                                                                   # B: face close-up (camera at the door)
        hx, hy, _, pxm = tr['head']
        s = pxm * HEIGHT_M / 1150 * 0.92
        ox, oy = HEAD_OFF['front']
        snap = keys(f, [(F_B + 50, 0.0), (F_B + 55, 1.0)])
        P = dict(view='front', brow=keys(f, [(F_B, 0.4), (F_B + 34, 1.0)]),
                 look=keys(f, [(F_B, (0.15, -0.05)), (F_B + 30, (0.15, -0.05)), (F_B + 36, (-0.85, 0.05)), (F_B + 50, (-0.85, 0.05)), (F_B + 56, (-1.0, 0.1))]),
                 lids=blink(f, (F_B + 22, F_B + 74)), mouth='open' if snap > 0.5 else 'o', mouth_open=0.15 + 0.5 * snap,
                 head_turn=-0.55 * snap, head_tilt=-4 * snap + 1.5 * math.sin(t * 2.2), sweat=True, **common)
        tremble = 2.5 * math.sin(t * 41)
        warm = keys(f, [(F_B, 0.18), (F_B + 8, 0.42), (F_B + 30, 0.28), (F_B + 55, 0.5), (F_C, 0.4)])
        return hx - ox * s + tremble, hy - oy * s, s, P, warm, False
    hx, hy, _, pxm = tr['head']                                                   # C: over his shoulder, key toward the door
    s = pxm * HEIGHT_M / 1150 * 0.85
    ox, oy = HEAD_OFF['back']
    fx, fy = hx + 300 - ox * s, hy - oy * s
    kx, ky = tr['knob'][:2]
    target = (kx - 10, ky + 95)                                                    # the keyhole, just under the handle
    best = None
    reach = ease((f - F_C) / 40)
    for ang in range(30, 150, 5):                                                 # aim the arm: hand + key go to the keyhole
        for elb in range(0, 100, 10):
            r = mascot(_scratch, fx, fy, s, view='back', arm_r=(ang, elb))
            px, py = r['hand_r']
            d = (px - target[0]) ** 2 + (py - target[1]) ** 2
            if best is None or d < best[0]:
                best = (d, ang, elb)
    ang = 10 + (best[1] - 10) * reach
    shake = 3 * math.sin(t * 31) * reach
    P = dict(view='back', arm_r=(ang + shake, best[2] * reach), arm_l=(5, 0), item='keys', **common)
    return fx, fy, s, P, 0.25, False


def draw(f):
    p = os.path.join(OUT, f'{f:04d}.png')
    if os.path.exists(p):
        return
    t = f / FPS
    srf = skia.Surface(W, H)
    cv = srf.getCanvas()
    bg = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(os.path.join(BG, f'{f:04d}.png')))
    cv.drawImageRect(bg, skia.Rect(0, 0, W, H), skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    fx, fy, s, P, warm, shadow = pose(f)
    if shadow:                                                                    # contact shadow on the 3D floor
        rx = 0.32 * TRACK[f]['feet'][3]
        cv.drawOval(skia.Rect(fx - rx, fy - rx * 0.18, fx + rx, fy + rx * 0.18), paint(C(INK, 0.5), blur=max(4, rx * 0.15)))
    w = max(4, min(12, 3.2 * s))
    ink = skia.ImageFilters.Merge([skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(14, 12, 26), skia.BlendMode.kSrcIn),
                                                                 skia.ImageFilters.Dilate(w, w)), None])
    cv.saveLayer(None, skia.Paint(ImageFilter=ink))
    cv.saveLayer(None, None)
    mascot(cv, fx, fy, s, **P)
    flick = F_B + 41 <= f <= F_B + 43 or F_B + 47 <= f <= F_B + 48                # the lamp flickers in the 3D set too
    cv.drawPaint(skia.Paint(Color=C('#5A5880' if flick else '#BEBAE4'), BlendMode=skia.BlendMode.kModulate))
    if warm > 0:                                                                  # warm leak from under the door
        g = skia.GradientShader.MakeLinear([(0, H), (0, H * 0.35)], [C(WARM, warm), C(WARM, 0.0)])
        cv.drawPaint(skia.Paint(Shader=g, BlendMode=skia.BlendMode.kSrcATop))
    cv.restore()
    cv.restore()
    shade(cv, (540, 900), 1150, 0.5)
    grain(cv, t, 0.06)
    os.makedirs(OUT, exist_ok=True)
    srf.makeImageSnapshot().save(p, skia.kPNG)


if __name__ == '__main__':
    a, b = 0, F_END - 1
    if '--frames' in sys.argv:
        a, b = (int(v) for v in sys.argv[sys.argv.index('--frames') + 1].split(','))
    fr = [f for f in range(a, b + 1) if os.path.exists(os.path.join(BG, f'{f:04d}.png'))]
    with Pool(4) as pool:
        pool.map(draw, fr, chunksize=4)
    print('COMP_OK', len(fr))
