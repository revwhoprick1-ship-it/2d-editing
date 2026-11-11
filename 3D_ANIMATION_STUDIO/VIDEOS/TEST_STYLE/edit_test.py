"""STYLE TEST EDL: camera moves are drawn in the scene (parallax), so the EDL only maps frames 1:1. Small captions, mid-screen."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = os.path.join(HERE, 'audio', 'narration', 'timing.json')
FPS, END = 30, 10.0
DURATION = END
AUDIO = os.path.join(HERE, 'audio', 'mix_master.wav')
SEGMENTS = [dict(t0=a, t1=b, src=j, map=[(a, a * FPS), (b, b * FPS)]) for a, b, j in ((0.0, 4.2, 'HALL'), (4.2, 7.2, 'FACE'), (7.2, 10.0, 'DOOR'))]
OVERLAYS = [dict(type='watermark', t0=0.0, t1=END)]
CAPTIONS = dict(timing=TIMING, offset=0.5, style='2dedit', y=1250, size=60, max_words=3, speakers={}, emphasis={'locked', 'key'})
