"""TEST_3D EDL: real 3D render (Blender EEVEE, toon + ink hull), camera moves are in 3D, so frames map 1:1. Mid captions."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
FPS, END = 30, 10.0
DURATION = END
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
SEGMENTS = [dict(t0=0.0, t1=END, src='ALL', map=[(0.0, 0), (END, 299)])]
OVERLAYS = [dict(type='watermark', t0=0.0, t1=END)]
CAPTIONS = dict(timing=TIMING, offset=0.5, style='2dedit', y=1250, size=60, max_words=3, speakers={}, emphasis={'locked', 'key'})
