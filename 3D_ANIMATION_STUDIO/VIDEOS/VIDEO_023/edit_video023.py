"""VIDEO_023 EDL — "The Last Two Humans" (2.5D ink, choice game, ~55 s). Retention update 2: never reset tension, CTA < 3 s,
characters always moving, the camera tracks the action (moves drawn in the scene). Colour per phase: burning orange street ->
green fluorescent store -> thermal -> icy freezer -> red."""
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


SHOT = {'K01': 'CHASE', 'K02': 'CHASE', 'Z01': 'GATEFACE', 'K03': 'DRONE', 'D01': 'THERMAL', 'K04': 'AISLE', 'D02': 'THERMAL',
        'K05': 'FREEZER', 'T01': 'CU_T', 'T02': 'CU_T', 'T03': 'STORE', 'K06': 'GLASS', 'T04': 'GLASS', 'K07': 'GLASSCU', 'K08': 'CHOICE'}
GAP_SHOT = {'Z01': 'GATE', 'D01': 'DRONE', 'D02': 'FREEZER', 'T03': 'DOORLOCK', 'K06': 'GLASS', 'T04': 'GLASS'}

B = dict(gate=e('K02') + 0.3, drone=s('K03'), thermal=s('D01'), aisle=s('K04'), freezer=e('K04') + 0.05, lock=e('T02') + 0.05,
         out=s('T03') - 0.3, swarm=e('T03') + 0.15, glass=s('K06') - 1.0, knock=s('T04') - 0.9, choice=s('K08'))
B['vault'] = 2.6
B['js1'] = B['swarm']
B['js2'] = e('K08') + 0.25
B['knocks'] = [B['knock'], B['knock'] + 0.3, B['knock'] + 0.6]


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
SEGMENTS = [S(r['t0'], r['t1'], r['src']) for r in _runs]


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


override(0.0, 0.25, 'CHASE', flash=[(0.0, 0.04)], shake=[(0.0, 0.3, 14)])
override(B['js1'], B['js1'] + JS, 'SWARM', flash=[(B['js1'], 0.03)], shake=[(B['js1'], B['js1'] + JS, 34)],
         fx_t=[(B['js1'], B['js1'] + 0.25, 'glitch'), (B['js1'] + 0.1, B['js1'] + 0.35, 'redflash')])
override(B['js2'], END, 'SLAM', flash=[(B['js2'], 0.03)], shake=[(B['js2'], END, 36)], fx_t=[(B['js2'], END, 'glitch')])
for sg in SEGMENTS:                                                         # handheld energy while running
    if sg['src'] in ('CHASE', 'AISLE', 'STORE') and 'shake' not in sg:
        sg['shake'] = [(sg['t0'], sg['t1'], 5)]
    if sg['src'] == 'GATE':
        sg['shake'] = [(sg['t0'] + 0.5, sg['t0'] + 0.9, 18)]

SCARES = [(B['js1'], B['js1'] + JS), (B['js2'], END)]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=48, hide=SCARES,
         cols=[([(0, 'HUMANS LEFT')], [(0, '2'), (B['swarm'] + 0.5, '1')]),
               ([(0, 'ZOMBIES')], [(0, '8,099,999,998'), (B['swarm'] + 0.5, '8,099,999,999')]),
               ([(0, 'BODY HEAT')], [(0, 'TRACKED'), (B['freezer'], '-18 C'), (s('D02'), '1 FOUND')])]),
    dict(type='choice', t0=B['choice'], t1=B['js2'] - 0.02, y=1250, header='WHAT DO YOU DO?',
         options=['OPEN THE DOOR', 'STAY IN THE FREEZER', 'BACK DOOR'], footer='FOLLOW FOR PART 2  ·  WATCH TARA\'S BREATH', stagger=0.15),
    dict(type='watermark', t0=0.0, t1=END),
]
NAMES = {'K': None, 'T': 'TARA', 'Z': 'ZOMBIE', 'D': 'POLICE DRONE'}
SPK = {l['id']: NAMES[l['id'][0]] for l in _T['lines'] if NAMES[l['id'][0]]}
SPK.update({'K04': 'MIKA (YOU)'})
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1230, size=66, max_words=3, speakers=SPK,
                hide=SCARES + [(B['choice'], END)],
                emphasis={'zombies', 'smart', 'fast', 'tara', 'hurt', 'drone', 'warm', 'freezer', 'cold', 'one', 'fogging', 'bit',
                          'lock', 'here', 'ten', 'gone', 'glass'})
CAPTIONS['y_over'] = [(sg['t0'], sg['t1'], 980) for sg in SEGMENTS if sg['src'] == 'DRONE']
