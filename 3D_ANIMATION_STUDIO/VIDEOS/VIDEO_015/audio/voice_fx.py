#!/usr/bin/env python3
"""VIDEO_015 voice FX (sox): your lines shake (tremolo), the class speaks as one (chorus mix), Kessrah = deep voice + your voice.
Originals are kept in narration/orig_lines; outputs keep the original length so the timing stays valid."""
import os
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
N = os.path.join(HERE, 'narration', 'lines')
O = os.path.join(HERE, 'narration', 'orig_lines')
CH = os.path.join(HERE, 'chorus', 'lines')
os.makedirs(O, exist_ok=True)
for f in os.listdir(N):
    if f.endswith('.wav') and not os.path.exists(os.path.join(O, f)):
        shutil.copy(os.path.join(N, f), os.path.join(O, f))


def sox(*a):
    subprocess.run(['sox', *a], check=True, stderr=subprocess.DEVNULL)


def dur(p):
    return subprocess.run(['soxi', '-D', p], capture_output=True, text=True).stdout.strip()


for f in ('Y01', 'Y02', 'Y03', 'Y04', 'Y05', 'Y06', 'Y07', 'Y08', 'Y09', 'Y10', 'Y11'):
    sox(os.path.join(O, f + '.wav'), os.path.join(N, f + '.wav'), 'tremolo', '7', '18', 'norm', '-3')

tmp = tempfile.mkdtemp()


def mix(line, extra, post):
    src = os.path.join(O, line + '.wav')
    parts = []
    for i, p in enumerate([src] + extra):
        q = os.path.join(tmp, f'{line}_{i}.wav')
        sox(p, '-r', '24000', '-c', '1', q, 'norm', '-6')
        parts.append(q)
    m = os.path.join(tmp, f'{line}_m.wav')
    sox('-m', *parts, m)
    sox(m, os.path.join(N, line + '.wav'), 'trim', '0', dur(src), *post, 'norm', '-3')


mix('C01', [os.path.join(CH, c) for c in ('C13.wav', 'C15.wav', 'C17.wav')], ['reverb', '40'])
mix('C02', [os.path.join(CH, c) for c in ('C12.wav', 'C14.wav', 'C16.wav', 'C18.wav')], ['reverb', '40'])
deep = os.path.join(tmp, 'k_deep.wav')
sox(os.path.join(O, 'K01.wav'), '-r', '24000', '-c', '1', deep, 'pitch', '-300')
yours = os.path.join(tmp, 'k_you.wav')
sox(os.path.join(CH, 'C19.wav'), '-r', '24000', '-c', '1', yours)
km = os.path.join(tmp, 'k_m.wav')
sox('-m', deep, yours, km)
sox(km, os.path.join(N, 'K01.wav'), 'trim', '0', dur(os.path.join(O, 'K01.wav')), 'overdrive', '4', 'reverb', '60', 'norm', '-3')
sox(os.path.join(O, 'H02.wav'), os.path.join(N, 'H02.wav'), 'pitch', '-80', 'reverb', '30', 'norm', '-3')
shutil.rmtree(tmp)
print('VOICE_FX_OK')
