#!/usr/bin/env python3
"""Inspect an exported video: container/stream specs, loudness, black/frozen frames,
and a contact sheet of frames at the start, middle, end and around every cut.

    python3 PIPELINE/quality_control/qc_video.py EXPORTS/VIDEO_001.mp4 --video-dir VIDEOS/VIDEO_001 \
        --out VIDEOS/VIDEO_001/qc
Writes qc_report.json and contact_*.png.  A person (or the pipeline operator)
must still LOOK at the contact sheets; this tool only gathers the evidence.
"""
import argparse
import json
import os
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'editing'))


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(['ffprobe', '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', path])
    return json.loads(r.stdout)


def loudness(path):
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'])
    txt = r.stderr[-2500:]
    get = lambda k: (re.findall(k + r':\s+(-?[\d.]+)', txt) or [None])[-1]
    return {'integrated_lufs': float(get('I')), 'lra_lu': float(get('LRA')), 'true_peak_dbfs': float(get('Peak'))}


def detect(path):
    r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-vf',
             'blackdetect=d=0.15:pix_th=0.06,freezedetect=n=0.002:d=1.5', '-an', '-f', 'null', '-'])
    black = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', r.stderr)
    freeze = re.findall(r'freeze_start: ([\d.]+)', r.stderr)
    return {'black_segments': [(float(a), float(b)) for a, b in black], 'freeze_starts': [float(f) for f in freeze]}


def grab(path, t, out):
    run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1',
         '-vf', 'scale=270:480', out])
    return out


def sheet(images, labels, out, cols=8):
    ims = [Image.open(p) for p in images if os.path.exists(p)]
    if not ims:
        return
    W, H = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    s = Image.new('RGB', (cols * W, rows * (H + 22)), (15, 15, 18))
    d = ImageDraw.Draw(s)
    for i, (im, lb) in enumerate(zip(ims, labels)):
        x, y = (i % cols) * W, (i // cols) * (H + 22)
        s.paste(im, (x, y + 22))
        d.text((x + 4, y + 4), lb, fill=(255, 200, 60))
    s.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--video-dir', default=None)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    pr = probe(a.video)
    v = [s for s in pr['streams'] if s['codec_type'] == 'video'][0]
    au = [s for s in pr['streams'] if s['codec_type'] == 'audio']
    dur = float(pr['format']['duration'])
    rep = {'file': a.video, 'duration_s': round(dur, 3), 'size_mb': round(int(pr['format']['size']) / 1e6, 2),
           'video': {'codec': v['codec_name'], 'profile': v.get('profile'), 'width': v['width'], 'height': v['height'],
                     'fps': v['r_frame_rate'], 'pix_fmt': v['pix_fmt'], 'color_primaries': v.get('color_primaries'),
                     'bitrate_kbps': round(int(pr['format']['bit_rate']) / 1000)},
           'audio': {'codec': au[0]['codec_name'], 'sample_rate': au[0]['sample_rate'], 'channels': au[0]['channels'],
                     'bitrate_kbps': round(int(au[0].get('bit_rate', 0)) / 1000)} if au else None}
    rep['loudness'] = loudness(a.video) if au else None
    rep['detect'] = detect(a.video)
    checks = {
        'is_1080x1920': (v['width'], v['height']) == (1080, 1920),
        'fps_30': v['r_frame_rate'] in ('30/1', '30000/1000'),
        'h264': v['codec_name'] == 'h264',
        'yuv420p': v['pix_fmt'] == 'yuv420p',
        'aac': bool(au) and au[0]['codec_name'] == 'aac',
        'loudness_-14_to_-16': bool(rep['loudness']) and -16.5 <= rep['loudness']['integrated_lufs'] <= -13.5,
        'true_peak_le_-1': bool(rep['loudness']) and rep['loudness']['true_peak_dbfs'] <= -0.9,
        'no_black_segments': not rep['detect']['black_segments'],
    }
    rep['checks'] = checks
    # frames: start/middle/end + every cut +/- 2 frames
    times = [0.05, dur / 2, dur - 0.1]
    labels = ['start', 'middle', 'end']
    if a.video_dir:
        from assemble import shots_from_module
        for sid, f0, f1 in shots_from_module(a.video_dir):
            for tt, lb in ((f0 / 30 + 0.05, f'{sid} in'), ((f0 + f1) / 2 / 30, f'{sid} mid'), (f1 / 30 - 0.07, f'{sid} out')):
                if tt < dur:
                    times.append(tt)
                    labels.append(f'{lb} {tt:.2f}s')
    paths = [grab(a.video, t, os.path.join(a.out, f'f_{i:03d}.png')) for i, t in enumerate(times)]
    sheet(paths[:3], labels[:3], os.path.join(a.out, 'contact_start_mid_end.png'), cols=3)
    sheet(paths[3:], labels[3:], os.path.join(a.out, 'contact_shots.png'), cols=9)
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass
    json.dump(rep, open(os.path.join(a.out, 'qc_report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
