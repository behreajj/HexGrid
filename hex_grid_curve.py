import bpy
import bmesh
import math
import mathutils
from bpy.props import (
    BoolProperty,
    IntProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty)


bl_info = {
    "name": "Create Hex Grid Curve",
    "author": "Jeremy Behreandt",
    "version": (0, 1),
    "blender": (4, 1, 0),
    "category": "Add Curve",
    "description": "Creates a hexagon grid curve.",
    "tracker_url": "https://github.com/behreajj/HexGrid"
}


class HexGridCurveMaker(bpy.types.Operator):
    """Creates a grid of hexagons"""

    bl_idname = "curve.primitive_hexgrid_add"
    bl_label = "Hex Grid"
    bl_options = {"REGISTER", "UNDO"}

    rings: IntProperty(
        name="Rings",
        description="Number of rings in grid",
        min=1,
        soft_max=32,
        default=4,
        step=1) # type: ignore

    cell_radius: FloatProperty(
        name="Cell Radius",
        description="Radius of each hexagon cell",
        min=0.0001,
        soft_max=100.0,
        step=1,
        precision=3,
        default=0.5) # type: ignore

    cell_margin: FloatProperty(
        name="Cell Margin",
        description="Margin between each hexagon cell",
        min=0.0,
        soft_max=99.0,
        step=1,
        precision=3,
        default=0.0325) # type: ignore
    
    straight_edge: EnumProperty(
        items=[
            ("FREE", "Free", "Free", 1),
            ("VECTOR", "Vector", "Vector", 2)],
        name="Handle Type",
        default="FREE",
        description="Handle type to use for straight edges") # type: ignore

    res_u: IntProperty(
        name="Resolution",
        description="Corner resolution",
        min=1,
        soft_max=64,
        default=12) # type: ignore

    fill_mode: EnumProperty(
        items=[
            ("NONE", "None", "None", 1),
            ("BACK", "Back", "Back", 2),
            ("FRONT", "Front", "Front", 3),
            ("BOTH", "Both", "Both", 4)],
        name="Fill Mode",
        default="BOTH",
        description="Fill mode to use") # type: ignore

    extrude_thick: FloatProperty(
        name="Extrude",
        description="Extrusion thickness",
        min=0.0,
        soft_max=1.0,
        step=1,
        precision=3,
        default=0.0) # type: ignore

    extrude_off: FloatProperty(
        name="Offset",
        description="Extrusion offset",
        min=-1.0,
        max=1.0,
        step=1,
        precision=3,
        subtype="FACTOR",
        default=0.0) # type: ignore
    
    def execute(self, context):
        # Constants.
        eps = 0.000001
        k = 0.5522847498307936
        o_3 = 1.0 / 3.0
        t_3 = 2.0 / 3.0
        sqrt_3 = 1.7320508075688772 #  3.0 ** 0.5

        # Unpack arguments.
        verif_rings = 1 if self.rings < 1 else self.rings
        verif_rad = max(eps, self.cell_radius)
        verif_margin = max(0.0, self.cell_margin)
        verif_rounding = 0.0
        straight_edge = self.straight_edge

        is_straight = verif_rounding <= 0.0
        is_circle = verif_rounding >= 1.0
        is_rounded = (not is_straight) \
            and (not is_circle)

        # Intermediate calculations.
        extent = sqrt_3 * verif_rad
        rad_1_5 = verif_rad * 1.5
        pad_rad = max(eps, verif_rad - verif_margin)
        half_ext = extent * 0.5
        one_round = 1.0 - verif_rounding
        handle_mag = math.tan(math.tau / (4 * 6)) * (4 / 3) * pad_rad

        # Added to hexagon center to find corners.
        half_rad = pad_rad * 0.5
        rad_rt3_2 = half_rad * sqrt_3

        i_max = verif_rings - 1
        i_min = -i_max

        crv_data = bpy.data.curves.new("Hex.Grid", "CURVE")
        crv_data.dimensions = "2D"
        crv_data.fill_mode = self.fill_mode
        crv_data.extrude = self.extrude_thick
        crv_data.offset = self.extrude_off
        crv_splines = crv_data.splines

        # See https://www.redblobgames.com/grids/hexagons/implementation.html#shape-hexagon
        for i in range(i_min, i_max + 1):
            j_min = max(i_min, i_min - i)
            j_max = min(i_max, i_max - i)
            i_ext = i * extent

            for j in range(j_min, j_max + 1):
                # Hexagon center.
                x = i_ext + j * half_ext
                y = j * rad_1_5

                # Hexagon edges.
                left = x - rad_rt3_2
                right = x + rad_rt3_2
                top = y + half_rad
                bottom = y - half_rad

                # Hexagon vertices, beginning at top center
                # moving counter clockwise.
                v0 = (x, y + pad_rad, 0.0)
                v1 = (left, top, 0.0)
                v2 = (left, bottom, 0.0)
                v3 = (x, y - pad_rad, 0.0)
                v4 = (right, bottom, 0.0)
                v5 = (right, top, 0.0)

                spline = crv_splines.new("BEZIER")
                spline.use_cyclic_u = True
                spline.resolution_u = self.res_u
                bz_pts = spline.bezier_points

                if is_straight:
                    bz_pts.add(5)
                    kn0 = bz_pts[0]
                    kn1 = bz_pts[1]
                    kn2 = bz_pts[2]
                    kn3 = bz_pts[3]
                    kn4 = bz_pts[4]
                    kn5 = bz_pts[5]
                    
                    kn0.co = v0
                    kn1.co = v1
                    kn2.co = v2
                    kn3.co = v3
                    kn4.co = v4
                    kn5.co = v5

                    kn0.handle_left_type = straight_edge
                    kn1.handle_left_type = straight_edge
                    kn2.handle_left_type = straight_edge
                    kn3.handle_left_type = straight_edge
                    kn4.handle_left_type = straight_edge
                    kn5.handle_left_type = straight_edge

                    kn0.handle_right_type = straight_edge
                    kn1.handle_right_type = straight_edge
                    kn2.handle_right_type = straight_edge
                    kn3.handle_right_type = straight_edge
                    kn4.handle_right_type = straight_edge
                    kn5.handle_right_type = straight_edge

                    kn0.handle_left = (
                        t_3 * v0[0] + o_3 * v5[0],
                        t_3 * v0[1] + o_3 * v5[1],
                        t_3 * v0[2] + o_3 * v5[2])
                    kn1.handle_left = (
                        t_3 * v1[0] + o_3 * v0[0],
                        t_3 * v1[1] + o_3 * v0[1],
                        t_3 * v1[2] + o_3 * v0[2])
                    kn2.handle_left = (
                        t_3 * v2[0] + o_3 * v1[0],
                        t_3 * v2[1] + o_3 * v1[1],
                        t_3 * v2[2] + o_3 * v1[2])
                    kn3.handle_left = (
                        t_3 * v3[0] + o_3 * v2[0],
                        t_3 * v3[1] + o_3 * v2[1],
                        t_3 * v3[2] + o_3 * v2[2])
                    kn4.handle_left = (
                        t_3 * v4[0] + o_3 * v3[0],
                        t_3 * v4[1] + o_3 * v3[1],
                        t_3 * v4[2] + o_3 * v3[2])
                    kn5.handle_left = (
                        t_3 * v5[0] + o_3 * v4[0],
                        t_3 * v5[1] + o_3 * v4[1],
                        t_3 * v5[2] + o_3 * v4[2])

                    kn0.handle_right = (
                        t_3 * v0[0] + o_3 * v1[0],
                        t_3 * v0[1] + o_3 * v1[1],
                        t_3 * v0[2] + o_3 * v1[2])
                    kn1.handle_right = (
                        t_3 * v1[0] + o_3 * v2[0],
                        t_3 * v1[1] + o_3 * v2[1],
                        t_3 * v1[2] + o_3 * v2[2])
                    kn2.handle_right = (
                        t_3 * v2[0] + o_3 * v3[0],
                        t_3 * v2[1] + o_3 * v3[1],
                        t_3 * v2[2] + o_3 * v3[2])
                    kn3.handle_right = (
                        t_3 * v3[0] + o_3 * v4[0],
                        t_3 * v3[1] + o_3 * v4[1],
                        t_3 * v3[2] + o_3 * v4[2])
                    kn4.handle_right = (
                        t_3 * v4[0] + o_3 * v5[0],
                        t_3 * v4[1] + o_3 * v5[1],
                        t_3 * v4[2] + o_3 * v5[2])
                    kn5.handle_right = (
                        t_3 * v5[0] + o_3 * v0[0],
                        t_3 * v5[1] + o_3 * v0[1],
                        t_3 * v5[2] + o_3 * v0[2])
                else:
                    # Calculate midpoints.
                    mp0 = (
                        (v0[0] + v1[0]) * 0.5,
                        (v0[1] + v1[1]) * 0.5,
                        (v0[2] + v1[2]) * 0.5)
                    mp1 = (
                        (v1[0] + v2[0]) * 0.5,
                        (v1[1] + v2[1]) * 0.5,
                        (v1[2] + v2[2]) * 0.5)
                    mp2 = (
                        (v2[0] + v3[0]) * 0.5,
                        (v2[1] + v3[1]) * 0.5,
                        (v2[2] + v3[2]) * 0.5)
                    mp3 = (
                        (v3[0] + v4[0]) * 0.5,
                        (v3[1] + v4[1]) * 0.5,
                        (v3[2] + v4[2]) * 0.5)
                    mp4 = (
                        (v4[0] + v5[0]) * 0.5,
                        (v4[1] + v5[1]) * 0.5,
                        (v4[2] + v5[2]) * 0.5)
                    mp5 = (
                        (v5[0] + v0[0]) * 0.5,
                        (v5[1] + v0[1]) * 0.5,
                        (v5[2] + v0[2]) * 0.5)

                    if is_circle:
                        bz_pts.add(5)
                        kn0 = bz_pts[0]
                        kn1 = bz_pts[1]
                        kn2 = bz_pts[2]
                        kn3 = bz_pts[3]
                        kn4 = bz_pts[4]
                        kn5 = bz_pts[5]

                        kn0.co = mp0
                        kn1.co = mp1
                        kn2.co = mp2
                        kn3.co = mp3
                        kn4.co = mp4
                        kn5.co = mp5

                        kn0.handle_left_type = "FREE"
                        kn1.handle_left_type = "FREE"
                        kn2.handle_left_type = "FREE"
                        kn3.handle_left_type = "FREE"
                        kn4.handle_left_type = "FREE"
                        kn5.handle_left_type = "FREE"

                        kn0.handle_right_type = "FREE"
                        kn1.handle_right_type = "FREE"
                        kn2.handle_right_type = "FREE"
                        kn3.handle_right_type = "FREE"
                        kn4.handle_right_type = "FREE"
                        kn5.handle_right_type = "FREE"

                        #TODO: Set left and right handles.
                    else:
                        # https://github.com/behreajj/CamZup/blob/f0adca3a58aab7568bf60ccc15e67f35d326d72d/src/camzup/core/Curve2.java#L1041
                        # https://github.com/behreajj/CamZup/blob/00696e7d3b28fa416ed5207029f870b6a6f656ef/src/camzup/core/Mesh2.java#L764

                        co00_l = (
                            one_round * v0[0] + verif_rounding * mp5[0],
                            one_round * v0[1] + verif_rounding * mp5[1],
                            one_round * v0[2] + verif_rounding * mp5[2])
                        co01_r = (
                            one_round * v0[0] + verif_rounding * mp0[0],
                            one_round * v0[1] + verif_rounding * mp0[1],
                            one_round * v0[2] + verif_rounding * mp0[2])
                        
                        co02_l = (
                            one_round * v1[0] + verif_rounding * mp0[0],
                            one_round * v1[1] + verif_rounding * mp0[1],
                            one_round * v1[2] + verif_rounding * mp0[2])
                        co03_r = (
                            one_round * v1[0] + verif_rounding * mp1[0],
                            one_round * v1[1] + verif_rounding * mp1[1],
                            one_round * v1[2] + verif_rounding * mp1[2])
                        
                        co04_l = (
                            one_round * v2[0] + verif_rounding * mp1[0],
                            one_round * v2[1] + verif_rounding * mp1[1],
                            one_round * v2[2] + verif_rounding * mp1[2])
                        co05_r = (
                            one_round * v2[0] + verif_rounding * mp2[0],
                            one_round * v2[1] + verif_rounding * mp2[1],
                            one_round * v2[2] + verif_rounding * mp2[2])
                        
                        co06_l = (
                            one_round * v3[0] + verif_rounding * mp2[0],
                            one_round * v3[1] + verif_rounding * mp2[1],
                            one_round * v3[2] + verif_rounding * mp2[2])
                        co07_r = (
                            one_round * v3[0] + verif_rounding * mp3[0],
                            one_round * v3[1] + verif_rounding * mp3[1],
                            one_round * v3[2] + verif_rounding * mp3[2])
                        
                        co08_l = (
                            one_round * v4[0] + verif_rounding * mp3[0],
                            one_round * v4[1] + verif_rounding * mp3[1],
                            one_round * v4[2] + verif_rounding * mp3[2])
                        co09_r = (
                            one_round * v4[0] + verif_rounding * mp4[0],
                            one_round * v4[1] + verif_rounding * mp4[1],
                            one_round * v4[2] + verif_rounding * mp4[2])
                        
                        co10_l = (
                            one_round * v5[0] + verif_rounding * mp4[0],
                            one_round * v5[1] + verif_rounding * mp4[1],
                            one_round * v5[2] + verif_rounding * mp4[2])
                        co11_r = (
                            one_round * v5[0] + verif_rounding * mp5[0],
                            one_round * v5[1] + verif_rounding * mp5[1],
                            one_round * v5[2] + verif_rounding * mp5[2])

                        bz_pts.add(11)
                        kn00_l = bz_pts[0]
                        kn01_r = bz_pts[1]
                        kn02_l = bz_pts[2]
                        kn03_r = bz_pts[3]
                        kn04_l = bz_pts[4]
                        kn05_r = bz_pts[5]
                        kn06_l = bz_pts[6]
                        kn07_r = bz_pts[7]
                        kn08_l = bz_pts[8]
                        kn09_r = bz_pts[9]
                        kn10_l = bz_pts[10]
                        kn11_r = bz_pts[11]

        # TODO: Look at Camzup for Bezier circle, see if commit
        # history still has a copy of corner rounding method?

        crv_obj = bpy.data.objects.new(crv_data.name, crv_data)
        crv_obj.location = context.scene.cursor.location
        context.scene.collection.objects.link(crv_obj)
        return {"FINISHED"}


def menu_func(self, context):
    self.layout.operator(HexGridCurveMaker.bl_idname, icon="SEQ_CHROMA_SCOPE")

def register():
    bpy.utils.register_class(HexGridCurveMaker)
    bpy.types.VIEW3D_MT_curve_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(HexGridCurveMaker)
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func)
