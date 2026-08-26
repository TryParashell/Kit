# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Protocol
from typing import TypeGuard

from interchange import Capability

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.registry.RegistryErrors import RegistryError


# adapter discovery needs an inspectable metadata boundary before trusting plugin values
class InfoSource(Protocol):

    # object output preserves runtime validation for plugins outside static checking
    @property
    def info(self) -> object:
        raise TypeError("adapter metadata requires a concrete implementation")


# tuple narrowing keeps untyped plugin values inspectable without weakening member types
def IsObjectTuple(FieldValue: object) -> TypeGuard[tuple[object, ...]]:
    return isinstance(FieldValue, tuple)


# frozen set narrowing keeps capability validation concrete after plugin boundaries
def IsObjectSet(FieldValue: object) -> TypeGuard[frozenset[object]]:
    return isinstance(FieldValue, frozenset)


# scalar metadata must remain normalized text because registry keys depend on it
def CheckText(FieldName: str, FieldValue: object) -> None:
    if not isinstance(FieldValue, str):
        raise RegistryError(f"adapter {FieldName} has an invalid type")
    if not FieldValue.strip() or FieldValue != FieldValue.strip():
        raise RegistryError(f"adapter {FieldName} must be a non-empty string")


# string tuple validation rejects whitespace and case insensitive duplicates before lookup begins
def CheckTextTuple(FieldName: str, FieldValue: object) -> None:
    if not IsObjectTuple(FieldValue):
        raise RegistryError(f"adapter {FieldName} has an invalid type")
    TextValues: list[str] = []
    for MemberValue in FieldValue:
        if (
            not isinstance(MemberValue, str)
            or not MemberValue.strip()
            or MemberValue != MemberValue.strip()
        ):
            raise RegistryError(f"adapter {FieldName} must be a string tuple")
        TextValues.append(MemberValue)
    if len({MemberValue.casefold() for MemberValue in TextValues}) != len(TextValues):
        raise RegistryError(f"adapter {FieldName} must be unique")


# capability sets stay immutable and enum bounded so selection evidence is trustworthy
def CheckCapSet(FieldName: str, FieldValue: object) -> None:
    if not IsObjectSet(FieldValue) or any(
        not isinstance(MemberValue, Capability) for MemberValue in FieldValue
    ):
        raise RegistryError(f"adapter {FieldName} has an invalid type")


# metadata field checks stay isolated because schema validation changes independently from namespace rules
def CheckInfoFields(InfoData: AdapterInfo) -> None:
    TextFields: tuple[tuple[str, object], ...] = (
        ("format_id", InfoData.FormatId),
        ("name", InfoData.DisplayName),
        ("version", InfoData.VersionText),
    )
    TupleFields: tuple[tuple[str, object], ...] = (
        ("extensions", InfoData.Extensions),
        ("aliases", InfoData.AliasNames),
        ("media_types", InfoData.MediaTypes),
        ("part_extensions", InfoData.PartExts),
        ("assembly_extensions", InfoData.AssemblyExts),
    )
    CapFields: tuple[tuple[str, object], ...] = (
        ("capabilities", InfoData.Capabilities),
        ("native_capabilities", InfoData.NativeCaps),
    )
    for FieldName, FieldValue in TextFields:
        CheckText(FieldName, FieldValue)
    for FieldName, FieldValue in TupleFields:
        CheckTextTuple(FieldName, FieldValue)
    for FieldName, FieldValue in CapFields:
        CheckCapSet(FieldName, FieldValue)


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
def ValidateInfo(AdapterData: InfoSource) -> AdapterInfo:
    InfoValue = AdapterData.info
    if not isinstance(InfoValue, AdapterInfo):
        raise RegistryError("adapter info must be AdapterInfo")
    InfoData = InfoValue
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
