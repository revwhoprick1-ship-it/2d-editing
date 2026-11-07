"""VIDEO_004 EDL — "What If Gravity Disappeared for 10 Seconds?"

All shots come from one STREET timeline: source frame = P + 30 * t. The last segment uses the calm
prelude (frames 8..99, same CAM_HOOK), so the final frame is the frame right before video frame 0.
Voice starts on frame 0; a story clock counts the ten seconds; the explainer is a motion graphic.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OFF = 0.0
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
FPS = 30
P = 100
END = DURATION = 33.6
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
LS = {l['id']: (l['start'], l['end']) for l in _T['lines']}
T_G = LS['L10'][0] + 0.75
T_LAND = T_G + 2.6
T_BONK = LS['L11'][1] + 0.35
T_RESET = 30.55


def w(line, word, nth=1, end=False):
    k = 0
    for x in _T['words']:
        if x['line'] == line and x['text'].lower().strip('.!?,:\'"') == word.lower():
            k += 1
            if k == nth:
                return round(x['end'] if end else x['start'], 3)
    raise KeyError((line, word))


def Fr(t):
    return P + t * FPS


def seg(t0, t1, src, **kw):
    d = dict(t0=t0, t1=t1, src=src)
    if 'map' not in kw:
        d['map'] = [(t0, Fr(t0)), (t1, Fr(t1))]
    d.update(kw)
    return d


t_fly, t_phone, t_coffee, t_sneeze = w('L02', 'flying'), w('L03', 'phone'), w('L03', 'coffee'), w('L03', 'sneeze')
t_space, t_jumped, t_jump, t_land = w('L04', 'space'), w('L06', 'jumped'), w('L07', 'jump'), w('L08', 'land')
t3, t2, t1 = w('L09', 'three'), w('L09', 'two'), w('L09', 'one')
FREEZE = lambda t: [(0, Fr(t)), (99, Fr(t))]

SEGMENTS = [
    seg(0.0, 2.86, 'HOOK', zoom=[(0.0, 1.0, 0.5, 0.5), (2.86, 1.08, 0.48, 0.5)]),
    seg(2.86, 4.45, 'CU', flash=[(3.75, 0.05)], shake=[(3.75, 4.1, 14)],
        zoom=[(2.86, 1.0, 0.5, 0.45), (t_fly - 0.05, 1.02, 0.5, 0.45), (t_fly + 0.05, 1.22, 0.5, 0.42), (4.45, 1.1, 0.5, 0.45)]),
    seg(4.45, 5.3, 'CU', whip_in=(1, 4), zoom=[(4.45, 1.0, 0.5, 0.5), (5.3, 0.96, 0.5, 0.5)]),
    seg(5.3, t_sneeze + 0.05, 'BIZ', whip_in=(-1, 4), zoom=[(5.3, 1.0, 0.5, 0.45), (t_sneeze, 1.08, 0.45, 0.4)]),
    seg(t_sneeze + 0.05, t_sneeze + 0.4, 'BIZ', map=FREEZE(t_sneeze + 0.05), flash=[(t_sneeze + 0.05, 0.06)],
        zoom=[(t_sneeze, 1.25, 0.45, 0.4), (t_sneeze + 0.4, 1.3, 0.45, 0.4)]),                       # impact freeze on the sneeze
    seg(t_sneeze + 0.4, 7.3, 'BIZ', shake=[(t_sneeze + 0.4, t_sneeze + 0.8, 10)], zoom=[(t_sneeze + 0.4, 1.1, 0.5, 0.42), (7.3, 1.0, 0.5, 0.45)]),
    seg(7.3, 12.9, 'WIDE', whip_in=(1, 5), zoom=[(7.3, 1.0, 0.5, 0.5), (t_space, 1.0, 0.5, 0.5), (t_space + 0.1, 1.12, 0.5, 0.45), (12.9, 1.18, 0.5, 0.45)]),
    seg(12.9, 15.9, 'CU', zoom=[(12.9, 1.0, 0.5, 0.55), (15.9, 1.08, 0.5, 0.55)]),
    seg(15.9, t_jumped + 0.25, 'REVEAL', zoom=[(15.9, 1.0, 0.5, 0.5), (t_jumped, 1.0, 0.5, 0.5), (t_jumped + 0.1, 1.5, 0.5, 0.32)]),
    seg(t_jumped + 0.25, 17.6, 'REVEAL', map=FREEZE(t_jumped + 0.25), fx=['freeze_tint'], flash=[(t_jumped + 0.25, 0.05)],
        zoom=[(t_jumped + 0.25, 1.5, 0.5, 0.32), (17.6, 1.6, 0.5, 0.3)]),                         # freeze: "...he jumped"
    seg(17.6, 18.75, 'CU', shake=[(t_jump, t_jump + 0.3, 12)], zoom=[(17.6, 1.05, 0.5, 0.45), (t_jump, 1.05, 0.5, 0.45), (t_jump + 0.08, 1.3, 0.5, 0.42)]),
    seg(18.75, 19.45, 'DOWN', zoom=[(18.75, 1.0, 0.5, 0.6), (19.45, 1.35, 0.5, 0.6)]),             # his view: vertigo push
    seg(19.45, t3 - 0.02, 'CU', shake=[(t_land, t_land + 0.3, 14)], zoom=[(19.45, 1.1, 0.5, 0.45), (t_land, 1.12, 0.5, 0.45), (t_land + 0.08, 1.35, 0.5, 0.42)]),
    seg(t3 - 0.02, t2 - 0.02, 'WIDE', zoom=[(t3, 1.0, 0.5, 0.45), (t2, 1.06, 0.5, 0.45)]),
    seg(t2 - 0.02, t1 - 0.02, 'CU', zoom=[(t2, 1.15, 0.5, 0.45), (t1, 1.22, 0.5, 0.45)]),
    seg(t1 - 0.02, LS['L09'][1] + 0.05, 'DOWN', zoom=[(t1, 1.0, 0.5, 0.6), (LS['L09'][1], 1.15, 0.5, 0.6)]),
    seg(LS['L09'][1] + 0.05, T_G, 'CU', zoom=[(LS['L09'][1], 1.0, 0.5, 0.45), (T_G - 0.05, 1.35, 0.5, 0.42)]),   # dead silence, slow push
    seg(T_G, 25.4, 'FALL', flash=[(T_G, 0.08)], shake=[(T_G, T_G + 0.5, 22)], whip_in=(1, 3),
        zoom=[(T_G, 1.15, 0.5, 0.45), (25.4, 1.0, 0.5, 0.45)]),
    seg(25.4, 26.2, 'GROUND', shake=[(25.5, 25.9, 16)], zoom=[(25.4, 1.0, 0.5, 0.5), (26.2, 1.08, 0.5, 0.5)]),
    seg(26.2, T_LAND, 'FALL', map=[(26.2, Fr(25.9)), (T_LAND, Fr(T_LAND))], zoom=[(26.2, 1.0, 0.5, 0.45), (T_LAND, 1.15, 0.5, 0.5)]),   # speed ramp into the landing
    seg(T_LAND, T_BONK, 'PILE', flash=[(T_LAND, 0.06)], shake=[(T_LAND, T_LAND + 0.45, 24)],
        zoom=[(T_LAND, 1.2, 0.5, 0.45), (T_LAND + 0.3, 1.0, 0.5, 0.45), (T_BONK - 0.05, 1.08, 0.5, 0.42)]),
    seg(T_BONK, T_RESET, 'PILE', map=FREEZE(T_BONK + 0.05), flash=[(T_BONK, 0.06)], shake=[(T_BONK, T_BONK + 0.2, 16)],
        zoom=[(T_BONK, 1.35, 0.5, 0.42), (T_RESET, 1.4, 0.5, 0.42)]),                               # BONK freeze
    dict(t0=T_RESET, t1=END, src='END', map=[(T_RESET, P - round((END - T_RESET) * FPS)), (END - 1 / FPS, P - 1)],
         zoom=[(T_RESET, 1.0, 0.5, 0.5), (END, 1.0, 0.5, 0.5)]),
]

OVERLAYS = [
    dict(type='title', t0=-0.1, t1=2.7, y=380, shake=True, lines=[('GRAVITY:', 104, (255, 255, 255)), ('OFF', 150, (255, 210, 61))]),
    dict(type='timer', t0=0.0, t1=t3 - 0.02, a=10.0, t_zero=(t3 - 0.02) * 10 / 7, y=140),            # story clock 10 -> 3
    dict(type='title', t0=t3 - 0.02, t1=t2 - 0.02, y=520, shake=True, lines=[('3', 300, (255, 255, 255))]),
    dict(type='title', t0=t2 - 0.02, t1=t1 - 0.02, y=520, shake=True, lines=[('2', 300, (255, 210, 61))]),
    dict(type='title', t0=t1 - 0.02, t1=LS['L09'][1] + 0.6, y=520, shake=True, lines=[('1', 300, (230, 40, 45))]),
    dict(type='timer', t0=T_G, t1=T_G + 2.6, a=0.0, t_zero=T_G, done='GRAVITY: ON', y=140),
    dict(type='chip', t0=t_phone, t1=5.3, emoji='📱', text='PHONE: ESCAPING', x=0.5, y=0.2, size=50, fill=(0, 0, 0, 200), fg=(255, 255, 255)),
    dict(type='chip', t0=t_coffee, t1=t_sneeze, emoji='☕', text='COFFEE: ALSO ESCAPING', x=0.5, y=0.2, size=46, fill=(0, 0, 0, 200), fg=(255, 255, 255)),
    dict(type='stamp', t0=t_sneeze + 0.05, t1=7.3, text='SNEEZE = ROCKET', x=0.5, y=0.22, size=84, rot=-6),
    dict(type='stamp', t0=7.5, t1=9.3, text='PHYSICS CHECK', x=0.5, y=0.22, size=84, rot=-5, color=(60, 160, 255)),
    dict(type='physics', t0=10.0, t1=15.9, anim=4.5, y=500),
    dict(type='banner', t0=t_jumped + 0.3, t1=17.6, emoji='📤', text='SEND THIS TO THE FRIEND WHO\'D JUMP', size=40, y=1600),
    dict(type='stamp', t0=t_jumped + 0.25, t1=17.6, text='~10 m UP', x=0.5, y=0.55, size=110, rot=-8),
    dict(type='chip', t0=T_LAND + 0.4, t1=29.0, emoji='💬', text='BE HONEST: WHAT WOULD YOU GRAB FIRST?', x=0.5, y=0.18, size=40,
         fill=(255, 210, 61, 245), fg=(20, 20, 24)),
    dict(type='chip', t0=29.0, t1=T_BONK, emoji='🛏️', text='SUBSCRIBE = FREE CRASH MATTRESS', x=0.5, y=0.18, size=40,
         fill=(255, 255, 255, 240), fg=(20, 20, 24), rot=-3),
    dict(type='stamp', t0=T_BONK, t1=T_RESET, text='BONK', x=0.5, y=0.25, size=150, rot=-10),
]

CAPTIONS = dict(timing=TIMING, offset=OFF, y=1420, size=94,
                emphasis={'gravity', 'off', 'ten', 'flying', 'phone', 'coffee', 'sneeze', 'space', 'spinning', 'straight',
                          'two', 'meters', 'jumped', 'jump', 'land', 'back', 'never', 'again', 'three', 'one'},
                y_over=[(0.0, 2.86, 1520)],
                hide=[(t3 - 0.02, LS['L09'][1] + 0.05)])
