# Mascot model & rig guide

Files: `CHARACTER/mascot.blend` (model only), `CHARACTER/mascot_rig.blend` (rigged, with the action library), built by `PIPELINE/blender_scripts/build_mascot.py`. All proportions and colours are in `studio_lib/mascot_config.py`. **To recalibrate the mascot against the uploaded reference image, edit that file and rebuild. Never hand‑edit a different character.**

## Construction (not primitives)
| Part | How it is built |
|---|---|
| Head | Spherified cube (≈5.5k verts) sculpted by a displacement field: cranium, jaw taper, chin, cheeks, eye sockets, brow ridge, nose bridge, tip and alae, lips, mouth corners, mentolabial fold. A **real mouth opening** with rolled lips and an inner mouth bag. Subdivision 2. |
| Mouth interior | Upper and lower teeth rows (lower on the jaw bone), tongue (on the jaw). |
| Eyes | Separate eyeballs with a corneal bulge. Procedural iris (fibres, limbal ring, light inner ring), large pupil, clear coat for catchlights. |
| Lids | Upper and lower hemispherical lid shells with thickness and a lash line, rotating around the eye centre. Upper lashes as a tapered strip with an outer flick. |
| Brows | Tapered strips on the brow ridge, each skinned to 3 bones (inner/mid/outer). |
| Ears | Flattened shell with helix rim, scapha, antihelix ridge, concha bowl and lobe, angled out from the head. |
| Hair | Scalp shell + ~70 tapered, flattened clumps in 4 layers (back/sides, top volume, temples, fringe) with per‑clump colour variation and a strand shader. |
| Arms + hands | One skin‑modifier mesh from shoulder to fingertips: 5 fingers × 3 joints, flattened palm, separate fingernails. |
| T‑shirt | Lofted torso with crew‑neck rib (dips at front), hem fold, set‑in sleeves with hem folds, solidified thickness, waist and armpit folds, seam colouring. |
| Jeans | Skin‑modifier pelvis and legs, rolled cuffs, outer‑seam topstitching, knee and ankle stacking wrinkles. |
| Sneakers | Sculpted shoe last with sole, toe bumper and heel counter accents, laces. **Sock feet** (hidden) for when a shoe is lost. |

## Bones & conventions
`root → hips → spine → chest → neck → head` (+ `jaw`, `eye.L/R`, `lid_up/lid_lo.L/R`, `brow_in/mid/out.L/R`, `eye_target`), `shoulder → upperarm → forearm → hand → thumb/index/middle/ring/pinky _01–03` per side, `thigh → shin` (IK to `foot_ik`, pole `knee_pole`), `foot → toe` under `foot_ik`, and optional arm IK (`hand_ik`, `elbow_pole`, constraint `ArmIK` with influence 0 by default).

Measured rotation signs (the API mirrors .R automatically):
| Control | Effect |
|---|---|
| `jaw` +X | opens |
| `head`/`neck` +X / +Y / +Z | nod down / turn to his left / tilt to his right |
| `spine`/`chest` +X / +Y | bend forward / twist left |
| `upperarm` +Z / +X | raise sideways / swing forward |
| `forearm` +X | bend elbow |
| `hand` −X | flex wrist toward palm |
| finger bones −X | curl |
| `lid_up` +X / −48° | opens wider / fully closed |
| `lid_lo` +X | raises (squint) |
| `lid_up` rotY (L+, R−) | raises outer corner (angry tilt) |
| brow bones `location.z` (metres) | raise |
| `eye_target` location (x, up, 0) | gaze in head space |
| `foot_ik` location (0, forward, up) | IK foot placement |
| `hips` location (0, up, forward) | crouch / sit / weight shift |

## Facial shape keys (head)
`smile.L/R, frown.L/R, wide, pucker, funnel, upper_lip_up, lower_lip_down, lips_press, lip_tuck, cheek_puff, cheek_raise.L/R, sneer.L/R, mouth_left, mouth_right`. These combine with the jaw bone.

## Python API (`studio_lib/mascot_api.py`)
```python
m = Mascot()                     # or from scene_kit.append_mascot()
m.expression('scared', 0.8)      # 12 expressions + neutral, blendable
m.head_pose(turn=20, nod=-5); m.spine_pose(bend=10); m.arm('R', raise_=60, forward=60, elbow=6)
m.hand('R', point=True); m.eyes(0.2, 0.05); m.key(frame)
blink(m, frame); walk(m, 1, 120, speed=1.1); walk(..., run=True); jump(m, f); sit_down(m, f)
wave(m, 'L', f); point_at(m, 'R', f); lipsync(m, words_with_phonemes)
```
Phoneme lip sync maps Kokoro/misaki phonemes to 12 visemes (`VISEMES`, `PHONEME_TO_VISEME`).

## Stored in `mascot_rig.blend`
Actions `ANIM_walk_cycle`, `ANIM_run_cycle`, `ANIM_jump`, `ANIM_sit`, `ANIM_wave_L`, `ANIM_point_R`, `ANIM_idle_breath`, and 13 `EXP_*` pose actions (bones; their shape‑key values are stored as JSON on each action). The full expression definitions are in `CHARACTER/expressions/expressions.json`.

## Known limitations
* Body volume under the clothes is not modelled (standard for stylised characters). Very extreme arm raises (> 120°) stretch the sleeve.
* Weights are generated procedurally (distance‑to‑bone falloff), not hand‑painted. Elbows and knees use preserve‑volume, but a hand‑painting pass would improve the shoulders.
* No cloth or hair simulation. Hair is rigid on the head bone.
* **The uploaded mascot image never reached this environment** (it was not in the repository or the conversation). The model follows the written description (voluminous brown hair, warm skin, large dark eyes, eyebrows, orange tee). Send the image to recalibrate `mascot_config.py`.
