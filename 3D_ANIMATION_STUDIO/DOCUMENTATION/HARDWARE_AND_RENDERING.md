# Hardware inspection & render decisions

## Machine this studio was built on (inspected 2026‑11‑06)
| Item | Value |
|---|---|
| OS | Ubuntu 24.04.5 LTS (cloud VM, KVM), kernel 6.18 |
| CPU | 4 × Intel Xeon @ 2.10 GHz (AVX‑512) |
| GPU | **None** (no CUDA/OptiX/HIP; OpenGL only through Mesa **llvmpipe** software rasteriser) |
| RAM | 15 GiB, no swap |
| Disk | ~31 GB free for the session |
| Blender | **5.2.3 LTS** (official linux‑x64 tarball, `/opt/tools/blender-5.2.3-linux-x64`, symlinked as `blender`) |
| Python | 3.13 system; **3.12 venv** for TTS/audio at `/opt/tools/tts312` (Kokoro needs < 3.13) |
| FFmpeg | 6.1.1 with libx264, libass, loudnorm/ebur128 |
| Video editors | None installed. Editing is scripted (`PIPELINE/editing/assemble.py` + FFmpeg). |
| Extra installs (all free / open source) | espeak‑ng, sox, Mesa EGL/GL drivers, PyTorch 2.15 CPU, kokoro 0.9.4, misaki, faster‑whisper, pyloudnorm, yt‑dlp |

## Render benchmarks (measured, not assumed)
| Test | Result |
|---|---|
| EEVEE, 1080×1920, simple scene, 16 TAA samples | 14–15 s/frame (steady state) |
| Cycles CPU, 720×1280, 24 spp + OIDN | 11–12 s/frame (simple scene) |
| **Real shot (SH02: ~260 cells, mascot, tunnel)**, EEVEE 540×960, 12 samples | 27.7 s/frame |
| same, 6 samples | 13.2 s |
| same, 6 samples, shadows only on key light, subdivision ≤ 1 | ≈ 11 s |
| same, Cycles 540×960 16 spp + OIDN | 55.9 s |
| same, EEVEE 720×1280, 6 samples, optimised | 17 s |
| Animatic preview 270×480, 2 samples | ≈ 5 s/frame (mostly fixed per‑frame cost: modifier evaluation + EEVEE sync) |
| One Blender instance | uses ≈ 1.9 of 4 cores, so **2 render workers run in parallel** |

## Decisions
* **EEVEE for previews and finals** on this machine. Cycles was 2–4× slower at equal resolution.
* **Final render: 540×960, 4 TAA samples, mild temporal denoise (ffmpeg hqdn3d) and upscale to 1080×1920** (Lanczos + light unsharp) at export. Native 1080 would take about 4× longer, roughly 15–20 h for a 57 s Short on this CPU. The export is a true 1080×1920 H.264 file, but its detail comes from a 540×960 render. **This is the biggest quality compromise in the project, and it is purely a hardware limit.**
* Measured on the final shots: 6 samples ≈ 12–33 s/frame and 4 samples ≈ 9.5–21 s/frame. **Only key lights cast shadows.** A deforming character invalidates the virtual shadow maps of every shadow‑casting light on every sample. Turning shadows off for fill, rim and glow lights cut SH07b from 21 s to 14 s.
* Per‑frame cost is reduced by: Simplify (subdivision ≤ 1 at render; the head and hands still get 1 level of smoothing), shadows on key lights only, half‑resolution shadow maps, material‑level distance fog instead of volumetrics, and procedural instancing of linked meshes.
* **On a machine with an NVIDIA/AMD GPU:** run the same scripts with `--res 1080x1920 --samples 16` (EEVEE) or switch `scene_defaults(engine='CYCLES')` for path‑traced finals. Nothing else changes.

## Free‑tool policy
Nothing paid was installed or called. Every library used is open source (Blender GPL, Kokoro Apache‑2.0 weights, PyTorch BSD, faster‑whisper MIT, FFmpeg LGPL/GPL, Montserrat OFL). Music and SFX are synthesised in‑house.
