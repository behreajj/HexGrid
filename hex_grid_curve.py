import bpy # type: ignore
from bpy.props import ( # type: ignore
    IntProperty,
    EnumProperty,
    FloatProperty)


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
        min=-100.0,
        soft_max=100.0,
        step=1,
        precision=3,
        default=0.0325) # type: ignore
    
    rounding: FloatProperty(
        name="Rounding",
        description="Percentage by which to round corners.",
        default=0.0,
        step=1,
        precision=3,
        min=0.0,
        max=1.0,
        subtype="FACTOR")  # type: ignore
    
    straight_edge: EnumProperty(
        items=[
            ("ALIGNED", "Aligned", "Aligned", 1),
            ("FREE", "Free", "Free", 2),
            ("VECTOR", "Vector", "Vector", 3)],
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
        o_3 = 1.0 / 3.0
        t_3 = 2.0 / 3.0
        sqrt_3 = 1.7320508075688772 # 3.0 ** 0.5
        handle_fac = t_3
        one_h_fac = 1.0 - handle_fac

        # Unpack arguments.
        verif_rings = 1 if self.rings < 1 else self.rings
        verif_rad = max(eps, self.cell_radius)
        # Allow negative cell margins so that the seed of life geometric
        # pattern can be created.
        verif_margin = self.cell_margin
        verif_rounding = self.rounding
        straight_handle_type = self.straight_edge

        is_straight = verif_rounding <= 0.0
        is_circle = verif_rounding >= 1.0
        if is_straight and straight_handle_type == "ALIGNED":
            straight_handle_type = "VECTOR"
        
        corner_handle_type = "FREE"
        if straight_handle_type == "ALIGNED":
            corner_handle_type = "ALIGNED"

        # Intermediate calculations.
        extent = sqrt_3 * verif_rad
        rad_1_5 = verif_rad * 1.5
        pad_rad = max(eps, verif_rad - verif_margin)
        half_ext = extent * 0.5
        one_round = 1.0 - verif_rounding

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
                v = [
                    (x, y + pad_rad, 0.0),
                    (left, top, 0.0),
                    (left, bottom, 0.0),
                    (x, y - pad_rad, 0.0),
                    (right, bottom, 0.0),
                    (right, top, 0.0) ]

                spline = crv_splines.new("BEZIER")
                spline.use_cyclic_u = True
                spline.resolution_u = self.res_u
                bz_pts = spline.bezier_points

                if is_straight:
                    bz_pts.add(5)

                    kn_idx_curr = 0
                    for kn in bz_pts:
                        kn_idx_prev = (kn_idx_curr - 1) % 6
                        kn_idx_next = (kn_idx_curr + 1) % 6

                        co_curr = v[kn_idx_curr]
                        co_prev = v[kn_idx_prev]
                        co_next = v[kn_idx_next]

                        kn.co = co_curr
                        kn.handle_left_type = straight_handle_type
                        kn.handle_right_type = straight_handle_type
                        kn.handle_left = (
                            t_3 * co_curr[0] + o_3 * co_prev[0],
                            t_3 * co_curr[1] + o_3 * co_prev[1],
                            t_3 * co_curr[2] + o_3 * co_prev[2])
                        kn.handle_right = (
                            t_3 * co_curr[0] + o_3 * co_next[0],
                            t_3 * co_curr[1] + o_3 * co_next[1],
                            t_3 * co_curr[2] + o_3 * co_next[2])

                        kn_idx_curr = kn_idx_curr + 1
                else:
                    # Calculate midpoints.
                    mp = [(0.0, 0.0, 0.0)] * 6
                    for mp_idx in range(0, 6):
                        mp_idx_next = (mp_idx + 1) % 6
                        v_curr = v[mp_idx]
                        v_next = v[mp_idx_next]
                        mp[mp_idx] = (
                            (v_curr[0] + v_next[0]) * 0.5,
                            (v_curr[1] + v_next[1]) * 0.5,
                            (v_curr[2] + v_next[2]) * 0.5)

                    if is_circle:
                        bz_pts.add(5)

                        kn_idx_curr = 0
                        for kn in bz_pts:
                            v_idx_next = (kn_idx_curr + 1) % 6                            
                            v_prev = v[kn_idx_curr]
                            v_next = v[v_idx_next]
                            co = mp[kn_idx_curr]

                            kn.co = co
                            kn.handle_left_type = corner_handle_type
                            kn.handle_right_type = corner_handle_type
                            kn.handle_left = (
                                    one_h_fac * co[0] + handle_fac * v_prev[0],
                                    one_h_fac * co[1] + handle_fac * v_prev[1],
                                    one_h_fac * co[2] + handle_fac * v_prev[2])
                            kn.handle_right = (
                                    one_h_fac * co[0] + handle_fac * v_next[0],
                                    one_h_fac * co[1] + handle_fac * v_next[1],
                                    one_h_fac * co[2] + handle_fac * v_next[2])
                            kn_idx_curr = kn_idx_curr + 1
                    else:
                        bz_pts.add(11)

                        kn_idx_curr = 0
                        for kn in bz_pts:
                            v_idx_curr = kn_idx_curr // 2
                            v_curr = v[v_idx_curr]
                            
                            is_even = kn_idx_curr % 2 != 1
                            if is_even:
                                v_idx_prev = (v_idx_curr - 1) % 6
                                v_prev = v[v_idx_prev]
                                mp_prev = mp[v_idx_prev]

                                co_curr = (
                                    one_round * v_curr[0] + verif_rounding * mp_prev[0],
                                    one_round * v_curr[1] + verif_rounding * mp_prev[1],
                                    one_round * v_curr[2] + verif_rounding * mp_prev[2])
                                
                                co_prev = (
                                    one_round * v_prev[0] + verif_rounding * mp_prev[0],
                                    one_round * v_prev[1] + verif_rounding * mp_prev[1],
                                    one_round * v_prev[2] + verif_rounding * mp_prev[2])
                                
                                kn.co = co_curr
                                kn.handle_left_type = straight_handle_type
                                kn.handle_right_type = corner_handle_type
                                kn.handle_left = (
                                    t_3 * co_curr[0] + o_3 * co_prev[0],
                                    t_3 * co_curr[1] + o_3 * co_prev[1],
                                    t_3 * co_curr[2] + o_3 * co_prev[2])
                                kn.handle_right = (
                                    one_h_fac * co_curr[0] + handle_fac * v_curr[0],
                                    one_h_fac * co_curr[1] + handle_fac * v_curr[1],
                                    one_h_fac * co_curr[2] + handle_fac * v_curr[2])
                            else:
                                v_idx_next = (v_idx_curr + 1) % 6
                                mp_next = mp[v_idx_curr]
                                v_next = v[v_idx_next]

                                co_curr = (
                                    one_round * v_curr[0] + verif_rounding * mp_next[0],
                                    one_round * v_curr[1] + verif_rounding * mp_next[1],
                                    one_round * v_curr[2] + verif_rounding * mp_next[2])
                                
                                co_next = (
                                    one_round * v_next[0] + verif_rounding * mp_next[0],
                                    one_round * v_next[1] + verif_rounding * mp_next[1],
                                    one_round * v_next[2] + verif_rounding * mp_next[2])

                                kn.co = co_curr
                                kn.handle_left_type = corner_handle_type
                                kn.handle_right_type = straight_handle_type
                                kn.handle_left = (
                                    one_h_fac * co_curr[0] + handle_fac * v_curr[0],
                                    one_h_fac * co_curr[1] + handle_fac * v_curr[1],
                                    one_h_fac * co_curr[2] + handle_fac * v_curr[2])
                                kn.handle_right = (
                                    t_3 * co_curr[0] + o_3 * co_next[0],
                                    t_3 * co_curr[1] + o_3 * co_next[1],
                                    t_3 * co_curr[2] + o_3 * co_next[2])

                            kn_idx_curr = kn_idx_curr + 1

        crv_obj = bpy.data.objects.new(crv_data.name, crv_data)
        crv_obj.location = context.scene.cursor.location
        context.collection.objects.link(crv_obj)
        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        return context.area.type == "VIEW_3D"

def menu_func(self, context):
    self.layout.operator(HexGridCurveMaker.bl_idname, icon="SEQ_CHROMA_SCOPE")

def register():
    bpy.utils.register_class(HexGridCurveMaker)
    bpy.types.VIEW3D_MT_curve_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(HexGridCurveMaker)
    bpy.types.VIEW3D_MT_curve_add.remove(menu_func)
