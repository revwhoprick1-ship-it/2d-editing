# VIDEO_007 — After Hours · Part 1 (2dEDIT, real 2D)

83.2 s · 1080×1920 · 30 fps · seamless loop · `EXPORTS/VIDEO_007_After_Hours_Part_1.mp4`

## Story (2nd person, choose-your-path like the reference)
* **Hook (0–6 s, flash-forward):** you are hiding under a desk. Something stands right outside the door: feet shadows under it, a tall shape behind the frosted glass, and the handle slowly pressing down. "Ten minutes ago... all you wanted was to change one grade. Now... something knows you're here." The HUD already reads `GRADE 88`.
* **VHS rewind**, then the title `AFTER HOURS / PART 1`. HUD: `11:52 PM · GATE · GRADE 38`.
* **The keys:** the night guard snores. You slide the key ring off his belt; he SNORTS, and you freeze.
* **Building C:** you run across the yard. In the dark corridor, every step echoes. The third key turns the lock on the teachers' office.
* **The files:** the drawer is full of student records, not tests, going back to 1987. Each one gets a red **KEPT** stamp (one thud per file, then a huge KEPT). The newest file shows **your photo** with the stamp box still empty, and a sticky note: "HE COMES BACK FOR THE ONES WHO CHEAT." The narrator never mentions the photo, so it is a detail to find on a rewatch.
* **The cheat:** a red pen turns 38 into 88, and the HUD grade flips to 88 in red.
* **BANG:** shake, flash, papers fly, then dead silence. "What was that?"
* **The peek:** through a crack in the door, a 2.4 m figure stands under the last flickering light, holding the guard's flashlight. The guard's cap lies on the floor in the beam. Its head turns with bone clicks, and it LOOKS AT YOU (sting, flash).
* **Ending:** you dive under the desk. Its footsteps come closer and stop right outside the door, which is the same picture as frame 0, so the video loops. A choice card asks "HOW DO YOU GET OUT?": 1 window · 2 filing cabinet · 3 stairs, with "COMMENT 1, 2 OR 3 · TOP COMMENT = PART 2".

## How it is made
* All flat 2D vector drawing (Skia): `anim2d.py` draws 18 shots and 2,472 frames in about 2 min on CPU. The puppet comes from `PIPELINE/twod/flat.py`: straight arms, a front/back stepping walk, a side-view walk/run cycle, crouch, a guard variant and the monster.
* Captions are in the 2dEDIT style (white with one red keyword; dialogue in quotes labelled `YOU`). The HUD copies the reference layout: three columns, each a small label over a bold value.
* **Voices:** free local Chatterbox, 26 lines. The narrator uses the Kokoro am_fenrir timbre and you use am_puck (whispers). Every word passed the Whisper check; the only differences are digits. "red pen... little line" needed 4 takes ("pin" and "lime" were rejected).
* **Sound:** 13 new synthesised SFX (snore, snort, key jingle, lock jiggle and click, stamp thud, pen scribble, paper rustle, panicked breathing, monster step, bone clicks, big bang, door handle), 85 cues in total, plus a horror score (`music_gen.cue_video007`). The music goes silent after the BANG and when the footsteps stop.

## QA (`qc/`)
1080×1920 · 30 fps · H.264/AAC · −14.2 LUFS · −1.0 dBTP. No black frames and no frozen frames. The loop test passes every check: the seam change is ordinary, there are no black frames, no silence and no click, and audio and video lengths match.
Fixed after the first export: the 38→88 pen moment was framed off the score and sat under the captions; the monster was too small in the hallway POV; the music was too quiet (−32 → −26 LUFS in the mix).
Known weak spots: the hand is hard to read in the key‑ring and door close‑ups; the guard's sitting pose is simple; the choice card covers the door in the last shot.
