using System;
using System.Collections.Generic;
using System.IO;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

internal static class ImportOracle
{
    private static object[] Values(object value)
    {
        return value as object[] ?? new object[0];
    }

    private static void Inspect(ModelDoc2 doc, string phase)
    {
        var part = doc as PartDoc;
        var solid = 0;
        var sheet = 0;
        var wire = 0;
        var faces = 0;
        var edges = 0;
        var vertices = 0;
        if (part != null)
        {
            foreach (var value in Values(part.GetBodies2((int)swBodyType_e.swAllBodies, true)))
            {
                var body = value as Body2;
                if (body == null)
                    continue;
                var type = body.GetType();
                if (type == (int)swBodyType_e.swSolidBody)
                    solid++;
                else if (type == (int)swBodyType_e.swSheetBody)
                    sheet++;
                else if (type == (int)swBodyType_e.swWireBody)
                    wire++;
                faces += Values(body.GetFaces()).Length;
                edges += Values(body.GetEdges()).Length;
                vertices += Values(body.GetVertices()).Length;
            }
        }
        Console.WriteLine(phase + " solid=" + solid + " sheet=" + sheet + " wire=" + wire + " faces=" + faces + " edges=" + edges + " vertices=" + vertices);
    }

    private static int Main(string[] args)
    {
        var app = new SldWorks();
        app.Visible = true;
        Console.WriteLine("revision=" + app.RevisionNumber());
        app.CloseAllDocuments(true);
        var errors = 0;
        var warnings = 0;
        ModelDoc2 doc;
        if (String.Equals(Path.GetExtension(args[0]), ".SLDPRT", StringComparison.OrdinalIgnoreCase))
            doc = (ModelDoc2)app.OpenDoc6(args[0], (int)swDocumentTypes_e.swDocPART, (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref errors, ref warnings);
        else
            doc = app.LoadFile4(args[0], "", null, ref errors);
        Console.WriteLine("load errors=" + errors + " warnings=" + warnings + " opened=" + (doc != null));
        if (doc == null)
        {
            app.ExitApp();
            return 1;
        }
        Inspect(doc, "before_save");
        var save = doc.SaveAs3(args[1], 0, 1);
        Console.WriteLine("save errors=" + save);
        app.CloseDoc(doc.GetTitle());
        warnings = 0;
        var reopenErrors = 0;
        var reopened = (ModelDoc2)app.OpenDoc6(args[1], (int)swDocumentTypes_e.swDocPART, (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref reopenErrors, ref warnings);
        Console.WriteLine("reopen errors=" + reopenErrors + " warnings=" + warnings + " opened=" + (reopened != null));
        if (reopened != null)
        {
            Inspect(reopened, "reopen_before_rebuild");
            Console.WriteLine("rebuild=" + reopened.ForceRebuild3(false));
            Inspect(reopened, "reopen_after_rebuild");
            app.CloseDoc(reopened.GetTitle());
        }
        app.ExitApp();
        return reopened == null ? 2 : 0;
    }
}
