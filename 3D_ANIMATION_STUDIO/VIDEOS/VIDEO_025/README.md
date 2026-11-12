# VIDEO_025 — The World Ends In 60 Seconds (hybrid: 3D world + flat 2D characters, choose game)

60.0 s, 1080x1920, 30 fps. The HUD clock is REAL TIME: 1:00 at frame 0 -> 0:00 at the white-out, which loops into frame 0.

## Story (standalone, forward only)
11:59 PM, every phone on Earth: "The world ends in sixty seconds." The sky cracks like glass. YOU (orange shirt) is three
blocks from home; little sister MIA (7, yellow shirt, teddy bear) is home alone. Run: a burning car falls, a piece of sky hits
the sidewalk, gravity blinks (everything floats, then slams), a car drops from the sky (jump scare). MOM calls (night shift):
"Don't let go of her hand. Promise me." "I promise." Call fails. White beams come down from the crack, searching (one stops
on you for a moment, moves on). Home: Mia under the table — "I knew you'd come." Side hug. The roof is torn off.
Alert: "Selection complete. One human will be kept." -> KEPT: YOU. The beam locks on you, you float up, Mia holds your hand:
"It picked you... It's okay. Go." "Not without you!" "Does it hurt... when the world ends?" "The light only takes one."
"I could go. I could give it to her. Or I could stay." Choice (3 s): 1 GO (leave Mia) · 2 GIVE MIA YOUR PLACE · 3 STAY, NEVER LET GO.

## Lore (never contradict)
- The crack opened at 11:59 PM. Exactly 60 s. The beams ("the light") scan every human and keep ONE. It can take only one.
- It chose YOU. The light can be handed over (option 2) — that is why it lets Mia hold on.
- Mom works nights, calls from far away; her last words: "Don't let go of her hand." (option 3 keeps the promise literally,
  option 2 keeps it in spirit).
- Hidden details: frame 0 — a faint beam is already on you (it picked you before the alert); the phone's tiny line
  "Selection in progress... 8,118,000,004 scanned"; at 25.8 s one beam stops on you and moves on; the wall clock reads 11:59.

## Pipeline (FAST hybrid, cloud CPU)
1. `blender -b --factory-startup --python VIDEOS/VIDEO_025/sets3d.py -- --samples 12` -> 12 overscanned plates + plates.json (~6 min).
2. Qwen3-TTS (local): `narrate_qwen.py script.json audio/narration` (refs: N/A from VIDEO_024, M/P from VIDEO_021, S = new child voice).
3. `python3 audio/voice_fx.py` (alert = robotic PA, Mom = phone) -> `place_lines.py` (absolute starts from timeline.py).
4. `python3 anim.py` -> frames2d/ALL/*.jpg (2D: sky directions, beams, puppets, props, FX, inserts).
5. `audio_synth.py` (world SFX) -> `music_gen.py video025` -> `audio/build_cues.py` -> `mix.py audio/cues.json`.
6. `python3 PIPELINE/editing/edl_engine.py VIDEOS/VIDEO_025/edit_video025.py --frames VIDEOS/VIDEO_025/frames2d --out EXPORTS/VIDEO_025_The_World_Ends_In_60_Seconds.mp4 --audio VIDEOS/VIDEO_025/audio/mix_master.wav`

## Title
The World Ends In 60 Seconds. Who Do You Save?

## Description
11:59 PM. Every phone on Earth says the same thing: the world ends in 60 seconds.
You run home to your little sister... and then the light picks YOU. Only one human will be kept.

1️⃣ GO — leave Mia behind
2️⃣ GIVE MIA YOUR PLACE
3️⃣ STAY — never let go

What do you choose? Comment 1, 2 or 3 👇
👀 The answer was decided at 0:00. Rewatch the first second.
Follow @insidethemindlessvault for more choose-your-ending stories.

#choosegame #whatwouldyoudo #endoftheworld #animation #2danimation #horrorstory #storytime #sad #shorts #reels

## Pinned comment
You had 3 seconds. 1, 2 or 3? 👇
Hint: rewatch the very first second. The light was already on you before the alert went off. 👀
