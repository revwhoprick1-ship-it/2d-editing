"""Hybrid kit, 2D side (Skia). Pairs with kit3d.py: loads the 3D plates + plates.json, projects any 3D point / sky direction
onto them, does every camera move as a 2D crop (zoom 1..K = sharp, beyond K = soft), and draws the flat puppets
(PIPELINE/twod/flat.py) standing IN the 3D set (feet on the projected floor point, scale from the projected depth).

    from comp import load_plates, View, actor, actor_head, with_ink, grain, talk, ease, keys
"""
import json
import math
import os
import sys

import numpy as np
import skia

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'twod'))
from flat import C, H, W, mascot, paint, shade  # noqa: E402,F401

_g = (np.random.default_rng(7).normal(128, 40, (512, 512))).clip(0, 255).astype(np.uint8)
GRAIN = skia.Image.fromarray(np.dstack([_g, _g, _g, np.full_like(_g, 255)]))
_scratch = skia.Surface(16, 16).getCanvas()
LIN = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)


def ease(u, mode='io'):
    u = max(0.0, min(1.0, u))
    if mode == 'out':
        return 1 - (1 - u) ** 3
    if mode == 'in':
        return u ** 3
    if mode == 'lin':
        return u
    return u * u * (3 - 2 * u)


def keys(t, pts, mode='io'):
    """Eased piecewise value from [(time, value), ...]; values may be numbers or tuples."""
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            e = ease((t - t0) / max(1e-6, t1 - t0), mode)
            if isinstance(v0, (tuple, list)):
                return tuple(a + (b - a) * e for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * e
    return pts[-1][1]


class Plate:
    def __init__(self, d, name, m):
        self.name, self.W, self.H, self.K, self.fpx = name, m['W'], m['H'], m['K'], m['fpx']
        M = np.array(m['mw'], dtype=float)
        self.R, self.T = M[:3, :3], M[:3, 3]
        self.path = os.path.join(d, name + '.png')
        self._img = None

    @property
    def img(self):
        if self._img is None:
            self._img = skia.Image.MakeFromEncoded(skia.Data.MakeFromFileName(self.path)).withDefaultMipmaps()
        return self._img

    def low(self, k):
        if not hasattr(self, '_low'):
            self._low = {}
        if k not in self._low:
            srf = skia.Surface(max(2, self.W // k), max(2, self.H // k))
            srf.getCanvas().drawImageRect(self.img, skia.Rect(0, 0, self.W // k, self.H // k), LIN)
            self._low[k] = srf.makeImageSnapshot()
        return self._low[k]

    def project(self, p):
        pc = self.R.T @ (np.asarray(p, dtype=float) - self.T)
        d = -pc[2]
        if d <= 1e-3:
            return None
        return self.W / 2 + self.fpx * pc[0] / d, self.H / 2 - self.fpx * pc[1] / d, d, self.fpx / d

    def project_dir(self, v):
        dc = self.R.T @ np.asarray(v, dtype=float)
        d = -dc[2]
        if d <= 1e-4:
            return None
        return self.W / 2 + self.fpx * dc[0] / d, self.H / 2 - self.fpx * dc[1] / d


def load_plates(d):
    meta = json.load(open(os.path.join(d, 'plates.json')))
    return {k: Plate(d, k, m) for k, m in meta.items()}


def sky_dir(az, el):
    """az: degrees from +Y toward +X; el: degrees above the horizon."""
    a, e = math.radians(az), math.radians(el)
    return (math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e))


class View:
    """A 2D camera on a plate: z=1 -> whole plate height fills the frame, z=K -> 1:1 pixels. (cx, cy) = plate px centre."""
    def __init__(self, plate, z, cx=None, cy=None):
        self.p = plate
        self.ch = plate.H / z
        self.cw = self.ch * W / H
        cx = plate.W / 2 if cx is None else cx
        cy = plate.H / 2 if cy is None else cy
        cx = min(max(cx, self.cw / 2), plate.W - self.cw / 2) if self.cw <= plate.W else plate.W / 2
        cy = min(max(cy, self.ch / 2), plate.H - self.ch / 2) if self.ch <= plate.H else plate.H / 2
        self.x0, self.y0 = cx - self.cw / 2, cy - self.ch / 2
        self.sc = H / self.ch
        self.z = z

    def map(self, x, y):
        return (x - self.x0) * self.sc, (y - self.y0) * self.sc

    def P(self, p3):
        r = self.p.project(p3)
        if r is None:
            return None
        x, y = self.map(r[0], r[1])
        return x, y, r[3] * self.sc

    def D(self, v):
        r = self.p.project_dir(v)
        return None if r is None else self.map(*r)

    @property
    def fpx(self):
        return self.p.fpx * self.sc

    def draw(self, cv, blur=0.0, alpha=1.0):
        if blur >= 6:                                                          # heavy blur: draw a cached low-res copy (fast + soft)
            k = max(2, int(blur / 3))
            low = self.p.low(k)
            cv.drawImageRect(low, skia.Rect.MakeXYWH(self.x0 / k, self.y0 / k, self.cw / k, self.ch / k), skia.Rect(0, 0, W, H), LIN,
                             skia.Paint(Alphaf=alpha))
            return
        if self.z > self.p.K + 0.05:                                           # beyond 1:1: soften instead of showing pixels
            blur = max(blur, 1.5 * (self.z / self.p.K - 1) + 0.8)
        pnt = skia.Paint(Alphaf=alpha)
        if blur > 0:
            pnt.setImageFilter(skia.ImageFilters.Blur(blur, blur))
        cv.drawImageRect(self.p.img, skia.Rect.MakeXYWH(self.x0, self.y0, self.cw, self.ch), skia.Rect(0, 0, W, H), LIN, pnt)


def view_on(plate, t, t0, t1, z0, z1, c0=None, c1=None, mode='io'):
    """Eased 2D move: zoom z0->z1, centre c0->c1 (plate px; None = plate centre)."""
    u = ease((t - t0) / max(1e-6, t1 - t0), mode)
    c0 = c0 or (plate.W / 2, plate.H / 2)
    c1 = c1 or c0
    return View(plate, z0 + (z1 - z0) * u, c0[0] + (c1[0] - c0[0]) * u, c0[1] + (c1[1] - c0[1]) * u)


_INKF = {}


def _ink_filter(w, ink):
    """Outline = the layer's silhouette in ink colour stamped in 12 directions under it (fast; Skia's Dilate is ~20x slower)."""
    key = (round(w * 2) / 2, ink)
    if key not in _INKF:
        r = key[0]
        black = skia.ImageFilters.ColorFilter(skia.ColorFilters.Blend(skia.Color(*ink), skia.BlendMode.kSrcIn), None)
        offs = [skia.ImageFilters.Offset(r * math.cos(a), r * math.sin(a), black) for a in [k * math.pi / 6 for k in range(12)]]
        _INKF[key] = skia.ImageFilters.Merge(offs + [None])
    return _INKF[key]


def with_ink(cv, w, fn, ink=(14, 12, 26), bounds=None):
    """Everything fn() draws gets a black ink outline. bounds (skia.Rect, canvas space) keeps the layer small = fast."""
    cv.saveLayer(bounds, skia.Paint(ImageFilter=_ink_filter(w, ink)))
    r = fn()
    cv.restore()
    return r


def grain(cv, t, a=0.06):
    p = skia.Paint(Alphaf=a, BlendMode=skia.BlendMode.kOverlay)
    for x in range(-(int(t * 997) % 512), W, 512):
        for y in range(-(int(t * 613) % 512), H, 512):
            cv.drawImage(GRAIN, x, y, skia.SamplingOptions(), p)


HEAD_DY = -900.0                      # puppet head centre above the feet at s=1 (flat.py)


def _puppet(cv, x, y, s, tint, top_light, mirror, ink_w, pose):
    def body():
        cv.saveLayer(None, None)
        if mirror:
            cv.save(); cv.translate(x, 0); cv.scale(-1, 1); cv.translate(-x, 0)
        r = {k: tuple(v_) for k, v_ in (mascot(cv, x, y, s, **pose) or {}).items()}  # noqa
        if mirror:
            cv.restore()
        if tint:
            cv.drawPaint(skia.Paint(Color=C(tint), BlendMode=skia.BlendMode.kModulate))
        if top_light:                                                          # light from above (the beam): white wash top-down
            col, a = top_light
            hy = y + HEAD_DY * s
            g = skia.GradientShader.MakeLinear([(0, hy - 260 * s), (0, hy + 700 * s)], [C(col, a), C(col, 0.0)])
            cv.drawPaint(skia.Paint(Shader=g, BlendMode=skia.BlendMode.kSrcATop))
        cv.restore()
        return r
    w = ink_w if ink_w is not None else max(3, min(12, 3.2 * s))
    pad = w + 6
    return with_ink(cv, w, body, bounds=skia.Rect(x - 780 * s - pad, y - 1330 * s - pad, x + 780 * s + pad, y + 160 * s + pad))


def actor(cv, v, feet3, height_m=1.6, tint=None, top_light=None, mirror=False, ink_w=None, **pose):
    """Puppet with its feet on the projected 3D point. Returns {'hand_r','head','s','x','y'} (output px)."""
    r = v.P(feet3)
    if r is None:
        return None
    x, y, pxm = r
    s = pxm * height_m / 1150
    out = _puppet(cv, x, y, s, tint, top_light, mirror, ink_w, pose) or {}
    out.update(s=s, x=x, y=y)
    return out


def actor_head(cv, v, head3, height_m=1.6, tint=None, top_light=None, mirror=False, ink_w=None, scale_mul=1.0, **pose):
    """Close-ups: scale from the depth of the HEAD (feet may be far off-screen)."""
    r = v.P(head3)
    if r is None:
        return None
    hx, hy, pxm = r
    s = pxm * height_m / 1150 * scale_mul
    x, y = hx, hy - HEAD_DY * s
    out = _puppet(cv, x, y, s, tint, top_light, mirror, ink_w, pose) or {}
    out.update(s=s, x=x, y=y)
    return out


def hand_of(height_s, view='front', **pose):
    """Where the right hand ends up (relative to the feet, s=1) for a pose: for aiming arms."""
    return tuple(mascot(_scratch, 0, 0, height_s, view=view, **pose)['hand_r'])


def talk(t, words, lines, amp=0.7):
    """Mouth-open amount from the word timings of the given line ids (0 when silent)."""
    for w in words:
        if w['line'] in lines and w['start'] - 0.03 <= t <= w['end']:
            ph = (t - w['start']) / max(0.08, w['end'] - w['start'])
            return amp * (0.35 + 0.65 * abs(math.sin(math.pi * ph * max(1, round((w['end'] - w['start']) / 0.16)))))
    return 0.0


def blink(t, period=3.1, offset=0.0):
    u = (t + offset) % period
    return max(0.0, 1 - abs(u - 0.08) / 0.08) if u < 0.17 else 0.0


def occlude(cv, v, quads):
    """Put 3D foreground back OVER the puppets: for each 3D polygon (e.g. a table edge), clip to its projection and redraw the plate."""
    for quad in quads:
        q = [v.P(p) for p in quad]
        if any(a is None for a in q):
            continue
        path = skia.Path()
        path.moveTo(q[0][0], q[0][1])
        for a in q[1:]:
            path.lineTo(a[0], a[1])
        path.close()
        cv.save()
        cv.clipPath(path, skia.ClipOp.kIntersect, True)
        v.draw(cv)
        cv.restore()


def glow(cv, x, y, r, col, a=0.5, blend=skia.BlendMode.kScreen, sy=1.0):
    """Soft light blob WITHOUT a blur filter (radial gradient): cheap at any size."""
    if r <= 1:
        return
    g = skia.GradientShader.MakeRadial((0, 0), r, [C(col, a), C(col, a * 0.35), C(col, 0.0)], [0.0, 0.45, 1.0])
    cv.save(); cv.translate(x, y); cv.scale(1.0, sy)
    cv.drawCircle(0, 0, r, skia.Paint(Shader=g, BlendMode=blend, AntiAlias=True))
    cv.restore()
