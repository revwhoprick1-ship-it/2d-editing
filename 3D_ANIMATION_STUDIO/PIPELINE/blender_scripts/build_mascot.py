"""Build the permanent mascot asset files.

    blender -b --factory-startup --python PIPELINE/blender_scripts/build_mascot.py

Writes CHARACTER/mascot.blend (model only) and CHARACTER/mascot_rig.blend
(model + armature + weights + facial shape keys + expression/animation actions).
"""
import os, sys, bpy
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
from studio_lib import mascot_build as MB, mascot_rig as MR

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
parts, M = MB.build_all('MASCOT')
col = bpy.data.collections['MASCOT']
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'CHARACTER', 'mascot.blend'), compress=True)
rig = MR.rig_mascot(parts, col)
try:
    from studio_lib import mascot_api as API
    API.store_library_actions(rig)
except ImportError:
    pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'CHARACTER', 'mascot_rig.blend'), compress=True)
print('MASCOT_BUILD_OK', len(col.objects), 'objects')
