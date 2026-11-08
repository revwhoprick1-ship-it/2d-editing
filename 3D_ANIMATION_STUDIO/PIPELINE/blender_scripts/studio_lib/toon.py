"""2dEDIT style: turn any scene into a flat, cel-shaded "2D animation" look (inspired by the user's reference).

Every material becomes: light -> Shader-to-RGB -> 3-step constant colour ramp -> x base colour -> emission.
Lights still matter (practical lamps, lanterns, screens shape the bands) but there is no gloss, no SSS,
no reflections: flat fills, soft-edged shadow steps, readable silhouettes. Emissive materials stay emissive.
Call toonify() after the scene is built and before rendering.
"""
import bpy


def _base_color_input(nt):
    p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None:
        return None, (0.6, 0.6, 0.6, 1)
    bc = p.inputs['Base Color']
    if bc.is_linked:
        return bc.links[0].from_socket, None
    return None, tuple(bc.default_value)


def _emissive(nt):
    p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if p is None:
        return None
    s = p.inputs.get('Emission Strength')
    if s is not None and s.default_value > 0.5:
        return p
    return None


def toon_material(m, shadow=0.42, mid=0.72, rim=0.0):
    if not m or not m.use_nodes or m.get('toon'):
        return
    nt = m.node_tree
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None:
        return
    em = _emissive(nt)
    sock, col = _base_color_input(nt)
    if em is not None:                                   # practical lights / screens: keep glowing, flat
        return
    diff = nt.nodes.new('ShaderNodeBsdfDiffuse')
    s2r = nt.nodes.new('ShaderNodeShaderToRGB')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'EASE'
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (shadow * 0.75, shadow * 0.8, shadow * 1.0, 1)   # cool-tinted shadow
    els[1].position, els[1].color = 0.75, (1, 1, 1, 1)
    e = els.new(0.3)
    e.color = (mid, mid, mid * 1.03, 1)
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    emit = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(diff.outputs['BSDF'], s2r.inputs['Shader'])
    nt.links.new(s2r.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mul.inputs['A'])
    if sock is not None:
        nt.links.new(sock, mul.inputs['B'])
    else:
        mul.inputs['B'].default_value = col
    nt.links.new(mul.outputs['Result'], emit.inputs['Color'])
    emit.inputs['Strength'].default_value = 1.0
    p = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    alpha = p.inputs['Alpha'].default_value if p is not None and not p.inputs['Alpha'].is_linked else 1.0
    if alpha < 0.999:                                    # see-through materials (tinted glass, dark 'mirror' steel) stay see-through
        tr = nt.nodes.new('ShaderNodeBsdfTransparent')
        mix = nt.nodes.new('ShaderNodeMixShader')
        mix.inputs['Fac'].default_value = alpha
        nt.links.new(tr.outputs['BSDF'], mix.inputs[1])
        nt.links.new(emit.outputs['Emission'], mix.inputs[2])
        nt.links.new(mix.outputs['Shader'], out.inputs['Surface'])
    else:
        nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    m['toon'] = 1


def toonify(scene=None, shadow=0.42, mid=0.72):
    sc = scene or bpy.context.scene
    for m in bpy.data.materials:
        try:
            toon_material(m, shadow, mid)
        except Exception as ex:                          # never break a render over one odd material
            print('TOON_SKIP', m.name, ex)
    vs = sc.view_settings
    vs.view_transform, vs.look, vs.exposure = 'Standard', 'None', 0.0
    ee = sc.eevee
    for attr, val in (('use_gtao', False), ('use_raytracing', False)):
        if hasattr(ee, attr):
            setattr(ee, attr, val)
