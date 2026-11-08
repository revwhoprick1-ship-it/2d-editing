#!/usr/bin/env python3
"""VIDEO_011 sound design -> cues.json (times from the EDL), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video011 as E  # noqa
B, s, e = E.B, E.s, E.e
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone',):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'arena_crowd', -6, 'packed gym (timeout)', bus='amb', loop=True, dur=B['flash'], fade_out=0.3)
c(0.05, 'arena_buzzer', -6, 'timeout buzzer (frame 0)')
c(B['you'], 'heartbeat_lubdub', -6, "that's you")
c(B['flash'], 'vhs_rewind', -10, 'two months ago')
c(B['flash'], 'room_tone', -10, 'tryouts gym', bus='amb', loop=True, dur=B['night'] - B['flash'], fade_out=0.2)
for k in range(4):
    c(B['flash'] + 0.4 + k * 0.6, 'ball_bounce', -14, 'dribbles at tryouts')
c(B['t1'] + 0.1, 'sneaker_squeak', -12, 'squeak')
c(B['laugh'], 'crowd_laugh', -6, 'the whole team laughs')
c(B['c1'] + 1.5, 'whistle_innocent', -14, 'coach whistle')
c(B['night'], 'room_tone', -8, 'empty gym at night', bus='amb', loop=True, dur=B['views'] - B['night'], fade_out=0.2)
period, t, k = 1.6, B['night'], 0
while t < B['views'] - 0.3:
    if t >= B['shots']:
        period = 0.75
    c(t + 0.05, 'ball_bounce', -10, 'set')
    c(t + period * 0.4, 'sneaker_squeak', -16, 'jump')
    c(t + period * 0.85, 'net_swish', -6, 'SWISH')
    t += period
    k += 1
c(B['record'], 'camera_snap', -8, 'janitor presses record')
c(B['views'], 'arena_crowd', -16, 'back in the gym', bus='amb', loop=True, dur=E.END - B['views'], fade_in=0.5)
c(B['views'] + 0.3, 'counter_ticks', -8, 'views counter')
c(B['views'] + 0.6, 'notif_pop', -10, 'comments')
c(B['views'] + 1.4, 'notif_pop', -12, 'comments')
c(B['fouls'], 'ref_whistle', -2, 'FOUL. Tyler fouls out')
c(B['number'], 'chant_23', -2, 'the crowd chants 23', loop=True, dur=B['c2'] + 0.6 - B['number'], fade_out=0.3)
c(B['c2'] + 0.6, 'crowd_gasp', -6, 'the gym erupts')
c(B['walk'], 'sneaker_squeak', -10, 'you stand up')
for k in range(4):
    c(B['walk'] + 0.3 + k * 0.45, 'footstep_hard', -12, 'walking onto the court')
c(B['walk'] + 2.3, 'whoosh_short', -8, 'the inbound pass')
c(B['walk'] + 2.6, 'ball_bounce', -6, 'ball in your hands')
c(B['choice'] + 0.2, 'heartbeat_lubdub', -10, 'the choice')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 1, 'music_cue': 'cue_video011',
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
