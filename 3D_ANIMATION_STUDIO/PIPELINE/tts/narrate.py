#!/usr/bin/env python3
"""Local, free narration generator built on Kokoro-82M (Apache-2.0 weights).

Run with the TTS venv:
    /opt/tools/tts312/bin/python PIPELINE/tts/narrate.py SCRIPT.json OUT_DIR [--voice am_michael]

SCRIPT.json:
{
  "voice": "af_heart",            # narrator identity (see AUDIO/narrator/NARRATOR.md)
  "lines": [
     {"id": "S01", "text": "...", "speed": 1.0, "pause_after": 0.35, "gain_db": 0, "delivery": "suspense"},
     ...
  ],
  "pronunciations": {"neutrophil": "nˈutɹəfˌɪl"}
}

Outputs (OUT_DIR):
  lines/<id>.wav         each line, 24 kHz mono, silence-trimmed
  narration_raw.wav      all lines concatenated with the scripted pauses
  timing.json            line and word timings (seconds) incl. phonemes for lip sync
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

SR = 24000

# Delivery presets: speed multiplier + default pause.  Kokoro has no emotion
# token, so delivery is shaped with speed, punctuation, chunking and pauses.
DELIVERY = {
    'hook':      dict(speed=1.00, pause=0.30),
    'curious':   dict(speed=0.97, pause=0.30),
    'excited':   dict(speed=1.07, pause=0.20),
    'suspense':  dict(speed=0.90, pause=0.45),
    'urgent':    dict(speed=1.12, pause=0.12),
    'calm':      dict(speed=0.95, pause=0.30),
    'dramatic':  dict(speed=0.94, pause=0.35),
    'humor':     dict(speed=1.00, pause=0.40),
}


def apply_pronunciations(text, prons):
    for word, ph in prons.items():
        text = re.sub(r'(?<![\w\[])(%s)(?![\w\]])' % re.escape(word), r'[\1](/%s/)' % ph, text, flags=re.I)
    return text


def trim(audio, thr_db=-45.0, pad=0.03):
    if len(audio) == 0:
        return audio, 0
    env = np.abs(audio)
    thr = 10 ** (thr_db / 20.0) * max(1e-9, env.max())
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return audio, 0
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(audio), idx[-1] + int(pad * SR))
    return audio[a:b], a


def synth_line(pipeline, text, voice, speed):
    chunks, words = [], []
    t0 = 0.0
    for res in pipeline(text, voice=voice, speed=speed, split_pattern=None):
        audio = res.audio.detach().cpu().numpy() if hasattr(res.audio, 'detach') else np.asarray(res.audio)
        for tok in (res.tokens or []):
            if tok.start_ts is None:
                continue
            words.append({'text': tok.text, 'phonemes': tok.phonemes or '',
                          'start': t0 + float(tok.start_ts), 'end': t0 + float(tok.end_ts or tok.start_ts)})
        chunks.append(audio)
        t0 += len(audio) / SR
    audio = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)
    return audio.astype(np.float32), words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('script')
    ap.add_argument('out')
    ap.add_argument('--voice', default=None)
    ap.add_argument('--only', default=None, help='comma list of line ids to (re)generate')
    a = ap.parse_args()
    from kokoro import KPipeline
    spec = json.load(open(a.script))
    voice = a.voice or spec.get('voice', 'af_heart')
    prons = spec.get('pronunciations', {})
    lang = spec.get('lang_code', 'a')
    pipe = KPipeline(lang_code=lang, repo_id='hexgrad/Kokoro-82M')
    os.makedirs(os.path.join(a.out, 'lines'), exist_ok=True)
    only = set(a.only.split(',')) if a.only else None
    timing = {'voice': voice, 'sample_rate': SR, 'lines': [], 'words': []}
    full = []
    cursor = 0.0
    for ln in spec['lines']:
        d = DELIVERY.get(ln.get('delivery', 'calm'), DELIVERY['calm'])
        speed = ln.get('speed', d['speed'])
        pause = ln.get('pause_after', d['pause'])
        lead = ln.get('pause_before', 0.0)
        path = os.path.join(a.out, 'lines', f"{ln['id']}.wav")
        meta_path = path.replace('.wav', '.json')
        if only is None or ln['id'] in only or not os.path.exists(path):
            text = apply_pronunciations(ln['text'], prons)
            audio, words = synth_line(pipe, text, voice, speed)
            audio, off = trim(audio)
            for w in words:
                w['start'] -= off / SR
                w['end'] -= off / SR
            g = 10 ** (ln.get('gain_db', 0.0) / 20.0)
            audio = audio * g
            sf.write(path, audio, SR, subtype='FLOAT')
            json.dump({'words': words, 'text': ln['text'], 'speed': speed}, open(meta_path, 'w'), ensure_ascii=False)
        audio, _ = sf.read(path, dtype='float32')
        words = json.load(open(meta_path))['words']
        if lead:
            full.append(np.zeros(int(lead * SR), np.float32))
            cursor += lead
        start = cursor
        full.append(audio)
        cursor += len(audio) / SR
        timing['lines'].append({'id': ln['id'], 'text': ln['text'], 'start': round(start, 3),
                                'end': round(cursor, 3), 'delivery': ln.get('delivery', 'calm'), 'speed': speed})
        for w in words:
            timing['words'].append({'line': ln['id'], 'text': w['text'], 'phonemes': w['phonemes'],
                                    'start': round(start + max(0.0, w['start']), 3),
                                    'end': round(start + max(0.0, w['end']), 3)})
        full.append(np.zeros(int(pause * SR), np.float32))
        cursor += pause
    out = np.concatenate(full)
    sf.write(os.path.join(a.out, 'narration_raw.wav'), out, SR, subtype='FLOAT')
    timing['duration'] = round(len(out) / SR, 3)
    json.dump(timing, open(os.path.join(a.out, 'timing.json'), 'w'), indent=1, ensure_ascii=False)
    print('NARRATION_OK', timing['duration'], 's', len(timing['words']), 'words')


if __name__ == '__main__':
    main()
