#!/usr/bin/env python3
"""VIDEO_008 sound design -> cues.json (times from the EDL), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video008 as E  # noqa
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


c(0.0, 'bus_engine', -10, 'bus engine + road (the whole ride)', bus='amb', loop=True, dur=E.END, fade_out=0.05)
c(0.0, 'crowd', -26, 'passengers murmur, phones', bus='amb', dur=B['blink'], fade_out=0.02)
c(B['blink'], 'blink_cut', -1, 'THE BLINK')
c(B['blink'] + 0.1, 'bass_impact', -6, 'they are gone')
c(B['empty'] + 0.3, 'phone_buzz', -14, 'a phone left on a seat buzzes')
c(B['play'], 'phone_beep', -4, 'play')
c(B['play'] + 0.1, 'crowd', -28, 'the recording: passengers murmur', bus='amb', dur=B['turn'] - B['play'], fade_out=0.02)
c(B['turn'], 'head_turn_mass', 0, 'everyone turns at once')
c(B['turn'] + 0.05, 'horror_sting', -5, 'they look at you')
c(B['ends'], 'tv_static_click', -8, 'video ends')
c(s('D1') - 0.1, 'footstep_hard', -12, 'you jump up')
c(B['you'], 'electronic_glitch', -6, 'route screen: YOU')
c(B['window'], 'wind', -18, 'fog outside', bus='amb', dur=B['button'] - B['window'], fade_in=0.5)
c(B['faces'] + 0.4, 'glass_tap', -6, 'tap tap tap on the glass')
c(B['waving'], 'creature_presence', -10, 'they wave')
c(B['slam'], 'button_click', -2, 'you slam the button')
c(B['slam'] + 0.05, 'stop_bell', -3, 'stop requested ding')
c(B['ticket'] + 0.1, 'paper_rustle', -8, 'ticket in your hand')
c(B['mirror'] + 0.2, 'heartbeat_lubdub', -8, 'the mirror')
c(B['noface'], 'horror_sting', 0, 'NO FACE')
c(B['noface'] + 0.02, 'bass_impact', -3, 'impact')
c(B['brake'], 'bus_brakes', -2, 'the bus slows: brakes')
c(B['brake'] + 0.3, 'heavy_breath', -8, 'panic breathing')
c(B['choice'] + 0.4, 'heavy_breath', -12, 'breathing under the choice')
c(B['choice'] + 2.4, 'heavy_breath', -12, 'breathing')
c(B['back'], 'power_cut', -4, 'lights flicker')
c(B['back'] + 0.25, 'flicker_buzz', -6, 'flicker')
c(B['back'] + 0.33, 'head_turn_mass', -2, 'THEY ARE BACK. staring. -> frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 1, 'music_cue': 'cue_video008',
     'music_gates': [[B['blink'] - 0.02, B['blink'] + 0.1, 0.02]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
