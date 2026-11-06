"""Render turnaround views and the 12-expression sheet of the rigged mascot.

    blender -b CHARACTER/mascot_rig.blend --python PIPELINE/blender_scripts/render_character_sheets.py -- <outdir> [quick]
"""
import os, sys, math, bpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from studio_lib import render_setup as RS, mascot_api as API
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OUT = os.path.abspath(args[0]) if args else os.path.join(HERE, '..', '..', 'CHARACTER', 'reference_sheets')
QUICK = 'quick' in args
os.makedirs(OUT, exist_ok=True)
sc = RS.scene_defaults(res=(900, 1600), samples=8 if QUICK else 24)
RS.world_gradient((0.32, 0.36, 0.42), (0.22, 0.24, 0.28), (0.10, 0.10, 0.12), 0.7)
# studio floor (soft cyclorama)
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new('Floor'); p = fm.node_tree.nodes['Principled BSDF']
p.inputs['Base Color'].default_value = (0.16, 0.17, 0.19, 1); p.inputs['Roughness'].default_value = 0.6
floor.data.materials.append(fm)
RS.three_point(target=(0, 0, 0.85), key=230)
m = API.Mascot()
m.reset(keep_root=False)
m.hand('L', curl=0.15); m.hand('R', curl=0.15)
m.arm('L', raise_=-8); m.arm('R', raise_=-8)
cam = RS.camera('Cam', (0, -4.2, 0.80), (0, 0, 0.78), lens=50)
sc.camera = cam
views = {'front': 0, 'three_quarter': 35, 'side': 90, 'back': 180}
rig = bpy.data.objects['MSC_Rig']
for name, ang in views.items():
    m.pb['root'].rotation_euler = (0, 0, math.radians(-ang))
    sc.render.filepath = os.path.join(OUT, f'mascot_{name}.png')
    bpy.ops.render.render(write_still=True)
m.pb['root'].rotation_euler = (0, 0, 0)
# expression close-ups
sc.render.resolution_x, sc.render.resolution_y = 640, 640
cam.location = (0.12, -0.95, 1.17); RS.look_at(cam, (0, 0, 1.15)); cam.data.lens = 62
for ex in ['neutral'] + [e for e in API.EXPRESSIONS if e != 'neutral']:
    m.expression(ex)
    sc.render.filepath = os.path.join(OUT, '..', 'expressions', f'exp_{ex}.png')
    bpy.ops.render.render(write_still=True)
print('SHEETS_DONE')
