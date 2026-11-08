# VIDEO_012 — Don't Touch The Vase · Part 1 (2dEDIT, real 2D horror with jumpscares)

66.3 s · 1080×1920 · 30 fps · `EXPORTS/VIDEO_012_Dont_Touch_The_Vase_Part_1.mp4`

## Hook and retention
* **Frame 0** shows Grandma's vase already rocking on the edge of the shelf, with the voice on frame 0: "Grandma had one rule. Never touch the vase." By 2.4 s comes "You just broke it." CRASH (flash + shake), black smoke, and a **3‑frame subliminal face** (glitch + hit) that makes viewers rewind.
* There is a new picture every 1–2.5 s, and open loops follow one after another: Mom hasn't blinked → the empty plate → Dad looks up → the power → the voice downstairs → **Mom's car isn't there**.
* The choice section never sits still. Shards twitch, a shape rises at the window, and red eyes open in the corner one pair at a time (each with clicks) while whispers rise. Then comes the last scare.

## Jumpscares (built, not random)
| # | Set‑up | Scare |
|---|---|---|
| 1 | A slow push on Dad lifting his head; the music fades out 0.9 s before; "Why did you let it out?" (voice pitched down + distorted) | His face stretches into the lens with void eyes and an open mouth. Glitch, red flash, 30 px shake, `jumpscare` shriek + tinnitus |
| fake‑out | The lock, a shadow under the door, "And then... nothing." 1.4 s of silence | Nothing happens (this lowers the viewer's guard) |
| 2 | The mirror: your reflection, lit by your phone. A beat of quiet | A cracked porcelain face is right behind your shoulder. Glitch, invert flash, shriek |
| 3 | The choice card, the eyes, the whispers; the music gate leaves 1.2 s of quiet | It lunges at the camera, then a cut to frame 0 (the vase) |

## Story
The vase shatters; something black crawls into the walls. At dinner, Mom's smile grows too wide, the sister chews on an empty plate, and Dad looks up (JS1). 2:13 AM: power out, phone at 4%. "Sweetie? Come downstairs." But Mom is still at work: lightning shows the empty driveway. Something climbs the stairs on all fours. You lock the bathroom door (fake‑out), then look in the mirror (JS2). Your phone dies. A whisper at your ear (am_nicole, pitched down and layered, with overdrive and reverb): "You broke my home. Now I live in yours." Choice: 1 glue the vase back · 2 burn the pieces · 3 run to Grandma's. Then JS3 → loop.

## Made with
* `anim2d.py`: 16 shots, 2,006 frames. New puppet options: long hair, void eyes, head stretch, a too‑wide smile. New monster: the cracked porcelain face, and a crawler on all fours.
* `edl_engine`: new effects `glitch`, `chroma`, `redflash`, `invert`, plus timed effects (`fx_t`).
* Voices: 24 lines with 4 timbres. Dad, Mom and the demon were post‑processed with sox (Dad pitched down + overdrive; Mom low‑passed with reverb, "from downstairs"; the demon layered at −9 semitones).
* **12 new SFX:** jumpscare shriek, subliminal hit, vase shatter, smoke hiss, moving whispers, fork scrape, wet chewing, tinnitus, thunder, rain, stair crawl, dread drone. 48 cues in total. The music has gates that leave silence before each scare.

## QA
−14.1 LUFS, −1.1 dBTP, no silence in the 3× loop.
* By design: the black power‑out (22.9–23.7 s), the phone dying (46.4–48.2 s), and the loop seam, which is the scare cut to the vase.
* Open: the audio runs 28 ms long.
* Fixed after the first export: the family was hidden behind the dinner table; the grandpa portrait spilled out of its frame; the 11 s choice section was static.
