"""VIDEO_017 EDL — "Flight 404" (2dEDIT horror). Rules from RETENTION_LESSONS.md: frame 0 = characters + threat + DING;
story only moves forward; no recap, no choice card; the last frame (a bin opening over Bob) loops into the first DING."""
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
B = dict(ding=0.0, click1=s('L01') + 1.2, map=s('B01') - 0.8, cart=s('A02') - 1.4, feet=s('B02') - 0.7, js1=s('A03') - 0.12,
         click2=e('M04') + 0.05, heads=e('M04') + 0.4, bin=s('L03') - 0.6, js2=e('M05') + 0.05, tray=e('M05') + 0.05 + JS,
         stowed=s('C01'), bins=s('B04'), reveal=s('M06') - 2.2, belt=s('B05') - 0.2, ceiling=s('X01') - 1.6, js3=s('X01') - 0.05,
         land=s('A04') - 1.6, window=e('M08') + 0.1, open_=e('M09') + 0.15)
B['grabbed'] = B['js2'] + 0.25

SHOT = {'A01': 'ROW', 'L01': 'CU_L', 'M01': 'CU_M', 'B01': 'MAP', 'M02': 'ROW14', 'A02': 'AISLE', 'M03': 'CU_M', 'B02': 'CU_B',
        'A03': 'TURN', 'L02': 'CU_L', 'M04': 'CU_M', 'L03': 'BIN', 'M05': 'CU_M', 'B03': 'CU_B', 'C01': 'ROW', 'B04': 'BINS',
        'M06': 'CU_M', 'B05': 'BELT', 'M07': 'CU_M', 'X01': 'FACE', 'A04': 'LAND', 'B06': 'CU_B', 'M08': 'CU_M', 'M09': 'WINDOW'}
GAP_SHOT = {'B01': 'MAP', 'A02': 'AISLE', 'B02': 'FEET', 'A03': 'TURN', 'L02': 'ROW', 'L03': 'HEADS', 'M05': 'BIN', 'B03': 'TRAY',
            'B04': 'ROW', 'M06': 'REVEAL', 'M07': 'BELT', 'X01': 'CEILING', 'A04': 'LAND'}


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
    SEGMENTS.append(S(prev_end, END, 'WINDOW'))

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


override(0.0, 0.5, 'ROW', flash=[(0.0, 0.06)], shake=[(0.0, 0.35, 10)], zoom=Z((0.0, 1.12, 0.5, 0.4), (0.5, 1.0, 0.5, 0.45)))
override(B['js1'], B['js1'] + JS, 'TURN', flash=[(B['js1'], 0.05)], shake=[(B['js1'], B['js1'] + JS, 26)],
         fx_t=[(B['js1'], B['js1'] + 0.3, 'glitch')], zoom=Z((B['js1'], 1.5, 0.5, 0.35), (B['js1'] + 0.15, 1.15, 0.5, 0.4), (B['js1'] + JS, 1.1, 0.5, 0.4)))
override(B['js2'], B['js2'] + JS, 'GRAB', flash=[(B['js2'], 0.05)], shake=[(B['js2'], B['js2'] + JS, 34)],
         fx_t=[(B['js2'], B['js2'] + JS, 'glitch'), (B['js2'] + 0.2, B['js2'] + 0.4, 'redflash')],
         zoom=Z((B['js2'], 1.0, 0.5, 0.4), (B['js2'] + JS, 1.25, 0.5, 0.3)))
override(B['js3'], e('X01') + 0.3, 'FACE', flash=[(B['js3'], 0.05)], shake=[(B['js3'], B['js3'] + 0.5, 28)],
         fx_t=[(B['js3'], B['js3'] + 0.3, 'glitch')], zoom=Z((B['js3'], 1.4, 0.5, 0.45), (B['js3'] + 0.2, 1.05, 0.5, 0.45), (e('X01') + 0.3, 1.1, 0.5, 0.45)))
override(e('X01') + 0.3, B['land'], None)                                       # cut to black: did it take him?
override(B['open_'], END, 'WINDOW', fx_t=[(B['open_'], END, 'redflash')])
for sg in SEGMENTS:
    if sg['src'] in ('CEILING', 'BELT') and 'shake' not in sg:
        sg['shake'] = [(sg['t0'], sg['t1'], 7)]                                    # turbulence

SCARES = [(B['js1'], B['js1'] + JS), (B['js2'], B['js2'] + JS), (B['js3'], B['js3'] + 0.4)]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50, hide=SCARES,
         cols=[([(0, 'FLIGHT 404')], [(0, '38,000 FT'), (B['land'], '38,000 FT')]),
               ([(0, 'PASSENGERS')], [(0, '212'), (B['stowed'] + 1.6, '211')]),
               ([(0, 'ARRIVAL')], [(0, '--:--'), (B['land'], 'NOW'), (B['window'], '--:--')])]),
    dict(type='watermark', t0=0.0, t1=END),
]
NAMES = {'M': 'YOU', 'B': 'BOB', 'L': 'LAWRENCE', 'A': 'ATTENDANT', 'C': 'CAPTAIN', 'X': '"LAWRENCE"?'}
SPK = {l['id']: NAMES[l['id'][0]] for l in _T['lines']}
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=74, max_words=4, speakers=SPK, hide=SCARES,
                emphasis={'nobody', 'reason', 'sprites', "don't", 'map', 'circling', 'six', 'empty', 'buckled', 'drink', 'feet', 'looked',
                          'bottle', 'ten', 'no', 'everyone', 'down', 'folded', 'bin', 'stowed', 'moving', 'belt', 'broken', 'arm',
                          'seconds', 'landed', 'unbuckle', 'made', 'window', 'never'})
CAPTIONS['y_over'] = [(sg['t0'], sg['t1'], 1150) for sg in SEGMENTS if sg['src'] in ('ROW', 'LAND', 'HEADS', 'BIN', 'AISLE', 'BINS')]
