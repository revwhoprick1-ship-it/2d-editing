# VIDEO_003 — What If ALL Drugs Became Legal?

≈33 s · 1080×1920 · 30 fps · seamless loop · export `EXPORTS/VIDEO_003_What_If_All_Drugs_Became_Legal.mp4`

## 1. Why viewers left VIDEO_002 (Instagram graph + YT 63.5 % stayed)
| Evidence | Diagnosis | Fix in VIDEO_003 |
|---|---|---|
| IG curve drops 100 % → ~70 % in the first ~3 s, then a slow, even slide to 33 % | the first 3 s didn't hook: frame 0 was a calm elevator (the puffs only appear on frame 4), the voice started 0.5 s late, and the 3‑way "eyes" split at 0.6 s was hard to read | frame 0 = mascot **already mid‑jump**, arms up, huge face, saturated pink, a 2‑line stamp `ALL DRUGS = LEGAL ✅`, and **voice on frame 0** |
| IG cover = the calm last frame ("WITH ONE TINY") | an empty grey elevator is the weakest still in the video | pick frame 0 (the jump + stamp) as the cover when uploading |
| "Mono, no emotion" voice (your note) | Kokoro af_heart: pitch range ≈ 9 semitones | **Chatterbox** (open source, free) with a male timbre (Kokoro am_fenrir), emotion knob per line: pitch range **17.6 semitones**, ≈2× more expressive |
| "Grainy" | EEVEE at 3 samples left fabric speckle | **1 sample + OpenImageDenoise**: clean, *and* 2× faster |
| Grey/brown elevator, desaturated AgX look | low vibrance | one loud colour per shot (pink, teal, purple, orange, green, red), Standard view transform + contrast look, +10 % saturation in render, +12 % in the edit grade |
| Comment rate 0.0 % | "comment 1, 2 or 3" was a quiz with no stake | an opinion question people actually argue about: `💬 WOULD THIS WORK IN YOUR COUNTRY?` |
| Slow, even decline after 3 s | jokes were spread out; long set‑ups (CCTV) | a joke every 2–3 s; each shot ≤ 4.8 s with a punch‑in on its punchline word |

## 2. Story
Concepts considered: (A) **"The New Normal"**: a montage of absurd consequences, then a real‑world twist (Portugal), then a responsible turn and a phone punchline; (B) the mascot opens a legal shop (too much 3D, and it glamorises); (C) a news countdown (a VIDEO_002 repeat). **A won**: the most jokes per second, the cheapest to render, and the most surprising twist.

v1 had "your grandma already has a dealer" (weak), no fact, and no safety line. v2 (final) adds the real
twist (Portugal 2001), a hard "legal ≠ safe" beat played as a joke (the cough fit), and a loop
punchline that turns the topic back on the viewer: the most addictive legal thing is the phone in
their hand.

| # | Line | Picture | Joke device |
|---|---|---|---|
| L01 | Every drug on Earth just became legal. | mascot mid‑jump, `ALL DRUGS = LEGAL ✅` | shock + celebration (frame 0) |
| L02–03 | Your grandma didn't even notice. She's already on fourteen prescriptions. | grandma deadpan behind a mountain of pill bottles, counter 0 → 14 | understatement → punch‑in |
| L04 | Drug dealers? Unemployed overnight. | dealer with a `WILL SELL OREGANO 4 FOOD` sign, `UNEMPLOYED` stamp | sad trombone |
| L05 | This guy just changed his LinkedIn to freelance pharmacist. | he beams; LinkedIn‑blue `💼 FREELANCE PHARMACIST` | corporate glow‑up |
| L06 | And the cartels went bankrupt and started a podcast. | two cartel guys at podcast mics, `CARTEL CAST · EP.1: 'WE'RE PIVOTING'` | out‑of‑pocket escalation |
| L07 | But here's the twist. | freeze + record scratch + silence | pattern break |
| L08–09 | Portugal decriminalized every drug back in 2001. Drug deaths went down. Nobody turned into a zombie. | globe dives to Portugal; the mascot plays a zombie, then snaps back to normal | real fact used as the surprise |
| L10 | Still, legal doesn't mean safe. Cigarettes are legal. Ask your lungs. | `⚠️ LEGAL ≠ SAFE`, coughing fit | safety line delivered as a joke |
| L11–12 | So what's the most addictive thing left on Earth? It's legal. It's free. And it's in your hand right now. | mascot glued to his phone | turn on the viewer |
| L13 | That's why you're about to watch this again. | he looks up at us, then the jump → **loop** | self‑aware loop |

**Hook test:** H1 "What if all drugs became legal?" (a question, slow) = 17; H2 "Every drug on Earth just became legal." + jump + stamp = **23**; H3 "Your grandma's dealer just got promoted." (confusing cold) = 16. **H2 chosen.**

## 3. Facts vs fiction
* **Fact:** Portugal decriminalized personal possession of all drugs in 2001 (Law 30/2000; *decriminalized*, not legalized; selling stayed illegal). Drug‑related deaths and HIV infections among people who use drugs fell substantially in the following years (EMCDDA, *Drug Policy Profiles: Portugal*; Transform/Cato reports).
* **Fact:** legal ≠ safe (tobacco is legal and is the leading preventable cause of death).
* **Fiction:** everything else (worldwide legalisation, the LinkedIn dealer, the cartel podcast). Nothing in the video says how to get, take or dose anything, and no drug use is shown.

## 4. Engagement (as jokes, spaced, none in the loop zone)
LIKE 9.8 s `👍 LIKE = ENDORSE HIS SKILLS` · SUBSCRIBE 11–14.7 s ticker `SUBSCRIBE TO CARTEL CAST? NO. SUBSCRIBE TO THIS CHANNEL.` · COMMENT 20.6–25.2 s `💬 WOULD THIS WORK IN YOUR COUNTRY?` · SHARE 29.5 s `📤 SEND TO SOMEONE GLUED TO THEIRS`.
**Pinned comment:** "Portugal did it in 2001. Would your country survive it? 👀"

## 5. Narrator
`PIPELINE/tts/narrate_chatterbox.py`: Chatterbox TTS (MIT licence, CPU). The voice timbre comes from a
Kokoro am_fenrir clip (Apache‑2.0), and each line has its own emotion setting. Every line was
generated twice and the take with the best Whisper word match won. The lines are tempo‑tightened
×1.12 (pitch kept), and the timing comes from Whisper word timestamps.

## Rebuild
```bash
/opt/tools/cbx/bin/python PIPELINE/tts/narrate_chatterbox.py VIDEOS/VIDEO_003/script.json VIDEOS/VIDEO_003/audio/narration
python3 VIDEOS/VIDEO_003/gfx/make_gfx.py
/opt/tools/tts312/bin/python PIPELINE/audio/sfx_comedy.py AUDIO
/opt/tools/tts312/bin/python PIPELINE/audio/music_gen.py video003 VIDEOS/VIDEO_003/audio/music_score.wav
/opt/tools/tts312/bin/python VIDEOS/VIDEO_003/audio/build_cues.py && /opt/tools/tts312/bin/python PIPELINE/audio/mix.py VIDEOS/VIDEO_003/audio/cues.json
python3 PIPELINE/rendering/render_needed.py VIDEOS/VIDEO_003/edit_video003.py video003 --out VIDEOS/VIDEO_003/frames \
    --res 540x960 --samples 1 --eevee use_raytracing=0 --extra="--denoise --vivid 0.1" --lanes 2
python3 PIPELINE/editing/edl_engine.py VIDEOS/VIDEO_003/edit_video003.py --frames VIDEOS/VIDEO_003/frames \
    --out EXPORTS/VIDEO_003_What_If_All_Drugs_Became_Legal.mp4 --audio VIDEOS/VIDEO_003/audio/mix_master.wav --crf 18
python3 PIPELINE/quality_control/qc_video.py EXPORTS/VIDEO_003_What_If_All_Drugs_Became_Legal.mp4 --out VIDEOS/VIDEO_003/qc
python3 PIPELINE/quality_control/loop_test.py EXPORTS/VIDEO_003_What_If_All_Drugs_Became_Legal.mp4 --out VIDEOS/VIDEO_003/qc
```
Render, QA and timing results: see `RENDER_QA.md`.
