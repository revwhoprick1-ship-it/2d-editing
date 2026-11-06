# VIDEO_001 — QA & Final Production Report

> Final file: `EXPORTS/VIDEO_001_What_If_You_Were_Shrunk.mp4`. Evidence: `qc/qc_report.json`, `qc/contact_*.png`, `audio/mix_stats.json`, `audio/narration/qc_report.json`.

## 1. Title
**What If You Were Shrunk Inside Your Own Body?**

## 2. Concept
The studio mascot wakes up shrunk smaller than a blood cell and rides one red blood cell along a real circulation route: vein, right heart (valves "lub‑dub"), lung capillary (O₂ in, CO₂ out). There a neutrophil treats him as an intruder and starts to engulf him. He kicks free, losing a sneaker, and the left ventricle launches him into the aorta. Final callback: a white blood cell somewhere in his lungs is still trying to digest the shoe.

## 3. Hook used
*"You've been shrunk smaller than a blood cell… and your own body is about to attack you."* Over an ECU of the mascot's eyes snapping open, then a pull‑back reveal of the blood‑cell tunnel with a pale shape gliding past.

## 4. Why this hook
It scored highest of 5 candidates (27/30, see `06_hook_engineering.md`). It states the premise and a specific ironic threat in one sentence. That opens a concrete information gap ("why would *my* body attack *me*?"), following Loewenstein's (1994) information‑gap account of curiosity, and the second person supports narrative transportation (Green & Brock 2000). The first visual (the mascot's face, then the cell tunnel) illustrates the line word for word. No logo, no intro.

## 5. Narrator & voice settings
Kokoro‑82M (local, Apache‑2.0), voice **af_heart**. 12 lines generated separately with delivery presets (speed 0.88–1.08, scripted pauses 0.15–0.8 s). Two lines rewritten after ASR QC ("riding"→"under you"; "valves slam"→"the valves behind you slam shut"). Final WER 0.00 on all lines; 56.5 s narration; 2.3–3.9 words/s. Narration chain: HPF 80 Hz, −2 dB @ 280 Hz, +2.5 dB @ 3.2 kHz, +1.5 dB @ 10 kHz, de‑esser, 3:1 compressor, light saturation, −16 LUFS.

## 6. Animation & environment techniques
* Mascot: procedural sculpted model + custom rig (`DOCUMENTATION/RIG_GUIDE.md`). Shots use library expressions blended per beat, blinks, eye targets, IK feet, procedural gestures (pats, grips, point, flinch on heartbeats, backing away, kick with anticipation, flailing, superman flight, foot lift).
* Environments (all procedural, `studio_lib/bio_assets.py`): vein and aorta tunnels with Voronoi endothelium; **Evans–Fung biconcave RBCs** (~260–420 per shot) with a parabolic flow profile and tumbling; capillary RBCs as "parachute" cups; ventricle interior with trabeculae, chordae and 3‑cusp valves animated open/shut; stylised anatomical heart (metaballs + great vessels + coronaries); alveolus cluster; O₂/CO₂ diffusion particles; neutrophil with ruffled translucent membrane, lobed nucleus, granules, animated undulation and pseudopods.
* Look: EEVEE, AgX Punchy, SSS on skin and tissue, coat for wet biology, material‑level distance fog, DOF on close‑ups, camera shake keyed to impacts, wall pulses keyed to heartbeats.

## 7. Music
Original score composed for this video (`PIPELINE/audio/music_gen.py`, `cue_video001`) in 8 sections that follow the story acts. Includes a stop‑time on the valve slam, a drop to near silence before the reveal, and a downbeat hit on the aortic launch. Owned by the studio; safe for monetisation.

## 8. Sound effects
72 cues from the studio's original SFX library: vein/capillary ambience beds, heartbeat motif (muffled → close → exterior → flinch beats), valve slam + sub impact, squelches, O₂ sparkles, creature presence, dramatic hit, engulf gloop, footsteps, kick, pop (shoe), whooshes, launch impacts, bubble "gulp" and comedic boing. Every cue is tied to a frame (`08_audio_cue_sheet.md`).

## 9. Duration
**57.0 s** (narration 0.2–55.9 s, music button 55.95 s)

## 10. Resolution & FPS
1080×1920, 30 fps, H.264 High, yuv420p, BT.709, AAC 320 kb/s 48 kHz. Rendered at 540×960 (EEVEE, 4 samples), denoised and upscaled. See the HARDWARE doc.

## 11. Production problems encountered (and fixes)
| Problem | Fix |
|---|---|
| YouTube blocked video download (403, then bot check) | Analysed only legitimately obtained material and documented the gap. The MP4s are needed for full analysis. |
| Mascot image never arrived | Built from the written description, with all identity parameters in one config file for recalibration. |
| New shape keys default to 1.0 in Blender 5 → RBCs rendered as cups/domes and swallowed the mascot | Explicitly zeroed new keys (RBC and face). Found in the animatic. |
| Ears built at the world origin (stale matrix) | `view_layer.update()` before applying transforms |
| Lying pose clipped his head into the cell rim ("bald" in the preview) | Hook redesigned as a slumped‑asleep sitting pose |
| Sleeves sheared at the shoulders | Procedural sleeve weights (armhole → hem blend) |
| Cameras behind the mascot or outside the opaque capillary | Recomputed camera placements after the animatic review |
| Render speed (no GPU): 25–48 s/frame per lane | Key‑only shadows, Simplify, see‑through panel instead of a transparent tube, 4 samples + hqdn3d, 2 lanes |
| TTS mispronunciation risks | ASR QC loop; 2 lines rewritten |

## 12. Quality‑assurance results
**Automated checks on the exported file (ffprobe + ffmpeg EBU R128):**
| Check | Result |
|---|---|
| Resolution / aspect | 1080×1920, 9:16 ✅ |
| Frame rate | 30/1 ✅ (1710 frames, every frame rendered, 0 filled) |
| Video | H.264 High, yuv420p, BT.709 tags, ~11.2 Mb/s (CRF 20, preset slow) ✅ |
| Audio | AAC 320 kb/s, 48 kHz stereo ✅ |
| Integrated loudness | **−14.0 LUFS** (target −14 to −16) ✅ |
| True peak | **−1.1 dBTP** (target ≤ −1) ✅ |
| Loudness range | 2.3 LU (dense, Shorts‑appropriate) |
| Clipped samples (mix) | 0 ✅ |
| Black segments / frozen segments | none / none ✅ |
| Narration ASR | 12/12 lines WER = 0 after 2 rewrites ✅ |

**Mix balance (from `mix_stats.json`):** narration normalised to −16 LUFS before the master gain. Music sits about 13 dB under the master (≈ −27 LUFS) and is ducked 9 dB under speech. SFX ≈ −20 LUFS, ambience ≈ −38 LUFS (bed level).

**Visual inspection (actually looked at):** the animatic contact sheet (start, middle and end of every shot), 40+ final frames during the render, the final export's start/middle/end frames and the in/mid/out frame of all 20 shots (`qc/contact_shots.png`). Problems found and fixed **in the final render** after this inspection:
1. SH05b: lids drifted half‑closed before each heartbeat flinch, so the face read as sleepy. Re‑keyed (eyes held wide, squeeze on the beat) and re‑rendered.
2. SH12b: a red cell sat in front of the lens for ~1.5 s, and the white sneaker vanished against an over‑lit membrane. Cell removed, lights lowered, re‑rendered. The gag now reads.
3. SH11b: the last 0.4 s flew out of the chamber into black. Path shortened and re‑rendered.

**Sync:** captions come from the same Kokoro word timestamps as the narration (+0.2 s offset), so caption timing is sample‑accurate. Every SFX cue is placed at the frame of its animation event (valve slam f491, lub‑dub f540, grab f1238, kick f1310, launch f1434…). The narrator is off‑screen, so no lip sync is needed in this video. The phoneme lip‑sync system is demonstrated in `CHARACTER/mascot_animation_test.mp4`.

**Known remaining issues (honest list):**
* Rendered at 540×960 and upscaled. Fine detail is softer than a native 1080 render (hardware limit, see the HARDWARE doc).
* Under the red interior lighting the jeans read lavender‑grey rather than denim blue.
* Shoulder/sleeve deformation leaves small skin gaps in some poses. The shirt hem and jeans clip in a deep crouch (visible in the animation test).
* SH10 ends on an out‑of‑focus cell crossing the lens, and SH11b's flight passes very close to the valve cusps. Both are brief (≤ 0.3 s) "whip" moments, not errors, but not elegant.
* The neutrophil reads as a pale granular ball. It could be bigger in frame and more menacing.
* Frame 0 shows the top of his slumped head. His face (eyes opening) appears at 0.33 s.
* Narration naturalness and the final mix were verified by measurement and ASR, **not by human listening**.

## 13. What to improve next time
1. **Render natively at 1080×1920** (any CUDA/OptiX GPU or a cloud GPU). Same scripts, `--res 1080x1920 --samples 12`.
2. **First frame:** open on the face, not the top of the head (thumbnail and scroll‑stop value).
3. **Rig polish:** corrective shape keys for the shoulders and sleeves, hem‑collision correction, spring bones for hair and shirt secondary motion.
4. **Neutrophil menace:** larger in frame, slower reveal, a stronger rim light, more visible pseudopod "reaching" before the grab.
5. **Denim colour:** add a slight blue emission/sheen or use a cooler fill on the character in red environments.
6. **Human review:** have a person listen to the narration and the mix, and watch at phone size before upload.
7. **Reference study:** redo REFERENCE_ANALYSIS with the actual MP4s (motion, audio, editing cadence).
8. **Mascot match:** recalibrate `mascot_config.py` against the real uploaded mascot image.
