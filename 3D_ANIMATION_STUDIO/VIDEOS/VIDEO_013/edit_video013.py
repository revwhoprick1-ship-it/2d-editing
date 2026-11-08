"""VIDEO_013 EDL — "Benched · Part 2" (2dEDIT, real 2D). The audience chose 1: TAKE THE THREE.

Stand-alone hook (works without Part 1): frame 0 = freeze frame, the ball in the air, the clock at 0:00.4, with the voice
"This shot decides the state championship." -> record scratch -> "And the kid who took it... was the water boy."
A 10-second recap montage (re-using Part 1's shots) catches new viewers up, then the play, the slow-motion shot, the rim,
it drops, the gym explodes, Coach hands HIM the water bottle, a college scout makes a call -> choice -> frame 0.
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
    water=w('N02', 'water'), recap=s('N03'), mates=w('N03', 'teammates'), night=s('N04'), viral=w('N04', 'then'),
    chant=s('N05'), until=w('N05', 'until'), chose=s('N06'), ball=s('N07'), d1=s('D1'), two=s('N08'), step=w('N08', 'step'),
    one=s('N09'), go=w('N09', 'go'), rim=s('N10'), drops=s('N11'), explode=s('N12'), tyler=w('N12', 'tyler'), janitor=w('N12', 'janitor'),
    coach=s('N13'), d2=s('D2'), scout=s('N14'), choice=s('N15') - 0.1,
)
B['slow_end'] = B['rim'] - 0.05
B['clang'] = B['rim'] + 0.55


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


RECAP = ['freeze_tint']
SEGMENTS = [
    S(0.0, B['water'] - 0.05, 'AIR', zoom=Z((0, 1.15, 0.5, 0.42), (B['water'], 1.0, 0.5, 0.45))),
    S(B['water'] - 0.05, B['recap'], 'AIR', fx=['freeze_tint'], zoom=Z((B['water'] - 0.05, 1.0, 0.5, 0.45), (B['water'] + 0.05, 1.3, 0.35, 0.6),
                                                                   (B['recap'], 1.35, 0.35, 0.6))),
    S(B['recap'], B['mates'], 'R_BENCH', fx=RECAP, whip_in=(1, 3)),
    S(B['mates'], B['night'], 'R_TRYOUT', fx=RECAP, whip_in=(-1, 3)),
    S(B['night'], B['viral'], 'R_NIGHT', fx=RECAP, whip_in=(1, 3)),
    S(B['viral'], B['chant'], 'R_VIEWS', fx=RECAP, whip_in=(-1, 3)),
    S(B['chant'], B['until'], 'R_CROWD', fx=RECAP, whip_in=(1, 3)),
    S(B['until'], B['chose'], 'R_COACH', fx=RECAP, whip_in=(-1, 3)),
    S(B['chose'], B['ball'], 'AIR', zoom=Z((B['chose'], 1.0, 0.5, 0.45), (B['ball'], 1.1, 0.5, 0.45))),
    S(B['ball'], B['d1'], 'PLAY', zoom=Z((B['ball'], 1.0, 0.5, 0.5), (B['d1'], 1.08, 0.5, 0.5))),
    S(B['d1'], B['two'], 'DEFENDER', zoom=Z((B['d1'], 1.0, 0.5, 0.45), (B['two'], 1.12, 0.5, 0.45))),
    S(B['two'], B['go'], 'PLAY', zoom=Z((B['two'], 1.08, 0.5, 0.5), (B['step'], 1.08, 0.5, 0.5), (B['step'] + 0.05, 1.25, 0.45, 0.5),
                                       (B['go'], 1.3, 0.45, 0.48)), shake=[(B['step'], B['step'] + 0.2, 6)]),
    S(B['go'], B['go'] + 1.0, 'SLOW', zoom=Z((B['go'], 1.0, 0.5, 0.5), (B['go'] + 1.0, 1.15, 0.5, 0.45))),
    S(B['go'] + 1.0, B['go'] + 1.6, 'R_COACHF', fx=[]),
    S(B['go'] + 1.6, B['go'] + 2.2, 'R_TYLERF'),
    S(B['go'] + 2.2, B['slow_end'], 'SLOW', zoom=Z((B['go'] + 2.2, 1.15, 0.5, 0.45), (B['slow_end'], 1.3, 0.55, 0.4))),
    S(B['slow_end'], B['drops'], 'RIM', shake=[(B['clang'], B['clang'] + 0.3, 10)],
      zoom=Z((B['slow_end'], 1.0, 0.5, 0.45), (B['drops'], 1.15, 0.5, 0.45))),
    S(B['drops'], B['explode'], 'RIM', flash=[(B['drops'] + 0.15, 0.08)], shake=[(B['drops'] + 0.15, B['explode'], 18)],
      zoom=Z((B['drops'], 1.15, 0.5, 0.45), (B['drops'] + 0.2, 1.3, 0.5, 0.45), (B['explode'], 1.35, 0.5, 0.45))),
    S(B['explode'], B['tyler'], 'CELEB', shake=[(B['explode'], B['explode'] + 1.0, 8)], zoom=Z((B['explode'], 1.0, 0.5, 0.5), (B['tyler'], 1.05, 0.5, 0.5))),
    S(B['tyler'], B['janitor'], 'R_TYLERF', zoom=Z((B['tyler'], 1.0, 0.5, 0.45), (B['janitor'], 1.1, 0.5, 0.45))),
    S(B['janitor'], B['coach'], 'JANITOR', zoom=Z((B['janitor'], 1.0, 0.5, 0.45), (B['coach'], 1.12, 0.5, 0.42))),
    S(B['coach'], B['scout'], 'COACH2', zoom=Z((B['coach'], 1.0, 0.5, 0.5), (B['d2'], 1.1, 0.5, 0.45), (B['scout'], 1.2, 0.5, 0.42))),
    S(B['scout'], B['choice'], 'SCOUT', zoom=Z((B['scout'], 1.0, 0.5, 0.5), (B['choice'], 1.25, 0.6, 0.42))),
    S(B['choice'], END, 'CELEB', zoom=Z((B['choice'], 1.0, 0.5, 0.5), (END, 1.04, 0.5, 0.5))),
]

OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50,
         cols=[([(0, 'STATE CHAMPIONSHIP')], [(0, '0:00.4'), (B['recap'], 'ALL SEASON'), (B['chose'], '0:03 · Q4'), (B['two'], '0:02'),
                                             (B['one'], '0:01'), (B['go'] + 0.4, '0:00'), (B['explode'], 'FINAL')]),
               ([(0, 'SCORE')], [(0, '58 – 60'), (B['drops'] + 0.15, '61 – 60')]),
               ([(0, 'HIS MINUTES')], [(0, '0:03'), (B['recap'], '0'), (B['chose'], '0:03')])]),
    dict(type='stamp', t0=B['water'], t1=B['recap'] - 0.05, text='THE WATER BOY', x=0.5, y=0.68, size=110, rot=-6, color=(230, 40, 45)),
    dict(type='text2d', t0=B['recap'] + 0.1, t1=B['chose'] - 0.1, text='PREVIOUSLY', y=330, size=60, emph=('previously',)),
    dict(type='comment', t0=B['chose'] + 0.2, t1=B['ball'] - 0.05, y=640, chose='YOU CHOSE 1 · TAKE THE THREE', label='TOP COMMENT · PART 1',
         handle='@the_solo_guy18', likes=315, text='1 COME ON MAN; THATS TOOO EASY'),
    dict(type='title', font='condensed', t0=B['explode'] + 0.1, t1=B['tyler'] - 0.1, y=700, stroke=8, spacing=-10,
         lines=[('BENCHED', 150, (255, 255, 255)), ('P A R T   2', 54, (230, 40, 45))]),
    dict(type='choice', t0=B['choice'], t1=END, y=1180, header='WHAT DOES HE DO NOW?',
         options=['FORGIVE COACH', 'TAKE THE COLLEGE OFFER', 'COACH FILLS THE WATER BOTTLES'],
         footer='COMMENT 1, 2 OR 3  ·  TOP COMMENT = PART 3', stagger=0.9),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=78, max_words=4,
                speakers={'D1': 'DEFENDER', 'D2': 'COACH'},
                hide=[(B['choice'] + 0.2, END), (B['water'] - 0.05, B['recap'])],
                emphasis={'championship', 'water', 'bench', 'shoes', 'hundred', 'viral', 'chanted', 'three', 'seconds', 'step',
                          'go', 'rim', 'drops', 'explodes', 'crying', 'bottle', "yours", 'college', 'comment'})
