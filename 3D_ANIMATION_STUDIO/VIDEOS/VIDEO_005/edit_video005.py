"""VIDEO_005 EDL — "What If Toilets Started Fighting Back?"

BATH source frame for video time t: P + 30 t (t < T_PRE) or 30 (t - T_PRE) (the ending lives in the prelude, so
the last frame flows into frame 0). STREET source frame: P + 30 t.  Voice on frame 0, SLAM on frame 3.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OFF = 0.0
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
FPS = 30
END = DURATION = 32.4
T_PRE = 28.4
P = int(round((END - T_PRE) * FPS))
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
LS = {l['id']: (l['start'], l['end']) for l in _T['lines']}
T_SPRAY = LS['L03'][1] + 0.12
T_FLUSH = LS['L05'][0] - 0.15
T_RUN = LS['L05'][1] + 0.15
T_TURN = LS['L09'][1] + 0.15
T_ROAR = T_TURN + 0.9
T_BLAST = T_ROAR + 1.3
T_TUB = T_BLAST + 0.65
T_LAUNCH = 31.45


def w(line, word, nth=1, end=False):
    k = 0
    for x in _T['words']:
        if x['line'] == line and x['text'].lower().strip('.!?,:\'"') == word.lower():
            k += 1
            if k == nth:
                return round(x['end'] if end else x['start'], 3)
    raise KeyError((line, word))


def Fb(t):
    return (t - T_PRE) * FPS if t >= T_PRE else P + t * FPS


def seg(t0, t1, src, **kw):
    d = dict(t0=t0, t1=t1, src=src)
    if 'map' not in kw:
        d['map'] = [(t0, Fb(t0)), (t1, Fb(t1) if not (t0 < T_PRE <= t1) else Fb(t1))]
    d.update(kw)
    return d


FREEZE = lambda t: [(0, Fb(t)), (99, Fb(t))]
t_quit, t_what, t_ser = w('L01', 'quit'), w('L02', 'what'), w('L04', 'seriously')
t_chase, t_exits, t_fire, t_miss = w('L07', 'chase'), w('L07', 'exits'), w('L07', 'fire'), w('L07', 'missiles')
t_bath = w('L09', 'bathroom')

SEGMENTS = [
    seg(0.0, 1.0, 'OPEN', shake=[(0.1, 0.4, 16)], flash=[(0.1, 0.04)],
        zoom=[(0.0, 1.0, 0.45, 0.5), (0.1, 1.0, 0.45, 0.5), (0.18, 1.18, 0.4, 0.45), (1.0, 1.22, 0.4, 0.45)]),     # SLAM
    seg(1.0, 1.75, 'TCU', zoom=[(1.0, 1.0, 0.5, 0.35), (1.75, 1.15, 0.5, 0.3)]),                               # the glare
    seg(1.75, 2.85, 'MCU', zoom=[(1.75, 1.05, 0.5, 0.4), (t_what, 1.05, 0.5, 0.4), (t_what + 0.06, 1.2, 0.5, 0.38)]),
    seg(2.85, 3.6, 'TCU', zoom=[(2.85, 1.25, 0.3, 0.32), (3.6, 1.4, 0.25, 0.3)]),                              # handle turns
    seg(3.6, T_SPRAY - 0.05, 'SIDE', zoom=[(3.6, 1.0, 0.5, 0.45), (T_SPRAY - 0.05, 1.12, 0.55, 0.42)]),
    seg(T_SPRAY - 0.05, T_SPRAY + 0.45, 'SIDE', map=[(T_SPRAY - 0.05, Fb(T_SPRAY - 0.05)), (T_SPRAY + 0.45, Fb(T_SPRAY + 0.2))],
        flash=[(T_SPRAY, 0.04)], shake=[(T_SPRAY, T_SPRAY + 0.3, 12)], zoom=[(T_SPRAY, 1.25, 0.6, 0.38), (T_SPRAY + 0.45, 1.3, 0.62, 0.36)]),  # slow-mo spray
    seg(T_SPRAY + 0.45, 6.6, 'MCU', map=[(T_SPRAY + 0.45, Fb(T_SPRAY + 0.2)), (6.6, Fb(6.6))],
        zoom=[(T_SPRAY + 0.45, 1.0, 0.5, 0.4), (t_ser, 1.0, 0.5, 0.4), (t_ser + 0.06, 1.25, 0.5, 0.37)]),     # "Bro, seriously?!"
    seg(6.6, T_FLUSH + 0.1, 'TCU', zoom=[(6.6, 1.1, 0.5, 0.33), (T_FLUSH, 1.2, 0.5, 0.3)]),                 # smug squint
    seg(T_FLUSH + 0.1, 8.7, 'SIDE', shake=[(T_FLUSH + 0.2, T_FLUSH + 1.4, 8)], whip_in=(1, 3), zoom=[(T_FLUSH, 1.0, 0.5, 0.45), (8.7, 1.08, 0.5, 0.42)]),
    seg(8.7, 9.3, 'SIDE', map=FREEZE(8.7), fx=['freeze_tint'], flash=[(8.7, 0.05)], zoom=[(8.7, 1.08, 0.5, 0.42), (9.3, 1.18, 0.55, 0.4)]),   # SOAKED freeze
    seg(9.3, 10.7, 'MCU', map=[(9.3, Fb(9.3)), (10.7, Fb(10.4))], whip_out=(1, 4), zoom=[(9.3, 1.0, 0.5, 0.45), (10.7, 1.05, 0.5, 0.45)]),
    seg(10.7, 14.7, 'RIOT', map=[(10.7, P + 10.7 * FPS), (14.7, P + 14.7 * FPS)], whip_in=(1, 4),
        zoom=[(10.7, 1.0, 0.5, 0.5), (w('L06', 'every'), 1.0, 0.5, 0.5), (w('L06', 'every') + 0.06, 1.15, 0.45, 0.5), (14.7, 1.25, 0.45, 0.5)]),
    seg(14.7, t_exits - 0.05, 'CHASE', map=[(14.7, P + 14.7 * FPS), (t_exits - 0.05, P + (t_exits - 0.05) * FPS)], whip_in=(-1, 3),
        shake=[(14.8, 15.9, 5)], zoom=[(14.7, 1.0, 0.5, 0.5), (15.9, 1.15, 0.5, 0.5)]),
    seg(t_exits - 0.05, t_fire - 0.05, 'EXIT', map=[(t_exits - 0.05, P + (t_exits - 0.05) * FPS), (t_fire - 0.05, P + (t_fire - 0.05) * FPS)],
        whip_in=(1, 3), zoom=[(t_exits, 1.0, 0.5, 0.5), (t_exits + 0.2, 1.2, 0.5, 0.52)]),
    seg(t_fire - 0.05, 18.6, 'TPMISS', map=[(t_fire - 0.05, P + (t_fire - 0.05) * FPS), (18.6, P + 18.2 * FPS)],
        whip_in=(-1, 3), shake=[(16.7, 17.9, 6)], zoom=[(t_fire, 1.0, 0.5, 0.5), (t_miss, 1.1, 0.4, 0.5), (18.6, 1.15, 0.4, 0.5)]),
    seg(18.6, t_bath + 0.35, 'POV', map=[(18.6, Fb(18.8)), (t_bath + 0.35, Fb(t_bath + 0.35))], whip_in=(1, 4),
        zoom=[(18.6, 1.0, 0.5, 0.55), (t_bath, 1.05, 0.55, 0.6), (t_bath + 0.06, 1.35, 0.6, 0.65)]),          # "The bathroom."
    seg(t_bath + 0.35, T_ROAR + 1.2, 'REVEAL', map=[(t_bath + 0.35, Fb(T_TURN - 0.2)), (T_ROAR + 1.2, Fb(T_ROAR + 1.2))],
        shake=[(T_ROAR, T_ROAR + 1.0, 18)], zoom=[(t_bath + 0.35, 1.0, 0.5, 0.45), (T_ROAR - 0.05, 1.05, 0.5, 0.4), (T_ROAR + 0.05, 1.3, 0.45, 0.35)]),
    seg(T_ROAR + 1.2, T_BLAST + 0.75, 'BLAST', map=[(T_ROAR + 1.2, Fb(T_BLAST - 0.2)), (T_BLAST, Fb(T_BLAST)), (T_BLAST + 0.4, Fb(T_BLAST + 0.12)), (T_BLAST + 0.75, Fb(T_TUB + 0.05))],
        flash=[(T_BLAST, 0.08)], shake=[(T_BLAST, T_BLAST + 0.6, 24)], zoom=[(T_BLAST, 1.15, 0.5, 0.5), (T_BLAST + 0.4, 1.0, 0.5, 0.5)]),   # impact + slow-mo
    seg(T_BLAST + 0.75, T_PRE, 'TUB', map=[(T_BLAST + 0.75, Fb(T_TUB + 0.05)), (T_PRE - 1 / FPS, P + T_PRE * FPS - 1)], shake=[(T_BLAST + 0.75, T_BLAST + 1.0, 14)],
        zoom=[(T_BLAST + 0.75, 1.0, 0.5, 0.45), (w('L10', 'again'), 1.08, 0.5, 0.45), (w('L10', 'again') + 0.06, 1.25, 0.55, 0.45), (T_PRE, 1.25, 0.55, 0.45)]),
    dict(t0=T_PRE, t1=T_LAUNCH, src='TUB', map=[(T_PRE, 0), (T_LAUNCH, (T_LAUNCH - T_PRE) * FPS)],
         zoom=[(T_PRE, 1.1, 0.5, 0.5), (29.0, 1.1, 0.45, 0.7), (29.1, 1.7, 0.42, 0.78), (30.6, 1.75, 0.42, 0.78), (T_LAUNCH, 1.2, 0.5, 0.6)]),   # tub eyes
    dict(t0=T_LAUNCH, t1=END, src='END', map=[(T_LAUNCH, (T_LAUNCH - T_PRE) * FPS), (END - 1 / FPS, P - 1)], whip_in=(-1, 3)),
]

OVERLAYS = [
    dict(type='title', t0=0.08, t1=1.6, y=300, shake=True, lines=[('TOILETS', 120, (255, 255, 255)), ('FIGHT BACK', 104, (255, 210, 61))]),
    dict(type='stamp', t0=8.7, t1=9.3, text='SOAKED', x=0.5, y=0.25, size=130, rot=-8, color=(60, 160, 255)),
    dict(type='chip', t0=T_FLUSH + 0.3, t1=8.7, emoji='📤', text='SEND TO WHOEVER CLOGGED IT', x=0.5, y=0.16, size=42, fill=(255, 255, 255, 240), fg=(20, 20, 24)),
    dict(type='stamp', t0=w('L06', 'every'), t1=14.6, text='TOILET UPRISING', x=0.5, y=0.2, size=96, rot=-5),
    dict(type='stamp', t0=T_ROAR, t1=T_BLAST - 0.1, text='BOSS FIGHT', x=0.5, y=0.16, size=120, rot=-6),
    dict(type='chip', t0=LS['L10'][0] - 0.4, t1=T_PRE - 0.1, emoji='💬', text='WHICH HOUSEHOLD OBJECT BETRAYS YOU NEXT?', x=0.5, y=0.14, size=36,
         fill=(255, 210, 61, 245), fg=(20, 20, 24)),
]

CAPTIONS = dict(timing=TIMING, offset=OFF, y=1470, size=92,
                emphasis={'toilet', 'quit', 'what', 'tired', 'bro', 'seriously', 'flushes', 'spite', 'every', 'earth', 'fighting',
                          'chase', 'block', 'exits', 'fire', 'missiles', 'bathroom', 'never', 'again', 'bathtub', 'disagrees'},
                y_over=[(0.0, 1.6, 1560)])
