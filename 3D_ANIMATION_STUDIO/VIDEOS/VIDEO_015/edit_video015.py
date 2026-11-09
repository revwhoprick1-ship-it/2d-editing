"""VIDEO_015 EDL — "Kessrah · Part 1" (2dEDIT, real 2D psychological horror, dialogue-driven). Lore: VIDEOS/KESSRAH_LORE.md.

Hook (frame 0): the whole class turned round in their seats, staring at you with the same smile. Your shaky whisper on frame 0:
"Okay... why is everyone looking at me?" The class, in unison: "Because you called him." -> 12 hours earlier.
Scares: JS1 the stare after your blink; JS2 every eyelid on Kessrah's face opens; JS3 the last blink -> its face -> frame 0.
POV blinks are drawn as real eyelids closing (ov_blink); the HUD counts your BLINKS.
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


END = DURATION = round(e('N11') + 3.4, 2)

B = dict(
    rewind=e('C01') + 0.1, ritual=s('Y02'), names=s('Y03'), candles=s('N03'), out=w('N03', 'out'), bed=s('Y04'), corner=s('N04'),
    school=s('Y05'), t01=s('T01'), y06=s('Y06'), t02=s('T02'), class_=s('H01'), kname=w('H01', 'kessrah'), y07=s('Y07'),
    blink1=w('N05', 'once', end=True) + 0.1, c02=s('C02'), y08=s('Y08'), h02=s('H02'), rub=s('N06'), empty=w('N06', 'open', end=True),
    y09=s('Y09'), board=s('N07'), y10=s('Y10'), k01=s('K01'), n08=s('N08'), eyes=s('N09'), y11=s('Y11'), choice=s('N10') - 0.1,
)
B['js1'] = B['blink1'] + 0.35
B['js2'] = e('N08') + 0.15
B['js3'] = END - 0.75
# your blinks (POV eyelids): the fatal one, the rub, then during the choice, faster and faster
BLINKS = [(B['blink1'], 0.12, 0.08, 0.15), (B['rub'] + 0.3, 0.2, 0.9, 0.35)]
_t, _gap = B['choice'] + 1.6, 2.4
while _t < B['js3'] - 1.0:
    BLINKS.append((_t, 0.1, 0.06, 0.14))
    _t += _gap
    _gap = max(0.9, _gap * 0.8)
BLINKS.append((B['js3'] - 0.3, 0.15, 0.15, 0.0))


def S(t0, t1, job, **kw):
    d = dict(t0=round(t0, 3), t1=round(t1, 3), src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)])
    d.update(kw)
    return d


def Z(*pts):
    return [tuple(p) for p in pts]


JS = 0.6
OLD = ['freeze_tint']
SEGMENTS = [
    S(0.0, B['rewind'], 'STARE', fx=['chroma'], zoom=Z((0, 1.0, 0.5, 0.5), (s('C01'), 1.06, 0.5, 0.52), (B['rewind'], 1.15, 0.5, 0.55))),
    dict(t0=B['rewind'], t1=B['ritual'], src='STARE', rewind=(B['rewind'] - 0.05, 0.0)),
    S(B['ritual'], B['names'], 'RITUAL', zoom=Z((B['ritual'], 1.0, 0.5, 0.5), (B['names'], 1.1, 0.5, 0.55))),
    S(B['names'], B['candles'], 'CANDLEFACE', zoom=Z((B['names'], 1.0, 0.5, 0.45), (B['candles'], 1.3, 0.5, 0.42))),
    S(B['candles'], B['bed'], 'CANDLES', zoom=Z((B['candles'], 1.0, 0.5, 0.5), (B['out'], 1.1, 0.5, 0.5), (B['bed'], 1.15, 0.5, 0.5))),
    S(B['bed'], B['corner'], 'DARKFACE', zoom=Z((B['bed'], 1.0, 0.5, 0.45), (B['corner'], 1.08, 0.5, 0.45))),
    S(B['corner'], B['school'], 'CORNER', zoom=Z((B['corner'], 1.0, 0.5, 0.5), (B['school'], 1.35, 0.35, 0.4))),
    S(B['school'], B['t01'], 'LOCKERS', zoom=Z((B['school'], 1.0, 0.5, 0.5), (B['t01'], 1.05, 0.5, 0.5))),
    S(B['t01'], B['y06'], 'THEO', zoom=Z((B['t01'], 1.0, 0.5, 0.45), (B['y06'], 1.12, 0.5, 0.45))),
    S(B['y06'], B['t02'], 'YOU', zoom=Z((B['y06'], 1.0, 0.5, 0.45), (B['t02'], 1.05, 0.5, 0.45))),
    S(B['t02'], B['class_'], 'THEO', zoom=Z((B['t02'], 1.1, 0.5, 0.45), (B['class_'], 1.3, 0.5, 0.42))),
    S(B['class_'], B['kname'] - 0.2, 'CLASS', zoom=Z((B['class_'], 1.0, 0.5, 0.5), (B['kname'], 1.05, 0.5, 0.5))),
    S(B['kname'] - 0.2, B['y07'], 'HART', fx=['chroma'], zoom=Z((B['kname'] - 0.2, 1.0, 0.5, 0.45), (B['y07'], 1.25, 0.5, 0.42))),
    S(B['y07'], B['js1'], 'YOU', zoom=Z((B['y07'], 1.0, 0.5, 0.45), (B['js1'], 1.15, 0.5, 0.42))),
    S(B['js1'], B['js1'] + JS, 'STARE', flash=[(B['js1'], 0.04)], shake=[(B['js1'], B['js1'] + JS, 26)],
      fx_t=[(B['js1'], B['js1'] + JS, 'glitch'), (B['js1'] + 0.2, B['js1'] + 0.35, 'redflash')],
      zoom=Z((B['js1'], 1.4, 0.5, 0.5), (B['js1'] + 0.15, 1.0, 0.5, 0.5), (B['js1'] + JS, 1.02, 0.5, 0.5))),
    S(B['js1'] + JS, B['y08'], 'STARE', fx=['chroma'], zoom=Z((B['js1'] + JS, 1.02, 0.5, 0.5), (B['y08'], 1.15, 0.5, 0.55))),
    S(B['y08'], B['h02'], 'YOU', shake=[(B['y08'], B['h02'], 4)], zoom=Z((B['y08'], 1.1, 0.5, 0.45), (B['h02'], 1.2, 0.5, 0.42))),
    S(B['h02'], B['rub'], 'HART', fx=['chroma'], zoom=Z((B['h02'], 1.0, 0.5, 0.45), (B['rub'], 1.3, 0.5, 0.4))),
    S(B['rub'], B['empty'], 'STARE', zoom=Z((B['rub'], 1.0, 0.5, 0.5), (B['empty'], 1.05, 0.5, 0.5))),
    S(B['empty'], B['y09'], 'EMPTY', zoom=Z((B['empty'], 1.0, 0.5, 0.5), (B['y09'], 1.05, 0.5, 0.5))),
    S(B['y09'], B['board'], 'YOU', zoom=Z((B['y09'], 1.0, 0.5, 0.45), (B['board'], 1.1, 0.5, 0.45))),
    S(B['board'], B['y10'], 'BOARD', zoom=Z((B['board'], 1.0, 0.5, 0.5), (B['y10'], 1.12, 0.5, 0.48))),
    S(B['y10'], B['k01'], 'YOU', shake=[(B['y10'], B['k01'], 5)], zoom=Z((B['y10'], 1.05, 0.5, 0.45), (B['k01'], 1.2, 0.5, 0.42))),
    S(B['k01'], B['js2'], 'BACK', zoom=Z((B['k01'], 1.0, 0.5, 0.5), (B['js2'], 1.3, 0.5, 0.35))),
    S(B['js2'], B['js2'] + JS, 'BACK', flash=[(B['js2'], 0.04)], shake=[(B['js2'], B['js2'] + JS, 30)],
      fx_t=[(B['js2'], B['js2'] + JS, 'glitch'), (B['js2'] + 0.15, B['js2'] + 0.3, 'invert')],
      zoom=Z((B['js2'], 1.3, 0.5, 0.35), (B['js2'] + 0.12, 1.9, 0.5, 0.28), (B['js2'] + JS, 2.0, 0.5, 0.28))),
    S(B['js2'] + JS, B['y11'], 'EYE', zoom=Z((B['js2'] + JS, 1.0, 0.5, 0.5), (B['y11'], 1.15, 0.5, 0.5))),
    S(B['y11'], B['choice'], 'YOU', shake=[(B['y11'], B['choice'], 5)], zoom=Z((B['y11'], 1.15, 0.5, 0.45), (B['choice'], 1.3, 0.5, 0.42))),
    S(B['choice'], B['js3'], 'CREEP'),
    S(B['js3'], END, 'SCARE', flash=[(B['js3'], 0.04)], shake=[(B['js3'], END, 34)],
      fx_t=[(B['js3'], END, 'glitch'), (B['js3'] + 0.25, B['js3'] + 0.4, 'redflash')],
      zoom=Z((B['js3'], 1.0, 0.5, 0.45), (B['js3'] + 0.15, 1.5, 0.5, 0.42), (END, 1.8, 0.5, 0.42))),
]

SCARES = [(B['js1'], B['js1'] + JS), (B['js2'], B['js2'] + JS), (B['js3'], END)]
_bk = [(0, '0')]
for _i, (_bt, *_r) in enumerate(BLINKS):
    _bk.append((_bt + 0.1, str(_i + 1)))
_bk.insert(1, (B['ritual'], '0'))
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=END, y=190, size=50, hide=SCARES + [(B['rewind'], B['ritual'])],
         cols=[([(0, 'FIRST PERIOD')], [(0, '8:14 AM'), (B['ritual'], '3:33 AM'), (B['school'], '7:58 AM'), (B['class_'], '8:12 AM'),
                                       (B['empty'], '8:14 AM')]),
               ([(0, 'BLINKS')], [(0, '1'), (B['ritual'], '0')] + _bk[2:]),
               ([(0, 'KESSRAH')], [(0, 'HERE'), (B['ritual'], '—'), (B['names'], 'CALLED'), (B['out'], 'HEARD'), (B['kname'], 'PRESENT'),
                                   (B['k01'], 'HERE')])]),
    dict(type='title', font='condensed', t0=B['ritual'] + 0.1, t1=B['names'] - 0.1, y=760, stroke=6, spacing=-10,
         lines=[('KESSRAH', 160, (255, 255, 255)), ('P A R T   1', 54, (230, 40, 45))]),
    dict(type='text2d', t0=B['rewind'] + 0.1, t1=B['ritual'] - 0.05, text='12 HOURS EARLIER', y=960, size=90, emph=('12',)),
    dict(type='choice', t0=B['choice'], t1=B['js3'] - 0.4, y=1000, header="DON'T BLINK. PICK ONE.",
         options=['RUN FOR THE DOOR', 'KEEP YOUR EYES OPEN', 'SAY HIS NAME BACKWARDS'],
         footer='COMMENT 1, 2 OR 3  ·  DON\'T BLINK WHILE YOU DECIDE', stagger=0.9),
    dict(type='blink', t0=0.0, t1=END, blinks=BLINKS),
    dict(type='watermark', t0=0.0, t1=END),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1420, size=78, max_words=4,
                speakers={k: v for k, v in (('Y01', 'YOU'), ('Y02', 'YOU'), ('Y03', 'YOU'), ('Y04', 'YOU'), ('Y05', 'YOU'), ('Y06', 'YOU'),
                                            ('Y07', 'YOU'), ('Y08', 'YOU'), ('Y09', 'YOU'), ('Y10', 'YOU'), ('Y11', 'YOU'), ('C01', 'EVERYONE'),
                                            ('C02', 'EVERYONE'), ('T01', 'THEO'), ('T02', 'THEO'), ('H01', 'MS. HART'), ('H02', 'MS. HART'),
                                            ('K01', 'YOU?'))},
                hide=[(B['choice'] + 0.2, END)] + SCARES,
                emphasis={'looking', 'called', 'stupid', 'blink', 'kessrah', 'out', 'nothing', 'blinks', 'finish', 'mean', 'when',
                          'attendance', 'say', 'once', 'waiting', 'stop', 'funny', 'sweetheart', 'empty', 'anyone', 'sentence',
                          'dreaming', 'mine', 'voice', 'burning', 'please', 'backwards', 'decide'})
