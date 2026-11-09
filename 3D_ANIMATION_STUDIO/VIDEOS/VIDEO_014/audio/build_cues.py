#!/usr/bin/env python3
"""VIDEO_014 sound design -> cues.json. Each scare is preceded by near-silence (music gates)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video014 as E  # noqa
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


c(0.0, 'room_tone', -6, 'air (never dead silence)', bus='amb', loop=True, dur=E.END)
c(0.0, 'rain_window', -8, 'rain', bus='amb', loop=True, dur=B['kitchen'], fade_out=0.4)
c(0.1, 'heartbeat_lubdub', -8, 'the eye in the peephole')
c(B['recap'], 'vhs_rewind', -10, 'previously')
c(B['recap'] + 0.1, 'vase_shatter', -8, 'recap: the vase')
c(B['r3'], 'jumpscare', -12, 'recap: Dad (quiet)')
c(B['card'], 'pop', -8, 'top comment card')
for k in range(int((B['lightning'] - B['card']) / 0.21)):
    c(B['card'] + k * 0.21, 'footstep_hard', -12, 'splashing steps')
c(B['card'] + 0.2, 'heavy_breath', -8, 'panting', loop=True, dur=B['lightning'] - B['card'] - 0.2)
c(B['card'] + 0.3, 'keys_jingle', -10, 'porcelain rattling in the sack', loop=True, dur=B['lightning'] - B['card'] - 0.3)
c(B['dad'] + 0.3, 'stair_crawl', -12, 'it keeps pace on the roofs', loop=True, dur=B['lightning'] - B['dad'])
c(B['d3'] - 0.1, 'whispers', -12, 'your own voice behind you')
c(B['lightning'] - 0.03, 'jumpscare', 2, 'JUMPSCARE 1: lightning, it is right there')
c(B['lightning'], 'thunder', -2, 'thunder')
c(B['blinkyou'], 'lock_click', -4, 'locks turning')
c(B['opens'], 'creak_long', -6, 'the door opens')
c(B['kitchen'], 'rain_window', -18, 'rain on Grandma\'s window', bus='amb', loop=True, dur=E.END - B['kitchen'])
c(B['kitchen'] + 0.6, 'vase_shatter', -18, 'pieces poured onto the table')
c(B['missing'] + 0.6, 'horror_sting', -6, '23 / 24: the face is missing')
c(B['g4'], 'vhs_rewind', -14, '1968')
c(B['so'] + 0.3, 'smoke_hiss', -6, 'the smoke sucked into the vase')
c(B['so'] + 1.1, 'stamp_thud', -4, 'wax seal pressed')
c(B['knock'] + 0.9, 'door_knock', 0, 'knock knock')
c(B['knock'] + 2.1, 'door_knock', -2, 'knock')
c(B['n13'] + 0.4, 'heartbeat_muffled', -8, 'Grandma frozen')
c(B['js2'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 2: the peephole')
c(B['js2'] + 0.5, 'tinnitus', -4, 'ringing')
c(B['js2'] + 1.0, 'door_knock', -6, 'knocking resumes')
c(B['js2'] + 2.6, 'door_knock', -4, 'harder')
c(B['js2'] + 3.3, 'knob_turn', -6, 'the handle turns')
for k in range(5):
    if B['js2'] + 1.5 * (k + 1) < B['js3'] - 1.2:
        c(B['js2'] + 1.5 * (k + 1), 'bone_clicks', -14 + k, f'eyes open {k + 1}')
c(B['choice'] + 1.5, 'whispers', -16, 'whispers rising', loop=True, dur=max(0.5, B['js3'] - B['choice'] - 2.7), fade_in=2.0)
c(B['js3'] - 0.03, 'jumpscare', 4, 'JUMPSCARE 3: lunge -> frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video014',
     'music_gates': [[B['lightning'] - 0.6, B['lightning'] - 0.02, 0.1], [e('N13'), B['js2'] - 0.02, 0.15], [B['js3'] - 1.2, B['js3'] - 0.02, 0.2]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 4},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
