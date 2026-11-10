"""VIDEO_020 EDL — "Testicular Pressure Syndrome" (2dEDIT adult comedy, ~40 s). Non-explicit: desk / podium / censor bar hide
everything; no one else is involved; the 'moans' are disguised as words. Doctor -> job interview -> best-man speech -> twist."""
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
JS = 0.5


def s(i):
    return LS[i][0]


def e(i):
    return LS[i][1]


SHOT = {'C01': 'XRAY', 'M01': 'CU_M', 'C02': 'DOC', 'M02': 'CU_M', 'A01': 'CU_A', 'M03': 'OFFICE', 'A02': 'CU_A', 'M04': 'OFFICE',
        'B01': 'WEDDING', 'M05': 'CU_M', 'M06': 'WEDDING', 'C03': 'PHONE', 'M07': 'PHONE', 'C04': 'PHONE', 'M08': 'CU_M'}
GAP_SHOT = {'A01': 'OFFICE', 'B01': 'WEDDING', 'M06': 'ALARM', 'C03': 'PHONE'}
B = dict(office=s('A01') - 0.8, wedding=s('B01') - 0.9, stop=e('M05') + 0.1, alarm=s('M06') - 1.4, phone=s('C03') - 0.6)
MOAN = [(s('M03'), s('M03') + 1.6), (s('M06'), s('M06') + 1.9)]


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
    SEGMENTS.append(S(prev_end, END, 'CU_M'))
_runs = []
for sg in SEGMENTS:
    if _runs and _runs[-1]['src'] == sg['src']:
        _runs[-1]['t1'] = sg['t1']
    else:
        _runs.append(dict(sg))
SEGMENTS = []
for k, r in enumerate(_runs):
    a, b = (1.0, 1.08) if k % 2 == 0 else (1.08, 1.0)
    SEGMENTS.append(S(r['t0'], r['t1'], r['src'], zoom=Z((r['t0'], a, 0.5, 0.45), (r['t1'], b, 0.5, 0.45))))
for sg in SEGMENTS:
    for a, b in MOAN:
        if sg['t0'] < b and sg['t1'] > a:
            sg['shake'] = [(max(a, sg['t0']), min(b, sg['t1']), 9)]
    if sg['src'] == 'ALARM':
        sg['shake'] = [(sg['t0'], sg['t1'], 22)]
        sg['fx_t'] = [(sg['t0'], sg['t1'], 'redflash')]
SEGMENTS[0]['flash'] = [(0.0, 0.05)]
SEGMENTS[-1]['zoom'] = Z((SEGMENTS[-1]['t0'], 1.0, 0.5, 0.42), (END, 1.35, 0.5, 0.4))

OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50,
         cols=[([(0, 'PATIENT')], [(0, 'AGE 29')]),
               ([(0, 'BALL PRESSURE')], [(0, '97%'), (B['stop'], '99%'), (B['alarm'], '100%!!'), (s('M06') + 1.2, '97%'), (s('C03'), '97%')]),
               ([(0, 'STOPPED FOR')], [(0, '0.0 S'), (B['stop'], '0.6 S'), (B['alarm'], '1.0 S'), (s('M06') + 1.2, '0.0 S')])]),
    dict(type='watermark', t0=0.0, t1=END),
]
SPK = {l['id']: {'M': 'YOU', 'C': 'DOCTOR', 'A': 'INTERVIEWER', 'B': 'BOB'}[l['id'][0]] for l in _T['lines']}
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=76, max_words=4, speakers=SPK,
                emphasis={'explode', 'stop', 'life', 'interview', 'mmmmanagement', 'okay', 'motivated', 'hands', "can't", 'beautiful',
                          'healthy', 'three', "don't"})
CAPTIONS['y_over'] = [(sg['t0'], sg['t1'], 1790) for sg in SEGMENTS if sg['src'] in ('OFFICE', 'WEDDING', 'DOC', 'XRAY', 'ALARM')] + \
    [(sg['t0'], sg['t1'], 1480) for sg in SEGMENTS if sg['src'] == 'PHONE']
