#!/usr/bin/env python3
"""VIDEO_009 sound design -> cues.json (times from the EDL), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video009 as E  # noqa
B, s, e = E.B, E.s, E.e
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'wind', 'city'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'room_tone', -6, 'classroom room tone (power out)', bus='amb', loop=True, dur=E.END, fade_out=0.05)
c(0.0, 'wind', -16, 'wind against the windows', bus='amb', loop=True, dur=E.END, fade_out=0.05)
c(B['knock'], 'door_knock', 2, 'KNOCK KNOCK (the hook)')
c(B['knock'] + 0.9, 'heavy_breath', -10, 'you hold your breath')
c(B['title'] + 0.05, 'dramatic_hit', -6, 'title')
c(B['flash'], 'vhs_rewind', -10, 'three days ago')
c(B['flash'] + 0.3, 'zombie_groan', -8, 'slow, stupid ones')
c(B['run'], 'whoosh_long', -6, 'now they RUN')
for k in range(6):
    c(B['run'] + 0.1 + k * 0.19, 'footstep_hard', -10, 'sprinting')
c(B['run'] + 0.2, 'zombie_groan', -4, 'running scream-groan')
c(B['traps'], 'record_scratch', -14, 'trap')
c(B['phone'], 'phone_buzz', -6, 'one of them used a phone')
c(B['wide'], 'cloth_rustle', -12, 'room 204')
c(B['bob'], 'pop', -16, 'name tag BOB')
c(B['law'], 'pop', -16, 'name tag LAWRENCE')
c(B['jus'], 'pop', -16, 'name tag JUSTIN')
c(B['door2'] + 0.2, 'zombie_groan', -16, 'breathing behind the door')
c(B['z1'] - 0.2, 'knob_turn', -10, 'the handle tries, gently')
c(B['window'], 'crowd_groan', -10, 'the courtyard: hundreds of them', loop=True, dur=B['text'] - B['window'], fade_in=0.4, fade_out=0.3)
c(B['up'], 'head_turn_mass', 0, 'they ALL look up')
c(B['up'] + 0.05, 'horror_sting', -4, 'at this window')
c(B['text'], 'notif_pop', -4, 'text from Mr. Peterson')
c(B['text'] + 1.2, 'notif_pop', -6, 'text 2')
c(B['msg'], 'notif_pop', -2, "I know you're in 204")
c(B['msg'] + 0.05, 'bass_impact', -6, 'impact')
c(B['stops'] + 0.1, 'door_knock', -4, 'one last knock... then nothing')
c(B['stops'] + 0.9, 'heartbeat_muffled', -8, 'only your heartbeat')
c(B['vent'], 'vent_scratch', -4, 'scratching in the vent', loop=True, dur=B['choice'] - B['vent'], fade_in=0.3)
c(B['vent2'], 'metal_bang', -6, 'the grille bends')
c(B['vent2'] + 0.8, 'metal_bang', -8, 'bang')
c(B['vent2'] + 1.6, 'zombie_groan', -6, 'it is right there')
c(B['choice'] + 0.4, 'heavy_breath', -12, 'breathing under the choice')
c(B['choice'] + 2.4, 'vent_scratch', -14, 'scratching continues', loop=True, dur=B['again'] - B['choice'] - 2.4)
c(B['again'] + 0.3, 'door_knock', 2, 'KNOCK KNOCK again -> frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 1, 'music_cue': 'cue_video009',
     'music_gates': [[B['stops'], B['vent'] - 0.1, 0.1]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
