# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from .adapter_discovery import GetPackageItems
from .adapter_discovery import GetPackageTypes
from .adapter_discovery import HasMethods
from .adapter_info import AdapterInfo
from .adapter_protocols import CadReaderAdapter
from .adapter_protocols import CadWriterAdapter
from .registry_errors import DiscoveryError


# construction failures retain exact class identity so package authors can diagnose discovery
def BuildAdapter(AdapterType: type[object]) -> object:
    try:
        AdapterData = AdapterType()
    except Exception as ErrorInfo:
        raise DiscoveryError(
            f"could not construct adapter {AdapterType.__module__}.{AdapterType.__qualname__}"
        ) from ErrorInfo
    IsReader = isinstance(AdapterData, CadReaderAdapter) and HasMethods(
        AdapterData, CadReaderAdapter
    )
    IsWriter = isinstance(AdapterData, CadWriterAdapter) and HasMethods(
        AdapterData, CadWriterAdapter
    )
    if not IsReader and not IsWriter:
        raise DiscoveryError(
            f"invalid adapter {AdapterType.__module__}.{AdapterType.__qualname__}"
        )
    InfoData = AdapterData.info
    if not isinstance(InfoData, AdapterInfo) or not InfoData.FormatId:
        raise DiscoveryError(
            f"invalid adapter metadata {AdapterType.__module__}.{AdapterType.__qualname__}"
        )
    return AdapterData


# package discovery deduplicates shared classes while preserving deterministic construction order
def FindAdapters(PackageName: str) -> tuple[object, ...]:
    InstanceList: list[object] = []
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
