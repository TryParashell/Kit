# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from dataclasses import Field as DataFieldInfo
from dataclasses import field as MakeDataField
from typing import ClassVar
from typing import Callable as ValueFactory
from typing import cast as CastValue
from typing import Mapping as TypeMap
from typing import overload as TypeOverload
from typing import TypeVar

from interchange.core.Reflection import GetFieldMap
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.Wire import GetModelField, GetSlotNames, ResolveField


# model decorators preserve each concrete class identity through dataclass transformation
ModelValue = TypeVar("ModelValue")


# wire lookup requires validated dataclass metadata before accepting dynamic model classes
def GetRecordType(ClassType: type[object]) -> type[DataRecord]:
    GetFieldMap(ClassType)
    return CastValue(type[DataRecord], ClassType)


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
    def __call__(
        self: type[ModelValue],
        *ArgValues: object,
        **NamedValues: object,
    ) -> ModelValue:
        ClassType = CastValue(type[object], self)
        RecordType = GetRecordType(ClassType)
        TranslatedValues: dict[str, object] = {}
        for FieldName, FieldValue in NamedValues.items():
            ModelName = ResolveField(RecordType, FieldName)
            if ModelName in TranslatedValues:
                if FieldName == ModelName:
                    TranslatedValues[ModelName] = FieldValue
                    continue
                if ModelName in NamedValues:
                    continue
                raise TypeError(f"duplicate model field {ModelName!r}")
            TranslatedValues[ModelName] = FieldValue
        ResultValue: object = super().__call__(*ArgValues, **TranslatedValues)
        return CastValue(ModelValue, ResultValue)

    # implementation names remain available after historical reflection identity is restored
    def __canonical_name__(self) -> str:
        CanonicalName: object = type.__getattribute__(self, "__dict__").get(
            "__canonical_name__"
        )
        return CanonicalName if isinstance(CanonicalName, str) else self.__name__

    # old class method spellings remain available without declaring noncompliant identifiers
    def __getattr__(self, FieldName: str) -> object:
        ClassType = CastValue(type[object], self)
        RawFields: object = type.__getattribute__(self, "__dict__").get(
            "__dataclass_fields__",
            {},
        )
        FieldNames: dict[object, object] = (
            CastValue(dict[object, object], RawFields)
            if isinstance(RawFields, dict)
            else {}
        )
        if FieldNames:
            ResolvedName = ResolveField(GetRecordType(ClassType), FieldName)
            ModelName = (
                ResolvedName
                if ResolvedName in FieldNames
                else KMethodAliases.get(FieldName, GetModelField(FieldName))
            )
        else:
            ModelName = KMethodAliases.get(FieldName, GetModelField(FieldName))
        ResultValue: object = type.__getattribute__(self, ModelName)
        return ResultValue


# shared alias behavior keeps compatibility logic out of every immutable model record
class ModelBase(metaclass=ModelMeta):
    locals()["__slots__"] = ()
    __dataclass_fields__: ClassVar[dict[str, DataFieldInfo[object]]]

    # undecorated model bases reject construction while transformed subclasses replace this initializer
    def __init__(self, *ArgValues: object, **NamedValues: object) -> None:
        raise TypeError(f"{type(self).__name__} must be transformed into a dataclass")

    # old attribute spellings remain readable while stored field names follow steering
    def __getattr__(self, FieldName: str) -> object:
        ClassType = type(self)
        ResolvedName = ResolveField(GetRecordType(ClassType), FieldName)
        SlotNames = GetSlotNames(ClassType)
        ModelName = (
            ResolvedName
            if ResolvedName in SlotNames
            else KMethodAliases.get(FieldName, ResolvedName)
        )
        ResultValue: object = object.__getattribute__(self, ModelName)
        return ResultValue


# direct decoration retains concrete model types when no configuration wrapper is needed
@TypeOverload
def ModelDataMut(
    ClassType: type[ModelValue],
    *,
    DefaultMap: TypeMap[str, object] | None = None,
    FactoryMap: TypeMap[str, ValueFactory[[], object]] | None = None,
    KeywordOnly: frozenset[str] = frozenset(),
) -> type[ModelValue]: ...


# configured decoration retains concrete model types after defaults are installed
@TypeOverload
def ModelDataMut(
    ClassType: None = None,
    *,
    DefaultMap: TypeMap[str, object] | None = None,
    FactoryMap: TypeMap[str, ValueFactory[[], object]] | None = None,
    KeywordOnly: frozenset[str] = frozenset(),
) -> ValueFactory[[type[ModelValue]], type[ModelValue]]: ...


# dynamic defaults keep instance fields distinct from true class constants during static checks
def ModelDataMut(
    ClassType: type[object] | None = None,
    *,
    DefaultMap: TypeMap[str, object] | None = None,
    FactoryMap: TypeMap[str, ValueFactory[[], object]] | None = None,
    KeywordOnly: frozenset[str] = frozenset(),
) -> object:

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
        RawType = CastValue(
            object,
            MakeDataClass(frozen=True, slots=True)(TargetType),
        )
        if not isinstance(RawType, type):
            raise TypeError("dataclass transformation did not return a type")
        return RawType

    if ClassType is None:
        return ApplyModelMut
    return ApplyModelMut(ClassType)
