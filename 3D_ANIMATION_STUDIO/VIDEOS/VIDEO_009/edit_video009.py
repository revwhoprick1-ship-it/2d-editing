"""VIDEO_009 EDL — "They Knock · Part 1" (2dEDIT, real 2D): smart, fast zombies; you + Bob, Lawrence, Justin in room 204.

Hook: frame 0 = the classroom door, a shape behind the glass. "They don't break down doors anymore... They knock." KNOCK KNOCK.
Ending: the choice card, then the knocking starts again -> frame 0.
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


END = DURATION = round(e('N16') + 1.4, 2)

B = dict(
    knock=w('N02', 'knock'), title=e('N02') + 0.15, flash=s('N03'), run=w('N04', 'run'), traps=w('N04', 'traps'), phone=w('N04', 'phone'),
    wide=s('N05'), bob=w('N17', 'bob'), law=w('N17', 'lawrence'), jus=w('N17', 'justin'), b1=s('B1'), j1=s('J1'),
    door2=s('N06'), z1=s('Z1'), l1=s('L1'), window=s('N07'), up=w('N08', 'up'), text=s('N09'), msg=s('N10'), stops=s('N11'),
    vent=s('N12'), b2=s('B2'), vent2=s('N13'), choice=s('N15') - 0.1, again=END - 0.9,
)


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


SEGMENTS = [
    S(0.0, B['flash'], 'DOOR', zoom=Z((0, 1.0, 0.5, 0.45), (B['knock'] - 0.05, 1.08, 0.5, 0.42), (B['knock'] + 0.04, 1.22, 0.5, 0.4), (B['flash'], 1.28, 0.5, 0.4)),
      shake=[(B['knock'], B['knock'] + 0.25, 10), (B['knock'] + 0.35, B['knock'] + 0.6, 10)]),
    S(B['flash'], B['wide'], 'FLASH', fx=['freeze_tint'] if False else [], zoom=Z((B['flash'], 1.0, 0.5, 0.5), (B['wide'], 1.08, 0.5, 0.5))),
    S(B['wide'], B['b1'], 'WIDE', zoom=Z((B['wide'], 1.0, 0.5, 0.5), (B['b1'], 1.08, 0.5, 0.55))),
    S(B['b1'], B['j1'], 'BOB', zoom=Z((B['b1'], 1.0, 0.5, 0.45), (B['j1'], 1.06, 0.5, 0.45))),
    S(B['j1'], B['door2'], 'JUSTIN', zoom=Z((B['j1'], 1.06, 0.5, 0.45), (B['door2'], 1.0, 0.5, 0.45)), shake=[(B['j1'], B['j1'] + 0.4, 5)]),
    S(B['door2'], B['l1'], 'DOOR', zoom=Z((B['door2'], 1.0, 0.5, 0.45), (B['z1'], 1.12, 0.5, 0.4), (B['l1'], 1.3, 0.5, 0.38))),
    S(B['l1'], B['window'], 'LAWRENCE', zoom=Z((B['l1'], 1.0, 0.5, 0.45), (B['window'], 1.1, 0.5, 0.45))),
    S(B['window'], B['text'], 'WINDOW', zoom=Z((B['window'], 1.0, 0.5, 0.5), (B['up'] - 0.05, 1.12, 0.5, 0.55), (B['up'] + 0.05, 1.35, 0.5, 0.6),
                                              (B['text'], 1.4, 0.5, 0.6))),
    S(B['text'], B['stops'], 'PHONE', zoom=Z((B['text'], 1.0, 0.5, 0.5), (B['msg'] - 0.05, 1.08, 0.5, 0.5), (B['msg'] + 0.05, 1.3, 0.5, 0.48),
                                             (B['stops'], 1.32, 0.5, 0.48)), shake=[(B['msg'], B['msg'] + 0.3, 6)]),
    S(B['stops'], B['vent'], 'DOOR', zoom=Z((B['stops'], 1.0, 0.5, 0.5), (B['vent'], 1.05, 0.5, 0.5))),
    S(B['vent'], B['b2'], 'VENT', zoom=Z((B['vent'], 1.0, 0.5, 0.5), (B['b2'], 1.2, 0.5, 0.45)), shake=[(B['vent'] + 0.6, B['b2'], 3)]),
    S(B['b2'], B['vent2'], 'BOB', zoom=Z((B['b2'], 1.1, 0.5, 0.45), (B['vent2'], 1.15, 0.5, 0.45))),
    S(B['vent2'], B['choice'], 'VENT', zoom=Z((B['vent2'], 1.0, 0.5, 0.5), (B['choice'], 1.3, 0.5, 0.42)), shake=[(B['vent2'], B['choice'], 6)]),
    S(B['choice'], B['again'], 'WIDE', zoom=Z((B['choice'], 1.0, 0.5, 0.5), (B['again'], 1.05, 0.5, 0.5))),
    S(B['again'], END, 'DOOR', zoom=Z((B['again'], 1.0, 0.5, 0.45), (END, 1.0, 0.5, 0.45)), shake=[(B['again'] + 0.3, B['again'] + 0.55, 10)]),
]

HUD_LABEL = 'DAY 3 · OUTBREAK'
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50,
         cols=[([(0, HUD_LABEL)], [(0, '4:12 PM'), (B['flash'], '3 DAYS AGO'), (B['wide'], '4:10 PM'), (B['window'], '4:11 PM'),
                                   (B['vent'], '4:12 PM')]),
               ([(0, 'ROOM')], [(0, '204')]),
               ([(0, 'SURVIVORS')], [(0, '4'), (B['vent2'], '4?')])]),
    dict(type='title', font='condensed', t0=B['title'], t1=B['flash'] + 1.2, y=760, stroke=6, spacing=-10,
         lines=[('THEY KNOCK', 150, (255, 255, 255)), ('P A R T   1', 54, (230, 40, 45))]),
    dict(type='text2d', t0=B['bob'], t1=B['b1'], text='BOB', x=300, y=1080, size=64, emph=('bob',)),
    dict(type='text2d', t0=B['law'], t1=B['b1'], text='LAWRENCE', x=560, y=980, size=64, emph=('lawrence',)),
    dict(type='text2d', t0=B['jus'], t1=B['b1'], text='JUSTIN', x=820, y=1080, size=64, emph=('justin',)),
    dict(type='choice', t0=B['choice'], t1=B['again'], y=900, header='YOU HAVE 10 SECONDS',
         options=['RUN FOR THE HALLWAY', 'CLIMB ONTO THE ROOF', 'HIDE IN THE SUPPLY CLOSET'],
         footer='COMMENT 1, 2 OR 3  ·  CHOOSE WRONG = SOMEONE DIES', stagger=0.9),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1400, size=78, max_words=4,
                speakers={'B1': 'BOB', 'B2': 'BOB', 'J1': 'JUSTIN', 'L1': 'LAWRENCE', 'Z1': 'MR. PETERSON?'},
                hide=[(B['choice'] + 0.2, END), (B['bob'], B['b1'])],
                emphasis={'doors', 'knock', 'slow', 'run', 'phone', 'answer', 'obviously', 'teacher', 'safe', 'bitten', 'full',
                          'window', 'text', 'two-oh-four', 'stops', 'vent', 'never', 'ten', 'closet', 'wrong'})
