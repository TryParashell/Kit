# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import fields as DataFields
from typing import Any as AnyValue
from typing import get_args as GetTypeArgs
from typing import get_origin as GetTypeOrigin
from typing import get_type_hints as GetTypeHints

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.FieldAliases import KFieldAliases
from convert.adapters.registry.RegistryErrors import RegistryError


# validation errors preserve public field vocabulary so existing callers can classify failures
def GetPublicField(FieldName: str) -> str:
    return next(
        (
            PublicName
            for PublicName, ModelName in KFieldAliases.items()
            if ModelName == FieldName
        ),
        FieldName,
    )


# field type validation prevents malformed adapter metadata from entering registry state safely
def IsFieldValid(FieldValue: object, HintValue: object) -> bool:
    OriginType = GetTypeOrigin(HintValue)
    TypeArgs = GetTypeArgs(HintValue)
    if HintValue is str:
        return isinstance(FieldValue, str)
    if OriginType is tuple and len(TypeArgs) == 2 and TypeArgs[1] is Ellipsis:
        return isinstance(FieldValue, tuple) and all(
            isinstance(MemberValue, TypeArgs[0]) for MemberValue in FieldValue
        )
    if OriginType is frozenset and len(TypeArgs) == 1:
        return isinstance(FieldValue, frozenset) and all(
            isinstance(MemberValue, TypeArgs[0]) for MemberValue in FieldValue
        )
    raise RegistryError("unsupported adapter field type")


# string tuple validation rejects whitespace and case insensitive duplicates before lookup begins
def CheckTextTuple(FieldName: str, FieldValue: tuple[str, ...]) -> None:
    if any(
        not isinstance(MemberValue, str)
        or not MemberValue.strip()
        or MemberValue != MemberValue.strip()
        for MemberValue in FieldValue
    ):
        raise RegistryError(f"adapter {FieldName} must be a string tuple")
    if len({MemberValue.casefold() for MemberValue in FieldValue}) != len(FieldValue):
        raise RegistryError(f"adapter {FieldName} must be unique")


# metadata field checks stay isolated because schema validation changes independently from namespace rules
def CheckInfoFields(InfoData: AdapterInfo) -> None:
    HintMap = GetTypeHints(AdapterInfo)
    for FieldData in DataFields(InfoData):
        PublicName = GetPublicField(FieldData.name)
        ModelName = KFieldAliases.get(FieldData.name, FieldData.name)
        FieldValue = getattr(InfoData, ModelName)
        HintValue = HintMap[FieldData.name]
        try:
            IsValid = IsFieldValid(FieldValue, HintValue)
        except RegistryError as ErrorInfo:
            raise RegistryError(
                f"unsupported adapter field {PublicName}"
            ) from ErrorInfo
        if not IsValid:
            raise RegistryError(f"adapter {PublicName} has an invalid type")
        if isinstance(FieldValue, str) and (
            not FieldValue.strip() or FieldValue != FieldValue.strip()
        ):
            raise RegistryError(f"adapter {PublicName} must be a non-empty string")
        if isinstance(FieldValue, tuple):
            CheckTextTuple(PublicName, FieldValue)


# extension validation keeps document kind subsets consistent with the advertised format
def CheckExtensions(InfoData: AdapterInfo) -> None:
    ExtensionKeys = {ValueText.casefold() for ValueText in InfoData.Extensions}
    if any(not ValueText.startswith(".") for ValueText in InfoData.Extensions):
        raise RegistryError("adapter extensions must begin with a dot")
    for KindName, ExtensionValues in (
        ("part", InfoData.PartExts),
        ("assembly", InfoData.AssemblyExts),
    ):
        if any(
            ValueText.casefold() not in ExtensionKeys for ValueText in ExtensionValues
        ):
            raise RegistryError(
                f"adapter {KindName} extensions must also be declared extensions"
            )


# complete validation returns the trusted object so registration remains expression friendly
def ValidateInfo(AdapterData: AnyValue) -> AdapterInfo:
    InfoData = AdapterData.info
    if not isinstance(InfoData, AdapterInfo):
        raise RegistryError("adapter info must be AdapterInfo")
    CheckInfoFields(InfoData)
    if InfoData.FormatId.casefold() in {
        AliasName.casefold() for AliasName in InfoData.AliasNames
    }:
        raise RegistryError("adapter alias must differ from its format id")
    CheckExtensions(InfoData)
    if not InfoData.NativeCaps <= InfoData.Capabilities:
        raise RegistryError(
            "adapter native capabilities must also be preservation capabilities"
        )
    return InfoData
