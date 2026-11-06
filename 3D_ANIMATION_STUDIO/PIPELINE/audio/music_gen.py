#!/usr/bin/env python3
"""Original procedural score engine.

The music is composed here, note by note, and rendered with the studio's own
synthesisers (dsp.py).  Nothing is sampled, so the studio owns it outright and
it is safe to use in monetised videos.

    /opt/tools/tts312/bin/python PIPELINE/audio/music_gen.py video001 OUT.wav

A score is a list of timed events built by a cue function such as cue_video001().
"""
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import *  # noqa


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {n: i for i, n in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])}


def n2m(name):
    """'D4' -> midi."""
    if name[1] in '#b':
        p, o = name[:2], int(name[2:])
        if p[1] == 'b':
            p = list(NOTE)[(NOTE[p[0]] - 1) % 12]
    else:
        p, o = name[0], int(name[1:])
    return NOTE[p] + 12 * (o + 1)


# ------------------------------------------------------------------ instruments (mono out)
def inst_pad(freqs, dur, bright=1800, attack=1.2, release=1.5, detune=0.006, seed=0):
    n = int((dur + release) * SR)
    x = np.zeros(n)
    rng = np.random.default_rng(seed)
    for f in freqs:
        for d in (-detune, 0.0, detune):
            x += saw(f * (1 + d + rng.normal(0, 0.0005)), dur + release) * 0.18
    x = lowpass(x, bright, 2)
    tt = np.arange(n) / SR
    x *= 1 + 0.08 * np.sin(2 * np.pi * 0.25 * tt)
    return x * env_adsr(n, attack, 0.5, 0.85, release) / max(1, len(freqs)) * 2.0


def inst_strings(freqs, dur, attack=0.4, release=0.8, bright=2600):
    n = int((dur + release) * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * tt)
        x += saw(f * vib, dur + release) * 0.25 + saw(f * 1.003 * vib, dur + release) * 0.2
    x = bandpass(x, 180, bright, 2)
    return x * env_adsr(n, attack, 0.2, 0.9, release) / max(1, len(freqs)) * 2.0


def inst_pluck(f, dur=1.2, bright=0.5, seed=0):
    return karplus(f, dur, decay=0.995, bright=bright, seed=seed) * 0.9


def inst_bell(f, dur=1.5):
    return fm_bell(f, dur, ratio=3.01, index=2.2, decay=dur * 0.45) * 0.5 + fm_bell(f * 2, dur, ratio=1.5, index=0.5, decay=dur * 0.2) * 0.15


def inst_bass(f, dur, cutoff=700, drive=1.6):
    n = int((dur + 0.05) * SR)
    x = saw(f, dur + 0.05) * 0.6 + sine(f / 2, dur + 0.05) * 0.5
    x = lowpass(x, cutoff, 2)
    return soft_sat(x, drive) * env_adsr(n, 0.004, 0.08, 0.7, 0.05)


def inst_stab(freqs, dur=0.35):
    n = int((dur + 0.4) * SR)
    x = np.zeros(n)
    for f in freqs:
        x += saw(f, dur + 0.4) * 0.3 + square(f * 1.002, dur + 0.4, duty=0.4) * 0.15
    x = sweep_filter(x, 4500, 900)
    return x * env_adsr(n, 0.003, 0.12, 0.4, 0.35) / len(freqs) * 2.2


def drum_kick(level=1.0):
    m = int(0.45 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * np.cumsum(48 + 140 * np.exp(-tt / 0.035)) / SR) * env_exp(m, 0.16)
    x += highpass(noise(m, 'white', 1), 2000) * env_exp(m, 0.004) * 0.25
    return soft_sat(x, 1.5) * level


def drum_snare(level=1.0, seed=2):
    m = int(0.35 * SR)
    tt = np.arange(m) / SR
    x = bandpass(noise(m, 'white', seed), 900, 9000) * env_exp(m, 0.08) * 0.8
    x += np.sin(2 * np.pi * 190 * tt) * env_exp(m, 0.05) * 0.6
    return x * level


def drum_hat(level=0.5, open_=False, seed=3):
    m = int((0.3 if open_ else 0.08) * SR)
    x = highpass(noise(m, 'white', seed), 7000) * env_exp(m, 0.12 if open_ else 0.02)
    return x * level


def drum_taiko(level=1.0, f=70):
    m = int(1.2 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-tt / 0.03))) / SR) * env_exp(m, 0.35)
    x += lowpass(noise(m, 'pink', 5), 600) * env_exp(m, 0.05) * 0.5
    return soft_sat(x, 1.8) * level


def drum_tick(level=0.3):
    m = int(0.03 * SR)
    return highpass(noise(m, 'white', 7), 4000) * env_exp(m, 0.005) * level


# ------------------------------------------------------------------ score container
class Score:
    def __init__(self, dur, bpm=120):
        self.dur = dur
        self.bpm = bpm
        self.beat = 60.0 / bpm
        self.buses = {k: np.zeros((int((dur + 4) * SR), 2)) for k in ('pad', 'bass', 'lead', 'perc', 'fx')}

    def add(self, bus, t, x, gain_db=0.0, pan_=0.0):
        if t < 0 or t >= self.dur:
            return
        y = pan(np.asarray(x, float), pan_) * from_db(gain_db)
        i = int(t * SR)
        b = self.buses[bus]
        j = min(len(b), i + len(y))
        b[i:j] += y[:j - i]

    def gate(self, bus, t0, t1, floor_db=-40, fade=0.08):
        """Duck a bus to near silence between t0 and t1 (stop-time / drop)."""
        b = self.buses[bus]
        g = np.ones(len(b))
        i0, i1 = int(t0 * SR), int(t1 * SR)
        fl = from_db(floor_db)
        fn = int(fade * SR)
        g[i0:i1] = fl
        g[max(0, i0 - fn):i0] = np.linspace(1, fl, min(fn, i0))
        g[i1:i1 + fn] = np.linspace(fl, 1, len(g[i1:i1 + fn]))
        b *= g[:, None]

    def render(self):
        ir_big = reverb_ir(3.0, 1.1, damp=5000, seed=3)
        ir_small = reverb_ir(1.2, 0.35, damp=7000, seed=4)
        mix = (convolve_stereo(self.buses['pad'], ir_big, 0.35) +
               convolve_stereo(self.buses['lead'], ir_big, 0.3) +
               convolve_stereo(self.buses['perc'], ir_small, 0.12) +
               self.buses['bass'] + convolve_stereo(self.buses['fx'], ir_big, 0.25))
        mix = mix[:int(self.dur * SR)]
        mix = highpass(mix, 30, 2)
        mix = soft_sat(mix * 0.9, 1.1)
        return normalize(fade(mix, 0.01, 0.6), -3)


# ------------------------------------------------------------------ VIDEO_001 cue
def chord(names):
    return [mtof(n2m(n)) for n in names]


def cue_video001(dur=57.0):
    S = Score(dur, bpm=120)
    b = S.beat
    # --- A 0.0-10.9  mystery / discovery (D minor 9, plucked motif with echoes)
    S.add('pad', 0.0, inst_pad(chord(['D3', 'A3', 'C4', 'F4', 'E5']), 11.5, bright=1400, attack=2.0), -6)
    motif = ['D5', 'A4', 'F5', 'E5', 'C5', 'A4', 'E5', 'D5']
    for i, nm in enumerate(motif * 2):
        t = 0.6 + i * b * 1.25
        if t > 10.6:
            break
        p = inst_pluck(mtof(n2m(nm)), 1.4, bright=0.35, seed=i)
        S.add('lead', t, p, -9, pan_=-0.3 if i % 2 else 0.3)
        S.add('lead', t + 0.375, p * 0.4, -12, pan_=0.5 if i % 2 else -0.5)   # echo
    # --- B 10.9-19.5  tension build towards the heart
    S.add('pad', 10.9, inst_strings(chord(['D3', 'A#3', 'D4', 'F4']), 8.6, attack=1.5), -8)
    for k in range(int((19.5 - 10.9) / (b / 2))):
        t = 10.9 + k * b / 2
        cut = 300 + 1600 * (t - 10.9) / 8.6
        S.add('bass', t, inst_bass(mtof(n2m('D2')), b / 2 * 0.9, cutoff=cut), -10 + 4 * (t - 10.9) / 8.6)
        S.add('perc', t, drum_tick(0.25), -6, pan_=0.4 if k % 2 else -0.4)
    S.gate('bass', 16.30, 16.95)          # stop-time on the valve slam
    S.gate('perc', 16.30, 16.95)
    # --- C 19.5-24.8  launch to the lungs: driving
    for k in range(int((24.8 - 19.5) / (b / 4))):
        t = 19.5 + k * b / 4
        f = mtof(n2m(['D2', 'D2', 'F2', 'D2', 'G2', 'D2', 'F2', 'A2'][k % 8]))
        S.add('bass', t, inst_bass(f, b / 4 * 0.85, cutoff=1400), -9)
        if k % 4 == 0:
            S.add('perc', t, drum_kick(), -5)
        if k % 8 == 4:
            S.add('perc', t, drum_snare(), -9)
        S.add('perc', t, drum_hat(0.4, seed=k), -12, pan_=0.3)
    S.add('pad', 19.5, inst_strings(chord(['D3', 'F3', 'A3', 'D4']), 5.3, attack=0.2), -9)
    # --- D 24.8-33.4  wonder: F major lift, bell arpeggios
    S.add('pad', 24.8, inst_pad(chord(['F3', 'C4', 'E4', 'A4', 'G5']), 8.6, bright=3200, attack=0.8), -7)
    arp = ['F5', 'A5', 'C6', 'E6', 'G6', 'E6', 'C6', 'A5']
    for k in range(int((32.6 - 24.8) / (b / 2))):
        t = 24.8 + k * b / 2
        S.add('lead', t, inst_bell(mtof(n2m(arp[k % 8])), 1.2), -14, pan_=np.sin(k * 0.7) * 0.6)
        if k % 2 == 0:
            S.add('bass', t, inst_bass(mtof(n2m('F2' if t < 29 else 'A#1')), b * 0.9, cutoff=600), -13)
    S.gate('lead', 32.6, 40.0, floor_db=-60)
    # --- E 33.4-35.9  the drop: near silence + sub drone
    for bus in ('pad', 'bass', 'perc'):
        S.gate(bus, 33.3, 35.9, floor_db=-60, fade=0.25)
    S.add('fx', 33.5, sine(36.7, 2.6) * env_adsr(int(2.6 * SR), 1.0, 0.2, 0.8, 0.8) * 0.8, -12)
    # --- F 35.9-44.7  danger: semitone ostinato, taiko, dissonant strings
    S.add('pad', 35.9, inst_strings(chord(['D3', 'D#3', 'A3', 'D4', 'D#4']), 8.8, attack=2.0, bright=1800), -6)
    for k in range(int((44.6 - 35.9) / (b / 2))):
        t = 35.9 + k * b / 2
        nm = 'D2' if (k // 2) % 2 == 0 else 'D#2'
        lvl = -12 + 6 * (t - 35.9) / 8.8
        S.add('bass', t, inst_bass(mtof(n2m(nm)), b / 2 * 0.8, cutoff=500 + 900 * (t - 35.9) / 8.8), lvl)
        if k % 4 == 0:
            S.add('perc', t, drum_taiko(1.0, 65 if k % 8 == 0 else 80), -6 + 3 * (t - 35.9) / 8.8)
    # riser into the kick (43.4)
    rise = np.zeros(int(2.4 * SR))
    tt = np.arange(len(rise)) / SR
    rise = sweep_filter(noise(len(rise), 'white', 9), 300, 8000, kind='bandpass', q=2) * (tt / 2.4) ** 2
    S.add('fx', 41.0, rise, -10)
    S.gate('bass', 43.40, 44.70, floor_db=-30)
    # --- G 44.7-50.4  climax: i-VI-III-VII, full kit, stabs; launch downbeat at 47.8
    prog = [(44.7, ['D3', 'F3', 'A3', 'D4']), (46.2, ['A#2', 'D3', 'F3', 'A#3']), (47.8, ['F3', 'A3', 'C4', 'F4']),
            (49.1, ['C3', 'E3', 'G3', 'C4'])]
    for (t, ch), (t2, _) in zip(prog, prog[1:] + [(50.4, None)]):
        S.add('pad', t, inst_strings(chord(ch), t2 - t, attack=0.05, release=0.5, bright=4500), -6)
        S.add('lead', t, inst_stab(chord([c[:-1] + str(int(c[-1]) + 1) for c in ch])), -8)
    for k in range(int((50.4 - 44.7) / (b / 4))):
        t = 44.7 + k * b / 4
        root = 'D2' if t < 46.2 else ('A#1' if t < 47.8 else ('F2' if t < 49.1 else 'C2'))
        S.add('bass', t, inst_bass(mtof(n2m(root)), b / 4 * 0.85, cutoff=1800), -8)
        if k % 4 == 0:
            S.add('perc', t, drum_kick(1.0), -4)
        if k % 8 == 4:
            S.add('perc', t, drum_snare(1.0, seed=k), -7)
        S.add('perc', t, drum_hat(0.5, open_=(k % 8 == 6), seed=k), -11, pan_=0.35)
    S.add('perc', 47.8, drum_taiko(1.2, 55), -2)
    # --- H 50.4-57  resolution: playful F major pizzicato + bells, final button
    S.add('pad', 50.4, inst_pad(chord(['F3', 'A3', 'C4', 'E4']), 5.6, bright=2600, attack=0.3), -10)
    tune = [('F5', 0.0), ('A5', 0.5), ('C6', 1.0), ('A5', 1.5), ('G5', 2.25), ('F5', 2.75), ('E5', 3.5), ('G5', 4.0),
            ('F5', 4.75)]
    for nm, dt in tune:
        S.add('lead', 50.6 + dt, inst_pluck(mtof(n2m(nm)), 0.9, bright=0.6, seed=int(dt * 10)), -8)
    for k in range(10):
        S.add('bass', 50.4 + k * b, inst_bass(mtof(n2m('F2' if k % 2 == 0 else 'C2')), b * 0.5, cutoff=500), -14)
    S.add('lead', 55.95, inst_bell(mtof(n2m('F5')), 1.0) + inst_bell(mtof(n2m('C6')), 1.0), -10)
    S.add('perc', 55.95, drum_kick(0.7), -10)
    return S


CUES = {'video001': cue_video001}

if __name__ == '__main__':
    cue, out = sys.argv[1], sys.argv[2]
    S = CUES[cue]()
    y = S.render()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sf.write(out, y.astype(np.float32), SR, subtype='PCM_24')
    print('MUSIC_OK', out, round(len(y) / SR, 2), 's')
