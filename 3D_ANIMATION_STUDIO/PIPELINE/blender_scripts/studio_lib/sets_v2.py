"""Sets and comedy VFX for everyday-world videos (VIDEO_002+).

Built for render speed: only what the camera sees, low-poly where geometry is
flat, a single shadow-casting key light per set, emission for practical lights.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector, Euler, noise

from . import render_setup as RS
from .geo import obj_from_bm, tube_along, add_subsurf, quad_sphere
from .materials import hex_rgb, _node, _link, _ramp, _bump

STUDIO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))


def _mat(name, color, rough=0.5, metal=0.0, coat=0.0, emission=None, sheen=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = hex_rgb(color) if isinstance(color, str) else color
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Coat Weight'].default_value = coat
    p.inputs['Sheen Weight'].default_value = sheen
    if emission:
        p.inputs['Emission Color'].default_value = hex_rgb(emission[0])
        p.inputs['Emission Strength'].default_value = emission[1]
    return m


def box(name, size, loc, mat, bevel=0.0, col=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(loc)
    ob = obj_from_bm(name, bm, [mat], col, smooth=False)
    if bevel:
        b = ob.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = 2
    return ob


def plane(name, w, h, loc, rot, mat, col=None):
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(p)) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new('UVMap')
    for loop, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (u, v)
    ob = obj_from_bm(name, bm, [mat], col, smooth=False)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def image_material(name, path, emission=0.0, rough=0.4):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = rough
    if emission:
        nt.links.new(tex.outputs['Color'], p.inputs['Emission Color'])
        p.inputs['Emission Strength'].default_value = emission
    return m


# =========================================================================================== gas puffs
def puff_material():
    m = bpy.data.materials.get('VFX_Gas')
    if m:
        return m
    m = bpy.data.materials.new('VFX_Gas')
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    oi = _node(nt, 'ShaderNodeObjectInfo', (-700, 0))
    tc = _node(nt, 'ShaderNodeTexCoord', (-900, -300))
    nz = _node(nt, 'ShaderNodeTexNoise', (-700, -300))
    nz.inputs['Scale'].default_value = 3.0
    _link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    r = _ramp(nt, [(0.3, hex_rgb('#9CC24A')), (0.75, hex_rgb('#D8E87A'))], (-450, 200))
    _link(nt, nz.outputs['Fac'], r.inputs['Fac'])
    _link(nt, r.outputs['Color'], p.inputs['Base Color'])
    _link(nt, r.outputs['Color'], p.inputs['Emission Color'])
    p.inputs['Emission Strength'].default_value = 0.35
    p.inputs['Roughness'].default_value = 0.7
    mul = _node(nt, 'ShaderNodeMath', (-450, -100), operation='MULTIPLY')
    _link(nt, oi.outputs['Alpha'], mul.inputs[0])
    mul.inputs[1].default_value = 0.78
    _link(nt, mul.outputs[0], p.inputs['Alpha'])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        pass
    return m


def gas_puff(name, loc, size, f0, grow=7, hold=18, fade=14, drift=(0, 0.15, 0.25), seed=1, parent=None, lumps=7):
    """Cartoon gas cloud: lumpy spheres that pop out (overshoot), drift and fade."""
    rnd = random.Random(seed)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    if parent:
        root.parent = parent
    mat = puff_material()
    me = bpy.data.meshes.get('VFX_PuffMesh')
    if me is None:
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        for v in bm.verts:
            v.co *= 1.0 + 0.12 * noise.noise(v.co * 2.2)
        me = bpy.data.meshes.new('VFX_PuffMesh')
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(mat)
    for i in range(lumps):
        ob = bpy.data.objects.new(f'{name}_{i}', me)
        bpy.context.scene.collection.objects.link(ob)
        ob.parent = root
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 0.6), rnd.gauss(0, 0.8))).normalized() * size * rnd.uniform(0.2, 0.8)
        ob.location = d
        s = size * rnd.uniform(0.35, 0.65)
        ob.scale = (s, s, s)
        ob.color = (1, 1, 1, 1.0)
        ob.keyframe_insert('color', frame=f0 + grow + hold)
        ob.color = (1, 1, 1, 0.0)
        ob.keyframe_insert('color', frame=f0 + grow + hold + fade)
    root.location = loc
    root.scale = (0.01, 0.01, 0.01)
    root.keyframe_insert('scale', frame=f0)
    root.keyframe_insert('location', frame=f0)
    root.scale = (1.18, 1.18, 1.18)
    root.keyframe_insert('scale', frame=f0 + int(grow * 0.7))
    root.scale = (1.0, 1.0, 1.0)
    root.keyframe_insert('scale', frame=f0 + grow)
    root.scale = (1.25, 1.25, 1.25)
    root.location = Vector(loc) + Vector(drift)
    root.keyframe_insert('scale', frame=f0 + grow + hold + fade)
    root.keyframe_insert('location', frame=f0 + grow + hold + fade)
    # invisible before f0
    root.hide_render = True
    root.keyframe_insert('hide_render', frame=f0 - 1)
    root.hide_render = False
    root.keyframe_insert('hide_render', frame=f0)
    for c in root.children:
        c.hide_render = True
        c.keyframe_insert('hide_render', frame=f0 - 1)
        c.hide_render = False
        c.keyframe_insert('hide_render', frame=f0)
    return root


# =========================================================================================== elevator
def elevator():
    """Interior 2.0 (x) x 1.7 (y) x 2.3 (z); doorway (open) in the front wall at y=-0.85."""
    W, D, H = 2.0, 1.7, 2.3
    steel = _mat('SET_Steel', '#B9BEC4', 0.28, metal=0.9)
    steel_dark = _mat('SET_SteelDark', '#7C8188', 0.32, metal=0.9)
    wood = _mat('SET_Wood', '#7A4E2E', 0.45, coat=0.4)
    floor = _mat('SET_ElevFloor', '#2B2B30', 0.35, coat=0.3)
    light = _mat('SET_CeilLight', '#FFF4E0', 0.5, emission=('#FFF2DC', 6.0))
    btn = _mat('SET_Button', '#FFD27A', 0.3, emission=('#FFB84A', 3.0))
    disp = _mat('SET_Display', '#200808', 0.3, emission=('#FF5A2A', 4.0))
    obs = []
    obs.append(box('ELV_Floor', (W, D, 0.04), (0, 0, -0.02), floor))
    obs.append(box('ELV_Ceil', (W, D, 0.04), (0, 0, H + 0.02), steel_dark))
    obs.append(box('ELV_Back', (W, 0.04, H), (0, D / 2 + 0.02, H / 2), wood))
    # steel frame panels on the back wall
    for x in (-0.66, 0.0, 0.66):
        obs.append(box(f'ELV_BackPanel{x}', (0.58, 0.012, 1.9), (x, D / 2 - 0.005, 1.15), steel, bevel=0.01))
    for side in (-1, 1):
        obs.append(box(f'ELV_Side{side}', (0.04, D, H), (side * (W / 2 + 0.02), 0, H / 2), steel))
        obs.append(box(f'ELV_FrontWall{side}', (0.33, 0.06, H), (side * (W / 2 - 0.165), -D / 2 - 0.03, H / 2), steel_dark))
        # handrails
        bm = bmesh.new()
        tube_along(bm, [Vector((side * (W / 2 - 0.05), -0.6, 0.95)), Vector((side * (W / 2 - 0.05), 0.6, 0.95))],
                   [(0.018, 0.018)] * 2, segs=12)
        obs.append(obj_from_bm(f'ELV_Rail{side}', bm, [steel], None))
    bm = bmesh.new()
    tube_along(bm, [Vector((-0.85, D / 2 - 0.05, 0.95)), Vector((0.85, D / 2 - 0.05, 0.95))], [(0.018, 0.018)] * 2, segs=12)
    obs.append(obj_from_bm('ELV_RailBack', bm, [steel], None))
    obs.append(box('ELV_Header', (W, 0.06, 0.32), (0, -D / 2 - 0.03, H - 0.16), steel_dark))
    obs.append(box('ELV_LightPanel', (1.3, 0.9, 0.02), (0, 0.05, H - 0.012), light))
    obs.append(box('ELV_Display', (0.32, 0.02, 0.12), (0, D / 2 - 0.02, 2.08), disp))
    # button panel on the right side wall
    obs.append(box('ELV_ButtonPlate', (0.012, 0.22, 0.5), (W / 2 - 0.005, -0.55, 1.25), steel_dark))
    for i in range(8):
        r, c = divmod(i, 2)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.022, radius2=0.022, depth=0.01)
        for v in bm.verts:
            v.co = Vector((v.co.z, v.co.x, v.co.y)) + Vector((W / 2 - 0.012, -0.6 + c * 0.1, 1.42 - r * 0.1))
        obs.append(obj_from_bm(f'ELV_Btn{i}', bm, [btn], None))
    # outside: lobby wall around the doorway (seen from the camera outside)
    lobby = _mat('SET_Lobby', '#D9CDBF', 0.6)
    for side in (-1, 1):
        obs.append(box(f'ELV_Lobby{side}', (1.6, 0.05, 3.0), (side * (0.70 + 0.8), -D / 2 - 0.09, 1.5), lobby))
    obs.append(box('ELV_LobbyTop', (3.0, 0.05, 0.7), (0, -D / 2 - 0.09, H + 0.35), lobby))
    obs.append(box('ELV_LobbyFloor', (4.0, 3.0, 0.04), (0, -D / 2 - 1.5, -0.02), _mat('SET_LobbyFloor', '#C9C2B6', 0.25, coat=0.5)))
    key = RS.area_light('Key_Ceil', (0, 0.05, H - 0.05), (0, 0.05, 0), 260, 1.4, (1.0, 0.93, 0.84))
    key.data.shape = 'RECTANGLE'
    key.data.size, key.data.size_y = 1.3, 0.9
    fill = RS.area_light('Fill_Door', (0, -2.6, 1.5), (0, 0, 1.0), 220, 2.0, (0.92, 0.95, 1.0))
    fill.data.use_shadow = False
    RS.world_color((0.05, 0.05, 0.06), 0.4)
    return obs


ELEVATOR_SPOTS = {  # character -> (x, y, facing_deg)
    'MASCOT': (0.0, -0.10, 0),
    'GRANDMA': (-0.58, 0.30, 8),
    'BUSINESSMAN': (0.52, 0.42, -6),
    'KID': (0.66, -0.28, -12),
}


# =========================================================================================== news studio
def news_studio(screen_image=None):
    desk_m = _mat('SET_Desk', '#1E2C4E', 0.3, coat=0.6)
    desk_top = _mat('SET_DeskTop', '#2E4C86', 0.3, coat=0.5)
    wall = _mat('SET_StudioWall', '#0E1A33', 0.6)
    strip = _mat('SET_StudioStrip', '#4FA6FF', 0.4, emission=('#3E8EFF', 5.0))
    strip_r = _mat('SET_StudioStripRed', '#FF3B3B', 0.4, emission=('#FF2D2D', 4.0))
    floor = _mat('SET_StudioFloor', '#0A0F1C', 0.5, coat=0.2)
    obs = []
    # curved desk
    bm = bmesh.new()
    pts = [Vector((math.sin(a) * 1.1, -math.cos(a) * 0.55 + 0.1, 0.0)) for a in [math.radians(d) for d in range(-60, 61, 10)]]
    rings = []
    for z in (0.0, 0.92):
        rings.append([bm.verts.new(p + Vector((0, 0, z))) for p in pts])
    for i in range(len(pts) - 1):
        bm.faces.new((rings[0][i], rings[0][i + 1], rings[1][i + 1], rings[1][i]))
    desk = obj_from_bm('NEWS_Desk', bm, [desk_m], None, smooth=True)
    sol = desk.modifiers.new('Solidify', 'SOLIDIFY')
    sol.thickness = 0.06
    obs.append(desk)
    obs.append(box('NEWS_DeskTop', (2.1, 0.75, 0.04), (0, -0.25, 0.94), desk_top, bevel=0.01))
    obs.append(box('NEWS_Wall', (8, 0.1, 5), (0, 2.2, 2.5), wall))
    obs.append(box('NEWS_Floor', (8, 8, 0.04), (0, 0, -0.02), floor))
    for i, x in enumerate((-2.9, -2.4, 2.4, 2.9)):
        obs.append(box(f'NEWS_Strip{i}', (0.06, 0.04, 3.0), (x, 2.13, 1.9), strip))
    obs.append(box('NEWS_StripRed', (5.4, 0.04, 0.05), (0, 2.13, 0.4), strip_r))
    if screen_image:
        scr = image_material('NEWS_Screen', screen_image, emission=1.6)
        obs.append(plane('NEWS_ScreenPlane', 3.4, 1.9, (0, 2.12, 2.0), (0, 0, 0), scr))
        # plane faces -Y after rotation: flip normal by scaling
        obs[-1].scale.y = 1
    key = RS.area_light('Key_News', (-1.4, -2.4, 2.8), (0, 0.3, 1.4), 520, 1.8, (1.0, 0.95, 0.9))
    rim = RS.area_light('Rim_News', (1.6, 1.6, 2.6), (0, 0.3, 1.5), 700, 1.2, (0.55, 0.75, 1.0))
    fill = RS.area_light('Fill_News', (2.0, -2.0, 1.3), (0, 0.3, 1.3), 160, 2.0, (0.85, 0.9, 1.0))
    for l in (rim, fill):
        l.data.use_shadow = False
    RS.world_color((0.02, 0.03, 0.06), 1.0)
    return obs


# =========================================================================================== wedding
def wedding():
    grass = bpy.data.materials.new('SET_Grass')
    nt = grass.node_tree
    p = nt.nodes['Principled BSDF']
    tc = _node(nt, 'ShaderNodeTexCoord', (-800, 0))
    nz = _node(nt, 'ShaderNodeTexNoise', (-600, 0))
    nz.inputs['Scale'].default_value = 6.0
    _link(nt, tc.outputs['Object'], nz.inputs['Vector'])
    r = _ramp(nt, [(0.3, hex_rgb('#3F7E2E')), (0.7, hex_rgb('#6DAA45'))], (-350, 0))
    _link(nt, nz.outputs['Fac'], r.inputs['Fac'])
    _link(nt, r.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.8
    obs = [box('WED_Ground', (30, 30, 0.04), (0, 4, -0.02), grass)]
    white = _mat('SET_ArchWhite', '#F6F2EC', 0.4)
    bm = bmesh.new()
    pts = [Vector((math.cos(a) * 1.0, 0.6, 1.25 + math.sin(a) * 1.0)) for a in [math.radians(d) for d in range(0, 181, 10)]]
    pts = [Vector((1.0, 0.6, 0.0))] + pts + [Vector((-1.0, 0.6, 0.0))]
    tube_along(bm, pts, [(0.05, 0.05)] * len(pts), segs=12)
    obs.append(obj_from_bm('WED_Arch', bm, [white], None))
    rnd = random.Random(5)
    flower_cols = ['#FF8FB0', '#FFFFFF', '#FFC1D6', '#F45A8A', '#FFE3A1']
    fme = bpy.data.meshes.new('WED_Flower')
    fb = bmesh.new()
    bmesh.ops.create_icosphere(fb, subdivisions=2, radius=1.0)
    for v in fb.verts:
        v.co *= 1.0 + 0.18 * math.sin(5 * math.atan2(v.co.y, v.co.x))
    fb.to_mesh(fme)
    fb.free()
    for poly in fme.polygons:
        poly.use_smooth = True
    leaf = _mat('SET_Leaf', '#3E8A3A', 0.6)
    for i in range(70):
        a = math.radians(rnd.uniform(15, 165))
        c = Vector((math.cos(a) * 1.0, 0.6 + rnd.uniform(-0.08, 0.08), 1.25 + math.sin(a) * 1.0))
        ob = bpy.data.objects.new(f'WED_Fl{i}', fme)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = c + Vector((rnd.uniform(-0.07, 0.07), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.07, 0.07)))
        s = rnd.uniform(0.045, 0.085)
        ob.scale = (s, s, s * 0.8)
        ob.active_material = _mat(f'SET_Flower{i % len(flower_cols)}', flower_cols[i % len(flower_cols)], 0.5, sheen=0.4)
        ob.material_slots[0].link = 'OBJECT'
        ob.material_slots[0].material = _mat(f'SET_Flower{i % len(flower_cols)}', flower_cols[i % len(flower_cols)], 0.5, sheen=0.4)
    # background bushes / trees as soft blobs, kept out of focus by DOF
    for i in range(12):
        bmb = bmesh.new()
        quad_sphere(bmb, 4)
        r = rnd.uniform(0.8, 1.6)
        c = Vector((rnd.uniform(-7, 7), rnd.uniform(6, 10), r * 0.8))
        for v in bmb.verts:
            v.co = c + v.co.normalized() * r * (1 + 0.15 * noise.noise(v.co * 2 + c))
        ob = obj_from_bm(f'WED_Tree{i}', bmb, [leaf], None)
    RS.world_gradient((0.42, 0.62, 0.95), (0.82, 0.88, 0.95), (0.6, 0.7, 0.5), 1.0)
    sun = bpy.data.lights.new('Key_Sun', 'SUN')
    sun.energy = 3.2
    sun.angle = math.radians(6)
    sun.color = (1.0, 0.95, 0.86)
    so = bpy.data.objects.new('Key_Sun', sun)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(-35))
    fill = RS.area_light('Fill_Wed', (0, -4, 2), (0, 0, 1.2), 300, 4.0, (0.9, 0.95, 1.0))
    fill.data.use_shadow = False
    return obs


# =========================================================================================== globe
def globe(tex_path):
    m = bpy.data.materials.new('SET_Earth')
    nt = m.node_tree
    p = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(tex_path, check_existing=True)
    tc = _node(nt, 'ShaderNodeTexCoord', (-900, 0))
    _link(nt, tc.outputs['UV'], tex.inputs['Vector'])
    _link(nt, tex.outputs['Color'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.55
    p.inputs['Coat Weight'].default_value = 0.25
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0)
    e = bpy.context.object
    e.name = 'GLB_Earth'
    bpy.ops.object.shade_smooth()
    e.data.materials.append(m)
    # atmosphere: slightly larger shell, fresnel blue emission, additive-looking
    am = bpy.data.materials.new('SET_Atmos')
    nt = am.node_tree
    for n in list(nt.nodes):
        if n.type == 'BSDF_PRINCIPLED':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    lw = _node(nt, 'ShaderNodeLayerWeight', (-600, 0))
    lw.inputs['Blend'].default_value = 0.35
    em = _node(nt, 'ShaderNodeEmission', (-300, 100))
    em.inputs['Color'].default_value = hex_rgb('#6FB8FF')
    em.inputs['Strength'].default_value = 2.5
    tr = _node(nt, 'ShaderNodeBsdfTransparent', (-300, -100))
    mix = _node(nt, 'ShaderNodeMixShader', (-100, 0))
    pw = _node(nt, 'ShaderNodeMath', (-450, 0), operation='POWER')
    pw.inputs[1].default_value = 2.2
    _link(nt, lw.outputs['Facing'], pw.inputs[0])
    _link(nt, pw.outputs[0], mix.inputs['Fac'])
    _link(nt, tr.outputs[0], mix.inputs[1])
    _link(nt, em.outputs[0], mix.inputs[2])
    _link(nt, mix.outputs[0], out.inputs['Surface'])
    try:
        am.surface_render_method = 'BLENDED'
    except Exception:
        pass
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.045)
    a = bpy.context.object
    a.name = 'GLB_Atmos'
    bpy.ops.object.shade_smooth()
    a.data.materials.append(am)
    # stars
    rnd = random.Random(2)
    sm = _mat('SET_Star', '#FFFFFF', 0.5, emission=('#FFFFFF', 8.0))
    me = bpy.data.meshes.new('GLB_StarMesh')
    sbm = bmesh.new()
    bmesh.ops.create_icosphere(sbm, subdivisions=1, radius=1.0)
    sbm.to_mesh(me)
    sbm.free()
    me.materials.append(sm)
    for i in range(160):
        ob = bpy.data.objects.new(f'GLB_Star{i}', me)
        bpy.context.scene.collection.objects.link(ob)
        d = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        if d.y < -0.2:
            d.y = -d.y
        ob.location = d * rnd.uniform(25, 40)
        s = rnd.uniform(0.02, 0.07)
        ob.scale = (s, s, s)
    RS.world_color((0.005, 0.007, 0.02), 1.0)
    sun = bpy.data.lights.new('Key_GlobeSun', 'SUN')
    sun.energy = 4.0
    sun.color = (1.0, 0.97, 0.92)
    so = bpy.data.objects.new('Key_GlobeSun', sun)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = (math.radians(60), math.radians(10), math.radians(-40))
    return e, a


def latlon_to_vec(lat, lon, r=1.0):
    """Matches Blender's UV-sphere equirectangular mapping (u=0 at -X side)."""
    la, lo = math.radians(lat), math.radians(lon)
    return Vector((-math.cos(la) * math.cos(lo), -math.cos(la) * math.sin(lo), math.sin(la))) * r
