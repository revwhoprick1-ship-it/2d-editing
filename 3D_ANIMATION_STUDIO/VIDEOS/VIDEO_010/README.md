# VIDEO_010 — Last Bus · Part 2 (2dEDIT, real 2D)

52.7 s · 1080×1920 · 30 fps · `EXPORTS/VIDEO_010_Last_Bus_Part_2.mp4`

The audience chose **2 · SMASH THE WINDOW**. The top comment, by @ZylaxVShark (6 likes), is shown on screen in the reference's "TOP COMMENT" card, under a red `YOU CHOSE 2 · SMASH THE WINDOW` pill.

**Hook:** frame 0 shows the fogged window with the faces outside, your hand raising the red emergency hammer, and the comment card. The voice starts on frame 0: "You chose the window." One swing, the glass cracks, then it **explodes** (flash, shake, flying shards) and the fog pours in.

**Story:**
* The faceless driver, in the mirror: "That's not an exit."
* You climb through and drop onto the road. The bus doesn't stop; its tail lights fade into the fog.
* The passengers stand in the road. **They've stopped waving.** Every head tilts at the same time, and then they walk toward you.
* You run (side‑scroll, with shapes keeping pace behind you) to a bus stop: ROUTE 13. On the glass is a **MISSING poster with your face** on it.
* Your phone: 47 missed calls from Mom, and "please come home". The date flips to **NOV 8, 2027**: one year from tonight. The HUD reads `1 YEAR LATER`.
* Headlights in the fog. The doors fold open, and the faceless driver says "You missed your stop."
* Inside, every passenger is back, waving, and **someone in your seat is wearing your face** (a smirking copy of you). The camera snaps in with a flash.

**Ending:** a choice card: 1 get back on the bus · 2 run into the fog · 3 call Mom back, with "TOP COMMENT = PART 3". Then a cut back to the intact window, so the video loops.

**Made with:** `anim2d.py` (9 shots, 1,590 frames). It reuses the bus, passengers and driver from VIDEO_008. The new `ov_comment` overlay in `edl_engine` draws the comment card. 18 Chatterbox lines (narrator am_fenrir, driver am_onyx); every word passed the Whisper check (only digits differ). 45 cues and the score `cue_video010`.

**QA:** −14.2 LUFS, −0.9 dBTP, no black or frozen frames, no silence or click in the 3× loop. Audio and video lengths match within 16 ms. The seam is a deliberate cut, from the choice card back to the window.
**Weak spots:** at the bus stop, the "ROUTE 13" sign slides under the HUD during the push‑in; on the phone, a caption briefly overlaps the message bubble.
