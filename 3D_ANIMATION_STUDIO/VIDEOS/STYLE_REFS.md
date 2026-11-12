# Style + flow refs (analyzed 2026-11-11)

**Style ref (prison reel, 47 s, 12 cuts):** 3D toon sets with black ink outlines + flat 2D round-head character (also inked).
Indigo/purple moonlight, warm lamp/flashlight pools, light beams, vignette. Few cuts: slow dolly / pan / push moves,
extreme face close-ups, low + dutch angles. Small white captions (2-3 words) mid-screen. End: black card "COMMENT X or Y".
-> Our "2.5D ink" look (VIDEOS/TEST_STYLE): `inked()` layer (Dilate + ink color) around sets AND puppet; mid-indigo
palette (#5A5AA0 / #40407A / lavender #A8A4E0 / warm #FFB870); camera moves drawn IN the scene (Cam z/x/eye per frame =
real parallax), not 2D zoom; light pools/beams; grain.

**Flow ref (survival base reel, 154 s, 62 cuts ~2.5 s/cut):** HOOK 0-3 s: title + emergency news on TV = stakes now.
BUILD UP: rules on cards ("RULE 1: the house must look dead"), x-ray/cross-section of the house, infographics
(1 person = 1 gallon/day, well 20/day = 20 people), pop-up labels on objects (LOOKS EMPTY, OURS, SOLAR ON), CCTV night cams,
color per phase (warm day -> green night-vision -> red danger). PAYOFF: three soft knocks, red door, "she isn't knocking",
choice card (OPEN / HIDE) + "Part 2 tomorrow". Lesson: logic + rules make viewers think along; labels explain without talk.

## Ref 3 (IG reel DflfItCxFd5, "World Games" gooning final) = HYBRID: 3D world + flat 2D characters
- Sets are real 3D renders (stadium, podiums, commentary booth): perspective, parallax camera moves, strong depth of field,
  vignette, soft grain. Props have thin black outlines.
- Characters are NOT 3D: flat 2D cut-outs (white round heads, black outline, flat clothes) standing in the 3D set.
- Flat graphic inserts full-screen (scoreboard, training calendar "DAY 1,461"), a sepia "1904" archive look for history.
- One-word captions mid-screen, white bold with black outline, the key word red/yellow.
- Our pipeline: `VIDEOS/TEST_3D/scene3d.py --bg 1` (Blender EEVEE: set + camera + DOF, writes track.json) ->
  `comp2d.py` (Skia: flat mascot glued to the 3D camera via track.json, contact shadow, tint, ink, grain) -> edl_engine.
