"""VIDEO_006 EDL — "The 13th Floor" (2dEDIT style).

Scene time == video time (every job is rendered at the frames the edit shows, 1:1: no blending, no holds).
Black at the lights-out and at the very end; the last frame is black + DING, which flows into frame 0
(the floor display, 11:48, "12" -> "13").
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
FPS = 30
END = DURATION = 38.0
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')

T_FLIP, T_DING1, T_OUT, T_PHOTO, T_TURN, T_SLAM, T_RUNB = 0.35, 7.0, 12.0, 14.6, 16.9, 17.2, 17.5
T_DOOR13, T_WALK2, T_PEEK, T_HEAD, T_STAND, T_DARK = 20.4, 21.5, 25.3, 25.7, 26.9, 29.85
T_DING2, T_FLIP2, T_CLOCK, T_BTN, T_REFL, T_SMILE, T_BLACK = 30.4, 32.6, 33.3, 34.3, 35.0, 36.3, 37.8


def w(line, word, nth=1):
    k = 0
    for x in _T['words']:
        if x['line'] == line and x['text'].lower().strip('.!?,') == word.lower():
            k += 1
            if k == nth:
                return round(x['start'], 3)
    raise KeyError((line, word))


def S(t0, t1, job, **kw):
    d = dict(t0=t0, t1=t1, src=job, map=[(t0, t0 * FPS), (t1, t1 * FPS)], fx=['vignette'])
    d.update(kw)
    return d


def BLACK(t0, t1):
    return dict(t0=t0, t1=t1, src=None)


t_twelve, t_wasnt, t_again = w('D1', 'twelve'), w('N1', "wasn't"), w('D3', 'again')

SEGMENTS = [
    S(0.0, 0.95, 'DISP', shake=[(T_FLIP, T_FLIP + 0.3, 4)],
      zoom=[(0.0, 1.0, 0.5, 0.5), (T_FLIP, 1.02, 0.5, 0.5), (T_FLIP + 0.06, 1.14, 0.5, 0.5), (0.95, 1.18, 0.5, 0.5)]),   # 12 -> 13
    S(0.95, 2.3, 'ELEV', zoom=[(0.95, 1.0, 0.5, 0.5), (2.3, 1.06, 0.5, 0.5)]),
    S(2.3, 5.5, 'FACE', zoom=[(2.3, 1.0, 0.5, 0.45), (t_twelve, 1.1, 0.5, 0.45), (t_twelve + 0.06, 1.22, 0.5, 0.42), (5.5, 1.26, 0.5, 0.42)]),
    S(5.5, 6.35, 'DISP', shake=[(5.6, 5.95, 3)], zoom=[(5.5, 1.2, 0.5, 0.5), (6.35, 1.26, 0.5, 0.5)]),      # display glitches
    S(6.35, 6.9, 'FACE', zoom=[(6.35, 1.25, 0.5, 0.42), (6.9, 1.3, 0.5, 0.42)]),
    S(6.9, 11.9, 'OUT', zoom=[(6.9, 1.0, 0.5, 0.48), (t_wasnt, 1.22, 0.5, 0.47), (t_wasnt + 0.06, 1.34, 0.5, 0.46), (11.9, 1.4, 0.5, 0.46)]),
    S(11.9, 14.9, 'TRACK', zoom=[(11.9, 1.0, 0.5, 0.5), (14.9, 1.08, 0.5, 0.5)]),
    S(14.9, 15.85, 'PHOTO', zoom=[(14.9, 1.0, 0.5, 0.5), (15.85, 1.22, 0.5, 0.47)]),                        # the photograph
    S(15.85, 16.85, 'EYES', zoom=[(15.85, 1.0, 0.5, 0.5), (15.9, 1.0, 0.5, 0.5), (15.98, 1.16, 0.5, 0.48), (16.85, 1.2, 0.5, 0.48)]),
    S(16.85, 17.9, 'HALL', flash=[(T_SLAM, 0.05)], shake=[(T_SLAM, T_SLAM + 0.45, 14)],
      zoom=[(16.85, 1.0, 0.5, 0.5), (T_SLAM, 1.0, 0.5, 0.5), (T_SLAM + 0.05, 1.12, 0.5, 0.5), (17.9, 1.14, 0.5, 0.5)]),   # SLAM
    S(17.9, 20.35, 'DOORSIDE', shake=[(17.9, 18.4, 4), (18.4, 19.5, 9), (19.5, 20.35, 3)],
      zoom=[(17.9, 1.05, 0.5, 0.5), (20.35, 1.12, 0.5, 0.5)]),                                               # "Hey! Wait!"
    S(20.35, 23.3, 'LONG', zoom=[(20.35, 1.0, 0.5, 0.5), (23.3, 1.12, 0.5, 0.5)]),                          # the far door creaks
    S(23.3, 27.85, 'OTS', zoom=[(23.3, 1.0, 0.5, 0.5), (T_HEAD, 1.04, 0.5, 0.5), (T_HEAD + 0.9, 1.22, 0.45, 0.5), (27.85, 1.26, 0.45, 0.5)]),
    S(27.85, T_DARK, 'DOUBLE', zoom=[(27.85, 1.0, 0.5, 0.45), (t_again, 1.1, 0.5, 0.44), (t_again + 0.08, 1.24, 0.5, 0.42), (T_DARK, 1.28, 0.5, 0.42)]),
    BLACK(T_DARK, T_DING2),                                                                                   # lights out
    S(T_DING2, 32.3, 'IN', shake=[(T_DING2, T_DING2 + 0.6, 8)], zoom=[(T_DING2, 1.1, 0.5, 0.5), (32.3, 1.0, 0.5, 0.5)]),
    S(32.3, 34.2, 'DISP2', zoom=[(32.3, 1.0, 0.5, 0.5), (T_CLOCK, 1.04, 0.5, 0.5), (T_CLOCK + 0.06, 1.2, 0.5, 0.5), (34.2, 1.24, 0.5, 0.5)]),
    S(34.2, 34.9, 'BTN', zoom=[(34.2, 1.0, 0.5, 0.4), (34.9, 1.1, 0.5, 0.38)]),                           # 13 still lit
    S(34.9, T_BLACK, 'MIRROR', zoom=[(34.9, 1.0, 0.5, 0.5), (T_BLACK, 1.1, 0.45, 0.48)]),                  # the reflection smiles
    BLACK(T_BLACK, END),
]

OVERLAYS = [
    dict(type='hud', t0=0.0, t1=END, y=170, size=34, hide=[(T_DARK, T_DING2), (T_BLACK, END)],
         items=[[(0.0, '11:48 PM'), (15.0, '11:49 PM'), (T_DOOR13, '11:50 PM'), (T_PEEK, '11:51 PM'), (T_CLOCK, '11:48 PM')],
                [(0.0, 'FLOOR 12'), (T_FLIP, 'FLOOR 13'), (T_FLIP2, 'FLOOR 12')],
                [(0.0, 'PASSENGERS: 1'), (12.6, 'PASSENGERS: 0'), (30.7, 'PASSENGERS: 1'), (T_SMILE, 'PASSENGERS: 2')]],
         red=[(T_SMILE, T_BLACK, 2), (T_CLOCK, T_CLOCK + 1.8, 0)]),
    dict(type='text2d', t0=0.05, t1=2.3, text='HE PRESSED 12.', emph=('12',), y=1340, size=84),
]

CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1340, size=80, max_words=4,
                speakers={'D1': 'HIM', 'D2': 'HIM', 'D3': '???'},
                emphasis={'twelve', 'opened', "wasn't", 'wait', 'late', 'again'})
