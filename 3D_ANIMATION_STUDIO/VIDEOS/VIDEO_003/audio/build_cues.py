#!/usr/bin/env python3
"""VIDEO_003 sound design: cues.json from the EDL's word times and shot frames, then run mix.py."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import edit_video003 as E  # noqa
C, F = 'AUDIO/sound_effects/comedy/', 'AUDIO/sound_effects/'
LIB = {d['name']: 'AUDIO/' + d['file'] for d in json.load(open(os.path.join(HERE, '..', '..', '..', 'AUDIO', 'sound_effects', 'LIBRARY.json')))}
cues = []


def c(t, name, gain, note, **kw):
    d = dict(t=round(t, 3), file=LIB[name], gain=gain, bus='sfx', note=note)
    d.update({k: v for k, v in kw.items() if v is not None})
    cues.append(d)


c(0.0, 'bass_impact', -8, 'E01 frame 0: the jump + stamp (score drop lands here too)')
c(0.05, 'pop', -12, 'E01 title stamp')
c(2.15, 'swish', -14, 'cut to grandma')
c(2.6, 'pill_rattle', -10, 'E02 grandma shakes the pile', pan=-0.2)
c(E.t_14 - 0.05, 'counter_ticks', -14, 'counter 0 -> 14 prescriptions')
c(E.t_14 + 0.45, 'cash_register', -11, 'counter lands on 14')
c(5.45, 'crowd_laugh', -15, 'laugh after "prescriptions"', dur=1.2, fade_out=0.3)
c(5.47, 'whoosh_short', -11, 'whip to the dealer (peak on the cut)')
c(E.t_unemp, 'impact_soft', -10, 'UNEMPLOYED stamp')
c(E.t_unemp + 0.15, 'sad_trombone', -16, 'sad trombone under "overnight"')
c(E.t_linked, 'notif_pop', -9, 'LinkedIn card pops')
c(E.t_pharm + 0.2, 'pop', -14, 'LIKE = ENDORSE chip')
c(10.77, 'whoosh_short', -11, 'whip to the podcast')
c(11.3, 'pop', -16, 'CARTEL CAST lower third')
c(E.t_pod + 0.55, 'crowd_laugh', -12, 'laugh on "podcast"', dur=1.0, fade_out=0.3)
c(E.t_twist - 0.07, 'record_scratch', -8, 'freeze: "But here\'s the twist"')
c(E.t_twist - 0.05, 'camera_snap', -10, 'freeze frame')
c(E.t_port - 0.33, 'whoosh_short', -11, 'whip in to the globe')
c(E.w('L08', '2001'), 'positive_chime', -13, 'pin lands on Portugal / 2001 chip')
c(E.t_deaths, 'pop', -14, 'DRUG DEATHS: DOWN chip')
c(E.t_zombie - 0.35, 'impact_soft', -12, 'cut to zombie')
c(E.t_zombie + 0.15, 'comedic_boing', -11, 'zombie snaps back to normal')
c(E.t_zombie - 0.35, 'pop', -16, 'COMMENT banner')
c(21.45, 'swish', -14, 'whip to the lungs shot')
c(E.t_safe - 0.4, 'dramatic_hit', -16, 'LEGAL ≠ SAFE chip (hit peaks on "safe")')
c(24.2, 'cough_fit', -6, 'cough fit (shot frames 81/90/99)')
c(25.15, 'swish', -15, 'cut to the question')
c(27.6, 'phone_buzz', -10, 'phone comes out')
for k, t in enumerate((28.25, 28.85, 29.45)):
    c(t, 'notif_pop', -15 - k, 'notifications keep coming')
c(E.t_hand + 0.05, 'bass_impact', -11, 'punch-in on "in your hand"')
c(E.t_hand + 0.1, 'pop', -15, 'SHARE chip')
C_ = {'duration': E.END, 'loop': True, 'narration': 'narration/narration_raw.wav', 'narration_offset': 0.0,
      'music': 'music_score.wav', 'music_gain_db': -1,
      'music_map': [['0.0–2.2', 'DROP', 'full 120 bpm groove + taiko/stab hit on frame 0 (wrapped from the loop build)'],
                    ['2.2–5.75', 'Light', 'plucks + half-time kit under grandma'], ['5.75–8.1', 'Sad', 'minor plucks + pad for the dealer'],
                    ['8.1–11.05', 'Groove', 'beat back for the LinkedIn glow-up'], ['11.05–14.65', 'Lo-fi', 'dull plucks for the podcast'],
                    ['14.65–15.8', 'SILENCE', 'record scratch, dead air: "here\'s the twist"'], ['15.8–21.5', 'Up', 'groove + bells for Portugal'],
                    ['21.5–25.2', 'Warning', 'dissonant strings + taiko'], ['25.2–27.6', 'Tension', 'ticking pulse, opening filter'],
                    ['27.6–33.0', 'Build', 'groove + rising hats, snare roll + riser into the drop on frame 0']], 'music_cue': 'cue_video003',
      'targets': {'narration_lufs': -16, 'master_lufs': -14, 'true_peak': -1.0, 'duck_db': 8},
      'cues': sorted(cues, key=lambda d: d['t'])}
json.dump(C_, open(os.path.join(HERE, 'cues.json'), 'w'), indent=1, ensure_ascii=False)
print('CUES_OK', len(cues))
