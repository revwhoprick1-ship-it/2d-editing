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
        self.buses = {k: np.zeros((int((dur + 4) * SR), 2)) for k in ('pad', 'bass', 'lead', 'perc', 'fx', 'room')}

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

    def render(self, loop=None):
        """loop=L: seamless loop of length L s. Everything past L (reverb tails and
        events scheduled after L) is folded back onto the start, so the end of the
        file runs continuously into its own beginning."""
        ir_big = reverb_ir(3.0, 1.1, damp=5000, seed=3)
        ir_small = reverb_ir(1.2, 0.35, damp=7000, seed=4)
        mix = (convolve_stereo(self.buses['pad'], ir_big, 0.35) +
               convolve_stereo(self.buses['lead'], ir_big, 0.3) +
               convolve_stereo(self.buses['perc'], ir_small, 0.12) +
               convolve_stereo(self.buses['room'], ir_small, 0.22) +
               self.buses['bass'] + convolve_stereo(self.buses['fx'], ir_big, 0.25))
        mix = highpass(mix, 30, 2)
        mix = soft_sat(mix * 0.9, 1.1)
        if loop:
            n = int(round(loop * SR))
            out = mix[:n].copy()
            tail = mix[n:]
            for k in range(0, len(tail), n):
                seg = tail[k:k + n]
                out[:len(seg)] += seg
            return normalize(out, -3)
        mix = mix[:int(self.dur * SR)]
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


# ------------------------------------------------------------------ VIDEO_002 cue (comedy, seamless loop)
def tape_warp(x, rate, align_i):
    """Variable-speed playback of x (n,2) - the tape-start / tape-stop effect.
    rate: per-output-sample speed (0..1). align_i: output sample that reads the
    same input sample as normal playback (keeps the beat grid in place)."""
    ph = np.cumsum(rate)
    ph += align_i - ph[align_i]
    ph = np.clip(ph, 0, len(x) - 1)
    y = np.stack([np.interp(ph, np.arange(len(x)), x[:, c]) for c in range(2)], 1)
    amp = np.clip(rate, 0, 1) ** 0.6
    return y * amp[:, None]


def inst_epiano(f, dur):
    x = fm_bell(f, dur + 0.6, ratio=1.0, index=1.3, decay=dur * 0.9 + 0.2) * 0.6
    x += fm_bell(f, dur + 0.6, ratio=14.0, index=0.25, decay=0.05) * 0.1
    return x * env_adsr(len(x), 0.003, 0.3, 0.7, 0.5)


def inst_vibes(f, dur):
    n = int((dur + 1.0) * SR)
    tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt / 0.15)) * np.exp(-tt / 0.9)
    return x * (1 + 0.25 * np.sin(2 * np.pi * 5.5 * tt)) * 0.5


def inst_marimba(f, dur=0.5):
    n = int((dur + 0.3) * SR)
    tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.22) + 0.35 * np.sin(2 * np.pi * f * 3.9 * tt) * np.exp(-tt / 0.04)
    return x * env_adsr(n, 0.002, 0.05, 1.0, 0.05) * 0.7


def inst_organ(freqs, dur):
    n = int((dur + 0.15) * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for h, a in ((0.5, 0.5), (1, 1.0), (2, 0.6), (3, 0.35), (4, 0.3), (6, 0.12), (8, 0.1)):
            x += np.sin(2 * np.pi * f * h * tt + h) * a
    x *= 1 + 0.12 * np.sin(2 * np.pi * 6.2 * tt)            # leslie-ish tremolo
    return x * env_adsr(n, 0.02, 0.05, 0.95, 0.12) / (len(freqs) * 3.2)


def inst_bassoon(f, dur):
    n = int((dur + 0.06) * SR)
    tt = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5 * tt)
    x = square(f * vib, n / SR, duty=0.32) * 0.6 + saw(f * vib, n / SR) * 0.3
    x = bandpass(x, 180, 1400, 2)
    return soft_sat(x * 1.4, 1.3) * env_adsr(n, 0.012, 0.06, 0.75, 0.05) * 0.8


def inst_tuba(f, dur):
    n = int((dur + 0.05) * SR)
    x = saw(f, n / SR) * 0.6 + sine(f, n / SR) * 0.6
    x = lowpass(x, 520, 2)
    return soft_sat(x * 1.5, 1.4) * env_adsr(n, 0.015, 0.08, 0.6, 0.05)


def inst_pizz(f, dur=0.35, seed=0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = (saw(f, dur) * 0.5 + sine(f, dur) * 0.7)
    x = sweep_filter(x, 3500, 500) * np.exp(-tt / 0.09)
    return x * env_adsr(n, 0.002, 0.05, 1.0, 0.03) * 0.8


def inst_tremolo(freqs, dur, rate=11.0, bright=2400):
    x = inst_strings(freqs, dur, attack=0.25, release=0.4, bright=bright)
    tt = np.arange(len(x)) / SR
    return x * (0.55 + 0.45 * np.sin(2 * np.pi * rate * tt) ** 2)


def drum_rim(level=0.5):
    m = int(0.06 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * 1700 * tt) * env_exp(m, 0.012) + bandpass(noise(m, 'white', 9), 1500, 6000) * env_exp(m, 0.006) * 0.6
    return x * level


def drum_shaker(level=0.3, seed=0):
    m = int(0.09 * SR)
    x = bandpass(noise(m, 'white', seed), 5000, 11000) * env_adsr(m, 0.02, 0.03, 0.4, 0.03)
    return x * level


def C(names):
    return chord(names)


def M(name):
    return mtof(n2m(name))


LOOP = 36.1


def muzak_block(tau0=-4.8, tau1=0.62, t_start=33.545 - LOOP, stop_at=0.12, stop_len=0.42):
    """Elevator bossa (F major, 100 bpm) on loop time tau (tau = 0 is the
    worldwide fart = video frame 0).  Tape-starts after the VHS rewind and
    tape-stops right after the fart.  Returned buffer starts at tau0."""
    beat = 0.6
    n = int((tau1 - tau0 + 1.5) * SR)
    buf = np.zeros((n, 2))

    def put(tau, x, g=0.0, p=0.0):
        i = int((tau - tau0) * SR)
        if i < 0 or i >= n:
            return
        y = pan(np.asarray(x, float), p) * from_db(g)
        j = min(n, i + len(y))
        buf[i:j] += y[:j - i]
    bars = [(-7.2, ['F3', 'A3', 'C4', 'E4'], 'F2', 'C3'), (-4.8, ['F3', 'A3', 'C4', 'E4'], 'F2', 'C3'),
            (-2.4, ['G3', 'Bb3', 'D4', 'F4'], 'G2', 'D3'), (-1.2, ['G3', 'Bb3', 'E4', 'C4'], 'C3', 'G2'),
            (0.0, ['F3', 'A3', 'C4', 'E4'], 'F2', 'C3')]
    for b0, ch, root, fifth in bars:
        span = 2.4 if b0 in (-7.2, -4.8, 0.0) else 1.2
        for off, nm, d in ((0.0, root, 0.85), (0.9, fifth, 0.28), (1.2, fifth, 0.85), (2.1, root, 0.28)):
            if off < span:
                put(b0 + off, inst_bass(M(nm), d, cutoff=420, drive=1.1), -9)
        for off in (0.0, 0.9, 1.5):
            if off < span:
                for f in C(ch):
                    put(b0 + off, inst_epiano(f, 0.35), -15, -0.2)
    mel = [(-4.8, 'C5', 0.85), (-3.9, 'A4', 0.28), (-3.6, 'C5', 0.55), (-3.0, 'E5', 0.55), (-2.4, 'D5', 0.85),
           (-1.5, 'Bb4', 0.28), (-1.2, 'C5', 0.55), (-0.6, 'G4', 0.55), (0.0, 'A4', 1.2)]
    for tau, nm, d in mel:
        put(tau, inst_vibes(M(nm), d), -10, 0.25)
    k = 0
    tau = -7.2
    while tau < tau1:
        put(tau, drum_shaker(0.35 if k % 2 == 0 else 0.22, seed=k), -14, 0.4)
        k += 1
        tau += beat / 2
    for bar0 in (-7.2, -4.8, -2.4, 0.0):
        for off in (0.0, 0.9, 1.8, 3.0, 3.6):           # 3-2 clave on the rim
            put(bar0 + off, drum_rim(0.4), -15, -0.35)
    # tape start (after the rewind) and tape stop (after the fart)
    rate = np.ones(n)
    tt = tau0 + np.arange(n) / SR
    s0, s1 = t_start, t_start + 0.22
    rate[tt < s0] = 0.0
    m = (tt >= s0) & (tt < s1)
    rate[m] = ((tt[m] - s0) / (s1 - s0)) ** 1.5
    e0, e1 = stop_at, stop_at + stop_len
    m = (tt >= e0) & (tt < e1)
    rate[m] = (1 - (tt[m] - e0) / (e1 - e0)) ** 1.3
    rate[tt >= e1] = 0.0
    align = int((0.0 - tau0) * SR)
    return tape_warp(buf, rate, align)


def cue_video002(dur=LOOP):
    S = Score(dur + 2.0, bpm=150)
    # ---- A. muzak across the loop seam (tau -> t = tau + LOOP, folded by render(loop))
    mz = muzak_block()
    S.buses['room'][int((LOOP - 4.8) * SR):int((LOOP - 4.8) * SR) + len(mz)] += mz * from_db(-2)
    # ---- B. CHAOS theme 0.62-6.05: comedy oom-pah in Bb, bassoon tune, 150 bpm
    b = 0.4
    t0 = 0.62
    prog = [('Bb1', 'F2', ['D4', 'F4', 'Bb4']), ('Eb2', 'Bb1', ['Eb4', 'G4', 'Bb4']), ('F1', 'C2', ['Eb4', 'F4', 'A4']),
            ('Bb1', 'F2', ['D4', 'F4', 'Bb4'])]
    for bar in range(4):
        root, fifth, ch = prog[bar]
        for k in range(4):
            t = t0 + (bar * 4 + k) * b
            if t >= 6.0:
                break
            S.add('bass', t, inst_tuba(M(root if k % 2 == 0 else fifth), b * 0.6), -6)
            if k % 2 == 1:
                S.add('lead', t, inst_stab(C(ch), 0.12), -16, 0.2)
                S.add('perc', t, drum_snare(0.5, seed=bar * 4 + k), -15)
            else:
                S.add('perc', t, drum_kick(0.8), -10)
            S.add('perc', t + b / 2, drum_hat(0.35, seed=k), -17, 0.3)
    tune = [('F3', 0, .4), ('D3', .4, .2), ('F3', .6, .2), ('Bb3', .8, .4), ('A3', 1.2, .2), ('Bb3', 1.4, .2),
            ('C4', 1.6, .4), ('Bb3', 2.0, .2), ('G3', 2.2, .2), ('Eb3', 2.4, .4),
            ('A3', 3.2, .2), ('Bb3', 3.4, .2), ('B3', 3.6, .2), ('C4', 3.8, .2), ('Eb4', 4.0, .3), ('C4', 4.4, .3),
            ('D4', 4.8, .2), ('C4', 5.0, .2)]
    for nm, dt, d in tune:
        S.add('lead', t0 + dt, inst_bassoon(M(nm), d * 0.85), -7, -0.15)
        S.add('lead', t0 + dt, inst_pizz(M(nm) * 2, 0.25), -15, 0.3)
    # a cymbal-ish lift when the planet appears (2.9)
    S.add('perc', 2.9, drum_hat(0.9, open_=True, seed=40), -9)
    S.add('perc', 2.9, drum_kick(1.0), -8)
    # ---- C. wedding organ 6.05-6.77 ("Here comes the bride", Wagner 1850, public domain) -> tape stop on the fart
    org_t0, org_stop = 6.05, 6.77
    n_org = int(1.3 * SR)
    org = np.zeros((n_org, 2))
    def oput(t, x, g=0.0):
        i = int((t - org_t0) * SR)
        y = pan(np.asarray(x, float), 0) * from_db(g)
        j = min(n_org, i + len(y))
        org[i:j] += y[:j - i]
    oput(6.05, inst_organ(C(['F3', 'A3', 'C4']), 1.0), -6)
    for nm, t, d in (('C5', 6.05, 0.22), ('F5', 6.29, 0.16), ('F5', 6.46, 0.06), ('F5', 6.53, 0.6)):
        oput(t, inst_organ([M(nm)], d), -3)
    rate = np.ones(n_org)
    tt = org_t0 + np.arange(n_org) / SR
    m = (tt >= org_stop) & (tt < org_stop + 0.3)
    rate[m] = 1 - (tt[m] - org_stop) / 0.3
    rate[tt >= org_stop + 0.3] = 0
    S.buses['room'][int(org_t0 * SR):int(org_t0 * SR) + n_org] += tape_warp(org, rate, 0)
    # ---- D. science 7.52-12.66: curious marimba in C, 110 bpm
    b = 60 / 110
    t0 = 7.52
    sci = [(['C4', 'E4', 'G4', 'C5'], 'C2'), (['A3', 'C4', 'E4', 'A4'], 'A1'), (['F3', 'A3', 'C4', 'F4'], 'F1')]
    for i, (ch, root) in enumerate(sci):
        tb = t0 + i * 4 * b
        S.add('pad', tb, inst_pad(C(ch), 4 * b, bright=1500, attack=0.4, release=0.6), -16)
        S.add('bass', tb, inst_pizz(M(root) * 2, 0.4), -8)
        S.add('bass', tb + 2 * b, inst_pizz(M(root) * 3, 0.4), -10)
        pat = [0, 1, 2, 3, 2, 1, 2, 3]
        fs = C(ch)
        for k in range(8):
            t = tb + k * b / 2
            if t < 12.6:
                S.add('lead', t, inst_marimba(fs[pat[k]] * 2), -11 if k % 2 == 0 else -14, 0.3 if k % 2 else -0.3)
    for bus in ('pad', 'bass', 'lead', 'perc', 'fx'):
        S.gate(bus, 12.66, 14.70, floor_db=-80, fade=0.12)     # the "Tiny." silence
    # ---- E. news bed 15.15-16.68 (D minor pulse), dun-dun-dun is an SFX on top
    b = 0.5
    for k in range(int((16.68 - 15.15) / (b / 4))):
        t = 15.15 + k * b / 4
        S.add('bass', t, inst_bass(M('D2'), b / 4 * 0.7, cutoff=900), -12 if k % 4 else -9)
        if k % 8 == 0:
            S.add('perc', t, drum_taiko(0.8, 60), -10)
    S.add('pad', 15.15, inst_strings(C(['D3', 'F3', 'A3', 'D4']), 1.55, attack=0.3, bright=2200), -13)
    # ---- F. investigation 17.96-22.45: ticking suspense, rises a semitone per ENHANCE
    t_enh = [19.015, 19.64, 20.265]
    keys = [(17.96, ['A2', 'C3', 'E3', 'A3']), (t_enh[0], ['Bb2', 'Db3', 'F3', 'Bb3']),
            (t_enh[1], ['B2', 'D3', 'F#3', 'B3']), (t_enh[2], ['C3', 'Eb3', 'G3', 'C4']), (20.765, ['C3', 'E3', 'G3', 'C4'])]
    for (t, ch), (t2, _) in zip(keys, keys[1:] + [(22.45, None)]):
        S.add('pad', t, inst_tremolo(C(ch), t2 - t, bright=2000), -12)
        S.add('bass', t, inst_bass(mtof(n2m(ch[0]) - 12), 0.18, cutoff=600), -6)
    for i, t in enumerate(t_enh):
        S.add('perc', t + 0.1, drum_taiko(1.0, 50 + 6 * i), -6)
    b = 0.5
    for k in range(int((22.42 - 17.96) / (b / 2))):
        t = 17.96 + k * b / 2
        S.add('perc', t, drum_tick(0.3), -10, 0.4 if k % 2 else -0.4)
        if t > 20.95:
            S.add('bass', t, inst_bass(M('C2'), b / 2 * 0.6, cutoff=500 + 1200 * (t - 20.95) / 1.5), -12 + 5 * (t - 20.95) / 1.5)
    S.add('lead', 20.765, inst_stab(C(['C5', 'E5', 'G5'])), -9)
    S.gate('pad', 22.44, 22.98, floor_db=-80, fade=0.02)       # freeze frame = stop-time
    S.gate('bass', 22.44, 22.98, floor_db=-80, fade=0.02)
    S.gate('perc', 22.44, 22.98, floor_db=-80, fade=0.02)
    S.gate('lead', 22.44, 22.98, floor_db=-80, fade=0.02)
    # ---- G. blame chain: sneaky pizzicato, up a whole tone per accusation, stab on each point
    b = 60 / 132
    sections = [(22.975, 24.335, 'E', 23.21), (24.335, 26.167, 'F#', 24.57), (26.167, 27.783, 'G#', 26.40)]
    for s0, s1, key_, t_point in sections:
        r = n2m(key_ + '2')
        figure = [0, None, 7, None, 0, 3, 7, None]
        k = 0
        while s0 + k * b / 2 < s1 - 0.05:
            t = s0 + k * b / 2
            st = figure[k % 8]
            if st is not None:
                S.add('bass', t, inst_pizz(mtof(r + st), 0.3), -6)
            if k % 4 == 2:
                S.add('perc', t, drum_rim(0.6), -12)
            k += 1
        S.add('lead', t_point, inst_stab([mtof(r + 24), mtof(r + 27), mtof(r + 31)], 0.2), -6)
        S.add('perc', t_point, drum_kick(1.0), -6)
    # deadpan kid (27.78-28.9): one held high tremolo note only
    S.add('pad', 27.80, inst_tremolo([M('B5')], 1.05, rate=13, bright=5000), -20)
    S.add('lead', 28.91, inst_stab(C(['A#4', 'C#5', 'E5', 'G5']), 0.3), -4)     # the kid's point lands: diminished hit
    S.add('perc', 28.91, drum_taiko(1.2, 48), -4)
    # ---- H. "Farts aren't contagious..." near silence: low suspicious drone, swell on "But this one?"
    S.add('pad', 29.85, inst_pad(C(['D2', 'A2']), 1.7, bright=500, attack=0.6, release=0.4), -16)
    S.add('pad', 31.56, inst_tremolo(C(['D3', 'D#3', 'A3', 'D4', 'G#4']), 1.05, rate=14, bright=3000), -9)
    S.add('perc', 31.56, drum_taiko(1.3, 44), -3)
    S.gate('pad', 32.64, 33.6, floor_db=-80, fade=0.03)        # cut by the VHS rewind
    return S


CUES = {'video001': cue_video001, 'video002': cue_video002}
LOOPS = {'video002': LOOP}


# ------------------------------------------------------------------ VIDEO_003 cue (120 bpm, 66 beats = one loop)
LOOP3 = 33.0


def cue_video003(dur=LOOP3):
    S = Score(dur + 2.0, bpm=120)
    b = 0.5
    prog = [('A1', ['A3', 'C4', 'E4']), ('F1', ['F3', 'A3', 'C4']), ('C2', ['G3', 'C4', 'E4']), ('G1', ['G3', 'B3', 'D4'])]
    sections = [  # (t0, t1, mode)
        (0.0, 2.2, 'drop'), (2.2, 5.75, 'light'), (5.75, 8.1, 'sad'), (8.1, 11.05, 'groove'),
        (11.05, 14.65, 'lofi'), (14.65, 15.8, 'silent'), (15.8, 21.5, 'up'), (21.5, 25.2, 'warn'),
        (25.2, 27.6, 'tension'), (27.6, LOOP3, 'build')]

    def mode_at(t):
        tt = t % LOOP3
        for a, c, m in sections:
            if a <= tt < c:
                return m
        return 'drop'
    for k in range(int(LOOP3 / (b / 2))):          # 16th-note grid over the whole loop
        t = k * b / 2
        beat, sub = divmod(k, 2)
        bar = beat // 4
        root, ch = prog[bar % 4]
        md = mode_at(t)
        if md == 'silent':
            continue
        if md in ('drop', 'groove', 'up', 'build'):
            if sub == 0 and beat % 4 in (0, 2) or (sub == 1 and beat % 4 == 2):
                S.add('perc', t, drum_kick(1.0), -6 if md != 'build' else -7)
            if sub == 0 and beat % 4 in (1, 3):
                S.add('perc', t, drum_snare(1.0, seed=k), -8)
            S.add('perc', t, drum_hat(0.45, open_=(sub == 1 and beat % 2 == 1), seed=k), -14, 0.3)
            if sub == 0 or beat % 2 == 1:
                S.add('bass', t, inst_bass(mtof(n2m(root)), b / 2 * 0.8, cutoff=900 if md != 'drop' else 1500), -8)
            if sub == 1 and beat % 2 == 0:
                S.add('lead', t, inst_stab([mtof(n2m(n)) for n in ch], 0.12), -15 if md != 'drop' else -11, -0.2)
            if md == 'up' and sub == 0:
                S.add('lead', t, inst_bell(mtof(n2m(ch[beat % 3])) * 2, 0.8), -17, 0.4)
        elif md == 'light' or md == 'lofi':
            if sub == 0 and beat % 4 == 0:
                S.add('perc', t, drum_kick(0.7), -10)
            if sub == 0 and beat % 4 == 2:
                S.add('perc', t, drum_snare(0.6, seed=k), -14 if md == 'lofi' else -12)
            if sub == 1:
                S.add('perc', t, drum_hat(0.25, seed=k), -20)
            if sub == 0 and beat % 2 == 0:
                S.add('lead', t, inst_pluck(mtof(n2m(ch[(beat // 2) % 3])) * 2, 0.8, bright=0.3 if md == 'lofi' else 0.6, seed=k), -12)
            if sub == 0 and beat % 4 == 0:
                S.add('bass', t, inst_bass(mtof(n2m(root)), b * 1.8, cutoff=500), -11)
        elif md == 'sad':
            if sub == 0 and beat % 2 == 0:
                S.add('lead', t, inst_pluck(mtof(n2m(['E4', 'D4', 'C4', 'B3'][(beat // 2) % 4])), 1.0, bright=0.25, seed=k), -10)
            if sub == 0 and beat % 4 == 0:
                S.add('pad', t, inst_pad([mtof(n2m(n)) for n in ('A2', 'C3', 'E3')], 2.0, bright=900, attack=0.3), -14)
        elif md == 'warn':
            if sub == 0 and beat % 4 == 0:
                S.add('pad', t, inst_strings([mtof(n2m(n)) for n in ('A2', 'A#2', 'E3')], 2.0, attack=0.5, bright=1600), -13)
                S.add('perc', t, drum_taiko(0.8, 55), -12)
        elif md == 'tension':
            if sub == 0:
                S.add('bass', t, inst_bass(mtof(n2m('A1')), b * 0.4, cutoff=400 + 300 * (t - 25.2)), -12)
            if sub == 1:
                S.add('perc', t, drum_tick(0.3), -12, 0.4 if beat % 2 else -0.4)
        if md == 'build' and sub == 1:
            S.add('perc', t, drum_hat(0.3 + 0.4 * (t - 27.6) / 5.4, seed=k + 7), -16, -0.3)
    # snare roll + riser into the loop point (the drop on video frame 0)
    for k in range(16):
        S.add('perc', LOOP3 - 1.0 + k / 16, drum_snare(0.4 + 0.6 * k / 16, seed=200 + k), -14 + 6 * k / 16)
    n = int(2.0 * SR)
    tt = np.arange(n) / SR
    rise = sweep_filter(noise(n, 'white', 33), 400, 9000, kind='bandpass', q=2) * (tt / 2.0) ** 2
    S.add('fx', LOOP3 - 2.0, rise, -14)
    S.add('perc', LOOP3, drum_taiko(1.2, 50), -6)            # lands on frame 0 (wraps)
    S.add('lead', LOOP3, inst_stab([mtof(n2m(x)) for x in ('A4', 'C5', 'E5')], 0.3), -8)
    return S


CUES['video003'] = cue_video003
LOOPS['video003'] = LOOP3


# ------------------------------------------------------------------ VIDEO_004 cue (gravity, 33.6 s loop)
LOOP4 = 33.6


def cue_video004(dur=LOOP4):
    import json as _j
    T = _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_004', 'audio', 'narration', 'timing.json')))
    LS = {l['id']: (l['start'], l['end']) for l in T['lines']}
    TG = LS['L10'][0] + 0.75
    TL = TG + 2.6
    S = Score(dur + 2.0, bpm=124)
    b = 60 / 124
    C = lambda names: [mtof(n2m(x)) for x in names]
    # curiosity motif (also the loop bed): plucked bells, D major-ish, runs 30.55 -> 33.6 -> wraps to 0 -> 2.9
    mot = ['D5', 'A4', 'F#5', 'E5', 'A5', 'F#5', 'E5', 'D5']
    for start in (30.55, LOOP4):
        for i, nm in enumerate(mot):
            t = start + i * b / 2 if start == 30.55 else start + i * b / 2
            if (start == 30.55 and t < LOOP4) or (start == LOOP4 and t < LOOP4 + 2.85):
                S.add('lead', t, inst_bell(mtof(n2m(nm)), 0.9), -14, 0.3 if i % 2 else -0.3)
    S.add('pad', 30.55, inst_pad(C(['D3', 'A3', 'F#4']), 3.05 + 2.9, bright=1600, attack=0.6), -15)
    # excitement 2.86 -> 10: bouncy groove
    for k in range(int((10.0 - 2.86) / (b / 2))):
        t = 2.86 + k * b / 2
        beat, sub = divmod(k, 2)
        root = ['D2', 'B1', 'G1', 'A1'][(beat // 4) % 4]
        if sub == 0 and beat % 2 == 0:
            S.add('perc', t, drum_kick(0.9), -8)
        if sub == 0 and beat % 2 == 1:
            S.add('perc', t, drum_snare(0.8, seed=k), -11)
        S.add('perc', t, drum_hat(0.35, seed=k), -17, 0.3)
        if sub == 0:
            S.add('bass', t, inst_bass(mtof(n2m(root)), b * 0.45, cutoff=1100), -9)
        if sub == 1 and beat % 2 == 0:
            S.add('lead', t, inst_pluck(mtof(n2m(['F#5', 'A5', 'D6', 'E5'][(beat // 2) % 4])), 0.6, bright=0.6, seed=k), -13)
    # floaty explainer 10 -> 15.9: pads + slow bells
    S.add('pad', 10.0, inst_pad(C(['D3', 'A3', 'E4', 'F#4']), 6.0, bright=2200, attack=0.8), -12)
    for i in range(12):
        S.add('lead', 10.0 + i * b, inst_bell(mtof(n2m(['A5', 'F#5', 'E5', 'D5'][i % 4])), 1.2), -17, 0.4 if i % 2 else -0.4)
    # ominous 16.2 -> 17.9: low drone, record-scratch moment is an SFX
    S.add('fx', 16.3, sine(36.7, 1.7) * env_adsr(int(1.7 * SR), 0.3, 0.2, 0.9, 0.4) * 0.9, -10)
    # panic 17.9 -> 20.4: fast minor pulse
    for k in range(int((20.4 - 17.9) / (b / 4))):
        t = 17.9 + k * b / 4
        S.add('bass', t, inst_bass(mtof(n2m('D2' if (k // 4) % 2 == 0 else 'D#2')), b / 4 * 0.7, cutoff=900), -10)
        if k % 4 == 0:
            S.add('perc', t, drum_taiko(0.8, 60), -11)
    S.add('pad', 17.9, inst_tremolo(C(['D3', 'D#3', 'A3']), 2.5, rate=13), -12)
    # countdown 20.4 -> 22.4: heartbeat that speeds up, then SILENCE until gravity returns
    for i, t in enumerate((20.42, 20.9, 21.14, 21.55, 21.85, 22.1)):
        S.add('perc', t, drum_kick(0.9), -6)
    # payoff at TG: huge hit + orchestral fall
    S.add('perc', TG, drum_taiko(1.4, 45), -2)
    S.add('lead', TG, inst_stab(C(['D4', 'F4', 'A4', 'D5']), 0.5), -5)
    S.add('pad', TG, inst_strings(C(['D3', 'F3', 'A3', 'D4']), TL - TG, attack=0.05, bright=4000), -8)
    for k in range(int((TL - TG) / (b / 2))):
        t = TG + k * b / 2
        S.add('perc', t, drum_snare(0.5 + 0.5 * k / 12, seed=400 + k), -14 + 6 * k / ((TL - TG) / (b / 2)))
    S.add('perc', TL, drum_taiko(1.3, 50), -3)
    # comedic ending TL+0.4 -> bonk: tiptoe pizzicato
    for i, nm in enumerate(['D4', 'F#4', 'A4', 'F#4', 'G4', 'B4', 'A4', None, 'D4', 'F#4', 'A4', 'D5']):
        t = TL + 0.5 + i * b / 2
        if nm and t < LS['L11'][1] + 0.3:
            S.add('lead', t, inst_pluck(mtof(n2m(nm)), 0.5, bright=0.5, seed=500 + i), -12)
    return S


CUES['video004'] = cue_video004
LOOPS['video004'] = LOOP4

if __name__ == '__main__':
    cue, out = sys.argv[1], sys.argv[2]
    S = CUES[cue]()
    y = S.render(loop=LOOPS.get(cue))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sf.write(out, y.astype(np.float32), SR, subtype='PCM_24')
    print('MUSIC_OK', out, round(len(y) / SR, 2), 's')
