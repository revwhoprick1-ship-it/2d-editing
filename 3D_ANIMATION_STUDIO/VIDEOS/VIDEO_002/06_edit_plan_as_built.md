# VIDEO_002 — Edit plan (as built)

Source of truth: `edit_video002.py` (EDL), rendered by `PIPELINE/editing/edl_engine.py`.
Every cut, zoom, flash and graphic is keyed to a **narration word time** (Kokoro word timestamps +
0.5 s) or to a **frame of the 3D animation**. If the narration is regenerated, the edit re‑times
itself.

**Pace:** 25 shots in 36.1 s, so the average shot is **1.44 s** (VIDEO_001: 2.85 s). The longest
shot is 3.2 s, and it has 3 punch‑ins inside it. Inside the shots there are 8 flashes, 5 shakes,
9 whip pans, ~60 zoom keys and 27 animated graphics. Captions are 92 px, max 3 words, and the
emphasis word is yellow.

| # | Time (s) | Shot | Editing technique | Synced to |
|---|---|---|---|---|
| E01 | 0.00–0.60 | Elevator wide, the jolt | **Cold open on the event** (frame 0 = everyone farts). Impact zoom 1.0→1.06, 2D shake. Title pops already in motion on frame 0. Clock bug 3:14:00 PM | fart chorus on sample 0 |
| E02 | 0.60–1.70 | **3‑way split screen** (grandma / mascot / businessman eyes) | reaction inserts; the mascot sits in the clean middle tile | the 2nd chorus blast |
| E03 | 1.70–2.90 | Elevator wide | slow push during the awkward **side‑eye** → **whip pan out** | elevator *ding* (2.0) |
| E04 | 2.90–4.01 | Earth | **whip in** + flash; counter 0 → 8,000,000,000; 45 puffs pop | a pitched *pfft* per puff frame |
| E05 | 4.01–4.85 | Mascot CU | **smash cut on "elevators"**: nose pinch and fanning, shake | tick + fan swishes per frame |
| E06 | 4.85–6.05 | Anchor CU | **smash cut on "On"**; frozen smile, eye twitch; **punch‑in** 1.0→1.12 at +0.5 s | wet fart on his jolt (f8), ticks on each twitch |
| E07 | 6.05–7.57 | Wedding kiss | cut on "In"; organ; the kiss → jolt; **punch‑in + shake**; organ **tape‑stops** | trumpet/squeaker farts + record scratch at f22 |
| E08 | 7.57–10.16 | Earth orbit | **whip in**; science chips `13–21× A DAY`, `✅ TOTALLY NORMAL` pop in | chime on "normal" |
| E09 | 10.16–13.19 | Polite guests | **slow push**; animated sulfur speck labelled `SULFUR (TINY)` drifts in | sparkle on "sulfur" |
| E10a | 13.19–13.87 | Guest (hold) | **pause before the punchline**: picture held, slow creep 1.1→1.28, music cut to silence | "Tiny." |
| E10b | 13.87–14.71 | Guests faint | **speed ramp** (snap, then fast), flash, heavy shake | slide whistle + 3 thuds on the landing frames |
| E11 | 14.71–17.96 | News wide | **punch‑in on "who farted first"** (1.24→1.38); lower‑third slam; **ticker**; live bug | news sting, dun‑dun‑DUNNN |
| E12 | 17.96–20.71 | CCTV | CCTV look (tint, scanlines, timestamp); **ENHANCE ×3** = 3 punch‑ins (1.9×, 3.4×, 6×) that de‑pixelate, flashes, target boxes | each "Enhance" word; computer beeps |
| E12b | 20.71–21.43 | CCTV face crop | `MATCH FOUND` stamp | beeps + brass stab |
| E13a | 21.43–22.18 | Elevator | everyone **turns to stare** (time‑remapped) | rustle; riser |
| E13b | 22.18–22.97 | Mascot CU | **freeze frame** (desaturated tint) + `SUSPECT #1` stamp + `👍 LIKE = GUILTY` | shutter snap, music **stop‑time** |
| E14–16 | 22.97–27.78 | Blame chain | **whip pans that follow each pointing finger** (pan direction = finger direction); numbered suspect tags; small punch‑in on each accusation | brass stab + kick on each finger landing (f267/313/361) |
| E17 | 27.78–29.18 | Kid OTS → mascot | **deadpan time‑remap**: the shot almost freezes (404→405 over 0.86 s), then the point snaps onto "him" with an off‑centre punch‑in | diminished stab + taiko on "him" |
| E18 | 29.18–29.79 | Mascot CU | **reaction insert**: flash, zoom‑out snap 1.25→1.05, shake | *boing* + gasp |
| E19 | 29.79–32.66 | Mascot 3/4 CU | innocent whistle, animated sweat drops, slow creep, then a **dramatic punch‑in on "But this one?"** | whistle cut off by the bass hit |
| E20 | 32.66–33.54 | **VHS rewind** through the whole video | re‑composites the earlier timeline backwards, tracking noise, `◀◀ REWIND` HUD | tape rewind squeal |
| E21 | 33.54–36.10 | Elevator wide (calm) | the **same continuous take** that frame 0 continues; clock 3:13:59 | muzak tape‑start; *pfft* at f66 → loop |

## Changes from the script table (04) during the build
* **L02:** the mascot pinches his nose and fans the air. Pulling the shirt over the nose didn't read at Shorts size.
* **L04:** the sulfur line plays over the polite wedding guests (with an animated speck), not the planet. The "Tiny." set‑up and punchline now happen in the same place as the faint.
* **L08:** the freeze frame uses a shutter snap and a music stop. The record scratch is used once, at the wedding, so it keeps its punch.
* **L07/L08:** `MATCH FOUND` holds through "One elevator" (0.7 s) and is readable. The first cut held it for only 0.14 s; QA caught this on the preview edit.

## Captions
Max 3 words per chunk, Montserrat ExtraBold 92 px, 8 px stroke + shadow. Emphasis words in yellow
(`billion, farted, second, elevators, tv, wedding, kiss, normal, tiny, sulfur, first, enhance, guy,
grandma, businessman, kid, him, contagious`). Captions sit at y=1250 and move up or down when a
graphic owns that area (title, news lower third, CCTV HUD). They are hidden during the rewind.
