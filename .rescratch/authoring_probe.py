from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import pythoncom  # noqa: E402
from win32com.client import VARIANT, Dispatch  # noqa: E402

OUTPUT = ROOT / ".rescratch" / "authored"
SW_DEFAULT_TEMPLATE_PART = 8


def byref_long() -> object:
    return VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)


def dispatch_value(owner: object, name: str) -> object:
    from win32com.client.dynamic import CDispatch

    attribute = getattr(owner, name)
    if isinstance(attribute, CDispatch) or not callable(attribute):
        return attribute
    return attribute()


def author_rectangle_pad(
    app: object,
    target: Path,
    *,
    width_mm: float,
    height_mm: float,
    depth_mm: float,
) -> None:
    template = app.GetUserPreferenceStringValue(SW_DEFAULT_TEMPLATE_PART)
    print("  template:", template, flush=True)
    model = app.NewDocument(template, 0, 0.0, 0.0)
    if model is None:
        raise RuntimeError("NewDocument returned None")
    model = Dispatch(model)
    selected = model.Extension.SelectByID2(
        "Front Plane", "PLANE", 0.0, 0.0, 0.0, False, 0, None, 0
    )
    print("  select plane:", selected, flush=True)
    model.SketchManager.InsertSketch(True)
    half_width = width_mm / 2000.0
    half_height = height_mm / 2000.0
    segments = model.SketchManager.CreateCornerRectangle(
        -half_width, -half_height, 0.0, half_width, half_height, 0.0
    )
    print(
        "  rectangle segments:",
        None if segments is None else len(segments),
        flush=True,
    )
    model.SketchManager.InsertSketch(True)
    model.ClearSelection2(True)
    picked = model.Extension.SelectByID2(
        "Sketch1", "SKETCH", 0.0, 0.0, 0.0, False, 0, None, 0
    )
    print("  select sketch:", picked, flush=True)
    feature = model.FeatureManager.FeatureExtrusion3(
        True,
        False,
        False,
        0,
        0,
        depth_mm / 1000.0,
        0.01,
        False,
        False,
        False,
        False,
        0.0,
        0.0,
        False,
        False,
        False,
        False,
        True,
        True,
        True,
        0,
        0.0,
        False,
    )
    print("  extrusion:", feature, flush=True)
    if feature is None:
        raise RuntimeError("FeatureExtrusion3 returned None")
    model.EditRebuild3()
    errors = byref_long()
    warnings = byref_long()
    ok = model.Extension.SaveAs2(
        str(target), 0, 1, None, "", False, errors, warnings
    )
    print(
        f"  saved={ok} errors={errors.value} warnings={warnings.value} "
        f"exists={target.is_file()}",
        flush=True,
    )
    app.CloseDoc(str(dispatch_value(model, "GetTitle")))


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    pythoncom.CoInitialize()
    app = Dispatch("SldWorks.Application")
    app.Visible = False
    app.UserControl = False
    try:
        cases = (
            ("rect_40x20x10", 40.0, 20.0, 10.0),
            ("rect_40x20x20", 40.0, 20.0, 20.0),
            ("rect_60x20x10", 60.0, 20.0, 10.0),
        )
        for label, width, height, depth in cases:
            print(f"{label}:", flush=True)
            target = OUTPUT / f"{label}.SLDPRT"
            if target.exists():
                target.unlink()
            try:
                author_rectangle_pad(
                    app,
                    target,
                    width_mm=width,
                    height_mm=height,
                    depth_mm=depth,
                )
            except Exception as exc:
                print(f"  FAILED {type(exc).__name__} {exc}", flush=True)
    finally:
        try:
            app.ExitApp()
        except Exception:
            pass
        pythoncom.CoUninitialize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
