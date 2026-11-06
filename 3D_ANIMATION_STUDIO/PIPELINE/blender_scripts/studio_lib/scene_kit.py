"""Shot-building helpers: mascot import, cameras with targets, shake, lights, world."""
import math
import os
import random
import bpy
from mathutils import Vector, Euler

from . import render_setup as RS
from .mascot_api import Mascot, _fcurves

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
MASCOT_RIG = os.path.join(STUDIO, 'CHARACTER', 'mascot_rig.blend')


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.actions, bpy.data.cameras, bpy.data.lights,
                bpy.data.metaballs, bpy.data.textures, bpy.data.armatures):
        for d in list(blk):
            if d.users == 0:
                blk.remove(d)


def append_mascot(path=MASCOT_RIG):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = ['MASCOT']
    col = dst.collections[0]
    bpy.context.scene.collection.children.link(col)
    rig = [o for o in col.objects if o.type == 'ARMATURE'][0]
    head = [o for o in col.objects if o.name.startswith('MSC_Head')][0]
    m = Mascot(rig, head)
    m.reset(keep_root=False)
    if rig.animation_data:
        rig.animation_data.action = None
    return m, col


def set_shoe_visible(col, side, shoe_visible, frame=None):
    """Swap sneaker <-> sock (used when the shoe gets lost)."""
    for o in col.objects:
        if o.name.startswith(f'MSC_Shoe_{side}'):
            o.hide_render = not shoe_visible
            o.hide_viewport = not shoe_visible
            if frame is not None:
                o.keyframe_insert('hide_render', frame=frame)
        if o.name.startswith(f'MSC_Sock_{side}'):
            o.hide_render = shoe_visible
            o.hide_viewport = shoe_visible
            if frame is not None:
                o.keyframe_insert('hide_render', frame=frame)


def cam_rig(name, lens=35.0, fstop=None, focus=None, sensor=36.0):
    tgt = bpy.data.objects.new(name + '_target', None)
    bpy.context.scene.collection.objects.link(tgt)
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.02
    cd.clip_end = 400
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        cd.dof.focus_object = focus or tgt
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    tr = cam.constraints.new('TRACK_TO')
    tr.target = tgt
    tr.track_axis = 'TRACK_NEGATIVE_Z'
    tr.up_axis = 'UP_Y'
    bpy.context.scene.camera = cam
    return cam, tgt


def key_cam(cam, tgt, frame, loc, look, lens=None, roll=None):
    cam.location = loc
    cam.keyframe_insert('location', frame=frame)
    tgt.location = look
    tgt.keyframe_insert('location', frame=frame)
    if lens is not None:
        cam.data.lens = lens
        cam.data.keyframe_insert('lens', frame=frame)


def shake(obj, f0, f1, amp=0.05, freq=0.35, seed=1, decay=True, data_path='location'):
    """Bake a handheld/impact shake as added keyframes on an object's location."""
    rnd = random.Random(seed)
    base = {}
    ad = obj.animation_data
    for f in range(f0, f1 + 1):
        bpy.context.scene.frame_set(f)
        k = (1.0 - (f - f0) / max(1, f1 - f0)) if decay else 1.0
        off = Vector((math.sin(f * freq * 6.1 + seed) + rnd.uniform(-0.4, 0.4),
                      math.sin(f * freq * 4.3 + seed * 2) * 0.6,
                      math.sin(f * freq * 5.7 + seed * 3) + rnd.uniform(-0.4, 0.4))) * amp * k
        obj.location = obj.matrix_basis.translation + off if False else obj.location + off
        obj.keyframe_insert('location', frame=f)
        obj.location -= off


def ease_all(obj, interp='BEZIER'):
    ad = obj.animation_data
    if ad and ad.action:
        for fc in _fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def fog_world(color, strength=1.0):
    w = RS.world_color(color, strength)
    return w
