"""VIDEO_025 EDL — "The World Ends In 60 Seconds". Hybrid render (3D plates + flat puppets) is drawn by anim.py, frames map 1:1.
The HUD clock is real time (1:00 -> 0:00). Choice card + 'One, two, or three. Choose.' in the last 3 s, white-out at 0:00, loops."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import timeline as TL  # noqa: E402

T, END, FPS = TL.T, TL.END, TL.FPS
DURATION = END
TIMING = TL.TIMING
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
L = TL.LINES

SHAKE = [(0.0, 0.3, 10), (T['crash'], T['crash'] + 0.5, 24), (T['pano'] + 0.45, T['pano'] + 0.75, 10), (T['lift'], T['slam'], 4),
         (T['slam'], T['slam'] + 0.45, 34), (T['scare'], T['scare'] + 0.4, 44), (T['door'], T['door'] + 0.3, 14),
         (T['rumble'], T['rip'], 6), (T['rip'], T['rip'] + 0.6, 40), (T['kept'], T['kept'] + 0.25, 12), (T['lock'], T['lock'] + 0.5, 30)]
SEGMENTS = [dict(t0=0.0, t1=END, src='ALL', map=[(0.0, 0.0), (END, END * FPS)], shake=SHAKE,
                 flash=[(T['scare'], 0.07), (T['slam'], 0.05)],
                 fx_t=[(T['scare'], T['scare'] + 0.22, 'glitch'), (T['kept'], T['kept'] + 0.2, 'glitch'), (T['rip'], T['rip'] + 0.12, 'chroma')])]

CLOCK = [(float(k), TL.clock(float(k))) for k in range(0, 60)] + [(T['white'], '0:00')]
OVERLAYS = [
    dict(type='hud3', t0=0.0, t1=T['white'], y=190, size=48, flash=0.3,
         cols=[([(0, 'WORLD ENDS IN')], CLOCK),
               ([(0, 'SKY')], [(0, 'CRACKING'), (T['grav'], 'BREAKING'), (T['rip'], 'OPEN')]),
               ([(0, 'SELECTED')], [(0, 'SCANNING'), (T['high'], 'SEARCHING'), (T['kept'], '1 HUMAN'), (T['lock'], 'YOU')])]),
    dict(type='choice', t0=T['choice'], t1=T['white'], y=1000, header='3 SECONDS LEFT. CHOOSE.', stagger=0.35,
         options=['GO. LEAVE MIA BEHIND', 'GIVE MIA YOUR PLACE', 'STAY. NEVER LET GO'], footer='COMMENT 1, 2 OR 3'),
    dict(type='watermark', t0=0.0, t1=END),
]
SPK = {'M01': 'YOU', 'M02': 'YOU', 'M03': 'YOU', 'S01': 'MIA', 'S02': 'MIA', 'S03': 'MIA', 'S04': 'MIA', 'P01': 'MOM', 'P02': 'MOM'}
HIDE = [(T['phone1'], T['run']), (T['phone2'], T['lock']), (T['choice'], END)]      # the phone shows the alert text itself
CAPTIONS = dict(timing=TIMING, offset=0.0, style='2dedit', y=1240, size=68, max_words=3, speakers=SPK, hide=HIDE,
                emphasis={'screamed', 'alone', 'ran', 'gravity', 'blinked', 'mia', 'promise', 'lights', 'someone', 'come',
                          'go', 'let', 'me', 'you', 'without', 'hurt', 'one', 'stay', 'choose'})
