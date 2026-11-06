"""Render, colour-management, camera and lighting helpers."""
import math
import bpy
from mathutils import Vector


def scene_defaults(scene=None, engine='BLENDER_EEVEE', res=(1080, 1920), fps=30, samples=16,
                   look='AgX - Punchy', exposure=0.0, motion_blur=False):
    sc = scene or bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = fps
    sc.render.film_transparent = False
    vs = sc.view_settings
    try:
        sc.display_settings.display_device = 'sRGB'
        vs.view_transform = 'AgX'
        vs.look = look
    except TypeError:
        vs.view_transform = 'Filmic'
    vs.exposure = exposure
    if engine == 'BLENDER_EEVEE':
        ee = sc.eevee
        ee.taa_render_samples = samples
        for attr, val in (('use_raytracing', True), ('use_shadows', True), ('use_gtao', True),
                          ('shadow_ray_count', 1), ('shadow_step_count', 6),
                          ('use_volumetric_shadows', False), ('volumetric_tile_size', '8'),
                          ('use_fast_gi', True), ('fast_gi_method', 'GLOBAL_ILLUMINATION')):
            if hasattr(ee, attr):
                try:
                    setattr(ee, attr, val)
                except Exception:
                    pass
        if hasattr(ee, 'shadow_resolution_scale'):
            ee.shadow_resolution_scale = 0.5
        sc.render.use_motion_blur = motion_blur
        if motion_blur:
            sc.render.motion_blur_shutter = 0.5
    else:
        sc.cycles.device = 'CPU'
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.render.use_motion_blur = motion_blur
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    return sc


def world_color(color=(0.05, 0.05, 0.06), strength=1.0, scene=None):
    sc = scene or bpy.context.scene
    w = sc.world or bpy.data.worlds.new('World')
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes.get('Background')
    bg.inputs['Color'].default_value = (*color, 1)
    bg.inputs['Strength'].default_value = strength
    return w


def world_gradient(top, horizon, bottom, strength=1.0, scene=None):
    sc = scene or bpy.context.scene
    w = sc.world or bpy.data.worlds.new('World')
    sc.world = w
    nt = w.node_tree
    for n in list(nt.nodes):
        if n.type not in ('OUTPUT_WORLD',):
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*bottom, 1)
    e = ramp.color_ramp.elements.new(0.5)
    e.color = (*horizon, 1)
    ramp.color_ramp.elements[-1].position = 0.75
    ramp.color_ramp.elements[-1].color = (*top, 1)
    nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    return w


def area_light(name, loc, target, energy, size=1.0, color=(1, 1, 1), shape='DISK', size_y=None,
               collection=None):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y is not None and shape in ('RECTANGLE', 'ELLIPSE'):
        ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def point_light(name, loc, energy, color=(1, 1, 1), radius=0.05, collection=None):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    return ob


def look_at(ob, target, roll=0.0):
    d = Vector(target) - ob.location
    q = d.to_track_quat('-Z', 'Y')
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = q.to_euler()
    if roll:
        ob.rotation_euler.rotate_axis('Z', roll)


def camera(name, loc, target, lens=50.0, sensor=36.0, dof_obj=None, fstop=2.8, collection=None,
           clip_start=0.01, clip_end=200.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = 'AUTO'
    cd.clip_start = clip_start
    cd.clip_end = clip_end
    if dof_obj is not None:
        cd.dof.use_dof = True
        cd.dof.focus_object = dof_obj
        cd.dof.aperture_fstop = fstop
    ob = bpy.data.objects.new(name, cd)
    (collection or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def three_point(target=(0, 0, 1.0), key=600.0, scale=1.0, warm=(1.0, 0.93, 0.85), cool=(0.8, 0.88, 1.0),
                collection=None):
    t = Vector(target)
    k = area_light('Key', t + Vector((-1.6, -2.2, 1.4)) * scale, t, key, 1.6 * scale, warm, collection=collection)
    f = area_light('Fill', t + Vector((2.2, -1.6, 0.4)) * scale, t, key * 0.35, 2.4 * scale, cool, collection=collection)
    r = area_light('Rim', t + Vector((1.2, 2.2, 1.6)) * scale, t, key * 0.9, 1.0 * scale, (1.0, 0.95, 0.9), collection=collection)
    return k, f, r
