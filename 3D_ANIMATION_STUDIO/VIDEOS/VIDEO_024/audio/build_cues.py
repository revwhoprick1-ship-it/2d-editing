#!/usr/bin/env python3
"""VIDEO_024 sound -> cues.json (blueprint section 3): JUMPSCARE_SLAM at 0.0, BONE_SNAP + glitch at 42.5, road -> tunnel bed,
streetlight whooshes every 1.5 s, the meter ticking, GPS chime, card slam. The 55 Hz drone is the music bed (ducked under voice)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video024 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'taxi_slam', 0, 'JUMPSCARE_SLAM (frame 0)')
c(0.0, 'taxi_road', -4, 'taxi at 90', bus='amb', loop=True, dur=B['tunnel'] + 0.1, fade_out=0.05)
c(0.45, 'lock_click', 0, 'the doors lock')
t = 0.0
while t < B['tunnel']:
    c(t + 0.55, 'light_whoosh', -12, 'streetlight passes')
    t += 1.5
c(B['meter'], 'counter_ticks', -14, 'the meter ticking', loop=True, dur=B['tunnel'] - B['meter'])
c(11.0, 'electronic_beep', -6, 'COUNTDOWN label')
c(B['flash'] - 0.1, 'whoosh_long', -8, 'a car passes (white flash)')
c(B['flash'] + 0.1, 'subliminal_hit', -4, 'the name is yours')
c(26.0, 'heartbeat_lubdub', -8, 'heartbeat', loop=True, dur=B['snap'] - 26.0)
c(B['tunnel'], 'tunnel_roar', -4, 'concrete tunnel', bus='amb', loop=True, dur=s('D01') - 0.15 - B['tunnel'], fade_out=0.15)
c(e('D01') + 0.05, 'tunnel_roar', -4, 'tunnel back after "We\'re home."', bus='amb', loop=True, dur=END - e('D01') - 0.05)
c(29.8, 'positive_chime', -10, 'GPS chime')
c(B['snap'] - 2.4, 'creak_long', -6, 'his neck turning')
c(B['snap'], 'bone_snap', 0, 'BONE_SNAP (42.5)')
c(B['snap'], 'glitch_stab', -4, 'SCREEN_GLITCH')
c(B['snap'] + 0.03, 'scare_shriek', -6, 'shriek')
c(e('D01') + 0.1, 'whispers', -14, 'whispers after "We\'re home."', dur=1.4, fade_out=0.4)
c(B['cta'], 'stamp_thud', -2, 'the choice card slams in')
c(B['cta'], 'heartbeat_lubdub', -6, 'heartbeat under the CTA', loop=True, dur=END - B['cta'])
for k, tw in enumerate((B['one'], B['two'], B['three'])):
    c(tw, 'button_click', -8, f'box {k + 1} lights')

C = {'duration': END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video024',
     'music_gates': [[s('D01') - 0.15, e('D01') + 0.05, 0.15]],                     # a pocket of silence for "We're home."
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -4.5, 'duck_db': 6},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
