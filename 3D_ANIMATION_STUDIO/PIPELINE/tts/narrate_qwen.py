#!/usr/bin/env python3
"""Dialogue with Qwen3-TTS only (Apache-2.0, local CPU, no API).

    /opt/tools/qwen/bin/python PIPELINE/tts/narrate_qwen.py VIDEOS/VIDEO_0xx/script.json OUT_DIR [--only K01,L03] [--takes 2]

* script['qwen_voices'] = {who: voice description}. Step 1 (VoiceDesign 1.7B): one reference clip per character -> ref_<who>.wav
  (kept, so the voice never changes between runs). Step 2 (Base 1.7B voice clone): every line is cloned from its character's
  reference, so each character keeps ONE consistent voice. Lines with 'as' (copied voices) use that character's reference.
* emotion comes from the text/punctuation + the reference delivery; N takes, best Whisper word match wins
* lines tempo-tightened (atempo, pitch kept), trimmed; Whisper word timestamps -> timing.json (same format as before)
"""
import argparse, gc, json, os, re, subprocess
import numpy as np, soundfile as sf, torch

REF_TEXT = "Okay. Listen to me. We stay together, we keep walking, and nobody goes off alone. If something feels wrong, we turn around."
DESIGN = 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign'
BASE = 'Qwen/Qwen3-TTS-12Hz-1.7B-Base'


def norm(s):
    return re.sub(r"[^a-z0-9' ]", ' ', s.lower().replace('2001', 'two thousand one')).split()


def trim(y, sr, th=0.006, pad=0.12):
    a = np.abs(y)
    idx = np.where(a > th * a.max())[0]
    if not len(idx):
        return y
    return y[max(0, idx[0] - int(pad * sr)):idx[-1] + int(pad * sr)]


def atempo(y, sr, t):
    if abs(t - 1) < 1e-3:
        return y
    r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(sr), '-ac', '1', '-i', '-', '-af', f'atempo={t}',
                        '-f', 'f32le', '-'], input=y.astype(np.float32).tobytes(), capture_output=True)
    return np.frombuffer(r.stdout, np.float32)


def to16k(y, sr):
    from scipy.signal import resample_poly
    return resample_poly(y, 16000, sr).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('script'); ap.add_argument('out')
    ap.add_argument('--only', default=None); ap.add_argument('--takes', type=int, default=3)
    a = ap.parse_args()
    S = json.load(open(a.script))
    torch.set_num_threads(os.cpu_count())
    os.makedirs(os.path.join(a.out, 'lines'), exist_ok=True)
    from qwen_tts import Qwen3TTSModel
    from faster_whisper import WhisperModel
    voices = S['qwen_voices']
    refp = {w: os.path.join(a.out, f'ref_{w}.wav') for w in voices}
    if any(not os.path.exists(p) for p in refp.values()):
        dm = Qwen3TTSModel.from_pretrained(DESIGN, device_map='cpu', dtype=torch.float32)
        for w, desc in voices.items():
            if not os.path.exists(refp[w]):
                torch.manual_seed(7)
                y, sr = dm.generate_voice_design(text=REF_TEXT, language='English', instruct=desc)
                sf.write(refp[w], trim(y[0], sr), sr)
                print('REF', w, flush=True)
        del dm; gc.collect()
    m = Qwen3TTSModel.from_pretrained(BASE, device_map='cpu', dtype=torch.float32)
    prompts = {w: m.create_voice_clone_prompt(ref_audio=refp[w], ref_text=REF_TEXT) for w in voices}
    wm = WhisperModel('small.en', device='cpu', compute_type='int8')
    only = set(a.only.split(',')) if a.only else None
    tempo = S.get('tempo', 1.0)
    report, sr = [], 24000
    for ln in S['lines']:
        p = os.path.join(a.out, 'lines', ln['id'] + '.wav')
        if (only and ln['id'] not in only) or (not only and os.path.exists(p)):
            continue
        who = ln.get('as', ln.get('who'))
        best = None
        for k in range(a.takes):
            torch.manual_seed(1000 * k + int(ln['id'][1:]))
            ys, sr = m.generate_voice_clone(text=ln['text'], language='English', voice_clone_prompt=prompts[who],
                                               max_new_tokens=int(12 * (0.55 * len(ln['text'].split()) + 2.5)))  # stops runaway takes
            y = trim(np.asarray(ys[0], np.float32), sr)
            y = trim(atempo(y, sr, ln.get('tempo', tempo)), sr)
            segs, _ = wm.transcribe(to16k(y, sr), word_timestamps=False)
            hyp = norm(' '.join(s.text for s in segs))
            ref_w = norm(ln['text'])
            miss = sum(1 for x in ref_w if x not in hyp) + max(0, len(hyp) - len(ref_w))
            score = (miss, -float(np.std(y)))
            print(ln['id'], 'take', k, 'miss', miss, ' '.join(hyp), flush=True)
            if best is None or score < best[0]:
                best = (score, y)
            if miss == 0:
                break
        sf.write(p, best[1], sr)
        report.append({'id': ln['id'], 'word_misses': best[0][0]})
    # assemble + word timing
    out, lines, words, t = [], [], [], 0.0
    for ln in S['lines']:
        y, _ = sf.read(os.path.join(a.out, 'lines', ln['id'] + '.wav'))
        segs, _ = wm.transcribe(to16k(y, sr), word_timestamps=True)
        hw = [w for s in segs for w in s.words]
        tw = ln['text'].split()
        # map script words onto whisper timings (same count -> 1:1, else proportional)
        if len(hw) == len(tw):
            spans = [(w.start, w.end) for w in hw]
        else:
            d = len(y) / sr
            spans = [(d * i / len(tw), d * (i + 1) / len(tw)) for i in range(len(tw))]
        for word, (s0, s1) in zip(tw, spans):
            words.append({'line': ln['id'], 'text': word, 'start': round(t + s0, 3), 'end': round(t + s1, 3)})
        lines.append({'id': ln['id'], 'who': ln.get('who', 'N'), 'text': ln['text'], 'start': round(t, 3), 'end': round(t + len(y) / sr, 3),
                      'delivery': ln.get('delivery', ''), 'speed': ln.get('tempo', tempo)})
        out.append(y)
        t += len(y) / sr
        gap = np.zeros(int(ln.get('pause_after', 0.2) * sr))
        out.append(gap)
        t += len(gap) / sr
    full = np.concatenate(out)
    sf.write(os.path.join(a.out, 'narration_raw.wav'), full, sr)
    json.dump({'voice': 'qwen3-tts', 'sample_rate': sr, 'lines': lines, 'words': words,
               'duration': round(len(full) / sr, 3)}, open(os.path.join(a.out, 'timing.json'), 'w'), indent=1)
    json.dump(report, open(os.path.join(a.out, 'takes_report.json'), 'w'), indent=1)
    print('NARRATION_OK', round(len(full) / sr, 2), 's')


if __name__ == '__main__':
    main()
