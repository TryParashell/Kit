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
from interchange.geometry.models.Vectors import BoundingBox, PlaneVector, SpaceVector, Transform
from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig

BooleanOp.__name__ = "BooleanOperation"
BooleanOp.__qualname__ = "BooleanOperation"
BooleanOp.__module__ = __name__
Capability.__module__ = __name__
ConstraintKind.__module__ = __name__
FeatureKind.__module__ = __name__
GeometryKind.__module__ = __name__
ParameterRole.__module__ = __name__
Severity.__module__ = __name__
UnitSystem.__module__ = __name__
ValueKind.__module__ = __name__

# historical defining module identity preserves direct imports and existing pickle payloads
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

globals().update(
    {
        "BooleanOperation": BooleanOp,
        "JsonScalar": KJsonScalar,
        "JsonValue": KJsonValue,
        "ParameterOverride": ParamOverride,
        "TopologySummary": TopologyCounts,
        "Vector2": PlaneVector,
        "Vector3": SpaceVector,
        "frozen_mapping": FreezeMapping,
    }
)

FreezeMapping.__module__ = __name__
FreezeMapping.__name__ = "frozen_mapping"
FreezeMapping.__qualname__ = "frozen_mapping"
FreezeMapping.__annotations__ = {
    "value": "Mapping[str, Any] | None",
    "return": "Mapping[str, Any]",
}
FreezeMapping.__signature__ = FuncSig(
    (
        FuncParam(
            "value",
            FuncParam.POSITIONAL_OR_KEYWORD,
            default=None,
            annotation="Mapping[str, Any] | None",
        ),
    ),
    return_annotation="Mapping[str, Any]",
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
