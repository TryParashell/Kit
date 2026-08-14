# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from typing import Any as AnyInfo
from OwnerNaming import KFoldRules, GetGroupPath, GetOwnerBase, GetOwnerKey
from ProgramModel import MethodData, ProgramData


# needed to keep reverse engineering responsibilities isolated and maintainable
def SortOwnerKey(OwnerKey: object) -> tuple[str, str]:
    return (type(OwnerKey).__name__, repr(OwnerKey))


# needed to keep reverse engineering responsibilities isolated and maintainable
def SortOwnerItem(OwnerItem: tuple[object, str]) -> tuple[str, str]:
    return SortOwnerKey(OwnerItem[0])


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuildMethods(Programs: tuple[ProgramData, ...]) -> tuple[dict[str, tuple[tuple[object, str], ...]], dict[str, tuple[MethodData, ...]]]:
    CatalogMaps: dict[str, dict[object, str]] = {}
    GroupBases: dict[str, set[str]] = {}
    VariantMaps: dict[str, dict[str, dict[str, list[tuple[int, int, object, str, AnyInfo]]]]] = {}
    FoldPaths = {GroupPath for SpareValue, GroupPath in KFoldRules}
    for ProgramItem in Programs:
        GroupStreams: dict[str, dict[str, list[tuple[int, int, object, str, AnyInfo]]]] = {}
        for StreamName, Operations in ProgramItem.Streams:
            for StartPos, FieldWidth, OwnerText, KindName, DefaultValue in Operations:
                GroupPath = GetGroupPath(OwnerText)
                OwnerKey = GetOwnerKey(OwnerText)
                OwnerBase = GetOwnerBase(OwnerText)
                GroupBases.setdefault(GroupPath, set()).add(OwnerBase)
                if len(GroupBases[GroupPath]) > 1 and GroupPath not in FoldPaths:
                    raise ValueError(f'owner path collision at {GroupPath}: {sorted(GroupBases[GroupPath])}')
                OwnerMap = CatalogMaps.setdefault(GroupPath, {})
                PriorOwner = OwnerMap.get(OwnerKey)
                if PriorOwner is not None and PriorOwner != OwnerText:
                    raise ValueError(f'owner site collision at {GroupPath} key {OwnerKey!r}')
                OwnerMap[OwnerKey] = OwnerText
                StreamMap = GroupStreams.setdefault(GroupPath, {})
                StreamMap.setdefault(StreamName, []).append((StartPos, FieldWidth, OwnerKey, KindName, DefaultValue))
        VariantMaps[ProgramItem.VariantPath] = GroupStreams
    Catalogs = {GroupPath: tuple(sorted(OwnerMap.items(), key=SortOwnerItem)) for GroupPath, OwnerMap in sorted(CatalogMaps.items())}
    VariantMethods: dict[str, tuple[MethodData, ...]] = {}
    for VariantPath, GroupStreams in sorted(VariantMaps.items()):
        MethodItems: list[MethodData] = []
        for GroupPath, StreamMap in sorted(GroupStreams.items()):
            StreamOps = tuple(((StreamName, tuple(Operations)) for StreamName, Operations in sorted(StreamMap.items())))
            MethodItems.append(MethodData(GroupPath=GroupPath, OwnerSites=Catalogs[GroupPath], StreamOps=StreamOps))
        VariantMethods[VariantPath] = tuple(MethodItems)
    return (Catalogs, VariantMethods)
