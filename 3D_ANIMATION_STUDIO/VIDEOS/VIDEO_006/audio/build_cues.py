#!/usr/bin/env python3
"""VIDEO_006 sound design -> cues.json (times from the EDL), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video006 as E  # noqa
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'wind'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


# ---- the elevator ride (0-7)
c(0.0, 'room_tone', -20, 'elevator room tone', bus='amb', dur=E.T_DARK, fade_out=0.02)
c(0.0, 'cable_hum', -14, 'car moving: motor hum + cable creaks', bus='amb', dur=7.1, loop=True, fade_out=0.4)
c(E.T_FLIP, 'button_click', -10, 'the 13 button lights up by itself')
c(E.T_FLIP + 0.02, 'electronic_beep', -20, 'display flips 12 -> 13')
c(4.8, 'flicker_buzz', -7, 'lights flicker', pan=0.1)
c(5.15, 'flicker_buzz', -9, 'flicker again', pan=-0.1)
c(5.6, 'electronic_glitch', -15, 'display glitches')
c(6.28, 'flicker_buzz', -11, 'last flicker')
# ---- the 13th floor (7-17)
c(E.T_DING1, 'elevator_ding_eerie', -3, 'DING: floor 13')
c(E.T_DING1 + 0.1, 'elev_door_slide', -7, 'doors slide open')
c(E.T_DING1 + 0.2, 'wind', -30, 'cold hallway draft', bus='amb', dur=E.T_DARK - E.T_DING1 - 0.2, fade_in=1.0, fade_out=0.02)
for i in range(3):
    c(9.0 + i, 'flicker_buzz', -15, f'sconce {i + 1} flickers', pan=-0.3 + 0.3 * i)
for k in range(5):
    c(E.T_OUT + 0.25 + k * 0.5, 'footstep_echo', -9 - (k % 2), 'slow steps, echoing hallway', pan=-0.1 if k % 2 else 0.1)
c(E.T_PHOTO + 0.3, 'horror_sting', -3, 'the photo: it is HIM (lands on the cut to the photo)')
c(15.95, 'heartbeat_lubdub', -7, 'recognition: heartbeat')
c(E.T_TURN, 'whoosh_short', -14, 'he spins round')
c(E.T_SLAM, 'metal_slam', -1, 'the doors SLAM shut')
for k in range(4):
    c(E.T_RUNB + k * 0.2, 'footstep_hard', -10, 'runs back')
for k in range(5):
    c(18.4 + k * 0.2, 'metal_bang', -5 - (k % 2) * 2, f'pounds the doors {k + 1}')
# ---- the apartment (20.4-29.85)
c(E.T_DOOR13, 'creak_long', -5, 'the far door creaks open')
c(E.T_DOOR13 + 0.3, 'tv_static_bed', -21, 'TV static leaking from the apartment', bus='amb', dur=E.T_DARK - E.T_DOOR13 - 0.3,
  loop=True, fade_in=2.0, fade_out=0.02)
for k in range(6):
    c(E.T_WALK2 + 0.25 + k * 0.5, 'footstep_echo', -11 - (k % 2), 'walks to the open door')
c(E.T_HEAD, 'cloth_rustle', -15, 'the double turns his head')
c(E.T_STAND, 'cloth_rustle', -12, 'the double stands up')
c(E.T_STAND + 0.2, 'heartbeat_muffled', -12, 'heartbeat under the silence')
c(E.T_DARK, 'power_cut', -1, 'LIGHTS OUT (hard cut to black)')
# ---- back in the elevator (30.4-37.8)
c(E.T_DING2, 'elevator_ding_eerie', -3, 'DING: back in the elevator')
c(E.T_DING2 + 0.05, 'elev_door_slide', -9, 'doors open')
c(E.T_DING2, 'room_tone', -20, 'elevator room tone', bus='amb', dur=E.T_BLACK - E.T_DING2, fade_out=0.02)
for k in range(3):
    c(30.75 + k * 0.2, 'footstep_hard', -10, 'stumbles in')
for k in range(4):
    c(31.4 + k * 5 / 30, 'button_click', -7, f'jabs the button {k + 1}')
c(31.9, 'elev_door_slide', -9, 'doors close')
c(32.5, 'impact_soft', -12, 'doors shut')
c(32.55, 'cable_hum', -16, 'car moving again', bus='amb', dur=E.T_BLACK - 32.55, loop=True, fade_in=0.3, fade_out=0.02)
c(E.T_FLIP2, 'electronic_beep', -18, 'display: 12')
c(E.T_CLOCK, 'dramatic_hit', -8, 'the clock: 11:48 again')
c(E.T_BTN, 'heartbeat_lubdub', -8, 'the 13 button is still lit')
c(E.T_SMILE - 0.1, 'glass_swell', -8, 'restrained sting: the reflection smiles (cut at the black)', dur=E.T_BLACK - E.T_SMILE + 0.1, fade_out=0.02)
c(E.T_BLACK + 0.03, 'elevator_ding_eerie', -2, 'black + DING -> loop to frame 0')

C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': -4, 'music_cue': 'cue_video006',
     'music_gates': [[27.7, E.T_DING2, 0.12], [E.T_BLACK, E.END + 1.0, 0.02]],
     'music_map': [['0-7', 'Ride', 'sub drone, detuned pad, lonely high piano; sour step when 13 lights'],
                   ['7-12', 'Hallway', 'tremolo strings swell'], ['12-14.6', 'Walk', 'slow heartbeat taiko'],
                   ['14.6-17.2', 'Photo', 'string cluster -> taiko hit on the slam'], ['17.2-20.4', 'Panic', 'fast low ostinato, tremolo'],
                   ['20.4-27.7', 'Apartment', 'sub drone + distant bell, slowing heartbeat'],
                   ['27.7-30.4', 'SILENCE', 'music out: "You\'re late... again." then lights out'],
                   ['30.4-34.9', 'Return', 'uneasy pulse; hit on the 11:48 clock'], ['34.9-37.8', 'Reflection', 'high tremolo creeping up, hard cut']],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 8},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
