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
