#!/usr/bin/env python3
"""VIDEO_016 sound design -> cues.json. Forest = wind + leaves (no animals: nothing lives here). House = creaks + hum.
Sections: hook / forest / bones / house / knocks / lights out / reveal / chase / edge / twist; dialogue always on top (ducking)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video016 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'wind', 'nature'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


# hook: dead quiet forest, a whisper, a branch
c(0.0, 'forest_night', -14, 'night forest, no animals', bus='amb', loop=True, dur=B['hookcut'])
c(0.0, 'heavy_breath', -10, 'Ken breathing')
c(B['hookcut'] - 0.6, 'branch_snap', -6, 'branch behind Ken')
c(s('X01'), 'dread_drone', -12, 'under the whisper', bus='amb', dur=B['title'] - s('X01'), fade_out=0.3)
c(B['title'] - 0.05, 'dramatic_hit', -2, 'TITLE')
# forest
c(B['enter'], 'forest_night', -10, 'forest bed', bus='amb', loop=True, dur=B['house_in'] - B['enter'], fade_out=1.0)
c(B['enter'], 'wind', -20, 'high wind in the canopy', bus='amb', loop=True, dur=B['house_in'] - B['enter'], fade_out=1.0)
for k in range(3):
    c(B['enter'] + 0.3 + k * 4.0, 'leaf_steps', -12, 'group walking on leaves')
c(B['fork'] + 0.2, 'leaf_steps', -14, 'walking to the fork')
c(B['sign'] - 0.2, 'creak_long', -16, 'old sign swinging')
c(B['bones'] + 0.2, 'leaf_steps', -14, 'stepping')
c(s('L03') - 0.4, 'bone_clicks', -8, 'skull kicked')
c(B['figure'], 'subliminal_hit', -14, 'figure in the trees (nobody sees it)')
c(B['turn'] + 0.6, 'branch_snap', -4, 'something in the trees')
c(B['help'] - 0.3, 'whoosh_short', -16, 'wind gust')
c(B['help'] + 1.0, 'heavy_breath', -8, 'gasp')
# house
c(B['house_in'] - 0.6, 'door_creak_slam', -12, 'front door')
c(B['house_in'], 'room_tone', -8, 'house air', bus='amb', loop=True, dur=B['reveal'] - B['house_in'])
c(B['house_in'], 'wind', -26, 'wind outside', bus='amb', loop=True, dur=B['chase'] - B['house_in'])
for k in range(4):
    c(B['house_in'] + 2.0 + k * 7.5, 'house_creak', -14, 'house settling')
c(B['dining'] + 0.3, 'glass_tap', -14, 'plates, set for five')
c(B['wall'], 'subliminal_hit', -10, 'WELCOME BACK')
c(B['wall'] + 0.4, 'heartbeat_muffled', -10, 'dread')
# knocks
for k, kt in enumerate(B['knocks']):
    c(kt, 'door_knock', -2 - k, f'KNOCK {k + 1}')
c(s('X03') - 0.3, 'mimic_click', -18, 'wet clicking outside')
c(s('X04') + 0.1, 'heavy_breath', -8, 'held breath')
c(B['handle'], 'knob_turn', -2, 'the handle turns')
c(B['dark'], 'power_cut', -3, 'lights out')
c(B['dark'] + 0.3, 'heavy_breath', -6, 'panic in the dark')
c(B['dark'] + 0.6, 'monster_step', -10, 'something inside')
# reveal + chase
c(B['js1'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 1: the Mimic in the hallway')
c(B['js1'] + 0.5, 'tinnitus', -6, 'ringing')
c(s('X05') + 0.2, 'mimic_click', -12, 'its throat')
c(B['js2'] - 0.03, 'jumpscare', 4, 'JUMPSCARE 2: it rushes')
c(B['js2'] + 0.4, 'zombie_groan', -8, 'it screams')
c(B['chase'], 'chase_run', -6, 'running', loop=True, dur=B['edge'] - B['chase'] - 0.3)
c(B['chase'], 'wind', -16, 'forest wind (chase)', bus='amb', loop=True, dur=B['edge'] - B['chase'])
c(B['chase'] + 0.2, 'heavy_breath', -6, 'running breath')
c(B['exit'] - 0.2, 'door_creak_slam', -6, 'side door')
for k in range(3):
    c(B['chase'] + 1.0 + k * 1.6, 'branch_snap', -10 - k, 'branches whipping')
c(B['chase'] + 2.0, 'monster_step', -8, 'it is behind you')
# edge + twist
c(B['edge'] - 0.3, 'whoosh_long', -8, 'burst out of the trees')
c(B['edge'], 'nature', -18, 'open air, first birds', bus='amb', loop=True, dur=B['twist'] - B['edge'], fade_out=0.8)
c(B['edge'] + 0.3, 'heavy_breath', -6, 'catching breath')
c(B['twist'], 'subliminal_hit', -6, 'GROUP: 5?')
c(B['twist'], 'dread_drone', -10, 'something is wrong', bus='amb', loop=True, dur=END - B['twist'])
c(B['shadows'] + 0.4, 'tinnitus', -14, 'shadow points the wrong way')
c(s('X06') - 0.2, 'whispers', -16, 'whisper', dur=1.6, fade_out=0.4)
c(B['js3'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 3: Ken smiles')

C = {'duration': END, 'loop': False, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video016',
     'music_gates': [[B['knock'], B['reveal'] - 0.02, 0.15], [B['js1'] - 0.4, B['js1'] - 0.02, 0.1], [B['js3'] - 0.5, B['js3'] - 0.02, 0.1]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
