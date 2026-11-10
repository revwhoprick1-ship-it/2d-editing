#!/usr/bin/env python3
"""VIDEO_017 voice FX (sox): attendant + captain over the cabin PA (band-limited, a touch of overdrive);
A03 "You looked." = the Purser's real voice (deep + doubled); X01 = Lawrence's voice from inside the bins (muffled, wet)."""
import os, shutil, subprocess
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


PA = ['highpass', '350', 'lowpass', '3400', 'overdrive', '3', 'reverb', '20']
FX = {'A01': PA, 'A02': ['reverb', '15'], 'A04': PA, 'C01': PA,
      'A03': ['pitch', '-500', 'chorus', '0.6', '0.9', '45', '0.5', '0.3', '2', '-t', 'overdrive', '6', 'reverb', '40'],
      'X01': ['pitch', '-120', 'lowpass', '1400', 'reverb', '50', 'overdrive', '3']}
for k, fx in FX.items():
    src = os.path.join(O, k + '.wav')
    sox(src, os.path.join(N, k + '.wav'), *fx, 'trim', '0', dur(src), 'norm', '-3')
print('VOICE_FX_OK')
