#!/usr/bin/env python3
"""VIDEO_019 comedy sound -> cues.json: squeaky bed + blanket rustle under everything; one gag sound per beat; record scratch on mom."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video019 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
LIB['room_tone'] = 'AUDIO/ambience/room_tone.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'room_tone', -12, 'room', bus='amb', loop=True, dur=END)
c(0.0, 'cloth_rustle', -8, 'blanket, nonstop', loop=True, dur=B['N07'] - 0.1)
c(0.0, 'creak_long', -12, 'bed creak', loop=True, dur=B['N07'] - 0.1)
c(B['N02'] + 1.6, 'crunch', -6, 'cookie bite')
c(B['N02'] + 0.1, 'cash_register', -10, '100 kcal')
c(B['N03'] + 0.2, 'slide_whistle_down', -6, 'shrinks into a raisin')
c(B['N04'] + 0.1, 'bone_clicks', -6, 'wrist crack')
c(B['N04'] + 0.9, 'stamp_thud', -4, 'divorce papers stamped')
c(B['N05'], 'smoke_hiss', -6, 'fire', dur=s('N06') - B['N05'])
c(B['N05'] + 1.2, 'water_spray', -6, 'extinguisher')
c(B['N06'], 'power_cut', -8, 'system shutdown')
c(B['N06'] + 0.4, 'electronic_beep', -12, 'rebooting')
c(B['N07'], 'counter_ticks', -12, 'time passes', dur=s('N08') - B['N07'])
c(B['N07'] + 0.6, 'whistle_innocent', -14, 'just sitting')
c(B['door'], 'creak_long', -6, 'door opens')
c(B['freeze'], 'record_scratch', 0, 'FREEZE')
c(B['freeze'] + 0.2, 'crowd_gasp', -8, 'gasp')

C = {'duration': END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video019',
     'music_gates': [[B['freeze'], END, 0.03]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 6},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
