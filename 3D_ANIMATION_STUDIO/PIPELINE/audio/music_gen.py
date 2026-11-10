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


# ------------------------------------------------------------------ VIDEO_005 cue (toilets, 32.4 s loop)
LOOP5 = 32.4


def cue_video005(dur=LOOP5):
    S = Score(dur + 2.0, bpm=132)
    b = 60 / 132
    C = lambda names: [mtof(n2m(x)) for x in names]
    # 0-3: sleepy morning (soft pad + plucks), the slam stab sits on 0.1
    S.add('pad', 0.0, inst_pad(C(['F3', 'A3', 'C4', 'E4']), 3.2, bright=1500, attack=0.3), -15)
    S.add('lead', 0.1, inst_stab(C(['F4', 'B4', 'D5']), 0.25), -7)
    S.add('perc', 0.1, drum_kick(1.0), -6)
    # 3-9.5: comedy (bassoon staccato + pizz + light kit)
    tune = ['C4', 'E4', 'G4', 'E4', 'F4', 'A4', 'G4', None, 'C4', 'E4', 'G4', 'C5', 'B4', 'G4', 'F4', 'D4']
    for k in range(int((9.5 - 3.0) / (b / 2))):
        t = 3.0 + k * b / 2
        nm = tune[k % len(tune)]
        if nm and k % 2 == 0:
            S.add('lead', t, inst_bassoon(mtof(n2m(nm)) / 2, b * 0.4), -9)
        if k % 4 == 0:
            S.add('bass', t, inst_tuba(mtof(n2m('C2' if (k // 8) % 2 == 0 else 'G1')), b * 0.5), -9)
        if k % 4 == 2:
            S.add('perc', t, drum_snare(0.5, seed=k), -16)
    S.gate('lead', 5.0, 5.4, floor_db=-40, fade=0.03)          # stop for the spray hit
    # 10.7-18.6: uprising chaos (driving kit, brass stabs, tuba ostinato)
    for k in range(int((18.6 - 10.7) / (b / 2))):
        t = 10.7 + k * b / 2
        beat, sub = divmod(k, 2)
        if sub == 0:
            S.add('perc', t, drum_kick(1.0), -6 if beat % 2 == 0 else -9)
        if sub == 0 and beat % 2 == 1:
            S.add('perc', t, drum_snare(1.0, seed=k), -9)
        S.add('perc', t, drum_hat(0.5, seed=k), -14, 0.3)
        S.add('bass', t, inst_tuba(mtof(n2m(['D2', 'D2', 'F2', 'G2', 'A2', 'G2', 'F2', 'E2'][k % 8])), b * 0.45), -8)
        if beat % 4 == 0 and sub == 0:
            S.add('lead', t, inst_stab(C(['D4', 'F4', 'A4', 'D5']), 0.3), -9)
    # 18.6-21.6: sneaky tiptoe pizzicato
    for i, nm in enumerate(['D4', None, 'F4', None, 'A4', 'G#4', 'A4', None, 'D4', None, 'F4', 'E4']):
        if nm:
            S.add('lead', 18.7 + i * b / 2, inst_pluck(mtof(n2m(nm)), 0.4, bright=0.4, seed=600 + i), -11)
    # 22.3-24.5: boss tension, then the blast hit
    S.add('pad', 22.3, inst_strings(C(['D2', 'A2', 'D3', 'D#3']), 2.3, attack=0.6, bright=1800), -7)
    for i in range(5):
        S.add('perc', 22.4 + i * 0.45, drum_taiko(1.0, 50), -6 + i)
    S.add('perc', 24.56, drum_taiko(1.4, 42), -2)
    S.add('lead', 24.56, inst_stab(C(['D3', 'F3', 'G#3', 'D4']), 0.6), -5)
    # 25.2-28.4: deflated comedy (slow sad tuba)
    for i, nm in enumerate(['A#1', 'A1', 'G#1', 'G1']):
        S.add('bass', 25.4 + i * 0.6, inst_tuba(mtof(n2m(nm)), 0.5 if i < 3 else 1.2), -8)
    # 28.4-31.45: the tub wakes (low drone + ticking), whoosh into the loop is an SFX
    S.add('fx', 28.6, sine(41.2, 2.9) * env_adsr(int(2.9 * SR), 0.6, 0.2, 0.9, 0.3) * 0.8, -10)
    S.add('pad', 28.9, inst_tremolo(C(['A2', 'A#2', 'E3']), 2.5, rate=12), -11)
    for i in range(10):
        S.add('perc', 28.9 + i * 0.25, drum_tick(0.4), -12)
    return S


CUES['video005'] = cue_video005
LOOPS['video005'] = LOOP5


# ------------------------------------------------------------------ VIDEO_006 cue: "The 13th Floor" (suspense)
LOOP6 = 38.0


def cue_video006(dur=LOOP6):
    """Dark, sparse suspense score. Hits sit on the story beats; the silences (before "You're late",
    the lights-out and the final black) are cut in the mix with music_gates (after reverb)."""
    S = Score(dur + 3.0, bpm=60)
    # 0-7: low drone (detuned), lonely high piano notes; a sour step when 13 lights up (0.35)
    S.add('fx', 0.0, sine(36.7, 7.2) * env_adsr(int(7.2 * SR), 0.05, 0.2, 0.9, 0.6) * 0.8, -12)
    S.add('pad', 0.0, inst_pad(C(['D2', 'A2', 'D3', 'F3']), 7.0, bright=900, attack=0.2), -16)
    S.add('pad', 0.35, inst_pad(C(['D#3', 'A3']), 6.6, bright=1200, attack=1.5), -18)
    for t, nm in ((0.4, 'A5'), (1.9, 'G#5'), (3.6, 'D5'), (5.2, 'D#5')):
        S.add('lead', t, inst_epiano(mtof(n2m(nm)), 1.2), -17)
    # 7-12: the doors open on the hallway: tremolo strings swell
    S.add('pad', 7.0, inst_tremolo(C(['D3', 'D#3', 'A3']), 5.2, rate=9, bright=1600), -15)
    S.add('fx', 7.0, sine(36.7, 5.5) * env_adsr(int(5.5 * SR), 1.0, 0.2, 0.9, 0.8) * 0.8, -10)
    # 12-14.6: walking: a slow heartbeat pulse (soft taiko)
    for i in range(4):
        S.add('perc', 12.1 + i * 0.75, drum_taiko(0.5, 52), -15)
    # 14.6-17.2: photo: cluster grows into the slam
    S.add('pad', 14.9, inst_strings(C(['D4', 'D#4', 'E4', 'A4']), 2.3, attack=1.2, bright=2200), -14)
    S.add('perc', 17.2, drum_taiko(1.4, 44), -4)
    # 17.2-20.4: panic: fast low ostinato + taiko
    for k in range(int((20.3 - 17.3) / 0.125)):
        t = 17.3 + k * 0.125
        S.add('bass', t, inst_bass(mtof(n2m(['D2', 'D2', 'D#2', 'D2'][k % 4])), 0.11, cutoff=500), -12)
        if k % 8 == 0:
            S.add('perc', t, drum_taiko(0.8, 50), -9)
    S.add('pad', 17.3, inst_tremolo(C(['D4', 'D#4', 'G#4']), 3.0, rate=13, bright=2600), -14)
    # 20.4-27.8: the walk to the apartment: sub drone only + distant bell, slowing heartbeat
    S.add('fx', 20.4, sine(32.7, 7.6) * env_adsr(int(7.6 * SR), 1.5, 0.2, 0.9, 0.3) * 0.9, -9)
    S.add('pad', 20.6, inst_pad(C(['D2', 'G#2', 'D3']), 7.0, bright=700, attack=2.0), -15)
    for i, t in enumerate((22.4, 23.3, 24.3, 25.4, 26.6)):
        S.add('perc', t, drum_taiko(0.4, 48), -16 - i)
    S.add('lead', 25.7, inst_bell(mtof(n2m('G#5')), 2.0), -16)                 # the double turns his head
    # 30.4-34.9: back in the elevator: uneasy pulse, then the clock reveal hit (33.3)
    for i in range(5):
        S.add('perc', 30.5 + i * 0.6, drum_taiko(0.5, 54), -14)
    S.add('pad', 30.5, inst_pad(C(['D2', 'A2', 'D3']), 2.6, bright=900, attack=0.4), -15)
    S.add('perc', 33.3, drum_taiko(1.0, 46), -8)
    S.add('pad', 33.3, inst_strings(C(['D3', 'D#3', 'A3', 'D#4']), 1.6, attack=0.05, bright=2000), -12)
    S.add('perc', 34.3, drum_taiko(0.7, 50), -11)
    # 34.9-37.8: the reflection: high tremolo creeping up to the cut
    S.add('pad', 34.9, inst_tremolo(C(['D5', 'D#5', 'A5']), 3.0, rate=14, bright=4000), -17)
    S.add('fx', 34.9, sine(36.7, 3.0) * env_adsr(int(3.0 * SR), 2.0, 0.2, 1.0, 0.05) * 0.9, -9)
    return S


CUES['video006'] = cue_video006
LOOPS['video006'] = LOOP6


# ------------------------------------------------------------------ VIDEO_007 cue: "After Hours · Part 1" (horror)
def cue_video007():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_007'))
    import edit_video007 as E7
    B, END = E7.B, E7.END
    S = Score(END + 3.0, bpm=70)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    # hook: drone + slow heartbeat + high tremolo cluster
    D(0.0, B['rewind0'] + 0.5)
    S.add('pad', 0.0, inst_tremolo(C(['D5', 'D#5', 'A5']), B['rewind0'], rate=12, bright=3500), -19)
    for i in range(int(B['rewind0'] / 0.9)):
        S.add('perc', 0.3 + i * 0.9, drum_taiko(0.45, 50), -15)
    # sneaking (booth -> office): low pizzicato ostinato in D minor + soft pad
    b = 60 / 70
    t = B['booth'] + 0.2
    pat = ['D2', None, 'F2', 'D2', None, 'A1', 'C2', None]
    k = 0
    while t < B['files'] - 0.3:
        nm = pat[k % len(pat)]
        if nm:
            S.add('bass', t, inst_pizz(mtof(n2m(nm)), 0.3, seed=k), -12)
        if k % 8 == 0:
            S.add('pad', t, inst_pad(C(['D3', 'F3', 'A3']) if (k // 8) % 2 == 0 else C(['A#2', 'D3', 'F3']), b * 4, bright=900, attack=0.6), -19)
        t += b / 2
        k += 1
    D(B['corr'], B['files'] - B['corr'], 41.2, -12)
    # files: music-box bells, slow and wrong; a hit on "Kept"
    mel = ['A5', 'F5', 'E5', 'D5', 'C#5', 'D5', 'A4', None, 'A5', 'G5', 'F5', 'E5', 'F5', 'D5']
    for i, nm in enumerate(mel):
        tt = B['files'] + 0.2 + i * 0.55
        if nm and tt < B['face']:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)) * 0.995, 1.2), -15)
    S.add('perc', B['kept'], drum_taiko(1.2, 44), -5)
    S.add('pad', B['kept'], inst_strings(C(['D3', 'D#3', 'A3', 'D#4']), 1.4, attack=0.02, bright=2200), -11)
    D(B['note'], B['bang'] - B['note'], 34.6, -11)
    # the pen: a riser into the BANG
    S.add('pad', B['becomes'] - 0.5, inst_tremolo(C(['D4', 'D#4']), B['bang'] - B['becomes'] + 0.5, rate=16, bright=3000), -16)
    S.add('perc', B['bang'], drum_taiko(1.6, 38), -2)
    # peek -> the reveal: sub drone + high cluster growing; stab when it looks at you
    D(B['peek'], B['face3'] - B['peek'] + 0.3, 30.9, -8)
    S.add('pad', B['pov'], inst_tremolo(C(['D5', 'D#5', 'E5', 'A#5']), B['looks'] - B['pov'], rate=14, bright=4200), -16)
    S.add('perc', B['looks'], drum_taiko(1.5, 40), -3)
    S.add('lead', B['looks'], inst_stab(C(['D3', 'D#3', 'G#3', 'D4']), 0.8), -6)
    # panic: fast low ostinato until the footsteps stop
    t = B['face3']
    k = 0
    while t < B['stop']:
        S.add('bass', t, inst_bass(mtof(n2m(['D2', 'D2', 'D#2', 'D2'][k % 4])), 0.1, cutoff=500), -11)
        if k % 4 == 0:
            S.add('perc', t, drum_taiko(0.8, 52), -10)
        t += 0.14
        k += 1
    # the choice: drone + clock ticks to the end
    D(B['stop'] + 1.2, END - B['stop'] - 1.0, 36.7, -11)
    for i in range(int((END - B['choice']) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    return S


CUES['video007'] = cue_video007
LOOPS['video007'] = None


# ------------------------------------------------------------------ VIDEO_008 cue: "Last Bus · Part 1"
def cue_video008():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_008'))
    import edit_video008 as E8
    B, END = E8.B, E8.END
    S = Score(END + 3.0, bpm=72)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    # 0..blink: a faint, ordinary late-night synth pad (it's just a bus)
    S.add('pad', 0.0, inst_pad(C(['F3', 'A3', 'C4', 'E4']), B['blink'] + 0.2, bright=1400, attack=0.05), -17)
    # after the blink: a hit, then the drone
    S.add('perc', B['blink'] + 0.1, drum_taiko(1.3, 42), -4)
    S.add('pad', B['blink'] + 0.1, inst_strings(C(['D3', 'D#3', 'A3']), 2.0, attack=0.02, bright=2000), -11)
    D(B['blink'] + 0.2, B['turn'] - B['blink'], 36.7, -10)
    S.add('pad', B['empty'], inst_tremolo(C(['D5', 'D#5']), B['turn'] - B['empty'], rate=11, bright=3200), -20)
    S.add('perc', B['turn'], drum_taiko(1.4, 40), -3)
    S.add('lead', B['turn'], inst_stab(C(['D3', 'F3', 'G#3', 'D4']), 0.7), -6)
    # driver: low pulse
    for i in range(int((B['route'] - B['driver']) / 0.8)):
        S.add('perc', B['driver'] + i * 0.8, drum_taiko(0.5, 50), -14)
    D(B['driver'], B['window'] - B['driver'], 32.7, -10)
    S.add('perc', B['you'], drum_taiko(1.2, 44), -5)
    # fog: music-box waltz, slow and detuned
    mel = ['D5', 'F5', 'A5', 'G#5', 'F5', 'D5', 'C#5', 'D5', 'E5', 'F5', 'E5', 'D5']
    for i, nm in enumerate(mel):
        tt = B['window'] + 0.2 + i * 0.5
        if tt < B['button']:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)) * 0.993, 1.2), -14)
    D(B['button'], B['mirror'] - B['button'], 34.6, -10)
    S.add('pad', B['ticket'], inst_tremolo(C(['D4', 'D#4', 'A4']), B['noface'] - B['ticket'], rate=15, bright=3500), -16)
    S.add('perc', B['noface'], drum_taiko(1.6, 38), -2)
    S.add('lead', B['noface'], inst_stab(C(['D3', 'D#3', 'G#3', 'D4']), 0.9), -5)
    # brakes -> choice: panic ostinato, then clock ticks
    t = B['brake']
    k = 0
    while t < B['choice']:
        S.add('bass', t, inst_bass(mtof(n2m(['D2', 'D2', 'D#2', 'D2'][k % 4])), 0.1, cutoff=500), -11)
        t += 0.14
        k += 1
    D(B['choice'], B['back'] - B['choice'], 36.7, -11)
    for i in range(int((B['back'] - B['choice']) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    S.add('perc', B['back'], drum_taiko(1.4, 40), -3)
    return S


CUES['video008'] = cue_video008
LOOPS['video008'] = None


# ------------------------------------------------------------------ VIDEO_009 cue: "They Knock · Part 1"
def cue_video009():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_009'))
    import edit_video009 as E9
    B, END = E9.B, E9.END
    S = Score(END + 3.0, bpm=96)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    D(0.0, B['flash'], 36.7, -10)
    S.add('perc', B['knock'] + 0.7, drum_taiko(1.3, 42), -4)
    S.add('pad', B['title'], inst_strings(C(['D3', 'D#3', 'A3']), 1.6, attack=0.02, bright=2000), -11)
    # flashback -> 'now they run': driving low pulse
    b = 60 / 96
    t, k = B['run'], 0
    while t < B['wide']:
        S.add('bass', t, inst_bass(mtof(n2m(['D2', 'D2', 'F2', 'D#2'][k % 4])), b * 0.45, cutoff=600), -11)
        if k % 2 == 0:
            S.add('perc', t, drum_taiko(0.7, 52), -11)
        t += b / 2
        k += 1
    S.add('perc', B['phone'], drum_taiko(1.2, 44), -6)
    # the room: tense pad + clock-like pizz
    D(B['wide'], B['window'] - B['wide'], 34.6, -11)
    t, k = B['wide'], 0
    while t < B['window']:
        S.add('bass', t, inst_pizz(mtof(n2m(['D3', 'A2', 'D3', 'G#2'][k % 4])), 0.3, seed=k), -14)
        t += b
        k += 1
    S.add('pad', B['z1'], inst_tremolo(C(['D4', 'D#4', 'A4']), B['l1'] - B['z1'] + 1.0, rate=12, bright=3000), -15)
    # courtyard: they look up
    D(B['window'], B['text'] - B['window'], 30.9, -9)
    S.add('perc', B['up'], drum_taiko(1.4, 40), -3)
    S.add('lead', B['up'], inst_stab(C(['D3', 'F3', 'G#3', 'D4']), 0.8), -6)
    S.add('perc', B['msg'], drum_taiko(1.2, 44), -5)
    # vent -> panic ostinato -> choice ticks
    S.add('pad', B['vent'], inst_tremolo(C(['D5', 'D#5', 'E5']), B['vent2'] - B['vent'], rate=15, bright=4000), -16)
    t, k = B['vent2'], 0
    while t < B['choice']:
        S.add('bass', t, inst_bass(mtof(n2m(['D2', 'D2', 'D#2', 'D2'][k % 4])), 0.1, cutoff=500), -10)
        if k % 4 == 0:
            S.add('perc', t, drum_taiko(0.9, 50), -9)
        t += 0.13
        k += 1
    D(B['choice'], END - B['choice'], 36.7, -11)
    for i in range(int((B['again'] - B['choice']) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    return S


CUES['video009'] = cue_video009
LOOPS['video009'] = None


# ------------------------------------------------------------------ VIDEO_010 cue: "Last Bus · Part 2"
def cue_video010():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_010'))
    import edit_video010 as E10
    B, END = E10.B, E10.END
    S = Score(END + 3.0, bpm=72)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    D(0.0, B['explodes'], 36.7, -10)
    S.add('pad', 0.0, inst_tremolo(C(['D4', 'D#4']), B['explodes'], rate=13, bright=3000), -16)
    S.add('perc', B['explodes'], drum_taiko(1.6, 38), -2)
    S.add('lead', B['explodes'], inst_stab(C(['D3', 'F3', 'G#3', 'D4']), 0.9), -5)
    D(B['mirror'], B['run'] - B['mirror'], 32.7, -9)
    mel = ['D5', 'F5', 'A5', 'G#5', 'F5', 'D5', 'C#5', 'D5']
    for i, nm in enumerate(mel):
        tt = B['them'] + i * 0.55
        if tt < B['tilts']:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)) * 0.993, 1.2), -14)
    S.add('perc', B['tilts'], drum_taiko(1.3, 42), -4)
    t, k = B['walking'], 0
    while t < B['poster']:
        S.add('bass', t, inst_bass(mtof(n2m(['D2', 'D2', 'D#2', 'D2'][k % 4])), 0.1, cutoff=500), -10)
        if k % 4 == 0:
            S.add('perc', t, drum_taiko(0.8, 50), -10)
        t += 0.14
        k += 1
    D(B['poster'], B['lights'] - B['poster'], 34.6, -10)
    S.add('perc', B['missing'], drum_taiko(1.3, 42), -4)
    S.add('perc', B['date'] + 0.3, drum_taiko(1.3, 42), -4)
    S.add('pad', B['date'], inst_strings(C(['D3', 'D#3', 'A3', 'D#4']), 2.0, attack=0.02, bright=2200), -11)
    D(B['lights'], B['choice'] - B['lights'], 30.9, -9)
    S.add('pad', B['inside'], inst_tremolo(C(['D5', 'D#5', 'A5']), B['yourface'] - B['inside'], rate=14, bright=4000), -16)
    S.add('perc', B['yourface'], drum_taiko(1.6, 38), -2)
    S.add('lead', B['yourface'], inst_stab(C(['D3', 'D#3', 'G#3', 'D4']), 0.9), -5)
    D(B['choice'], END - B['choice'], 36.7, -11)
    for i in range(int((B['loopback'] - B['choice']) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    return S


CUES['video010'] = cue_video010
LOOPS['video010'] = None


# ------------------------------------------------------------------ VIDEO_011 cue: "Benched · Part 1" (sports drama)
def cue_video011():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_011'))
    import edit_video011 as E11
    B, END = E11.B, E11.END
    S = Score(END + 3.0, bpm=90)
    b = 60 / 90
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    # hook: heartbeat pulse + low drone; a hit on "That's you."
    D(0.0, B['flash'], 41.2, -10)
    for i in range(int(B['you'] / 0.8)):
        S.add('perc', 0.2 + i * 0.8, drum_kick(0.8), -9)
    S.add('perc', B['you'], drum_taiko(1.3, 44), -4)
    S.add('pad', B['you'], inst_strings(C(['A2', 'E3', 'A3', 'C4']), 2.2, attack=0.05, bright=1800), -11)
    # flashback: lonely piano in A minor
    mel = ['A4', 'C5', 'E5', 'D5', 'C5', 'B4', 'A4', 'E4', 'F4', 'A4', 'G4', 'E4']
    for i, nm in enumerate(mel):
        tt = B['flash'] + 0.2 + i * b
        if tt < B['night']:
            S.add('lead', tt, inst_epiano(mtof(n2m(nm)), b * 0.9), -13)
    S.add('pad', B['flash'], inst_pad(C(['A2', 'E3', 'A3', 'C4']), B['night'] - B['flash'], bright=1000, attack=0.8), -17)
    # the grind: building beat (kick/snare/hats) + rising chords
    t, k = B['night'], 0
    prog = [['A2', 'E3', 'A3', 'C4'], ['F2', 'C3', 'F3', 'A3'], ['C3', 'G3', 'C4', 'E4'], ['G2', 'D3', 'G3', 'B3']]
    while t < B['except_']:
        if k % 2 == 0:
            S.add('perc', t, drum_kick(1.0), -7)
        if k % 4 == 2:
            S.add('perc', t, drum_snare(0.9, seed=k), -10)
        if t > B['shots']:
            S.add('perc', t, drum_hat(0.5, seed=k), -15)
        if k % 8 == 0:
            S.add('pad', t, inst_strings(C(prog[(k // 8) % 4]), b * 4, attack=0.3, bright=2200), -14)
            S.add('bass', t, inst_bass(mtof(n2m(prog[(k // 8) % 4][0])), b * 3.5, cutoff=600), -11)
        t += b / 2
        k += 1
    # "except Coach": the beat drops out; low tension
    D(B['except_'], B['crowd'] - B['except_'], 36.7, -10)
    # the chant: stomp-clap rhythm builds, big swell on "You. Get in."
    t, k = B['crowd'], 0
    while t < B['c2']:
        S.add('perc', t, drum_taiko(0.8, 50), -9 + min(4, k * 0.2))
        t += 0.5
        k += 1
    S.add('pad', B['turn'], inst_tremolo(C(['A3', 'C4', 'E4']), B['c2'] - B['turn'], rate=12, bright=3000), -14)
    S.add('perc', B['c2'] + 0.6, drum_taiko(1.5, 40), -2)
    S.add('pad', B['c2'] + 0.6, inst_strings(C(['A2', 'E3', 'A3', 'C#4', 'E4']), 3.0, attack=0.05, bright=3000), -8)
    S.add('lead', B['c2'] + 0.6, inst_stab(C(['A3', 'C#4', 'E4', 'A4']), 0.8), -7)
    # the walk + choice: tension pulse, ticking clock
    D(B['walk'], END - B['walk'], 41.2, -11)
    for i in range(int((END - B['choice']) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    return S


CUES['video011'] = cue_video011
LOOPS['video011'] = None


# ------------------------------------------------------------------ VIDEO_012 cue: "Don't Touch The Vase" (jumpscare horror)
def cue_video012():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_012'))
    import edit_video012 as E12
    B, END = E12.B, E12.END
    S = Score(END + 3.0, bpm=60)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    # hook: a music box (grandma's), slightly out of tune, that dies on the crash
    mel = ['E5', 'G5', 'B5', 'A5', 'G5', 'E5', 'D#5', 'E5']
    for i, nm in enumerate(mel):
        tt = 0.05 + i * 0.32
        if tt < B['crash']:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)) * 0.99, 1.0), -13)
    S.add('perc', B['crash'], drum_taiko(1.6, 38), -2)
    S.add('pad', B['crash'], inst_strings(C(['E3', 'F3', 'A#3', 'E4']), 2.4, attack=0.02, bright=2600), -9)
    D(B['crash'] + 0.2, B['dinner'] - B['crash'], 32.7, -9)
    # dinner: a 'normal' warm pad that keeps detuning; drone under
    S.add('pad', B['dinner'], inst_pad(C(['C3', 'E3', 'G3', 'B3']), B['mom'] - B['dinner'] + 0.5, bright=1200, attack=0.3), -16)
    S.add('pad', B['mom'], inst_pad([f * 0.985 for f in C(['C3', 'E3', 'G3', 'B3'])], B['dad'] - B['mom'], bright=1000, attack=0.8), -17)
    D(B['mom'], B['js1'] - B['mom'], 34.6, -10)
    S.add('pad', B['dad'], inst_tremolo(C(['E4', 'F4', 'A#4']), B['js1'] - B['dad'], rate=10, bright=2500), -18)
    # night: dread
    D(B['power'], B['js2'] - B['power'], 30.9, -8)
    S.add('pad', B['window'], inst_tremolo(C(['D5', 'D#5', 'A5']), B['stairs'] - B['window'], rate=14, bright=3500), -18)
    for i in range(int((B['bath'] - B['stairs']) / 0.45)):
        S.add('perc', B['stairs'] + i * 0.45, drum_taiko(0.6 + 0.08 * i, 48), -12 + i)
    D(B['js2'] + 0.6, B['choice'] - B['js2'], 29.1, -8)
    D(B['choice'], B['js3'] - B['choice'], 36.7, -10)
    for i in range(int((B['js3'] - B['choice'] - 1.2) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    return S


CUES['video012'] = cue_video012
LOOPS['video012'] = None


# ------------------------------------------------------------------ VIDEO_013 cue: "Benched · Part 2" (the shot)
def cue_video013():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_013'))
    import edit_video013 as E13
    B, END = E13.B, E13.END
    S = Score(END + 3.0, bpm=100)
    b = 60 / 100
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    # hook: suspended chord under the freeze
    S.add('pad', 0.0, inst_strings(C(['A2', 'E3', 'B3', 'E4']), B['recap'], attack=0.05, bright=2200), -11)
    S.add('perc', B['water'], drum_taiko(1.2, 44), -5)
    # recap: driving montage beat
    t, k = B['recap'], 0
    prog = [['A2', 'E3', 'A3', 'C4'], ['F2', 'C3', 'F3', 'A3'], ['C3', 'G3', 'C4', 'E4'], ['G2', 'D3', 'G3', 'B3']]
    while t < B['ball']:
        if k % 2 == 0:
            S.add('perc', t, drum_kick(1.0), -7)
        if k % 4 == 2:
            S.add('perc', t, drum_snare(0.9, seed=k), -10)
        S.add('perc', t, drum_hat(0.4, seed=k), -16)
        if k % 8 == 0:
            S.add('pad', t, inst_strings(C(prog[(k // 8) % 4]), b * 4, attack=0.2, bright=2400), -14)
            S.add('bass', t, inst_bass(mtof(n2m(prog[(k // 8) % 4][0])), b * 3.5, cutoff=600), -11)
        t += b / 2
        k += 1
    # the play: heartbeat + rising tremolo
    D(B['ball'], B['go'] - B['ball'], 41.2, -10)
    for i in range(int((B['go'] - B['ball']) / 0.55)):
        S.add('perc', B['ball'] + i * 0.55, drum_kick(0.9), -8)
    S.add('pad', B['ball'], inst_tremolo(C(['A3', 'C4', 'E4']), B['go'] - B['ball'], rate=12, bright=3000), -15)
    # slow motion: one long held note, heartbeat slowing
    S.add('pad', B['go'], inst_pad(C(['A2', 'E3', 'A3', 'E4']), B['slow_end'] - B['go'] + 0.5, bright=1600, attack=0.6), -12)
    for i, dt in enumerate((0.0, 0.9, 1.9, 3.0)):
        if B['go'] + dt < B['rim']:
            S.add('perc', B['go'] + dt, drum_kick(0.8), -9)
    # it drops: the anthem
    tin = B['drops'] + 0.15
    S.add('perc', tin, drum_taiko(1.6, 40), -1)
    S.add('lead', tin, inst_stab(C(['A3', 'C#4', 'E4', 'A4']), 1.0), -5)
    t, k = tin, 0
    anth = [['A2', 'E3', 'A3', 'C#4'], ['F#2', 'C#3', 'F#3', 'A3'], ['D3', 'A3', 'D4', 'F#4'], ['E3', 'B3', 'E4', 'G#4']]
    while t < B['scout']:
        if k % 2 == 0:
            S.add('perc', t, drum_kick(1.0), -6)
        if k % 4 == 2:
            S.add('perc', t, drum_snare(1.0, seed=k), -8)
        S.add('perc', t, drum_hat(0.5, seed=k), -14)
        if k % 8 == 0:
            S.add('pad', t, inst_strings(C(anth[(k // 8) % 4]), b * 4, attack=0.1, bright=3200), -10)
            S.add('bass', t, inst_bass(mtof(n2m(anth[(k // 8) % 4][0])), b * 3.5, cutoff=700), -9)
        t += b / 2
        k += 1
    # scout -> choice: intrigue
    D(B['scout'], END - B['scout'], 41.2, -11)
    S.add('pad', B['scout'], inst_pad(C(['A2', 'C3', 'E3', 'B3']), END - B['scout'], bright=1200, attack=0.8), -15)
    for i in range(int((END - B['choice']) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -13)
    return S


CUES['video013'] = cue_video013
LOOPS['video013'] = None


# ------------------------------------------------------------------ VIDEO_014 cue: "Don't Touch The Vase · Part 2"
def cue_video014():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_014'))
    import edit_video014 as E14
    B, END = E14.B, E14.END
    S = Score(END + 3.0, bpm=60)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    D(0.0, B['recap'], 34.6, -10)
    S.add('pad', 0.0, inst_tremolo(C(['E4', 'F4']), B['recap'], rate=10, bright=2500), -18)
    S.add('perc', B['recap'], drum_taiko(1.2, 44), -5)
    # the run: fast pulse
    t, k = B['card'], 0
    while t < B['lightning']:
        S.add('bass', t, inst_bass(mtof(n2m(['E2', 'E2', 'F2', 'E2'][k % 4])), 0.12, cutoff=500), -11)
        if k % 4 == 0:
            S.add('perc', t, drum_taiko(0.7, 50), -11)
        t += 0.16
        k += 1
    D(B['door'], B['g4'] - B['door'], 32.7, -10)
    # Grandma's kitchen: grandma's music box (the same tune as Part 1), slower
    mel = ['E5', 'G5', 'B5', 'A5', 'G5', 'E5', 'D#5', 'E5']
    for i, nm in enumerate(mel):
        tt = B['kitchen'] + 0.3 + i * 0.45
        if tt < B['g3']:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)) * 0.99, 1.2), -15)
    S.add('perc', B['missing'] + 0.6, drum_taiko(1.2, 44), -5)
    # 1968: a faded, warped lullaby
    for i, nm in enumerate(['E4', 'G4', 'B4', 'A4', 'G4', 'E4', 'D#4', 'E4', 'B3', 'E4']):
        tt = B['g4'] + 0.2 + i * 0.6
        if tt < B['g5']:
            S.add('lead', tt, inst_epiano(mtof(n2m(nm)) * 0.985, 0.55), -14)
    S.add('pad', B['g4'], inst_pad([f * 0.985 for f in C(['E3', 'G3', 'B3'])], B['g5'] - B['g4'], bright=900, attack=0.6), -17)
    D(B['knock'], B['js2'] - B['knock'], 30.9, -8)
    S.add('pad', B['e1'], inst_tremolo(C(['D5', 'D#5', 'A5']), B['js2'] - B['e1'], rate=14, bright=3500), -17)
    D(B['js2'] + 0.6, B['js3'] - B['js2'], 29.1, -8)
    for i in range(int((B['js3'] - B['choice'] - 1.2) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    return S


CUES['video014'] = cue_video014
LOOPS['video014'] = None


# ------------------------------------------------------------------ VIDEO_015 cue: "Kessrah · Part 1"
def cue_video015():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_015'))
    import edit_video015 as E15
    B, END = E15.B, E15.END
    S = Score(END + 3.0, bpm=60)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    D(0.0, B['rewind'], 34.6, -9)
    S.add('pad', 0.0, inst_tremolo(C(['E4', 'F4', 'A#4']), B['rewind'], rate=11, bright=2600), -17)
    # 3:33 AM: a slow, low choir-ish pad; a hit when the candles die
    S.add('pad', B['ritual'], inst_pad(C(['D2', 'A2', 'D3', 'F3']), B['candles'] - B['ritual'] + 1.0, bright=900, attack=1.0), -15)
    S.add('perc', B['out'], drum_taiko(1.4, 42), -4)
    S.add('pad', B['out'], inst_strings(C(['D3', 'D#3', 'A3']), 1.8, attack=0.02, bright=2200), -11)
    D(B['bed'], B['school'] - B['bed'], 32.7, -10)
    # morning: deceptively normal soft piano, with a wrong note that keeps coming back
    mel = ['C5', 'E5', 'G5', 'E5', 'C5', 'D5', 'F#5', 'D5', 'C5', 'E5', 'G5', 'F#5']
    for i, nm in enumerate(mel * 3):
        tt = B['school'] + 0.2 + i * 0.5
        if tt < B['class_']:
            S.add('lead', tt, inst_epiano(mtof(n2m(nm)), 0.45), -16)
    D(B['class_'], B['js1'] - B['class_'], 36.7, -11)
    S.add('pad', B['kname'], inst_tremolo(C(['E4', 'F4']), B['js1'] - B['kname'], rate=13, bright=3000), -16)
    D(B['js1'] + 0.6, B['empty'] - B['js1'], 30.9, -8)
    D(B['empty'], B['js2'] - B['empty'], 29.1, -8)
    for i, nm in enumerate(['E5', 'G5', 'B5', 'A#5', 'G5', 'E5']):
        tt = B['board'] + i * 0.7
        if tt < B['k01']:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)) * 0.99, 1.2), -15)
    D(B['js2'] + 0.6, B['js3'] - B['js2'], 30.9, -8)
    for i in range(int((B['js3'] - B['choice'] - 1.0) / 0.5)):
        S.add('perc', B['choice'] + i * 0.5, drum_tick(0.5), -12)
    return S


CUES['video015'] = cue_video015
LOOPS['video015'] = None

def cue_video016():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'VIDEOS', 'VIDEO_016'))
    import edit_video016 as E16
    B, END, s16, e16 = E16.B, E16.END, E16.s, E16.e
    S = Score(END + 3.0, bpm=60)
    D = lambda t, d, f=36.7, g=-10: S.add('fx', t, sine(f, d) * env_adsr(int(d * SR), min(1.5, d / 3), 0.2, 0.9, min(1.0, d / 4)) * 0.8, g)
    # hook: one low pulse under the whisper, then a hit on the title
    D(0.0, B['title'], 32.7, -9)
    S.add('perc', B['title'], drum_taiko(1.6, 40), -3)
    S.add('pad', B['title'], inst_strings(C(['C3', 'C#3', 'G3']), 1.6, attack=0.02, bright=2000), -10)
    # the forest: cold, open minor pad (blue-green), a lonely bell figure
    S.add('pad', B['enter'], inst_pad(C(['A2', 'E3', 'C4']), B['sign'] - B['enter'], bright=1100, attack=1.5), -16)
    for i, nm in enumerate(['E5', 'C5', 'A4', 'B4', 'E5', 'C5', 'A4', 'G#4'] * 2):
        tt = B['enter'] + 1.0 + i * 1.1
        if tt < B['sign'] - 0.5:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)), 1.4), -19)
    # the sign + bones: the floor drops out
    S.add('pad', B['sign'], inst_pad(C(['A1', 'A2', 'D#3']), B['house_in'] - B['sign'], bright=700, attack=1.0), -14)
    D(B['bones'], B['house_in'] - B['bones'], 30.9, -9)
    S.add('pad', B['figure'], inst_tremolo(C(['D#5', 'E5']), 2.5, rate=14, bright=3200), -15)
    S.add('perc', B['help'], drum_taiko(1.0, 46), -9)
    # the house: warm but wrong (a slow out-of-tune music box)
    for i, nm in enumerate(['A4', 'C5', 'E5', 'D#5', 'C5', 'A4', 'B4', 'F5'] * 4):
        tt = B['house_in'] + 0.5 + i * 0.6
        if tt < B['knock'] - 0.6:
            S.add('lead', tt, inst_bell(mtof(n2m(nm)) * (1.0 + 0.012 * (i % 3 - 1)), 1.0), -18)
    S.add('pad', B['wall'], inst_tremolo(C(['A3', 'A#3']), B['knock'] - B['wall'], rate=9, bright=2200), -17)
    # knocks: almost nothing, just a sub; then lights out
    D(B['knock'], B['reveal'] - B['knock'], 29.1, -8)
    # the reveal + chase: hits, then driving taiko 8ths and string ostinato
    S.add('perc', B['js1'], drum_taiko(1.4, 38), -2)
    S.add('pad', B['js1'], inst_strings(C(['D3', 'D#3', 'A3']), 1.6, attack=0.02, bright=2400), -10)
    S.add('pad', B['x05'], inst_tremolo(C(['D4', 'D#4', 'G#4']), B['rush'] - B['x05'], rate=12, bright=2800), -14)
    S.add('perc', B['js2'], drum_taiko(1.4, 36), -1)
    t, i = B['chase'], 0
    while t < B['edge'] - 0.3:
        S.add('perc', t, drum_taiko(0.8, 55 if i % 4 else 44), -9 if i % 4 else -5)
        if i % 2 == 0:
            S.add('lead', t, inst_strings(C(['D3' if (i // 8) % 2 == 0 else 'D#3']), 0.24, attack=0.005, bright=3000), -13)
        t += 0.2; i += 1
    S.add('perc', B['edge'] - 0.3, drum_taiko(1.2, 40), -5)
    # the edge: grey dawn relief... then the twist
    S.add('pad', B['edge'], inst_pad(C(['F3', 'A3', 'C4', 'E4']), B['twist'] - B['edge'] + 0.5, bright=1300, attack=1.2), -16)
    S.add('pad', B['twist'], inst_strings(C(['F3', 'F#3', 'C4']), 1.4, attack=0.01, bright=2600), -10)
    D(B['twist'], B['js3'] - B['twist'], 30.9, -8)
    S.add('pad', B['shadows'], inst_tremolo(C(['F#4', 'G4']), B['js3'] - B['shadows'], rate=13, bright=3000), -15)
    S.add('perc', B['js3'], drum_taiko(1.6, 36), -1)
    return S


CUES['video016'] = cue_video016
LOOPS['video016'] = None

if __name__ == '__main__':
    cue, out = sys.argv[1], sys.argv[2]
    S = CUES[cue]()
    y = S.render(loop=LOOPS.get(cue))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sf.write(out, y.astype(np.float32), SR, subtype='PCM_24')
    print('MUSIC_OK', out, round(len(y) / SR, 2), 's')
