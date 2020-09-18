
import numpy as np
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.math import supported_metrics
from sverchok.utils.curve.core import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.math import ZERO, FRENET, HOUSEHOLDER, TRACK, DIFF, NORMAL_DIR, NONE, TRACK_NORMAL
from sverchok.utils.surface.nurbs import nurbs_sweep
from sverchok.dependencies import geomdl

class SvNurbsSweepNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: NURBS Sweep / Birail
    Tooltip: Generate a NURBS surface by sweeping one curve along another (a.k.a birail)
    """
    bl_idname = 'SvNurbsSweepNode'
    bl_label = 'NURBS Sweep'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_SURFACE_FROM_CURVES'

    u_knots_modes = [
            ('UNIFY', "Unify", "Unify knot vectors of curves by inserting knots into curves where needed", 0),
            ('AVERAGE', "Average", "Use average knot vector from curves; this will work only when curves have same number of control points!", 1)
        ]

    u_knots_mode : EnumProperty(
            name = "U Knots",
            description = "How to make slice curves knot vectors equal",
            items = u_knots_modes,
            default = 'UNIFY',
            update = updateNode)

    metric : EnumProperty(
            name = "Metric",
            description = "Metric to be used for interpolation",
            items = supported_metrics,
            default = 'DISTANCE',
            update = updateNode)

    def get_implementations(self, context):
        items = []
        i = 0
        if geomdl is not None:
            item = (SvNurbsCurve.GEOMDL, "Geomdl", "Geomdl (NURBS-Python) package implementation",i)
            i += 1
            items.append(item)
        item = (SvNurbsCurve.NATIVE, "Sverchok", "Sverchok built-in implementation", i)
        items.append(item)
        return items

    nurbs_implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    modes = [
        (NONE, "None", "No rotation", 0),
        (FRENET, "Frenet", "Frenet / native rotation", 1),
        (ZERO, "Zero-twist", "Zero-twist rotation", 2),
        (HOUSEHOLDER, "Householder", "Use Householder reflection matrix", 3),
        (TRACK, "Tracking", "Use quaternion-based tracking", 4),
        (DIFF, "Rotation difference", "Use rotational difference calculation", 5),
        (TRACK_NORMAL, "Track normal", "Try to maintain constant normal direction by tracking along curve", 6),
        (NORMAL_DIR, "Specified plane", "Use plane defined by normal vector in Normal input; i.e., offset in direction perpendicular to Normal input", 7)
    ]

    @throttled
    def update_sockets(self, context):
        self.inputs['Resolution'].hide_safe = self.algorithm not in {ZERO, TRACK_NORMAL}
        self.inputs['Normal'].hide_safe = self.algorithm != NORMAL_DIR
        self.inputs['V'].hide_safe = not self.explicit_v
        #self.inputs['VSections'].hide_safe = self.explicit_v

    algorithm : EnumProperty(
            name = "Algorithm",
            items = modes,
            default = NONE,
            update = update_sockets)

    resolution : IntProperty(
        name = "Resolution",
        description = "Resolution for rotation calculation algorithm",
        min = 10, default = 50,
        update = updateNode)

    profiles_count : IntProperty(
        name = "V Sections",
        description = "Number of profile curve instances to be placed along the path curve",
        min = 2,
        default = 10,
        update = updateNode)

    explicit_v : BoolProperty(
        name = "Explicit V values",
        description = "Provide values of V parameter (along path curve) for profile curves explicitly",
        default = False,
        update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'nurbs_implementation', text='')
        layout.prop(self, "algorithm")
        layout.prop(self, "explicit_v")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'u_knots_mode')
        layout.prop(self, 'metric')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Path")
        self.inputs.new('SvCurveSocket', "Profile")
        self.inputs.new('SvStringsSocket', "VSections").prop_name = 'profiles_count'
        self.inputs.new('SvStringsSocket', "V")
        self.inputs.new('SvStringsSocket', "Resolution").prop_name = 'resolution'
        p = self.inputs.new('SvVerticesSocket', "Normal")
        p.use_prop = True
        p.default_property = (0.0, 0.0, 1.0)
        self.outputs.new('SvSurfaceSocket', "Surface")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        path_s = self.inputs['Path'].sv_get()
        profile_s = self.inputs['Profile'].sv_get()
        if self.explicit_v:
            v_s = self.inputs['V'].sv_get()
            v_s = ensure_nesting_level(v_s, 3)
        else:
            v_s = [[[]]]
        profiles_count_s = self.inputs['VSections'].sv_get()
        resolution_s = self.inputs['Resolution'].sv_get()
        normal_s = self.inputs['Normal'].sv_get()

        path_s = ensure_nesting_level(path_s, 2, data_types=(SvCurve,))
        profile_s = ensure_nesting_level(profile_s, 3, data_types=(SvCurve,))
        resolution_s = ensure_nesting_level(resolution_s, 2)
        normal_s = ensure_nesting_level(normal_s, 3)
        profiles_count_s = ensure_nesting_level(profiles_count_s, 2)

        surfaces_out = []
        for params in zip_long_repeat(path_s, profile_s, v_s, profiles_count_s, resolution_s, normal_s):
            new_surfaces = []
            for path, profiles, vs, profiles_count, resolution, normal in zip_long_repeat(*params):
                path = SvNurbsCurve.to_nurbs(path)
                if path is None:
                    raise Exception("Path is not a NURBS curve!")
                profiles = [SvNurbsCurve.to_nurbs(profile) for profile in profiles]
                if any(p is None for p in profiles):
                    raise Exception("Some of profiles are not NURBS curves!")
                if self.explicit_v:
                    ts = np.array(vs)
                else:
                    ts = None
                surface = nurbs_sweep(path, profiles,
                                    ts = ts,
                                    min_profiles = profiles_count,
                                    algorithm = self.algorithm,
                                    knots_u = self.u_knots_mode,
                                    metric = self.metric,
                                    implementation = self.nurbs_implementation,
                                    resolution = resolution,
                                    normal = np.array(normal))
                new_surfaces.append(surface)
            surfaces_out.append(new_surfaces)

        self.outputs['Surface'].sv_set(surfaces_out)

def register():
    bpy.utils.register_class(SvNurbsSweepNode)

def unregister():
    bpy.utils.unregister_class(SvNurbsSweepNode)
