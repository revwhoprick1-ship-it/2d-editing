# Prompt: build an automated short-video studio (3D + 2D), from scratch

Copy everything below into an AI coding agent (e.g. Claude Code) running on a Linux machine or a cloud container.

---

You are my video studio engineer. Build a complete code-driven pipeline that turns a story idea into a finished vertical
short (1080×1920, 30 fps, 30–90 s, H.264/AAC MP4) with **no manual editing**. Everything must be free/open-source and run on
CPU only (no GPU, no paid APIs). Build it in this repo under `STUDIO/`, commit as you go, and keep every step re-runnable
from one command.

## 0. Ground rules
* Free tools only: Blender (3D), Skia/`skia-python` (2D vector), numpy/PIL, ffmpeg, a local open-source TTS
  (e.g. Chatterbox with a reference voice clip), faster-whisper (for checking speech), pyloudnorm/scipy (audio).
  Ask before installing anything paid or using any paid API.
* All music and sound effects are **synthesised by code** (no copyrighted audio). Fonts must be open licence (OFL/Apache).
* Never claim something is tested when it isn't. Report render times and QA results honestly.
* After every export: **send/show me the video first**, then run QA, then fix and re-export.
* All on-screen text must stay inside a safe area (≥36 px margin; shrink to fit, never overflow).
* Default to normal, natural colour (no over-saturated "vibrant" grade unless asked).

## 1. Folder layout
```
STUDIO/
  PIPELINE/
    tts/           narrate.py (script.json -> per-line wavs + narration_raw.wav + word timing.json), voice_qc.py
    audio/         dsp.py, sfx_*.py (procedural SFX library -> AUDIO/sound_effects/*.flac + LIBRARY.json),
                   music_gen.py (procedural score per video), mix.py (cues.json -> mix_master.wav)
    blender_scripts/ studio_lib/ (sets, characters, rigs, lights, cameras, toon shader), videos/videoNNN.py
    twod/          flat.py (2D vector puppets + painting helpers), kit.py (timing, text, perspective camera)
    rendering/     render_shot.py (one Blender job), render_needed.py (render only frames the edit uses)
    editing/       edl_engine.py (compositor: EDL -> finished mp4)
    quality_control/ qc_video.py, loop_test.py
  VIDEOS/VIDEO_NNN/ script.json, edit_videoNNN.py (the EDL), anim2d.py (2D videos), audio/, gfx/, qc/, README.md
  EXPORTS/        final mp4s
  ASSETS/fonts/   open-licence fonts
```

## 2. Narration (local TTS)
* `script.json`: lines with `id`, `who` (narrator / character), `text`, `delivery`, emotion knob, `pause_after`, optional
  per-line `voice_ref`. Generate **N takes per line**, transcribe each with Whisper, keep the take with the fewest word
  mismatches (digits vs words don't count). Short lines hallucinate: rewrite them if they keep failing.
* Output per-line wavs, an assembled `narration_raw.wav`, and `timing.json` with **word-level start/end times** – the
  whole edit (cuts, captions, lip-sync, SFX) is timed from these words.
* Optionally place lines at fixed story times instead of back-to-back (a small `place_lines.py`).

## 3. Sound
* `dsp.py`: noise colours, filters, envelopes, FM bells, Karplus strings, reverb IR + convolution, saturation,
  compressor, true-peak limiter.
* SFX library: every effect is a small function (`@reg(name, description)`) that synthesises audio; a generator writes
  FLACs + `LIBRARY.json`. Add new effects per video as needed (impacts, whooshes, footsteps, doors, ambiences…).
* `music_gen.py`: a `Score` class with buses (pad/bass/lead/perc/fx), simple instruments (pad, strings, pluck, bell,
  bass, stabs, drums, tremolo) and `gate()`; one `cue_videoNNN()` per video that places music on the story beats it
  imports from the EDL. Optional seamless-loop render (tails folded to the start).
* `cues.json` (built by `VIDEOS/.../audio/build_cues.py` from EDL times): every SFX cue with time, gain, bus, note.
* `mix.py`: narration chain + loudness to −16 LUFS, music side-chain ducked under speech, music gates (silences),
  SFX/ambience buses, master to **−14 LUFS integrated, ≤ −1 dBTP**, optional circular mix for loops, stems + stats.

## 4. Picture, mode A: 3D (Blender, CPU EEVEE)
* `studio_lib`: reusable sets, a rigged character generator, extras built from it, lights (only `Key*` lights cast
  shadows), camera rigs with keyframed moves, an optional toon-shader pass.
* `videos/videoNNN.py`: builds the scene, performs characters (expressions, walks, lip-sync from word timing),
  defines cameras and a `JOBS` table (job → camera, time range).
* `render_shot.py`: renders one job at half resolution (540×960), 1 sample + OpenImageDenoise, ray tracing off.
* `render_needed.py`: walks the EDL through the compositor, records every (job, frame) actually shown, and renders only
  those, in parallel lanes, resumable after a crash.
* Always render **test stills of every shot** before the full render and fix framing first.

## 5. Picture, mode B: real 2D animation (Skia vector, much faster)
* `flat.py`: 2D cut-out puppet drawn from vector shapes (flat fill + one cel-shadow tone + optional rim light), with a
  pose dict: eyes/pupils/lids/brows/mouth shapes, talk amount, head tilt and fake 3/4 turn, arms (shoulder + elbow),
  front/back stepping walk, side-view walk/run cycle, crouch, held items, colour/costume parameters for other
  characters. Helpers: gradients, painted glows (additive), vignettes, blobs (smooth shapes).
* `kit.py`: eased keyframe helper, blink, mouth-open from word timing, text drawing, flicker, a **one-point perspective
  camera** (project x/height/depth → screen, scale characters by depth) for rooms and corridors.
* `VIDEOS/.../anim2d.py`: one draw function per shot (`shot_NAME(canvas, t)`), drawn natively at 1080×1920; renders only
  the frames the EDL needs with a multiprocessing pool (~0.05–0.1 s per frame on CPU).

## 6. The edit (`edl_engine.py` + `edit_videoNNN.py`)
* The EDL is a Python module: `SEGMENTS` (time range → source job + time map), `OVERLAYS`, `CAPTIONS`, `AUDIO`,
  `DURATION`. Beat times are computed from the narration words, so re-recorded lines re-time the edit automatically.
* Segment effects (all 2D, so fixes never need a re-render): punch-in zoom keys, shake, white flash, whip pans with
  motion blur, freeze-frame tint, VHS rewind of earlier video time, split screens, pixelate, vignette, hard cut to black.
* Overlays: titles, stamps, chips/pills, counters, timers, lower thirds, a small HUD row (values that change flash),
  choice cards ("comment 1, 2 or 3"), etc. Everything goes through one `paste()` that enforces the safe area.
* Captions from word timing: short phrases (≤4 words, split on punctuation), keyword emphasis, optional speaker labels
  for dialogue, per-time position overrides so captions never cover faces or key props.
* Encode: x264 `slow`, CRF 18, yuv420p, BT.709, AAC 48 kHz, `+faststart`.

## 7. QA (always on the real export)
* `qc_video.py`: resolution/fps/codec, duration, loudness + true peak, black and frozen segments, contact sheet.
* `loop_test.py` (for looping videos): plays it 3× back-to-back; checks black/silence at the seam, clicks, audio gap,
  seam picture change vs normal frame-to-frame motion, A/V length match.
* Visual pass: a contact sheet every 0.5–1 s; look for text out of bounds, captions on faces, unreadable shots,
  characters off-frame, pops/teleports. Fix, re-export, re-check. Write `README.md` + a render/QA report per video
  (render time estimated vs actual, what was fixed, known weak spots).

## 8. Per-video workflow
1. Story: 2–3 concepts, pick one; beat sheet; score 3 hooks (event on frame 0 beats a question); plan the loop
   (last frame flows into frame 0) and any engagement prompts as part of the story, not on top of the hook.
2. `script.json` → narration + word timing (QC every word).
3. Build shots (3D or 2D) → test stills of every shot → fix framing.
4. EDL → SFX cues → music cue → mix.
5. Render only needed frames → export → **show the video** → QA → fix → final export → docs → commit.

Start by scaffolding the folders and `dsp.py`, `flat.py`, `kit.py`, `edl_engine.py`, `mix.py` and the QC scripts, then make
a 10-second test video in 2D mode end-to-end (one character, one room, two lines of narration) to prove the pipeline.
