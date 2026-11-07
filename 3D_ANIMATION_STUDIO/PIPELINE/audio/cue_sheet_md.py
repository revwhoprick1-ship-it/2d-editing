#!/usr/bin/env python3
"""Render a human-readable audio cue sheet (markdown) from a video's cues.json.
    python3 PIPELINE/audio/cue_sheet_md.py VIDEOS/VIDEO_001
"""
import json, os, sys
vd = sys.argv[1]
c = json.load(open(os.path.join(vd, 'audio', 'cues.json')))
t = json.load(open(os.path.join(vd, 'audio', 'narration', 'timing.json')))
off = c.get('narration_offset', 0)
rows = []
for ln in t['lines']:
    rows.append((ln['start'] + off, 'NARRATION', ln['id'], f"{ln['delivery']} (speed {ln['speed']})", f"\"{ln['text']}\""))
for q in c['cues']:
    rows.append((q['t'], q.get('bus', 'sfx').upper(), os.path.basename(q['file']), f"{q.get('gain', 0):+.0f} dB" + (f", {q['dur']:.1f}s" if q.get('dur') else ''), q.get('note', '')))
rows.sort(key=lambda r: r[0])
name = os.path.basename(os.path.abspath(vd))
cue_fn = c.get('music_cue', 'cue_' + name.lower().replace('_', ''))
out = [f'# {name} — Audio Cue Sheet', '',
       f"Generated from `audio/cues.json` and `audio/narration/timing.json`. Narration offset {off:.2f} s. "
       f"Music: `audio/music_score.wav` (original, `PIPELINE/audio/music_gen.py {cue_fn}`), base gain {c['music_gain_db']} dB, "
       f"sidechain duck {c['targets']['duck_db']} dB under speech. Targets: narration {c['targets']['narration_lufs']} LUFS, "
       f"master {c['targets']['master_lufs']} LUFS integrated, true peak ≤ {c['targets']['true_peak']} dBTP.", '',
       '## Music map', '',
       '| Time | Section | Content |', '|---|---|---|',
       '| 0.0–10.9 | A Mystery | D‑minor‑9 pad, plucked motif with ping‑pong echoes |',
       '| 10.9–19.5 | B Tension | Dark strings (Bb/D), D pedal 8ths with an opening filter, ticks. **Stop‑time 16.30–16.95** for the valve slam |',
       '| 19.5–24.8 | C Launch | Driving 16th bass, kick/snare/hats |',
       '| 24.8–33.4 | D Wonder | F‑major lift, bell arpeggios (lead cut at 32.6 s) |',
       '| 33.4–35.9 | E Drop | Near silence + 37 Hz sub drone (pattern interrupt) |',
       '| 35.9–44.7 | F Danger | D/Eb semitone ostinato, taiko, dissonant strings, riser 41.0 s, bass gated at the kick |',
       '| 44.7–50.4 | G Climax | i–VI–III–VII (Dm–Bb–F–C), stabs, full kit, **downbeat hit 47.8 s** (launch) |',
       '| 50.4–57.0 | H Resolution | Playful F‑major pizzicato tune, final bell button 55.95 s |', '']
if c.get('music_map'):
    out = out[:out.index('| Time | Section | Content |') + 2] + [f'| {a} | {b} | {d} |' for a, b, d in c['music_map']] + ['']
out += [
       '## Timeline', '', '| Time (s) | Layer | Asset / line | Level / length | Sync event / note |', '|---|---|---|---|---|']
if c.get('loop'):
    out.insert(out.index('## Music map'), f"**Seamless loop:** the mix is built circularly (`\"loop\": true`): tails past {c['duration']} s fold back onto 0 s, and ducking, filters and limiter run as if the video had already looped once. Music gates (hard silence): {', '.join(f'{a:.2f}–{b:.2f} s' for a, b, _ in c.get('music_gates', []))}.\n")
for r in rows:
    out.append(f"| {r[0]:6.2f} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
open(os.path.join(vd, '08_audio_cue_sheet.md'), 'w').write('\n'.join(out) + '\n')
print('ok', len(rows))
