# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.registry.AdapterDiscovery import HasMethods
from convert.adapters.base.AdapterMetadata import ValidateInfo
from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.registry.RegistryBinding import AdapterBinding
from convert.adapters.registry.RegistryState import BindReaderMut
from convert.adapters.registry.RegistryState import BindWriterMut
from convert.adapters.registry.RegistryState import CopyState


# compatibility keywords stay centralized because historical registration calls use replace
def IsReplaceFlag(
    NamedValues: dict[str, object],
    CallName: str,
) -> bool:
    AllowedNames = {"replace", "ReplaceFlag"}
    UnknownNames = tuple(
        NameText for NameText in NamedValues if NameText not in AllowedNames
    )
    if UnknownNames:
        raise TypeError(
            f"{CallName}() got an unexpected keyword argument {UnknownNames[0]!r}"
        )
    if "replace" in NamedValues and "ReplaceFlag" in NamedValues:
        raise TypeError(f"{CallName}() got multiple values for 'replace'")
    ReplaceFlag = NamedValues.get("replace", NamedValues.get("ReplaceFlag", False))
    if not isinstance(ReplaceFlag, bool):
        raise TypeError("replace must be a boolean")
    return ReplaceFlag


# protocol classification requires concrete methods because runtime protocols accept data attributes
def GetAdapterKinds(AdapterData: object) -> tuple[bool, bool]:
    IsReader = isinstance(AdapterData, CadReaderAdapter) and HasMethods(
        AdapterData, CadReaderAdapter
    )
    IsWriter = isinstance(AdapterData, CadWriterAdapter) and HasMethods(
        AdapterData, CadWriterAdapter
    )
    return IsReader, IsWriter


# paired registration mutates both maps transactionally so partial adapters never remain visible
def RegisterPairMut(
    BindingMap: dict[str, AdapterBinding],
    AliasMap: dict[str, str],
    AdapterData: object,
    ReplaceFlag: bool,
) -> None:
    PriorState = CopyState(BindingMap, AliasMap)
    IsReader, IsWriter = GetAdapterKinds(AdapterData)
    IsCoordinated = IsReader and IsWriter and ReplaceFlag
    try:
        InfoData = ValidateInfo(AdapterData)
        if IsReader:
            BindReaderMut(
                AdapterData,
                InfoData,
                BindingMap,
                AliasMap,
                ReplaceFlag,
                IsCoordinated,
            )
        if IsWriter:
            BindWriterMut(
                AdapterData,
                InfoData,
                BindingMap,
                AliasMap,
                ReplaceFlag,
                IsCoordinated,
            )
        if not IsReader and not IsWriter:
            raise TypeError("adapter implements neither reader nor writer protocol")
    except Exception:
        BindingMap.clear()
        BindingMap.update(PriorState[0])
        AliasMap.clear()
        AliasMap.update(PriorState[1])
        raise


# focused public bindings keep reader and writer registration independently reviewable
class BindingApi:

    # reader registration validates metadata before mutating the shared format namespace
    def RegisterReader(
        SelfValue,
        AdapterData: CadReaderAdapter,
        **NamedValues: object,
    ) -> None:
        ReplaceFlag = IsReplaceFlag(NamedValues, "register_reader")
        BindReaderMut(
            AdapterData,
            ValidateInfo(AdapterData),
            SelfValue.BindingMap,
            SelfValue.AliasMap,
            ReplaceFlag,
            False,
        )

    # writer registration validates metadata before mutating the shared format namespace
    def RegisterWriter(
        SelfValue,
        AdapterData: CadWriterAdapter,
        **NamedValues: object,
    ) -> None:
        ReplaceFlag = IsReplaceFlag(NamedValues, "register_writer")
        BindWriterMut(
            AdapterData,
            ValidateInfo(AdapterData),
            SelfValue.BindingMap,
            SelfValue.AliasMap,
            ReplaceFlag,
            False,
        )


# dual protocol registration owns transaction coordination without growing the registry facade
class RegisterApi:

    # one adapter may fill either or both registry roles with atomic rollback
    def RegisterOne(
        SelfValue,
        AdapterData: object,
        **NamedValues: object,
    ) -> None:
        RegisterPairMut(
            SelfValue.BindingMap,
            SelfValue.AliasMap,
            AdapterData,
            IsReplaceFlag(NamedValues, "register"),
        )
