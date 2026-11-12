#!/usr/bin/env python3
"""VIDEO_026 sound design — procedural numpy/scipy synthesis (original, nothing licensed, free to monetise).
Writes AUDIO/sound_effects/mimic/*.flac and registers them in LIBRARY.json (category 'mimic').

    /opt/tools/cbx/bin/python studio/audio_synth.py

JUMPSCARE_SLAM (0 ms attack) · FLESH_ZIP_RIP · METAL_SCREECH · three wood-door thuds (110 Hz body + high slap) + the same
low-passed at 400 Hz with SoX (Bob pounding outside) · phone buzz (160 Hz modulated square, 5 ms smoothed attack) · our own
message double-chime, pitch-bent down with SoX · 50 Hz heartbeat thud · CRT static + sub hum · alert double-beep ·
ringtone blast · cloth rip · sub thud · ink-tendril writhe bed · the swell that carries the last frame into frame 0.
Harsh sources are low-passed: square waves overshoot after AAC encoding.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import soundfile as sf

STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'audio'))
from dsp import SR, bandpass, convolve_stereo, fade, highpass, lowpass, noise, normalize, reverb_ir, soft_sat  # noqa: E402


def _t(d):
    return np.arange(int(d * SR)) / SR


def mimic_slam():
    """JUMPSCARE_SLAM: 150 -> 28 Hz sub drop + noise burst + a struck-metal ring. Sample 0 is the peak (0 ms attack)."""
    tt = _t(1.8); n = len(tt)
    sub = np.sin(2 * np.pi * np.cumsum(28 + 122 * np.exp(-tt * 5.0)) / SR) * np.exp(-tt * 1.6)
    burst = highpass(noise(n, 'white', 2601), 1800) * np.exp(-tt * 8.0) * 0.8
    ring = sum(np.sin(2 * np.pi * f * tt + k) for k, f in enumerate((412.0, 733.0, 1189.0))) * 0.10 * np.exp(-tt * 3.0)
    x = soft_sat(sub * 1.4 + burst + ring, 2.4); x[0] = 1.0
    return normalize(convolve_stereo(x, reverb_ir(1.5, 0.5, seed=2602), 0.25), -0.5)


def flesh_zip_rip():
    """FLESH_ZIP_RIP: a zipper tearing open (accelerating ticks) inside wet ripping tissue, then a low flap."""
    tt = _t(1.3); n = len(tt); rng = np.random.default_rng(2603); x = np.zeros(n)
    tk = 0.0
    while tk < 0.42:                                                          # the zipper: 90 -> 260 teeth per second
        i = int(tk * SR); m = int(0.004 * SR)
        x[i:i + m] += rng.uniform(0.6, 1.0) * np.sin(2 * np.pi * rng.uniform(2200, 3400) * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 900)
        tk += 1.0 / (90 + 170 * (tk / 0.42))
    wet = bandpass(noise(n, 'pink', 2604), 250, 3200)
    gr = np.zeros(n)
    for k in range(60):                                                       # fibres snapping
        i = int(rng.uniform(0, 0.6) * SR); m = int(rng.uniform(0.01, 0.04) * SR)
        gr[i:i + m] += np.hanning(m) * rng.uniform(0.4, 1.0)
    x += wet * np.clip(gr, 0, 1.6) * 1.1
    x += np.sin(2 * np.pi * np.cumsum(70 - 30 * np.clip(tt / 0.5, 0, 1)) / SR) * np.exp(-((tt - 0.42) ** 2) / 0.006) * 0.9
    x[0] = 0.8
    return normalize(soft_sat(convolve_stereo(lowpass(x, 7500), reverb_ir(0.9, 0.3, seed=2605), 0.18), 1.5), -1.0)


def metal_screech():
    """METAL_SCREECH: inharmonic FM shriek that bends down (1.4 s), low-passed at 8 kHz."""
    tt = _t(1.4)
    f0 = 2300 * np.exp(-tt * 0.5)
    mod = np.sin(2 * np.pi * np.cumsum(f0 * 1.414) / SR) * (3.0 + 2.0 * np.exp(-tt * 3))
    x = np.sin(2 * np.pi * np.cumsum(f0) / SR + mod) + 0.5 * np.sin(2 * np.pi * np.cumsum(f0 * 2.76) / SR + mod * 0.6)
    x *= np.exp(-tt * 2.2) * (0.8 + 0.2 * np.sin(2 * np.pi * 31 * tt))
    x = lowpass(x, 8000); x[0] = 0.7
    return normalize(convolve_stereo(x, reverb_ir(1.6, 0.7, seed=2606), 0.3), -3.0)


def door_thud():
    """One heavy thud on a wooden door: 110 Hz resonant body + a high slap."""
    tt = _t(0.7)
    body = np.sin(2 * np.pi * np.cumsum(110 + 60 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 9)
    body += 0.5 * np.sin(2 * np.pi * 223 * tt) * np.exp(-tt * 16)
    slap = bandpass(noise(len(tt), 'white', 2607), 1500, 5500) * np.exp(-tt * 70) * 0.7
    x = soft_sat(body * 1.3 + slap, 1.8); x[0] = 0.6
    return normalize(convolve_stereo(x, reverb_ir(0.8, 0.35, seed=2608), 0.22), -1.0)


def phone_buzz160():
    """Phone vibrating against a hand: 160 Hz square, amplitude-modulated, every burst with a smoothed 5 ms attack."""
    tt = _t(1.1); x = np.zeros(len(tt))
    for t0, d in ((0.0, 0.42), (0.55, 0.42)):
        i0, i1 = int(t0 * SR), int((t0 + d) * SR)
        s = tt[i0:i1] - t0
        sq = np.tanh(4 * np.sin(2 * np.pi * 160 * s)) * (0.75 + 0.25 * np.sin(2 * np.pi * 27 * s))
        x[i0:i1] += sq * np.minimum(1, s / 0.005) * np.minimum(1, (d - s) / 0.03)
    x = lowpass(x, 2400) + 0.2 * bandpass(noise(len(tt), 'white', 2609), 2000, 5000) * np.abs(x)
    return normalize(soft_sat(x, 1.6), -4.0)


def msg_chime():
    """Our own incoming-message double chime (two glassy notes)."""
    tt = _t(0.9); x = np.zeros(len(tt))
    for t0, f in ((0.0, 1318.5), (0.13, 1760.0)):
        i = int(t0 * SR); s = tt[:len(tt) - i]
        x[i:] += (np.sin(2 * np.pi * f * s) + 0.35 * np.sin(2 * np.pi * f * 2.01 * s) + 0.15 * np.sin(2 * np.pi * f * 3.02 * s)) * np.exp(-s * 9) * np.minimum(1, s / 0.002)
    return normalize(convolve_stereo(x, reverb_ir(0.7, 0.25, seed=2610), 0.2), -3.0)


def sub_heart50():
    """A 50 Hz heartbeat: two soft sub thumps (lub-dub)."""
    tt = _t(0.75); x = np.zeros(len(tt))
    for t0, a in ((0.0, 1.0), (0.24, 0.7)):
        i = int(t0 * SR); s = tt[:len(tt) - i]
        x[i:] += a * np.sin(2 * np.pi * np.cumsum(50 + 30 * np.exp(-s * 40)) / SR) * np.exp(-s * 13) * np.minimum(1, s / 0.004)
    return normalize(lowpass(x, 240), -1.0)


def crt_on():
    """A TV switching itself: high-voltage static crackle + a low sub hum settling (1.6 s)."""
    tt = _t(1.6); n = len(tt); rng = np.random.default_rng(2611)
    st = highpass(noise(n, 'white', 2612), 2500) * (np.exp(-tt * 3.5) * 0.9 + 0.08)
    for k in range(40):
        i = int(rng.uniform(0, 0.5) ** 1.5 * SR); m = int(0.003 * SR)
        st[i:i + m] += rng.uniform(-1, 1) * 1.2
    hum = (np.sin(2 * np.pi * 60 * tt) + 0.4 * np.sin(2 * np.pi * 120 * tt)) * np.minimum(1, tt / 0.05) * 0.5
    whine = 0.05 * np.sin(2 * np.pi * 7800 * tt) * np.exp(-tt * 1.5)
    x = lowpass(st, 9000) + hum + whine; x[0] = 0.9
    return normalize(fade(x, 0.0, 0.25), -2.0)


def alert_beep2():
    """Digital alert double-beep."""
    tt = _t(0.5); x = np.zeros(len(tt))
    for t0 in (0.0, 0.17):
        i0, i1 = int(t0 * SR), int((t0 + 0.11) * SR); s = tt[i0:i1] - t0
        x[i0:i1] += np.sin(2 * np.pi * 1975 * s) * np.minimum(1, s / 0.004) * np.minimum(1, (0.11 - s) / 0.01)
    return normalize(x, -5.0)


def ringtone_blast():
    """A ringtone at full volume in a silent room: a fast two-note trill (2.2 s), low-passed at 6.5 kHz."""
    tt = _t(2.2); x = np.zeros(len(tt))
    k = 0
    while k * 0.09 < 2.1:
        t0 = k * 0.09
        if (k // 8) % 2 == 0:                                                 # ring ... (short gap) ... ring
            f = 1568.0 if k % 2 == 0 else 2093.0
            i0, i1 = int(t0 * SR), int((t0 + 0.08) * SR); s = tt[i0:i1] - t0
            x[i0:i1] += (np.sin(2 * np.pi * f * s) + 0.4 * np.tanh(3 * np.sin(2 * np.pi * f * s))) * np.minimum(1, s / 0.003) * np.minimum(1, (0.08 - s) / 0.01)
        k += 1
    x = lowpass(x, 6500)
    return normalize(convolve_stereo(x, reverb_ir(0.9, 0.4, seed=2613), 0.22), -3.0)


def cloth_rip():
    tt = _t(0.5); n = len(tt); rng = np.random.default_rng(2614)
    g = np.zeros(n)
    for k in range(70):
        i = int(rng.uniform(0, 0.35) * SR); m = int(rng.uniform(0.002, 0.012) * SR)
        g[i:i + m] += np.hanning(m) * rng.uniform(0.5, 1.0)
    x = bandpass(noise(n, 'white', 2615), 900, 6500) * np.clip(g, 0, 1.5); x[0] = 0.5
    return normalize(x, -3.0)


def sub_thud():
    tt = _t(0.8)
    x = np.sin(2 * np.pi * np.cumsum(36 + 60 * np.exp(-tt * 18)) / SR) * np.exp(-tt * 6); x[0] = 0.8
    return normalize(soft_sat(lowpass(x, 300), 1.5), -1.0)


def tendril_writhe():
    """Ink tendrils: slow wet slither + tiny clicks (8 s, loopable)."""
    tt = _t(8.0); n = len(tt); rng = np.random.default_rng(2616)
    x = bandpass(noise(n, 'pink', 2617), 300, 2600) * (0.25 + 0.75 * np.abs(np.sin(2 * np.pi * 0.7 * tt + np.sin(2 * np.pi * 0.23 * tt) * 2)) ** 2) * 0.6
    for k in range(140):
        i = int(rng.uniform(0, 7.95) * SR); m = int(0.006 * SR)
        x[i:i + m] += np.sin(2 * np.pi * rng.uniform(900, 2600) * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 500) * rng.uniform(0.1, 0.5)
    return normalize(fade(convolve_stereo(x, reverb_ir(1.2, 0.5, seed=2618), 0.3), 0.4, 0.4), -8.0)


def loop_swell():
    """A reverse swell (0.9 s) that ends exactly on the loop point, so the last frame falls into the frame-0 slam."""
    tt = _t(0.9); n = len(tt)
    env = (tt / 0.9) ** 3
    x = bandpass(noise(n, 'pink', 2619), 200, 5000) * env + np.sin(2 * np.pi * np.cumsum(60 + 240 * (tt / 0.9) ** 2) / SR) * env * 0.7
    return normalize(lowpass(x, 7000), -3.0)


SFX = dict(mimic_slam=mimic_slam, flesh_zip_rip=flesh_zip_rip, metal_screech=metal_screech, door_thud=door_thud, phone_buzz160=phone_buzz160,
           msg_chime=msg_chime, sub_heart50=sub_heart50, crt_on=crt_on, alert_beep2=alert_beep2, ringtone_blast=ringtone_blast,
           cloth_rip=cloth_rip, sub_thud=sub_thud, tendril_writhe=tendril_writhe, loop_swell=loop_swell)
SOX_POST = {'msg_chime': ['bend', '0.06,-180,0.5'],                           # pitch-bent downward with SoX
            'door_thud_muffled': ('door_thud', ['lowpass', '400', 'gain', '4'])}   # Bob pounding outside: SoX low-pass 400 Hz

if __name__ == '__main__':
    root = os.path.join(STUDIO, 'AUDIO'); d = os.path.join(root, 'sound_effects', 'mimic'); os.makedirs(d, exist_ok=True)
    libp = os.path.join(root, 'sound_effects', 'LIBRARY.json'); lib = [e for e in json.load(open(libp)) if e.get('category') != 'mimic']
    made = {}
    for name, fn in SFX.items():
        y = np.asarray(fn(), np.float32)
        y = np.stack([y, y], 1) if y.ndim == 1 else y
        made[name] = (y, (fn.__doc__ or name).strip().split('\n')[0])
    tmp = tempfile.mkdtemp()
    for name, spec in SOX_POST.items():
        src, fx = (name, spec) if isinstance(spec, list) else spec
        a, b = os.path.join(tmp, 'a.wav'), os.path.join(tmp, 'b.wav')
        sf.write(a, made[src][0], SR, subtype='PCM_24')
        subprocess.run(['sox', a, b, *fx], check=True, stderr=subprocess.DEVNULL)
        y, _ = sf.read(b, dtype='float32', always_2d=True)
        made[name] = (y, made[src][1] + ' (SoX: ' + ' '.join(fx) + ')')
    for name, (y, desc) in made.items():
        p = os.path.join(d, name + '.flac'); sf.write(p, y, SR, subtype='PCM_24')
        lib.append({'file': os.path.relpath(p, root), 'category': 'mimic', 'name': name, 'description': desc, 'duration_s': round(len(y) / SR, 2),
                    'sample_rate': SR, 'licence': 'Original procedural synthesis (VIDEOS/VIDEO_026/studio/audio_synth.py). Free for monetised use.'})
        print('SFX', name, round(len(y) / SR, 2))
    json.dump(lib, open(libp, 'w'), indent=1)
