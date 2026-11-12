#!/usr/bin/env python3
"""VIDEO_025 voice FX (sox; explicit lengths; faded tails, reverb tails kept). A = the emergency alert voice (robotic, PA reverb),
P = Mom on the phone (band-limited, a little crunch). Originals kept in narration/orig_lines."""
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


ROBOT = ['highpass', '300', 'lowpass', '4000', 'flanger', '0', '2', '0', '71', '0.5', 'sine', '25', 'lin', 'overdrive', '3', 'reverb', '30']
PHONE = ['highpass', '380', 'lowpass', '3200', 'overdrive', '5', 'gain', '-2']
FX = {'A01': ROBOT, 'A02': ROBOT, 'P01': PHONE, 'P02': PHONE}
tmp = tempfile.mkdtemp()
for k, fx in FX.items():
    a = os.path.join(tmp, k + '.wav')
    sox(os.path.join(O, k + '.wav'), a, *fx, 'pad', '0', '0.35' if fx is ROBOT else '0.1')
    sox(a, os.path.join(N, k + '.wav'), 'fade', 't', '0.01', dur(a), '0.25', 'norm', '-3')
shutil.rmtree(tmp)
print('VOICE_FX_OK')
