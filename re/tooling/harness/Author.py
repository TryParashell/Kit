import os
import pathlib

import FreeCAD as App
import Part
import Sketcher

OUTPUT = os.environ.get(
    "KIT_FCSTD_OUT",
    str(pathlib.Path(__file__).resolve().parents[3] / ".rescratch" / "sw" / "fcstd"),
)

PLANES = {
    "front": "XY_Plane",
    "top": "XZ_Plane",
    "right": "YZ_Plane",
}


def _new(name):
    document = App.newDocument(name)
    body = document.addObject("PartDesign::Body", "Body")
    return document, body


def _rectangle(document, body, label, plane, bounds):
    sketch = document.addObject("Sketcher::SketchObject", label)
    body.addObject(sketch)
    sketch.AttachmentSupport = [(document.getObject(PLANES[plane]), "")]
    sketch.MapMode = "FlatFace"
    minimum_x, minimum_y, maximum_x, maximum_y = bounds
    corners = (
        (minimum_x, minimum_y),
        (maximum_x, minimum_y),
        (maximum_x, maximum_y),
        (minimum_x, maximum_y),
    )
    for index in range(4):
        start = corners[index]
        end = corners[(index + 1) % 4]
        sketch.addGeometry(
            Part.LineSegment(
                App.Vector(start[0], start[1], 0.0),
                App.Vector(end[0], end[1], 0.0),
            ),
            False,
        )
    for index in range(4):
        sketch.addConstraint(
            Sketcher.Constraint("Coincident", index, 2, (index + 1) % 4, 1)
        )
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
    sketch.addConstraint(Sketcher.Constraint("Horizontal", 2))
    sketch.addConstraint(Sketcher.Constraint("Vertical", 1))
    sketch.addConstraint(Sketcher.Constraint("Vertical", 3))
    sketch.addConstraint(
        Sketcher.Constraint("DistanceX", 0, 1, 0, 2, maximum_x - minimum_x)
    )
    sketch.addConstraint(
        Sketcher.Constraint("DistanceY", 1, 1, 1, 2, maximum_y - minimum_y)
    )
    document.recompute()
    return sketch


def _circle(document, body, label, plane, centre, radius):
    sketch = document.addObject("Sketcher::SketchObject", label)
    body.addObject(sketch)
    sketch.AttachmentSupport = [(document.getObject(PLANES[plane]), "")]
    sketch.MapMode = "FlatFace"
    sketch.addGeometry(
        Part.Circle(
            App.Vector(centre[0], centre[1], 0.0), App.Vector(0.0, 0.0, 1.0), radius
        ),
        False,
    )
    sketch.addConstraint(Sketcher.Constraint("Radius", 0, radius))
    document.recompute()
    return sketch


def _pad(document, body, label, sketch, length, midplane=False, reversed_flag=False):
    pad = document.addObject("PartDesign::Pad", label)
    body.addObject(pad)
    pad.Profile = sketch
    pad.Length = length
    pad.Type = 0
    pad.Midplane = midplane
    pad.Reversed = reversed_flag
    document.recompute()
    return pad


def _pocket_through(document, body, label, sketch, reversed_flag=False):
    pocket = document.addObject("PartDesign::Pocket", label)
    body.addObject(pocket)
    pocket.Profile = sketch
    pocket.Type = 1
    pocket.Midplane = False
    pocket.Reversed = reversed_flag
    document.recompute()
    return pocket


def _pocket(document, body, label, sketch, length, reversed_flag=False):
    pocket = document.addObject("PartDesign::Pocket", label)
    body.addObject(pocket)
    pocket.Profile = sketch
    pocket.Length = length
    pocket.Type = 0
    pocket.Midplane = False
    pocket.Reversed = reversed_flag
    document.recompute()
    return pocket


def _save(document, body, name):
    target = f"{OUTPUT}\\{name}.FCStd"
    document.saveAs(target)
    shape = body.Shape
    print(
        f"KIT_AUTHORED {name} volume_mm3={shape.Volume!r} area_mm2={shape.Area!r} "
        f"solids={len(shape.Solids)} valid={shape.isValid()} path={target}",
        flush=True,
    )
    App.closeDocument(document.Name)


def boss_blind(name):
    document, body = _new(name)
    sketch = _rectangle(document, body, "Sketch", "front", (-25.0, -15.0, 25.0, 15.0))
    _pad(document, body, "Pad", sketch, 12.0)
    _save(document, body, name)


def boss_cut(name):
    document, body = _new(name)
    outer = _rectangle(document, body, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0))
    _pad(document, body, "Pad", outer, 15.0)
    inner = _rectangle(document, body, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0))
    _pocket(document, body, "Pocket", inner, 6.0, reversed_flag=True)
    _save(document, body, name)


def boss_boss(name):
    document, body = _new(name)
    outer = _rectangle(document, body, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0))
    _pad(document, body, "Pad", outer, 10.0)
    inner = _rectangle(document, body, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0))
    _pad(document, body, "Pad001", inner, 25.0)
    _save(document, body, name)


def boss_cut_cut(name):
    document, body = _new(name)
    outer = _rectangle(document, body, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0))
    _pad(document, body, "Pad", outer, 15.0)
    first = _rectangle(document, body, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0))
    _pocket(document, body, "Pocket", first, 6.0, reversed_flag=True)
    second = _rectangle(document, body, "Sketch002", "front", (15.0, -5.0, 25.0, 5.0))
    _pocket(document, body, "Pocket001", second, 5.0, reversed_flag=True)
    _save(document, body, name)


def boss_cut_cut_cut(name):
    document, body = _new(name)
    outer = _rectangle(document, body, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0))
    _pad(document, body, "Pad", outer, 15.0)
    first = _rectangle(document, body, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0))
    _pocket(document, body, "Pocket", first, 6.0, reversed_flag=True)
    second = _rectangle(document, body, "Sketch002", "front", (15.0, -5.0, 25.0, 5.0))
    _pocket(document, body, "Pocket001", second, 5.0, reversed_flag=True)
    third = _rectangle(document, body, "Sketch003", "front", (-25.0, -4.0, -17.0, 4.0))
    _pocket(document, body, "Pocket002", third, 4.0, reversed_flag=True)
    _save(document, body, name)


def boss_cut_through(name):
    document, body = _new(name)
    outer = _rectangle(document, body, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0))
    _pad(document, body, "Pad", outer, 15.0)
    inner = _rectangle(document, body, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0))
    _pocket_through(document, body, "Pocket", inner, reversed_flag=True)
    _save(document, body, name)


def circle_boss(name):
    document, body = _new(name)
    sketch = _circle(document, body, "Sketch", "front", (0.0, 0.0), 14.0)
    _pad(document, body, "Pad", sketch, 9.0)
    _save(document, body, name)


def boss_midplane(name):
    document, body = _new(name)
    sketch = _rectangle(document, body, "Sketch", "front", (-20.0, -12.0, 20.0, 12.0))
    _pad(document, body, "Pad", sketch, 18.0, midplane=True)
    _save(document, body, name)


def boss_right_plane(name):
    document, body = _new(name)
    sketch = _rectangle(document, body, "Sketch", "right", (-18.0, -11.0, 18.0, 11.0))
    _pad(document, body, "Pad", sketch, 7.0)
    _save(document, body, name)


def boss_top_plane(name):
    document, body = _new(name)
    sketch = _rectangle(document, body, "Sketch", "top", (-22.0, -9.0, 22.0, 9.0))
    _pad(document, body, "Pad", sketch, 13.0)
    _save(document, body, name)


def boss_reversed(name):
    document, body = _new(name)
    sketch = _rectangle(document, body, "Sketch", "front", (-16.0, -16.0, 16.0, 16.0))
    _pad(document, body, "Pad", sketch, 11.0, reversed_flag=True)
    _save(document, body, name)


import sys

CASES = {
    "kit_boss_blind": boss_blind,
    "kit_boss_cut": boss_cut,
    "kit_boss_boss": boss_boss,
    "kit_boss_cut_cut": boss_cut_cut,
    "kit_boss_cut_cut_cut": boss_cut_cut_cut,
    "kit_boss_cut_through": boss_cut_through,
    "kit_circle_boss": circle_boss,
    "kit_boss_midplane": boss_midplane,
    "kit_boss_right_plane": boss_right_plane,
    "kit_boss_top_plane": boss_top_plane,
    "kit_boss_reversed": boss_reversed,
}

selected = [item for item in sys.argv[1:] if item in CASES] or list(CASES)
for label in selected:
    CASES[label](label)
print("KIT_DONE", flush=True)
