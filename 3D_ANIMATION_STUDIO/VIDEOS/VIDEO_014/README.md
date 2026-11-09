# VIDEO_014 — Don't Touch The Vase · Part 2 (2dEDIT, real 2D horror)

76.8 s · 1080×1920 · 30 fps · `EXPORTS/VIDEO_014_Dont_Touch_The_Vase_Part_2.mp4` · watermark `@insidethemindlessvault`
Top comment (Part 1): **@yungthuggaxo** (29 likes), "grab the pieces and run to gma" → choice 3. **Lore bible: `VIDEOS/VASE_LORE.md`.**

**Stand‑alone hook:** frame 0 shows an old woman's eye in a door peephole, in the rain. "Before I open this door... blink." "Because the thing from the vase never blinks." It sets up a rule and a threat in about 4 s, with no Part 1 needed.

**Recap (5 s, "PREVIOUSLY"):** these are Part 1 shots: the vase breaking, Mom's smile, Dad's face (glitched), the mirror. Then the top‑comment card appears with `YOU CHOSE 3 · RUN TO GRANDMA'S`.

**Story:**
* Three streets in the rain with a pillowcase of porcelain. It calls in Dad's voice ("Come home, buddy."), then Mom's ("Sweetie, you forgot something."), then **your own** ("Don't let her in.") while your mouth stays shut.
* **JS1:** lightning, and it's on the roof right next to you.
* You blink, so the door opens. Grandma: "Give me the pieces. All of them." On the table there are **23 / 24**: the **face piece is missing**.
* **The lore (1968, faded):** Grandma Rose's twin brother **Eli** stopped blinking. Their mother, a porcelain painter, **painted every room of the house onto the vase** so the thing would think it was home. The smoke was drawn in and the vase sealed with black wax. "Without the face, we can't seal it back in."
* Three slow knocks: "Rosie? It's me. It's Eli. Let me in." (a child's voice, pitched up, layered with a low double). Eli would be 70 now; the voice is still twelve.
* **JS2:** the peephole shows a child's porcelain face pressed to the glass.

**Choice:** 1 go back for the face piece · 2 let Grandma face it alone · 3 open the door for Eli. While the card is up, the knocking continues, the handle turns and eyes open. **JS3** lunge, then a cut to frame 0.

**Consistency with Part 1:**
* The "GRANDMA'S HOUSE" HUD in Part 1 is the old family house.
* Mom being at work and the voice imitation both match.
* "Why did you let it out?" and "You broke my home. Now I live in yours." are explained by the vase‑as‑home rule.
* The battery stays at 0% because the phone died in Part 1.
* The wax seal is visible on the vase in Part 1.

**Made with:** `anim2d.py` (18 shots, 2,325 frames), which imports VIDEO_012's porcelain face, the crawler and the recap shots. There are 25 Chatterbox lines with 6 voices, post‑processed with sox: Dad deep and overdriven; Mom muffled; you slightly low with reverb; Eli pitched up with a low double; Grandma pitched slightly down with a tremble. The mix has 112 cues (including a step every 0.21 s during the run), music gates before each scare, and the score `cue_video014`, which brings back Grandma's music‑box tune from Part 1. The watermark overlay (`ov_watermark`) was added to `edl_engine`.

**QA:** −14.2 LUFS, −1.8 dBTP, no black or frozen frames, no silence or click in the 3× loop, and the audio is within 9 ms of the video. The seam is a deliberate cut (scare → peephole).
**Fixed:**
* A divide‑by‑zero in the street shot stopped the first draw. It was fixed before the video was sent, and every frame was redrawn.
* The peephole eye started closed on frame 0.
* The seal shot was hard to read.
**Weak spots:** the run (about 7 s) and the choice section (about 10 s) are the slowest parts.
