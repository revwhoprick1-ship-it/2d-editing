"""VIDEO_010 EDL — "Last Bus · Part 2" (2dEDIT, real 2D). The audience chose 2: SMASH THE WINDOW.

Hook: frame 0 = you swinging the emergency hammer at the fogged window, the top comment card on screen, "You chose the window."
Ending: the bus is back, you in your seat already... choice card -> the intact window again (frame 0).
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
    swing=w('N02', 'swing'), explodes=w('N02', 'explodes'), mirror=s('D1') - 0.2, climb=s('N03'), drop=w('N03', 'drop'),
    fade=s('N04'), them=s('N05'), stopped=s('N06'), tilts=w('N07', 'tilts'), walking=w('N07', 'walking'), run=s('N08'),
    stop=w('N08', 'stop'), poster=s('N09'), missing=w('N09', 'missing'), phone=s('N10'), date=s('N11'), lights=s('N12'),
    doors=w('N12', 'doors'), d2=s('D2'), inside=s('N13'), seat=s('N14'), yourface=w('N14', 'face'), choice=s('N15') - 0.1,
    loopback=END - 0.5,
)


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


SEGMENTS = [
    S(0.0, B['mirror'], 'SMASH', zoom=Z((0, 1.0, 0.5, 0.5), (B['explodes'] - 0.05, 1.05, 0.5, 0.5), (B['explodes'] + 0.04, 1.25, 0.5, 0.45),
                                        (B['mirror'], 1.3, 0.5, 0.45)),
      shake=[(B['explodes'], B['explodes'] + 0.6, 22)], flash=[(B['explodes'], 0.05)]),
    S(B['mirror'], B['climb'], 'MIRROR', zoom=Z((B['mirror'], 1.3, 0.5, 0.35), (B['climb'], 1.4, 0.5, 0.33))),
    S(B['climb'], B['them'], 'ROAD', zoom=Z((B['climb'], 1.0, 0.5, 0.5), (B['fade'], 1.0, 0.5, 0.5), (B['them'], 1.15, 0.5, 0.45)),
      shake=[(B['drop'] + 0.3, B['drop'] + 0.6, 12)]),
    S(B['them'], B['run'], 'FOG', zoom=Z((B['them'], 1.0, 0.5, 0.5), (B['stopped'], 1.15, 0.5, 0.47), (B['tilts'], 1.2, 0.5, 0.47),
                                         (B['tilts'] + 0.05, 1.4, 0.5, 0.45), (B['run'], 1.45, 0.5, 0.45))),
    S(B['run'], B['poster'], 'RUN', shake=[(B['run'], B['stop'], 4)]),
    S(B['poster'], B['phone'], 'STOP', zoom=Z((B['poster'], 1.0, 0.5, 0.5), (B['missing'] - 0.05, 1.1, 0.5, 0.5), (B['missing'] + 0.05, 1.45, 0.62, 0.45),
                                            (B['phone'], 1.5, 0.62, 0.45))),
    S(B['phone'], B['lights'], 'PHONE', zoom=Z((B['phone'], 1.0, 0.5, 0.5), (B['date'], 1.1, 0.5, 0.45), (B['date'] + 1.0, 1.4, 0.5, 0.4),
                                             (B['lights'], 1.45, 0.5, 0.4))),
    S(B['lights'], B['inside'], 'ARRIVE', zoom=Z((B['lights'], 1.0, 0.5, 0.5), (B['d2'], 1.15, 0.5, 0.45), (B['inside'], 1.25, 0.5, 0.45))),
    S(B['inside'], B['choice'], 'INSIDE', zoom=Z((B['inside'], 1.0, 0.5, 0.5), (B['seat'], 1.05, 0.5, 0.5), (B['yourface'] - 0.05, 1.3, 0.3, 0.62),
                                                (B['yourface'] + 0.05, 1.8, 0.25, 0.66), (B['choice'], 1.85, 0.25, 0.66)),
      flash=[(B['yourface'], 0.05)], shake=[(B['yourface'], B['yourface'] + 0.4, 10)]),
    S(B['choice'], B['loopback'], 'INSIDE', zoom=Z((B['choice'], 1.0, 0.5, 0.5), (B['loopback'], 1.04, 0.5, 0.5))),
    S(B['loopback'], END, 'SMASH'),
]

TOP = dict(handle='@ZylaxVShark', likes=6,
           text='Guys lets just agree for 2 break the window why would you want to be hunted forever so vote me')
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50,
         cols=[([(0, 'NIGHT BUS · ROUTE 13')], [(0, '12:00 AM'), (B['date'], '1 YEAR LATER'), (B['lights'], '12:00 AM')]),
               ([(0, 'NEXT STOP')], [(0, 'YOU'), (B['climb'], '—'), (B['doors'], 'YOU')]),
               ([(0, 'PASSENGERS')], [(0, '1'), (B['climb'], '0'), (B['inside'], '15')])]),
    dict(type='comment', t0=0.05, t1=B['mirror'] - 0.1, y=620, chose='YOU CHOSE 2 · SMASH THE WINDOW', label='TOP COMMENT · PART 1', **TOP),
    dict(type='title', font='condensed', t0=B['mirror'], t1=B['climb'] + 0.4, y=740, stroke=6, spacing=-10,
         lines=[('LAST BUS', 150, (255, 255, 255)), ('P A R T   2', 54, (230, 40, 45))]),
    dict(type='choice', t0=B['choice'], t1=B['loopback'], y=900, header='WHAT DO YOU DO?',
         options=['GET BACK ON THE BUS', 'RUN INTO THE FOG', 'CALL MOM BACK'],
         footer='COMMENT 1, 2 OR 3  ·  TOP COMMENT = PART 3', stagger=0.9),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=78, max_words=4,
                speakers={'D1': 'DRIVER', 'D2': 'DRIVER'},
                hide=[(B['choice'] + 0.2, END)],
                emphasis={'window', 'explodes', 'exit', 'drop', 'fade', 'passengers', 'waving', 'tilts', 'toward', 'run',
                          'missing', 'forty-seven', 'year', 'headlights', 'missed', 'waving', 'face', 'mom', 'three'})
