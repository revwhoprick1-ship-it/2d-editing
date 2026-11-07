# VIDEO_005 — Audio Cue Sheet

Generated from `audio/cues.json` and `audio/narration/timing.json`. Narration offset 0.00 s. Music: `audio/music_score.wav` (original, `PIPELINE/audio/music_gen.py cue_video005`), base gain -3 dB, sidechain duck 8 dB under speech. Targets: narration -16 LUFS, master -14 LUFS integrated, true peak ≤ -1.0 dBTP.

**Seamless loop:** the mix is built circularly (`"loop": true`): tails past 32.4 s fold back onto 0 s, and ducking, filters and limiter run as if the video had already looped once. Music gates (hard silence): 21.68–22.66 s.

## Music map

| Time | Section | Content |
|---|---|---|
| 0-3 | Sleepy | soft pad; stab + kick on the slam |
| 3-9.5 | Comedy | bassoon staccato, tuba, light kit; drops out for the spray |
| 10.7-18.6 | Uprising | driving kit, brass stabs, tuba ostinato |
| 18.6-21.6 | Sneaky | tiptoe pizzicato |
| 21.7-22.7 | SILENCE | "The bathroom." dead air |
| 22.3-24.6 | Boss | low strings + building taiko, huge hit on the blast |
| 25.2-28.4 | Deflated | sad tuba |
| 28.4-31.5 | The tub wakes | sub drone, tremolo, ticking |

## Timeline

| Time (s) | Layer | Asset / line | Level / length | Sync event / note |
|---|---|---|---|---|
|   0.00 | NARRATION | L01 | hook (speed 1.12) | "Your toilet just quit its job." |
|   0.00 | AMB | room_tone.flac | -10 dB, 10.7s | bathroom room tone |
|   0.08 | SFX | lid_slam.flac | -8 dB | frame 3: the lid SLAMS |
|   0.30 | SFX | cartoon_tick.flac | -17 dB | eyes snap open |
|   1.00 | SFX | toilet_grumble.flac | -14 dB | small toilet: grumpy gurgle-growl (its voice) |
|   1.76 | NARRATION | L02 | confused (speed 1.12) | "Wait... what?" |
|   2.90 | SFX | mechanical_servo.flac | -20 dB | handle slowly turns toward him |
|   3.12 | NARRATION | L03 | reassuring (speed 1.12) | "Okay. Maybe it's just tired." |
|   5.04 | SFX | water_spray.flac | -9 dB | SPRAY to the face (slow-mo) |
|   5.12 | SFX | impact_soft.flac | -15 dB | hit |
|   5.29 | NARRATION | L04 | outraged (speed 1.12) | "Bro, seriously?!" |
|   5.57 | SFX | sweat_drip.flac | -19 dB | drips off his hair |
|   5.90 | SFX | sweat_drip.flac | -20 dB | drip |
|   6.60 | SFX | toilet_grumble.flac | -15 dB | smug gurgle |
|   6.88 | SFX | flush_big.flac | -8 dB | it flushes itself, violently |
|   7.03 | NARRATION | L05 | comic (speed 1.12) | "Now it flushes itself. Out of pure spite." |
|   7.13 | SFX | water_splash.flac | -13 dB | geyser splashes the room |
|   8.70 | SFX | record_scratch.flac | -14 dB | SOAKED freeze |
|   8.72 | SFX | camera_snap.flac | -16 dB | freeze frame |
|   9.40 | SFX | whoosh_short.flac | -15 dB | he bolts (whip out) |
|   9.60 | SFX | footstep_hard.flac | -17 dB | running footsteps |
|   9.90 | SFX | footstep_hard.flac | -17 dB | running footsteps |
|  10.40 | SFX | door_creak_slam.flac | -15 dB | out the door |
|  10.70 | AMB | city.flac | -20 dB, 7.9s | street |
|  10.70 | AMB | crowd.flac | -18 dB, 7.9s | panicking crowd |
|  10.75 | SFX | crowd_gasp.flac | -15 dB | screams |
|  10.77 | NARRATION | L06 | epic (speed 1.12) | "And it's not just yours. Every toilet on Earth is fighting back." |
|  13.50 | SFX | lid_slam.flac | -21 dB | chasing toilet chomps as it hops |
|  13.86 | SFX | lid_slam.flac | -23 dB | chasing toilet chomps as it hops |
|  14.22 | SFX | lid_slam.flac | -21 dB | chasing toilet chomps as it hops |
|  14.58 | SFX | lid_slam.flac | -23 dB | chasing toilet chomps as it hops |
|  14.73 | NARRATION | L07 | fast (speed 1.12) | "They chase you. They block the exits. They fire toilet paper like missiles." |
|  14.94 | SFX | lid_slam.flac | -21 dB | chasing toilet chomps as it hops |
|  15.30 | SFX | lid_slam.flac | -23 dB | chasing toilet chomps as it hops |
|  15.66 | SFX | lid_slam.flac | -21 dB | chasing toilet chomps as it hops |
|  16.01 | SFX | lid_slam.flac | -13 dB | blocker toilet snaps at the kid |
|  16.02 | SFX | lid_slam.flac | -23 dB | chasing toilet chomps as it hops |
|  16.16 | SFX | toilet_grumble.flac | -17 dB | blocker growls |
|  16.60 | SFX | tp_thump.flac | -14 dB | toilet-paper missile 1 |
|  16.85 | SFX | tp_thump.flac | -15 dB | toilet-paper missile 2 |
|  17.10 | SFX | tp_thump.flac | -14 dB | toilet-paper missile 3 |
|  17.35 | SFX | tp_thump.flac | -15 dB | toilet-paper missile 4 |
|  17.60 | SFX | tp_thump.flac | -14 dB | toilet-paper missile 5 |
|  18.60 | SFX | whoosh_short.flac | -17 dB | back to the bathroom |
|  18.80 | SFX | door_creak_slam.flac | -19 dB | he sneaks in |
|  18.94 | NARRATION | L08 | sly (speed 1.12) | "So he hides in the one room they'd never check." |
|  21.62 | NARRATION | L09 | deadpan (speed 1.12) | "The bathroom." |
|  21.86 | AMB | room_tone.flac | -6 dB, 1.0s | quiet... |
|  22.66 | SFX | dramatic_hit.flac | -15 dB | red eyes open (peak lands on the turn) |
|  23.26 | SFX | giant_roar.flac | -7 dB | GIANT ROAR (its voice: deep porcelain roar) |
|  24.31 | SFX | tension_riser.flac | -19 dB, 0.3s | charge |
|  24.56 | SFX | bass_impact.flac | -8 dB | BLAST impact frame |
|  24.56 | SFX | flush_big.flac | -9 dB | water cannon |
|  24.61 | SFX | water_spray.flac | -11 dB | blast spray |
|  25.21 | SFX | water_splash.flac | -9 dB | lands in the tub |
|  25.26 | SFX | body_thud.flac | -13 dB | tub thud |
|  26.01 | SFX | pop.flac | -21 dB | comment chip |
|  26.41 | NARRATION | L10 | exhausted (speed 1.12) | "I'm never using a toilet again!" |
|  28.62 | NARRATION | L11 | ominous (speed 1.12) | "Unfortunately, the bathtub disagrees." |
|  28.90 | SFX | drain_gurgle.flac | -11 dB | the tub wakes up: drain gurgles |
|  29.70 | SFX | cartoon_tick.flac | -15 dB | tub eyes open |
|  30.60 | SFX | drain_gurgle.flac | -14 dB | second gurgle |
|  31.35 | SFX | comedic_boing.flac | -11 dB | the tub flings him |
|  31.45 | SFX | whoosh_long.flac | -13 dB | flight back to the toilet -> loop (frame 3 slam) |
