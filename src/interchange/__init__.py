# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .assembly import (
    AssemblyData,
    ComponentDefinition,
    ComponentDocument,
    ComponentInstance,
    ComponentKind,
    MateAlignment,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4,
)
from .brep import (
    BrepBody,
    BrepCoedge,
    BrepCurve,
    BrepEdge,
    BrepEntity,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepPcurve,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    BrepWire,
    CircleCurve,
    CirclePcurve,
    ConeSurface,
    CylinderSurface,
    EllipseCurve,
    IntersectionCurve,
    LineCurve,
    LinePcurve,
    NativeCurve,
    NativePcurve,
    NativeSurface,
    NurbsCurve,
    NurbsPcurve,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
)
from .document import (
    CadDocument,
    CadDocumentValidationError,
    filter_document,
    infer_capabilities,
    retained_capabilities,
    semantic_metadata,
    source_payload_indexes,
    with_wrapper_metadata,
)
from .geometry import (
    ArcEllipseGeometry,
    ArcGeometry,
    ArcHyperbolaGeometry,
    ArcParabolaGeometry,
    CircleGeometry,
    ConstraintReference,
    EllipseGeometry,
    HyperbolaGeometry,
    LineGeometry,
    NativeGeometry,
    ParabolaGeometry,
    PointGeometry,
    Selection,
    SelectionPathElement,
    Sketch,
    SketchConstraint,
    SketchEntity,
    SplineGeometry,
    SupportPlane,
)
from .history import (
    AdapterCapabilities,
    Body,
    BrepPayload,
    ChamferFeature,
    CombineFeature,
    DomeFeature,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureConfigurationState,
    FeatureDefinition,
    FeatureStep,
    FilletFeature,
    HoleFeature,
    MoveBodyFeature,
    NativeFeatureDefinition,
    PayloadRole,
    ReferencePlaneFeature,
    RevolutionFeature,
    ScaleFeature,
    ShellFeature,
    TopologySummary,
    _migrate_brep_payload,
)
from .mesh import Mesh
from .serialization import register_migration, register_types
from .types import (
    BooleanOperation,
    BoundingBox,
    CadSource,
    Capability,
    Configuration,
    ConstraintKind,
    Diagnostic,
    Expression,
    FeatureKind,
    GeometryKind,
    Parameter,
    ParameterOverride,
    ParameterRole,
    ParameterValue,
    Provenance,
    ProvenanceSpan,
    Severity,
    Transform,
    UnitSystem,
    ValueKind,
    Vector2,
    Vector3,
    frozen_mapping,
)


from dataclasses import is_dataclass as _is_dataclass
from enum import Enum as _Enum

register_types(
    *(
        value
        for name, value in tuple(globals().items())
        if not name.startswith("_")
        and isinstance(value, type)
        and (_is_dataclass(value) or issubclass(value, _Enum))
    )
)
register_migration(BrepPayload, _migrate_brep_payload)


__all__ = [name for name in globals() if not name.startswith("_")]
