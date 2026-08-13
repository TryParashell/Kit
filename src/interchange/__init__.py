# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase

from . import assembly as AssemblyModule
from . import brep as BrepModule
from . import document as DocumentModule
from . import geometry as GeometryModule
from . import history as HistoryModule
from . import mesh as MeshModule
from . import serialization as SerialModule
from . import types as TypesModule
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
    Vector2 as LegacyVectorTwo,
    Vector3 as LegacyVectorThree,
    frozen_mapping as FrozenMapping,
)
from .assembly import (
    AssemblyData,
    ComponentDef,
    ComponentDoc,
    ComponentInst,
    ComponentKind,
    MateAlignment,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    TransformMatrix,
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
from .common import FreezeMapping, KJsonScalar, KJsonValue
from .document import (
    AddWrapperMeta,
    CadDocument,
    DocumentError,
    FilterDocument,
    GetPayloadIds,
    GetRetainedCaps,
    GetSemanticMeta,
    InferCaps,
)
from .enums import (
    BooleanOp,
    Capability,
    ConstraintKind,
    FeatureKind,
    GeometryKind,
    ParameterRole,
    Severity,
    UnitSystem,
    ValueKind,
)
from .features import (
    ChamferFeature,
    CirclePattern,
    CombineFeature,
    DesignBody,
    DomeFeature,
    ExtrudeEnd,
    ExtrudeFeature,
    FeatureCfgState,
    FeatureDef,
    FeatureStep,
    FilletFeature,
    HoleFeature,
    LinearPattern,
    MoveBodyFeature,
    NativeFeature,
    RefPlaneFeature,
    RevolveFeature,
    ScaleFeature,
    ShellFeature,
)
from .geometry import (
    ArcEllipseGeom,
    ArcGeometry,
    ArcHyperGeom,
    ArcParabGeom,
    CircleGeometry,
    ConstraintRef,
    EllipseGeometry,
    HyperbolaGeom,
    LineGeometry,
    NativeGeometry,
    ParabolaGeom,
    PointGeometry,
    SelectPathElem,
    Selection,
    Sketch,
    SketchEntity,
    SketchRelation,
    SplineGeometry,
    SupportPlane,
)
from .history import AdapterCaps
from .mesh import SurfaceMesh
from .payloads import BrepPayload, MigratePayload, PayloadRole
from .package_exports import KPackageExports
from .python_compat import BindTypeGlobals
from .records import (
    CadSource,
    Configuration,
    Diagnostic,
    Expression,
    Parameter,
    ParameterValue,
    ParamOverride,
    Provenance,
    ProvenanceSpan,
    TopologyCounts,
)
from .serialization import RegMigration, RegisterTypes
from .vectors import BoundingBox, PlaneVector, SpaceVector, Transform

globals().update(
    {
        "AdapterCapabilities": AdapterCaps,
        "ArcEllipseGeometry": ArcEllipseGeom,
        "ArcHyperbolaGeometry": ArcHyperGeom,
        "ArcParabolaGeometry": ArcParabGeom,
        "Body": DesignBody,
        "BooleanOperation": BooleanOperation,
        "CircularPatternFeature": CirclePattern,
        "ComponentDefinition": ComponentDef,
        "ComponentDocument": ComponentDoc,
        "ComponentInstance": ComponentInst,
        "ConstraintReference": ConstraintRef,
        "CadDocumentValidationError": DocumentError,
        "ExtrusionEndCondition": ExtrudeEnd,
        "ExtrusionFeature": ExtrudeFeature,
        "FeatureDefinition": FeatureDef,
        "FeatureConfigurationState": FeatureCfgState,
        "HyperbolaGeometry": HyperbolaGeom,
        "LinearPatternFeature": LinearPattern,
        "Matrix4": TransformMatrix,
        "Mesh": SurfaceMesh,
        "NativeFeatureDefinition": NativeFeature,
        "ParabolaGeometry": ParabolaGeom,
        "ParameterOverride": ParameterOverride,
        "ReferencePlaneFeature": RefPlaneFeature,
        "RevolutionFeature": RevolveFeature,
        "SelectionPathElement": SelectPathElem,
        "SketchConstraint": SketchRelation,
        "TopologySummary": TopologyCounts,
        "Vector2": LegacyVectorTwo,
        "Vector3": LegacyVectorThree,
        "filter_document": FilterDocument,
        "frozen_mapping": FrozenMapping,
        "infer_capabilities": InferCaps,
        "retained_capabilities": GetRetainedCaps,
        "register_migration": RegMigration,
        "register_types": RegisterTypes,
        "semantic_metadata": GetSemanticMeta,
        "source_payload_indexes": GetPayloadIds,
        "with_wrapper_metadata": AddWrapperMeta,
    }
)

globals().update(
    {
        "assembly": AssemblyModule,
        "brep": BrepModule,
        "document": DocumentModule,
        "geometry": GeometryModule,
        "history": HistoryModule,
        "mesh": MeshModule,
        "serialization": SerialModule,
        "types": TypesModule,
    }
)

# package consumers need one intentional stable list of supported public symbols
__all__ = KPackageExports

BindTypeGlobals(
    (
        vars(AssemblyModule),
        vars(BrepModule),
        vars(DocumentModule),
        vars(GeometryModule),
        vars(HistoryModule),
        vars(MeshModule),
        vars(TypesModule),
    ),
    tuple(
        globals()[NameValue]
        for NameValue in __all__
        if isinstance(globals()[NameValue], type)
    ),
)

RegisterTypes(
    *(
        globals()[NameValue]
        for NameValue in __all__
        if isinstance(globals()[NameValue], type)
        and (
            IsDataClass(globals()[NameValue])
            or issubclass(globals()[NameValue], EnumBase)
        )
    )
)

RegMigration(BrepPayload, MigratePayload)
