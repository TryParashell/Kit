# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from copy import copy as CopyValue
from dataclasses import fields as GetFields
from inspect import signature as GetSignature
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.compatibility.PythonCompatData import KLegacyAnnots, KLegacyModels
from interchange.serialization.Wire import GetSlotNames, GetWireField


# annotation rendering keeps historical source names independent from compliant implementation hints
def GetLegacyAnnot(FieldValue: AnyValue) -> AnyValue:
    FieldType = FieldValue.type
    if isinstance(FieldType, type):
        FieldType = FieldType.__name__
    if not isinstance(FieldType, str):
        FieldType = str(FieldType).replace("typing.", "")
        if FieldType.startswith("<class '") and FieldType.endswith("'>"):
            FieldType = FieldType[8:-2].rsplit(".", 1)[-1]
    AliasNames = {
        "AnyValue": "Any",
        "BooleanOp": "BooleanOperation",
        "ComponentDef": "ComponentDefinition",
        "ComponentDoc": "ComponentDocument",
        "ComponentInst": "ComponentInstance",
        "ConstraintRef": "ConstraintReference",
        "DesignBody": "Body",
        "ExtrudeEnd": "ExtrusionEndCondition",
        "FeatureCfgState": "FeatureConfigurationState",
        "FeatureDef": "FeatureDefinition",
        "IntersectCurve": "IntersectionCurve",
        "ParamOverride": "ParameterOverride",
        "PlaneVector": "Vector2",
        "SelectPathElem": "SelectionPathElement",
        "SketchRelation": "SketchConstraint",
        "SpaceVector": "Vector3",
        "SurfaceMesh": "Mesh",
        "TopologyCounts": "TopologySummary",
        "TransformMatrix": "Matrix4",
        "TypeMap": "Mapping",
        "KGeometryTypes": "Geometry",
    }
    for ModelName, LegacyName in AliasNames.items():
        FieldType = FieldType.replace(ModelName, LegacyName)
    FieldType = FieldType.replace("interchange.enum_document.", "")
    if FieldValue.name == "EntityKind" and "GeometryKind" in FieldType:
        FieldType = "GeometryKind"
    return FieldType


# copied field metadata lets standard dataclass reflection expose historical names safely
def GetLegacyFields(ClassType: type) -> dict[str, AnyValue]:
    FieldMap: dict[str, AnyValue] = {}
    for FieldValue in GetFields(ClassType):
        LegacyName = GetWireField(FieldValue.name, ClassType)
        LegacyField = CopyValue(FieldValue)
        setattr(LegacyField, "name", LegacyName)
        setattr(
            LegacyField,
            "type",
            ClassType.__annotations__.get(
                LegacyName,
                GetLegacyAnnot(FieldValue),
            ),
        )
        FieldMap[LegacyName] = LegacyField
    return FieldMap


# reflected and canonical field maps both need one storage name lookup path
def GetStoredField(ClassType: type, FieldName: str) -> AnyValue:
    FieldMap = ClassType.__dataclass_fields__
    FieldValue = FieldMap.get(FieldName)
    if FieldValue is not None:
        return FieldValue
    LegacyName = GetWireField(FieldName, ClassType)
    FieldValue = FieldMap.get(LegacyName)
    if FieldValue is not None:
        return FieldValue
    for Candidate in FieldMap.values():
        if GetWireField(Candidate.name, ClassType) == FieldName:
            return Candidate
    raise KeyError(FieldName)


# historical signatures preserve normal inspect behavior despite keyword translation metaclasses
def GetLegacySig(ClassType: type) -> AnyValue:
    InitSig = GetSignature(ClassType.__init__)
    ParamValues = []
    for ParamValue in tuple(InitSig.parameters.values())[1:]:
        LegacyName = GetWireField(ParamValue.name, ClassType)
        FieldValue = GetStoredField(ClassType, ParamValue.name)
        ParamValues.append(
            ParamValue.replace(
                name=LegacyName,
                annotation=GetLegacyAnnot(FieldValue),
            )
        )
    return InitSig.replace(parameters=ParamValues)


# canonical pickle state must remain independent from reflected historical dataclass fields
def GetModelState(SelfValue: AnyValue) -> list[AnyValue]:
    ClassType = type(SelfValue)
    return [
        object.__getattribute__(SelfValue, FieldName)
        for FieldName in GetSlotNames(ClassType)
    ]


# canonical slots need direct assignment when historical pickles restore positional state
def SetModelState(SelfValue: AnyValue, StateValues: list[AnyValue]) -> None:
    ClassType = type(SelfValue)
    for FieldName, FieldValue in zip(GetSlotNames(ClassType), StateValues):
        object.__setattr__(SelfValue, FieldName, FieldValue)


# historical repr keeps default bearing signatures and diagnostics source compatible
def GetModelRepr(SelfValue: AnyValue) -> str:
    ClassType = type(SelfValue)
    FieldTexts = (
        f"{GetWireField(FieldName, ClassType)}={getattr(SelfValue, FieldName)!r}"
        for FieldName in GetSlotNames(ClassType)
    )
    return f"{ClassType.__qualname__}({', '.join(FieldTexts)})"


# one installer synchronizes historical identity signatures annotations and module globals
def BindCompatMut(
    ClassTypes: tuple[type, ...],
    ModuleScopes: TypeMap[str, dict[str, AnyValue]],
) -> None:
    for ClassType in ClassTypes:
        CanonicalValue = ClassType.__dict__.get("__canonical_name__")
        ModelName = (
            CanonicalValue if isinstance(CanonicalValue, str) else ClassType.__name__
        )
        LegacyName, ModuleName = KLegacyModels[ModelName]
        ClassType.__canonical_name__ = ModelName
        LocalFields = tuple(ClassType.__slots__)
        LegacyFieldsList = KLegacyAnnots.get(
            ModelName,
            tuple(GetWireField(FieldName, ClassType) for FieldName in LocalFields),
        )
        ClassType.__annotations__ = {
            LegacyField: GetLegacyAnnot(GetStoredField(ClassType, ModelField))
            for ModelField, LegacyField in zip(LocalFields, LegacyFieldsList)
        }
        ClassType.__match_args__ = tuple(
            GetWireField(FieldValue.name, ClassType)
            for FieldValue in GetFields(ClassType)
            if not FieldValue.kw_only
        )
        ClassType.__signature__ = GetLegacySig(ClassType)
        ClassType.__getstate__ = GetModelState
        ClassType.__setstate__ = SetModelState
        ClassType.__repr__ = GetModelRepr
        ClassType.__dataclass_fields__ = GetLegacyFields(ClassType)
        ClassType.__name__ = LegacyName
        ClassType.__qualname__ = LegacyName
        ClassType.__module__ = ModuleName
        ModuleScopes[ModuleName][LegacyName] = ClassType


# historical annotations need their public type names available in every defining facade
def BindTypeGlobals(
    ModuleScopes: tuple[dict[str, AnyValue], ...],
    ClassTypes: tuple[type, ...],
) -> None:
    SharedValues: dict[str, AnyValue] = {
        "Any": AnyValue,
        "Mapping": TypeMap,
    }
    SharedValues.update({ClassType.__name__: ClassType for ClassType in ClassTypes})
    for ModuleScope in ModuleScopes:
        ModuleScope.update(SharedValues)
