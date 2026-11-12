"""Hybrid kit, Blender side (runs inside `blender -b --factory-startup --python <set script>`).

The FAST hybrid look (user's reference reels): the WORLD is a real 3D render, the CHARACTERS are flat 2D puppets.
CPU cloud = slow EEVEE, so a set script renders ONE overscanned still ("plate") per camera angle and writes plates.json
(camera matrix + focal length) so PIPELINE/hybrid/comp.py can project ANY 3D point onto the plate and do every move in 2D.

    from kit3d import *          # (sys.path must contain PIPELINE/hybrid)
    setup(samples=12); ... build with box/ball/cyl/prism ... ; plate('NAME', loc, target, lens=24, K=1.2, focus=(x,y,z))
    finish(out_dir)
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
OPT = dict(zip(ARGS[::2], ARGS[1::2]))
ONLY = set(OPT['--only'].split(',')) if '--only' in OPT else None
SC = None
_mats = {}
META = {}
INK = None


def hexc(h, a=1.0):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return (*[c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb], a)


def setup(samples=12, transparent=True, ambient='#140C1E', ambient_strength=1.0):
    """Empty scene, EEVEE, Standard view (flat toon colours), transparent film (the 2D sky goes behind)."""
    global SC, INK
    bpy.ops.wm.read_factory_settings(use_empty=True)
    SC = bpy.context.scene
    SC.render.engine = 'BLENDER_EEVEE'
    SC.eevee.taa_render_samples = int(OPT.get('--samples', samples))
    for attr, val in (('use_shadows', True), ('use_raytracing', False), ('use_gtao', True), ('shadow_resolution_scale', 0.5)):
        if hasattr(SC.eevee, attr):
            try:
                setattr(SC.eevee, attr, val)
            except Exception:
                pass
    SC.view_settings.view_transform = 'Standard'
    SC.render.film_transparent = transparent
    SC.render.image_settings.file_format = 'PNG'
    SC.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    SC.render.resolution_percentage = 100
    w = bpy.data.worlds.new('W'); SC.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = hexc(ambient)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = ambient_strength
    INK = bpy.data.materials.new('INK'); INK.use_nodes = True
    nt = INK.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = hexc('#0E0C1A'); nt.links.new(e.outputs[0], o.inputs['Surface'])
    INK.use_backface_culling = True
    return SC


def toon(name, col, shadow=0.40, mid=0.72, rim=0.0, emit=0.0):
    """Cel shading: light -> 3 flat bands x base colour -> Emission. emit>0: a flat glowing colour (lamps, windows)."""
    key = (name, col, shadow, mid, rim, emit)
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    if emit > 0:
        em.inputs['Color'].default_value = hexc(col); em.inputs['Strength'].default_value = emit
        nt.links.new(em.outputs[0], out.inputs['Surface'])
        _mats[key] = m
        return m
    diff = nt.nodes.new('ShaderNodeBsdfDiffuse')
    s2r = nt.nodes.new('ShaderNodeShaderToRGB')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    e = ramp.color_ramp.elements
    e[0].position, e[0].color = 0.0, (shadow * 0.85, shadow * 0.85, shadow * 1.15, 1)
    e[1].position, e[1].color = 0.5, (1.0, 1.0, 1.0, 1)
    e2 = e.new(0.12); e2.color = (mid, mid * 0.98, mid * 1.05, 1)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    mul.inputs['B'].default_value = hexc(col)
    nt.links.new(diff.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mul.inputs['A'])
    last = mul.outputs['Result']
    if rim > 0:
        fr = nt.nodes.new('ShaderNodeLayerWeight'); fr.inputs['Blend'].default_value = 0.25
        st = nt.nodes.new('ShaderNodeMath'); st.operation = 'GREATER_THAN'; st.inputs[1].default_value = 0.72
        nt.links.new(fr.outputs['Facing'], st.inputs[0])
        add = nt.nodes.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'
        nt.links.new(st.outputs[0], add.inputs['Factor']); nt.links.new(last, add.inputs['A'])
        add.inputs['B'].default_value = (0.25 * rim, 0.22 * rim, 0.45 * rim, 1)
        last = add.outputs['Result']
    nt.links.new(last, em.inputs['Color'])
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    _mats[key] = m
    return m


def holdout(name='HOLE'):
    """Window glass / openings: transparent in the render, so the 2D sky drawn behind the plate shows through."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); h = nt.nodes.new('ShaderNodeHoldout')
    nt.links.new(h.outputs[0], o.inputs['Surface'])
    _mats[name] = m
    return m


def ink(ob, w=0.02):
    """Inverted-hull black ink line around a mesh."""
    if ob.type != 'MESH' or w <= 0:
        return
    ob.data.materials.append(INK)
    sol = ob.modifiers.new('ink', 'SOLIDIFY')
    sol.thickness = w; sol.offset = 1.0; sol.use_flip_normals = True; sol.use_rim = False
    sol.material_offset = len(ob.data.materials) - 1


def _finish(ob, name, col, w, mat=None, coll=None, **kw):
    ob.name = name
    ob.data.materials.append(mat if mat is not None else toon(name, col, **kw))
    ink(ob, w)
    if coll:
        link(ob, coll)
    return ob


def _smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True


def box(name, loc, size, col, rot=(0, 0, 0), w=0.02, mat=None, coll=None, **kw):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    ob = bpy.context.object; ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return _finish(ob, name, col, w, mat, coll, **kw)


def ball(name, loc, scale, col, w=0.02, seg=24, mat=None, coll=None, **kw):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, segments=seg, ring_count=seg // 2)
    ob = bpy.context.object; ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); _smooth(ob)
    return _finish(ob, name, col, w, mat, coll, **kw)


def cyl(name, loc, r, depth, col, rot=(0, 0, 0), w=0.02, verts=16, mat=None, coll=None, **kw):
    bpy.ops.mesh.primitive_cylinder_add(location=loc, radius=r, depth=depth, rotation=rot, vertices=verts)
    ob = bpy.context.object; _smooth(ob)
    return _finish(ob, name, col, w, mat, coll, **kw)


def prism(name, loc, size, col, axis='y', w=0.02, mat=None, coll=None, **kw):
    """Gable roof: triangular prism, ridge along `axis`, size = (x, y, height)."""
    sx, sy, h = size[0] / 2, size[1] / 2, size[2]
    if axis == 'y':
        v = [(-sx, -sy, 0), (sx, -sy, 0), (0, -sy, h), (-sx, sy, 0), (sx, sy, 0), (0, sy, h)]
    else:
        v = [(-sx, -sy, 0), (-sx, sy, 0), (-sx, 0, h), (sx, -sy, 0), (sx, sy, 0), (sx, 0, h)]
    f = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (0, 2, 5, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    ob = bpy.data.objects.new(name, me); SC.collection.objects.link(ob); ob.location = loc
    return _finish(ob, name, col, w, mat, coll, **kw)


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in SC.collection.children:
        SC.collection.children.link(c)
    return c


def link(ob, coll):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)


def show(coll_name, on):
    c = bpy.data.collections.get(coll_name)
    if c:
        c.hide_render = not on


def light(kind, loc, col, energy, size=0.2, rot=None, target=None, coll=None, spot=None):
    bpy.ops.object.light_add(type=kind, location=loc)
    L = bpy.context.object
    L.data.color = hexc(col)[:3]; L.data.energy = energy
    if kind in ('POINT', 'SPOT'):
        L.data.shadow_soft_size = size
    if kind == 'AREA':
        L.data.size = size
    if kind == 'SPOT' and spot:
        L.data.spot_size = math.radians(spot)
        L.data.spot_blend = 0.4
    if target is not None:
        d = Vector(target) - Vector(loc); L.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    elif rot is not None:
        L.rotation_euler = [math.radians(a) for a in rot]
    if coll:
        link(L, coll)
    return L


def plate(name, loc, target, lens=24, K=1.2, focus=None, fstop=2.8, res=(1080, 1920), setup_fn=None, out_dir=None):
    """Render ONE still: camera at loc looking at target, K x overscanned (room for the 2D push-in), DOF on `focus` (a 3D point).
    Vertical sensor fit: fpx = lens / 24 * H."""
    if ONLY and name not in ONLY:
        return
    if setup_fn:
        setup_fn()
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_fit = 'VERTICAL'; cd.sensor_height = 24.0
    cd.clip_start = 0.05; cd.clip_end = 400
    cam = bpy.data.objects.new(name, cd); SC.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if focus is not None:
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = (Vector(focus) - Vector(loc)).length
    SC.camera = cam
    W, H = int(res[0] * K) // 2 * 2, int(res[1] * K) // 2 * 2
    SC.render.resolution_x, SC.render.resolution_y = W, H
    bpy.context.view_layer.update()
    SC.render.filepath = os.path.join(out_dir, f'{name}.png')
    bpy.ops.render.render(write_still=True)
    META[name] = dict(W=W, H=H, K=K, fpx=lens / 24.0 * H, mw=[list(r) for r in cam.matrix_world], lens=lens)
    print('PLATE_OK', name, W, H, flush=True)


def finish(out_dir):
    p = os.path.join(out_dir, 'plates.json')
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(META)
    json.dump(old, open(p, 'w'), indent=1)
    print('PLATES_DONE', len(META))
