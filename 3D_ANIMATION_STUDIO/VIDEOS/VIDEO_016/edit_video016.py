"""VIDEO_016 EDL — "The Forest That Eats People" (2dEDIT, real 2D horror, dialogue-driven).

Each line plays on the speaker's close-up unless SHOT overrides it with a wide/insert; the silences placed between lines
(audio/place_lines.py GAP) carry the action: the hook, the figure in the trees, the knocks, the reveal, the chase, the twist.
"""
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


B = dict(
    hookcut=s('X01') - 0.05, title=e('X01') + 0.2, enter=s('K01') - 1.2, fork=s('K03') - 0.8, sign=s('B03'), bones=s('K05') - 1.2,
    figure=s('J03') + 0.5, turn=s('M03') - 1.6, help=s('X02'), house_in=s('K07') - 1.2, dining=s('B05') - 1.8, wall=s('L05') + 0.4,
    knock=s('X03') - 2.6, handle=e('L06') + 0.1, dark=e('L06') + 1.4, reveal=s('X05') - 1.4, x05=s('X05'), rush=e('K10') - 0.1,
    chase=e('M06') + 0.2, escape=e('M06') + 0.2, edge=s('L08') - 1.4, twist=s('K11'), shadows=s('M07') - 0.8,
)
B['knocks'] = [B['knock'] + 0.4, B['knock'] + 1.0, B['knock'] + 1.6]
B['exit'] = s('M06')
B['js1'] = B['reveal']
B['js2'] = B['rush']
B['js3'] = e('K12') + 0.25

# which shot each line plays on (default: the speaker's close-up; X lines need an explicit shot)
SHOT = {'X01': 'BLACK', 'K01': 'ENTER', 'J01': 'ENTER', 'M01': 'CU_M', 'K03': 'FORK', 'J02': 'FORK', 'B03': 'SIGN', 'M02': 'CU_M',
        'K05': 'BONES', 'J03': 'BONES', 'X02': 'TREES', 'K07': 'HOUSE', 'J04': 'HOUSE', 'B05': 'DINING', 'J05': 'DINING',
        'K08': 'DINING', 'L05': 'WALL', 'X03': 'DOOR', 'X04': 'DOOR', 'L06': 'DOOR', 'X05': 'HALL', 'J07': 'CHASE', 'L07': 'CHASE',
        'B08': 'CHASE', 'M06': 'EXIT', 'L08': 'EDGE', 'J08': 'EDGE', 'B09': 'EDGE', 'M07': 'SHADOWS', 'B10': 'SHADOWS', 'K12': 'CU_K',
        'X06': 'BLACK'}
# action fillers in the gaps before a line
GAP_SHOT = {'X01': 'HOOK', 'K01': 'TITLE', 'K03': 'FORK', 'K05': 'BONES', 'M03': 'BONES', 'X02': 'TREES', 'K07': 'HOUSE',
            'B05': 'DINING', 'X03': 'DOOR', 'X05': 'DOOR', 'J07': 'HALL', 'L08': 'CHASE', 'M07': 'SHADOWS', 'K12': 'CU_K', 'X06': 'BLACK'}


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job)
    if job is not None:
        d['map'] = [(t0, t0 * FPS), (t1, t1 * FPS)]
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


def push(t0, t1, a=1.0, b=1.1, cy=0.45):
    return Z((t0, a, 0.5, cy), (t1, b, 0.5, cy))


# ---------------------------------------------------------------- build the cut list from the dialogue
SEGMENTS = []
prev_end = 0.0
for i, lid in enumerate(ORDER):
    st, en = LS[lid]
    nxt = LS[ORDER[i + 1]][0] if i + 1 < len(ORDER) else END
    shot = SHOT.get(lid, 'CU_' + lid[0])
    if st - prev_end > 0.05:                                                      # the gap before this line: action
        g = GAP_SHOT.get(lid, shot)
        SEGMENTS.append(S(prev_end, st, g if g != 'BLACK' else None, zoom=push(prev_end, st, 1.0, 1.08) if g != 'BLACK' else []))
    SEGMENTS.append(S(st, nxt, shot if shot != 'BLACK' else None, zoom=push(st, nxt, 1.0, 1.12) if shot != 'BLACK' else []))
    prev_end = nxt

# one continuous slow push per run of the same shot (no zoom snapping back at a cut to the same picture)
_runs = []
for sg in SEGMENTS:
    if _runs and _runs[-1]['src'] == sg['src']:
        _runs[-1]['t1'] = sg['t1']
    else:
        _runs.append(dict(sg))
SEGMENTS = []
for k, r in enumerate(_runs):
    zin = k % 2 == 0                                                              # alternate push-in / pull-out
    a, b = (1.0, 1.06) if zin else (1.06, 1.0)
    SEGMENTS.append(S(r['t0'], r['t1'], r['src'], zoom=push(r['t0'], r['t1'], a, b) if r['src'] else []))


def override(t0, t1, job, **kw):
    """Cut [t0, t1) out of the list and insert a special segment."""
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


JS = 0.55
override(B['hookcut'], s('X01'), None)                                                          # cut to black before the whisper
override(B['help'] + 0.9, B['help'] + 2.0, 'CU_M', zoom=push(B['help'] + 0.9, B['help'] + 2.0, 1.15, 1.3))
override(B['js1'], B['js1'] + JS, 'HALL', flash=[(B['js1'], 0.05)], shake=[(B['js1'], B['js1'] + JS, 24)],
         fx_t=[(B['js1'], B['js1'] + 0.3, 'glitch')], zoom=Z((B['js1'], 1.6, 0.5, 0.3), (B['js1'] + 0.15, 1.0, 0.5, 0.45), (B['js1'] + JS, 1.02, 0.5, 0.45)))
override(B['js1'] + JS, s('X05'), 'HALL', zoom=push(B['js1'] + JS, s('X05'), 1.0, 1.25, 0.35))
override(B['js2'], B['js2'] + JS, 'HALL', flash=[(B['js2'], 0.05)], shake=[(B['js2'], B['js2'] + JS, 34)],
         fx_t=[(B['js2'], B['js2'] + JS, 'glitch'), (B['js2'] + 0.2, B['js2'] + 0.35, 'redflash')],
         zoom=Z((B['js2'], 1.0, 0.5, 0.4), (B['js2'] + 0.15, 1.8, 0.5, 0.32), (B['js2'] + JS, 2.0, 0.5, 0.3)))
override(B['js3'], END - 1.4, 'CU_K', flash=[(B['js3'], 0.04)], shake=[(B['js3'], B['js3'] + 0.4, 26)], fx_t=[(B['js3'], B['js3'] + 0.3, 'glitch')],
         zoom=Z((B['js3'], 1.3, 0.5, 0.42), (END - 1.4, 1.6, 0.5, 0.4)))
override(B['dark'], B['reveal'], None)                                                          # lights out
for k, sg in enumerate(SEGMENTS):                                                               # chase: fast handheld shake
    if sg['src'] == 'CHASE':
        sg.setdefault('shake', [(sg['t0'], sg['t1'], 8)])

SCARES = [(B['js1'], B['js1'] + JS), (B['js2'], B['js2'] + JS), (B['js3'], B['js3'] + 0.4)]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50, hide=SCARES + [(B['hookcut'], B['enter'])],
         cols=[([(0, 'NIGHT 1 · BLACKWOOD FOREST')], [(0, '3:12 AM'), (B['enter'], '9:41 PM'), (B['house_in'], '11:58 PM'), (B['knock'], '2:47 AM'),
                                                     (B['edge'], '3:12 AM')]),
               ([(0, 'ANIMALS SEEN')], [(0, '0')]),
               ([(0, 'GROUP')], [(0, '5'), (B['enter'], '5'), (B['twist'] + 2.5, '5?')])]),
    dict(type='title', font='condensed', t0=B['title'], t1=B['enter'] + 0.6, y=820, stroke=6, spacing=-14,
         lines=[('THE FOREST', 140, (255, 255, 255)), ('THAT EATS', 140, (255, 255, 255)), ('PEOPLE', 160, (230, 40, 45))]),
    dict(type='watermark', t0=0.0, t1=END),
]

NAMES = {'M': 'YOU', 'B': 'BOB', 'L': 'LAWRENCE', 'K': 'KEN', 'J': 'JUSTIN'}
SPK = {}
for l in _T['lines']:
    if l['id'][0] in NAMES:
        SPK[l['id']] = NAMES[l['id'][0]]
SPK.update({'X01': '???', 'X02': '"KEN"?', 'X03': '"YOU"?', 'X04': '"JUSTIN"?', 'X05': 'IT', 'X06': '???'})
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=74, max_words=4, speakers=SPK, hide=SCARES,
                emphasis={'ken', 'dangerous', 'disappear', 'decades', 'adventure', 'animal', 'unusual', 'die', 'sign', 'scratches', 'warn',
                          'halloween', 'skull', 'human', 'together', 'following', 'help', "wasn't", 'shelter', 'demonic', 'immediately',
                          'five', 'butler', 'stop', 'door', 'outside', 'cold', 'copying', 'now', 'leaving', 'hell', 'run', 'told', 'coming',
                          'never', 'everyone', 'fun', 'move', 'forgot', 'inside'})
# group shots: captions sit above the heads, not on them
CAPTIONS['y_over'] = [(sg['t0'], sg['t1'], 1150) for sg in SEGMENTS if sg['src'] in ('ENTER', 'BONES', 'EDGE', 'CHASE', 'EXIT')]
