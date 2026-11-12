"""VIDEO_025 timeline — ONE source of truth for anim.py, edit_video025.py, audio/place_lines.py and audio/build_cues.py.
The HUD clock is REAL TIME: the video is 60.0 s and the world ends at 0:00 (white flash -> loops to frame 0)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
FPS, END = 30, 60.0

# line starts (absolute video seconds); place_lines.py speeds a line up (max x1.3) if it would overrun the next one
START = {'N01': 0.15, 'A01': 3.4, 'N02': 6.75, 'N03': 10.2, 'N04': 12.35, 'P01': 17.3, 'M01': 18.4, 'P02': 19.55, 'M02': 21.9,
         'N05': 23.6, 'S01': 29.5, 'N06': 31.4, 'A02': 36.8, 'N07': 41.1, 'S02': 42.55, 'S03': 44.0, 'M03': 45.8, 'S04': 47.45,
         'N08': 50.45, 'N09': 53.0, 'N10': 57.1}
TEMPO = {'N01': 1.3, 'N02': 1.2, 'N03': 1.2, 'N04': 1.1, 'M01': 1.2, 'N05': 1.1, 'N06': 1.1, 'N09': 1.1, 'N10': 1.25}

T = dict(crash=0.35, phone1=3.3, run=6.6, pano=10.1, grav=12.2, lift=13.0, slam=14.5, front=14.95, scare=15.75, call=16.6,
         run2=17.2, close=19.45, fail=22.85, high=23.45, sweep=25.8, door=27.4, table=29.2, hug=31.2, rumble=34.0, rip=34.75,
         open=35.0, phone2=36.6, kept=38.9, lock=40.1, cmia=42.5, cyou=45.75, cmia2=47.4, wide=50.3, go=52.9, her=54.3,
         hands=55.6, choice=57.0, white=59.65, end=END)

WORDS, LINES = [], {}
if os.path.exists(TIMING):
    _t = json.load(open(TIMING))
    WORDS = _t['words']
    LINES = {ln['id']: (ln['start'], ln['end']) for ln in _t['lines']}


def w_at(lid, word, default):
    for w in WORDS:
        if w['line'] == lid and w['text'].lower().strip('.,:!?') == word:
            return w['start']
    return default


if 'N09' in LINES:                                                      # cut on the three clauses of "I could go / give it to her / stay"
    T['go'] = LINES['N09'][0] - 0.12
    T['her'] = w_at('N09', 'give', T['her'] + 0.35) - 0.38
    T['hands'] = w_at('N09', 'or', T['hands'] + 0.15) - 0.15
if 'A02' in LINES:                                                      # "KEPT: YOU" lands on the word "kept"; the beam right after
    T['kept'] = w_at('A02', 'kept', T['kept'])
    T['lock'] = max(T['lock'], LINES['A02'][1] + 0.05)
if 'N10' in LINES:
    T['choice'] = min(T['choice'], LINES['N10'][0] - 0.2)

SHOTS = [(0.0, T['phone1'], 'SH01'), (T['phone1'], T['run'], 'PH1'), (T['run'], T['pano'], 'SH03'), (T['pano'], T['grav'], 'SH04'),
         (T['grav'], T['front'], 'SH05'), (T['front'], T['call'], 'SH06'), (T['call'], T['run2'], 'PH_MOM'),
         (T['run2'], T['close'], 'SH08'), (T['close'], T['fail'], 'SH08B'), (T['fail'], T['high'], 'PH_FAIL'),
         (T['high'], T['door'], 'SH10'), (T['door'], T['table'], 'SH11'), (T['table'], T['hug'], 'SH12'), (T['hug'], T['open'], 'SH13'),
         (T['open'], T['phone2'], 'SH14'), (T['phone2'], T['lock'], 'PH2'), (T['lock'], T['cmia'], 'SH16'), (T['cmia'], T['cyou'], 'SH17'),
         (T['cyou'], T['cmia2'], 'SH18'), (T['cmia2'], T['wide'], 'SH19'), (T['wide'], T['go'], 'SH20'), (T['go'], T['her'], 'SH20B'),
         (T['her'], T['hands'], 'SH20C'), (T['hands'], T['choice'], 'HANDS'), (T['choice'], END, 'SH22')]


def shot_at(t):
    for a, b, n in SHOTS:
        if a <= t < b:
            return n, a, b
    return SHOTS[-1][2], SHOTS[-1][0], SHOTS[-1][1]


def clock(t):
    """The HUD / phone countdown: 1:00 at frame 0 -> 0:00 at the end."""
    n = max(0, min(60, int(-(-(END - t) // 1))))
    return '1:00' if n == 60 else f'0:{n:02d}'
