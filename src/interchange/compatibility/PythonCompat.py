# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from copy import copy as CopyValue
from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig
from inspect import signature as GetSignature
from types import ModuleType
import typing as TypingTypes
from typing import Mapping as TypeMap
from typing import cast as CastValue

from interchange.compatibility.PythonCompatData import KLegacyAnnots, KLegacyModels
from interchange.core.Reflection import (
    DataField,
    GetCanonicalName,
    GetDataFields,
    GetFieldMap,
)
from interchange.serialization.Wire import GetModelField, GetSlotNames, GetWireField


# annotation rendering keeps historical source names independent from compliant implementation hints
def GetLegacyAnnot(FieldValue: DataField) -> str:
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
    FieldType = FieldType.replace("interchange.enums.EnumDocument.", "")
    if FieldValue.name == "EntityKind" and "GeometryKind" in FieldType:
        FieldType = "GeometryKind"
    return FieldType


# copied field metadata lets standard dataclass reflection expose historical names safely
def GetLegacyFields(ClassType: type[object]) -> dict[str, DataField]:
    FieldMap: dict[str, DataField] = {}
    for FieldValue in GetDataFields(ClassType):
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
def GetStoredField(ClassType: type[object], FieldName: str) -> DataField:
    FieldMap = GetFieldMap(ClassType)
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
def GetLegacySig(ClassType: type[object]) -> FuncSig:
    InitSig = GetSignature(ClassType.__init__)
    ParamValues: list[FuncParam] = []
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
def GetModelState(SelfValue: object) -> list[object]:
    ClassType = type(SelfValue)
    return [
        object.__getattribute__(SelfValue, FieldName)
        for FieldName in GetSlotNames(ClassType)
    ]


# canonical slots need direct assignment when historical pickles restore positional state
def SetModelState(SelfValue: object, StateValues: list[object]) -> None:
    ClassType = type(SelfValue)
    for FieldName, FieldValue in zip(GetSlotNames(ClassType), StateValues):
        object.__setattr__(SelfValue, FieldName, FieldValue)


# historical repr keeps default bearing signatures and diagnostics source compatible
def GetModelRepr(SelfValue: object) -> str:
    ClassType = type(SelfValue)
    FieldTexts = (
        f"{GetWireField(FieldName, ClassType)}={getattr(SelfValue, FieldName)!r}"
        for FieldName in GetSlotNames(ClassType)
    )
    return f"{ClassType.__qualname__}({', '.join(FieldTexts)})"


# installed properties preserve historical fields without making every unknown attribute valid
def BindFieldMut(ClassType: type[object], ModelName: str, LegacyName: str) -> None:
    if ModelName == LegacyName:
        return

    # direct slot access avoids recursion while each alias keeps its canonical storage owner
    def GetLegacyValue(SelfValue: object) -> object:
        return object.__getattribute__(SelfValue, ModelName)

    setattr(ClassType, LegacyName, property(GetLegacyValue))


# declared compatibility members need concrete runtime properties before annotations are normalized
def BindTypedFields(ClassType: type[object]) -> None:
    FieldMap = GetFieldMap(ClassType)
    for StoredField in FieldMap.values():
        WireName = GetWireField(StoredField.name, ClassType)
        CompatName = GetModelField(WireName, ClassType)
        BindFieldMut(ClassType, StoredField.name, CompatName)


# one installer synchronizes historical identity signatures annotations and module globals
def BindCompatMut(
    ClassTypes: tuple[type[object], ...],
    ModuleScopes: TypeMap[str, dict[str, object]],
) -> None:
    for ClassType in ClassTypes:
        ModelName = GetCanonicalName(ClassType)
        LegacyName, ModuleName = KLegacyModels[ModelName]
        setattr(ClassType, "__canonical_name__", ModelName)
        BindTypedFields(ClassType)
        LocalFields = GetSlotNames(ClassType)
        LegacyFieldsList = KLegacyAnnots.get(
            ModelName,
            tuple(GetWireField(FieldName, ClassType) for FieldName in LocalFields),
        )
        LegacyAnnots = {
            LegacyField: GetLegacyAnnot(GetStoredField(ClassType, ModelField))
            for ModelField, LegacyField in zip(LocalFields, LegacyFieldsList)
        }
        for ModelField, LegacyField in zip(LocalFields, LegacyFieldsList):
            BindFieldMut(ClassType, ModelField, LegacyField)
            BindFieldMut(
                ClassType,
                ModelField,
                GetModelField(LegacyField, ClassType),
            )
        setattr(ClassType, "__annotations__", LegacyAnnots)
        MatchArgs = tuple(
            GetWireField(FieldValue.name, ClassType)
            for FieldValue in GetDataFields(ClassType)
            if not FieldValue.kw_only
        )
        setattr(ClassType, "__match_args__", MatchArgs)
        setattr(ClassType, "__signature__", GetLegacySig(ClassType))
        setattr(ClassType, "__getstate__", GetModelState)
        setattr(ClassType, "__setstate__", SetModelState)
        setattr(ClassType, "__repr__", GetModelRepr)
        setattr(ClassType, "__dataclass_fields__", GetLegacyFields(ClassType))
        setattr(ClassType, "__name__", LegacyName)
        setattr(ClassType, "__qualname__", LegacyName)
        setattr(ClassType, "__module__", ModuleName)
        ModuleScopes[ModuleName][LegacyName] = ClassType


# historical annotations need their public type names available in every defining facade
def BindTypeGlobals(
    ModuleScopes: tuple[ModuleType, ...],
    ClassTypes: tuple[type[object], ...],
) -> None:
    SharedValues: dict[str, object] = {
        "Any": TypingTypes.Any,
        "Mapping": TypeMap,
    }
    SharedValues.update({ClassType.__name__: ClassType for ClassType in ClassTypes})
    for ModuleScope in ModuleScopes:
        for ValueName, ValueType in SharedValues.items():
            setattr(ModuleScope, ValueName, ValueType)
