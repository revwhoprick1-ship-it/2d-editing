# VIDEO_008 — Last Bus · Part 1 (2dEDIT, real 2D)

57.9 s · 1080×1920 · 30 fps · `EXPORTS/VIDEO_008_Last_Bus_Part_1.mp4`

**Hook:** frame 0 is a full night bus: 14 passengers with phones glowing, and you in the front seat. The voice starts on frame 0: "You blinked." Then comes a 3-frame black blink, and every seat is empty except yours. The HUD flips `PASSENGERS 14 → 1` in red. Title: `LAST BUS / PART 1`.

**Story:**
* The left-behind phones are still lit and a coffee is still steaming.
* One phone is still recording. You press play: it is one minute ago, everyone is there, and then they all turn and look at you at the same time. VIDEO ENDED.
* "Driver! Where did everyone go?" He never turns around (deep Kokoro am_onyx timbre): "They got off at their stop." "We haven't stopped once!"
* The route screen reads **NEXT STOP: YOU**.
* Fog fills the windows, and in it stand every passenger, perfectly still, waving goodbye.
* You slam the stop button. "Not yet. You still have a ticket." The ticket is in your hand: **ONE WAY**.
* The rear‑view mirror shows the driver, and he **has no face**.
* The brakes squeal and your stop is coming.

**Ending:** a choice card asks WHAT DO YOU DO? 1 pull the emergency handle · 2 smash the window · 3 sit back down. Then the lights flicker and **every passenger is back, staring at you** (HUD `PASSENGERS 15`). That cuts to frame 0, the full bus, so the loop has its own twist.

**Made with:** `anim2d.py` (11 shots, 1,750 frames, about 1.5 min of CPU drawing). 19 Chatterbox lines (narrator am_fenrir, you am_puck, driver am_onyx), and every word passed the Whisper check. 7 new bus SFX (engine, brakes, stop bell, blink, phone tap, mass head‑turn, glass taps), 28 cues, and a score cue (`cue_video008`).

**QA:** −14.2 LUFS, −1.0 dBTP, no frozen frames. Black segment: the 0.1 s blink, by design. The loop seam is a deliberate picture change: from everyone staring to the normal full bus.
Fixed after the first look: passengers sat too low to show over the seats (camera raised, adult proportions), you were hidden behind another passenger in the hook, the faceless head was cut off in the mirror, and the route text was too wide.
Weak spots: the faces in the fog are small; the mirror shot is a small part of the frame.
