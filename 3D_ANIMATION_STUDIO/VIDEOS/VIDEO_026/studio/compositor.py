"""VIDEO_026 compositor.

Part 1 (used by renderer.py, Skia): the in-frame passes — top HUD row (REC / BPM / ANOMALIES), red pop-up labels with target
boxes, the 3-box choice card (Y=780), film grain + vignette, and the VHS glitch pass (RGB channel separation with
BlendMode.kScreen, horizontal scanline tears, colour strobes).

Part 2 (read by PIPELINE/editing/edl_engine.py): the EDL — frames map 1:1, mid-screen captions at Y=1240 (condensed bold white,
one red keyword, small red speaker label), the @insidethemindlessvault watermark, the POV eyelid blink at frames 775-785.

    python3 studio/compositor.py            -> EXPORTS/VIDEO_026_two_bobs_mimic.mp4 (H.264 + AAC)
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
STUDIO = os.path.abspath(os.path.join(VIDEO, '..', '..'))
for _p in (HERE, os.path.join(STUDIO, 'PIPELINE', 'twod'), os.path.join(STUDIO, 'PIPELINE', 'hybrid')):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import timeline as TL  # noqa: E402

F, T, FPS, END, NF = TL.F, TL.T, TL.FPS, TL.END, TL.NF
RED = '#E8282D'

# ====================================================================================== Part 1: Skia passes (lazy imports: the EDL side needs none of it)
HUD_BPM = [(0, '116'), (F['s2a'], '132'), (F['snap'], '164'), (F['s5b'], '178'), (F['ring'], '192'), (F['unzip'], '204 [CRITICAL]')]
HUD_ANOM = [(0, '1'), (F['s2a'], '2'), (F['snap'], '3'), (F['s5b'], '4'), (F['unzip'], 'FATAL')]
GLITCH = [(0, 5, 18, 18), (F['live_turn'], F['live_turn'] + 4, 7, 3), (F['snap'], F['snap'] + 8, 14, 3), (F['feed'] - 10, F['feed'] + 2, 9, 2),
          (F['ring'], F['ring'] + 5, 10, 2), (F['unzip'], F['unzip'] + 16, 18, 5), (F['box3'], F['box3'] + 4, 22, 6), (NF - 6, NF, 3, 18)]
#          (frame0, frame1, px at start, px at end)


def _key(keys, f):
    cur, since = keys[0][1], keys[0][0]
    for k, v in keys:
        if f >= k:
            cur, since = v, k
    return cur, since


def glitch_px(f):
    for a, b, p0, p1 in GLITCH:
        if a <= f < b:
            return p0 + (p1 - p0) * (f - a) / max(1, b - a - 1)
    return 0.0


def hud(cv, f, t):
    """REC timecode | BPM | ANOMALIES (the blueprint's telemetry). A changed value flashes red; CRITICAL / FATAL / EXPOSED stay red."""
    import skia
    from kit import text
    from puppets import C, paint
    exposed = F['ring'] <= f < F['s6b']
    cols = [('DECIBELS' if exposed else 'REC', '98 dB [EXPOSED]' if exposed else TL.clock_rec(t), F['ring'] if exposed else -99, 70, 'left'),
            ('BPM',) + _key(HUD_BPM, f) + (540, 'center'), ('ANOMALIES',) + _key(HUD_ANOM, f) + (1010, 'right')]
    for label, val, since, x, al in cols:
        hot = (0 <= f - since < 26 and since > 0) or any(k in val for k in ('CRITICAL', 'FATAL', 'EXPOSED'))
        lx = x + (26 if (label == 'REC' and al == 'left') else 0)
        text(cv, label, lx + 2, 176, 26, '#000000', align=al, alpha=0.6, bold=False)
        text(cv, label, lx, 174, 26, '#C8C8CE', align=al, bold=False)
        text(cv, val, x + 2, 226, 48, '#000000', align=al, alpha=0.65)
        text(cv, val, x, 224, 48, RED if hot else '#FFFFFF', align=al)
    if not exposed and int(t * 1.6) % 2 == 0:
        cv.drawCircle(80, 165, 8, paint(RED))


def label(cv, f, f0, f1, txt, at, target=None, size=36, leader=True):
    """Red pop-up label `[ TXT ]` at `at` (centre), optional target box (l, t, r, b) with corner brackets + a leader line."""
    import skia
    from kit import TF_B, text
    from puppets import C, paint, stroke
    if not (f0 <= f < f1):
        return
    k = min(1.0, (f - f0 + 1) / 4.0)
    a = min(1.0, (f1 - f) / 5.0)
    blink_on = (f - f0) > 8 or (f - f0) % 4 < 2
    s = '[ ' + txt + ' ]'
    font = skia.Font(TF_B, size)
    w = font.measureText(s)
    if w > 900:
        size = size * 900 / w; font = skia.Font(TF_B, size); w = font.measureText(s)
    cx = min(max(at[0], 70 + w / 2 + 22), 1010 - w / 2 - 22)                   # keep the text inside the safe area
    cy = at[1]
    if target is not None:
        l, t_, r, b = target
        m = 34 * (2 - k)
        for (x0, y0, dx, dy) in ((l, t_, 1, 1), (r, t_, -1, 1), (l, b, 1, -1), (r, b, -1, -1)):
            cv.drawLine(x0, y0, x0 + dx * m, y0, stroke(RED, 6, a)); cv.drawLine(x0, y0, x0, y0 + dy * m, stroke(RED, 6, a))
        if leader:
            tx, ty = (l + r) / 2, (t_ if cy < t_ else b)
            cv.drawLine(tx, ty, cx, cy + (26 if cy < t_ else -26), stroke(RED, 3, 0.8 * a))
    cv.save(); cv.translate(cx, cy); cv.scale(1 + 0.18 * (1 - k), 1 + 0.18 * (1 - k))
    box = skia.Rect.MakeLTRB(-w / 2 - 22, -size * 0.78, w / 2 + 22, size * 0.62)
    cv.drawRoundRect(box, 8, 8, paint(C('#0A0A10', 0.82 * a)))
    cv.drawRoundRect(box, 8, 8, stroke(RED, 3.5, a))
    if blink_on:
        cv.drawString(s, -w / 2, size * 0.32, font, paint(C('#FFFFFF', a)))
    cv.restore()


CHOICES = ['SMASH PHONE LIGHT', 'ROLL UNDER COUCH', 'RUN TO REAL BOB']


def choice_times():
    return [max(F['s7b'], int(round(TL.w_at('N20', w, d) * FPS))) for w, d in (('smash', T['s7b']), ('hide', T['box2']), ('run', T['box3']))]


def choice_card(cv, f):
    """3 boxes slam in at Y=780; each one flashes red on its word (frames ~1590 / 1615 / 1638)."""
    import skia
    from kit import TF_B, text
    from puppets import C, paint, stroke
    if f < F['s7b']:
        return
    times = choice_times()
    k0 = min(1.0, (f - F['s7b'] + 1) / 3.0)
    rh, gap, wd = 92, 14, 880
    y0 = 780 - (3 * rh + 2 * gap) / 2
    cv.save(); cv.translate(540, 780); cv.scale(1 + 0.3 * (1 - k0), 1 + 0.3 * (1 - k0)); cv.translate(-540, -780)
    for i, txt in enumerate(CHOICES):
        if f < times[i]:
            continue
        df = f - times[i]
        y = y0 + i * (rh + gap)
        flash = df < 7
        pop = 1 + 0.08 * max(0.0, 1 - df / 4.0)
        cv.save(); cv.translate(540, y + rh / 2); cv.scale(pop, pop); cv.translate(-540, -(y + rh / 2))
        box = skia.Rect.MakeLTRB(540 - wd / 2, y, 540 + wd / 2, y + rh)
        cv.drawRoundRect(box, 20, 20, paint(C(RED, 0.95) if flash else C('#0C0C12', 0.86)))
        cv.drawRoundRect(box, 20, 20, stroke('#FFFFFF' if flash else RED, 5))
        badge = skia.Rect.MakeLTRB(540 - wd / 2 + 16, y + 14, 540 - wd / 2 + 16 + 76, y + rh - 14)
        cv.drawRoundRect(badge, 14, 14, paint('#FFFFFF' if flash else RED))
        text(cv, str(i + 1), 540 - wd / 2 + 54, y + rh / 2 + 18, 52, RED if flash else '#FFFFFF')
        text(cv, txt, 540 - wd / 2 + 118, y + rh / 2 + 18, 52, '#FFFFFF', align='left')
        cv.restore()
    if f >= times[2] + 6:
        text(cv, 'COMMENT 1, 2 OR 3', 542, y0 + 3 * (rh + gap) + 40, 38, '#000000', alpha=0.6)
        text(cv, 'COMMENT 1, 2 OR 3', 540, y0 + 3 * (rh + gap) + 38, 38, '#FFFFFF')
    cv.restore()


def grade(cv, t, vign=0.55, g=0.07, centre=(540, 900)):
    from comp import grain, shade
    shade(cv, centre, 1150, vign)
    grain(cv, t, g)


def strobe(cv, f):
    """Colour strobes: white phone flash on frame 1; crimson on the snap; crimson/cyan for 0.5 s on the unzip; cyan on the ring."""
    import skia
    from puppets import C, H, W, paint
    col = None
    if f == 1:
        col = C('#FFFFFF', 0.85)
    elif f in (F['snap'], F['snap'] + 1):
        col = C('#E8101C', 0.6)
    elif F['ring'] <= f < F['ring'] + 3:
        col = C('#BFF0FF', 0.5 - 0.15 * (f - F['ring']))
    elif F['unzip'] <= f < F['unzip'] + 16:
        k = f - F['unzip']
        col = C('#E8101C' if (k // 2) % 2 == 0 else '#37BEFF', max(0.0, 0.5 - k * 0.027))
    elif F['box3'] <= f < F['box3'] + 2:
        col = C('#E8101C', 0.35)
    if col is not None:
        cv.drawRect(skia.Rect(0, 0, W, H), paint(col, blend=skia.BlendMode.kScreen if f != 1 else None))


def glitch_pass(srf, cv, f):
    """VHS pass on the finished frame: R / G / B drawn apart by +-px (BlendMode.kScreen) + horizontal scanline tears."""
    import numpy as np
    import skia
    from puppets import H, W
    px = glitch_px(f)
    if px < 0.5:
        return
    img = srf.makeImageSnapshot()
    cv.save(); cv.resetMatrix()
    cv.clear(skia.ColorBLACK)
    for dx, m in ((-px, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]), (0, [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]),
                  (px, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0])):
        cv.drawImage(img, dx, 0, skia.SamplingOptions(), skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m), BlendMode=skia.BlendMode.kScreen))
    rng = np.random.default_rng(f * 13 + 5)
    img2 = srf.makeImageSnapshot()
    for _ in range(int(3 + px / 3)):                                           # scanline tears
        y = float(rng.uniform(0, H - 60)); h = float(rng.uniform(6, 46)); sh = float(rng.uniform(-3.5, 3.5) * px)
        cv.drawImageRect(img2, skia.Rect.MakeXYWH(0, y, W, h), skia.Rect.MakeXYWH(sh, y, W, h), skia.SamplingOptions(), skia.Paint())
    for _ in range(4):                                                         # little colour dashes at the edges (like the reference)
        y = float(rng.uniform(40, H - 40)); x = float(rng.choice([rng.uniform(0, 160), rng.uniform(W - 220, W - 30)]))
        col = [skia.Color(255, 40, 60, 200), skia.Color(40, 230, 255, 200), skia.Color(255, 220, 60, 200)][int(rng.integers(0, 3))]
        cv.drawRect(skia.Rect.MakeXYWH(x, y, float(rng.uniform(30, 120)), 5), skia.Paint(Color=col))
    cv.restore()


# ====================================================================================== Part 2: the EDL (edl_engine.py loads this file)
TIMING = TL.TIMING
DURATION = END
AUDIO = os.path.join(VIDEO, 'audio', 'mix_master.wav')
SEGMENTS = [dict(t0=0.0, t1=END, src='ALL', map=[(0.0, 0.0), (END, END * FPS)])]
OVERLAYS = [dict(type='blink', t0=T['blink'], t1=T['blink'] + 0.4, blinks=[(T['blink'], 0.10, 0.07, 0.16)]),
            dict(type='watermark', t0=0.0, t1=END)]
SPK = {'M01': 'YOU', 'B01': 'BOB?', 'D01': 'IT'}
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1240, size=68, max_words=3, speakers=SPK,
                emphasis={"don't", 'door', 'you', 'twenty', 'photo', 'tv', 'throat', 'text', 'lips', 'freezing', 'pounds', 'real', 'breath', 'sound',
                          'security', 'climbs', 'delay', 'behind', 'phone', 'splits', 'middle', 'locked', 'me', 'kicked', 'smash', 'hide', 'run', 'now'})

if __name__ == '__main__':
    sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'editing'))
    import edl_engine
    out = os.path.join(STUDIO, 'EXPORTS', 'VIDEO_026_two_bobs_mimic.mp4')
    edl_engine.render(os.path.abspath(__file__), os.path.join(VIDEO, 'frames2d'), out, AUDIO, crf=19, preset='medium')
