#!/usr/bin/env python3
"""VIDEO_020 comedy sound -> cues.json: a desk/podium creak loop everywhere he 'keeps going'; a pressure alarm when he stops."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video020 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'crowd'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'room_tone', -12, 'room', bus='amb', loop=True, dur=END)
c(0.0, 'heartbeat_lubdub', -8, 'x-ray pulse', dur=s('M01'))
c(e('C01') - 0.4, 'dramatic_hit', -2, '"...your balls explode"')
c(0.0, 'cloth_rustle', -12, 'keeps going', loop=True, dur=B['stop'])
c(B['office'], 'creak_long', -10, 'desk creak', loop=True, dur=B['wedding'] - B['office'])
c(B['office'] + 0.3, 'glass_clink', -12, 'coffee cup rattling')
c(s('A02') - 0.2, 'record_scratch', -6, 'interviewer stares')
c(B['wedding'], 'crowd', -16, 'wedding guests', bus='amb', loop=True, dur=B['phone'] - B['wedding'], fade_out=0.4)
c(B['wedding'] + 0.2, 'glass_tap', -6, 'toast')
c(B['stop'], 'counter_ticks', -8, 'he stopped...', dur=s('M06') - B['stop'])
c(B['alarm'], 'electronic_beep', -2, 'PRESSURE ALARM', loop=True, dur=s('M06') - B['alarm'] + 0.2)
c(B['alarm'], 'thunder', -8, 'rumble')
c(B['alarm'] + 0.2, 'tension_riser', -8, 'about to blow')
c(s('M06') + 1.8, 'arena_crowd', -10, 'guests applaud', dur=2.0, fade_out=0.6)
c(B['phone'] - 0.2, 'phone_buzz', -4, 'doctor calling')
c(s('C04') + 0.6, 'cloth_rustle', -10, 'still going', loop=True, dur=END - s('C04') - 0.6)
c(s('M08') + 0.8, 'surprise_sting', -6, 'button')

C = {'duration': END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video020',
     'music_gates': [[B['stop'], s('M06'), 0.05]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 6},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
