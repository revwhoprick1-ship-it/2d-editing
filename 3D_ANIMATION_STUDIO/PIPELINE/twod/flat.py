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
    arm_l=(3, 0), arm_r=(3, 0),   # (shoulder deg out from hanging straight down, elbow bend deg)
    hand_l='rest', hand_r='rest',
    walk=None,                # phase 0..1 or None
    run=False,
    crouch=0.0,               # 0 standing .. 1 squatting / hugging knees (front view)
    sweat=False,
    light_side=1,             # +1 key light from the right, -1 from the left
    rim='#9FC3FF', rim_a=0.0,
    view='front',             # front / back / side
    face=1,                   # side view: +1 faces right, -1 faces left
    skin=SKIN, skin_sh=SKIN_SH, hair=HAIR, hair_sh=HAIR_SH,
    shirt=SHIRT, shirt_sh=SHIRT_SH, pants=JEANS, pants_sh=JEANS_SH, shoe=SHOE, shoe_sh=SHOE_SH,
    belly=1.0,                # torso width
    cap=None, mustache=None, bald=False,
    item=None,                # 'flashlight' / 'pen' / 'keys' in the right hand
)

LEG_L1, LEG_L2, HIP_Y, SH_Y = 210, 205, -430, -760
import os as _os
_TF = skia.Typeface.MakeFromFile(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'ASSETS', 'fonts', 'RobotoCondensed-Bold.ttf'))


def _seg(cv, pts, col, w):
    cv.drawPath(poly(pts, closed=False), paint(col, style='stroke', width=w))


def _shoe(cv, fx, fy, col, col_sh, dirx=0):
    """dirx: 0 front view, +1/-1 side view toe direction."""
    if dirx == 0:
        cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(fx - 56, fy - 24, fx + 56, fy + 30), 26, 26)), paint(col))
        cv.drawRect(skia.Rect(fx - 54, fy + 14, fx + 54, fy + 30), paint(col_sh))
    else:
        cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(fx - 40 + dirx * 20, fy - 26, fx + 40 + dirx * 46, fy + 30), 26, 26)), paint(col))
        cv.drawRect(skia.Rect(fx - 40 + dirx * 20, fy + 14, fx + 40 + dirx * 46, fy + 30), paint(col_sh))


def _item(cv, P, hx, hy, ang):
    it = P['item']
    if it == 'flashlight':
        a = math.radians(ang)
        cv.save(); cv.translate(hx, hy); cv.rotate(-math.degrees(a))
        cv.drawRect(skia.Rect(-14, -10, 14, 110), paint('#2B2B30'))
        cv.drawRect(skia.Rect(-20, 100, 20, 128), paint('#45464E'))
        cv.drawRect(skia.Rect(-16, 124, 16, 132), paint('#FFF6D8'))
        cv.restore()
    elif it == 'pen':
        cv.drawLine(hx - 6, hy + 10, hx + 30, hy - 60, paint('#D8302A', style='stroke', width=12))
    elif it == 'keys':
        cv.drawCircle(hx, hy + 30, 18, paint('#C9A45C', style='stroke', width=6))
        for k in range(3):
            cv.drawLine(hx - 10 + k * 10, hy + 46, hx - 14 + k * 12, hy + 92, paint('#D9C27A', style='stroke', width=9))


def _hand_pos(cv, x, y):
    m = cv.getTotalMatrix()
    return m.mapXY(x, y)


def mascot(cv, x, y, s=1.0, **pose):
    """Draw a puppet with feet at (x, y). s = scale (1.0 ~ 1150 px tall). Returns {'hand_r': (x, y)} in canvas px."""
    P = dict(DEFAULT_POSE)
    P.update(pose)
    if P['view'] == 'side':
        return _side(cv, x, y, s, P)
    out = {}
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    ls = P['light_side']
    back = P['view'] == 'back'
    ph = P['walk']
    cr = P['crouch']
    drop = cr * 300
    cv.translate(0, drop)
    bw = P['belly']
    # ---------------- legs (front/back: the stepping leg lifts and shortens; no sideways kicks)
    if P.get('legs', True) and cr < 0.5:
        for side in (-1, 1):
            hx = side * 48 * bw
            lift = 0.0
            if ph is not None:
                q = math.sin(2 * math.pi * (ph + (0.5 if side > 0 else 0)))
                lift = max(0.0, q) * (1.5 if P['run'] else 1.0)
            fy = HIP_Y + LEG_L1 + LEG_L2 - lift * 95 - drop
            fx = hx + side * 4
            kx, ky = hx + side * (10 + lift * 22), HIP_Y + (fy - HIP_Y) * 0.5
            col = P['pants'] if side == ls else P['pants_sh']
            if P.get('shorts'):
                _seg(cv, [(kx, ky), (fx, fy)], P['skin'] if side == ls else P['skin_sh'], 64)
                _seg(cv, [(hx, HIP_Y), (kx, ky + 20)], col, 104)
            else:
                _seg(cv, [(hx, HIP_Y), (kx, ky), (fx, fy)], col, 92)
            _shoe(cv, fx, fy, P['shoe'] if side == ls else P['shoe_sh'], '#B9BCC4' if P['shoe'] == SHOE else P['shoe_sh'])
    # ---------------- torso
    lean = P['body_lean']
    cv.save()
    cv.rotate(lean, 0, HIP_Y)
    tw = 112 * bw
    torso = blob([(-tw, SH_Y + 10), (0, SH_Y - 14), (tw, SH_Y + 10), (tw + 16, SH_Y + 160), (tw + 8, HIP_Y + 20), (0, HIP_Y + 34),
                  (-tw - 8, HIP_Y + 20), (-tw - 16, SH_Y + 160)])
    cv.drawPath(torso, paint(P['shirt']))
    cv.save()
    cv.clipPath(torso, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(-400 if ls > 0 else 30, SH_Y - 40, -30 if ls > 0 else 400, HIP_Y + 60), paint(P['shirt_sh']))
    if P['rim_a'] > 0:
        cv.clipRect(skia.Rect(-400, -2000, -60, 2000) if ls > 0 else skia.Rect(60, -2000, 400, 2000))
        cv.drawPath(torso, paint(C(P['rim'], P['rim_a']), style='stroke', width=12, blur=3))
    cv.restore()
    if P.get('number') is not None:
        f = skia.Font(_TF, 170)
        txt = str(P['number'])
        cv.drawString(txt, -f.measureText(txt) / 2, SH_Y + 260, f, paint(P.get('number_col', '#FFFFFF')))
    if not back:
        cv.drawPath(blob([(-46, SH_Y - 6), (0, SH_Y + 30), (46, SH_Y - 6), (0, SH_Y + 8)]), paint(P['skin_sh']))
    # crouched: knees pulled up in front of the body
    if cr >= 0.5 and P.get('legs', True):
        for side in (-1, 1):
            col = P['pants'] if side == ls else P['pants_sh']
            cv.drawOval(skia.Rect(side * 70 - 78, HIP_Y - 190, side * 70 + 78, HIP_Y + 10), paint(col))
            _shoe(cv, side * 74, HIP_Y + 60, P['shoe'] if side == ls else P['shoe_sh'], '#B9BCC4')
    # ---------------- arms: hang straight from the shoulders, swing a little when walking
    for side, (ang, bend), hand in ((-1, P['arm_l'], P['hand_l']), (1, P['arm_r'], P['hand_r'])):
        sx = side * (tw - 14)
        if ph is not None and ang < 20:
            ang = ang + 5 * math.sin(2 * math.pi * (ph + (0 if side > 0 else 0.5)))
        col = P['skin'] if side == ls else P['skin_sh']
        a1 = math.radians(ang) * side
        x1, y1 = sx + math.sin(a1) * 175, SH_Y + 40 + math.cos(a1) * 175
        a2 = a1 + math.radians(bend) * side
        x2, y2 = x1 + math.sin(a2) * 160, y1 + math.cos(a2) * 160
        _seg(cv, [(sx, SH_Y + 40), (x1, y1), (x2, y2)], col, 50)
        if not P.get('sleeveless'):
            _seg(cv, [(sx, SH_Y + 34), (sx + math.sin(a1) * 92, SH_Y + 40 + math.cos(a1) * 92)], P['shirt'] if side == ls else P['shirt_sh'], 80)
        cv.drawCircle(x2, y2, 32, paint(col))
        if side > 0:
            _item(cv, P, x2, y2, math.degrees(a2))
            out['hand_r'] = _hand_pos(cv, x2, y2)
    cv.restore()
    # ---------------- head
    cv.save()
    cv.translate(math.sin(math.radians(lean)) * 330, -900)
    cv.rotate(P['head_tilt'])
    if P.get('stretch'):
        cv.scale(1 - 0.25 * P['stretch'], 1 + P['stretch'])
    out['head'] = _hand_pos(cv, 0, 0)
    _head_front(cv, P, back)
    cv.restore()
    cv.restore()
    return out


def _head_front(cv, P, back):
    ls, turn = P['light_side'], P['head_turn']
    SK, SKS, HR, HRS = P['skin'], P['skin_sh'], P['hair'], P['hair_sh']
    if P.get('long_hair'):
        cv.drawPath(blob([(-200, -120), (0, -250), (200, -120), (230, 200), (180, 330), (0, 300), (-180, 330), (-230, 200)]), paint(HRS if not back else HR))
    cv.drawRect(skia.Rect(-38, 40, 38, 150), paint(SKS))
    head = blob([(-178, -40), (-150, -170), (0, -222), (150, -170), (178, -40), (160, 90), (90, 175), (0, 195), (-90, 175), (-160, 90)])
    cv.drawPath(head, paint(SK))
    cv.save()
    cv.clipPath(head, skia.ClipOp.kIntersect, True)
    cv.drawOval(skia.Rect(-430, -280, -115, 280) if ls > 0 else skia.Rect(115, -280, 430, 280), paint(SKS, blur=18))
    if P['rim_a'] > 0:
        cv.clipRect(skia.Rect(-400, -400, -70, 400) if ls > 0 else skia.Rect(70, -400, 400, 400))
        cv.drawPath(head, paint(C(P['rim'], P['rim_a']), style='stroke', width=14, blur=4))
    cv.restore()
    for side in (-1, 1):
        ex = side * 176 + turn * -30
        cv.drawOval(skia.Rect(ex - 30, -30, ex + 30, 60), paint(SK if side == ls else SKS))
    if back:
        if not P['bald']:
            hair = blob([(-190, -20), (-185, -150), (-90, -245), (40, -252), (160, -190), (192, -60), (185, 70), (120, 150), (0, 175), (-120, 150), (-185, 70)])
            cv.drawPath(hair, paint(HR))
            cv.drawPath(blob([(-60, -200), (30, -230), (100, -170), (20, -150)]), paint(HRS))
            if P.get('long_hair'):                                                    # long hair covers the whole back of the head
                cv.drawPath(blob([(-200, -120), (0, -250), (200, -120), (230, 200), (180, 330), (0, 300), (-180, 330), (-230, 200)]), paint(HR))
        _cap(cv, P, 0)
        return
    fx = turn * 60
    if not P['bald']:
        hair = blob([(-192, -10), (-186, -150), (-110, -240), (20, -256), (150, -205), (196, -90), (190, 0), (160, -70), (120, -120),
                     (60, -110), (10, -150), (-40, -105), (-110, -120), (-160, -70)])
        cv.drawPath(hair, paint(HR))
        cv.drawPath(blob([(-40, -230), (60, -235), (150, -190), (60, -175)]), paint(HRS))
    _cap(cv, P, fx)
    if P.get('faceless'):                                 # smooth skin where the face should be
        return
    lid = P['lids']
    for side in (-1, 1):
        ex, ey = fx + side * 72, -10
        if P.get('void_eyes'):                            # black, empty eyes with a pinprick of light
            cv.drawOval(skia.Rect(ex - 50, ey - 62, ex + 50, ey + 62), paint('#050505'))
            cv.drawCircle(ex + P['look'][0] * 14, ey, 7, paint('#F0F0F0'))
            continue
        cv.drawOval(skia.Rect(ex - 46, ey - 56, ex + 46, ey + 56), paint('#FFFFFF'))
        px, py = ex + P['look'][0] * 18, ey + P['look'][1] * 20
        cv.save()
        cv.clipPath(skia.Path.Oval(skia.Rect(ex - 46, ey - 56, ex + 46, ey + 56)), skia.ClipOp.kIntersect, True)
        k = P.get('pupil', 1.0)
        cv.drawCircle(px, py + 6, 34 * k, paint(P.get('iris', EYE_IRIS)))
        cv.drawCircle(px, py + 6, 20 * k, paint('#160C06'))
        cv.drawCircle(px + 11 * k, py - 6 * k, 9 * min(1, k + 0.2), paint('#FFFFFF'))
        if lid >= 0.95:                                  # closed: skin + a curved lash line, no white
            cv.restore()
            cv.drawOval(skia.Rect(ex - 48, ey - 58, ex + 48, ey + 58), paint(SK))
            q = skia.Path(); q.moveTo(ex - 40, ey + 4); q.quadTo(ex, ey + 26, ex + 40, ey + 4)
            cv.drawPath(q, paint(LINE, style='stroke', width=7))
            b = P['brow']
            cv.drawPath(poly([(ex - side * 30, ey - 82 - b * 26), (ex + side * 40, ey - 82 + b * 10)], closed=False), paint(HRS, style='stroke', width=17))
            continue
        if lid > 0:
            cv.drawRect(skia.Rect(ex - 50, ey - 60, ex + 50, ey - 60 + 116 * lid), paint(SK))
            cv.drawLine(ex - 50, ey - 60 + 116 * lid, ex + 50, ey - 60 + 116 * lid, paint(LINE, style='stroke', width=6))
        cv.restore()
        cv.drawOval(skia.Rect(ex - 46, ey - 56, ex + 46, ey + 56), paint(LINE, style='stroke', width=5))
        b = P['brow']
        inner, outer = ey - 82 - b * 26, ey - 82 + b * 10
        cv.drawPath(poly([(ex - side * 30, inner), (ex + side * 40, outer)], closed=False), paint(HRS, style='stroke', width=17))
    if P.get('glasses'):
        gp = paint(P['glasses'], style='stroke', width=12)
        for side in (-1, 1):
            ex = fx + side * 72
            cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect(ex - 62, -72, ex + 62, 52), 26, 26), gp)
        cv.drawLine(fx - 10, -20, fx + 10, -20, gp)
    if P.get('zombie'):
        for side in (-1, 1):
            ex = fx + side * 72
            cv.drawPath(skia.Path().addArc(skia.Rect(ex - 50, 10, ex + 50, 80), 20, 140), paint(C('#3A2A30', 0.8), style='stroke', width=10))
        cv.drawPath(blob([(fx + 30, 120), (fx + 44, 118), (fx + 40, 190), (fx + 32, 192)]), paint('#7A1E1E'))
    cv.drawPath(blob([(fx - 10, 52), (fx + 2, 40), (fx + 14, 54), (fx + 2, 64)]), paint(SKS))
    if P['mustache']:
        cv.drawPath(blob([(fx - 70, 92), (fx, 74), (fx + 70, 92), (fx + 40, 104), (fx, 94), (fx - 40, 104)]), paint(P['mustache']))
    _mouth(cv, P, fx, 112)
    if P.get('blush', 0) > 0:
        for side in (-1, 1):
            cv.drawOval(skia.Rect(fx + side * 112 - 34, 52, fx + side * 112 + 34, 80), paint(C('#E86A5A', P['blush']), blur=8))
    if P['sweat']:
        cv.drawPath(blob([(fx + 150, -80), (fx + 162, -40), (fx + 150, -26), (fx + 138, -40)]), paint('#BFE3FF'))


def _cap(cv, P, fx):
    if not P['cap']:
        return
    cv.drawPath(blob([(-185, -120), (-150, -220), (0, -262), (150, -220), (185, -120), (0, -140)]), paint(P['cap']))
    cv.drawPath(blob([(fx - 150, -128), (fx, -150), (fx + 150, -128), (fx + 120, -100), (fx, -112), (fx - 120, -100)]), paint('#151A24'))
    cv.drawCircle(fx, -190, 22, paint('#C9A45C'))


def _mouth(cv, P, fx, my):
    m, o = P['mouth'], P['mouth_open']
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
    elif m == 'wide':                                     # a smile that is far too wide
        q = skia.Path(); q.moveTo(fx - 150, my - 50); q.quadTo(fx, my + 90, fx + 150, my - 50); q.quadTo(fx, my + 20, fx - 150, my - 50)
        cv.drawPath(q, paint('#1A0808'))
        for k in range(12):
            tx = fx - 120 + k * 22
            cv.drawPath(poly([(tx, my - 10 + abs(k - 5.5) * -6), (tx + 9, my + 26 - abs(k - 5.5) * 4), (tx + 18, my - 10 + abs(k - 5.5) * -6)]), paint('#EDE6D6'))
        cv.drawPath(q, mp)
    elif m == 'grin':
        q = skia.Path(); q.moveTo(fx - 60, my - 10); q.quadTo(fx, my + 40, fx + 60, my - 10); q.close()
        cv.drawPath(q, paint('#FFFFFF')); cv.drawPath(q, mp)
    elif m == 'frown':
        q = skia.Path(); q.moveTo(fx - 40, my + 14); q.quadTo(fx, my - 12, fx + 40, my + 14)
        cv.drawPath(q, mp)
    else:
        cv.drawLine(fx - 30, my + 4, fx + 30, my + 4, mp)


def _side(cv, x, y, s, P):
    """Profile view, facing right (mirrored for face=-1). Proper walk/run cycle: legs swing, knees bend, arms counter-swing."""
    out = {}
    cv.save()
    cv.translate(x, y)
    cv.scale(s * P['face'], s)
    ph = P['walk']
    run = P['run']
    amp = 34 if run else 24
    bw = P['belly']
    lean = P['body_lean'] + (10 if run and ph is not None else 0)

    def leg(phase, near):
        if ph is None:
            th, kn = (4 if near else -4), 0
        else:
            q = math.sin(2 * math.pi * phase)
            th = amp * q                                   # + forward
            kn = max(0.0, math.cos(2 * math.pi * phase)) * (70 if run else 40)   # bend while swinging forward
        a = math.radians(th)
        kx, ky = math.sin(a) * LEG_L1, HIP_Y + math.cos(a) * LEG_L1
        b = a - math.radians(kn)
        fx, fy = kx + math.sin(b) * LEG_L2, ky + math.cos(b) * LEG_L2
        lift = 0 if ph is None else max(0.0, -HIP_Y - fy + 0) * 0
        col = P['pants'] if near else P['pants_sh']
        if P.get('shorts'):
            _seg(cv, [(kx, ky), (fx, fy)], P['skin'] if near else P['skin_sh'], 60)
            _seg(cv, [(0, HIP_Y), (kx, ky + 20)], col, 98)
        else:
            _seg(cv, [(0, HIP_Y), (kx, ky), (fx, fy)], col, 86)
        _shoe(cv, fx, fy, P['shoe'] if near else P['shoe_sh'], '#B9BCC4', dirx=1)

    def arm(phase, near):
        ang, bend = (P['arm_r'] if near else P['arm_l'])
        if ph is not None and ang < 30:
            ang = -(amp + 6) * math.sin(2 * math.pi * phase)
            bend = 25 + (20 if run else 0)
        a1 = math.radians(ang)                            # + forward
        sx, sy = 0, SH_Y + 40
        x1, y1 = sx + math.sin(a1) * 175, sy + math.cos(a1) * 175
        a2 = a1 + math.radians(bend)
        x2, y2 = x1 + math.sin(a2) * 160, y1 + math.cos(a2) * 160
        col = P['skin'] if near else P['skin_sh']
        if ang > 60:                                       # raised arm crosses the face: outline it so it reads
            _seg(cv, [(sx, sy), (x1, y1), (x2, y2)], LINE, 60)
            cv.drawCircle(x2, y2, 37, paint(LINE))
        _seg(cv, [(sx, sy), (x1, y1), (x2, y2)], col, 48)
        if not P.get('sleeveless'):
            _seg(cv, [(sx, sy - 6), (sx + math.sin(a1) * 90, sy + math.cos(a1) * 90)], P['shirt'] if near else P['shirt_sh'], 76)
        cv.drawCircle(x2, y2, 31, paint(col))
        if near:
            _item(cv, P, x2, y2, math.degrees(a2))
            out['hand_r'] = _hand_pos(cv, x2, y2)

    phn = 0 if ph is None else ph
    cv.save()
    cv.rotate(lean * 0.3, 0, HIP_Y)
    arm(phn + 0.5, False)
    leg(phn + 0.5, False)
    leg(phn, True)
    cv.restore()
    cv.save()
    cv.rotate(lean, 0, HIP_Y)
    torso = blob([(-70 * bw, SH_Y + 6), (10, SH_Y - 12), (80 * bw, SH_Y + 12), (92 * bw, SH_Y + 170), (84 * bw, HIP_Y + 20), (0, HIP_Y + 34),
                  (-80 * bw, HIP_Y + 20), (-84 * bw, SH_Y + 160)])
    cv.drawPath(torso, paint(P['shirt']))
    cv.save()
    cv.clipPath(torso, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(-200, SH_Y - 40, -20, HIP_Y + 60), paint(P['shirt_sh']))
    if P['rim_a'] > 0:
        cv.drawPath(torso, paint(C(P['rim'], P['rim_a']), style='stroke', width=12, blur=3))
    cv.restore()
    arm(phn, True)
    # head (profile)
    cv.save()
    cv.translate(26, -900)
    cv.rotate(P['head_tilt'])
    out['head'] = _hand_pos(cv, 0, 0)
    SK, SKS, HR, HRS = P['skin'], P['skin_sh'], P['hair'], P['hair_sh']
    cv.drawRect(skia.Rect(-40, 40, 30, 150), paint(SKS))
    head = blob([(-160, -40), (-140, -170), (0, -222), (130, -175), (172, -60), (190, 20), (168, 60), (150, 120), (80, 180), (-20, 192), (-120, 160), (-158, 80)])
    cv.drawPath(head, paint(SK))
    cv.save()
    cv.clipPath(head, skia.ClipOp.kIntersect, True)
    cv.drawOval(skia.Rect(-420, -280, -60, 280), paint(SKS, blur=18))
    cv.restore()
    cv.drawPath(blob([(176, 6), (214, 38), (186, 56), (168, 40)]), paint(SK))                     # nose
    cv.drawOval(skia.Rect(-70, -14, -24, 58), paint(SKS)); cv.drawArc(skia.Rect(-62, -2, -34, 44), 90, 180, False, paint(LINE, style='stroke', width=4))  # ear
    if not P['bald']:
        hair = blob([(-176, 40), (-190, -120), (-110, -240), (20, -258), (140, -210), (184, -120), (150, -110), (110, -150),
                     (40, -120), (-30, -140), (-60, -60), (-110, 10), (-140, 80)])
        cv.drawPath(hair, paint(HR))
        cv.drawPath(blob([(-60, -220), (40, -240), (120, -190), (30, -180)]), paint(HRS))
    _cap(cv, P, 30)
    ex, ey = 104, -14                                                                               # one eye
    cv.drawOval(skia.Rect(ex - 30, ey - 52, ex + 34, ey + 52), paint('#FFFFFF'))
    cv.save()
    cv.clipPath(skia.Path.Oval(skia.Rect(ex - 30, ey - 52, ex + 34, ey + 52)), skia.ClipOp.kIntersect, True)
    k = P.get('pupil', 1.0)
    px, py = ex + 8 + P['look'][0] * 10, ey + 6 + P['look'][1] * 18
    cv.drawCircle(px, py, 28 * k, paint(EYE_IRIS))
    cv.drawCircle(px, py, 16 * k, paint('#160C06'))
    cv.drawCircle(px + 8, py - 10, 7, paint('#FFFFFF'))
    if P['lids'] > 0:
        cv.drawRect(skia.Rect(ex - 34, ey - 56, ex + 38, ey - 56 + 108 * P['lids']), paint(SK))
    cv.restore()
    cv.drawOval(skia.Rect(ex - 30, ey - 52, ex + 34, ey + 52), paint(LINE, style='stroke', width=5))
    b = P['brow']
    cv.drawPath(poly([(ex - 30, ey - 70 + b * 8), (ex + 40, ey - 80 - b * 20)], closed=False), paint(HRS, style='stroke', width=16))
    if P['mustache']:
        cv.drawPath(blob([(110, 84), (176, 70), (196, 90), (140, 104)]), paint(P['mustache']))
    m, o = P['mouth'], P['mouth_open']
    if o > 0.05 or m in ('open', 'o'):
        oo = max(o, 0.6 if m in ('open', 'o') else 0)
        cv.drawOval(skia.Rect(118, 100 - 10 * oo, 168, 104 + 34 * oo), paint('#5B1F1A'))
    else:
        cv.drawLine(124, 108, 166, 104 + (8 if m == 'frown' else (-8 if m in ('smile', 'smirk') else 0)), paint(LINE, style='stroke', width=7))
    if P['sweat']:
        cv.drawPath(blob([(40, -90), (52, -50), (40, -36), (28, -50)]), paint('#BFE3FF'))
    cv.restore()
    if P['arm_r'][0] > 100 and ph is None:                # raised arm (shooting, waving): in front of the head
        arm(phn, True)
    cv.restore()
    cv.restore()
    return out


def monster(cv, x, y, s=1.0, look=(0.0, 0.0), head_tilt=20.0, arm=0.0, step=None, eye_glow=1.0, flashlight=True, jaw=0.0, rim='#9FC3FF'):
    """The thing in the hallway: 2.4 m, too thin, too many joints. Feet at (x, y); s=1 ~ 2300 px tall."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    body = '#0B0C0F'
    edge = C(rim, 0.35)
    lp = 0 if step is None else math.sin(2 * math.pi * step)
    for side in (-1, 1):                                                         # legs: three joints each
        k = lp * side
        pts = [(side * 40, -1100), (side * (70 + 30 * k), -760), (side * (40 - 40 * k), -420), (side * (60 + 20 * k), -80), (side * 70, 0)]
        _seg(cv, pts, body, 44)
    cv.drawPath(blob([(-120, -1700), (0, -1760), (120, -1700), (80, -1300), (60, -1080), (0, -1050), (-60, -1080), (-80, -1300)]), paint(body))
    for r in range(6):                                                           # ribs
        yy = -1640 + r * 70
        cv.drawLine(-70 + r * 4, yy, 70 - r * 4, yy + 20, paint(C('#2A2E36', 0.9), style='stroke', width=6))
    for side in (-1, 1):                                                         # arms: hang to the knees
        sw = arm if side > 0 else 0
        pts = [(side * 110, -1700), (side * 170, -1380 + 60 * sw), (side * 150 + 140 * sw, -1040 - 200 * sw), (side * 190 + 160 * sw, -720 - 300 * sw)]
        _seg(cv, pts, body, 34)
        fx, fy = pts[-1]
        for f in range(4):
            cv.drawLine(fx, fy, fx + side * (f * 14 - 10), fy + 120 + f * 14, paint(body, style='stroke', width=10))
        if side > 0 and flashlight:
            out = _hand_pos(cv, fx, fy + 40)
            cv.save(); cv.translate(fx, fy + 40); cv.rotate(-30)
            cv.drawRect(skia.Rect(-16, -10, 16, 120), paint('#2B2B30'))
            cv.drawRect(skia.Rect(-22, 110, 22, 140), paint('#45464E'))
            cv.restore()
    # head: small, tilted too far
    cv.save()
    cv.translate(0, -1840)
    cv.rotate(head_tilt)
    cv.drawRect(skia.Rect(-26, 0, 26, 120), paint(body))
    head = blob([(-110, -40), (-80, -170), (0, -200), (80, -170), (110, -40), (70, 80), (0, 110), (-70, 80)])
    cv.drawPath(head, paint(body))
    cv.drawPath(head, paint(edge, style='stroke', width=8, blur=4))
    if jaw > 0:
        cv.drawPath(blob([(-60, 40), (0, 30), (60, 40), (40, 40 + 160 * jaw), (0, 50 + 190 * jaw), (-40, 40 + 160 * jaw)]), paint('#000000'))
        for t in range(6):
            tx = -48 + t * 19
            cv.drawPath(poly([(tx, 40), (tx + 9, 70 + 40 * jaw), (tx + 18, 40)]), paint('#D9D6C8'))
    for side in (-1, 1):
        ex, ey = side * 46 + look[0] * 10, -70 + look[1] * 8
        if eye_glow > 0:
            glow(cv, _hand_pos(cv, ex, ey), 70 * s * 4, '#E9F2FF', 0.35 * eye_glow) if False else None
            cv.drawCircle(ex, ey, 60, paint(C('#E9F2FF', 0.25 * eye_glow), blur=20))
        cv.drawOval(skia.Rect(ex - 22, ey - 16, ex + 22, ey + 16), paint(C('#F4F8FF', eye_glow)))
        cv.drawCircle(ex + look[0] * 6, ey, 6, paint('#000000'))
    cv.restore()
    cv.restore()


def kessrah(cv, x, y, s=1.0, open_=0.0, t=0.0, tilt=0.0, reach=0.0):
    """Kessrah, the One Behind the Eyelids: tall, black, too-long fingers; a pale face made of closed eyelids that open (red irises).
    Feet at (x, y); s=1 ~ 2400 px tall. open_: 0 all lids closed .. 1 all open."""
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    body = '#060607'
    for side in (-1, 1):
        cv.drawPath(poly([(side * 50, -1150), (side * 80, -600), (side * 60, 0)], closed=False), paint(body, style='stroke', width=50))
    cv.drawPath(blob([(-150, -1900), (0, -1960), (150, -1900), (110, -1500), (80, -1150), (0, -1120), (-80, -1150), (-110, -1500)]), paint(body))
    for side in (-1, 1):
        r = reach if side > 0 else 0.0
        pts = [(side * 140, -1880), (side * 230 + r * 200, -1500 - r * 250), (side * 260 + r * 420, -1100 - r * 450)]
        cv.drawPath(poly(pts, closed=False), paint(body, style='stroke', width=36))
        fx, fy = pts[-1]
        for f in range(5):
            cv.drawLine(fx, fy, fx + side * (f * 22 - 30) + r * 80, fy + 200 + f * 10 - r * 120, paint(body, style='stroke', width=11))
    cv.save(); cv.translate(0, -2120); cv.rotate(tilt)
    cv.drawRect(skia.Rect(-30, 0, 30, 180), paint(body))
    face = blob([(-150, -60), (-120, -220), (0, -260), (120, -220), (150, -60), (110, 140), (0, 200), (-110, 140)])
    cv.drawPath(face, paint('#D9D4CC'))
    cv.save(); cv.clipPath(face, skia.ClipOp.kIntersect, True)
    cv.drawOval(skia.Rect(-240, -300, -60, 300), paint(C('#A8A29A', 0.8), blur=30))
    k = 0
    for row in range(5):                                                       # dozens of eyelids
        n = 3 + (row % 2)
        for c in range(n):
            ex = -110 + c * (220 / max(1, n - 1)) + (row % 2) * 8
            ey = -200 + row * 80
            w_ = 40 - abs(row - 2) * 3
            o = max(0.0, min(1.0, open_ * 1.6 - (k % 7) * 0.08))
            if o > 0.05:
                cv.drawOval(skia.Rect(ex - w_, ey - 18 * o, ex + w_, ey + 18 * o), paint('#F2EEE6'))
                cv.drawCircle(ex, ey, 12 * o, paint('#B01212'))
                cv.drawCircle(ex, ey, 5 * o, paint('#050505'))
            q = skia.Path(); q.moveTo(ex - w_, ey); q.quadTo(ex, ey + 22 * (1 - o) - 18 * o, ex + w_, ey)
            cv.drawPath(q, paint('#3A2E2A', style='stroke', width=5))
            for l in range(4):
                lx = ex - w_ * 0.6 + l * w_ * 0.4
                cv.drawLine(lx, ey + 4, lx - 2, ey + 14, paint('#2A201C', style='stroke', width=3))
            k += 1
    cv.restore()
    cv.drawPath(face, paint(C('#8A8278', 0.6), style='stroke', width=6))
    cv.restore()
    cv.restore()


def mimic(cv, x, y, s=1.0, t=0.0, tilt=70.0, grin=1.0, reach=0.0, run=None, look=(0.0, 0.0), rim='#9FC3E0', rim_a=0.5):
    """The Mimic (VIDEO_016): something trying to look human and failing. 2.6 m, limbs too long, fingers too long, pale bloodied skin,
    neck bent sideways, a stretched human smile, small human eyes that stare at the viewer. Feet at (x, y); s=1 ~ 2600 px tall.
    run: phase 0..1 for a lurching gallop (leaning forward, arms reaching)."""
    skin, sh, blood = '#C9BFB2', '#9E9488', '#6A1414'
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    lean = 0.0 if run is None else 35.0
    cv.rotate(lean, 0, -1300)
    ph = 0.0 if run is None else math.sin(2 * math.pi * run)
    for side in (-1, 1):                                                       # legs: thin, jointed wrong
        k = ph * side
        pts = [(side * 60, -1300), (side * (110 + 60 * k), -800), (side * (40 - 70 * k), -380), (side * (90 + 40 * k), 0)]
        cv.drawPath(poly(pts, closed=False), paint(sh if side < 0 else skin, style='stroke', width=60))
    torso = blob([(-170, -2050), (0, -2110), (170, -2050), (120, -1650), (90, -1300), (0, -1270), (-90, -1300), (-120, -1650)])
    cv.drawPath(torso, paint(skin))
    cv.save(); cv.clipPath(torso, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(-300, -2200, -20, -1200), paint(sh))
    for r in range(5):
        cv.drawLine(-90, -1950 + r * 60, 90, -1930 + r * 60, paint(C('#8A8075', 0.8), style='stroke', width=7))
    for bx, by, br in ((40, -1800, 70), (-60, -1600, 50), (80, -1450, 40)):
        cv.drawPath(blob([(bx - br, by), (bx, by - br * 0.8), (bx + br, by - 10), (bx + 10, by + br * 1.6)]), paint(C(blood, 0.85)))
    cv.drawPath(torso, paint(C(rim, rim_a), style='stroke', width=12, blur=4))
    cv.restore()
    for side in (-1, 1):                                                       # arms to the knees, fingers like twigs
        r = reach if side > 0 else reach * 0.6
        sw = ph * side * 0.5
        pts = [(side * 160, -2030), (side * (230 + 260 * r), -1600 - 380 * r + 120 * sw), (side * (210 + 520 * r), -1050 - 650 * r + 200 * sw)]
        cv.drawPath(poly(pts, closed=False), paint(skin if side > 0 else sh, style='stroke', width=44))
        fx, fy = pts[-1]
        for f in range(5):
            a = math.radians(-40 + f * 20) + (0.6 * r * side)
            cv.drawLine(fx, fy, fx + math.sin(a) * 220 * side, fy + math.cos(a) * 220 - 150 * r, paint(skin, style='stroke', width=14))
        cv.drawCircle(fx, fy, 30, paint(C(blood, 0.7)))
    cv.save(); cv.translate(0, -2100); cv.rotate(tilt)                       # the neck bends too far; the head hangs sideways
    cv.drawRect(skia.Rect(-34, -330, 34, 0), paint(skin))
    cv.translate(0, -330)
    head = blob([(-150, -40), (-130, -190), (0, -230), (130, -190), (150, -40), (120, 110), (0, 160), (-120, 110)])
    cv.drawPath(head, paint(skin))
    cv.save(); cv.clipPath(head, skia.ClipOp.kIntersect, True)
    cv.drawOval(skia.Rect(-260, -260, -40, 260), paint(sh, blur=20))
    cv.drawPath(blob([(-130, -200), (-40, -240), (40, -180), (-60, -120)]), paint(C('#2A2420', 0.9)))     # patchy hair
    cv.restore()
    for side in (-1, 1):                                                       # small human eyes, too far apart, staring
        ex = side * 70
        cv.drawOval(skia.Rect(ex - 30, -70, ex + 30, -34), paint('#EEE8DE'))
        cv.drawCircle(ex + look[0] * 8, -52 + look[1] * 6, 9, paint('#0A0A0A'))
        cv.drawCircle(ex + look[0] * 8 + 3, -56, 3, paint('#FFFFFF'))
    w_ = 70 + 70 * grin                                                        # the stretched smile, cheek to cheek
    q = skia.Path(); q.moveTo(-w_, 30); q.quadTo(0, 30 + 90 * grin, w_, 30); q.quadTo(0, 50 + 40 * grin, -w_, 30)
    cv.drawPath(q, paint('#1A0808'))
    for k in range(12):
        tx = -w_ * 0.85 + k * (w_ * 1.7 / 11)
        cv.drawRect(skia.Rect(tx - 7, 34 + 8 * grin, tx + 7, 52 + 18 * grin), paint('#E4DCC8'))
    cv.drawPath(q, paint('#2A0A0A', style='stroke', width=6))
    cv.drawPath(blob([(w_ - 10, 40), (w_ + 10, 50), (w_, 140), (w_ - 14, 120)]), paint(C(blood, 0.9)))
    cv.drawPath(head, paint(C(rim, rim_a), style='stroke', width=10, blur=4))
    cv.restore()
    cv.restore()


def purser(cv, x, y, s=1.0, t=0.0, neck=0.0, mask=0.0, reach=0.0, head_turn=0.0, crawl=False, wrong=0.0, rim='#E8C890', rim_a=0.5,
           blood_=0.0):
    """The Purser (VIDEO_017): a flight attendant from far away. Up close: 2.4 m, navy uniform, pillbox hat, gold wings.
    Its face is a yellow oxygen mask with a smile painted on it; mask=1 lifts the mask off a round mouth of teeth (lamprey).
    neck 0..1 unfolds an accordion neck (like a jet bridge); arms fold out in three hinged slats like tray tables.
    wrong 0..1: knees bend backwards, shoes on backwards (heels forward). head_turn in degrees (180 = facing behind).
    crawl=True: drawn for a ceiling crawl (caller rotates the canvas 180). Feet at (x, y); s=1 ~ 2400 px tall."""
    navy, navy_sh, skin, sh, gold, blood = '#1E2A44', '#141C30', '#D8CFC6', '#ADA49A', '#D8B45A', '#6A1010'
    cv.save(); cv.translate(x, y); cv.scale(s, s)
    for side in (-1, 1):                                                       # legs, stockings; knees bend the wrong way
        kx = side * 70 + (90 * wrong) * (1 if not crawl else -1)
        pts = [(side * 60, -1150), (kx, -620), (side * 55, -60)]
        cv.drawPath(poly(pts, closed=False), paint(sh if side < 0 else skin, style='stroke', width=58))
        hx = -1 if wrong > 0.5 else 1                                          # shoes: toe forward, or heel forward
        cv.drawPath(blob([(side * 55 - 40 * hx, -70), (side * 55 + 90 * hx, -40), (side * 55 + 100 * hx, 0), (side * 55 - 50 * hx, 0)]), paint('#0E0E12'))
        cv.drawRect(skia.Rect(side * 55 - 50 * hx - 6, -40, side * 55 - 50 * hx + 6, 0), paint('#0E0E12'))
    skirt = blob([(-150, -1450), (150, -1450), (130, -1050), (-130, -1050)])
    cv.drawPath(skirt, paint(navy_sh))
    torso = blob([(-180, -2000), (0, -2050), (180, -2000), (150, -1650), (140, -1430), (0, -1410), (-140, -1430), (-150, -1650)])
    cv.drawPath(torso, paint(navy))
    cv.save(); cv.clipPath(torso, skia.ClipOp.kIntersect, True)
    cv.drawRect(skia.Rect(-300, -2100, -30, -1400), paint(navy_sh))
    cv.drawPath(poly([(-60, -2040), (0, -1840), (60, -2040)]), paint('#EDE6DA'))   # blouse V + scarf
    cv.drawPath(poly([(-40, -1990), (0, -1900), (40, -1990), (70, -1860), (0, -1880), (-70, -1860)]), paint('#9A1E24'))
    for k in range(3):
        cv.drawCircle(0, -1780 + k * 110, 12, paint(gold))
    cv.drawPath(poly([(70, -1820), (150, -1830), (110, -1800)]), paint(gold))  # wings pin
    cv.drawRect(skia.Rect(-150, -1840, -60, -1805), paint('#EDE6DA'))         # name tag
    if blood_ > 0:
        for bx, by, br in ((-60, -1700, 60), (40, -1560, 45), (-20, -1480, 35)):
            cv.drawPath(blob([(bx - br, by), (bx, by - br), (bx + br, by), (bx + 8, by + br * 1.8)]), paint(C(blood, 0.9 * blood_)))
    cv.drawPath(torso, paint(C(rim, rim_a), style='stroke', width=12, blur=4))
    cv.restore()
    for side in (-1, 1):                                                       # arms: three hinged slats, too long
        r = reach if side > 0 else reach * 0.7
        p0 = (side * 170, -1980)
        p1 = (side * (220 + 200 * r), -1650 - 300 * r)
        p2 = (side * (200 + 480 * r), -1300 - 560 * r)
        p3 = (side * (230 + 760 * r), -1050 - 760 * r)
        for a, b in ((p0, p1), (p1, p2), (p2, p3)):
            cv.drawPath(poly([a, b], closed=False), paint(navy if (a == p0) else (skin if side > 0 else sh), style='stroke', width=42))
            cv.drawCircle(b[0], b[1], 26, paint(sh))                           # hinges
        for f in range(4):
            ang = math.radians(-30 + f * 20) + 0.5 * r * side
            cv.drawLine(p3[0], p3[1], p3[0] + math.sin(ang) * 230 * side, p3[1] + math.cos(ang) * 230 - 160 * r, paint(skin, style='stroke', width=13))
    nl = 140 + 900 * neck                                                      # accordion neck
    cv.save(); cv.translate(0, -2040)
    for k in range(int(4 + 14 * neck)):
        yy = -k * nl / (4 + 14 * neck)
        w_ = 46 if k % 2 == 0 else 34
        cv.drawRect(skia.Rect(-w_, yy - nl / (4 + 14 * neck), w_, yy), paint(skin if k % 2 == 0 else sh))
    cv.translate(0, -nl)
    cv.rotate(head_turn * 0.15 + 6 * math.sin(t * 1.3))
    head = blob([(-140, -30), (-120, -200), (0, -250), (120, -200), (140, -30), (100, 110), (0, 150), (-100, 110)])
    cv.drawPath(head, paint(skin))
    cv.drawPath(blob([(-150, -120), (-110, -270), (0, -300), (110, -270), (150, -120), (90, -170), (0, -190), (-90, -170)]), paint('#1A1410'))
    cv.drawRect(skia.Rect(-90, -330, 90, -250), paint(navy)); cv.drawRect(skia.Rect(-90, -275, 90, -258), paint(gold))   # pillbox hat
    if abs(head_turn) > 120:                                                   # facing behind: only hair, but the mask is on the back
        cv.drawPath(head, paint('#1A1410'))
    my = -60 - 260 * mask                                                      # the mouth under the mask: a ring of teeth
    cv.drawCircle(0, 0, 92, paint('#1A0606'))
    for k in range(18):
        a = 2 * math.pi * k / 18
        cv.drawPath(poly([(math.cos(a) * 92, math.sin(a) * 92), (math.cos(a + 0.12) * 92, math.sin(a + 0.12) * 92), (math.cos(a + 0.06) * 50, math.sin(a + 0.06) * 50)]), paint('#E8E0CC'))
    cv.drawCircle(0, 0, 40, paint('#000000'))
    if blood_ > 0:
        cv.drawPath(blob([(-60, 70), (60, 70), (30, 200), (-20, 230)]), paint(C(blood, blood_)))
    cv.save(); cv.translate(0, my * (1 if mask > 0 else 0) + (0 if mask > 0 else -60)); cv.rotate(-25 * mask)
    cup = blob([(-120, -40), (-100, -110), (0, -130), (100, -110), (120, -40), (90, 110), (0, 140), (-90, 110)])
    cv.drawPath(cup, paint('#E6C23A'))
    cv.drawPath(cup, paint('#B8961E', style='stroke', width=8))
    for side in (-1, 1):                                                       # painted-on eyes and lashes
        cv.drawCircle(side * 50, -40, 14, paint('#1A1410'))
        for l_ in range(3):
            cv.drawLine(side * 50, -54, side * (50 + 10 + l_ * 8), -74 - l_ * 4, paint('#1A1410', style='stroke', width=4))
    q = skia.Path(); q.moveTo(-60, 40); q.quadTo(0, 95, 60, 40)
    cv.drawPath(q, paint('#B01E2A', style='stroke', width=12))               # painted smile
    cv.drawLine(0, 140, 40 * math.sin(t * 2), 420, paint('#D8D0C0', style='stroke', width=6))   # the dangling tube
    cv.restore()
    cv.drawPath(head, paint(C(rim, rim_a), style='stroke', width=10, blur=4))
    cv.restore()
    cv.restore()
