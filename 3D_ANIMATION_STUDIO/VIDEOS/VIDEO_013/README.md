# VIDEO_013 — Benched · Part 2 (2dEDIT, real 2D). The audience chose 1: take the three.

55.6 s · 1080×1920 · 30 fps · `EXPORTS/VIDEO_013_Benched_Part_2.mp4`

**Stand‑alone hook (no Part 1 needed):** frame 0 is the release itself. He's in the air, the ball sits at the top of its arc, the clock reads 0:00.4, and the voice says "This shot decides the state championship." Then a record scratch and freeze, a red stamp `THE WATER BOY`, and "And the kid who took it... was the water boy." Context and contradiction land in under 5 s.

**Recap (about 13 s, "PREVIOUSLY", whip‑pans, faded grade):** these shots re‑use Part 1's shots from VIDEO_011, re‑timed: the bench, the laughing teammates, 500 shots a night, the viral video, the chant, and Coach's "You. Get in." Then the vote card: `YOU CHOSE 1 · TAKE THE THREE`.

**The play:**
* The inbound, then the defender (#10): "Aren't you the water boy?" Two seconds: step back. One second: release.
* Slow motion: the clock hits 0:00 while the ball is in the air. Cut to Coach frozen, Tyler frozen.
* It hits the rim (clang)... rolls... in near‑silence with a heartbeat... and drops in. Flash, SWISH, and the score goes to `61 – 60` FINAL.
* The gym explodes: confetti, teammates lift him. Tyler can't look, and the janitor is crying.
* Coach walks over and hands HIM the water bottle: "Kid... I think this one's yours."
* In the stands, a STATE U scout is already on the phone.

**Choice:** 1 forgive Coach · 2 take the college offer · 3 Coach fills the water bottles. TOP COMMENT = PART 3. It loops back to the shot.

**Made with:** `anim2d.py` (17 shots, 1,689 frames), which imports VIDEO_011's shot functions for the recap and the reaction close‑ups. 18 Chatterbox lines (narrator am_fenrir, defender am_eric, Coach am_onyx). 40 cues and the score `cue_video013`: a suspended chord, a driving recap beat, heartbeat tension, a held note through the slow motion, silence on the rim, and an anthem on the swish.

**QA:** −14.2 LUFS, −1.7 dBTP, no black or frozen frames, no silence or click in the 3× loop.
* By design: the loop seam is a cut from the celebration back to the shot.
* Still open: the audio is 40 ms longer than the video.
* Fixed after the first export: the two players overlapped in the side views; there was true silence on the rim; and the AAC encode pushed the true peak to −0.4 dBTP, so the mix now limits to −2.
