"""VIDEO_011 EDL — "Benched · Part 1" (2dEDIT, real 2D). Sports drama.

Hook (in medias res): frame 0 = the scoreboard. 0:03 left, down by two, and the best player in the gym is on the bench.
"That's you." Then the flashback: tryouts, the laughter, water bottles, 500 shots a night, the janitor's viral video.
Back to the final: Tyler fouls out, the crowd chants 23, Coach: "You. Get in." Choice: shoot / drive / pass -> frame 0.
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


END = DURATION = round(e('N15') + 1.4, 2)

B = dict(
    bench=s('N02'), you=s('N03'), flash=s('N04'), t1=s('T1'), laugh=s('N05'), c1=s('C1'), night=s('N06'), shots=s('N07'),
    janitor=s('N08'), record=w('N08', 'record'), views=s('N09'), except_=s('N10'), t2=s('T2'), crowd=s('N11'), fouls=w('N11', 'fouls'),
    number=w('N11', 'number'), turn=s('N12'), c2=s('C2'), walk=s('N13'), choice=s('N14') - 0.1,
)


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


FB = ['freeze_tint']                         # flashback grade

SEGMENTS = [
    S(0.0, B['bench'], 'SCORE', zoom=Z((0, 1.0, 0.5, 0.5), (B['bench'], 1.12, 0.5, 0.5))),
    S(B['bench'], B['you'], 'BENCH', zoom=Z((B['bench'], 1.0, 0.5, 0.5), (B['you'], 1.2, 0.3, 0.62))),
    S(B['you'], B['flash'], 'FACE', zoom=Z((B['you'], 1.0, 0.5, 0.45), (B['you'] + 0.06, 1.15, 0.5, 0.42), (B['flash'], 1.2, 0.5, 0.42))),
    S(B['flash'], B['t1'], 'TRYOUT', fx=FB, zoom=Z((B['flash'], 1.0, 0.5, 0.5), (B['t1'], 1.08, 0.5, 0.55))),
    S(B['t1'], B['laugh'], 'TYLER', fx=FB),
    S(B['laugh'], B['c1'], 'TRYOUT', fx=FB, zoom=Z((B['laugh'], 1.1, 0.5, 0.5), (B['c1'], 1.2, 0.6, 0.45)), shake=[(B['laugh'] + 0.3, B['c1'], 3)]),
    S(B['c1'], B['night'], 'COACH', fx=FB),
    S(B['night'], B['janitor'], 'NIGHT', zoom=Z((B['night'], 1.0, 0.5, 0.5), (B['shots'], 1.05, 0.5, 0.5), (B['janitor'], 1.15, 0.55, 0.45))),
    S(B['janitor'], B['views'], 'JANITOR', zoom=Z((B['janitor'], 1.0, 0.5, 0.5), (B['record'], 1.1, 0.4, 0.5), (B['views'], 1.18, 0.35, 0.5))),
    S(B['views'], B['except_'], 'VIEWS', zoom=Z((B['views'], 1.0, 0.5, 0.5), (B['except_'], 1.2, 0.5, 0.45))),
    S(B['except_'], B['t2'], 'SIDELINE', zoom=Z((B['except_'], 1.0, 0.5, 0.5), (B['t2'], 1.1, 0.5, 0.45))),
    S(B['t2'], B['crowd'], 'TYLER'),
    S(B['crowd'], B['turn'], 'CROWD', zoom=Z((B['crowd'], 1.0, 0.5, 0.5), (B['number'], 1.06, 0.5, 0.5), (B['number'] + 0.05, 1.2, 0.5, 0.48),
                                           (B['turn'], 1.25, 0.5, 0.48)), shake=[(B['number'], B['turn'], 4)]),
    S(B['turn'], B['walk'], 'COACH', zoom=Z((B['turn'], 1.0, 0.5, 0.45), (B['c2'] - 0.05, 1.1, 0.5, 0.45), (B['c2'] + 0.04, 1.3, 0.5, 0.42),
                                          (B['walk'], 1.32, 0.5, 0.42))),
    S(B['walk'], B['choice'], 'WALK', zoom=Z((B['walk'], 1.0, 0.5, 0.5), (B['choice'], 1.1, 0.5, 0.5))),
    S(B['choice'], END, 'SCORE', zoom=Z((B['choice'], 1.0, 0.5, 0.5), (END, 1.0, 0.5, 0.5))),
]

OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50,
         cols=[([(0, 'STATE CHAMPIONSHIP')], [(0, '0:03 · Q4'), (B['flash'], '2 MONTHS AGO'), (B['night'], '11:47 PM'),
                                             (B['views'], 'TODAY'), (B['except_'], '0:03 · Q4')]),
               ([(0, 'SCORE')], [(0, '58 – 60')]),
               ([(0, 'YOUR MINUTES')], [(0, '0'), (B['c2'] + 0.4, 'IN')])]),
    dict(type='title', font='condensed', t0=B['you'] + 0.5, t1=B['flash'] + 0.3, y=760, stroke=6, spacing=-10,
         lines=[('BENCHED', 160, (255, 255, 255)), ('P A R T   1', 54, (230, 40, 45))]),
    dict(type='choice', t0=B['choice'], t1=END, y=1460, header='3 SECONDS. YOUR CALL.',
         options=['TAKE THE THREE FOR THE WIN', 'DRIVE IN FOR THE TIE', 'PASS IT'],
         footer='COMMENT 1, 2 OR 3  ·  TOP COMMENT = PART 2', stagger=0.9),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=78, max_words=4,
                speakers={'T1': 'TYLER', 'T2': 'TYLER', 'C1': 'COACH', 'C2': 'COACH'},
                hide=[(B['choice'] + 0.2, END)],
                emphasis={'championship', 'bench', "that's", 'shoes', 'grandpa', 'loudest', 'water', 'practiced', 'hundred',
                          'janitor', 'record', 'million', 'except', 'fouls', 'twenty-three', 'get', 'watching', 'three', 'comment'})
