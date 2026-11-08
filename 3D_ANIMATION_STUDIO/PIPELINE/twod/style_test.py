"""2D style frame: the mascot in the elevator (flat vector, painted light). Writes a PNG."""
import os
import sys

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flat import C, H, W, blob, glow, lin, mascot, paint, poly, rad, shade  # noqa


def elevator_bg(cv, lit=1.0):
    # back wall (brushed steel panels, cool)
    cv.drawRect(skia.Rect(0, 0, W, H), paint('#1B2129'))
    vx0, vx1, vy0, vy1 = 170, 910, 360, 1500                    # back-wall rectangle (one-point perspective)
    cv.drawRect(skia.Rect(vx0, vy0, vx1, vy1), paint('#3A4552', shader=lin((0, vy0), (0, vy1), [C('#4A5664'), C('#2C343E')])))
    for i in range(3):                                          # steel panels
        x = vx0 + 30 + i * (vx1 - vx0 - 60) / 3
        cv.drawRect(skia.Rect(x + 10, vy0 + 40, x + (vx1 - vx0 - 60) / 3 - 10, vy1 - 160),
                    paint('#43505E', shader=lin((x, 0), (x + 240, 0), [C('#4C5967'), C('#3B4653')])))
    # side walls
    cv.drawPath(poly([(0, 0), (vx0, vy0), (vx0, vy1), (0, H)]), paint('#252D37', shader=lin((0, 0), (vx0, 0), [C('#1A2028'), C('#2E3742')])))
    cv.drawPath(poly([(W, 0), (vx1, vy0), (vx1, vy1), (W, H)]), paint('#2A333E', shader=lin((W, 0), (vx1, 0), [C('#1D232C'), C('#36404C')])))
    # ceiling + light panel
    cv.drawPath(poly([(0, 0), (W, 0), (vx1, vy0), (vx0, vy0)]), paint('#161B22'))
    cv.drawPath(poly([(330, 150), (750, 150), (700, 300), (380, 300)]), paint('#E6F0FF'))
    # floor
    cv.drawPath(poly([(0, H), (vx0, vy1), (vx1, vy1), (W, H)]), paint('#2B2622', shader=lin((0, vy1), (0, H), [C('#2A2420'), C('#3A322B')])))
    # handrail (back wall + right wall)
    cv.drawRect(skia.Rect(vx0, 1060, vx1, 1078), paint('#8E99A6'))
    cv.drawPath(poly([(vx1, 1060), (W, 1180), (W, 1204), (vx1, 1078)]), paint('#7D8895'))
    # button panel on the right wall
    cv.drawPath(poly([(960, 760), (1040, 735), (1040, 1010), (960, 1000)]), paint('#59636F'))
    for k, (bx, by, col) in enumerate(((1000, 790, '#FF3B2F'), (985, 850, '#FFB23A'), (1018, 850, '#C9CED6'), (985, 905, '#C9CED6'), (1018, 905, '#C9CED6'))):
        cv.drawCircle(bx, by, 14, paint(col))
    glow(cv, (1000, 790), 60, '#FF3B2F', 0.5)
    glow(cv, (985, 850), 50, '#FFB23A', 0.35)
    # floor display above the doors is behind the camera: show its red glow on the ceiling
    glow(cv, (540, 0), 260, '#FF4A3A', 0.12)


def main(out):
    surf = skia.Surface(W, H)
    cv = surf.getCanvas()
    elevator_bg(cv)
    mascot(cv, 520, 1640, 0.95, look=(0.15, -0.9), brow=0.9, mouth='flat', head_tilt=-6, arm_l=(8, 8), arm_r=(10, 12),
           light_side=1, rim='#9FC3FF', rim_a=0.55)
    glow(cv, (540, 230), 900, '#BFD6FF', 0.22)                 # cool overhead key
    shade(cv, (540, 820), 1250, 0.75)                          # low-key: dark corners
    img = surf.makeImageSnapshot()
    img.save(out, skia.kPNG)
    print('OK', out)


if __name__ == '__main__':
    main(sys.argv[1])
