#!/usr/bin/env python3
"""VIDEO_005 sound design -> cues.json (times from the EDL), then mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video005 as E  # noqa
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
for a in ('room_tone', 'city', 'crowd'):
    LIB[a] = f'AUDIO/ambience/{a}.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)   # SFX -5 dB: narration stays on top
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'room_tone', -10, 'bathroom room tone', bus='amb', dur=10.7, fade_out=0.1)
c(0.08, 'lid_slam', -3, 'frame 3: the lid SLAMS')
c(0.3, 'cartoon_tick', -12, 'eyes snap open')
c(1.0, 'toilet_grumble', -9, 'small toilet: grumpy gurgle-growl (its voice)')
c(2.9, 'mechanical_servo', -15, 'handle slowly turns toward him')
c(E.T_SPRAY - 0.03, 'water_spray', -4, 'SPRAY to the face (slow-mo)')
c(E.T_SPRAY + 0.05, 'impact_soft', -10, 'hit')
c(E.T_SPRAY + 0.5, 'sweat_drip', -14, 'drips off his hair')
c(5.9, 'sweat_drip', -15, 'drip')
c(6.6, 'toilet_grumble', -10, 'smug gurgle')
c(E.T_FLUSH, 'flush_big', -3, 'it flushes itself, violently')
c(E.T_FLUSH + 0.25, 'water_splash', -8, 'geyser splashes the room')
c(8.7, 'record_scratch', -9, 'SOAKED freeze')
c(8.72, 'camera_snap', -11, 'freeze frame')
c(9.4, 'whoosh_short', -10, 'he bolts (whip out)')
c(9.6, 'footstep_hard', -12, 'running footsteps')
c(9.9, 'footstep_hard', -12, 'running footsteps')
c(10.4, 'door_creak_slam', -10, 'out the door')
c(10.7, 'city', -20, 'street', bus='amb', dur=7.9, fade_in=0.05, fade_out=0.2)
c(10.7, 'crowd', -18, 'panicking crowd', bus='amb', dur=7.9, fade_in=0.1, fade_out=0.2)
c(10.75, 'crowd_gasp', -10, 'screams')
for k in range(8):
    c(13.2 + k * 0.36 + 0.3, 'lid_slam', -16 - (k % 2) * 2, 'chasing toilet chomps as it hops')
c(E.t_exits, 'lid_slam', -8, 'blocker toilet snaps at the kid')
c(E.t_exits + 0.15, 'toilet_grumble', -12, 'blocker growls')
for i, t0 in enumerate((16.6, 16.85, 17.1, 17.35, 17.6)):
    c(t0, 'tp_thump', -9 - i % 2, f'toilet-paper missile {i + 1}')
c(18.6, 'whoosh_short', -12, 'back to the bathroom')
c(18.8, 'door_creak_slam', -14, 'he sneaks in')
c(E.T_TURN - 0.5, 'room_tone', -6, 'quiet...', bus='amb', dur=1.0, fade_in=0.2)
c(E.T_TURN + 0.3, 'dramatic_hit', -10, 'red eyes open (peak lands on the turn)')
c(E.T_ROAR, 'giant_roar', -2, 'GIANT ROAR (its voice: deep porcelain roar)')
c(E.T_BLAST - 0.25, 'tension_riser', -14, 'charge', dur=0.3, fade_out=0.05)
c(E.T_BLAST, 'bass_impact', -3, 'BLAST impact frame')
c(E.T_BLAST, 'flush_big', -4, 'water cannon')
c(E.T_BLAST + 0.05, 'water_spray', -6, 'blast spray')
c(E.T_TUB, 'water_splash', -4, 'lands in the tub')
c(E.T_TUB + 0.05, 'body_thud', -8, 'tub thud')
c(E.LS['L10'][0] - 0.4, 'pop', -16, 'comment chip')
c(28.9, 'drain_gurgle', -6, 'the tub wakes up: drain gurgles')
c(29.7, 'cartoon_tick', -10, 'tub eyes open')
c(30.6, 'drain_gurgle', -9, 'second gurgle')
c(E.T_LAUNCH - 0.1, 'comedic_boing', -6, 'the tub flings him')
c(E.T_LAUNCH, 'whoosh_long', -8, 'flight back to the toilet -> loop (frame 3 slam)')
C = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': -3, 'music_cue': 'cue_video005',
     'music_gates': [[E.t_bath - 0.1, E.T_TURN + 0.3, 0.05]],
     'music_map': [['0-3', 'Sleepy', 'soft pad; stab + kick on the slam'], ['3-9.5', 'Comedy', 'bassoon staccato, tuba, light kit; drops out for the spray'],
                   ['10.7-18.6', 'Uprising', 'driving kit, brass stabs, tuba ostinato'], ['18.6-21.6', 'Sneaky', 'tiptoe pizzicato'],
                   ['21.7-22.7', 'SILENCE', '"The bathroom." dead air'], ['22.3-24.6', 'Boss', 'low strings + building taiko, huge hit on the blast'],
                   ['25.2-28.4', 'Deflated', 'sad tuba'], ['28.4-31.5', 'The tub wakes', 'sub drone, tremolo, ticking']],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 8},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
