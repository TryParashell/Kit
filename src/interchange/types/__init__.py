# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.core.Common import FreezeMapping, KJsonScalar, KJsonValue
from interchange.enums.EnumDocument import Capability, Severity
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumGeometry import ConstraintKind, GeometryKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.records.RecordConfig import Configuration, ParamOverride
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordParameter import Expression, Parameter, ParameterValue
from interchange.records.RecordProvenance import Provenance, ProvenanceSpan
from interchange.records.RecordSource import CadSource
from interchange.records.RecordTopology import TopologyCounts
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.compatibility.PublicMetadata import (
    BindFunctionMut,
    BindModules,
    BindNameMut,
)
from interchange.geometry.models.Vectors import (
    BoundingBox,
    PlaneVector,
    SpaceVector,
    Transform,
)
from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig

BindNameMut(BooleanOp, __name__, "BooleanOperation", globals())
BindModules(
    (
        Capability,
        ConstraintKind,
        FeatureKind,
        GeometryKind,
        ParameterRole,
        Severity,
        UnitSystem,
        ValueKind,
    ),
    __name__,
)

BindCompatMut(
    (
        PlaneVector,
        SpaceVector,
        Transform,
        BoundingBox,
        ProvenanceSpan,
        Provenance,
        ParameterValue,
        Expression,
        Parameter,
        ParamOverride,
        Configuration,
        CadSource,
        Diagnostic,
    ),
    {__name__: globals()},
)

JsonScalar = KJsonScalar
JsonValue = KJsonValue
BooleanOperation = BooleanOp
ParameterOverride = ParamOverride
TopologySummary = TopologyCounts
Vector2 = PlaneVector
Vector3 = SpaceVector
frozen_mapping = FreezeMapping

BindFunctionMut(
    FreezeMapping,
    __name__,
    "frozen_mapping",
    {
        "value": "Mapping[str, Any] | None",
        "return": "Mapping[str, Any]",
    },
    FuncSig(
        (
            FuncParam(
                "value",
                FuncParam.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation="Mapping[str, Any] | None",
            ),
        ),
        return_annotation="Mapping[str, Any]",
    ),
    globals(),
)

# legacy module exports stay explicit so integrations cannot depend on implementation details
__all__ = (
    "BooleanOperation",
    "BoundingBox",
    "CadSource",
    "Capability",
    "Configuration",
    "ConstraintKind",
    "Diagnostic",
    "Expression",
    "FeatureKind",
    "GeometryKind",
    "JsonScalar",
    "JsonValue",
    "Parameter",
    "ParameterOverride",
    "ParameterRole",
    "ParameterValue",
    "Provenance",
    "ProvenanceSpan",
    "Severity",
    "Transform",
    "UnitSystem",
    "ValueKind",
    "Vector2",
    "Vector3",
    "frozen_mapping",
)
