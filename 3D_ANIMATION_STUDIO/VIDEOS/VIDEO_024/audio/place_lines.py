#!/usr/bin/env python3
"""VIDEO_024: place every line at the blueprint's ABSOLUTE start time. If a line is longer than its slot, it is sped up
(sox tempo, pitch kept, max x1.35) to fit. N12 + N13 are placed backwards from the end so 'now' ends at 54.9 s (the blueprint's
2.5 s for N12 / 0.5 s for N13 are physically too short). Writes narration_raw.wav + timing.json (video time)."""
import json, os, subprocess, tempfile
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
N = os.path.join(HERE, 'narration')
END = 55.0
START = {'N01': 0.5, 'N02': 4.5, 'N03': 6.0, 'N04': 8.5, 'M01': 11.0, 'N05': 14.5, 'N06': 19.0, 'N07': 22.5, 'N08': 26.0, 'G01': 30.0,
         'N09': 33.5, 'N10': 40.0, 'N11': 43.0, 'D01': 46.5}
src = json.load(open(os.path.join(N, 'timing_tts.json') if os.path.exists(os.path.join(N, 'timing_tts.json')) else os.path.join(N, 'timing.json')))
json.dump(src, open(os.path.join(N, 'timing_tts.json'), 'w'), indent=1)
sr = src['sample_rate']
order = [l['id'] for l in src['lines']]


def load(lid, tempo=1.0):
    p = os.path.join(N, 'lines', lid + '.wav')
    if tempo > 1.001:
        q = os.path.join(tempfile.gettempdir(), lid + '_fit.wav')
        subprocess.run(['sox', p, q, 'tempo', '-s', f'{tempo:.3f}'], check=True, stderr=subprocess.DEVNULL)
        p = q
    y, _ = sf.read(p)
    y = y.mean(1) if y.ndim > 1 else y
    fi, fo = int(0.012 * sr), int(0.09 * sr)
    y = y.copy(); y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo) ** 2
    return y


# the ending: N13 ends at 54.9, N12 right before it (tempo up to 1.2 if needed to stay after D01)
y13 = load('N13'); START['N13'] = 54.9 - len(y13) / sr
t12 = 1.0
y12 = load('N12')
d01_end = START['D01'] + len(load('D01')) / sr
while START['N13'] - 0.12 - len(y12) / sr < d01_end + 0.3 and t12 < 1.35:
    t12 += 0.05; y12 = load('N12', t12)
START['N12'] = START['N13'] - 0.12 - len(y12) / sr
lines, words, clips = [], [], []
for i, l in enumerate(src['lines']):
    lid = l['id']
    slot = (START[order[i + 1]] if i + 1 < len(order) else END) - START[lid] - 0.08
    y = load(lid) if lid not in ('N12', 'N13') else (y12 if lid == 'N12' else y13)
    tempo = 1.0
    if lid not in ('N12', 'N13') and len(y) / sr > slot:
        tempo = min(1.35, (len(y) / sr) / slot); y = load(lid, tempo)
    if lid == 'N12':
        tempo = t12
    t = START[lid]
    clips.append((t, y))
    k_ = (len(y) / sr) / max(0.05, l['end'] - l['start'])
    lines.append(dict(l, start=round(t, 3), end=round(t + len(y) / sr, 3), tempo=round(tempo, 3)))
    words += [dict(w, start=round(t + (w['start'] - l['start']) * k_, 3), end=round(t + (w['end'] - l['start']) * k_, 3))
              for w in src['words'] if w['line'] == lid]
out = np.zeros(int(END * sr) + 1)
for t0, y in clips:
    i = int(t0 * sr); out[i:i + len(y)] += y[:len(out) - i]
sf.write(os.path.join(N, 'narration_raw.wav'), out, sr)
json.dump(dict(src, lines=lines, words=words, duration=END), open(os.path.join(N, 'timing.json'), 'w'), indent=1)
print('PLACED', END, [(l['id'], l['start'], l['end'], l['tempo']) for l in lines if l['tempo'] > 1.0])
