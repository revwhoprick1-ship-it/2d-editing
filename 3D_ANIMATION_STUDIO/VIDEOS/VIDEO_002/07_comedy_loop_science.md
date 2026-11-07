# VIDEO_002 — Comedy beats, loop design, science check

## Comedy beats (and the device behind each)
| Time (s) | Beat | Device |
|---|---|---|
| 0.0 | A silent, packed elevator. Everyone jolts at once and five different farts hit together | shock and absurd scale; the joke is understood with the sound off (title) |
| 0.6–2.9 | Three faces in a split screen, then the slow **side‑eye** while nobody moves. Elevator *ding* | awkward silence, mutual suspicion |
| 4.9–6.0 | Live‑TV anchor jolts, keeps a frozen smile on air, and his eye twitches | professional composure cracking |
| 6.1–7.5 | Wedding organ → the kiss → trumpet fart → the organ **tape‑stops** and the needle scratches | expectation break (sacred moment) |
| 10.2–13.2 | "The smell is just a **tiny** bit of sulfur gas." The polite guests try very hard to smile | understatement set‑up |
| 13.2–13.9 | "…**Tiny.**" Dead silence, a held stare | the pause before the punchline |
| 13.9–14.7 | All the guests faint like dominoes (speed ramp, three thuds) | punchline contradicts the narrator |
| 14.7–18.0 | Grave breaking news: "WHO FARTED FIRST?" + dun‑dun‑DUNNN | mock‑serious register |
| 18.0–21.4 | "Enhance. Enhance. ENHANCE!" on a blurry CCTV still | crime‑show parody |
| 22.2–23.0 | "One guy." Freeze frame + SUSPECT #1 | dramatic irony (it's our hero) |
| 23.0–27.8 | Grandma blamed → she blames the businessman → he blames the kid | rule‑of‑three escalation |
| 27.8–29.2 | The kid holds a long deadpan… then points at the mascot | the chain closes on the accuser (callback) |
| 29.2–31.6 | The mascot whistles innocently and sweats; "Farts aren't contagious." | guilty innocence |
| 31.6–32.7 | "But this one?" | the fiction admits it's fiction (wink) |
| 33.5–36.1 | "It all started… with one tiny…" *pfft* (the mascot's own puff) | the sentence is finished by a sound; Patient Zero reveal |

## Loop design
The story is circular: the ending **causes** the opening.
* **Picture:** E21 shows ELEV frames 0→76 of one continuous animation take. Its last video frame is
  frame 76, and video frame 0 (E01) is frame 77: the next frame of the same camera move. The
  mascot's tiny puff (f66) is still hanging in the air when everyone jolts at f77.
* **Words:** "It all started… with one tiny…" [pfft] → "Eight billion people just farted." The
  narration reads as one sentence across the seam.
* **Clock:** 3:13:59 PM on the last frame → 3:14:00 PM on frame 0.
* **Music:** the elevator muzak tape‑starts after the rewind. It's one continuous performance from
  33.55 s through the loop point to 0.12 s, where it tape‑stops, so it never restarts at the seam.
* **Mix:** built circularly (`"loop": true` in `audio/cues.json`). Anything that rings past 36.1 s
  (reverb, SFX tails) is folded onto 0 s, and the ducking, filters and limiter run as if the video
  had already played once. There is no fade at either end.
* **No frame‑0 flash:** removed during QA so the first frame reads instantly, both as a hook and on
  replay.

## Science: fact vs fiction
| Claim in the video | Status |
|---|---|
| "Farting is normal." Chip: `MOST PEOPLE: 13–21× A DAY` | **Fact.** Passing gas about 13–21 times a day is normal (NHS / Cleveland Clinic patient guidance). |
| "The smell is just a tiny bit of sulfur gas." | **Fact.** Most flatus is odourless gas (nitrogen, CO₂, hydrogen, methane). The smell comes from trace sulfur compounds such as hydrogen sulfide (MedlinePlus / gastroenterology reviews). |
| Guests fainting | **Fiction**, played as a slapstick contradiction of "tiny". The narration never says it's dangerous. |
| 8 billion people farting in the same second | **Fiction** (the premise). It's never described as explosive or poisonous. The video avoids those claims. |
| "Farts aren't contagious." | **Fact**, stated plainly. |
| "But this one?" | **Fiction**, openly flagged as a joke. |
| CCTV "enhance" | **Fiction / parody.** |
