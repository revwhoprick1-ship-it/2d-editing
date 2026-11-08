#!/usr/bin/env python3
"""VIDEO_006 "The 13th Floor" — real 2D animation (2dEDIT). Draws every shot as flat vector art with Skia.

    python3 VIDEOS/VIDEO_006/anim2d.py [--jobs DISP,FACE] [--still JOB:frame ...] [--procs 4]

Writes frames2d/<JOB>/<frame>.png (frame = scene frame = video frame; the EDL maps them 1:1).
Only the frames the EDL shows are drawn.
"""
import argparse
import math
import os
import sys
from multiprocessing import Pool

import skia

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'twod'))
sys.path.insert(0, HERE)
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa
import edit_video006 as E  # noqa

FPS = 30
TF = skia.Typeface.MakeFromFile(os.path.join(STUDIO, 'ASSETS', 'fonts', 'RobotoCondensed-Bold.ttf'))
OUT = os.path.join(HERE, 'frames2d')
WORDS = E._T['words']


def font(size):
    return skia.Font(TF, size)


def text(cv, s, x, y, size, col, align='center', alpha=1.0, blur=0):
    f = font(size)
    w = f.measureText(s)
    x0 = x - w / 2 if align == 'center' else (x - w if align == 'right' else x)
    cv.drawString(s, x0, y, f, paint(C(col, alpha), blur=blur))


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ramp(t, t0, t1, a, b):
    return a + (b - a) * ease((t - t0) / (t1 - t0)) if t1 > t0 else b


def keys(t, ks):
    """[(t, v), ...] eased piecewise."""
    if t <= ks[0][0]:
        return ks[0][1]
    for (t0, a), (t1, b) in zip(ks, ks[1:]):
        if t < t1:
            if isinstance(a, tuple):
                return tuple(ramp(t, t0, t1, x, y) for x, y in zip(a, b))
            return ramp(t, t0, t1, a, b)
    return ks[-1][1]


def mouth_open(t, lines):
    for w in WORDS:
        if w['line'] in lines and w['start'] <= t < w['end'] + 0.04:
            u = t - w['start']
            return 0.35 + 0.5 * abs(math.sin(2 * math.pi * 5.5 * u + 0.4))
    return 0.0


def blink(t, times, dur=0.14):
    for b in times:
        if b <= t < b + dur:
            return 1 - abs((t - b) / dur * 2 - 1)
    return 0.0


def dim(cv, a, col='#000000'):
    if a > 0.001:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(C(col, min(1.0, a))))


# ===================================================================== timeline facts
T = E
L_FLICK = [(4.8, 4.9, 0.25), (5.15, 5.3, 0.12), (6.28, 6.4, 0.35)]


def elev_light(t):
    for a, b, v in L_FLICK:
        if a <= t < b:
            return v
    return 1.0


def door_open(t):
    """Elevator doors: 0 shut .. 1 open."""
    return keys(t, [(0, 0.0), (T.T_DING1 + 0.1, 0.0), (T.T_DING1 + 1.3, 1.0), (T.T_SLAM - 0.02, 1.0), (T.T_SLAM + 0.22, 0.0),
                    (T.T_DING2 + 0.05, 0.0), (T.T_DING2 + 0.4, 1.0), (31.9, 1.0), (32.5, 0.0)])


def far_door(t):
    return keys(t, [(0, 0.0), (T.T_DOOR13, 0.0), (T.T_DOOR13 + 1.6, 1.0)])


def his_z(t):
    """His distance down the 13th-floor hallway (m from the elevator doors)."""
    return keys(t, [(0, -0.6), (T.T_OUT, -0.6), (T.T_PHOTO - 0.2, 3.1), (T.T_TURN, 3.1), (T.T_RUNB, 3.1), (18.3, 0.12),
                    (T.T_WALK2, 0.12), (T.T_PEEK - 0.1, 9.75), (40, 9.75)])


def walking(t):
    if T.T_OUT <= t < T.T_PHOTO - 0.2:
        return ((t - T.T_OUT) / 1.0) % 1.0
    if T.T_RUNB <= t < 18.3:
        return ((t - T.T_RUNB) / 0.4) % 1.0
    if T.T_WALK2 <= t < T.T_PEEK - 0.1:
        return ((t - T.T_WALK2) / 0.75) % 1.0
    return None


def bob(ph):
    return 0 if ph is None else -abs(math.sin(2 * math.pi * ph)) * 14


# ===================================================================== perspective (one-point)
F_PX = 1000.0


class Cam:
    def __init__(self, z, eye=1.35, vx=540, vy=900, x=0.0, f=F_PX, facing=1):
        self.z, self.eye, self.vx, self.vy, self.x, self.f, self.facing = z, eye, vx, vy, x, f, facing

    def d(self, z):
        return (z - self.z) * self.facing

    def p(self, x, h, z):
        d = max(self.d(z), 0.05)
        return (self.vx + self.f * (x - self.x) * self.facing / d, self.vy - self.f * (h - self.eye) / d)

    def scale(self, z, height=1.25):
        return self.f * height / max(self.d(z), 0.05) / 1150.0


HW, HH, ZEND = 0.92, 2.5, 10.2


def quad(cam, pts):
    return poly([cam.p(*q) for q in pts])


def wall_strip(cv, cam, x, z0, z1, h0, h1, col):
    cv.drawPath(quad(cam, [(x, h0, z0), (x, h0, z1), (x, h1, z1), (x, h1, z0)]), paint(col))


def hallway(cv, cam, t, lit=1.0, sil=False, photo_scene=False):
    """13th-floor hallway, seen from cam (facing +z = towards the far door, or -z = back to the elevator)."""
    near = cam.z + 0.12 * cam.facing
    z0 = max(near, -0.0) if cam.facing > 0 else min(near, ZEND)
    zf = ZEND if cam.facing > 0 else 0.0
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0B0D0F'))
    # end wall
    if cam.facing > 0:
        cv.drawPath(quad(cam, [(-HW, 0, zf), (HW, 0, zf), (HW, HH, zf), (-HW, HH, zf)]), paint('#2A2E26'))
    # walls, ceiling, floor
    for x, col0, col1 in ((-HW, '#2C3A2E', '#1A221B'), (HW, '#28352A', '#161D17')):
        a, b = cam.p(x, 0, z0), cam.p(x, 0, zf)
        cv.drawPath(quad(cam, [(x, 0, z0), (x, 0, zf), (x, HH, zf), (x, HH, z0)]),
                    paint(col0, shader=lin(a, b, [C(col1), C(col0)])))
        z = 0.0
        while z < ZEND:                                    # wallpaper stripes (give depth)
            if (z - z0) * cam.facing > 0 and (zf - z) * cam.facing > 0:
                p0, p1 = cam.p(x, 0.12, z), cam.p(x, HH, z)
                cv.drawLine(*p0, *p1, paint(C('#3E5040', 0.55), style='stroke', width=max(1.0, 220 / max(cam.d(z), 0.3) * 0.02)))
            z += 0.3
        wall_strip(cv, cam, x, z0, zf, 0, 0.12, '#1A120D')            # baseboard
        wall_strip(cv, cam, x, z0, zf, 0.95, 1.0, '#3C2A1E')          # dado rail
    cv.drawPath(quad(cam, [(-HW, HH, z0), (HW, HH, z0), (HW, HH, zf), (-HW, HH, zf)]), paint('#0F1112'))
    cv.drawPath(quad(cam, [(-HW, 0, z0), (HW, 0, z0), (HW, 0, zf), (-HW, 0, zf)]),
                paint('#3B2D22', shader=lin(cam.p(0, 0, zf), cam.p(0, 0, z0 + 0.5 * cam.facing), [C('#2A2018'), C('#4A382A')])))
    cv.drawPath(quad(cam, [(-0.45, 0.002, z0), (0.45, 0.002, z0), (0.45, 0.002, zf), (-0.45, 0.002, zf)]), paint('#3A1C1A'))
    cv.drawPath(quad(cam, [(-0.38, 0.003, z0), (0.38, 0.003, z0), (0.38, 0.003, zf), (-0.38, 0.003, zf)]), paint('#4A2420'))
    # far door (apartment 1313) or the elevator at the other end
    if cam.facing > 0:
        o = far_door(t)
        dx0, dx1 = -0.45, 0.45
        cv.drawPath(quad(cam, [(dx0 - 0.06, 0, zf), (dx1 + 0.06, 0, zf), (dx1 + 0.06, 2.12, zf), (dx0 - 0.06, 2.12, zf)]), paint('#1B140F'))
        if o > 0.01:                                       # warm room light behind the door
            cv.drawPath(quad(cam, [(dx0, 0, zf), (dx1, 0, zf), (dx1, 2.05, zf), (dx0, 2.05, zf)]), paint('#C98A4E'))
            c = cam.p(0, 1.0, zf)
            glow(cv, c, 900 / max(cam.d(zf), 0.5), '#FFB067', 0.35 * o)
            spill = [cam.p(dx0, 0, zf), cam.p(dx1, 0, zf), cam.p(0.7, 0, zf - 2.5 * o), cam.p(-0.7, 0, zf - 2.5 * o)]
            cv.drawPath(poly(spill), paint(C('#FFB067', 0.18 * o), blur=10))
        th = o * math.radians(80)
        ex, ez = dx0 + 0.9 * math.cos(th), zf - 0.9 * math.sin(th)
        cv.drawPath(quad(cam, [(dx0, 0, zf), (ex, 0, ez), (ex, 2.05, ez), (dx0, 2.05, zf)]), paint('#4A3020'))
        k = cam.p(dx0 + 0.78 * math.cos(th), 1.0, zf - 0.78 * math.sin(th))
        cv.drawCircle(*k, max(1.5, 30 / max(cam.d(zf), 0.4)), paint('#C9A45C'))
        pl = [cam.p(-0.12, 1.62, zf - 0.001), cam.p(0.12, 1.62, zf - 0.001)]
        if o < 0.05:
            text(cv, '1313', (pl[0][0] + pl[1][0]) / 2, pl[0][1], max(8, 120 / max(cam.d(zf), 0.4)), '#C9A45C')
    # photo frame + plaque (left wall, z=3.6)
    if not photo_scene:
        fr = quad(cam, [(-HW + 0.01, 1.17, 3.36), (-HW + 0.01, 1.17, 3.84), (-HW + 0.01, 1.75, 3.84), (-HW + 0.01, 1.75, 3.36)])
        cv.drawPath(fr, paint('#5A3A22'))
        cv.drawPath(quad(cam, [(-HW + 0.012, 1.22, 3.41), (-HW + 0.012, 1.22, 3.79), (-HW + 0.012, 1.70, 3.79), (-HW + 0.012, 1.70, 3.41)]),
                    paint('#3A4A55'))
    # sconces (left wall)
    for i, zs in enumerate((3.0, 6.2, 9.4)):
        if (zs - z0) * cam.facing <= 0.05:
            continue
        on = lit * (0.12 if 9.0 + i <= t < 9.12 + i else 1.0)
        c = cam.p(-HW + 0.05, 1.9, zs)
        r = 70 / max(cam.d(zs), 0.3)
        cv.drawRect(skia.Rect(c[0] - r * 0.5, c[1] - r * 0.7, c[0] + r * 0.5, c[1] + r * 0.7), paint(C('#FFD39A', 0.25 + 0.75 * on)))
        if on > 0.2:
            glow(cv, c, r * 9, '#FFB060', 0.33 * on)
            fl = cam.p(-HW + 0.4, 0.0, zs)
            glow(cv, fl, r * 7, '#FFB060', 0.12 * on)
    if sil and cam.facing > 0:                             # the figure at the end of the hall
        z = 9.8
        silhouette(cv, *cam.p(0.15, 0, z), cam.scale(z))
    # dust motes
    for k in range(40):
        zx = (k * 0.618) % 1
        z = 0.5 + zx * 9.5
        if (z - z0) * cam.facing <= 0.2:
            continue
        x = -0.8 + ((k * 0.381) % 1) * 1.6
        h = 0.4 + ((k * 0.7548) % 1) * 1.9 + 0.08 * math.sin(t * 0.7 + k)
        q = cam.p(x, h, z)
        cv.drawCircle(*q, max(1.2, 9 / max(cam.d(z), 0.4)), paint(C('#FFE9C8', 0.35)))


def silhouette(cv, x, y, s):
    cv.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Blend(C('#050506').toColor(), skia.BlendMode.kSrcIn)))
    mascot(cv, x, y, s * 1.12, arm_l=(3, 0), arm_r=(3, 0))
    cv.restore()
    for side in (-1, 1):
        cv.drawCircle(x + side * 70 * s * 1.12, y - 910 * s * 1.12, 12 * s * 1.12, paint('#E8E8E8'))


def mascot_at(cv, cam, x, z, **pose):
    s = cam.scale(z)
    fx, fy = cam.p(x, 0, z)
    mascot(cv, fx, fy + bob(pose.get('walk')) * s, s, **pose)


# ===================================================================== the elevator
def elevator_back(cv, light=1.0):
    """Inside the car, looking at the back wall (the style frame view)."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1B2129'))
    vx0, vx1, vy0, vy1 = 170, 910, 360, 1500
    cv.drawRect(skia.Rect(vx0, vy0, vx1, vy1), paint('#3A4552', shader=lin((0, vy0), (0, vy1), [C('#4A5664'), C('#2C343E')])))
    for i in range(3):
        x = vx0 + 30 + i * (vx1 - vx0 - 60) / 3
        cv.drawRect(skia.Rect(x + 10, vy0 + 40, x + (vx1 - vx0 - 60) / 3 - 10, vy1 - 160),
                    paint('#43505E', shader=lin((x, 0), (x + 240, 0), [C('#4C5967'), C('#3B4653')])))
    cv.drawPath(poly([(0, 0), (vx0, vy0), (vx0, vy1), (0, H)]), paint('#252D37', shader=lin((0, 0), (vx0, 0), [C('#1A2028'), C('#2E3742')])))
    cv.drawPath(poly([(W, 0), (vx1, vy0), (vx1, vy1), (W, H)]), paint('#2A333E', shader=lin((W, 0), (vx1, 0), [C('#1D232C'), C('#36404C')])))
    cv.drawPath(poly([(0, 0), (W, 0), (vx1, vy0), (vx0, vy0)]), paint('#161B22'))
    cv.drawPath(poly([(330, 150), (750, 150), (700, 300), (380, 300)]), paint(C('#E6F0FF', 0.25 + 0.75 * light)))
    cv.drawPath(poly([(0, H), (vx0, vy1), (vx1, vy1), (W, H)]), paint('#2B2622', shader=lin((0, vy1), (0, H), [C('#2A2420'), C('#3A322B')])))
    cv.drawRect(skia.Rect(vx0, 1060, vx1, 1078), paint('#8E99A6'))
    cv.drawPath(poly([(vx1, 1060), (W, 1180), (W, 1204), (vx1, 1078)]), paint('#7D8895'))
    cv.drawPath(poly([(960, 760), (1040, 735), (1040, 1010), (960, 1000)]), paint('#59636F'))
    for bx, by, col in ((1000, 790, '#FF3B2F'), (985, 850, '#FFB23A'), (1018, 850, '#C9CED6'), (985, 905, '#C9CED6'), (1018, 905, '#C9CED6')):
        cv.drawCircle(bx, by, 14, paint(col))
    glow(cv, (1000, 790), 60, '#FF3B2F', 0.5)
    glow(cv, (985, 850), 50, '#FFB23A', 0.35)


def light_over(cv, light):
    glow(cv, (540, 230), 900, '#BFD6FF', 0.22 * light)
    shade(cv, (540, 820), 1250, 0.75)
    dim(cv, (1 - light) * 0.8)


def elevator_front(cv, t, beyond, light=1.0, cam_z=-1.6):
    """Inside the car, looking OUT at the doors. beyond(cv) draws what is past the doorway."""
    beyond(cv)
    cam = Cam(cam_z, eye=1.35, vy=880)
    # front wall with the doorway hole (z = 0); doorway x +-0.67, h 2.1
    col = '#2E3640'
    for pts in ([(-1.0, 0, 0), (-0.67, 0, 0), (-0.67, 2.3, 0), (-1.0, 2.3, 0)], [(0.67, 0, 0), (1.0, 0, 0), (1.0, 2.3, 0), (0.67, 2.3, 0)],
                [(-1.0, 2.1, 0), (1.0, 2.1, 0), (1.0, 2.3, 0), (-1.0, 2.3, 0)]):
        cv.drawPath(quad(cam, pts), paint(col))
    # side walls / ceiling / floor of the car (between cam and the front wall)
    for pts, c in (([(-1.0, 0, cam_z + 0.2), (-1.0, 0, 0), (-1.0, 2.3, 0), (-1.0, 2.3, cam_z + 0.2)], '#232A33'),
                   ([(1.0, 0, cam_z + 0.2), (1.0, 0, 0), (1.0, 2.3, 0), (1.0, 2.3, cam_z + 0.2)], '#27303A'),
                   ([(-1.0, 2.3, cam_z + 0.2), (1.0, 2.3, cam_z + 0.2), (1.0, 2.3, 0), (-1.0, 2.3, 0)], '#14181E'),
                   ([(-1.0, 0, cam_z + 0.2), (1.0, 0, cam_z + 0.2), (1.0, 0, 0), (-1.0, 0, 0)], '#2B2622')):
        cv.drawPath(quad(cam, pts), paint(c))
    o = door_open(t)
    for s in (-1, 1):                                      # sliding door panels
        x_in = s * 0.67 * o
        cv.drawPath(quad(cam, [(x_in, 0, 0.01), (s * (0.67 + 0.67 * o) if o > 0 else s * 0.67, 0, 0.01),
                                (s * (0.67 + 0.67 * o) if o > 0 else s * 0.67, 2.1, 0.01), (x_in, 2.1, 0.01)]),
                    paint('#56616D', shader=lin(cam.p(x_in, 1, 0), cam.p(s * 0.67, 1, 0), [C('#606C79'), C('#46505B')])))
        a, b = cam.p(x_in, 0, 0.01), cam.p(x_in, 2.1, 0.01)
        cv.drawLine(*a, *b, paint('#1B2026', style='stroke', width=4))
    # floor display above the doorway
    c = cam.p(0, 2.2, 0)
    cv.drawRect(skia.Rect(c[0] - 120, c[1] - 40, c[0] + 120, c[1] + 40), paint('#1A0E0C'))
    text(cv, display_floor(t), c[0] - 30, c[1] + 26, 70, '#FF5A40')
    light_over(cv, light)


def display_floor(t):
    if t < T.T_FLIP or t >= T.T_FLIP2:
        return '12'
    if 5.6 <= t < 5.95 and int(t * 20) % 2 == 0:
        return ''
    return '13'


def display_clock(t):
    if T.T_FLIP2 <= t < T.T_CLOCK:
        return '11:51' if int(t * 14) % 3 else '11:5_'
    return '11:48'


# ===================================================================== shots
def shot_DISP(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#20262E', shader=lin((0, 0), (0, H), [C('#2A313A'), C('#14181D')])))
    cv.drawRect(skia.Rect(60, 690, 1020, 1230), paint('#0E0B0A'))
    cv.drawRect(skia.Rect(80, 710, 1000, 1210), paint('#1A0E0C', shader=lin((0, 710), (0, 1210), [C('#241210'), C('#140A09')])))
    fl = display_floor(t)
    red = '#FF4A36'
    if fl:
        text(cv, fl, 420, 1120, 400, red, blur=0)
        glow(cv, (420, 960), 330, red, 0.28)
    arrow_up = t < T.T_DING1 + 0.6 or (T.T_FLIP2 - 0.6 <= t)
    if arrow_up:
        cv.drawPath(poly([(830, 800), (900, 890), (760, 890)]), paint(red))
    clk = display_clock(t)
    hot = T.T_CLOCK <= t < T.T_CLOCK + 1.2 and int(t * 6) % 2 == 0
    text(cv, clk, 830, 1080, 120, '#FFFFFF' if hot else '#FF8A70')
    for i in range(0, 540, 6):                                     # LED scanlines
        cv.drawLine(80, 710 + i, 1000, 710 + i, paint(C('#000000', 0.25), style='stroke', width=2))
    glow(cv, (540, 300), 900, '#BFD6FF', 0.12)
    shade(cv, (540, 960), 1100, 0.7)
    dim(cv, (1 - elev_light(t)) * 0.75)


def his_face_pose(t):
    if t < 1.0:
        return dict(look=(0.0, -0.85), brow=0.4, lids=0.35, mouth='flat', head_tilt=-4)
    if t < 2.4:
        return dict(look=(0.1, -0.9), brow=0.8, lids=0.1, mouth='flat', head_tilt=-8)
    if t < 4.8:
        return dict(look=(0.15, -0.8), brow=0.9, mouth='flat', head_tilt=keys(t, [(2.4, -8), (3.8, 6)]))
    if t < 7.0:
        return dict(look=(0.0, -0.95) if t < 6.4 else (0.0, 0.0), brow=1.0, mouth='o' if t > 6.4 else 'flat', pupil=0.75, sweat=t > 5.3)
    return dict(look=(0.0, 0.0), brow=1.0, mouth='o', pupil=0.7, sweat=True)


def shot_ELEV(cv, t):
    elevator_back(cv, elev_light(t))
    P = his_face_pose(t)
    P['lids'] = max(P.get('lids', 0), blink(t, [1.9]))
    mascot(cv, 520, 1640, 0.95, arm_l=(3, 0), arm_r=(3, 0), light_side=1, rim_a=0.5, **P)
    light_over(cv, elev_light(t))


def shot_FACE(cv, t):
    elevator_back(cv, elev_light(t))
    P = his_face_pose(t)
    P['mouth_open'] = mouth_open(t, ('D1',))
    P['lids'] = max(P.get('lids', 0), blink(t, [3.0, 4.6]))
    mascot(cv, 540, 2900, 2.35, arm_l=(3, 0), arm_r=(3, 0), light_side=1, rim_a=0.6, **P)
    light_over(cv, elev_light(t))


def shot_OUT(cv, t):
    """POV from the car: the doors open on the 13th floor."""
    cam = Cam(-1.6, eye=1.35, vy=880)
    elevator_front(cv, t, lambda c: hallway(c, cam, t, sil=True), light=elev_light(t), cam_z=-1.6)


def shot_TRACK(cv, t):
    z = his_z(t)
    cam = Cam(z - 1.7, eye=1.45, vy=860)
    hallway(cv, cam, t, sil=True)
    ph = walking(t)
    head = keys(t, [(T.T_PHOTO - 0.4, 0.0), (T.T_PHOTO, -0.6)])
    mascot_at(cv, cam, 0.05, z, view='back', walk=ph, head_tilt=-6 * head, light_side=-1)
    shade(cv, (540, 900), 1300, 0.55)


def photo_content(cv, x0, y0, w, h):
    """The photograph: him (blue shirt) in this very hallway."""
    surf = skia.Surface(int(w), int(h))
    c = surf.getCanvas()
    c.scale(w / W, h / H)
    cam = Cam(4.4, eye=1.3, vy=900)
    hallway(c, cam, 0.0, photo_scene=True)
    mascot_at(c, cam, 0.0, 6.6, shirt='#2F6FD0', shirt_sh='#22539F', look=(0, 0), mouth='flat', light_side=1)
    glow(c, (540, 700), 900, '#FFFFFF', 0.12)                       # flash photo
    cv.drawImageRect(surf.makeImageSnapshot(), skia.Rect(x0, y0, x0 + w, y0 + h), skia.SamplingOptions(skia.FilterMode.kLinear))


def wallpaper(cv):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#26332A'))
    for x in range(-40, W + 40, 90):
        cv.drawRect(skia.Rect(x, 0, x + 8, H), paint(C('#334437', 0.9)))
    for i in range(14):
        for j in range(8):
            cx, cy = j * 150 + (75 if i % 2 else 0), i * 150
            cv.drawPath(blob([(cx, cy - 34), (cx + 26, cy), (cx, cy + 34), (cx - 26, cy)]), paint(C('#30402F', 0.9)))


def shot_PHOTO(cv, t):
    wallpaper(cv)
    cv.drawRect(skia.Rect(150, 330, 930, 1370), paint('#5A3A22'))
    cv.drawRect(skia.Rect(178, 358, 902, 1342), paint('#3F2816'))
    photo_content(cv, 200, 380, 680, 940)
    glow(cv, (300, 200), 800, '#FFB060', 0.25)                      # sconce above-left
    cv.drawRect(skia.Rect(400, 1440, 680, 1540), paint('#B08A3C'))
    text(cv, '13', 540, 1522, 92, '#2A1E0A')
    shade(cv, (540, 860), 1100, 0.65)


def shot_EYES(cv, t):
    wallpaper(cv)
    glow(cv, (900, 200), 900, '#FFB060', 0.3)
    k = keys(t, [(15.85, 1.0), (15.95, 0.55)])
    mascot(cv, 470, 4300, 4.2, look=(-0.85, -0.05), brow=1.0, pupil=k, mouth='o', head_turn=-0.25, light_side=1, rim='#FFB060', rim_a=0.4,
           lids=blink(t, [16.4]))
    shade(cv, (540, 900), 1200, 0.6)


def shot_HALL(cv, t):
    """From down the hall, looking back at the lit elevator: the doors SLAM."""
    cam = Cam(4.6, eye=1.4, vy=880, facing=-1)
    hallway(cv, cam, t)
    # elevator end (z = 0): lit car interior behind the doors
    o = door_open(t)
    cv.drawPath(quad(cam, [(-1.0, 0, 0), (1.0, 0, 0), (1.0, 2.5, 0), (-1.0, 2.5, 0)]), paint('#20262D'))
    cv.drawPath(quad(cam, [(-0.67, 0, 0), (0.67, 0, 0), (0.67, 2.1, 0), (-0.67, 2.1, 0)]), paint('#C9D6E6'))
    if o > 0.02:
        glow(cv, cam.p(0, 1.2, 0), 500, '#CFE0FF', 0.35 * o)
    for s in (-1, 1):
        x_in = s * 0.67 * o
        cv.drawPath(quad(cam, [(x_in, 0, -0.01), (s * 0.67 * (1 + o), 0, -0.01), (s * 0.67 * (1 + o), 2.1, -0.01), (x_in, 2.1, -0.01)]),
                    paint('#56616D'))
    c = cam.p(0, 2.25, 0)
    cv.drawRect(skia.Rect(c[0] - 40, c[1] - 14, c[0] + 40, c[1] + 14), paint('#1A0E0C'))
    text(cv, '13', c[0], c[1] + 10, 26, '#FF5A40')
    turned = keys(t, [(T.T_TURN - 0.05, 0.0), (T.T_TURN + 0.25, 1.0)])
    view = 'front' if turned < 0.5 else 'back'
    mascot_at(cv, cam, -0.35, 3.1, view=view, look=(0.6, 0), brow=1.0, mouth='o', pupil=0.6, light_side=-1, rim='#FFB060', rim_a=0.3,
              arm_l=(3, 0), arm_r=(3, 0), head_turn=0.5 if view == 'front' else 0)
    shade(cv, (540, 900), 1300, 0.55)


def shot_DOORSIDE(cv, t):
    """He pounds the shut doors (back view, close)."""
    cam = Cam(1.6, eye=1.3, vy=900, facing=-1)
    hallway(cv, cam, t)
    cv.drawPath(quad(cam, [(-1.0, 0, 0), (1.0, 0, 0), (1.0, 2.5, 0), (-1.0, 2.5, 0)]), paint('#20262D'))
    for s in (-1, 1):
        cv.drawPath(quad(cam, [(0, 0, -0.01), (s * 0.67, 0, -0.01), (s * 0.67, 2.1, -0.01), (0, 2.1, -0.01)]),
                    paint('#56616D', shader=lin(cam.p(0, 1, 0), cam.p(s * 0.67, 1, 0), [C('#606C79'), C('#46505B')])))
    a, b = cam.p(0, 0, -0.02), cam.p(0, 2.1, -0.02)
    cv.drawLine(*a, *b, paint('#1B2026', style='stroke', width=5))
    c = cam.p(0, 2.25, 0)
    cv.drawRect(skia.Rect(c[0] - 100, c[1] - 34, c[0] + 100, c[1] + 34), paint('#1A0E0C'))
    text(cv, '13', c[0], c[1] + 24, 64, '#FF5A40')
    pound = 0.0
    for k in range(5):
        f0 = 18.4 + k * 0.2
        if f0 <= t < f0 + 0.2:
            pound = 1 - (t - f0) / 0.2
    up = 150 + 15 * pound
    mascot_at(cv, cam, 0.15, 0.55, view='back', arm_r=(up, 30 - 25 * pound), arm_l=(30, 40) if t < 18.4 else (120 + 20 * (1 - pound), 50),
              head_tilt=4 * pound, light_side=-1)
    shade(cv, (540, 900), 1200, 0.6)


def shot_LONG(cv, t):
    cam = Cam(0.35, eye=1.5, vy=860)
    hallway(cv, cam, t)
    z = his_z(t)
    if z > cam.z + 0.35:
        ph = walking(t)
        mascot_at(cv, cam, 0.0, z, view='back', walk=ph, light_side=-1)
    shade(cv, (540, 860), 1300, 0.55)


def apartment(cv, cam, t, show_double=True):
    """The apartment past the far door (z 10.2 .. 13.9), warm, TV static on the right wall."""
    z0, z1, w = ZEND, 13.9, 2.0
    cv.drawPath(quad(cam, [(-w, 0, z1), (w, 0, z1), (w, 2.5, z1), (-w, 2.5, z1)]), paint('#7A5236'))
    for x, col in ((-w, '#6E4A30'), (w, '#674530')):
        cv.drawPath(quad(cam, [(x, 0, z0), (x, 0, z1), (x, 2.5, z1), (x, 2.5, z0)]), paint(col))
    cv.drawPath(quad(cam, [(-w, 0, z0), (w, 0, z0), (w, 0, z1), (-w, 0, z1)]), paint('#4A3424'))
    cv.drawPath(quad(cam, [(-1.2, 0.003, 12.4), (1.2, 0.003, 12.4), (1.2, 0.003, 13.6), (-1.2, 0.003, 13.6)]), paint('#3C4A5C'))
    # TV on the right wall
    tv = quad(cam, [(w - 0.02, 0.7, 12.9), (w - 0.02, 0.7, 13.7), (w - 0.02, 1.2, 13.7), (w - 0.02, 1.2, 12.9)])
    cv.drawPath(tv, paint('#D7DCE4'))
    for k in range(18):
        y = 0.72 + k * 0.026
        a, b = cam.p(w - 0.03, y, 12.92), cam.p(w - 0.03, y, 13.68)
        cv.drawLine(*a, *b, paint(C('#6A7280', 0.5 + 0.5 * math.sin(t * 37 + k * 2.1)), style='stroke', width=2))
    glow(cv, cam.p(w - 0.1, 0.95, 13.3), 700 / max(cam.d(13.3), 0.5), '#A8C8FF', 0.4)
    # lamp (back left)
    lc = cam.p(-1.6, 1.3, 13.6)
    cv.drawPath(quad(cam, [(-1.75, 1.15, 13.6), (-1.45, 1.15, 13.6), (-1.5, 1.45, 13.6), (-1.7, 1.45, 13.6)]), paint('#F6CF92'))
    glow(cv, lc, 1400 / max(cam.d(13.6), 0.5), '#FFB067', 0.4)
    # the double + sofa (sofa back behind him, seat front hides his legs while he sits)
    stand = keys(t, [(T.T_STAND, 0.0), (T.T_STAND + 0.9, 1.0)])
    head_turn = keys(t, [(T.T_HEAD, 0.9), (T.T_HEAD + 1.0, 0.0)])
    sz = 13.15
    cv.drawPath(quad(cam, [(-1.25, 0.0, 13.5), (0.55, 0.0, 13.5), (0.55, 0.9, 13.5), (-1.25, 0.9, 13.5)]), paint('#5A2A2A'))
    cv.drawPath(quad(cam, [(-1.25, 0.9, 13.5), (0.55, 0.9, 13.5), (0.55, 0.98, 13.45), (-1.25, 0.98, 13.45)]), paint('#6E3434'))
    if show_double:
        s = cam.scale(sz)
        fx, fy = cam.p(-0.35, 0, sz)
        sit_drop = (1 - stand) * 250 * s
        mascot(cv, fx, fy + sit_drop, s, look=(0.9 * head_turn, 0.0), head_turn=head_turn, mouth='smile' if stand > 0.5 else 'flat',
               brow=-0.1, lids=0.25, light_side=1, rim='#A8C8FF', rim_a=0.5, legs=stand > 0.3, arm_l=(3, 0), arm_r=(3, 0))
    if stand < 0.3:
        cv.drawPath(quad(cam, [(-1.25, 0.0, 12.95), (0.55, 0.0, 12.95), (0.55, 0.42, 12.95), (-1.25, 0.42, 12.95)]), paint('#4E2424'))


def shot_OTS(cv, t):
    cam = Cam(8.55, eye=1.45, vy=900, x=0.2)
    hallway(cv, cam, t)
    # cut the doorway: draw the apartment inside the open door's frame
    surf = skia.Surface(W, H)
    c2 = surf.getCanvas()
    c2.clear(skia.Color4f(0, 0, 0, 0))
    apartment(c2, cam, t)
    hole = quad(cam, [(-0.45, 0, ZEND), (0.45, 0, ZEND), (0.45, 2.05, ZEND), (-0.45, 2.05, ZEND)])
    cv.save()
    cv.clipPath(hole, skia.ClipOp.kIntersect, True)
    cv.drawImage(surf.makeImageSnapshot(), 0, 0)
    cv.restore()
    th = math.radians(80)
    ex, ez = -0.45 + 0.9 * math.cos(th), ZEND - 0.9 * math.sin(th)
    cv.drawPath(quad(cam, [(-0.45, 0, ZEND), (ex, 0, ez), (ex, 2.05, ez), (-0.45, 2.05, ZEND)]), paint('#4A3020'))
    z = his_z(t)
    if z > cam.z + 0.3:
        ph = walking(t)
        lean = keys(t, [(T.T_PEEK - 0.1, 0.0), (T.T_PEEK + 0.4, -7.0)])
        mascot_at(cv, cam, 0.42, z, view='back', walk=ph, body_lean=lean, light_side=-1, rim='#FFB067', rim_a=0.5,
                  arm_l=(3, 0), arm_r=(3, 0) if t > T.T_PEEK else (10, 10))
    shade(cv, (540, 900), 1300, 0.6)


def shot_DOUBLE(cv, t):
    cam = Cam(11.2, eye=1.15, vy=900, x=-0.3)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A1C14'))
    apartment(cv, cam, t, show_double=False)
    mascot(cv, 540, 2480, 1.85, look=(0.0, 0.0), mouth='smile', mouth_open=mouth_open(t, ('D3',)) * 0.7, brow=-0.15,
           lids=0.28 + blink(t, [28.95]) * 0.7, light_side=-1, rim='#A8C8FF', rim_a=0.7, arm_l=(3, 0), arm_r=(3, 0))
    glow(cv, (160, 500), 700, '#FFB067', 0.25)
    shade(cv, (540, 820), 1200, 0.55)


def shot_IN(cv, t):
    """Inside the car, looking at the doors: he stumbles in out of the pitch-black floor."""
    cam = Cam(-1.6, eye=1.35, vy=880)

    def black(c):
        c.drawRect(skia.Rect(0, 0, W, H), paint('#020203'))
    elevator_front(cv, t, black, light=1.0, cam_z=-1.6)
    z = keys(t, [(T.T_DING2, 1.6), (T.T_DING2 + 0.35, 1.6), (31.3, -0.75), (40, -0.75)])
    x = keys(t, [(31.3, 0.0), (31.6, 0.35)])
    if z < 1.5:
        s = cam.scale(z)
        fx, fy = cam.p(x, 0, z)
        ph = ((t - T.T_DING2) / 0.4) % 1 if t < 31.3 else None
        jab = 0.0
        for k in range(4):
            f0 = 31.4 + k * 5 / 30
            if f0 <= t < f0 + 5 / 30:
                jab = 1 - (t - f0) * 6
        mascot(cv, fx, fy + bob(ph) * s, s, walk=ph, look=(0.5 if t > 31.3 else 0, 0), brow=1.0, mouth='open', mouth_open=0.4, pupil=0.6,
               sweat=True, arm_r=(80 + 20 * jab, 10) if t > 31.35 else (25, 30), arm_l=(3, 0), head_turn=0.4 if t > 31.3 else 0,
               light_side=1, rim_a=0.3)
    dim(cv, keys(t, [(T.T_DING2, 0.9), (T.T_DING2 + 0.25, 0.0)]))


def shot_BTN(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A313A', shader=lin((0, 0), (W, 0), [C('#232A33'), C('#323B46')])))
    cv.drawRect(skia.Rect(260, 220, 820, 1700), paint('#5C6672'))
    cv.drawRect(skia.Rect(260, 220, 820, 1700), paint('#2A3038', style='stroke', width=10))
    pos = {13: (540, 420)}
    for n in range(12, 0, -1):
        row, col = (12 - n) // 2, (n % 2)
        pos[n] = (400 + col * 280, 640 + row * 200)
    for n, (x, y) in pos.items():
        if y > 1650:
            continue
        lit = {13: '#FF3B2F', 12: '#FFB23A'}.get(n)
        if lit:
            glow(cv, (x, y), 230, lit, 0.45)
        cv.drawCircle(x, y, 82, paint(lit or '#C9CED6'))
        cv.drawCircle(x, y, 82, paint('#2A2E34', style='stroke', width=8))
        text(cv, str(n), x, y + 32, 90, '#FFFFFF' if lit else '#2A2E34')
    shade(cv, (540, 700), 1100, 0.6)


def shot_MIRROR(cv, t):
    """He faces the dark steel wall; his reflection smiles. He doesn't."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#141A21'))
    cv.drawRect(skia.Rect(40, 160, 1040, 1800), paint('#1E262F', shader=lin((40, 0), (1040, 0), [C('#232C36'), C('#161C23')])))
    for y in range(160, 1800, 7):                                # brushed steel
        cv.drawLine(40, y, 1040, y, paint(C('#FFFFFF', 0.018), style='stroke', width=2))
    cv.drawRect(skia.Rect(40, 1130, 1040, 1150), paint('#7D8895'))           # handrail
    # the reflection: front view, cold, darker, behind "glass"
    smile = keys(t, [(T.T_SMILE - 0.1, 0.0), (T.T_SMILE + 0.6, 1.0)])
    cv.saveLayer(None, skia.Paint(Alphaf=0.9, ColorFilter=skia.ColorFilters.Blend(C('#3A5A80', 0.45).toColor(), skia.BlendMode.kMultiply)))
    mascot(cv, 760, 2050, 1.3, look=(0.0, 0.0), brow=1.0 - 1.3 * smile, lids=0.05 + 0.35 * smile, pupil=0.75,
           mouth='smirk' if smile > 0.15 else 'o', light_side=-1, rim='#9FC3FF', rim_a=0.4, arm_l=(3, 0), arm_r=(3, 0),
           head_tilt=4 * smile)
    cv.restore()
    cv.drawRect(skia.Rect(40, 160, 1040, 1800), paint(C('#9FC3FF', 0.05)))    # sheen
    cv.drawPath(poly([(40, 160), (380, 160), (40, 900)]), paint(C('#FFFFFF', 0.04)))
    # him, back view, frozen, foreground left
    mascot(cv, 250, 2700, 1.75, view='back', light_side=1, rim='#9FC3FF', rim_a=0.5, arm_l=(3, 0), arm_r=(3, 0))
    glow(cv, (540, 0), 900, '#BFD6FF', 0.15)
    shade(cv, (600, 800), 1200, 0.65)


SHOTS = {'DISP': shot_DISP, 'DISP2': shot_DISP, 'ELEV': shot_ELEV, 'FACE': shot_FACE, 'OUT': shot_OUT, 'TRACK': shot_TRACK,
         'PHOTO': shot_PHOTO, 'EYES': shot_EYES, 'HALL': shot_HALL, 'DOORSIDE': shot_DOORSIDE, 'LONG': shot_LONG, 'OTS': shot_OTS,
         'DOUBLE': shot_DOUBLE, 'IN': shot_IN, 'BTN': shot_BTN, 'MIRROR': shot_MIRROR}


def needed():
    """(job, frame) pairs the EDL shows."""
    out = []
    for s in E.SEGMENTS:
        if s['src'] is None:
            continue
        f0, f1 = int(round(s['t0'] * FPS)), int(round(s['t1'] * FPS))
        out += [(s['src'], f) for f in range(f0, f1 + 1)]
    return sorted(set(out))


def draw(job_frame):
    job, f = job_frame
    p = os.path.join(OUT, job, f'{f:04d}.png')
    if os.path.exists(p):
        return
    surf = skia.Surface(W, H)
    cv = surf.getCanvas()
    SHOTS[job](cv, f / FPS)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    surf.makeImageSnapshot().save(p, skia.kPNG)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', default='')
    ap.add_argument('--procs', type=int, default=4)
    ap.add_argument('--still', nargs='*', default=None, help='JOB:frame ... -> OUT dir is --out')
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    OUT = a.out
    if a.still:
        todo = [(s.split(':')[0], int(s.split(':')[1])) for s in a.still]
    else:
        todo = needed()
        if a.jobs:
            js = set(a.jobs.split(','))
            todo = [x for x in todo if x[0] in js]
    with Pool(a.procs) as pool:
        for i, _ in enumerate(pool.imap_unordered(draw, todo, chunksize=4)):
            if i % 100 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
