#!/usr/bin/env python3
"""Re-place the dialogue with room for action: GAP[id] = extra seconds of silence (action) BEFORE that line.
Reads narration/lines/*.wav + the back-to-back timing.json from TTS; writes narration_raw.wav + timing.json (video time)."""
import json, os
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
N = os.path.join(HERE, 'narration')
GAP = {'O01': 0.35, 'N03': 0.2, 'M01': 0.3, 'N04': 0.4, 'P01': 1.15, 'N05': 0.5, 'P03': 0.75, 'O04': 0.4, 'N07': 0.3, 'N08': 0.8, 'X01': 0.4}
TAIL = 0.8
src = json.load(open(os.path.join(N, 'timing_tts.json') if os.path.exists(os.path.join(N, 'timing_tts.json')) else os.path.join(N, 'timing.json')))
json.dump(src, open(os.path.join(N, 'timing_tts.json'), 'w'), indent=1)
script = {l['id']: l for l in json.load(open(os.path.join(HERE, '..', 'script.json')))['lines']}
sr = src['sample_rate']
t = 0.0
lines, words, clips = [], [], []
for l in src['lines']:
    t += GAP.get(l['id'], 0.0)
    y, _ = sf.read(os.path.join(N, 'lines', l['id'] + '.wav'))
    if y.ndim > 1:
        y = y.mean(1)
    fi, fo = int(0.012 * sr), int(0.09 * sr)                                    # soft edges: no hard cuts
    y = y.copy(); y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo) ** 2
    d = t - l['start']
    clips.append((t, y))
    lines.append(dict(l, start=round(t, 3), end=round(t + len(y) / sr, 3)))
    words += [dict(w, start=round(w['start'] + d, 3), end=round(w['end'] + d, 3)) for w in src['words'] if w['line'] == l['id']]
    t += len(y) / sr + 0.6 * script[l['id']].get('pause_after', 0.2)
END = t + TAIL
out = np.zeros(int(END * sr) + 1)
for t0, y in clips:
    i = int(t0 * sr)
    out[i:i + len(y)] += y[:len(out) - i]
sf.write(os.path.join(N, 'narration_raw.wav'), out, sr)
json.dump(dict(src, lines=lines, words=words, duration=round(END, 3)), open(os.path.join(N, 'timing.json'), 'w'), indent=1)
print('PLACED', round(END, 2), 's')
