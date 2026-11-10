"""VIDEO_019 EDL — "What If You Never Stopped?" (2dEDIT comedy, ~25 s). Non-explicit: everything stays under the blanket
behind a CENSORED bar; the jokes are the science. One shot per narrator line + punch-ins; the mom freeze loops to frame 0."""
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


SHOT = {'N01': 'BED', 'N02': 'COOKIE', 'N03': 'RAISIN', 'N04': 'WRIST', 'N05': 'FIRE', 'N06': 'REBOOT', 'N07': 'SIT', 'N08': 'DOOR'}
B = {k: s(k) for k in ORDER}
B['door'] = s('N08')
B['freeze'] = e('N08') + 0.05


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job)
    if job is not None:
        d['map'] = [(t0, t0 * FPS), (t1, t1 * FPS)]
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


SEGMENTS = []
for i, lid in enumerate(ORDER):
    t0 = 0.0 if i == 0 else s(lid) - 0.05
    t1 = s(ORDER[i + 1]) - 0.05 if i + 1 < len(ORDER) else END
    k = i % 2
    SEGMENTS.append(S(t0, t1, SHOT[lid], zoom=Z((t0, 1.0 if k == 0 else 1.1, 0.5, 0.45), (t1, 1.1 if k == 0 else 1.0, 0.5, 0.45))))
SEGMENTS[0]['shake'] = [(0.0, 0.4, 10)]
SEGMENTS[0]['flash'] = [(0.0, 0.05)]
SEGMENTS[-1]['zoom'] = Z((B['door'], 1.0, 0.5, 0.45), (B['freeze'], 1.0, 0.5, 0.45), (B['freeze'] + 0.25, 1.5, 0.5, 0.45), (END, 1.55, 0.5, 0.45))

OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50,
         cols=[([(0, 'NONSTOP FOR')], [(0, '0:00:01'), (B['N02'], '1 HOUR'), (B['N03'], '1 DAY'), (B['N04'], '3 DAYS'), (B['N05'], '1 WEEK'),
                                       (B['N07'], 'FOREVER')]),
               ([(0, 'CALORIES')], [(0, '0'), (B['N02'], '-100'), (B['N03'], '-2,400'), (B['N05'], '-16,800')]),
               ([(0, 'WATER')], [(0, '100%'), (B['N03'], '61%'), (B['N05'], 'RAISIN')])]),
    dict(type='watermark', t0=0.0, t1=END),
]
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=78, max_words=4, speakers={},
                emphasis={'stopped', 'second', 'cookie', 'raisin', 'divorce', 'friction', 'always', 'cooldown', 'no', 'forever', 'mom'})
CAPTIONS['y_over'] = [(sg['t0'], sg['t1'], 1790) for sg in SEGMENTS if sg['src'] in ('BED', 'SIT', 'DOOR', 'RAISIN', 'FIRE', 'COOKIE', 'REBOOT')]
