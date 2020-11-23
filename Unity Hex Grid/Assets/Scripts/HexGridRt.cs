using System.Collections.Generic;
using UnityEngine;

public class HexGridRt : MonoBehaviour
{
    const float Sqrt3 = 1.7320508075688772f;
    const float Sqrt3_2 = 0.8660254037844386f;
    const float Sqrt3_4 = 0.4330127018922193f;

    public enum FaceType : int
    {
        TriFan = 0,
        CatalanRay = 1,
        CatalanTri = 2,
        CatalanZ = 3
    }

    [SerializeField]
    [Min (1)]
    protected int rings = 4;

    [SerializeField]
    [Min (0.0001f)]
    protected float cellRadius = 0.5f;

    [SerializeField]
    [Min (0.0001f)]
    protected float cellMargin = 0.0325f;

    [SerializeField]
    protected FaceType faceType = FaceType.TriFan;

    [SerializeField]
    [Min (0.0f)]
    protected float extrudeLb = 0.0f;

    [SerializeField]
    [Min (0.0001f)]
    protected float extrudeUb = 1.0f;

    [SerializeField]
    protected Vector2 noiseOffset = new Vector2 (0.0f, 0.0f);

    [SerializeField]
    protected float noiseScale = 1.0f;

    public List<GameObject> gameObjects = new List<GameObject> ( );

    public Material material;

    void Start ( )
    {
        float extent = Sqrt3 * cellRadius;
        float rad15 = cellRadius * 1.5f;
        float padRad = cellRadius - cellMargin;

        float halfExt = extent * 0.5f;
        float halfRad = padRad * 0.5f;
        float radRt32 = halfRad * Sqrt3;

        int iMax = rings - 1;
        int iMin = -iMax;

        int hexCount = 1 + iMax * rings * 3;

        for (int k = 0, i = iMin; i <= iMax; ++i)
        {
            int jMin = Mathf.Max (iMin, iMin - i);
            int jMax = Mathf.Min (iMax, iMax - i);
            float iExt = i * extent;

            for (int j = jMin; j <= jMax; ++j, ++k)
            {
                float jf = j;

                // Hexagon center.
                float x = iExt + jf * halfExt;
                float z = jf * rad15;

                // Elevation.
                // TODO: Since this is opting for maximum user interface
                // friendliness, why not scale the transform instead of
                // the mesh itself and therefore allow yourself to make
                // ONE mesh.
                float fac = Mathf.PerlinNoise (
                    noiseScale * x + noiseOffset.x,
                    noiseScale * z + noiseOffset.y);
                float y = Mathf.Lerp (extrudeLb, extrudeUb, fac);

                string name = "Hex." + k.ToString ("D3");
                GameObject go = new GameObject (name);
                Transform tr = go.transform;
                tr.localPosition = new Vector3 (x, 0.0f, z);
                tr.parent = this.transform;
                gameObjects.Add (go);

                MeshFilter mf = go.AddComponent<MeshFilter> ( );
                MeshRenderer mr = go.AddComponent<MeshRenderer> ( );

                mf.mesh = Hexagon2 (padRad, y);
                mr.sharedMaterial = material;
            }
        }
    }

    static Mesh Hexagon2 (in float r = 1.0f, in float y = 0.0f)
    {
        float r32 = r * Sqrt3_2;
        float rhalf = r * 0.5f;

        Vector3[ ] vs = {
            new Vector3 (0.0f, y, 0.0f),
            new Vector3 (0.0f, y, r),
            new Vector3 (r32, y, rhalf),
            new Vector3 (r32, y, -rhalf),
            new Vector3 (0.0f, y, -r),
            new Vector3 (-r32, y, -rhalf),
            new Vector3 (-r32, y, rhalf),
        };

        Vector2[ ] vts = {
            new Vector2 (0.5f, 0.5f),
            new Vector2 (0.5f, 1.0f),
            new Vector2 (0.9330127f, 0.75f),
            new Vector2 (0.9330127f, 0.25f),
            new Vector2 (0.5f, 0.0f),
            new Vector2 (0.0669873f, 0.25f),
            new Vector2 (0.0669873f, 0.75f),
        };

        Vector3[ ] vns = {
            new Vector3 (0.0f, 1.0f, 0.0f),
            new Vector3 (0.0f, 1.0f, 0.0f),
            new Vector3 (0.0f, 1.0f, 0.0f),
            new Vector3 (0.0f, 1.0f, 0.0f),
            new Vector3 (0.0f, 1.0f, 0.0f),
            new Vector3 (0.0f, 1.0f, 0.0f),
            new Vector3 (0.0f, 1.0f, 0.0f)
        };

        int[ ] fs = {
            0,
            1,
            2,

            0,
            2,
            3,

            0,
            3,
            4,

            0,
            4,
            5,

            0,
            5,
            6,

            0,
            6,
            1
        };

        Mesh mesh = new Mesh ( );
        mesh.vertices = vs;
        mesh.uv = vts;
        mesh.normals = vns;

        mesh.triangles = fs;
        mesh.RecalculateTangents ( );
        mesh.Optimize ( );

        return mesh;
    }
}