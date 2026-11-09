#!/usr/bin/env python3
"""VIDEO_015 sound design -> cues.json. Fear lives in the breathing: panicked breaths around every one of your lines."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video015 as E  # noqa
B, s, e = E.B, E.s, E.e
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'wind', 'crowd'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'room_tone', -5, 'air', bus='amb', loop=True, dur=E.END)
c(0.0, 'flicker_buzz', -18, 'fluorescent hum', loop=True, dur=B['rewind'])
c(0.0, 'heavy_breath', -6, 'your held breath (frame 0)')
c(s('C01') - 0.1, 'head_turn_mass', -10, 'chairs creak as they all lean')
c(B['rewind'], 'vhs_rewind', -6, '12 hours earlier')
c(B['ritual'], 'wind', -24, 'night outside', bus='amb', loop=True, dur=B['school'] - B['ritual'])
c(B['ritual'] + 0.2, 'smoke_hiss', -22, 'candles burning')
for k in range(3):
    c(E.w_at('Y03', k) if hasattr(E, 'w_at') else B['names'] + k * 0.9, 'whispers', -18 - k * -3, f'the name, echoing {k + 1}', dur=1.2, fade_out=0.4)
c(B['out'], 'power_cut', -6, 'all three candles out at once')
c(B['out'] + 0.05, 'smoke_hiss', -8, 'smoke')
c(B['bed'] + 0.1, 'heavy_breath', -12, 'shaky laugh breath')
c(B['corner'] + 1.2, 'bone_clicks', -10, 'something blinks')
c(B['school'], 'crowd', -26, 'school hallway', bus='amb', dur=B['class_'] - B['school'], fade_out=0.5)
c(B['school'] + 0.2, 'metal_bang', -24, 'locker')
c(B['t02'] + 0.1, 'heartbeat_muffled', -12, 'what Theo said')
c(B['class_'], 'flicker_buzz', -22, 'classroom hum', loop=True, dur=B['empty'] - B['class_'])
c(B['kname'] + 0.05, 'subliminal_hit', -12, '"...and Kessrah"')
c(B['y07'] - 0.2, 'heavy_breath', -8, 'breath')
c(B['blink1'], 'blink_cut', -6, 'YOUR BLINK')
c(B['js1'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 1: the whole class staring')
c(B['js1'] + 0.5, 'tinnitus', -4, 'ringing')
c(B['js1'] + 0.6, 'whispers', -14, 'whispering class', loop=True, dur=B['rub'] - B['js1'] - 0.6)
c(B['y08'] - 0.25, 'heavy_breath', -4, 'panic breath')
c(B['rub'] + 0.3, 'cloth_rustle', -8, 'rubbing your eyes')
c(B['empty'], 'flicker_buzz', -10, 'one buzzing light in an empty room', loop=True, dur=B['js3'] - B['empty'])
c(B['empty'] + 0.1, 'dread_drone', -10, 'emptiness', bus='amb', loop=True, dur=B['js3'] - B['empty'])
c(B['y09'] - 0.25, 'heavy_breath', -6, 'crying breath')
c(B['board'] + 0.3, 'pen_scribble', -4, 'chalk writing by itself', dur=2.2)
c(B['y10'] - 0.25, 'heavy_breath', -4, 'sobbing breath')
c(B['k01'] - 0.2, 'whispers', -10, 'from the back')
c(B['js2'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 2: every eyelid opens')
c(B['js2'] + 0.5, 'tinnitus', -4, 'ringing')
c(B['eyes'], 'heartbeat_lubdub', -6, 'eyes burning')
c(B['y11'] - 0.25, 'heavy_breath', -4, 'begging breath')
for (bt, *_r) in E.BLINKS[2:-1]:
    c(bt, 'blink_cut', -10, 'a blink')
    c(bt + 0.15, 'bone_clicks', -10, 'it moved closer')
c(B['js3'] - 0.03, 'jumpscare', 4, 'JUMPSCARE 3: last blink -> frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video015',
     'music_gates': [[B['blink1'] - 0.3, B['js1'] - 0.02, 0.1], [e('N08') - 0.3, B['js2'] - 0.02, 0.15], [B['js3'] - 1.0, B['js3'] - 0.02, 0.2]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 4},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
