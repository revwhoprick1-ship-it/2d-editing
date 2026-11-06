# VIDEO_001 — Final Critical Reviews Before Rendering

## A. Viewer review (ordinary viewer, no biology background)
| Question | Answer | Action |
|---|---|---|
| Would I keep watching after 3 s? | Yes. A boy wakes up on a giant red cushion inside a red tunnel while a voice says my body is about to attack me. | — |
| Is it understandable without biology knowledge? | Mostly. Each term arrives with an image ("cushion → red blood cell", "valves → slam shut", "neutrophil → first responder that swallows intruders"). | Captions emphasise the key nouns. |
| Boring moments? | Risk at S07 (gas exchange, ~8 s). | Kept visually active: particles, colour shift, pointing, and a camera move through the wall. The planted shadow ends the shot. |
| Is the danger understandable? | Yes. A giant cell blocks a tunnel he can barely fit in, then grabs his leg. | — |
| Does the ending deliver? | Yes. A callback joke (the shoe) plus a visual gag insert. | — |
| Confusion risk | The exterior heart "map" shot (SH04a) shows a glowing dot, which might not read as "you". | Narration "That's your heart" + the dot's warm mascot‑orange colour + it enters a vessel. Accepted. |

## B. Scientific review
| Item | Status |
|---|---|
| RBC shape | Biconcave profile from the Evans & Fung (1972) equation, 7.8 µm scaled. ✅ |
| RBCs fold in capillaries | Shown as "parachute" cups in single file. Supported by "barely wide enough for an erythrocyte to squeeze through" (OpenStax). ✅ The "single file" wording was **not** narrated (no direct source). |
| Heart route | Vein → right side → lungs → back to the heart → left ventricle (main systemic pump) → aorta. ✅ Matches OpenStax §19.1. |
| Lub‑dub | Narrated as valves closing. ✅ OpenStax §19.3. |
| Gas exchange | O₂ into the blood, CO₂ out to the air sac, through a ~0.5 µm membrane ("over a hundred times thinner than paper", derived). ✅ |
| Oxygenated colour | Cells brighten after O₂ uptake. Shown, not narrated. ✅ |
| Neutrophil | Granular, lobed nucleus, larger than RBCs and capillaries so it deforms, phagocytosis by pseudopods. ✅ "First responder" (Cleveland Clinic) ✅ |
| Fiction framing | Being shrunk, surviving, "the cell keeps a shoe". The narration never claims these are possible. The script's tone ("You've been shrunk…") is plainly a what‑if. ✅ |
| Colours | Convention colours (blue O₂ etc.) are teaching colours. Noted in the research doc. ✅ |
| Removed claims | 1‑minute circulation, 25 trillion RBCs, alveoli count, neutrophil transit speed: removed (unsourced). ✅ |

## C. Production review
| Question | Answer | Action |
|---|---|---|
| Can each scene be made at the desired quality on this hardware? | Yes, at 540×960 render resolution (see HARDWARE doc). Native 1080 would take about 15–20 h. | Final at 540×960 ×6 samples, 2 parallel workers, Lanczos upscale. |
| Are the environments detailed enough? | Vein (cobblestone endothelium, fog, ~260–420 tumbling cells, plasma specks), ventricle (trabeculae, chordae, valve cusps), capillary + alveolus cluster, aorta. ✅ | — |
| Can the mascot perform the actions? | Sit, grip, pat, flinch, point, back away, flail, kick, fly, lift a foot. ✅ via API. Lying pose was **redesigned** (his head clipped into the cell's rim, found in the preview). | SH01 now opens slumped asleep in the dimple. |
| Shots to redesign? | SH01 (above). SH12b (the sneaker was too small inside the noisy translucent membrane): sneaker 2× bigger, membrane alpha lowered. | Done before the final render. |
| Biggest risk | Translucent (dithered) membranes look noisy at low sample counts. | Final uses 6 samples. Neutrophil close‑ups use DOF to soften. |
