# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from importlib import import_module as ImportModule
from inspect import isabstract as IsAbstract
from inspect import isclass as IsClass
from pkgutil import iter_modules as IterModules
from pkgutil import walk_packages as WalkPackages
from types import ModuleType

from .adapter_protocols import CadReaderAdapter
from .adapter_protocols import CadWriterAdapter
from .registry_errors import DiscoveryError


# protocol member checks exclude inherited protocol artifacts while confirming concrete methods
def HasMethods(AdapterData: object, ProtocolType: type[object]) -> bool:
    ProtocolNames = getattr(ProtocolType, "__protocol_attrs__", None)
    if ProtocolNames is None:
        ProtocolNames = {
            NameValue
            for NameValue in vars(ProtocolType)
            if not NameValue.startswith("_")
        }
    MemberNames = (NameValue for NameValue in ProtocolNames if NameValue != "info")
    return all(
        callable(getattr(AdapterData, NameValue, None)) for NameValue in MemberNames
    )


# class filtering prevents abstract imported and protocol declarations from becoming adapters
def GetAdapterType(CandidateData: object, PackageName: str) -> type[object] | None:
    if (
        not IsClass(CandidateData)
        or IsAbstract(CandidateData)
        or getattr(CandidateData, "_is_protocol", False)
        or not (
            CandidateData.__module__ == PackageName
            or CandidateData.__module__.startswith(PackageName + ".")
        )
        or not hasattr(CandidateData, "info")
    ):
        return None
    IsReader = HasMethods(CandidateData, CadReaderAdapter)
    IsWriter = HasMethods(CandidateData, CadWriterAdapter)
    return CandidateData if IsReader or IsWriter else None


# module inspection deduplicates imported symbols while preserving deterministic class ordering
def GetModuleTypes(ModuleData: ModuleType) -> tuple[type[object], ...]:
    AdapterTypes = {
        AdapterType
        for CandidateData in vars(ModuleData).values()
        if (AdapterType := GetAdapterType(CandidateData, ModuleData.__name__))
        is not None
    }
    return tuple(
        sorted(
            AdapterTypes,
            key=GetTypeKey,
        )
    )


# class ordering remains deterministic because module and qualified names are stable
def GetTypeKey(TypeData: type[object]) -> tuple[str, str]:
    return TypeData.__module__, TypeData.__qualname__


# nested package names remain deterministic and exclude private implementation branches
def GetNestedNames(ModuleData: ModuleType) -> tuple[str, ...]:
    try:
        return tuple(
            sorted(
                ItemData.name
                for ItemData in WalkPackages(
                    ModuleData.__path__, ModuleData.__name__ + "."
                )
                if all(
                    not NamePart.startswith("_")
                    for NamePart in ItemData.name[len(ModuleData.__name__) + 1 :].split(
                        "."
                    )
                )
            )
        )
    except Exception as ErrorInfo:
        raise DiscoveryError(
            f"could not inspect format package {ModuleData.__name__}"
        ) from ErrorInfo


# one package group may expose adapter classes from focused nested implementation modules
def GetPackageTypes(ModuleName: str, IsPackage: bool) -> tuple[type[object], ...]:
    try:
        ModuleData = ImportModule(ModuleName)
    except Exception as ErrorInfo:
        raise DiscoveryError(
            f"could not import format package {ModuleName}"
        ) from ErrorInfo
    ModuleValues = [ModuleData]
    if IsPackage:
        ModuleValues.extend(
            ImportModule(NameValue) for NameValue in GetNestedNames(ModuleData)
        )
    AdapterTypes = {
        AdapterType
        for CandidateModule in ModuleValues
        for AdapterType in GetModuleTypes(CandidateModule)
    }
    if not AdapterTypes and IsPackage:
        raise DiscoveryError(f"format package contains no adapter: {ModuleName}")
    return tuple(
        sorted(
            AdapterTypes,
            key=GetTypeKey,
        )
    )


# top level enumeration validates package shape before any adapter instances are constructed
def GetPackageItems(PackageName: str) -> tuple[tuple[str, bool], ...]:
    try:
        PackageData = ImportModule(PackageName)
    except Exception as ErrorInfo:
        raise DiscoveryError(
            f"could not import adapter package {PackageName}"
        ) from ErrorInfo
    PathValues = getattr(PackageData, "__path__", None)
    if PathValues is None:
        raise DiscoveryError(f"adapter package has no path: {PackageName}")
    try:
        PackageItems = tuple(
            sorted(
                (ItemData.name, ItemData.ispkg)
                for ItemData in IterModules(
                    PathValues,
                    PackageData.__name__ + ".",
                )
                if not ItemData.name.rsplit(".", 1)[-1].startswith("_")
            )
        )
    except Exception as ErrorInfo:
        raise DiscoveryError(
            f"could not enumerate adapter package {PackageName}"
        ) from ErrorInfo
    if not PackageItems:
        raise DiscoveryError(f"adapter package is empty: {PackageName}")
    return PackageItems
