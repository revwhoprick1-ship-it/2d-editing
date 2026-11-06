"""Small DSP toolkit (numpy/scipy) shared by the SFX synthesiser, music generator and mixer.
All sounds made with this are original and owned by the studio (no third-party samples)."""
import numpy as np
from scipy import signal

SR = 48000


def t_axis(dur, sr=SR):
    return np.arange(int(dur * sr)) / sr


def env_adsr(n, a=0.01, d=0.1, s=0.7, r=0.2, sr=SR):
    a_n, d_n, r_n = int(a * sr), int(d * sr), int(r * sr)
    s_n = max(0, n - a_n - d_n - r_n)
    e = np.concatenate([np.linspace(0, 1, max(1, a_n)), np.linspace(1, s, max(1, d_n)), np.full(s_n, s),
                        np.linspace(s, 0, max(1, r_n))])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def env_exp(n, decay, sr=SR, attack=0.002):
    t = np.arange(n) / sr
    e = np.exp(-t / max(decay, 1e-4))
    a = int(attack * sr)
    if a > 0:
        e[:a] *= np.linspace(0, 1, a)
    return e


def noise(n, color='white', seed=None):
    rng = np.random.default_rng(seed)
    w = rng.standard_normal(n)
    if color == 'white':
        return w
    f = np.fft.rfft(w)
    k = np.arange(len(f))
    k[0] = 1
    if color == 'pink':
        f /= np.sqrt(k)
    elif color == 'brown':
        f /= k
    x = np.fft.irfft(f, n)
    return x / (np.max(np.abs(x)) + 1e-9)


def bandpass(x, lo, hi, order=2, sr=SR):
    sos = signal.butter(order, [max(10, lo), min(sr / 2 - 100, hi)], 'bandpass', fs=sr, output='sos')
    return signal.sosfilt(sos, x)


def lowpass(x, fc, order=2, sr=SR):
    sos = signal.butter(order, min(fc, sr / 2 - 100), 'lowpass', fs=sr, output='sos')
    return signal.sosfilt(sos, x)


def highpass(x, fc, order=2, sr=SR):
    sos = signal.butter(order, max(10, fc), 'highpass', fs=sr, output='sos')
    return signal.sosfilt(sos, x)


def sweep_filter(x, f_start, f_end, q=1.0, kind='lowpass', sr=SR, block=256):
    """Time-varying biquad (block processed) for filter sweeps."""
    out = np.zeros_like(x)
    zi = np.zeros((1, 2))
    n = len(x)
    for i in range(0, n, block):
        u = i / max(1, n - 1)
        fc = f_start * (f_end / f_start) ** u
        fc = np.clip(fc, 20, sr / 2 - 200)
        if kind == 'lowpass':
            b, a = signal.iirfilter(2, fc, btype='lowpass', ftype='butter', fs=sr)
        elif kind == 'highpass':
            b, a = signal.iirfilter(2, fc, btype='highpass', ftype='butter', fs=sr)
        else:
            bw = fc / q
            b, a = signal.iirfilter(2, [max(20, fc - bw / 2), min(sr / 2 - 200, fc + bw / 2)], btype='bandpass',
                                    ftype='butter', fs=sr)
        sos = signal.tf2sos(b, a)
        seg, zi_new = signal.sosfilt(sos, x[i:i + block], zi=zi if zi.shape == (sos.shape[0], 2) else np.zeros((sos.shape[0], 2)))
        out[i:i + block] = seg
        zi = zi_new
    return out


def sine(freq, dur, sr=SR, phase=0.0):
    t = t_axis(dur, sr)
    if np.ndim(freq) == 0:
        return np.sin(2 * np.pi * freq * t + phase)
    ph = 2 * np.pi * np.cumsum(freq) / sr
    return np.sin(ph + phase)


def saw(freq, dur, sr=SR):
    t = t_axis(dur, sr)
    if np.ndim(freq) == 0:
        ph = freq * t
    else:
        ph = np.cumsum(freq) / sr
    return 2 * (ph - np.floor(ph + 0.5))


def square(freq, dur, sr=SR, duty=0.5):
    t = t_axis(dur, sr)
    ph = (freq * t) % 1.0 if np.ndim(freq) == 0 else (np.cumsum(freq) / sr) % 1.0
    return np.where(ph < duty, 1.0, -1.0)


def karplus(freq, dur, sr=SR, decay=0.996, bright=0.5, seed=0):
    n = int(dur * sr)
    p = max(2, int(sr / freq))
    rng = np.random.default_rng(seed)
    buf = rng.uniform(-1, 1, p) * 0.8
    buf = lowpass(buf, 1500 + 8000 * bright) if p > 32 else buf
    out = np.zeros(n)
    idx = 0
    for i in range(n):
        out[i] = buf[idx]
        nxt = (idx + 1) % p
        buf[idx] = decay * 0.5 * (buf[idx] + buf[nxt])
        idx = nxt
    return out


def fm_bell(freq, dur, ratio=3.5, index=3.0, decay=1.2, sr=SR):
    t = t_axis(dur, sr)
    mod = np.sin(2 * np.pi * freq * ratio * t) * index * np.exp(-t / (decay * 0.5))
    return np.sin(2 * np.pi * freq * t + mod) * np.exp(-t / decay)


def reverb_ir(dur=2.0, decay=0.6, sr=SR, seed=1, predelay=0.012, damp=6000):
    n = int(dur * sr)
    rng = np.random.default_rng(seed)
    L = rng.standard_normal(n) * np.exp(-np.arange(n) / sr / decay)
    R = rng.standard_normal(n) * np.exp(-np.arange(n) / sr / decay)
    L, R = lowpass(L, damp), lowpass(R, damp)
    pd = np.zeros(int(predelay * sr))
    L, R = np.concatenate([pd, L]), np.concatenate([pd, R])
    norm = np.sqrt(np.sum(L ** 2))
    return np.stack([L, R], 1) / (norm + 1e-9)


def convolve_stereo(x, ir, wet=0.25):
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    yL = signal.fftconvolve(x[:, 0], ir[:, 0])[:len(x)]
    yR = signal.fftconvolve(x[:, 1], ir[:, 1])[:len(x)]
    return x * (1 - wet) + np.stack([yL, yR], 1) * wet


def pan(x, p):
    """p in [-1, 1]; equal-power."""
    if x.ndim == 2:
        x = x.mean(1)
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)


def normalize(x, peak_db=-1.0):
    m = np.max(np.abs(x)) + 1e-12
    return x * (10 ** (peak_db / 20) / m)


def fade(x, fin=0.005, fout=0.02, sr=SR):
    x = x.copy()
    a, b = int(fin * sr), int(fout * sr)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def from_db(d):
    return 10 ** (d / 20)


def envelope_follower(x, sr=SR, attack=0.01, release=0.2):
    x = np.abs(x if x.ndim == 1 else x.mean(1))
    ga, gr = np.exp(-1 / (attack * sr)), np.exp(-1 / (release * sr))
    out = np.zeros_like(x)
    e = 0.0
    # vectorised-ish: process in python loop at decimated rate for speed
    dec = 48
    xd = x[: len(x) // dec * dec].reshape(-1, dec).max(1)
    ga, gr = np.exp(-dec / (attack * sr)), np.exp(-dec / (release * sr))
    od = np.zeros_like(xd)
    for i, v in enumerate(xd):
        g = ga if v > e else gr
        e = g * e + (1 - g) * v
        od[i] = e
    out = np.repeat(od, dec)
    return np.pad(out, (0, len(x) - len(out)), mode='edge')


def compressor(x, thresh_db=-18, ratio=3.0, attack=0.005, release=0.12, knee=6.0, makeup_db=0.0, sr=SR):
    env = envelope_follower(x, sr, attack, release)
    lvl = db(env)
    over = lvl - thresh_db
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * (1 - 1 / ratio),
                           (1 - 1 / ratio) * (over + knee / 2) ** 2 / (2 * knee)))
    g = from_db(-gr + makeup_db)
    return x * (g[:, None] if x.ndim == 2 else g)


def deesser(x, freq=6500, thresh_db=-30, max_red_db=6, sr=SR):
    mono = x if x.ndim == 1 else x.mean(1)
    side = bandpass(mono, freq, min(12000, freq * 1.8), 2, sr)
    env = envelope_follower(side, sr, 0.002, 0.05)
    over = np.clip(db(env) - thresh_db, 0, max_red_db)
    hi = highpass(mono, freq, 2, sr)
    lo = mono - hi
    y = lo + hi * from_db(-over)
    return y


def peaking_eq(x, f0, gain_db, q=1.0, sr=SR):
    A = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / sr
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * A, -2 * np.cos(w0), 1 - alpha * A]
    a = [1 + alpha / A, -2 * np.cos(w0), 1 - alpha / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)


def soft_sat(x, drive=1.5):
    return np.tanh(x * drive) / np.tanh(drive)


def true_peak_limiter(x, ceiling_db=-1.0, sr=SR, lookahead=0.005, release=0.05):
    """Lookahead limiter using a 4x-oversampled peak detector to respect true peak."""
    over = signal.resample_poly(x, 4, 1, axis=0)
    pk = np.max(np.abs(over), axis=1) if over.ndim == 2 else np.abs(over)
    pk = pk.reshape(-1, 4).max(1)[:len(x)]
    ceil = from_db(ceiling_db)
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    la = int(lookahead * sr)
    # running min over lookahead window
    from scipy.ndimage import minimum_filter1d
    g = minimum_filter1d(need, size=2 * la + 1, origin=0)
    # smooth release
    rel = np.exp(-1 / (release * sr))
    out = np.empty_like(g)
    cur = 1.0
    for i in range(0, len(g), 32):
        tgt = g[i:i + 32].min()
        cur = tgt if tgt < cur else rel ** 32 * cur + (1 - rel ** 32) * tgt
        out[i:i + 32] = cur
    return x * (out[:, None] if x.ndim == 2 else out)
