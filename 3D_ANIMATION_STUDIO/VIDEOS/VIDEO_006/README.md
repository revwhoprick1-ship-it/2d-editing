# VIDEO_006 — The 13th Floor (2dEDIT)

38.0 s · 1080×1920 · 30 fps · seamless loop · `EXPORTS/VIDEO_006_The_13th_Floor.mp4`

## 1. Style: "2dEDIT" = real 2D animation
v1 was made in Blender with toon shading and still read as 3D, so it was scrapped. This version has no 3D at all:
* Every frame is **flat vector art drawn with Skia** (`VIDEOS/VIDEO_006/anim2d.py`, puppet in `PIPELINE/twod/flat.py`).
* **Characters** are 2D cut-out puppets. The mascot is redrawn flat (orange tee, brown swept hair, big eyes, jeans, white shoes). Each part has one flat fill, one cel-shadow tone and a rim light. The face rig has eyes, pupils, brows, lids, mouth shapes and blush, plus a walk cycle, arms, head tilt and a fake 3/4 turn.
* **Sets** are flat paintings in one-point perspective: the elevator, the hallway (wallpaper, runner, sconces, the photo, the far door that swings open) and the apartment (lamp, TV static, sofa).
* **Light is painted:** additive glows, light spill, flicker and a vignette. The mood is dark and muted.
* **Captions and HUD:** Roboto Condensed Bold captions in white with one red keyword. Dialogue is in quotes with a small red speaker label. One small top HUD row (`11:48 PM · FLOOR 12 · PASSENGERS: 1`) shows only story facts; a value that changes flashes red.

## 2. Story → shots
| Time | Beat | Shot / device |
|---|---|---|
| 0–0.95 | the display jumps 12 → **13** by itself; `HE PRESSED 12.` | display CU, punch‑in on the flip; HUD `FLOOR 13` flashes red |
| 0.95–6.9 | "Wait… this building only has twelve floors." Lights flicker, the display glitches | high wide → face CU (punch on "twelve") → display → face |
| 7.0–11.9 | DING. The doors open on a dark, old hallway; a silhouette at the far end. "But when the doors opened… this wasn't another floor." | POV from inside the car, slow push, punch on "wasn't" |
| 11.9–16.85 | he walks out; a framed photo on the wall: **him**, same hallway | tracking OTS → photo insert (sting) → eyes ECU |
| 16.9–20.35 | he turns; the doors **SLAM**; he pounds them: "Hey! Wait!" | reverse wide (flash + shake) → handheld door side |
| 20.4–27.85 | the far door creaks open by itself. Warm apartment, TV static, someone on the couch… it's him. He turns his head, then stands | long lens down the hall → OTS into the apartment; silence builds |
| 27.85–29.85 | the double: **"You're late… again."** | CU, punch on "again" |
| 29.85–30.4 | lights out | hard cut to black, power‑cut thunk |
| 30.4–34.9 | DING — he stumbles back into the elevator, jabs the button. Display: 12. Clock: **11:48** again (HUD flashes red). The 13 button is still lit | inside wide → display → button insert |
| 34.9–37.8 | he faces the steel wall. His reflection **smiles**; he doesn't. HUD: `PASSENGERS: 2` (red) | over‑the‑shoulder into the "mirror", slow push |
| 37.8–38.0 | black + DING → frame 0 (the display flips to 13 again) | loop |

The reflection is a mirrored copy of the mascot (scale x = −1) standing behind the semi‑transparent right wall, lit by its own light, so it can act on its own (the smile).

## 3. Sound
Score (`music_gen.cue_video006`): sub drone, detuned pad, lonely high piano; tremolo strings at the doors; heartbeat taiko; a string cluster into the slam; a fast low ostinato for the panic; near‑nothing for the walk; **music out** from 27.7 s ("You're late… again." plays over TV static only) through the lights‑out; uneasy pulse and a hit on the 11:48 clock; high tremolo that is cut dead on the final black.
New synthesised SFX (all original, `sfx_comedy.py`): eerie elevator ding, fluorescent flicker buzz, door slide, steel slam, fist on steel, footsteps with hallway echo, photo sting, long door creak, TV static bed, power cut, glass swell (the smile), cable hum. 62 cues in `audio/cues.json`.

## 4. Voices
Free local Chatterbox. Mascot: Kokoro `am_puck` timbre (D1, D2). The double: same timbre, calm and slow (D3). Narrator: Kokoro `am_fenrir` timbre (N1). Every word matched in the Whisper check.

Render/QA: `RENDER_QA.md`.

