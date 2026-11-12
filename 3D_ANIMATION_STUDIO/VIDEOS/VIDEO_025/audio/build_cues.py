#!/usr/bin/env python3
"""VIDEO_025 sound -> cues.json. Frame 0 = the sky cracking + every phone screaming. Hits are instant (no risers before scares).
Beds: sirens + fire in the street, the ground rumble everywhere, wind after the roof is gone, the beam's hum after the lock."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import timeline as TL  # noqa
T, END = TL.T, TL.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'sky_crack', 0, 'frame 0: the sky splits')
c(0.0, 'alert_tone', -3, 'every phone screams')
c(T['crash'], 'fall_crash', 0, 'the burning car lands')
c(T['crash'], 'impact_heavy', -2, 'car impact')
c(T['crash'], 'fire_bed', -6, 'car burning (street)', bus='amb', loop=True, dur=T['grav'] - T['crash'], fade_out=0.4)
c(0.0, 'sirens_far', -12, 'sirens across the city', bus='amb', loop=True, dur=T['door'], fade_out=0.6)
c(0.0, 'rumble_bed', -12, 'the ground shaking', bus='amb', loop=True, dur=T['white'], fade_out=0.05)
c(T['phone1'], 'phone_buzz', -8, 'phone vibrating (insert)')
c(T['phone1'] + 0.05, 'alert_tone', -7, 'alert on the screen')
c(T['run'], 'chase_run', -9, 'running', loop=True, dur=T['lift'] - T['run'], fade_out=0.2)
c(T['run'], 'heavy_breath', -12, 'breathing', loop=True, dur=T['slam'] - T['run'], fade_out=0.3)
c(T['pano'] + 0.45, 'impact_heavy', -4, 'a piece of sky hits the sidewalk')
c(T['pano'] + 0.45, 'glass_shatter', -8, 'sky shard shatters')
c(T['lift'], 'gravity_up', -2, 'gravity blinks: everything lifts')
c(T['lift'], 'air_float', -10, 'floating', dur=T['slam'] - T['lift'], fade_out=0.05)
c(T['slam'], 'impact_heavy', 0, 'SLAM: everything falls')
c(T['slam'], 'bass_impact', -2, 'slam sub')
c(T['slam'] + 0.04, 'metal_slam', -6, 'cars hit the road')
c(T['slam'] + 0.1, 'chase_run', -9, 'running again', loop=True, dur=T['call'] - T['slam'] - 0.1, fade_out=0.2)
c(T['scare'], 'scare_slam', 0, 'JUMPSCARE: a car from the sky (unannounced)')
c(T['scare'], 'metal_bang', -3, 'car crunch')
c(T['scare'], 'glitch_stab', -9, 'glitch')
c(T['scare'] + 0.02, 'glass_shatter', -6, 'windows burst')
c(T['scare'] + 0.1, 'fire_bed', -8, 'second car burning', bus='amb', loop=True, dur=T['high'] - T['scare'] - 0.1, fade_out=0.3)
c(T['call'], 'phone_ring', -6, 'MOM calling', dur=T['run2'] - T['call'] + 0.05, fade_out=0.05)
c(T['run2'], 'chase_run', -11, 'running with the phone', loop=True, dur=T['fail'] - T['run2'], fade_out=0.3)
c(T['fail'], 'call_fail', -5, 'CALL FAILED')
c(T['high'], 'beam_hum', -12, 'the lights come down', bus='amb', loop=True, dur=T['door'] - T['high'], fade_out=0.4)
for k, d in enumerate((0.0, 0.4, 0.9, 1.4)):
    c(T['high'] + d, 'light_whoosh', -8, f'beam {k + 1} lands')
c(T['sweep'] - 0.15, 'subliminal_hit', -7, 'the beam stops ON you (foreshadow)')
c(T['door'], 'door_creak_slam', -3, 'you burst in')
c(T['door'] + 0.6, 'flicker_buzz', -10, 'lamp flickers')
c(T['table'], 'heartbeat_lubdub', -10, 'heartbeat (Mia)', loop=True, dur=T['rumble'] - T['table'], fade_out=0.3)
c(T['rumble'], 'rumble_bed', -1, 'the house starts shaking', bus='amb', dur=T['rip'] - T['rumble'] + 0.3, fade_out=0.3)
c(T['rumble'] + 0.05, 'house_creak', -4, 'the house groans')
c(T['rumble'] + 0.3, 'flicker_buzz', -8, 'lights die')
c(T['rip'], 'roof_rip', 0, 'THE ROOF IS TORN OFF')
c(T['rip'], 'sky_crack', -3, 'the sky right above')
c(T['rip'], 'wind_roar', -5, 'open sky wind', bus='amb', loop=True, dur=T['white'] - T['rip'], fade_out=0.05)
c(T['phone2'], 'phone_buzz', -8, 'phones on the floor light up')
c(T['phone2'] + 0.05, 'alert_tone', -6, 'second alert')
c(T['kept'], 'glitch_stab', -7, 'KEPT: YOU')
c(T['lock'], 'beam_slam', 0, 'THE BEAM LOCKS ON YOU')
c(T['lock'], 'beam_hum', -7, 'inside the light', bus='amb', loop=True, dur=T['white'] - T['lock'], fade_out=0.05)
c(T['choice'], 'stamp_thud', -4, 'choice card')
c(T['choice'], 'heartbeat_lubdub', -6, 'heartbeat under the choice', loop=True, dur=T['white'] - T['choice'], fade_out=0.05)
c(T['white'], 'end_boom', 0, '0:00: the world ends (white) -> loop')

C = {'duration': END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 1, 'music_cue': 'cue_video025',
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -4.5, 'duck_db': 7},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
