from __future__ import annotations

from pathlib import Path
import sys

import pythoncom
from win32com.client import VARIANT, Dispatch

ROOT = Path(__file__).parent
SAMPLE = ROOT / "examples" / ".SLDPRT" / "example.SLDPRT"


def probe(label: str, action: object) -> None:
    try:
        value = action()
    except Exception as exc:
        print(f"{label}: FAIL {type(exc).__name__} {exc}", flush=True)
        return
    print(f"{label}: OK {value!r}", flush=True)


def main() -> int:
    probe(
        "CLSIDFromProgID",
        lambda: pythoncom.CLSIDFromProgID("SldWorks.Application"),
    )
    pythoncom.CoInitialize()
    app = Dispatch("SldWorks.Application")
    app.Visible = False
    errors = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    model = app.OpenDoc6(str(SAMPLE), 1, 1, "", errors, warnings)
    print("model:", model, "errors:", errors.value, flush=True)
    probe("GetType", lambda: model.GetType)
    probe("GetTitle", lambda: model.GetTitle())
    probe("FirstFeature-call", lambda: model.FirstFeature())
    probe("FirstFeature-prop", lambda: model.FirstFeature)
    probe("FeatureManager", lambda: model.FeatureManager)
    probe(
        "GetFeatureCount",
        lambda: model.Extension.GetFeatureCount(),
    )
    feature = None
    try:
        feature = model.FirstFeature()
    except Exception:
        feature = None
    if feature is None:
        try:
            feature = model.FeatureByPositionReverse(0)
            print("fallback FeatureByPositionReverse:", feature, flush=True)
        except Exception as exc:
            print("fallback failed:", exc, flush=True)
    walked = 0
    while feature is not None and walked < 80:
        walked += 1
        try:
            name = feature.Name
        except Exception as exc:
            name = f"<name failed {exc}>"
        try:
            type_name = feature.GetTypeName2()
        except Exception as exc:
            type_name = f"<type failed {exc}>"
        print(f"  feature[{walked}] name={name!r} type={type_name!r}", flush=True)
        try:
            feature = feature.GetNextFeature()
        except Exception as exc:
            print("  next failed:", exc, flush=True)
            break
    probe("Extension.CreateMassProperty", lambda: model.Extension.CreateMassProperty())
    probe(
        "Extension.CreateMassProperty2",
        lambda: model.Extension.CreateMassProperty2(-1, "", False),
    )
    probe("GetMassProperties", lambda: model.Extension.GetMassProperties(1, errors))
    probe(
        "GetMassProperties2",
        lambda: model.Extension.GetMassProperties2(1, errors, True),
    )
    probe("Parameter-D1", lambda: model.Parameter("D1@Sketch1"))
    app.CloseDoc(model.GetTitle())
    app.ExitApp()
    pythoncom.CoUninitialize()
    return 0


if __name__ == "__main__":
    sys.exit(main())
