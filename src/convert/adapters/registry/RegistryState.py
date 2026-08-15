# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.registry.RegistryBinding import AdapterBinding
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.base.WritePolicy import GetFormatKey


# state snapshots support transactional registration across reader writer and bulk operations
def CopyState(
    BindingMap: dict[str, AdapterBinding],
    AliasMap: dict[str, str],
) -> tuple[dict[str, AdapterBinding], dict[str, str]]:
    return (
        {
            NameValue: AdapterBinding(
                BindingData.ReaderData,
                BindingData.WriterData,
            )
            for NameValue, BindingData in BindingMap.items()
        },
        dict(AliasMap),
    )


# namespace validation prevents format ids and aliases from changing owners silently
def CheckNamespace(
    InfoData: AdapterInfo,
    BindingMap: dict[str, AdapterBinding],
    AliasMap: dict[str, str],
) -> None:
    FormatKey = GetFormatKey(InfoData.FormatId)
    OwnerKey = AliasMap.get(FormatKey)
    if OwnerKey is not None:
        raise RegistryError(
            f"format id is already an alias for {OwnerKey}: {InfoData.FormatId}"
        )
    for AliasName in InfoData.AliasNames:
        AliasKey = GetFormatKey(AliasName)
        if AliasKey in BindingMap:
            raise RegistryError(f"adapter alias is already a format id: {AliasName}")
        ExistingKey = AliasMap.get(AliasKey)
        if ExistingKey is not None and ExistingKey != FormatKey:
            raise RegistryError(f"adapter alias already registered: {AliasName}")


# alias replacement removes stale names while retaining names owned by the current format
def BindAliasesMut(
    InfoData: AdapterInfo,
    AliasMap: dict[str, str],
    ReplaceFlag: bool,
) -> None:
    OwnerKey = GetFormatKey(InfoData.FormatId)
    AliasKeys = {GetFormatKey(AliasName) for AliasName in InfoData.AliasNames}
    if ReplaceFlag:
        StaleNames = tuple(
            AliasName
            for AliasName, ExistingKey in AliasMap.items()
            if ExistingKey == OwnerKey and AliasName not in AliasKeys
        )
        for AliasName in StaleNames:
            del AliasMap[AliasName]
    for AliasName in InfoData.AliasNames:
        AliasMap[GetFormatKey(AliasName)] = OwnerKey


# reader registration enforces metadata agreement with an independently registered writer
def BindReaderMut(
    AdapterData: CadReaderAdapter,
    InfoData: AdapterInfo,
    BindingMap: dict[str, AdapterBinding],
    AliasMap: dict[str, str],
    ReplaceFlag: bool,
    Coordinated: bool,
) -> None:
    CheckNamespace(InfoData, BindingMap, AliasMap)
    FormatKey = GetFormatKey(InfoData.FormatId)
    BindingData = BindingMap.get(FormatKey, AdapterBinding())
    if (
        BindingData.WriterData is not None
        and BindingData.WriterData.info != InfoData
        and not Coordinated
    ):
        raise RegistryError(
            f"reader and writer metadata differ for {InfoData.FormatId}"
        )
    if BindingData.ReaderData is not None and not ReplaceFlag:
        if (
            type(BindingData.ReaderData) is type(AdapterData)
            and BindingData.ReaderData.info == InfoData
        ):
            return
        raise RegistryError(f"reader already registered for {InfoData.FormatId}")
    BindAliasesMut(InfoData, AliasMap, ReplaceFlag)
    BindingMap.setdefault(FormatKey, BindingData)
    BindingData.ReaderData = AdapterData


# writer registration enforces metadata agreement with an independently registered reader
def BindWriterMut(
    AdapterData: CadWriterAdapter,
    InfoData: AdapterInfo,
    BindingMap: dict[str, AdapterBinding],
    AliasMap: dict[str, str],
    ReplaceFlag: bool,
    Coordinated: bool,
) -> None:
    CheckNamespace(InfoData, BindingMap, AliasMap)
    FormatKey = GetFormatKey(InfoData.FormatId)
    BindingData = BindingMap.get(FormatKey, AdapterBinding())
    if (
        BindingData.ReaderData is not None
        and BindingData.ReaderData.info != InfoData
        and not Coordinated
    ):
        raise RegistryError(
            f"reader and writer metadata differ for {InfoData.FormatId}"
        )
    if BindingData.WriterData is not None and not ReplaceFlag:
        if (
            type(BindingData.WriterData) is type(AdapterData)
            and BindingData.WriterData.info == InfoData
        ):
            return
        raise RegistryError(f"writer already registered for {InfoData.FormatId}")
    BindAliasesMut(InfoData, AliasMap, ReplaceFlag)
    BindingMap.setdefault(FormatKey, BindingData)
    BindingData.WriterData = AdapterData
