# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from inspect import Parameter as SigParam
from inspect import Signature as CallSignature
from dataclasses import MISSING as MissingValue
from dataclasses import Field as DataField
from typing import Mapping as TypeMap
from typing import TypeGuard
from typing import TypeVar
from typing import cast as CastValue
from convert.adapters.base.FieldAliases import KFieldAliases

# generic construction preserves each dataclass result type through the compatibility metaclass
ContractValue = TypeVar("ContractValue")


# dictionary narrowing supports reflected dataclass state without unknown key or value types
def IsObjectDict(FieldValue: object) -> TypeGuard[dict[object, object]]:
    return isinstance(FieldValue, dict)


# metaclass instances require runtime narrowing before ordinary class reflection APIs accept them
def GetClassType(ClassValue: object) -> type[object]:
    if not isinstance(ClassValue, type):
        raise TypeError("contract metadata requires a class")
    return CastValue(type[object], ClassValue)


# reflected fields need runtime proof before compatibility signatures consume their defaults
def GetDataFields(ClassValue: object) -> tuple[DataField[object], ...]:
    ClassType = GetClassType(ClassValue)
    FieldMap: object = type.__getattribute__(ClassType, "__dataclass_fields__")
    if not IsObjectDict(FieldMap):
        raise TypeError("contract class must expose dataclass fields")
    FieldValues: list[DataField[object]] = []
    for FieldValue in FieldMap.values():
        if not isinstance(FieldValue, DataField):
            raise TypeError("contract field metadata must be a dataclass Field")
        FieldValues.append(CastValue(DataField[object], FieldValue))
    return tuple(FieldValues)


# constructor translation remains separate because compatibility records may choose strict canonical collision handling
def GetCtorValues(
    ClassType: type[object],
    NamedValues: TypeMap[str, object],
) -> dict[str, object]:
    TranslatedValues: dict[str, object] = {}
    PublicValues: dict[str, str] = {}
    IsStrictAliases = ClassType.__name__ == "AdapterInfo"
    for FieldName, FieldValue in NamedValues.items():
        ModelName = KFieldAliases.get(FieldName, FieldName)
        if ModelName in TranslatedValues:
            if not IsStrictAliases and PublicValues[ModelName] != ModelName:
                continue
            raise TypeError(f"got multiple values for field {ModelName!r}")
        TranslatedValues[ModelName] = FieldValue
        PublicValues[ModelName] = FieldName
    return TranslatedValues


# compatibility translation accepts historical constructor keywords without duplicating schema fields
class ContractMeta(type):

    # dataclass constructors retain historical field reflection despite compliant internal storage names
    @property
    def __signature__(self) -> CallSignature:
        ParamValues: list[SigParam] = []
        for FieldData in GetDataFields(self):
            ModelName = KFieldAliases.get(FieldData.name, FieldData.name)
            PublicName = GetLegacyName(ModelName)
            DefaultValue = FieldData.default
            if FieldData.default_factory is not MissingValue:
                DefaultValue = FieldData.default_factory
            elif DefaultValue is MissingValue:
                DefaultValue = SigParam.empty
            ParamValues.append(
                SigParam(
                    PublicName,
                    SigParam.POSITIONAL_OR_KEYWORD,
                    default=DefaultValue,
                    annotation=GetLegacyType(self, ModelName),
                )
            )
        return CallSignature(ParamValues, return_annotation=None)

    # callers can upgrade independently because old keyword names still reach compliant fields
    def __call__(
        self: type[ContractValue],
        *ArgValues: object,
        **NamedValues: object,
    ) -> ContractValue:
        TranslatedValues = GetCtorValues(self, NamedValues)
        FieldNames = tuple(FieldData.name for FieldData in GetDataFields(self))
        for ModelName in FieldNames[: len(ArgValues)]:
            if ModelName in TranslatedValues:
                PublicName = GetLegacyName(ModelName)
                raise TypeError(
                    f"{self.__name__}() got multiple values for argument "
                    f"{PublicName!r}"
                )
        ResultValue = type.__call__(self, *ArgValues, **TranslatedValues)
        return CastValue(ContractValue, ResultValue)

    # class level legacy fields keep introspection and descriptor access compatible for external adapters
    def __getattr__(self, FieldName: str) -> object:
        ModelName = KFieldAliases.get(FieldName, FieldName)
        ResultValue: object = type.__getattribute__(self, ModelName)
        return ResultValue


# historical reflection chooses the public field spelling for each compliant storage name
def GetLegacyName(ModelName: str) -> str:
    return next(
        (
            FieldName
            for FieldName, FieldModel in KFieldAliases.items()
            if FieldModel == ModelName
        ),
        ModelName,
    )


# historical annotations remain readable because third party adapters may inspect constructor contracts
def GetLegacyType(ClassValue: object, ModelName: str) -> object:
    ClassType = GetClassType(ClassValue)
    AnnotationValue: object = type.__getattribute__(ClassType, "__annotations__")
    if not IsObjectDict(AnnotationValue):
        return SigParam.empty
    AnnotationMap = CastValue(dict[str, object], AnnotationValue)
    return AnnotationMap.get(
        ModelName,
        AnnotationMap.get(GetLegacyName(ModelName), SigParam.empty),
    )


# shared alias behavior keeps legacy attributes out of every focused contract record
class ContractBase(metaclass=ContractMeta):
    locals()["__slots__"] = ()

    # old attribute spellings remain available because wire and api behavior cannot drift
    def __getattr__(self, FieldName: str) -> object:
        ModelName = KFieldAliases.get(FieldName, FieldName)
        ResultValue: object = object.__getattribute__(self, ModelName)
        return ResultValue
