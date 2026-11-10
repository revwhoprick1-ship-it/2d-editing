#!/usr/bin/env python3
"""VIDEO_021 sound -> cues.json. Scares are UNANNOUNCED: no riser, no music drop before them; the hit is on the first frame.
Morning = sizzle + birds; night = fridge hum + clock tick; basement = drip + chain."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video021 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'rain', 'wind'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


# hook: hallway at night
c(0.0, 'house_night', -4, 'night house', bus='amb', loop=True, dur=B['kitchen'])
c(0.0, 'lock_jiggle', -4, 'your hand on the basement doorknob')
c(s('O01') - 0.05, 'subliminal_hit', -8, 'she is suddenly right behind you')
c(e('O01') + 0.1, 'heavy_breath', -8, 'you freeze')
# mornings
c(B['kitchen'], 'kitchen_morning', -6, 'sizzle + birds', bus='amb', loop=True, dur=B['car'] - B['kitchen'])
for k, m in enumerate(B['montage']):
    c(m, 'record_scratch' if k == 0 else 'blink_cut', -14, 'same morning, again')
# the crash memory
c(B['car'], 'rain', -6, 'rain on the windshield', bus='amb', loop=True, dur=B['kitchen2'] - B['car'], fade_out=0.2)
c(B['car'] + 0.05, 'glitch_stab', -6, 'memory tears open')
c(e('Q01') - 0.15, 'fall_crash', -6, 'the crash (cut off)')
c(B['kitchen2'], 'kitchen_morning', -8, 'back in the kitchen', bus='amb', loop=True, dur=B['night'] - B['kitchen2'])
# JS1: mid-word "love", 5 frames
c(B['js1'], 'glitch_stab', 2, 'JS1 subliminal true face')
c(B['js1'], 'scare_shriek', -4, 'JS1 shriek (short)', dur=0.35, fade_out=0.1)
# night 2
c(B['night'], 'house_night', -4, 'night', bus='amb', loop=True, dur=B['door'] - B['night'])
for k, kt in enumerate(B['knocks']):
    c(kt, 'door_knock', 0 - k, f'KNOCK {k + 1} from under the floor')
c(s('P01'), 'heartbeat_muffled', -10, 'her voice from below')
c(B['door'], 'creak_long', -4, 'basement door opens')
c(B['door'] + 0.4, 'dread_drone', -12, 'basement air', bus='amb', loop=True, dur=B['choice'] - B['door'])
for k in range(5):
    c(s('N05') + 0.2 + k * 0.55, 'footstep_hard', -10 - k, f'step {k + 1}')
# JS2: on "thirteen"
c(B['js2'], 'scare_slam', 3, 'JS2 hand grabs your ankle')
c(B['js2'] + 0.05, 'scare_shriek', -6, 'JS2 shriek')
c(B['basement'], 'sweat_drip', -12, 'drip', loop=True, dur=B['choice'] - B['basement'])
c(B['basement'] + 0.5, 'keys_jingle', -12, 'the chain moves')
c(B['upstairs'], 'creak_long', -10, 'the top step creaks: she is there')
# choice: a slow pulse... and JS3 in the middle of it
c(B['choice'], 'heartbeat_lubdub', -8, 'heartbeat under the card', loop=True, dur=END - B['choice'])
c(B['js3'] - 0.12, 'power_cut', -2, 'lights die')
c(B['js3'], 'scare_slam', 4, 'JS3 both lunge')
c(B['js3'] + 0.02, 'scare_shriek', 0, 'JS3 shriek')
c(B['pick'] - 0.1, 'whispers', -10, '"Pick me." from everywhere', dur=1.4, fade_out=0.4)

C = {'duration': END, 'loop': False, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video021',
     'music_gates': [[B['js3'] - 0.12, B['js3'] + 0.5, 0.2]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
