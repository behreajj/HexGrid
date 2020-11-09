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
    "name": "Create Hex Grid",
    "author": "Jeremy Behreandt",
    "version": (0, 1),
    "blender": (2, 90, 1),
    "category": "Add Mesh",
    "description": "Creates a hexagon grid.",
    "tracker_url": "https://github.com/behreajj/HexGrid"
}


class HexGridMaker(bpy.types.Operator):
    """Creates a grid of hexagons"""

    bl_idname = "mesh.primitive_hexgrid_add"
    bl_label = "Hex Grid"
    bl_options = {"REGISTER", "UNDO"}

    rings: IntProperty(
        name="Rings",
        description="Number of rings in grid",
        min=1,
        soft_max=32,
        default=4,
        step=1)

    cell_radius: FloatProperty(
        name="Cell Radius",
        description="Radius of each hexagon cell",
        min=0.0001,
        soft_max=100.0,
        step=1,
        precision=3,
        default=0.5)

    cell_margin: FloatProperty(
        name="Cell Margin",
        description="Margin between each hexagon cell",
        min=0.0,
        soft_max=99.0,
        step=1,
        precision=3,
        default=0.0325)

    orientation: FloatProperty(
        name="Rotation",
        description="Rotation of hexagonal grid",
        soft_min=-math.pi,
        soft_max=math.pi,
        default=0.0,
        subtype="ANGLE",
        unit="ROTATION")

    merge_verts: BoolProperty(
        name="Merge Vertices",
        description="Merge overlapping hexagon cell vertices (when margin is 0.0)",
        default=False)

    face_type: EnumProperty(
        items=[
            ("NGON", "NGon", "Fill with a hexagon", 1),
            ("PENTA", "Pentagon Fan",
             "Fill with 3 pentagons sharing a central vertex; creates 3 extra vertices", 2),
            ("QUAD", "Quad Fan", "Fill with 3 quadrilaterals sharing a central vertex", 3),
            ("TRI", "Tri Fan", "Fill with 6 triangles sharing a central vertex", 4),
            ("WIRE", "Wire", "Do not fill; use only edges", 5)],
        name="Face Type",
        default="NGON",
        description="How to fill each hexagon cell")

    extrude_lb: FloatProperty(
        name="Extrude Lower",
        description="Extrusion lower bound on the z axis",
        min=0.0,
        soft_max=1.0,
        step=1,
        precision=3,
        default=0.0)

    extrude_ub: FloatProperty(
        name="Extrude Upper",
        description="Extrusion upper bound on the z axis",
        min=0.0,
        soft_max=2.0,
        step=1,
        precision=3,
        default=0.0)

    terrain_type: EnumProperty(
        items=[
            ("UNIFORM", "Uniform", "Extrude by a uniform amount", 1),
            ("NOISE", "Noise", "Extrude with Perlin noise", 2)
        ],
        name="Terrain Type",
        default="UNIFORM",
        description="How to extrude each hexagon cell")

    noise_offset: FloatVectorProperty(
        name="Noise Offset",
        description="Offset added to noise input",
        default=(0.0, 0.0, 0.0),
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        precision=3,
        subtype="TRANSLATION")

    noise_scale: FloatProperty(
        name="Noise Scale",
        description="Scalar multiplied with noise input",
        soft_min=0.0,
        soft_max=10.0,
        step=1,
        precision=3,
        default=1.0)

    noise_basis: EnumProperty(
        items=[
            ("BLENDER", "Blender", "", 1),
            ("PERLIN_ORIGINAL", "Perlin Original", "", 2),
            ("PERLIN_NEW", "Perlin New", "", 3),
            ("VORONOI_F1", "Voronoi F1", "", 4),
            ("VORONOI_F2", "Voronoi F2", "", 5),
            ("VORONOI_F3", "Voronoi F3", "", 6),
            ("VORONOI_F4", "Voronoi F4", "", 7),
            ("VORONOI_F2F1", "Voronoi F2 F1", "", 8),
            ("VORONOI_CRACKLE", "Voronoi Crackle", "", 9),
            ("CELLNOISE", "Cell Noise", "", 10)],
        name="Noise Basis",
        default="BLENDER",
        description="Underlying noise algorithm to use")

    def execute(self, context):
        bm = bmesh.new()

        hex_faces = HexGridMaker.grid_hex(
            bm=bm,
            rings=self.rings,
            cell_radius=self.cell_radius,
            cell_margin=self.cell_margin,
            face_type=self.face_type,
            orientation=self.orientation,
            merge_verts=self.merge_verts)

        if self.face_type != "WIRE":
            HexGridMaker.extrude_hexagons(
                bm=bm,
                faces=hex_faces,
                extrude_lb=self.extrude_lb,
                extrude_ub=self.extrude_ub,
                terrain_type=self.terrain_type,
                noise_offset=self.noise_offset,
                noise_scale=self.noise_scale,
                noise_basis=self.noise_basis,
                merge_verts=self.merge_verts)

        mesh_data = bpy.data.meshes.new("Hex.Grid")
        # TODO: Consider vertex groups... All, Centers, Edges

        bm.to_mesh(mesh_data)
        bm.free()
        mesh_obj = bpy.data.objects.new(mesh_data.name, mesh_data)
        mesh_obj.rotation_mode = "QUATERNION"
        context.scene.collection.objects.link(mesh_obj)

        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        return context.area.type == "VIEW_3D"

    @staticmethod
    def grid_hex(
            bm=None,
            rings=1,
            cell_radius=0.5,
            cell_margin=0.0,
            face_type="NGON",
            orientation=0.0,
            merge_verts=False) -> list:

        # Validate input arguments.
        verif_rings = 1 if rings < 1 else rings
        verif_rad = max(0.000001, cell_radius)
        verif_margin = max(0.0, cell_margin)

        # Pentagonal faces subdivide edges that share a boundary with edges that
        # remain undivided, leading to issues.
        verif_merge = merge_verts and verif_margin == 0.0 and face_type != "PENTA"

        # Intermediate calculations.
        sqrt_3 = 3.0 ** 0.5  # 1.7320508075688772
        altitude = sqrt_3 * verif_rad
        rad_1_5 = verif_rad * 1.5
        pad_rad = max(0.000001, verif_rad - verif_margin)

        half_alt = altitude * 0.5
        half_rad = pad_rad * 0.5
        rad_rt3_2 = half_rad * sqrt_3

        i_max = verif_rings - 1
        i_min = -i_max

        verts = []
        faces = []

        for i in range(i_min, i_max + 1):
            j_min = max(i_min, i_min - i)
            j_max = min(i_max, i_max - i)
            i_alt = i * altitude

            for j in range(j_min, j_max + 1):

                # Hexagon center.
                x = i_alt + j * half_alt
                y = j * rad_1_5

                # Hexagon edges.
                left = x - rad_rt3_2
                right = x + rad_rt3_2
                top = y + half_rad
                bottom = y - half_rad

                # Vertices on hexagon edge starting at the top center vertex, then
                # moving counter- clockwise to the top right shoulder vertex.
                hex_vs = [
                    bm.verts.new((x, y + pad_rad, 0.0)),
                    bm.verts.new((left, top, 0.0)),
                    bm.verts.new((left, bottom, 0.0)),
                    bm.verts.new((x, y - pad_rad, 0.0)),
                    bm.verts.new((right, bottom, 0.0)),
                    bm.verts.new((right, top, 0.0))]
                hex_faces = []

                # Insert hexagon center for tri- and quad-fan face pattern.
                if face_type == 'TRI':
                    hex_vs.insert(0, bm.verts.new((x, y, 0.0)))

                    # Six triangles.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[2]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[2], hex_vs[3]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[3], hex_vs[4]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[4], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[5], hex_vs[6]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[6], hex_vs[1]]))

                elif face_type == 'QUAD':
                    hex_vs.insert(0, bm.verts.new((x, y, 0.0)))

                    # Three quadrilaterals.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[2], hex_vs[3]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[3], hex_vs[4], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[5], hex_vs[6], hex_vs[1]]))

                elif face_type == 'PENTA':

                    # Calculate midpoints.
                    mp0 = 0.5 * (hex_vs[0].co + hex_vs[1].co)
                    mp1 = 0.5 * (hex_vs[2].co + hex_vs[3].co)
                    mp2 = 0.5 * (hex_vs[4].co + hex_vs[5].co)

                    # Insert center and midpoints.
                    hex_vs.insert(0, bm.verts.new((x, y, 0.0)))
                    hex_vs.insert(2, bm.verts.new((mp0[0], mp0[1], 0.0)))
                    hex_vs.insert(5, bm.verts.new((mp1[0], mp1[1], 0.0)))
                    hex_vs.insert(8, bm.verts.new((mp2[0], mp2[1], 0.0)))

                    # Three pentagons.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[2], hex_vs[3], hex_vs[4], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[5], hex_vs[6], hex_vs[7], hex_vs[8]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[8], hex_vs[9], hex_vs[1], hex_vs[2]]))

                elif face_type == 'WIRE':
                    bm.edges.new([hex_vs[0], hex_vs[1]])
                    bm.edges.new([hex_vs[1], hex_vs[2]])
                    bm.edges.new([hex_vs[2], hex_vs[3]])
                    bm.edges.new([hex_vs[3], hex_vs[4]])
                    bm.edges.new([hex_vs[4], hex_vs[5]])
                    bm.edges.new([hex_vs[5], hex_vs[0]])

                else:
                    # "NGON" is the default case.
                    hex_faces.append(bm.faces.new(hex_vs))

                verts.append(hex_vs)
                faces.append(hex_faces)

        # Remove duplicate vertices on hexagon edges.
        if verif_merge:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.000001)

        # Ensure vertices have indices.
        bm.verts.sort(key=HexGridMaker.vertex_comparator)
        bm.verts.index_update()

        # Find dimensions of grid.
        lb, ub = HexGridMaker.calc_dimensions(bm)
        width = ub[0] - lb[0]
        height = ub[1] - lb[1]
        x_inv = 1.0 / width
        y_inv = 1.0 / height

        # Calculate UV coordinates.
        # This will stretch UVs to fill map, without
        # preserving aspect ratio (width / height).
        vts = []
        for vert in bm.verts:
            v = vert.co
            vt_x = (v[0] - lb[0]) * x_inv
            vt_y = (v[1] - lb[1]) * y_inv
            vts.append((vt_x, vt_y))

        # Create or verify UV Map.
        uv_layer = bm.loops.layers.uv.verify()
        for face in bm.faces:
            for loop in face.loops:
                loop[uv_layer].uv = vts[loop.vert.index]

        # Transform BMesh.
        rot_mat = mathutils.Matrix.Rotation(
            orientation, 4, (0.0, 0.0, 1.0))
        bmesh.ops.rotate(bm, matrix=rot_mat, verts=bm.verts)

        # Update normals, jic.
        bm.normal_update()

        return faces

    @staticmethod
    def extrude_hexagons(
            bm=None,
            faces=None,
            extrude_lb=0.000001,
            extrude_ub=1.0,
            terrain_type="UNIFORM",
            noise_offset=(0.0, 0.0, 0.0),
            noise_scale=1.0,
            noise_basis="BLENDER",
            merge_verts=False):

        # Validate input arguments.
        verif_lb = min(extrude_lb, extrude_ub)
        verif_ub = max(extrude_lb, extrude_ub)
        if verif_lb < 0.000001 and verif_ub < 0.000001:
            return

        if merge_verts:
            result = bmesh.ops.extrude_face_region(
                bm,
                geom=bm.faces,
                use_keep_orig=True)

            # Filter vertices out of results.
            geom = result['geom']
            new_verts = []
            for elm in geom:
                if isinstance(elm, bmesh.types.BMVert):
                    new_verts.append(elm)

            bmesh.ops.translate(bm, verts=new_verts,
                                vec=(0.0, 0.0, verif_ub))
        else:
            for hex_faces in faces:
                # Extrude does not translate.
                result = bmesh.ops.extrude_face_region(
                    bm,
                    geom=hex_faces,
                    use_keep_orig=True)

                # Filter vertices out of results.
                geom = result['geom']
                new_verts = []
                for elm in geom:
                    if isinstance(elm, bmesh.types.BMVert):
                        new_verts.append(elm)

                # TODO: Consider linear and spherical falloff, cosine wave
                if terrain_type == "NOISE":

                    # Find the center point of all the faces.
                    center = mathutils.Vector((0.0, 0.0, 0.0))
                    for hex_face in hex_faces:
                        center += hex_face.calc_center_median()
                    center /= len(hex_faces)

                    # Offset and scale the noise input.
                    noise_in = noise_offset + noise_scale * center

                    # Returns a value in [-1, 1] that needs to be converted to [0, 1].
                    fac = mathutils.noise.noise(
                        noise_in, noise_basis=noise_basis)
                    fac *= 0.5
                    fac += 0.5
                    z = (1.0 - fac) * verif_lb + fac * verif_ub
                    bmesh.ops.translate(bm, verts=new_verts, vec=(0.0, 0.0, z))

                else:
                    # "UNIFORM" is the default case.
                    bmesh.ops.translate(bm, verts=new_verts,
                                        vec=(0.0, 0.0, verif_ub))

        bm.normal_update()

    @staticmethod
    def calc_dimensions(bm=None) -> tuple:

        # Initialize to an arbitrarily large +/- value.
        lb = [1000000.0, 1000000.0, 1000000.0]
        ub = [-1000000.0, -1000000.0, -1000000.0]

        verts = bm.verts
        for vert in verts:
            co = vert.co

            lb[0] = min(co[0], lb[0])
            lb[1] = min(co[1], lb[1])
            lb[2] = min(co[2], lb[2])

            ub[0] = max(co[0], ub[0])
            ub[1] = max(co[1], ub[1])
            ub[2] = max(co[2], ub[2])

        return lb, ub

    @staticmethod
    def vertex_comparator(a) -> float:
        aco = a.co
        heading = math.atan2(aco[1], aco[0]) % math.tau
        mag = (aco[0] ** 2 + aco[1] ** 2 + aco[2] ** 2) ** 0.5
        return heading * mag


def menu_func(self, context):

    # To find an icon String, go to Edit > Preferences > Add-ons,
    # then enable Icon Viewer. Then, in the Console Editor window,
    # click on the Icon Viewer button.
    self.layout.operator(HexGridMaker.bl_idname, icon="SEQ_CHROMA_SCOPE")


def register():
    bpy.utils.register_class(HexGridMaker)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(HexGridMaker)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
