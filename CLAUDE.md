# Studio rules (from the user)

* **"2dEDIT"** = **real 2D animation** (flat vector drawing, NOT 3D, NOT toon-shaded Blender). Characters are 2D cut-out
  puppets (flat fill + one cel-shadow tone + rim light), sets are flat vector paintings, light is painted (glows, cones,
  vignette), dark muted low-key mood, small top HUD row, condensed bold white captions with one red keyword, dialogue in
  quotes with a small red speaker label. Implementation: `PIPELINE/twod/flat.py` (Skia, BSD) draws every frame at
  1080x1920; captions/HUD from edl_engine (`CAPTIONS['style'] = '2dedit'`, `ASSETS/fonts/RobotoCondensed-Bold.ttf`).
* Always **send the exported video first**, then run QA and fix/re-render.
* Normal (non-vibrant) colour unless asked. Keep all on-screen text inside the safe area. Narrator: free local
  Chatterbox (Kokoro timbre), never paid TTS without approval.
* Reply in short "caveman" talk.
