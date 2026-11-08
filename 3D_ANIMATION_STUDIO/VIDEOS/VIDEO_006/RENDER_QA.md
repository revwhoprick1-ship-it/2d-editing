# VIDEO_006 — Render and QA

Export: `EXPORTS/VIDEO_006_The_13th_Floor.mp4`. **38.0 s · 1080×1920 · 30 fps · H.264 High yuv420p · AAC 48 kHz · 8.8 MB.**

## Render (real 2D)
| | |
|---|---|
| Drawing | `anim2d.py`: Skia vector, 1080×1920 native, 4 processes, only the 1,136 frames the EDL shows |
| Draw time | **≈ 25 s** for all frames (≈ 0.09 s per frame, CPU) |
| Edit + encode | ≈ 2.3 min (captions, HUD, punch-ins, shake, flashes; x264 `slow`, CRF 18) |
| Earlier 3D attempt | 59.5 min in Blender (1,118 frames), scrapped: it read as 3D, not 2D |

The 2D pipeline is ~100× faster than the 3D one, and drawing at native resolution means no upscaling and no grain.

## QA (on the export)
| Check | Result |
|---|---|
| 1080×1920, 30 fps, H.264, yuv420p, AAC | ✅ |
| Duration 35–40 s | ✅ 38.0 s |
| Loudness | ✅ −14.5 LUFS, true peak −1.0 dBTP, LRA 7.9 LU (suspense needs the quiet parts) |
| Silence ≥ 250 ms in the 3× loop | ✅ none (room tone, power‑cut tail and the final DING cover the blacks) |
| Audio gap / click at the seam, A/V length | ✅ / ✅ / ✅ |
| Black segments | ⚠️ **by design:** 29.87–30.43 s (lights out, the story beat) and 37.80–37.97 s (cut to black + DING into frame 0) |
| Seam picture change | ⚠️ **by design:** black → the lit floor display, carried by the DING |

Fixed during QA: captions covered the eyes in the two face close‑ups (faces moved up); the reflection's smile was hidden behind his head (reflection moved right, made clearer).

Known weak spots: the cut‑out puppet only has front and back views (no true profile), so the door‑pounding shot is from behind. The double sitting on the sofa is small in the wide over‑the‑shoulder shot. He pops into the long hallway shot from behind the camera.
