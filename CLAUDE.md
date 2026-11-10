# Studio rules (from the user)

* **"2dEDIT"** = **real 2D animation** (flat vector drawing, NOT 3D, NOT toon-shaded Blender). Characters are 2D cut-out
  puppets (flat fill + one cel-shadow tone + rim light), sets are flat vector paintings, light is painted (glows, cones,
  vignette), dark muted low-key mood, small top HUD row, condensed bold white captions with one red keyword, dialogue in
  quotes with a small red speaker label. Implementation: `PIPELINE/twod/flat.py` (Skia, BSD) draws every frame at
  1080x1920; captions/HUD from edl_engine (`CAPTIONS['style'] = '2dedit'`, `ASSETS/fonts/RobotoCondensed-Bold.ttf`).
* Always **send the exported video first**, then run QA and fix/re-render.
* Every video gets the slightly transparent watermark **@insidethemindlessvault** (edl overlay `{'type': 'watermark'}`).
* Series parts: hook must work for new viewers; recap ≤ ~6 s; keep a lore bible (e.g. `VIDEOS/VASE_LORE.md`) and never contradict it.
* Always send a **title + description** (with hashtags + pinned comment) with every video.
* Normal (non-vibrant) colour unless asked. Keep all on-screen text inside the safe area. Narrator: free local
  Qwen3-TTS ONLY (Apache-2.0, `/opt/tools/qwen`: VoiceDesign ref per character -> Base voice clone per line), never paid TTS/ElevenLabs.
* **Retention rules** (from real stats): read `3D_ANIMATION_STUDIO/VIDEOS/RETENTION_LESSONS.md` before every new video. Frame 0 =
  character in danger; no flashbacks/recaps; standalone stories (no "Part 2"); no end choice card; 60–75 s.
* **Always be creative**: never a plain "what if" list. Give the premise a character with a problem, a goal and escalating
  situations (e.g. a disease that forces a funny behaviour during a school day), with a twist.
* **Captions mid-screen** (y ~1150-1300, max 1480): the bottom ~25% is covered by the platforms' own captions/UI.
  Voice lines never hard-cut: soft fades on every line, keep reverb tails (no trim-to-length after FX).
* Reply in short "caveman" talk.
