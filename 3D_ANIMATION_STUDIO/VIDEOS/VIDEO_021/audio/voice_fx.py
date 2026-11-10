#!/usr/bin/env python3
"""VIDEO_021 voice FX (sox). Q01 = the crash memory (underwater, warbling, dissolving). P = basement Mom (hoarse, concrete room).
O at night = the copy in the dark hallway / at the top of the stairs (close, a little too clean). X01 'Pick me.' = BOTH voices in
unison: the O render + a hoarse lower copy of itself, 25 ms apart."""
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


BASE = ['reverb', '45', '50', '60', 'highpass', '120']
FX = {'Q01': ['lowpass', '1800', 'tremolo', '5', '40', 'reverb', '70', 'pitch', '-40'],
      'P01': ['overdrive', '4', *BASE, 'lowpass', '3000'], 'P02': ['overdrive', '4', *BASE, 'lowpass', '3000'],
      'P03': ['overdrive', '3', 'reverb', '40'], 'P04': ['overdrive', '3', 'reverb', '40'],
      'O01': ['reverb', '12'], 'O04': ['reverb', '35', '50', '40'], 'O05': ['reverb', '35', '50', '40']}
for k, fx in FX.items():
    src = os.path.join(O, k + '.wav')
    sox(src, os.path.join(N, k + '.wav'), *fx, 'fade', 't', '0.01', '-0', '0.25', 'norm', '-3')   # keep the reverb tail, fade it
tmp = tempfile.mkdtemp()
src = os.path.join(O, 'X01.wav')
a, b, m = (os.path.join(tmp, x) for x in ('a.wav', 'b.wav', 'm.wav'))
sox(src, '-r', '24000', '-c', '1', a, 'norm', '-6')
sox(src, '-r', '24000', '-c', '1', b, 'pitch', '-180', 'overdrive', '6', 'pad', '0.025', 'norm', '-7')
sox('-m', a, b, m)
sox(m, os.path.join(N, 'X01.wav'), 'reverb', '40', 'fade', 't', '0.01', '-0', '0.3', 'norm', '-3')
shutil.rmtree(tmp)
print('VOICE_FX_OK')
