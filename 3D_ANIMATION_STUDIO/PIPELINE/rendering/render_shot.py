"""Build one shot of a video in a fresh Blender session, save its .blend and render frames.

    blender -b --factory-startup --python PIPELINE/rendering/render_shot.py -- \
        --video video001 --shot SH01 [--res 720x1280] [--samples 12] [--frames 1,60] \
        [--step 1] [--still 72] [--list 77,78,90] [--eevee use_raytracing=0] [--no-render] [--out DIR]

Frames go to VIDEOS/<VIDEO>/frames/<SHOT>/####.png (global frame numbers).
"""
import argparse
import importlib
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'blender_scripts'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'blender_scripts', 'videos'))

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--video', required=True)
ap.add_argument('--shot', required=True)
ap.add_argument('--res', default='720x1280')
ap.add_argument('--samples', type=int, default=12)
ap.add_argument('--frames', default=None)
ap.add_argument('--step', type=int, default=1)
ap.add_argument('--still', type=int, default=None)
ap.add_argument('--list', default=None, help='explicit comma list of frames (overrides range/step)')
ap.add_argument('--no-render', action='store_true')
ap.add_argument('--save-blend', action='store_true')
ap.add_argument('--out', default=None)
ap.add_argument('--eevee', default='', help='overrides, e.g. use_raytracing=0,use_fast_gi=0')
a = ap.parse_args(argv)

from studio_lib import render_setup as RS, scene_kit as SK

mod = importlib.import_module(a.video)
SK.clear_scene()
rx, ry = (int(v) for v in a.res.split('x'))
sc = RS.scene_defaults(res=(rx, ry), samples=a.samples, fps=30)
info = mod.build_shot(a.shot)
for kv in filter(None, a.eevee.split(',')):
    k, v = kv.split('=')
    setattr(sc.eevee, k, type(getattr(sc.eevee, k))(float(v)) if not isinstance(getattr(sc.eevee, k), str) else v)
f0, f1 = info['frames']
# CPU budget rule: only key lights cast shadows (deforming characters invalidate
# virtual shadow maps for every shadow-casting light, every sample)
for ld in bpy.data.lights:
    if not ld.name.startswith('Key'):
        ld.use_shadow = False
sc.frame_start, sc.frame_end = f0, f1 - 1
VID = mod.VIDEO_DIR
if a.save_blend:
    bdir = os.path.join(VID, 'blender')
    os.makedirs(bdir, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(bdir, f'{a.shot}.blend'), compress=True)
if a.no_render:
    print('BUILD_ONLY', a.shot, f0, f1)
    sys.exit(0)
out = a.out or os.path.join(VID, 'frames', a.shot)
os.makedirs(out, exist_ok=True)
step = a.step if a.step != 1 else info.get('step', 1)
frames = list(range(f0, f1, step))
if step > 1 and (f1 - 1) not in frames:
    frames.append(f1 - 1)
if a.frames:
    lo, hi = (int(v) for v in a.frames.split(','))
    frames = [f for f in frames if lo <= f <= hi]
if a.list:
    frames = sorted({int(v) for v in a.list.split(',')})
if a.still is not None:
    frames = [a.still]
t0 = time.time()
for f in frames:
    path = os.path.join(out, f'{f:04d}.png')
    if os.path.exists(path) and a.still is None:
        continue
    sc.frame_set(f)
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f'FRAME {a.shot} {f} {time.time() - t:.1f}s', flush=True)
print(f'SHOT_DONE {a.shot} {len(frames)} frames in {time.time() - t0:.0f}s', flush=True)
