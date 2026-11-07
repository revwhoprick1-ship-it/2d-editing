# VIDEO_002 — Render and QA report

Export: `EXPORTS/VIDEO_002_What_If_Everyone_Farted.mp4`. **36.1 s · 1080×1920 · 30 fps · H.264 High
(yuv420p, BT.709) · AAC 48 kHz stereo · 82.9 MB.**

## Render
| | |
|---|---|
| Machine | 4‑core Xeon, no GPU (Mesa llvmpipe) |
| Engine | Blender 5.2.3 **EEVEE**, 540×960, **3 samples**, screen‑space ray tracing off, upscaled ×2 (Lanczos) in the edit |
| Frames rendered | **765** (only the frames the edit shows), in 23 render jobs |
| **Estimate before the render** | Benchmark 5.6 s/frame × 769 frames ≈ 72 min on one lane. I expected ≈ 55 min with 2 lanes (≈1.3× from overlapping scene evaluation and rasterisation). After the first 2 minutes the measured rate was 5.8 s/frame of wall time, so I revised the estimate to **≈ 70–75 min**. |
| **Actual render time** | **58.0 min wall time** (1,363 s + 2,117 s): **4.55 s per frame**. The container restarted after 22.7 min. The renderer skips finished frames, so the second run resumed with no loss (the restart downtime is not counted). |
| Edit + encode (1,083 frames) | **137 s** (numpy/PIL compositor → x264 `slow`, CRF 18) |
| Preview pass (before the final) | 270×480, 2 samples, every 3rd frame, ≈ 22 min wall. It caught the sleeve, camera and edit problems listed below. |

### Optimisations (what each one saved)
1. **Render only what the edit shows.** `render_needed.py` walks the EDL through the real compositor and records every frame it asks for. A hold, a freeze or the CCTV ENHANCE sequence costs a single frame (the CCTV beat is **1 frame for 2.75 s** of screen time; the kid's 1.4 s deadpan is 15 frames). The result is 765 frames instead of ≈ 850 for the full job ranges, and no frame of any cut‑away is rendered.
2. **3 samples, no ray tracing.** Benchmarked on the same frame: 7.6 s (4 samples + RT) vs **5.6 s** (3 samples, no RT) with comparable noise. 2 samples (4.1 s) was too grainy on the shirts.
3. **Half resolution + ×2 upscale.** 540×960 has 1/4 of the pixels of 1080×1920. Text and graphics are drawn at full 1080×1920 resolution in the edit, so they stay sharp.
4. **Slow shots on twos** (wide end, whistle, news wide, wedding guests, globe orbit), with the editor blending neighbouring frames.
5. **Per‑job cast hiding** (characters outside the camera's view are hidden). The split‑screen close‑ups render at 0.67 resolution scale. CCTV and freeze effects use stills.
6. **Only `Key*` lights cast shadows.** Extras use `lean_character` (no subdivision on hair, eyes or shoes). Simplify caps subdivision at 1.
7. **All editing effects are 2D.** Zooms, whips, splits, freeze, CCTV, VHS rewind and every graphic are composited. Fixing an edit costs 2.3 min, not a re‑render (this was used five times during QA).
8. **Two cost‑balanced lanes**, resumable, so a crash or restart costs nothing.

## QA (all checks ran on the actual export)
### Technical (`qc/qc_report.json`)
| Check | Result |
|---|---|
| 1080×1920, 30 fps, H.264, yuv420p, AAC | ✅ |
| Duration 30–40 s | ✅ 36.1 s |
| Loudness | ✅ −14.0 LUFS integrated, LRA 2.5 LU |
| True peak | ✅ −1.1 dBTP |
| Black segments / frozen segments | ✅ none / none |

### Loop test (`qc/loop_report.json`, `qc/loop_seam_frames.png`, `qc/loop_seam_audio.png`)
`loop_test.py` decodes the export and also plays it 3× back‑to‑back (108.3 s).
| Check | Result |
|---|---|
| Black frame at the seam / anywhere in the 3× loop | ✅ none (frame luma 0.474 → 0.459) |
| Silence ≥ 250 ms below −50 dB in the 3× loop | ✅ none. The freeze‑frame stop‑time first measured as dead air, so it got room tone. |
| Audio gap at the seam | ✅ none (−35.7 dB going out on the muzak → −18.3 dB on the fart; whole mix −16.8 dB) |
| Click at the seam | ✅ sample jump 0.003, inside the local range (max 0.017) |
| Audio vs video length | ✅ the audio is 17 ms longer (AAC frame padding) |
| Seam picture change "as small as ordinary motion" | ⚠️ **No, by design.** The change from the last frame to the first is 0.12. Ordinary frame‑to‑frame motion is ≤ 0.055 (90th percentile), and real cuts are 0.46–0.55. The seam is not a cut: it is the same camera take (ELEV f76 → f77). The difference is the fart itself: the camera starts its impact push, the 2D shake starts, and the hook title pops in. All three are synced to the fart sound. |

### Sound sync (measured on the stems against the cue times)
Fart chorus +7 ms · kiss fart +4 ms · the three faint thuds +1/+3/+1 ms · freeze shutter 0 ms ·
kid's point lands +1 ms · "But" bass hit 0 ms · loop *pfft* 0 ms · boing −29 ms (within one frame).

### Narration (`audio/narration/qc_report.json`)
13 lines, Kokoro `af_heart`. The Whisper re‑transcription matches every word. The only
"error" is L01's "eight" transcribed as "8". The pitch range is 6.8–14.1 semitones per
line (expressive, not monotone). Narration sits at −16 LUFS in the mix, with music ducked 9 dB
under speech.

### Visual inspection (`qc/contact_every_0.5s.jpg` + full‑size frames)
Problems found and **fixed**:
* Every character's arm showed through the lowered sleeve. The hidden part of the arm now tapers, wears the shirt colour and uses the sleeve's skin weights.
* The whistle shot was too tight (the mouth was cut off). The first blame shot cut grandma off at the frame edge.
* The news wide showed a noisy floor at the bottom. The shot now starts punched in at 1.2.
* Frame 0 was a white flash. The title was clipped at its pop. The clock disappeared for one frame at the loop.
* The mascot was hidden behind the title in the split screen.
* `MATCH FOUND` was on screen for 0.14 s, then was hard to read (green on green) and collided with the caption.
* The LIKE and COMMENT prompts overlapped. Name tags sat off screen.
* Captions covered the mouth in the shock and whistle shots.

Known minor issues **left in** (all small on a phone):
* Fine render grain on fabric at 3 samples.
* A tiny shirt‑fold shard near grandma's hem (second blame shot, bottom of frame).
* The jeans peek through the mascot's shirt when his spine twists (first blame shot).
* The mascot rests a hand on his hip during the side‑eye.
