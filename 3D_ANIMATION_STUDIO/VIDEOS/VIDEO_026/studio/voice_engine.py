#!/usr/bin/env python3
"""VIDEO_026 voice engine — free local Qwen3-TTS ONLY (Apache-2.0). No paid TTS.

    python3 studio/voice_engine.py tts     Qwen3-TTS Base clones every line from one reference per character
                                           (N narrator, M you, B Bob; refs kept from earlier videos so the cast sounds the same).
                                           Up to 3 takes per line, faster-whisper check, token cap (PIPELINE/tts/narrate_qwen.py).
    python3 studio/voice_engine.py squeeze shorten the narrator's long inner pauses (words untouched), re-time words with faster-whisper
    python3 studio/voice_engine.py fx      SoX FX with explicit lengths + faded tails (never '-0', never trimmed after FX):
                                           B01 = Bob's voice as a tape recording from a throat (band-pass 300-3400, pitch glitch, crackle)
                                           D01 = the Mimic: Bob clone + the SAME take pitched -380 cents with chorus (always in sync)
                                                 + a noise-whisper of the same take (stereo, goes to the SFX bus).
    python3 studio/voice_engine.py place   Every line at its absolute start (timeline.START), per-line tempo (sox tempo -s), anchors
                                           (the scare lands mid-word), 12 ms / 90 ms fades -> narration_raw.wav + timing.json.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
STUDIO = os.path.abspath(os.path.join(VIDEO, '..', '..'))
N = os.path.join(VIDEO, 'audio', 'narration')
LINES_D, ORIG_D, FX_D = os.path.join(N, 'lines'), os.path.join(N, 'orig_lines'), os.path.join(N, 'fx')
QWEN_PY, NP_PY = '/opt/tools/qwen/bin/python', '/opt/tools/cbx/bin/python'


def sox(*a):
    subprocess.run(['sox', *a], check=True, stderr=subprocess.DEVNULL)


def dur(p):
    return float(subprocess.run(['soxi', '-D', p], capture_output=True, text=True).stdout.strip())


def tts():
    subprocess.run([QWEN_PY, os.path.join(STUDIO, 'PIPELINE', 'tts', 'narrate_qwen.py'), os.path.join(VIDEO, 'script.json'), N], check=True)
    shutil.copy(os.path.join(N, 'timing.json'), os.path.join(N, 'timing_tts.json'))
    print('TTS_OK')


def fx():
    import numpy as np
    import soundfile as sf
    from scipy import signal
    os.makedirs(ORIG_D, exist_ok=True); os.makedirs(FX_D, exist_ok=True)
    for f in os.listdir(LINES_D):
        if f.endswith('.wav') and not os.path.exists(os.path.join(ORIG_D, f)):
            shutil.copy(os.path.join(LINES_D, f), os.path.join(ORIG_D, f))
    tmp = tempfile.mkdtemp()
    # ---- B01: "Let me in, I'm freezing!" played back by a throat: telephone band, a pitch glitch in the middle, tape crackle
    src = os.path.join(ORIG_D, 'B01.wav'); a = os.path.join(tmp, 'b01a.wav'); d = dur(src)
    sox(src, a, 'highpass', '300', 'lowpass', '3400', 'bend', f'{d * 0.52:.2f},-260,0.07', '0.06,260,0.07', 'overdrive', '6', 'gain', '-3',
        'pad', '0', '0.25')
    y, sr = sf.read(a)
    rng = np.random.default_rng(26)
    crackle = np.zeros(len(y))
    for i in rng.integers(0, len(y) - 40, 90):                                # dusty clicks
        crackle[i:i + 30] += rng.uniform(-1, 1) * np.exp(-np.arange(30) / 6.0)
    hiss = signal.lfilter(*signal.butter(2, [900, 3200], 'bandpass', fs=sr), rng.normal(0, 1, len(y))) * 0.012
    wow = 1 + 0.06 * np.sin(2 * np.pi * 5.5 * np.arange(len(y)) / sr)          # tape flutter
    y = y * wow + crackle * 0.05 + hiss
    fo = int(0.2 * sr); y[-fo:] *= np.linspace(1, 0, fo) ** 2
    sf.write(os.path.join(LINES_D, 'B01.wav'), (y / max(1e-6, np.abs(y).max()) * 0.7).astype(np.float32), sr)
    # ---- D01: the Mimic. Layer 1 Bob (dry) + layer 2 the SAME take at -380 cents with chorus -> one mono line (always in sync).
    src = os.path.join(ORIG_D, 'D01.wav'); d = dur(src)
    low = os.path.join(tmp, 'd01_low.wav'); dry = os.path.join(tmp, 'd01_dry.wav')
    sox(src, low, 'pitch', '-380', 'chorus', '0.6', '0.9', '55', '0.4', '0.25', '2', '-t', 'pad', '0.018', '0.4', 'reverb', '22')
    sox(src, dry, 'highpass', '110', 'pad', '0', f'{dur(low) - d:.3f}')
    y1, sr = sf.read(dry); y2, _ = sf.read(low)
    y2 = y2.mean(1) if y2.ndim > 1 else y2
    n = min(len(y1), len(y2))
    mono = y1[:n] * 0.9 + y2[:n] * 0.62
    fo = int(0.25 * sr); mono[-fo:] *= np.linspace(1, 0, fo) ** 2
    sf.write(os.path.join(LINES_D, 'D01.wav'), (mono / max(1e-6, np.abs(mono).max()) * 0.75).astype(np.float32), sr)
    # layer 3: a whisper made from the same take (speech magnitudes, noise phase) + wide chorus -> stereo SFX-bus layer
    f_, t_, Z = signal.stft(y1[:n], sr, nperseg=512, noverlap=384)
    mag = signal.medfilt(np.abs(Z), kernel_size=(9, 1))                         # smear harmonics -> breath
    W_ = mag * np.exp(2j * np.pi * rng.uniform(0, 1, mag.shape))
    _, wh = signal.istft(W_, sr, nperseg=512, noverlap=384)
    wh = signal.lfilter(*signal.butter(2, 900, 'highpass', fs=sr), wh[:n])
    wp = os.path.join(tmp, 'd01_wh.wav'); sf.write(wp, (wh / max(1e-6, np.abs(wh).max()) * 0.6).astype(np.float32), sr)
    sox(wp, os.path.join(FX_D, 'D01_wide.wav'), 'channels', '2', 'chorus', '0.7', '0.9', '45', '0.5', '0.3', '2.5', '-t', '60', '0.4', '0.4', '1.8', '-s',
        'reverb', '35', 'fade', 't', '0.02', f'{n / sr:.3f}', '0.3')
    shutil.rmtree(tmp)
    print('VOICE_FX_OK')


def squeeze():
    """The narrator leaves long pauses at commas/periods. Shorten every inner pause to <= PAUSE s (sox silence -l), keep the words
    untouched, then re-time every line with faster-whisper word timestamps -> timing_tts.json. Originals stay in raw_lines/."""
    raw_d = os.path.join(N, 'raw_lines')
    os.makedirs(raw_d, exist_ok=True)
    S = json.load(open(os.path.join(VIDEO, 'script.json')))
    pause = {'M': 0.34, 'B': 0.30}
    for ln in S['lines']:
        f = ln['id'] + '.wav'
        if not os.path.exists(os.path.join(raw_d, f)):
            shutil.copy(os.path.join(LINES_D, f), os.path.join(raw_d, f))
        keep = ln.get('pause', pause.get(ln['who'], 0.13))
        sox(os.path.join(raw_d, f), os.path.join(LINES_D, f), 'silence', '-l', '1', '0.0', '0.6%', '-1', f'{keep:.2f}', '0.6%', 'pad', '0', '0.06')
    code = r"""
import json, re, sys, numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
S = json.load(open(sys.argv[1])); N = sys.argv[2]
wm = WhisperModel('small.en', device='cpu', compute_type='int8')
lines, words, t = [], [], 0.0
for ln in S['lines']:
    y, sr = sf.read(N + '/lines/' + ln['id'] + '.wav'); y = y.mean(1) if y.ndim > 1 else y
    segs, _ = wm.transcribe(resample_poly(y, 16000, sr).astype(np.float32), word_timestamps=True)
    hw = [w for s in segs for w in s.words]; tw = ln['text'].split(); d = len(y) / sr
    spans = [(w.start, w.end) for w in hw] if len(hw) == len(tw) else [(d * i / len(tw), d * (i + 1) / len(tw)) for i in range(len(tw))]
    for word, (a, b) in zip(tw, spans):
        words.append({'line': ln['id'], 'text': word, 'start': round(t + a, 3), 'end': round(t + b, 3)})
    lines.append({'id': ln['id'], 'who': ln.get('who', 'N'), 'text': ln['text'], 'start': round(t, 3), 'end': round(t + d, 3), 'exact': len(hw) == len(tw)})
    t += d + 0.2
json.dump({'voice': 'qwen3-tts', 'sample_rate': sr, 'lines': lines, 'words': words, 'duration': round(t, 3)}, open(N + '/timing_tts.json', 'w'), indent=1)
print('RETIMED', [(l['id'], round(l['end'] - l['start'], 2), l['exact']) for l in lines]); print('TOTAL', round(sum(l['end'] - l['start'] for l in lines), 2))
"""
    subprocess.run(['/opt/tools/tts312/bin/python', '-c', code, os.path.join(VIDEO, 'script.json'), N], check=True)


def place():
    import numpy as np
    import soundfile as sf
    sys.path.insert(0, HERE)
    import timeline as TL
    src_p = os.path.join(N, 'timing_tts.json')
    if not os.path.exists(src_p):
        shutil.copy(os.path.join(N, 'timing.json'), src_p)
    src = json.load(open(src_p))
    sr = src['sample_rate']
    by_id = {l['id']: l for l in src['lines']}
    order = sorted(TL.START, key=TL.START.get)

    def load(lid, tempo=1.0):
        p = os.path.join(LINES_D, lid + '.wav')
        if tempo > 1.001:
            q = os.path.join(tempfile.gettempdir(), lid + '_fit26.wav')
            sox(p, q, 'tempo', '-s', f'{tempo:.3f}')
            p = q
        y, _ = sf.read(p)
        y = y.mean(1) if y.ndim > 1 else y
        fi, fo = int(0.012 * sr), int(0.09 * sr)
        y = y.copy(); y[:fi] *= np.linspace(0, 1, fi); y[-fo:] *= np.linspace(1, 0, fo) ** 2
        return y

    def word_off(lid, word, k):
        l = by_id[lid]
        for w in src['words']:
            if w['line'] == lid and w['text'].lower().strip('.,:!?') == word:
                return (w['start'] - l['start']) * k
        return None

    lines, words, clips, prev_end = [], [], [], 0.0
    for i, lid in enumerate(order):
        l = by_id[lid]
        raw = l['end'] - l['start']
        nxt = TL.START[order[i + 1]] if i + 1 < len(order) else TL.END
        tempo = TL.TEMPO.get(lid, 1.0)
        t0 = TL.START[lid]
        for _ in range(8):
            y = load(lid, tempo)
            d = len(y) / sr
            k = d / max(0.05, raw)
            if lid in TL.ANCHOR:                                               # the anchored word starts exactly at its time
                wd, ta = TL.ANCHOR[lid]
                off = word_off(lid, wd, k)
                t0 = ta - off if off is not None else TL.START[lid]
                over = max(prev_end + 0.05 - t0, 0.0)
            elif i + 1 == len(order):                                          # the last line ends on the loop point
                t0 = max(TL.START[lid], TL.LAST_END - d)
                over = max(t0 + d - TL.LAST_END, 0.0)
            else:
                over = max(t0 + d - (nxt - 0.05), 0.0)
            if over <= 0.005 or tempo >= 1.38:
                break
            tempo = min(1.38, tempo * d / max(0.2, d - over) + 0.005)
        clips.append((t0, y))
        prev_end = t0 + d
        lines.append(dict(l, start=round(t0, 3), end=round(t0 + d, 3), tempo=round(tempo, 3)))
        words += [dict(w, start=round(t0 + (w['start'] - l['start']) * k, 3), end=round(t0 + (w['end'] - l['start']) * k, 3))
                  for w in src['words'] if w['line'] == lid]
    out = np.zeros(int(TL.END * sr) + 1)
    for t0, y in clips:
        i = int(t0 * sr); m = min(len(y), len(out) - i)
        out[i:i + m] += y[:m]
    sf.write(os.path.join(N, 'narration_raw.wav'), out, sr)
    json.dump(dict(src, lines=lines, words=words, duration=TL.END, placed=True), open(os.path.join(N, 'timing.json'), 'w'), indent=1)
    wide = os.path.join(FX_D, 'D01_wide.wav')                                  # keep the stereo whisper layer in sync with D01's tempo
    d01 = [l for l in lines if l['id'] == 'D01'][0]
    if os.path.exists(wide) and d01['tempo'] > 1.001:
        sox(wide, os.path.join(FX_D, 'D01_wide_fit.wav'), 'tempo', '-s', f"{d01['tempo']:.3f}")
    over = [(a['id'], b['id'], round(a['end'] - b['start'], 2)) for a, b in zip(lines, lines[1:]) if a['end'] > b['start'] - 0.02]
    for l in lines:
        print(f"{l['id']} {l['start']:6.2f}-{l['end']:6.2f}  x{l['tempo']:.2f}  {l['text']}")
    print('OVERLAPS', over, '| last ends', lines[-1]['end'])


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd in ('fx', 'place'):
        try:
            import soundfile  # noqa: F401
        except ImportError:                                                    # numpy/soundfile/scipy live in the cbx env
            os.execv(NP_PY, [NP_PY, os.path.abspath(__file__)] + sys.argv[1:])
    {'tts': tts, 'squeeze': squeeze, 'fx': fx, 'place': place}[cmd]()
