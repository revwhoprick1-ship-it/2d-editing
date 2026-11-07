"""VIDEO_002 edit decision list for PIPELINE/editing/edl_engine.py.

Every cut, punch-in, flash and graphic is timed to a narration word (Kokoro
word timestamps + 0.5 s offset) or to an animation event in the render jobs.
Loop: the last segment (EL_WIDE_END, ELEV frames 0-76) runs straight into the
first segment (EL_WIDE_JOLT from frame 77) -> one continuous elevator take.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OFF = 0.5
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
ANN_PATH = os.path.join(HERE, 'gfx', 'annotations.json')
ANN = json.load(open(ANN_PATH)) if os.path.exists(ANN_PATH) else {}


def w(line, word, nth=1, end=False):
    k = 0
    for x in _T['words']:
        if x['line'] == line and x['text'].lower().strip('.!?,') == word.lower():
            k += 1
            if k == nth:
                return round((x['end'] if end else x['start']) + OFF, 3)
    raise KeyError((line, word, nth))


def L(line, end=False):
    for l in _T['lines']:
        if l['id'] == line:
            return round((l['end'] if end else l['start']) + OFF, 3)


def head(job, char, default=(0.5, 0.35)):
    try:
        fr = ANN[job]
        k = sorted(fr, key=int)[len(fr) // 2]
        x, y, _ = fr[k][char]
        return x, y
    except Exception:
        return default


FPS = 30
END = 36.1
DURATION = END
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')

# key times
t_farted = w('L01', 'farted')
t_second = w('L01', 'second')
t_elev = w('L02', 'elevators')
t_live = w('L02', 'on')
t_wedd = w('L02', 'in', 2)
t_relax = L('L03')
t_normal = w('L03', 'normal')
t_smell = L('L04')
t_sulfur = w('L04', 'sulfur')
t_tiny = L('L05')
t_tiny_end = L('L05', True)
t_who = L('L06')
t_whofirst = w('L06', 'who')
t_sec = L('L07')
t_enh = [w('L07', 'enhance', i) for i in (1, 2, 3)]
t_one = L('L08')
t_guy = w('L08', 'guy')
t_bl1 = L('L09')
t_bl2 = w('L09', 'grandma', 2)
t_bl3 = w('L09', 'the', 2)
t_kid = L('L10')
t_him = w('L10', 'him')
t_cont = L('L11')
t_but = L('L12')
t_but_end = L('L12', True)
t_start = L('L13')

mx, my = head('EL_CCTV', 'MASCOT', (0.48, 0.47))
SEGMENTS = [
    # E01 frame 0: the worldwide fart (continuation of the last segment's take)
    dict(t0=0.0, t1=0.6, src='EL_WIDE_JOLT', f0=77, flash=[(0.0, 0.07)], shake=[(0.0, 0.35, 16)],
         zoom=[(0.0, 1.0, 0.5, 0.5), (0.1, 1.06, 0.5, 0.48), (0.6, 1.08, 0.5, 0.48)]),
    # E02 3-way reaction split
    dict(t0=0.6, t1=1.7, tiles=[dict(src='EL_CU_MASCOT1', f0=92, cy=0.42, zoom=1.0),
                                 dict(src='EL_CU_GMA1', f0=92, cy=0.40, zoom=1.0),
                                 dict(src='EL_CU_BIZ1', f0=92, cy=0.40, zoom=1.0)]),
    # E03 awkward side-eye, slow push
    dict(t0=1.7, t1=2.9, src='EL_WIDE_JOLT', f0=128, zoom=[(1.7, 1.05, 0.5, 0.48), (2.9, 1.18, 0.5, 0.45)],
         whip_out=(1, 4)),
    # E04 the planet
    dict(t0=2.9, t1=t_elev - 0.08, src='GL_POP', f0=0, whip_in=(1, 5), flash=[(2.9, 0.05)],
         zoom=[(2.9, 1.15, 0.5, 0.5), (3.4, 1.0, 0.5, 0.5)]),
    # E05 "In elevators."
    dict(t0=t_elev - 0.08, t1=t_live - 0.04, src='EL_CU_NOSE', f0=164, zoom=[(0, 1.0, 0.5, 0.45), (99, 1.0, 0.5, 0.45)],
         shake=[(t_elev - 0.08, t_elev + 0.2, 8)]),
    # E06 "On live TV."
    dict(t0=t_live - 0.04, t1=t_wedd - 0.04, src='NW_ANCHOR_CU', f0=0, zoom=[(t_live, 1.0, 0.5, 0.42), (t_live + 0.45, 1.0, 0.5, 0.42),
                                                                             (t_live + 0.5, 1.12, 0.5, 0.38), (t_wedd, 1.15, 0.5, 0.38)]),
    # E07 wedding kiss interrupted (jolt at local 22)
    dict(t0=t_wedd - 0.04, t1=t_relax + 0.05, src='WD_KISS', map=[(t_wedd - 0.04, 0), (t_wedd + 0.68, 22), (t_relax + 0.05, 22 + (t_relax + 0.09 - t_wedd - 0.68) * 30)],
         shake=[(t_wedd + 0.70, t_wedd + 1.0, 14)], zoom=[(t_wedd, 1.0, 0.5, 0.42), (t_wedd + 0.7, 1.0, 0.5, 0.42), (t_wedd + 0.75, 1.1, 0.5, 0.40), (t_relax, 1.12, 0.5, 0.40)]),
    # E08 "Scientists said: relax, farting is normal."
    dict(t0=t_relax + 0.05, t1=t_smell - 0.05, src='GL_ORBIT', f0=36, whip_in=(-1, 5),
         zoom=[(t_relax, 1.0, 0.5, 0.5), (t_smell, 1.12, 0.5, 0.5)]),
    # E09 "The smell is just a tiny bit of sulfur gas." -> slow push on polite guests
    dict(t0=t_smell - 0.05, t1=t_tiny - 0.02, src='WD_GUESTS', map=[(t_smell - 0.05, 50), (t_tiny - 0.02, 141)],
         zoom=[(t_smell, 1.0, 0.5, 0.45), (t_tiny, 1.1, 0.42, 0.40)]),
    # E10a "Tiny." -> hold the stiff smiles (dramatic beat)
    dict(t0=t_tiny - 0.02, t1=t_tiny_end + 0.02, src='WD_GUESTS', map=[(t_tiny, 141), (t_tiny_end, 141)],
         zoom=[(t_tiny, 1.1, 0.42, 0.40), (t_tiny_end, 1.28, 0.38, 0.36)]),
    # E10b domino faint (speed ramp: snap)
    dict(t0=t_tiny_end + 0.02, t1=t_who - 0.04, src='WD_FAINT', map=[(t_tiny_end, 142), (t_tiny_end + 0.25, 146), (t_who - 0.04, 176)],
         flash=[(t_tiny_end + 0.02, 0.05)], shake=[(t_tiny_end + 0.3, t_who, 20)]),
    # E11 news: who farted first?
    dict(t0=t_who - 0.04, t1=t_sec - 0.03, src='NW_WIDE', map=[(t_who - 0.04, 40), (t_sec - 0.03, 133)],
         zoom=[(t_who, 1.2, 0.5, 0.42), (t_whofirst, 1.24, 0.5, 0.42), (t_whofirst + 0.15, 1.38, 0.5, 0.40), (t_sec, 1.40, 0.5, 0.40)]),
    # E12 CCTV + ENHANCE x3
    dict(t0=t_sec - 0.03, t1=t_enh[2] + 0.55, src='EL_CCTV', map=[(0, 140), (99, 140)], fx=['cctv'],
         zoom=[(t_sec, 1.0, 0.5, 0.5), (t_enh[0], 1.0, 0.5, 0.5), (t_enh[0] + 0.1, 1.9, mx, my),
               (t_enh[1], 1.9, mx, my), (t_enh[1] + 0.1, 3.4, mx, my), (t_enh[2], 3.4, mx, my), (t_enh[2] + 0.1, 6.0, mx, my)],
         pixelate=[(t_enh[0] + 0.1, t_enh[0] + 0.35, 26, 4), (t_enh[1] + 0.1, t_enh[1] + 0.35, 30, 6), (t_enh[2] + 0.1, t_enh[2] + 0.45, 38, 9)],
         flash=[(t_enh[0], 0.06), (t_enh[1], 0.06), (t_enh[2], 0.06)]),
    dict(t0=t_enh[2] + 0.55, t1=t_one - 0.02, src='EL_CCTV_FACE', map=[(0, 140), (99, 140)], fx=['cctv'], flash=[(t_enh[2] + 0.55, 0.08)],
         zoom=[(t_enh[2] + 0.55, 1.15, 0.5, 0.42), (t_one, 1.25, 0.5, 0.42)]),
    # E13a "One elevator." -> everyone turns to stare
    dict(t0=t_one - 0.02, t1=t_guy - 0.05, src='EL_STARE', map=[(t_one, 200), (t_guy - 0.05, 229)],
         zoom=[(t_one, 1.0, 0.5, 0.5), (t_guy, 1.1, 0.5, 0.45)]),
    # E13b "One guy." -> freeze frame
    dict(t0=t_guy - 0.05, t1=t_guy + 0.22, src='EL_GUILTY', map=[(t_guy - 0.05, 230), (t_guy + 0.22, 238)],
         zoom=[(t_guy - 0.05, 1.0, 0.5, 0.42), (t_guy + 0.22, 1.04, 0.5, 0.42)]),
    dict(t0=t_guy + 0.22, t1=t_bl1 - 0.03, src='EL_GUILTY', map=[(0, 238), (99, 238)], fx=['freeze_tint'],
         flash=[(t_guy + 0.22, 0.06)], zoom=[(t_guy + 0.22, 1.04, 0.5, 0.42), (t_guy + 0.28, 1.22, 0.5, 0.40), (t_bl1, 1.26, 0.5, 0.40)]),
    # E14-E16 blame chain with whip pans following the pointing fingers
    dict(t0=t_bl1 - 0.03, t1=t_bl2 - 0.1, src='EL_BLAME1', map=[(t_bl1 - 0.03, 260), (t_bl2 - 0.1, 260 + (t_bl2 - t_bl1 - 0.07) * 30)],
         whip_out=(-1, 4), zoom=[(t_bl1, 1.0, 0.5, 0.45), (t_bl1 + 0.25, 1.08, 0.5, 0.45)]),
    dict(t0=t_bl2 - 0.1, t1=t_bl3 - 0.08, src='EL_BLAME2', map=[(t_bl2 - 0.1, 306), (t_bl3 - 0.08, 306 + (t_bl3 - t_bl2 + 0.02) * 30)],
         whip_in=(-1, 4), whip_out=(1, 4), zoom=[(t_bl2, 1.0, 0.5, 0.45), (t_bl2 + 0.25, 1.08, 0.5, 0.45)]),
    dict(t0=t_bl3 - 0.08, t1=t_kid - 0.06, src='EL_BLAME3', map=[(t_bl3 - 0.08, 354), (t_kid - 0.06, 354 + (t_kid - t_bl3 + 0.02) * 30)],
         whip_in=(1, 4), whip_out=(1, 4), zoom=[(t_bl3, 1.0, 0.5, 0.45), (t_bl3 + 0.25, 1.08, 0.5, 0.45)]),
    # E17 "And the kid... blamed him." (deadpan hold, then the point lands on "him")
    dict(t0=t_kid - 0.06, t1=t_him + 0.18, src='EL_BLAME4', map=[(t_kid - 0.06, 404), (t_him - 0.35, 405), (t_him - 0.05, 412), (t_him + 0.18, 418)],
         whip_in=(1, 4), zoom=[(t_kid, 1.0, 0.5, 0.45), (t_him - 0.06, 1.0, 0.5, 0.45), (t_him, 1.15, 0.4, 0.42)]),
    # E18 mascot shocked (boing)
    dict(t0=t_him + 0.18, t1=t_cont - 0.05, src='EL_SHOCK', f0=434, flash=[(t_him + 0.18, 0.05)],
         zoom=[(t_him + 0.18, 1.25, 0.5, 0.42), (t_him + 0.3, 1.05, 0.5, 0.42)], shake=[(t_him + 0.18, t_him + 0.4, 12)]),
    # E19 "Farts aren't contagious... But this one?" (innocent whistle) + dramatic punch
    dict(t0=t_cont - 0.05, t1=t_but_end + 0.25, src='EL_WHISTLE', map=[(t_cont - 0.05, 450), (t_but_end + 0.25, 529)],
         zoom=[(t_cont, 1.0, 0.5, 0.45), (t_but - 0.05, 1.12, 0.5, 0.42), (t_but + 0.05, 1.35, 0.5, 0.40), (t_but_end + 0.25, 1.38, 0.5, 0.40)]),
    # E20 VHS rewind through the whole video (back to 3:13:59)
    dict(t0=t_but_end + 0.25, t1=t_start - 0.02, rewind=(t_but_end, 0.4)),
    # E21 the calm elevator, one tiny pfft -> loops into E01
    dict(t0=t_start - 0.02, t1=END, src='EL_WIDE_END', map=[(t_start - 0.02, 0), (END, 77 - 1 + 1 / 30.0 * 0)]),
]
# make E21 land exactly on frame 76 at the last video frame (frame 77 = video frame 0 -> seamless take)
_n_end = round((END - (t_start - 0.02)) * FPS)
SEGMENTS[-1]['map'] = [(t_start - 0.02, 76 - (_n_end - 1)), (END - 1 / FPS, 76)]

gx, gy = head('EL_BLAME1', 'GRANDMA', (0.25, 0.32))
bx, by = head('EL_BLAME3', 'BUSINESSMAN', (0.45, 0.25))
kx, ky = head('EL_BLAME3', 'KID', (0.8, 0.45))
k4x, k4y = head('EL_BLAME4', 'KID', (0.6, 0.35))
emx, emy = head('EL_WHISTLE', 'MASCOT', (0.5, 0.4))

OVERLAYS = [
    # opening title + clock (frame 0)
    dict(type='title', t0=0.0, t1=t_farted + 0.5, y=470, shake=True,
         lines=[('8,000,000,000', 132, (255, 210, 61)), ('FARTS. 1 SECOND.', 92, (255, 255, 255))]),
    dict(type='clock', t0=0.0, t1=2.9, text='3:14:00 PM'),
    # planet counter
    dict(type='counter', t0=2.95, t1=t_elev - 0.08, a=0, b=8_000_000_000, dur=0.55, label='PEOPLE. SAME SECOND.', y=330),
    # SHARE (relatable elevator moment)
    dict(type='banner', t0=t_elev + 0.05, t1=t_wedd + 0.2, emoji='📤', text='SEND THIS TO YOUR ELEVATOR BUDDY', size=40, y=260),
    dict(type='live_bug', t0=t_live - 0.04, t1=t_wedd - 0.04, text='WORLD NEWS 24'),
    # science chip
    dict(type='chip', t0=t_normal, t1=t_smell - 0.05, emoji='✅', text='TOTALLY NORMAL', x=0.5, y=0.20, size=58,
         fill=(60, 200, 110, 245), fg=(255, 255, 255)),
    dict(type='chip', t0=t_relax + 0.4, t1=t_smell - 0.05, text='MOST PEOPLE: 13–21× A DAY', x=0.5, y=0.27, size=40,
         fill=(0, 0, 0, 180), fg=(255, 255, 255)),
    # tiny sulfur speck drifting to grandma's nose
    dict(type='speck', t0=t_smell + 0.1, t1=t_tiny_end, x0=0.95, y0=0.30, x1=0.38, y1=0.36, label='SULFUR (TINY)',
         t_label=t_sulfur),
    # news graphics + SUBSCRIBE gag in the ticker
    dict(type='live_bug', t0=t_who - 0.04, t1=t_sec - 0.03, text='WORLD NEWS 24'),
    dict(type='lower_third', t0=t_who + 0.1, t1=t_sec - 0.03, text='WHO FARTED FIRST?', t_head=t_whofirst, y=1300),
    dict(type='ticker', t0=t_who - 0.04, t1=t_sec - 0.03, y=1440, speed=380,
         text='SUBSCRIBERS OF THIS CHANNEL REPORT ZERO SMELL: "WE SAW IT COMING"  •  ELEVATORS EVACUATED WORLDWIDE  •  WEDDING KISSES POSTPONED  •'),
    # CCTV hud + enhance boxes
    dict(type='cctv_hud', t0=t_sec - 0.03, t1=t_one - 0.02, stamp='2026-11-07  15:14:00', cam='CAM 02 · ELEVATOR B'),
    dict(type='enhance', t0=t_enh[0], t1=t_enh[0] + 0.5, x=0.5, y=0.5, box=360),
    dict(type='enhance', t0=t_enh[1], t1=t_enh[1] + 0.5, x=0.5, y=0.5, box=420),
    dict(type='enhance', t0=t_enh[2], t1=t_enh[2] + 0.5, x=0.5, y=0.5, box=480),
    dict(type='stamp', t0=t_enh[2] + 0.6, t1=t_one - 0.02, text='MATCH FOUND', x=0.5, y=0.78, color=(60, 255, 120), size=86, rot=-4),
    # freeze frame + LIKE gag
    dict(type='stamp', t0=t_guy + 0.22, t1=t_bl1 - 0.03, text='SUSPECT #1', x=0.5, y=0.70, size=110, rot=-8),
    dict(type='chip', t0=t_guy + 0.35, t1=t_bl1 + 1.2, emoji='👍', text='LIKE = GUILTY', x=0.5, y=0.17, size=62,
         fill=(30, 110, 255, 245), fg=(255, 255, 255), rot=3),
    # COMMENT prompt + numbered suspects during the blame chain
    dict(type='banner', t0=t_bl1 + 0.3, t1=t_him + 0.18, emoji='💬', text='WHO DID IT? COMMENT 1, 2 OR 3', size=44, y=230,
         fill=(255, 210, 61, 245), fg=(20, 20, 24)),
    dict(type='tag', t0=t_bl1 + 0.45, t1=t_bl2 - 0.1, n='1', label='GRANDMA', x=gx, y=max(0.12, gy - 0.14)),
    dict(type='tag', t0=t_bl2 + 0.1, t1=t_bl3 - 0.08, n='1', label='GRANDMA', x=0.30, y=0.20),
    dict(type='tag', t0=t_bl3 + 0.2, t1=t_kid - 0.06, n='2', label='BUSINESSMAN', x=bx, y=max(0.12, by - 0.15)),
    dict(type='tag', t0=t_bl3 + 0.6, t1=t_kid - 0.06, n='3', label='KID', x=min(0.85, kx), y=max(0.12, ky - 0.14)),
    dict(type='tag', t0=t_kid + 0.1, t1=t_him + 0.18, n='3', label='KID', x=k4x, y=max(0.12, k4y - 0.15)),
    # innocent whistling: sweat
    dict(type='sweat', t0=t_cont + 0.2, t1=t_but_end + 0.25, drops=[(emx - 0.16, emy - 0.12, 0.0), (emx + 0.17, emy - 0.08, 0.45)]),
    # rewind HUD + final clock (3:13:59 -> loop to 3:14:00)
    dict(type='rewind_hud', t0=t_but_end + 0.25, t1=t_start - 0.02),
    dict(type='clock', t0=t_start - 0.02, t1=END, text='3:13:59 PM'),
]

CAPTIONS = dict(timing=TIMING, offset=OFF, y=1250, size=92,
                emphasis={'billion', 'farted', 'second', 'elevators', 'tv', 'wedding', 'kiss', 'normal', 'tiny',
                          'sulfur', 'first', 'enhance', 'guy', 'grandma', 'businessman', 'kid', 'him', 'contagious'},
                y_over=[(0.0, 2.9, 1330), (t_who - 0.04, t_sec - 0.03, 1120), (t_sec - 0.03, t_one, 1350)],
                hide=[(t_but_end + 0.25, t_start - 0.02)])
