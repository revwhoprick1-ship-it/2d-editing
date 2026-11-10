"""VIDEO_018 EDL — "The Extra Passenger" (2dEDIT horror). Rules from RETENTION_LESSONS.md: frame 0 = characters + threat + DING;
story only moves forward; no recap, no choice card; choice game: short card (~5 s) with the count still climbing, then a jumpscare that loops into frame 0."""
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


JS = 0.55
B = dict(a02=s('A02'), aisle=s('M02') - 0.9, girl=s('G01'), drawing=s('B03') - 0.9, dark=s('A03') - 2.0, js1=s('A03') - 1.3,
         tickets=s('B04') - 0.5, lsmile=s('L03'), js2=s('X01') - 0.05, girl2=s('G02') - 0.5)
B['choice'] = e('G02') + 0.2
B['js3'] = END - 0.55
B['counts'] = [0.2, 1.3, 2.4] + [s('A03') + 0.05]

SHOT = {'A01': 'COUNT', 'A02': 'COUNT', 'L01': 'CU_L', 'M01': 'ROW', 'B01': 'CU_B', 'M02': 'MAN', 'B02': 'MAN', 'L02': 'CU_L',
        'G01': 'GIRL', 'B03': 'DRAWING', 'A03': 'COUNT', 'M03': 'CU_M', 'B04': 'TICKETS', 'M04': 'CU_M', 'L03': 'LSMILE',
        'X01': 'MANTURN', 'G02': 'GIRL2'}
GAP_SHOT = {'M02': 'AISLE', 'G01': 'GIRL', 'B03': 'DRAWING', 'A03': 'DARK', 'B04': 'TICKETS', 'L03': 'ROW', 'X01': 'MAN', 'G02': 'GIRL2'}


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job)
    if job is not None:
        d['map'] = [(t0, t0 * FPS), (t1, t1 * FPS)]
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


def push(t0, t1, a=1.0, b=1.06, cy=0.45):
    return Z((t0, a, 0.5, cy), (t1, b, 0.5, cy))


SEGMENTS = []
prev_end = 0.0
for i, lid in enumerate(ORDER):
    st, en = LS[lid]
    nxt = LS[ORDER[i + 1]][0] if i + 1 < len(ORDER) else END
    shot = SHOT[lid]
    if st - prev_end > 0.05:
        SEGMENTS.append(S(prev_end, st, GAP_SHOT.get(lid, shot)))
    hold = nxt if nxt - en < 0.9 else en + 0.3
    SEGMENTS.append(S(st, hold, shot))
    prev_end = hold
if END - prev_end > 0.05:
    SEGMENTS.append(S(prev_end, END, 'CHOICE'))

# one continuous gentle push per run of the same shot
_runs = []
for sg in SEGMENTS:
    if _runs and _runs[-1]['src'] == sg['src']:
        _runs[-1]['t1'] = sg['t1']
    else:
        _runs.append(dict(sg))
SEGMENTS = []
for k, r in enumerate(_runs):
    a, b = (1.0, 1.06) if k % 2 == 0 else (1.06, 1.0)
    SEGMENTS.append(S(r['t0'], r['t1'], r['src'], zoom=push(r['t0'], r['t1'], a, b)))


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


override(0.0, 0.4, 'COUNT', flash=[(0.0, 0.05)], zoom=Z((0.0, 1.1, 0.5, 0.42), (0.4, 1.0, 0.5, 0.45)))
override(B['js1'], B['js1'] + JS, 'FACELESS', flash=[(B['js1'], 0.05)], shake=[(B['js1'], B['js1'] + JS, 26)],
         fx_t=[(B['js1'], B['js1'] + 0.3, 'glitch')], zoom=Z((B['js1'], 1.4, 0.5, 0.4), (B['js1'] + JS, 1.1, 0.5, 0.42)))
override(B['js2'], e('X01') + 0.4, 'MANTURN', flash=[(B['js2'], 0.05)], shake=[(B['js2'], B['js2'] + 0.5, 30)],
         fx_t=[(B['js2'], B['js2'] + 0.3, 'glitch'), (B['js2'] + 0.15, B['js2'] + 0.35, 'redflash')],
         zoom=Z((B['js2'], 1.0, 0.5, 0.4), (B['js2'] + 0.2, 1.35, 0.5, 0.35), (e('X01') + 0.4, 1.4, 0.5, 0.35)))
override(B['js3'], END, 'FACELESS', flash=[(B['js3'], 0.04)], shake=[(B['js3'], END, 34)], fx_t=[(B['js3'], END, 'glitch')],
         zoom=Z((B['js3'], 1.0, 0.5, 0.45), (END, 1.9, 0.5, 0.42)))

SCARES = [(B['js1'], B['js1'] + JS), (B['js2'], B['js2'] + 0.5), (B['js3'], END)]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50, hide=SCARES,
         cols=[([(0, 'FLIGHT 1213')], [(0, '37,000 FT')]),
               ([(0, 'SEATS')], [(0, '212')]),
               ([(0, 'PASSENGERS')], [(0, '211'), (B['counts'][1], '212'), (B['counts'][2], '213'), (s('A03'), '214'), (B['choice'] + 2.0, '215'),
                                       (B['choice'] + 3.5, '216')])]),
    dict(type='choice', t0=B['choice'], t1=B['js3'] - 0.05, y=980, header="WHO'S THE EXTRA PASSENGER?",
         options=['THE MAN IN 22C', 'THE GIRL IN 23A', 'LAWRENCE'], footer='COMMENT 1, 2 OR 3  ·  PICK WRONG = YOU BECOME THE EXTRA', stagger=0.5),
    dict(type='watermark', t0=0.0, t1=END),
]
NAMES = {'M': 'YOU', 'B': 'BOB', 'L': 'LAWRENCE', 'A': 'ATTENDANT', 'G': 'GIRL IN 23A', 'X': '22C'}
SPK = {l['id']: NAMES[l['id'][0]] for l in _T['lines']}
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=74, max_words=4, speakers=SPK, hide=SCARES,
                emphasis={'thirteen', 'twelve', 'lap', 'full', 'extra', 'moved', 'breathing', 'drawing', 'everyone', 'face', 'fourteen', 'two',
                          'booked', 'ticket', 'always', 'lying', 'real', 'wrong'})
CAPTIONS['y_over'] = [(sg['t0'], sg['t1'], 1150) for sg in SEGMENTS if sg['src'] in ('ROW', 'AISLE')] + \
    [(sg['t0'], sg['t1'], 1800) for sg in SEGMENTS if sg['src'] in ('MAN', 'GIRL', 'GIRL2', 'COUNT')]
