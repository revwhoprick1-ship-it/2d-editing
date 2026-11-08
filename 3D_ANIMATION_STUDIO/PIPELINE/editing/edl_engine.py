#!/usr/bin/env python3
"""Shorts editing engine: composites rendered 3D frames into a finished 1080x1920
edit with modern short-form editing grammar, then encodes it with the mix.

An edit is a Python module exposing:
    SEGMENTS : list of dicts (video time ranges -> source + effects)
    OVERLAYS : list of dicts (motion graphics drawn on top)
    CAPTIONS : dict (timing file, offset, style, per-time y overrides)
    AUDIO    : path to the mixed master
    DURATION : seconds

Segment keys
    t0, t1          video time range (s)
    src             render job id (frames in FRAMES_ROOT/<src>/####.png) or None
    map             [(t, src_frame), ...] piecewise-linear time map (speed ramps, holds)
                    (alternative: f0 + rate)
    tiles           [{'src','f0','cy','zoom'}, ...] -> stacked horizontal split screen
    rewind          (t_from, t_to): re-composite earlier video time in reverse (VHS)
    zoom            [(t, scale, cx, cy), ...]  2D punch-in (eased)
    shake           [(t0, t1, amp_px)]
    flash           [(t, dur_s)]  white flash frames
    whip_in/out     (+1|-1, frames)  whip-pan with directional motion blur
    fx              ['cctv', 'vhs', 'freeze_tint', 'desat', ...]
    pixelate        [(t0, t1, block_start, block_end)]
"""
import importlib.util
import json
import math
import os
import subprocess
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
FONT_B = os.path.join(STUDIO, 'ASSETS', 'fonts', 'Montserrat-800.ttf')
FONT_S = os.path.join(STUDIO, 'ASSETS', 'fonts', 'Montserrat-600.ttf')
FONT_E = os.path.join(STUDIO, 'ASSETS', 'fonts', 'NotoEmoji-600.ttf')
FONT_C = os.path.join(STUDIO, 'ASSETS', 'fonts', 'RobotoCondensed-Bold.ttf')       # 2dEDIT captions
FONT_CR = os.path.join(STUDIO, 'ASSETS', 'fonts', 'RobotoCondensed-Regular.ttf')   # 2dEDIT HUD
YELLOW = (255, 210, 61)
RED = (230, 40, 45)


@lru_cache(maxsize=64)
def font(path, size):
    return ImageFont.truetype(path, int(size))


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def interp_keys(keys, t, n=1):
    """keys: [(t, v1, v2...)] eased piecewise interpolation."""
    if not keys:
        return None
    if t <= keys[0][0]:
        return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= t <= b[0]:
            u = ease((t - a[0]) / max(1e-6, b[0] - a[0]))
            return tuple(x + (y - x) * u for x, y in zip(a[1:], b[1:]))
    return keys[-1][1:]


def lin_map(pairs, t):
    if t <= pairs[0][0]:
        return pairs[0][1]
    for a, b in zip(pairs, pairs[1:]):
        if a[0] <= t <= b[0]:
            u = (t - a[0]) / max(1e-6, b[0] - a[0])
            return a[1] + (b[1] - a[1]) * u
    return pairs[-1][1]


# ============================================================================ sources
class Frames:
    def __init__(self, root):
        self.root = root
        self._avail = {}

    def avail(self, job):
        if job not in self._avail:
            d = os.path.join(self.root, job)
            fs = sorted(int(f[:-4]) for f in os.listdir(d) if f.endswith('.png')) if os.path.isdir(d) else []
            self._avail[job] = fs
        return self._avail[job]

    @lru_cache(maxsize=48)
    def load(self, job, f):
        im = Image.open(os.path.join(self.root, job, f'{f:04d}.png')).convert('RGB')
        return np.asarray(im, dtype=np.float32) / 255.0

    def get(self, job, fr):
        """Frame at (possibly fractional / missing) index: blends neighbours rendered on twos."""
        av = self.avail(job)
        if not av:
            return np.zeros((960, 540, 3), np.float32)
        fr = min(max(fr, av[0]), av[-1])
        import bisect
        i = bisect.bisect_left(av, fr)
        if i < len(av) and abs(av[i] - fr) < 1e-6:
            return self.load(job, av[i])
        lo = av[max(0, i - 1)]
        hi = av[min(len(av) - 1, i)]
        if hi == lo:
            return self.load(job, lo)
        u = (fr - lo) / (hi - lo)
        if u < 0.02:
            return self.load(job, lo)
        if u > 0.98:
            return self.load(job, hi)
        return self.load(job, lo) * (1 - u) + self.load(job, hi) * u


def crop_resize(img, out_w, out_h, zoom=1.0, cx=0.5, cy=0.5):
    zoom = max(1.0, zoom)                                # never crop outside the rendered frame
    h, w = img.shape[:2]
    ar = out_w / out_h
    cw = w / zoom
    ch = cw / ar
    if ch > h / zoom:
        ch = h / zoom
        cw = ch * ar
    x0 = min(max(0.0, cx * w - cw / 2), w - cw)
    y0 = min(max(0.0, cy * h - ch / 2), h - ch)
    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    pil = pil.resize((out_w, out_h), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
    return np.asarray(pil, dtype=np.float32) / 255.0


# ============================================================================ effects
def fx_cctv(a, t):
    g = a @ np.array([0.30, 0.59, 0.11], np.float32)
    g = np.clip((g - 0.08) * 1.25, 0, 1)
    out = np.stack([g * 0.86, g * 1.0, g * 0.88], -1)
    rng = np.random.default_rng(int(t * 1000))
    out += rng.normal(0, 0.035, out.shape[:2])[..., None]
    out[::4] *= 0.86
    yy, xx = np.mgrid[0:out.shape[0], 0:out.shape[1]]
    v = 1 - 0.55 * (((xx / out.shape[1] - 0.5) * 1.6) ** 2 + ((yy / out.shape[0] - 0.5) * 1.2) ** 2)
    return np.clip(out * v[..., None], 0, 1)


def fx_vhs(a, t):
    rng = np.random.default_rng(int(t * 997))
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], 9, axis=1)
    out[..., 2] = np.roll(a[..., 2], -9, axis=1)
    for _ in range(6):
        y = rng.integers(0, H - 40)
        hgt = rng.integers(4, 30)
        out[y:y + hgt] = np.roll(out[y:y + hgt], rng.integers(-60, 60), axis=1)
    band = int((t * 900) % H)
    out[band:band + 26] = out[band:band + 26] * 0.5 + 0.45
    out += rng.normal(0, 0.05, out.shape[:2])[..., None]
    out = out * 1.05 + 0.03
    return np.clip(out, 0, 1)


def fx_freeze_tint(a, t):
    g = a @ np.array([0.30, 0.59, 0.11], np.float32)
    out = a * 0.45 + g[..., None] * 0.55
    out = out * np.array([1.12, 0.92, 0.88], np.float32)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    v = 1 - 0.6 * (((xx / a.shape[1] - 0.5) * 1.5) ** 2 + ((yy / a.shape[0] - 0.5) * 1.1) ** 2)
    return np.clip(out * v[..., None], 0, 1)


@lru_cache(maxsize=4)
def _vignette(h, w, k):
    yy, xx = np.mgrid[0:h, 0:w]
    v = 1 - k * (((xx / w - 0.5) * 1.4) ** 2 + ((yy / h - 0.5) * 1.0) ** 2)
    return np.clip(v, 0, 1).astype(np.float32)[..., None]


def fx_vignette(a, t):
    return a * _vignette(a.shape[0], a.shape[1], 0.55)


def fx_pixelate(a, block):
    if block <= 1:
        return a
    h, w = a.shape[:2]
    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    small = pil.resize((max(1, w // block), max(1, h // block)), Image.BILINEAR)
    return np.asarray(small.resize((w, h), Image.NEAREST), dtype=np.float32) / 255.0


def motion_blur_x(a, length):
    n = max(1, min(14, int(abs(length) / 12)))
    if n <= 1:
        return a
    acc = np.zeros_like(a)
    for i in range(n):
        acc += np.roll(a, int(length * (i / (n - 1) - 0.5)), axis=1)
    return acc / n


# ============================================================================ text / graphics
def text_layer(lines, stroke=8, shadow=True, align='center', spacing=10, pad=24):
    """lines: [(text, size, fill, fontpath)] -> RGBA image."""
    ims = []
    for text, size, fill, fp in lines:
        f = font(fp or FONT_B, size)
        bb = f.getbbox(text, stroke_width=stroke)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        im = Image.new('RGBA', (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if shadow:
            d.text((pad - bb[0] + 5, pad - bb[1] + 7), text, font=f, fill=(0, 0, 0, 150), stroke_width=stroke,
                   stroke_fill=(0, 0, 0, 150))
        d.text((pad - bb[0], pad - bb[1]), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=(12, 12, 14))
        ims.append(im)
    wmax = max(i.width for i in ims)
    htot = sum(i.height for i in ims) - spacing * (len(ims) - 1)
    out = Image.new('RGBA', (wmax, max(1, htot)), (0, 0, 0, 0))
    y = 0
    for i in ims:
        x = (wmax - i.width) // 2 if align == 'center' else 0
        out.alpha_composite(i, (x, y))
        y += i.height - spacing
    return out


def paste(canvas, layer, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    lay = layer
    if abs(scale - 1.0) > 1e-3:
        lay = lay.resize((max(1, int(lay.width * scale)), max(1, int(lay.height * scale))), Image.BICUBIC)
    if abs(rot) > 1e-3:
        lay = lay.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = lay.split()[3].point(lambda v: int(v * alpha))
        lay = lay.copy()
        lay.putalpha(a)
    # SAFE AREA (always on): nothing may leave the frame. Too big -> shrink to fit; off-edge -> push inside.
    m = SAFE_MARGIN
    fit = min(1.0, (canvas.width - 2 * m) / lay.width, (canvas.height - 2 * m) / lay.height)
    if fit < 0.999:
        lay = lay.resize((max(1, int(lay.width * fit)), max(1, int(lay.height * fit))), Image.BICUBIC)
    x = min(max(cx - lay.width / 2, m), canvas.width - m - lay.width)
    y = min(max(cy - lay.height / 2, m), canvas.height - m - lay.height)
    canvas.alpha_composite(lay, (int(x), int(y)))


SAFE_MARGIN = 36


def pop_scale(t, t0, dur=0.18, over=1.12):
    u = (t - t0) / dur
    if u <= 0:
        return 0.0
    if u >= 1:
        return 1.0
    if u < 0.6:
        return 0.55 + (over - 0.55) * ease(u / 0.6)
    return over + (1.0 - over) * ease((u - 0.6) / 0.4)


def rounded_box(w, h, fill, r=26, outline=None, width=0):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill, outline=outline, width=width)
    return im


def pill(text, emoji=None, size=46, fill=(255, 255, 255, 235), fg=(20, 20, 24), pad=(30, 18), efill=None):
    f = font(FONT_B, size)
    fe = font(FONT_E, int(size * 1.05))
    tb = f.getbbox(text)
    ew = (fe.getbbox(emoji)[2] + 16) if emoji else 0
    w = tb[2] - tb[0] + ew + pad[0] * 2
    h = max(tb[3] - tb[1], size) + pad[1] * 2
    im = rounded_box(w, h, fill, r=h // 2)
    d = ImageDraw.Draw(im)
    x = pad[0]
    if emoji:
        d.text((x, pad[1] - 4), emoji, font=fe, fill=efill or fg)
        x += ew
    d.text((x - tb[0], (h - (tb[3] - tb[1])) / 2 - tb[1]), text, font=f, fill=fg)
    return im


# ============================================================================ overlay renderers
def ov_title(cv, o, t):
    s = pop_scale(t, o['t0'], 0.16, 1.15)
    if o.get('shake'):
        jitter = math.sin(t * 90) * 6 * max(0, 1 - (t - o['t0']) / 0.4)
    else:
        jitter = 0
    alpha = 1.0 if t < o['t1'] - 0.12 else max(0, (o['t1'] - t) / 0.12)
    paste(cv, o['_layer'], W / 2 + jitter, o['y'], s, o.get('rot', 0), alpha)


def ov_clock(cv, o, t):
    lay = o.get('_layer')
    if lay is None:
        lay = o['_layer'] = pill(o['text'], '⏰', 40, fill=(0, 0, 0, 170), fg=(255, 255, 255))
    paste(cv, lay, 40 + lay.width / 2, 150, pop_scale(t, o['t0'], 0.12, 1.08))


def ov_counter(cv, o, t):
    u = ease((t - o['t0']) / o.get('dur', 0.6))
    val = int(o['a'] + (o['b'] - o['a']) * u)
    lay = text_layer([(f'{val:,}', o.get('size', 120), YELLOW, FONT_B), (o.get('label', ''), 54, (255, 255, 255), FONT_B)],
                     stroke=9)
    paste(cv, lay, W / 2, o.get('y', 420), pop_scale(t, o['t0'], 0.15, 1.1))


def ov_chip(cv, o, t):
    lay = o.get('_layer')
    if lay is None:
        lay = o['_layer'] = pill(o['text'], o.get('emoji'), o.get('size', 50), fill=o.get('fill', (255, 255, 255, 240)),
                                 fg=o.get('fg', (20, 20, 24)), efill=o.get('efill'))
    paste(cv, lay, o['x'] * W, o['y'] * H, pop_scale(t, o['t0'], 0.18, 1.15), o.get('rot', 0))


def ov_banner(cv, o, t):
    lay = o.get('_layer')
    if lay is None:
        lay = o['_layer'] = pill(o['text'], o.get('emoji'), o.get('size', 44), fill=o.get('fill', (255, 255, 255, 235)),
                                 fg=o.get('fg', (20, 20, 24)), efill=o.get('efill'))
    slide = 1 - ease((t - o['t0']) / 0.2)
    out = ease((t - (o['t1'] - 0.2)) / 0.2)
    paste(cv, lay, W / 2, o.get('y', 250) - 160 * slide - 160 * out)


def ov_stamp(cv, o, t):
    lay = o.get('_layer')
    if lay is None:
        f = font(FONT_B, o.get('size', 104))
        tb = f.getbbox(o['text'])
        w, h = tb[2] - tb[0] + 70, tb[3] - tb[1] + 60
        lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        col = o.get('color', RED)
        d.rounded_rectangle((4, 4, w - 5, h - 5), 14, outline=col + (255,), width=10, fill=tuple(o.get('fill', (255, 255, 255, 40))))
        d.text((35 - tb[0], 30 - tb[1]), o['text'], font=f, fill=col + (255,))
        o['_layer'] = lay
    u = (t - o['t0']) / 0.12
    s = 2.4 - 1.4 * ease(u) if u < 1 else 1.0
    paste(cv, lay, o['x'] * W, o['y'] * H, s, o.get('rot', -8), min(1.0, max(0.0, u * 2)))


def ov_lower_third(cv, o, t):
    u = ease((t - o['t0']) / 0.25)
    y = o.get('y', 1330)
    red = rounded_box(360, 76, (215, 30, 40, 255), r=8)
    ImageDraw.Draw(red).text((22, 14), 'BREAKING', font=font(FONT_B, 44), fill=(255, 255, 255))
    head = o.get('_head')
    if head is None:
        f = font(FONT_B, 60)
        tb = f.getbbox(o['text'])
        head = rounded_box(tb[2] - tb[0] + 60, 96, (255, 255, 255, 250), r=8)
        ImageDraw.Draw(head).text((30 - tb[0], 18 - tb[1]), o['text'], font=f, fill=(15, 18, 35))
        maxw = W - 40 - SAFE_MARGIN                     # safe area: the resting position must fit on screen
        if head.width > maxw:
            head = head.resize((maxw, int(head.height * maxw / head.width)), Image.BICUBIC)
        o['_head'] = head
    x0 = -800 + 830 * u
    cv.alpha_composite(red, (int(x0 + 10), int(y - 80)))
    if t > o.get('t_head', o['t0']):
        uh = ease((t - o.get('t_head', o['t0'])) / 0.18)
        cv.alpha_composite(head, (int(40 - (1 - uh) * 1100), int(y)))


def ov_ticker(cv, o, t):
    y = o.get('y', 1460)
    band = Image.new('RGBA', (W, 70), (12, 16, 40, 235))
    d = ImageDraw.Draw(band)
    f = font(FONT_B, 40)
    txt = o['text']
    tw = f.getbbox(txt)[2]
    x = W - (t - o['t0']) * o.get('speed', 300)
    for k in range(3):
        d.text((x + k * (tw + 60), 12), txt, font=f, fill=(255, 220, 90))
    ImageDraw.Draw(band).rectangle((0, 0, 140, 70), fill=(215, 30, 40, 255))
    ImageDraw.Draw(band).text((18, 12), 'LIVE', font=f, fill=(255, 255, 255))
    cv.alpha_composite(band, (0, int(y)))


def ov_live_bug(cv, o, t):
    lay = o.get('_layer')
    if lay is None:
        lay = Image.new('RGBA', (430, 78), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle((0, 0, 120, 77), 10, fill=(215, 30, 40, 255))
        d.text((16, 14), 'LIVE', font=font(FONT_B, 42), fill=(255, 255, 255))
        d.rounded_rectangle((126, 0, 429, 77), 10, fill=(10, 20, 50, 220))
        d.text((142, 16), o.get('text', 'WORLD NEWS 24'), font=font(FONT_B, 34), fill=(255, 255, 255))
        o['_layer'] = lay
    cv.alpha_composite(lay, (40, 120))


def ov_tag(cv, o, t):
    lay = o.get('_layer')
    if lay is None:
        f = font(FONT_B, 62)
        lab = font(FONT_B, 34)
        lb = lab.getbbox(o.get('label', ''))
        w = max(116, lb[2] + 30)
        lay = Image.new('RGBA', (w, 170), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        cx = w // 2
        d.ellipse((cx - 52, 0, cx + 52, 104), fill=YELLOW + (255,), outline=(20, 20, 20, 255), width=6)
        nb = f.getbbox(o['n'])
        d.text((cx - (nb[2] - nb[0]) / 2 - nb[0], 52 - (nb[3] - nb[1]) / 2 - nb[1]), o['n'], font=f, fill=(20, 20, 20))
        if o.get('label'):
            d.rounded_rectangle((0, 116, w - 1, 168), 12, fill=(0, 0, 0, 190))
            d.text(((w - lb[2]) / 2, 122), o['label'], font=lab, fill=(255, 255, 255))
        o['_layer'] = lay
    bob = math.sin((t - o['t0']) * 7) * 6
    x = min(max(o['x'], 0.12), 0.88)                 # keep the tag on screen
    paste(cv, lay, x * W, o['y'] * H + bob, pop_scale(t, o['t0'], 0.18, 1.2))


def ov_speck(cv, o, t):
    u = ease((t - o['t0']) / (o['t1'] - o['t0']))
    x = (o['x0'] + (o['x1'] - o['x0']) * u) * W + math.sin(t * 9) * 10
    y = (o['y0'] + (o['y1'] - o['y0']) * u) * H + math.cos(t * 7) * 8
    glow = Image.new('RGBA', (90, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.ellipse((20, 20, 70, 70), fill=(255, 230, 60, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(9))
    d = ImageDraw.Draw(glow)
    d.ellipse((38, 38, 52, 52), fill=(255, 245, 120, 255))
    cv.alpha_composite(glow, (int(x - 45), int(y - 45)))
    if o.get('label') and t > o.get('t_label', o['t0']):
        lay = o.get('_lab')
        if lay is None:
            lay = o['_lab'] = pill(o['label'], '👇', 42, fill=(255, 230, 60, 245), fg=(30, 25, 10))
        paste(cv, lay, x, y - 110, pop_scale(t, o['t_label'], 0.18, 1.15))


def ov_sweat(cv, o, t):
    for i, (px, py, ph) in enumerate(o['drops']):
        k = ((t - o['t0']) * 0.9 + ph) % 1.0
        x, y = px * W, py * H + k * 140
        a = 1 - k
        dr = Image.new('RGBA', (60, 90), (0, 0, 0, 0))
        d = ImageDraw.Draw(dr)
        d.polygon([(30, 0), (52, 55), (8, 55)], fill=(170, 220, 255, int(220 * a)))
        d.ellipse((8, 34, 52, 84), fill=(170, 220, 255, int(220 * a)))
        d.ellipse((18, 46, 28, 60), fill=(255, 255, 255, int(230 * a)))
        cv.alpha_composite(dr, (int(x - 30), int(y - 45)))


def ov_enhance(cv, o, t):
    x, y, s = o['x'] * W, o['y'] * H, o.get('box', 300)
    d = ImageDraw.Draw(cv)
    blink = int(t * 8) % 2 == 0
    c = (60, 255, 120, 255)
    L = s / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            d.line([(x + sx * L, y + sy * L), (x + sx * L - sx * 50, y + sy * L)], fill=c, width=8)
            d.line([(x + sx * L, y + sy * L), (x + sx * L, y + sy * L - sy * 50)], fill=c, width=8)
    if blink:
        lay = text_layer([(o.get('text', 'ENHANCE'), 64, (60, 255, 120), FONT_B)], stroke=6)
        paste(cv, lay, x, y + L + 60)


def ov_cctv_hud(cv, o, t):
    d = ImageDraw.Draw(cv)
    f = font(FONT_B, 40)
    if int(t * 2) % 2 == 0:
        d.ellipse((60, 140, 100, 180), fill=(255, 40, 40, 255))
    d.text((115, 136), 'REC', font=f, fill=(255, 255, 255))
    d.text((60, 196), o.get('cam', 'CAM 02 · ELEVATOR B'), font=font(FONT_S, 34), fill=(220, 255, 220))
    d.text((60, 1600), o.get('stamp', '2026-11-07  15:14:00'), font=font(FONT_B, 44), fill=(220, 255, 220))


def ov_rewind_hud(cv, o, t):
    d = ImageDraw.Draw(cv)
    if int(t * 6) % 2 == 0:
        lay = text_layer([('◀◀  REWIND', 92, (255, 255, 255), FONT_B)], stroke=7)
        paste(cv, lay, W / 2, 420)
    u = ease((t - o['t0']) / (o['t1'] - o['t0']))
    sec = int(round(60 - u * 1)) % 60
    stamp = '3:14:00 PM' if u < 0.5 else '3:13:59 PM'
    lay = text_layer([(stamp, 70, YELLOW, FONT_B)], stroke=7)
    paste(cv, lay, W / 2, 560)



def ov_timer(cv, o, t):
    """Story clock: counts o['a'] -> 0 over [t0, t_zero]; afterwards shows o['done'] (red)."""
    if t < o['t_zero']:
        v = o['a'] * (1 - (t - o['t0']) / (o['t_zero'] - o['t0']))
        lay = pill(f"{o.get('label', 'ZERO-G')}  {max(0.0, v):4.1f}s", None, o.get('size', 54), fill=(0, 0, 0, 200), fg=(255, 255, 255))
        warn = v < 3.0 and int(t * 6) % 2 == 0
        if warn:
            lay = pill(f"{o.get('label', 'ZERO-G')}  {max(0.0, v):4.1f}s", None, o.get('size', 54), fill=(230, 40, 45, 235), fg=(255, 255, 255))
    else:
        lay = pill(o.get('done', 'GRAVITY: ON'), None, o.get('size', 54), fill=(230, 40, 45, 240), fg=(255, 255, 255))
    paste(cv, lay, W / 2, o.get('y', 150), pop_scale(t, o['t0'], 0.15, 1.1))


def ov_physics(cv, o, t):
    """Animated explainer: you keep going straight, Earth's surface curves away beneath you."""
    u = ease(min(1.0, max(0.0, (t - o['t0']) / max(0.1, o.get('anim', 2.5)))))
    pw, ph = 900, 620
    lay = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), 36, fill=(12, 20, 40, 225))
    R = 1500                                       # exaggerated Earth curve
    cx, cy = pw / 2, 300 + R
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(40, 120, 80, 255), outline=(120, 220, 140, 255), width=6)
    d.rounded_rectangle((0, 0, pw - 1, ph - 1), 36, outline=(255, 255, 255, 80), width=3)
    x0 = 170
    import math as _m
    y0 = cy - _m.sqrt(R * R - (x0 - cx) ** 2) - 18
    x1 = x0 + 560 * u
    d.line((x0, y0, x0 + 600, y0), fill=(255, 255, 255, 120), width=4)          # straight path (dashed look)
    for k in range(0, 600, 40):
        d.line((x0 + k + 20, y0, x0 + k + 40, y0), fill=(12, 20, 40, 255), width=6)
    gy = cy - _m.sqrt(max(0, R * R - (x1 - cx) ** 2))
    d.ellipse((x1 - 22, y0 - 44, x1 + 22, y0), fill=(255, 140, 40, 255), outline=(255, 255, 255, 255), width=4)   # you
    if u > 0.15:
        d.line((x1, y0, x1, gy), fill=YELLOW + (255,), width=6)
        f = font(FONT_B, 40)
        d.text((x1 - 250, (y0 + gy) / 2 - 10), o.get('gap', '≈ 2 m'), font=f, fill=YELLOW + (255,))
    f = font(FONT_B, 44)
    d.text((40, 30), o.get('title', 'YOU KEEP GOING STRAIGHT'), font=f, fill=(255, 255, 255, 255))
    d.text((40, 84), o.get('sub', 'EARTH CURVES AWAY UNDER YOU'), font=font(FONT_B, 36), fill=(160, 210, 255, 255))
    a = min(1.0, (t - o['t0']) / 0.2, (o['t1'] - t) / 0.2)
    paste(cv, lay, W / 2, o.get('y', 560), 0.85 + 0.15 * min(1.0, (t - o['t0']) / 0.2), 0, max(0.0, a))


def _at(keys, t):
    """[(t, value), ...] -> (value, time it became active)."""
    v, since = keys[0][1], keys[0][0]
    for k, val in keys:
        if t >= k:
            v, since = val, k
    return v, since


def ov_hud(cv, o, t):
    """2dEDIT top HUD row: small condensed items separated by dots. A value that just changed flashes red.
    o['items'] = [[(t, 'TEXT'), ...], ...]; o['red'] = [(t0, t1, item_index)] keeps an item red."""
    if any(a <= t < b for a, b in o.get('hide', [])):
        return
    size = o.get('size', 34)
    f = font(FONT_CR, size)
    fb = font(FONT_C, size)
    parts = []
    for i, keys in enumerate(o['items']):
        v, since = _at(keys, t)
        hot = (t - since < o.get('flash', 1.2) and since > o['t0'] + 0.01) or any(a <= t < b and j == i for a, b, j in o.get('red', []))
        parts.append((v, RED if hot else (236, 236, 236), fb if hot else f))
    sep = '   ·   '
    widths = [p[2].getbbox(p[0])[2] for p in parts]
    sw = f.getbbox(sep)[2]
    lw = sum(widths) + sw * (len(parts) - 1) + 40
    lay = Image.new('RGBA', (int(lw), int(size * 1.6) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x = 20
    for k, (txt, col, ff) in enumerate(parts):
        d.text((x + 2, 12), txt, font=ff, fill=(0, 0, 0, 170))
        d.text((x, 10), txt, font=ff, fill=col + (235,))
        x += widths[k]
        if k < len(parts) - 1:
            d.text((x, 10), sep, font=f, fill=(200, 200, 200, 150))
            x += sw
    if o.get('rec', True):                                # small red REC-style dot = "this is being watched"
        if int(t * 1.6) % 2 == 0:
            d.ellipse((2, 10 + size * 0.42, 14, 22 + size * 0.42), fill=RED + (230,))
    paste(cv, lay, W / 2, o.get('y', 170), 1.0, 0, o.get('alpha', 1.0))


def caption_2d_layer(words, size=80, quote=False, label=None, emph=()):
    """2dEDIT caption: condensed bold white, thin dark outline + soft shadow, one red keyword,
    dialogue in quotes with a small red speaker label above."""
    f = font(FONT_C, size)
    toks = [w.upper() for w in words]
    if quote:
        toks[0] = '\u201C' + toks[0]
        toks[-1] = toks[-1] + '\u201D'
    cols = []
    for w in words:
        key = ''.join(c for c in w.lower() if c.isalnum() or c == "'")
        cols.append(RED if key in emph else (255, 255, 255))
    stroke = 4
    widths = [f.getbbox(x, stroke_width=stroke)[2] for x in toks]
    space = int(size * 0.24)
    total = sum(widths) + space * (len(toks) - 1)
    lines = [[0, len(toks)]]
    if total > W - 160 and len(toks) > 1:
        h = (len(toks) + 1) // 2
        lines = [[0, h], [h, len(toks)]]
    lw = max(sum(widths[a:b]) + space * (b - a - 1) for a, b in lines) + 40
    lab_h = int(size * 0.62) if label else 0
    lay = Image.new('RGBA', (int(lw), int(size * 1.22 * len(lines)) + 40 + lab_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if label:
        fl = font(FONT_C, int(size * 0.42))
        lwid = fl.getbbox(label)[2]
        d.text(((lw - lwid) / 2 + 2, 14), label, font=fl, fill=(0, 0, 0, 160))
        d.text(((lw - lwid) / 2, 12), label, font=fl, fill=RED)
    shadow = Image.new('RGBA', lay.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    for li, (a, b) in enumerate(lines):
        tw = sum(widths[a:b]) + space * (b - a - 1)
        x = (lw - tw) / 2
        yy = 20 + lab_h + li * size * 1.18
        for k in range(a, b):
            ds.text((x + 3, yy + 5), toks[k], font=f, fill=(0, 0, 0, 200), stroke_width=stroke + 2, stroke_fill=(0, 0, 0, 200))
            d.text((x, yy), toks[k], font=f, fill=cols[k], stroke_width=stroke, stroke_fill=(14, 14, 16))
            x += widths[k] + space
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    shadow.alpha_composite(lay)
    return shadow


def ov_text2d(cv, o, t):
    """On-screen (unspoken) text in the 2dEDIT caption style."""
    if '_lay' not in o:
        o['_lay'] = caption_2d_layer(o['text'].split(), o.get('size', 80), o.get('quote', False), o.get('label'),
                                     set(o.get('emph', ())))
    a = min(1.0, (t - o['t0']) / 0.12, (o['t1'] - t) / 0.12)
    paste(cv, o['_lay'], W / 2, o.get('y', 1380), 1.0, 0, max(0.0, a))


OVERLAYS_FN = {'title': ov_title, 'clock': ov_clock, 'counter': ov_counter, 'chip': ov_chip, 'banner': ov_banner,
               'stamp': ov_stamp, 'lower_third': ov_lower_third, 'ticker': ov_ticker, 'live_bug': ov_live_bug,
               'tag': ov_tag, 'speck': ov_speck, 'sweat': ov_sweat, 'enhance': ov_enhance, 'cctv_hud': ov_cctv_hud,
               'rewind_hud': ov_rewind_hud, 'timer': ov_timer, 'physics': ov_physics, 'hud': ov_hud, 'text2d': ov_text2d}


# ============================================================================ captions
def build_chunks(timing, offset, max_words=3, split_punct=False):
    import re
    words = [w for w in timing['words'] if w['text'].strip()]
    chunks, cur = [], []
    for w in words:
        is_p = not re.search(r'[A-Za-z0-9]', w['text'])
        if is_p:
            if cur:
                cur[-1]['text'] += w['text'] if w['text'] in '!?' else ''
                if w['text'] in '.?!,':
                    chunks.append(cur)
                    cur = []
            continue
        if cur and (len(cur) >= max_words or w['start'] - cur[-1]['end'] > 0.3 or w['line'] != cur[-1]['line']
                    or (split_punct and cur[-1]['text'][-1:] in '.!?')):
            chunks.append(cur)
            cur = []
        cur.append({'text': w['text'], 'start': w['start'] + offset, 'end': w['end'] + offset, 'line': w['line']})
    if cur:
        chunks.append(cur)
    for i, ch in enumerate(chunks):
        nxt = chunks[i + 1][0]['start'] if i + 1 < len(chunks) else ch[-1]['end'] + 0.6
        ch_end = min(nxt, ch[-1]['end'] + 0.5)
        for w in ch:
            w['chunk_end'] = ch_end
    return chunks


def draw_caption(cv, chunks, t, cfg):
    for ch in chunks:
        if ch[0]['start'] <= t < ch[-1]['chunk_end']:
            break
    else:
        return
    if any(a <= t < b for a, b in cfg.get('hide', [])):
        return
    y = cfg.get('y', 1220)
    for a, b, yy in cfg.get('y_over', []):
        if a <= t < b:
            y = yy
    if cfg.get('style') == '2dedit':                    # whole phrase at once, no karaoke colouring
        spk = cfg.get('speakers', {}).get(ch[0]['line'])
        key = tuple(w['text'] for w in ch)
        cache = cfg.setdefault('_cache', {})
        if key not in cache:
            cache[key] = caption_2d_layer(list(key), cfg.get('size', 80), quote=spk is not None, label=spk,
                                          emph=set(cfg.get('emphasis', ())))
        a = min(1.0, (t - ch[0]['start']) / 0.08)
        paste(cv, cache[key], W / 2, y, 1.0, 0, a)
        return
    size = cfg.get('size', 92)
    emph = cfg.get('emphasis', set())
    f = font(FONT_B, size)
    parts = []
    for w in ch:
        word = w['text'].upper()
        active = w['start'] <= t < max(w['end'], w['start'] + 0.12)
        key = ''.join(c for c in w['text'].lower() if c.isalpha() or c == '-')
        col = YELLOW if (active or key in emph) else (255, 255, 255)
        if key in emph and not active:
            col = (255, 160, 60)
        parts.append((word, col, active))
    stroke = 10
    widths = [f.getbbox(p[0], stroke_width=stroke)[2] for p in parts]
    space = int(size * 0.28)
    total = sum(widths) + space * (len(parts) - 1)
    lines = [[0, len(parts)]]
    if total > W - 120 and len(parts) > 1:
        lines = [[0, 1], [1, len(parts)]] if len(parts) == 2 else [[0, 2], [2, len(parts)]]
    lw = max(sum(widths[a:b]) + space * (b - a - 1) for a, b in lines) + 40   # sized to the text, so paste() can shrink it to fit
    layer = Image.new('RGBA', (int(lw), int(size * 1.4 * len(lines)) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for li, (a, b) in enumerate(lines):
        tw = sum(widths[a:b]) + space * (b - a - 1)
        x = (lw - tw) / 2
        yy = 20 + li * size * 1.25
        for k in range(a, b):
            word, col, active = parts[k]
            d.text((x + 6, yy + 8), word, font=f, fill=(0, 0, 0, 140), stroke_width=stroke, stroke_fill=(0, 0, 0, 140))
            d.text((x, yy), word, font=f, fill=col, stroke_width=stroke, stroke_fill=(10, 10, 12))
            x += widths[k] + space
    s = pop_scale(t, ch[0]['start'], 0.14, 1.08)
    paste(cv, layer, W / 2, y, s)


# ============================================================================ compositor
class Editor:
    def __init__(self, edl, frames_root):
        self.E = edl
        self.F = Frames(frames_root)
        self.timing = json.load(open(edl.CAPTIONS['timing']))
        self.chunks = build_chunks(self.timing, edl.CAPTIONS.get('offset', 0.0), edl.CAPTIONS.get('max_words', 3),
                                   edl.CAPTIONS.get('style') == '2dedit')
        for o in edl.OVERLAYS:
            if o['type'] == 'title':
                o['_layer'] = text_layer([(tx, sz, col, FONT_B) for tx, sz, col in o['lines']], stroke=11)

    def seg_at(self, t):
        for s in self.E.SEGMENTS:
            if s['t0'] <= t < s['t1']:
                return s
        return self.E.SEGMENTS[-1]

    def src_frame(self, s, t):
        if 'map' in s:
            return lin_map(s['map'], t)
        return s.get('f0', 0) + (t - s['t0']) * FPS * s.get('rate', 1.0)

    def base(self, t, depth=0):
        s = self.seg_at(t)
        if 'rewind' in s:
            ta, tb = s['rewind']
            u = (t - s['t0']) / (s['t1'] - s['t0'])
            u = u ** 1.6
            img = self.base(ta + (tb - ta) * u, depth + 1)
            return fx_vhs(img, t)
        if 'tiles' in s:
            n = len(s['tiles'])
            th = H // n
            out = np.zeros((H, W, 3), np.float32)
            for i, tl in enumerate(s['tiles']):
                fr = tl.get('f0', 0) + (t - s['t0']) * FPS * tl.get('rate', 1.0)
                img = self.F.get(tl['src'], fr)
                z = tl.get('zoom', 1.0) * (1 + 0.04 * (t - s['t0']))
                out[i * th:(i + 1) * th] = crop_resize(img, W, th, z, tl.get('cx', 0.5), tl.get('cy', 0.4))
                out[(i + 1) * th - 6:(i + 1) * th + 6] = 0.02
            return out
        if s['src'] is None:                            # hard cut to black (or a solid colour)
            return np.zeros((H, W, 3), np.float32) + np.array(s.get('fill', (0, 0, 0)), np.float32)
        img = self.F.get(s['src'], self.src_frame(s, t))
        z, cx, cy = 1.0, 0.5, 0.5
        zk = interp_keys(s.get('zoom'), t)
        if zk:
            z, cx, cy = zk
        a = crop_resize(img, W, H, z, cx, cy)
        for ta, tb, b0, b1 in s.get('pixelate', []):
            if ta <= t < tb:
                a = fx_pixelate(a, int(b0 + (b1 - b0) * ease((t - ta) / (tb - ta))))
        for name in s.get('fx', []):
            a = {'cctv': fx_cctv, 'vhs': fx_vhs, 'freeze_tint': fx_freeze_tint, 'vignette': fx_vignette}[name](a, t)
        return a

    def frame(self, i):
        t = i / FPS
        s = self.seg_at(t)
        a = self.base(t)
        # camera shake (2D)
        for ta, tb, amp in s.get('shake', []):
            if ta <= t < tb:
                k = 1 - (t - ta) / (tb - ta)
                rng = np.random.default_rng(i)
                dx, dy = (rng.uniform(-1, 1, 2) * amp * k).astype(int)
                a = np.roll(np.roll(a, dx, axis=1), dy, axis=0)
        # whip pans
        for key, sign in (('whip_in', 1), ('whip_out', -1)):
            if key in s:
                d, n = s[key]
                k = (t - s['t0']) * FPS if key == 'whip_in' else (s['t1'] - t) * FPS
                if k < n:
                    u = 1 - k / n
                    off = int(d * u * u * W * 0.55) * (1 if key == 'whip_in' else -1)
                    a = motion_blur_x(np.roll(a, off, axis=1), d * u * 420)
        for tf, dur in s.get('flash', []):
            if tf <= t < tf + dur:
                a = a + (1 - (t - tf) / dur) * 0.9 * (1 - a)
        g = getattr(self.E, 'GRADE', None)
        if g:                                           # global colour grade: saturation + contrast around mid-grey
            lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
            a = lum[..., None] + (a - lum[..., None]) * g.get('sat', 1.0)
            a = 0.5 + (a - 0.5) * g.get('contrast', 1.0)
        cv = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
        for o in self.E.OVERLAYS:
            if o['t0'] <= t < o['t1']:
                OVERLAYS_FN[o['type']](cv, o, t)
        draw_caption(cv, self.chunks, t, self.E.CAPTIONS)
        return cv.convert('RGB')


def render(edl_path, frames_root, out_mp4, audio=None, crf=20, preset='slow', start=0, end=None, still_dir=None,
           stills=None):
    spec = importlib.util.spec_from_file_location('edl', edl_path)
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    ed = Editor(E, frames_root)
    n = int(round(E.DURATION * FPS))
    if stills:
        os.makedirs(still_dir, exist_ok=True)
        for t in stills:
            ed.frame(int(round(t * FPS))).save(os.path.join(still_dir, f'edit_{t:06.2f}.jpg'), quality=88)
        return
    end = n if end is None else end
    audio = audio or E.AUDIO
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-']
    if audio and os.path.exists(audio):
        cmd += ['-ss', f'{start / FPS:.4f}', '-i', audio, '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest']
    cmd += ['-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-profile:v', 'high', '-level', '4.2',
            '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
            '-movflags', '+faststart', out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(start, end):
        p.stdin.write(ed.frame(i).tobytes())
        if i % 60 == 0:
            print(f'EDIT frame {i}/{end}', flush=True)
    p.stdin.close()
    p.wait()
    print('EDIT_OK', out_mp4)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('edl')
    ap.add_argument('--frames', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--audio', default=None)
    ap.add_argument('--crf', type=int, default=20)
    ap.add_argument('--preset', default='slow')
    ap.add_argument('--stills', default=None, help='comma list of times -> jpg stills in --out dir')
    a = ap.parse_args()
    if a.stills:
        render(a.edl, a.frames, None, still_dir=a.out, stills=[float(x) for x in a.stills.split(',')])
    else:
        render(a.edl, a.frames, a.out, a.audio, a.crf, a.preset)
