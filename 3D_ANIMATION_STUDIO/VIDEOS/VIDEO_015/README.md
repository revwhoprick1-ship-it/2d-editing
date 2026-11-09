# VIDEO_015 — Kessrah · Part 1 (2dEDIT, real 2D psychological horror, dialogue-driven)

87.7 s · 1080×1920 · 30 fps · `EXPORTS/VIDEO_015_Kessrah_Part_1.mp4` · watermark `@insidethemindlessvault`. **Lore bible:** `VIDEOS/KESSRAH_LORE.md`.

**Hook:** on frame 0 the whole class has turned round in their seats, staring at you with one wide smile. Your shaking whisper starts on frame 0: "Okay... why is everyone looking at me?" The class answers in unison (5 voices): "Because you called him." A VHS rewind follows, then **12 HOURS EARLIER**.

**Story:**
* 3:33 AM, salt circle, three candles. The phone video shows the rules.
* You say "Kessrah" three times, getting more scared each time. All three candles go out at once. "Nothing happened. I'm going to bed." Something blinks in the corner.
* At school, Theo: "You said it three times? Out loud? You're not supposed to finish it... He doesn't come when you call him. He comes when you blink."
* Ms. Hart takes attendance: "Theo. Maya. And... Kessrah."
* You blink once (real POV eyelids) → **JS1**: the whole class staring. "We've been waiting for you to blink." You: "Stop looking at me! This isn't funny!" Ms. Hart, wrong: "Kessrah is taking attendance now."
* You rub your eyes, and the class is **empty**. The chalk writes by itself: **YOU CALLED. I CAME. DON'T BLINK.** You: "I'm still dreaming. Wake up!"
* From the back, in your own voice: "You're not dreaming. You're mine." Kessrah stands up → **JS2**: every eyelid on its face opens.
* Your eye, watering and veined: "Please, I don't want to blink."

**Choice:** 1 run for the door · 2 keep your eyes open · 3 say his name backwards. Your blinks come faster and faster, and Kessrah is a row closer after each one. The HUD counts **BLINKS**. Last blink → **JS3**, then a cut to frame 0.

**Voices (free, local):** Chatterbox with emotion pushed high for you (exaggeration 0.9–1.4, low cfg) plus a sox tremolo shake, and a panicked breath sound placed before every scared line.
* Theo is am_liam; Ms. Hart is af_sarah (her "wrong" line is pitched down).
* The class is the line in 5 voices mixed together (am_adam, am_eric, af_kore, am_michael, af_bella).
* Kessrah is am_onyx pitched down and mixed with **your own voice** (am_puck), plus overdrive and reverb.
* All 29 lines passed the Whisper check. "Kessrah" is heard as "kessra"; that's a spelling difference, not a wrong word.

**Made with:** `anim2d.py` (19 shots, about 2,800 frames). There is a new Kessrah puppet (a face made of eyelids that open) and a new POV eyelid blink overlay `ov_blink` in `edl_engine`. 47 cues and the score `cue_video015`; the music is gated before each scare.

**QA:** −14.2 LUFS, −2.0 dBTP, no silence or click in the 3× loop, audio 11 ms off video.
* Black on purpose: the eye‑rub (51.5–52.5 s) and the final blink. The loop seam is a deliberate cut.
* Fixed after the first export: a 3 s nearly‑black corner shot (now moonlit, with a shape and eyes); a 9 s static ritual shot (now split with the phone's ritual instructions); Kessrah's head out of frame in JS2, the creep and JS3; a crash in the blink overlay.
