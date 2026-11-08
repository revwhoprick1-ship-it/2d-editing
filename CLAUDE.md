# Studio rules (from the user)

* **"2dEDIT"** = make the video in the flat **2D animation look** of the user's reference (stylized characters, cel/toon
  shading with soft colour steps, no gloss, low-key mood lighting from practical lights, dark muted palette, small top
  HUD row, condensed bold white captions with one red keyword, dialogue in quotes with a small red speaker label).
  Implementation: build the scene as usual, then `studio_lib.toon.toonify()` before rendering; captions with
  `ASSETS/fonts/RobotoCondensed-Bold.ttf` (edl_engine `CAPTIONS['style'] = '2dedit'`).
* Always **send the exported video first**, then run QA and fix/re-render.
* Normal (non-vibrant) colour unless asked. Keep all on-screen text inside the safe area. Narrator: free local
  Chatterbox (Kokoro timbre), never paid TTS without approval.
* Reply in short "caveman" talk.
