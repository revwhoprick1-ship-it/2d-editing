#!/usr/bin/env python3
"""VIDEO_013 sound design -> cues.json."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video013 as E  # noqa
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


c(0.0, 'arena_crowd', -8, 'packed gym', bus='amb', loop=True, dur=B['recap'], fade_out=0.1)
c(0.0, 'room_tone', -4, 'gym air (no dead air)', bus='amb', loop=True, dur=E.END)
c(B['rim'] + 1.0, 'heartbeat_lubdub', -6, 'held breath: heartbeat on the rim')
c(0.0, 'whoosh_long', -8, 'the ball in the air (frame 0)')
c(B['water'] - 0.05, 'record_scratch', -2, 'FREEZE: the water boy')
c(B['water'], 'camera_snap', -6, 'freeze frame')
for k, key in enumerate(('recap', 'mates', 'night', 'viral', 'chant', 'until')):
    c(B[key], 'whoosh_short', -10, f'recap whip {k + 1}')
c(B['mates'] + 0.2, 'crowd_laugh', -14, 'teammates laughing')
c(B['night'] + 0.3, 'net_swish', -10, 'swish')
c(B['viral'] + 0.2, 'notif_pop', -10, 'viral')
c(B['chant'], 'chant_23', -8, 'chant', dur=B['until'] - B['chant'], fade_out=0.2)
c(B['chose'], 'pop', -8, 'your vote card')
c(B['ball'], 'arena_crowd', -10, 'the gym', bus='amb', loop=True, dur=B['go'] - B['ball'], fade_out=0.6)
c(B['ball'] + 0.05, 'arena_buzzer', -12, 'clock starts')
c(B['ball'] + 0.5, 'ball_bounce', -6, 'catch')
for k in range(4):
    c(B['ball'] + 0.9 + k * 0.45, 'ball_bounce', -8, f'dribble {k + 1}')
c(B['step'], 'sneaker_squeak', -2, 'STEP BACK')
c(B['go'] - 0.2, 'sneaker_squeak', -6, 'rise')
c(B['go'], 'whoosh_long', -4, 'release (slow motion)')
c(B['go'] + 0.4, 'arena_buzzer', -6, 'the buzzer: ball still in the air')
c(B['go'] + 0.2, 'heartbeat_lubdub', -4, 'heartbeat (slow-mo)')
c(B['go'] + 1.4, 'heartbeat_lubdub', -6, 'heartbeat')
c(B['clang'], 'metal_bang', -2, 'IT HITS THE RIM')
c(B['clang'] + 0.35, 'metal_bang', -12, 'rolls on the rim')
c(B['drops'] + 0.15, 'net_swish', 0, 'SWISH')
c(B['drops'] + 0.2, 'crowd_gasp', -5, 'the gym explodes')
c(B['drops'] + 0.2, 'arena_crowd', -2, 'roar', bus='amb', loop=True, dur=B['scout'] - B['drops'], fade_out=1.0)
c(B['janitor'], 'crowd_laugh', -18, 'happy crowd')
c(B['d2'] - 0.3, 'object_slide', -14, 'water bottle handed over')
c(B['scout'], 'phone_buzz', -10, 'the scout dials')
c(B['scout'], 'arena_crowd', -14, 'crowd', bus='amb', loop=True, dur=E.END - B['scout'], fade_in=0.5)
c(E.END - 0.6, 'whoosh_long', -8, 'back to the shot -> frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 1, 'music_cue': 'cue_video013',
     'music_gates': [[B['rim'] - 0.1, B['drops'] + 0.12, 0.1]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
