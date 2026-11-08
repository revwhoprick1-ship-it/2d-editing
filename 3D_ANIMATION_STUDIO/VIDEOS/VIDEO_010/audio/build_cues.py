#!/usr/bin/env python3
"""VIDEO_010 sound design -> cues.json (times from the EDL), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video010 as E  # noqa
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


c(0.0, 'bus_engine', -10, 'inside the bus', bus='amb', loop=True, dur=B['climb'], fade_out=0.2)
c(0.0, 'pop', -12, 'top comment card')
c(B['swing'] - 0.25, 'whoosh_short', -4, 'the swing')
c(B['swing'] + 0.05, 'glass_tap', -2, 'crack')
c(B['explodes'], 'glass_shatter', 2, 'THE WINDOW EXPLODES')
c(B['explodes'] + 0.02, 'bass_impact', -4, 'impact')
c(B['explodes'] + 0.1, 'wind', -8, 'fog pours in', bus='amb', loop=True, dur=E.END - B['explodes'] - 0.1, fade_in=0.2, fade_out=0.1)
c(B['drop'] + 0.3, 'body_thud', -4, 'you land on the road')
c(B['fade'], 'bus_engine', -14, 'the bus pulls away', dur=3.0, fade_out=2.5)
c(B['them'] + 0.3, 'creature_presence', -8, 'the passengers in the road')
c(B['stopped'], 'heartbeat_lubdub', -6, 'they stopped waving')
c(B['tilts'], 'bone_clicks', -2, 'every head tilts at once')
for k in range(5):
    c(B['walking'] + 0.2 + k * 0.5, 'footstep_soft', -8, f'their steps {k + 1}')
for k in range(int((B['poster'] - B['run']) / 0.2)):
    c(B['run'] + k * 0.2, 'footstep_hard', -10, 'you run')
c(B['run'] + 0.3, 'heavy_breath', -8, 'panting')
c(B['missing'], 'horror_sting', -3, 'MISSING: your face')
c(B['phone'], 'phone_buzz', -2, 'phone buzzes')
c(B['phone'] + 1.2, 'notif_pop', -8, 'Mom: please come home')
c(B['date'] + 0.3, 'dramatic_hit', -4, 'one year from tonight')
c(B['lights'], 'bus_engine', -10, 'the bus approaches', dur=B['inside'] - B['lights'], fade_in=1.2)
c(B['doors'], 'elev_door_slide', -4, 'the doors fold open')
c(B['doors'] + 0.1, 'stop_bell', -8, 'ding')
c(B['inside'], 'crowd', -26, 'passengers', dur=B['choice'] - B['inside'])
c(B['yourface'], 'horror_sting', 0, 'someone in your seat: YOU')
c(B['yourface'] + 0.02, 'bass_impact', -3, 'impact')
c(B['choice'] + 0.4, 'heavy_breath', -12, 'breathing under the choice')
c(B['loopback'], 'whoosh_short', -8, 'back to the window -> frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 1, 'music_cue': 'cue_video010',
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
