#!/usr/bin/env python3
"""VIDEO_022 voice FX (sox, explicit lengths, faded tails). G01 = Grandma on the phone (band-limited). O01 = 'Mom' from
downstairs (far, roomy); O02 = right outside your door (close, dry). X = the Tenant: Grandma's voice pulled down + a
whisper an octave up, doubled."""
import os, shutil, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
N = os.path.join(HERE, 'narration', 'lines'); O = os.path.join(HERE, 'narration', 'orig_lines')
os.makedirs(O, exist_ok=True)
for f in os.listdir(N):
    if f.endswith('.wav') and not os.path.exists(os.path.join(O, f)):
        shutil.copy(os.path.join(N, f), os.path.join(O, f))


def sox(*a):
    subprocess.run(['sox', *a], check=True, stderr=subprocess.DEVNULL)


def dur(p):
    return subprocess.run(['soxi', '-D', p], capture_output=True, text=True).stdout.strip()


tmp = tempfile.mkdtemp()


def out(k, src_fx):
    sox(src_fx, os.path.join(N, k + '.wav'), 'fade', 't', '0.01', dur(src_fx), '0.25', 'norm', '-3')


FX = {'G01': ['highpass', '400', 'lowpass', '3200', 'overdrive', '4'], 'O01': ['reverb', '60', '50', '80', 'lowpass', '3500'],
      'O02': ['reverb', '8']}
for k, fx in FX.items():
    a = os.path.join(tmp, k + '.wav')
    sox(os.path.join(O, k + '.wav'), a, *fx, 'pad', '0', '0.3')
    out(k, a)
for k in ('X01', 'X02'):
    src = os.path.join(O, k + '.wav')
    lo, hi, m = (os.path.join(tmp, f'{k}_{x}.wav') for x in ('lo', 'hi', 'm'))
    sox(src, '-r', '24000', '-c', '1', lo, 'pitch', '-520', 'overdrive', '8', 'norm', '-4')
    sox(src, '-r', '24000', '-c', '1', hi, 'pitch', '700', 'highpass', '1500', 'pad', '0.03', 'norm', '-12')
    sox('-m', lo, hi, m)
    m2 = os.path.join(tmp, f'{k}_m2.wav')
    sox(m, m2, 'reverb', '50', 'pad', '0', '0.4')
    out(k, m2)
for k, tempo in (('N01', '1.3'), ('N02', '1.15')):                                       # faster hook (pitch kept)
    a = os.path.join(tmp, k + '_t.wav')
    sox(os.path.join(O, k + '.wav'), a, 'tempo', '-s', tempo, 'pad', '0', '0.1')
    out(k, a)
shutil.rmtree(tmp)
print('VOICE_FX_OK')
