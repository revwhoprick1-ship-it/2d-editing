"""Project character head positions through each job's camera (no rendering).
    blender -b --factory-startup --python PIPELINE/rendering/annotate_v2.py -- video002 JOB [JOB...]
Appends to VIDEOS/<VIDEO>/gfx/annotations.json : {job: {frame: {char: [x, y]}}} (x,y in 0..1, y from top)."""
import importlib, json, os, sys, bpy
from bpy_extras.object_utils import world_to_camera_view
HERE = os.path.dirname(os.path.abspath(__file__)); STUDIO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'blender_scripts')); sys.path.insert(0, os.path.join(STUDIO, 'PIPELINE', 'blender_scripts', 'videos'))
argv = sys.argv[sys.argv.index('--') + 1:]
from studio_lib import scene_kit as SK, render_setup as RS
mod = importlib.import_module(argv[0])
path = os.path.join(mod.VIDEO_DIR, 'gfx', 'annotations.json')
data = json.load(open(path)) if os.path.exists(path) else {}
for job in argv[1:]:
    SK.clear_scene(); sc = RS.scene_defaults(res=(540, 960), samples=1)
    info = mod.build_shot(job); f0, f1 = info['frames']
    out = {}
    for f in sorted({f0, (f0 + f1) // 2, f1 - 1}):
        sc.frame_set(f)
        res = {}
        for ob in bpy.data.objects:
            if ob.type == 'ARMATURE' and 'head' in ob.pose.bones:
                head = [o for o in ob.children if o.name.split('_', 1)[-1].startswith('Head')]
                if head and head[0].hide_render:
                    continue
                pb = ob.pose.bones['head']
                p = ob.matrix_world @ (pb.head + (pb.tail - pb.head) * 0.42)
                v = world_to_camera_view(sc, sc.camera, p)
                res[ob.get('char_name', 'MASCOT')] = [round(v.x, 4), round(1 - v.y, 4), round(v.z, 3)]
        out[str(f)] = res
    data[job] = out
    print('ANNOT', job, out)
os.makedirs(os.path.dirname(path), exist_ok=True)
json.dump(data, open(path, 'w'), indent=1)
