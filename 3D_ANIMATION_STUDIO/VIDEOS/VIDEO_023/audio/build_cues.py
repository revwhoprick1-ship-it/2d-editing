#!/usr/bin/env python3
"""VIDEO_023 sound -> cues.json: running feet + panting + the horde's footsteps under the whole first half; instant scares."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video023 as E  # noqa
B, s, e, END, JS = E.B, E.s, E.e, E.END, E.JS
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('wind', 'room_tone', 'crowd'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'scare_slam', -4, 'frame 0 hit')
c(0.0, 'wind', -10, 'burning city wind', bus='amb', loop=True, dur=B['gate'] + 0.6)
c(0.0, 'chase_run', -2, 'our feet', loop=True, dur=B['gate'] + 0.4)
c(0.0, 'zombie_groan', -10, 'the horde', loop=True, dur=B['gate'] + 0.8)
c(0.0, 'heavy_breath', -6, 'panting', loop=True, dur=B['gate'])
c(B['vault'], 'whoosh_short', -6, 'Tara vaults the car')
c(B['vault'] + 0.6, 'body_thud', -6, 'lands')
c(B['gate'], 'metal_slam', 0, 'the gate slams down')
c(B['gate'] + 0.5, 'metal_bang', -2, 'zombies hit the gate')
c(B['gate'] + 0.8, 'metal_bang', -4, 'again')
c(B['gate'], 'flicker_buzz', -14, 'store lights', loop=True, dur=B['freezer'] - B['gate'])
c(B['drone'], 'cable_hum', -6, 'drone rotors', loop=True, dur=s('D01') + 1.6 - B['drone'])
c(s('D01') - 0.2, 'electronic_beep', -8, 'thermal on')
c(B['aisle'], 'chase_run', -4, 'running down the aisle', dur=B['freezer'] - B['aisle'])
c(B['freezer'], 'metal_slam', -2, 'freezer door slams')
c(B['freezer'], 'machinery_hum', -12, 'freezer compressor', bus='amb', loop=True, dur=END - B['freezer'])
c(s('D02') - 0.3, 'electronic_beep', -8, 'thermal again')
c(s('K05') + 1.2, 'heartbeat_muffled', -6, 'her breath is not fogging')
c(B['lock'] + 0.5, 'lock_click', 0, 'latch')
c(B['out'], 'footstep_hard', -6, 'Tara running out', loop=True, dur=B['swarm'] - B['out'])
c(s('T03') + 0.6, 'crowd_gasp', -10, 'the horde turns')
c(B['js1'], 'scare_slam', 2, 'JS1 the swarm leaps')
c(B['js1'] + 0.02, 'scare_shriek', -2, 'JS1')
c(B['glass'], 'wet_chew', -6, 'behind the door', dur=1.2, fade_out=0.3)
c(B['glass'] + 0.3, 'squelch', -6, 'blood on the glass')
for k, kt in enumerate(B['knocks']):
    c(kt, 'door_knock', -2 - k, f'knock {k + 1}')
c(B['choice'], 'heartbeat_lubdub', -6, 'heartbeat', loop=True, dur=END - B['choice'])
c(B['choice'] + 0.3, 'knob_turn', -6, 'the handle turns')
c(B['js2'], 'scare_slam', 2, 'JS2 Tara slams the glass')
c(B['js2'] + 0.02, 'glass_shatter', -4, 'glass cracks')
c(B['js2'] + 0.04, 'scare_shriek', -2, 'JS2')

C = {'duration': END, 'loop': False, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video023',
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -3.2, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
