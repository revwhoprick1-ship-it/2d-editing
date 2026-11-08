"""VIDEO_008 EDL — "Last Bus · Part 1" (2dEDIT, real 2D). Shot times come from the narration words.

Hook: frame 0 = a full night bus; on "blinked" the picture blinks (black) and every seat is empty (HUD 14 -> 1).
Ending: the choice card, then the lights flicker and every passenger is back, staring at you -> frame 0 (full bus).
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


END = DURATION = round(e('N15') + 1.6, 2)

B = dict(
    blink=w('N01', 'blinked', end=True) + 0.02, gone=w('N01', 'gone'), empty=s('N02'), phone=s('N03'), play=w('N03', 'play'),
    turn=w('N04', 'turn'), ends=s('N05'), face=e('N05') + 0.3, driver=s('N06'), face2=e('D2') + 0.2, route=s('N07'),
    you=w('N07', 'you'), window=s('N08'), faces=w('N08', 'faces'), waving=w('N09', 'waving'), button=s('N10'),
    slam=w('N10', 'slam'), driver2=s('D4') - 0.15, ticket=s('N11'), oneway=w('N11', 'one'), mirror=s('N12'),
    noface=w('N12', 'face'), brake=s('N13'), choice=s('N14') - 0.1, back=END - 0.75,
)


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


SEGMENTS = [
    S(0.0, B['empty'], 'BUS', zoom=Z((0, 1.0, 0.5, 0.5), (B['blink'], 1.04, 0.5, 0.5), (B['blink'] + 0.15, 1.15, 0.5, 0.5), (B['empty'], 1.2, 0.5, 0.5)),
      shake=[(B['blink'] + 0.12, B['blink'] + 0.45, 6)]),
    S(B['empty'], B['phone'], 'EMPTY', zoom=Z((B['empty'], 1.0, 0.5, 0.5), (B['phone'], 1.12, 0.5, 0.55))),
    S(B['phone'], B['face'], 'PHONE', zoom=Z((B['phone'], 1.0, 0.5, 0.5), (B['play'], 1.05, 0.5, 0.45), (B['turn'], 1.25, 0.5, 0.42),
                                             (B['turn'] + 0.08, 1.45, 0.5, 0.4), (B['face'], 1.5, 0.5, 0.4)),
      shake=[(B['turn'] + 0.05, B['turn'] + 0.4, 6)]),
    S(B['face'], B['driver'], 'FACE', zoom=Z((B['face'], 1.0, 0.5, 0.45), (B['driver'], 1.1, 0.5, 0.45))),
    S(B['driver'], B['face2'], 'DRIVER', zoom=Z((B['driver'], 1.0, 0.5, 0.5), (B['face2'], 1.15, 0.45, 0.45))),
    S(B['face2'], B['route'], 'FACE', zoom=Z((B['face2'], 1.15, 0.5, 0.45), (B['route'], 1.25, 0.5, 0.45)), shake=[(s('D3'), s('D3') + 0.5, 6)]),
    S(B['route'], B['window'], 'ROUTE', zoom=Z((B['route'], 1.0, 0.5, 0.5), (B['you'] - 0.05, 1.08, 0.5, 0.5), (B['you'] + 0.04, 1.3, 0.5, 0.5),
                                              (B['window'], 1.32, 0.5, 0.5))),
    S(B['window'], B['button'], 'WINDOW', zoom=Z((B['window'], 1.0, 0.5, 0.5), (B['faces'], 1.05, 0.5, 0.5), (B['button'], 1.25, 0.55, 0.45))),
    S(B['button'], B['driver2'], 'BUTTON', zoom=Z((B['button'], 1.0, 0.5, 0.5), (B['slam'], 1.05, 0.5, 0.5), (B['slam'] + 0.05, 1.2, 0.5, 0.45),
                                                  (B['driver2'], 1.22, 0.5, 0.45)), shake=[(B['slam'], B['slam'] + 0.25, 8)]),
    S(B['driver2'], B['ticket'], 'DRIVER', zoom=Z((B['driver2'], 1.15, 0.45, 0.45), (B['ticket'], 1.25, 0.45, 0.45))),
    S(B['ticket'], B['mirror'], 'TICKET', zoom=Z((B['ticket'], 1.0, 0.5, 0.5), (B['oneway'], 1.1, 0.5, 0.5), (B['oneway'] + 0.05, 1.3, 0.5, 0.6),
                                                 (B['mirror'], 1.32, 0.5, 0.6))),
    S(B['mirror'], B['brake'], 'MIRROR', flash=[(B['noface'], 0.05)], shake=[(B['noface'], B['noface'] + 0.4, 12)],
      zoom=Z((B['mirror'], 1.0, 0.5, 0.35), (B['noface'] - 0.05, 1.12, 0.5, 0.33), (B['noface'] + 0.04, 1.45, 0.5, 0.3), (B['brake'], 1.5, 0.5, 0.3))),
    S(B['brake'], B['choice'], 'FACE3', shake=[(B['brake'], B['choice'], 7)], zoom=Z((B['brake'], 1.0, 0.5, 0.45), (B['choice'], 1.12, 0.5, 0.45))),
    S(B['choice'], END, 'BUS', zoom=Z((B['choice'], 1.0, 0.5, 0.5), (B['back'], 1.06, 0.5, 0.5), (B['back'] + 0.1, 1.0, 0.5, 0.5), (END, 1.0, 0.5, 0.5))),
]

OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50,
         cols=[([(0, 'NIGHT BUS · ROUTE 13')], [(0, '11:58 PM'), (B['route'], '11:59 PM'), (B['mirror'], '12:00 AM'), (B['back'], '11:58 PM')]),
               ([(0, 'NEXT STOP')], [(0, 'ELM ST'), (B['you'] - 0.1, 'YOU'), (B['back'], 'ELM ST')]),
               ([(0, 'PASSENGERS')], [(0, '14'), (B['blink'] + 0.15, '1'), (B['back'], '15')])]),
    dict(type='title', font='condensed', t0=B['gone'] + 0.5, t1=B['empty'] + 1.6, y=760, stroke=6, spacing=-10,
         lines=[('LAST BUS', 160, (255, 255, 255)), ('P A R T   1', 54, (230, 40, 45))]),
    dict(type='choice', t0=B['choice'], t1=B['back'], y=900, header='WHAT DO YOU DO?',
         options=['PULL THE EMERGENCY HANDLE', 'SMASH THE WINDOW', 'SIT BACK DOWN'],
         footer='COMMENT 1, 2 OR 3  ·  TOP COMMENT = PART 2', stagger=0.9),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1400, size=78, max_words=4,
                speakers={'D1': 'YOU', 'D3': 'YOU', 'D2': 'DRIVER', 'D4': 'DRIVER'},
                hide=[(B['choice'] + 0.2, END)],
                emphasis={'blinked', 'gone', 'warm', 'recording', 'play', 'look', 'ends', 'stop', 'once',
                          'fog', 'goodbye', 'button', 'ticket', 'way', 'face', 'slowing', 'window', 'comment'})
