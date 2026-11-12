#!/usr/bin/env python3
"""VIDEO_026 QA inspector — everything is measured on the FINAL exported MP4.

    python3 studio/qa_inspector.py [EXPORTS/VIDEO_026_two_bobs_mimic.mp4]

1. Format: H.264 + AAC, 1080x1920, 30 fps, 56.0 s (1,680 frames).
2. Loudness: integrated LUFS (target -14 +/- 0.6) and true peak (<= -2 dBTP), ffmpeg ebur128 after AAC encoding.
3. Black / frozen frames (PIPELINE/quality_control/qc_video.py).
4. Contact sheet at 1 fps -> qc/contact_sheet_1fps.jpg.
5. Whisper (faster-whisper small.en) transcript of every line cut out of the final mix, compared word by word with script.json.
6. Loop: the last frame against frame 0 (mean absolute pixel difference) and the audio level around the loop point.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
STUDIO = os.path.abspath(os.path.join(VIDEO, '..', '..'))
mp4 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(STUDIO, 'EXPORTS', 'VIDEO_026_two_bobs_mimic.mp4')
QC = os.path.join(VIDEO, 'qc'); os.makedirs(QC, exist_ok=True)
report = {}

r = subprocess.run(['ffmpeg', '-hide_banner', '-i', mp4, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
lufs = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]); tp = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1])
info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration',
                                  '-of', 'json', mp4], capture_output=True, text=True).stdout)
vs = [s for s in info['streams'] if s.get('width')][0]; as_ = [s for s in info['streams'] if not s.get('width')][0]
fmt_ok = (vs['codec_name'] == 'h264' and as_['codec_name'] == 'aac' and vs['width'] == 1080 and vs['height'] == 1920 and vs['r_frame_rate'] == '30/1'
          and abs(float(info['format']['duration']) - 56.0) < 0.05)
print(f"FORMAT {vs['codec_name']}+{as_['codec_name']} {vs['width']}x{vs['height']} {vs['r_frame_rate']} fps, {info['format']['duration']} s, "
      f"{vs.get('nb_frames')} frames ->", 'PASS' if fmt_ok else 'FAIL')
loud_ok = abs(lufs + 14) <= 0.6 and tp <= -2.0
print(f'LOUDNESS integrated {lufs} LUFS (target -14)  true peak {tp} dBTP (limit -2) ->', 'PASS' if loud_ok else 'FAIL')
subprocess.run([sys.executable, os.path.join(STUDIO, 'PIPELINE', 'quality_control', 'qc_video.py'), mp4, '--out', QC], capture_output=True)
qc = json.load(open(os.path.join(QC, 'qc_report.json')))
black, frozen = qc['detect']['black_segments'], qc['detect']['freeze_starts']
print('BLACK', black, 'FROZEN', frozen, '->', 'PASS' if not black and not frozen else 'CHECK')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-vf', 'fps=1,scale=135:240,tile=14x4', '-frames:v', '1', os.path.join(QC, 'contact_sheet_1fps.jpg')], check=True)
print('CONTACT SHEET', os.path.join(QC, 'contact_sheet_1fps.jpg'))
# loop check: last frame vs first frame, and audio RMS just before / after the loop point
tmp = tempfile.mkdtemp()
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', mp4, '-vf', 'select=eq(n\\,0)', '-frames:v', '1', os.path.join(tmp, 'f0.png')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.05', '-i', mp4, '-update', '1', '-frames:v', '1', os.path.join(tmp, 'fl.png')], check=True)
wav = os.path.join(tmp, 'qa026.wav')
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', mp4, '-ac', '1', '-ar', '16000', wav], check=True)
code = r'''
import json, re, sys, numpy as np, soundfile as sf
from PIL import Image
from faster_whisper import WhisperModel
T = json.load(open(sys.argv[1])); y, sr = sf.read(sys.argv[2]); tmp = sys.argv[3]
a = np.asarray(Image.open(tmp + '/f0.png').convert('L').resize((270, 480)), float); b = np.asarray(Image.open(tmp + '/fl.png').convert('L').resize((270, 480)), float)
print('LOOP picture: mean abs difference last frame vs frame 0 = %.1f / 255 ->' % np.abs(a - b).mean(), 'PASS' if np.abs(a - b).mean() < 22 else 'CHECK')
rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
print('LOOP audio: last 0.15 s %.1f dBFS | first 0.15 s %.1f dBFS (the slam)' % (rms(y[-int(0.15 * sr):]), rms(y[:int(0.15 * sr)])))
m = WhisperModel('small.en', device='cpu', compute_type='int8')
NUM = {'1': 'one', '2': 'two', '3': 'three', '5': 'five', '20': 'twenty', 'tv': 'tv'}
def norm(s):
    out = []
    for w in re.sub(r"[^a-z0-9' ]", ' ', s.lower().replace('-', ' ')).split():
        out.append(NUM.get(w, w))
    return out
bad = 0
for l in T['lines']:
    seg = y[max(0, int((l['start'] - 0.12) * sr)):int((l['end'] + 0.2) * sr)].astype(np.float32)
    hyp = ' '.join(s.text for s in m.transcribe(seg, language='en')[0]).strip()
    miss = [w for w in norm(l['text']) if w not in norm(hyp)]
    bad += bool(miss)
    print(f"{l['id']} {l['start']:6.2f}s  {'OK  ' if not miss else 'DIFF'} | {hyp}" + (f'   (missing: {miss})' if miss else ''))
n = len(T['lines'])
print('TRANSCRIPT %d/%d lines exact ->' % (n - bad, n), 'PASS' if bad == 0 else 'CHECK')
'''
subprocess.run(['/opt/tools/tts312/bin/python', '-c', code, os.path.join(VIDEO, 'audio', 'narration', 'timing.json'), wav, tmp])
