# STYLE BIBLE: the studio's permanent standard

Every video follows this file. Change it on purpose, never by drift.

## 1. Format
| Item | Standard |
|---|---|
| Canvas | 9:16, **1080×1920** delivery |
| Frame rate | **30 fps** (same as the references). Animate on ones. |
| Length | 45–60 s by default. Story decides. |
| Codec | MP4 · H.264 High@4.2 · yuv420p · BT.709 tags · CRF ≤ 18 · AAC 320 kb/s 48 kHz · `+faststart` |
| Render resolution | Native 1080×1920 when a GPU is available. On the current CPU‑only machine, render at **540×960 (EEVEE, 6 TAA samples)** and upscale with Lanczos + light unsharp (documented trade‑off; see DOCUMENTATION/HARDWARE_AND_RENDERING.md). |
| Safe areas | Keep faces and captions out of the bottom 20% (YouTube UI) and the top 8%. Captions sit 30% above the bottom edge. |

## 2. The mascot (non‑negotiable)
* One protagonist in every video: the studio mascot (`CHARACTER/mascot_rig.blend`). Always append that file. Never rebuild or substitute him.
* Identity locks: voluminous brown side‑swept hair, warm skin, large dark‑brown eyes with catchlights, dark expressive brows, **orange T‑shirt**, blue jeans, white sneakers. Proportions as in `CHARACTER/reference_sheets/`.
* He **acts**: grips, points, flinches, kicks. Every narration beat has a body or face reaction.
* Expressions come from the library (`CHARACTER/expressions/expressions.json`: 12 + neutral). Blend intensity, never exceed 1.2.
* Blink every 2–4 s when he is calm, and on impacts. Eyes always target something (`eye_target`).

## 3. Look
* **Engine:** EEVEE (preview and final on this hardware). Cycles is supported by the same scenes for GPU machines.
* **Colour management:** AgX, look "Punchy". Exposure 0. Never clip skin.
* **Materials:** PBR Principled only. SSS on skin and organic tissue. Clearcoat for "wet" biology. Fabric sheen on clothes.
* **Lighting recipe:** warm key from camera‑left above (area light, soft), cool or tinted fill at 25–35%, strong rim from behind (often a saturated environment colour). Only the key casts shadows in CPU renders.
* **Depth:** distance fog in every interior (material‑level fog toward the world colour) plus shallow DOF on close‑ups (f/1.8–2.8). Foreground elements pass the lens for parallax.
* **Colour script per act** (from Ref 1): calm set‑up, then tension (darker, more saturated), then the danger act (colour shift, more contrast), then release (warm and bright).
* **Biology colour code:** blood/RBC red (dark when deoxygenated, bright when oxygenated), immune cells translucent pale lavender, O₂ blue particles, CO₂ grey particles, nerves yellow, chemical signals green.

## 4. Camera grammar
* **Lens kit:** 18 mm (environments, speed), 24 (action), 35 (medium), 50–55 (CU), 85 (ECU / compression).
* Shot 1 shows the mascot within 0.5 s. The hook pattern is **ECU → fast reveal pull‑back** or **action in progress**.
* Average shot length **1.5–3.5 s**. A shot may hold up to 4.5 s only if it is moving and reveals something.
* Every move has a reason: push‑in = realisation/fear, pull‑back = scale/reveal, track = travel, shake = impact (decaying 6–12 frames), low angle = threat/scale.
* Reaction ECUs land on every emotional turn.

## 5. Story & script rules
1. Line 1 = premise + stakes, in second person when the title is "What if you…".
2. A new fact, danger or joke in every sentence. No "today we'll learn", no CTA filler.
3. Facts must appear in the video's research table with a source. Fiction is framed as fiction.
4. At least one **pattern interrupt** (music drop, silence beat, colour flip) before the main conflict.
5. The ending is a callback, twist or open question. Never "follow for more".
6. Write 3 concepts, score them, draft, critique, revise (see `TEMPLATES/production_template.md`).

## 6. Narration
* **Narrator identity:** Kokoro‑82M voice **`af_heart`** (warm, clear US‑English female storyteller, Kokoro quality grade A). Backup male voice `am_fenrir` (grade C+). Do not switch narrators within a series.
* Delivery presets (speed / pause): hook 0.93, curious 0.97, calm 0.95, suspense 0.88–0.95 with longer pauses, urgent 1.05–1.12, excited 1.04–1.07, humour 0.98 with a beat before the punchline.
* Every line must pass ASR QC (WER = 0 after normalisation). Pronunciation fixes go through `pronunciations` or a rephrase.
* Target pace is 2.6–3.4 words/s. A hook line should not exceed about 3.9 words/s.

## 7. Captions
* Font: **Montserrat ExtraBold** (SIL OFL), 78 px at 1080 width, ALL CAPS.
* White, 7 px near‑black outline, soft 4 px shadow. 2–3 words per chunk. Pop‑in 0.16 s (82% → 104% → 100%).
* One **emphasis colour #FFC83D** (warm yellow‑orange, related to the mascot's shirt) for key nouns and verbs only.
* Position 30% from the bottom, centred. Move up only if the mascot's face is there.

## 8. Sound
* **Layers:** narration, music (ducked), SFX, ambience. Stems are always exported.
* **Narration chain:** HPF 80 Hz → −2 dB @ 280 Hz → +2.5 dB @ 3.2 kHz → +1.5 dB @ 10 kHz → de‑ess → 3:1 comp → light saturation → −16 LUFS.
* **Music:** original procedural score (`PIPELINE/audio/music_gen.py`), composed per video around the story acts. Sidechain duck about 9 dB under speech. One **drop to silence** before the big reveal.
* **SFX:** studio library (`AUDIO/sound_effects`, 46 sounds, all original). Every SFX is tied to an on‑screen event in the cue sheet. A recurring motif per video (VIDEO_001: the heartbeat).
* **Master:** −14 LUFS integrated (±0.5), **true peak ≤ −1 dBTP**, zero clipped samples. Verified with ffmpeg EBU R128.

## 9. QA gates (all must pass before export)
Story review (viewer, science, production), narration QC report, preview animatic watched against narration, render‑frame inspection at the start, middle, end and every cut, mix stats in range, captions checked against the script, and an exported‑file probe (resolution, fps, codec, duration, loudness). See `PIPELINE/quality_control/`.
