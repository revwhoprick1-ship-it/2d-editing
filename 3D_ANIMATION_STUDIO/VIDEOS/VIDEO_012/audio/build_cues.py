#!/usr/bin/env python3
"""VIDEO_012 sound design -> cues.json. Scares are set up by SILENCE: every jumpscare has ~0.8 s of near-silence before it."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video012 as E  # noqa
B, s, e = E.B, E.s, E.e
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'wind'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'room_tone', -6, 'house room tone (always on: no dead air)', bus='amb', loop=True, dur=E.END, fade_out=0.02)
c(0.0, 'clock_tick' if 'clock_tick' in LIB else 'counter_ticks', -18, 'grandfather clock')
c(0.05, 'object_slide', -6, 'the vase rocks on the shelf (frame 0)')
c(B['crash'] - 0.4, 'whoosh_short', -6, 'it falls')
c(B['crash'], 'vase_shatter', 2, 'CRASH: the vase shatters')
c(B['crash'] + 0.15, 'smoke_hiss', -2, 'black smoke pours out')
c(B['sub'], 'subliminal_hit', 0, 'subliminal face (3 frames)')
c(B['sub'] + 0.3, 'whispers', -8, 'whispers', dur=2.5, fade_out=0.6)
c(B['walls'], 'bone_clicks', -6, 'it slides into the wall')
c(B['dinner'], 'crowd', -32, 'dinner murmur', bus='amb', dur=B['mom'] - B['dinner'] + 0.5, fade_out=0.6)
c(B['dinner'] + 0.2, 'glass_clink', -14, 'cutlery')
c(B['mom'] + 0.4, 'heartbeat_muffled', -10, 'Mom has not blinked')
c(B['mom'] + 1.5, 'whispers', -16, 'faint whispers', dur=2.0, fade_out=0.5)
c(B['sister'], 'wet_chew', -6, 'chewing on nothing')
c(B['sister'] + 0.4, 'fork_scrape', -6, 'fork on an empty plate')
c(B['dad'], 'heartbeat_lubdub', -8, 'Dad looks up')
c(B['js1'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 1: Dad lunges')
c(B['js1'] + 0.5, 'tinnitus', -4, 'ears ringing')
c(B['normal'] + 0.2, 'glass_clink', -16, 'normal again...')
c(B['out'], 'power_cut', 0, 'POWER OUT')
c(B['out'] + 0.9, 'button_click', -8, 'phone flashlight on')
c(B['out'], 'rain_window', -10, 'rain', bus='amb', loop=True, dur=E.END - B['out'], fade_in=1.0)
c(B['phone'] + 0.1, 'phone_buzz', -10, 'low battery')
c(B['mom2'] + 0.3, 'whispers', -18, 'whispers below')
c(B['car'] - 0.1, 'thunder', 0, 'lightning: the driveway is empty')
c(B['stairs'], 'stair_crawl', -2, 'climbing on all fours', loop=True, dur=B['bath'] - B['stairs'], fade_out=0.1)
c(B['fours'], 'bone_clicks', -4, 'joints cracking')
c(B['bath'], 'footstep_hard', -6, 'you run')
c(B['lock'], 'metal_slam', -6, 'bathroom door slams')
c(B['lock'] + 0.15, 'lock_click', -2, 'LOCK')
c(B['lock'] + 1.0, 'stair_crawl', -14, 'it stops outside...', dur=0.6, fade_out=0.3)
c(B['nothing'] + 0.4, 'heartbeat_muffled', -10, 'nothing. (fake-out)')
c(B['mirror'] + 0.2, 'heavy_breath', -10, 'your breathing in the mirror')
c(B['js2'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 2: it is behind you in the mirror')
c(B['js2'] + 0.5, 'tinnitus', -4, 'ringing')
c(B['dies'], 'power_cut', -10, 'phone dies')
c(B['whisper'], 'whispers', -6, 'whispers circling your head', loop=True, dur=e('D3') - B['whisper'] + 0.5, fade_out=0.4)
c(B['choice'] + 0.3, 'heavy_breath', -12, 'breathing under the choice')
c(B['choice'] + 2.5, 'heartbeat_muffled', -10, 'heartbeat')
for k in range(7):
    if B['choice'] + 1.4 * (k + 1) < B['js3'] - 1.2:
        c(B['choice'] + 1.4 * (k + 1), 'bone_clicks', -14 + k, f'another pair of eyes opens {k + 1}')
c(B['choice'] + 2.0, 'whispers', -16, 'whispers rising', loop=True, dur=B['js3'] - B['choice'] - 3.2, fade_in=3.0, fade_out=0.1)
c(B['js3'] - 0.03, 'jumpscare', 4, 'JUMPSCARE 3: the lunge -> frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video012',
     'music_gates': [[B['js1'] - 0.9, B['js1'] - 0.02, 0.15], [B['nothing'] - 0.2, B['js2'] - 0.02, 0.2], [B['js3'] - 1.2, B['js3'] - 0.02, 0.2]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 4},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
