using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class BroadComCorpus
{
    private static readonly string Root = @"D:\kit-solidworks-com-broad-20260802";
    private static readonly List<Dictionary<string, object>> Calls = new List<Dictionary<string, object>>();
    private static readonly List<Dictionary<string, object>> Artifacts = new List<Dictionary<string, object>>();
    private static SldWorks App;
    private static string PartTemplate;
    private static string AssemblyTemplate;

    [STAThread]
    public static int Main(string[] args)
    {
        Directory.CreateDirectory(Root);
        App = new SldWorks();
        App.Visible = true;
        PartTemplate = Required(
            "ISldWorks.GetUserPreferenceStringValue.part",
            () => App.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplatePart)
        );
        AssemblyTemplate = Required(
            "ISldWorks.GetUserPreferenceStringValue.assembly",
            () => App.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplateAssembly)
        );
        var selected = new HashSet<string>(args, StringComparer.OrdinalIgnoreCase);
        try
        {
            if (Selected(selected, "01")) GeneratePart("01_sketch_geometry_suite", SketchGeometrySuite);
            if (Selected(selected, "02")) GeneratePart("02_sketch_transform_suite", SketchTransformSuite);
            if (Selected(selected, "03")) GeneratePart("03_boss_cut_hole_suite", BossCutHoleSuite);
            if (Selected(selected, "04")) GeneratePart("04_revolve_suite", RevolveSuite);
            if (Selected(selected, "05")) GeneratePart("05_fillet_suite", FilletSuite);
            if (Selected(selected, "06")) GeneratePart("06_chamfer_suite", ChamferSuite);
            if (Selected(selected, "07")) GeneratePart("07_shell_dome_suite", ShellDomeSuite);
            if (Selected(selected, "08")) GeneratePart("08_multibody_suite", MultibodySuite);
            if (Selected(selected, "09")) GeneratePart("09_equation_configuration_suite", EquationConfigurationSuite);
            if (Selected(selected, "10")) GeneratePart("10_reference_surface_suite", ReferenceSurfaceSuite);
            if (Selected(selected, "11")) GenerateAssembly("11_mated_assembly_suite");
            WriteJson(Path.Combine(Root, "generation_log.json"), new Dictionary<string, object>
            {
                { "generated_at_utc", DateTime.UtcNow.ToString("o") },
                { "solidworks_revision", App.RevisionNumber() },
                { "part_template", PartTemplate },
                { "assembly_template", AssemblyTemplate },
                { "artifacts", Artifacts },
                { "calls", Calls }
            });
            return Artifacts.Any(item => Convert.ToString(item["status"]) != "verified") ? 1 : 0;
        }
        finally
        {
            try { App.CloseAllDocuments(true); } catch { }
            try { App.ExitApp(); } catch { }
        }
    }

    private static bool Selected(HashSet<string> selected, string value)
    {
        return selected.Count == 0 || selected.Contains(value);
    }

    private static void GeneratePart(string name, Action<ModelDoc2, Dictionary<string, object>> build)
    {
        var path = Path.Combine(Root, name + ".SLDPRT");
        var artifact = Artifact(name, path, "part");
        ModelDoc2 doc = null;
        ModelDoc2 reopened = null;
        try
        {
            doc = Required("ISldWorks.NewDocument.part", () => (ModelDoc2)App.NewDocument(PartTemplate, 0, 0.0, 0.0));
            build(doc, artifact);
            VerifyAndSave(doc, artifact, path);
            Close(doc);
            doc = null;
            reopened = Open(path, (int)swDocumentTypes_e.swDocPART, artifact);
            artifact["after_reopen"] = Snapshot(reopened);
            artifact["mutation"] = MutateFirstDrivingDimension(reopened);
            artifact["rebuild_after_reopen"] = Call("IModelDoc2.ForceRebuild3.after_reopen", () => reopened.ForceRebuild3(false));
            artifact["status"] = "verified";
        }
        catch (Exception ex)
        {
            artifact["status"] = "failed";
            artifact["error_type"] = ex.GetType().FullName;
            artifact["error"] = ex.ToString();
        }
        finally
        {
            if (doc != null) SafeClose(doc);
            if (reopened != null) SafeClose(reopened);
            WriteJson(Path.Combine(Root, name + ".json"), artifact);
        }
    }

    private static void GenerateAssembly(string name)
    {
        var path = Path.Combine(Root, name + ".SLDASM");
        var artifact = Artifact(name, path, "assembly");
        ModelDoc2 doc = null;
        ModelDoc2 reopened = null;
        try
        {
            var first = Path.Combine(Root, "03_boss_cut_hole_suite.SLDPRT");
            var second = Path.Combine(Root, "04_revolve_suite.SLDPRT");
            if (!File.Exists(first) || !File.Exists(second)) throw new InvalidOperationException("assembly component corpus files are missing");
            doc = Required("ISldWorks.NewDocument.assembly", () => (ModelDoc2)App.NewDocument(AssemblyTemplate, 0, 0.0, 0.0));
            var assembly = (AssemblyDoc)doc;
            var component1 = Required("IAssemblyDoc.AddComponent5.first", () => assembly.AddComponent5(first, 0, "", false, "", 0.0, 0.0, 0.0));
            var component2 = Required("IAssemblyDoc.AddComponent5.second", () => assembly.AddComponent5(second, 0, "", false, "", 0.08, 0.0, 0.0));
            artifact["component_names"] = new[] { component1.Name2, component2.Name2 };
            var mates = new List<Dictionary<string, object>>();
            mates.Add(AddPlaneMate(doc, assembly, component1, component2, "Front Plane", "Front Plane", (int)swMateType_e.swMateCOINCIDENT, 0.0, 0.0));
            mates.Add(AddPlaneMate(doc, assembly, component1, component2, "Top Plane", "Top Plane", (int)swMateType_e.swMateDISTANCE, 0.08, 0.0));
            mates.Add(AddPlaneMate(doc, assembly, component1, component2, "Right Plane", "Right Plane", (int)swMateType_e.swMateANGLE, 0.0, Math.PI / 6.0));
            artifact["mates"] = mates;
            artifact["assembly_rebuild"] = Call("IAssemblyDoc.ForceRebuild", () => { assembly.ForceRebuild(); return true; });
            VerifyAndSave(doc, artifact, path);
            Close(doc);
            doc = null;
            reopened = Open(path, (int)swDocumentTypes_e.swDocASSEMBLY, artifact);
            var reopenedAssembly = (AssemblyDoc)reopened;
            artifact["component_count_after_reopen"] = ArrayLength(Call("IAssemblyDoc.GetComponents", () => reopenedAssembly.GetComponents(true)));
            artifact["after_reopen"] = Snapshot(reopened);
            artifact["status"] = "verified";
        }
        catch (Exception ex)
        {
            artifact["status"] = "failed";
            artifact["error_type"] = ex.GetType().FullName;
            artifact["error"] = ex.ToString();
        }
        finally
        {
            if (doc != null) SafeClose(doc);
            if (reopened != null) SafeClose(reopened);
            WriteJson(Path.Combine(Root, name + ".json"), artifact);
        }
    }

    private static Dictionary<string, object> AddPlaneMate(ModelDoc2 doc, AssemblyDoc assembly, Component2 first, Component2 second, string firstPlane, string secondPlane, int type, double distance, double angle)
    {
        doc.ClearSelection2(true);
        var firstSelected = Call("IModelDocExtension.SelectByID2.first_plane", () => doc.Extension.SelectByID2(firstPlane + "@" + first.Name2, "PLANE", 0.0, 0.0, 0.0, false, 1, null, 0));
        var secondSelected = Call("IModelDocExtension.SelectByID2.second_plane", () => doc.Extension.SelectByID2(secondPlane + "@" + second.Name2, "PLANE", 0.0, 0.0, 0.0, true, 1, null, 0));
        var error = 0;
        var mate = Call("IAssemblyDoc.AddMate5", () => assembly.AddMate5(type, (int)swMateAlign_e.swMateAlignALIGNED, false, distance, distance, distance, 1.0, 1.0, angle, angle, angle, false, false, 0, out error));
        doc.ClearSelection2(true);
        return new Dictionary<string, object>
        {
            { "type", type },
            { "first_selected", firstSelected },
            { "second_selected", secondSelected },
            { "error", error },
            { "created", mate != null }
        };
    }

    private static void SketchGeometrySuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        BeginSketch(doc, 0);
        var manager = doc.SketchManager;
        manager.AddToDB = true;
        manager.DisplayWhenAdded = false;
        Required("ISketchManager.CreatePoint", () => manager.CreatePoint(-0.09, 0.04, 0.0));
        Required("ISketchManager.CreateLine", () => manager.CreateLine(-0.09, 0.03, 0.0, -0.07, 0.03, 0.0));
        Required("ISketchManager.CreateCenterLine", () => manager.CreateCenterLine(-0.09, 0.02, 0.0, -0.07, 0.02, 0.0));
        Required("ISketchManager.CreateCircle", () => manager.CreateCircle(-0.06, 0.03, 0.0, -0.055, 0.03, 0.0));
        Required("ISketchManager.CreateCircleByRadius", () => manager.CreateCircleByRadius(-0.04, 0.03, 0.0, 0.006));
        Required("ISketchManager.CreateArc", () => manager.CreateArc(-0.02, 0.03, 0.0, -0.014, 0.03, 0.0, -0.02, 0.036, 0.0, 1));
        Required("ISketchManager.Create3PointArc", () => manager.Create3PointArc(0.0, 0.03, 0.0, 0.012, 0.03, 0.0, 0.006, 0.037, 0.0));
        Required("ISketchManager.CreateEllipse", () => manager.CreateEllipse(0.03, 0.03, 0.0, 0.04, 0.03, 0.0, 0.03, 0.035, 0.0));
        Call("ISketchManager.CreateEllipticalArc", () => manager.CreateEllipticalArc(0.06, 0.03, 0.0, 0.07, 0.03, 0.0, 0.06, 0.035, 0.0, 0.07, 0.03, 0.0, 0.06, 0.035, 0.0, 1));
        Call("ISketchManager.CreateParabola", () => manager.CreateParabola(-0.08, 0.0, 0.0, -0.075, 0.0, 0.0, -0.07, -0.006, 0.0, -0.07, 0.006, 0.0));
        Call("ISketchManager.CreateConic", () => manager.CreateConic(-0.05, 0.0, 0.0, -0.045, 0.0, 0.0, -0.04, -0.006, 0.0, -0.04, 0.006, 0.0));
        Call("ISketchManager.CreateSpline", () => manager.CreateSpline(new double[] { -0.025, -0.005, 0.0, -0.018, 0.007, 0.0, -0.010, -0.004, 0.0, -0.002, 0.006, 0.0 }));
        Call("ISketchManager.CreateSpline2", () => manager.CreateSpline2(new double[] { 0.005, -0.006, 0.0, 0.012, 0.006, 0.0, 0.02, -0.003, 0.0, 0.027, 0.007, 0.0 }, true));
        Call("ISketchManager.CreateEquationSpline", () => manager.CreateEquationSpline("0.004*sin(50*x)", 0.0, 0.02, false, 0.0, 0.035, 0.0, false, false));
        Required("ISketchManager.CreatePolygon", () => manager.CreatePolygon(0.07, 0.0, 0.0, 0.078, 0.0, 0.0, 6, true));
        Required("ISketchManager.CreateSketchSlot", () => manager.CreateSketchSlot((int)swSketchSlotCreationType_e.swSketchSlotCreationType_line, (int)swSketchSlotLengthType_e.swSketchSlotLengthType_CenterCenter, 0.006, -0.085, -0.025, 0.0, -0.065, -0.025, 0.0, 0.0, 0.0, 0.0, 1, true));
        Required("ISketchManager.CreateCornerRectangle", () => manager.CreateCornerRectangle(-0.05, -0.035, 0.0, -0.03, -0.02, 0.0));
        Required("ISketchManager.CreateCenterRectangle", () => manager.CreateCenterRectangle(-0.005, -0.027, 0.0, 0.005, -0.02, 0.0));
        Required("ISketchManager.Create3PointCornerRectangle", () => manager.Create3PointCornerRectangle(0.02, -0.035, 0.0, 0.04, -0.035, 0.0, 0.02, -0.02, 0.0));
        Required("ISketchManager.Create3PointCenterRectangle", () => manager.Create3PointCenterRectangle(0.065, -0.027, 0.0, 0.075, -0.027, 0.0, 0.065, -0.018, 0.0));
        Required("ISketchManager.CreateParallelogram", () => manager.CreateParallelogram(0.035, -0.055, 0.0, 0.055, -0.055, 0.0, 0.04, -0.042, 0.0));
        manager.AddToDB = false;
        manager.DisplayWhenAdded = true;
        EndSketch(doc);
        artifact["sketch_geometry_count"] = SketchGeometryCount(doc);
    }

    private static void SketchTransformSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        BeginSketch(doc, 0);
        var manager = doc.SketchManager;
        var line = Required("ISketchManager.CreateLine.transform", () => manager.CreateLine(-0.03, 0.0, 0.0, 0.03, 0.0, 0.0));
        Required("ISketchManager.CreateCircle.transform", () => manager.CreateCircleByRadius(0.0, 0.02, 0.0, 0.006));
        Call("ISketchSegment.Select4", () => line.Select4(false, null));
        Call("IModelDoc2.SketchAddConstraints.horizontal", () => { doc.SketchAddConstraints("sgHORIZONTAL2D"); return true; });
        Call("IModelDoc2.AddDimension2", () => doc.AddDimension2(0.0, -0.01, 0.0));
        doc.ClearSelection2(true);
        var circle = Required("ISketchManager.CreateCircle.pattern_seed", () => manager.CreateCircleByRadius(-0.02, -0.025, 0.0, 0.003));
        Call("ISketchSegment.Select4.pattern_seed", () => circle.Select4(false, null));
        Call("ISketchManager.CreateLinearSketchStepAndRepeat", () => manager.CreateLinearSketchStepAndRepeat(3, 2, 0.01, 0.01, 0.0, Math.PI / 2.0, "", false, false, false, false, false));
        doc.ClearSelection2(true);
        var arc = Required("ISketchManager.CreateArc.circular_seed", () => manager.CreateArc(0.035, -0.02, 0.0, 0.04, -0.02, 0.0, 0.035, -0.015, 0.0, 1));
        Call("ISketchSegment.Select4.circular_seed", () => arc.Select4(false, null));
        Call("ISketchManager.CreateCircularSketchStepAndRepeat", () => manager.CreateCircularSketchStepAndRepeat(0.02, Math.PI * 2.0, 4, Math.PI / 2.0, true, "", false, false, false));
        EndSketch(doc);
        artifact["sketch_geometry_count"] = SketchGeometryCount(doc);
    }

    private static void BossCutHoleSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        var boss = CreateBoss(doc, -0.03, -0.02, 0.03, 0.02, 0.02, true);
        artifact["boss_name"] = boss.Name;
        var top = SelectPlanarFace(doc, true);
        Call("ISketchManager.InsertSketch.top_face", () => { doc.SketchManager.InsertSketch(true); return true; });
        Required("ISketchManager.CreateCircle.cut", () => doc.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, 0.008));
        EndSketch(doc);
        var cut = Required("IFeatureManager.FeatureCut4", () => doc.FeatureManager.FeatureCut4(true, false, false, 0, 0, 0.012, 0.012, false, false, false, false, 0.0, 0.0, false, false, false, false, false, true, true, false, false, false, 0, 0.0, false, false));
        artifact["cut_name"] = cut.Name;
        SelectPlanarFace(doc, true);
        var hole = Call("IFeatureManager.SimpleHole2", () => doc.FeatureManager.SimpleHole2(0.004, true, false, false, 0, 0, 0.01, 0.01, false, false, false, false, 0.0, 0.0, false, false, false, false, true, true, false, false, false));
        artifact["simple_hole_created"] = hole != null;
    }

    private static void RevolveSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        BeginSketch(doc, 0);
        var manager = doc.SketchManager;
        Required("ISketchManager.CreateCenterLine.revolve", () => manager.CreateCenterLine(0.0, -0.035, 0.0, 0.0, 0.035, 0.0));
        Required("ISketchManager.CreateLine.revolve.1", () => manager.CreateLine(0.01, -0.025, 0.0, 0.025, -0.025, 0.0));
        Required("ISketchManager.CreateLine.revolve.2", () => manager.CreateLine(0.025, -0.025, 0.0, 0.025, 0.025, 0.0));
        Required("ISketchManager.CreateLine.revolve.3", () => manager.CreateLine(0.025, 0.025, 0.0, 0.01, 0.025, 0.0));
        Required("ISketchManager.CreateLine.revolve.4", () => manager.CreateLine(0.01, 0.025, 0.0, 0.01, -0.025, 0.0));
        EndSketch(doc);
        var feature = Required("IFeatureManager.FeatureRevolve2", () => doc.FeatureManager.FeatureRevolve2(true, true, false, false, false, false, 0, 0, Math.PI * 2.0, 0.0, false, false, 0.0, 0.0, 0, 0.0, 0.0, true, true, true));
        artifact["revolve_name"] = feature.Name;
    }

    private static void FilletSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        CreateBoss(doc, -0.03, -0.02, 0.03, 0.02, 0.02, true);
        var edge = SelectFirstEdge(doc);
        var feature = Call("IFeatureManager.FeatureFillet3", () => doc.FeatureManager.FeatureFillet3(0, 0.003, 0.0, 0.0, 0, 0, 0, null, null, null, null, null, null, null));
        artifact["edge_selected"] = edge;
        artifact["fillet_created"] = feature != null;
    }

    private static void ChamferSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        CreateBoss(doc, -0.03, -0.02, 0.03, 0.02, 0.02, true);
        var edge = SelectFirstEdge(doc);
        var feature = Call("IFeatureManager.InsertFeatureChamfer", () => doc.FeatureManager.InsertFeatureChamfer((int)swFeatureChamferOption_e.swFeatureChamferTangentPropagation, (int)swChamferType_e.swChamferEqualDistance, 0.002, Math.PI / 4.0, 0.002, 0.0, 0.0, 0.0));
        artifact["edge_selected"] = edge;
        artifact["chamfer_created"] = feature != null;
    }

    private static void ShellDomeSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        CreateBoss(doc, -0.03, -0.025, 0.03, 0.025, 0.02, true);
        SelectPlanarFace(doc, true);
        artifact["shell_call"] = Call("IModelDoc2.InsertFeatureShell", () => { doc.InsertFeatureShell(0.002, false); return true; });
        doc.ClearSelection2(true);
        SelectPlanarFace(doc, true);
        artifact["dome_call"] = Call("IModelDoc2.InsertDome", () => { doc.InsertDome(0.004, false, true); return true; });
    }

    private static void MultibodySuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        CreateBoss(doc, -0.04, -0.015, -0.01, 0.015, 0.015, false);
        CreateBoss(doc, 0.01, -0.015, 0.04, 0.015, 0.015, false);
        var bodies = Bodies(doc);
        artifact["body_count_before"] = bodies.Length;
        if (bodies.Length > 1)
        {
            doc.ClearSelection2(true);
            ((Body2)bodies[1]).Select2(false, null);
            artifact["move_copy_created"] = Call("IFeatureManager.InsertMoveCopyBody2", () => doc.FeatureManager.InsertMoveCopyBody2(0.0, 0.0, 0.005, 0.005, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, true, 2)) != null;
            doc.ClearSelection2(true);
            bodies = Bodies(doc);
            if (bodies.Length > 1)
            {
                artifact["combine_created"] = Call("IFeatureManager.InsertCombineFeature", () => doc.FeatureManager.InsertCombineFeature((int)swBodyOperationType_e.SWBODYADD, (Body2)bodies[0], bodies.Skip(1).ToArray())) != null;
            }
        }
        doc.ClearSelection2(true);
        artifact["body_count_after"] = Bodies(doc).Length;
    }

    private static void EquationConfigurationSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        CreateBoss(doc, -0.02, -0.015, 0.02, 0.015, 0.01, true);
        var equations = doc.GetEquationMgr();
        var addGlobal = Call("IEquationMgr.Add3.global", () => equations.Add3(-1, "\"Width\" = 0.04m", true, (int)swInConfigurationOpts_e.swAllConfiguration, null));
        var addDepth = Call("IEquationMgr.Add3.depth", () => equations.Add3(-1, "\"D1@Boss-Extrude1\" = \"Width\" / 4", true, (int)swInConfigurationOpts_e.swAllConfiguration, null));
        var manager = doc.ConfigurationManager;
        var configuration = Call("IConfigurationManager.AddConfiguration2", () => manager.AddConfiguration2("Long", "COM corpus configuration", "", 0, "", "", true));
        var properties = doc.Extension.get_CustomPropertyManager("");
        var propertyResult = Call("ICustomPropertyManager.Add3", () => properties.Add3("KitCorpus", (int)swCustomInfoType_e.swCustomInfoText, "Broad COM API corpus", (int)swCustomPropertyAddOption_e.swCustomPropertyReplaceValue));
        artifact["equation_indexes"] = new[] { addGlobal, addDepth };
        artifact["configuration_created"] = configuration != null;
        artifact["custom_property_result"] = propertyResult;
    }

    private static void ReferenceSurfaceSuite(ModelDoc2 doc, Dictionary<string, object> artifact)
    {
        var boss = CreateBoss(doc, -0.025, -0.02, 0.025, 0.02, 0.012, true);
        var plane = FirstReferencePlane(doc, 0);
        doc.ClearSelection2(true);
        plane.Select2(false, 0);
        var offsetPlane = Call("IFeatureManager.InsertRefPlane", () => doc.FeatureManager.InsertRefPlane((int)swRefPlaneReferenceConstraints_e.swRefPlaneReferenceConstraint_Distance, 0.025, 0, 0.0, 0, 0.0));
        artifact["offset_plane_created"] = offsetPlane != null;
        doc.ClearSelection2(true);
        plane.Select2(false, 0);
        Call("ISketchManager.InsertSketch.surface_profile", () => { doc.SketchManager.InsertSketch(true); return true; });
        Required("ISketchManager.CreateCircle.surface_profile", () => doc.SketchManager.CreateCircleByRadius(0.0, 0.0, 0.0, 0.01));
        EndSketch(doc);
        var sketch = LastFeatureOfType(doc, "ProfileFeature");
        doc.ClearSelection2(true);
        sketch.Select2(false, 0);
        artifact["surface_extrude_created"] = Call("IFeatureManager.FeatureExtruRefSurface3", () => { doc.FeatureManager.FeatureExtruRefSurface3(false, false, 0, 0.0, 0, 0, 0.03, 0.03, false, false, false, false, 0.0, 0.0, false, false, false, false, false, false, false, false); return true; });
        doc.ClearSelection2(true);
        boss.Select2(false, 0);
        artifact["scale_created"] = Call("IFeatureManager.InsertScale", () => doc.FeatureManager.InsertScale(0, true, 1.1, 1.1, 1.1)) != null;
    }

    private static Feature CreateBoss(ModelDoc2 doc, double x1, double y1, double x2, double y2, double depth, bool merge)
    {
        BeginSketch(doc, 0);
        Required("ISketchManager.CreateCornerRectangle.boss", () => doc.SketchManager.CreateCornerRectangle(x1, y1, 0.0, x2, y2, 0.0));
        EndSketch(doc);
        return Required("IFeatureManager.FeatureExtrusion3", () => doc.FeatureManager.FeatureExtrusion3(true, false, false, 0, 0, depth, depth, false, false, false, false, 0.0, 0.0, false, false, false, false, merge, true, true, 0, 0.0, false));
    }

    private static void BeginSketch(ModelDoc2 doc, int planeOrdinal)
    {
        doc.ClearSelection2(true);
        var plane = FirstReferencePlane(doc, planeOrdinal);
        if (!Required("IFeature.Select2.reference_plane", () => plane.Select2(false, 0))) throw new InvalidOperationException("reference plane selection failed");
        Call("ISketchManager.InsertSketch.begin", () => { doc.SketchManager.InsertSketch(true); return true; });
    }

    private static void EndSketch(ModelDoc2 doc)
    {
        Call("ISketchManager.InsertSketch.end", () => { doc.SketchManager.InsertSketch(true); return true; });
        doc.ClearSelection2(true);
    }

    private static Feature FirstReferencePlane(ModelDoc2 doc, int ordinal)
    {
        var feature = (Feature)doc.FirstFeature();
        var current = 0;
        while (feature != null)
        {
            if (feature.GetTypeName2() == "RefPlane")
            {
                if (current == ordinal) return feature;
                current++;
            }
            feature = (Feature)feature.GetNextFeature();
        }
        throw new InvalidOperationException("reference plane not found");
    }

    private static Feature LastFeatureOfType(ModelDoc2 doc, string type)
    {
        Feature selected = null;
        var feature = (Feature)doc.FirstFeature();
        while (feature != null)
        {
            if (feature.GetTypeName2() == type) selected = feature;
            feature = (Feature)feature.GetNextFeature();
        }
        if (selected == null) throw new InvalidOperationException("feature type not found: " + type);
        return selected;
    }

    private static bool SelectFirstEdge(ModelDoc2 doc)
    {
        doc.ClearSelection2(true);
        var bodies = Bodies(doc);
        if (bodies.Length == 0) return false;
        var edges = ((Body2)bodies[0]).GetEdges() as object[];
        if (edges == null || edges.Length == 0) return false;
        return ((Entity)edges[0]).Select4(false, null);
    }

    private static bool SelectPlanarFace(ModelDoc2 doc, bool highest)
    {
        doc.ClearSelection2(true);
        var bodies = Bodies(doc);
        if (bodies.Length == 0) return false;
        var faces = ((Body2)bodies[0]).GetFaces() as object[];
        if (faces == null || faces.Length == 0) return false;
        Face2 selected = null;
        var selectedZ = highest ? double.NegativeInfinity : double.PositiveInfinity;
        foreach (var value in faces)
        {
            var face = (Face2)value;
            var box = face.GetBox() as double[];
            if (box == null || box.Length < 6) continue;
            var z = (box[2] + box[5]) / 2.0;
            if ((highest && z > selectedZ) || (!highest && z < selectedZ))
            {
                selected = face;
                selectedZ = z;
            }
        }
        return selected != null && ((Entity)selected).Select4(false, null);
    }

    private static object[] Bodies(ModelDoc2 doc)
    {
        var part = doc as PartDoc;
        if (part == null) return new object[0];
        return part.GetBodies2((int)swBodyType_e.swSolidBody, false) as object[] ?? new object[0];
    }

    private static int SketchGeometryCount(ModelDoc2 doc)
    {
        var total = 0;
        var feature = (Feature)doc.FirstFeature();
        while (feature != null)
        {
            var sketch = feature.GetSpecificFeature2() as Sketch;
            if (sketch != null)
            {
                var segments = sketch.GetSketchSegments() as object[];
                var points = sketch.GetSketchPoints2() as object[];
                total += segments == null ? 0 : segments.Length;
                total += points == null ? 0 : points.Length;
            }
            feature = (Feature)feature.GetNextFeature();
        }
        return total;
    }

    private static Dictionary<string, object> MutateFirstDrivingDimension(ModelDoc2 doc)
    {
        var result = new Dictionary<string, object> { { "attempted", false } };
        var feature = (Feature)doc.FirstFeature();
        while (feature != null)
        {
            var display = feature.GetFirstDisplayDimension() as DisplayDimension;
            while (display != null)
            {
                var dimension = display.GetDimension2(0);
                if (dimension != null && !dimension.DrivenState.Equals((int)swDimensionDrivenState_e.swDimensionDriven))
                {
                    var before = dimension.SystemValue;
                    var snapshotBefore = Snapshot(doc);
                    dimension.SystemValue = before * 1.125;
                    var rebuild = Call("IDimension.SystemValue.mutation", () => doc.ForceRebuild3(false));
                    var snapshotAfter = Snapshot(doc);
                    dimension.SystemValue = before;
                    var restored = Call("IDimension.SystemValue.restore", () => doc.ForceRebuild3(false));
                    result["attempted"] = true;
                    result["feature"] = feature.Name;
                    result["dimension"] = dimension.FullName;
                    result["before"] = before;
                    result["mutated"] = before * 1.125;
                    result["rebuild"] = rebuild;
                    result["restore_rebuild"] = restored;
                    result["snapshot_before"] = snapshotBefore;
                    result["snapshot_after"] = snapshotAfter;
                    result["shape_changed"] = Serialize(snapshotBefore) != Serialize(snapshotAfter);
                    return result;
                }
                display = feature.GetNextDisplayDimension(display) as DisplayDimension;
            }
            feature = (Feature)feature.GetNextFeature();
        }
        return result;
    }

    private static Dictionary<string, object> Snapshot(ModelDoc2 doc)
    {
        var features = new List<Dictionary<string, object>>();
        var feature = (Feature)doc.FirstFeature();
        var ordinal = 0;
        while (feature != null && ordinal < 10000)
        {
            var item = new Dictionary<string, object>
            {
                { "ordinal", ordinal },
                { "name", feature.Name },
                { "type", feature.GetTypeName2() },
                { "id", feature.GetID() },
                { "suppressed", feature.IsSuppressed2((int)swInConfigurationOpts_e.swThisConfiguration, null) }
            };
            try
            {
                var definition = feature.GetDefinition();
                item["definition_type"] = definition == null ? null : definition.GetType().FullName;
            }
            catch (Exception ex)
            {
                item["definition_error"] = ex.GetType().FullName;
            }
            features.Add(item);
            feature = (Feature)feature.GetNextFeature();
            ordinal++;
        }
        var bodies = Bodies(doc);
        var bodyData = new List<Dictionary<string, object>>();
        foreach (var value in bodies)
        {
            var body = (Body2)value;
            var faces = body.GetFaces() as object[];
            var edges = body.GetEdges() as object[];
            bodyData.Add(new Dictionary<string, object>
            {
                { "name", body.Name },
                { "face_count", faces == null ? 0 : faces.Length },
                { "edge_count", edges == null ? 0 : edges.Length }
            });
        }
        object box = null;
        var part = doc as PartDoc;
        if (part != null) box = Value(part.GetPartBox(false));
        return new Dictionary<string, object>
        {
            { "title", doc.GetTitle() },
            { "features", features },
            { "bodies", bodyData },
            { "part_box", box },
            { "sketch_geometry_count", SketchGeometryCount(doc) }
        };
    }

    private static void VerifyAndSave(ModelDoc2 doc, Dictionary<string, object> artifact, string path)
    {
        artifact["before_save"] = Snapshot(doc);
        artifact["rebuild_before_save"] = Call("IModelDoc2.ForceRebuild3.before_save", () => doc.ForceRebuild3(false));
        artifact["save_error"] = Call("IModelDoc2.SaveAs3", () => doc.SaveAs3(path, 0, (int)swSaveAsOptions_e.swSaveAsOptions_Silent));
        artifact["saved_exists"] = File.Exists(path);
        artifact["saved_length"] = File.Exists(path) ? new FileInfo(path).Length : 0L;
        if (!File.Exists(path)) throw new InvalidOperationException("save did not create output");
    }

    private static ModelDoc2 Open(string path, int type, Dictionary<string, object> artifact)
    {
        var errors = 0;
        var warnings = 0;
        var doc = Call("ISldWorks.OpenDoc6", () => (ModelDoc2)App.OpenDoc6(path, type, (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref errors, ref warnings));
        artifact["open_errors"] = errors;
        artifact["open_warnings"] = warnings;
        if (doc == null) throw new InvalidOperationException("OpenDoc6 returned null");
        return doc;
    }

    private static Dictionary<string, object> Artifact(string name, string path, string kind)
    {
        var artifact = new Dictionary<string, object>
        {
            { "name", name },
            { "path", path },
            { "kind", kind },
            { "status", "started" }
        };
        Artifacts.Add(artifact);
        return artifact;
    }

    private static void Close(ModelDoc2 doc)
    {
        var title = doc.GetTitle();
        Call("ISldWorks.CloseDoc", () => { App.CloseDoc(title); return true; });
    }

    private static void SafeClose(ModelDoc2 doc)
    {
        try { App.CloseDoc(doc.GetTitle()); } catch { }
    }

    private static T Required<T>(string api, Func<T> operation)
    {
        var value = Call(api, operation);
        if (ReferenceEquals(value, null)) throw new InvalidOperationException(api + " returned null");
        return value;
    }

    private static T Call<T>(string api, Func<T> operation)
    {
        var record = new Dictionary<string, object>
        {
            { "sequence", Calls.Count + 1 },
            { "timestamp_utc", DateTime.UtcNow.ToString("o") },
            { "api", api }
        };
        Calls.Add(record);
        try
        {
            var result = operation();
            record["success"] = true;
            record["result"] = Value(result);
            return result;
        }
        catch (Exception ex)
        {
            record["success"] = false;
            record["error_type"] = ex.GetType().FullName;
            record["error"] = ex.ToString();
            return default(T);
        }
    }

    private static int ArrayLength(object value)
    {
        var array = value as Array;
        return array == null ? 0 : array.Length;
    }

    private static object Value(object value)
    {
        if (value == null) return null;
        var type = value.GetType();
        if (type.IsPrimitive || value is string || value is decimal) return value;
        var array = value as Array;
        if (array != null)
        {
            var values = new List<object>();
            foreach (var item in array) values.Add(Value(item));
            return values;
        }
        if (Marshal.IsComObject(value)) return new Dictionary<string, object> { { "type", type.FullName }, { "com_object", true } };
        return Convert.ToString(value);
    }

    private static string Serialize(object value)
    {
        return new JavaScriptSerializer { MaxJsonLength = int.MaxValue, RecursionLimit = 1000 }.Serialize(value);
    }

    private static void WriteJson(string path, object value)
    {
        File.WriteAllText(path, Serialize(value));
    }
}
