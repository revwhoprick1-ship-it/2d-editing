# VIDEO_026 — "Two Bobs" (56.0 s, 1,680 frames @ 30 fps, 1080x1920) — STATE

Title: My Best Friend Just Texted Me "Don't Open The Door"… While Sitting Next To Me
Style: 2dEDIT (real flat 2D, Skia). Channel: @insidethemindlessvault. Voices: local Qwen3-TTS only.

## Where the user's `studio/` files live in this repo
| Blueprint name | Here |
|---|---|
| `studio/puppets.py`, `compositor.py`, `renderer.py`, `voice_engine.py`, `audio_synth.py`, `qa_inspector.py` | `VIDEOS/VIDEO_026/studio/` (+ `timeline.py`, `sets.py`, `sound_mix.py`) |
| `script.json`, `STATE.md` | `VIDEOS/VIDEO_026/` |
| `exports/two_bobs_mimic.mp4` | `EXPORTS/VIDEO_026_two_bobs_mimic.mp4` |

## Steps
- [x] 0. VIEWER_MODE_AGENT audit + upgrades (VIEWER_AUDIT.md) — simulated score 8.2 -> 9.4
- [x] 1. script.json + timeline.py + STATE.md committed
- [ ] 2. voices: `python3 studio/voice_engine.py tts` -> `fx` -> `place`
- [ ] 3. sound: `studio/audio_synth.py` -> music cue `video026` -> `studio/sound_mix.py` -> `PIPELINE/audio/mix.py`
- [ ] 4. frames: `python3 studio/renderer.py` (Pool(4), JPG) -> `frames2d/ALL`
- [ ] 5. edit: `PIPELINE/editing/edl_engine.py studio/compositor.py` -> EXPORTS
- [ ] 6. send video, then `studio/qa_inspector.py`, fix, re-render
- [ ] 7. title / description / pinned comment / verdict report (README.md)

## Deviations from the blueprint (and why)
- Hook text unified to the TITLE: banner + narrator both say "Don't open the door" (blueprint had 3 different texts).
- Lines shortened where real speech cannot fit the slot (e.g. 10 words in 1.07 s before the 15.67 s snap). Scares stay on their frames.
- Shot 3B starts at frame 417 (not 435) so "His lips don't move" is heard while his lips are on screen.
- TV twist re-ordered so a DELAYED feed is logical: feed shows it climb over the couch -> "5-second delay" -> real couch is empty.
- The TV is already on at the start (its flicker lights the couch), so at 27.0 s it "switches itself" to the security feed.
- The ankle grab is not dropped: the camera is tugged down while it rises (no tension reset).
- 50.5 s: the door kick is SHOWN (whip to the hallway) instead of only told.
