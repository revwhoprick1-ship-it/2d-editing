#!/usr/bin/env python3
"""VIDEO_009 "They Knock · Part 1" — real 2D animation (2dEDIT), flat vector drawn with Skia.

    python3 VIDEOS/VIDEO_009/anim2d.py [--jobs A,B] [--still JOB:frame ...] [--out DIR] [--procs 4]
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
from kit import Cam, blink, dim, ease, flicker, keys, mouth_open, quad, ramp, text  # noqa
import edit_video009 as E  # noqa

FPS = 30
OUT = os.path.join(HERE, 'frames2d')
B, LS, WORDS = E.B, E.LS, E.WORDS
DAY = '#B8C6D4'          # cold overcast daylight from the windows

BOB = dict(belly=1.35, shirt='#3E7A3E', shirt_sh='#2C5A2C', hair='#1A1A1A', hair_sh='#0A0A0A', skin='#8E5A3C', skin_sh='#6E432C')
LAW = dict(glasses='#22262C', shirt='#8FB4D8', shirt_sh='#6A8EB0', hair='#E0C080', hair_sh='#C0A060', skin='#F5D0B0', skin_sh='#D9AE8C')
JUS = dict(shirt='#C83030', shirt_sh='#9A2222', hair='#5A3A1A', hair_sh='#3A2410')
ZOMBIE = dict(skin='#9AAE94', skin_sh='#7A8E74', iris='#B01E1E', zombie=True, shirt='#5A5A60', shirt_sh='#404046', pants='#2A2E36',
              pants_sh='#1E2228', brow=-0.6, pupil=0.6)
ZHAIR = [('#2A1A10', '#1A100A'), ('#8A8A8A', '#6A6A6A'), ('#C26A2A', '#9A521E'), ('#1A1A1A', '#0A0A0A'), ('#D9B06A', '#B38C4E')]
PETERSON = dict(ZOMBIE, shirt='#C9C2AE', shirt_sh='#A8A08C', hair='#6A6A6A', hair_sh='#4A4A4A', mustache='#5A5A5A', glasses='#22262C')


def talk(t, *lines):
    return mouth_open(t, WORDS, lines)


def knocking(t):
    """Knock impulses: the hook (on 'knock' x2) and again at the very end (-> loop)."""
    for k0 in (B['knock'], B['again'] + 0.3):
        for d in (0.0, 0.35):
            if k0 + d <= t < k0 + d + 0.12:
                return 1 - (t - k0 - d) / 0.12
    return 0.0


# ===================================================================== room 204
def classroom_bg(cv, t, lights=1.0):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1C232B'))
    cv.drawRect(skia.Rect(0, 0, W, 1300), paint('#3A4148', shader=lin((0, 0), (0, 1300), [C('#2A3036'), C('#454C53')])))
    cv.drawRect(skia.Rect(120, 330, 960, 820), paint('#1E3A2C'))                      # chalkboard
    cv.drawRect(skia.Rect(110, 320, 970, 830), paint('#6A4A2E', style='stroke', width=16))
    text(cv, 'QUIZ FRIDAY', 330, 470, 62, '#D8D8D0', alpha=0.7, bold=False)
    text(cv, 'DONT OPEN', 640, 640, 92, '#E8E0D0', alpha=0.85, skew=-0.2)
    cv.drawLine(420, 670, 870, 655, paint(C('#E8E0D0', 0.8), style='stroke', width=8))
    cv.drawRect(skia.Rect(0, 1300, W, H), paint('#2E2A26', shader=lin((0, 1300), (0, H), [C('#2A2622'), C('#3A342E')])))
    for x in range(0, W, 120):
        cv.drawLine(x, 1300, x - 300, H, paint(C('#1E1A16', 0.6), style='stroke', width=3))
    glow(cv, (0, 700), 900, DAY, 0.25)                                                 # window light from the left
    cv.drawPath(poly([(0, 1300), (420, 1300), (700, H), (0, H)]), paint(C(DAY, 0.07), blur=12))


def desk(cv, x, y, s=1.0, rot=0):
    cv.save(); cv.translate(x, y); cv.rotate(rot); cv.scale(s, s)
    cv.drawRect(skia.Rect(-150, -20, 150, 10), paint('#B08A5A'))
    cv.drawRect(skia.Rect(-140, 10, -126, 220), paint('#5A626C'))
    cv.drawRect(skia.Rect(126, 10, 140, 220), paint('#5A626C'))
    cv.restore()


def kid(cv, who, x, y, s, **pose):
    base = {'you': {}, 'bob': BOB, 'law': LAW, 'jus': JUS}[who]
    P = dict(base)
    P.update(pose)
    mascot(cv, x, y, s, light_side=-1, rim=DAY, rim_a=0.4, **P)


def shot_WIDE(cv, t):
    classroom_bg(cv, t)
    late = t >= B['choice']
    scared = dict(brow=1.0, mouth='o', pupil=0.65, sweat=True)
    look_door = (-0.8, 0.0) if not late else (0.0, 0.0)
    # the four of you
    kid(cv, 'bob', 300, 1720, 0.55, look=look_door, **dict(scared, mouth='flat'))
    kid(cv, 'law', 560, 1640, 0.5, look=look_door, **scared)
    kid(cv, 'jus', 820, 1720, 0.55, look=look_door, arm_r=(150, 10), **scared)
    if not late:
        kid(cv, 'you', 540, 2520, 1.0, view='back')
    else:
        kid(cv, 'you', 540, 2520, 1.0, view='back', head_tilt=-6)
    # hockey stick in Justin's raised hand
    cv.drawLine(900, 1080, 980, 700, paint('#3A2A1A', style='stroke', width=14))
    # barricade (left): desks piled against the door
    for k, (dx, dy, r) in enumerate(((60, 1500, -8), (120, 1380, 12), (40, 1260, -20))):
        desk(cv, dx, dy, 0.9, r)
    glow(cv, (540, 0), 1000, DAY, 0.1 * flicker(t, 2, 4.0, 0.6))
    shade(cv, (560, 1200), 1250, 0.6)


def door_bg(cv, t):
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#30373E'))
    k = knocking(t)
    jx = 6 * k
    cv.drawRect(skia.Rect(240 + jx, 260, 840 + jx, 1640), paint('#5A3E28'))
    cv.drawRect(skia.Rect(220, 240, 860, 260), paint('#3A2A1C'))
    win = skia.Rect(380 + jx, 380, 700 + jx, 860)
    cv.drawRect(win, paint('#7C8794'))
    text(cv, '204', 540 + jx, 1000, 80, '#E8E0D0')
    cv.drawCircle(780 + jx, 1050, 26, paint('#B9A27A'))
    # the shape behind the glass
    present = t < B['flash'] or (B['door2'] <= t < B['l1']) or t >= B['again'] or (B['stops'] <= t < B['stops'] + 0.6)
    if present:
        cv.save(); cv.clipRect(win)
        lean = 10 * math.sin(t * 0.8) if t < B['stops'] else 0
        cv.drawPath(blob([(470 + lean, 860), (480 + lean, 560), (540 + lean, 470), (600 + lean, 560), (610 + lean, 860)]), paint(C('#15181C', 0.85), blur=10))
        if B['door2'] <= t < B['l1']:                                                  # it presses its face to the glass
            cv.drawCircle(512 + lean, 560, 9, paint(C('#E8E0D0', 0.6)))
            cv.drawCircle(568 + lean, 560, 9, paint(C('#E8E0D0', 0.6)))
        cv.restore()
    cv.drawRect(win, paint(C('#FFFFFF', 0.05)))
    # barricade in front
    for (dx, dy, r) in ((380, 1660, -6), (700, 1640, 8), (540, 1500, -3), (330, 1450, 15)):
        desk(cv, dx, dy, 1.1, r)
    cv.drawRect(skia.Rect(0, 1700, W, H), paint('#2E2A26'))


def shot_DOOR(cv, t):
    door_bg(cv, t)
    # backs of the four of you, watching the door (foreground silhouettes)
    for who, x, s_ in (('bob', 140, 1.0), ('jus', 960, 0.95)):
        kid(cv, who, x, 2500, s_, view='back')
    glow(cv, (0, 600), 1000, DAY, 0.15)
    shade(cv, (540, 800), 1150, 0.65)


def shot_FLASH(cv, t):
    """Three days ago (slow, stupid) -> now (they run, they set traps, one used a phone). Side views, a red-tinted memory."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1A1614'))
    cv.drawRect(skia.Rect(0, 0, W, 1250), paint('#2E2622', shader=lin((0, 0), (0, 1250), [C('#3A2E28'), C('#2A221E')])))
    cv.drawRect(skia.Rect(0, 1250, W, H), paint('#221C18'))
    for k in range(5):                                                                   # street buildings
        cv.drawRect(skia.Rect(k * 230 - 20, 500 - (k % 2) * 140, k * 230 + 190, 1250), paint('#1E1816'))
    if t < B['run']:                                                                      # slow, shambling
        for k in range(3):
            x = 200 + k * 300 + (t - B['flash']) * 30
            hr = ZHAIR[k]
            mascot(cv, x, 1600, 0.42, view='side', face=1, walk=((t * 0.45 + k * 0.3) % 1), arm_r=(80, 0), arm_l=(85, 0), body_lean=12,
                   hair=hr[0], hair_sh=hr[1], **ZOMBIE)
        text(cv, '3 DAYS AGO', 540, 1780, 70, '#C9C2AE', alpha=0.8)
    elif t < B['phone']:                                                                  # now they RUN
        u = t - B['run']
        x = -200 + u * 900
        mascot(cv, x, 1650, 0.5, view='side', face=1, walk=(t * 2.6) % 1, run=True, hair=ZHAIR[3][0], hair_sh=ZHAIR[3][1], **ZOMBIE)
        for k in range(6):                                                                # speed lines
            y = 900 + k * 110
            cv.drawLine(x - 500 - k * 60, y, x - 120, y, paint(C('#E8E0D0', 0.25), style='stroke', width=6))
        if t >= B['traps']:                                                               # a tripwire across the street
            cv.drawLine(0, 1580, W, 1560, paint(C('#E8E0D0', 0.8), style='stroke', width=4))
            text(cv, 'TRAP', 860, 1520, 60, '#E62828')
        text(cv, 'NOW', 540, 1880, 70, '#E62828')
    else:                                                                                  # one of them used a phone
        mascot(cv, 540, 2500, 1.4, look=(0.0, 0.6), head_tilt=8, arm_r=(20, -110), arm_l=(20, -110), hair=ZHAIR[1][0], hair_sh=ZHAIR[1][1],
               **ZOMBIE)
        cv.drawRect(skia.Rect(470, 1500, 610, 1700), paint('#101215'))
        cv.drawRect(skia.Rect(482, 1514, 598, 1686), paint('#BFE0FF'))
        glow(cv, (540, 1400), 500, '#BFE0FF', 0.35)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#5A1A10', 0.18)))                       # memory tint
    shade(cv, (540, 1100), 1150, 0.65)


def face_cu(cv, t, who, line, **pose):
    classroom_bg(cv, t)
    base = {'you': {}, 'bob': BOB, 'law': LAW, 'jus': JUS}[who]
    P = dict(base)
    P.update(pose)
    P['mouth_open'] = talk(t, *line)
    mascot(cv, 540, 2700, 1.95, light_side=-1, rim=DAY, rim_a=0.5, **P)
    shade(cv, (540, 950), 1100, 0.55)


def shot_BOB(cv, t):
    if t < B['b2']:
        face_cu(cv, t, 'bob', ('B1',), look=(-0.6, 0.0), brow=0.3, mouth='flat', head_turn=-0.3)
    else:
        face_cu(cv, t, 'bob', ('B2',), look=(0.0, -0.95), brow=1.0, mouth='flat', pupil=0.6, sweat=True, head_tilt=-8)


def shot_JUSTIN(cv, t):
    face_cu(cv, t, 'jus', ('J1',), look=(0.6, 0.0), brow=1.0, mouth='open', pupil=0.6, sweat=True, head_turn=0.3)


def shot_LAWRENCE(cv, t):
    face_cu(cv, t, 'law', ('L1',), look=(-0.5, 0.1), brow=1.0, mouth='frown', pupil=0.55, sweat=True)


def shot_WINDOW(cv, t):
    """Looking down from the third floor: the courtyard, packed. Nobody moves. Then they all look up."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#5A626C'))
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#4A5058', shader=lin((0, 0), (0, H), [C('#3A4048'), C('#5A626C')])))
    for k in range(9):
        cv.drawLine(0, 300 + k * 200, W, 300 + k * 200, paint(C('#2E343A', 0.5), style='stroke', width=4))
    up = ease((t - B['up']) / 0.25)
    i = 0
    for r in range(9):
        for c in range(7):
            x = 70 + c * 160 + (80 if r % 2 else 0)
            y = 260 + r * 190
            if x > W + 60:
                continue
            hr = ZHAIR[(r * 7 + c) % len(ZHAIR)]
            s_ = 0.22
            cv.save(); cv.translate(x, y); cv.scale(s_, s_)
            cv.drawCircle(0, 0, 200, paint('#404046'))                                     # shoulders from above
            if up < 0.5:                                                                     # tops of heads
                cv.drawCircle(0, -10, 150, paint(hr[0]))
            else:                                                                            # faces turned up at the window
                cv.drawCircle(0, -10, 150, paint(ZOMBIE['skin']))
                cv.drawPath(blob([(-150, -40), (-120, -150), (0, -180), (120, -150), (150, -40), (0, -110)]), paint(hr[0]))
                for sd in (-1, 1):
                    cv.drawCircle(sd * 55, 10, 30, paint('#F0E8E0'))
                    cv.drawCircle(sd * 55, 10, 13, paint('#B01E1E'))
                cv.drawOval(skia.Rect(-30, 70, 30, 110), paint('#3A1A1A'))
            cv.restore()
            i += 1
    # window frame + glass
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C(DAY, 0.08)))
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#2A3036', style='stroke', width=70))
    cv.drawRect(skia.Rect(520, 0, 560, H), paint('#2A3036'))
    shade(cv, (540, 960), 1150, 0.55)


def shot_PHONE(cv, t):
    classroom_bg(cv, t)
    cv.drawRect(skia.Rect(0, 0, W, H), paint(C('#000000', 0.55)))
    cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(200, 260, 880, 1560), 60, 60)), paint('#101215'))
    cv.drawRect(skia.Rect(230, 330, 850, 1490), paint('#ECEFF3'))
    cv.drawRect(skia.Rect(230, 330, 850, 470), paint('#D9DEE5'))
    text(cv, 'Mr. Peterson', 540, 420, 52, '#1A1F26')
    msgs = [(B['text'] + 0.3, 'Justin. Where are you?'), (B['text'] + 1.2, 'Is everyone okay?'), (B['msg'], "I know you're in 204.")]
    y = 560
    for tm, m in msgs:
        if t >= tm:
            a = ease((t - tm) / 0.2)
            red = m.startswith('I know')
            cv.drawPath(skia.Path().addRRect(skia.RRect.MakeRectXY(skia.Rect(260, y, 780, y + 120), 36, 36)),
                        paint(C('#E62828' if red else '#C9CED6', a)))
            text(cv, m, 290, y + 78, 44, C('#FFFFFF' if red else '#1A1F26', a), align='left')
            y += 160
    if t >= B['msg'] + 1.2:
        text(cv, 'Mr. Peterson is typing...', 290, y + 60, 38, '#6A707A', align='left', bold=False)
    for side in (-1, 1):
        hx = 540 + side * 360
        cv.drawPath(blob([(hx - 70, 1200), (hx + 70, 1180), (hx + 90, 1440), (hx - 60, 1500)]), paint('#F2C29B'))
        cv.drawPath(poly([(hx - 80, 1440), (hx + 100, 1420), (hx + 160, H), (hx - 140, H)]), paint('#C83030' if side > 0 else '#9A2222'))
    glow(cv, (540, 900), 700, '#BFE0FF', 0.2)
    shade(cv, (540, 900), 1100, 0.55)


def shot_VENT(cv, t):
    """The ceiling vent, right above you: scratching, the grille bulging, grey fingers through the slats."""
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#3A4148', shader=lin((0, 0), (0, H), [C('#2E343A'), C('#454C53')])))
    for k in range(6):
        cv.drawLine(0, 200 + k * 300, W, 200 + k * 300, paint(C('#2A3036', 0.6), style='stroke', width=6))
    late = t >= B['vent2']
    bulge = keys(t, [(B['vent'], 0.0), (B['b2'], 0.2), (B['vent2'], 0.3), (B['choice'], 1.0)])
    jit = 5 * math.sin(t * 50) * (0.3 + bulge)
    x0, y0, x1, y1 = 240 + jit, 620, 840 + jit, 1220
    cv.drawRect(skia.Rect(x0, y0, x1, y1), paint('#050608'))
    if t > B['vent'] + 0.5:                                                                    # fingers through the slats
        for k in range(4):
            fx = 420 + k * 70 + 10 * math.sin(t * 7 + k)
            ln = 60 + 140 * bulge + 20 * math.sin(t * 9 + k * 2)
            cv.drawLine(fx, y0 + 200, fx + 6, y0 + 200 + ln, paint(ZOMBIE['skin_sh'], style='stroke', width=28))
            cv.drawCircle(fx + 6, y0 + 200 + ln, 15, paint('#5A4A3A'))
    if late:                                                                                    # an eye in the dark
        cv.drawCircle(640, 760, 30, paint('#F0E8E0'))
        cv.drawCircle(640, 760, 13, paint('#B01E1E'))
    for k in range(9):                                                                          # the grille slats
        y = y0 + 30 + k * 64 + bulge * 30 * math.sin(math.pi * k / 8)
        cv.drawRect(skia.Rect(x0, y, x1, y + 26), paint('#A8B0B8'))
    cv.drawRect(skia.Rect(x0 - 20, y0 - 20, x1 + 20, y1 + 20), paint('#C9CED6', style='stroke', width=24))
    for k in range(12):                                                                          # dust falling
        ph = (t * 0.6 + k * 0.083) % 1
        cv.drawCircle(300 + k * 45, y1 + ph * 700, 4, paint(C('#D8D2C0', 0.6 * (1 - ph))))
    shade(cv, (540, 920), 1100, 0.6)


SHOTS = {'DOOR': shot_DOOR, 'FLASH': shot_FLASH, 'WIDE': shot_WIDE, 'BOB': shot_BOB, 'JUSTIN': shot_JUSTIN, 'LAWRENCE': shot_LAWRENCE,
         'WINDOW': shot_WINDOW, 'PHONE': shot_PHONE, 'VENT': shot_VENT}


def needed():
    out = []
    for sgm in E.SEGMENTS:
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
            if i % 300 == 0:
                print('DRAW', i, '/', len(todo), flush=True)
    print('DRAW_OK', len(todo))
