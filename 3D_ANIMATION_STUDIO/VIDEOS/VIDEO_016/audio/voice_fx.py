#!/usr/bin/env python3
"""VIDEO_016 voice FX (sox) for the copied voices (X lines). Same length out as in, so timing stays valid.
X01/X06 whispers: low + dark room.  X02 'Help...': far away in the trees.  X03/X04: muffled through the door.
X05: the thing using Ken's voice to your face: slightly too low, doubled, wrong."""
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
N = os.path.join(HERE, 'narration', 'lines')
O = os.path.join(HERE, 'narration', 'orig_lines')
os.makedirs(O, exist_ok=True)
for f in os.listdir(N):
    if f.endswith('.wav') and not os.path.exists(os.path.join(O, f)):
        shutil.copy(os.path.join(N, f), os.path.join(O, f))


def sox(*a):
    subprocess.run(['sox', *a], check=True, stderr=subprocess.DEVNULL)


def dur(p):
    return subprocess.run(['soxi', '-D', p], capture_output=True, text=True).stdout.strip()


FX = {
    'X01': ['pitch', '-180', 'overdrive', '3', 'reverb', '55', 'lowpass', '5000'],
    'X02': ['highpass', '300', 'lowpass', '2400', 'reverb', '80', '50', '100', 'vol', '0.6'],
    'X03': ['lowpass', '900', 'reverb', '25', 'overdrive', '2'],
    'X04': ['lowpass', '900', 'reverb', '25', 'overdrive', '2'],
    'X05': ['pitch', '-90', 'chorus', '0.6', '0.9', '45', '0.5', '0.3', '2', '-t', 'overdrive', '4', 'reverb', '30'],
    'X06': ['pitch', '-220', 'reverb', '60', 'lowpass', '4500'],
}
for k, fx in FX.items():
    src = os.path.join(O, k + '.wav')
    sox(src, os.path.join(N, k + '.wav'), *fx, 'trim', '0', dur(src), 'norm', '-3')
print('VOICE_FX_OK')
