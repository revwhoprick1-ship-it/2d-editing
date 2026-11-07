#!/usr/bin/env python3
"""Objective narration QC.  I (the pipeline) cannot *hear*, so every take is
checked with proxies that catch the most common TTS failures:

  * intelligibility  - local Whisper (faster-whisper) transcription vs. script -> word error rate
  * pronunciation    - per-word mismatches are listed so problem words can get phoneme overrides
  * pacing           - words per second, longest internal pause
  * expressiveness   - pitch (f0) range in semitones and f0 standard deviation
  * level            - peak, RMS, clipping count

Usage:
  /opt/tools/tts312/bin/python PIPELINE/tts/voice_qc.py WAV "expected text" [--json out.json]
  or import qc_file() from other scripts.
"""
import argparse
import json
import re
import sys

import numpy as np
import soundfile as sf

_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel('small.en', device='cpu', compute_type='int8')
    return _MODEL


def norm_words(t):
    t = t.lower().replace('-', ' ').replace('—', ' ')
    t = re.sub(r"[^a-z0-9' ]+", ' ', t)
    return [w for w in t.split() if w]


def wer(ref, hyp):
    r, h = norm_words(ref), norm_words(hyp)
    d = np.zeros((len(r) + 1, len(h) + 1), int)
    d[:, 0] = range(len(r) + 1)
    d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    # backtrace mismatches
    i, j, miss = len(r), len(h), []
    while i > 0 and j > 0:
        if r[i - 1] == h[j - 1]:
            i, j = i - 1, j - 1
        elif d[i, j] == d[i - 1, j - 1] + 1:
            miss.append((r[i - 1], h[j - 1])); i, j = i - 1, j - 1
        elif d[i, j] == d[i - 1, j] + 1:
            miss.append((r[i - 1], None)); i -= 1
        else:
            miss.append((None, h[j - 1])); j -= 1
    return d[len(r), len(h)] / max(1, len(r)), list(reversed(miss))


def f0_track(x, sr, fmin=70, fmax=400, hop=0.01, win=0.04):
    n, h = int(win * sr), int(hop * sr)
    out = []
    for s in range(0, len(x) - n, h):
        fr = x[s:s + n] * np.hanning(n)
        if np.sqrt(np.mean(fr ** 2)) < 0.01:
            continue
        ac = np.correlate(fr, fr, 'full')[n - 1:]
        ac /= ac[0] + 1e-9
        lo, hi = int(sr / fmax), int(sr / fmin)
        k = np.argmax(ac[lo:hi]) + lo
        if ac[k] > 0.45:
            out.append(sr / k)
    return np.array(out)


def qc_file(path, text):
    x, sr = sf.read(path, dtype='float32')
    if x.ndim > 1:
        x = x.mean(1)
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(16000, sr)
    x16 = resample_poly(x, 16000 // g, sr // g).astype(np.float32)
    segs, info = _model().transcribe(x16, beam_size=5, language='en', word_timestamps=True)
    segs = list(segs)
    hyp = ' '.join(s.text for s in segs)
    e, miss = wer(text, hyp)
    words = [w for s in segs for w in (s.words or [])]
    gaps = [b.start - a.end for a, b in zip(words, words[1:])]
    dur = len(x) / sr
    f0 = f0_track(x, sr)
    st = 12 * np.log2(f0 / np.median(f0)) if len(f0) else np.array([0.0])
    return {
        'file': path, 'duration_s': round(dur, 2), 'transcript': hyp.strip(), 'wer': round(e, 3),
        'mismatches': miss, 'words_per_sec': round(len(norm_words(text)) / max(dur, 1e-3), 2),
        'longest_pause_s': round(max(gaps) if gaps else 0.0, 2),
        'f0_median_hz': round(float(np.median(f0)) if len(f0) else 0.0, 1),
        'f0_range_semitones_p5_p95': round(float(np.percentile(st, 95) - np.percentile(st, 5)), 2),
        'f0_std_semitones': round(float(np.std(st)), 2),
        'peak_dbfs': round(20 * np.log10(np.max(np.abs(x)) + 1e-9), 2),
        'rms_dbfs': round(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9), 2),
        'clipped_samples': int(np.sum(np.abs(x) >= 0.999)),
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('wav')
    ap.add_argument('text')
    ap.add_argument('--json')
    a = ap.parse_args()
    r = qc_file(a.wav, a.text)
    print(json.dumps(r, indent=1, default=float))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1, default=float)
