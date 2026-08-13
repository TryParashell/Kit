# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeDataField
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .wire import GetModelField, GetSlotNames, ResolveField


# historical method names remain reachable so identifier cleanup does not break existing callers
KMethodAliases: TypeMap[str, str] = {
    "assert_valid": "AssertValid",
    "children": "GetChildren",
    "Definition": "GetDefinition",
    "definition": "GetDefinition",
    "Document": "GetDocument",
    "document": "GetDocument",
    "feature": "GetFeature",
    "from_dict": "FromMapping",
    "from_json": "FromJson",
    "is_finite": "IsFinite",
    "parameter": "GetParameter",
    "plane": "GetPlane",
    "read_json": "ReadJson",
    "rows": "GetRows",
    "sketch": "GetSketch",
    "supports": "HasCapability",
    "to_dict": "ToMapping",
    "to_json": "ToJson",
    "transform_point": "TransformPoint",
    "validate": "GetErrors",
    "write_json": "WriteJson",
}


# model construction translates historical keywords so compliant fields retain source compatibility
class ModelMeta(type):

    # old constructor keywords remain accepted because adapters may upgrade independently
    def __call__(ClassType, *ArgValues: AnyValue, **NamedValues: AnyValue) -> AnyValue:
        TranslatedValues: dict[str, AnyValue] = {}
        for FieldName, FieldValue in NamedValues.items():
            ModelName = ResolveField(ClassType, FieldName)
            if ModelName in TranslatedValues:
                if FieldName == ModelName:
                    TranslatedValues[ModelName] = FieldValue
                    continue
                if ModelName in NamedValues:
                    continue
                raise TypeError(f"duplicate model field {ModelName!r}")
            TranslatedValues[ModelName] = FieldValue
        return super().__call__(*ArgValues, **TranslatedValues)

    # implementation names remain available after historical reflection identity is restored
    def __canonical_name__(ClassType) -> str:
        CanonicalName = type.__getattribute__(ClassType, "__dict__").get(
            "__canonical_name__"
        )
        return CanonicalName if isinstance(CanonicalName, str) else ClassType.__name__

    # old class method spellings remain available without declaring noncompliant identifiers
    def __getattr__(ClassType, FieldName: str) -> AnyValue:
        FieldNames = type.__getattribute__(ClassType, "__dict__").get(
            "__dataclass_fields__",
            {},
        )
        ResolvedName = ResolveField(ClassType, FieldName) if FieldNames else None
        ModelName = (
            ResolvedName
            if ResolvedName in FieldNames
            else KMethodAliases.get(FieldName, GetModelField(FieldName))
        )
        return type.__getattribute__(ClassType, ModelName)


# shared alias behavior keeps compatibility logic out of every immutable model record
class ModelBase(metaclass=ModelMeta):
    locals()["__slots__"] = ()

    # old attribute spellings remain readable while stored field names follow steering
    def __getattr__(SelfValue, FieldName: str) -> AnyValue:
        ClassType = type(SelfValue)
        ResolvedName = ResolveField(ClassType, FieldName)
        SlotNames = GetSlotNames(ClassType)
        ModelName = (
            ResolvedName
            if ResolvedName in SlotNames
            else KMethodAliases.get(FieldName, ResolvedName)
        )
        return object.__getattribute__(SelfValue, ModelName)


# dynamic defaults keep instance fields distinct from true class constants during static checks
def ModelDataMut(
    ClassType: type | None = None,
    *,
    DefaultMap: TypeMap[str, AnyValue] | None = None,
    FactoryMap: TypeMap[str, AnyValue] | None = None,
    KeywordOnly: frozenset[str] = frozenset(),
) -> AnyValue:

    # class mutation is isolated here because dataclasses require defaults before transformation
    def ApplyModelMut(TargetType: type) -> type:
        for FieldName, DefaultValue in (DefaultMap or {}).items():
            FieldInfo = MakeDataField(
                default=DefaultValue,
                kw_only=FieldName in KeywordOnly,
            )
            setattr(TargetType, FieldName, FieldInfo)
        for FieldName, FactoryValue in (FactoryMap or {}).items():
            FieldInfo = MakeDataField(
                default_factory=FactoryValue,
                kw_only=FieldName in KeywordOnly,
            )
            setattr(TargetType, FieldName, FieldInfo)
        return MakeDataClass(frozen=True, slots=True)(TargetType)

    if ClassType is None:
        return ApplyModelMut
    return ApplyModelMut(ClassType)
