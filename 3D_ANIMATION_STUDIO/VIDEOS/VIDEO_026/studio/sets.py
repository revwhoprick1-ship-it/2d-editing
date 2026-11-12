"""VIDEO_026 sets + inserts (2dEDIT flat vector paintings). ONE fixed layout per place, 1-point perspective, VP = (540, 920).

Speed: every static set is painted ONCE per process into an overscanned plate (cached image); per frame the renderer only
crops/zooms it and draws what moves (light, rain, puppets). Blurred plates are cached too.

The 3 hidden lore details live here:  #1 the wall clock above the hallway arch is stuck at 11:47 (X=310, Y=580);
#2 (drawn by the renderer) the mascot has a heavy shadow on the couch, the copy has none;  #3 the framed photo on the side
table: Justin, Lawrence, You, Ken ... and Bob scratched out of the glass.
"""
import math
import os
import sys

import numpy as np
import skia

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from puppets import INKC, K, SKIN_M, C, H, W, blob, lin, paint, poly, stroke  # noqa: E402
from kit import Cam, quad, text  # noqa: E402

VPX, VPY = 540, 920
MARGIN = 120
LIN = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
WALL_T, WALL_B = '#22254E', '#2B2E62'
COUCH, COUCH_D, COUCH_L = '#4F5C8C', '#394570', '#6B79AA'
R = skia.Rect.MakeLTRB


def rr(cv, l, t, r, b, rad, col, ink=0.0):
    cv.drawRoundRect(R(l, t, r, b), rad, rad, paint(col))
    if ink:
        cv.drawRoundRect(R(l, t, r, b), rad, rad, stroke(INKC, ink))


def fill(cv, path, col, ink=0.0):
    cv.drawPath(path, paint(col))
    if ink:
        cv.drawPath(path, stroke(INKC, ink))


def hatch(cv, box, n, seed, ang=-58, ln=(14, 34), col=INKC, a=0.26, w=2.2):
    rng = np.random.default_rng(seed)
    dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for _ in range(n):
        x, y, L = rng.uniform(box[0], box[2]), rng.uniform(box[1], box[3]), rng.uniform(*ln)
        cv.drawLine(x, y, x + dx * L, y + dy * L, stroke(col, w, a))


# ----------------------------------------------------------------------------------------------- shared props
def clock_1147(cv, cx, cy, s=1.0):
    """Hidden detail #1: the digital wall clock, stuck at 11:47."""
    rr(cv, cx - 75 * s, cy - 29 * s, cx + 75 * s, cy + 29 * s, 10 * s, '#07070D', 4 * s)
    cv.drawRoundRect(R(cx - 75 * s, cy - 29 * s, cx + 75 * s, cy + 29 * s), 10 * s, 10 * s, stroke('#3C4070', 3 * s))
    text(cv, '11:47', cx, cy + 16 * s, 46 * s, '#FF3B30', blur=5 * s, alpha=0.7)
    text(cv, '11:47', cx, cy + 16 * s, 46 * s, '#FF5A4E')


def arch(cv, l, r, top, bottom, glow=0.5):
    rad = (r - l) / 2
    p = skia.Path()
    p.moveTo(l, bottom); p.lineTo(l, top + rad); p.arcTo(R(l, top, r, top + 2 * rad), 180, 180, False); p.lineTo(r, bottom); p.close()
    cv.save(); cv.clipPath(p, K, True)
    cv.drawPaint(paint('#090A18'))
    k = 0.4                                                                    # the hallway recedes to the vanishing point
    fx = lambda x: VPX + (x - VPX) * k  # noqa: E731
    fy = lambda y: VPY + (y - VPY) * k  # noqa: E731
    cv.drawPath(poly([(l, bottom), (r, bottom), (fx(r), fy(bottom)), (fx(l), fy(bottom))]), paint('#15142A'))
    cv.drawPath(poly([(l, top), (fx(l), fy(top)), (fx(l), fy(bottom)), (l, bottom)]), paint('#0F1024'))
    cv.drawRect(R(fx(l), fy(top), fx(r), fy(bottom)), paint('#101226'))
    cv.drawRect(R(fx(l) + 14, fy(top) + 40, fx(r) - 14, fy(top) + 120), paint(C('#9FB6D8', glow), blur=10))   # porch light through the door glass
    cv.restore()
    cv.drawPath(p, stroke('#454B8A', 13)); cv.drawPath(p, stroke(INKC, 4))
    return p


def window(cv, l, t, r, b, seed=3):
    cv.drawLine(l - 42, t - 28, r + 42, t - 28, stroke('#12122A', 9))
    cv.drawRect(R(l, t, r, b), paint('#000000', shader=lin((0, t), (0, b), [C('#0B1030'), C('#18214A')])))
    rng = np.random.default_rng(seed)
    for _ in range(5):                                                         # far windows of other houses
        x, y = rng.uniform(l + 20, r - 30), rng.uniform(t + (b - t) * 0.55, b - 30)
        cv.drawRect(R(x, y, x + 12, y + 16), paint(C('#E8B870', 0.55)))
    cv.drawCircle(r - 50, t + (b - t) * 0.3, 90, paint('#000000', shader=skia.GradientShader.MakeRadial((r - 50, t + (b - t) * 0.3), 90,
                                                                                                        [C('#9FB4FF', 0.35).toColor(), C('#9FB4FF', 0.0).toColor()])))
    cv.drawLine((l + r) / 2, t, (l + r) / 2, b, stroke('#3F4478', 10)); cv.drawLine(l, t + (b - t) * 0.5, r, t + (b - t) * 0.5, stroke('#3F4478', 10))
    cv.drawRect(R(l, t, r, b), stroke('#3F4478', 14)); cv.drawRect(R(l - 7, t - 7, r + 7, b + 7), stroke(INKC, 4))
    rr(cv, l - 16, b, r + 16, b + 20, 4, '#474C86', 3)
    for sd, x0 in ((-1, l - 30), (1, r + 30)):                                  # curtains
        d = poly([(x0 - 32, t - 26), (x0 + 32, t - 26), (x0 + 22 * sd + 6, t + (b - t) * 0.4), (x0 + 36, b + 14), (x0 - 36, b + 18), (x0 - 26 * sd - 6, t + (b - t) * 0.6)])
        fill(cv, d, '#2F3266', 4)
        for k in (-14, 4, 20):
            cv.drawLine(x0 + k, t - 10, x0 + k + 5 * sd, b, stroke('#22244E', 3, 0.8))


def bookshelf(cv, l, t, r, b, seed=5):
    rr(cv, l, t, r, b, 4, '#17172F', 4)
    rng = np.random.default_rng(seed)
    n = max(3, int((b - t) / 135))
    cols = ['#6B4A5A', '#3F5B7A', '#7A6A45', '#4A6A5A', '#5A4A7A', '#8A8296', '#7A4A3A']
    for i in range(n):
        y1 = t + (i + 1) * (b - t) / n
        cv.drawLine(l, y1, r, y1, stroke(INKC, 5)); cv.drawLine(l, y1 - 4, r, y1 - 4, stroke('#2A2A50', 3))
        x = l + 8
        if i == 1:                                                             # a small framed picture + a box, like the reference
            rr(cv, l + 12, y1 - 74, l + 66, y1 - 6, 3, '#2B2440', 3); cv.drawRect(R(l + 20, y1 - 66, l + 58, y1 - 14), paint('#56607A'))
            x = l + 80
        while x < r - 16:
            w_, h_ = rng.uniform(13, 26), rng.uniform(62, 104) * min(1.0, (b - t) / n / 130)
            lean = rng.uniform(-1, 1) > 0.86
            cv.save()
            if lean:
                cv.rotate(-12, x, y1 - 6)
            cv.drawRect(R(x, y1 - 6 - h_, x + w_, y1 - 6), paint(cols[int(rng.integers(0, len(cols)))]))
            cv.drawRect(R(x, y1 - 6 - h_, x + w_, y1 - 6), stroke(INKC, 2))
            cv.restore()
            x += w_ + rng.uniform(1, 5)


def friends_photo(cv, l, t, r, b, tilt=0.0):
    """Hidden detail #3: Justin, Lawrence, You, Ken ... and Bob, scratched out of the glass."""
    w_, h_ = r - l, b - t
    cv.save(); cv.rotate(tilt, (l + r) / 2, b)
    rr(cv, l, t, r, b, w_ * 0.04, '#2E2536', max(2.0, w_ * 0.03))
    rr(cv, l + w_ * 0.08, t + h_ * 0.08, r - w_ * 0.08, b - h_ * 0.08, 2, '#A9A4BA')
    pl, pt, pr, pb = l + w_ * 0.13, t + h_ * 0.13, r - w_ * 0.13, b - h_ * 0.13
    cv.save(); cv.clipRect(R(pl, pt, pr, pb))
    cv.drawRect(R(pl, pt, pr, pb), paint('#000000', shader=lin((0, pt), (0, pb), [C('#5B6A8A'), C('#3F4A66')])))
    people = [(0.12, '#E8B892', '#4A3A30', '#8E8E9A', 1.2), (0.31, '#8A5A44', '#1E1612', '#6A4A9A', 1.0), (0.5, '#F2C29B', '#6B3E1F', '#F07A1A', 1.0),
              (0.69, '#F2C8A0', '#D8C070', '#B8463A', 1.0), (0.88, '#E8B892', '#2A1E16', '#2F8A86', 1.0)]
    hw = (pr - pl) * 0.085
    for i, (fx, skin, hair, shirt, k) in enumerate(people):
        x, y = pl + (pr - pl) * fx, pt + (pb - pt) * (0.5 - 0.06 * (k - 1))
        cv.drawRoundRect(R(x - hw * 1.5 * k, y + hw * 0.8, x + hw * 1.5 * k, pb + 10), hw * 0.6, hw * 0.6, paint(shirt))
        cv.drawCircle(x, y, hw * k, paint(skin))
        cv.drawArc(R(x - hw * k, y - hw * k, x + hw * k, y + hw * k), 180, 180, True, paint(hair))
        if i < 4:
            cv.drawLine(x - hw * 0.4, y + hw * 0.45, x + hw * 0.4, y + hw * 0.45, stroke('#3A2420', max(1.2, hw * 0.14)))
    cv.restore()
    bx, by = pl + (pr - pl) * 0.88, pt + (pb - pt) * 0.5                       # Bob: gouged out of the glass
    rng = np.random.default_rng(47)
    for k in range(11):
        a = rng.uniform(0, math.pi)
        L = hw * rng.uniform(1.2, 2.0)
        x0, y0 = bx + rng.uniform(-hw * 0.5, hw * 0.5), by + rng.uniform(-hw * 0.5, hw * 0.5)
        cv.drawLine(x0 - math.cos(a) * L, y0 - math.sin(a) * L, x0 + math.cos(a) * L, y0 + math.sin(a) * L, stroke('#F4F2F8', max(1.5, hw * 0.16), 0.92))
    for k in range(4):
        a = rng.uniform(0, math.pi)
        cv.drawLine(bx - math.cos(a) * hw * 1.6, by - math.sin(a) * hw * 1.6, bx + math.cos(a) * hw * 1.6, by + math.sin(a) * hw * 1.6, stroke('#17131F', max(1.0, hw * 0.09), 0.9))
    cv.restore()


def cam_dome(cv, x, y, s=1.0):
    rr(cv, x - 14 * s, y - 16 * s, x + 14 * s, y - 6 * s, 3, '#8E90A8', 2)
    cv.drawArc(R(x - 18 * s, y - 24 * s, x + 18 * s, y + 12 * s), 0, 180, True, paint('#C9CCE0'))
    cv.drawArc(R(x - 18 * s, y - 24 * s, x + 18 * s, y + 12 * s), 0, 180, True, stroke(INKC, 2.5))
    cv.drawCircle(x, y + 2 * s, 6 * s, paint('#14141E'))


def couch_front(cv, l=150, r=880, back_top=1078, seat_y=1338, front_y=1452, base_y=1556, floor_y=1668):
    """The loveseat seen from the TV: two back cushions, two seat cushions, armrests."""
    mid = (l + r) / 2
    cv.drawOval(R(l - 90, floor_y - 30, r + 90, floor_y + 34), paint(C('#000000', 0.5), blur=14))
    rr(cv, l - 10, back_top + 16, r + 10, base_y + 60, 30, COUCH_D, 4)
    for x0, x1 in ((l, mid), (mid, r)):                                        # back cushions
        rr(cv, x0 + 6, back_top, x1 - 6, seat_y + 12, 36, COUCH, 4)
        cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(R(x0 + 6, back_top, x1 - 6, seat_y + 12), 36, 36), True)
        cv.drawRect(R(x0, back_top, x1, back_top + 46), paint('#000000', shader=lin((0, back_top), (0, back_top + 46), [C(COUCH_L, 0.9), C(COUCH_L, 0.0)])))
        cv.restore()
        hatch(cv, (x0 + 40, back_top + 70, x1 - 40, seat_y - 30), 16, int(x0), a=0.22)
    for sd, x0 in ((-1, l - 62), (1, r - 58)):                                  # armrests
        rr(cv, x0, back_top + 72, x0 + 120, base_y + 30, 44, COUCH_D, 4)
        cv.drawOval(R(x0 + 10, back_top + 76, x0 + 110, back_top + 118), paint(C(COUCH_L, 0.55)))
    for x0, x1 in ((l, mid), (mid, r)):                                        # seat cushions: top + front face
        fill(cv, poly([(x0 + 8, seat_y), (x1 - 8, seat_y), (x1 + 2, front_y), (x0 - 2, front_y)]), COUCH_L, 4)
        rr(cv, x0 - 2, front_y - 6, x1 + 2, base_y, 22, COUCH, 4)
        hatch(cv, (x0 + 30, front_y + 16, x1 - 30, base_y - 20), 9, int(x1), a=0.2)
    rr(cv, l - 12, base_y - 4, r + 12, base_y + 84, 10, COUCH_D, 4)
    for x0 in (l + 12, r - 48):
        cv.drawRect(R(x0, base_y + 84, x0 + 36, floor_y), paint('#1A1626'))


# ----------------------------------------------------------------------------------------------- SET V1: living room from the TV
def living_static(cv):
    cv.drawPaint(paint('#121327'))
    fill(cv, poly([(-200, -300), (1280, -300), (1280, -148), (970, 300), (110, 300), (-200, -148)]), '#16173A')         # ceiling
    fill(cv, poly([(-200, -148), (110, 300), (110, 1250), (-200, 1487)]), '#1D1F47')                                 # left wall
    fill(cv, poly([(1280, -148), (970, 300), (970, 1250), (1280, 1487)]), '#1A1C41')                                 # right wall
    cv.drawRect(R(110, 300, 970, 1250), paint('#000000', shader=lin((0, 300), (0, 1250), [C(WALL_T), C(WALL_B)])))
    fill(cv, poly([(110, 1250), (970, 1250), (1280, 1487), (1280, 2100), (-200, 2100), (-200, 1487)]), '#231C33')    # floor
    cv.save(); cv.clipPath(poly([(110, 1250), (970, 1250), (1280, 1487), (1280, 2100), (-200, 2100), (-200, 1487)]), K, True)
    for i in range(-4, 16):                                                    # floor boards run to the vanishing point
        x = 110 + i * 86
        cv.drawLine(x, 1250, VPX + (x - VPX) * 3.6, VPY + (1250 - VPY) * 3.6, stroke('#17122A', 3, 0.8))
    cv.restore()
    cv.drawRect(R(110, 1010, 970, 1250), paint(C('#1C1E48', 0.55))); cv.drawLine(110, 1010, 970, 1010, stroke('#3A3E78', 5))
    for a, b in (((110, 300), (-200, -148)), ((970, 300), (1280, -148)), ((110, 1250), (-200, 1487)), ((970, 1250), (1280, 1487)),
                 ((110, 300), (110, 1250)), ((970, 300), (970, 1250)), ((110, 300), (970, 300)), ((110, 1250), (970, 1250))):
        cv.drawLine(*a, *b, stroke(INKC, 4))
    hatch(cv, (120, 310, 960, 420), 60, 1, a=0.2); hatch(cv, (120, 310, 200, 1000), 30, 2, a=0.2); hatch(cv, (880, 900, 960, 1240), 24, 3, a=0.2)
    arch(cv, 200, 420, 640, 1250)
    clock_1147(cv, 310, 580)
    bookshelf(cv, 440, 470, 620, 1250)
    window(cv, 690, 440, 910, 890)
    cv.drawOval(R(454, 162, 626, 210), paint('#2A2C55')); cv.drawOval(R(454, 162, 626, 210), stroke(INKC, 4))             # ceiling lamp (off)
    cv.drawArc(R(470, 150, 610, 250), 0, 180, True, paint('#3A3C6A')); cv.drawArc(R(470, 150, 610, 250), 0, 180, True, stroke(INKC, 4))
    cam_dome(cv, 938, 326)
    rr(cv, 90, 1600, 990, 1900, 60, '#3B2F4E', 4); cv.drawRoundRect(R(116, 1626, 964, 1874), 40, 40, stroke('#57466E', 6))  # rug
    # side table + lamp + the framed photo (right of the couch)
    cv.drawRect(R(994, 1190, 1010, 1640), paint('#2A2238'))
    cv.drawOval(R(936, 1168, 1068, 1202), paint('#3A2F4A')); cv.drawOval(R(936, 1168, 1068, 1202), stroke(INKC, 4))
    cv.drawRect(R(1034, 1096, 1042, 1180), paint('#17162A'))
    fill(cv, poly([(1010, 1010), (1066, 1010), (1084, 1098), (992, 1098)]), '#3E3A5E', 4)
    couch_front(cv)
    friends_photo(cv, 922, 1052, 1016, 1178, tilt=-4)                             # hidden detail #3 (in front of the lamp, beside Bob)
    cv.drawRect(R(-200, 1838, 1280, 2100), paint('#12101E')); cv.drawLine(-200, 1838, 1280, 1838, stroke('#2E2A44', 5))  # coffee table edge (foreground)
    rr(cv, 700, 1814, 838, 1840, 8, '#1C1A2A', 3)
    rr(cv, 214, 1766, 268, 1840, 8, C('#8FA6D8', 0.25), 3)


# ----------------------------------------------------------------------------------------------- SET V2: the right wall (behind Bob in profile)
def rightwall_static(cv):
    cv.drawPaint(paint('#000000', shader=lin((0, 0), (0, H), [C('#252851'), C('#1C1F45')])))
    cv.drawRect(R(-200, 1180, 1280, 2100), paint(C('#1A1C42', 0.9))); cv.drawLine(-200, 1180, 1280, 1180, stroke('#3A3E78', 6))
    hatch(cv, (-100, 60, 1180, 520), 70, 11, a=0.2); hatch(cv, (700, 520, 1180, 1160), 50, 12, a=0.2)
    rr(cv, 660, 380, 950, 760, 6, '#2B2440', 5)                                 # wall picture (a pale landscape)
    cv.drawRect(R(690, 410, 920, 730), paint('#000000', shader=lin((0, 410), (0, 730), [C('#56607A'), C('#3A4460')])))
    cv.drawPath(poly([(690, 730), (760, 610), (820, 680), (880, 590), (920, 730)]), paint('#2E3650'))
    cv.drawCircle(860, 480, 26, paint(C('#C8CCE0', 0.7)))
    rr(cv, 96, 1262, 600, 1298, 6, '#3A2F4A', 5)                                # side table
    for x in (130, 560):
        cv.drawRect(R(x - 12, 1298, x + 12, 2100), paint('#2A2238'))
    cv.drawRect(R(196, 1090, 214, 1262), paint('#17162A')); rr(cv, 160, 1240, 250, 1264, 6, '#17162A', 3)
    fill(cv, poly([(130, 880), (280, 880), (330, 1094), (80, 1094)]), '#3E3A5E', 5)                                   # lamp shade (off)
    friends_photo(cv, 330, 1010, 560, 1264, tilt=5)
    rr(cv, -240, 1200, 170, 2200, 80, COUCH, 5)                                 # couch back (behind his shoulders)
    hatch(cv, (-100, 1260, 140, 1900), 26, 14, a=0.22)
    rr(cv, 60, 1600, 1300, 2200, 90, COUCH_D, 5)                                # the armrest beyond him
    cv.drawOval(R(120, 1608, 1240, 1690), paint(C(COUCH_L, 0.35)))


# ----------------------------------------------------------------------------------------------- SET V4: the TV wall
TV_SCREEN = (140, 612, 940, 1062)                                               # 800 x 450: the feed is drawn 1:1 into it


def tvwall_static(cv):
    cv.drawPaint(paint('#000000', shader=lin((0, 0), (0, H), [C('#191A38'), C('#121229')])))
    hatch(cv, (-100, 40, 1180, 560), 80, 21, a=0.2)
    for x in (-40, 320, 680, 1040):
        cv.drawLine(x, -200, x, 1094, stroke('#101128', 4, 0.8))
    rr(cv, 40, 1094, 1040, 1340, 10, '#221C30', 5)                              # console
    for x in (373, 706):
        cv.drawLine(x, 1104, x, 1330, stroke(INKC, 4))
    rr(cv, 80, 1150, 330, 1300, 8, '#17131F', 3); rr(cv, 420, 1170, 660, 1290, 8, '#17131F', 3)
    cv.drawCircle(760, 1232, 5, paint('#3AD06A'))
    cv.drawRect(R(-200, 1340, 1280, 2100), paint('#17132A')); cv.drawLine(-200, 1340, 1280, 1340, stroke(INKC, 5))
    rr(cv, 470, 1072, 610, 1096, 4, '#0E0E18', 3)
    rr(cv, 118, 594, 962, 1080, 14, '#0B0B14', 5)                               # the 65-inch TV
    rr(cv, 300, 1102, 780, 1132, 10, '#15151F', 3)                              # soundbar
    fill(cv, poly([(930, 1094), (960, 930), (990, 1094)]), '#23402F', 3); fill(cv, poly([(948, 1094), (1004, 960), (1010, 1094)]), '#2B4A38', 3)
    rr(cv, 936, 1060, 1016, 1098, 8, '#3A2F4A', 3)


# ----------------------------------------------------------------------------------------------- SET V5: floor level, in front of the couch
GAP_T, GAP_B = 840, 1080                                                        # the dark gap under the couch


def floor_static(cv):
    cv.drawPaint(paint('#1A1528'))
    cv.drawRect(R(-200, GAP_B, 1280, 2100), paint('#000000', shader=lin((0, GAP_B), (0, 1920), [C('#2A2238'), C('#3A2E46')])))
    cv.save(); cv.clipRect(R(-200, GAP_B, 1280, 2100))
    for i in range(-10, 12):
        x = VPX + i * 210
        cv.drawLine(VPX + (x - VPX) * 0.16, GAP_B, VPX + (x - VPX) * 1.4, 2100, stroke('#17122A', 4, 0.9))
    cv.restore()
    rr(cv, -260, GAP_B + 60, 1340, 1560, 30, '#43354F', 4); cv.drawRoundRect(R(-230, GAP_B + 86, 1310, 1534), 20, 20, stroke('#5B4A6E', 7))   # rug
    cv.drawRect(R(-200, GAP_T, 1280, GAP_B), paint('#000000', shader=lin((0, GAP_T), (0, GAP_B), [C('#020206'), C('#0B0914')])))   # the gap
    for x in (70, 930):
        rr(cv, x, GAP_T - 6, x + 84, GAP_B + 8, 6, '#17131F', 4)                 # couch feet
    cv.drawRect(R(-200, 250, 1280, GAP_T), paint('#000000', shader=lin((0, 250), (0, GAP_T), [C(COUCH), C(COUCH_D)])))            # couch front
    hatch(cv, (-100, 300, 1180, 800), 60, 31, a=0.22)
    cv.drawLine(-200, GAP_T, 1280, GAP_T, stroke(INKC, 6)); cv.drawLine(-200, GAP_T - 26, 1280, GAP_T - 26, stroke(COUCH_L, 6, 0.7))
    cv.drawLine(540, 250, 540, GAP_T - 26, stroke(INKC, 5))
    rr(cv, -260, -200, 1340, 262, 60, COUCH_L, 5)                                # seat cushion edge
    cv.drawLine(540, -200, 540, 262, stroke(INKC, 5))


# ----------------------------------------------------------------------------------------------- SET V6: looking back over the couch
def pov_static(cv):
    cv.drawPaint(paint('#121327'))
    fill(cv, poly([(-200, -300), (1280, -300), (1280, 170), (-200, 170)]), '#15162E')                                 # ceiling
    cv.drawRect(R(-200, 170, 1280, 2100), paint('#000000', shader=lin((0, 170), (0, 1600), [C(WALL_T), C(WALL_B)])))
    cv.drawLine(-200, 170, 1280, 170, stroke(INKC, 5))
    hatch(cv, (-100, 190, 1180, 330), 50, 41, a=0.2); hatch(cv, (20, 330, 170, 1400), 30, 42, a=0.2)
    arch(cv, 170, 450, 650, 1700, glow=0.6)
    clock_1147(cv, 310, 580, 1.45)
    bookshelf(cv, 478, 300, 648, 1700, seed=9)
    window(cv, 730, 330, 1010, 1080, seed=4)
    cam_dome(cv, 1034, 196, 1.5)


def pov_backrest(cv, dy=0.0):
    """The couch backrest right in front of the lens (drawn per frame: it jerks when the hand tugs your ankle)."""
    rr(cv, -260, 1500 + dy, 1340, 2300 + dy, 90, COUCH_D, 6)
    cv.drawRoundRect(R(-240, 1506 + dy, 1320, 1580 + dy), 40, 40, paint(C(COUCH_L, 0.5)))
    cv.drawLine(540, 1510 + dy, 540, 2100 + dy, stroke(INKC, 6))
    hatch(cv, (-100, 1600 + dy, 1180, 1900 + dy), 30, 51, a=0.25)


PLATES = {'living': (living_static, 2.0), 'rightwall': (rightwall_static, 1.5), 'tvwall': (tvwall_static, 2.0), 'floor': (floor_static, 1.25),
          'pov': (pov_static, 2.0)}
_CACHE = {}


def plate(name, blur=0):
    key = (name, blur)
    if key not in _CACHE:
        fn, ps = PLATES[name]
        if blur == 0:
            srf = skia.Surface(int((W + 2 * MARGIN) * ps), int((H + 2 * MARGIN) * ps))
            cv = srf.getCanvas(); cv.scale(ps, ps); cv.translate(MARGIN, MARGIN)
            fn(cv)
            _CACHE[key] = srf.makeImageSnapshot().withDefaultMipmaps()
        else:                                                                   # blurred copy at low resolution: free at draw time
            base = plate(name)
            k = 4
            srf = skia.Surface(base.width() // k, base.height() // k)
            p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur * ps / k, blur * ps / k))
            srf.getCanvas().drawImageRect(base, R(0, 0, base.width() // k, base.height() // k), LIN, p)
            _CACHE[key] = srf.makeImageSnapshot()
    return _CACHE[key]


def draw_plate(cv, name, blur=0, alpha=1.0):
    cv.drawImageRect(plate(name, blur), R(-MARGIN, -MARGIN, W + MARGIN, H + MARGIN), LIN, skia.Paint(Alphaf=alpha))


def rain(cv, box, t, n=16, a=0.35):
    """Rain streaks on a window (world coords box)."""
    cv.save(); cv.clipRect(R(*box))
    rng = np.random.default_rng(8)
    w_, h_ = box[2] - box[0], box[3] - box[1]
    for k in range(n):
        x = box[0] + rng.uniform(0, w_)
        sp = rng.uniform(500, 900)
        y = box[1] + (rng.uniform(0, h_) + sp * t) % (h_ + 80) - 40
        cv.drawLine(x, y, x - 8, y + 44, stroke('#AEBBE8', 2.2, a * rng.uniform(0.5, 1)))
    cv.restore()


# ----------------------------------------------------------------------------------------------- the hallway (real dolly parallax)
def hallway(cv, cam, t, door_open=0.0, flash=0.0, hands=(0.0, 0.0), shudder=0.0, handle=0.0, sil=0.0, arch_frame=True, bob_door=0.0):
    """Looking down the hallway to the front door (frosted glass window). cam = kit.Cam (z along the hallway; the door wall at z=5)."""
    q = lambda pts: quad(cam, pts)  # noqa: E731
    Z = 5.0
    cv.drawPaint(paint('#0A0B18'))
    cv.drawPath(q([(-0.7, 2.5, 0), (0.7, 2.5, 0), (0.7, 2.5, Z), (-0.7, 2.5, Z)]), paint('#131430'))                 # ceiling
    cv.drawPath(q([(-0.7, 0, 0), (0.7, 0, 0), (0.7, 0, Z), (-0.7, 0, Z)]), paint('#1D1830'))                           # floor
    cv.drawPath(q([(-0.42, 0.002, 0.2), (0.42, 0.002, 0.2), (0.42, 0.002, Z - 0.3), (-0.42, 0.002, Z - 0.3)]), paint('#3A2A44'))   # runner
    cv.drawPath(q([(-0.31, 0.004, Z), (0.31, 0.004, Z), (0.6, 0.004, Z - 2.6), (-0.6, 0.004, Z - 2.6)]),
                paint('#000000', shader=lin(cam.p(0, 0, Z), cam.p(0, 0, Z - 2.6), [C('#AFC0F0', 0.30 + 0.5 * flash), C('#AFC0F0', 0.0)])))   # porch light through the glass
    for sd in (-1, 1):
        x = sd * 0.7
        cv.drawPath(q([(x, 0, 0), (x, 2.5, 0), (x, 2.5, Z), (x, 0, Z)]), paint('#000000', shader=lin(cam.p(x, 1.2, 0), cam.p(x, 1.2, Z), [C('#1A1C40'), C('#23264F')])))
        cv.drawPath(q([(x, 0, 0), (x, 0.12, 0), (x, 0.12, Z), (x, 0, Z)]), paint('#3A3E78'))
        cv.drawPath(q([(x, 0.95, 0), (x, 1.0, 0), (x, 1.0, Z), (x, 0.95, Z)]), paint('#30346A'))
        for z0 in (2.4, 3.5):                                                    # picture frames
            fill(cv, q([(x, 1.35, z0), (x, 1.85, z0), (x, 1.85, z0 + 0.45), (x, 1.35, z0 + 0.45)]), '#2B2440', 3)
            cv.drawPath(q([(x, 1.42, z0 + 0.06), (x, 1.78, z0 + 0.06), (x, 1.78, z0 + 0.39), (x, 1.42, z0 + 0.39)]), paint('#56607A' if z0 < 3 else '#6A5A6A'))
    # coat rack (left) + jacket, console table (right)
    cv.drawPath(q([(-0.7, 1.62, 1.2), (-0.7, 1.7, 1.2), (-0.7, 1.7, 2.1), (-0.7, 1.62, 2.1)]), paint('#17162A'))
    fill(cv, q([(-0.68, 0.75, 1.3), (-0.68, 1.66, 1.3), (-0.62, 1.66, 1.75), (-0.62, 0.7, 1.8)]), '#3F4A5A', 3)
    fill(cv, q([(-0.66, 0.8, 1.85), (-0.66, 1.66, 1.85), (-0.6, 1.66, 2.05), (-0.6, 0.86, 2.08)]), '#5A3A44', 3)
    fill(cv, q([(0.7, 0.78, 1.5), (0.7, 0.84, 1.5), (0.7, 0.84, 2.4), (0.7, 0.78, 2.4)]), '#3A2F4A', 3)
    fill(cv, q([(0.42, 0.84, 1.5), (0.7, 0.84, 1.5), (0.7, 0.84, 2.4), (0.42, 0.84, 2.4)]), '#463A58', 3)
    for z0 in (1.55, 2.35):
        cv.drawPath(q([(0.45, 0, z0), (0.45, 0.84, z0), (0.49, 0.84, z0), (0.49, 0, z0)]), paint('#2A2238'))
    for (sx, sz, col) in ((-0.5, 4.5, '#D8D8E0'), (-0.36, 4.62, '#C8463A')):       # shoes by the door
        fill(cv, q([(sx, 0, sz), (sx, 0.1, sz), (sx + 0.1, 0.1, sz + 0.26), (sx + 0.1, 0, sz + 0.26)]), col, 2)
    # door wall
    cv.drawPath(q([(-0.7, 0, Z), (0.7, 0, Z), (0.7, 2.5, Z), (-0.7, 2.5, Z)]), paint('#1B1D42'))
    sx = 0.006 * math.sin(t * 90) * shudder
    dl, dr = -0.46 + sx, 0.46 + sx
    fill(cv, q([(dl - 0.06, 0, Z), (dr + 0.06, 0, Z), (dr + 0.06, 2.13, Z), (dl - 0.06, 2.13, Z)]), '#3A3E72', 3)            # frame
    if door_open > 0.01:                                                        # kicked open: night + porch light flood in
        cv.drawPath(q([(dl, 0, Z), (dr, 0, Z), (dr, 2.05, Z), (dl, 2.05, Z)]), paint('#000000', shader=lin(cam.p(0, 2.05, Z), cam.p(0, 0, Z), [C('#9CB4E8'), C('#D8E4FF')])))
        a = math.radians(100 * door_open)                                       # the door leaf swings in on its left hinges
        ex, ez = dl + 0.92 * math.cos(a), Z - 0.92 * math.sin(a)
        fill(cv, q([(dl, 0, Z), (ex, 0, ez), (ex, 2.05, ez), (dl, 2.05, Z)]), '#2A2440', 3)
        spill = q([(dl, 0.003, Z), (dr, 0.003, Z), (0.62, 0.003, 0.4), (-0.3, 0.003, 0.4)])
        cv.drawPath(spill, paint(C('#BFD0FF', 0.42 * door_open)))
        if bob_door > 0:                                                        # the REAL Bob in the doorway: he has a long shadow
            shadow = q([(-0.2, 0.004, Z - 0.05), (0.24, 0.004, Z - 0.05), (0.34, 0.004, 1.2), (-0.02, 0.004, 1.2)])
            cv.drawPath(shadow, paint(C('#05050C', 0.8 * bob_door)))
            hx, hy = cam.p(0.02, 1.52, Z - 0.02)
            k = cam.f / max(cam.d(Z), 0.05)
            cv.drawOval(R(hx - 0.2 * k, hy - 0.2 * k, hx + 0.2 * k, hy + 0.2 * k), paint(C('#0B0B16', bob_door)))
            bx0, by0 = cam.p(-0.26, 1.34, Z - 0.02); bx1, by1 = cam.p(0.3, 0.0, Z - 0.02)
            cv.drawRoundRect(R(bx0, by0, bx1, by1), 0.1 * k, 0.1 * k, paint(C('#0B0B16', bob_door)))
            ax, ay = cam.p(0.3, 1.2, Z - 0.02); ex2, ey2 = cam.p(0.5, 1.5, Z - 0.02)
            cv.drawLine(ax, ay, ex2, ey2, stroke('#0B0B16', 0.1 * k, bob_door))                                       # his arm braced on the frame
            cv.drawOval(R(hx - 0.2 * k, hy - 0.2 * k, hx + 0.2 * k, hy + 0.2 * k), stroke('#58B5AC', 0.012 * k, 0.8 * bob_door))
    else:
        fill(cv, q([(dl, 0, Z), (dr, 0, Z), (dr, 2.05, Z), (dl, 2.05, Z)]), '#2A2440', 3)                              # door leaf
        fill(cv, q([(dl + 0.1, 0.12, Z), (dr - 0.1, 0.12, Z), (dr - 0.1, 0.9, Z), (dl + 0.1, 0.9, Z)]), '#231D36', 3)
        wl, wr, wb, wt = -0.31 + sx, 0.31 + sx, 1.05, 1.95
        g0, g1 = cam.p(wl, wt, Z), cam.p(wr, wb, Z)
        glass = R(g0[0], g0[1], g1[0], g1[1])
        cv.drawRect(glass, paint('#000000', shader=lin((g0[0], g0[1]), (g1[0], g1[1]), [C('#8FA2C8'), C('#4A5880')])))
        cv.save(); cv.clipRect(glass)
        gw, gh = g1[0] - g0[0], g1[1] - g0[1]
        cv.drawCircle(g1[0] - gw * 0.1, g0[1] + gh * 0.12, gw * 0.7, paint(C('#FFE2B0', 0.5), blur=gw * 0.14))        # porch light
        if sil > 0:                                                             # someone standing out there
            cv.drawOval(R(g0[0] + gw * 0.3, g0[1] + gh * 0.2, g0[0] + gw * 0.7, g0[1] + gh * 0.66), paint(C('#141426', 0.75 * sil), blur=gw * 0.035))
            cv.drawRoundRect(R(g0[0] + gw * 0.12, g0[1] + gh * 0.6, g0[0] + gw * 0.88, g1[1] + gh * 0.2), gw * 0.16, gw * 0.16,
                             paint(C('#141426', 0.75 * sil), blur=gw * 0.035))
        for k, (hx_, hy_, fl) in enumerate(((0.26, 0.6, 1), (0.74, 0.56, -1))):                                        # bloodied palms on the glass
            if hands[k] > 0:
                from puppets import palm_on_glass
                palm_on_glass(cv, g0[0] + gw * hx_, g0[1] + gh * hy_, gw / 620.0 * (0.9 + 0.1 * hands[k]), flip=fl, blood=hands[k], press=hands[k])
        if flash > 0:
            cv.drawRect(glass, paint(C('#FFFFFF', 0.85 * flash)))
        rain(cv, (g0[0], g0[1], g1[0], g1[1]), t, n=10, a=0.3)
        cv.restore()
        cv.drawRect(glass, stroke('#454B8A', max(3.0, gw * 0.03))); cv.drawRect(glass, stroke(INKC, 3))
        hx_, hy_ = cam.p(0.37 + sx, 1.0, Z)
        k = cam.f / max(cam.d(Z), 0.05)
        cv.save(); cv.rotate(handle, hx_, hy_)
        cv.drawLine(hx_, hy_, hx_ - 0.12 * k, hy_, stroke('#C9A45C', 0.03 * k)); cv.drawCircle(hx_, hy_, 0.03 * k, paint('#8A7A4A'))
        cv.restore()
    if arch_frame and cam.d(0) > 0.06:                                          # the living-room wall with the arch, in front
        a0, a1 = cam.p(-0.75, 0, 0), cam.p(0.75, 2.25, 0)
        k = cam.f / cam.d(0)
        p = skia.Path()
        p.addRect(R(-4000, -4000, 5000, 6000))
        hole = skia.Path()
        rad = 0.75 * k
        hole.moveTo(a0[0], a0[1] + 4000); hole.lineTo(a0[0], a1[1] + rad); hole.arcTo(R(a0[0], a1[1], a1[0], a1[1] + 2 * rad), 180, 180, False)
        hole.lineTo(a1[0], a0[1] + 4000); hole.close()
        p.addPath(hole); p.setFillType(skia.PathFillType.kEvenOdd)
        cv.drawPath(p, paint('#000000', shader=lin((0, 0), (0, H), [C('#1E2148'), C('#262958')])))
        cv.drawPath(hole, stroke('#454B8A', max(6.0, 0.05 * k))); cv.drawPath(hole, stroke(INKC, 4))
        cx_, cy_ = cam.p(0, 2.42, 0)
        clock_1147(cv, cx_, cy_, 0.0022 * k)                                    # hidden detail #1 again: above the arch, still 11:47


# ----------------------------------------------------------------------------------------------- inserts: the security camera view
G0, G1, G2, G3, G4, G5 = '#06140C', '#0D2416', '#17402A', '#27673F', '#47A066', '#8CE0A8'


def _cam_head(cv, x, y, r, ang, pin=1.0, hair=G1, face=G4, glasses=True, frame=0):
    """A head seen from the ceiling camera: hair on top, a face patch on the side it is turned to (ang: 0 = image right, 90 = down)."""
    cv.drawCircle(x, y, r, paint(hair)); cv.drawCircle(x, y, r, stroke(G0, 2.5))
    if ang is None:
        return
    a = math.radians(ang)
    fx, fy = x + math.cos(a) * r * 0.52, y + math.sin(a) * r * 0.52
    cv.save(); cv.translate(fx, fy); cv.rotate(ang)
    cv.drawOval(R(-r * 0.42, -r * 0.7, r * 0.5, r * 0.7), paint(face))
    if glasses:
        for sd in (-1, 1):
            cv.drawCircle(r * 0.12, sd * r * 0.32, r * 0.26, stroke(G5, 2))
            if pin > 0:                                                         # two pinpricks behind each lens = four
                for dy in (-0.09, 0.09):
                    px, py = r * 0.14, sd * r * 0.32 + dy * r + 0.4 * math.sin(frame * 0.3 + dy * 40)
                    cv.drawCircle(px, py, r * 0.16, paint(C('#FF2A2A', 0.5 * pin), blur=r * 0.1))
                    cv.drawCircle(px, py, r * 0.065, paint(C('#FF4A3A', pin)))
    else:
        for sd in (-1, 1):
            cv.drawCircle(r * 0.16, sd * r * 0.3, r * 0.09, paint(G0))
    cv.restore()


def feed_thing(cv, u, frame):
    """The thing on the DELAYED feed. u = seconds since it started to move (u < 0: still sitting)."""
    sil, edge = paint(G0), stroke('#12301E', 2.5)
    wob = lambda k: 4 * math.sin(frame * 0.5 + k)  # noqa: E731
    if u < 0:
        cv.drawRoundRect(R(265, 268, 345, 312), 16, 16, paint(G2)); cv.drawRoundRect(R(265, 268, 345, 312), 16, 16, edge)
        _cam_head(cv, 305, 250, 34, 0, frame=frame)
        return
    if u < 0.8:                                                                 # it unfolds: arms reach back over the backrest
        k = u / 0.8
        cv.drawRoundRect(R(268, 262 - 20 * k, 342, 316), 16, 16, sil)
        for sd in (-1, 1):
            cv.drawPath(poly([(305 + sd * 30, 280), (305 + sd * (52 + 10 * k), 262 - 30 * k), (305 + sd * 36, 262 + 58 * k)], closed=False), stroke(G0, 9))
        _cam_head(cv, 305, 250 - 22 * k, 34, 0, hair=G0, frame=frame)
        return
    if u < 1.6:                                                                 # perched on the backrest like a spider
        k = (u - 0.8) / 0.8
        cy = 300 + 16 * k
        cv.drawOval(R(272, cy - 26, 338, cy + 22), sil)
        for sd in (-1, 1):
            cv.drawPath(poly([(305 + sd * 26, cy - 6), (305 + sd * 72, cy - 44 + wob(sd)), (305 + sd * 58, cy + 8)], closed=False), stroke(G0, 8))
            cv.drawPath(poly([(305 + sd * 22, cy + 10), (305 + sd * 64, cy + 2 + wob(sd + 2)), (305 + sd * 44, cy + 40)], closed=False), stroke(G0, 8))
        _cam_head(cv, 305, cy - 24, 32, 0, hair=G0, frame=frame)
        return
    if u < 2.1:                                                                 # slides down behind the couch
        k = (u - 1.6) / 0.5
        cy = 316 + 112 * k
        cv.drawOval(R(274, cy - 30, 336, cy + 24), sil)
        for sd in (-1, 1):
            cv.drawPath(poly([(305 + sd * 24, cy - 8), (305 + sd * 66, cy - 50), (305 + sd * 50, cy - 86 + 60 * k)], closed=False), stroke(G0, 8))
        _cam_head(cv, 305, cy - 6, 30, 20 - 20 * k, hair=G0, frame=frame)
        return
    k = min(1.0, (u - 2.1) / 1.9)                                               # crawls along the wall to right behind you
    k = k * k * (3 - 2 * k)
    x = 305 + 187 * k
    cv.drawOval(R(x - 40, 412, x + 40, 452), sil)
    for sd in (-1, 1):
        cv.drawPath(poly([(x + sd * 30, 428), (x + sd * 66, 404 + wob(sd)), (x + sd * 84, 436)], closed=False), stroke(G0, 8))
    _cam_head(cv, x, 424, 28, -90 if k > 0.95 else 0, hair=G0, frame=frame)       # at the end it looks up... at the back of your head


def cam_scene(cv, t, frame, mode='tv', u=-1.0, you_ang=None, thing_ang=0.0, badge=0.0, static=0.0, pin=1.0):
    """HOME CAM 02 (800 x 450 local units): the ceiling camera BEHIND the couch, looking at the TV wall. Green night vision;
    the only red in the picture is its four eyes. mode 'photo' = the still Bob sends (thing_ang = where its head points)."""
    cv.drawRect(R(0, 0, 800, 450), paint(G1))
    cv.drawRect(R(0, 0, 800, 118), paint(G2))
    cv.drawOval(R(190, 110, 610, 215), paint(C(G3, 0.5), blur=14))                                                     # TV light on the floor
    rr(cv, 322, 30, 478, 106, 4, G0); cv.drawRect(R(330, 36, 470, 100), paint(G4))
    cv.drawRect(R(368, 52, 432, 88), paint(C(G5, 0.7)))                                                                 # the feed inside the feed
    cv.drawOval(R(150, 180, 650, 330), paint(C(G2, 0.7)))
    rr(cv, 330, 160, 470, 204, 8, G3); cv.drawRoundRect(R(330, 160, 470, 204), 8, 8, stroke(G0, 2.5))
    rr(cv, 150, 214, 192, 346, 14, G2); rr(cv, 608, 214, 650, 346, 14, G2)                                                # armrests
    rr(cv, 176, 222, 624, 302, 12, G3)                                                                                  # seats
    cv.drawLine(400, 224, 400, 300, stroke(G1, 3))
    if u >= 0.8 or (mode == 'tv' and u >= 0):
        cv.drawOval(R(272, 246, 338, 286), paint(C(G1, 0.8)))                                                           # the dent it left
    cv.drawOval(R(470, 262, 580, 300), paint(C(G0, 0.75), blur=6))                                                      # YOUR shadow on the seat. It has none.
    cv.drawRoundRect(R(455, 268, 535, 312), 16, 16, paint(G4)); cv.drawRoundRect(R(455, 268, 535, 312), 16, 16, stroke(G0, 2.5))
    _cam_head(cv, 495, 250, 34, you_ang, hair=G2, face=G5, glasses=False)
    if u < 1.6:
        if mode == 'photo':
            cv.drawRoundRect(R(265, 268, 345, 312), 16, 16, paint(G2)); cv.drawRoundRect(R(265, 268, 345, 312), 16, 16, stroke('#12301E', 2.5))
            for k in range(3):                                                                                          # the neck, wrung like a towel
                cv.drawArc(R(291, 262 + k * 5, 319, 276 + k * 5), 200, 140, False, stroke(G0, 2))
            _cam_head(cv, 305, 250, 34, thing_ang, pin=pin, frame=frame)
        else:
            feed_thing(cv, u, frame)
    rr(cv, 170, 298, 630, 342, 14, G4); cv.drawRoundRect(R(170, 298, 630, 342), 14, 14, stroke(G0, 2.5))                  # backrest top
    cv.drawRect(R(174, 340, 626, 428), paint('#000000', shader=lin((0, 340), (0, 428), [C(G2), C(G1)])))                  # the back of the couch
    cv.drawRect(R(0, 428, 800, 450), paint(G0))
    if mode == 'tv' and u >= 1.6:
        feed_thing(cv, u, frame)
    for y in range(0, 450, 4):                                                                                          # scanlines
        cv.drawLine(0, y, 800, y, stroke('#000000', 1.2, 0.2))
    rng = np.random.default_rng(frame)
    for _ in range(90):
        x, y = rng.uniform(0, 800), rng.uniform(0, 450)
        cv.drawRect(R(x, y, x + 2.5, y + 2.5), paint(C(G5, rng.uniform(0.1, 0.4))))
    cv.drawRect(R(0, 0, 800, 450), paint('#000000', shader=skia.GradientShader.MakeRadial((400, 225), 470, [C('#000000', 0.0).toColor(), C('#000000', 0.55).toColor()], [0.55, 1.0])))
    text(cv, 'HOME CAM 02 — LIVING ROOM', 96, 34, 21, G5, align='left')
    if int(t * 2) % 2 == 0:
        cv.drawCircle(104, 58, 6, paint('#FF3B30'))
    text(cv, 'REC', 116, 65, 18, G5, align='left')
    text(cv, '11:47 PM', 96, 432, 22, G5, align='left')
    if mode == 'tv':
        on = badge <= 0 or int(t * 3.4) % 2 == 0
        col = '#FF3B30' if badge > 0 else G4
        cv.drawRoundRect(R(486, 20, 712, 56), 6, 6, paint(C('#000000', 0.6)))
        if on:
            cv.drawRoundRect(R(486, 20, 712, 56), 6, 6, stroke(col, 2.5))
            text(cv, 'FEED DELAY: −5.0 SECONDS', 599, 45, 17.5, col)
    if static > 0:                                                                                                      # switching on: white static
        rng = np.random.default_rng(frame * 7 + 1)
        for _ in range(int(900 * static)):
            x, y = rng.uniform(0, 800), rng.uniform(0, 450)
            cv.drawRect(R(x, y, x + rng.uniform(3, 26), y + 3), paint(C('#FFFFFF', rng.uniform(0.3, 0.9) * static)))
        cv.drawRect(R(0, 0, 800, 450), paint(C('#FFFFFF', 0.5 * static)))


# ----------------------------------------------------------------------------------------------- inserts: phone screens (phone-local units)
def _status(cv, col='#FFFFFF'):
    text(cv, '12:07', -262, -566, 34, col, align='left')
    text(cv, '5G', 196, -566, 30, col, align='right')
    cv.drawRoundRect(R(208, -590, 262, -566), 6, 6, stroke(col, 3)); cv.drawRect(R(212, -586, 236, -570), paint(col))


def ui_lock(cv, t, pulse=1.0):
    """Lock screen: the crimson banner. BOB: DON'T OPEN THE DOOR."""
    cv.drawRect(R(-300, -620, 300, 620), paint('#000000', shader=lin((0, -620), (0, 620), [C('#0B0C1E'), C('#171A3A')])))
    _status(cv)
    text(cv, '12:07', 0, -360, 150, '#FFFFFF', alpha=0.92)
    text(cv, 'Friday', 0, -296, 40, '#C8CCE8', bold=False)
    a = 0.78 + 0.22 * math.sin(t * 2 * math.pi * 6) * pulse
    cv.drawRoundRect(R(-282, -236, 282, 176), 34, 34, paint(C('#D81E28', a)))
    cv.drawRoundRect(R(-282, -236, 282, 176), 34, 34, stroke('#FF6A6A', 5, 0.9))
    cv.drawRoundRect(R(-256, -212, -206, -162), 12, 12, paint('#FFFFFF')); text(cv, '!', -231, -170, 44, '#D81E28')
    text(cv, 'MESSAGES', -190, -172, 30, '#FFD8D8', align='left', bold=False)
    text(cv, 'now', 256, -172, 30, '#FFD8D8', align='right', bold=False)
    text(cv, 'BOB', -256, -92, 74, '#FFFFFF', align='left')
    text(cv, "DON'T OPEN", 0, 22, 104, '#FFFFFF')
    text(cv, 'THE DOOR.', 0, 130, 104, '#FFFFFF')
    text(cv, 'swipe up to open', 0, 560, 30, '#8A8EB0', bold=False)


def ui_thread(cv, t, frame, load=0.0, sharp=0.0, thing_ang=0.0, pin=1.0, typing=True, show=1.0):
    """Messages with BOB: his first text, then the photo from HOME CAM 02 (load 0..1 = loading bar, sharp 0..1 = un-blur)."""
    cv.drawRect(R(-300, -620, 300, 620), paint('#0C0D1C'))
    _status(cv)
    cv.drawRect(R(-300, -540, 300, -430), paint('#14162C')); cv.drawLine(-300, -430, 300, -430, stroke('#23264A', 3))
    cv.drawCircle(-196, -486, 36, paint('#2F8A86')); text(cv, 'B', -196, -468, 46, '#FFFFFF')
    text(cv, 'BOB', -144, -470, 50, '#FFFFFF', align='left')
    cv.drawRoundRect(R(-276, -406, 190, -318), 30, 30, paint('#2A2C48')); text(cv, "DON'T OPEN THE DOOR.", -250, -346, 40, '#FFFFFF', align='left')
    box = R(-270, -290, 270, 14)                                                  # 540 x 304 = the photo
    if show <= 0:
        return
    cv.save(); cv.translate(-270, 14); cv.scale(show, show); cv.translate(270, -14)   # the new bubble pops in
    cv.save(); cv.clipRRect(skia.RRect.MakeRectXY(box, 26, 26), True)
    cv.drawRect(box, paint('#101226'))
    if load >= 1.0:
        cv.save(); cv.translate(-270, -290); cv.scale(1.08, 1.08); cv.translate(-150, -170)                              # crop: the couch, from behind
        if sharp < 1.0:
            cv.saveLayer(None, skia.Paint(ImageFilter=skia.ImageFilters.Blur(14 * (1 - sharp), 14 * (1 - sharp))))
        cam_scene(cv, t, frame, mode='photo', you_ang=None, thing_ang=thing_ang, pin=pin * sharp)
        if sharp < 1.0:
            cv.restore()
        cv.restore()
        cv.drawRoundRect(R(-256, -276, -176, -240), 8, 8, paint('#D81E28')); text(cv, 'LIVE', -216, -249, 26, '#FFFFFF')
        cv.drawRoundRect(R(-168, -276, -56, -240), 8, 8, paint(C('#000000', 0.62))); text(cv, '11:47 PM', -112, -249, 24, '#FFFFFF')
        cv.drawRoundRect(R(120, -30, 262, 4), 6, 6, paint(C('#000000', 0.6))); text(cv, '11:47 PM', 191, -4, 26, '#FFFFFF')
    else:
        text(cv, 'HOME CAM 02', 0, -170, 34, '#6A70A0', bold=False)
        cv.drawRoundRect(R(-200, -138, 200, -118), 10, 10, paint('#23264A'))
        cv.drawRoundRect(R(-200, -138, -200 + 400 * load, -118), 10, 10, paint('#4AA8FF'))
        text(cv, f'{int(load * 100)}%', 0, -70, 44, '#FFFFFF')
    cv.restore()
    cv.drawRoundRect(box, 26, 26, stroke('#3A3E70', 3))
    cv.restore()
    if typing:
        cv.drawRoundRect(R(-276, 44, -150, 112), 30, 30, paint('#2A2C48'))
        for k in range(3):
            cv.drawCircle(-244 + k * 31, 78 - 6 * max(0.0, math.sin(t * 9 - k * 0.9)), 9, paint('#A8ACD0'))
    cv.drawRoundRect(R(-276, 520, 276, 590), 34, 34, stroke('#3A3E70', 3)); text(cv, 'Message', -240, 568, 34, '#5A5E88', align='left', bold=False)


def ui_call(cv, t):
    """INCOMING CALL: BOB. (Bob's phone is pressed against your door glass.)"""
    cv.drawRect(R(-300, -620, 300, 620), paint('#000000', shader=lin((0, -620), (0, 620), [C('#10283A'), C('#07101C')])))
    _status(cv)
    text(cv, 'INCOMING CALL', 0, -420, 44, '#9FE8FF')
    k = 1 + 0.06 * math.sin(t * 2 * math.pi * 5)
    cv.drawCircle(0, -200, 150 * k, paint(C('#2F8A86', 0.35))); cv.drawCircle(0, -200, 118, paint('#2F8A86')); text(cv, 'B', 0, -150, 150, '#FFFFFF')
    text(cv, 'BOB', 0, 90, 150, '#FFFFFF')
    text(cv, 'mobile', 0, 150, 40, '#9FB0C8', bold=False)
    cv.drawCircle(-150, 420, 78, paint('#E83A3A')); cv.drawCircle(150, 420, 78, paint('#3AC85A'))
