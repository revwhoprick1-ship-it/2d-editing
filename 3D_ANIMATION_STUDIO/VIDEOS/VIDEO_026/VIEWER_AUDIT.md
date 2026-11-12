# VIEWER_MODE_AGENT — audit of the blueprint (simulated viewer, not real analytics)

Persona: bored 1 AM scroller, 1.5 s attention, zero creator bias. Benchmarks: Bus (139.23 % start, 78.39 % avg, 45.60 % left at 99 %),
Grandma (−9.51 % at 29–40 % from a tension reset; −29.30 % in the last 10 % from a long 3-choice outro).
Score = 10 − mean SWIPE_RISK/10 − 0.1 per window that fails VISUAL_CHANGE_RATE (a change at least every 1.5–2.0 s).

| # | Window | Baseline beat | SWIPE | CUR | VIS | Problem | SWIPE after |
|---|---|---|---|---|---|---|---|
| 1 | 0.0–3.5 | slam, phone, whip-pan, two-shot | 14 % | 9 | ok | banner / voice / title = 3 different texts; paradox spoken only by 4.5 s | 6 % |
| 2 | 3.5–7.0 | "twenty minutes", photo loading bar | 18 % | 8 | ok | 1.5 s of loading bar; line only describes the picture | 7 % |
| 3 | 7.0–10.5 | macro zoom on the photo | 9 % | 9 | ok | – | 6 % |
| 4 | 10.5–14.0 | "your throat", Mascot whispers | 13 % | 8 | FAIL | 3 s static close-up | 6 % |
| 5 | 14.0–17.5 | profile, head snap | 5 % | 9 | ok | 10-word line cannot fit in 1.07 s | 4 % |
| 6 | 17.5–21.0 | knocks, whip to the door | 10 % | 9 | ok | narrator repeats the picture | 6 % |
| 7 | 21.0–24.5 | dolly, real Bob | 16 % | 8 | FAIL | 2 s of empty dolly; 13-word setup | 6 % |
| 8 | 24.5–28.0 | "hunts by sound", TV | 8 % | 9 | ok | – | 6 % |
| 9 | 28.0–31.5 | TV: couch empty | 19 % | 8 | FAIL | 4.5 s on a still TV, action pauses | 6 % |
| 10 | 31.5–35.0 | delay badge, crawl | 15 % | 9 | ok | a delayed feed cannot show "empty" first and the crawl after | 6 % |
| 11 | 35.0–38.5 | "5 seconds ago", sneakers, ring | 10 % | 9 | ok | line repeats the label | 6 % |
| 12 | 38.5–42.0 | ankle grab, then he looks back | 17 % | 8 | ok | the grab is dropped = tension reset | 6 % |
| 13 | 42.0–45.5 | the face unzips | 3 % | 10 | ok | – | 3 % |
| 14 | 45.5–49.0 | mimic whisper | 14 % | 8 | FAIL | one 7 s close-up | 6 % |
| 15 | 49.0–52.5 | "Bob kicked the door" | 18 % | 9 | FAIL | told, not shown | 6 % |
| 16 | 52.5–56.0 | CTA | 20 % | 8 | ok | 14 words in 3 s cannot be spoken | 9 % |

Baseline: mean 13.1 %, 5 fails -> **8.2 / 10**. After upgrades: mean 5.9 %, 0 fails -> **9.4 / 10**.

## Dialogue upgrades
1. Hook = the title: "Bob just texted you: Don't open the door." / "But Bob is sitting right next to you." / "For the last twenty minutes."
   Banner on the phone says the same words. Bob is on screen at 0.9 s.
2. "He sends a live photo." -> "Then he sends a photo... of your living room." (loading bar done in 0.6 s)
3. "...but his throat plays a recording—" -> "His lips don't move. His throat does—" SNAP
4. "It's the real Bob outside. He presses a warning against the glass:" -> "The real Bob. He holds up his phone:"
5. Twist: "The TV switches to your security feed." / "On screen, it climbs over the couch and drops behind you." /
   "Then you see the corner: five-second delay." / "It's been behind you for five seconds."
6. "Then the thing calls your phone—just to make it ring." -> "You hold your breath." (ring) "So it calls your phone."
7. CTA: "One: smash the phone. Two: hide. Three: run. Comment now."

## Visual micro-reveals
- 11.0 s the live photo moves: its head turns to the lens.
- 13.0 s Bob's fingers walk across the cushion while you whisper.
- 20.2 s lightning: a silhouette behind the frosted glass; the handle rattles.
- 29–31 s on the feed it climbs over the backrest.
- 34.3 s the real couch: empty dented seat, four red dots rise behind your shoulder.
- 40.5 s the ankle stays grabbed: the camera is tugged down while it rises.
- 47–49 s tendrils enter the frame; a cracked lens drops.
- 50.5 s whip to the hallway: the door flies open, Bob has a long shadow; half of the split face turns to the noise.
- Loop: the hand lifts the phone into the frame-0 pose; 55 Hz drone = 3080 whole cycles in 56 s; swell into the frame-0 slam.

## Logic holes closed
- Feed-delay order. TV already on (it "switches"). Phone clock 12:07 vs wall clock stuck at 11:47 = the twenty minutes.
- Bob pounds on purpose: he makes himself the loudest thing, so it leaves the couch toward him ("it hunts by sound").
