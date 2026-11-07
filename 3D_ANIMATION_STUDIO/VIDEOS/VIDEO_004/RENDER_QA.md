# VIDEO_004 — Render + QA

Export `EXPORTS/VIDEO_004_What_If_Gravity_Disappeared.mp4`: **33.6 s exactly (1,008 frames), 1080×1920, 30 fps, H.264 High/AAC, 17.1 MB.**

## Render
* Blender 5.2 **EEVEE**, 540×960 → ×2 upscale in the edit (text drawn at full 1080×1920), **1 sample + OpenImageDenoise**, ray tracing off, AgX (normal colour). CPU only: this machine has no GPU (llvmpipe), so GPU rendering was not an option.
* Only the frames the edit shows: **984 frames**, all at full frame rate (nothing on twos).
* **Actual render: 2,368 s = 39.5 min wall** (2 lanes; 4.0–5.8 s per frame per lane, 2.4 s per frame wall). Edit + encode: 119 s. Every edit/QA fix after the render was 2D only (no re‑render).
* Cost drivers: 4 characters + a city street in every frame; the CU/PILE/FALL shots hide the cast they don't show.

## QA (on the export)
* ✅ duration 33.6 s · 1080×1920 · 30 fps · −14.1 LUFS · −1.1 dBTP · no black or frozen segments.
* ✅ **Loop test, all 7 checks pass:**
  * last → first frame change 0.024, *below* ordinary frame motion (90th percentile: 0.038), so the seam is invisible as a cut;
  * no black frame, no silence and no click in a 3× loop;
  * audio and video are exactly the same length;
  * a rising whoosh peaks on the loop point (−26.7 dB going out, −14.9 dB coming in).
* ✅ Narration: 12/12 lines matched word‑for‑word by Whisper; two voices (narrator / mascot).
* Watched every 0.5 s (`qc/contact_every_0.5s.jpg`) + full‑size checks.
  * **Fixed after watching:**
    * edit crash (zoom < 1×; the engine now clamps zoom);
    * the physics panel covered the mascot's face;
    * the "~10 m UP" freeze missed him, then the stamp covered him;
    * dead digital silence before gravity returns (now a −40 dB hush);
    * quiet loop tail (now a whoosh).
  * **Earlier test‑render fixes:**
    * props doubled in height (Blender's apply‑transform baked in the position);
    * props vanished in shots without the kid (wrong collection);
    * washed‑out light;
    * the car blocking shots.

## Known weaknesses (honest)
* The city is simple low‑poly (box buildings with window textures, a simple car); the background people are small in the wide shots.
* The fall shots have plain building walls behind him, so the speed reads mainly from the scream and the editing.
* The lying pose on the mattresses is stiff (arms straight out), and the phone hitting his head is quick; the `BONK` freeze sells it more than the animation does.
* Story time is slowed (the clock counts 10 s over ~23 s of video); the README explains this.
