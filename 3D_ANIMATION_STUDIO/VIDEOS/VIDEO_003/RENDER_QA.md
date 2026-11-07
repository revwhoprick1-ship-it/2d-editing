# VIDEO_003 — Render + QA

Export: `EXPORTS/VIDEO_003_What_If_All_Drugs_Became_Legal.mp4`: **33.0 s, 1080×1920, 30 fps, H.264/AAC, 26.2 MB**.

## Render
| | VIDEO_002 | **VIDEO_003** |
|---|---|---|
| Settings | EEVEE 540×960, 3 samples | EEVEE 540×960, **1 sample + OpenImageDenoise**, ray tracing off |
| Frames | 765 | 910 (every frame rendered, nothing on twos, no frame blending) |
| Wall time | 58.0 min (4.55 s/frame) | **29.5 min (1.94 s/frame)** |
| Grain | visible on fabric | none (the denoiser removes it; the file is 3× smaller because x264 no longer spends bits on grain) |
| Estimate before the render | — | 2.2 s/frame × 910 ≈ 33 min |

Edit + encode: 143 s. Speed comes from: 1 sample + denoise; rendering only the frames the edit shows;
1–2 characters per shot on a simple set; 2 lanes; all effects done in 2D.

## QA (on the export)
* ✅ 1080×1920, 30 fps, H.264 High, yuv420p, AAC 48 kHz; −14.1 LUFS, −0.9 dBTP; no black or frozen segments.
* Loop test (3× back‑to‑back): ✅ no black frame, no silence, no click at the seam, audio/video within 3 ms.
  ⚠️ The seam frame change (0.16) is larger than ordinary motion. It's the same take, but the camera
  widens on the jump (the drop). Real cuts measure 0.52–0.55.
* Narration: 13/13 lines, every word matched by Whisper. Pitch range 17.6 semitones (VIDEO_002: ≈9).
* Visual check (`qc/contact_every_0.5s.jpg`):
  * **Fixed:** an over‑saturated first grade (yellow skin, the pink backdrop rendering as red); emoji boxes in the big title; the caption over grandma's face on the punch‑in.
  * **Left in:**
    * the mascot's face is warm/yellow under the yellow glow light in the pink shots;
    * the pill bottles hide grandma's hands;
    * the phone prop is small.
