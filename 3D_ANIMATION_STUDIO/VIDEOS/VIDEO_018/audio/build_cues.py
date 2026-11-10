#!/usr/bin/env python3
"""VIDEO_018 sound design -> cues.json. The clicker is the heartbeat of the film: every click = one more passenger."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video018 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
LIB['room_tone'] = 'AUDIO/ambience/room_tone.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'cabin_drone', -6, 'engines', bus='amb', loop=True, dur=B['dark'], fade_out=0.05)
for k, tc in enumerate(B['counts']):
    c(tc, 'buckle_click', -2 if k < 3 else 2, f'CLICK (count {211 + k})')
c(s('A02') + 0.2, 'heartbeat_muffled', -10, 'dread')
c(B['aisle'], 'cloth_rustle', -14, 'looking across the aisle')
c(s('B02') + 1.0, 'subliminal_hit', -12, "22C's eyes open (2 frames)")
c(B['girl'] - 0.6, 'pen_scribble', -6, 'crayon', dur=2.2)
c(B['drawing'] + 0.4, 'subliminal_hit', -8, 'the one with no face')
c(B['dark'], 'power_cut', -2, 'LIGHTS OUT (engines too)')
c(B['dark'] + 0.1, 'dread_drone', -10, 'dark', bus='amb', dur=s('A03') - B['dark'])
c(B['dark'] + 0.2, 'heavy_breath', -6, 'breathing in the dark')
c(B['js1'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 1: faceless between you and Bob')
c(s('A03') - 0.1, 'flicker_buzz', -10, 'lights back, buzzing', loop=True, dur=B['choice'] - s('A03'))
c(s('A03') - 0.1, 'cabin_drone', -8, 'engines back', bus='amb', loop=True, dur=END - s('A03'))
c(B['tickets'] + 0.1, 'paper_rustle', -6, 'boarding passes')
c(B['lsmile'] - 0.2, 'tinnitus', -16, 'Lawrence... smiling')
c(B['js2'] - 0.03, 'jumpscare', 4, "JUMPSCARE 2: 22C wakes up")
c(B['js2'] + 0.4, 'bone_clicks', -6, 'neck cracks')
c(B['girl2'], 'paper_rustle', -8, 'she holds up the drawing')
c(B['choice'], 'whispers', -12, 'whispering cabin', dur=B['js3'] - B['choice'], fade_out=0.3)
c(B['choice'] + 2.0, 'buckle_click', 0, 'CLICK 215')
c(B['choice'] + 3.5, 'buckle_click', 2, 'CLICK 216')
c(B['js3'] - 0.03, 'jumpscare', 4, 'JUMPSCARE 3 -> loop')

C = {'duration': END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video018',
     'music_gates': [[B['dark'], s('A03') - 0.1, 0.05], [B['js2'] - 0.5, B['js2'] - 0.02, 0.1], [B['js3'] - 0.5, B['js3'] - 0.02, 0.1]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
