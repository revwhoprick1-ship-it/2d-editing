#!/usr/bin/env python3
"""VIDEO_026 cue sheet -> audio/cues.json (then PIPELINE/audio/mix.py makes mix_master.wav: -14 LUFS, true peak <= -2 dBTP).

    python3 studio/sound_mix.py && /opt/tools/cbx/bin/python PIPELINE/audio/mix.py VIDEOS/VIDEO_026/audio/cues.json

Frame 0 = JUMPSCARE_SLAM + phone buzz. Scares are instant (no riser before them). The 55 Hz drone (music cue video026) is
ducked 6 dB under dialogue. loop=True: tails wrap onto the start, and a swell carries the last frame into the frame-0 slam.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import timeline as TL  # noqa: E402

T, END, L = TL.T, TL.END, TL.LINES
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(VIDEO, '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name] if name in LIB else name, gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


# beds
c(0.0, 'house_night', -6, 'the house at night', bus='amb', loop=True, dur=END, fade_in=0.5)
c(0.0, 'rain_window', -9, 'rain on the window', bus='amb', loop=True, dur=T['s4a'], fade_in=0.6)
c(T['s4a'], 'rain_window', -3, 'rain, closer: the front door', bus='amb', loop=True, dur=T['s5a'] - T['s4a'], fade_out=0.3)
c(T['s5a'], 'rain_window', -9, 'rain', bus='amb', loop=True, dur=END - T['s5a'])
c(0.0, 'tv_static_bed', -20, 'the TV murmuring', bus='amb', loop=True, dur=T['s5a'], fade_in=0.6, fade_out=0.05)
c(T['feed'], 'cable_hum', -16, 'security feed hum', bus='amb', loop=True, dur=T['s6a'] - T['feed'], fade_out=0.2)
# 1A/1B the hook
c(0.0, 'mimic_slam', -3, 'FRAME 0: JUMPSCARE_SLAM')
c(0.02, 'phone_buzz160', -3, 'phone vibrating in your hand (160 Hz)')
c(T['whip1'], 'whoosh_short', -5, 'whip-pan to Bob')
c(T['whip1_end'], 'subliminal_hit', -8, 'Bob is right there')
c(T['label_dist'], 'electronic_beep', -10, 'label: PULSE 0 BPM')
# 2A/2B the photo
c(T['chime'], 'msg_chime', -2, 'second message (double chime, bent down)')
c(T['chime'] + 0.05, 'phone_buzz160', -9, 'buzz', dur=0.45, fade_out=0.05)
c(T['unblur'] - 0.1, 'subliminal_hit', -9, 'the photo sharpens')
c(T['s2b'] + 0.17, 'sub_heart50', -3, '50 Hz heartbeat thud')
c(T['s2b'] + 0.95, 'heartbeat_lubdub', -9, 'heartbeat', loop=True, dur=T['snap'] - T['s2b'] - 1.0, fade_out=0.05)
c(T['label_ir'], 'electronic_beep', -10, 'label: NECK ROTATION 94')
c(T['live_turn'], 'glitch_stab', -10, 'the live photo moves')
c(T['live_turn'], 'bone_clicks', -6, 'its neck')
# 3A/3B
c(T['fingers'], 'cloth_rustle', -8, 'its hand creeps over the cushion')
c(T['snap'], 'glitch_stab', -3, 'GLITCH_STAB (mid-word)')
c(T['snap'], 'bone_snap', 0, 'BONE_SNAP: the head turns in one frame')
c(T['snap'] + 0.4, 'electronic_beep', -10, 'label: LIPS CLOSED')
# 4A/4B the door
for k, (name, g) in enumerate((('knock1', 0), ('knock2', -1), ('knock3', -1))):
    c(T[name], 'door_thud', g, f'door thud {k + 1} (110 Hz body + slap)')
c(T['s4a'], 'whoosh_long', -8, 'whip-pan to the hallway')
c(T['knock2'] + 0.05, 'impact_soft', -7, 'a hand slaps the glass')
c(T['knock3'] + 0.05, 'impact_soft', -7, 'the other hand')
c(T['lightning'], 'thunder', -5, 'lightning: a silhouette', dur=3.0, fade_out=1.2)
c(T['handle'], 'lock_jiggle', -4, 'the handle rattles')
c(T['s4b'] + 0.17, 'door_thud_muffled', 0, 'Bob pounding outside (low-pass 400 Hz)')
c(T['s4b'] + 0.63, 'door_thud_muffled', -1, 'pounding')
c(T['label_out'], 'electronic_beep', -10, 'label: OUTSIDE = REAL BOB')
c(T['note'], 'glass_tap', -2, 'his phone slaps the glass')
c(T['note'], 'subliminal_hit', -8, 'the note')
# 5A/5B/5C the delayed feed
c(T['s5a'], 'crt_on', -1, 'the TV switches itself: CRT static + sub hum')
c(T['s5a'], 'tv_static_click', -4, 'click')
c(T['climb'], 'whispers', -15, 'it moves on the screen', dur=2.6, fade_out=0.6)
c(T['drop'], 'impact_soft', -10, 'it drops behind the couch (on the feed)')
c(T['s5b'] + 0.17, 'alert_beep2', -4, 'digital alert double-beep: FEED DELAY')
c(T['label_5s'], 'subliminal_hit', -5, 'label: 5 SECONDS AGO')
c(T['s5c'], 'bass_impact', -6, 'the real couch: the seat is empty')
c(T['s5c'], 'heartbeat_lubdub', -6, 'heartbeat, fast', loop=True, dur=T['ring'] - T['s5c'], fade_out=0.05)
c(T['dots'], 'creature_presence', -7, 'it rises behind your shoulder')
# 6A the ring + the hand
c(T['ring'], 'ringtone_blast', -1, 'RINGTONE at full volume', dur=2.1, fade_out=0.25)
c(T['ring'], 'cloth_rip', -2, 'cloth rip')
c(T['ring'], 'sub_thud', 0, 'the hand clamps your ankle')
c(T['ring'] + 0.02, 'phone_buzz160', -8, 'buzz')
c(T['yank'], 'impact_heavy', -4, 'it yanks')
c(T['yank'], 'object_slide', -5, 'your shoe scrapes the floor')
# 6B/7A/7B it rises, it unzips
c(T['s6b'], 'tendril_writhe', -4, 'ink tendrils', bus='amb', loop=True, dur=END - T['s6b'])
c(T['s6b'] + 0.1, 'creak_long', -7, 'it rises behind the couch')
c(T['s6b'] + 0.4, 'impact_soft', -6, 'tug on your ankle')
c(T['s6b'] + 1.33, 'impact_soft', -6, 'tug')
c(T['unzip'], 'mimic_slam', 0, 'JUMPSCARE_SLAM (mid-word, 0 ms attack)')
c(T['unzip'], 'flesh_zip_rip', 0, 'FLESH_ZIP_RIP')
c(T['unzip'], 'metal_screech', -4, 'METAL_SCREECH')
c(T['unzip'], 'glitch_stab', -8, 'VHS tear')
c(T['s7a'], 'bass_impact', -8, 'inches from the lens')
if 'D01' in L:                                                                 # the Mimic's stereo whisper layer (same take as D01)
    wide = os.path.join(VIDEO, 'audio', 'narration', 'fx', 'D01_wide_fit.wav')
    wide = wide if os.path.exists(wide) else os.path.join(VIDEO, 'audio', 'narration', 'fx', 'D01_wide.wav')
    c(L['D01'][0], wide, -6, 'the Mimic: whisper layer with stereo chorus')
c(T['kick'] + 0.02, 'door_thud', 1, 'the real Bob kicks the door in')
c(T['kick'] + 0.04, 'door_creak_slam', -7, 'door flies open', dur=0.9, fade_out=0.4)
c(T['kick'], 'whoosh_short', -6, 'whip to the hallway')
c(T['kick'] + 0.1, 'thunder', -13, 'storm outside', dur=2.2, fade_out=1.0)
c(T['peek_end'] - 0.2, 'whoosh_short', -6, 'whip back')
c(T['s7b'], 'stamp_thud', -4, 'the choice card slams in')
import compositor as CP  # noqa: E402
for k, fr in enumerate(CP.choice_times()):
    c(fr / TL.FPS, 'button_click', -8, f'box {k + 1} flashes')
c(T['box3'], 'glitch_stab', -7, 'mid-card micro-scare: the four eyes flare')
c(T['s7b'], 'heartbeat_lubdub', -6, 'heartbeat under the CTA', loop=True, dur=END - T['s7b'] - 0.05)
c(END - 0.9, 'loop_swell', -3, 'swell into the loop point (frame 0 slam)')

gates = []
for lid, pad in (('N07', 0.0), ('N17', 0.0)):                                  # nothing: the hits are SFX; music is ducked by the mixer
    pass
C_ = {'duration': END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
      'music': 'music_score.wav', 'music_gain_db': 0, 'music_cue': 'cue_video026',
      'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -4.5, 'duck_db': 6},
      'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C_, open(os.path.join(VIDEO, 'audio', 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
