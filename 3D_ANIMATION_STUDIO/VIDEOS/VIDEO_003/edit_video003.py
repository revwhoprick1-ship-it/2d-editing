"""VIDEO_003 EDL for PIPELINE/editing/edl_engine.py — "What If ALL Drugs Became Legal?"

Voice starts on frame 0 (VIDEO_002 lost viewers in a 0.5 s silent start). Every job's local
frame 0 sits at its JOBS t0 in video002-style 1:1 time, so f0 = 0 at t0. The PINK take runs
across the loop seam: E13 ends on local frame SEAM-1, and E01 starts on SEAM.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OFF = 0.0
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
_T = json.load(open(TIMING))
FPS = 30
END = DURATION = 33.0
SEAM = 234
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
GRADE = None   # natural colour straight from the render (user asked for normal, not vibrant)


def w(line, word, nth=1, end=False):
    k = 0
    for x in _T['words']:
        if x['line'] == line and x['text'].lower().strip('.!?,:\'"') == word.lower():
            k += 1
            if k == nth:
                return round(x['end'] if end else x['start'], 3)
    raise KeyError((line, word))


def L(line, end=False):
    return next(round(l['end'] if end else l['start'], 3) for l in _T['lines'] if l['id'] == line)


t_14 = w('L03', 'fourteen')
t_unemp = w('L04', 'unemployed')
t_linked = w('L05', 'linkedin')
t_pharm = w('L05', 'pharmacist')
t_pod = w('L06', 'podcast')
t_twist = L('L07')
t_port = L('L08')
t_deaths = L('L09')
t_zombie = w('L09', 'zombie')
t_safe = w('L10', 'safe')
t_lungs = w('L10', 'lungs')
t_q = L('L11')
t_hand = w('L12', 'hand')
t_again = L('L13')

SEGMENTS = [
    # E01 frame 0: he's already mid-jump, stamp on screen, voice on frame 0
    dict(t0=0.0, t1=2.2, src='PINK_START', f0=SEAM, shake=[(0.0, 0.3, 14)],
         zoom=[(0.0, 1.18, 0.5, 0.42), (0.18, 1.0, 0.5, 0.45), (2.2, 1.06, 0.5, 0.42)]),
    # E02-E03 grandma: deadpan, then punch-in on "fourteen"
    dict(t0=2.2, t1=5.75, src='GRANDMA', map=[(2.2, 1.5), (5.75, 108)], flash=[(2.2, 0.05)],
         zoom=[(2.2, 1.0, 0.5, 0.40), (t_14 - 0.05, 1.06, 0.5, 0.36), (t_14 + 0.05, 1.45, 0.5, 0.30), (5.75, 1.5, 0.5, 0.30)]),
    # E04 dealer: "Unemployed overnight" (sad), E05 LinkedIn glow-up
    dict(t0=5.75, t1=8.1, src='DEALER', map=[(5.75, 0), (8.1, 70.5)], whip_in=(1, 4),
         zoom=[(5.75, 1.0, 0.5, 0.5), (t_unemp, 1.0, 0.5, 0.5), (t_unemp + 0.1, 1.15, 0.5, 0.42), (8.1, 1.18, 0.5, 0.42)]),
    dict(t0=8.1, t1=11.05, src='DEALER', map=[(8.1, 70.5), (11.05, 159)], flash=[(8.1, 0.05)],
         zoom=[(8.1, 1.05, 0.5, 0.40), (11.05, 1.12, 0.5, 0.38)]),
    # E06 cartel podcast, punch-in on "podcast"
    dict(t0=11.05, t1=t_twist - 0.05, src='PODCAST', map=[(11.05, 0), (t_twist - 0.05, (t_twist - 0.05 - 11.05) * 30)], whip_in=(-1, 4),
         zoom=[(11.05, 1.0, 0.5, 0.42), (t_pod - 0.05, 1.04, 0.5, 0.42), (t_pod + 0.05, 1.25, 0.5, 0.40), (t_twist, 1.28, 0.5, 0.40)]),
    # E07 "But here's the twist" - freeze + scratch, push in
    dict(t0=t_twist - 0.05, t1=t_port - 0.05, src='PODCAST', map=[(0, (t_twist - 0.05 - 11.05) * 30), (99, (t_twist - 0.05 - 11.05) * 30)],
         fx=['freeze_tint'], flash=[(t_twist - 0.05, 0.06)], zoom=[(t_twist, 1.28, 0.5, 0.40), (t_port, 1.5, 0.5, 0.38)]),
    # E08 globe dive to Portugal (sped up a little so it lands on "2001")
    dict(t0=t_port - 0.05, t1=t_zombie - 0.35, src='GLOBE', map=[(t_port - 0.05, 0), (w('L08', '2001'), 120), (t_zombie - 0.35, 159)],
         whip_in=(1, 5), zoom=[(t_port, 1.0, 0.5, 0.5), (t_zombie, 1.1, 0.5, 0.5)]),
    # E09 "Nobody turned into a zombie" -> zombie snaps back to normal on "zombie"
    dict(t0=t_zombie - 0.35, t1=21.5, src='ZOMBIE', map=[(t_zombie - 0.35, 0), (t_zombie + 0.15, 14), (t_zombie + 0.4, 24), (21.5, 46)],
         flash=[(t_zombie - 0.35, 0.05)], zoom=[(t_zombie - 0.35, 1.15, 0.5, 0.42), (21.5, 1.05, 0.5, 0.42)]),
    # E10 legal != safe -> cough fit
    dict(t0=21.5, t1=25.2, src='LUNGS', f0=0, whip_in=(-1, 4), shake=[(24.2, 25.0, 10)],
         zoom=[(21.5, 1.0, 0.5, 0.45), (t_lungs, 1.05, 0.5, 0.45), (t_lungs + 0.1, 1.3, 0.5, 0.40), (25.2, 1.32, 0.5, 0.40)]),
    # E11-E13 PINK take: question -> phone -> "watch this again" (ends on local SEAM-1, loops into E01)
    dict(t0=25.2, t1=27.6, src='PINK_END', f0=0, flash=[(25.2, 0.05)], zoom=[(25.2, 1.0, 0.5, 0.45), (27.6, 1.06, 0.5, 0.43)]),
    dict(t0=27.6, t1=t_again, src='PINK_END', f0=0, zoom=[(27.6, 1.12, 0.5, 0.55), (t_hand - 0.05, 1.15, 0.5, 0.58), (t_hand + 0.05, 1.4, 0.55, 0.62), (t_again, 1.42, 0.55, 0.62)]),
    dict(t0=t_again, t1=END, src='PINK_END', map=[(t_again, (t_again - 25.2) * 30), (END - 1 / FPS, SEAM - 1)],
         zoom=[(t_again, 1.0, 0.5, 0.42), (END, 1.12, 0.5, 0.40)]),
]

OVERLAYS = [
    dict(type='title', t0=-0.10, t1=2.15, y=380, shake=True,
         lines=[('ALL DRUGS', 124, (255, 225, 60)), ('= LEGAL', 104, (255, 255, 255))]),
    dict(type='counter', t0=t_14 - 0.05, t1=5.75, a=0, b=14, dur=0.45, label='PRESCRIPTIONS', y=330),
    dict(type='stamp', t0=t_unemp, t1=8.1, text='UNEMPLOYED', x=0.5, y=0.22, size=104, rot=-7),
    dict(type='chip', t0=t_linked, t1=11.05, emoji='💼', text='FREELANCE PHARMACIST', x=0.5, y=0.17, size=58,
         fill=(10, 102, 194, 250), fg=(255, 255, 255)),
    dict(type='chip', t0=t_pharm + 0.2, t1=11.05, emoji='👍', text='LIKE = ENDORSE HIS SKILLS', x=0.5, y=0.24, size=44,
         fill=(255, 255, 255, 245), fg=(10, 102, 194), rot=-3),
    dict(type='lower_third', t0=11.3, t1=t_twist - 0.05, text="CARTEL CAST · EP.1: 'WE'RE PIVOTING'", t_head=11.3, y=1500),
    dict(type='ticker', t0=11.05, t1=t_twist - 0.05, y=1640, speed=420,
         text='SUBSCRIBE TO CARTEL CAST? NO. SUBSCRIBE TO THIS CHANNEL.  •  NEW EPISODE: "TAXES, WHAT ARE THOSE?"  •'),
    dict(type='chip', t0=t_port + 0.3, t1=t_zombie - 0.35, text='PORTUGAL · 2001 · DECRIMINALIZED', x=0.5, y=0.17, size=46,
         fill=(0, 0, 0, 200), fg=(255, 255, 255)),
    dict(type='chip', t0=t_deaths, t1=t_zombie - 0.35, emoji='📉', text='DRUG DEATHS: DOWN', x=0.5, y=0.24, size=50,
         fill=(60, 200, 110, 245), fg=(255, 255, 255)),
    dict(type='banner', t0=t_zombie - 0.35, t1=25.2, emoji='💬', text='WOULD THIS WORK IN YOUR COUNTRY?', size=44, y=230,
         fill=(255, 210, 61, 245), fg=(20, 20, 24)),
    dict(type='chip', t0=t_safe, t1=25.2, emoji='⚠️', text='LEGAL ≠ SAFE', x=0.5, y=0.30, size=70,
         fill=(255, 255, 255, 250), fg=(220, 20, 50), rot=-4),
    dict(type='chip', t0=t_hand + 0.1, t1=t_again, emoji='📤', text='SEND TO SOMEONE GLUED TO THEIRS', x=0.5, y=0.17, size=40,
         fill=(255, 255, 255, 240), fg=(20, 20, 24)),
]

CAPTIONS = dict(timing=TIMING, offset=OFF, y=1300, size=96,
                emphasis={'drug', 'legal', 'grandma', 'fourteen', 'unemployed', 'linkedin', 'pharmacist', 'cartels',
                          'podcast', 'twist', 'portugal', '2001', 'down', 'zombie', 'safe', 'lungs', 'addictive',
                          'free', 'hand', 'again'},
                y_over=[(0.0, 2.2, 1420), (t_14 - 0.05, 5.75, 1680), (11.05, t_twist, 1250)])
