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
        description="Rotation of grid as a whole",
        soft_min=-math.pi,
        soft_max=math.pi,
        default=0.0,
        subtype="ANGLE",
        unit="ROTATION")

    merge_verts: BoolProperty(
        name="Merge Vertices",
        description="Merge overlapping hexagon cell vertices when margin is 0.0",
        default=False)

    face_type: EnumProperty(
        items=[
            ("NGON", "NGon", "Fill with a hexagon", 1),
            ("PENTA3", "Pentagon Fan",
             "Fill with 3 pentagons sharing a central vertex; creates 3 extra vertices", 2),
            ("QUAD6", "Quad 6 Fan",
             "Fill with 6 quadrilaterals sharing a central vertex; creates 6 extra vertices", 3),
            ("QUAD3", "Quad 3 Fan",
             "Fill with 3 quadrilaterals sharing a central vertex", 4),
            ("TRI", "Tri Fan", "Fill with 6 triangles sharing a central vertex", 5),
            ("QUAD_CR", "Quad Cross",
             "Fill with 4 quadrilaterals sharing a central vertex; creates 2 extra vertices", 6),
            ("QUAD2", "Quad Split", "Split with 2 quadrilaterlas on a central axis", 7),
            ("PENTA2", "Penta Split", "Split with 2 pentagons on a central axis", 8),
            ("CATALAN_RAY", "Catalan Ray",
             "Fills with triangles by connecting a corner to non-adjacent vertices", 9),
            ("CATALAN_TRI", "Catalan Tri",
             "Fill with a central tri surrounded by 3 peripheral tris", 10),
            ("CATALAN_Z", "Catalan Z",
             "Fill with 4 triangles, with edges forming a z pattern", 11),
            ("WIRE", "Wire", "Do not fill; use only edges", 12),
            ("POINTS", "Points", "Create only center points", 13)],
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
            ("LINEAR", "Linear", "Linear gradient", 2),
            ("SPHERICAL", "Spherical", "Spherical gradient", 3)],
        name="Terrain Type",
        default="UNIFORM",
        description="How to extrude each hexagon cell")

    origin: FloatVectorProperty(
        name="Origin",
        description="Linear gradient origin",
        default=(-1.0, -1.0),
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        precision=3,
        size=2,
        subtype="TRANSLATION")

    destination: FloatVectorProperty(
        name="Destination",
        description="Linear gradient destination",
        default=(1.0, 1.0),
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        precision=3,
        size=2,
        subtype="TRANSLATION")

    noise_influence: FloatProperty(
        name="Noise Influence",
        description="Amount that noise contributes to the extrusion",
        default=0.0,
        step=1,
        precision=3,
        min=0.0,
        max=1.0,
        subtype="FACTOR")

    noise_scale: FloatProperty(
        name="Noise Scale",
        description="Scalar multiplied with noise input; values less than 1.0 yield a smoother result",
        soft_min=0.0,
        soft_max=10.0,
        step=1,
        precision=3,
        default=1.0)

    noise_offset: FloatVectorProperty(
        name="Noise Offset",
        description="Offset added to noise input",
        default=(0.0, 0.0, 0.0),
        step=1,
        precision=3,
        subtype="TRANSLATION")

    noise_basis: EnumProperty(
        items=[
            ("BLENDER", "Blender", "Blender", 1),
            ("PERLIN_ORIGINAL", "Perlin Original", "Perlin Original", 2),
            ("PERLIN_NEW", "Perlin New", "Perlin New", 3),
            ("VORONOI_F1", "Voronoi F1", "Voronoi F1", 4),
            ("VORONOI_F2", "Voronoi F2", "Voronoi F2", 5),
            ("VORONOI_F3", "Voronoi F3", "Voronoi F3", 6),
            ("VORONOI_F4", "Voronoi F4", "Voronoi F4", 7),
            ("VORONOI_F2F1", "Voronoi F2 F1", "Voronoi F2 F1", 8),
            ("VORONOI_CRACKLE", "Voronoi Crackle", "Voronoi Crackle", 9),
            ("CELLNOISE", "Cell Noise", "Cell Noise", 10)],
        name="Noise Basis",
        default="BLENDER",
        description="Underlying noise algorithm to use")

    def execute(self, context):
        bm = bmesh.new()

        result = HexGridMaker.grid_hex(
            bm=bm,
            rings=self.rings,
            cell_radius=self.cell_radius,
            cell_margin=self.cell_margin,
            face_type=self.face_type,
            orientation=self.orientation,
            merge_verts=self.merge_verts)

        extruded = False
        if self.face_type not in ["WIRE", "POINTS"]:
            extruded = HexGridMaker.extrude_hexagons(
                bm=bm,
                faces=result["faces"],
                extrude_lb=self.extrude_lb,
                extrude_ub=self.extrude_ub,
                terrain_type=self.terrain_type,
                noise_influence=self.noise_influence,
                noise_scale=self.noise_scale,
                noise_offset=self.noise_offset,
                noise_basis=self.noise_basis,
                origin=self.origin,
                dest=self.destination,
                merge_verts=self.merge_verts)

        mesh_data = bpy.data.meshes.new("Hex.Grid")
        bm.to_mesh(mesh_data)
        bm.free()

        mesh_obj = bpy.data.objects.new(mesh_data.name, mesh_data)
        mesh_obj.rotation_mode = "QUATERNION"
        context.scene.collection.objects.link(mesh_obj)

        #TODO: Make this optional... Turn on/off one vertex group
        # with all or separate vert groups?
        fph = HexGridMaker.faces_per_hexagon(
            face_type=self.face_type)
        if extruded:
            fph *= 2
            fph += HexGridMaker.edges_per_hexagon(
                face_type=self.face_type)
        hex_count = result["hex_count"]

        vert_group = mesh_obj.vertex_groups.new(name="All")
        mesh_polys = mesh_data.polygons
        to_fac = 1.0 / (hex_count - 1.0)

        for mesh_poly in mesh_polys:
            poly_index = mesh_poly.index
            poly_vert_idcs = mesh_poly.vertices
            fac = (poly_index // fph) * to_fac
            vert_group.add(poly_vert_idcs, fac, "REPLACE")

        return {"FINISHED"}

    @classmethod
    def poll(cls, context):
        return context.area.type == "VIEW_3D"

    @staticmethod
    def edges_per_hexagon(face_type="NGON") -> int:
        if face_type == "TRI":
            return 6
        elif face_type == "QUAD2":
            return 6
        elif face_type == "QUAD3":
            return 6
        elif face_type == "QUAD_CR":
            return 8
        elif face_type == "QUAD6":
            return 12
        elif face_type == "NGON":
            return 6
        elif face_type == "PENTA2":
            return 8
        elif face_type == "PENTA3":
            return 9
        elif face_type == "CATALAN_RAY":
            return 6
        elif face_type == "CATALAN_TRI":
            return 6
        elif face_type == "CATALAN_Z":
            return 6
        else:
            return 0

    @staticmethod
    def faces_per_hexagon(face_type="NGON") -> int:
        if face_type == "TRI":
            return 6
        elif face_type == "QUAD2":
            return 2
        elif face_type == "QUAD3":
            return 3
        elif face_type == "QUAD_CR":
            return 4
        elif face_type == "QUAD6":
            return 6
        elif face_type == "NGON":
            return 1
        elif face_type == "PENTA2":
            return 2
        elif face_type == "PENTA3":
            return 3
        elif face_type == "CATALAN_RAY":
            return 4
        elif face_type == "CATALAN_TRI":
            return 4
        elif face_type == "CATALAN_Z":
            return 4
        else:
            return 0

    @staticmethod
    def grid_hex(
            bm=None,
            rings=1,
            cell_radius=0.5,
            cell_margin=0.0,
            face_type="NGON",
            orientation=0.0,
            merge_verts=False) -> dict:

        # Validate input arguments.
        verif_rings = 1 if rings < 1 else rings
        verif_rad = max(0.000001, cell_radius)
        verif_margin = max(0.0, cell_margin)

        # Pentagonal faces subdivide edges that share a boundary with edges that
        # remain undivided, leading to issues.
        verif_merge = merge_verts and verif_margin == 0.0 and face_type != "PENTA3"

        # Intermediate calculations.
        sqrt_3 = 3.0 ** 0.5  # 1.7320508075688772
        extent = sqrt_3 * verif_rad
        rad_1_5 = verif_rad * 1.5
        pad_rad = max(0.000001, verif_rad - verif_margin)

        half_ext = extent * 0.5
        half_rad = pad_rad * 0.5
        rad_rt3_2 = half_rad * sqrt_3

        i_max = verif_rings - 1
        i_min = -i_max

        verts = []
        faces = []

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

                # Vertices on hexagon edge starting at the top center vertex, then
                # moving counter- clockwise to the top right shoulder vertex.
                if face_type == "POINTS":
                    hex_vs = [bm.verts.new((x, y, 0.0))]
                else:
                    hex_vs = [
                        bm.verts.new((x, y + pad_rad, 0.0)),
                        bm.verts.new((left, top, 0.0)),
                        bm.verts.new((left, bottom, 0.0)),
                        bm.verts.new((x, y - pad_rad, 0.0)),
                        bm.verts.new((right, bottom, 0.0)),
                        bm.verts.new((right, top, 0.0))]

                hex_faces = []

                # Insert hexagon center for tri- and quad-fan face pattern.
                if face_type == "TRI":
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

                elif face_type == "QUAD2":

                    # Two quadrilaterals.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[2], hex_vs[3]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[3], hex_vs[4], hex_vs[5], hex_vs[0]]))

                elif face_type == "QUAD3":
                    hex_vs.insert(0, bm.verts.new((x, y, 0.0)))

                    # Three quadrilaterals.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[2], hex_vs[3]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[3], hex_vs[4], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[5], hex_vs[6], hex_vs[1]]))

                elif face_type == "QUAD_CR":
                    # Calculate midpoints.
                    mp0 = 0.5 * (hex_vs[1].co + hex_vs[2].co)
                    mp1 = 0.5 * (hex_vs[4].co + hex_vs[5].co)

                    # Insert center and midpoints.
                    hex_vs.insert(0, bm.verts.new((x, y, 0.0)))
                    hex_vs.insert(3, bm.verts.new((mp0[0], mp0[1], 0.0)))
                    hex_vs.insert(7, bm.verts.new((mp1[0], mp1[1], 0.0)))

                    # Four quadrilaterals.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[2], hex_vs[3]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[3], hex_vs[4], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[5], hex_vs[6], hex_vs[7]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[7], hex_vs[8], hex_vs[1]]))

                elif face_type == "QUAD6":
                    # Calculate midpoints.
                    mp0 = 0.5 * (hex_vs[0].co + hex_vs[1].co)
                    mp1 = 0.5 * (hex_vs[1].co + hex_vs[2].co)
                    mp2 = 0.5 * (hex_vs[2].co + hex_vs[3].co)
                    mp3 = 0.5 * (hex_vs[3].co + hex_vs[4].co)
                    mp4 = 0.5 * (hex_vs[4].co + hex_vs[5].co)
                    mp5 = 0.5 * (hex_vs[5].co + hex_vs[0].co)

                    # Insert center and midpoints.
                    hex_vs.insert(0, bm.verts.new((x, y, 0.0)))
                    hex_vs.insert(2, bm.verts.new((mp0[0], mp0[1], 0.0)))
                    hex_vs.insert(4, bm.verts.new((mp1[0], mp1[1], 0.0)))
                    hex_vs.insert(6, bm.verts.new((mp2[0], mp2[1], 0.0)))
                    hex_vs.insert(8, bm.verts.new((mp3[0], mp3[1], 0.0)))
                    hex_vs.insert(10, bm.verts.new((mp4[0], mp4[1], 0.0)))
                    hex_vs.insert(12, bm.verts.new((mp5[0], mp5[1], 0.0)))

                    # Six quadrilaterals.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[12], hex_vs[1], hex_vs[2]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[2], hex_vs[3], hex_vs[4]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[4], hex_vs[5], hex_vs[6]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[6], hex_vs[7], hex_vs[8]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[8], hex_vs[9], hex_vs[10]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[10], hex_vs[11], hex_vs[12]]))

                elif face_type == "PENTA2":
                    # Calculate midpoints.
                    mp0 = 0.5 * (hex_vs[1].co + hex_vs[2].co)
                    mp1 = 0.5 * (hex_vs[4].co + hex_vs[5].co)

                    # Insert midpoints.
                    hex_vs.insert(2, bm.verts.new((mp0[0], mp0[1], 0.0)))
                    hex_vs.insert(6, bm.verts.new((mp1[0], mp1[1], 0.0)))

                    # Two pentagons.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[2], hex_vs[6], hex_vs[7]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[2], hex_vs[3], hex_vs[4], hex_vs[5], hex_vs[6]]))

                elif face_type == "PENTA3":
                    # Calculate midpoints.
                    mp0 = 0.5 * (hex_vs[0].co + hex_vs[1].co)
                    mp1 = 0.5 * (hex_vs[2].co + hex_vs[3].co)
                    mp2 = 0.5 * (hex_vs[4].co + hex_vs[5].co)

                    # Insert center and midpoints.
                    hex_vs.insert(0, bm.verts.new((x, y, 0.0)))
                    hex_vs.insert(2, bm.verts.new((mp0[0], mp0[1], 0.0)))
                    hex_vs.insert(5, bm.verts.new((mp1[0], mp1[1], 0.0)))
                    hex_vs.insert(8, bm.verts.new((mp2[0], mp2[1], 0.0)))

                    # TODO Rearrange so there is a face at the top ?

                    # Three pentagons.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[2], hex_vs[3], hex_vs[4], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[5], hex_vs[6], hex_vs[7], hex_vs[8]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[8], hex_vs[9], hex_vs[1], hex_vs[2]]))

                elif face_type == "CATALAN_RAY":
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[2]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[2], hex_vs[3]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[3], hex_vs[4]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[4], hex_vs[5]]))

                elif face_type == "CATALAN_TRI":
                    # Central triangle.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[1], hex_vs[3], hex_vs[5]]))

                    # Peripheral triangles.
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[1], hex_vs[2], hex_vs[3]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[3], hex_vs[4], hex_vs[5]]))

                elif face_type == "CATALAN_Z":
                    hex_faces.append(bm.faces.new(
                        [hex_vs[0], hex_vs[1], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[1], hex_vs[2], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[2], hex_vs[4], hex_vs[5]]))
                    hex_faces.append(bm.faces.new(
                        [hex_vs[2], hex_vs[3], hex_vs[4]]))

                elif face_type == "WIRE":
                    bm.edges.new([hex_vs[0], hex_vs[1]])
                    bm.edges.new([hex_vs[1], hex_vs[2]])
                    bm.edges.new([hex_vs[2], hex_vs[3]])
                    bm.edges.new([hex_vs[3], hex_vs[4]])
                    bm.edges.new([hex_vs[4], hex_vs[5]])
                    bm.edges.new([hex_vs[5], hex_vs[0]])

                elif face_type == "NGON":
                    hex_faces.append(bm.faces.new(hex_vs))

                verts.append(hex_vs)
                faces.append(hex_faces)

        # Remove duplicate vertices on hexagon edges.
        if verif_merge:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.000001)

        # Transform BMesh.
        # Do this before assigning UVs so that they are orthonormal
        # regardless of world coordinates.
        rot_mat = mathutils.Matrix.Rotation(
            orientation, 4, (0.0, 0.0, 1.0))
        bmesh.ops.rotate(bm, matrix=rot_mat, verts=bm.verts)

        # Ensure vertices have indices.
        # bm.verts.sort(key=HexGridMaker.vertex_comparator)
        # bm.verts.index_update()

        # TODO: Alternate, simpler way to find width and height?
        # width: (cellradius * 2) * ((3 ** 0.5) * 0.5) * (rings * 2 - 1)

        # Causes issues with extrusion (verts deleted.)
        # bmesh.ops.bevel(
        #     bm,
        #     geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
        #     offset=15.0,
        #     profile=0.5,
        #     offset_type="PERCENT",
        #     segments=3,
        #     affect="VERTICES")

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

        # Update normals, jic.
        bm.normal_update()

        return {
            "faces": faces,
            "hex_count": 1 + i_max * verif_rings * 3,
            "verif_merge": verif_merge,
            "width": width,
            "height": height}

    @staticmethod
    def extrude_hexagons(
            bm=None,
            faces=None,
            extrude_lb=0.000001,
            extrude_ub=1.0,
            terrain_type="UNIFORM",
            noise_influence=0.0,
            noise_scale=1.0,
            noise_offset=(0.0, 0.0, 0.0),
            noise_basis="BLENDER",
            origin=(-1.0, -1.0),
            dest=(1.0, 1.0),
            merge_verts=False) -> bool:

        # Validate input arguments.
        verif_lb = min(extrude_lb, extrude_ub)
        verif_ub = max(extrude_lb, extrude_ub)
        verif_infl = max(0.0, min(noise_influence, 1.0))
        if verif_lb < 0.000001 and verif_ub < 0.000001:
            return False

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

            z = verif_ub
            bmesh.ops.translate(bm, verts=new_verts,
                                vec=(0.0, 0.0, z))
        else:

            # For linear gradient.
            b = (dest[0] - origin[0],
                 dest[1] - origin[1])
            dot_bb = b[0] ** 2 + b[1] ** 2
            inv_dot_bb = 0.0 if dot_bb == 0.0 else 1.0 / dot_bb

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

                # Find median point of hexagon.
                point = mathutils.Vector((0.0, 0.0, 0.0))
                for hex_face in hex_faces:
                    point += hex_face.calc_center_median()
                point /= len(hex_faces)

                if terrain_type == "LINEAR":

                    # Subtract the median from the gradient origin.
                    a = (point[0] - origin[0],
                         point[1] - origin[1])

                    # Find the clamped scalar projection.
                    dot_ab = a[0] * b[0] + a[1] * b[1]
                    scalar_proj = dot_ab * inv_dot_bb
                    terrain_fac = max(0.0, min(1.0, scalar_proj))

                elif terrain_type == "SPHERICAL":

                    # Find distance from origin to point.
                    a = (point[0] - origin[0],
                         point[1] - origin[1])

                    # Divide distance squared by max distance squared.
                    dot_aa = a[0] ** 2 + a[1] ** 2
                    norm_dot = dot_aa * inv_dot_bb
                    terrain_fac = 1.0 - max(0.0, min(1.0, norm_dot))

                else:

                    # UNIFORM is default.
                    terrain_fac = 1.0

                # Offset and scale the noise input.
                noise_in = noise_offset + noise_scale * point

                # Returns a value in [-1, 1] that needs to be converted to [0, 1].
                noise_fac = 0.5 + 0.5 * mathutils.noise.noise(
                    noise_in, noise_basis=noise_basis)

                # TODO Instead have a noise contribution in [0,1]
                # fac = noise_fac * terrain_fac
                fac = (1.0 - verif_infl) * terrain_fac + verif_infl * noise_fac
                z = (1.0 - fac) * verif_lb + fac * verif_ub
                bmesh.ops.translate(bm, verts=new_verts, vec=(0.0, 0.0, z))

        bm.normal_update()

        return True

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
