# VIDEO_016 · The Forest That Eats People (2dEDIT horror, 2:31)

Export: `EXPORTS/VIDEO_016_The_Forest_That_Eats_People.mp4` (1080x1920, 30 fps, -14.1 LUFS, TP -2.0).

**Voices:** Qwen3-TTS only (Apache-2.0, local CPU). `PIPELINE/tts/narrate_qwen.py`: VoiceDesign makes one reference per
character (`audio/narration/ref_*.wav`), Base clones every line from it. Copied voices (X lines) = the copied character's
voice + sox FX (`audio/voice_fx.py`). Then `audio/place_lines.py` adds the action gaps.

**Pipeline:** `anim2d.py` (4359 frames) -> `edit_video016.py` EDL -> `audio/build_cues.py` (58 cues, new forest SFX) +
`cue_video016` music -> `mix.py` -> `edl_engine.py`.

**QA:** all format/loudness checks pass. Black on purpose: hook cut before the whisper (3.2-5.0 s), lights out
(111-112.6 s), 1.4 s silent ending. Known weak spot: in the side-door exit shot the runners' heads go off the top.
