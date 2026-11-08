# VIDEO_006 — The 13th Floor (2dEDIT)

38.0 s · 1080×1920 · 30 fps · seamless loop · `EXPORTS/VIDEO_006_The_13th_Floor.mp4`

## 1. Style: "2dEDIT"
The user's reference look, applied to our own sets and mascot:
* **Toon shading** (`studio_lib/toon.py`): every material becomes light → Shader‑to‑RGB → 3‑step eased ramp × base colour → emission. No gloss, flat fills, soft shadow steps. Lamps, screens and the display stay emissive. See‑through materials (the dark "mirror" steel) keep their alpha.
* **Low‑key practical lighting:** a cool ceiling panel in the elevator, three warm wall sconces in the hallway, a lamp and a TV glow in the apartment. Dark, muted palette. Normal colour (no saturation boost).
* **Captions** (`edl_engine` `CAPTIONS['style']='2dedit'`): Roboto Condensed Bold, white, thin outline + soft shadow, **one red keyword**, short phrases. Dialogue is in quotes with a small red speaker label (`HIM`, `???`).
* **HUD** (`ov_hud`): one small top row, only story facts: `11:48 PM · FLOOR 12 · PASSENGERS: 1`. A value that changes flashes red.

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
