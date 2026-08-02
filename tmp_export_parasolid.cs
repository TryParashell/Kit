using System;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

internal static class ExportParasolid
{
    private static int Main(string[] args)
    {
        var app = new SldWorks();
        app.Visible = false;
        var preference = (int)swUserPreferenceIntegerValue_e.swParasolidOutputVersion;
        var previous = app.GetUserPreferenceIntegerValue(preference);
        ModelDoc2 doc = null;
        try
        {
            var set = app.SetUserPreferenceIntegerValue(preference, (int)swParasolidOutputVersion_e.swParasolidOutputVersion_120);
            Console.WriteLine("preference " + previous + " " + set + " " + app.GetUserPreferenceIntegerValue(preference));
            var errors = 0;
            var warnings = 0;
            doc = (ModelDoc2)app.OpenDoc6(args[0], (int)swDocumentTypes_e.swDocPART, (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref errors, ref warnings);
            Console.WriteLine("open " + errors + " " + warnings + " " + (doc != null));
            if (doc == null)
            {
                return 1;
            }
            var result = doc.SaveAs3(args[1], 0, 1);
            Console.WriteLine("save " + result);
            return result == 0 ? 0 : 2;
        }
        finally
        {
            if (doc != null)
            {
                app.CloseDoc(doc.GetTitle());
            }
            var restored = app.SetUserPreferenceIntegerValue(preference, previous);
            Console.WriteLine("restore " + restored + " " + app.GetUserPreferenceIntegerValue(preference));
            app.ExitApp();
        }
    }
}
