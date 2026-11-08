# VIDEO_011 — Benched · Part 1 (2dEDIT, real 2D, sports drama)

61.8 s · 1080×1920 · 30 fps · `EXPORTS/VIDEO_011_Benched_Part_1.mp4`

**Hook (in medias res):** frame 0 is the scoreboard: HOME 58 – AWAY 60, 0:03, Q4. The timeout buzzer sounds on frame 0, and the voice says "Three seconds left in the championship. Down by two." Next comes "And the best player in this gym is sitting on the bench." over you at the end of the bench, towel on your shoulders, next to the water bottles. Then a close‑up on #23 for "That's you." and the title `BENCHED / PART 1`. The HUD reads `YOUR MINUTES: 0`.

**Story (flashback in a warm, faded grade):**
* Tryouts: old brown shoes and a baggy grey #00 jersey. Tyler (#1): "Nice shoes. Did your grandpa lend you those?" The team laughs; Coach laughs loudest: "Kid, you're here to fill water bottles."
* Every night in the empty gym, under one light, you shoot. A counter climbs from SHOT 1 to 500. Left hand, right hand, eyes closed.
* The janitor sees 20 threes in a row and presses record. The video now has 2,104,388 views, with comments like "WHO IS #23??", "coach is blind fr" and "START HIM."
* Everyone has seen it... except Coach, who has his head in his clipboard while the crowd behind him watches on their phones.
* Back to the final. Tyler: "Stay on the bench, water boy." Then **Tyler fouls out** (whistle, towel over his head). The crowd stands and chants **23** (stomp‑stomp‑clap, signs).
* Coach turns around: **"You. Get in."** The music swells and HUD minutes → IN. You walk onto the court into a spotlight and catch the inbound pass.

**Ending:** the scoreboard again, with a choice card ("3 SECONDS. YOUR CALL."): 1 take the three for the win · 2 drive in for the tie · 3 pass it. TOP COMMENT = PART 2. This leads back to frame 0.

**Made with:** `anim2d.py` (12 shots, 1,869 frames). The puppet gained a jersey number, shorts and a sleeveless option, and a raised arm in side view now draws in front of the head with an outline. 19 Chatterbox lines with 3 voices: narrator am_fenrir, Tyler am_adam, Coach am_onyx. 7 new SFX (arena crowd, "23" chant, ref whistle, buzzer, bounce, swish, sneaker squeak), 68 cues, and the score `cue_video011` (heartbeat hook, piano flashback, building practice beat, chant, a swell on "Get in").

**QA:** −14.2 LUFS, −1.0 dBTP, no black/frozen frames; loop test passes every check.
Fixed after the first export: the towel covered your face on the bench; the shooting arms were hidden in front of the face (same skin colour); the choice card covered the score.
**Weak spots:** the chibi proportions make the jump shot read as "arm across the face" rather than a full release; the crowd is simple dots and signs.
