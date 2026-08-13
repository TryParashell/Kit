# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap


# renamed models retain historical wire tags so stored documents remain readable
KWireTypes: TypeMap[str, str] = {
    "AdapterCaps": "AdapterCapabilities",
    "ArcEllipseGeom": "ArcEllipseGeometry",
    "ArcHyperGeom": "ArcHyperbolaGeometry",
    "ArcParabGeom": "ArcParabolaGeometry",
    "BooleanOp": "BooleanOperation",
    "CirclePattern": "CircularPatternFeature",
    "ComponentDef": "ComponentDefinition",
    "ComponentDoc": "ComponentDocument",
    "ComponentInst": "ComponentInstance",
    "ConstraintRef": "ConstraintReference",
    "DesignBody": "Body",
    "DocumentError": "CadDocumentValidationError",
    "ExtrudeEnd": "ExtrusionEndCondition",
    "ExtrudeFeature": "ExtrusionFeature",
    "FeatureCfgState": "FeatureConfigurationState",
    "FeatureDef": "FeatureDefinition",
    "HyperbolaGeom": "HyperbolaGeometry",
    "IntersectCurve": "IntersectionCurve",
    "LinearPattern": "LinearPatternFeature",
    "NativeFeature": "NativeFeatureDefinition",
    "ParamOverride": "ParameterOverride",
    "ParabolaGeom": "ParabolaGeometry",
    "PlaneVector": "Vector2",
    "RefPlaneFeature": "ReferencePlaneFeature",
    "RevolveFeature": "RevolutionFeature",
    "SelectPathElem": "SelectionPathElement",
    "SketchRelation": "SketchConstraint",
    "SpaceVector": "Vector3",
    "SurfaceMesh": "Mesh",
    "TopologyCounts": "TopologySummary",
    "TransformMatrix": "Matrix4",
}
