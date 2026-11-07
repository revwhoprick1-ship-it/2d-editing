# VIDEO_003 — Audio Cue Sheet

Generated from `audio/cues.json` and `audio/narration/timing.json`. Narration offset 0.00 s. Music: `audio/music_score.wav` (original, `PIPELINE/audio/music_gen.py cue_video003`), base gain -1 dB, sidechain duck 8 dB under speech. Targets: narration -16 LUFS, master -14 LUFS integrated, true peak ≤ -1.0 dBTP.

**Seamless loop:** the mix is built circularly (`"loop": true`): tails past 33.0 s fold back onto 0 s, and ducking, filters and limiter run as if the video had already looped once. Music gates (hard silence): .

## Music map

| Time | Section | Content |
|---|---|---|
| 0.0–2.2 | DROP | full 120 bpm groove + taiko/stab hit on frame 0 (wrapped from the loop build) |
| 2.2–5.75 | Light | plucks + half-time kit under grandma |
| 5.75–8.1 | Sad | minor plucks + pad for the dealer |
| 8.1–11.05 | Groove | beat back for the LinkedIn glow-up |
| 11.05–14.65 | Lo-fi | dull plucks for the podcast |
| 14.65–15.8 | SILENCE | record scratch, dead air: "here's the twist" |
| 15.8–21.5 | Up | groove + bells for Portugal |
| 21.5–25.2 | Warning | dissonant strings + taiko |
| 25.2–27.6 | Tension | ticking pulse, opening filter |
| 27.6–33.0 | Build | groove + rising hats, snare roll + riser into the drop on frame 0 |

## Timeline

| Time (s) | Layer | Asset / line | Level / length | Sync event / note |
|---|---|---|---|---|
|   0.00 | NARRATION | L01 | hook (speed 1.12) | "Every drug on Earth just became legal." |
|   0.00 | SFX | bass_impact.flac | -8 dB | E01 frame 0: the jump + stamp (score drop lands here too) |
|   0.05 | SFX | pop.flac | -12 dB | E01 title stamp |
|   2.15 | SFX | swish.flac | -14 dB | cut to grandma |
|   2.21 | NARRATION | L02 | deadpan (speed 1.12) | "Your grandma didn't even notice." |
|   2.60 | SFX | pill_rattle.flac | -10 dB | E02 grandma shakes the pile |
|   3.59 | NARRATION | L03 | punchline (speed 1.12) | "She's already on fourteen prescriptions." |
|   4.42 | SFX | counter_ticks.flac | -14 dB | counter 0 -> 14 prescriptions |
|   4.92 | SFX | cash_register.flac | -11 dB | counter lands on 14 |
|   5.45 | SFX | crowd_laugh.flac | -15 dB, 1.2s | laugh after "prescriptions" |
|   5.47 | SFX | whoosh_short.flac | -11 dB | whip to the dealer (peak on the cut) |
|   5.80 | NARRATION | L04 | news (speed 1.12) | "Drug dealers? Unemployed overnight." |
|   6.92 | SFX | impact_soft.flac | -10 dB | UNEMPLOYED stamp |
|   7.07 | SFX | sad_trombone.flac | -16 dB | sad trombone under "overnight" |
|   8.11 | NARRATION | L05 | comic (speed 1.12) | "This guy just changed his LinkedIn to freelance pharmacist." |
|   9.33 | SFX | notif_pop.flac | -9 dB | LinkedIn card pops |
|  10.41 | SFX | pop.flac | -14 dB | LIKE = ENDORSE chip |
|  10.77 | SFX | whoosh_short.flac | -11 dB | whip to the podcast |
|  11.13 | NARRATION | L06 | comic (speed 1.12) | "And the cartels went bankrupt and started a podcast." |
|  11.30 | SFX | pop.flac | -16 dB | CARTEL CAST lower third |
|  14.36 | SFX | crowd_laugh.flac | -12 dB, 1.0s | laugh on "podcast" |
|  14.70 | SFX | record_scratch.flac | -8 dB | freeze: "But here's the twist" |
|  14.72 | SFX | camera_snap.flac | -10 dB | freeze frame |
|  14.77 | NARRATION | L07 | suspense (speed 1.12) | "But here's the twist." |
|  15.51 | SFX | whoosh_short.flac | -11 dB | whip in to the globe |
|  15.84 | NARRATION | L08 | fact (speed 1.12) | "Portugal decriminalized every drug back in 2001." |
|  18.00 | SFX | positive_chime.flac | -13 dB | pin lands on Portugal / 2001 chip |
|  18.83 | NARRATION | L09 | fact (speed 1.12) | "Drug deaths went down. Nobody turned into a zombie." |
|  18.83 | SFX | pop.flac | -14 dB | DRUG DEATHS: DOWN chip |
|  20.62 | SFX | impact_soft.flac | -12 dB | cut to zombie |
|  20.62 | SFX | pop.flac | -16 dB | COMMENT banner |
|  21.12 | SFX | comedic_boing.flac | -11 dB | zombie snaps back to normal |
|  21.45 | SFX | swish.flac | -14 dB | whip to the lungs shot |
|  21.55 | NARRATION | L10 | warning (speed 1.12) | "Still, legal doesn't mean safe. Cigarettes are legal. Ask your lungs." |
|  22.53 | SFX | dramatic_hit.flac | -16 dB | LEGAL ≠ SAFE chip (hit peaks on "safe") |
|  24.20 | SFX | cough_fit.flac | -6 dB | cough fit (shot frames 81/90/99) |
|  25.15 | SFX | swish.flac | -15 dB | cut to the question |
|  25.38 | NARRATION | L11 | question (speed 1.12) | "So what's the most addictive thing left on Earth?" |
|  27.60 | SFX | phone_buzz.flac | -10 dB | phone comes out |
|  27.77 | NARRATION | L12 | reveal (speed 1.12) | "It's legal. It's free. And it's in your hand right now." |
|  28.25 | SFX | notif_pop.flac | -15 dB | notifications keep coming |
|  28.85 | SFX | notif_pop.flac | -16 dB | notifications keep coming |
|  29.45 | SFX | notif_pop.flac | -17 dB | notifications keep coming |
|  30.02 | SFX | bass_impact.flac | -11 dB | punch-in on "in your hand" |
|  30.07 | SFX | pop.flac | -15 dB | SHARE chip |
|  30.85 | NARRATION | L13 | loop (speed 1.12) | "That's why you're about to watch this again." |
