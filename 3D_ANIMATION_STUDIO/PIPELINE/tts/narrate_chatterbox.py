#!/usr/bin/env python3
"""Expressive male narration with Chatterbox (MIT, runs on CPU), voice timbre from a free Kokoro voice.

    /opt/tools/cbx/bin/python PIPELINE/tts/narrate_chatterbox.py VIDEOS/VIDEO_003/script.json OUT_DIR [--only L03,L05] [--takes 2]

* reference voice: "kokoro:<voice>" -> a reference clip is rendered with Kokoro (Apache-2.0) in the
  tts312 venv, Chatterbox copies its timbre and adds emotion ("exaggeration" per line)
* each line: N takes; the take with the best Whisper word match, then the widest pitch range, wins
* lines are tempo-tightened (ffmpeg atempo, pitch kept), silence-trimmed, joined with pause_after
* Whisper word timestamps -> timing.json in the same format as narrate.py (captions + edit sync)
"""
import argparse, json, os, re, subprocess, sys
import numpy as np, soundfile as sf, torch, torchaudio as ta

HERE = os.path.dirname(os.path.abspath(__file__))
TTS312 = '/opt/tools/tts312/bin/python'


def kokoro_ref(voice, path):
    if os.path.exists(path):
        return path
    code = ("from kokoro import KPipeline; import soundfile as sf, numpy as np; p=KPipeline(lang_code='a'); "
            "t='Okay, listen to this. Yesterday something completely ridiculous happened, and honestly, nobody saw it coming. I mean nobody!'; "
            f"a=np.concatenate([x.audio.numpy() for x in p(t, voice='{voice}')]); sf.write('{path}', a, 24000)")
    subprocess.run([TTS312, '-c', code], check=True, capture_output=True)
    return path


def norm(s):
    return re.sub(r"[^a-z0-9' ]", ' ', s.lower().replace('2001', 'two thousand one')).split()


def trim(y, sr, th=0.012, pad=0.04):
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
    return ta.functional.resample(torch.tensor(y, dtype=torch.float32), sr, 16000).numpy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('script'); ap.add_argument('out')
    ap.add_argument('--only', default=None); ap.add_argument('--takes', type=int, default=2)
    a = ap.parse_args()
    S = json.load(open(a.script))
    os.makedirs(os.path.join(a.out, 'lines'), exist_ok=True)
    ref = S.get('voice_ref', 'kokoro:am_fenrir')
    if ref.startswith('kokoro:'):
        ref = kokoro_ref(ref.split(':')[1], os.path.join(a.out, f"ref_{ref.split(':')[1]}.wav"))
    from chatterbox.tts import ChatterboxTTS
    from faster_whisper import WhisperModel
    m = ChatterboxTTS.from_pretrained(device='cpu')
    wm = WhisperModel('small.en', device='cpu', compute_type='int8')
    only = set(a.only.split(',')) if a.only else None
    tempo = S.get('tempo', 1.0)
    report = []
    for ln in S['lines']:
        p = os.path.join(a.out, 'lines', ln['id'] + '.wav')
        if only and ln['id'] not in only and os.path.exists(p):
            continue
        best = None
        for k in range(a.takes):
            torch.manual_seed(1000 * k + int(ln['id'][1:]))
            w = m.generate(ln['text'], audio_prompt_path=ref, exaggeration=ln.get('exaggeration', 0.6),
                           cfg_weight=ln.get('cfg', 0.35), temperature=0.8)
            y = trim(w.squeeze(0).numpy(), m.sr)
            y = trim(atempo(y, m.sr, ln.get('tempo', tempo)), m.sr)
            segs, _ = wm.transcribe(to16k(y, m.sr), word_timestamps=False)
            hyp = norm(' '.join(s.text for s in segs))
            ref_w = norm(ln['text'])
            miss = sum(1 for x in ref_w if x not in hyp) + max(0, len(hyp) - len(ref_w))
            score = (miss, -float(np.std(y)))
            print(ln['id'], 'take', k, 'miss', miss, ' '.join(hyp), flush=True)
            if best is None or score < best[0]:
                best = (score, y)
            if miss == 0 and k >= 0 and a.takes > 1 and k == 0 and ln.get('delivery') not in ('hook', 'reveal', 'punchline'):
                break
        sf.write(p, best[1], m.sr)
        report.append({'id': ln['id'], 'word_misses': best[0][0]})
    # assemble + word timing
    sr = m.sr
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
        lines.append({'id': ln['id'], 'text': ln['text'], 'start': round(t, 3), 'end': round(t + len(y) / sr, 3),
                      'delivery': ln.get('delivery', ''), 'speed': ln.get('tempo', tempo)})
        out.append(y)
        t += len(y) / sr
        gap = np.zeros(int(ln.get('pause_after', 0.2) * sr))
        out.append(gap)
        t += len(gap) / sr
    full = np.concatenate(out)
    sf.write(os.path.join(a.out, 'narration_raw.wav'), full, sr)
    json.dump({'voice': 'chatterbox+' + S.get('voice_ref', ''), 'sample_rate': sr, 'lines': lines, 'words': words,
               'duration': round(len(full) / sr, 3)}, open(os.path.join(a.out, 'timing.json'), 'w'), indent=1)
    json.dump(report, open(os.path.join(a.out, 'takes_report.json'), 'w'), indent=1)
    print('NARRATION_OK', round(len(full) / sr, 2), 's')


if __name__ == '__main__':
    main()
