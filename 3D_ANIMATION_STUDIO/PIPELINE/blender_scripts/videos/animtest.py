"""Mascot animation test: walk-in (foot-planted IK), turn, wave + lip-synced line,
expression changes, jump (anticipation/landing), point, blinks.  9 s @ 30 fps.

Rendered with the same shot renderer as videos:
  render_video.sh animtest 540x960 6 1 CHARACTER/animations/anim_test/frames
"""
import json
import math
import os

import bpy
from mathutils import Vector

from studio_lib import scene_kit as SK, render_setup as RS, mascot_api as API
from studio_lib.materials import hex_rgb

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
VIDEO_DIR = os.path.join(STUDIO, 'CHARACTER', 'animations', 'anim_test')
SHOTS = {
    'T01': (1, 271),
}
VOICE_AT = 90


def stage():
    RS.world_gradient((0.30, 0.34, 0.42), (0.20, 0.22, 0.27), (0.08, 0.08, 0.10), 0.8)
    bpy.ops.mesh.primitive_plane_add(size=1)
    cyc = bpy.context.object
    cyc.name = 'Cyclorama'
    me = cyc.data
    import bmesh
    bm = bmesh.new()
    rows, cols = 24, 2
    verts = []
    for i in range(rows + 1):
        t = i / rows
        if t < 0.5:
            y, z = -6 + 12 * t, 0.0
        else:
            a = (t - 0.5) / 0.5 * math.pi / 2
            y, z = 3.0 + math.sin(a) * 2.0, (1 - math.cos(a)) * 2.0
            if t > 0.98:
                z = 6.0
        verts.append([bm.verts.new((x, y, z)) for x in (-8, 8)])
    for i in range(rows):
        bm.faces.new((verts[i][0], verts[i][1], verts[i + 1][1], verts[i + 1][0]))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    m = bpy.data.materials.new('Stage')
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = hex_rgb('#3B4A63')
    p.inputs['Roughness'].default_value = 0.55
    me.materials.append(m)
    RS.area_light('Key', (-2.5, -3.2, 3.2), (0, 0, 0.9), 650, 2.5, (1.0, 0.92, 0.85))
    f = RS.area_light('Fill', (3.0, -2.5, 1.4), (0, 0, 0.8), 220, 3.0, (0.8, 0.88, 1.0))
    r = RS.area_light('Rim', (1.5, 2.8, 2.4), (0, 0, 1.0), 700, 1.5, (1.0, 0.75, 0.55))
    f.data.use_shadow = False
    r.data.use_shadow = False


def build_shot(sid):
    f0, f1 = SHOTS[sid]
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = f0, f1 - 1
    sc.render.use_simplify = True
    sc.render.simplify_subdivision_render = 2
    stage()
    m, col = SK.append_mascot()
    # --- walk in (heading +X), feet planted
    end = API.walk(m, f0, f0 + 69, speed=1.0, cycle=30, start_pos=(-2.3, 0.0), heading_deg=90)
    # --- settle + turn to camera
    m.touched = set()
    m.reset(keep_root=True)
    m.loc('root', end[0], end[1], 0)
    m.rot('root', 0, 0, 90)
    m.key_all(f0 + 72)
    m.touched = set()
    m.loc('root', end[0], end[1], 0)
    m.rot('root', 0, 0, 0)
    m.loc('hips', 0, -0.03, 0)
    m.key(f0 + 84)
    m.touched = set(); m.loc('hips', 0, 0, 0); m.key(f0 + 90)
    def ex(f, name, w=1.0, eyes=(0, 0), head=None):
        m.touched = set()
        m.expression(name, w, keep_body=head is None)
        m.eyes(*eyes)
        m.key(f)
    ex(f0, 'neutral', eyes=(0.25, 0))
    ex(f0 + 60, 'curious', 0.6, eyes=(0.2, 0))
    ex(f0 + 82, 'happy', 1.0)
    # --- wave + lip-synced line
    API.wave(m, 'L', f0 + 84, cycles=4, period=10)
    m.touched = set(); m.arm('L', raise_=0, forward=0, elbow=0); m.hand('L', curl=0.0); m.key(f0 + 138)
    t = json.load(open(os.path.join(VIDEO_DIR, 'voice', 'timing.json')))
    API.lipsync(m, t['words'], fps=30, offset_frames=VOICE_AT, intensity=1.0,
                base_keys={'wide': 0.15})
    ex(f0 + 150, 'excited', 0.9)
    API.blink(m, f0 + 120, base_up=4)
    # --- jump
    API.jump(m, f0 + 168, height=0.35)
    ex(f0 + 172, 'surprised', 1.0)
    ex(f0 + 200, 'laughing', 0.9)
    # --- point up-right
    API.point_at(m, 'R', f0 + 212, raise_=70, forward=55, hold=40)
    ex(f0 + 214, 'excited', 1.0, eyes=(-0.25, 0.2))
    m.touched = set(); m.head_pose(-20, -10, 0); m.key(f0 + 218)
    API.blink(m, f0 + 236, base_up=6)
    ex(f1 - 1, 'happy', 1.0, eyes=(-0.2, 0.15))
    # --- camera
    cam, tgt = SK.cam_rig('Cam', lens=35, fstop=4.0)
    SK.key_cam(cam, tgt, f0, Vector((-0.8, -4.6, 1.2)), Vector((-1.4, 0, 0.85)), lens=35)
    SK.key_cam(cam, tgt, f0 + 75, Vector((0.2, -3.8, 1.15)), Vector((-0.05, 0, 0.9)), lens=40)
    SK.key_cam(cam, tgt, f0 + 150, Vector((0.25, -2.4, 1.15)), Vector((0, 0, 1.0)), lens=45)
    SK.key_cam(cam, tgt, f0 + 168, Vector((0.6, -4.2, 1.0)), Vector((0, 0, 0.9)), lens=35)
    SK.key_cam(cam, tgt, f1 - 1, Vector((0.9, -3.4, 1.2)), Vector((0.1, 0, 1.05)), lens=38)
    return {'frames': (f0, f1)}
