"""VIDEO_026 "Two Bobs" timeline — ONE source of truth for renderer.py, compositor.py (EDL), voice_engine.py and sound_mix.py.
56.0 s = 1,680 frames @ 30 fps. Frame numbers follow the user's blueprint; where real speech could not fit the blueprint's
slots (e.g. 10 words in 1.07 s before the 15.67 s snap) the LINE was shortened, never the scare moved."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
TIMING = os.path.join(VIDEO, 'audio', 'narration', 'timing.json')
FPS, END, NF = 30, 56.0, 1680


def fr(frame):
    return frame / FPS


# ---- key events (seconds). F = the blueprint's frame numbers.
F = dict(whip1=18, whip1_end=27, s1b=45, label_dist=65, s2a=135, chime=138, unblur=180, s2b=240, label_ir=265, live_turn=327,
         s3a=345, fingers=381, s3b=417, snap=470, s4a=540, knock1=540, knock2=554, knock3=568, lightning=606, handle=640,
         s4b=675, label_out=705, note=737, blink=775, s5a=810, feed=820, climb=872, drop=936, s5b=945, label_5s=1015,
         s5c=1030, dots=1058, s6a=1095, ring=1146, yank=1191, s6b=1215, unzip=1290, s7a=1380, kick=1515, peek=1515,
         peek_end=1569, s7b=1590, box2=1615, box3=1638, hand=1650, end=1680)
T = {k: v / FPS for k, v in F.items()}

SHOTS = [('S1A', 0, F['s1b']), ('S1B', F['s1b'], F['s2a']), ('S2A', F['s2a'], F['s2b']), ('S2B', F['s2b'], F['s3a']),
         ('S3A', F['s3a'], F['s3b']), ('S3B', F['s3b'], F['s4a']), ('S4A', F['s4a'], F['s4b']), ('S4B', F['s4b'], F['s5a']),
         ('S5A', F['s5a'], F['s5b']), ('S5B', F['s5b'], F['s5c']), ('S5C', F['s5c'], F['s6a']), ('S6A', F['s6a'], F['s6b']),
         ('S6B', F['s6b'], F['s7a']), ('S7A', F['s7a'], F['s7b']), ('S7B', F['s7b'], NF)]


def shot_at(f):
    for n, a, b in SHOTS:
        if a <= f < b:
            return n, a, b
    return SHOTS[-1]


# ---- narration: absolute line starts (s) + per-line tempo (sox tempo, pitch kept). voice_engine.py place speeds a line up
# (max x1.38) only if it would still overrun the next one. ANCHOR = (line, word, time): the word must START at that time.
START = {'N01': 0.1, 'N03': 3.15, 'N04': 4.95, 'N05': 8.1, 'N06': 10.05, 'M01': 11.9, 'N07': 13.7, 'B01': 15.86,
         'N08': 18.5, 'N09': 22.7, 'N10': 24.85, 'N11': 27.2, 'N12': 29.2, 'N13': 31.7, 'N14': 34.5, 'N15': 36.75,
         'N16': 38.5, 'N17': 40.6, 'N18': 44.15, 'D01': 46.3, 'N19': 50.8, 'N20': 52.98}
TEMPO = {'N01': 1.38, 'N03': 1.3, 'N04': 1.15, 'N05': 1.2, 'N06': 1.25, 'N07': 1.3, 'N08': 1.15, 'N09': 1.3, 'N10': 1.3,
         'N11': 1.3, 'N12': 1.2, 'N13': 1.25, 'N14': 1.1, 'N15': 1.2, 'N16': 1.2, 'N17': 1.3, 'N18': 1.1, 'N19': 1.34, 'N20': 1.2}
ANCHOR = {'N07': ('does', T['snap'] - 0.30), 'N17': ('splits', T['unzip'] - 0.30)}     # the hit lands MID-WORD
LAST_END = END - 0.07                                                        # "Comment now." ends on the loop point

WORDS, LINES = [], {}
if os.path.exists(TIMING):
    _t = json.load(open(TIMING))
    if _t.get('placed'):
        WORDS = _t['words']
        LINES = {ln['id']: (ln['start'], ln['end']) for ln in _t['lines']}


def w_at(lid, word, default):
    for w in WORDS:
        if w['line'] == lid and w['text'].lower().strip('.,:!?') == word:
            return w['start']
    return default


def clock_rec(t):
    """HUD timecode REC 00:SS."""
    s = int(t)
    return f'{s // 60:02d}:{s % 60:02d}'
