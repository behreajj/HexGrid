using UnityEditor;
using UnityEngine;

public class HexGridMaker : EditorWindow
{
    public enum FaceType : int
    {
        TriFan = 0,
        CatalanRay = 1,
        CatalanTri = 2,
        CatalanZ = 3
    }

    public enum TerrainType : int
    {
        Flat = 0,
        Uniform = 1,
        Noise = 2,
        Linear = 3,
        Spherical = 4
    }

    string folderPath = "Assets/Meshes/";
    string meshName = "Capsule";
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
        cellRadius = Mathf.Max (0.0001f, EditorGUILayout.FloatField (cellRadLabel, cellRadius));
        cellMargin = Mathf.Max (0.0f, EditorGUILayout.FloatField (cellMarginLabel, cellMargin));
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

        }
    }

    public static int FacesPerHexagon (FaceType faceType)
    {
        switch (faceType)
        {
            case FaceType.CatalanRay:
                return 4;
            case FaceType.CatalanTri:
                return 4;
            case FaceType.CatalanZ:
                return 4;
            case FaceType.TriFan:
                return 6;
            default:
                return 0;
        }
    }
}