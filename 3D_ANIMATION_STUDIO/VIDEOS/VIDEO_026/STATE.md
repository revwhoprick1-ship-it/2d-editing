# VIDEO_026 — "Two Bobs" (56.0 s, 1,680 frames @ 30 fps, 1080x1920) — STATE

Title: My Best Friend Just Texted Me "Don't Open The Door"… While Sitting Next To Me
Style: 2dEDIT (real flat 2D, Skia). Channel: @insidethemindlessvault. Voices: local Qwen3-TTS only.

## Where the user's `studio/` files live in this repo
| Blueprint name | Here |
|---|---|
| `studio/puppets.py`, `compositor.py`, `renderer.py`, `voice_engine.py`, `audio_synth.py`, `qa_inspector.py` | `VIDEOS/VIDEO_026/studio/` (+ `timeline.py`, `sets.py`, `sound_mix.py`) |
| `script.json`, `STATE.md` | `VIDEOS/VIDEO_026/` |
| `exports/two_bobs_mimic.mp4` | `EXPORTS/VIDEO_026_two_bobs_mimic.mp4` |

## Steps (all done)
- [x] 0. VIEWER_MODE_AGENT audit + upgrades (VIEWER_AUDIT.md) — simulated score 8.2 -> 9.4
- [x] 1. script.json + timeline.py + STATE.md committed
- [x] 2. voices: `voice_engine.py tts` -> `squeeze` -> `fx` -> `place` (22 lines, 0 word misses)
- [x] 3. sound: `audio_synth.py` (15 new SFX) -> music cue `video026` -> `sound_mix.py` (73 cues) -> `mix.py`
- [x] 4. frames: `renderer.py` (1,680 frames, ~4 min)
- [x] 5. edit: `compositor.py` -> EXPORTS/VIDEO_026_two_bobs_mimic.mp4
- [x] 6. video sent first, then `qa_inspector.py` -> fixes -> re-render (qc/qa_report.txt: all PASS)
- [x] 7. title / description / pinned comment (README.md), lore (VIDEOS/TWO_BOBS_LORE.md)

## Deviations from the blueprint (and why)
- Hook text unified to the TITLE: banner + narrator both say "Don't open the door" (blueprint had 3 different texts).
- Lines shortened where real speech cannot fit the slot (e.g. 10 words in 1.07 s before the 15.67 s snap). Scares stay on their frames.
- Shot 3B starts at frame 417 (not 435) so "His lips don't move" is heard while his lips are on screen.
- TV twist re-ordered so a DELAYED feed is logical: feed shows it climb over the couch -> "5-second delay" -> real couch is empty.
- The TV is already on at the start (its flicker lights the couch), so at 27.0 s it "switches itself" to the security feed.
- The ankle grab is not dropped: the camera is tugged down while it rises (no tension reset).
- 50.5 s: the door kick is SHOWN (whip to the hallway) instead of only told.
- The narrator reads slowly: 23 blueprint-style lines were 61 s of speech for a 56 s video. Inner pauses are squeezed (words untouched),
  the hook is ONE sentence (= the title), three lines trimmed, CTA = "Smash, hide, or run? Comment now."
- The two mid-word hits land 0.30 s into "does" / "splits" (at 0.14 s Whisper could no longer hear the word).
- Frame-0 slam is 3 dB lower and the noise beds fade in over 0.5 s: with both at full level AAC overshot to -1.2 dBTP.
