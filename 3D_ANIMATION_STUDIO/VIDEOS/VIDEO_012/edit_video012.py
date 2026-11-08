"""VIDEO_012 EDL — "Don't Touch The Vase · Part 1" (2dEDIT, real 2D horror with real jumpscares).

Retention plan: frame 0 = the vase already teetering + voice; it shatters within ~2.5 s, with a 3-frame subliminal face.
A new picture every 1-2.5 s. Scares are built (silence, slow push, held breath), not random:
  JS1 dinner: Dad slowly looks up... "Why did you let it out?" -> his face stretches into the camera (glitch, red, scream)
  fake-out: "It stops right outside the door. And then... nothing." (1.4 s of silence, nothing happens)
  JS2 mirror: the reflection is fine... for a beat... then a cracked porcelain face is right behind your shoulder
  JS3 last second: after the choice card, the quiet... then it lunges at the camera -> cut to frame 0 (the vase).
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
FPS = 30
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
LS = {l['id']: (l['start'], l['end']) for l in _T['lines']}
WORDS = _T['words']


def s(i):
    return LS[i][0]


def e(i):
    return LS[i][1]


def w(line, word, nth=1, end=False):
    k = 0
    for x in WORDS:
        if x['line'] == line and x['text'].lower().strip('.!?,') == word.lower():
            k += 1
            if k == nth:
                return round(x['end'] if end else x['start'], 3)
    raise KeyError((line, word))


END = DURATION = round(e('N20') + 3.2, 2)

B = dict(
    crash=w('N02', 'broke'), sub=e('N02') + 0.05, smoke=e('N02') + 0.25, walls=w('N03', 'walls'),
    dinner=s('N04'), mom=s('N05'), sister=s('N06'), dad=s('N07'), d1=s('D1'), js1=e('D1') + 0.02, normal=s('N08'),
    power=s('N09'), out=w('N09', 'out'), phone=s('N10'), mom2=s('N11'), d2=s('D2'), window=s('N12'), car=w('N12', 'car'),
    stairs=s('N13'), fours=w('N13', 'fours'), bath=s('N14'), lock=w('N14', 'bathroom'), nothing=w('N15', 'nothing'),
    mirror=s('N16'), js2=e('N16') + 0.55, dies=s('N17'), whisper=s('N18'), d3=s('D3'), choice=s('N19') - 0.1,
)
B['js3'] = END - 0.75


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


JS = 0.55                                      # jumpscare hold
SEGMENTS = [
    S(0.0, B['crash'], 'VASE', zoom=Z((0, 1.15, 0.5, 0.42), (B['crash'], 1.0, 0.5, 0.45))),
    S(B['crash'], B['sub'], 'VASE', flash=[(B['crash'], 0.05)], shake=[(B['crash'], B['crash'] + 0.5, 20)],
      zoom=Z((B['crash'], 1.0, 0.5, 0.5), (B['sub'], 1.08, 0.5, 0.55))),
    S(B['sub'], B['sub'] + 0.1, 'SCARE', fx_t=[(B['sub'], B['sub'] + 0.1, 'glitch')]),          # subliminal: 3 frames
    S(B['sub'] + 0.1, B['dinner'], 'SMOKE', zoom=Z((B['sub'] + 0.1, 1.0, 0.5, 0.5), (B['walls'], 1.1, 0.7, 0.45), (B['dinner'], 1.15, 0.75, 0.45))),
    S(B['dinner'], B['mom'], 'DINNER', zoom=Z((B['dinner'], 1.0, 0.5, 0.5), (B['mom'], 1.06, 0.5, 0.5))),
    S(B['mom'], B['sister'], 'MOM', fx=['chroma'], zoom=Z((B['mom'], 1.0, 0.5, 0.45), (B['sister'], 1.25, 0.5, 0.42))),
    S(B['sister'], B['dad'], 'SISTER', zoom=Z((B['sister'], 1.0, 0.5, 0.45), (B['dad'] - 0.8, 1.05, 0.5, 0.6), (B['dad'], 1.25, 0.5, 0.65))),
    S(B['dad'], B['js1'], 'DAD', zoom=Z((B['dad'], 1.0, 0.5, 0.45), (B['js1'], 1.3, 0.5, 0.42))),
    S(B['js1'], B['js1'] + JS, 'DAD', flash=[(B['js1'], 0.04)], shake=[(B['js1'], B['js1'] + JS, 30)],
      fx_t=[(B['js1'], B['js1'] + JS, 'glitch'), (B['js1'] + 0.2, B['js1'] + 0.35, 'redflash')],
      zoom=Z((B['js1'], 1.3, 0.5, 0.42), (B['js1'] + 0.12, 1.9, 0.5, 0.4), (B['js1'] + JS, 2.1, 0.5, 0.4))),
    S(B['js1'] + JS, B['power'], 'DINNER', zoom=Z((B['js1'] + JS, 1.0, 0.5, 0.5), (B['power'], 1.05, 0.5, 0.5))),
    S(B['power'], B['phone'], 'ROOM', zoom=Z((B['power'], 1.0, 0.5, 0.5), (B['phone'], 1.1, 0.5, 0.5))),
    S(B['phone'], B['mom2'], 'PHONE', zoom=Z((B['phone'], 1.0, 0.5, 0.5), (B['mom2'], 1.15, 0.5, 0.45))),
    S(B['mom2'], B['window'], 'HALL', zoom=Z((B['mom2'], 1.0, 0.5, 0.5), (B['d2'], 1.05, 0.5, 0.55), (B['window'], 1.3, 0.5, 0.65))),
    S(B['window'], B['stairs'], 'WINDOW', zoom=Z((B['window'], 1.0, 0.5, 0.5), (B['car'], 1.1, 0.5, 0.55), (B['stairs'], 1.25, 0.5, 0.6))),
    S(B['stairs'], B['bath'], 'STAIRS', zoom=Z((B['stairs'], 1.0, 0.5, 0.55), (B['fours'], 1.15, 0.5, 0.6), (B['bath'], 1.45, 0.5, 0.62)),
      fx_t=[(B['fours'], B['fours'] + 0.1, 'glitch')]),
    S(B['bath'], B['mirror'], 'BATH', shake=[(B['lock'], B['lock'] + 0.3, 12)], zoom=Z((B['bath'], 1.0, 0.5, 0.5), (B['nothing'], 1.08, 0.5, 0.6),
                                                                                       (B['mirror'], 1.2, 0.5, 0.75))),
    S(B['mirror'], B['js2'], 'MIRROR', zoom=Z((B['mirror'], 1.0, 0.5, 0.45), (B['js2'], 1.12, 0.5, 0.42))),
    S(B['js2'], B['js2'] + JS, 'MIRROR', flash=[(B['js2'], 0.04)], shake=[(B['js2'], B['js2'] + JS, 30)],
      fx_t=[(B['js2'], B['js2'] + JS, 'glitch'), (B['js2'] + 0.15, B['js2'] + 0.3, 'invert')],
      zoom=Z((B['js2'], 1.25, 0.62, 0.4), (B['js2'] + 0.1, 1.7, 0.66, 0.38), (B['js2'] + JS, 1.8, 0.66, 0.38))),
    S(B['js2'] + JS, B['choice'], 'BLACK', zoom=Z((B['js2'] + JS, 1.0, 0.5, 0.5), (B['choice'], 1.15, 0.5, 0.45))),
    S(B['choice'], B['js3'], 'FLOOR', zoom=Z((B['choice'], 1.0, 0.5, 0.5), (B['js3'], 1.08, 0.5, 0.55))),
    S(B['js3'], END, 'SCARE', flash=[(B['js3'], 0.04)], shake=[(B['js3'], END, 34)],
      fx_t=[(B['js3'], END, 'glitch'), (B['js3'] + 0.25, B['js3'] + 0.4, 'redflash')],
      zoom=Z((B['js3'], 1.0, 0.5, 0.45), (B['js3'] + 0.15, 1.6, 0.5, 0.42), (END, 1.9, 0.5, 0.42))),
]

SCARES = [(B['sub'], B['sub'] + 0.1), (B['js1'], B['js1'] + JS), (B['js2'], B['js2'] + JS), (B['js3'], END)]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50, hide=SCARES,
         cols=[([(0, "GRANDMA'S HOUSE")], [(0, '6:12 PM'), (B['dinner'], '7:30 PM'), (B['power'], '2:13 AM'), (B['js2'] + JS, '2:16 AM')]),
               ([(0, 'POWER')], [(0, 'ON'), (B['out'], 'OFF')]),
               ([(0, 'BATTERY')], [(0, '23%'), (B['phone'], '4%'), (B['dies'], '0%')])]),
    dict(type='title', font='condensed', t0=B['smoke'] + 0.6, t1=B['dinner'] + 0.3, y=760, stroke=6, spacing=-10,
         lines=[("DON'T TOUCH", 120, (255, 255, 255)), ('THE VASE', 150, (255, 255, 255)), ('P A R T   1', 54, (230, 40, 45))]),
    dict(type='choice', t0=B['choice'], t1=B['js3'] - 0.05, y=980, header='HOW DO YOU SURVIVE?',
         options=['GLUE THE VASE BACK TOGETHER', 'BURN THE PIECES', "RUN TO GRANDMA'S HOUSE"],
         footer='COMMENT 1, 2 OR 3  ·  IF YOU SURVIVE: PART 2', stagger=0.9),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=78, max_words=4,
                speakers={'D1': 'DAD', 'D2': 'MOM?', 'D3': '???'},
                hide=[(B['choice'] + 0.2, END)] + SCARES,
                emphasis={'vase', 'broke', 'walls', 'normal', 'blinked', 'empty', 'dad', 'out', 'power', 'four', 'mom',
                          'something', 'work', 'fours', 'bathroom', 'nothing', 'mirror', 'dies', 'ear', 'yours', 'grandma', 'survive'})
