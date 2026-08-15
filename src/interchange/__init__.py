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
from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.AssemblyEnums import (
    ComponentKind,
    MateAlignment,
    MateEntityKind,
    MateKind,
)
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentDocument import ComponentDoc
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity
from interchange.assembly.MateGroup import MateGroup
from interchange.assembly.TransformMatrix import TransformMatrix
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
from interchange.document.models.DocumentCaps import GetRetainedCaps, InferCaps
from interchange.document.models.DocumentError import DocumentError
from interchange.document.models.DocumentFilter import FilterDocument
from interchange.document.models.DocumentMetadata import AddWrapperMeta, GetSemanticMeta
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentPayload import GetPayloadIds
from interchange.enums.EnumDocument import Capability, Severity
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureContract import FeatureDef
from interchange.features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.features.FeatureKinds import (
    ChamferFeature,
    CirclePattern,
    CombineFeature,
    DomeFeature,
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
from interchange.features.FeatureStep import FeatureCfgState, FeatureStep
from interchange.geometry.models.GeometryConics import (
    ArcEllipseGeom,
    ArcHyperGeom,
    ArcParabGeom,
    EllipseGeometry,
    HyperbolaGeom,
    ParabolaGeom,
)
from interchange.geometry.models.GeometryCurves import (
    ArcGeometry,
    CircleGeometry,
    LineGeometry,
    NativeGeometry,
    PointGeometry,
    SplineGeometry,
)
from interchange.geometry.models.Selection import Selection, SelectPathElem
from interchange.geometry.models.Sketch import (
    ConstraintRef,
    Sketch,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.models.SupportPlane import SupportPlane
from .geometry.models.VectorPlane import PlaneVector
from .geometry.models.VectorSpace import SpaceVector
from .history import AdapterCaps
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.payloads.PayloadMigrate import MigratePayload
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.payloads.PayloadRoles import PayloadRole
from interchange.compatibility.PythonCompat import BindTypeGlobals
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.records.RecordProvenance import Provenance, ProvenanceSpan
from interchange.records.RecordSource import CadSource
from interchange.records.RecordTopology import TopologyCounts
from interchange.serialization.MigrationRegistry import RegMigration
from interchange.serialization.TypeRegistry import RegisterTypes
from interchange.geometry.models.Vectors import (
    BoundingBox,
    Transform,
)

# direct aliases make the runtime public contract visible to static analyzers
AdapterCapabilities = AdapterCaps
ArcEllipseGeometry = ArcEllipseGeom
ArcHyperbolaGeometry = ArcHyperGeom
ArcParabolaGeometry = ArcParabGeom
Body = DesignBody
CircularPatternFeature = CirclePattern
ComponentDefinition = ComponentDef
ComponentDocument = ComponentDoc
ComponentInstance = ComponentInst
ConstraintReference = ConstraintRef
CadDocumentValidationError = DocumentError
ExtrusionEndCondition = ExtrudeEnd
ExtrusionFeature = ExtrudeFeature
FeatureDefinition = FeatureDef
FeatureConfigurationState = FeatureCfgState
HyperbolaGeometry = HyperbolaGeom
LinearPatternFeature = LinearPattern
Matrix4 = TransformMatrix
Mesh = SurfaceMesh
NativeFeatureDefinition = NativeFeature
ParabolaGeometry = ParabolaGeom
ReferencePlaneFeature = RefPlaneFeature
RevolutionFeature = RevolveFeature
SelectionPathElement = SelectPathElem
SketchConstraint = SketchRelation
TopologySummary = TopologyCounts
Vector2 = LegacyVectorTwo
Vector3 = LegacyVectorThree
filter_document = FilterDocument
frozen_mapping = FrozenMapping
infer_capabilities = InferCaps
retained_capabilities = GetRetainedCaps
register_migration = RegMigration
register_types = RegisterTypes
semantic_metadata = GetSemanticMeta
source_payload_indexes = GetPayloadIds
with_wrapper_metadata = AddWrapperMeta
assembly = AssemblyModule
brep = BrepModule
document = DocumentModule
geometry = GeometryModule
history = HistoryModule
mesh = MeshModule
serialization = SerialModule
types = TypesModule

# package consumers need one intentional stable list of supported public symbols
__all__ = (
    "AdapterCapabilities",
    "ArcEllipseGeometry",
    "ArcGeometry",
    "ArcHyperbolaGeometry",
    "ArcParabolaGeometry",
    "AssemblyData",
    "Body",
    "BooleanOperation",
    "BoundingBox",
    "BrepBody",
    "BrepCoedge",
    "BrepCurve",
    "BrepEdge",
    "BrepEntity",
    "BrepFace",
    "BrepFaceUse",
    "BrepLoop",
    "BrepModel",
    "BrepPayload",
    "BrepPcurve",
    "BrepRegion",
    "BrepShell",
    "BrepShellUse",
    "BrepSurface",
    "BrepVertex",
    "BrepWire",
    "CadDocument",
    "CadDocumentValidationError",
    "CadSource",
    "Capability",
    "ChamferFeature",
    "CircleCurve",
    "CircleGeometry",
    "CirclePcurve",
    "CircularPatternFeature",
    "CombineFeature",
    "ComponentDefinition",
    "ComponentDocument",
    "ComponentInstance",
    "ComponentKind",
    "Configuration",
    "ConeSurface",
    "ConstraintKind",
    "ConstraintReference",
    "CylinderSurface",
    "Diagnostic",
    "DomeFeature",
    "EllipseCurve",
    "EllipseGeometry",
    "Expression",
    "ExtrusionEndCondition",
    "ExtrusionFeature",
    "FeatureConfigurationState",
    "FeatureDefinition",
    "FeatureKind",
    "FeatureStep",
    "FilletFeature",
    "GeometryKind",
    "HoleFeature",
    "HyperbolaGeometry",
    "IntersectionCurve",
    "LineCurve",
    "LineGeometry",
    "LinePcurve",
    "LinearPatternFeature",
    "MateAlignment",
    "MateConstraint",
    "MateEntity",
    "MateEntityKind",
    "MateGroup",
    "MateKind",
    "Matrix4",
    "Mesh",
    "MoveBodyFeature",
    "NativeCurve",
    "NativeFeatureDefinition",
    "NativeGeometry",
    "NativePcurve",
    "NativeSurface",
    "NurbsCurve",
    "NurbsPcurve",
    "NurbsSurface",
    "OffsetSurface",
    "Parameter",
    "ParameterOverride",
    "ParameterRole",
    "ParameterValue",
    "ParabolaGeometry",
    "PayloadRole",
    "PlaneSurface",
    "PointGeometry",
    "PlaneVector",
    "Provenance",
    "ProvenanceSpan",
    "ReferencePlaneFeature",
    "RevolutionFeature",
    "ScaleFeature",
    "Selection",
    "SelectionPathElement",
    "Severity",
    "ShellFeature",
    "Sketch",
    "SketchConstraint",
    "SketchEntity",
    "SphereSurface",
    "SplineGeometry",
    "SupportPlane",
    "SpaceVector",
    "TopologySummary",
    "TorusSurface",
    "Transform",
    "UnitSystem",
    "ValueKind",
    "Vector2",
    "Vector3",
    "assembly",
    "brep",
    "document",
    "filter_document",
    "frozen_mapping",
    "geometry",
    "history",
    "infer_capabilities",
    "mesh",
    "register_migration",
    "register_types",
    "retained_capabilities",
    "semantic_metadata",
    "serialization",
    "source_payload_indexes",
    "with_wrapper_metadata",
    "types",
)

BindTypeGlobals(
    (
        AssemblyModule,
        BrepModule,
        DocumentModule,
        GeometryModule,
        HistoryModule,
        MeshModule,
        TypesModule,
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
