"""Place each voice line at its story moment (not back-to-back) -> narration_raw.wav + timing.json (video time)."""
import json, os
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
N = os.path.join(HERE, 'narration')
AT = {'D1': 2.45, 'N1': 8.35, 'D2': 18.45, 'D3': 28.3}
END = 38.0
T = json.load(open(os.path.join(N, 'timing.json')))
sr = T['sample_rate']
out = np.zeros(int(END * sr))
lines, words = [], []
for l in T['lines']:
    y, _ = sf.read(os.path.join(N, 'lines', l['id'] + '.wav'))
    t0 = AT[l['id']]
    i = int(t0 * sr)
    out[i:i + len(y)] += y[:len(out) - i]
    d = t0 - l['start']
    lines.append(dict(l, start=round(t0, 3), end=round(t0 + len(y) / sr, 3)))
    words += [dict(w, start=round(w['start'] + d, 3), end=round(w['end'] + d, 3)) for w in T['words'] if w['line'] == l['id']]
sf.write(os.path.join(N, 'narration_raw.wav'), out, sr)
json.dump(dict(T, lines=lines, words=words, duration=END), open(os.path.join(N, 'timing.json'), 'w'), indent=1)
for l in lines:
    print(l['id'], l['who'], l['start'], l['end'])
