# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import os as OsLayer
import pathlib as Pathlib
import FreeCAD as AppInfo
import Part as PartInfo
import Sketcher

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutput = OsLayer.environ.get(
    "KIT_FCSTD_OUT",
    str(Pathlib.Path(__file__).resolve().parents[3] / ".rescratch" / "sw" / "fcstd"),
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KPlanes = {"front": "XY_Plane", "top": "XZ_Plane", "right": "YZ_Plane"}


# needed to keep reverse engineering responsibilities isolated and maintainable
def NewInfo(NameTextInfo):
    Document = AppInfo.newDocument(NameTextInfo)
    BodyInfo = Document.addObject("PartDesign::Body", "Body")
    return (Document, BodyInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def RectangleInfo(Document, BodyInfo, LabelInfo, Plane, Bounds):
    Sketch = Document.addObject("Sketcher::SketchObject", LabelInfo)
    BodyInfo.addObject(Sketch)
    Sketch.AttachmentSupport = [(Document.getObject(KPlanes[Plane]), "")]
    Sketch.MapMode = "FlatFace"
    MinimumX, MinimumY, MaximumX, MaximumY = Bounds
    Corners = (
        (MinimumX, MinimumY),
        (MaximumX, MinimumY),
        (MaximumX, MaximumY),
        (MinimumX, MaximumY),
    )
    for IndexData in range(4):
        StartRun = Corners[IndexData]
        EndIndex = Corners[(IndexData + 1) % 4]
        Sketch.addGeometry(
            PartInfo.LineSegment(
                AppInfo.Vector(StartRun[0], StartRun[1], 0.0),
                AppInfo.Vector(EndIndex[0], EndIndex[1], 0.0),
            ),
            False,
        )
    for IndexData in range(4):
        Sketch.addConstraint(
            Sketcher.Constraint("Coincident", IndexData, 2, (IndexData + 1) % 4, 1)
        )
    Sketch.addConstraint(Sketcher.Constraint("Horizontal", 0))
    Sketch.addConstraint(Sketcher.Constraint("Horizontal", 2))
    Sketch.addConstraint(Sketcher.Constraint("Vertical", 1))
    Sketch.addConstraint(Sketcher.Constraint("Vertical", 3))
    Sketch.addConstraint(
        Sketcher.Constraint("DistanceX", 0, 1, 0, 2, MaximumX - MinimumX)
    )
    Sketch.addConstraint(
        Sketcher.Constraint("DistanceY", 1, 1, 1, 2, MaximumY - MinimumY)
    )
    Document.recompute()
    return Sketch


# needed to keep reverse engineering responsibilities isolated and maintainable
def CircleInfo(Document, BodyInfo, LabelInfo, Plane, Centre, Radius):
    Sketch = Document.addObject("Sketcher::SketchObject", LabelInfo)
    BodyInfo.addObject(Sketch)
    Sketch.AttachmentSupport = [(Document.getObject(KPlanes[Plane]), "")]
    Sketch.MapMode = "FlatFace"
    Sketch.addGeometry(
        PartInfo.Circle(
            AppInfo.Vector(Centre[0], Centre[1], 0.0),
            AppInfo.Vector(0.0, 0.0, 1.0),
            Radius,
        ),
        False,
    )
    Sketch.addConstraint(Sketcher.Constraint("Radius", 0, Radius))
    Document.recompute()
    return Sketch


# needed to keep reverse engineering responsibilities isolated and maintainable
def PadInfo(
    Document, BodyInfo, LabelInfo, Sketch, Length, Midplane=False, ReversedFlag=False
):
    PadInfoInfo = Document.addObject("PartDesign::Pad", LabelInfo)
    BodyInfo.addObject(PadInfoInfo)
    PadInfoInfo.Profile = Sketch
    PadInfoInfo.Length = Length
    setattr(PadInfoInfo, "Type", 0)
    PadInfoInfo.Midplane = Midplane
    PadInfoInfo.Reversed = ReversedFlag
    Document.recompute()
    return PadInfoInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def PocketThrough(Document, BodyInfo, LabelInfo, Sketch, ReversedFlag=False):
    PocketInfo = Document.addObject("PartDesign::Pocket", LabelInfo)
    BodyInfo.addObject(PocketInfo)
    PocketInfo.Profile = Sketch
    setattr(PocketInfo, "Type", 1)
    PocketInfo.Midplane = False
    PocketInfo.Reversed = ReversedFlag
    Document.recompute()
    return PocketInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def Pocket(Document, BodyInfo, LabelInfo, Sketch, Length, ReversedFlag=False):
    PocketInfo = Document.addObject("PartDesign::Pocket", LabelInfo)
    BodyInfo.addObject(PocketInfo)
    PocketInfo.Profile = Sketch
    PocketInfo.Length = Length
    setattr(PocketInfo, "Type", 0)
    PocketInfo.Midplane = False
    PocketInfo.Reversed = ReversedFlag
    Document.recompute()
    return PocketInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def SaveInfo(Document, BodyInfo, NameTextInfo):
    Target = f"{KOutput}\\{NameTextInfo}.FCStd"
    Document.saveAs(Target)
    Shape = BodyInfo.Shape
    print(
        f"KIT_AUTHORED {NameTextInfo} volume_mm3={Shape.Volume!r} area_mm2={Shape.Area!r} solids={len(Shape.Solids)} valid={Shape.isValid()} path={Target}",
        flush=True,
    )
    AppInfo.closeDocument(Document.Name)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossBlind(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Sketch = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-25.0, -15.0, 25.0, 15.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Sketch, 12.0)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossCut(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Outer = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Outer, 15.0)
    Inner = RectangleInfo(
        Document, BodyInfo, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0)
    )
    Pocket(Document, BodyInfo, "Pocket", Inner, 6.0, ReversedFlag=True)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossBoss(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Outer = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Outer, 10.0)
    Inner = RectangleInfo(
        Document, BodyInfo, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0)
    )
    PadInfo(Document, BodyInfo, "Pad001", Inner, 25.0)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossCutCut(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Outer = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Outer, 15.0)
    First = RectangleInfo(
        Document, BodyInfo, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0)
    )
    Pocket(Document, BodyInfo, "Pocket", First, 6.0, ReversedFlag=True)
    Second = RectangleInfo(
        Document, BodyInfo, "Sketch002", "front", (15.0, -5.0, 25.0, 5.0)
    )
    Pocket(Document, BodyInfo, "Pocket001", Second, 5.0, ReversedFlag=True)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossCutCutCut(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Outer = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Outer, 15.0)
    First = RectangleInfo(
        Document, BodyInfo, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0)
    )
    Pocket(Document, BodyInfo, "Pocket", First, 6.0, ReversedFlag=True)
    Second = RectangleInfo(
        Document, BodyInfo, "Sketch002", "front", (15.0, -5.0, 25.0, 5.0)
    )
    Pocket(Document, BodyInfo, "Pocket001", Second, 5.0, ReversedFlag=True)
    Third = RectangleInfo(
        Document, BodyInfo, "Sketch003", "front", (-25.0, -4.0, -17.0, 4.0)
    )
    Pocket(Document, BodyInfo, "Pocket002", Third, 4.0, ReversedFlag=True)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossCutThrough(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Outer = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-30.0, -20.0, 30.0, 20.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Outer, 15.0)
    Inner = RectangleInfo(
        Document, BodyInfo, "Sketch001", "front", (-10.0, -8.0, 10.0, 8.0)
    )
    PocketThrough(Document, BodyInfo, "Pocket", Inner, ReversedFlag=True)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def CircleBoss(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Sketch = CircleInfo(Document, BodyInfo, "Sketch", "front", (0.0, 0.0), 14.0)
    PadInfo(Document, BodyInfo, "Pad", Sketch, 9.0)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossMidplane(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Sketch = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-20.0, -12.0, 20.0, 12.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Sketch, 18.0, Midplane=True)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossRightPlane(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Sketch = RectangleInfo(
        Document, BodyInfo, "Sketch", "right", (-18.0, -11.0, 18.0, 11.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Sketch, 7.0)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossTopPlane(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Sketch = RectangleInfo(
        Document, BodyInfo, "Sketch", "top", (-22.0, -9.0, 22.0, 9.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Sketch, 13.0)
    SaveInfo(Document, BodyInfo, NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossReversed(NameTextInfo):
    Document, BodyInfo = NewInfo(NameTextInfo)
    Sketch = RectangleInfo(
        Document, BodyInfo, "Sketch", "front", (-16.0, -16.0, 16.0, 16.0)
    )
    PadInfo(Document, BodyInfo, "Pad", Sketch, 11.0, ReversedFlag=True)
    SaveInfo(Document, BodyInfo, NameTextInfo)


import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KCases = {
    "kit_boss_blind": BossBlind,
    "kit_boss_cut": BossCut,
    "kit_boss_boss": BossBoss,
    "kit_boss_cut_cut": BossCutCut,
    "kit_boss_cut_cut_cut": BossCutCutCut,
    "kit_boss_cut_through": BossCutThrough,
    "kit_circle_boss": CircleBoss,
    "kit_boss_midplane": BossMidplane,
    "kit_boss_right_plane": BossRightPlane,
    "kit_boss_top_plane": BossTopPlane,
    "kit_boss_reversed": BossReversed,
}

# needed to keep reverse engineering responsibilities isolated and maintainable
KSelected = [ItemData for ItemData in System.argv[1:] if ItemData in KCases] or list(
    KCases
)
for LabelInfo in KSelected:
    KCases[LabelInfo](LabelInfo)
print("KIT_DONE", flush=True)
