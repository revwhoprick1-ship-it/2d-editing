"""Physically based material library (Blender 5.x node API).

All materials are procedural so the project carries no third-party texture
licences.  Each builder returns a bpy Material and re-uses an existing one
with the same name.
"""
import bpy


def hex_rgb(h, a=1.0):
    h = h.lstrip('#')
    srgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


def _new(name):
    m = bpy.data.materials.get(name)
    if m:
        return m, None
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    return m, nt


def _bsdf(nt):
    return nt.nodes.get('Principled BSDF')


def _link(nt, a, b):
    nt.links.new(a, b)


def _node(nt, kind, loc=(0, 0), **props):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, v in props.items():
        setattr(n, k, v)
    return n


def _ramp(nt, stops, loc=(0, 0)):
    r = _node(nt, 'ShaderNodeValToRGB', loc)
    cr = r.color_ramp
    while len(cr.elements) > len(stops):
        cr.elements.remove(cr.elements[-1])
    while len(cr.elements) < len(stops):
        cr.elements.new(0.5)
    for el, (pos, col) in zip(cr.elements, stops):
        el.position = pos
        el.color = col if len(col) == 4 else (*col, 1)
    return r


def _bump(nt, height_socket, strength=0.2, distance=0.002, loc=(0, 0)):
    b = _node(nt, 'ShaderNodeBump', loc)
    b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = distance
    _link(nt, height_socket, b.inputs['Height'])
    return b


# ------------------------------------------------------------------ character
def skin(colors):
    m, nt = _new('MSC_Skin')
    if nt is None:
        return m
    p = _bsdf(nt)
    tc = _node(nt, 'ShaderNodeTexCoord', (-1200, 0))
    # blush: object-space cheeks + nose tip, read from a colour attribute painted by the builder
    attr = _node(nt, 'ShaderNodeAttribute', (-900, 300), attribute_name='blush')
    mix = _node(nt, 'ShaderNodeMix', (-500, 250), data_type='RGBA')
    mix.inputs['A'].default_value = hex_rgb(colors['skin'])
    mix.inputs['B'].default_value = hex_rgb(colors['skin_blush'])
    _link(nt, attr.outputs['Fac'], mix.inputs['Factor'])
    # micro variation (pores / mottling) — subtle
    noise = _node(nt, 'ShaderNodeTexNoise', (-900, -100))
    noise.inputs['Scale'].default_value = 180.0
    noise.inputs['Detail'].default_value = 6.0
    _link(nt, tc.outputs['Object'], noise.inputs['Vector'])
    mott = _node(nt, 'ShaderNodeMix', (-250, 200), data_type='RGBA', blend_type='MULTIPLY')
    mott.inputs['Factor'].default_value = 0.06
    _link(nt, mix.outputs['Result'], mott.inputs['A'])
    _link(nt, noise.outputs['Color'], mott.inputs['B'])
    lipa = _node(nt, 'ShaderNodeAttribute', (-500, 500), attribute_name='lipmask')
    lipmix = _node(nt, 'ShaderNodeMix', (-50, 300), data_type='RGBA')
    _link(nt, lipa.outputs['Fac'], lipmix.inputs['Factor'])
    _link(nt, mott.outputs['Result'], lipmix.inputs['A'])
    lipmix.inputs['B'].default_value = hex_rgb(colors['lip'])
    _link(nt, lipmix.outputs['Result'], p.inputs['Base Color'])
    rmix = _node(nt, 'ShaderNodeMath', (-50, 0), operation='MULTIPLY_ADD')
    _link(nt, lipa.outputs['Fac'], rmix.inputs[0])
    rmix.inputs[1].default_value = -0.14
    rmix.inputs[2].default_value = 0.5
    _link(nt, rmix.outputs[0], p.inputs['Roughness'])
    p.inputs['Roughness'].default_value = 0.5
    p.inputs['Subsurface Weight'].default_value = 0.22
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.38, 0.22)
    p.inputs['Subsurface Scale'].default_value = 0.012
    p.inputs['Specular IOR Level'].default_value = 0.45
    p.inputs['Coat Weight'].default_value = 0.04
    b = _bump(nt, noise.outputs['Fac'], 0.06, 0.0004, (-250, -250))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    return m


def lip(colors):
    m, nt = _new('MSC_Lip')
    if nt is None:
        return m
    p = _bsdf(nt)
    p.inputs['Base Color'].default_value = hex_rgb(colors['lip'])
    p.inputs['Roughness'].default_value = 0.38
    p.inputs['Subsurface Weight'].default_value = 0.25
    p.inputs['Subsurface Radius'].default_value = (1.0, 0.3, 0.2)
    p.inputs['Subsurface Scale'].default_value = 0.01
    return m


def simple(name, color, rough=0.5, sss=0.0, coat=0.0, emission=None, metallic=0.0, sheen=0.0):
    m, nt = _new(name)
    if nt is None:
        return m
    p = _bsdf(nt)
    p.inputs['Base Color'].default_value = hex_rgb(color) if isinstance(color, str) else color
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
    if sss:
        p.inputs['Subsurface Weight'].default_value = sss
        p.inputs['Subsurface Scale'].default_value = 0.01
    if coat:
        p.inputs['Coat Weight'].default_value = coat
    if sheen:
        p.inputs['Sheen Weight'].default_value = sheen
    if emission:
        p.inputs['Emission Color'].default_value = hex_rgb(emission[0])
        p.inputs['Emission Strength'].default_value = emission[1]
    return m


def hair(colors):
    m, nt = _new('MSC_Hair')
    if nt is None:
        return m
    p = _bsdf(nt)
    tc = _node(nt, 'ShaderNodeTexCoord', (-1300, 0))
    # strand direction is stored in UV.x along the clump length; UV.y across
    uv = _node(nt, 'ShaderNodeUVMap', (-1300, -300))
    sep = _node(nt, 'ShaderNodeSeparateXYZ', (-1100, -300))
    _link(nt, uv.outputs['UV'], sep.inputs['Vector'])
    # fine strands: noise stretched across the clump
    comb = _node(nt, 'ShaderNodeCombineXYZ', (-900, -300))
    mul = _node(nt, 'ShaderNodeMath', (-1000, -420), operation='MULTIPLY')
    mul.inputs[1].default_value = 3.0
    _link(nt, sep.outputs['X'], mul.inputs[0])
    _link(nt, mul.outputs[0], comb.inputs['X'])
    mul2 = _node(nt, 'ShaderNodeMath', (-1000, -560), operation='MULTIPLY')
    mul2.inputs[1].default_value = 70.0
    _link(nt, sep.outputs['Y'], mul2.inputs[0])
    _link(nt, mul2.outputs[0], comb.inputs['Y'])
    strands = _node(nt, 'ShaderNodeTexNoise', (-700, -300))
    strands.inputs['Scale'].default_value = 4.0
    strands.inputs['Detail'].default_value = 8.0
    _link(nt, comb.outputs['Vector'], strands.inputs['Vector'])
    # root-to-tip gradient + per-clump variation
    var = _node(nt, 'ShaderNodeAttribute', (-900, 250), attribute_name='clump_var')
    ramp = _ramp(nt, [(0.0, hex_rgb(colors['hair'])), (1.0, hex_rgb(colors['hair_tip']))], (-500, 200))
    tipmix = _node(nt, 'ShaderNodeMath', (-700, 200), operation='MULTIPLY_ADD')
    _link(nt, sep.outputs['X'], tipmix.inputs[0])
    tipmix.inputs[1].default_value = 0.55
    _link(nt, var.outputs['Fac'], tipmix.inputs[2])
    _link(nt, tipmix.outputs[0], ramp.inputs['Fac'])
    dark = _node(nt, 'ShaderNodeMix', (-250, 150), data_type='RGBA', blend_type='MULTIPLY')
    dark.inputs['Factor'].default_value = 0.35
    _link(nt, ramp.outputs['Color'], dark.inputs['A'])
    _link(nt, strands.outputs['Color'], dark.inputs['B'])
    _link(nt, dark.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.42
    p.inputs['Specular IOR Level'].default_value = 0.6
    p.inputs['Coat Weight'].default_value = 0.18
    p.inputs['Coat Roughness'].default_value = 0.25
    p.inputs['Sheen Weight'].default_value = 0.08
    p.inputs['Sheen Tint'].default_value = hex_rgb(colors['hair_tip'])
    p.inputs['Anisotropic'].default_value = 0.6
    b = _bump(nt, strands.outputs['Fac'], 0.45, 0.002, (-250, -300))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    return m


def eye(colors, iris_ratio, pupil_ratio):
    """Eyeball shader.  The eye mesh is built with its pole on -Y (looking
    forward), unit radius in object space."""
    m, nt = _new('MSC_Eye')
    if nt is None:
        return m
    p = _bsdf(nt)
    tc = _node(nt, 'ShaderNodeTexCoord', (-1500, 0))
    sep = _node(nt, 'ShaderNodeSeparateXYZ', (-1300, 0))
    _link(nt, tc.outputs['Object'], sep.inputs['Vector'])
    # radial distance from the forward axis
    vx = _node(nt, 'ShaderNodeCombineXYZ', (-1100, 100))
    _link(nt, sep.outputs['X'], vx.inputs['X'])
    _link(nt, sep.outputs['Z'], vx.inputs['Y'])
    ln = _node(nt, 'ShaderNodeVectorMath', (-900, 100), operation='LENGTH')
    _link(nt, vx.outputs['Vector'], ln.inputs[0])
    # front mask (y < 0)
    front = _node(nt, 'ShaderNodeMath', (-900, -100), operation='LESS_THAN')
    _link(nt, sep.outputs['Y'], front.inputs[0])
    front.inputs[1].default_value = 0.0
    r = ln.outputs['Value']
    # angular texture for iris fibres
    ang = _node(nt, 'ShaderNodeMath', (-900, -300), operation='ARCTAN2')
    _link(nt, sep.outputs['Z'], ang.inputs[0])
    _link(nt, sep.outputs['X'], ang.inputs[1])
    fib_in = _node(nt, 'ShaderNodeCombineXYZ', (-700, -300))
    m1 = _node(nt, 'ShaderNodeMath', (-800, -450), operation='MULTIPLY')
    m1.inputs[1].default_value = 9.0
    _link(nt, ang.outputs[0], m1.inputs[0])
    _link(nt, m1.outputs[0], fib_in.inputs['X'])
    m2 = _node(nt, 'ShaderNodeMath', (-800, -560), operation='MULTIPLY')
    m2.inputs[1].default_value = 2.5
    _link(nt, r, m2.inputs[0])
    _link(nt, m2.outputs[0], fib_in.inputs['Y'])
    fib = _node(nt, 'ShaderNodeTexNoise', (-550, -300))
    fib.inputs['Scale'].default_value = 3.0
    fib.inputs['Detail'].default_value = 6.0
    _link(nt, fib_in.outputs['Vector'], fib.inputs['Vector'])
    ir = iris_ratio
    pr = pupil_ratio
    stops = [
        (0.0, hex_rgb(colors['pupil'])),
        (pr * 0.97, hex_rgb(colors['pupil'])),
        (pr * 1.06, hex_rgb(colors['iris_light'])),
        (ir * 0.62, hex_rgb(colors['iris'])),
        (ir * 0.93, hex_rgb(colors['iris'])),
        (ir * 1.0, hex_rgb(colors['iris_ring'])),
        (ir * 1.07, hex_rgb(colors['sclera'])),
        (1.0, hex_rgb(colors['sclera'])),
    ]
    ramp = _ramp(nt, stops, (-550, 150))
    _link(nt, r, ramp.inputs['Fac'])
    # fibres only inside iris
    fibmix = _node(nt, 'ShaderNodeMix', (-250, 150), data_type='RGBA', blend_type='OVERLAY')
    irmask = _node(nt, 'ShaderNodeMath', (-450, -100), operation='LESS_THAN')
    _link(nt, r, irmask.inputs[0])
    irmask.inputs[1].default_value = ir
    irm2 = _node(nt, 'ShaderNodeMath', (-300, -100), operation='MULTIPLY')
    _link(nt, irmask.outputs[0], irm2.inputs[0])
    irm2.inputs[1].default_value = 0.55
    _link(nt, irm2.outputs[0], fibmix.inputs['Factor'])
    _link(nt, ramp.outputs['Color'], fibmix.inputs['A'])
    _link(nt, fib.outputs['Color'], fibmix.inputs['B'])
    # back of eye = sclera
    backmix = _node(nt, 'ShaderNodeMix', (-50, 150), data_type='RGBA')
    backmix.inputs['A'].default_value = hex_rgb(colors['sclera'])
    _link(nt, front.outputs[0], backmix.inputs['Factor'])
    _link(nt, fibmix.outputs['Result'], backmix.inputs['B'])
    _link(nt, backmix.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.08
    p.inputs['Coat Weight'].default_value = 1.0
    p.inputs['Coat Roughness'].default_value = 0.02
    p.inputs['Subsurface Weight'].default_value = 0.08
    p.inputs['Subsurface Scale'].default_value = 0.004
    return m


def fabric(name, color, rib_color=None, scale=1500.0, bump=0.05, sheen=0.5, seam_attr=None):
    """Knit fabric (T-shirt) with fine weave bump and optional seam darkening
    read from a float colour attribute."""
    m, nt = _new(name)
    if nt is None:
        return m
    p = _bsdf(nt)
    tc = _node(nt, 'ShaderNodeTexCoord', (-1300, 0))
    wave = _node(nt, 'ShaderNodeTexWave', (-1000, -200), wave_type='BANDS', bands_direction='Z')
    wave.inputs['Scale'].default_value = scale
    wave.inputs['Distortion'].default_value = 1.5
    _link(nt, tc.outputs['Object'], wave.inputs['Vector'])
    noise = _node(nt, 'ShaderNodeTexNoise', (-1000, 200))
    noise.inputs['Scale'].default_value = 40.0
    noise.inputs['Detail'].default_value = 4.0
    _link(nt, tc.outputs['Object'], noise.inputs['Vector'])
    base = _node(nt, 'ShaderNodeMix', (-600, 200), data_type='RGBA', blend_type='MULTIPLY')
    base.inputs['Factor'].default_value = 0.12
    base.inputs['A'].default_value = hex_rgb(color)
    _link(nt, noise.outputs['Color'], base.inputs['B'])
    col_out = base.outputs['Result']
    if seam_attr:
        sa = _node(nt, 'ShaderNodeAttribute', (-600, 450), attribute_name=seam_attr)
        sm = _node(nt, 'ShaderNodeMix', (-350, 300), data_type='RGBA')
        _link(nt, sa.outputs['Fac'], sm.inputs['Factor'])
        _link(nt, col_out, sm.inputs['A'])
        sm.inputs['B'].default_value = hex_rgb(rib_color or color)
        col_out = sm.outputs['Result']
    _link(nt, col_out, p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.85
    p.inputs['Sheen Weight'].default_value = sheen
    p.inputs['Sheen Roughness'].default_value = 0.4
    p.inputs['Specular IOR Level'].default_value = 0.3
    b = _bump(nt, wave.outputs['Fac'], bump, 0.0008, (-350, -250))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    return m


def denim(colors):
    m, nt = _new('MSC_Denim')
    if nt is None:
        return m
    p = _bsdf(nt)
    tc = _node(nt, 'ShaderNodeTexCoord', (-1400, 0))
    # twill: diagonal bands
    mapn = _node(nt, 'ShaderNodeMapping', (-1200, 0))
    mapn.inputs['Rotation'].default_value = (0.0, 0.6, 0.6)
    _link(nt, tc.outputs['Object'], mapn.inputs['Vector'])
    wave = _node(nt, 'ShaderNodeTexWave', (-950, -200), wave_type='BANDS', bands_direction='X')
    wave.inputs['Scale'].default_value = 2600.0
    _link(nt, mapn.outputs['Vector'], wave.inputs['Vector'])
    fade = _node(nt, 'ShaderNodeTexNoise', (-950, 250))
    fade.inputs['Scale'].default_value = 9.0
    fade.inputs['Detail'].default_value = 3.0
    _link(nt, tc.outputs['Object'], fade.inputs['Vector'])
    ramp = _ramp(nt, [(0.35, hex_rgb(colors['jeans_dark'])), (0.75, hex_rgb(colors['jeans']))], (-650, 250))
    _link(nt, fade.outputs['Fac'], ramp.inputs['Fac'])
    thread = _node(nt, 'ShaderNodeMix', (-350, 200), data_type='RGBA', blend_type='SCREEN')
    thread.inputs['Factor'].default_value = 0.05
    _link(nt, ramp.outputs['Color'], thread.inputs['A'])
    _link(nt, wave.outputs['Color'], thread.inputs['B'])
    sa = _node(nt, 'ShaderNodeAttribute', (-350, 450), attribute_name='seam')
    sm = _node(nt, 'ShaderNodeMix', (-150, 300), data_type='RGBA')
    _link(nt, sa.outputs['Fac'], sm.inputs['Factor'])
    _link(nt, thread.outputs['Result'], sm.inputs['A'])
    sm.inputs['B'].default_value = hex_rgb('#C9893A')  # golden topstitch
    _link(nt, sm.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = 0.88
    p.inputs['Sheen Weight'].default_value = 0.3
    b = _bump(nt, wave.outputs['Fac'], 0.12, 0.0005, (-350, -250))
    _link(nt, b.outputs['Normal'], p.inputs['Normal'])
    return m


def character_set(colors, iris_ratio, pupil_ratio):
    return {
        'skin': skin(colors),
        'lip': lip(colors),
        'hair': hair(colors),
        'brow': simple('MSC_Brow', colors['brow'], 0.6, sheen=0.4),
        'lash': simple('MSC_Lash', '#1C0F08', 0.5),
        'eye': eye(colors, iris_ratio, pupil_ratio),
        'shirt': fabric('MSC_Shirt', colors['shirt'], colors['shirt_rib'], seam_attr='seam'),
        'denim': denim(colors),
        'shoe': simple('MSC_ShoeUpper', colors['shoe'], 0.55, sheen=0.2),
        'shoe_accent': simple('MSC_ShoeAccent', colors['shoe_accent'], 0.6),
        'sole': simple('MSC_Sole', colors['sole'], 0.7),
        'lace': simple('MSC_Lace', colors['lace'], 0.8, sheen=0.3),
        'mouth': simple('MSC_Mouth', colors['mouth'], 0.6, sss=0.2),
        'teeth': simple('MSC_Teeth', colors['teeth'], 0.25, sss=0.1, coat=0.3),
        'tongue': simple('MSC_Tongue', colors['tongue'], 0.35, sss=0.3, coat=0.2),
        'nail': simple('MSC_Nail', colors['nail'], 0.3, coat=0.5),
    }
