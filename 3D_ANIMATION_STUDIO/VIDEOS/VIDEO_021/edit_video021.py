"""VIDEO_021 EDL — "My Mother Isn't Real" (2dEDIT horror choice game, ~60 s). Lore: VIDEOS/MOTHER_LORE.md.
Rules: frame 0 = you at the forbidden basement door + Mom right behind you; story only moves forward (the crash is a
0.3-1 s memory glitch, never an 'X years earlier' scene). Jumpscares are INSTANT and unannounced: no music drop, no riser,
they land mid-line / mid-count / mid-card. Choice card at the end with FOLLOW + hidden-detail hint; cliffhanger 'Pick me.'"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
FPS = 30
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
LS = {l['id']: (l['start'], l['end']) for l in _T['lines']}
ORDER = [l['id'] for l in _T['lines']]
WORDS = _T['words']
END = DURATION = round(_T['duration'], 2)


def s(i):
    return LS[i][0]


def e(i):
    return LS[i][1]


def w_at(lid, word):
    """Start time of the first word in line lid that contains `word`."""
    for w in WORDS:
        if w['line'] == lid and word in w['text'].lower():
            return w['start']
    return s(lid)


SHOT = {'O01': 'HOOK', 'N01': 'KITCHEN', 'N02': 'MONTAGE', 'O02': 'CU_O', 'N03': 'CAR', 'Q01': 'CAR', 'M01': 'CU_M', 'O03': 'CU_O',
        'N04': 'HALL', 'P01': 'FLOOR', 'M02': 'CU_MN', 'P02': 'DOOR', 'N05': 'STAIRS', 'P03': 'BASEMENT', 'O04': 'UPSTAIRS',
        'P04': 'CU_P', 'O05': 'CU_OS', 'N06': 'BOTH', 'X01': 'BOTH'}
GAP_SHOT = {'O01': 'HOOK', 'M01': 'KITCHEN', 'N04': 'HALL', 'P01': 'FLOOR', 'N05': 'DOOR', 'P03': 'BASEMENT', 'O04': 'BASEMENT',
            'N03': 'CAR', 'X01': 'BOTH'}

JS = 0.42
B = dict(
    kitchen=s('N01'), car=s('N03') - 0.2, kitchen2=s('M01') - 0.5, js1=w_at('O03', 'love'), night=s('N04') - 0.6,
    knocks=[s('P01') - 1.3, s('P01') - 0.9, s('P01') - 0.5], door=s('N05') - 0.6, js2=w_at('N05', 'thirteen'),
    basement=s('P03') - 1.0, upstairs=s('O04') - 0.5, both=s('N06'), choice=e('N06') + 0.15,
)
B['js3'] = B['choice'] + 1.7
B['pick'] = s('X01')
B['montage'] = [s('N02'), w_at('N02', 'same'), w_at('N02', 'smile') - 0.25]


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job)
    if job is not None:
        d['map'] = [(t0, t0 * FPS), (t1, t1 * FPS)]
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


SEGMENTS = []
prev_end = 0.0
for i, lid in enumerate(ORDER):
    st, en = LS[lid]
    nxt = LS[ORDER[i + 1]][0] if i + 1 < len(ORDER) else END
    if st - prev_end > 0.05:
        SEGMENTS.append(S(prev_end, st, GAP_SHOT.get(lid, SHOT[lid])))
    hold = nxt if nxt - en < 0.9 else en + 0.3
    SEGMENTS.append(S(st, hold, SHOT[lid]))
    prev_end = hold
if END - prev_end > 0.05:
    SEGMENTS.append(S(prev_end, END, 'BOTH'))
_runs = []
for sg in SEGMENTS:
    if _runs and _runs[-1]['src'] == sg['src']:
        _runs[-1]['t1'] = sg['t1']
    else:
        _runs.append(dict(sg))
SEGMENTS = []
for k, r in enumerate(_runs):
    a, b = (1.0, 1.06) if k % 2 == 0 else (1.06, 1.0)
    SEGMENTS.append(S(r['t0'], r['t1'], r['src'], zoom=Z((r['t0'], a, 0.5, 0.45), (r['t1'], b, 0.5, 0.45))))


def override(t0, t1, job, **kw):
    global SEGMENTS
    out = []
    for sg in SEGMENTS:
        if sg['t1'] <= t0 or sg['t0'] >= t1:
            out.append(sg)
            continue
        if sg['t0'] < t0:
            out.append(dict(sg, t1=t0))
        if sg['t1'] > t1:
            out.append(dict(sg, t0=t1))
    out.append(S(t0, t1, job, **kw))
    SEGMENTS = sorted(out, key=lambda x: x['t0'])


# montage: the same morning, three times, hard cuts (punch-in each time)
for k, t0 in enumerate(B['montage']):
    t1 = B['montage'][k + 1] if k + 1 < 3 else e('N02') + 0.05
    override(t0, t1, 'MONTAGE', zoom=Z((t0, 1.0 + 0.12 * k, 0.5, 0.45), (t1, 1.04 + 0.12 * k, 0.5, 0.45)))
# the crash memory: glitchy, unstable
for sg in SEGMENTS:
    if sg['src'] == 'CAR':
        sg['fx_t'] = [(sg['t0'], sg['t0'] + 0.25, 'glitch'), (sg['t1'] - 0.2, sg['t1'], 'glitch')]
        sg['shake'] = [(sg['t0'], sg['t1'], 4)]
# JS1: 5 frames, mid-word "love". JS2: on "thirteen", a hand grabs your ankle. JS3: mid-card, the lights die and both lunge.
override(B['js1'], B['js1'] + 0.17, 'TRUEFACE', flash=[(B['js1'], 0.03)], shake=[(B['js1'], B['js1'] + 0.17, 30)],
         fx_t=[(B['js1'], B['js1'] + 0.17, 'glitch')], zoom=Z((B['js1'], 1.25, 0.5, 0.42), (B['js1'] + 0.17, 1.4, 0.5, 0.42)))
override(B['js2'], B['js2'] + JS, 'GRAB', flash=[(B['js2'], 0.03)], shake=[(B['js2'], B['js2'] + JS, 34)],
         fx_t=[(B['js2'], B['js2'] + 0.25, 'glitch'), (B['js2'] + 0.1, B['js2'] + 0.3, 'redflash')],
         zoom=Z((B['js2'], 1.3, 0.5, 0.6), (B['js2'] + JS, 1.05, 0.5, 0.55)))
override(B['js3'] - 0.12, B['js3'], None)
override(B['js3'], B['js3'] + JS, 'LUNGE', flash=[(B['js3'], 0.03)], shake=[(B['js3'], B['js3'] + JS, 36)],
         fx_t=[(B['js3'], B['js3'] + JS, 'glitch')], zoom=Z((B['js3'], 1.0, 0.5, 0.45), (B['js3'] + JS, 1.6, 0.5, 0.42)))

SCARES = [(B['js1'], B['js1'] + 0.17), (B['js2'], B['js2'] + JS), (B['js3'] - 0.12, B['js3'] + JS)]
CARD = dict(type='choice', y=980, header='WHICH MOM IS REAL?', options=['THE MOM IN THE BASEMENT', 'THE MOM ON THE STAIRS', 'NEITHER. RUN.'],
            footer='FOLLOW FOR PART 2  ·  ONE HIDDEN DETAIL GIVES IT AWAY', stagger=0.35)
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=48, hide=SCARES,
         cols=[([(0, 'SINCE THE CRASH')], [(0, '730 DAYS'), (B['montage'][1], '731 DAYS'), (B['montage'][2], '732 DAYS'), (B['night'], '732 DAYS')]),
               ([(0, 'MOM')], [(0, 'HOME'), (B['knocks'][0], 'HOME?'), (B['upstairs'], 'x2')]),
               ([(0, 'BASEMENT')], [(0, 'FORBIDDEN'), (B['door'], 'OPEN')])]),
    dict(CARD, t0=B['choice'], t1=B['js3'] - 0.14),
    dict(CARD, t0=B['js3'] + JS + 0.02, t1=END - 0.05, stagger=0.0),
    dict(type='watermark', t0=0.0, t1=END),
]
NAMES = {'N': None, 'M': 'YOU', 'O': 'MOM', 'Q': 'MOM (2 YEARS AGO)', 'P': 'MOM?', 'X': 'BOTH OF THEM'}
SPK = {l['id']: NAMES[l['id'][0]] for l in _T['lines'] if NAMES[l['id'][0]]}
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=74, max_words=4, speakers=SPK, hide=SCARES + [(B['choice'], B['pick'] - 0.05)],
                emphasis={'basement', 'died', 'breakfast', 'same', 'smile', 'crash', 'voice', 'not', 'car', 'love', 'night', 'floor',
                          'asleep', 'hear', 'thirteen', 'two', "isn't", 'remember', 'crawled', 'pick'})
CAPTIONS['y_over'] = [(sg['t0'], sg['t1'], 1700) for sg in SEGMENTS if sg['src'] in ('KITCHEN', 'MONTAGE', 'HALL', 'BASEMENT', 'UPSTAIRS', 'BOTH', 'HOOK', 'DOOR', 'STAIRS', 'CAR', 'FLOOR')]
