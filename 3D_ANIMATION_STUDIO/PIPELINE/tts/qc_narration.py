#!/usr/bin/env python3
"""QC every narration line of a video: ASR WER, pacing, pitch movement, levels.
    /opt/tools/tts312/bin/python PIPELINE/tts/qc_narration.py VIDEOS/VIDEO_00X/audio/narration
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from voice_qc import qc_file
d = sys.argv[1]
t = json.load(open(os.path.join(d, 'timing.json')))
rep = []
for ln in t['lines']:
    q = qc_file(os.path.join(d, 'lines', ln['id'] + '.wav'), ln['text'])
    q['id'] = ln['id']; q['delivery'] = ln['delivery']
    rep.append(q)
    flag = 'OK ' if q['wer'] == 0 else 'CHECK'
    print(f"{flag} {ln['id']} {ln['delivery']:9s} {q['duration_s']:5.2f}s wps={q['words_per_sec']:.2f} f0rng={q['f0_range_semitones_p5_p95']:.1f}st WER={q['wer']:.2f} {q['mismatches'] if q['wer'] else ''} | {q['transcript']}")
json.dump(rep, open(os.path.join(d, 'qc_report.json'), 'w'), indent=1, default=str)
print('TOTAL', t['duration'])
