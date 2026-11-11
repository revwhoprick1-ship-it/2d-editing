#!/usr/bin/env python3
"""VIDEO_023 voice FX (sox; explicit lengths; faded tails). Z01 = a zombie talking through the steel gate (metallic, calm).
D = police drone megaphone (band-limited, distorted, slapback). T04 = 'Tara' after she turned: too calm, slightly lower,
through the freezer door (muffled). T03 = Tara yelling across the store (roomy)."""
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
FX = {'Z01': ['pitch', '-150', 'overdrive', '3', 'echo', '0.8', '0.7', '18', '0.35'],
      'D01': ['highpass', '500', 'lowpass', '3000', 'overdrive', '10', 'echo', '0.8', '0.6', '120', '0.3'],
      'D02': ['highpass', '500', 'lowpass', '3000', 'overdrive', '10', 'echo', '0.8', '0.6', '120', '0.3'],
      'T03': ['reverb', '55'], 'T04': ['pitch', '-90', 'lowpass', '1800', 'reverb', '20']}
for k, fx in FX.items():
    a = os.path.join(tmp, k + '.wav')
    sox(os.path.join(O, k + '.wav'), a, *fx, 'pad', '0', '0.3')
    sox(a, os.path.join(N, k + '.wav'), 'fade', 't', '0.01', dur(a), '0.25', 'norm', '-3')
a = os.path.join(tmp, 'K08_t.wav')                                                     # CTA must stay under 3 s
sox(os.path.join(O, 'K08.wav'), a, 'tempo', '-s', '1.22', 'pad', '0', '0.1')
sox(a, os.path.join(N, 'K08.wav'), 'fade', 't', '0.01', dur(a), '0.2', 'norm', '-3')
shutil.rmtree(tmp)
print('VOICE_FX_OK')
