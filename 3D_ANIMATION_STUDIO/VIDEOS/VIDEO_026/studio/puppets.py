"""VIDEO_026 puppets (2dEDIT: flat vector, Skia). The star is `draw_bob_mimic_puppet` = "The Unzipped Bob Mimic"
(reference image: a man on a couch whose face is unzipped down the middle — two halves with cracked round glasses, a black
void between them lined with needle teeth, four red pinprick eyes inside, a round fanged maw below, black ink tendrils,
teal collared shirt, cold cyan phone light from below, crimson rim light).

Also here: seated bodies, the real Bob behind frosted glass, the long double-jointed hand, phone-in-hand.
"""
import math
import os
import sys

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
for _p in (os.path.join(STUDIO, 'PIPELINE', 'twod'), os.path.join(STUDIO, 'PIPELINE', 'hybrid')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from flat import C, H, W, blob, lin, mascot, paint, poly  # noqa: E402
from comp import with_ink  # noqa: E402

INKC = '#0E0C1A'
SKIN_M, SKIN_M_SH, SKIN_M_HI = '#9E98B5', '#716B94', '#C6C1DB'          # the copy: desaturated lavender-grey skin
TEAL, TEAL_SH, TEAL_HI = '#2F8A86', '#1E5C5C', '#58B5AC'
HAIR_B, HAIR_B_SH = '#2A1E16', '#170F0A'
VOID, GUM, TOOTH, EYE_RED = '#030206', '#42060E', '#F4F1E8', '#FF1A1A'
CYAN_UNDER = skia.Color(55, 190, 255, 135)                               # smartphone under-light
CRIMSON_RIM = skia.Color(255, 25, 40, 120)                               # TV alert rim light
BOB = dict(hair=HAIR_B, hair_sh=HAIR_B_SH, shirt=TEAL, shirt_sh=TEAL_SH, pants='#2B2F4A', pants_sh='#1E2136', shoe='#D8D8E0', shoe_sh='#A9AAB8')
FAKE = dict(BOB, skin=SKIN_M, skin_sh=SKIN_M_SH)
YOU = dict()                                                             # the mascot = flat.py defaults (brown hair, orange shirt, jeans)
PIVX, PIVY = 89.0, -10.0                                                 # each torn half turns about its own middle
HEAD_PTS = [(-178, -40), (-150, -170), (0, -222), (150, -170), (178, -40), (160, 90), (90, 175), (0, 195), (-90, 175), (-160, 90)]
K = skia.ClipOp.kIntersect


def stroke(col, w, a=1.0):
    return paint(C(col, a) if isinstance(col, str) else col, style='stroke', width=w)


def _xf(side, g, x, y):
    """Half-face transform: translate side*g*55 px, rotate side*g*16 deg about the chin pivot."""
    a = math.radians(side * g * 16.0)
    c, s_ = math.cos(a), math.sin(a)
    dx, dy = x - side * PIVX, y - PIVY
    return side * PIVX + dx * c - dy * s_ + side * g * 55.0, PIVY + dx * s_ + dy * c


def _notch(y, g, jd):
    """How far the torn inner edge of a half sits from the centre line (head units)."""
    e = 1.5 * g
    if y < -50:
        e += (-50 - y) / 175.0 * 12.0 * g
    if y > 55:
        u = min(1.0, (y - 55) / 150.0)
        e += math.sin(math.pi * u) * (10 * g + 34 * g * jd)
    e += (2.5 * math.sin(y * 0.33) + 1.5 * math.sin(y * 0.71 + 1)) * min(1.0, g * 3)
    return max(0.0, e)


def _lens(cv, sd, P):
    g, crack = P['g'], P['crack']
    cv.save()
    cv.translate(sd * 78, -6 + 12 * g * (1 + 0.6 * crack))
    cv.rotate(sd * 13 * g * (0.4 + 0.6 * crack))
    lens = skia.Path.Circle(0, 0, 62)
    cv.drawPath(lens, paint(C('#D6F1FF', min(0.94, P['lens_a'] + 0.74 * crack))))
    cv.save(); cv.clipPath(lens, K, True)
    cv.drawPath(poly([(-70, 20), (-20, -70), (8, -70), (-70, 62)]), paint(C('#FFFFFF', 0.24 * (1 - 0.5 * crack))))      # glare band
    if crack > 0.02:                                                     # jagged white fractures from one impact point
        ix, iy = sd * 14, -18
        rng = np.random.default_rng(7 if sd < 0 else 11)
        for k in range(7):
            a = k / 7 * 2 * math.pi + rng.uniform(-0.3, 0.3)
            pts = [(ix, iy)]
            for q in range(1, 5):
                r = q * 22 * crack + rng.uniform(-4, 4)
                pts.append((ix + math.cos(a + rng.uniform(-0.22, 0.22)) * r, iy + math.sin(a + rng.uniform(-0.22, 0.22)) * r))
            cv.drawPath(poly(pts, closed=False), stroke('#FFFFFF', 3.2, 0.95))
            cv.drawPath(poly(pts, closed=False), stroke('#5C6A86', 1.2, 0.8))
        for r in (24, 44):
            cv.drawArc(skia.Rect(ix - r, iy - r, ix + r, iy + r), 20 + sd * 40, 110, False, stroke('#FFFFFF', 2.4, 0.8 * crack))
    cv.restore()
    cv.drawPath(lens, stroke('#17151F', 9))
    cv.restore()


def _face(cv, P):
    """The whole Bob head in head units (centre 0,0). Drawn once (sealed) or twice (clipped to each torn half)."""
    g, crack, roll, age = P['g'], P['crack'], P['roll'], P['age']
    SK, SKS, HR = P['skin'], P['skin_sh'], P['hair']
    ms = P['mess']
    for sd in (-1, 1):                                                    # messy tufts behind the skull (bigger when it stops pretending)
        cv.drawPath(poly([(sd * 150, -150), (sd * (170 + 82 * ms), -160 - 45 * ms), (sd * (176 + 40 * ms), -128), (sd * (180 + 102 * ms), -84),
                          (sd * (176 + 32 * ms), -52), (sd * (178 + 68 * ms), 6), (sd * 168, -16)]), paint(HR))
    for sd in (-1, 1):                                                    # ears
        cv.drawOval(skia.Rect.MakeLTRB(sd * 176 - 30, -32, sd * 176 + 30, 58), paint(SK if sd < 0 else SKS))
        cv.drawOval(skia.Rect.MakeLTRB(sd * 176 - 30, -32, sd * 176 + 30, 58), stroke(INKC, 4))
    head = blob(HEAD_PTS)
    cv.drawPath(head, paint(SK))
    cv.save(); cv.clipPath(head, K, True)
    cv.drawRect(skia.Rect(10, -260, 260, 260), paint('#000000', shader=lin((10, 0), (185, 0), [C(SKS, 0.0), C(SKS, 0.95)])))
    cv.drawRect(skia.Rect(-260, 110, 260, 260), paint('#000000', shader=lin((0, 110), (0, 200), [C(SKS, 0.0), C(SKS, 0.8)])))
    cv.restore()
    cv.drawPath(head, stroke(INKC, 5))
    hair = blob([(-192, -10), (-186, -150), (-110, -240), (20, -256), (150, -205), (196, -90), (190, 0), (160, -70), (120, -120),
                 (60, -110), (10, -150), (-40, -105), (-110, -120), (-160, -70)])
    cv.drawPath(hair, paint(HR))
    for sp in ([(-70, -232), (-98, -296), (-34, -246)], [(6, -250), (2, -314), (50, -248)], [(84, -232), (126, -286), (124, -216)]):
        cv.drawPath(poly(sp), paint(HR))
    cv.drawPath(blob([(-40, -230), (60, -235), (150, -190), (60, -175)]), paint(P['hair_sh']))
    if age > 0.03:                                                        # the skin of the copy creases when it stops pretending
        wp = stroke('#4E4870', 3.6, min(1.0, age))
        for sd in (-1, 1):
            for yy in (-152, -130):
                q = skia.Path(); q.moveTo(sd * 36, yy); q.quadTo(sd * 84, yy - 13, sd * 132, yy + 3); cv.drawPath(q, wp)
            cv.drawArc(skia.Rect.MakeLTRB(sd * 78 - 66, -50, sd * 78 + 66, 82), 30 if sd > 0 else 40, 110, False, wp)
            q = skia.Path(); q.moveTo(sd * 40, 58); q.quadTo(sd * 76, 92, sd * 62, 140); cv.drawPath(q, wp)
            for k in range(4):
                cv.drawLine(sd * (118 + k * 10), 44 + k * 16, sd * (138 + k * 8), 26 + k * 16, wp)
    for sd in (-1, 1):                                                    # eyes behind the lenses
        ex, ey = sd * 78, -6
        eye = skia.Path.Oval(skia.Rect.MakeLTRB(ex - 42, ey - 50, ex + 42, ey + 50))
        cv.drawPath(eye, paint('#EDEAF4'))
        cv.save(); cv.clipPath(eye, K, True)
        px, py = ex + P['look'][0] * 16, ey + P['look'][1] * 18 - roll * 86
        cv.drawCircle(px, py + 5, 27, paint('#3B2B24')); cv.drawCircle(px, py + 5, 14, paint('#0B0707'))
        cv.drawCircle(px + 9, py - 5, 6, paint('#FFFFFF'))
        if roll > 0.5:                                                    # rolled back: thin red veins
            for k in range(3):
                cv.drawLine(ex - 30 + k * 26, ey + 46, ex - 22 + k * 22, ey + 10 - k * 6, stroke('#B04A5A', 2.2, 0.7))
        cv.restore()
        cv.drawPath(eye, stroke(INKC, 4))
        cv.drawLine(sd * 138, -14 + 10 * g, sd * 178, 0, stroke('#17151F', 7))             # temple arm to the ear
    for sd in (-1, 1):
        _lens(cv, sd, P)
    if g < 0.02 and crack < 0.3:
        cv.drawLine(-16, -14, 16, -14, stroke('#17151F', 8))                              # the nose bridge, whole
    else:
        for sd in (-1, 1):
            cv.drawLine(sd * 17, -12 + 10 * g, sd * 5, -2 + 14 * g, stroke('#17151F', 7))    # snapped at the bridge
    b = P['brow']
    for sd in (-1, 1):
        cv.drawLine(sd * 26, -92 - b * 12, sd * 126, -88 + b * 8, stroke(HR, 13))
    cv.drawPath(blob([(-13, 50), (0, 34), (13, 50), (0, 63)]), paint(SKS))                    # nose
    if P['jd'] < 0.03:
        q = skia.Path(); q.moveTo(-36, 119); q.quadTo(0, 112, 36, 119)
        cv.drawPath(q, stroke('#3B2C40', 7))                                                # the lips that never move


def _tendril(cv, pts, w0, col=VOID):
    """Tapered ink tendril along a cubic (p0, c1, c2, p3)."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = pts
    L, R = [], []
    n = 22
    for i in range(n + 1):
        u = i / n
        a, b_, c, d = (1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3
        x = a * x0 + b_ * x1 + c * x2 + d * x3
        y = a * y0 + b_ * y1 + c * y2 + d * y3
        dx = 3 * (1 - u) ** 2 * (x1 - x0) + 6 * u * (1 - u) * (x2 - x1) + 3 * u * u * (x3 - x2)
        dy = 3 * (1 - u) ** 2 * (y1 - y0) + 6 * u * (1 - u) * (y2 - y1) + 3 * u * u * (y3 - y2)
        m = math.hypot(dx, dy) or 1.0
        hw = w0 * (1 - u) ** 0.8 + 1.2
        L.append((x - dy / m * hw, y + dx / m * hw)); R.append((x + dy / m * hw, y - dx / m * hw))
    cv.drawPath(poly(L + R[::-1]), paint(col))


TENDRILS = [  # p0, then offsets of c1, c2, p3 from p0 (head units); group: 0 top of the split, 1 sides, 2 collar / jaw seam
    (0, (-22, -206), (-70, -110), (46, -190), (-36, -300), 13),
    (0, (26, -206), (86, -96), (-34, -186), (62, -292), 12),
    (0, (0, -214), (14, -130), (-54, -226), (20, -346), 10),
    (1, (-172, 64), (-92, 28), (-58, 166), (-162, 196), 13),
    (1, (172, 64), (98, 22), (66, 170), (170, 186), 13),
    (2, (-44, 204), (-84, 60), (-18, 166), (-134, 226), 14),
    (2, (44, 204), (92, 52), (26, 170), (142, 232), 14),
    (2, (0, 208), (32, 96), (-44, 176), (12, 268), 12)]


def _tendrils(cv, P, groups):
    amp, fr, g = P['tend'], P['frame'], P['g']
    if amp <= 0.01:
        return
    for i, (grp, p0, c1, c2, p3, w0) in enumerate(TENDRILS):
        if grp not in groups:
            continue
        osc = math.sin(fr * 0.35 + i) * 24.0 * amp
        osc2 = math.cos(fr * 0.27 + i * 1.3) * 14.0 * amp
        x0, y0 = p0
        if grp == 0:
            x0 = x0 * (0.4 + 1.2 * g)
        k = min(1.0, amp)
        pts = [(x0, y0), (x0 + c1[0] * k + osc * 0.5, y0 + c1[1] * k), (x0 + c2[0] * k - osc, y0 + c2[1] * k + osc2),
               (x0 + p3[0] * k + osc * 1.3, y0 + p3[1] * k - osc2)]
        _tendril(cv, pts, w0 * (0.5 + 0.5 * k))


def _maw(cv, P):
    k = min(1.0, P['g'] * 1.6) * P['jd']
    if k < 0.03:
        return
    cx, cy = 0.0, 122 + 26 * P['jd']
    rx, ry = 30 + 78 * k, 14 + 92 * k
    cv.drawOval(skia.Rect.MakeLTRB(cx - rx - 13, cy - ry - 13, cx + rx + 13, cy + ry + 13), paint(GUM))
    cv.drawOval(skia.Rect.MakeLTRB(cx - rx - 13, cy - ry - 13, cx + rx + 13, cy + ry + 13), stroke(INKC, 4))
    cv.drawOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), paint(VOID))
    n = 18
    for i in range(n):
        th = 2 * math.pi * i / n + 0.17
        ln = (22 + 40 * abs(math.sin(th))) * k * (0.8 + 0.4 * ((i * 7) % 3) / 2)
        bx, by = cx + rx * math.cos(th), cy + ry * math.sin(th)
        tx, ty = -math.sin(th), math.cos(th)
        tip = (cx + (rx - ln) * math.cos(th) + 4 * math.sin(P['frame'] * 0.5 + i), cy + (ry - ln) * math.sin(th))
        tooth = poly([(bx + tx * 10, by + ty * 10), tip, (bx - tx * 10, by - ty * 10)])
        cv.drawPath(tooth, paint(TOOTH)); cv.drawPath(tooth, stroke(INKC, 1.8))


def _edges(P):
    g, jd = P['g'], P['jd']
    return {sd: [(sd * _notch(y, g, jd), y) for y in range(-262, 250, 12)] for sd in (-1, 1)}


def _mimic_head_lit(cv, P):
    """Everything that catches light: neck + the face (sealed, or clipped to the two torn halves)."""
    g = P['g']
    cv.drawRect(skia.Rect(-46, 150, 46, 276), paint(P['skin_sh']))                              # neck
    if g < 0.004:
        _face(cv, P)
        return
    edge = _edges(P)
    for sd in (-1, 1):
        cv.save()
        cv.translate(sd * g * 55.0, 0); cv.rotate(sd * g * 16.0, sd * PIVX, PIVY)
        cv.clipPath(poly(edge[sd] + [(sd * 520, 250), (sd * 520, -340)]), K, True)
        _face(cv, P)
        cv.restore()


def _mimic_head_dark(cv, P):
    """Everything light does not touch: the abyss, the four eyes, gums + 32 needle teeth, the maw, the ink tendrils."""
    g, jd = P['g'], P['jd']
    if g < 0.004:
        return
    edge = _edges(P)
    left = [_xf(-1, g, x, y) for x, y in edge[-1] if -226 <= y <= 200]
    right = [_xf(1, g, x, y) for x, y in edge[1] if -226 <= y <= 200]
    cv.drawPath(poly(left + right[::-1] + [(0, left[0][1] + 34 * g)]), paint(VOID))             # the abyss between the halves
    cv.drawLine(0, 190, 0, 276, stroke(VOID, 6 + 10 * g))                                       # the tear runs down the throat
    ea = max(0.0, min(1.0, (g - 0.3) / 0.35))
    if ea > 0:                                                                                  # four red pinprick eyes inside
        for k, (yy, fx) in enumerate(((-44, 0.46), (-44, -0.46), (6, 0.40), (6, -0.40))):
            half = abs(_xf(-1, g, -_notch(yy, g, jd), yy)[0])
            ex = fx * half + P['look'][0] * 5 + 2.2 * math.sin(P['frame'] * 0.23 + k * 1.7)
            ey = yy + P['look'][1] * 5 + 1.8 * math.cos(P['frame'] * 0.19 + k * 2.3)
            r = (5.0 + 2.5 * g) * P['eye_k']
            gp = paint(C(EYE_RED, 0.85 * ea))
            gp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 9.0))
            cv.drawCircle(ex, ey, r * 2.6, gp)
            cv.drawCircle(ex, ey, r, paint(C(EYE_RED, ea))); cv.drawCircle(ex, ey, r * 0.4, paint(C('#FFD0C8', ea)))
    _tendrils(cv, P, (0,))
    tg = min(1.0, g * 1.3)
    for sd in (-1, 1):
        cv.save()
        cv.translate(sd * g * 55.0, 0); cv.rotate(sd * g * 16.0, sd * PIVX, PIVY)
        e = [q for q in edge[sd] if -226 <= q[1] <= 200]
        cv.drawPath(poly(e, closed=False), stroke(GUM, 6 + 12 * tg))                              # crimson gum along the tear
        for i in range(16):                                                                     # 16 needle teeth per side = 32
            y = -212 + i * 26.0
            x = sd * _notch(y, g, jd)
            hgt = 0.35 + 0.65 * (1.0 if (y < -70 or y > 70) else 0.25)
            ln = (14 + 30 * hgt + 6 * ((i * 5) % 3)) * tg
            if ln < 1.5:
                continue
            tooth = poly([(x, y - 9), (x - sd * ln, y + 3 * math.sin(i * 2.1)), (x, y + 9)])
            cv.drawPath(tooth, paint(TOOTH)); cv.drawPath(tooth, stroke(INKC, 1.6))
        cv.restore()
    _maw(cv, P)


def _collar(cv, P):
    """Teal collar, placket, chest pocket (mascot-local units, feet at 0,0); torn open when the tendrils are out."""
    for sd in (-1, 1):
        wing = poly([(sd * 74, -782), (sd * 8, -744), (sd * 54, -696)])
        cv.drawPath(wing, paint(TEAL_HI)); cv.drawPath(wing, stroke(INKC, 4))
    cv.drawLine(0, -744, 0, -470, stroke(TEAL_SH, 6))
    for k in range(4):
        cv.drawCircle(0, -712 + k * 62, 6, paint('#BFE6E0'))
    pocket = skia.Rect.MakeLTRB(40, -668, 100, -604)
    cv.drawRoundRect(pocket, 8, 8, paint(TEAL_SH)); cv.drawRoundRect(pocket, 8, 8, stroke(INKC, 3))
    cv.drawLine(58, -676, 58, -640, stroke('#D8D8E0', 5))                                       # the pen he always carries
    if P['tend'] > 0.05:
        tear = poly([(-52, -772), (-20, -742), (-34, -706), (0, -690), (30, -712), (22, -744), (54, -770), (0, -752)])
        cv.drawPath(tear, paint(VOID))


def draw_bob_mimic_puppet(canvas, x, y, scale, split_gap, jaw_drop, tendril_amp, glasses_crack, glitch_px, frame=0, pose=None,
                          hip_y=None, floor_y=None, body=True, look=(0.0, 0.0), eye_roll=0.0, head_tilt=0.0, brow=0.0,
                          tint='#B4B1DC', under=1.0, rim=1.0, ink_w=None, lens_a=0.16, eye_k=1.0, age=None, mess=None):
    """The Unzipped Bob Mimic. (x, y) = feet (flat.py convention; or pass hip_y + floor_y for a seated body), scale 1 ~ 1150 px tall.
    split_gap 0 = Bob's disguise (lavender-grey skin, NO contact shadow) .. 1 = unzipped: each half moves 55 px out and turns 16 deg,
    glasses snapped at the bridge. jaw_drop opens the round maw. tendril_amp grows + animates the 8 ink tendrils
    (sin(frame * 0.35 + i) * 24 * amp). glasses_crack whitens + fractures the lenses. glitch_px > 0: RGB split + scanline tears."""
    cv, s, g = canvas, scale, max(0.0, min(1.0, split_gap))
    if hip_y is not None:
        y = hip_y + 430 * s
    P = dict(g=g, jd=max(0.0, jaw_drop), tend=max(0.0, tendril_amp), crack=max(0.0, min(1.0, glasses_crack)), frame=frame, look=look,
             roll=eye_roll, age=g if age is None else age, brow=brow, skin=SKIN_M, skin_sh=SKIN_M_SH, hair=HAIR_B, hair_sh=HAIR_B_SH,
             lens_a=lens_a, eye_k=eye_k, mess=0.3 + 0.7 * g if mess is None else mess)
    pose = dict(pose or {})
    lean = pose.get('body_lean', 0.0)
    hx = x + s * math.sin(math.radians(lean)) * 330
    hy = y + s * (-900 + pose.get('crouch', 0.0) * 300)
    bounds = skia.Rect.MakeLTRB(hx - 640 * s, hy - 560 * s, hx + 640 * s, (y if body else hy + 520 * s) + 60 * s)

    def head_xf(fn):
        cv.save(); cv.translate(hx, hy); cv.scale(s, s); cv.rotate(head_tilt)
        fn()
        cv.restore()

    def flesh():
        if body:
            mascot(cv, x, y, s, no_head=True, legs=hip_y is None and pose.get('legs', True), light_side=-1,
                   **{**FAKE, **{k: v for k, v in pose.items() if k != 'legs'}})
            if hip_y is not None and floor_y is not None:
                sit_legs(cv, x, hip_y, s, floor_y, FAKE['pants'], FAKE['pants_sh'], FAKE['shoe'], FAKE['shoe_sh'])
            cv.save(); cv.translate(x, y); cv.scale(s, s); cv.rotate(lean, 0, -430)
            _collar(cv, P)
            cv.restore()
        head_xf(lambda: _mimic_head_lit(cv, P))

    def draw():                                                                                 # unlit (for the RGB ghosts)
        head_xf(lambda: _tendrils(cv, P, (1,)))
        flesh()
        head_xf(lambda: (_mimic_head_dark(cv, P), _tendrils(cv, P, (2,))))

    def lit():
        head_xf(lambda: _tendrils(cv, P, (1,)))                                                 # ink tendrils stay black: outside the lit group
        cv.saveLayer(bounds, None)
        flesh()
        if tint:
            cv.drawPaint(paint(C(tint), blend=skia.BlendMode.kModulate))
        if under > 0:                                                                           # cold cyan phone light from below
            c0, c1 = skia.Color(55, 190, 255, int(min(255, 135 * under))), skia.Color(55, 190, 255, 0)
            if body:                                                                            # strongest on the chest + under the chin
                sh = skia.GradientShader.MakeLinear([(0, y - 250 * s), (0, hy - 250 * s)], [c1, c0, c1], [0.0, 0.42, 1.0])
            else:
                sh = skia.GradientShader.MakeLinear([(0, hy + 330 * s), (0, hy - 250 * s)], [c0, c1])
            cv.drawPaint(skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kSrcATop))
        if rim > 0:                                                                             # crimson TV alert rim from the left
            c0 = skia.Color(255, 25, 40, int(min(255, 120 * rim)))
            cv.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeLinear([(hx - 285 * s, 0), (hx - 178 * s, 0)], [c0, skia.Color(255, 25, 40, 0)]),
                                    BlendMode=skia.BlendMode.kSrcATop))
        cv.restore()
        head_xf(lambda: (_mimic_head_dark(cv, P), _tendrils(cv, P, (2,))))

    w = ink_w if ink_w is not None else max(3, min(11, 3.2 * s))
    with_ink(cv, w, lit, bounds=bounds)
    if glitch_px > 0:                                                                           # VHS: RGB ghosts (screen) + scanline tears
        for dx, col in ((-glitch_px, skia.Color(255, 40, 40)), (glitch_px, skia.Color(40, 255, 255))):
            lp = skia.Paint(BlendMode=skia.BlendMode.kScreen, ColorFilter=skia.ColorFilters.Blend(col, skia.BlendMode.kModulate), Alphaf=0.55)
            cv.saveLayer(bounds, lp)
            cv.translate(dx, 0); draw()
            cv.restore()
        rng = np.random.default_rng(frame)
        for _ in range(5):
            ty = rng.uniform(bounds.top(), bounds.bottom()); th = rng.uniform(8, 34) * max(1.0, s); sh = rng.uniform(-3, 3) * glitch_px
            cv.save(); cv.clipRect(skia.Rect.MakeLTRB(bounds.left(), ty, bounds.right(), ty + th)); cv.translate(sh, 0)
            lit()
            cv.restore()
    return dict(head=(hx, hy), s=s, x=x, y=y)


# ----------------------------------------------------------------------------------------------- seated bodies
def sit_legs(cv, x, hip_y, s, floor_y, pants, pants_sh, shoe, shoe_sh, ls=-1, knee_dy=64, spread=1.0, foot_dx=(0, 0)):
    """Front view, sitting: foreshortened thighs to the seat edge, shins down to the floor, shoes."""
    for i, side in enumerate((-1, 1)):
        hx, kx, ky = x + side * 50 * s, x + side * 68 * s * spread, hip_y + knee_dy * s
        col = pants if side == ls else pants_sh
        fx = kx + side * 4 * s + foot_dx[i]
        cv.drawLine(hx, hip_y + 4 * s, kx, ky, stroke(col, 104 * s))
        cv.drawLine(kx, ky, fx, floor_y - 34 * s, stroke(col, 88 * s))
        sh = skia.Rect.MakeLTRB(fx - 58 * s, floor_y - 52 * s, fx + 58 * s, floor_y + 8 * s)
        cv.drawRoundRect(sh, 26 * s, 26 * s, paint(shoe if side == ls else shoe_sh))
        cv.drawRect(skia.Rect.MakeLTRB(fx - 56 * s, floor_y - 8 * s, fx + 56 * s, floor_y + 8 * s), paint('#8E90A0'))


def seated(cv, x, hip_y, s, floor_y, tint, cols=None, lights=(), ink_w=None, phone=None, **pose):
    """A flat.py puppet sitting on the couch (front view). phone=(alpha) draws the phone's back in his hands + its glow on him."""
    cols = cols or {}
    y = hip_y + 430 * s
    bounds = skia.Rect.MakeLTRB(x - 420 * s, y - 1180 * s, x + 420 * s, floor_y + 30 * s)
    out = {}

    def draw():
        r = mascot(cv, x, y, s, legs=False, **{**cols, **pose})
        out.update({k: tuple(v) for k, v in (r or {}).items()})
        sit_legs(cv, x, hip_y, s, floor_y, cols.get('pants', '#3557A6'), cols.get('pants_sh', '#26407E'), cols.get('shoe', '#F4F4F4'),
                 cols.get('shoe_sh', '#C9CCD3'), ls=pose.get('light_side', 1))
        if phone is not None:
            px, py = x + phone[0] * s, hip_y + phone[1] * s
            cv.save(); cv.translate(px, py); cv.rotate(phone[2] if len(phone) > 2 else 0)
            ph = skia.Rect.MakeLTRB(-46 * s, -92 * s, 46 * s, 92 * s)
            cv.drawRoundRect(ph, 14 * s, 14 * s, paint('#15141C'))
            cv.drawRoundRect(skia.Rect.MakeLTRB(-34 * s, -80 * s, -6 * s, -44 * s), 8 * s, 8 * s, paint('#2A2934'))
            cv.restore()
            for sd in (-1, 1):                                                                  # thumbs / fingers over its edges
                cv.drawCircle(px + sd * 46 * s, py + 30 * s, 26 * s, paint(cols.get('skin', '#F2C29B')))

    def lit():
        cv.saveLayer(bounds, None)
        draw()
        if tint:
            cv.drawPaint(paint(C(tint), blend=skia.BlendMode.kModulate))
        for sh in lights:
            cv.drawPaint(skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kSrcATop))
        cv.restore()
    with_ink(cv, ink_w if ink_w is not None else max(3, min(11, 3.2 * s)), lit, bounds=bounds)
    out.update(x=x, y=y, s=s, head=(x + s * math.sin(math.radians(pose.get('body_lean', 0.0))) * 330, y - 900 * s))
    return out


def lit_puppet(cv, x, y, s, tint=None, lights=(), ink_w=None, bounds=None, post=None, **pose):
    """Any flat.py puppet (any view) with the studio ink outline, a colour tint and painted lights. post() draws extras inside the lit layer."""
    bounds = bounds or skia.Rect.MakeLTRB(x - 780 * s, y - 1330 * s, x + 780 * s, y + 160 * s)
    out = {}

    def lit():
        cv.saveLayer(bounds, None)
        r = mascot(cv, x, y, s, **pose)
        out.update({k: tuple(v) for k, v in (r or {}).items()})
        if post:
            post()
        if tint:
            cv.drawPaint(paint(C(tint), blend=skia.BlendMode.kModulate))
        for sh in lights:
            cv.drawPaint(skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kSrcATop))
        cv.restore()
    with_ink(cv, ink_w if ink_w is not None else max(3, min(11, 3.2 * s)), lit, bounds=bounds)
    out.update(x=x, y=y, s=s)
    return out


def under_light(x, y_bottom, y_top, a=0.55, col=(55, 190, 255)):
    return skia.GradientShader.MakeLinear([(x, y_bottom), (x, y_top)], [skia.Color(col[0], col[1], col[2], int(255 * a)), skia.Color(col[0], col[1], col[2], 0)])


def side_light(x0, x1, a=0.4, col=(255, 25, 40)):
    return skia.GradientShader.MakeLinear([(x0, 0), (x1, 0)], [skia.Color(col[0], col[1], col[2], int(255 * a)), skia.Color(col[0], col[1], col[2], 0)])


# ----------------------------------------------------------------------------------------------- hands, phone
def phone_in_hand(cv, cx, cy, s, tilt, screen_fn, sleeve='#E87A20', skin='#F2C29B', skin2='#E4B088', ink=6.0, tremble=0.0):
    """A phone held up to the lens (screen facing us). Phone-local units: body 660 x 1300, screen (-300..300, -620..620).
    screen_fn(cv) draws the UI in those units."""
    def palm():
        cv.save(); cv.translate(cx, cy); cv.scale(s, s); cv.rotate(tilt)
        cv.save(); cv.translate(330, 900); cv.rotate(-22)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-200, -60, 200, 1300), 160, 160, paint(sleeve))
        cv.restore()
        cv.drawOval(skia.Rect.MakeLTRB(-150, 330, 440, 860), paint(skin))
        cv.restore()
    with_ink(cv, ink, palm)

    def body():
        cv.save(); cv.translate(cx, cy); cv.scale(s, s); cv.rotate(tilt)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-330, -650, 330, 650), 74, 74, paint('#17151D'))
        cv.restore()
    with_ink(cv, ink, body)
    cv.save(); cv.translate(cx, cy); cv.scale(s, s); cv.rotate(tilt)
    cv.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(-300, -620, 300, 620), 52, 52), True)
    screen_fn(cv)
    cv.restore()

    def fingers():
        cv.save(); cv.translate(cx, cy); cv.scale(s, s); cv.rotate(tilt)
        for k in range(4):
            cv.drawRoundRect(skia.Rect.MakeLTRB(-398, 150 + k * 104 + tremble * math.sin(k * 2.1), -262, 236 + k * 104), 42, 42, paint(skin if k % 2 == 0 else skin2))
        cv.save(); cv.translate(304, 320); cv.rotate(-28)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-60, -176, 60, 124), 58, 58, paint(skin))
        cv.restore()
        cv.restore()
    with_ink(cv, ink, fingers)


def long_hand(cv, joints, grip, s, t, wrap=1.0, ink=5.0):
    """The double-jointed arm from under the couch: polyline joints -> wrist at `grip`; fingers wrap `wrap` (0..1) around an ankle."""
    def draw():
        pts = list(joints) + [grip]
        for (a, b) in zip(pts, pts[1:]):
            cv.drawLine(a[0], a[1], b[0], b[1], stroke(SKIN_M, 46 * s))
        for j in pts[1:-1]:
            cv.drawCircle(j[0], j[1], 31 * s, paint(SKIN_M_SH))                                 # knobbly extra elbows
        gx, gy = grip
        cv.drawOval(skia.Rect.MakeLTRB(gx - 64 * s, gy - 54 * s, gx + 64 * s, gy + 54 * s), paint(SKIN_M))
        for k in range(4):                                                                      # four long fingers hooking over the ankle
            fy = gy - 66 * s + k * 44 * s
            reach = (150 + 30 * math.sin(k * 1.7)) * s * (0.35 + 0.65 * wrap)
            q = skia.Path(); q.moveTo(gx - 20 * s, fy)
            q.quadTo(gx - reach * 0.6, fy - 40 * s * wrap, gx - reach, fy + 22 * s * wrap + 3 * s * math.sin(t * 9 + k))
            cv.drawPath(q, stroke(SKIN_M, 30 * s))
            cv.drawCircle(gx - reach, fy + 22 * s * wrap, 12 * s, paint('#2A2238'))             # dark nail
        q = skia.Path(); q.moveTo(gx + 10 * s, gy + 40 * s); q.quadTo(gx - 60 * s, gy + 110 * s, gx - 120 * s * wrap, gy + 96 * s)
        cv.drawPath(q, stroke(SKIN_M_SH, 32 * s))                                               # thumb
    xs = [p[0] for p in joints] + [grip[0] - 220 * s, grip[0] + 80 * s]
    ys = [p[1] for p in joints] + [grip[1] - 140 * s, grip[1] + 160 * s]
    with_ink(cv, ink, draw, bounds=skia.Rect.MakeLTRB(min(xs) - 60, min(ys) - 60, max(xs) + 60, max(ys) + 60))


def palm_on_glass(cv, x, y, s, flip=1, blood=1.0, press=1.0):
    """A hand pressed flat on frosted glass (seen from inside): bright where the skin touches, blood smeared around it."""
    cv.save(); cv.translate(x, y); cv.scale(s * flip, s)
    if blood > 0:
        for k, (bx, by, br) in enumerate(((-30, 70, 60), (40, 30, 46), (0, 130, 40), (-70, -10, 30))):
            cv.drawCircle(bx, by, br, paint(C('#6E1016', 0.55 * blood), blur=10))
        for k in range(3):
            cv.drawLine(-40 + k * 40, 120, -44 + k * 42, 260 + 40 * k, stroke('#6E1016', 12 - 2 * k, 0.6 * blood))  # drips
    skin = C('#EBCDBE', 0.55 + 0.4 * press)
    cv.drawRoundRect(skia.Rect.MakeLTRB(-70, -20, 70, 130), 50, 50, paint(skin))
    for k, (fx, ln, a) in enumerate(((-58, 120, -14), (-20, 150, -4), (20, 146, 5), (56, 116, 15))):
        cv.save(); cv.translate(fx, 0); cv.rotate(a)
        cv.drawRoundRect(skia.Rect.MakeLTRB(-17, -ln, 17, 10), 17, 17, paint(skin))
        cv.restore()
    cv.save(); cv.translate(-78, 70); cv.rotate(-62)
    cv.drawRoundRect(skia.Rect.MakeLTRB(-18, -84, 18, 10), 18, 18, paint(skin))
    cv.restore()
    cv.restore()
