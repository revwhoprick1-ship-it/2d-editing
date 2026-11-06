#!/usr/bin/env python3
"""Procedural sound-effect library generator.

Every sound is synthesised from oscillators/noise in this file, so the whole
library is original studio work (no third-party samples, no licence strings).

    /opt/tools/tts312/bin/python PIPELINE/audio/sfx_synth.py AUDIO
writes AUDIO/sound_effects/<category>/*.wav, AUDIO/ambience/*.wav and
AUDIO/sound_effects/LIBRARY.json (descriptions, durations, tags).
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import *  # noqa

LIB = {}


def reg(cat, name, desc, tags=()):
    def deco(fn):
        LIB[(cat, name)] = (fn, desc, list(tags))
        return fn
    return deco


def st(x):
    return x if x.ndim == 2 else np.stack([x, x], 1)


# ------------------------------------------------------------------ BIO / VIDEO_001 essentials
@reg('bio', 'heartbeat_lubdub', 'Close, chest-deep heartbeat: "lub" (AV valves) + "dub" (semilunar valves).', ['heart', 'pulse'])
def heartbeat_lubdub(seed=0, dub_gap=0.26):
    n = int(0.9 * SR)
    out = np.zeros(n)
    for t0, f, amp, dec in ((0.0, 48, 1.0, 0.11), (dub_gap, 62, 0.75, 0.08)):
        i0 = int(t0 * SR)
        m = int(0.4 * SR)
        tt = np.arange(m) / SR
        fr = f * (1 + 0.8 * np.exp(-tt / 0.02))
        body = np.sin(2 * np.pi * np.cumsum(fr) / SR) * env_exp(m, dec, attack=0.004)
        thump = lowpass(noise(m, 'pink', seed + int(t0 * 100)), 180) * env_exp(m, 0.03) * 0.6
        out[i0:i0 + m] += amp * (body + thump)
    out = soft_sat(lowpass(out, 400), 1.6)
    return st(normalize(out, -1))


@reg('bio', 'heartbeat_muffled', 'Heartbeat heard from inside a vessel (darker, roomy).', ['heart', 'inside'])
def heartbeat_muffled():
    x = heartbeat_lubdub()[:, 0]
    x = lowpass(x, 160)
    return normalize(convolve_stereo(x, reverb_ir(1.2, 0.35, damp=1200), 0.45), -3)


@reg('bio', 'bloodstream_bed', 'Bloodstream ambience: low rumble, wet flow, gentle swells (30 s, loopable).', ['ambience', 'flow'])
def bloodstream_bed(dur=30.0):
    n = int(dur * SR)
    rum = lowpass(noise(n, 'brown', 1), 90) * 0.9
    flow = bandpass(noise(n, 'pink', 2), 120, 900) * 0.35
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * np.arange(n) / SR)
    gurg = np.zeros(n)
    rng = np.random.default_rng(3)
    for _ in range(int(dur * 2.5)):
        i = rng.integers(0, n - SR)
        m = int(rng.uniform(0.05, 0.18) * SR)
        f0 = rng.uniform(180, 520)
        tt = np.arange(m) / SR
        g = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.5 * tt / tt[-1])) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2
        gurg[i:i + m] += g * rng.uniform(0.05, 0.15)
    x = rum + flow * lfo + lowpass(gurg, 1500)
    L = x + 0.15 * bandpass(noise(n, 'pink', 4), 200, 1200)
    R = x + 0.15 * bandpass(noise(n, 'pink', 5), 200, 1200)
    y = np.stack([L, R], 1)
    y = fade(y, 1.0, 1.0)
    return normalize(y, -6)


@reg('bio', 'capillary_bed', 'Tight capillary ambience: closer, higher, wet creaks and soft squelches (20 s).', ['ambience'])
def capillary_bed(dur=20.0):
    n = int(dur * SR)
    base = bandpass(noise(n, 'pink', 11), 250, 2500) * 0.25 + lowpass(noise(n, 'brown', 12), 140) * 0.5
    rng = np.random.default_rng(13)
    sq = np.zeros(n)
    for _ in range(int(dur * 1.5)):
        i = rng.integers(0, n - SR)
        sq[i:i + int(0.3 * SR)] += squelch(rng.integers(0, 999))[:int(0.3 * SR), 0] * rng.uniform(0.1, 0.3)
    y = st(base + sq)
    return normalize(fade(y, 1.0, 1.0), -8)


@reg('bio', 'squelch', 'Soft wet squelch / cell squeeze.', ['wet', 'cell'])
def squelch(seed=0):
    m = int(0.35 * SR)
    tt = np.arange(m) / SR
    rng = np.random.default_rng(seed)
    f = rng.uniform(250, 420) * (1 - 0.5 * tt / tt[-1])
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(m, 0.08)
    nz = sweep_filter(noise(m, 'white', seed), 2500, 400, kind='bandpass', q=3) * env_exp(m, 0.06)
    return st(normalize(tone * 0.6 + nz * 0.7, -3))


@reg('bio', 'valve_slam', 'Heavy wet slam of a heart valve closing (impact + body + flap).', ['heart', 'impact'])
def valve_slam():
    m = int(1.2 * SR)
    tt = np.arange(m) / SR
    sub = np.sin(2 * np.pi * np.cumsum(55 * (1 + 2 * np.exp(-tt / 0.03))) / SR) * env_exp(m, 0.25)
    slap = highpass(noise(m, 'white', 21), 600) * env_exp(m, 0.015) * 0.8
    flap = bandpass(noise(m, 'pink', 22), 150, 1200) * env_exp(m, 0.09) * 0.8
    x = soft_sat(sub + slap + flap, 2.0)
    return normalize(convolve_stereo(x, reverb_ir(1.5, 0.5, damp=2500), 0.3), -1)


@reg('bio', 'engulf_gloop', 'Neutrophil engulfing: viscous stretching gloop with low swell.', ['cell', 'creature'])
def engulf_gloop():
    m = int(1.6 * SR)
    tt = np.arange(m) / SR
    f = 90 + 60 * np.sin(2 * np.pi * 1.3 * tt) + 40 * tt
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1])
    wet = sweep_filter(noise(m, 'pink', 31), 300, 1800, kind='bandpass', q=2) * (0.3 + 0.7 * np.sin(np.pi * tt / tt[-1]))
    bub = np.zeros(m)
    rng = np.random.default_rng(32)
    for _ in range(14):
        i = rng.integers(0, m - 6000)
        bub[i:i + 4000] += bubble(rng.integers(0, 99))[:4000, 0] * 0.25
    x = body * 0.6 + wet * 0.5 + bub
    return normalize(convolve_stereo(x, reverb_ir(1.0, 0.3), 0.25), -2)


@reg('bio', 'bubble', 'Single small bubble blip.', ['water', 'pop'])
def bubble(seed=0):
    rng = np.random.default_rng(seed)
    m = int(0.12 * SR)
    tt = np.arange(m) / SR
    f0 = rng.uniform(500, 1400)
    f = f0 * (1 + 2.2 * tt / tt[-1])
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(m, 0.03, attack=0.001)
    return st(normalize(x, -6))


@reg('bio', 'sparkle_o2', 'Soft glassy sparkle for oxygen particles arriving.', ['magic', 'reveal'])
def sparkle_o2(dur=2.5):
    n = int(dur * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(41)
    for k in range(26):
        i = int(rng.uniform(0, dur - 0.6) * SR)
        f = rng.choice([1760, 1975.5, 2349.3, 2637, 2960, 3520])
        b = fm_bell(f, 0.6, ratio=2.01, index=1.2, decay=0.25) * rng.uniform(0.15, 0.4)
        out[i:i + len(b)] += b
    y = convolve_stereo(out, reverb_ir(2.0, 0.6, damp=9000), 0.45)
    return normalize(fade(y, 0.05, 0.4), -6)


@reg('bio', 'creature_presence', 'Huge presence arriving: sub swell + breathy low texture (no voice).', ['tension', 'reveal'])
def creature_presence(dur=3.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    swell = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.5
    sub = np.sin(2 * np.pi * 38 * tt) * 0.7
    tex = bandpass(noise(n, 'pink', 51), 60, 400) * 0.6
    x = (sub + tex) * swell
    return normalize(convolve_stereo(x, reverb_ir(2.5, 0.8, damp=900), 0.4), -3)


# ------------------------------------------------------------------ MOVEMENT
@reg('movement', 'whoosh_short', 'Fast short whoosh (0.5 s).', ['whoosh', 'transition'])
def whoosh_short():
    return whoosh(0.5)


@reg('movement', 'whoosh_long', 'Slow big whoosh (1.4 s).', ['whoosh'])
def whoosh_long():
    return whoosh(1.4)


def whoosh(dur, seed=61):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    sh = np.sin(np.pi * tt / dur) ** 2
    x = sweep_filter(noise(n, 'pink', seed), 300, 3500, kind='bandpass', q=1.5) * sh
    y = np.stack([x * np.linspace(1.2, 0.4, n), x * np.linspace(0.4, 1.2, n)], 1)
    return normalize(y, -2)


@reg('movement', 'impact_soft', 'Soft body/cushion impact.', ['impact'])
def impact_soft():
    m = int(0.5 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * np.cumsum(90 * (1 + np.exp(-tt / 0.02))) / SR) * env_exp(m, 0.08) + lowpass(noise(m, 'pink', 71), 900) * env_exp(m, 0.03)
    return st(normalize(x, -2))


@reg('movement', 'impact_heavy', 'Heavy cinematic impact with tail.', ['impact', 'hit'])
def impact_heavy():
    m = int(2.0 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * np.cumsum(42 * (1 + 3 * np.exp(-tt / 0.04))) / SR) * env_exp(m, 0.45)
    x += highpass(noise(m, 'white', 72), 1500) * env_exp(m, 0.02) * 0.6
    x = soft_sat(x, 2.5)
    return normalize(convolve_stereo(x, reverb_ir(2.5, 0.9, damp=3000), 0.3), -1)


@reg('movement', 'footstep_soft', 'Sneaker footstep on a soft floor.', ['footstep'])
def footstep_soft(seed=0):
    m = int(0.25 * SR)
    x = bandpass(noise(m, 'pink', 80 + seed), 120, 2500) * env_exp(m, 0.03) + np.sin(2 * np.pi * 70 * np.arange(m) / SR) * env_exp(m, 0.04) * 0.5
    return st(normalize(x, -4))


@reg('movement', 'footstep_hard', 'Hard-shoe footstep on tile.', ['footstep'])
def footstep_hard(seed=0):
    m = int(0.25 * SR)
    x = highpass(noise(m, 'white', 90 + seed), 800) * env_exp(m, 0.012) + bandpass(noise(m, 'pink', 91), 200, 1200) * env_exp(m, 0.03) * 0.6
    return st(normalize(x, -4))


@reg('movement', 'cloth_rustle', 'Clothing movement rustle.', ['foley'])
def cloth_rustle():
    m = int(0.6 * SR)
    tt = np.arange(m) / SR
    x = bandpass(noise(m, 'white', 101), 1500, 7000) * (np.sin(np.pi * tt / tt[-1]) ** 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 9 * tt))
    return st(normalize(x, -10))


@reg('movement', 'object_slide', 'Object sliding/scraping on a surface.', ['foley'])
def object_slide():
    m = int(0.9 * SR)
    tt = np.arange(m) / SR
    x = bandpass(noise(m, 'pink', 111), 400, 3000) * np.sin(np.pi * tt / tt[-1]) * (0.7 + 0.3 * np.sin(2 * np.pi * 23 * tt))
    return st(normalize(x, -6))


@reg('movement', 'mechanical_servo', 'Small mechanical servo whirr.', ['mechanical'])
def mechanical_servo():
    m = int(0.8 * SR)
    tt = np.arange(m) / SR
    f = 300 + 500 * np.sin(np.pi * tt / tt[-1])
    x = (square(f, 0.8) * 0.3 + saw(f * 2, 0.8) * 0.2) * env_adsr(m, 0.03, 0.1, 0.8, 0.1)
    return st(normalize(lowpass(x, 3000), -8))


# ------------------------------------------------------------------ REACTIONS
@reg('reactions', 'pop', 'Cartoon pop.', ['pop', 'comedy'])
def pop():
    m = int(0.15 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * np.cumsum(900 * np.exp(-tt / 0.03) + 200) / SR) * env_exp(m, 0.03)
    return st(normalize(x, -3))


@reg('reactions', 'surprise_sting', 'Short rising surprise sting (orchestral-ish stab).', ['surprise'])
def surprise_sting():
    m = int(1.2 * SR)
    x = np.zeros(m)
    for f in (392, 493.9, 587.3, 784):
        x += saw(f * (1 + 0.003 * np.random.default_rng(int(f)).standard_normal()), 1.2) * 0.25
    x = sweep_filter(x, 800, 6000) * env_adsr(m, 0.005, 0.2, 0.4, 0.8)
    return normalize(convolve_stereo(x, reverb_ir(1.8, 0.6), 0.35), -3)


@reg('reactions', 'comedic_boing', 'Comedic boing (springy).', ['comedy'])
def comedic_boing():
    m = int(0.7 * SR)
    tt = np.arange(m) / SR
    f = 220 * (1 + 0.6 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt / 0.25))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(m, 0.25)
    return st(normalize(x, -4))


@reg('reactions', 'slide_whistle_down', 'Comedic slide whistle falling.', ['comedy', 'fall'])
def slide_whistle_down():
    m = int(0.9 * SR)
    tt = np.arange(m) / SR
    f = 1400 * (0.35 ** (tt / tt[-1]))
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.01 * np.sin(2 * np.pi * 6 * tt))) / SR) * env_adsr(m, 0.02, 0.05, 0.9, 0.15)
    return st(normalize(x + 0.05 * noise(m, 'white', 1) * env_adsr(m, 0.02, 0.05, 0.9, 0.15), -6))


@reg('reactions', 'dramatic_hit', 'Dramatic low hit with metallic shimmer (braam-like).', ['hit', 'drama'])
def dramatic_hit():
    m = int(3.0 * SR)
    x = np.zeros(m)
    for f, a in ((55, 1.0), (55 * 1.5, 0.5), (110, 0.6), (110 * 1.19, 0.35)):
        x += saw(f, 3.0) * a
    x = lowpass(x, 900) * env_adsr(m, 0.01, 0.4, 0.5, 2.0)
    ih = impact_heavy()[:, 0]
    x = soft_sat(x, 2.0)
    x[:len(ih)] += ih[:m] * 0.6
    return normalize(convolve_stereo(x, reverb_ir(3.0, 1.0, damp=2500), 0.35), -1)


@reg('reactions', 'tension_riser', 'Rising tension (4 s): noise + pitch rise + tremolo.', ['riser', 'tension'])
def tension_riser(dur=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 110 * (4 ** (tt / dur))
    x = saw(f, dur) * 0.3 + saw(f * 1.01, dur) * 0.3
    x = sweep_filter(x, 300, 6000) + sweep_filter(noise(n, 'white', 121), 400, 9000, kind='highpass') * 0.3
    x *= (tt / dur) ** 1.5 * (0.7 + 0.3 * np.sin(2 * np.pi * (4 + 12 * tt / dur) * tt))
    return normalize(convolve_stereo(x, reverb_ir(2.0, 0.6), 0.3), -2)


@reg('reactions', 'fall_crash', 'Falling whistle into a crash.', ['fall', 'crash'])
def fall_crash():
    a = slide_whistle_down()[:, 0]
    m = int(1.5 * SR)
    crash = highpass(noise(m, 'white', 131), 400) * env_exp(m, 0.35)
    ih = impact_heavy()[:m, 0]
    crash[:len(ih)] += ih * 0.5
    x = np.concatenate([a, crash])
    return normalize(st(x), -2)


# ------------------------------------------------------------------ ENVIRONMENT
@reg('environment', 'door_creak_slam', 'Wooden door creak then slam.', ['door'])
def door_creak_slam():
    m = int(1.0 * SR)
    tt = np.arange(m) / SR
    f = 180 + 120 * np.sin(2 * np.pi * 0.7 * tt)
    creak = bandpass(square(f, 1.0, duty=0.05), 300, 2500) * 0.5
    slam = impact_heavy()[:int(0.8 * SR), 0]
    return normalize(st(np.concatenate([creak, slam])), -2)


@reg('environment', 'button_click', 'Plastic button click.', ['ui', 'click'])
def button_click():
    m = int(0.06 * SR)
    x = highpass(noise(m, 'white', 141), 2000) * env_exp(m, 0.004) + np.sin(2 * np.pi * 2200 * np.arange(m) / SR) * env_exp(m, 0.006) * 0.4
    return st(normalize(x, -6))


@reg('environment', 'vehicle_passby', 'Car pass-by with doppler (4 s).', ['vehicle'])
def vehicle_passby(dur=4.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    rel = (tt - dur / 2) * 15
    dop = 1 - 0.12 * np.tanh(rel / 6)
    eng = saw(70 * dop, dur) * 0.5 + bandpass(noise(n, 'pink', 151), 100, 1200) * 0.6
    amp = 1 / (1 + (rel / 8) ** 2)
    x = lowpass(eng, 2500) * amp
    p = np.tanh(rel / 10)
    y = np.stack([x * (1 - p) / 2, x * (1 + p) / 2], 1)
    return normalize(y, -3)


@reg('environment', 'water_flow', 'Running water / stream (6 s loop).', ['water'])
def water_flow(dur=6.0):
    n = int(dur * SR)
    x = bandpass(noise(n, 'white', 161), 400, 6000) * 0.5
    rng = np.random.default_rng(162)
    for _ in range(int(dur * 20)):
        i = rng.integers(0, n - 6000)
        x[i:i + 5760] += bubble(rng.integers(0, 999))[:5760, 0] * rng.uniform(0.05, 0.2)
    return normalize(fade(st(x), 0.3, 0.3), -8)


@reg('environment', 'glass_clink', 'Glass clink.', ['glass'])
def glass_clink():
    x = fm_bell(2630, 1.0, ratio=2.76, index=1.5, decay=0.35) + fm_bell(4100, 1.0, ratio=1.41, index=0.8, decay=0.2) * 0.5
    return st(normalize(x, -4))


@reg('environment', 'glass_shatter', 'Glass shatter.', ['glass', 'crash'])
def glass_shatter():
    m = int(1.5 * SR)
    x = highpass(noise(m, 'white', 171), 2500) * env_exp(m, 0.25)
    rng = np.random.default_rng(172)
    for _ in range(40):
        i = rng.integers(0, int(0.8 * SR))
        b = fm_bell(rng.uniform(2500, 7000), 0.3, ratio=2.3, index=1, decay=0.08)
        x[i:i + len(b)] += b * rng.uniform(0.1, 0.4)
    return normalize(convolve_stereo(x, reverb_ir(1.2, 0.4), 0.2), -2)


@reg('environment', 'electronic_beep', 'Device beep (two-tone).', ['electronic', 'ui'])
def electronic_beep():
    a = sine(1320, 0.09) * env_adsr(int(0.09 * SR), 0.002, 0.01, 0.9, 0.02)
    b = sine(1760, 0.12) * env_adsr(int(0.12 * SR), 0.002, 0.01, 0.9, 0.03)
    return st(normalize(np.concatenate([a, np.zeros(int(0.04 * SR)), b]), -8))


@reg('environment', 'electronic_glitch', 'Digital glitch burst.', ['electronic'])
def electronic_glitch():
    m = int(0.5 * SR)
    rng = np.random.default_rng(181)
    x = np.zeros(m)
    for i in range(0, m, 1200):
        f = rng.choice([200, 400, 800, 1600, 3200])
        x[i:i + 1200] = square(f, 1200 / SR, duty=rng.uniform(0.1, 0.5)) * rng.uniform(0.2, 1.0)
    return st(normalize(x * env_adsr(m, 0.005, 0.1, 0.6, 0.1), -8))


@reg('environment', 'machinery_hum', 'Machinery hum loop (6 s).', ['machinery'])
def machinery_hum(dur=6.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tt) * a for f, a in ((60, 1), (120, 0.6), (180, 0.3), (240, 0.2)))
    x += bandpass(noise(n, 'pink', 191), 200, 800) * 0.3
    x *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.5 * tt)
    return normalize(fade(st(x), 0.3, 0.3), -10)


# ------------------------------------------------------------------ TRANSITIONS
@reg('transitions', 'swish', 'Quick swish for cuts (0.3 s).', ['transition'])
def swish():
    return whoosh(0.3, seed=201)


@reg('transitions', 'riser_2s', 'Short 2 s riser into a cut.', ['riser'])
def riser_2s():
    return tension_riser(2.0)


@reg('transitions', 'downlifter', 'Downlifter (2 s) after a hit.', ['downlifter'])
def downlifter(dur=2.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 880 * (0.1 ** (tt / dur))
    x = saw(f, dur) * 0.3 + sweep_filter(noise(n, 'white', 211), 8000, 200, kind='lowpass') * 0.5
    x *= (1 - tt / dur) ** 1.2
    return normalize(convolve_stereo(x, reverb_ir(2.0, 0.6), 0.3), -3)


@reg('transitions', 'bass_impact', 'Sub-bass drop impact.', ['impact', 'sub'])
def bass_impact():
    m = int(2.0 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-tt / 0.06)) / SR) * env_exp(m, 0.7)
    return st(normalize(soft_sat(x, 1.8), -1))


@reg('transitions', 'short_transition', 'Short tonal transition blip + air (0.6 s).', ['transition'])
def short_transition():
    m = int(0.6 * SR)
    tt = np.arange(m) / SR
    x = np.sin(2 * np.pi * np.cumsum(600 + 900 * tt / tt[-1]) / SR) * env_adsr(m, 0.01, 0.1, 0.5, 0.3) * 0.5 + whoosh(0.6, 221)[:, 0] * 0.6
    return st(normalize(x, -4))


# ------------------------------------------------------------------ AMBIENCE (AUDIO/ambience)
@reg('ambience', 'wind', 'Wind (20 s loop).', ['outdoor'])
def wind(dur=20.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    gust = 0.5 + 0.5 * lowpass(noise(n, 'white', 301), 0.5) / 0.02
    gust = np.clip(0.4 + 0.6 * (gust - gust.min()) / (np.ptp(gust) + 1e-9), 0, 1)
    x = bandpass(noise(n, 'pink', 302), 150, 1800) * gust
    return normalize(fade(np.stack([x, bandpass(noise(n, 'pink', 303), 150, 1800) * gust], 1), 1, 1), -8)


@reg('ambience', 'rain', 'Steady rain (20 s loop).', ['outdoor', 'weather'])
def rain(dur=20.0):
    n = int(dur * SR)
    x = highpass(noise(n, 'pink', 311), 800) * 0.4
    rng = np.random.default_rng(312)
    for _ in range(int(dur * 400)):
        i = rng.integers(0, n - 300)
        x[i:i + 200] += highpass(rng.standard_normal(200), 2000) * np.exp(-np.arange(200) / 30) * rng.uniform(0.05, 0.3)
    return normalize(fade(np.stack([x, np.roll(x, 777)], 1), 1, 1), -8)


@reg('ambience', 'city', 'City ambience: distant traffic bed + occasional pass-bys (20 s).', ['urban'])
def city(dur=20.0):
    n = int(dur * SR)
    x = st(lowpass(noise(n, 'brown', 321), 400) * 0.6 + bandpass(noise(n, 'pink', 322), 200, 2000) * 0.15)
    for t0 in (2.0, 9.0, 14.5):
        v = vehicle_passby(4.0) * 0.4
        i = int(t0 * SR)
        x[i:i + len(v)] += v[:max(0, min(len(v), n - i))]
    return normalize(fade(x, 1, 1), -8)


@reg('ambience', 'room_tone', 'Quiet interior room tone (15 s).', ['interior'])
def room_tone(dur=15.0):
    n = int(dur * SR)
    x = lowpass(noise(n, 'pink', 331), 1200) * 0.3 + np.sin(2 * np.pi * 60 * np.arange(n) / SR) * 0.01
    return normalize(fade(np.stack([x, np.roll(x, 3331)], 1), 1, 1), -20)


@reg('ambience', 'nature', 'Nature: breeze + synthetic bird chirps + insects (20 s).', ['outdoor'])
def nature(dur=20.0):
    n = int(dur * SR)
    x = wind(dur)[:, 0] * 0.4
    rng = np.random.default_rng(341)
    for _ in range(int(dur * 1.2)):
        i = rng.integers(0, n - SR)
        m = int(rng.uniform(0.08, 0.2) * SR)
        tt = np.arange(m) / SR
        f = rng.uniform(2500, 4500) * (1 + 0.3 * np.sin(2 * np.pi * rng.uniform(10, 25) * tt))
        x[i:i + m] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]) * 0.15
    ins = bandpass(noise(n, 'white', 342), 5000, 7000) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * np.arange(n) / SR)) * 0.05
    return normalize(fade(np.stack([x + ins, x * 0.9 + np.roll(ins, 999)], 1), 1, 1), -10)


@reg('ambience', 'crowd', 'Indistinct crowd murmur (synthetic babble, 15 s).', ['crowd'])
def crowd(dur=15.0):
    n = int(dur * SR)
    x = np.zeros(n)
    rng = np.random.default_rng(351)
    for v in range(14):
        f0 = rng.uniform(100, 230)
        tt = np.arange(n) / SR
        syl = (np.sin(2 * np.pi * rng.uniform(3, 6) * tt + rng.uniform(0, 6)) > 0.2).astype(float)
        syl = lowpass(syl, 20)
        src = saw(f0 * (1 + 0.05 * np.sin(2 * np.pi * 0.7 * tt + v)), dur)
        form = bandpass(src, rng.uniform(400, 900), rng.uniform(1200, 2600))
        x += form * syl * rng.uniform(0.3, 1.0)
    x = lowpass(x, 3000)
    return normalize(fade(convolve_stereo(x, reverb_ir(1.5, 0.5), 0.4), 1, 1), -12)


def main():
    root = sys.argv[1]
    manifest = []
    for (cat, name), (fn, desc, tags) in LIB.items():
        y = fn()
        y = np.asarray(y, dtype=np.float32)
        if y.ndim == 1:
            y = np.stack([y, y], 1)
        d = os.path.join(root, 'ambience') if cat == 'ambience' else os.path.join(root, 'sound_effects', cat)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, name + '.flac')
        sf.write(p, y, SR, subtype='PCM_24')
        manifest.append({'file': os.path.relpath(p, root), 'category': cat, 'name': name, 'description': desc,
                         'tags': tags, 'duration_s': round(len(y) / SR, 2), 'sample_rate': SR,
                         'licence': 'Original procedural synthesis by this studio (PIPELINE/audio/sfx_synth.py). '
                                    'No third-party audio. Free for monetised use.'})
        print('SFX', cat, name, round(len(y) / SR, 2))
    json.dump(manifest, open(os.path.join(root, 'sound_effects', 'LIBRARY.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
