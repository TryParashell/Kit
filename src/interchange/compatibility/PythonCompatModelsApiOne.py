# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap


# historical api identity set 1 keeps pickle globals stable after module splits
KLegacyApiOne: TypeMap[str, tuple[str, str]] = {
    "CadDocument": ("CadDocument", "interchange.document"),
    "PointGeometry": ("PointGeometry", "interchange.geometry"),
    "LineGeometry": ("LineGeometry", "interchange.geometry"),
    "CircleGeometry": ("CircleGeometry", "interchange.geometry"),
    "ArcGeometry": ("ArcGeometry", "interchange.geometry"),
    "EllipseGeometry": ("EllipseGeometry", "interchange.geometry"),
    "ArcEllipseGeom": ("ArcEllipseGeometry", "interchange.geometry"),
    "HyperbolaGeom": ("HyperbolaGeometry", "interchange.geometry"),
    "ArcHyperGeom": ("ArcHyperbolaGeometry", "interchange.geometry"),
    "ParabolaGeom": ("ParabolaGeometry", "interchange.geometry"),
    "ArcParabGeom": ("ArcParabolaGeometry", "interchange.geometry"),
    "SplineGeometry": ("SplineGeometry", "interchange.geometry"),
    "NativeGeometry": ("NativeGeometry", "interchange.geometry"),
    "SupportPlane": ("SupportPlane", "interchange.geometry"),
    "SketchEntity": ("SketchEntity", "interchange.geometry"),
    "ConstraintRef": ("ConstraintReference", "interchange.geometry"),
    "SketchRelation": ("SketchConstraint", "interchange.geometry"),
    "Sketch": ("Sketch", "interchange.geometry"),
    "SelectPathElem": ("SelectionPathElement", "interchange.geometry"),
    "Selection": ("Selection", "interchange.geometry"),
    "FeatureCfgState": ("FeatureConfigurationState", "interchange.history"),
    "ExtrudeFeature": ("ExtrusionFeature", "interchange.history"),
    "FilletFeature": ("FilletFeature", "interchange.history"),
    "RevolveFeature": ("RevolutionFeature", "interchange.history"),
}
