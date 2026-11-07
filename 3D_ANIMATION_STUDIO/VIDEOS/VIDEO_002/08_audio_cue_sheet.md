# VIDEO_002 — Audio Cue Sheet

Generated from `audio/cues.json` and `audio/narration/timing.json`. Narration offset 0.50 s. Music: `audio/music_score.wav` (original, `PIPELINE/audio/music_gen.py cue_video002`), base gain -3 dB, sidechain duck 9 dB under speech. Targets: narration -16 LUFS, master -14 LUFS integrated, true peak ≤ -1.0 dBTP.

**Seamless loop:** the mix is built circularly (`"loop": true`): tails past 36.1 s fold back onto 0 s, and ducking, filters and limiter run as if the video had already looped once. Music gates (hard silence): 12.66–14.68 s, 22.43–22.96 s.

## Music map

| Time | Section | Content |
|---|---|---|
| 33.55→36.1→0.55 | Muzak (loop seam) | F‑major elevator bossa (Rhodes, vibes, rim clave, shaker). Tape‑starts after the rewind, plays straight through the loop point and tape‑stops 0.12 s after the fart → one continuous performance across the seam |
| 0.62–6.05 | Chaos | Comedy oom‑pah in Bb at 150 bpm: tuba, bassoon tune, pizzicato double, polka kit; kick + open hat lift when the planet appears (2.9 s) |
| 6.05–6.77 | Wedding organ | "Here Comes the Bride" (Wagner, 1850 – public domain melody, our own performance); tape‑stops on the kiss fart (6.77 s) |
| 7.52–12.66 | Science | Curious marimba arpeggios in C (C–Am–F) at 110 bpm, soft pad; the Am change lands on "normal" (9.71 s) |
| 12.66–14.68 | SILENCE | Music gated: dead air before and during "Tiny." – the faint lands on silence + slide whistle |
| 15.15–16.68 | News bed | D‑minor 16th pulse + timpani + strings under the anchor; dun‑dun‑DUNNN SFX on "who / farted / first" |
| 17.96–22.44 | Investigation | Tremolo strings that climb a semitone on every ENHANCE, taiko hits on each zoom, stab on MATCH FOUND (20.77 s), rising pulse into the freeze |
| 22.44–22.98 | STOP‑TIME | Freeze frame: music cut dead under the shutter snap |
| 22.98–27.78 | Blame chain | Sneaky pizzicato ostinato, up a whole tone per accusation (E → F# → G#), brass stab + kick on every finger point |
| 27.80–28.91 | Deadpan | Only a thin high tremolo B while the kid stares |
| 28.91 | Hit | Diminished brass stab + taiko as the kid's finger lands on "him" |
| 29.85–31.56 | Suspicion | Low D drone under the innocent whistle |
| 31.56–32.64 | Swell | Dissonant tremolo cluster + taiko on "But this one?", cut by the VHS rewind |

## Timeline

| Time (s) | Layer | Asset / line | Level / length | Sync event / note |
|---|---|---|---|---|
|   0.00 | SFX | fart_chorus.flac | -3 dB | E01 frame 0: everyone farts (ELEV jolt f77); 2nd blast lands on the split-screen cut |
|   0.28 | SFX | crowd_gasp.flac | -13 dB | E01 the four passengers gasp |
|   0.50 | NARRATION | L01 | hook (speed 1.04) | "Eight billion people just farted. At the exact same second!" |
|   0.52 | SFX | swish.flac | -15 dB | E02 split transition |
|   0.60 | SFX | impact_soft.flac | -14 dB | E02 3-way split slams in |
|   2.00 | SFX | elevator_ding.flac | -15 dB | E03 awkward elevator ding during the side-eye |
|   2.62 | SFX | whoosh_short.flac | -12 dB | E03->E04 whip pan to the planet (peak on the cut) |
|   2.90 | SFX | fart_rumble.flac | -11 dB | E04 the planet rumbles |
|   2.90 | SFX | v002_globe_popcorn.flac | -7 dB | E04 45 puffs pop across the globe: one pitched pfft per puff frame |
|   2.95 | SFX | counter_ticks.flac | -15 dB | E04 counter 0 -> 8,000,000,000 |
|   4.00 | NARRATION | L02 | excited (speed 1.12) | "In elevators. On live TV. In the middle of a wedding kiss!" |
|   4.01 | SFX | impact_soft.flac | -18 dB | E05 cut |
|   4.18 | SFX | cartoon_tick.flac | -13 dB | E05 nose pinch (f169) |
|   4.18 | SFX | swish.flac | -24 dB | E05 hand fans the air (f169) |
|   4.31 | SFX | swish.flac | -24 dB | E05 hand fans the air (f173) |
|   4.44 | SFX | swish.flac | -24 dB | E05 hand fans the air (f177) |
|   4.58 | SFX | swish.flac | -24 dB | E05 hand fans the air (f181) |
|   4.71 | SFX | swish.flac | -24 dB | E05 hand fans the air (f185) |
|   4.83 | SFX | tv_static_click.flac | -16 dB | E06 cut to the news feed |
|   5.10 | SFX | fart_wet.flac | -8 dB | E06 anchor jolts on air (f8) |
|   5.38 | SFX | cartoon_tick.flac | -13 dB | E06 frozen smile, eye twitch (f16) |
|   5.65 | SFX | cartoon_tick.flac | -13 dB | E06 frozen smile, eye twitch (f24) |
|   5.92 | SFX | cartoon_tick.flac | -13 dB | E06 frozen smile, eye twitch (f32) |
|   6.76 | SFX | fart_trumpet.flac | -10 dB | E07 the kiss is interrupted (f22, groom side) |
|   6.78 | SFX | record_scratch.flac | -11 dB | E07 organ needle-drop: the wedding music dies |
|   6.80 | SFX | fart_squeaker.flac | -12 dB | E07 bride answers (f23) |
|   7.30 | SFX | crowd_eww.flac | -12 dB, 1.0s | E07 guests react (after "kiss!") |
|   7.45 | SFX | swish.flac | -14 dB | E08 whip-in to the globe |
|   7.52 | NARRATION | L03 | calm (speed 1.06) | "Scientists said: relax, farting is normal." |
|   7.57 | SFX | v002_globe_orbit.flac | -19 dB | E08 sparse distant pffts, one per late puff frame (under narration) |
|   7.92 | SFX | pop.flac | -17 dB | E08 "13-21x a day" chip pops in |
|   9.71 | SFX | positive_chime.flac | -12 dB | E08 TOTALLY NORMAL chip |
|  10.16 | AMB | crowd.flac | -27 dB, 3.0s | E09 polite wedding murmur that dies before "Tiny." |
|  10.21 | NARRATION | L04 | calm (speed 1.06) | "The smell is just a tiny bit of sulfur gas." |
|  10.31 | SFX | pop.flac | -19 dB | E09 sulfur speck appears |
|  11.78 | SFX | sparkle_o2.flac | -14 dB | E09 "SULFUR (TINY)" label |
|  13.21 | NARRATION | L05 | humor (speed 0.9) | "Tiny." |
|  13.87 | SFX | slide_whistle_down.flac | -9 dB | E10b guests topple (speed ramp) |
|  14.27 | SFX | body_thud.flac | -6 dB | E10b guest 1 hits the floor (f154) |
|  14.37 | SFX | body_thud.flac | -7 dB | E10b guest 2 hits the floor (f159) |
|  14.47 | SFX | body_thud.flac | -6 dB | E10b guest 3 hits the floor (f164) |
|  14.71 | SFX | news_sting.flac | -9 dB | E11 breaking-news sting on the cut |
|  14.75 | NARRATION | L06 | dramatic (speed 1.08) | "So the whole planet asked one question: who farted first?" |
|  16.68 | SFX | dun_dun_dun.flac | -11 dB | E11 dun / dun / DUNNN on "who / farted / first" |
|  17.94 | SFX | tv_static_click.flac | -10 dB | E12 cut to security footage |
|  17.99 | NARRATION | L07 | urgent (speed 1.05) | "Security footage. Enhance. Enhance. Enhance!" |
|  18.95 | SFX | enhance_beep.flac | -10 dB | E12 ENHANCE #1: whoosh on the zoom, beep as the pixels resolve |
|  19.57 | SFX | enhance_beep.flac | -10 dB | E12 ENHANCE #2: whoosh on the zoom, beep as the pixels resolve |
|  20.20 | SFX | enhance_beep.flac | -10 dB | E12 ENHANCE #3: whoosh on the zoom, beep as the pixels resolve |
|  20.62 | SFX | riser_2s.flac | -16 dB | E12-E13 riser peaks on the freeze frame |
|  20.70 | SFX | tv_static_click.flac | -14 dB | E12 cut to the face crop |
|  20.77 | SFX | electronic_beep.flac | -12 dB | E12 MATCH FOUND |
|  20.89 | SFX | electronic_beep.flac | -12 dB | E12 MATCH FOUND (2nd beep) |
|  20.98 | NARRATION | L08 | dramatic (speed 1.0) | "One elevator. One guy." |
|  21.48 | SFX | cloth_rustle.flac | -20 dB | E13a everyone slowly turns to stare |
|  22.41 | AMB | room_tone.flac | -2 dB, 0.7s | E13b room tone under the stop-time, so the pause reads as a pause, not a dropout |
|  22.45 | SFX | camera_snap.flac | -6 dB | E13b freeze-frame shutter (music stops dead) |
|  22.59 | SFX | pop.flac | -14 dB | E13b LIKE = GUILTY chip |
|  22.98 | SFX | impact_soft.flac | -15 dB | E14 unfreeze |
|  23.00 | NARRATION | L09 | excited (speed 1.16) | "He blamed grandma. Grandma blamed the businessman. The businessman blamed the kid." |
|  23.04 | SFX | swish.flac | -18 dB | EL_BLAME1 arm swings up to point (f262); stab in the score at f267 |
|  23.45 | SFX | pop.flac | -19 dB | E14 tag 1 GRANDMA |
|  24.05 | SFX | whoosh_short.flac | -11 dB | EL_BLAME1 whip pan follows the finger (peak on the cut) |
|  24.34 | SFX | pop.flac | -18 dB | E15 COMMENT banner (after the LIKE chip leaves) |
|  24.40 | SFX | swish.flac | -18 dB | EL_BLAME2 arm swings up to point (f308); stab in the score at f313 |
|  25.89 | SFX | whoosh_short.flac | -11 dB | EL_BLAME2 whip pan follows the finger (peak on the cut) |
|  26.23 | SFX | swish.flac | -18 dB | EL_BLAME3 arm swings up to point (f356); stab in the score at f361 |
|  26.45 | SFX | pop.flac | -19 dB | E16 tag 2 BUSINESSMAN |
|  26.85 | SFX | pop.flac | -19 dB | E16 tag 3 KID |
|  27.50 | SFX | whoosh_short.flac | -11 dB | EL_BLAME3 whip pan follows the finger (peak on the cut) |
|  27.84 | NARRATION | L10 | humor (speed 1.0) | "And the kid... blamed him." |
|  27.94 | SFX | pop.flac | -19 dB | E17 tag 3 KID |
|  28.69 | SFX | swish.flac | -15 dB | E17 the kid finally points (f406) |
|  28.90 | SFX | bass_impact.flac | -10 dB | E17 the point lands on "him" (f411) |
|  29.18 | SFX | comedic_boing.flac | -11 dB | E18 mascot shocked (flash + shake) |
|  29.30 | SFX | crowd_gasp.flac | -19 dB | E18 passengers gasp |
|  29.84 | NARRATION | L11 | calm (speed 0.98) | "Farts aren't contagious." |
|  29.94 | SFX | whistle_innocent.flac | -13 dB, 1.6s | E19 innocent whistle (pucker f454), cut off by "But" |
|  30.04 | SFX | sweat_drip.flac | -13 dB | E19 sweat drop 1 spawns |
|  30.65 | SFX | sweat_drip.flac | -15 dB | E19 sweat drop 2 spawns |
|  31.15 | SFX | sweat_drip.flac | -14 dB | E19 sweat drop 1 spawns |
|  31.55 | NARRATION | L12 | suspense (speed 0.92) | "But this one?" |
|  31.55 | SFX | bass_impact.flac | -9 dB | E19 "But this one?" punch-in |
|  31.78 | SFX | sweat_drip.flac | -17 dB | E19 sweat drop 2 spawns |
|  32.28 | SFX | sweat_drip.flac | -16 dB | E19 sweat drop 1 spawns |
|  32.63 | SFX | vhs_rewind.flac | -9 dB, 0.9s | E20 VHS rewind back to 3:13:59 |
|  33.53 | SFX | button_click.flac | -17 dB | E21 tape PLAY clunk; muzak tape-starts in the score |
|  33.56 | NARRATION | L13 | suspense (speed 0.95) | "It all started... with one tiny..." |
|  35.72 | SFX | fart_tiny_pfft.flac | -6 dB | E21 "...one tiny..." pfft (ELEV f66) = Patient Zero; loops into E01 |
