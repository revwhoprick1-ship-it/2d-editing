# How to make the next video (VIDEO_002+)

1. **Copy the checklist:** `cp TEMPLATES/production_template.md VIDEOS/VIDEO_002/00_checklist.md` and follow it top to bottom.
2. **Research:** list every fact with a credible source (NIH/NLM, MedlinePlus, Cleveland Clinic, OpenStax, university sites). Remove anything you can't source.
3. **Story:** write 3 concepts, score them, draft, write a hostile review, revise, compare hooks. Use files 02–06 of VIDEO_001 as the model.
4. **script.json:** one line per beat with a delivery preset. Generate and QC the narration, iterating until every line has WER = 0. Timing comes from `timing.json`.
5. **Video module:** copy `PIPELINE/blender_scripts/videos/video001.py` to `video002.py`. Keep the helpers (`mascot()`, `place_rig`, `pose_sit`, `expr_key`, `lights_rig`, `pulse`) and write new `set_*` environments and `shot_*` functions. Shot frame ranges come from the narration timing (frame = seconds × 30, plus the narration offset).
   * New environments: add reusable builders to `studio_lib/` (e.g. `city_assets.py`), following `bio_assets.py` (procedural meshes + PBR materials + fog).
   * The mascot always comes from `scene_kit.append_mascot()`. Use the `Mascot` API for every pose, expression and blink.
6. **Preview animatic** (270×480, 2 samples, every 3rd frame), assemble with the narration, **watch it** (or inspect contact sheets), fix, re‑preview the changed shots.
7. **Music:** add `cue_video002()` to `music_gen.py` (sections follow the story acts; include one silence beat before the main reveal).
8. **SFX:** write `audio/cues.json` (every cue tied to a frame/event), run `cue_sheet_md.py`, run `mix.py`, and check `mix_stats.json` (−14 LUFS, ≤ −1 dBTP, 0 clipped).
9. **Final render:** two `render_video.sh` workers splitting the shot list. Frames already rendered are skipped, so you can resume after interruptions.
10. **Assemble + QA:** `assemble.py` → `qc_video.py`. Look at the contact sheets, then write the QA and production report.

## Adding a new expression or animation
* Expression: add an entry to `EXPRESSIONS` in `mascot_api.py` (brow mm, lid degrees, jaw degrees, shape‑key weights, head, eyes) and rebuild the rig to refresh `expressions.json` and the `EXP_*` actions.
* Motion: write a generator in `mascot_api.py` (see `walk`, `jump`, `wave`). Generators key frames, so they adapt to any timing.

## Character dialogue (lip sync)
Generate the line with `narrate.py` using the mascot's voice (`am_puck`). Then `lipsync(m, timing['words'], offset_frames=…)` keys jaw and mouth shapes from Kokoro's phonemes (see `PIPELINE/blender_scripts/anim_test.py`).
