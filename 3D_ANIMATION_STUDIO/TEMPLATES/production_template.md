# VIDEO_XXX — Production Checklist (copy into VIDEOS/VIDEO_XXX/)

## 0. Brief
- Title / concept:
- Target length: 45–60 s · Mascot role:
- Required facts (with sources) → `01_research_and_references.md`

## 1. Story development (do not skip)
- [ ] 3 distinct concepts (hook, conflict, discoveries, escalation, payoff) → `02_story_concepts_and_comparison.md`
- [ ] Score each concept on the 8 criteria and pick one with a written reason
- [ ] Draft v1 → `03_script_draft_v1.md`
- [ ] Critical review as a hostile viewer → `04_script_review_v1.md`
- [ ] Revised script + change log + second review → `05_script_final.md`
- [ ] ≥4 hook candidates scored on clarity, curiosity, novelty, emotion, visual, relevance → `06_hook_engineering.md`

## 2. Pre‑production
- [ ] `script.json` (lines, delivery, speed, pauses, pronunciations)
- [ ] Narration: `PIPELINE/tts/narrate.py` → `PIPELINE/tts/qc_narration.py`. All lines WER = 0; fix and regenerate until clean.
- [ ] Storyboard with frame ranges from the narration timing → `07_storyboard.md`
- [ ] Video module `PIPELINE/blender_scripts/videos/videoXXX.py` with SHOTS + one `shot_*` function per shot
- [ ] Pre‑render reviews: viewer / science / production → `09_pre_render_reviews.md`

## 3. Production
- [ ] Animatic preview: `render_video.sh videoXXX 270x480 2 3 VIDEOS/VIDEO_XXX/preview/frames`, then `assemble.py --frames-root …/preview/frames`
- [ ] Watch the preview against the narration; list fixes; re‑preview the shots you changed
- [ ] Music cue → `PIPELINE/audio/music_gen.py` (add a `cue_videoXXX`)
- [ ] SFX cue list → `audio/cues.json`, then `PIPELINE/audio/cue_sheet_md.py` → `08_audio_cue_sheet.md`
- [ ] Mix: `PIPELINE/audio/mix.py audio/cues.json`, then check `mix_stats.json`
- [ ] Final render (540×960 @6 samples on CPU, native 1080×1920 on GPU), 2 parallel workers

## 4. QA + delivery
- [ ] `assemble.py` → `EXPORTS/VIDEO_XXX_final.mp4`
- [ ] `PIPELINE/quality_control/qc_video.py` → LOOK at `contact_*.png`, confirm every check passes
- [ ] QA report and final production report → `10_QA_and_production_report.md`
