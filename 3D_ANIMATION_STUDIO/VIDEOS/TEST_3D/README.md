# TEST_3D — hybrid style test (3D world + flat 2D character), 10 s

1. `blender -b --factory-startup --python scene3d.py -- --frames 0,299 --res 720x1280 --samples 8 --bg 1`
   -> `frames3d/BG/####.png` (3D hallway only, toon ramp + ink hull, DOF) and `track.json` (feet/head/handle on screen + px per metre).
   (without `--bg` it renders the fully 3D toon mascot too — the first try; the user wants the flat 2D characters.)
2. `python3 comp2d.py` -> `frames2d/ALL/####.png` (1080x1920): the flat mascot puppet (`PIPELINE/twod/flat.py`) drawn at the tracked
   spot/scale, back view in shot A, face close-up in B, over-the-shoulder hand + keys to the keyhole in C.
3. Audio: narration reused from TEST_STYLE (Qwen), `audio/cues.json` -> `/opt/tools/cbx/bin/python PIPELINE/audio/mix.py`.
4. `python3 PIPELINE/editing/edl_engine.py VIDEOS/TEST_3D/edit_test3d.py --frames VIDEOS/TEST_3D/frames2d --out EXPORTS/TEST_3D_Hybrid.mp4 --audio VIDEOS/TEST_3D/audio/mix_master.wav`
Shots: A 0-4.2 s dolly down the hall to you at the basement door; B 4.2-7.2 s face close-up, eyes slide, head snaps;
C 7.2-10 s over the shoulder, key to the keyhole, the handle turns by itself from the other side.
