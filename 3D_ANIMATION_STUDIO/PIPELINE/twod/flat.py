"""2dEDIT — real flat 2D animation (vector, drawn with Skia; no 3D).

Characters are 2D cut-out puppets built from vector shapes (flat fill + one cel-shadow tone + rim light),
sets are flat vector paintings with gradients, light is painted (radial glows, light cones, vignette).
Everything is resolution-independent and drawn straight at 1080x1920.
"""
import math

import numpy as np
import skia

W, H = 1080, 1920


def C(hexs, a=1.0):
    h = hexs.lstrip('#')
    return skia.Color4f(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def paint(col, aa=True, style='fill', width=0.0, blur=0.0, shader=None, blend=None):
    p = skia.Paint(AntiAlias=aa)
    if isinstance(col, str):
        col = C(col)
    p.setColor4f(col)
    if style == 'stroke':
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader is not None:
        p.setShader(shader)
    if blend is not None:
        p.setBlendMode(blend)
    return p


def poly(pts, closed=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def blob(pts):
    """Smooth closed shape through points (Catmull-Rom -> cubic)."""
    n = len(pts)
    p = skia.Path()
    p.moveTo(*pts[0])
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    p.close()
    return p


def lin(p0, p1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(*p0), skia.Point(*p1)], [c if isinstance(c, int) else c.toColor() for c in cols], pos)


def rad(c, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(*c), r, [c_.toColor() for c_ in cols], pos)


def glow(cv, c, r, col, alpha=0.6):
    """Painted light: additive radial falloff."""
    cv.drawCircle(*c, r, paint(col, shader=rad(c, r, [C(col, alpha), C(col, alpha * 0.35), C(col, 0.0)], [0, 0.35, 1]),
                                blend=skia.BlendMode.kPlus))


def shade(cv, c, r, alpha=0.6):
    """Darkness: multiply-style radial vignette (dark outside)."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#000000', shader=rad(c, r, [C('#000000', 0.0), C('#000000', 0.0), C('#000000', alpha)], [0, 0.45, 1])))


# ===================================================================== the mascot (2D cut-out puppet)
SKIN, SKIN_SH = '#F2C29B', '#D99B76'
HAIR, HAIR_SH = '#6B3E1F', '#4A2912'
SHIRT, SHIRT_SH = '#F07A1A', '#C85A0C'
JEANS, JEANS_SH = '#3557A6', '#26407E'
SHOE, SHOE_SH = '#F4F4F4', '#C9CCD3'
EYE_IRIS = '#5A3417'
LINE = '#2A1A12'

DEFAULT_POSE = dict(
    look=(0.0, 0.0),          # pupils (-1..1, -1..1)
    brow=0.0,                 # -1 angry .. 0 neutral .. +1 worried/raised
    lids=0.0,                 # 0 open .. 1 closed (upper lid)
    mouth='flat',             # flat / o / smile / frown / open / grin / smirk
    mouth_open=0.0,           # 0..1 for talking
    head_tilt=0.0,            # degrees
    head_turn=0.0,            # -1..1 (fake 3/4 turn: features slide)
    body_lean=0.0,            # degrees
    arm_l=(10, 10), arm_r=(10, 10),   # (shoulder deg from down, elbow bend deg)
    hand_l='rest', hand_r='rest',
    walk=None,                # phase 0..1 or None
    sweat=False,
    light_side=1,             # +1 key light from the right, -1 from the left
    rim='#9FC3FF', rim_a=0.0,
    view='front',             # front / back
    shirt=SHIRT, shirt_sh=SHIRT_SH,
    dark=0.0,                 # 0..1 overall darkening (low-key)
)


def _limb(cv, x0, y0, ang, l1, bend, l2, w, col, col_sh, end=None, flip=1):
    """Two-segment limb. ang: degrees from straight down (positive = outward by flip)."""
    a1 = math.radians(ang) * flip
    x1, y1 = x0 + math.sin(a1) * l1, y0 + math.cos(a1) * l1
    a2 = a1 + math.radians(bend) * flip
    x2, y2 = x1 + math.sin(a2) * l2, y1 + math.cos(a2) * l2
    p = skia.Path()
    p.moveTo(x0, y0)
    p.lineTo(x1, y1)
    p.lineTo(x2, y2)
    cv.drawPath(p, paint(col, style='stroke', width=w))
    return (x1, y1), (x2, y2)


def mascot(cv, x, y, s=1.0, **pose):
    """Draw the mascot with feet at (x, y). s = scale (1.0 ~ 1000 px tall)."""
    P = dict(DEFAULT_POSE)
    P.update(pose)
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    ls = P['light_side']
    back = P['view'] == 'back'
    # ---------------- legs
    hip_y = -430
    ph = P['walk']
    for side in ((-1, 1) if P.get('legs', True) else ()):
        if ph is None:
            th, kn = 2 * side, 0
        else:
            q = math.sin(2 * math.pi * (ph + (0.5 if side > 0 else 0)))
            th, kn = 22 * q, max(0, -q) * 35
        hx = side * 48
        a = math.radians(th)
        kx, ky = hx + math.sin(a) * 210, hip_y + math.cos(a) * 210
        b = a - math.radians(kn)
        fx, fy = kx + math.sin(b) * 205, ky + math.cos(b) * 205
        col = JEANS if side == ls else JEANS_SH
        cv.drawPath(poly([(hx, hip_y), (kx, ky), (fx, fy)], closed=False), paint(col, style='stroke', width=92))
        sh = skia.Path()
        sh.addRRect(skia.RRect.MakeRectXY(skia.Rect(fx - 58 + side * 6, fy - 24, fx + 62 + side * 6, fy + 30), 26, 26))
        cv.drawPath(sh, paint(SHOE if side == ls else SHOE_SH))
        cv.drawRect(skia.Rect(fx - 56 + side * 6, fy + 14, fx + 60 + side * 6, fy + 30), paint('#B9BCC4'))
    # ---------------- torso (t-shirt)
    lean = P['body_lean']
    cv.save()
    cv.rotate(lean, 0, hip_y)
    sh_y = -760
    torso = blob([(-112, sh_y + 10), (0, sh_y - 14), (112, sh_y + 10), (128, sh_y + 160), (120, hip_y + 20), (0, hip_y + 34), (-120, hip_y + 20), (-128, sh_y + 160)])
    cv.drawPath(torso, paint(P['shirt']))
    cv.save()
    cv.clipPath(torso, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(-200 if ls > 0 else 30, sh_y - 40, -30 if ls > 0 else 200, hip_y + 60), paint(P['shirt_sh']))
    if P['rim_a'] > 0:                                    # rim light only on the shadow side
        cv.clipRect(skia.Rect(-400, -2000, -60, 2000) if ls > 0 else skia.Rect(60, -2000, 400, 2000))
        cv.drawPath(torso, paint(C(P['rim'], P['rim_a']), style='stroke', width=12, blur=3))
    cv.restore()
    if not back:                                          # collar
        cv.drawPath(blob([(-46, sh_y - 6), (0, sh_y + 30), (46, sh_y - 6), (0, sh_y + 8)]), paint(SKIN_SH))
    # ---------------- arms
    for side, (ang, bend), hand in ((-1, P['arm_l'], P['hand_l']), (1, P['arm_r'], P['hand_r'])):
        sx = side * 112
        col = SKIN if side == ls else SKIN_SH
        (ex, ey), (hx, hy) = _limb(cv, sx, sh_y + 40, ang, 175, bend, 165, 54, col, col, flip=side)
        a = math.radians(ang) * side
        sx2, sy2 = sx + math.sin(a) * 95, sh_y + 40 + math.cos(a) * 95
        cv.drawPath(poly([(sx, sh_y + 30), (sx2, sy2)], closed=False), paint(P['shirt'] if side == ls else P['shirt_sh'], style='stroke', width=82))
        r = 34 if hand != 'fist' else 36
        cv.drawCircle(hx, hy, r, paint(col))
        if hand == 'point':
            cv.drawPath(poly([(hx, hy), (hx + math.sin(a + 0.6 * side) * 70, hy + math.cos(a + 0.6 * side) * 70)], closed=False),
                        paint(col, style='stroke', width=20))
    cv.restore()
    # ---------------- head
    cv.save()
    hx0, hy0 = math.sin(math.radians(lean)) * 330, -900
    cv.translate(hx0, hy0)
    cv.rotate(P['head_tilt'])
    turn = P['head_turn']
    # neck
    cv.drawRect(skia.Rect(-38, 40, 38, 150), paint(SKIN_SH))
    head = blob([(-178, -40), (-150, -170), (0, -222), (150, -170), (178, -40), (160, 90), (90, 175), (0, 195), (-90, 175), (-160, 90)])
    cv.drawPath(head, paint(SKIN))
    cv.save()
    cv.clipPath(head, skia.ClipOp.kIntersect, True)
    cv.drawOval(skia.Rect(-430, -280, -115, 280) if ls > 0 else skia.Rect(115, -280, 430, 280), paint(SKIN_SH, blur=18))
    if P['rim_a'] > 0:
        cv.clipRect(skia.Rect(-400, -400, -70, 400) if ls > 0 else skia.Rect(70, -400, 400, 400))
        cv.drawPath(head, paint(C(P['rim'], P['rim_a']), style='stroke', width=14, blur=4))
    cv.restore()
    for side in (-1, 1):                                   # ears
        ex = side * 176 + turn * -30
        cv.drawOval(skia.Rect(ex - 30, -30, ex + 30, 60), paint(SKIN if side == ls else SKIN_SH))
    if back:
        hair = blob([(-190, -20), (-185, -150), (-90, -245), (40, -252), (160, -190), (192, -60), (185, 70), (120, 150), (0, 175), (-120, 150), (-185, 70)])
        cv.drawPath(hair, paint(HAIR))
        cv.drawPath(blob([(-60, -200), (30, -230), (100, -170), (20, -150)]), paint(HAIR_SH))
        cv.restore()
        cv.restore()
        return
    fx = turn * 60                                         # features slide for a fake 3/4 turn
    # hair (front): swept fringe
    hair = blob([(-192, -10), (-186, -150), (-110, -240), (20, -256), (150, -205), (196, -90), (190, 0), (160, -70), (120, -120),
                 (60, -110 + 0), (10, -150), (-40, -105), (-110, -120), (-160, -70)])
    cv.drawPath(hair, paint(HAIR))
    cv.drawPath(blob([(-40, -230), (60, -235), (150, -190), (60, -175)]), paint(HAIR_SH))
    # eyes
    lid = P['lids']
    for side in (-1, 1):
        ex, ey = fx + side * 72, -10
        cv.drawOval(skia.Rect(ex - 46, ey - 56, ex + 46, ey + 56), paint('#FFFFFF'))
        px, py = ex + P['look'][0] * 18, ey + P['look'][1] * 20
        cv.save()
        cv.clipPath(skia.Path.Oval(skia.Rect(ex - 46, ey - 56, ex + 46, ey + 56)), skia.ClipOp.kIntersect, True)
        k = P.get('pupil', 1.0)
        cv.drawCircle(px, py + 6, 34 * k, paint(P.get('iris', EYE_IRIS)))
        cv.drawCircle(px, py + 6, 20 * k, paint('#160C06'))
        cv.drawCircle(px + 11 * k, py - 6 * k, 9 * min(1, k + 0.2), paint('#FFFFFF'))
        if lid > 0:
            cv.drawRect(skia.Rect(ex - 50, ey - 60, ex + 50, ey - 60 + 116 * lid), paint(SKIN))
            cv.drawLine(ex - 50, ey - 60 + 116 * lid, ex + 50, ey - 60 + 116 * lid, paint(LINE, style='stroke', width=6))
        cv.restore()
        cv.drawOval(skia.Rect(ex - 46, ey - 56, ex + 46, ey + 56), paint(LINE, style='stroke', width=5))
        # brows
        b = P['brow']
        inner = ey - 82 - b * 26
        outer = ey - 82 + b * 10
        x_in, x_out = ex - side * 30, ex + side * 40
        cv.drawPath(poly([(x_in, inner), (x_out, outer)], closed=False), paint(HAIR_SH, style='stroke', width=17))
    # nose
    cv.drawPath(blob([(fx - 10, 52), (fx + 2, 40), (fx + 14, 54), (fx + 2, 64)]), paint(SKIN_SH))
    # mouth
    my, m, o = 112, P['mouth'], P['mouth_open']
    mp = paint(LINE, style='stroke', width=8)
    if o > 0.05 or m in ('open', 'o'):
        oo = max(o, 0.6 if m in ('open', 'o') else 0)
        wdt = 26 if m == 'o' else 46
        cv.drawOval(skia.Rect(fx - wdt, my - 12 * oo, fx + wdt, my + 40 * oo), paint('#5B1F1A'))
        cv.drawOval(skia.Rect(fx - wdt * 0.6, my + 18 * oo, fx + wdt * 0.6, my + 40 * oo), paint('#D9706B'))
    elif m == 'smile':
        cv.drawPath(poly([(fx - 44, my - 6), (fx, my + 18), (fx + 44, my - 6)], closed=False), mp)
    elif m == 'smirk':
        q = skia.Path(); q.moveTo(fx - 38, my + 6); q.quadTo(fx + 10, my + 16, fx + 52, my - 14)
        cv.drawPath(q, mp)
    elif m == 'grin':
        q = skia.Path(); q.moveTo(fx - 60, my - 10); q.quadTo(fx, my + 40, fx + 60, my - 10); q.close()
        cv.drawPath(q, paint('#FFFFFF')); cv.drawPath(q, mp)
    elif m == 'frown':
        q = skia.Path(); q.moveTo(fx - 40, my + 14); q.quadTo(fx, my - 12, fx + 40, my + 14)
        cv.drawPath(q, mp)
    else:
        cv.drawLine(fx - 30, my + 4, fx + 30, my + 4, mp)
    if P.get('blush', 0) > 0:
        for side in (-1, 1):
            cv.drawOval(skia.Rect(fx + side * 112 - 34, 52, fx + side * 112 + 34, 80), paint(C('#E86A5A', P['blush']), blur=8))
    if P['sweat']:
        cv.drawPath(blob([(fx + 150, -80), (fx + 162, -40), (fx + 150, -26), (fx + 138, -40)]), paint('#BFE3FF'))
    cv.restore()
    cv.restore()
