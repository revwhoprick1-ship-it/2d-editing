# VIDEO_005 — Render + QA

Export `EXPORTS/VIDEO_005_What_If_Toilets_Fought_Back.mp4`: **32.4 s (972 frames), 1080×1920, 30 fps, H.264/AAC, 20.6 MB.**

## Render
* EEVEE, 540×960 → ×2 in the edit, **1 sample + OpenImageDenoise**, ray tracing off, AgX Medium‑High‑Contrast, soft shadows. CPU only (no GPU on this machine).
* **936 frames, 2,606 s = 43.4 min wall** (2 lanes, ~4–5 s per frame per lane), plus a **7.1 min** re‑render of 121 frames after QA (POV + street exit shot). **Total ≈ 50.5 min.**
* Edit + encode ≈ 2.2 min per export.

## QA (on the export)
* ✅ 32.4 s · −14.1 LUFS · −1.0 dBTP · no black or frozen segments.
* ✅ **Loop test, 7/7:**
  * seam change 0.013, below normal motion (0.050);
  * no black frame, no silence and no click in a 3× loop;
  * the audio runs straight into the frame‑3 slam.
* ✅ Narration: 11/11 lines matched by Whisper after re‑generating 3 bad takes. The narrator stays the loudest layer (SFX −5 dB, music ducked 8 dB under speech).
* Watched every 0.5 s.
  * **v1 → v2 fixes:**
    * 19–21.5 s was blown‑out white (the POV camera sat inside the giant toilet);
    * the mascot ran through the street camera;
    * the tub eyes now get a punch‑in.
  * **Fixed in test renders, before the final render:**
    * the toilet's lid hid its eyes (moved to "frog eyes" on the tank);
    * the giant's head was inside the back wall;
    * the run cycle rotated his whole body;
    * cameras sat inside walls and inside the mascot;
    * the mascot sank into the solid tub.

## Known weaknesses
* The tub's face is small and reads late, even with the punch‑in.
* The tub landing pose is awkward (legs up over the rim).
* In the boss over‑the‑shoulder shot the mascot is mostly cut off at the edge.
* The water is stylised (tapered jets + droplets), not a fluid simulation.
* The street set is reused from VIDEO_004, so it is simpler than the bathroom.
* Background people are small.
