#!/usr/bin/env python3
"""VIDEO_018 voice FX (sox): the girl slightly airy and close; 22C's 'He's lying.' = a dead man's voice
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


FX = {'G01': ['reverb', '25', 'treble', '3'], 'G02': ['reverb', '35', 'treble', '3'],
      'X01': ['pitch', '-350', 'overdrive', '8', 'chorus', '0.6', '0.9', '50', '0.4', '0.25', '2', '-t', 'reverb', '45']}
for k, fx in FX.items():
    src = os.path.join(O, k + '.wav')
    sox(src, os.path.join(N, k + '.wav'), *fx, 'trim', '0', dur(src), 'norm', '-3')
print('VOICE_FX_OK')
