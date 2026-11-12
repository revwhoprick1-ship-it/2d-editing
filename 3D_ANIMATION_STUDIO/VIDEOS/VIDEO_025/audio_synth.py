#!/usr/bin/env python3
"""VIDEO_025 sound design (procedural, original, free to use): the end of the world.
Writes AUDIO/sound_effects/world/*.flac and registers them in LIBRARY.json (category 'world').
The phone alert is our OWN tone (not a real emergency-broadcast signal)."""
import json, os, sys
import numpy as np, soundfile as sf
STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'audio'))
from dsp import SR, bandpass, convolve_stereo, env_exp, fade, highpass, lowpass, noise, normalize, reverb_ir, soft_sat  # noqa


def _t(d):
    return np.arange(int(d * SR)) / SR


def alert_tone():
    """3 urgent pulses, two notes a fifth apart, soft square, smoothed (no harsh overshoot)."""
    tt = _t(2.4); x = np.zeros(len(tt))
    for k in range(3):
        for j, f in enumerate((880.0, 1318.5)):
            i0, i1 = int((k * 0.8 + j * 0.2) * SR), int((k * 0.8 + j * 0.2 + 0.18) * SR)
            s = tt[i0:i1] - tt[i0]
            x[i0:i1] += np.tanh(3 * np.sin(2 * np.pi * f * s)) * np.minimum(1, s / 0.006) * np.minimum(1, (0.18 - s) / 0.02)
    x = lowpass(x, 5000)
    return normalize(convolve_stereo(x, reverb_ir(0.6, 0.2, seed=2501), 0.15), -3)


def sky_crack():
    """The sky splitting: a sharp glassy crackle + a huge low boom that rolls away (4 s)."""
    tt = _t(4.0); n = len(tt)
    boom = lowpass(noise(n, 'brown', 2502), 120) * np.exp(-tt * 1.1) * 2.2
    boom += np.sin(2 * np.pi * np.cumsum(38 + 40 * np.exp(-tt * 3)) / SR) * np.exp(-tt * 1.6)
    cr = np.zeros(n); rng = np.random.default_rng(2503)
    for k in range(70):
        i = int(rng.uniform(0, 1.2) ** 2 * SR); m = int(0.012 * SR)
        cr[i:i + m] += highpass(noise(m, 'white', 2600 + k), 2500) * rng.uniform(0.3, 1.0) * np.exp(-np.arange(m) / SR * 300)
    x = soft_sat(boom + cr * 0.8, 1.6); x[0] = 0.0
    return normalize(convolve_stereo(x, reverb_ir(3.0, 1.2, seed=2504), 0.35), -1)


def fire_bed():
    """Burning car: roar + random crackles, loopable (8 s)."""
    tt = _t(8.0); n = len(tt)
    x = bandpass(noise(n, 'pink', 2505), 120, 1800) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.6 * tt)) * 0.6
    rng = np.random.default_rng(2506)
    for k in range(160):
        i = int(rng.uniform(0, 7.95) * SR); m = int(0.008 * SR)
        x[i:i + m] += highpass(noise(m, 'white', 2700 + k), 1500) * rng.uniform(0.2, 0.9)
    return normalize(fade(x, 0.3, 0.3), -6)


def rumble_bed():
    """The ground shaking: sub rumble with slow surges, loopable (10 s)."""
    tt = _t(10.0); n = len(tt)
    x = lowpass(noise(n, 'brown', 2507), 90) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.23 * tt) ** 2)
    x += 0.25 * lowpass(noise(n, 'pink', 2508), 300)
    return normalize(fade(x, 0.4, 0.4), -4)


def wind_roar():
    """Open sky after the roof is gone: howling wind (10 s)."""
    tt = _t(10.0); n = len(tt)
    x = bandpass(noise(n, 'pink', 2509), 200, 2400) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.17 * tt + 1))
    x += 0.3 * bandpass(noise(n, 'white', 2510), 800 + 0 * tt[0], 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.31 * tt))
    return normalize(fade(convolve_stereo(x, reverb_ir(2.0, 0.8, seed=2511), 0.3), 0.5, 0.5), -6)


def beam_hum():
    """The light: an airy chord that breathes + shimmer (10 s, loopable)."""
    tt = _t(10.0)
    x = sum(np.sin(2 * np.pi * f * tt + k) * a for k, (f, a) in enumerate(((110, 0.5), (220.4, 0.4), (329.8, 0.3), (440.6, 0.22), (659.3, 0.12))))
    x = x * (0.75 + 0.25 * np.sin(2 * np.pi * 0.25 * tt))
    x += 0.15 * highpass(noise(len(tt), 'white', 2512), 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.1 * tt))
    return normalize(fade(convolve_stereo(x, reverb_ir(3.0, 1.0, seed=2513), 0.5), 0.6, 0.6), -6)


def beam_slam():
    """The light locks on: instant sub drop + white blast + ringing shimmer (zero attack)."""
    tt = _t(3.0); n = len(tt)
    sub = np.sin(2 * np.pi * np.cumsum(28 + 90 * np.exp(-tt * 5)) / SR) * np.exp(-tt * 1.3)
    blast = highpass(noise(n, 'white', 2514), 1500) * np.exp(-tt * 5) * 0.7
    ring = sum(np.sin(2 * np.pi * f * tt) for f in (880, 1320.5, 1760.7)) * 0.12 * np.exp(-tt * 1.0)
    x = soft_sat(sub * 1.4 + blast + ring, 1.8); x[0] = 0.9
    return normalize(convolve_stereo(x, reverb_ir(2.5, 1.0, seed=2515), 0.35), -1)


def gravity_up():
    """Everything lifts: a rising airy sweep with a sub swell (1.4 s)."""
    tt = _t(1.4); n = len(tt)
    x = bandpass(noise(n, 'pink', 2516), 300, 4000) * (tt / 1.4) ** 1.5
    x += np.sin(2 * np.pi * np.cumsum(40 + 60 * tt / 1.4) / SR) * (tt / 1.4) * 0.6
    return normalize(fade(x, 0.02, 0.15), -4)


def roof_rip():
    """Wood and nails tearing + a roar of air (2.5 s)."""
    tt = _t(2.5); n = len(tt); rng = np.random.default_rng(2517); x = np.zeros(n)
    for k in range(45):
        i = int(rng.uniform(0, 1.0) * SR); m = int(rng.uniform(0.02, 0.07) * SR)
        f0 = rng.uniform(300, 1400)
        s = np.arange(m) / SR
        x[i:i + m] += (bandpass(noise(m, 'white', 2800 + k), f0, f0 * 3) + 0.4 * np.sin(2 * np.pi * f0 * 0.5 * s)) * np.exp(-s * 40) * rng.uniform(0.4, 1)
    x += lowpass(noise(n, 'brown', 2518), 200) * np.exp(-tt * 0.8) * 1.5
    x[0] = 0.0
    return normalize(soft_sat(convolve_stereo(x, reverb_ir(1.8, 0.7, seed=2519), 0.3), 1.4), -1)


def phone_ring():
    """A ringtone (soft marimba-ish, 2 rings, 2.4 s)."""
    tt = _t(2.4); x = np.zeros(len(tt))
    for r in range(2):
        for k, f in enumerate((1046.5, 1318.5, 1568.0, 1318.5)):
            i = int((r * 1.2 + k * 0.11) * SR); m = int(0.3 * SR); s = np.arange(m) / SR
            x[i:i + m] += (np.sin(2 * np.pi * f * s) + 0.3 * np.sin(2 * np.pi * f * 4 * s)) * np.exp(-s * 14)
    return normalize(x, -4)


def call_fail():
    """Call failed: three falling beeps."""
    tt = _t(1.0); x = np.zeros(len(tt))
    for k, f in enumerate((988.0, 784.0, 587.3)):
        i = int(k * 0.22 * SR); m = int(0.16 * SR); s = np.arange(m) / SR
        x[i:i + m] += np.sin(2 * np.pi * f * s) * np.minimum(1, s / 0.005) * np.minimum(1, (0.16 - s) / 0.02)
    return normalize(x, -6)


def sirens_far():
    """Distant sirens across the city, wailing slowly (10 s, loopable)."""
    tt = _t(10.0)
    x = sum(np.sin(2 * np.pi * np.cumsum(650 + 220 * np.sin(2 * np.pi * r * tt + ph)) / SR) for r, ph in ((0.19, 0), (0.23, 2.1)))
    x = lowpass(x, 1800) * 0.5
    return normalize(fade(convolve_stereo(x, reverb_ir(3.0, 1.4, seed=2520), 0.7), 0.5, 0.5), -10)


def end_boom():
    """The end (0:00): one enormous white-out boom (sample 0 = peak), long tail (5 s)."""
    tt = _t(5.0); n = len(tt)
    x = np.sin(2 * np.pi * np.cumsum(25 + 70 * np.exp(-tt * 2.5)) / SR) * np.exp(-tt * 0.7) * 1.4
    x += lowpass(noise(n, 'brown', 2521), 400) * np.exp(-tt * 0.9) * 1.2 + highpass(noise(n, 'white', 2522), 3000) * np.exp(-tt * 6) * 0.5
    x = soft_sat(x, 1.7); x[0] = 1.0
    return normalize(convolve_stereo(x, reverb_ir(4.0, 1.8, seed=2523), 0.4), -1)


SFX = {k: (v, (v.__doc__ or '').strip().split('\n')[0]) for k, v in dict(
    alert_tone=alert_tone, sky_crack=sky_crack, fire_bed=fire_bed, rumble_bed=rumble_bed, wind_roar=wind_roar, beam_hum=beam_hum,
    beam_slam=beam_slam, gravity_up=gravity_up, roof_rip=roof_rip, phone_ring=phone_ring, call_fail=call_fail, sirens_far=sirens_far,
    end_boom=end_boom).items()}
if __name__ == '__main__':
    root = os.path.join(STUDIO, 'AUDIO'); d = os.path.join(root, 'sound_effects', 'world'); os.makedirs(d, exist_ok=True)
    libp = os.path.join(root, 'sound_effects', 'LIBRARY.json'); lib = [e for e in json.load(open(libp)) if e.get('category') != 'world']
    for name, (fn, desc) in SFX.items():
        y = np.asarray(fn(), np.float32)
        y = np.stack([y, y], 1) if y.ndim == 1 else y
        p = os.path.join(d, name + '.flac'); sf.write(p, y, SR, subtype='PCM_24')
        lib.append({'file': os.path.relpath(p, root), 'category': 'world', 'name': name, 'description': desc, 'duration_s': round(len(y) / SR, 2),
                    'sample_rate': SR, 'licence': 'Original procedural synthesis (VIDEOS/VIDEO_025/audio_synth.py). Free for monetised use.'})
        print('SFX', name, round(len(y) / SR, 2))
    json.dump(lib, open(libp, 'w'), indent=1)
