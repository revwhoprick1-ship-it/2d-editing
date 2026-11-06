#!/usr/bin/env python3
"""Assemble rendered shot frames + mixed audio + word-timed captions into the final Short.

    python3 PIPELINE/editing/assemble.py VIDEOS/VIDEO_001 --frames-root VIDEOS/VIDEO_001/frames \
        --step 1 --out EXPORTS/VIDEO_001_final.mp4 [--no-captions] [--crf 16]

* Shots are concatenated in the order of the video module's SHOTS dict (global frames).
* Missing frames are filled with the previous frame (so a preview rendered every Nth
  frame still plays in real time).
* Upscales to 1080x1920 (Lanczos + light sharpening), burns ASS captions, muxes AAC.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
FONT_DIR = os.path.join(STUDIO, 'ASSETS', 'fonts')

EMPHASIS = {'attack', 'blood', 'cell', 'heart', 'millions', 'valves', 'slam', 'lub-dub', 'lungs', 'squeeze', 'oxygen',
            'carbon', 'dioxide', 'paper', 'neutrophil', 'intruder', 'whole', 'kick', 'launches', 'artery', 'survived',
            'shoe', 'barely', 'notices', 'hundred'}


def shots_from_module(video_dir):
    name = os.path.basename(os.path.normpath(video_dir)).lower().replace('_', '')
    src = open(os.path.join(STUDIO, 'PIPELINE', 'blender_scripts', 'videos', name + '.py')).read()
    m = re.search(r'SHOTS = \{(.*?)\n\}', src, re.S)
    return [(k, int(a), int(b)) for k, a, b in re.findall(r"'(SH\w+)': \((\d+), (\d+)\)", m.group(1))]


def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'


def build_captions(timing, offset, out_path, W=1080, H=1920, max_words=3):
    words = [w for w in timing['words'] if w['text'].strip()]
    chunks, cur = [], []
    for i, w in enumerate(words):
        is_punct = not re.search(r'[A-Za-z0-9]', w['text'])
        if is_punct:
            if cur:
                cur[-1]['punct'] = cur[-1].get('punct', '') + w['text']
                if w['text'] in '.?!' or w['text'] == ',':
                    chunks.append(cur)
                    cur = []
            continue
        if cur and (len(cur) >= max_words or w['start'] - cur[-1]['end'] > 0.25 or w['line'] != cur[-1]['line']):
            chunks.append(cur)
            cur = []
        cur.append(dict(w))
    if cur:
        chunks.append(cur)
    lines = []
    for i, ch in enumerate(chunks):
        st = ch[0]['start'] + offset
        en = (chunks[i + 1][0]['start'] + offset) if i + 1 < len(chunks) else ch[-1]['end'] + offset + 0.4
        en = min(en, ch[-1]['end'] + offset + 0.6)
        if en - st < 0.25:
            en = st + 0.25
        parts = []
        for w in ch:
            txt = w['text'].upper()
            key = re.sub(r'[^a-z\-]', '', w['text'].lower())
            if key in EMPHASIS:
                parts.append(r'{\c&H3DC8FF&}' + txt + r'{\c&HFFFFFF&}')
            else:
                parts.append(txt)
        text = ' '.join(parts)
        pop = r'{\fscx82\fscy82\t(0,90,\fscx104\fscy104)\t(90,160,\fscx100\fscy100)}'
        lines.append(f'Dialogue: 0,{ass_time(st)},{ass_time(en)},Cap,,0,0,0,,{pop}{text}')
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,78,&H00FFFFFF,&H00FFFFFF,&H00101010,&H96000000,0,0,0,0,100,100,1,0,1,7,4,2,70,70,{int(H * 0.30)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(out_path, 'w') as f:
        f.write(header + '\n'.join(lines) + '\n')
    return len(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video_dir')
    ap.add_argument('--frames-root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--audio', default=None)
    ap.add_argument('--no-captions', action='store_true')
    ap.add_argument('--crf', type=int, default=16)
    ap.add_argument('--preset', default='slow')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--denoise', default='1.5:1.2:4:3', help="hqdn3d params; '' to disable")
    a = ap.parse_args()
    vd = os.path.abspath(a.video_dir)
    shots = shots_from_module(vd)
    seq_dir = os.path.join(vd, '_seq')
    shutil.rmtree(seq_dir, ignore_errors=True)
    os.makedirs(seq_dir)
    last = None
    missing = 0
    k = 0
    for sid, f0, f1 in shots:
        d = os.path.join(a.frames_root, sid)
        for f in range(f0, f1):
            p = os.path.join(d, f'{f:04d}.png')
            if os.path.exists(p):
                last = p
            else:
                missing += 1
            if last is None:
                continue
            os.symlink(os.path.abspath(last), os.path.join(seq_dir, f'{k:05d}.png'))
            k += 1
    print('frames', k, 'filled', missing)
    timing = json.load(open(os.path.join(vd, 'audio', 'narration', 'timing.json')))
    cues = json.load(open(os.path.join(vd, 'audio', 'cues.json')))
    audio = a.audio or os.path.join(vd, 'audio', 'mix_master.wav')
    # mild spatio-temporal denoise BEFORE the upscale (removes low-sample EEVEE grain),
    # then Lanczos 2x and light sharpening
    vf = ([f'hqdn3d={a.denoise}'] if a.denoise else []) + ['scale=1080:1920:flags=lanczos', 'unsharp=5:5:0.6:5:5:0.0']
    if not a.no_captions:
        ass = os.path.join(vd, 'captions.ass')
        n = build_captions(timing, cues.get('narration_offset', 0.0), ass)
        print('captions', n)
        vf.append(f"ass={ass}:fontsdir={FONT_DIR}")
    vf.append('format=yuv420p')
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-framerate', str(a.fps), '-i',
           os.path.join(seq_dir, '%05d.png'), '-i', audio, '-vf', ','.join(vf),
           '-c:v', 'libx264', '-preset', a.preset, '-crf', str(a.crf), '-profile:v', 'high', '-level', '4.2',
           '-pix_fmt', 'yuv420p', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
           '-movflags', '+faststart', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest', a.out]
    subprocess.run(cmd, check=True)
    shutil.rmtree(seq_dir, ignore_errors=True)
    print('EXPORT_OK', a.out)


if __name__ == '__main__':
    main()
