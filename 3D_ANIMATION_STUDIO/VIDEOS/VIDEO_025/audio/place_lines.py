#!/usr/bin/env python3
"""VIDEO_025: every line at its ABSOLUTE start (timeline.START). Lines get their TEMPO (sox tempo, pitch kept) and are sped up
further (max x1.35) only if they would still run into the next line. Soft edge fades (never hard cuts). -> narration_raw.wav + timing.json."""
import json, os, subprocess, sys, tempfile
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import timeline as TL  # noqa
N = os.path.join(HERE, 'narration')
END = TL.END
src_p = os.path.join(N, 'timing_tts.json')
if not os.path.exists(src_p):
    json.dump(json.load(open(os.path.join(N, 'timing.json'))), open(src_p, 'w'), indent=1)
src = json.load(open(src_p))
sr = src['sample_rate']
order = sorted(TL.START, key=TL.START.get)


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


lines, words, clips = [], [], []
by_id = {l['id']: l for l in src['lines']}
for i, lid in enumerate(order):
    l = by_id[lid]
    nxt = TL.START[order[i + 1]] if i + 1 < len(order) else TL.T['white']
    slot = nxt - TL.START[lid] - 0.06
    tempo = TL.TEMPO.get(lid, 1.0)
    y = load(lid, tempo)
    if len(y) / sr > slot:
        tempo = min(1.35, tempo * (len(y) / sr) / slot); y = load(lid, tempo)
    t = TL.START[lid]
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
over = [(a['id'], b['id'], round(a['end'] - b['start'], 2)) for a, b in zip(lines, lines[1:]) if a['end'] > b['start'] - 0.03]
print('PLACED', [(l['id'], l['start'], l['end'], l['tempo']) for l in lines])
print('OVERLAPS', over)
