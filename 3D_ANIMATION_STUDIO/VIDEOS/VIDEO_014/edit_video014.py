"""VIDEO_014 EDL — "Don't Touch The Vase · Part 2" (2dEDIT, real 2D horror). Top comment: grab the pieces and run to Grandma's.
Lore: VIDEOS/VASE_LORE.md (never contradict it).

Stand-alone hook: frame 0 = an old woman's eye in a door peephole, rain: "Before I open this door... blink."
"Because the thing from the vase never blinks." -> 5 s recap (Part 1 shots) -> the vote card -> the run -> Grandma -> the lore
-> one piece missing -> three knocks: "It's Eli" -> peephole jumpscare -> choice -> final lunge -> frame 0.
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


END = DURATION = round(e('N15') + 3.0, 2)

B = dict(
    recap=s('N02'), r2=w('N02', 'something'), r3=w('N02', 'took'), r4=w('N02', 'voices'), card=s('N03'), run=s('N04'),
    dad=s('N05'), mom=s('N06'), yours=s('N07'), d3=s('D3'), lightning=w('N08', 'lightning'), door=s('N09'), blinkyou=w('N09', 'blink'),
    opens=w('N09', 'opens'), kitchen=s('G2'), pale=w('N10', 'pale'), g3=s('G3'), missing=s('N11'), g4=s('G4'), mother=w('G4', 'mother'),
    so=w('G4', 'so'), g5=s('G5'), knock=s('N12'), e1=s('E1'), n13=s('N13'), choice=s('N14') - 0.1,
)
B['js2'] = e('N13') + 0.45
B['js3'] = END - 0.75


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


JS = 0.55
OLD = ['freeze_tint']
SEGMENTS = [
    S(0.0, B['recap'], 'PEEPOUT', zoom=Z((0, 1.25, 0.5, 0.42), (B['recap'], 1.0, 0.5, 0.45))),
    S(B['recap'], B['r2'], 'R_VASE', fx=OLD, whip_in=(1, 3)),
    S(B['r2'], B['r3'], 'R_MOM', fx=OLD, whip_in=(-1, 3)),
    S(B['r3'], B['r4'], 'R_DAD', fx=OLD, whip_in=(1, 3), fx_t=[(B['r3'], B['r4'], 'glitch')]),
    S(B['r4'], B['card'], 'R_MIRROR', fx=OLD, whip_in=(-1, 3)),
    S(B['card'], B['dad'], 'RUN', zoom=Z((B['card'], 1.0, 0.5, 0.5), (B['dad'], 1.05, 0.5, 0.5))),
    S(B['dad'], B['yours'], 'FRONT', zoom=Z((B['dad'], 1.0, 0.5, 0.5), (B['yours'], 1.15, 0.5, 0.45))),
    S(B['yours'], B['lightning'], 'YOUFACE', fx=['chroma'], zoom=Z((B['yours'], 1.0, 0.5, 0.45), (B['lightning'], 1.25, 0.5, 0.42))),
    S(B['lightning'], B['lightning'] + JS, 'ROOF', flash=[(B['lightning'], 0.05)], shake=[(B['lightning'], B['lightning'] + JS, 28)],
      fx_t=[(B['lightning'], B['lightning'] + 0.3, 'glitch')], zoom=Z((B['lightning'], 1.0, 0.5, 0.45), (B['lightning'] + 0.15, 1.5, 0.62, 0.32),
                                                                      (B['lightning'] + JS, 1.55, 0.62, 0.32))),
    S(B['lightning'] + JS, B['door'], 'ROOF', zoom=Z((B['lightning'] + JS, 1.0, 0.5, 0.5), (B['door'], 1.05, 0.5, 0.5))),
    S(B['door'], B['kitchen'], 'PEEPOUT', zoom=Z((B['door'], 1.0, 0.5, 0.45), (B['opens'], 1.0, 0.5, 0.45), (B['kitchen'], 1.1, 0.5, 0.5))),
    S(B['kitchen'], B['g3'], 'KITCHEN', zoom=Z((B['kitchen'], 1.0, 0.5, 0.5), (B['pale'], 1.05, 0.5, 0.5), (B['pale'] + 0.05, 1.2, 0.35, 0.42),
                                              (B['g3'], 1.22, 0.35, 0.42))),
    S(B['g3'], B['missing'], 'GMA', zoom=Z((B['g3'], 1.0, 0.5, 0.45), (B['missing'], 1.12, 0.5, 0.42))),
    S(B['missing'], B['g4'], 'TABLE', zoom=Z((B['missing'], 1.0, 0.5, 0.5), (B['g4'] - 0.6, 1.3, 0.5, 0.42), (B['g4'], 1.35, 0.5, 0.42))),
    S(B['g4'], B['mother'], 'F_TWINS', fx=OLD, zoom=Z((B['g4'], 1.0, 0.5, 0.5), (B['mother'], 1.15, 0.62, 0.42))),
    S(B['mother'], B['so'], 'F_PAINT', fx=OLD, zoom=Z((B['mother'], 1.0, 0.5, 0.5), (B['so'], 1.12, 0.55, 0.45))),
    S(B['so'], B['g5'], 'F_SEAL', fx=OLD, zoom=Z((B['so'], 1.0, 0.5, 0.5), (B['g5'], 1.2, 0.5, 0.35))),
    S(B['g5'], B['knock'], 'GMA', zoom=Z((B['g5'], 1.0, 0.5, 0.45), (B['knock'], 1.08, 0.5, 0.45))),
    S(B['knock'], B['n13'], 'HALL', zoom=Z((B['knock'], 1.0, 0.5, 0.5), (B['e1'], 1.08, 0.5, 0.45), (B['n13'], 1.2, 0.5, 0.4))),
    S(B['n13'], B['js2'], 'GMA', zoom=Z((B['n13'], 1.0, 0.5, 0.45), (B['js2'], 1.2, 0.5, 0.42))),
    S(B['js2'], B['js2'] + JS, 'PEEP', flash=[(B['js2'], 0.04)], shake=[(B['js2'], B['js2'] + JS, 30)],
      fx_t=[(B['js2'], B['js2'] + JS, 'glitch'), (B['js2'] + 0.15, B['js2'] + 0.3, 'invert')],
      zoom=Z((B['js2'], 1.0, 0.5, 0.45), (B['js2'] + 0.12, 1.5, 0.5, 0.45), (B['js2'] + JS, 1.6, 0.5, 0.45))),
    S(B['js2'] + JS, B['js3'], 'HALL', zoom=Z((B['js2'] + JS, 1.0, 0.5, 0.5), (B['js3'], 1.1, 0.5, 0.45))),
    S(B['js3'], END, 'SCARE', flash=[(B['js3'], 0.04)], shake=[(B['js3'], END, 34)],
      fx_t=[(B['js3'], END, 'glitch'), (B['js3'] + 0.25, B['js3'] + 0.4, 'redflash')],
      zoom=Z((B['js3'], 1.0, 0.5, 0.45), (B['js3'] + 0.15, 1.6, 0.5, 0.42), (END, 1.9, 0.5, 0.42))),
]

SCARES = [(B['lightning'], B['lightning'] + JS), (B['js2'], B['js2'] + JS), (B['js3'], END)]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50, hide=SCARES + [(B['recap'], B['card'])],
         cols=[([(0, 'NIGHT 1')], [(0, '2:31 AM'), (B['run'], '2:24 AM'), (B['door'], '2:31 AM'), (B['knock'], '2:44 AM')]),
               ([(0, 'PIECES')], [(0, '24?'), (B['missing'], '23 / 24')]),
               ([(0, 'BATTERY')], [(0, '0%')])]),
    dict(type='text2d', t0=B['recap'] + 0.05, t1=B['card'] - 0.05, text='PREVIOUSLY', y=330, size=60, emph=('previously',)),
    dict(type='comment', t0=B['card'] + 0.1, t1=B['dad'] - 0.05, y=640, chose='YOU CHOSE 3 · RUN TO GRANDMA\'S', label='TOP COMMENT · PART 1',
         handle='@yungthuggaxo', likes=29, text='grab the pieces and run to gma'),
    dict(type='title', font='condensed', t0=B['kitchen'] + 0.1, t1=B['pale'] - 0.1, y=700, stroke=6, spacing=-10,
         lines=[("DON'T TOUCH", 110, (255, 255, 255)), ('THE VASE', 140, (255, 255, 255)), ('P A R T   2', 54, (230, 40, 45))]),
    dict(type='text2d', t0=B['g4'] + 0.05, t1=B['g5'] - 0.05, text='1968', y=420, size=110, emph=('1968',)),
    dict(type='choice', t0=B['choice'], t1=B['js3'] - 0.05, y=1000, header='WHAT DO YOU DO?',
         options=['GO BACK FOR THE FACE PIECE', 'LET GRANDMA FACE IT ALONE', 'OPEN THE DOOR FOR ELI'],
         footer='COMMENT 1, 2 OR 3  ·  PART 3... IF YOU\'RE STILL HERE', stagger=0.9),
    dict(type='watermark', t0=0.0, t1=END),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=78, max_words=4,
                speakers={'G1': 'GRANDMA', 'G2': 'GRANDMA', 'G3': 'GRANDMA', 'G4': 'GRANDMA', 'G5': 'GRANDMA', 'D1': 'DAD?', 'D2': 'MOM?',
                          'D3': 'YOU?', 'E1': 'ELI?'},
                hide=[(B['choice'] + 0.2, END)] + SCARES,
                emphasis={'blink', 'blinks', 'vase', 'voices', "grandma's", 'rain', "dad's", "mom's", 'yours', 'her', 'roofs', 'opens', 'pieces',
                          'pale', 'face', 'missing', 'eli', 'home', 'seal', 'knocks', 'twelve', 'door', 'here'})
