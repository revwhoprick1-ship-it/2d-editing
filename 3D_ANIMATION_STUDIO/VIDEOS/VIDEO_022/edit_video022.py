"""VIDEO_022 EDL — "Don't Touch The Vase" remake (2.5D ink style, choice game, ~65 s). Lore: VIDEOS/VASE_LORE.md.
Flow (from the flow ref): HOOK = the rule + breaking it in 3 s; BUILD = Grandma's rule note, count the pieces (labels),
Mom's voice vs her empty driveway, the no-blink countdown; PAYOFF = the blink -> the Tenant, "Give me my face", the face
piece in your hand, narrated choice, cliffhanger "Blink.". Scares instant + unannounced."""
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
JS = 0.42


def s(i):
    return LS[i][0]


def e(i):
    return LS[i][1]


SHOT = {'N01': 'HOOK', 'N02': 'HOOK', 'N03': 'SMOKE', 'N04': 'NOTE', 'N05': 'NOTE', 'N06': 'PIECES', 'N07': 'PIECES', 'O01': 'DOOR',
        'N08': 'WINDOW', 'G01': 'PHONE', 'O02': 'DOOR', 'N09': 'EYES', 'M01': 'EYES', 'X01': 'REVEAL', 'N10': 'HAND', 'N11': 'CHOICE',
        'N12': 'CHOICE', 'X02': 'CHOICE'}
GAP_SHOT = {'N03': 'SHATTER', 'G01': 'PHONE', 'O02': 'DOOR', 'X01': 'REVEAL', 'N10': 'HAND', 'X02': 'CHOICE'}

B = dict(crash=[w['start'] for w in WORDS if w['line'] == 'N02' and w['text'].lower().startswith('broke')][0], note=s('N04'), count=s('N06'), phone=s('G01') - 0.6, feet=s('O02') - 0.3, eyes=s('N09'))
B['js1'] = e('M01') + 0.1                     # the blink you couldn't stop -> it is RIGHT there
B['choice'] = s('N11')
B['js2'] = e('X02') + 0.05
B['rules'] = [w['start'] for w in WORDS if w['line'] == 'N05' and w['text'].lower().strip('.,') in ("don't", 'count')]
B['blinkcount'] = s('N09')


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job)
    if job is not None:
        d['map'] = [(t0, t0 * FPS), (t1, t1 * FPS)]
    d.update(kw)
    return d


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
    SEGMENTS.append(S(prev_end, END, 'CHOICE'))
_runs = []
for sg in SEGMENTS:
    if _runs and _runs[-1]['src'] == sg['src']:
        _runs[-1]['t1'] = sg['t1']
    else:
        _runs.append(dict(sg))
SEGMENTS = [S(r['t0'], r['t1'], r['src']) for r in _runs]          # camera moves are drawn in the scene (parallax)


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


override(B['crash'], B['crash'] + 0.5, 'SHATTER', flash=[(B['crash'], 0.04)], shake=[(B['crash'], B['crash'] + 0.5, 22)])
override(B['js1'], B['js1'] + JS, 'FACE', flash=[(B['js1'] + 0.18, 0.03)], shake=[(B['js1'] + 0.18, B['js1'] + JS, 34)],
         fx_t=[(B['js1'] + 0.18, B['js1'] + JS, 'glitch')])
override(B['js2'], END, 'FACE', flash=[(B['js2'], 0.03)], shake=[(B['js2'], END, 36)], fx_t=[(B['js2'], END, 'glitch')])

BLINKS = [(B['js1'] - 0.02, 0.08, 0.1, 0.06)]           # the forced blink: lids slam shut... and open on its face
SCARES = [(B['js1'], B['js1'] + JS), (B['js2'], END)]
CARD = dict(type='choice', y=930, header='WHAT DO YOU DO?', options=['GIVE IT THE FACE', 'SMASH THE FACE', "RUN TO GRANDMA'S"],
            footer='FOLLOW FOR PART 2  ·  GRANDMA LEFT A 4TH RULE', stagger=0.35)
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=48, hide=SCARES,
         cols=[([(0, 'GRANDMA\'S RULE')], [(0, 'DON\'T TOUCH'), (B['crash'], 'BROKEN')]),
               ([(0, 'PIECES')], [(0, '24'), (B['count'] + 1.4, '23')]),
               ([(0, 'BLINK IN')], [(0, '--'), (B['eyes'], '0:03'), (B['eyes'] + 1.0, '0:02'), (B['eyes'] + 2.0, '0:01'), (B['js1'], '0:00')])]),
    dict(type='blink', t0=0.0, t1=END, blinks=BLINKS),
    dict(CARD, t0=B['choice'], t1=B['js2'] - 0.02),
    dict(type='watermark', t0=0.0, t1=END),
]
NAMES = {'N': None, 'M': 'YOU', 'O': 'MOM?', 'G': 'GRANDMA (PHONE)', 'X': 'IT'}
SPK = {l['id']: NAMES[l['id'][0]] for l in _T['lines'] if NAMES[l['id'][0]]}
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1230, size=66, max_words=3, speakers=SPK,
                hide=SCARES + [(B['choice'], s('X02') - 0.05)],
                emphasis={'rule', 'never', 'broke', 'black', 'bed', 'note', 'blink', 'answer', 'count', 'twenty-three', 'face', 'dinner',
                          'driveway', 'see', 'talking', 'burning', 'hand', 'fast', 'closer'})
