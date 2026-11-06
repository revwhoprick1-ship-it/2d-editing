#!/usr/bin/env python3
"""Professional-ish mix bus for a video.

    /opt/tools/tts312/bin/python PIPELINE/audio/mix.py VIDEOS/VIDEO_00X/audio/cues.json

cues.json:
{
 "duration": 57.0, "narration": "narration/narration_raw.wav", "narration_offset": 0.2,
 "music": "music_score.wav", "music_gain_db": -6,
 "targets": {"narration_lufs": -16, "master_lufs": -14, "true_peak": -1.0, "duck_db": 9},
 "cues": [ {"t": 0.0, "file": "AUDIO/sound_effects/bio/bloodstream_bed.wav", "gain": -14, "bus": "amb",
            "pan": 0, "dur": 14.6, "fade_in": 0.5, "fade_out": 1.0, "note": "..."}, ... ]
}
Paths in cues are relative to the studio root; narration/music relative to the cue file.
Writes mix_master.wav (48 kHz stereo 24-bit) + stems/ and prints loudness stats.
"""
import json
import os
import sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import *  # noqa

STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def load(path, sr=SR):
    x, s = sf.read(path, dtype='float64', always_2d=True)
    if s != sr:
        g = np.gcd(s, sr)
        x = signal.resample_poly(x, sr // g, s // g, axis=0)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, 1)
    return x


def place(buf, x, t, gain_db=0.0, pan_=None, dur=None, fin=0.0, fout=0.0):
    if dur is not None:
        x = x[:int(dur * SR)]
    if pan_:
        m = x.mean(1)
        x = pan(m, pan_) * np.sqrt(2)
    x = fade(x, fin or 0.002, fout or 0.01)
    i = int(t * SR)
    j = min(len(buf), i + len(x))
    if j > i:
        buf[i:j] += x[:j - i] * from_db(gain_db)


def voice_chain(v):
    m = v.mean(1)
    m = highpass(m, 80, 2)
    m = peaking_eq(m, 280, -2.0, 1.0)
    m = peaking_eq(m, 3200, 2.5, 0.9)
    m = peaking_eq(m, 10000, 1.5, 0.7)
    m = deesser(m, 6500, thresh_db=-32, max_red_db=5)
    m = compressor(m, thresh_db=-22, ratio=3.0, attack=0.006, release=0.12, knee=6)
    m = soft_sat(m * 1.0, 1.15)
    return np.stack([m, m], 1)


def lufs(x, meter):
    try:
        return meter.integrated_loudness(x)
    except Exception:
        return -70.0


def main():
    cue_path = sys.argv[1]
    base = os.path.dirname(os.path.abspath(cue_path))
    C = json.load(open(cue_path))
    T = C.get('targets', {})
    n = int(C['duration'] * SR)
    meter = pyln.Meter(SR)
    buses = {k: np.zeros((n, 2)) for k in ('narration', 'music', 'sfx', 'amb')}
    # narration
    v = voice_chain(load(os.path.join(base, C['narration'])))
    place(buses['narration'], v, C.get('narration_offset', 0.0))
    nl = lufs(buses['narration'], meter)
    buses['narration'] *= from_db(T.get('narration_lufs', -16) - nl)
    # music with sidechain ducking under narration
    if C.get('music'):
        mu = load(os.path.join(base, C['music']))
        place(buses['music'], mu, C.get('music_offset', 0.0), C.get('music_gain_db', -6))
    env = envelope_follower(buses['narration'], SR, attack=0.05, release=0.35)
    speech = np.clip((db(env) + 45) / 15, 0, 1)        # 0 = silence, 1 = speech present
    duck = from_db(-T.get('duck_db', 9) * speech)
    buses['music'] *= duck[:, None]
    for c in C['cues']:
        p = c['file'] if os.path.isabs(c['file']) else os.path.join(STUDIO, c['file'])
        x = load(p)
        if c.get('loop') and c.get('dur') and len(x) < c['dur'] * SR:
            reps = int(np.ceil(c['dur'] * SR / len(x)))
            x = np.concatenate([x] * reps)
        place(buses[c.get('bus', 'sfx')], x, c['t'], c.get('gain', 0.0), c.get('pan'), c.get('dur'),
              c.get('fade_in', 0.0), c.get('fade_out', 0.0))
    # gentle ducking of SFX/ambience under speech too (keeps words clear)
    buses['amb'] *= from_db(-4 * speech)[:, None]
    buses['sfx'] *= from_db(-2 * speech)[:, None]
    master = sum(buses.values())
    master = highpass(master, 25, 2)
    # loudness normalise then true-peak limit (iterate twice)
    for _ in range(2):
        ml = lufs(master, meter)
        master *= from_db(T.get('master_lufs', -14) - ml)
        master = true_peak_limiter(master, T.get('true_peak', -1.0) - 0.2)
    out_dir = base
    os.makedirs(os.path.join(out_dir, 'stems'), exist_ok=True)
    sf.write(os.path.join(out_dir, 'mix_master.wav'), master.astype(np.float32), SR, subtype='PCM_24')
    scale = from_db(T.get('master_lufs', -14) - lufs(sum(buses.values()), meter))
    for k, b in buses.items():
        sf.write(os.path.join(out_dir, 'stems', f'{k}.wav'), (b * scale).astype(np.float32), SR, subtype='PCM_24')
    over = signal.resample_poly(master, 4, 1, axis=0)
    tp = db(np.max(np.abs(over)))
    stats = {'master_integrated_lufs': round(lufs(master, meter), 2), 'true_peak_dbtp_approx': round(float(tp), 2),
             'narration_lufs_pre_master': round(T.get('narration_lufs', -16), 1),
             'music_lufs_in_mix': round(lufs(buses['music'] * scale, meter), 2) if np.any(buses['music']) else None,
             'sfx_lufs_in_mix': round(lufs(buses['sfx'] * scale, meter), 2),
             'amb_lufs_in_mix': round(lufs(buses['amb'] * scale, meter), 2),
             'clipped_samples': int(np.sum(np.abs(master) >= 1.0))}
    json.dump(stats, open(os.path.join(out_dir, 'mix_stats.json'), 'w'), indent=1)
    print('MIX_OK', json.dumps(stats))


if __name__ == '__main__':
    main()
