#!/usr/bin/env python3
"""Comedy SFX pack (all synthesised -> original, licence-free).
    /opt/tools/tts312/bin/python PIPELINE/audio/sfx_comedy.py AUDIO
Writes AUDIO/sound_effects/comedy/*.flac and merges entries into LIBRARY.json."""
import json, os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dsp import *  # noqa

LIB = {}
def reg(name, desc):
    def d(fn):
        LIB[name] = (fn, desc); return fn
    return d


def fart(dur=0.8, f0=95, f1=70, flutter=14, wet=0.2, breath=0.25, formant=(350, 1100), seed=0, wobble=0.12, tail=0.15):
    """Physical-ish fart: jittery pulse train (sphincter flutter) through a soft formant."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    u = tt / dur
    f = (f0 + (f1 - f0) * u) * (1 + wobble * np.sin(2 * np.pi * (2.5 + 3 * rng.random()) * tt + rng.random() * 6))
    f *= 1 + 0.06 * lowpass(rng.standard_normal(n), 40) * 8
    ph = np.cumsum(f) / SR
    pulse = (np.sin(2 * np.pi * ph) > 0.55 - 0.3 * rng.random()).astype(float) - 0.3
    pulse = lowpass(pulse, 2600)
    am = 0.65 + 0.35 * np.sin(2 * np.pi * flutter * tt + rng.random() * 6) ** 2
    env = env_adsr(n, 0.015, 0.05, 0.85, tail)
    body = bandpass(pulse, formant[0] * 0.3, formant[1]) * am * env
    br = bandpass(noise(n, 'pink', seed + 1), 120, 1800) * env * breath
    x = body + br
    if wet > 0:
        bub = np.zeros(n)
        for _ in range(int(dur * 22 * wet)):
            i = rng.integers(0, max(1, n - 3000))
            m = 2400
            ft = rng.uniform(250, 900) * (1 + 1.5 * np.arange(m) / m)
            bub[i:i + m] += np.sin(2 * np.pi * np.cumsum(ft) / SR) * np.exp(-np.arange(m) / (0.008 * SR)) * rng.uniform(0.2, 0.6)
        x = x + bub * env * wet
    x = soft_sat(x * 2.2, 1.6)
    return normalize(x, -3)


@reg('fart_tiny_pfft', 'Tiny innocent "pfft": short breathy puff with a lip pop.')
def tiny():
    n = int(0.32 * SR)
    tt = np.arange(n) / SR
    x = bandpass(noise(n, 'pink', 5), 300, 2500) * env_adsr(n, 0.005, 0.05, 0.4, 0.15) * 0.8
    x += fart(0.22, 140, 120, 30, 0.0, 0.3, seed=6)[:n] * 0.5 if n <= int(0.22 * SR) else np.pad(fart(0.22, 140, 120, 30, 0.0, 0.3, seed=6), (0, n - int(0.22 * SR))) * 0.5
    return normalize(x, -6)

@reg('fart_squeaker', 'High rising squeaker (0.6 s).')
def squeaker(): return fart(0.6, 190, 290, 20, 0.0, 0.15, (500, 2400), seed=11, wobble=0.06, tail=0.08)

@reg('fart_trumpet', 'Long brassy trumpet with wobble (1.3 s).')
def trumpet(): return fart(1.3, 110, 85, 9, 0.1, 0.2, (300, 1300), seed=12, wobble=0.18)

@reg('fart_rumble', 'Deep rumbling bass fart (1.0 s).')
def rumble(): return fart(1.0, 52, 44, 7, 0.15, 0.35, (180, 700), seed=13, wobble=0.1)

@reg('fart_wet', 'Wet bubbly one (0.8 s).')
def wet(): return fart(0.8, 85, 70, 16, 0.9, 0.3, (300, 1200), seed=14)

@reg('fart_machinegun', 'Rapid-fire staccato bursts (1.0 s).')
def machinegun():
    out = np.zeros(int(1.0 * SR))
    for k in range(7):
        b = fart(0.11, 120 - k * 6, 110 - k * 6, 30, 0.0, 0.2, seed=20 + k, tail=0.03)
        i = int(k * 0.13 * SR)
        out[i:i + len(b)] += b
    return normalize(out, -3)

@reg('fart_whine', 'Descending whiny deflation (1.4 s).')
def whine(): return fart(1.4, 240, 90, 22, 0.0, 0.15, (500, 2000), seed=15, wobble=0.05, tail=0.3)

@reg('fart_chorus', '8 billion at once: a layered chord of 7 different farts + crowd jolt (1.6 s).')
def chorus():
    n = int(1.6 * SR)
    out = np.zeros((n, 2))
    layers = [(squeaker(), -0.7, 0.00, -4), (trumpet(), 0.3, 0.02, -2), (rumble(), 0.0, 0.0, -1), (wet(), 0.6, 0.04, -5),
              (machinegun(), -0.4, 0.05, -7), (whine(), 0.8, 0.03, -8), (fart(1.1, 70, 60, 11, 0.3, 0.3, seed=31), -0.2, 0.01, -4)]
    for x, p, d, g in layers:
        i = int(d * SR)
        y = pan(x, p) * from_db(g)
        m = min(n - i, len(y))
        out[i:i + m] += y[:m]
    return normalize(convolve_stereo(out, reverb_ir(0.9, 0.25), 0.18), -1)

@reg('record_scratch', 'Vinyl record scratch (0.45 s).')
def scratch():
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    spd = np.sin(2 * np.pi * 3.2 * tt) * 1.6
    ph = np.cumsum(np.abs(spd) * 700) / SR
    tone = np.sin(2 * np.pi * ph) * 0.5 + bandpass(noise(n, 'white', 41), 800, 6000) * np.abs(spd) * 0.6
    tone = sweep_filter(tone, 5000, 900, kind='lowpass')
    return normalize(tone * env_adsr(n, 0.003, 0.05, 0.9, 0.08), -3)

def vowel_voice(f0, dur, formants, seed):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f0 * (1 + 0.03 * np.sin(2 * np.pi * 5 * tt + rng.random() * 6)) * (1 + 0.15 * np.sin(np.pi * tt / dur))
    src = saw(f, dur)
    out = np.zeros(n)
    for fc, bw, g in formants:
        out += bandpass(src, fc - bw / 2, fc + bw / 2) * g
    return out * env_adsr(n, 0.06, 0.1, 0.8, dur * 0.4)

@reg('crowd_gasp', 'Group gasp "HUH!" (0.7 s).')
def gasp():
    n = int(0.7 * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(3)
    for v in range(9):
        f0 = rng.uniform(110, 260)
        x = vowel_voice(f0, 0.5, [(800, 200, 1.0), (1250, 250, 0.6), (2600, 400, 0.3)], v)
        x += bandpass(noise(len(x), 'white', v), 1500, 6000) * env_adsr(len(x), 0.02, 0.1, 0.3, 0.2) * 0.4
        i = int(rng.uniform(0, 0.06) * SR)
        out[i:i + len(x)] += x[:n - i]
    return normalize(convolve_stereo(out, reverb_ir(1.0, 0.3), 0.25), -3)

@reg('crowd_eww', 'Group disgusted "EWWW" (1.0 s).')
def eww():
    n = int(1.0 * SR)
    out = np.zeros(n)
    rng = np.random.default_rng(4)
    for v in range(9):
        f0 = rng.uniform(120, 280)
        x = vowel_voice(f0, 0.9, [(300, 120, 1.0), (2200, 300, 0.5), (3000, 400, 0.2)], 10 + v)
        i = int(rng.uniform(0, 0.08) * SR)
        out[i:i + len(x)] += x[:n - i]
    return normalize(convolve_stereo(out, reverb_ir(1.2, 0.35), 0.25), -3)

@reg('elevator_ding', 'Elevator arrival chime (two tones).')
def ding():
    a = fm_bell(1318.5, 1.4, ratio=2.0, index=0.8, decay=0.6)
    b = fm_bell(1046.5, 1.6, ratio=2.0, index=0.8, decay=0.7)
    out = np.zeros(int(2.0 * SR)); out[:len(a)] += a; out[int(0.32 * SR):int(0.32 * SR) + len(b)] += b
    return normalize(convolve_stereo(out, reverb_ir(1.2, 0.4), 0.3), -6)

@reg('news_sting', 'Breaking-news sting: brass stabs + timpani (1.6 s).')
def news():
    n = int(1.6 * SR)
    out = np.zeros(n)
    for k, (t0, ch) in enumerate(((0.0, (220, 277.2, 329.6)), (0.18, (246.9, 311.1, 370)), (0.42, (293.7, 370, 440, 587.3)))):
        m = int(0.9 * SR)
        x = sum(saw(f, 0.9) + saw(f * 1.004, 0.9) for f in ch)
        x = sweep_filter(x, 4000, 1200) * env_adsr(m, 0.01, 0.15, 0.5, 0.5)
        i = int(t0 * SR); out[i:i + m] += x[:n - i] * 0.25
    tim = np.sin(2 * np.pi * np.cumsum(80 * (1 + np.exp(-np.arange(n) / SR / 0.05))) / SR) * env_exp(n, 0.4)
    out += tim * 0.8
    return normalize(convolve_stereo(soft_sat(out, 1.5), reverb_ir(1.5, 0.5), 0.3), -2)

@reg('dun_dun_dun', 'Dramatic "dun dun DUNNN" (2.0 s).')
def dundun():
    n = int(2.2 * SR)
    out = np.zeros(n)
    for t0, f, d in ((0.0, 98, 0.3), (0.35, 92.5, 0.3), (0.7, 82.4, 1.4)):
        m = int(d * SR) + int(0.5 * SR)
        x = sum(saw(f * k, m / SR) / k for k in (1, 2, 3)) + saw(f * 1.5, m / SR) * 0.4
        x = lowpass(x, 1400) * env_adsr(m, 0.01, 0.1, 0.8, 0.5)
        i = int(t0 * SR); out[i:i + m] += x[:n - i]
    return normalize(convolve_stereo(soft_sat(out, 2.0), reverb_ir(2.0, 0.7), 0.3), -2)

@reg('enhance_beep', 'Computer "enhance": zoom whoosh + data chirps + beep (0.6 s).')
def enhance():
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    whoosh = sweep_filter(noise(n, 'white', 51), 400, 7000, kind='bandpass', q=2) * np.sin(np.pi * tt / tt[-1]) * 0.6
    chirps = np.zeros(n)
    rng = np.random.default_rng(52)
    for k in range(10):
        i = int(k * 0.035 * SR); m = int(0.025 * SR)
        chirps[i:i + m] += square(rng.choice([1200, 1600, 2000, 2400]), m / SR, duty=0.5) * 0.25
    beep = np.zeros(n); m = int(0.12 * SR); beep[int(0.42 * SR):int(0.42 * SR) + m] = sine(1760, m / SR) * env_adsr(m, 0.005, 0.02, 0.9, 0.04) * 0.6
    return normalize(whoosh + lowpass(chirps, 5000) + beep, -4)

@reg('camera_snap', 'Freeze-frame shutter snap + whoosh (0.4 s).')
def snap():
    n = int(0.4 * SR)
    x = highpass(noise(n, 'white', 61), 2500) * env_exp(n, 0.012) + bandpass(noise(n, 'white', 62), 500, 3000) * env_exp(n, 0.04) * 0.6
    x[int(0.06 * SR):] += highpass(noise(n - int(0.06 * SR), 'white', 63), 3000) * env_exp(n - int(0.06 * SR), 0.01) * 0.7
    return normalize(x, -3)

@reg('vhs_rewind', 'Tape rewind squeal with wobble (1.0 s).')
def rewind():
    n = int(1.0 * SR)
    tt = np.arange(n) / SR
    f = 900 + 1800 * tt + 200 * np.sin(2 * np.pi * 17 * tt)
    x = saw(f, 1.0) * 0.25 + sweep_filter(noise(n, 'white', 71), 2000, 9000, kind='bandpass', q=3) * 0.5
    x *= 0.6 + 0.4 * (np.sin(2 * np.pi * 23 * tt) > 0)
    return normalize(lowpass(x, 9000) * env_adsr(n, 0.02, 0.05, 0.9, 0.05), -5)

@reg('whistle_innocent', 'Innocent whistled tune (2.4 s).')
def whistle():
    notes = [(784, 0.22), (988, 0.22), (1175, 0.34), (988, 0.2), (880, 0.22), (784, 0.5), (659, 0.3)]
    out = []
    for f, d in notes:
        m = int(d * SR); tt = np.arange(m) / SR
        x = np.sin(2 * np.pi * f * (1 + 0.012 * np.sin(2 * np.pi * 6 * tt)) * tt) * env_adsr(m, 0.03, 0.05, 0.85, 0.06)
        x += bandpass(noise(m, 'white', int(f)), f * 0.9, f * 1.2) * 0.12 * env_adsr(m, 0.03, 0.05, 0.85, 0.06)
        out.append(x)
    return normalize(convolve_stereo(np.concatenate(out), reverb_ir(1.0, 0.3), 0.2), -6)

@reg('sad_trombone', 'Wah-wah-wah-waaah (1.9 s).')
def trombone():
    out = []
    for f, d in ((233, 0.32), (220, 0.32), (207.7, 0.32), (196, 0.95)):
        m = int(d * SR); tt = np.arange(m) / SR
        vib = 1 + (0.025 * np.sin(2 * np.pi * 6 * tt) if d > 0.5 else 0)
        x = saw(f * vib, d) * 0.5 + saw(f * 2 * vib, d) * 0.15
        x = sweep_filter(x, 600, 1800, kind='lowpass') * env_adsr(m, 0.03, 0.05, 0.85, 0.12)
        out.append(x)
    return normalize(convolve_stereo(np.concatenate(out), reverb_ir(1.2, 0.4), 0.2), -4)

@reg('body_thud', 'Body falling on grass (0.5 s).')
def thud():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(70 * (1 + np.exp(-tt / 0.02))) / SR) * env_exp(n, 0.09)
    x += lowpass(noise(n, 'pink', 81), 900) * env_exp(n, 0.05) * 0.8
    return normalize(soft_sat(x, 1.5), -2)

@reg('tv_static_click', 'TV channel switch: click + static burst (0.3 s).')
def static():
    n = int(0.3 * SR)
    x = noise(n, 'white', 91) * env_exp(n, 0.08) * 0.6
    x[:200] += 1.0
    return normalize(highpass(x, 300), -6)

@reg('counter_ticks', 'Rapid number-counter ticks (0.6 s).')
def ticks():
    n = int(0.6 * SR); out = np.zeros(n)
    for k in range(18):
        i = int(k * 0.031 * SR); m = 600
        out[i:i + m] += sine(2600 + 40 * k, m / SR) * env_exp(m, 0.004)
    return normalize(out, -8)

@reg('positive_chime', 'Friendly "correct!" chime.')
def chime():
    out = np.zeros(int(1.0 * SR))
    for k, f in enumerate((1046.5, 1318.5, 1568)):
        b = fm_bell(f, 0.7, ratio=3.0, index=0.6, decay=0.3); i = int(k * 0.07 * SR); out[i:i + len(b)] += b
    return normalize(out, -6)

@reg('cartoon_tick', 'Tiny cartoon tick for eye twitches.')
def tick():
    m = int(0.06 * SR); return normalize(sine(2200, m / SR) * env_exp(m, 0.008), -10)

@reg('sweat_drip', 'Cartoon sweat drop "plip".')
def drip():
    m = int(0.18 * SR); tt = np.arange(m) / SR
    return normalize(np.sin(2 * np.pi * np.cumsum(1400 - 800 * tt / tt[-1]) / SR) * env_exp(m, 0.05), -8)



# ---------------------------------------------------------------- VIDEO_003 additions
@reg('cough_fit', 'Three dry coughs (1.1 s).')
def cough():
    n = int(1.1 * SR); out = np.zeros(n)
    for k, t0 in enumerate((0.0, 0.3, 0.6)):
        m = int(0.22 * SR); tt = np.arange(m) / SR
        x = bandpass(noise(m, 'white', 80 + k), 300, 2600) * env_exp(m, 0.06) * (1.0 - 0.15 * k)
        x += np.sin(2 * np.pi * (180 - 30 * k) * tt) * env_exp(m, 0.03) * 0.5
        i = int(t0 * SR); out[i:i + m] += x
    return normalize(convolve_stereo(out, reverb_ir(0.6, 0.15), 0.12), -4)

@reg('pill_rattle', 'Pill bottle shake (0.6 s).')
def rattle():
    n = int(0.6 * SR); out = np.zeros(n); rng = np.random.default_rng(91)
    for t0 in np.sort(rng.uniform(0, 0.5, 26)):
        m = int(0.02 * SR); i = int(t0 * SR)
        out[i:i + m] += highpass(noise(m, 'white', int(t0 * 1e4)), 2500) * env_exp(m, 0.004) * rng.uniform(0.3, 1)
    return normalize(out, -6)

@reg('cash_register', 'Ka-ching (0.9 s).')
def kaching():
    n = int(0.9 * SR); out = np.zeros(n)
    m = int(0.06 * SR); out[:m] += highpass(noise(m, 'white', 93), 1500) * env_exp(m, 0.01)
    b = fm_bell(2637, 0.8, ratio=2.0, index=1.2, decay=0.35) + fm_bell(3520, 0.8, ratio=2.0, index=1.0, decay=0.3) * 0.7
    out[int(0.08 * SR):int(0.08 * SR) + len(b)] += b[:n - int(0.08 * SR)] * 0.6
    return normalize(out, -5)

@reg('notif_pop', 'Social-app notification blip (0.25 s).')
def notif():
    n = int(0.25 * SR); out = np.zeros(n)
    for t0, f in ((0.0, 1318.5), (0.07, 1975.5)):
        m = int(0.12 * SR); i = int(t0 * SR)
        out[i:i + m] += sine(f, m / SR) * env_adsr(m, 0.003, 0.03, 0.5, 0.06) * 0.6
    return normalize(out, -6)

@reg('phone_buzz', 'Phone vibrate (0.5 s).')
def buzz():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    x = square(170, 0.5, duty=0.5) * (np.sin(2 * np.pi * 8 * tt) > -0.3)
    return normalize(lowpass(x, 900) * env_adsr(n, 0.01, 0.05, 0.9, 0.05), -8)

@reg('crowd_laugh', 'Small sitcom laugh (1.6 s).')
def laugh():
    n = int(1.6 * SR); out = np.zeros(n); rng = np.random.default_rng(97)
    for v in range(9):
        f0 = rng.uniform(140, 320); t0 = rng.uniform(0, 0.25)
        k = 0.0
        while t0 + k < 1.3:
            m = int(0.11 * SR); i = int((t0 + k) * SR)
            x = vowel_voice(f0 * rng.uniform(0.95, 1.08), m / SR, ((rng.uniform(600, 900), 120, 1.0), (rng.uniform(1100, 1500), 160, 0.5)), int(v * 100 + k * 10))
            out[i:i + len(x)] += x[:n - i] * env_adsr(len(x), 0.01, 0.03, 0.7, 0.04)[:n - i] * rng.uniform(0.4, 0.8) * (1 - (k / 1.4))
            k += rng.uniform(0.13, 0.19)
    return normalize(convolve_stereo(out, reverb_ir(1.2, 0.4), 0.3), -6)


# ---------------------------------------------------------------- VIDEO_004 additions
@reg('sneeze', 'Ah... CHOO! (1.0 s).')
def sneeze():
    n = int(1.0 * SR); out = np.zeros(n)
    a = vowel_voice(260, 0.35, ((750, 110, 1.0), (1200, 150, 0.4)), 301) * np.linspace(0.3, 1.0, int(0.35 * SR))
    out[:len(a)] += a * 0.5
    m = int(0.4 * SR); i = int(0.5 * SR)
    ch = bandpass(noise(m, 'white', 302), 1500, 7000) * env_exp(m, 0.12) + vowel_voice(300, m / SR, ((450, 120, 1.0), (900, 140, 0.4)), 303)[:m] * env_exp(m, 0.15) * 0.6
    out[i:i + m] += ch
    return normalize(out, -4)

@reg('scream_fall', 'Falling cartoon scream, pitch slides down (2.4 s).')
def scream():
    n = int(2.4 * SR); tt = np.arange(n) / SR
    f0 = 520 * np.exp(-tt * 0.35) * (1 + 0.03 * np.sin(2 * np.pi * 6 * tt))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    x = sum(np.sin(ph * k) / k for k in range(1, 8))
    x = bandpass(x, 400, 3500) + bandpass(noise(n, 'white', 311), 800, 4000) * 0.15
    return normalize(x * env_adsr(n, 0.05, 0.1, 0.9, 0.3), -5)

@reg('bonk', 'Hollow cartoon head bonk (0.5 s).')
def bonk():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(700 * np.exp(-tt * 3) + 300) / SR) * env_exp(n, 0.08)
    x += highpass(noise(n, 'white', 321), 2000) * env_exp(n, 0.006) * 0.6
    return normalize(x, -3)

@reg('air_float', 'Airy weightless shimmer bed (4 s).')
def airfloat():
    n = int(4.0 * SR); tt = np.arange(n) / SR
    x = sweep_filter(noise(n, 'pink', 331), 600, 2400, kind='bandpass', q=3) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.4 * tt))
    x += sum(np.sin(2 * np.pi * f * tt + f) for f in (880, 1320, 1760)) * 0.05 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * tt))
    return normalize(x * env_adsr(n, 0.6, 0.1, 1.0, 0.8), -10)

@reg('water_splash', 'Big water splash (1.2 s).')
def splash():
    n = int(1.2 * SR)
    x = bandpass(noise(n, 'white', 341), 300, 6000) * env_exp(n, 0.25) + lowpass(noise(n, 'brown', 342), 300) * env_exp(n, 0.15) * 1.5
    rng = np.random.default_rng(343)
    for t0 in rng.uniform(0.1, 1.0, 30):
        m = int(0.03 * SR); i = int(t0 * SR)
        x[i:i + m] += highpass(noise(m, 'white', int(t0 * 1e4)), 2500) * env_exp(m, 0.01) * rng.uniform(0.1, 0.4)
    return normalize(x, -4)


# ---------------------------------------------------------------- VIDEO_005 additions (toilet identities)
@reg('lid_slam', 'Porcelain toilet-lid SLAM: hard clack + body thump (0.6 s).')
def lid_slam():
    n = int(0.6 * SR); tt = np.arange(n) / SR
    clack = highpass(noise(n, 'white', 401), 1800) * env_exp(n, 0.012)
    ring = sum(np.sin(2 * np.pi * f * tt) * a for f, a in ((1870, 0.5), (2960, 0.3), (4410, 0.2))) * env_exp(n, 0.06)
    thump = np.sin(2 * np.pi * np.cumsum(140 * np.exp(-tt / 0.03) + 60) / SR) * env_exp(n, 0.08)
    return normalize(clack + ring * 0.4 + thump * 0.9, -2)

@reg('water_spray', 'Pressurised water spray hiss with splatter (0.8 s).')
def spray():
    n = int(0.8 * SR)
    x = bandpass(noise(n, 'white', 411), 1500, 9000) * env_adsr(n, 0.01, 0.1, 0.8, 0.25)
    x += bandpass(noise(n, 'pink', 412), 300, 2000) * env_adsr(n, 0.01, 0.1, 0.6, 0.25) * 0.5
    return normalize(x, -4)

@reg('flush_big', 'Violent self-flush: handle clunk, roaring swirl, gurgle tail (2.4 s).')
def flush():
    n = int(2.4 * SR); tt = np.arange(n) / SR
    clunk = np.zeros(n); m = int(0.05 * SR); clunk[:m] = highpass(noise(m, 'white', 421), 800) * env_exp(m, 0.01)
    swirl = sweep_filter(noise(n, 'pink', 422), 2500, 400, kind='bandpass', q=1.5) * (0.6 + 0.4 * np.sin(2 * np.pi * 5 * tt)) * env_adsr(n, 0.08, 0.2, 0.9, 0.9)
    gl = np.zeros(n)
    rng = np.random.default_rng(423)
    for t0 in rng.uniform(0.6, 2.2, 22):
        k = int(0.06 * SR); i = int(t0 * SR); f0 = rng.uniform(200, 600)
        gl[i:i + k] += np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f0 * 1.8, k)) / SR) * env_exp(k, 0.02) * 0.5
    return normalize(clunk * 0.8 + swirl + gl, -3)

@reg('toilet_grumble', 'Small toilet personality: grumpy wet gurgle-growl (0.9 s).')
def grumble():
    n = int(0.9 * SR); tt = np.arange(n) / SR
    f0 = 130 * (1 + 0.25 * np.sin(2 * np.pi * 7 * tt))
    x = vowel_voice(150, 0.9, ((500, 180, 1.0), (900, 200, 0.5)), 431)[:n] * (0.7 + 0.3 * np.sign(np.sin(2 * np.pi * 13 * tt)))
    x += lowpass(noise(n, 'brown', 432), 400) * 0.6 * np.abs(np.sin(2 * np.pi * 9 * tt))
    return normalize(x * env_adsr(n, 0.05, 0.1, 0.8, 0.25), -5)

@reg('giant_roar', 'Giant toilet: deep porcelain roar with flushing gargle (2.0 s).')
def roar():
    n = int(2.0 * SR); tt = np.arange(n) / SR
    f0 = 70 * (1 + 0.1 * np.sin(2 * np.pi * 4 * tt))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    x = sum(np.sin(ph * k) / k ** 0.7 for k in range(1, 14))
    x = bandpass(x, 60, 2500) + bandpass(noise(n, 'pink', 441), 200, 1800) * 0.8 * np.abs(np.sin(2 * np.pi * 11 * tt))
    x += sweep_filter(noise(n, 'white', 442), 3000, 500, kind='bandpass', q=2) * 0.3
    return normalize(soft_sat(x * 2.0, 2.0) * env_adsr(n, 0.15, 0.2, 0.9, 0.6), -2)

@reg('tp_thump', 'Toilet-paper missile launch: hollow thoomp + whoosh (0.5 s).')
def tpthump():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(220 * np.exp(-tt / 0.05) + 80) / SR) * env_exp(n, 0.05)
    x += sweep_filter(noise(n, 'white', 451), 500, 4000, kind='bandpass', q=2) * env_adsr(n, 0.02, 0.1, 0.5, 0.2) * 0.5
    return normalize(x, -4)

@reg('drain_gurgle', 'Bathtub drain wakes up: slow sinister gurgle (1.6 s).')
def gurgle():
    n = int(1.6 * SR); out = np.zeros(n); rng = np.random.default_rng(461)
    for t0 in np.sort(rng.uniform(0, 1.4, 14)):
        k = int(rng.uniform(0.08, 0.16) * SR); i = int(t0 * SR); f0 = rng.uniform(90, 200)
        b = np.sin(2 * np.pi * np.cumsum(np.linspace(f0, f0 * 2.2, k)) / SR) * env_adsr(k, 0.01, 0.03, 0.6, 0.05)
        out[i:i + k] += b[:n - i]
    out += lowpass(noise(n, 'brown', 462), 250) * 0.3
    return normalize(convolve_stereo(out, reverb_ir(0.8, 0.3), 0.3), -4)

# ---------------------------------------------------------------- suspense pack (VIDEO_006 "The 13th Floor")
@reg('elevator_ding_eerie', 'Elevator arrival ding, single low bell in a big dark shaft (2.4 s).')
def ding_eerie():
    a = fm_bell(987.8, 2.2, ratio=2.0, index=0.6, decay=0.9) + 0.35 * fm_bell(493.9, 2.2, ratio=2.0, index=0.3, decay=1.1)
    out = np.zeros(int(2.4 * SR)); out[:len(a)] += a
    return normalize(convolve_stereo(out, reverb_ir(2.2, 0.55, seed=601), 0.45), -5)

@reg('flicker_buzz', 'Fluorescent light flicker: mains buzz chopped on/off with arcing ticks (0.7 s).')
def flicker_buzz():
    n = int(0.7 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(602)
    x = soft_sat(np.sin(2 * np.pi * 120 * tt) + 0.5 * np.sin(2 * np.pi * 240 * tt) + 0.3 * np.sin(2 * np.pi * 360 * tt), 3.0)
    gate = np.zeros(n)
    t = 0.0
    while t < 0.7:
        d = rng.uniform(0.02, 0.09); on = rng.random() < 0.6
        gate[int(t * SR):int((t + d) * SR)] = 1.0 if on else 0.05
        t += d
    gate = lowpass(gate, 300)
    x = x * gate + highpass(noise(n, 'white', 603), 2000) * (np.abs(np.diff(gate, prepend=0)) > 0.02) * 0.8
    return normalize(x * env_adsr(n, 0.005, 0.1, 0.9, 0.08), -8)

@reg('elev_door_slide', 'Elevator doors sliding: motor whirr + rumble on the track (1.1 s).')
def elev_door_slide():
    n = int(1.1 * SR); tt = np.arange(n) / SR
    whirr = np.sin(2 * np.pi * np.cumsum(180 + 60 * np.sin(np.pi * tt / 1.1)) / SR) * 0.3
    rum = lowpass(noise(n, 'brown', 604), 400) * 1.2 + bandpass(noise(n, 'pink', 605), 800, 3000) * 0.25
    x = (whirr + rum) * env_adsr(n, 0.15, 0.2, 0.8, 0.3)
    return normalize(convolve_stereo(x, reverb_ir(0.6, 0.3, seed=606), 0.2), -8)

def _metal(dur, f0s, seed, decay=0.5):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n); rng = np.random.default_rng(seed)
    for f in f0s:
        x += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * env_exp(n, decay * rng.uniform(0.6, 1.0)) * rng.uniform(0.3, 1.0)
    x += lowpass(noise(n, 'pink', seed + 1), 2500) * env_exp(n, 0.04) * 2.0
    x += np.sin(2 * np.pi * np.cumsum(60 * (1 + 2 * np.exp(-tt / 0.03))) / SR) * env_exp(n, 0.12) * 1.5
    return x

@reg('metal_slam', 'Heavy steel elevator doors slamming shut, ringing tail (1.6 s).')
def metal_slam():
    x = _metal(1.6, [212, 347, 529, 811, 1230], 607, 0.6)
    return normalize(convolve_stereo(soft_sat(x, 1.8), reverb_ir(1.6, 0.5, seed=608), 0.35), -1)

@reg('metal_bang', 'Fist pounding on steel elevator doors (0.5 s).')
def metal_bang():
    x = _metal(0.5, [180, 296, 455, 700], 609, 0.18)
    return normalize(convolve_stereo(soft_sat(x, 2.0), reverb_ir(0.8, 0.4, seed=610), 0.3), -2)

@reg('footstep_echo', 'Slow footstep on an old carpet runner in an empty hallway, long echo (1.0 s).')
def footstep_echo():
    n = int(0.25 * SR)
    x = bandpass(noise(n, 'pink', 611), 100, 1800) * env_exp(n, 0.035) + np.sin(2 * np.pi * 65 * np.arange(n) / SR) * env_exp(n, 0.05) * 0.6
    out = np.zeros(int(1.0 * SR)); out[:n] += x
    return normalize(convolve_stereo(out, reverb_ir(1.0, 0.5, seed=612, predelay=0.04), 0.4), -6)

@reg('horror_sting', 'Photo reveal: dissonant string cluster stab + low boom (2.2 s).')
def horror_sting():
    n = int(2.2 * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for k, f in enumerate([466.2, 493.9, 523.3, 987.8, 1046.5]):
        vib = 1 + 0.004 * np.sin(2 * np.pi * (5.5 + k * 0.3) * tt)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        x += (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph)) * 0.25
    x = x * env_adsr(n, 0.008, 0.3, 0.45, 1.2)
    x += np.sin(2 * np.pi * np.cumsum(45 * (1 + np.exp(-tt / 0.05))) / SR) * env_exp(n, 0.5) * 1.2
    return normalize(convolve_stereo(highpass(x, 30), reverb_ir(2.0, 0.55, seed=613), 0.4), -2)

@reg('creak_long', 'Old wooden apartment door creaking slowly open (1.8 s).')
def creak_long():
    n = int(1.8 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(614)
    rate = 18 + 22 * np.sin(np.pi * tt / 1.8) + 6 * np.sin(2 * np.pi * 1.3 * tt)
    ph = np.cumsum(rate) / SR
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * rng.uniform(0.5, 1.0, n)
    x = sum(bandpass(pulses, f * 0.85, f * 1.15) * g for f, g in ((520, 1.0), (1150, 0.6), (2300, 0.3)))
    x = x * env_adsr(n, 0.1, 0.2, 0.9, 0.3)
    return normalize(convolve_stereo(x, reverb_ir(1.2, 0.45, seed=615), 0.35), -6)

@reg('tv_static_bed', 'Old TV static, room-filtered, loopable (6 s).')
def tv_static_bed():
    n = int(6.0 * SR)
    x = bandpass(noise(n, 'white', 616), 400, 6000) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.7 * np.arange(n) / SR))
    x += 0.15 * np.sin(2 * np.pi * 15734 / 4 * np.arange(n) / SR)
    return normalize(fade(x, 0.05, 0.05), -10)

@reg('power_cut', 'Lights out: breaker thunk + electrical power-down whine (1.0 s).')
def power_cut():
    n = int(1.0 * SR); tt = np.arange(n) / SR
    thunk = np.sin(2 * np.pi * np.cumsum(80 * (1 + np.exp(-tt / 0.02))) / SR) * env_exp(n, 0.08) * 1.4
    whine = np.sin(2 * np.pi * np.cumsum(240 * np.exp(-tt / 0.35) + 40) / SR) * env_exp(n, 0.35) * 0.4
    snap = highpass(noise(n, 'white', 617), 1500) * env_exp(n, 0.01) * 0.9
    return normalize(soft_sat(thunk + whine + snap, 1.5), -2)

@reg('glass_swell', 'Restrained high glassy cluster swelling in, then cut (1.6 s).')
def glass_swell():
    n = int(1.6 * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for f in (1760.0, 1864.7, 2637.0, 2793.8):
        x += np.sin(2 * np.pi * f * tt) * 0.25 * (1 + 0.3 * np.sin(2 * np.pi * 6.2 * tt))
    x *= np.clip(tt / 1.4, 0, 1) ** 2 * env_adsr(n, 0.001, 0.1, 1.0, 0.04)
    return normalize(convolve_stereo(x, reverb_ir(1.4, 0.5, seed=618), 0.4), -8)

@reg('cable_hum', 'Elevator car moving: low motor hum + cable creaks (6 s).')
def cable_hum():
    n = int(6.0 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(619)
    x = (np.sin(2 * np.pi * 50 * tt) + 0.5 * np.sin(2 * np.pi * 100 * tt) + 0.25 * np.sin(2 * np.pi * 150 * tt)) * 0.4
    x += lowpass(noise(n, 'brown', 620), 200) * 0.8
    for t0 in rng.uniform(0.3, 5.5, 5):
        k = int(0.25 * SR); i = int(t0 * SR)
        c = bandpass(noise(k, 'white', int(t0 * 100)), 700, 1400) * env_adsr(k, 0.05, 0.1, 0.5, 0.1) * 0.25
        x[i:i + k] += c[:n - i]
    return normalize(fade(x, 0.2, 0.2), -10)


# ---------------------------------------------------------------- horror pack 2 (VIDEO_007 "After Hours")
@reg('snore', 'Deep sleepy snore: in-breath rattle + out-breath (2.2 s).')
def snore():
    n = int(2.2 * SR); tt = np.arange(n) / SR
    inh = (np.sin(2 * np.pi * 38 * tt) > 0).astype(float) * bandpass(noise(n, 'pink', 701), 150, 900) * env_adsr(n, 0.4, 0.2, 0.8, 0.5)
    inh *= (tt < 1.2)
    exh = bandpass(noise(n, 'pink', 702), 200, 1400) * np.clip((tt - 1.3) / 0.15, 0, 1) * np.exp(-np.clip(tt - 1.4, 0, None) * 2.5) * 0.5
    return normalize(inh + exh, -6)

@reg('snort', 'Sleeper snorts and stirs (0.6 s).')
def snort():
    n = int(0.6 * SR); tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 55 * tt) > 0.3).astype(float) * bandpass(noise(n, 'white', 703), 200, 1500) * env_exp(n, 0.12)
    return normalize(soft_sat(x, 2), -3)

@reg('keys_jingle', 'Key ring lifted slowly: small metallic jingles (1.4 s).')
def keys_jingle():
    n = int(1.4 * SR); out = np.zeros(n); rng = np.random.default_rng(704)
    for t0 in np.sort(rng.uniform(0, 1.2, 14)):
        k = int(0.18 * SR); i = int(t0 * SR); tt = np.arange(k) / SR
        f = rng.uniform(2800, 5200)
        b = sum(np.sin(2 * np.pi * f * m * tt) / m for m in (1, 2.76, 5.4)) * env_exp(k, 0.04) * rng.uniform(0.3, 1)
        out[i:i + k] += b[:n - i]
    return normalize(out, -8)

@reg('lock_jiggle', 'Wrong key jiggled in an old lock (0.8 s).')
def lock_jiggle():
    n = int(0.8 * SR); out = np.zeros(n); rng = np.random.default_rng(705)
    for t0 in np.arange(0.05, 0.75, 0.07):
        k = int(0.05 * SR); i = int((t0 + rng.uniform(0, 0.02)) * SR)
        b = bandpass(noise(k, 'white', int(t0 * 1000)), 1500, 6000) * env_exp(k, 0.01)
        out[i:i + k] += b[:n - i]
    return normalize(out, -8)

@reg('lock_click', 'Key turns: heavy deadbolt clack (0.4 s).')
def lock_click():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    x = bandpass(noise(n, 'white', 706), 800, 5000) * env_exp(n, 0.015) + np.sin(2 * np.pi * 180 * tt) * env_exp(n, 0.04) * 0.6
    return normalize(convolve_stereo(x, reverb_ir(0.6, 0.3, seed=707), 0.25), -3)

@reg('stamp_thud', 'Rubber stamp slammed on paper on a wooden desk (0.4 s).')
def stamp_thud():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(120 * (1 + np.exp(-tt / 0.01))) / SR) * env_exp(n, 0.06) + lowpass(noise(n, 'pink', 708), 1800) * env_exp(n, 0.02)
    return normalize(soft_sat(x, 1.6), -3)

@reg('pen_scribble', 'Felt pen drawing a loop on paper (1.0 s).')
def pen_scribble():
    n = int(1.0 * SR); tt = np.arange(n) / SR
    x = bandpass(noise(n, 'white', 709), 2500, 8000) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 3.2 * tt))) * env_adsr(n, 0.05, 0.1, 0.9, 0.1)
    return normalize(x, -12)

@reg('paper_rustle', 'Files and folders shuffled (1.2 s).')
def paper_rustle():
    n = int(1.2 * SR); rng = np.random.default_rng(710)
    x = bandpass(noise(n, 'white', 711), 1000, 7000) * lowpass(np.abs(rng.standard_normal(n)), 18) * 3
    return normalize(x * env_adsr(n, 0.05, 0.2, 0.8, 0.2), -10)

@reg('heavy_breath', 'Panicked held breathing, in and out (2.0 s).')
def heavy_breath():
    n = int(2.0 * SR); tt = np.arange(n) / SR
    e = np.clip(np.sin(2 * np.pi * 1.0 * tt), 0, None) ** 1.5 + 0.6 * np.clip(-np.sin(2 * np.pi * 1.0 * tt), 0, None) ** 2
    x = bandpass(noise(n, 'pink', 712), 300, 3500) * e
    return normalize(x, -10)

@reg('monster_step', 'Something heavy and wrong takes a step: thud + bone creak (0.9 s).')
def monster_step():
    n = int(0.9 * SR); tt = np.arange(n) / SR
    thud = np.sin(2 * np.pi * np.cumsum(48 * (1 + np.exp(-tt / 0.03))) / SR) * env_exp(n, 0.18) * 1.4
    creak = bandpass(noise(n, 'white', 713), 400, 1200) * (np.sin(2 * np.pi * 23 * tt) > 0.6) * env_adsr(n, 0.08, 0.1, 0.5, 0.3) * 0.5
    return normalize(convolve_stereo(soft_sat(thud + creak, 1.5), reverb_ir(1.2, 0.4, seed=714), 0.3), -2)

@reg('bone_clicks', 'Its head turns: wet bone clicks / cracks (1.0 s).')
def bone_clicks():
    n = int(1.0 * SR); out = np.zeros(n); rng = np.random.default_rng(715)
    for t0 in np.sort(rng.uniform(0, 0.9, 9)):
        k = int(0.04 * SR); i = int(t0 * SR)
        out[i:i + k] += (bandpass(noise(k, 'white', int(t0 * 999)), 600, 4000) * env_exp(k, 0.006) * rng.uniform(0.5, 1))[:n - i]
    return normalize(convolve_stereo(out, reverb_ir(0.5, 0.3, seed=716), 0.2), -3)

@reg('big_bang', 'Huge BANG down the hallway: locker slammed by something strong, boom + metal ring (2.4 s).')
def big_bang():
    n = int(2.4 * SR); tt = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(40 * (1 + 2 * np.exp(-tt / 0.04))) / SR) * env_exp(n, 0.5) * 1.6
    hit = lowpass(noise(n, 'pink', 717), 3000) * env_exp(n, 0.05) * 2.0
    ring = sum(np.sin(2 * np.pi * f * tt) * env_exp(n, 0.7) * 0.25 for f in (233, 377, 611, 989))
    return normalize(convolve_stereo(soft_sat(boom + hit + ring, 2.0), reverb_ir(2.4, 0.6, seed=718), 0.45), -0.5)

@reg('knob_turn', 'Door handle slowly pressed down: metal latch creak (1.2 s).')
def knob_turn():
    n = int(1.2 * SR); tt = np.arange(n) / SR
    x = bandpass(noise(n, 'white', 719), 900, 2600) * (np.sin(2 * np.pi * 14 * tt) > 0.2) * env_adsr(n, 0.2, 0.1, 0.8, 0.2) * 0.6
    x[int(1.0 * SR):int(1.05 * SR)] += bandpass(noise(int(0.05 * SR), 'white', 720), 1000, 5000) * 1.0
    return normalize(x, -6)


# ---------------------------------------------------------------- bus pack (VIDEO_008 "Last Bus")
@reg('bus_engine', 'City bus interior: diesel idle rumble + road noise, loopable (6 s).')
def bus_engine():
    n = int(6.0 * SR); tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 34 * tt) + 0.5 * np.sin(2 * np.pi * 68 * tt) + 0.25 * np.sin(2 * np.pi * 102 * tt)) * (0.8 + 0.2 * np.sin(2 * np.pi * 4.3 * tt))
    x = x * 0.35 + lowpass(noise(n, 'brown', 801), 300) * 0.9 + bandpass(noise(n, 'pink', 802), 300, 1500) * 0.12
    return normalize(fade(x, 0.2, 0.2), -10)

@reg('bus_brakes', 'Air brakes hiss + long brake squeal (2.2 s).')
def bus_brakes():
    n = int(2.2 * SR); tt = np.arange(n) / SR
    sq = np.sin(2 * np.pi * np.cumsum(1900 + 120 * np.sin(2 * np.pi * 7 * tt)) / SR) * env_adsr(n, 0.2, 0.2, 0.7, 0.4) * 0.35
    hiss = highpass(noise(n, 'white', 803), 2500) * np.clip((tt - 1.6) / 0.05, 0, 1) * np.exp(-np.clip(tt - 1.65, 0, None) * 4) * 0.8
    return normalize(sq + hiss, -4)

@reg('stop_bell', 'Bus stop-request bell: two-tone ding (1.0 s).')
def stop_bell():
    a = fm_bell(1567.98, 0.9, ratio=2.0, index=0.5, decay=0.35)
    b = fm_bell(1318.5, 0.9, ratio=2.0, index=0.5, decay=0.4)
    out = np.zeros(int(1.0 * SR)); out[:len(a)] += a; out[int(0.18 * SR):int(0.18 * SR) + len(b)] += b[:len(out) - int(0.18 * SR)]
    return normalize(out, -4)

@reg('blink_cut', 'A blink: soft thump + everything drops out (0.4 s).')
def blink_cut():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(70 * (1 + np.exp(-tt / 0.02))) / SR) * env_exp(n, 0.08) + lowpass(noise(n, 'pink', 804), 600) * env_exp(n, 0.03) * 0.6
    return normalize(x, -3)

@reg('phone_beep', 'Phone video play tap (0.2 s).')
def phone_beep():
    a = fm_bell(2093.0, 0.2, ratio=1.0, index=0.2, decay=0.06)
    return normalize(a, -10)

@reg('head_turn_mass', 'Many heads turning at once: fabric rustle + creak (0.7 s).')
def head_turn_mass():
    n = int(0.7 * SR); tt = np.arange(n) / SR
    x = bandpass(noise(n, 'white', 805), 800, 5000) * env_adsr(n, 0.05, 0.1, 0.6, 0.3) * 0.7
    x += bandpass(noise(n, 'white', 806), 300, 900) * (np.sin(2 * np.pi * 21 * tt) > 0.5) * env_adsr(n, 0.1, 0.1, 0.5, 0.2) * 0.4
    return normalize(x, -6)

@reg('glass_tap', 'Knuckles tapping on a bus window, slowly, from outside (1.2 s).')
def glass_tap():
    n = int(1.2 * SR); out = np.zeros(n)
    for t0 in (0.05, 0.45, 0.85):
        k = int(0.12 * SR); i = int(t0 * SR); tt = np.arange(k) / SR
        b = (np.sin(2 * np.pi * 1100 * tt) + 0.6 * np.sin(2 * np.pi * 2730 * tt)) * env_exp(k, 0.02)
        out[i:i + k] += b
    return normalize(convolve_stereo(out, reverb_ir(0.6, 0.3, seed=807), 0.2), -6)


# ---------------------------------------------------------------- zombie pack (VIDEO_009 "They Knock")
@reg('door_knock', 'Two slow, deliberate knocks on a wooden classroom door (0.9 s).')
def door_knock():
    n = int(0.9 * SR); out = np.zeros(n)
    for t0 in (0.0, 0.35):
        k = int(0.3 * SR); i = int(t0 * SR); tt = np.arange(k) / SR
        b = np.sin(2 * np.pi * np.cumsum(140 * (1 + 0.6 * np.exp(-tt / 0.01))) / SR) * env_exp(k, 0.05)
        b += bandpass(noise(k, 'pink', 900 + i % 7), 300, 2500) * env_exp(k, 0.012) * 1.2
        out[i:i + k] += b
    return normalize(convolve_stereo(soft_sat(out, 1.4), reverb_ir(0.8, 0.35, seed=901), 0.25), -1)

@reg('vent_scratch', 'Nails scratching inside a metal air duct, loopable (3 s).')
def vent_scratch():
    n = int(3.0 * SR); out = np.zeros(n); rng = np.random.default_rng(902)
    for t0 in np.sort(rng.uniform(0, 2.8, 18)):
        k = int(rng.uniform(0.08, 0.22) * SR); i = int(t0 * SR); tt = np.arange(k) / SR
        f = rng.uniform(1500, 3800)
        b = bandpass(noise(k, 'white', int(t0 * 1000)), f * 0.8, f * 1.2) * env_adsr(k, 0.01, 0.03, 0.7, 0.04)
        b += np.sin(2 * np.pi * rng.uniform(300, 700) * tt) * env_exp(k, 0.05) * 0.2
        out[i:i + k] += b[:n - i]
    return normalize(convolve_stereo(out, reverb_ir(0.4, 0.3, seed=903), 0.35), -6)

@reg('zombie_groan', 'Low wet zombie groan (1.8 s).')
def zombie_groan():
    n = int(1.8 * SR); tt = np.arange(n) / SR
    f0 = 85 + 15 * np.sin(2 * np.pi * 0.7 * tt)
    src = np.sign(np.sin(2 * np.pi * np.cumsum(f0) / SR)) * 0.5 + noise(n, 'pink', 904) * 0.4
    x = bandpass(src, 200, 900) + bandpass(src, 1000, 1600) * 0.4
    x *= env_adsr(n, 0.2, 0.3, 0.8, 0.5) * (0.7 + 0.3 * np.abs(np.sin(2 * np.pi * 3.1 * tt)))
    return normalize(soft_sat(x, 2.0), -4)

@reg('crowd_groan', 'Many zombies far below: a low murmuring groan bed, loopable (5 s).')
def crowd_groan():
    n = int(5.0 * SR); out = np.zeros(n); rng = np.random.default_rng(905)
    for k in range(10):
        f = rng.uniform(70, 120); tt = np.arange(n) / SR
        src = np.sign(np.sin(2 * np.pi * np.cumsum(f + 10 * np.sin(2 * np.pi * rng.uniform(0.2, 0.6) * tt)) / SR)) * 0.3
        out += bandpass(src + noise(n, 'pink', 906 + k) * 0.3, 180, 800) * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(0.1, 0.3) * tt + k)) * 0.3
    return normalize(fade(lowpass(out, 1200), 0.3, 0.3), -8)


# ---------------------------------------------------------------- basketball pack (VIDEO_011 "Benched")
@reg('arena_crowd', 'Packed gym crowd murmur + cheers, loopable (6 s).')
def arena_crowd():
    n = int(6.0 * SR); tt = np.arange(n) / SR
    x = bandpass(noise(n, 'pink', 1001), 300, 3000) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.3 * tt))
    x += bandpass(noise(n, 'white', 1002), 1500, 5000) * 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.17 * tt + 1))
    return normalize(convolve_stereo(fade(x, 0.3, 0.3), reverb_ir(1.5, 0.5, seed=1003), 0.4), -8)

@reg('chant_23', 'Crowd chant: stomp-stomp-clap, twice a second, loopable (4 s).')
def chant_23():
    n = int(4.0 * SR); out = np.zeros(n)
    for b in range(8):
        t0 = b * 0.5
        for d, kind in ((0.0, 'st'), (0.17, 'st'), (0.34, 'cl')):
            k = int(0.15 * SR); i = int((t0 + d) * SR); tt = np.arange(k) / SR
            if kind == 'st':
                y = np.sin(2 * np.pi * 60 * tt) * env_exp(k, 0.05) + lowpass(noise(k, 'pink', 1004 + b), 400) * env_exp(k, 0.03)
            else:
                y = bandpass(noise(k, 'white', 1010 + b), 800, 4000) * env_exp(k, 0.02) * 1.4
            out[i:i + k] += y[:n - i]
    out += bandpass(noise(n, 'pink', 1020), 300, 2500) * 0.25
    return normalize(convolve_stereo(out, reverb_ir(1.6, 0.5, seed=1021), 0.45), -6)

@reg('ref_whistle', 'Referee whistle blast (0.7 s).')
def ref_whistle():
    n = int(0.7 * SR); tt = np.arange(n) / SR
    f = 3100 + 60 * np.sin(2 * np.pi * 38 * tt)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (1 + 0.4 * np.sin(2 * np.pi * 38 * tt)) * env_adsr(n, 0.01, 0.05, 0.9, 0.08)
    return normalize(x + highpass(noise(n, 'white', 1022), 3000) * 0.15 * env_adsr(n, 0.01, 0.05, 0.9, 0.08), -4)

@reg('arena_buzzer', 'Scoreboard buzzer/horn (1.0 s).')
def arena_buzzer():
    n = int(1.0 * SR); tt = np.arange(n) / SR
    x = sum(np.sign(np.sin(2 * np.pi * f * tt)) * g for f, g in ((233, 0.6), (277, 0.4), (349, 0.3)))
    return normalize(lowpass(x, 2500) * env_adsr(n, 0.01, 0.05, 0.9, 0.05), -4)

@reg('ball_bounce', 'Basketball dribble on hardwood (0.4 s).')
def ball_bounce():
    n = int(0.4 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(180 * (1 + 0.5 * np.exp(-tt / 0.01))) / SR) * env_exp(n, 0.04) + bandpass(noise(n, 'pink', 1023), 200, 1500) * env_exp(n, 0.015)
    return normalize(convolve_stereo(x, reverb_ir(1.2, 0.5, seed=1024), 0.35), -4)

@reg('net_swish', 'Ball through the net: swish (0.6 s).')
def net_swish():
    n = int(0.6 * SR)
    x = bandpass(noise(n, 'white', 1025), 2000, 9000) * env_adsr(n, 0.05, 0.1, 0.5, 0.3)
    return normalize(convolve_stereo(x, reverb_ir(1.0, 0.5, seed=1026), 0.3), -6)

@reg('sneaker_squeak', 'Sneaker squeak on a gym floor (0.3 s).')
def sneaker_squeak():
    n = int(0.3 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(1500 + 900 * tt / 0.3 + 200 * np.sin(2 * np.pi * 40 * tt)) / SR) * env_adsr(n, 0.01, 0.05, 0.7, 0.1)
    return normalize(convolve_stereo(x, reverb_ir(0.9, 0.4, seed=1027), 0.3), -8)


# ---------------------------------------------------------------- jumpscare pack (VIDEO_012 "Don't Touch The Vase")
@reg('jumpscare', 'JUMPSCARE: violent impact + dissonant shriek cluster + distorted roar (1.6 s).')
def jumpscare():
    n = int(1.6 * SR); tt = np.arange(n) / SR
    hit = np.sin(2 * np.pi * np.cumsum(45 * (1 + 3 * np.exp(-tt / 0.03))) / SR) * env_exp(n, 0.35) * 2.0
    hit += lowpass(noise(n, 'white', 1101), 4000) * env_exp(n, 0.06) * 2.0
    shriek = np.zeros(n)
    for k, f in enumerate((1240, 1318, 1397, 1975, 2637)):
        vib = 1 + 0.02 * np.sin(2 * np.pi * (11 + k) * tt)
        shriek += np.sign(np.sin(2 * np.pi * np.cumsum(f * vib) / SR)) * 0.18
    shriek = bandpass(shriek, 900, 6000) * env_adsr(n, 0.005, 0.25, 0.6, 0.6)
    roar = soft_sat(bandpass(noise(n, 'pink', 1102), 80, 900) * (1 + np.sin(2 * np.pi * 37 * tt)), 4.0) * env_adsr(n, 0.01, 0.3, 0.5, 0.6) * 0.8
    return normalize(convolve_stereo(soft_sat(hit + shriek + roar, 2.2), reverb_ir(1.8, 0.6, seed=1103), 0.35), -0.3)

@reg('subliminal_hit', 'A 0.1 s burst for a subliminal flash: click + shriek blip (0.5 s).')
def subliminal_hit():
    n = int(0.5 * SR); tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * 1975 * tt)) * env_exp(n, 0.05) * 0.6 + highpass(noise(n, 'white', 1104), 2000) * env_exp(n, 0.02)
    return normalize(convolve_stereo(x, reverb_ir(1.2, 0.5, seed=1105), 0.5), -3)

@reg('vase_shatter', 'Porcelain vase hits a wooden floor and shatters: crack + ringing shards (2.0 s).')
def vase_shatter():
    n = int(2.0 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(1106)
    x = np.sin(2 * np.pi * np.cumsum(90 * (1 + np.exp(-tt / 0.02))) / SR) * env_exp(n, 0.1) * 1.2
    x += highpass(noise(n, 'white', 1107), 2500) * env_exp(n, 0.05) * 1.5
    for t0 in np.sort(rng.uniform(0.02, 1.4, 26)):
        k = int(0.2 * SR); i = int(t0 * SR); f = rng.uniform(2500, 7000)
        b = np.sin(2 * np.pi * f * np.arange(k) / SR) * env_exp(k, 0.03) * rng.uniform(0.1, 0.5)
        x[i:i + k] += b[:n - i]
    return normalize(convolve_stereo(x, reverb_ir(1.4, 0.45, seed=1108), 0.35), -0.5)

@reg('smoke_hiss', 'Black smoke pouring out: low hiss + reversed breath (2.4 s).')
def smoke_hiss():
    n = int(2.4 * SR); tt = np.arange(n) / SR
    x = sweep_filter(noise(n, 'white', 1109), 3000, 300, kind='lowpass') * env_adsr(n, 0.1, 0.4, 0.7, 0.8) * 0.8
    x += bandpass(noise(n, 'pink', 1110), 100, 400) * np.clip(tt / 2.4, 0, 1) ** 2 * 1.2
    return normalize(convolve_stereo(x, reverb_ir(2.0, 0.6, seed=1111), 0.5), -4)

@reg('whispers', 'Layered unintelligible whispers moving around the head, loopable (4 s).')
def whispers():
    n = int(4.0 * SR); out = np.zeros((n, 2)); rng = np.random.default_rng(1112)
    for k in range(9):
        t0 = rng.uniform(0, 3.4); d = rng.uniform(0.3, 0.8); m = int(d * SR); i = int(t0 * SR)
        tt = np.arange(m) / SR
        syl = np.clip(np.sin(2 * np.pi * rng.uniform(5, 9) * tt), 0, 1) ** 2
        w = bandpass(noise(m, 'white', 1113 + k), rng.uniform(1500, 2500), rng.uniform(4000, 7000)) * syl * env_adsr(m, 0.05, 0.1, 0.8, 0.1)
        p = rng.uniform(-1, 1)
        out[i:i + m, 0] += w[:n - i] * (1 - p) * 0.5
        out[i:i + m, 1] += w[:n - i] * (1 + p) * 0.5
    return normalize(out, -10)

@reg('fork_scrape', 'A fork scraping an empty plate, slow (1.6 s).')
def fork_scrape():
    n = int(1.6 * SR); tt = np.arange(n) / SR
    f = 2600 + 400 * np.sin(2 * np.pi * 0.7 * tt)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 9 * tt))) * env_adsr(n, 0.1, 0.1, 0.8, 0.3) * 0.4
    x += bandpass(noise(n, 'white', 1114), 2000, 6000) * 0.3 * env_adsr(n, 0.1, 0.1, 0.8, 0.3)
    return normalize(x, -8)

@reg('wet_chew', 'Slow wet chewing, close (2.0 s).')
def wet_chew():
    n = int(2.0 * SR); out = np.zeros(n); rng = np.random.default_rng(1115)
    for t0 in np.arange(0.05, 1.9, 0.28):
        k = int(0.14 * SR); i = int(t0 * SR)
        b = bandpass(noise(k, 'pink', int(t0 * 100)), 300, 2500) * env_adsr(k, 0.02, 0.05, 0.5, 0.05) * rng.uniform(0.5, 1)
        out[i:i + k] += b[:n - i]
    return normalize(out, -8)

@reg('tinnitus', 'Post-scare ear ringing: high sine that fades (3.0 s).')
def tinnitus():
    n = int(3.0 * SR); tt = np.arange(n) / SR
    return normalize(np.sin(2 * np.pi * 7200 * tt) * env_adsr(n, 0.01, 0.2, 0.6, 2.4) * 0.3, -14)

@reg('thunder', 'Lightning crack + rolling thunder (3.0 s).')
def thunder():
    n = int(3.0 * SR); tt = np.arange(n) / SR
    x = highpass(noise(n, 'white', 1116), 1500) * env_exp(n, 0.04) * 1.5
    x += lowpass(noise(n, 'brown', 1117), 300) * env_adsr(n, 0.05, 0.6, 0.6, 2.0) * 2.0 * (0.7 + 0.3 * np.sin(2 * np.pi * 3 * tt))
    return normalize(convolve_stereo(soft_sat(x, 1.5), reverb_ir(2.5, 0.7, seed=1118), 0.45), -1)

@reg('rain_window', 'Heavy rain on a window, loopable (5 s).')
def rain_window():
    n = int(5.0 * SR); rng = np.random.default_rng(1119)
    x = bandpass(noise(n, 'pink', 1120), 800, 8000) * 0.5
    drops = (rng.random(n) > 0.9985).astype(float) * rng.uniform(0.3, 1.0, n)
    x += highpass(np.convolve(drops, np.exp(-np.arange(200) / 30), 'same'), 2000) * 0.8
    return normalize(fade(x, 0.2, 0.2), -10)

@reg('stair_crawl', 'Something climbing stairs on all fours: knuckle taps + creaks + scrape (3.0 s).')
def stair_crawl():
    n = int(3.0 * SR); out = np.zeros(n); rng = np.random.default_rng(1121)
    for t0 in np.arange(0.05, 2.9, 0.19):
        k = int(0.08 * SR); i = int((t0 + rng.uniform(0, 0.04)) * SR)
        b = (np.sin(2 * np.pi * rng.uniform(150, 260) * np.arange(k) / SR) * 0.6 + bandpass(noise(k, 'white', int(t0 * 77)), 500, 3000)) * env_exp(k, 0.012)
        out[i:i + k] += b[:n - i] * rng.uniform(0.4, 1.0)
    out += bandpass(noise(n, 'white', 1122), 400, 1200) * (np.sin(2 * np.pi * 0.7 * np.arange(n) / SR) > 0.85) * 0.3
    return normalize(convolve_stereo(out, reverb_ir(1.0, 0.4, seed=1123), 0.3), -4)

@reg('dread_drone', 'Sub-bass dread drone with a slow beating, loopable (8 s).')
def dread_drone():
    n = int(8.0 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * 36 * tt) + np.sin(2 * np.pi * 37.3 * tt) + 0.4 * np.sin(2 * np.pi * 72.4 * tt)
    x += bandpass(noise(n, 'brown', 1124), 30, 200) * 0.8
    return normalize(fade(x * 0.6, 0.5, 0.5), -6)


@reg('forest_night', 'Night forest bed: soft wind in leaves + sparse crickets + far owl, loopable (12 s).')
def forest_night():
    n = int(12.0 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(1601)
    x = bandpass(noise(n, 'pink', 1602), 300, 3500) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * tt) ** 2) * 0.5
    cr = np.sin(2 * np.pi * 4300 * tt) * (np.sin(2 * np.pi * 28 * tt) > 0.3) * (np.sin(2 * np.pi * 0.6 * tt) > 0.2) * 0.04
    x += cr
    for t0 in (3.0, 9.5):
        k = int(0.5 * SR); i = int(t0 * SR); f = 370 + 30 * rng.uniform()
        x[i:i + k] += np.sin(2 * np.pi * f * np.arange(k) / SR) * env_adsr(k, 0.08, 0.1, 0.6, 0.25) * 0.08
    return normalize(fade(convolve_stereo(x, reverb_ir(1.5, 0.5, seed=1603), 0.3), 0.5, 0.5), -8)

@reg('leaf_steps', 'Several people walking on dry leaves and twigs (4 s).')
def leaf_steps():
    n = int(4.0 * SR); out = np.zeros(n); rng = np.random.default_rng(1604)
    for t0 in np.arange(0.0, 3.8, 0.17):
        k = int(0.18 * SR); i = int((t0 + rng.uniform(0, 0.08)) * SR)
        b = bandpass(noise(k, 'white', int(t0 * 91)), 900, 7000) * env_exp(k, 0.05) * (rng.uniform(0, 1, k) > 0.6)
        out[i:i + k] += b[:n - i] * rng.uniform(0.3, 0.9)
    return normalize(fade(out, 0.05, 0.2), -6)

@reg('branch_snap', 'A dry branch snapping in the dark, close (0.8 s).')
def branch_snap():
    n = int(0.8 * SR); out = np.zeros(n)
    for j, (t0, a) in enumerate(((0.0, 1.0), (0.03, 0.7), (0.07, 0.5), (0.12, 0.3))):
        k = int(0.06 * SR); i = int(t0 * SR)
        out[i:i + k] += bandpass(noise(k, 'white', 1605 + j), 1200, 6000) * env_exp(k, 0.012) * a
    out += lowpass(noise(n, 'white', 1609), 300) * env_exp(n, 0.05) * 0.6
    return normalize(convolve_stereo(out, reverb_ir(1.2, 0.5, seed=1610), 0.35), -3)

@reg('house_creak', 'Old wooden house settling: slow low creaks (3 s).')
def house_creak():
    n = int(3.0 * SR); tt = np.arange(n) / SR
    f = 95 + 25 * np.sin(2 * np.pi * 0.4 * tt)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * bandpass(noise(n, 'white', 1611), 200, 1800)
    x = bandpass(x, 150, 1500) * (np.sin(np.pi * tt / 3.0) ** 2) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt))
    return normalize(convolve_stereo(x, reverb_ir(1.4, 0.5, seed=1612), 0.4), -6)

@reg('mimic_click', 'Wet clicking throat of something imitating a voice (1.5 s).')
def mimic_click():
    n = int(1.5 * SR); out = np.zeros(n); rng = np.random.default_rng(1613)
    for t0 in np.sort(rng.uniform(0, 1.4, 14)):
        k = int(0.03 * SR); i = int(t0 * SR)
        out[i:i + k] += bandpass(noise(k, 'white', int(t0 * 1e4)), 800, 4000) * env_exp(k, 0.006) * rng.uniform(0.4, 1)
    out += lowpass(noise(n, 'brown', 1614), 200) * 0.4 * env_adsr(n, 0.3, 0.2, 0.7, 0.5)
    return normalize(convolve_stereo(out, reverb_ir(0.9, 0.4, seed=1615), 0.3), -4)

@reg('chase_run', 'Five people sprinting through brush, branches whipping (4 s).')
def chase_run():
    n = int(4.0 * SR); out = np.zeros(n); rng = np.random.default_rng(1616)
    for t0 in np.arange(0.0, 3.9, 0.11):
        k = int(0.12 * SR); i = int((t0 + rng.uniform(0, 0.05)) * SR)
        b = (lowpass(noise(k, 'white', int(t0 * 97)), 400) * 1.5 + bandpass(noise(k, 'white', int(t0 * 31)), 1500, 6000) * 0.5) * env_exp(k, 0.04)
        out[i:i + k] += b[:n - i] * rng.uniform(0.5, 1)
    for t0 in rng.uniform(0.2, 3.6, 6):
        k = int(0.25 * SR); i = int(t0 * SR)
        out[i:i + k] += bandpass(noise(k, 'pink', int(t0 * 53)), 600, 5000) * env_adsr(k, 0.03, 0.05, 0.5, 0.15) * 0.6
    return normalize(fade(out, 0.05, 0.2), -4)


def main():
    root = sys.argv[1]
    d = os.path.join(root, 'sound_effects', 'comedy')
    os.makedirs(d, exist_ok=True)
    libp = os.path.join(root, 'sound_effects', 'LIBRARY.json')
    lib = json.load(open(libp)) if os.path.exists(libp) else []
    lib = [e for e in lib if e.get('category') != 'comedy']
    for name, (fn, desc) in LIB.items():
        y = np.asarray(fn(), np.float32)
        if y.ndim == 1:
            y = np.stack([y, y], 1)
        p = os.path.join(d, name + '.flac')
        sf.write(p, y, SR, subtype='PCM_24')
        lib.append({'file': os.path.relpath(p, root), 'category': 'comedy', 'name': name, 'description': desc,
                    'duration_s': round(len(y) / SR, 2), 'sample_rate': SR,
                    'licence': 'Original procedural synthesis (PIPELINE/audio/sfx_comedy.py). Free for monetised use.'})
        print('SFX', name, round(len(y) / SR, 2))
    json.dump(lib, open(libp, 'w'), indent=1)


if __name__ == '__main__':
    main()
