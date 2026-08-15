# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.registry.AdapterDiscovery import GetPackageItems
from convert.adapters.registry.AdapterDiscovery import GetPackageTypes
from convert.adapters.registry.AdapterDiscovery import IsReaderAdapter
from convert.adapters.registry.AdapterDiscovery import IsWriterAdapter
from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.registry.RegistryErrors import DiscoveryError


# discovery trusts metadata only after confirming its concrete contract and identifier
def ValidateAdapterInfo(InfoValue: object) -> AdapterInfo:
    if not isinstance(InfoValue, AdapterInfo) or not InfoValue.FormatId:
        raise DiscoveryError("invalid adapter metadata")
    return InfoValue


# construction failures retain exact class identity so package authors can diagnose discovery
def BuildAdapter(
    AdapterType: type[object],
) -> CadReaderAdapter | CadWriterAdapter:
    try:
        AdapterData = AdapterType()
    except Exception as ErrorInfo:
        raise DiscoveryError(
            f"could not construct adapter {AdapterType.__module__}.{AdapterType.__qualname__}"
        ) from ErrorInfo
    if IsReaderAdapter(AdapterData):
        ValidAdapter: CadReaderAdapter | CadWriterAdapter = AdapterData
    elif IsWriterAdapter(AdapterData):
        ValidAdapter = AdapterData
    else:
        raise DiscoveryError(
            f"invalid adapter {AdapterType.__module__}.{AdapterType.__qualname__}"
        )
    try:
        ValidateAdapterInfo(ValidAdapter.info)
    except DiscoveryError as ErrorInfo:
        raise DiscoveryError(
            f"invalid adapter metadata {AdapterType.__module__}.{AdapterType.__qualname__}"
        ) from ErrorInfo
    return ValidAdapter


# package discovery deduplicates shared classes while preserving deterministic construction order
def FindAdapters(
    PackageName: str,
) -> tuple[CadReaderAdapter | CadWriterAdapter, ...]:
    InstanceList: list[CadReaderAdapter | CadWriterAdapter] = []
    SeenTypes: set[type[object]] = set()
    for ModuleName, IsPackage in GetPackageItems(PackageName):
        try:
            AdapterTypes = GetPackageTypes(ModuleName, IsPackage)
        except DiscoveryError:
            raise
        except Exception as ErrorInfo:
            raise DiscoveryError(
                f"could not inspect format package {ModuleName}"
            ) from ErrorInfo
        for AdapterType in AdapterTypes:
            if AdapterType in SeenTypes:
                continue
            SeenTypes.add(AdapterType)
            InstanceList.append(BuildAdapter(AdapterType))
    return tuple(InstanceList)
