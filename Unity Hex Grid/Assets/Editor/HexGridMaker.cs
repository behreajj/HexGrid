using System.Text;
using UnityEditor;
using UnityEngine;

public class HexGridMaker : EditorWindow
{
    enum FaceType : int
    {
        TriFan = 0,
        CatalanRay = 1,
        CatalanTri = 2,
        CatalanZ = 3
    }

    enum TerrainType : int
    {
        Flat = 0,
        Uniform = 1,
        Noise = 2,
        Linear = 3,
        Spherical = 4
    }

    const float Sqrt3 = 1.7320508075688772f;

    string folderPath = "Assets/Meshes/";
    string meshName = "Hex.Grid";
    bool createInstance = true;

    int rings = 4;
    float cellRadius = 0.5f;
    float cellMargin = 0.0325f;
    float orientation = 0.0f;
    FaceType faceType = FaceType.TriFan;
    float extrudeLb = 0.0f;
    float extrudeUb = 0.0f;

    TerrainType terrainType = TerrainType.Flat;
    Vector3 noiseOffset = new Vector3 (0.0f, 0.0f, 0.0f);
    float noiseScale = 1.0f;
    Vector3 origin = new Vector3 (-1.0f, -1.0f, -1.0f);
    Vector3 destination = new Vector3 (1.0f, 1.0f, 1.0f);

    GUIContent nameLabel = new GUIContent (
        "Name",
        "The name of the mesh asset.");
    GUIContent pathLabel = new GUIContent (
        "Path",
        "The file path relative to the project folder.");
    GUIContent instLabel = new GUIContent (
        "Instantiate",
        "Instantiate a game object upon creation.");

    GUIContent ringsLabel = new GUIContent ("Rings", "Number of rings in grid.");
    GUIContent cellRadLabel = new GUIContent ("Cell Radius", "Radius of each hexagon cell.");
    GUIContent cellMarginLabel = new GUIContent ("Cell Margin", "Margin between each hexagon cell.");
    GUIContent orientationLabel = new GUIContent ("Rotation", "Rotation of hexagonal grid.");
    GUIContent faceTypeLabel = new GUIContent ("Face Type", "How to fill each hexagon cell.");

    GUIContent terrainTypeLabel = new GUIContent ("Terrain Type", "How to extrude each hexagon cell.");

    GUIContent extrudeLbLabel = new GUIContent ("Extrude Lower", "Extrusion lower bound on the y axis.");
    GUIContent extrudeUbLabel = new GUIContent ("Extrude Upper", "Extrusion upper bound on the y axis.");

    GUIContent noiseOffsetLabel = new GUIContent ("Noise Offset", "Offset added to noise input.");
    GUIContent noiseScaleLabel = new GUIContent ("Noise Scale", "Scalar multiplied with noise input.");

    GUIContent originLabel = new GUIContent ("Origin", "Linear gradient origin.");
    GUIContent destLabel = new GUIContent ("Destination", "Linear gradient destination.");

    [MenuItem ("Window/Hex Grid")]
    static void Init ( )
    {
        HexGridMaker window = (HexGridMaker) EditorWindow.GetWindow (
            t: typeof (HexGridMaker),
            utility: false,
            title: "Hex Grid",
            focus : true);
        window.Show ( );
    }

    void OnGUI ( )
    {
        meshName = EditorGUILayout.TextField (nameLabel, meshName);
        folderPath = EditorGUILayout.TextField (pathLabel, folderPath);
        createInstance = EditorGUILayout.ToggleLeft (instLabel, createInstance);
        EditorGUILayout.Space ( );

        rings = Mathf.Max (1, EditorGUILayout.IntField (ringsLabel, rings));
        cellRadius = Mathf.Max (0.0002f, EditorGUILayout.FloatField (cellRadLabel, cellRadius));
        cellMargin = Mathf.Clamp (EditorGUILayout.FloatField (cellMarginLabel, cellMargin), 0.0f, cellRadius - 0.0001f);
        orientation = Mathf.Clamp (EditorGUILayout.FloatField (orientationLabel, orientation), -Mathf.PI, Mathf.PI);
        faceType = (FaceType) EditorGUILayout.EnumPopup (faceTypeLabel, faceType);

        EditorGUILayout.Space ( );
        terrainType = (TerrainType) EditorGUILayout.EnumPopup (terrainTypeLabel, terrainType);

        switch (terrainType)
        {
            case TerrainType.Noise:
                extrudeLb = Mathf.Max (0.0f, EditorGUILayout.FloatField (extrudeLbLabel, extrudeLb));
                extrudeUb = Mathf.Max (0.0f, EditorGUILayout.FloatField (extrudeUbLabel, extrudeUb));
                noiseOffset = EditorGUILayout.Vector3Field (noiseOffsetLabel, noiseOffset);
                noiseScale = EditorGUILayout.FloatField (noiseScaleLabel, noiseScale);
                break;

            case TerrainType.Linear:
                extrudeLb = Mathf.Max (0.0f, EditorGUILayout.FloatField (extrudeLbLabel, extrudeLb));
                extrudeUb = Mathf.Max (0.0f, EditorGUILayout.FloatField (extrudeUbLabel, extrudeUb));
                origin = EditorGUILayout.Vector3Field (originLabel, origin);
                destination = EditorGUILayout.Vector3Field (destLabel, destination);
                break;

            case TerrainType.Spherical:
                extrudeLb = Mathf.Max (0.0f, EditorGUILayout.FloatField (extrudeLbLabel, extrudeLb));
                extrudeUb = Mathf.Max (0.0f, EditorGUILayout.FloatField (extrudeUbLabel, extrudeUb));
                origin = EditorGUILayout.Vector3Field (originLabel, origin);
                destination = EditorGUILayout.Vector3Field (destLabel, destination);
                break;

            case TerrainType.Uniform:
                extrudeUb = Mathf.Max (0.0f, EditorGUILayout.FloatField (extrudeUbLabel, extrudeUb));
                break;

            case TerrainType.Flat:
            default:
                break;
        }

        if (GUILayout.Button ("Create"))
        {
            Mesh mesh = HexGridData ( );
            string pth = new StringBuilder (96)
                .Append (folderPath)
                .Append (meshName)
                .Append (".mesh")
                .ToString ( );
            AssetDatabase.CreateAsset (mesh, pth);
            AssetDatabase.SaveAssets ( );

            if (createInstance)
            {
                GameObject go = InstantMesh (meshName, mesh);
            }
        }
    }

    Mesh HexGridData ( )
    {
        float altitude = HexGridMaker.Sqrt3 * cellRadius;
        float rad15 = cellRadius * 1.5f;
        float padRad = cellRadius - cellMargin;

        float halfAlt = altitude * 0.5f;
        float halfRad = padRad * 0.5f;
        float radRt32 = halfRad * HexGridMaker.Sqrt3;

        int iMax = rings - 1;
        int iMin = -iMax;

        int hexCount = 1 + iMax * rings * 3;
        int vertsPerHex = VertsPerHexagon (faceType);
        int facesPerHex = FacesPerHexagon (faceType);
        int vertCount = hexCount * vertsPerHex;
        int faceCount = hexCount * facesPerHex;
        int fStride = facesPerHex * 3;

        Vector3[ ] vs = new Vector3[vertCount];
        Vector2[ ] vts = new Vector2[vertCount];
        Vector3[ ] vns = new Vector3[vertCount];
        int[ ] fs = new int[faceCount * 3];

        int vIdx = 0;
        int fIdx = 0;
        for (int i = iMin; i <= iMax; ++i)
        {
            int jMin = Mathf.Max (iMin, iMin - i);
            int jMax = Mathf.Min (iMax, iMax - i);
            float iAlt = i * altitude;

            for (int j = jMin; j <= jMax; ++j)
            {
                float jf = j;

                // Hexagon center.
                float x = iAlt + jf * halfAlt;
                float z = jf * rad15;

                // Hexagon edges.
                float left = x - radRt32;
                float right = x + radRt32;
                float top = z + halfRad;
                float bottom = z - halfRad;

                // Edge indices.
                int edgeIdx0 = vIdx;
                int edgeIdx1 = vIdx + 1;
                int edgeIdx2 = vIdx + 2;
                int edgeIdx3 = vIdx + 3;
                int edgeIdx4 = vIdx + 4;
                int edgeIdx5 = vIdx + 5;

                // Coordinates.
                vs[edgeIdx0].Set (x, 0.0f, z + padRad);
                vs[edgeIdx1].Set (right, 0.0f, top);
                vs[edgeIdx2].Set (right, 0.0f, bottom);
                vs[edgeIdx3].Set (x, 0.0f, z - padRad);
                vs[edgeIdx4].Set (left, 0.0f, bottom);
                vs[edgeIdx5].Set (left, 0.0f, top);

                // Texture coordinates.
                vts[edgeIdx0].Set (0.5f, 1.0f);
                vts[edgeIdx1].Set (0.9330127f, 0.75f);
                vts[edgeIdx2].Set (0.9330127f, 0.25f);
                vts[edgeIdx3].Set (0.5f, 0.0f);
                vts[edgeIdx4].Set (0.0669873f, 0.25f);
                vts[edgeIdx5].Set (0.0669873f, 0.75f);

                // Normals.
                vns[edgeIdx0].Set (0.0f, 1.0f, 0.0f);
                vns[edgeIdx1].Set (0.0f, 1.0f, 0.0f);
                vns[edgeIdx2].Set (0.0f, 1.0f, 0.0f);
                vns[edgeIdx3].Set (0.0f, 1.0f, 0.0f);
                vns[edgeIdx4].Set (0.0f, 1.0f, 0.0f);
                vns[edgeIdx5].Set (0.0f, 1.0f, 0.0f);

                switch (faceType)
                {
                    case FaceType.CatalanRay:

                        // Triangle 1.
                        fs[fIdx] = edgeIdx0;
                        fs[fIdx + 1] = edgeIdx1;
                        fs[fIdx + 2] = edgeIdx2;

                        // Triangle 2.
                        fs[fIdx + 3] = edgeIdx0;
                        fs[fIdx + 4] = edgeIdx2;
                        fs[fIdx + 5] = edgeIdx3;

                        // Triangle 3.
                        fs[fIdx + 6] = edgeIdx0;
                        fs[fIdx + 7] = edgeIdx3;
                        fs[fIdx + 8] = edgeIdx4;

                        // Triangle 4.
                        fs[fIdx + 9] = edgeIdx0;
                        fs[fIdx + 10] = edgeIdx4;
                        fs[fIdx + 11] = edgeIdx5;

                        break;

                    case FaceType.CatalanTri:

                        // Central Triangle.
                        fs[fIdx] = edgeIdx1;
                        fs[fIdx + 1] = edgeIdx3;
                        fs[fIdx + 2] = edgeIdx5;

                        // Peripheral Triangle 1.
                        fs[fIdx + 3] = edgeIdx0;
                        fs[fIdx + 4] = edgeIdx1;
                        fs[fIdx + 5] = edgeIdx5;

                        // Peripheral Triangle 2.
                        fs[fIdx + 6] = edgeIdx1;
                        fs[fIdx + 7] = edgeIdx2;
                        fs[fIdx + 8] = edgeIdx3;

                        // Peripheral Triangle 3.
                        fs[fIdx + 9] = edgeIdx3;
                        fs[fIdx + 10] = edgeIdx4;
                        fs[fIdx + 11] = edgeIdx5;

                        break;

                    case FaceType.CatalanZ:

                        // Triangle 1.
                        fs[fIdx] = edgeIdx0;
                        fs[fIdx + 1] = edgeIdx1;
                        fs[fIdx + 2] = edgeIdx5;

                        // Triangle 2.
                        fs[fIdx + 3] = edgeIdx1;
                        fs[fIdx + 4] = edgeIdx2;
                        fs[fIdx + 5] = edgeIdx5;

                        // Triangle 3.
                        fs[fIdx + 6] = edgeIdx2;
                        fs[fIdx + 7] = edgeIdx4;
                        fs[fIdx + 8] = edgeIdx5;

                        // Triangle 4.
                        fs[fIdx + 9] = edgeIdx2;
                        fs[fIdx + 10] = edgeIdx3;
                        fs[fIdx + 11] = edgeIdx4;

                        break;

                    case FaceType.TriFan:

                        int centerIdx = vIdx + 6;
                        vs[centerIdx].Set (x, 0.0f, z);
                        vts[centerIdx].Set (0.5f, 0.5f);
                        vns[centerIdx].Set (0.0f, 1.0f, 0.0f);

                        // Triangle 1.
                        fs[fIdx] = centerIdx;
                        fs[fIdx + 1] = edgeIdx0;
                        fs[fIdx + 2] = edgeIdx1;

                        // Triangle 2.
                        fs[fIdx + 3] = centerIdx;
                        fs[fIdx + 4] = edgeIdx1;
                        fs[fIdx + 5] = edgeIdx2;

                        // Triangle 3.
                        fs[fIdx + 6] = centerIdx;
                        fs[fIdx + 7] = edgeIdx2;
                        fs[fIdx + 8] = edgeIdx3;

                        // Triangle 4.
                        fs[fIdx + 9] = centerIdx;
                        fs[fIdx + 10] = edgeIdx3;
                        fs[fIdx + 11] = edgeIdx4;

                        // Triangle 5.
                        fs[fIdx + 12] = centerIdx;
                        fs[fIdx + 13] = edgeIdx4;
                        fs[fIdx + 14] = edgeIdx5;

                        // Triangle 6.
                        fs[fIdx + 15] = centerIdx;
                        fs[fIdx + 16] = edgeIdx5;
                        fs[fIdx + 17] = edgeIdx0;

                        break;
                }

                fIdx += fStride;
                vIdx += vertsPerHex;
            }
        }

        Mesh mesh = new Mesh ( );
        mesh.vertices = vs;
        mesh.uv = vts;
        mesh.normals = vns;

        // Triangles must be assigned last.
        mesh.triangles = fs;
        mesh.RecalculateTangents ( );
        mesh.Optimize ( );

        return mesh;
    }

    static int FacesPerHexagon (in FaceType faceType)
    {
        switch (faceType)
        {
            case FaceType.CatalanRay:
            case FaceType.CatalanTri:
            case FaceType.CatalanZ:
                return 4;
            case FaceType.TriFan:
                return 6;
            default:
                return 0;
        }
    }

    static int VertsPerHexagon (in FaceType faceType)
    {
        switch (faceType)
        {
            case FaceType.CatalanRay:
            case FaceType.CatalanTri:
            case FaceType.CatalanZ:
                return 6;
            case FaceType.TriFan:
                return 7;
            default:
                return 0;
        }
    }

    static GameObject InstantMesh (in string name, in Mesh mesh)
    {
        GameObject go = new GameObject (name);

        MeshFilter mf = go.AddComponent<MeshFilter> ( );
        MeshRenderer mr = go.AddComponent<MeshRenderer> ( );

        mf.sharedMesh = mesh;
        mr.sharedMaterial = AssetDatabase.GetBuiltinExtraResource<Material> (
            "Default-Diffuse.mat");

        Selection.activeObject = go;
        return go;
    }
}