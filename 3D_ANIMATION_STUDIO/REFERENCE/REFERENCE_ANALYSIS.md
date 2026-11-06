# Reference Analysis: 8 YouTube Shorts

## 0. What could actually be inspected (read this first)

Frame‑by‑frame analysis of all eight videos was **not possible from this environment**, and this document does not pretend otherwise.

| Ref | URL | Title / channel (YouTube oEmbed) | Material actually obtained |
|---|---|---|---|
| 1 | youtube.com/shorts/Gx-qXjrwUBg | *What if you were in a zombie apocalypse in a supermarket?* — **Whatif..animations** | Full metadata (80 s, 1080×1920 available, 30 fps), **full auto‑caption transcript with timestamps**, **YouTube storyboard sprites: 81 frames, one every ≈0.99 s** (50×90 px each), HQ thumbnail |
| 2 | youtube.com/shorts/kxXVVMNe5SI | *How Iron Man's nanobots stitch his wounds* — **Super Labs** | **Full auto‑caption transcript**, HQ thumbnail |
| 3 | youtube.com/shorts/PL-Yro2meY4 | *Your Brain's Secret Idea Zone* — **Ricks Clips** | HQ thumbnail + title only |
| 4 | youtube.com/shorts/MIGjmXaVWsU | *The math behind Gojo's Infinity* — **Silenthys** | HQ thumbnail + title only |
| 5 | youtube.com/shorts/M9XQWnWxhmo | *How badly does a Scorpion Sting Hurt?* — **In Plain Motion** | HQ thumbnail + title only |
| 6 | youtube.com/shorts/AtPy447-jNw | *Can a Bullet Kill a Crocodile?* — **ZipStories** | HQ thumbnail + title only |
| 7 | youtube.com/shorts/tTmyKYyQ5Do | *Why Mosquito Bites Itch* — **Blink Animated** | HQ thumbnail + title only |
| 8 | youtube.com/shorts/h39gkIUTs_g | *Your Painkiller Has No Idea Where Your Pain Is* — **Your Body, Explained** | HQ thumbnail + title only |

**Why:** the first video request returned metadata, but the media stream itself was **HTTP 403**. Every request after that hit YouTube's *"Sign in to confirm you're not a bot"* wall. Getting around that check was deliberately not attempted. Thumbnails (`i.ytimg.com`) and titles (YouTube oEmbed) are public endpoints, so they were used.

**What this means:** Ref 1 can be analysed for structure, pacing, cutting, captions, colour scripting and staging (at thumbnail resolution). Ref 2 can be analysed for script structure. Refs 3–8 can only be analysed for **key‑frame look** (one representative frame each) and **title/hook framing**. Animation quality, lip sync, audio mix, music and SFX **could not be analysed for any reference**, because no audio or motion was obtained. Those sections below are marked *not analysable* instead of being guessed.

**To finish this analysis properly,** please drop the eight MP4 files into `REFERENCE/raw/` (any resolution). `PIPELINE/quality_control/` contains the tools to extract frames and measure audio loudness. The analysis will then be redone at full depth.

Saved evidence: `REFERENCE/reference_frames/ref1_storyboard_contact.png` (81 timestamped frames) and `REFERENCE/reference_frames/all_thumbnails.png` (all 8 key frames).

---

## 1. Individual analyses

### Ref 1 — Zombie apocalypse in a supermarket (Whatif..animations), 80 s
*Source: 81‑frame storyboard + transcript. Times are the storyboard's ≈1 s steps.*

| Time | What is on screen | Narration (auto‑captions) |
|---|---|---|
| 0.0–3.0 | Bright supermarket. The hero (Mark: brown cap‑like hair, red‑orange tee, jeans) pushes a cart, then a close‑up of him drinking. Caption "THE ZOMBIE APOCALYPSE". | "In 3 seconds, the zombie apocalypse will begin…" |
| 4.0–5.9 | Extreme close‑up of his face (big white eyes). Cut to the exterior through glass doors. Captions "WORST POSSIBLE / PLACE TO SURVIVE". | "…and he's in the worst possible place to survive." |
| 6.9–8.9 | **Countdown:** giant red **3 / 2** numerals over face and zombie close‑ups, then a calm face on "1". | "3, 2, 1" |
| 9.9–12.8 | Zombie crashes through the entrance. Shocked close‑up, then an open‑mouth scream ECU, then a wide shot of crowd panic. | "A zombie crashes through the supermarket entrance. Everyone starts screaming…" |
| 13.8–15.8 | He runs toward the camera down the aisle. | "…and Mark runs for his life." |
| 16.8–21.7 | Storage room. Two ECUs ("BUT THERE'S JUST / ONE PROBLEM"), then a reveal of three zombies and a zombie close‑up. | "…three zombies are already inside." |
| 22.7–26.7 | Metal pipe, low angle smashing a window, jump‑through (action pose), landing. | "…grabs a metal pipe, smashes through a window and barely escapes." |
| 27.7–33.6 | Shopping‑cart barricade, then **insert shots listing discoveries**: shelves of food, monitors, green EXIT sign. | "…a security room filled with food, cameras and a back exit." |
| 33.6–34.6 | Relief pose (arms up, smile). | "He thinks he's safe…" |
| 35.5–38.5 | **Lights out.** Grade drops to near black, then a dark red emergency tint. | "…until suddenly all the lights go out." |
| 39.5–45.4 | Monitors. ECU with blue‑white "blood runs cold" grade. **Green night‑vision CCTV UI** of a horde. Big caption "SURROUNDING THE SUPERMARKET!" | "His blood runs cold. Hundreds of zombies…" |
| 46.4–53.3 | "THEN… HE HEARS SOMETHING." Knock knock. Camera switch to a girl outside (CCTV). | "Knock. Knock. Knock…" |
| 55.3–62.2 | Girl crying close‑up (new character, pink dress). Mark ECU with sweat and tears, horror. | "Please, let me in… I don't want to die." |
| 63.2–71.1 | CCTV of approaching zombies, hand hovering over door controls, dilemma beats. | "If he opens the doors, the zombies could get inside, too." |
| 72.1–79.0 | Sad ECU, then the **end card "SAVE HER or LEAVE HER? COMMENT YOUR CHOICE"** on a dark CCTV background. | "Should Mark save the little girl or leave her outside…?" |

* **Visual production:** simple stylised low‑to‑mid‑poly models. The head is about ⅓ of the body, with large white sclera eyes and small dark pupils, cap‑like hair and simple clothing. The environments are clean and readable but sparsely detailed. Lighting is mostly flat and bright, with soft shadows. Production value comes from **colour scripting**, not from model detail: neutral daylight, then darkness, then red emergency, then green night‑vision, then blue horror.
* **Character animation:** *not analysable at 1 fps.* Poses read clearly (run, jump, arms up, hand on controls). Faces rely on eye size and simple mouth shapes, with sweat drops and tears for emotion.
* **Cinematography:** very frequent **ECU reactions** (≈20 of 81 sampled frames are face close‑ups). Wides establish each new location. Low angle is used for the action beat. CCTV POV changes the perspective.
* **Storytelling:** second‑by‑second escalation (zombie, room, more zombies, escape, false safety, darkness, horde, girl, dilemma). A **false‑safety beat** ("he thinks he's safe… until") resets tension. It **ends on an unresolved choice**, which drives comments.
* **Editing:** a new image in almost every 1‑s storyboard sample, so the average shot is about 1–2 s. Captions are 2–4 words, ALL CAPS, heavy condensed font, white/yellow with a thick black outline, red emphasis words, and sit just below the frame centre (≈60–65% of height). Large **graphic numbers (3‑2‑1)** act as pattern interrupts.
* **Audio:** *not analysable.* The captions show `[music]` throughout and `[panting]`. There is a second voice (the girl) as character dialogue.
* **Retention:** **countdown hook** ("in 3 seconds…") creates anticipation in the first second. Cuts on every caption phrase. Ends on a question.

### Ref 2 — Iron Man's nanobots stitch wounds (Super Labs)
* **Script (from transcript):** a single process told in strict time order: detection → swarm → seal → sub‑surface repair → framework for new cells → vessel repair → detach. Signposts: *"When…", "As they…", "Afterwards…", "Over the next moments…"*. It borrows a famous IP for the hook. The narration is a calm explanation, not a story.
* **Key frame:** **realistic macro render.** Skin‑tone surface, a dense swarm of blue micro‑bots around a deep red cut, shallow depth of field, soft key light, cool/warm contrast (blue bots against red flesh). The caption "nanobots spread" is white sentence case with a soft shadow, in the lower‑middle.
* **Takeaway:** micro‑scale realism plus one clear **colour code** (blue = agent, red = body) lets viewers read a complex process instantly.
* **Not analysable:** motion, audio, pacing.

### Ref 3 — Your Brain's Secret Idea Zone (Ricks Clips)
* **Key frame:** a **translucent glass/ice‑blue stylised figure** with a pink brain visible inside its head, sitting on a wooden chair. A single bare bulb overhead in a dark void, a spotlight pool and concentric rings on the floor. Strong chiaroscuro, theatrical staging. The caption is one bold white word with an outline.
* **Takeaway:** **cutaway transparency** shows the inside of a body without leaving the character. A minimal set with one motivated light gives a premium look cheaply.

### Ref 4 — The math behind Gojo's Infinity (Silenthys)
* **Key frame:** **2D flat vector illustration** (Zeno, laurel wreath, beard) between dark columns with a warm gradient. Lower‑third label "ZENO · 450 BC". A red rubber‑stamp graphic reads "NEVER ARRIVES". The caption sits at the top ("Except").
* **Takeaway:** motion‑graphic **labels and stamps** carry facts without narration. Captions can move to the top when the subject fills the lower frame. *(A 2D style, not adopted for our 3D look, but the labelling idea is.)*

### Ref 5 — How badly does a scorpion sting hurt? (In Plain Motion)
* **Key frame:** a stylised but textured 3D scorpion on a macro **skin surface with hairs**. Warm golden key light, a heavy depth‑of‑field falloff to a warm backdrop, slightly glowing red skin under the sting. The caption "nerves **instantly**" has the emphasis word in **orange‑yellow**.
* **Takeaway:** **coloured emphasis on one word per caption**, warm macro lighting and a shallow focal plane.

### Ref 6 — Can a bullet kill a crocodile? (ZipStories)
* **Key frame:** semi‑realistic 3D gorilla (groomed fur) and crocodile (scaly) on a **blue grid "test lab" floor** in a void. Even studio lighting. A single large thin white word caption in the centre.
* **Takeaway:** a neutral "lab" stage makes comparisons clear. Realistic creature assets carry the attention.

### Ref 7 — Why mosquito bites itch (Blink Animated)
* **Key frame:** **stylised 3D cutaway of skin layers**: a red blood vessel, round white cells, yellow fat lobules, a pink dermis band with cell texture, **green histamine particles**. Bright, saturated "candy" palette, soft lighting. The caption "But your body" is white bold with an outline, lower‑middle.
* **Takeaway (most relevant to VIDEO_001):** body interiors read best as **colour‑coded layers and particles**: blood red, immune cells white/pale, chemical signals in a contrasting colour.

### Ref 8 — Your painkiller has no idea where your pain is (Your Body, Explained)
* **Key frame:** a **holographic x‑ray human** (blue translucent skeleton, glowing organs) inside a HUD frame with corner brackets, a channel watermark, and a red label "HEADACHE" with a dashed target ring on the head. The caption "is completely **blind**," is white bold.
* **Takeaway:** a **"body map" HUD shot** locates the viewer before a zoom‑in. It is a strong clarity device for "where in the body are we?"

---

## 2. Common production characteristics (supported by the material above)
1. **Vertical 1080×1920, 30 fps** (confirmed for Ref 1 from its format list).
2. **Captions are always on screen:** short chunks, bold sans‑serif, white with an outline or shadow, in the lower‑middle third, with **one emphasis colour** (yellow, orange or red).
3. **One clear subject per frame** on a dark or simple background, with strong separation from light, colour or depth of field.
4. **Body/biology topics use macro scale, cutaways and colour codes** (Refs 2, 3, 5, 7, 8).
5. **Titles are hooks.** Questions or "what if / how / why" (all 8). Several use **second person** ("your brain", "your body", "your painkiller").
6. **The first line states the premise immediately.** No intros or logos (Refs 1 and 2, confirmed from transcripts).

## 3. Differences
| Axis | Range seen |
|---|---|
| Rendering | 2D flat (4), stylised simple 3D (1), stylised cutaway 3D (3, 7), semi‑real 3D (2, 5, 6), holographic UI (8) |
| Structure | Character story with escalation and a cliffhanger (1). Process explainer (2, 7, 8). Comparison / what‑would‑happen (6). Concept explainer (3, 4, 5). |
| Caption style | ALL CAPS heavy with an outline (1) versus sentence‑case clean (2, 5, 7, 8), or single large words (3, 6) |
| Protagonist | Recurring human character (1). Abstract/no character (2, 4–8). Generic glass figure (3). |

## 4. Why they look appealing
* Controlled palettes with **one accent colour** and value contrast between subject and background.
* **Depth:** shallow DOF macro shots (2, 5), atmospheric darkness (3), layered cutaways (7).
* **Motivated light:** one bulb (3), warm sun‑like key (5), self‑illuminated hologram (8).
* In Ref 1, **colour scripting by act** makes even simple models feel produced.

## 5. Why the storytelling works
* **Immediate premise plus a ticking element** ("In 3 seconds…").
* **Constant escalation with no flat beats.** Each sentence adds a new problem or fact.
* **False safety, then a reversal** (Ref 1, around 34 s).
* **Ending as a question or open loop** (Ref 1). For explainers, the "aha" fact lands at the end (Ref 8's title promise).
* **Second‑person framing** puts the viewer inside the story (7, 8, our title).

## 6. What we should do better
* **Character quality:** Ref 1's character is very simple (cap hair, minimal face rig). Our mascot has a sculpted face, a rigged jaw and lids, brows and 12 expressions.
* **A protagonist inside explainers:** most body explainers (2, 5, 7, 8) have no character. Our mascot gives emotional stakes *inside* the science.
* **Accuracy:** body explainers often skip sources. We keep a sourced fact table for every video.
* **Audio:** unknown for the references, so we set our own measurable standard (LUFS and true‑peak targets, synced SFX).

## 7. Consolidated production style guide
The binding version is `REFERENCE/STYLE_BIBLE.md`. In short: second‑person hook with the premise and threat in line 1, mascot on screen in frame 1. A new shot every 1.5–3.5 s, with ECU reactions on every emotional beat. Colour script per act. A colour code for biology (red = blood, pale lavender = immune, blue = O₂, grey = CO₂). Captions in 2–3‑word chunks, bold, white, outlined, with an orange‑yellow emphasis word. End on a callback or open question.
