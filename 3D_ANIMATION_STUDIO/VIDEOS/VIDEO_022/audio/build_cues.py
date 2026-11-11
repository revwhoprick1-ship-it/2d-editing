#!/usr/bin/env python3
"""VIDEO_022 sound -> cues.json. Instant scares (no riser, no music drop before). The house is quiet; every sound means something."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video022 as E  # noqa
B, s, e, END = E.B, E.s, E.e, E.END
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
cues = []


def c(t, name, gain, note, **kw):
    bus = kw.pop('bus', 'sfx')
    d = dict(t=round(t, 3), file=LIB[name], gain=gain - (5 if bus == 'sfx' else 0), bus=bus, note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'house_night', -2, 'night house', bus='amb', loop=True, dur=END)
c(0.6, 'whoosh_short', -8, 'the vase tips')
c(B['crash'], 'vase_shatter', 2, 'CRASH')
c(B['crash'] + 0.1, 'smoke_hiss', -4, 'black smoke')
c(s('N03') + 0.8, 'stair_crawl', -12, 'it slides under the bed', dur=2.0, fade_out=0.5)
c(B['note'], 'paper_rustle', -6, 'the note')
for k, rt in enumerate(B['rules']):
    c(rt - 0.05, 'pen_scribble', -14, f'rule {k + 1}', dur=0.8)
for k in range(23):
    c(B['count'] + k * 0.06, 'glass_tap', -22, 'counting pieces')
c(B['count'] + 1.4, 'subliminal_hit', -6, '23 / 24')
c(s('O01') - 0.2, 'heartbeat_muffled', -10, 'her voice downstairs')
c(s('N08'), 'stamp_thud', -8, "label: MOM'S CAR: GONE")
c(B['phone'], 'phone_buzz', -2, 'Grandma calling')
c(B['feet'], 'creak_long', -6, 'the floor right outside your door')
c(B['feet'] + 0.6, 'knob_turn', -6, 'the handle turns')
c(B['eyes'], 'tinnitus', -12, 'eyes burning', dur=B['js1'] - B['eyes'])
c(B['eyes'], 'heartbeat_lubdub', -6, 'heartbeat speeds up', loop=True, dur=B['js1'] - B['eyes'])
c(B['js1'] + 0.16, 'scare_slam', 1, 'JS1: you blinked. it is right there')
c(B['js1'] + 0.18, 'scare_shriek', -2, 'JS1 shriek')
c(B['js1'] + JS + 0.1, 'mimic_click', -6, 'porcelain clicking into place', loop=True, dur=s('N10') - B['js1'] - JS)
c(s('N10') + 0.4, 'subliminal_hit', -8, 'the face piece')
c(B['choice'], 'heartbeat_lubdub', -8, 'heartbeat under the choice', loop=True, dur=B['js2'] - B['choice'])
c(B['choice'], 'bone_clicks', -10, 'it steps closer', loop=True, dur=B['js2'] - B['choice'])
c(s('X02') - 0.3, 'whispers', -10, '"Blink."', dur=1.0, fade_out=0.3)
c(B['js2'], 'scare_slam', 2, 'JS2 end lunge')
c(B['js2'] + 0.02, 'scare_shriek', 0, 'JS2 shriek')

C = {'duration': END, 'loop': False, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
     'music': 'music_score.wav', 'music_gain_db': 2, 'music_cue': 'cue_video022',
     'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -3.2, 'duck_db': 5},
     'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
