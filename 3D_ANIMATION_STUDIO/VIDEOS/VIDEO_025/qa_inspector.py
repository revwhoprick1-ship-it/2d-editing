#!/usr/bin/env python3
"""VIDEO_025 QA: format + loudness (ffmpeg ebur128: integrated LUFS, true peak), black/frozen detection (qc_video.py), and a
Whisper transcript of every line FROM THE FINAL MP4 compared word-by-word with script.json.

    python3 VIDEOS/VIDEO_025/qa_inspector.py EXPORTS/VIDEO_025_The_Taxi_Final.mp4"""
import json, os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
mp4 = sys.argv[1]
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', mp4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
lufs = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); tp = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate:format=duration', '-of', 'json', mp4],
                       capture_output=True, text=True).stdout
info = json.loads(probe)
subprocess.run([sys.executable, os.path.join(STUDIO, 'PIPELINE', 'quality_control', 'qc_video.py'), mp4, '--out', os.path.join(HERE, 'qc')],
               capture_output=True)
qc = json.load(open(os.path.join(HERE, 'qc', 'qc_report.json')))
print('FORMAT', [(s_.get('codec_name'), s_.get('width'), s_.get('height'), s_.get('r_frame_rate')) for s_ in info['streams']],
      'duration', info['format']['duration'])
print(f'LOUDNESS integrated {lufs} LUFS (target -14)  true peak {tp} dBTP (target <= -2)  ->', 'PASS' if abs(lufs + 14) <= 0.6 and tp <= -2 else 'FAIL')
print('BLACK', qc['detect']['black_segments'], 'FROZEN', qc['detect']['freeze_starts'])
wav = os.path.join(tempfile.gettempdir(), 'qa025.wav')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', mp4, '-ac', '1', '-ar', '16000', wav], check=True)
code = r'''
import json, re, sys, numpy as np, soundfile as sf
from faster_whisper import WhisperModel
T = json.load(open(sys.argv[1])); y, sr = sf.read(sys.argv[2]); m = WhisperModel('small.en', device='cpu', compute_type='int8')
NUM = {'1': 'one', '2': 'two', '3': 'three', '60': 'sixty', '50': 'fifty', '11': 'eleven', '59': 'fifty-nine'}
norm = lambda s: [NUM.get(w, w) for w in re.sub(r"[^a-z0-9' ]", ' ', s.lower()).split()]
bad = 0
for l in T['lines']:
    seg = y[int(l['start'] * sr):int((l['end'] + 0.15) * sr)].astype(np.float32)
    hyp = ' '.join(s.text for s in m.transcribe(seg)[0]).strip()
    miss = [w for w in norm(l['text']) if w not in norm(hyp)]
    bad += bool(miss)
    print(f"{l['id']} {l['start']:6.2f}s  {'OK  ' if not miss else 'DIFF'} | {hyp}" + (f'   (missing: {miss})' if miss else ''))
print('TRANSCRIPT', 'PASS' if bad == 0 else f'{bad} line(s) differ')
'''
subprocess.run(['/opt/tools/tts312/bin/python', '-c', code, os.path.join(HERE, 'audio', 'narration', 'timing.json'), wav])
