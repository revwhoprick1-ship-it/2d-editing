# VIDEO_024 · The Taxi (built from the user's shot-by-shot blueprint) — 55.0 s

Export: `EXPORTS/VIDEO_024_The_Taxi_Final.mp4` (1080x1920, 30 fps). QA (`qa_inspector.py`): -14.6 LUFS, true peak -2.0 dBTP,
no black/frozen frames, Whisper transcript of the FINAL file: 14/16 lines exact, 2 near-misses ("backward" for "backwards";
"grab a wheel" for "grab the wheel" at x1.35 speed).
Files (blueprint names): `renderer.py` (2 camera setups in one fixed taxi: A looking back at you, B looking forward; vector dolly
/ pan / shake), `audio_synth.py` (JUMPSCARE_SLAM 140->30 Hz + HP noise, zero attack; BONE_SNAP wood-block + 8 kHz crunch; road,
tunnel, streetlight whoosh), `audio/place_lines.py` (every line at the blueprint's absolute time; tempo-fit when a line is longer
than its slot), `qa_inspector.py`. Music: continuous 55 Hz soft-clipped drone (`cue_video024`).
Deviations from the blueprint (forced): Impact font not available -> RobotoCondensed-Bold at y 1240; N12 ("One: Jump out...")
cannot fit 2.5 s -> placed backwards from the end at x1.35 so 'now' still ends at 54.9 s (CTA ~6.2 s, not 3 s); N10 sped up to
end at 42.4 s so the bone snap lands exactly at 42.5 s; captions moved to y 1480 during the ID-card shot so the card stays visible;
a short silence pocket (tunnel + drone ducked) under "We're home." so the pitched-down voice is understood.
Hidden details: dash clock 11:47; Bob's crumpled MISSING poster on the back-seat floor; the ID card number #1147.
