#!/usr/bin/env python3
"""VIDEO_017 sound design -> cues.json. The cabin drone is the floor of the whole film; when Lawrence unbuckles it
CUTS OUT (dead silence) - the loudest thing in the video is that silence. Dialogue always on top (ducking)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video017 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
LIB['room_tone'] = 'AUDIO/ambience/room_tone.flac'
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'seatbelt_ding', 0, 'DING (frame 0)')
c(0.0, 'cabin_drone', -6, 'engines', bus='amb', loop=True, dur=B['click2'], fade_out=0.05)
c(0.05, 'cloth_rustle', -10, '212 passengers sit up at once')
c(B['click1'], 'buckle_click', -12, 'Lawrence fiddles with the buckle (not open)')
c(B['map'] + 0.1, 'electronic_beep', -16, 'screen')
c(s('M02') + 0.2, 'phone_buzz', -18, 'the phone on the empty seat')
c(B['cart'], 'cart_rattle', -8, 'the cart', dur=B['js1'] - B['cart'], fade_out=0.3)
c(B['feet'] + 0.1, 'creak_long', -14, 'joints bending the wrong way')
c(B['js1'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 1: "You looked."')
c(B['js1'] + 0.5, 'tinnitus', -8, 'ringing')
c(B['click2'], 'buckle_click', 0, 'CLICK. Lawrence unbuckles')
c(B['click2'] + 0.1, 'dread_drone', -14, 'silence... except this', bus='amb', dur=B['js2'] - B['click2'], fade_out=0.1)
c(B['heads'], 'head_turn_mass', -4, '212 heads turn at once')
c(B['bin'] + 0.2, 'creak_long', -8, 'the bin opens by itself')
c(B['js2'] - 0.03, 'jumpscare', 4, 'JUMPSCARE 2: Lawrence yanked up')
c(B['js2'] + 0.3, 'bin_slam', 2, 'SLAM')
c(B['js2'] + 0.6, 'crunch', -2, 'inside the bin')
c(B['js2'] + 1.6, 'crunch', -6, 'again')
c(B['js2'], 'cabin_drone', -8, 'engines back', bus='amb', loop=True, dur=B['land'] - B['js2'] - 1.0, fade_out=0.5)
for k in range(5):
    c(B['tray'] + 0.3 + k * 0.45, 'sweat_drip', -6, 'blood drips on the tray')
c(B['tray'] + 1.15, 'body_thud', -6, 'his sneaker hits the tray')
c(B['stowed'] - 0.6, 'seatbelt_ding', -4, 'ding: captain')
c(B['bins'], 'vent_scratch', -6, 'every bin thumping', loop=True, dur=e('B04') + 0.6 - B['bins'])
for k in range(4):
    c(B['bins'] + k * 0.35, 'door_knock', -10 - k, 'bin bangs')
c(B['reveal'], 'mimic_click', -6, 'it unfolds')
c(B['reveal'] + 0.4, 'creak_long', -6, 'neck unfolding')
c(B['belt'] + 0.3, 'buckle_click', -2, "Bob's belt pops open")
c(B['belt'], 'thunder', -12, 'turbulence')
c(B['ceiling'], 'whoosh_long', -6, 'oxygen masks drop')
c(B['ceiling'] + 0.4, 'stair_crawl', -4, 'crawling on the ceiling')
c(B['js3'] - 0.03, 'jumpscare', 3, 'JUMPSCARE 3: its face, upside down')
c(B['land'] - 0.4, 'seatbelt_ding', -2, 'DING: landed')
c(B['land'], 'room_tone', -10, 'quiet cabin', bus='amb', loop=True, dur=B['open_'] - B['land'])
c(s('B06') + 0.35, 'buckle_click', -4, 'Bob unbuckles')
c(B['window'], 'cabin_drone', -10, 'engines: still flying', bus='amb', loop=True, dur=END - B['window'])
c(B['open_'] - 0.6, 'creak_long', -4, 'the bin above Bob opens')
c(END - 0.25, 'seatbelt_ding', -2, 'DING -> loops into frame 0')

C = {'duration': END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video017',
     'music_gates': [[B['click2'], B['js2'] - 0.02, 0.05], [B['js1'] - 0.5, B['js1'] - 0.02, 0.1], [B['js3'] - 0.5, B['js3'] - 0.02, 0.1]],
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -2.0, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
