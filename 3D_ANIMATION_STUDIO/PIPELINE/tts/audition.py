#!/usr/bin/env python3
"""Audition Kokoro voices on representative lines and score them objectively.
    /opt/tools/tts312/bin/python PIPELINE/tts/audition.py AUDIO/narrator/auditions
"""
import json, os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_qc import qc_file
from kokoro import KPipeline
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
VOICES = ['af_heart', 'af_bella', 'af_nicole', 'am_michael', 'am_fenrir', 'am_puck', 'am_adam', 'am_eric', 'am_liam', 'am_onyx']
LINES = {
    'hook': "You've been shrunk smaller than a blood cell... and your own body is about to attack you.",
    'science': "A neutrophil. Your body's first responder. It swallows intruders whole, in your capillaries and your lungs.",
    'suspense': "Then... something notices you.",
    'excited': "And it launches you straight into the biggest artery you have!",
}
pipe = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
rows = []
for v in VOICES:
    for k, t in LINES.items():
        chunks = [r.audio.numpy() for r in pipe(t, voice=v, speed=1.0, split_pattern=None)]
        a = np.concatenate(chunks)
        p = os.path.join(OUT, f'{v}_{k}.wav')
        sf.write(p, a, 24000)
        q = qc_file(p, t)
        q.update(voice=v, line=k)
        rows.append(q)
        print(v, k, q['wer'], q['words_per_sec'], q['f0_range_semitones_p5_p95'], q['f0_std_semitones'], q['mismatches'][:4], flush=True)
json.dump(rows, open(os.path.join(OUT, 'audition_results.json'), 'w'), indent=1)
# summary per voice
summ = {}
for r in rows:
    s = summ.setdefault(r['voice'], {'wer': [], 'f0r': [], 'f0s': [], 'wps': []})
    s['wer'].append(r['wer']); s['f0r'].append(r['f0_range_semitones_p5_p95']); s['f0s'].append(r['f0_std_semitones']); s['wps'].append(r['words_per_sec'])
print('\nVOICE        meanWER  f0range  f0std  wps')
for v, s in summ.items():
    print(f"{v:12s} {np.mean(s['wer']):.3f}   {np.mean(s['f0r']):5.2f}   {np.mean(s['f0s']):4.2f}  {np.mean(s['wps']):.2f}")
