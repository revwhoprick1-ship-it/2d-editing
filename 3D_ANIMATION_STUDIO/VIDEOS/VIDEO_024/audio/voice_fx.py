#!/usr/bin/env python3
"""VIDEO_024 voice FX (sox; explicit lengths; faded tails). G01 = GPS: robotic female (band-limit + flanger + bitcrush-ish).
D01 = the driver: hoarse voice pitched -400 + wide chorus (blueprint), a little overdrive."""
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
FX = {'G01': ['highpass', '300', 'lowpass', '4000', 'flanger', '0', '2', '0', '71', '0.5', 'sine', '25', 'lin', 'overdrive', '3'],
      'D01': ['pitch', '-400', 'chorus', '0.6', '0.9', '55', '0.4', '0.25', '2', '-t', 'reverb', '25']}   # blueprint: -400 + chorus (no extra overdrive: keeps 'home' clear)
for k, fx in FX.items():
    a = os.path.join(tmp, k + '.wav')
    sox(os.path.join(O, k + '.wav'), a, *fx, 'pad', '0', '0.25')
    sox(a, os.path.join(N, k + '.wav'), 'fade', 't', '0.01', dur(a), '0.2', 'norm', '-3')
shutil.rmtree(tmp)
print('VOICE_FX_OK')
