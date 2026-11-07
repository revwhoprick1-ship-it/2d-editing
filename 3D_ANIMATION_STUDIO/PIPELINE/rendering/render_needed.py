#!/usr/bin/env python3
"""Render only the source frames an edit actually shows, in parallel lanes.

    python3 PIPELINE/rendering/render_needed.py VIDEOS/VIDEO_002/edit_video002.py video002 \
        --out VIDEOS/VIDEO_002/frames --res 540x960 --samples 3 --eevee use_raytracing=0 --lanes 2 [--dry]

How: the EDL is walked at 30 fps through the same compositor the final edit uses
(edl_engine.Editor.base), recording every (job, frame) it asks for.  Holds,
freeze frames and speed ramps therefore cost only the frames they show; frames a
cut skips are never rendered.  Jobs the shot module marks as "on twos" (STEP) are
snapped to even frames and blended by the editor.  Lanes are balanced by frame
count x a per-job cost weight; each job's per-frame time goes to the log.
"""
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
import threading
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'editing'))
import edl_engine as EE  # noqa: E402


def needed(edl_path, steps):
    spec = importlib.util.spec_from_file_location('edl', edl_path)
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    req = {}

    class Rec(EE.Frames):
        def get(self, job, fr):
            st = steps.get(job, 1)
            s = req.setdefault(job, set())
            if abs(fr - round(fr)) < 0.05:
                f = int(round(fr))
                s.add(f if st == 1 else int(round(f / st) * st))
            else:
                lo, hi = math.floor(fr), math.ceil(fr)
                if st > 1:
                    lo, hi = math.floor(fr / st) * st, math.ceil(fr / st) * st
                s.update((lo, hi))
            return np.zeros((8, 8, 3), np.float32)

    ed = EE.Editor.__new__(EE.Editor)
    ed.E = E
    ed.F = Rec('')
    EE.crop_resize = lambda img, w, h, *a, **k: np.zeros((h, w, 3), np.float32)
    for i in range(int(round(E.DURATION * E.FPS))):
        ed.base(i / E.FPS)
    return {j: sorted(v) for j, v in req.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('edl')
    ap.add_argument('video')
    ap.add_argument('--out', required=True)
    ap.add_argument('--res', default='540x960')
    ap.add_argument('--samples', type=int, default=3)
    ap.add_argument('--eevee', default='')
    ap.add_argument('--lanes', type=int, default=2)
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'blender_scripts', 'videos'))
    src = open(os.path.join(STUDIO, 'PIPELINE', 'blender_scripts', 'videos', a.video + '.py')).read()
    ns = {}
    exec(src.split('def key(')[0].split('import bpy')[0] if False else '', ns)
    # STEP / SHOTS are plain literals in the shot module: read them without importing bpy
    import ast
    tree = ast.parse(src)
    lit = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('STEP', 'SHOTS'):
            try:
                lit[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                pass
    steps = lit.get('STEP', {})
    shots = lit.get('SHOTS', {})
    need = needed(a.edl, steps)
    rx, ry = (int(v) for v in a.res.split('x'))
    total = 0
    plan = []
    for job, frames in sorted(need.items()):
        todo = [f for f in frames if not os.path.exists(os.path.join(a.out, job, f'{f:04d}.png'))]
        scale = shots.get(job, (None,) * 5)[4] if job in shots else 1.0
        cast = shots.get(job, (None, None, None, 'all'))[3]
        w = (len(todo) * (0.5 + scale ** 2 * (1.0 if cast == 'all' else 0.7))) if todo else 0
        plan.append((w, job, frames, todo))
        total += len(frames)
        print(f'NEED {job:14s} {len(frames):3d} frames ({len(todo)} to render)  {frames[0]}-{frames[-1]}')
    print('NEED_TOTAL', total, 'frames;', sum(len(p[3]) for p in plan), 'to render')
    json.dump({j: f for _, j, f, _ in plan}, open(os.path.join(os.path.dirname(a.edl), 'needed_frames.json'), 'w'), indent=0)
    if a.dry:
        return
    lanes = [[] for _ in range(a.lanes)]
    loads = [0.0] * a.lanes
    for w, job, frames, todo in sorted(plan, reverse=True):
        if not todo:
            continue
        k = loads.index(min(loads))
        lanes[k].append((job, todo))
        loads[k] += w
    log_path = os.path.join(a.out, 'render_log.jsonl')
    os.makedirs(a.out, exist_ok=True)
    lock = threading.Lock()

    def run(lane_id, jobs):
        for job, todo in jobs:
            t0 = time.time()
            cmd = ['nice', '-n', '5', 'blender', '-b', '--factory-startup', '--python',
                   os.path.join(STUDIO, 'PIPELINE', 'rendering', 'render_shot.py'), '--', '--video', a.video, '--shot', job,
                   '--res', a.res, '--samples', str(a.samples), '--list', ','.join(map(str, todo)),
                   '--out', os.path.join(a.out, job)]
            if a.eevee:
                cmd += ['--eevee', a.eevee]
            r = subprocess.run(cmd, capture_output=True, text=True)
            dt = time.time() - t0
            ok = 'SHOT_DONE' in r.stdout
            with lock:
                rec = dict(lane=lane_id, job=job, frames=len(todo), secs=round(dt, 1), per_frame=round(dt / len(todo), 2), ok=ok)
                open(log_path, 'a').write(json.dumps(rec) + '\n')
                print('JOB', json.dumps(rec), flush=True)
                if not ok:
                    print(r.stdout[-2000:], r.stderr[-2000:], flush=True)
    t0 = time.time()
    th = [threading.Thread(target=run, args=(i, l)) for i, l in enumerate(lanes)]
    [x.start() for x in th]
    [x.join() for x in th]
    print(f'ALL_DONE {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
