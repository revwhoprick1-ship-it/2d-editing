"""TEST_3D — real 3D render in the "2.5D ink" look (toon-shaded 3D + black ink outlines), 10 s, 1080x1920, 30 fps.

    blender -b --factory-startup --python VIDEOS/TEST_3D/scene3d.py -- [--frames 0,300] [--still 60] [--res 1080x1920] [--samples 8]

Everything is built here from primitives (no assets):
  * toon material: Diffuse -> Shader-to-RGB -> 3-step colour ramp (shadow / mid / lit) x base colour -> Emission  (+ rim light term)
  * ink outline: inverted hull (Solidify, flipped normals, black, backface culling) on every mesh
  * the mascot: big round head, simple face (white eyes, black pupils, brows, mouth), brown hair cap, orange shirt, jeans
  * the hallway (same layout as the 2D test): basement door on the right wall, photos + side table + lamp on the left,
    moonlit window, runner rug; indigo palette, warm lamp, lavender moon
  * 3 cameras switched by timeline markers: A dolly down the hall (0-4.2 s), B face close-up (4.2-7.2 s), C push to the door + key.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
opt = dict(zip(argv[::2], argv[1::2]))
RES = tuple(int(v) for v in opt.get('--res', '1080x1920').split('x'))
SAMPLES = int(opt.get('--samples', '8'))
FPS = 30
F_A, F_B, F_C, F_END = 0, 126, 216, 300

# ----------------------------------------------------------------------------------------------- scene + render
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = RES
sc.render.resolution_percentage = 100
sc.render.fps = FPS
sc.frame_start, sc.frame_end = F_A, F_END
sc.eevee.taa_render_samples = SAMPLES
for attr, val in (('use_shadows', True), ('use_raytracing', False), ('use_gtao', True), ('shadow_resolution_scale', 0.5)):
    if hasattr(sc.eevee, attr):
        try:
            setattr(sc.eevee, attr, val)
        except Exception:
            pass
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'
world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.02, 0.05, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0


def hexc(h, a=1.0):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


_mats = {}


def toon(name, col, shadow=0.38, mid=0.72, rim=0.0, emit=0.0):
    """Cel shading: light -> 3 flat bands, multiplied with the base colour, output as Emission (flat, graphic)."""
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
    e[0].position, e[0].color = 0.0, (shadow * 0.85, shadow * 0.85, shadow * 1.15, 1)      # cool shadow
    e[1].position, e[1].color = 0.5, (1.0, 1.0, 1.0, 1)
    e2 = e.new(0.12); e2.color = (mid, mid * 0.98, mid * 1.05, 1)
    mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    mul.inputs['B'].default_value = hexc(col)
    nt.links.new(diff.outputs[0], s2r.inputs[0]); nt.links.new(s2r.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mul.inputs['A'])
    last = mul.outputs['Result']
    if rim > 0:                                                                               # rim light from the view edge
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


INK = bpy.data.materials.new('INK'); INK.use_nodes = True
INK.node_tree.nodes.clear()
_o = INK.node_tree.nodes.new('ShaderNodeOutputMaterial'); _e = INK.node_tree.nodes.new('ShaderNodeEmission')
_e.inputs['Color'].default_value = hexc('#0E0C1A'); INK.node_tree.links.new(_e.outputs[0], _o.inputs['Surface'])
INK.use_backface_culling = True
if hasattr(INK, 'use_backface_culling_shadow'):
    INK.use_backface_culling_shadow = True


def ink(ob, w=0.012):
    """Inverted-hull ink line around the object."""
    if ob.type != 'MESH':
        return
    ob.data.materials.append(INK)
    sol = ob.modifiers.new('ink', 'SOLIDIFY')
    sol.thickness = w; sol.offset = 1.0; sol.use_flip_normals = True; sol.use_rim = False
    sol.material_offset = len(ob.data.materials) - 1


def shade_smooth(ob):
    for p in ob.data.polygons:
        p.use_smooth = True


def box(name, loc, size, col, rot=(0, 0, 0), w=0.012, **kw):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    ob = bpy.context.object; ob.name = name; ob.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(toon(name, col, **kw)); ink(ob, w)
    return ob


def ball(name, loc, scale, col, w=0.01, seg=32, **kw):
    bpy.ops.mesh.primitive_uv_sphere_add(location=loc, segments=seg, ring_count=seg // 2)
    ob = bpy.context.object; ob.name = name; ob.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True); shade_smooth(ob)
    ob.data.materials.append(toon(name, col, **kw)); ink(ob, w)
    return ob


def cyl(name, loc, r, depth, col, rot=(0, 0, 0), w=0.01, verts=24, **kw):
    bpy.ops.mesh.primitive_cylinder_add(location=loc, radius=r, depth=depth, rotation=rot, vertices=verts)
    ob = bpy.context.object; ob.name = name; shade_smooth(ob)
    ob.data.materials.append(toon(name, col, **kw)); ink(ob, w)
    return ob


def parent(child, par):
    bpy.context.view_layer.update()
    m = child.matrix_world.copy(); child.parent = par; child.matrix_world = m


# ----------------------------------------------------------------------------------------------- the hallway (fixed layout)
WALL, WALL2, FLOOR, CEIL = '#5A5AA0', '#4E4E92', '#6A5A86', '#3A3A70'
box('floor', (0, 5, -0.05), (2.6, 12, 0.1), FLOOR, w=0.0)
box('ceil', (0, 5, 2.75), (2.6, 12, 0.1), CEIL, w=0.0, shadow=0.55, mid=0.62)
box('wallL', (-1.35, 5, 1.35), (0.1, 12, 2.7), WALL, w=0.0)
box('wallR', (1.35, 5, 1.35), (0.1, 12, 2.7), WALL2, w=0.0)
box('wallEnd', (0, 10.5, 1.35), (2.6, 0.1, 2.7), '#4A4A8C', w=0.0)
for side in (-1, 1):
    box(f'skirt{side}', (side * 1.29, 5, 0.07), (0.03, 12, 0.14), '#C8C0D8')
    box(f'rail{side}', (side * 1.29, 5, 0.95), (0.03, 12, 0.05), '#C8C0D8')                  # chair rail (wainscot)
for k in range(10):                                                                           # floorboard seams
    box(f'seam{k}', (0, k * 1.0 + 0.5, 0.002), (2.6, 0.012, 0.004), '#4A3E66', w=0.0)
box('rug', (0, 4.5, 0.008), (1.1, 6.5, 0.012), '#7A4A6A', w=0.006)
box('rugEdge', (0, 4.5, 0.012), (0.9, 6.2, 0.006), '#C8A0B0', w=0.0)
# basement door on the right wall
box('doorFrame', (1.31, 3.5, 1.08), (0.04, 1.1, 2.2), '#D8D0E0')
door = box('door', (1.28, 3.5, 1.03), (0.05, 0.9, 2.06), '#8A8AC8')
for zc in (0.55, 1.5):
    box(f'panel{zc}', (1.25, 3.5, zc), (0.01, 0.62, 0.7), '#7676B2', w=0.006)
ball('knob', (1.22, 3.88, 1.0), (0.04, 0.04, 0.04), '#E8C060', w=0.006)
knob_pivot = bpy.data.objects.new('knobPivot', None); sc.collection.objects.link(knob_pivot)
knob_pivot.location = (1.2, 3.88, 1.0)
lever = box('lever', (1.19, 3.8, 1.0), (0.03, 0.16, 0.03), '#E8C060', w=0.006)
parent(lever, knob_pivot)
box('keyhole', (1.247, 3.88, 0.9), (0.006, 0.02, 0.045), '#120E18', w=0.0)
paper = box('note', (1.245, 3.5, 1.45), (0.005, 0.42, 0.3), '#F4F0E6', w=0.006)
bpy.ops.object.text_add(location=(1.24, 3.5, 1.42), rotation=(math.radians(90), 0, math.radians(-90)))
txt = bpy.context.object; txt.data.body = 'DO NOT\nOPEN'; txt.data.align_x = 'CENTER'; txt.data.align_y = 'CENTER'
txt.data.size = 0.1; txt.data.extrude = 0.001; txt.data.materials.append(toon('noteTxt', '#C8302A'))
box('doorGlow', (1.27, 3.5, 0.008), (0.04, 0.88, 0.012), '#FFB870', emit=6.0, w=0.0)       # light under the door
# left wall: photos, side table + lamp, the window (moon)
for k, (yy, zz, wd, ht) in enumerate(((2.3, 1.6, 0.7, 0.5), (3.6, 1.7, 0.4, 0.45), (4.6, 1.65, 0.45, 0.55))):
    box(f'frame{k}', (-1.29, yy, zz), (0.03, wd, ht), '#C8A060')
    box(f'photo{k}', (-1.272, yy, zz), (0.01, wd - 0.08, ht - 0.08), ['#7A88B8', '#B87A8A', '#88A878'][k], w=0.0)
box('tableTop', (-1.1, 5.8, 0.78), (0.42, 0.7, 0.05), '#6A5A82')
for dy in (-0.3, 0.3):
    for dx in (-0.16, 0.16):
        box(f'leg{dy}{dx}', (-1.1 + dx, 5.8 + dy, 0.38), (0.04, 0.04, 0.76), '#4A3E5E', w=0.006)
cyl('lampBase', (-1.1, 5.8, 0.9), 0.05, 0.2, '#3A3A44')
bpy.ops.mesh.primitive_cone_add(location=(-1.1, 5.8, 1.12), radius1=0.18, radius2=0.1, depth=0.22, vertices=24)
shadeL = bpy.context.object; shadeL.data.materials.append(toon('lampShade', '#FFD8A0', emit=3.0)); ink(shadeL, 0.008)
box('window', (-1.29, 7.4, 1.6), (0.02, 0.9, 1.0), '#C8C0E0')
box('windowGlass', (-1.275, 7.4, 1.6), (0.01, 0.8, 0.9), '#6A7AD0', emit=1.6, w=0.0)
box('windowBar', (-1.265, 7.4, 1.6), (0.01, 0.04, 0.9), '#C8C0E0', w=0.0)
# lights
bpy.ops.object.light_add(type='POINT', location=(-1.0, 5.8, 1.3)); L = bpy.context.object
L.data.energy = 120; L.data.color = hexc('#FFB060')[:3]; L.data.shadow_soft_size = 0.1
bpy.ops.object.light_add(type='AREA', location=(-1.0, 7.4, 1.8)); M_ = bpy.context.object
M_.data.energy = 220; M_.data.color = hexc('#A8A4E0')[:3]; M_.data.size = 0.35; M_.rotation_euler = (0, math.radians(-90), 0)
bpy.ops.object.light_add(type='POINT', location=(1.0, 3.5, 0.15)); D_ = bpy.context.object             # warm leak under the door
D_.data.energy = 25; D_.data.color = hexc('#FFB870')[:3]; D_.data.shadow_soft_size = 0.05
bpy.ops.object.light_add(type='SUN', location=(0, 0, 5)); S_ = bpy.context.object
S_.data.energy = 0.6; S_.data.color = hexc('#7A7AD0')[:3]; S_.rotation_euler = (math.radians(50), 0, math.radians(30))

# ----------------------------------------------------------------------------------------------- the mascot (built like the 2D puppet)
SKIN, SHIRT, JEANS, HAIR, SHOE = '#F2C29B', '#E87A20', '#2E4A7A', '#6A4024', '#E8E8EC'
root = bpy.data.objects.new('mascot', None); sc.collection.objects.link(root)
root.location = (0.45, 3.65, 0)
root.rotation_euler = (0, 0, math.radians(-90))          # faces +X (the door)
parts = []


def P(ob):
    parts.append(ob); parent(ob, root); return ob


def at(x, y, z):                                           # local (mascot) coords -> world before parenting (mascot faces -Y locally)
    return (root.location.x + y, root.location.y - x, z) if False else (x, y, z)


# build at the origin facing -Y, then move the root
root.location = (0, 0, 0); root.rotation_euler = (0, 0, 0)
for side in (-1, 1):
    P(cyl(f'leg{side}', (side * 0.085, 0, 0.3), 0.07, 0.5, JEANS))
    P(ball(f'shoe{side}', (side * 0.085, -0.04, 0.05), (0.08, 0.12, 0.055), SHOE))
torso = P(ball('torso', (0, 0, 0.78), (0.2, 0.15, 0.3), SHIRT, rim=1.0))
head_pivot = bpy.data.objects.new('headPivot', None); sc.collection.objects.link(head_pivot)
head_pivot.location = (0, 0, 1.05); parent(head_pivot, root)
hp = []


def H(ob):
    hp.append(ob); parent(ob, head_pivot); return ob


H(ball('head', (0, 0, 1.3), (0.3, 0.28, 0.29), SKIN, rim=1.0, seg=48))
H(ball('hair', (0, 0.05, 1.42), (0.31, 0.29, 0.22), HAIR))
H(ball('fringe', (0.05, -0.17, 1.52), (0.2, 0.1, 0.07), HAIR))
H(ball('fringe2', (-0.12, -0.12, 1.5), (0.12, 0.12, 0.08), HAIR))
for side in (-1, 1):
    H(ball(f'ear{side}', (side * 0.29, 0.0, 1.28), (0.05, 0.035, 0.07), SKIN))
eyes = []
for side in (-1, 1):
    ew = H(ball(f'eyeW{side}', (side * 0.1, -0.245, 1.32), (0.075, 0.03, 0.09), '#FFFFFF', w=0.008))
    pu = H(ball(f'pupil{side}', (side * 0.1, -0.272, 1.31), (0.036, 0.012, 0.042), '#1A1410', w=0.0))
    hl = H(ball(f'hl{side}', (side * 0.1 + 0.015, -0.283, 1.335), (0.011, 0.004, 0.011), '#FFFFFF', w=0.0))
    br = H(box(f'brow{side}', (side * 0.1, -0.255, 1.44), (0.11, 0.02, 0.022), '#3A2416', rot=(0, side * math.radians(-14), 0), w=0.004))
    eyes.append((ew, pu, hl, br, side))
mouth = H(ball('mouth', (0, -0.25, 1.18), (0.035, 0.022, 0.03), '#5A1A1A', w=0.004))
sweat = H(ball('sweat', (0.25, -0.18, 1.42), (0.022, 0.012, 0.034), '#BFE3FF', w=0.004))
arms = {}
for side in (-1, 1):
    sh = bpy.data.objects.new(f'shoulder{side}', None); sc.collection.objects.link(sh)
    sh.location = (side * 0.2, 0, 0.98); parent(sh, root)
    for ob in (cyl(f'sleeve{side}', (side * 0.2, 0, 0.9), 0.06, 0.16, SHIRT),
               cyl(f'arm{side}', (side * 0.2, 0, 0.72), 0.04, 0.36, SKIN),
               ball(f'hand{side}', (side * 0.2, 0, 0.53), (0.05, 0.05, 0.05), SKIN)):
        parts.append(ob); parent(ob, sh)
    arms[side] = sh
root.location = (0.45, 3.65, 0)
root.rotation_euler = (0, 0, math.radians(90))            # local -Y (face) -> world +X (the door)

# key in the right hand (used in shot C)
key_par = arms[1]
kring = bpy.ops.mesh.primitive_torus_add(location=(0.2, -0.06, 0.48), major_radius=0.035, minor_radius=0.009)
kr = bpy.context.object; kr.data.materials.append(toon('key', '#E8C060')); ink(kr, 0.004); parent(kr, key_par)
kb = box('keyBlade', (0.2, -0.06, 0.4), (0.012, 0.012, 0.11), '#E8C060', w=0.004); parent(kb, key_par)


# ----------------------------------------------------------------------------------------------- animation
def kf(ob, path, frame, val):
    setattr(ob, path, val); ob.keyframe_insert(data_path=path, frame=frame)


# shot A: reaching slowly for the knob (right arm up/forward), breathing
kf(arms[1], 'rotation_euler', 0, (math.radians(10), 0, 0))
kf(arms[1], 'rotation_euler', 110, (math.radians(-70), 0, math.radians(-10)))
kf(arms[-1], 'rotation_euler', 0, (0, 0, 0))
for f in range(0, F_END + 1, 30):
    kf(torso, 'scale', f, (1.0, 1.0, 1.0)); kf(torso, 'scale', f + 15, (1.02, 1.02, 1.0))
# shot B: face close-up (camera at the door looking back at him). Pupils slide left, blink, then the head snaps over the shoulder.
kf(arms[1], 'rotation_euler', F_B, (math.radians(-60), 0, math.radians(-10)))
kf(arms[1], 'rotation_euler', F_B + 20, (math.radians(-20), 0, 0))
kf(head_pivot, 'rotation_euler', F_B, (math.radians(4), 0, math.radians(-8)))
kf(head_pivot, 'rotation_euler', F_B + 50, (math.radians(4), 0, math.radians(-8)))
kf(head_pivot, 'rotation_euler', F_B + 56, (math.radians(-4), 0, math.radians(-30)))
kf(head_pivot, 'rotation_euler', F_C - 1, (math.radians(-4), 0, math.radians(-33)))
for ew, pu, hl, br, side in eyes:
    for ob in (pu, hl):
        base = ob.location.copy()
        for f, dx in ((F_B, 0.0), (F_B + 30, 0.0), (F_B + 36, -0.034), (F_B + 60, -0.034), (F_B + 66, -0.01)):
            kf(ob, 'location', f, (base.x + dx, base.y, base.z))
        kf(ob, 'location', F_C, base)
    for ob in (ew, pu, hl):                                                                     # blinks
        for fb in (F_B + 22, F_B + 74):
            kf(ob, 'scale', fb - 2, (1, 1, 1)); kf(ob, 'scale', fb, (1, 1, 0.08)); kf(ob, 'scale', fb + 3, (1, 1, 1))
    for f, rz in ((F_B, 0), (F_B + 34, side * math.radians(10)), (F_C, side * math.radians(10))):   # brows go up (fear)
        kf(br, 'rotation_euler', f, (0, side * math.radians(-14) + rz, 0))
mb = mouth.scale.copy()
for f, sz in ((F_B, 1.0), (F_B + 52, 1.0), (F_B + 56, 1.9), (F_C, 1.6)):
    kf(mouth, 'scale', f, (mb.x * (1.0 if sz == 1 else 0.8), mb.y, mb.z * sz))
kf(sweat, 'location', F_B, sweat.location.copy())
kf(sweat, 'location', F_C, sweat.location + Vector((0, 0, -0.12)))
# lamp flicker + the warm leak under the door breathing on his face
for f, e in ((0, 120), (F_B + 40, 120), (F_B + 41, 15), (F_B + 44, 120), (F_B + 47, 10), (F_B + 49, 120)):
    kf(L.data, 'energy', f, e)
for f, e in ((0, 25), (F_B, 25), (F_B + 8, 70), (F_B + 30, 40), (F_B + 55, 90), (F_C, 60), (F_C + 50, 30), (F_END, 110)):
    kf(D_.data, 'energy', f, e)
# shot C: he turns back, the hand comes up holding the key toward the door ... and the handle turns by itself (from the other side)
for f, a in ((0, 0), (F_C + 40, 0), (F_C + 43, 28), (F_C + 47, 4), (F_C + 51, 34), (F_C + 56, 6), (F_C + 60, 40), (F_END, 42)):
    kf(knob_pivot, 'rotation_euler', f, (math.radians(a), 0, 0))
kf(head_pivot, 'rotation_euler', F_C, (0, 0, math.radians(-25)))
kf(head_pivot, 'rotation_euler', F_C + 25, (0, 0, 0))
kf(arms[1], 'rotation_euler', F_C, (math.radians(-20), 0, 0))
kf(arms[1], 'rotation_euler', F_C + 35, (math.radians(-88), 0, math.radians(-5)))

# ----------------------------------------------------------------------------------------------- cameras: every frame keyed (eased dolly + handheld)
def camera(name, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.sensor_width = 36
    ob = bpy.data.objects.new(name, cd); sc.collection.objects.link(ob)
    tgt = bpy.data.objects.new(name + '_tgt', None); sc.collection.objects.link(tgt)
    c = ob.constraints.new('TRACK_TO'); c.target = tgt; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    return ob, tgt


def ease(u, mode='io'):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3 if mode == 'out' else u * u * (3 - 2 * u)


def lerp(a, b, u):
    return Vector(a).lerp(Vector(b), u)


SHOTS = [  # cam, lens, f0, f1, loc0, loc1, tgt0, tgt1, ease
    ('camA', 24, F_A, F_B - 1, (-0.2, -0.8, 1.5), (0.1, 1.85, 1.25), (0.6, 5.0, 1.0), (0.7, 3.7, 1.0), 'out'),
    ('camB', 24, F_B, F_C - 1, (1.2, 3.42, 1.4), (1.08, 3.48, 1.36), (0.45, 3.66, 1.3), (0.45, 3.66, 1.31), 'io'),
    ('camC', 30, F_C, F_END, (-0.7, 2.5, 1.15), (0.3, 2.7, 1.12), (1.25, 3.55, 1.1), (1.25, 3.62, 1.18), 'io'),
]
for name, lens, f0, f1, l0, l1, t0, t1, md in SHOTS:
    cam, tgt = camera(name, lens)
    for f in range(f0, f1 + 1):
        u = ease((f - f0) / max(1, f1 - f0), md)
        wob = Vector((0.006 * math.sin(f * 0.37) + 0.003 * math.sin(f * 0.91), 0.0, 0.005 * math.sin(f * 0.53 + 1)))
        kf(cam, 'location', f, lerp(l0, l1, u))
        kf(tgt, 'location', f, lerp(t0, t1, u) + wob)
    mk = sc.timeline_markers.new(name, frame=f0); mk.camera = cam
    if f0 == F_A:
        sc.camera = cam

# ----------------------------------------------------------------------------------------------- render
out = os.path.join(HERE, 'frames3d', 'ALL')
os.makedirs(out, exist_ok=True)
if '--still' in opt:
    f = int(opt['--still']); sc.frame_set(f)
    sc.render.filepath = os.path.join(out, f'{f:04d}.png'); bpy.ops.render.render(write_still=True)
    print('STILL_OK', f)
else:
    a, b = (int(v) for v in opt.get('--frames', f'{F_A},{F_END}').split(','))
    sc.frame_start, sc.frame_end = a, b
    sc.render.filepath = os.path.join(out, '####')
    bpy.ops.render.render(animation=True)
    print('RENDER_OK', a, b)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'scene3d.blend'))
