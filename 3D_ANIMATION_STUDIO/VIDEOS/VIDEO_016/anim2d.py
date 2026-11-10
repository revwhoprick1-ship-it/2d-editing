#!/usr/bin/env python3
"""VIDEO_016 "The Forest That Eats People" — real 2D horror (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_016/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]

Lighting by place: forest = cold blue-green moonlight + fog + light shafts; house = weak warm tungsten, flickering;
the Mimic = hard rim light; edge of the forest = open moonlit field (the brightest place: you can see the shadows).
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
from flat import C, H, W, blob, glow, lin, mascot, mimic, paint, poly, rad, shade  # noqa
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video016 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
MOON = '#9FD0C8'          # blue-green moonlight
TUNG = '#FFC27A'          # weak tungsten

CAST = {
    'M': dict(),
    'B': dict(glasses='#22262C', hair='#3A2A1A', hair_sh='#24180E', shirt='#2A7A7A', shirt_sh='#1E5C5C'),
    'L': dict(hair='#1A1A1A', hair_sh='#0A0A0A', shirt='#6A4A8A', shirt_sh='#50366A', skin='#8E5A3C', skin_sh='#6E432C'),
    'K': dict(hair='#E8C060', hair_sh='#C09A40', shirt='#D8B020', shirt_sh='#A88618', skin='#F5D0B0', skin_sh='#D9AE8C', blush=0.3),
    'J': dict(belly=1.35, hair='#1A1A1A', hair_sh='#0A0A0A', shirt='#3E5A3E', shirt_sh='#2C422C', skin='#6E4A30', skin_sh='#543622'),
}
SPEAK = {'M': ('M',), 'B': ('B',), 'L': ('L',), 'K': ('K',), 'J': ('J',)}


def talk(t, who):
    return mouth_open(t, WORDS, [l['id'] for l in E._T['lines'] if l['id'][0] == who])


def mood(t):
    """Story-wide emotional state."""
    if t < B['bones']:
        return 'calm'
    if t < B['chase']:
        return 'scared'
    if t < B['edge']:
        return 'terror'
    return 'tired'


def face_pose(who, t):
    m = mood(t)
    P = dict(CAST[who])
    o = talk(t, who)
    P['mouth_open'] = o
    if m == 'calm':
        P.update(brow={'K': -0.1, 'L': 0.3, 'B': 0.2, 'J': -0.2, 'M': 0.1}[who], mouth='smile' if who == 'K' else 'flat')
    elif m == 'scared':
        P.update(brow=1.0, mouth='o', pupil=0.75, sweat=who != 'K' or t > B['help'])
    elif m == 'terror':
        P.update(brow=1.0, mouth='open', pupil=0.5, sweat=True)
    else:
        P.update(brow=0.6, mouth='o', lids=0.25, sweat=True)
    if o > 0 and P.get('mouth') in ('flat', 'smile', 'o'):
        P['mouth'] = 'open'
    P['lids'] = max(P.get('lids', 0.0), blink(t, [k * 3.7 + hash(who) % 3 for k in range(60)]))
    return P


# ===================================================================== places
def forest(cv, t, cam_x=0.0, fog=0.5, depth=1.0, twisted=True, dead=False, shafts=True):
    """Moonlit forest in layers (parallax by cam_x): far trees, mid trees, near trunks; light shafts; fog."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0A1418', shader=lin((0, 0), (0, H), [C('#0C1A1E'), C('#06100F')])))
    glow(cv, (760, 260), 500, MOON, 0.35)
    cv.drawCircle(760, 260, 70, paint('#DDEFEA'))
    for layer, (col, n, base, wid, par) in enumerate((('#10221F', 9, 1250, 60, 0.2), ('#0C1A18', 7, 1400, 95, 0.5), ('#070E0D', 4, 1700, 170, 1.0))):
        for k in range(n):
            x = ((k * 263 + layer * 97 - cam_x * par * 300) % (W + 400)) - 200
            sway = 6 * math.sin(t * 0.7 + k + layer)
            top = -100
            if twisted:
                pts = [(x - wid / 2, base + 300), (x - wid / 2 + 40 * math.sin(k), base - 300), (x - wid / 2 - 30 + sway, base - 700),
                       (x - wid / 2 + 20 + sway, top), (x + wid / 2 + 20 + sway, top), (x + wid / 2 - 30 + sway, base - 700),
                       (x + wid / 2 + 40 * math.sin(k), base - 300), (x + wid / 2, base + 300)]
            else:
                pts = [(x - wid / 2, base + 300), (x - wid / 2, top), (x + wid / 2, top), (x + wid / 2, base + 300)]
            cv.drawPath(poly(pts), paint(col if not dead else '#1A1A18'))
            for bb in range(3):                                                  # bare, crooked branches
                by = base - 900 - bb * 220
                d = 1 if (k + bb) % 2 else -1
                cv.drawPath(poly([(x, by), (x + d * (120 + 40 * layer), by - 90), (x + d * (200 + 60 * layer), by - 60)], closed=False),
                            paint(col, style='stroke', width=8 + 6 * layer))
    cv.drawRect(skia.Rect(0, 1500, W, H), paint('#0E1A16', shader=lin((0, 1500), (0, H), [C('#0E1A16'), C('#1A2A22')])))
    if shafts:
        for k in range(3):                                                       # light shafts between the trees
            x = 200 + k * 330 - cam_x * 60
            cv.drawPath(poly([(x, 0), (x + 70, 0), (x + 260, 1800), (x + 80, 1800)]), paint(C(MOON, 0.07), blur=24))
    for k in range(6):                                                           # drifting ground fog
        x = ((t * 25 + k * 260 - cam_x * 200) % 1500) - 250
        cv.drawOval(skia.Rect(x - 300, 1350 + k * 70, x + 300, 1550 + k * 70), paint(C('#AFC8C2', 0.10 * fog * 2), blur=40))


def leaves(cv, n=40, seed=0):
    for k in range(n):
        x = (k * 137 + seed * 31) % W
        y = 1560 + (k * 53) % 360
        cv.drawOval(skia.Rect(x - 14, y - 6, x + 14, y + 6), paint(C(['#3A2A18', '#4A3420', '#2A2010'][k % 3], 0.9)))


def group_walk(cv, t, order='KLBJM', y0=1900, s=0.46, walking=True, mood_=None, spread=205, views=None, bob_=True, xs=None):
    xs = xs or [540 + (i - 2) * spread for i in range(5)]
    for i, who in enumerate(order):
        P = face_pose(who, t)
        if mood_:
            P.update(mood_)
        ph = ((t * 0.9) + i * 0.27) % 1 if walking else None
        v = (views or {}).get(who, 'front')
        yy = y0 + (i % 2) * 50
        mascot(cv, xs[i], yy, s * (0.94 if i % 2 == 0 else 1.0) * (1.25 if who == 'J' else 1.0) * (0.92 if who == 'B' else 1.0), walk=ph, view=v, light_side=1, rim=MOON,
               rim_a=0.5, **P)


def house_room(cv, t, lit=1.0):
    """Inside: warm, weak tungsten from one bulb; dark corners; peeling wallpaper."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#120C08'))
    cv.drawRect(skia.Rect(0, 0, W, 1350), paint('#3A2A1E', shader=lin((0, 0), (0, 1350), [C('#24180F'), C('#4A3626')])))
    for x in range(0, W, 140):
        cv.drawRect(skia.Rect(x, 0, x + 6, 1350), paint(C('#2A1C12', 0.8)))
    cv.drawRect(skia.Rect(0, 1350, W, H), paint('#2A1E14', shader=lin((0, 1350), (0, H), [C('#20160E'), C('#34261A')])))
    for k in range(9):
        cv.drawLine(0, 1400 + k * 60, W, 1420 + k * 60, paint(C('#1A120A', 0.8), style='stroke', width=3))
    cv.drawLine(540, 0, 540, 200, paint('#100A06', style='stroke', width=5))
    cv.drawCircle(540, 214, 22, paint(C('#FFE6B0', 0.3 + 0.7 * lit)))
    glow(cv, (540, 240), 1100, TUNG, 0.38 * lit)


def table(cv, t, plates=5):
    cv.drawRect(skia.Rect(80, 1300, 1000, 1360), paint('#4A3020'))
    cv.drawRect(skia.Rect(110, 1360, 970, 1700), paint('#2E1E14'))
    for k in range(plates):
        x = 180 + k * 180
        cv.drawOval(skia.Rect(x - 70, 1285, x + 70, 1325), paint('#E8E2D4'))
        cv.drawRect(skia.Rect(x + 50, 1230, x + 76, 1300), paint(C('#C8D8E0', 0.6)))


# ===================================================================== shots
def shot_HOOK(cv, t):
    """ECU: Ken, drenched in sweat. Something tall stands in the dark behind him. He slowly turns his head."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#05090A'))
    glow(cv, (300, 200), 900, MOON, 0.2)
    turn = keys(t, [(0.0, 0.0), (1.0, 0.0), (B['hookcut'] - 0.2, -0.9)])
    cv.save()                                                                      # the figure behind, mostly darkness, a sliver of smile
    mimic(cv, 860, 3600, 1.15, t=t, tilt=55, grin=1.0, look=(-1, 0), rim=MOON, rim_a=0.35)
    cv.restore()
    dim(cv, 0.35)
    P = dict(CAST['K'], brow=1.0, mouth='o', mouth_open=0.2 + 0.1 * math.sin(t * 9), pupil=0.45, sweat=True, look=(-0.9 * turn, 0.0),
             head_turn=-0.7 * turn)
    mascot(cv, 430 + 4 * math.sin(t * 31), 2850, 2.1, light_side=-1, rim=MOON, rim_a=0.7, **P)
    for k in range(5):                                                             # sweat running
        y = 700 + ((t * 300 + k * 120) % 600)
        cv.drawPath(blob([(330 + k * 70, y), (342 + k * 70, y + 30), (330 + k * 70, y + 44), (318 + k * 70, y + 30)]), paint(C('#BFE3FF', 0.8)))
    shade(cv, (430, 900), 1000, 0.6)


def shot_ENTER(cv, t):
    """Wide: the five walking into the forest toward us; no birds, no insects; twisted trees."""
    forest(cv, t, cam_x=t * 0.15)
    group_walk(cv, t)
    leaves(cv)
    shade(cv, (540, 1100), 1300, 0.5)


def cu_bg(cv, t, place):
    if place == 'forest':
        forest(cv, t, cam_x=0.4, fog=0.4, shafts=False)
        dim(cv, 0.25)
    elif place == 'house':
        house_room(cv, t, lit=flicker(t, 3, 7.0, 0.55) if t >= B['knock'] else 1.0)
    else:
        edge_bg(cv, t)


def place_at(t):
    if t < B['dining']:
        return 'forest'
    if t < B['exit']:
        return 'house'
    if t < B['edge']:
        return 'forest'
    return 'edge'


def make_cu(who):
    def shot(cv, t):
        pl = place_at(t)
        cu_bg(cv, t, pl)
        P = face_pose(who, t)
        if who == 'K' and t >= B['twist']:                                       # the final twist: Ken's smile stretches
            u = t - B['twist']
            P.update(mouth='wide', brow=-0.3, pupil=0.4, head_tilt=min(28.0, u * 12), lids=0.0, void_eyes=u > 2.2, mouth_open=0.0)
        rimc = MOON if pl != 'house' else TUNG
        sz = 2.05 if who != 'J' else 1.9
        shake_ = 5 * math.sin(t * 41) if mood(t) == 'terror' else 0
        mascot(cv, 540 + shake_, 2760, sz, light_side=1 if pl == 'house' else -1, rim=rimc, rim_a=0.55, look=(0.3 * math.sin(t * 0.8 + len(who)), 0.0), **P)
        shade(cv, (540, 950), 1100, 0.55)
    return shot


def shot_FORK(cv, t):
    """Two paths. Left: ordinary. Right: dead trees, and the sign. The group from behind."""
    forest(cv, t, cam_x=0.2)
    cv.drawPath(poly([(160, 1920), (420, 1500), (480, 1500), (380, 1920)]), paint('#2A2618'))
    cv.drawPath(poly([(700, 1920), (600, 1500), (660, 1500), (980, 1920)]), paint('#1E1A14'))
    cv.drawRect(skia.Rect(620, 900, 980, 1500), paint(C('#1A1A16', 0.85)))                       # dead grove on the right
    cv.drawRect(skia.Rect(780, 1180, 800, 1560), paint('#3A2A1A'))                                 # the sign
    cv.drawRect(skia.Rect(660, 1080, 940, 1260), paint('#5A4028'))
    text(cv, 'DO NOT ENTER', 800, 1150, 44, '#C8C0A8')
    text(cv, 'TURN BACK', 800, 1220, 40, '#C83030')
    group_walk(cv, t, y0=2080, s=0.5, walking=False, views={w: 'back' for w in 'KLBJM'}, xs=[90, 260, 430, 140, 330])
    shade(cv, (540, 1100), 1300, 0.5)


def shot_SIGN(cv, t):
    forest(cv, t, cam_x=0.6, shafts=False)
    dim(cv, 0.3)
    cv.drawRect(skia.Rect(520, 1200, 560, H), paint('#3A2A1A'))
    cv.drawRect(skia.Rect(90, 500, 990, 1260), paint('#5A4028', shader=lin((90, 500), (990, 1260), [C('#6A4A2E'), C('#4A3220')])))
    for k in range(8):
        cv.drawLine(90, 560 + k * 90, 990, 560 + k * 90, paint(C('#3A2818', 0.8), style='stroke', width=4))
    text(cv, 'DO NOT ENTER.', 540, 720, 120, '#D8D0B8')
    text(cv, 'TURN BACK', 540, 900, 110, '#C83030')
    text(cv, 'WHILE YOU CAN.', 540, 1060, 100, '#C83030')
    for k in range(14):                                                                         # desperate scratches
        x = 160 + (k * 61) % 760
        y = 560 + (k * 97) % 640
        for j in range(4):
            cv.drawLine(x + j * 14, y, x + j * 14 + 40, y + 120, paint(C('#2A1A0E', 0.9), style='stroke', width=5))
    glow(cv, (300, 400), 800, MOON, 0.2)
    shade(cv, (540, 900), 1100, 0.5)


def shot_BONES(cv, t):
    """A clearing: bones and a half-buried skull. A slow pan right... and for a few frames a tall shape between two trees."""
    pan = (t - B['bones']) * 0.12
    forest(cv, t, cam_x=0.8 + pan, fog=0.7)
    for k in range(12):
        x, y = 300 + (k * 173) % 480, 1300 + (k * 89) % 200
        cv.save(); cv.rotate((k * 47) % 180, x, y)
        cv.drawRect(skia.Rect(x - 50, y - 8, x + 50, y + 8), paint('#D8D0BC'))
        cv.drawCircle(x - 50, y, 13, paint('#D8D0BC')); cv.drawCircle(x + 50, y, 13, paint('#D8D0BC'))
        cv.restore()
    sx, sy = 540, 1380                                                                          # the skull, half in the dirt
    cv.drawPath(blob([(sx - 90, sy), (sx - 80, sy - 110), (sx, sy - 150), (sx + 80, sy - 110), (sx + 90, sy)]), paint('#E4DCC8'))
    for side in (-1, 1):
        cv.drawOval(skia.Rect(sx + side * 40 - 26, sy - 90, sx + side * 40 + 26, sy - 50), paint('#1A1410'))
    cv.drawRect(skia.Rect(sx - 110, sy, sx + 110, sy + 40), paint('#0E1A16'))
    if B['figure'] <= t < B['figure'] + 0.35:                                                 # nobody notices
        mimic(cv, 900, 1520, 0.36, t=t, tilt=40, grin=1.0, rim=MOON, rim_a=0.4)
    group_walk(cv, t, y0=1960, s=0.44, walking=False, xs=[100, 260, 820, 980, 540])
    shade(cv, (540, 1100), 1300, 0.5)


def shot_TREES(cv, t):
    """The mascot's POV, turning: just trees. Nothing there."""
    forest(cv, t, cam_x=1.5 + (t - B['turn']) * 0.6, fog=0.8)
    shade(cv, (540, 1000), 1100, 0.6)


def shot_HOUSE(cv, t):
    """The old house in the fog: broken windows, the door ajar. Moonlight; no light inside."""
    forest(cv, t, cam_x=2.5, fog=0.9, shafts=True)
    hx0, hx1, hy = 160, 920, 1500
    cv.drawRect(skia.Rect(hx0, 800, hx1, hy), paint('#1E1A16'))
    cv.drawPath(poly([(hx0 - 60, 820), (540, 440), (hx1 + 60, 820)]), paint('#15120F'))
    for x, y in ((250, 940), (700, 940)):
        cv.drawRect(skia.Rect(x, y, x + 140, y + 160), paint('#05070A'))
        cv.drawPath(poly([(x, y), (x + 70, y + 60), (x + 30, y + 160)]), paint(C('#5A6A6A', 0.4)))      # broken glass
    cv.drawRect(skia.Rect(470, 1150, 610, 1500), paint('#05070A'))
    cv.drawRect(skia.Rect(470, 1150, 560, 1500), paint('#2A2018'))                                 # door ajar
    cv.drawRect(skia.Rect(hx0, 800, hx1, hy), paint(C(MOON, 0.06)))
    group_walk(cv, t, walking=t < B['house_in'] - 1.5, views={w: 'back' for w in 'KLBJM'}, s=0.4, y0=2080, xs=[110, 280, 800, 970, 540])
    shade(cv, (540, 1100), 1300, 0.5)


def shot_DINING(cv, t):
    """Inside: a table set for five. Five plates, five glasses. The group around it."""
    house_room(cv, t)
    for k, who in enumerate('BJKLM'):
        x = 150 + k * 195
        P = face_pose(who, t)
        mascot(cv, x, 1560, 0.46 * (1.15 if who == 'J' else 1.0), light_side=1, rim=TUNG, rim_a=0.4, legs=False, **P)
    table(cv, t)
    shade(cv, (540, 1000), 1250, 0.55)


def shot_WALL(cv, t):
    """A slow pan along the wall: WELCOME BACK, written in something dark."""
    house_room(cv, t, lit=0.8)
    a = ease((t - B['wall']) / 1.0)
    cv.save(); cv.rotate(-3, 540, 800)
    text(cv, 'WELCOME', 540, 720, 190, C('#5A0E0E', 0.9 * a), skew=-0.1)
    text(cv, 'BACK.', 540, 920, 190, C('#5A0E0E', 0.9 * a), skew=-0.1)
    for k in range(9):                                                                          # drips
        x = 200 + k * 85
        cv.drawLine(x, 940, x, 940 + (k % 4) * 60 * a, paint(C('#5A0E0E', 0.8 * a), style='stroke', width=8))
    cv.restore()
    shade(cv, (540, 800), 1000, 0.6)


def shot_DOOR(cv, t):
    """The front door from inside. Three knocks. The handle turns: slowly, then violently. The group's backs."""
    house_room(cv, t, lit=flicker(t, 4, 7.0, 0.5) if t >= B['handle'] else 1.0)
    jolt = 0
    for k0 in B['knocks']:
        if k0 <= t < k0 + 0.12:
            jolt = 8
    cv.drawRect(skia.Rect(330 + jolt, 420, 750 + jolt, 1500), paint('#3A2618'))
    for r in range(3):
        cv.drawRect(skia.Rect(380 + jolt, 500 + r * 330, 700 + jolt, 780 + r * 330), paint('#2E1E12', style='stroke', width=10))
    hang = 0.0
    if t >= B['handle']:
        u = t - B['handle']
        hang = -35 * min(1.0, u / 1.5) + (18 * math.sin(u * 30) if u > 1.5 else 0)
    cv.save(); cv.translate(700 + jolt, 1000); cv.rotate(hang)
    cv.drawRect(skia.Rect(-10, -12, 90, 12), paint('#B9A27A'))
    cv.restore()
    cv.drawCircle(700 + jolt, 1000, 22, paint('#8E7A56'))
    cv.drawRect(skia.Rect(340, 1490, 740, 1505), paint(C(MOON, 0.7)))
    if t >= B['knocks'][0]:
        for x in (450, 600):
            cv.drawRect(skia.Rect(x, 1490, x + 60, 1505), paint('#000000'))
    for i, who in enumerate('JK'):
        mascot(cv, (120, 960)[i], 2600, 0.85 * (1.15 if who == 'J' else 1.0), view='back', light_side=1, rim=TUNG, rim_a=0.4, **CAST[who])
    if t >= B['dark'] and t < B['reveal']:
        dim(cv, 0.97)
    shade(cv, (540, 1000), 1200, 0.55)


def shot_HALL(cv, t):
    """Lights back: at the end of the hallway, IT. Low angle, hard rim light. It tilts its head."""
    cam = Cam(0.0, eye=0.7, vy=1150)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#0C0806'))
    for x0, c0 in ((-1.2, '#2E2016'), (1.2, '#281C12')):
        cv.drawPath(quad(cam, [(x0, 0, 0.5), (x0, 0, 9), (x0, 2.8, 9), (x0, 2.8, 0.5)]), paint(c0))
    cv.drawPath(quad(cam, [(-1.2, 0, 0.5), (1.2, 0, 0.5), (1.2, 0, 9), (-1.2, 0, 9)]), paint('#1E140C'))
    cv.drawPath(quad(cam, [(-1.2, 2.8, 0.5), (1.2, 2.8, 0.5), (1.2, 2.8, 9), (-1.2, 2.8, 9)]), paint('#0A0604'))
    lt = flicker(t, 9, 8.0, 0.2)
    p = cam.p(0, 2.75, 8.0)
    glow(cv, p, 900, TUNG, 0.45 * lt)
    tilt = keys(t, [(B['reveal'], 20.0), (B['reveal'] + 1.2, 20.0), (B['x05'], 75.0)])
    z = 8.0 - (max(0.0, t - B['rush']) * 14 if t >= B['rush'] else 0)
    z = max(1.2, z)
    fx, fy = cam.p(0, 0, z)
    mimic(cv, fx, fy, cam.scale(z, 2.6) * 1150 / 2600, t=t, tilt=tilt, grin=1.0, reach=0.9 if t >= B['rush'] else 0.0,
          run=((t * 2.5) % 1) if t >= B['rush'] else None, look=(0, 0.2), rim=TUNG, rim_a=0.7)
    dim(cv, (1 - lt) * 0.6)
    shade(cv, (540, 1000), 1100, 0.5)


def shot_CHASE(cv, t):
    """Side-scroll: all five running through the forest at night; it lopes behind them, far too fast."""
    u = t - B['chase']
    forest(cv, t, cam_x=u * 3.0, fog=0.5)
    leaves(cv, 30, int(u * 10))
    for i, who in enumerate('MBLJK'):
        x = 1000 - i * 175 + 20 * math.sin(t * 3 + i)
        P = face_pose(who, t)
        mascot(cv, x, 1800 + (i % 2) * 50, 0.42 * (1.2 if who == 'J' else 1.0), view='side', face=1, walk=(t * 2.8 + i * 0.3) % 1, run=True,
               light_side=1, rim=MOON, rim_a=0.6, **P)
    gap = max(-120.0, 80 - u * 40)
    mimic(cv, gap, 1840, 0.42, t=t, tilt=30, grin=1.0, run=(t * 2.2) % 1, reach=1.0, rim=MOON, rim_a=0.5)
    shade(cv, (600, 1100), 1250, 0.5)


def shot_EXIT(cv, t):
    """The side door bursts open into the forest: they pour out."""
    house_room(cv, t, lit=flicker(t, 2, 10.0, 0.2))
    o = ease((t - B['exit']) / 0.3)
    cv.drawRect(skia.Rect(260, 380, 820, 1500), paint('#0A1418'))
    forest(cv, t, cam_x=3.0) if False else None
    glow(cv, (540, 900), 500, MOON, 0.35 * o)
    cv.save(); cv.translate(260, 0); cv.scale(1 - 0.85 * o, 1)
    cv.drawRect(skia.Rect(0, 380, 560, 1500), paint('#3A2618'))
    cv.restore()
    for i, who in enumerate('MBLJ'):
        u = min(1.5, t - B['exit'])
        x = 540 + (i - 1.5) * 150 * (1 - 0.3 * u / 1.5)
        mascot(cv, x, 1720 + i * 30 - u * 120, 0.5 * (1 - 0.35 * u / 1.5), view='back', walk=(t * 2.8 + i * 0.3) % 1, run=True, light_side=1, rim=MOON,
               rim_a=0.5, **CAST[who])
    shade(cv, (540, 1000), 1200, 0.5)


def edge_bg(cv, t):
    """The forest edge: an open field under a big moon (the brightest place in the episode)."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A2A30', shader=lin((0, 0), (0, 1300), [C('#14222A'), C('#2E4448')])))
    glow(cv, (300, 300), 600, '#E8F4F0', 0.5)
    cv.drawCircle(300, 300, 110, paint('#EEF6F2'))
    for k in range(12):
        x = k * 100
        cv.drawPath(poly([(x - 60, 1300), (x, 1050 - (k % 3) * 60), (x + 60, 1300)]), paint('#0A1214'))
    cv.drawRect(skia.Rect(0, 1300, W, H), paint('#2A3A30', shader=lin((0, 1300), (0, H), [C('#22322A'), C('#3A4A3A')])))


def shot_EDGE(cv, t):
    """They stumble out into the field. Exhausted. Counting heads."""
    edge_bg(cv, t)
    for i, who in enumerate('LJBKM'):
        P = face_pose(who, t)
        crouch = 0.35 if who in 'LB' else 0.0
        mascot(cv, 120 + i * 210, 1860 + (i % 2) * 40, 0.47 * (1.2 if who == 'J' else 1.0), crouch=crouch, light_side=-1, rim='#E8F4F0', rim_a=0.6,
               **P)
    shade(cv, (540, 1100), 1300, 0.4)


def shot_SHADOWS(cv, t):
    """Low and close on the grass: five long moon-shadows... and one of them is facing the wrong way."""
    edge_bg(cv, t)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.15)))
    for i in range(5):
        x = 140 + i * 200
        wrong = i == 3                                                                            # Ken
        sk = skia.Path()
        dx = -1 if not wrong else 1
        sk.moveTo(x - 40, 1500); sk.lineTo(x + 40, 1500); sk.lineTo(x + dx * 380 + 30, 1900); sk.lineTo(x + dx * 380 - 50, 1900); sk.close()
        cv.drawPath(sk, paint(C('#05080A', 0.75), blur=6))
        if wrong:
            cv.drawCircle(x + dx * 360, 1880, 50, paint(C('#05080A', 0.75), blur=6))
            cv.drawPath(blob([(x + 280, 1820), (x + 330, 1790), (x + 380, 1830)]), paint(C('#6A1414', 0.0)))
        for side in (-1, 1):                                                                     # the five pairs of feet
            cv.drawOval(skia.Rect(x + side * 22 - 26, 1480, x + side * 22 + 26, 1510), paint('#1A1A1A' if i != 3 else '#2A2A2A'))
    shade(cv, (540, 1300), 1100, 0.4)


def shot_TITLE(cv, t):
    forest(cv, t, cam_x=0.0, fog=1.0)
    dim(cv, 0.35)
    shade(cv, (540, 900), 1100, 0.6)


SHOTS = {'HOOK': shot_HOOK, 'ENTER': shot_ENTER, 'FORK': shot_FORK, 'SIGN': shot_SIGN, 'BONES': shot_BONES, 'TREES': shot_TREES,
         'HOUSE': shot_HOUSE, 'DINING': shot_DINING, 'WALL': shot_WALL, 'DOOR': shot_DOOR, 'HALL': shot_HALL, 'CHASE': shot_CHASE,
         'EXIT': shot_EXIT, 'EDGE': shot_EDGE, 'SHADOWS': shot_SHADOWS, 'TITLE': shot_TITLE}
for _w in 'MBLKJ':
    SHOTS['CU_' + _w] = make_cu(_w)


def needed():
    out = []
    for sgm in E.SEGMENTS:
        if sgm['src'] is None:
            continue
        f0, f1 = int(round(sgm['t0'] * FPS)), int(round(sgm['t1'] * FPS))
        out += [(sgm['src'], f) for f in range(f0, f1 + 1)]
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
    ap.add_argument('--still', nargs='*', default=None)
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    OUT = a.out
    if a.still:
        todo = [(x.split(':')[0], int(x.split(':')[1])) for x in a.still]
    else:
        todo = needed()
        if a.jobs:
            js = set(a.jobs.split(','))
            todo = [x for x in todo if x[0] in js]
    with Pool(a.procs) as pool:
        for i, _ in enumerate(pool.imap_unordered(draw, todo, chunksize=4)):
            if i % 400 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
