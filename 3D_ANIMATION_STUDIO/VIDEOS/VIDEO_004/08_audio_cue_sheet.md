# VIDEO_004 — Audio Cue Sheet

Generated from `audio/cues.json` and `audio/narration/timing.json`. Narration offset 0.00 s. Music: `audio/music_score.wav` (original, `PIPELINE/audio/music_gen.py cue_video004`), base gain -2 dB, sidechain duck 8 dB under speech. Targets: narration -16 LUFS, master -14 LUFS integrated, true peak ≤ -1.0 dBTP.

**Seamless loop:** the mix is built circularly (`"loop": true`): tails past 33.6 s fold back onto 0 s, and ducking, filters and limiter run as if the video had already looped once. Music gates (hard silence): 22.40–24.32 s.

## Music map

| Time | Section | Content |
|---|---|---|
| 30.55→33.6→2.9 | Curiosity (loop bed) | bell motif + pad, plays across the loop point |
| 2.9–10 | Excitement | bouncy 124 bpm groove |
| 10–15.9 | Floating | pads + slow bells under the physics explainer |
| 16.3–17.9 | Uh-oh | sub drone |
| 17.9–20.4 | Panic | fast semitone pulse + taiko |
| 20.4–22.4 | Countdown | heartbeat kicks |
| 22.4–24.34 | SILENCE | everything stops, even the street |
| 24.34–26.94 | Payoff | taiko + brass hit, strings + snare build during the fall |
| 26.94–30.23 | Comedy | tiptoe pizzicato |

## Timeline

| Time (s) | Layer | Asset / line | Level / length | Sync event / note |
|---|---|---|---|---|
|   0.00 | NARRATION | L01 | hook (speed 1.12) | "Gravity just switched off. You've got ten seconds." |
|   0.00 | AMB | city.flac | -24 dB, 22.3s | street ambience (stops dead before gravity returns) |
|   0.00 | AMB | air_float.flac | -16 dB, 22.3s | weightless shimmer while floating |
|   0.00 | SFX | whoosh_long.flac | -16 dB | frame 0: feet leave the ground |
|   0.55 | SFX | crowd_gasp.flac | -15 dB | passers-by gasp |
|   2.86 | NARRATION | L02 | joy (speed 1.12) | "Wait. I'm flying?!" |
|   3.55 | SFX | whoosh_long.flac | -9 dB | the fatal jump |
|   4.65 | NARRATION | L03 | comic (speed 1.12) | "Your phone. Your coffee. That guy's sneeze." |
|   4.85 | SFX | swish.flac | -15 dB | phone drifts off |
|   5.33 | SFX | bubble.flac | -12 dB | coffee blob escapes the cup |
|   5.86 | SFX | sneeze.flac | -7 dB | ah... CHOO lands on the freeze frame |
|   6.71 | SFX | whoosh_short.flac | -10 dB | sneeze propels him backwards |
|   7.45 | SFX | record_scratch.flac | -11 dB | PHYSICS CHECK pattern interrupt |
|   7.48 | NARRATION | L04 | fact (speed 1.12) | "Quick physics check: you won't shoot into space." |
|   7.50 | SFX | impact_soft.flac | -12 dB | stamp |
|  10.00 | SFX | whoosh_short.flac | -16 dB | diagram slides in |
|  10.00 | NARRATION | L05 | fact (speed 1.12) | "Earth keeps spinning, you keep drifting straight, and the ground slowly falls away. About two meters in ten seconds." |
|  16.38 | NARRATION | L06 | ominous (speed 1.12) | "Unless you jumped." |
|  16.98 | SFX | record_scratch.flac | -9 dB | freeze: he jumped |
|  17.03 | SFX | camera_snap.flac | -10 dB | freeze frame |
|  17.92 | NARRATION | L07 | panic (speed 1.12) | "Why did I jump?!" |
|  18.75 | SFX | whoosh_long.flac | -12 dB | vertigo push: his view of the street |
|  18.75 | AMB | wind.flac | -18 dB, 0.8s | high-altitude wind |
|  18.91 | NARRATION | L08 | panic (speed 1.12) | "Where am I supposed to land?!" |
|  20.42 | NARRATION | L09 | countdown (speed 0.95) | "Three. Two. One." |
|  22.30 | AMB | room_tone.flac | -6 dB, 2.0s | eerie hush before gravity returns (quiet, not dead air) |
|  23.59 | NARRATION | L10 | payoff (speed 1.12) | "And gravity's back." |
|  24.34 | AMB | city.flac | -24 dB, 9.3s | street ambience back after the crash |
|  24.34 | SFX | bass_impact.flac | -4 dB | GRAVITY ON (impact frame) |
|  24.34 | SFX | impact_heavy.flac | -8 dB | everything drops |
|  24.39 | SFX | scream_fall.flac | -9 dB | mascot screams all the way down |
|  24.44 | SFX | crowd_gasp.flac | -12 dB | crowd |
|  25.42 | SFX | impact_heavy.flac | -9 dB | car lands and bounces |
|  25.44 | SFX | water_splash.flac | -11 dB | fountain water comes back down |
|  25.52 | SFX | body_thud.flac | -7 dB | extra 1 lands (2-3.6 m drop: a thud, not an injury) |
|  25.58 | SFX | body_thud.flac | -8 dB | extra 2 lands (2-3.6 m drop: a thud, not an injury) |
|  25.64 | SFX | body_thud.flac | -9 dB | extra 3 lands (2-3.6 m drop: a thud, not an injury) |
|  26.94 | SFX | comedic_boing.flac | -5 dB | lands on the mattress pile |
|  26.94 | SFX | body_thud.flac | -12 dB | mattress thump |
|  27.34 | SFX | pop.flac | -16 dB | comment chip |
|  27.76 | NARRATION | L11 | relief (speed 1.12) | "Okay. I'm never complaining about gravity again." |
|  29.00 | SFX | pop.flac | -16 dB | subscribe chip |
|  30.23 | SFX | bonk.flac | -4 dB | his phone finally comes down: BONK |
|  30.50 | SFX | swish.flac | -16 dB | jump-cut back to his mark |
|  31.68 | NARRATION | L12 | loop (speed 1.12) | "Now imagine it happens again." |
|  32.76 | SFX | whoosh_long.flac | -13 dB | rising whoosh that peaks on the loop point (feet about to lift again) |
