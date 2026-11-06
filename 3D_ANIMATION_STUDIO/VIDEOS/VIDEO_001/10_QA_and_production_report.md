# VIDEO_001 — QA & Final Production Report

> Status: **filled in after the final render and export.** Numbers marked ⟨…⟩ come from `qc/qc_report.json` and `audio/mix_stats.json`.

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
⟨duration⟩ s

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
⟨filled from qc_report.json: spec checks, loudness, true peak, black/freeze detection, contact‑sheet review notes⟩

## 13. What to improve next time
⟨filled after review⟩
