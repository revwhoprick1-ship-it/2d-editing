"""Small 2D animation kit shared by the 2dEDIT videos: timing helpers, text, one-point perspective camera."""
import math
import os

import skia

from flat import C, H, W, paint, poly

STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
TF_B = skia.Typeface.MakeFromFile(os.path.join(STUDIO, 'ASSETS', 'fonts', 'RobotoCondensed-Bold.ttf'))
TF_R = skia.Typeface.MakeFromFile(os.path.join(STUDIO, 'ASSETS', 'fonts', 'RobotoCondensed-Regular.ttf'))


def text(cv, s, x, y, size, col, align='center', alpha=1.0, blur=0, bold=True, skew=0.0):
    f = skia.Font(TF_B if bold else TF_R, size)
    if skew:
        f.setSkewX(skew)
    w = f.measureText(s)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    cv.drawString(s, x0, y, f, paint(C(col, alpha) if isinstance(col, str) else col, blur=blur))
    return w


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ramp(t, t0, t1, a, b):
    return a + (b - a) * ease((t - t0) / (t1 - t0)) if t1 > t0 else b


def keys(t, ks):
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, a), (t1, b) in zip(ks, ks[1:]):
        if t < t1:
            if isinstance(a, tuple):
                return tuple(ramp(t, t0, t1, x, y) for x, y in zip(a, b))
            return ramp(t, t0, t1, a, b)
    return ks[-1][1]


def blink(t, times, dur=0.14):
    for b in times:
        if b <= t < b + dur:
            return 1 - abs((t - b) / dur * 2 - 1)
    return 0.0


def mouth_open(t, words, lines):
    for w in words:
        if w['line'] in lines and w['start'] <= t < w['end'] + 0.04:
            u = t - w['start']
            return 0.35 + 0.5 * abs(math.sin(2 * math.pi * 5.5 * u + 0.4))
    return 0.0


def dim(cv, a, col='#000000'):
    if a > 0.001:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C(col, min(1.0, a))))


def flicker(t, seed=0, rate=9.0, low=0.15):
    """Broken fluorescent tube: mostly on, random drop-outs."""
    k = int(t * rate) + seed * 31
    r = (math.sin(k * 12.9898 + seed * 78.233) * 43758.5453) % 1.0
    return low if r < 0.22 else 1.0


class Cam:
    """One-point perspective. x right, h up, z forward (facing=+1) or backward (facing=-1)."""

    def __init__(self, z, eye=1.35, vx=540, vy=900, x=0.0, f=1000.0, facing=1):
        self.z, self.eye, self.vx, self.vy, self.x, self.f, self.facing = z, eye, vx, vy, x, f, facing

    def d(self, z):
        return (z - self.z) * self.facing

    def p(self, x, h, z):
        d = max(self.d(z), 0.05)
        return (self.vx + self.f * (x - self.x) * self.facing / d, self.vy - self.f * (h - self.eye) / d)

    def scale(self, z, height=1.25):
        return self.f * height / max(self.d(z), 0.05) / 1150.0


def quad(cam, pts):
    return poly([cam.p(*q) for q in pts])
