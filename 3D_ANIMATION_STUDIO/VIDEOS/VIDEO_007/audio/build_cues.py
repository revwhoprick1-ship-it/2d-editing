#!/usr/bin/env python3
"""VIDEO_007 sound design -> cues.json (times from the EDL), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video007 as E  # noqa
B, s, e, w = E.B, E.s, E.e, E.w
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'wind'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


# ---- hook: under the desk, something outside
c(0.0, 'room_tone', -18, 'office room tone', bus='amb', dur=B['rewind0'], fade_out=0.05)
c(0.0, 'heavy_breath', -9, 'your held breathing')
c(1.9, 'heavy_breath', -10, 'breathing')
c(0.4, 'monster_step', -8, 'a heavy step outside the door')
c(s('N02') - 0.1, 'knob_turn', -4, 'the handle presses down slowly')
c(s('N02') + 0.8, 'bone_clicks', -10, 'clicks behind the door')
c(B['rewind0'], 'vhs_rewind', -6, 'REWIND: ten minutes earlier')
c(B['title'] + 0.05, 'dramatic_hit', -6, 'title: AFTER HOURS')
# ---- the guard booth
c(B['booth'], 'room_tone', -20, 'booth room tone', bus='amb', dur=B['ext'] - B['booth'], fade_out=0.1)
c(B['booth'] + 0.1, 'flicker_buzz', -20, 'CCTV hum', loop=True, dur=B['ext'] - B['booth'] - 0.2, fade_out=0.1)
for k in range(4):
    c(B['booth'] + 0.3 + k * 2.86, 'snore', -6, f'the guard snores {k + 1}')
c(s('N05') + 0.1, 'keys_jingle', -6, 'the keys slide off the belt')
c(s('N05') + 1.2, 'keys_jingle', -9, 'jingle')
c(B['snort'], 'snort', -3, 'the guard SNORTS and stirs (freeze)')
c(B['snort'] + 0.1, 'heartbeat_lubdub', -8, 'your heart')
# ---- outside / corridor / door
c(B['ext'], 'wind', -20, 'night wind', bus='amb', dur=B['corr'] - B['ext'], fade_in=0.1, fade_out=0.2)
for k in range(8):
    c(B['ext'] + 0.15 + k * 0.21, 'footstep_hard', -16, 'running across the yard')
c(B['corr'] - 0.05, 'door_creak_slam', -14, 'side door')
c(B['corr'], 'room_tone', -17, 'empty corridor', bus='amb', dur=B['door'] - B['corr'], fade_out=0.1)
c(B['corr'] + 0.1, 'button_click', -12, 'flashlight on')
for k in range(int((B['door'] - B['corr']) / 0.4)):
    c(B['corr'] + 0.3 + k * 0.4, 'footstep_echo', -11 - (k % 2), 'steps echo back at you')
c(B['door'] + 0.35, 'lock_jiggle', -6, 'key 1: no')
c(B['door'] + 1.3, 'lock_jiggle', -6, 'key 2: no')
c(B['key_turn'], 'lock_click', -2, 'key 3 turns')
c(B['key_turn'] + 0.4, 'creak_long', -5, 'the office door creaks open')
# ---- the office + the files
c(B['office'], 'room_tone', -17, 'office room tone', bus='amb', dur=B['bang'] - B['office'], fade_out=0.02)
c(B['office'] + 0.2, 'object_slide', -9, 'drawer slides out')
c(B['office'] + 1.0, 'paper_rustle', -8, 'digging through files')
c(B['files'] + 0.1, 'paper_rustle', -8, 'folder opens')
c(B['files'] + 0.3, 'horror_sting', -9, "these aren't tests")
for i in range(5):
    c(B['stamps'] + 0.25 + i * 0.28, 'stamp_thud', -6, f'KEPT stamp {i + 1}')
c(B['kept'], 'stamp_thud', -1, 'KEPT (the big one)')
c(B['note'], 'paper_rustle', -10, 'the newest file slides in')
c(B['note'] + 0.7, 'horror_sting', -6, 'your photo. the note.')
c(B['face'], 'heavy_breath', -11, 'you breathe')
c(B['test'] + 0.1, 'paper_rustle', -10, 'the test')
c(B['becomes'], 'pen_scribble', -4, '3 becomes 8')
c(B['becomes'] + 0.45, 'pen_scribble', -6, 'second loop')
# ---- BANG
c(B['bang'], 'big_bang', 0, 'BANG from the hallway')
c(B['bang'] + 0.02, 'bass_impact', -4, 'sub hit')
c(B['bang'] + 2.0, 'room_tone', -14, 'dead silence after', bus='amb', dur=B['pov'] - B['bang'] - 2.0, fade_in=0.4)
c(B['peek'] + 0.1, 'creak_long', -8, 'door opens a crack')
c(B['pov'], 'flicker_buzz', -10, 'the last light flickers', loop=True, dur=B['turn'] - B['pov'])
c(B['pov'] + 0.3, 'creature_presence', -6, 'it breathes')
c(B['hand'] + 0.2, 'monster_step', -9, 'it shifts its weight')
c(B['turn'] + 0.2, 'bone_clicks', -2, 'its head turns: clicks')
c(B['looks'], 'horror_sting', -1, 'it LOOKS AT YOU')
c(B['looks'] + 0.02, 'bass_impact', -3, 'impact')
c(B['face3'], 'heavy_breath', -6, 'panic breathing')
# ---- dive under the desk, footsteps, the stop
c(B['dive'], 'cloth_rustle', -6, 'you dive under the desk')
c(B['dive'] + 0.15, 'body_thud', -10, 'thud')
for k in range(5):
    tk = B['dive'] + 0.8 + k * ((B['stop'] - B['dive'] - 0.8) / 5)
    c(tk, 'monster_step', -12 + k * 2, f'its footsteps come closer {k + 1}')
c(B['stop'] + 0.05, 'monster_step', -1, 'the footsteps STOP (right outside)')
c(B['stop'] + 0.6, 'heartbeat_muffled', -8, 'heartbeat in the silence')
c(B['stop'] + 1.5, 'room_tone', -16, 'silence', bus='amb', dur=E.END - B['stop'] - 1.5, fade_out=0.05)
c(B['choice'] + 0.1, 'heavy_breath', -12, 'breathing under the choice')
c(B['choice'] + 2.2, 'heavy_breath', -12, 'breathing')
c(E.END - 1.2, 'knob_turn', -6, 'the handle starts to turn -> loops into frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 1, 'music_cue': 'cue_video007',
     'music_gates': [[B['rewind0'] + 0.05, B['booth'] - 0.1, 0.1], [B['bang'] + 0.15, B['peek'], 0.05], [B['stop'], B['stop'] + 1.2, 0.05]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
