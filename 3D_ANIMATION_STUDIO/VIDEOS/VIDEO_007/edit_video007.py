"""VIDEO_007 EDL — "After Hours · Part 1" (2dEDIT, real 2D). Shot times come from the narration timing.

Flash-forward hook (hiding under the desk, something outside the door) -> VHS rewind + title -> the story -> back
under the same desk at the end, so the last frame flows into frame 0. Ends on a comment-to-choose card.
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


END = DURATION = round(e('N23') + 1.4, 2)

# ---------------------------------------------------------------- story beats (video time)
B = dict(
    rewind0=e('N02') + 0.15, title=e('N02') + 0.3, booth=s('N03') - 0.05,
    keys=s('N04') + 0.6, snort=e('N05') + 0.05, ext=s('N06'), corr=e('N06') + 0.2, door=s('N08'),
    key_turn=w('N08', 'turns'), office=e('N08') + 0.3, files=s('N10'), stamps=w('N12', 'stamped'), kept=w('N12', 'kept'),
    note=s('N13'), face=e('N13') + 0.2, test=e('D1') + 0.2, pen=w('N15', 'line'), becomes=w('N15', 'becomes'),
    bang=e('N15') + 0.6, face2=s('D2') - 0.1, peek=e('D2') + 0.2, pov=s('N17') + 0.3, hand=s('N18') + 0.1,
    turn=e('N18') + 0.3, looks=w('N19', 'looks'), face3=e('N19') + 0.2, dive=e('D3') + 0.15, stop=w('N20', 'stop'),
    choice=s('N22') - 0.2,
)


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


SEGMENTS = [
    S(0.0, B['rewind0'], 'HIDE', zoom=Z((0, 1.0, 0.45, 0.5), (B['rewind0'], 1.15, 0.5, 0.5))),
    dict(t0=B['rewind0'], t1=B['booth'], src='HIDE', rewind=(B['rewind0'] - 0.05, 0.0)),
    S(B['booth'], B['keys'], 'BOOTH', zoom=Z((B['booth'], 1.0, 0.5, 0.5), (B['keys'], 1.12, 0.5, 0.55))),
    S(B['keys'], B['snort'], 'KEYS', zoom=Z((B['keys'], 1.0, 0.5, 0.5), (B['snort'], 1.15, 0.55, 0.55))),
    S(B['snort'], B['ext'], 'GUARDCU', shake=[(B['snort'], B['snort'] + 0.3, 6)], zoom=Z((B['snort'], 1.1, 0.5, 0.45), (B['ext'], 1.18, 0.5, 0.45))),
    S(B['ext'], B['corr'], 'EXT', zoom=Z((B['ext'], 1.0, 0.5, 0.5), (B['corr'], 1.06, 0.5, 0.5))),
    S(B['corr'], B['door'], 'CORR'),
    S(B['door'], B['office'], 'DOOR', zoom=Z((B['door'], 1.0, 0.5, 0.5), (B['key_turn'], 1.08, 0.5, 0.52), (B['key_turn'] + 0.06, 1.2, 0.5, 0.55), (B['office'], 1.22, 0.5, 0.55))),
    S(B['office'], B['files'], 'OFFICE', zoom=Z((B['office'], 1.0, 0.5, 0.5), (B['files'], 1.1, 0.6, 0.5))),
    S(B['files'], B['note'], 'FILES', zoom=Z((B['files'], 1.0, 0.5, 0.5), (B['kept'] - 0.05, 1.08, 0.5, 0.5), (B['kept'] + 0.03, 1.22, 0.5, 0.5), (B['note'], 1.24, 0.5, 0.5)),
      shake=[(B['kept'], B['kept'] + 0.25, 10)]),
    S(B['note'], B['face'], 'FILES', zoom=Z((B['note'], 1.0, 0.5, 0.5), (B['face'], 1.3, 0.62, 0.62))),
    S(B['face'], B['test'], 'FACE', zoom=Z((B['face'], 1.0, 0.5, 0.45), (B['test'], 1.1, 0.5, 0.45))),
    S(B['test'], B['bang'], 'TEST', zoom=Z((B['test'], 1.0, 0.5, 0.5), (B['pen'], 1.1, 0.55, 0.6), (B['becomes'] - 0.2, 1.45, 0.62, 0.8), (B['bang'], 1.55, 0.62, 0.8))),
    S(B['bang'], B['face2'], 'BANG', flash=[(B['bang'], 0.06)], shake=[(B['bang'], B['bang'] + 0.7, 26)],
      zoom=Z((B['bang'], 1.18, 0.5, 0.5), (B['bang'] + 0.25, 1.0, 0.5, 0.5), (B['face2'], 1.04, 0.5, 0.5))),
    S(B['face2'], B['peek'], 'FACE2', zoom=Z((B['face2'], 1.0, 0.5, 0.45), (B['peek'], 1.12, 0.45, 0.45))),
    S(B['peek'], B['pov'], 'PEEK', zoom=Z((B['peek'], 1.0, 0.5, 0.5), (B['pov'], 1.1, 0.45, 0.5))),
    S(B['pov'], B['hand'], 'POV', zoom=Z((B['pov'], 1.3, 0.5, 0.48), (B['hand'], 1.75, 0.5, 0.47))),
    S(B['hand'], B['turn'], 'HANDCU', zoom=Z((B['hand'], 1.0, 0.5, 0.5), (B['turn'], 1.12, 0.5, 0.55))),
    S(B['turn'], B['face3'], 'TURN', flash=[(B['looks'], 0.05)], shake=[(B['looks'], B['looks'] + 0.4, 12)],
      zoom=Z((B['turn'], 1.0, 0.5, 0.4), (B['looks'] - 0.05, 1.08, 0.5, 0.4), (B['looks'] + 0.04, 1.35, 0.5, 0.35), (B['face3'], 1.4, 0.5, 0.35))),
    S(B['face3'], B['dive'], 'FACE3', shake=[(B['face3'], B['dive'], 5)], zoom=Z((B['face3'], 1.15, 0.5, 0.45), (B['dive'], 1.0, 0.5, 0.45))),
    S(B['dive'], END, 'HIDE', zoom=Z((B['dive'], 1.15, 0.5, 0.5), (B['stop'], 1.0, 0.45, 0.5), (END - 0.6, 1.0, 0.45, 0.5), (END, 1.0, 0.45, 0.5))),
]

HUD_LABEL = 'NIGHT 1 · WESTBROOK HIGH'
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50, hide=[(B['rewind0'], B['booth'])],
         cols=[([(0, HUD_LABEL)], [(0, '12:02 AM'), (B['booth'], '11:52 PM'), (B['corr'], '11:55 PM'), (B['office'], '11:58 PM'),
                                     (B['bang'], '12:01 AM'), (B['dive'], '12:02 AM')]),
               ([(0, 'BUILDING')], [(0, 'C'), (B['booth'], 'GATE'), (B['ext'], 'C')]),
               ([(0, 'GRADE')], [(0, '88'), (B['booth'], '38'), (B['becomes'] + 0.5, '88')])]),
    dict(type='title', font='condensed', t0=B['title'], t1=B['booth'] + 0.6, y=760, stroke=6, spacing=-10,
         lines=[('AFTER HOURS', 150, (255, 255, 255)), ('P A R T   1', 54, (230, 40, 45))]),
    dict(type='choice', t0=B['choice'], t1=END, y=900, header='HOW DO YOU GET OUT?',
         options=['CLIMB OUT THE WINDOW', 'HIDE IN THE FILING CABINET', 'RUN FOR THE STAIRS'],
         footer='COMMENT 1, 2 OR 3  ·  TOP COMMENT = PART 2', stagger=0.9),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1400, size=78, max_words=4,
                speakers={'D1': 'YOU', 'D2': 'YOU', 'D3': 'YOU'},
                hide=[(B['choice'] + 0.2, END)],
                y_over=[(B['pen'] - 0.3, B['bang'], 620)],
                emphasis={'grade', 'here', 'asleep', 'keys', 'tests', 'echoes', 'creaks', "aren't", 'files', 'eighty-seven',
                          'kept', 'cheat', 'nope', 'eighty-eight', 'crack', 'tall', 'flashlight',
                          'looks', 'desk', 'stop', 'chance', 'window', 'comment'})
