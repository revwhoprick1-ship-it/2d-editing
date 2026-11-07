#!/usr/bin/env python3
"""Test an exported Short as a continuous loop (what the Shorts player does).

    python3 PIPELINE/quality_control/loop_test.py EXPORTS/VIDEO_002.mp4 --out VIDEOS/VIDEO_002/qc [--x3 OUT.mp4]

Checks on the *decoded export*, not on the project files:
  video  - the jump from the last frame to the first frame, compared with ordinary frame-to-frame
           changes inside the video (a cut would show up as an outlier); black / near-black frames
           anywhere in a 3x loop (ffmpeg blackdetect over the concatenation)
  audio  - decoded audio length vs video length; RMS in the 100 ms either side of the seam
           (an audio gap = a hole in the level); the sample jump across the seam vs local sample
           jumps (a click); silencedetect over the 3x loop
Writes loop_report.json, loop_seam_frames.png (last 4 + first 4 frames) and loop_seam_audio.png.
--x3 also writes the export looped 3 times (re-encoded) so a person can watch the seam.
"""
import argparse
import json
import os
import re
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw


def run(cmd):
    return subprocess.run(cmd, capture_output=True)


def decode_frames(path, w=270, h=480):
    r = run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    a = np.frombuffer(r.stdout, np.uint8)
    return a.reshape(-1, h, w, 3).astype(np.float32) / 255.0


def decode_audio(path, sr=48000):
    r = run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '2', '-ar', str(sr), '-'])
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--out', required=True)
    ap.add_argument('--x3', default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = {'file': a.video}
    # ------------------------------------------------------------- video seam
    F = decode_frames(a.video)
    n = len(F)
    diffs = np.abs(np.diff(F, axis=0)).mean(axis=(1, 2, 3))
    seam = float(np.abs(F[0] - F[-1]).mean())
    cuts = np.sort(diffs)[::-1]
    rep['video'] = {'frames': n, 'duration_s': n / 30, 'seam_diff': round(seam, 4),
                    'median_frame_diff': round(float(np.median(diffs)), 4),
                    'p90_frame_diff': round(float(np.percentile(diffs, 90)), 4),
                    'largest_cut_diffs': [round(float(x), 4) for x in cuts[:5]],
                    'seam_percentile_among_frame_changes': round(float((diffs < seam).mean() * 100), 1),
                    'first_frame_mean_luma': round(float(F[0].mean()), 3), 'last_frame_mean_luma': round(float(F[-1].mean()), 3),
                    'darkest_frame_mean_luma': round(float(F.mean(axis=(1, 2, 3)).min()), 3)}
    # strip of the seam
    strip = list(F[-4:]) + list(F[:4])
    W, H = 270, 480
    im = Image.new('RGB', (W * 8, H + 26), (15, 15, 18))
    d = ImageDraw.Draw(im)
    for i, f in enumerate(strip):
        im.paste(Image.fromarray((f * 255).astype(np.uint8)), (i * W, 26))
        lab = f'last-{3 - i}' if i < 4 else f'first+{i - 4}'
        d.text((i * W + 6, 6), lab + ('  | LOOP' if i == 4 else ''), fill=(255, 200, 60))
    im.save(os.path.join(a.out, 'loop_seam_frames.png'))
    # ------------------------------------------------------------- audio seam
    A = decode_audio(a.video)
    sr = 48000
    m = A.mean(1)
    rep['audio'] = {'decoded_duration_s': round(len(A) / sr, 4), 'video_minus_audio_ms': round((n / 30 - len(A) / sr) * 1000, 1)}
    L = int(round(n / 30 * sr))            # the loop length the player uses (video duration)
    loop = m[:L]
    w = int(0.1 * sr)
    rms = lambda x: float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9))
    rep['audio'].update({
        'rms_last_100ms_db': round(rms(loop[-w:]), 1), 'rms_first_100ms_db': round(rms(loop[:w]), 1),
        'rms_whole_db': round(rms(loop), 1),
        'seam_sample_jump': round(float(abs(loop[0] - loop[-1])), 5),
        'local_median_sample_jump': round(float(np.median(np.abs(np.diff(np.concatenate([loop[-2400:], loop[:2400]]))))), 5),
        'local_max_sample_jump': round(float(np.max(np.abs(np.diff(np.concatenate([loop[-2400:], loop[:2400]]))))), 5),
    })
    # waveform plot around the seam (+-0.5 s)
    seg = np.concatenate([loop[-sr // 2:], loop[:sr // 2]])
    PW, PH = 1200, 240
    pim = Image.new('RGB', (PW, PH), (18, 18, 22))
    pd = ImageDraw.Draw(pim)
    k = len(seg) // PW
    for x in range(PW):
        c = seg[x * k:(x + 1) * k]
        y0, y1 = PH / 2 - c.max() * PH / 2, PH / 2 - c.min() * PH / 2
        pd.line([(x, y0), (x, y1)], fill=(90, 200, 255))
    pd.line([(PW // 2, 0), (PW // 2, PH)], fill=(255, 80, 80))
    pd.text((6, 6), 'audio: last 0.5 s | first 0.5 s (red = loop point)', fill=(255, 200, 60))
    pim.save(os.path.join(a.out, 'loop_seam_audio.png'))
    # ------------------------------------------------------------- 3x loop: black / silence detection
    with tempfile.TemporaryDirectory() as td:
        lst = os.path.join(td, 'l.txt')
        open(lst, 'w').write(''.join(f"file '{os.path.abspath(a.video)}'\n" for _ in range(3)))
        out3 = a.x3 or os.path.join(td, 'x3.mp4')
        run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:v', 'libx264', '-preset', 'veryfast',
             '-crf', '23', '-c:a', 'aac', '-b:a', '192k', out3])
        r = run(['ffmpeg', '-hide_banner', '-nostats', '-i', out3, '-vf', 'blackdetect=d=0.03:pix_th=0.08',
                 '-af', 'silencedetect=n=-50dB:d=0.25', '-f', 'null', '-'])
        err = r.stderr.decode()
        rep['loop_x3'] = {'black_segments': re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', err),
                          'silences_over_250ms_below_-50dB': re.findall(r'silence_start: ([\d.]+)', err),
                          'duration_s': None}
        pr = run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out3])
        rep['loop_x3']['duration_s'] = float(pr.stdout.decode().strip() or 0)
    v, au = rep['video'], rep['audio']
    rep['checks'] = {
        'seam_picture_change_is_ordinary (below the 90th percentile of frame changes)': v['seam_diff'] <= v['p90_frame_diff'],
        'no_black_frame_at_seam': min(v['first_frame_mean_luma'], v['last_frame_mean_luma']) > 0.08,
        'no_black_segments_in_3x_loop': not rep['loop_x3']['black_segments'],
        'no_silence_in_3x_loop': not rep['loop_x3']['silences_over_250ms_below_-50dB'],
        'no_audio_gap_at_seam (both sides within 20 dB of the mix)': min(au['rms_last_100ms_db'], au['rms_first_100ms_db']) > au['rms_whole_db'] - 20,
        'no_click_at_seam (jump <= local max)': au['seam_sample_jump'] <= au['local_max_sample_jump'],
        'audio_video_length_match_within_25ms': abs(au['video_minus_audio_ms']) <= 25,
    }
    json.dump(rep, open(os.path.join(a.out, 'loop_report.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
