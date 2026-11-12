#!/usr/bin/env python3
"""VIDEO_024 audio synthesis (blueprint section 3): JUMPSCARE_SLAM, BONE_SNAP, taxi road rumble, tunnel roar, streetlight whoosh.
Writes AUDIO/sound_effects/taxi/*.flac (procedural, original, free to use) and registers them in LIBRARY.json."""
import json, os, sys
import numpy as np, soundfile as sf
STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'audio'))
from dsp import SR, bandpass, convolve_stereo, env_adsr, env_exp, fade, highpass, lowpass, noise, normalize, reverb_ir, soft_sat  # noqa


def jumpscare_slam():
    """140 Hz -> 30 Hz exponential pitch drop + high-passed white noise burst. ZERO attack (sample 0 = peak)."""
    n = int(1.5 * SR); tt = np.arange(n) / SR
    f = 30 + 110 * np.exp(-tt * 4.0)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.8)
    burst = highpass(noise(n, 'white', 2401), 2000) * np.exp(-tt * 7.0) * 0.9
    x = soft_sat(tone * 1.3 + burst, 2.5)
    x[0] = 1.0
    return normalize(convolve_stereo(x, reverb_ir(1.4, 0.45, seed=2402), 0.25), -0.5)


def bone_snap():
    """Wood-block transient (high, sharp) + crunch: white noise downsampled to 8 kHz (aliased grit), short."""
    n = int(0.7 * SR); tt = np.arange(n) / SR; out = np.zeros(n)
    for t0, f0, a in ((0.0, 1900, 1.0), (0.035, 2400, 0.7), (0.09, 1600, 0.5)):
        i = int(t0 * SR); m = int(0.06 * SR)
        k = np.arange(m) / SR
        out[i:i + m] += (np.sin(2 * np.pi * f0 * k) + 0.5 * np.sin(2 * np.pi * f0 * 2.76 * k)) * np.exp(-k * 90) * a
    cr = noise(int(0.4 * 8000), 'white', 2403)
    cr = np.repeat(cr, SR // 8000)[:int(0.4 * SR)] * env_adsr(int(0.4 * SR), 0.002, 0.1, 0.3, 0.2) * 0.7
    out[:len(cr)] += bandpass(cr, 300, 5000)
    return normalize(soft_sat(out, 1.8), -1.0)


def taxi_road():
    """Engine at speed + tyre/road rumble, loopable (10 s)."""
    n = int(10 * SR); tt = np.arange(n) / SR
    x = lowpass(noise(n, 'brown', 2404), 220) * 1.2 + bandpass(noise(n, 'pink', 2405), 500, 2500) * 0.25
    x += 0.2 * np.sin(2 * np.pi * 72 * tt) * (1 + 0.2 * np.sin(2 * np.pi * 9 * tt))
    return normalize(fade(x, 0.4, 0.4), -6)


def tunnel_roar():
    """Inside a concrete tunnel at speed: roaring, reflective, a slow flanged swirl (10 s)."""
    n = int(10 * SR); tt = np.arange(n) / SR
    x = bandpass(noise(n, 'pink', 2406), 120, 3000) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.4 * tt))
    return normalize(fade(convolve_stereo(x, reverb_ir(2.0, 0.7, seed=2407), 0.5), 0.4, 0.4), -5)


def light_whoosh():
    n = int(0.7 * SR); tt = np.arange(n) / SR
    x = bandpass(noise(n, 'pink', 2408), 600, 5000) * np.sin(np.pi * tt / 0.7) ** 2
    return normalize(x, -6)


SFX = {'taxi_slam': (jumpscare_slam, 'JUMPSCARE_SLAM: 140->30 Hz exp drop + HP noise burst, zero attack (1.5 s).'),
       'bone_snap': (bone_snap, 'BONE_SNAP: wood-block transient + 8 kHz downsampled noise crunch (0.7 s).'),
       'taxi_road': (taxi_road, 'Taxi at speed: engine + road rumble, loopable (10 s).'),
       'tunnel_roar': (tunnel_roar, 'Concrete tunnel at speed, roaring + reflective, loopable (10 s).'),
       'light_whoosh': (light_whoosh, 'A streetlight passing the window (0.7 s).')}
if __name__ == '__main__':
    root = os.path.join(STUDIO, 'AUDIO'); d = os.path.join(root, 'sound_effects', 'taxi'); os.makedirs(d, exist_ok=True)
    libp = os.path.join(root, 'sound_effects', 'LIBRARY.json'); lib = [e for e in json.load(open(libp)) if e.get('category') != 'taxi']
    for name, (fn, desc) in SFX.items():
        y = np.asarray(fn(), np.float32)
        y = np.stack([y, y], 1) if y.ndim == 1 else y
        p = os.path.join(d, name + '.flac'); sf.write(p, y, SR, subtype='PCM_24')
        lib.append({'file': os.path.relpath(p, root), 'category': 'taxi', 'name': name, 'description': desc, 'duration_s': round(len(y) / SR, 2),
                    'sample_rate': SR, 'licence': 'Original procedural synthesis (VIDEOS/VIDEO_024/audio_synth.py). Free for monetised use.'})
        print('SFX', name, round(len(y) / SR, 2))
    json.dump(lib, open(libp, 'w'), indent=1)
