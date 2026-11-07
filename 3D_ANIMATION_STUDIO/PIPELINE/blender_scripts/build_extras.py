"""Build supporting-cast characters.
    blender -b --factory-startup --python PIPELINE/blender_scripts/build_extras.py -- GRANDMA
Writes CHARACTER/extras/<name>.blend (collection <NAME>, rig <PREFIX>Rig)."""
import os, sys, bpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
name = sys.argv[sys.argv.index('--') + 1]
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)
from studio_lib import extras_build as EB
rig, col = EB.build_variant(name)
os.makedirs(os.path.join(ROOT, 'CHARACTER', 'extras'), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'CHARACTER', 'extras', name.lower() + '.blend'), compress=True)
print('EXTRA_OK', name, len(col.objects))
