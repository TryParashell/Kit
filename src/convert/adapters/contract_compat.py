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
from dataclasses import fields as DataFields
from typing import Any as AnyValue
from typing import Mapping as TypeMap
from .field_aliases import KFieldAliases


# constructor translation remains separate because compatibility records may choose strict canonical collision handling
def GetCtorValues(
    ClassType: type,
    NamedValues: TypeMap[str, AnyValue],
) -> dict[str, AnyValue]:
    TranslatedValues: dict[str, AnyValue] = {}
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
    def __signature__(ClassType) -> CallSignature:
        ParamValues: list[SigParam] = []
        for FieldData in DataFields(ClassType):
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
                    annotation=GetLegacyType(ClassType, ModelName),
                )
            )
        return CallSignature(ParamValues, return_annotation=None)

    # callers can upgrade independently because old keyword names still reach compliant fields
    def __call__(ClassType, *ArgValues: AnyValue, **NamedValues: AnyValue) -> AnyValue:
        TranslatedValues = GetCtorValues(ClassType, NamedValues)
        FieldNames = tuple(FieldData.name for FieldData in DataFields(ClassType))
        for ArgIndex, ModelName in enumerate(FieldNames[: len(ArgValues)]):
            if ModelName in TranslatedValues:
                PublicName = GetLegacyName(ModelName)
                raise TypeError(
                    f"{ClassType.__name__}() got multiple values for argument "
                    f"{PublicName!r}"
                )
        return super().__call__(*ArgValues, **TranslatedValues)

    # class level legacy fields keep introspection and descriptor access compatible for external adapters
    def __getattr__(ClassType, FieldName: str) -> AnyValue:
        ModelName = KFieldAliases.get(FieldName, FieldName)
        return type.__getattribute__(ClassType, ModelName)


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
def GetLegacyType(ClassType: type, ModelName: str) -> AnyValue:
    AnnotationMap: TypeMap[str, AnyValue] = getattr(ClassType, "__annotations__", {})
    return AnnotationMap.get(
        ModelName,
        AnnotationMap.get(GetLegacyName(ModelName), SigParam.empty),
    )


# shared alias behavior keeps legacy attributes out of every focused contract record
class ContractBase(metaclass=ContractMeta):
    locals()["__slots__"] = ()

    # old attribute spellings remain available because wire and api behavior cannot drift
    def __getattr__(SelfValue, FieldName: str) -> AnyValue:
        ModelName = KFieldAliases.get(FieldName, FieldName)
        return object.__getattribute__(SelfValue, ModelName)
