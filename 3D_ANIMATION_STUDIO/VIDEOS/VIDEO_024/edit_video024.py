"""VIDEO_024 EDL — "The Taxi" (blueprint by the user; 55.0 s, ends on 'now' and loops). Shots by the blueprint's clock:
1 CAB_BACK 0-10 · 2 METER 10-18 · 3 IDCARD 18-29 · 4 TUNNEL 29-39 · 5 DRIVER 39-CTA (swap at 42.5) · 6 CTA (N12 start) - 55.0.
Camera moves (dolly/pan/shake) are drawn IN renderer.py (vector, stays sharp at x2.5); the EDL maps frames 1:1."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
FPS = 30
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
LS = {l['id']: (l['start'], l['end']) for l in _T['lines']}
WORDS = _T['words']
END = DURATION = 55.0


def s(i):
    return LS[i][0]


def e(i):
    return LS[i][1]


def w_at(lid, word):
    for w in WORDS:
        if w['line'] == lid and w['text'].lower().strip('.,:!?') == word:
            return w['start']
    return s(lid)


B = dict(meter=10.0, idcard=18.0, flash=22.5, tunnel=29.0, driver=39.0, snap=42.5, cta=min(52.0, s('N12')))
B['one'], B['two'], B['three'] = w_at('N12', 'one'), w_at('N12', 'two'), w_at('N12', 'three')
JS = 0.4


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


SEGMENTS = [S(0.0, B['meter'], 'CAB_BACK', shake=[(0.0, 0.35, 16)]),
            S(B['meter'], B['idcard'], 'METER'),
            S(B['idcard'], B['tunnel'], 'IDCARD', flash=[(B['flash'], 0.08)]),
            S(B['tunnel'], B['driver'], 'TUNNEL'),
            S(B['driver'], B['cta'], 'DRIVER', fx_t=[(B['snap'], B['snap'] + 2 / 30, 'redflash'), (B['snap'], B['snap'] + 0.3, 'glitch')],
              shake=[(B['snap'], B['snap'] + 0.4, 30)]),
            S(B['cta'], END, 'CTA', shake=[(B['cta'], B['cta'] + 0.15, 20)])]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=48,
         cols=[([(0, 'DECIBELS')], [(0, '95 dB'), (B['tunnel'], '102 dB'), (B['snap'], '118 dB')]),
               ([(0, 'HEART RATE')], [(0, '110 BPM'), (11.0, '135 BPM'), (B['flash'], '150 BPM'), (33.5, '160 BPM'), (B['snap'], '190 BPM')]),
               ([(0, 'ANOMALIES')], [(0, '1'), (B['flash'], '2'), (33.5, '3'), (B['snap'], 'CRITICAL')])]),
    dict(type='watermark', t0=0.0, t1=END),
]
SPK = {'M01': 'YOU', 'G01': 'GPS', 'D01': 'DRIVER'}
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1240, size=68, max_words=3, speakers=SPK, hide=[(B['cta'], END)],
                emphasis={'lock', 'ninety', 'realize', 'money', 'down', 'house', 'answer', 'id', 'yours', 'you', 'cemetery', 'tunnel',
                          'exit', 'head', 'backwards', 'home'})
