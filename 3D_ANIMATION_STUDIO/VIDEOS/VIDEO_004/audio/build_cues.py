#!/usr/bin/env python3
"""VIDEO_004 sound design -> cues.json (times from the EDL / narration), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video004 as E  # noqa
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
LIB['city'] = 'AUDIO/ambience/city.flac'
LIB['wind'] = 'AUDIO/ambience/wind.flac'
cues = []


def c(t, name, gain, note, **kw):
    d = dict(t=round(t, 3), file=LIB[name], gain=gain, bus=kw.pop('bus', 'sfx'), note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


TG, TL, TB = E.T_G, E.T_LAND, E.T_BONK
c(0.0, 'city', -24, 'street ambience (stops dead before gravity returns)', bus='amb', dur=22.3, loop=True, fade_out=0.25)
c(TG, 'city', -24, 'street ambience back after the crash', bus='amb', dur=E.END - TG, loop=True, fade_in=0.05)
c(0.0, 'air_float', -16, 'weightless shimmer while floating', bus='amb', dur=22.3, loop=True, fade_in=0.3, fade_out=0.3)
c(0.0, 'whoosh_long', -16, 'frame 0: feet leave the ground')
c(0.55, 'crowd_gasp', -15, 'passers-by gasp')
c(3.55, 'whoosh_long', -9, 'the fatal jump')
c(E.t_phone, 'swish', -15, 'phone drifts off')
c(E.t_coffee, 'bubble', -12, 'coffee blob escapes the cup')
c(E.t_sneeze - 0.45, 'sneeze', -7, 'ah... CHOO lands on the freeze frame')
c(E.t_sneeze + 0.4, 'whoosh_short', -10, 'sneeze propels him backwards')
c(7.45, 'record_scratch', -11, 'PHYSICS CHECK pattern interrupt')
c(7.5, 'impact_soft', -12, 'stamp')
c(10.0, 'whoosh_short', -16, 'diagram slides in')
c(E.t_jumped + 0.2, 'record_scratch', -9, 'freeze: he jumped')
c(E.t_jumped + 0.25, 'camera_snap', -10, 'freeze frame')
c(18.75, 'whoosh_long', -12, 'vertigo push: his view of the street')
c(18.75, 'wind', -18, 'high-altitude wind', bus='amb', dur=0.75, fade_in=0.1, fade_out=0.2)
LIB['room_tone'] = 'AUDIO/ambience/room_tone.flac'
c(22.3, 'room_tone', -6, 'eerie hush before gravity returns (quiet, not dead air)', bus='amb', dur=TG - 22.3, fade_in=0.1, fade_out=0.02)
c(TG, 'bass_impact', -4, 'GRAVITY ON (impact frame)')
c(TG, 'impact_heavy', -8, 'everything drops')
c(TG + 0.05, 'scream_fall', -9, 'mascot screams all the way down')
c(TG + 0.1, 'crowd_gasp', -12, 'crowd')
c(TG + 1.08, 'impact_heavy', -9, 'car lands and bounces')
c(TG + 1.1, 'water_splash', -11, 'fountain water comes back down')
for k, dt in enumerate((1.18, 1.24, 1.3)):
    c(TG + dt, 'body_thud', -7 - k, f'extra {k + 1} lands (2-3.6 m drop: a thud, not an injury)')
c(TL, 'comedic_boing', -5, 'lands on the mattress pile')
c(TL, 'body_thud', -12, 'mattress thump')
c(TL + 0.4, 'pop', -16, 'comment chip')
c(29.0, 'pop', -16, 'subscribe chip')
c(TB, 'bonk', -4, 'his phone finally comes down: BONK')
c(E.T_RESET - 0.05, 'swish', -16, 'jump-cut back to his mark')
c(E.END - 0.84, 'whoosh_long', -13, 'rising whoosh that peaks on the loop point (feet about to lift again)')
C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': -2, 'music_cue': 'cue_video004',
     'music_gates': [[22.4, TG - 0.02, 0.05]],
     'music_map': [['30.55→33.6→2.9', 'Curiosity (loop bed)', 'bell motif + pad, plays across the loop point'],
                   ['2.9–10', 'Excitement', 'bouncy 124 bpm groove'], ['10–15.9', 'Floating', 'pads + slow bells under the physics explainer'],
                   ['16.3–17.9', 'Uh-oh', 'sub drone'], ['17.9–20.4', 'Panic', 'fast semitone pulse + taiko'],
                   ['20.4–22.4', 'Countdown', 'heartbeat kicks'], ['22.4–' + f'{TG:.2f}', 'SILENCE', 'everything stops, even the street'],
                   [f'{TG:.2f}–{TL:.2f}', 'Payoff', 'taiko + brass hit, strings + snare build during the fall'],
                   [f'{TL:.2f}–{TB:.2f}', 'Comedy', 'tiptoe pizzicato']],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 8},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
