# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
from pathlib import Path as PathInfo
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / "harness"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Model as Modellib
import Renumber as Renumberlib


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLegacyAttr(SelfRef, NameText):
    AliasName = SelfRef.KAliasNames.get(NameText)
    if AliasName is None:
        raise AttributeError(NameText)
    return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetLegacyMut(SelfRef, NameText, ValueData):
    TargetName = SelfRef.KAliasNames.get(NameText, NameText)
    object.__setattr__(SelfRef, TargetName, ValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
class GrowError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class CountField:
    NodeInfoInfo: int
    BodyOffset: int
    WidthInfo: int

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def ReadData(SelfRef, ModelInfo: Modellib.Model) -> int:
        BodyInfo = ModelInfo.nodes[SelfRef.NodeInfoInfo].body
        return int.from_bytes(
            BodyInfo[SelfRef.BodyOffset : SelfRef.BodyOffset + SelfRef.WidthInfo],
            "little",
        )

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Write(SelfRef, ModelInfo: Modellib.Model, ValueInfo: int) -> None:
        NodeInfoInfo = ModelInfo.nodes[SelfRef.NodeInfoInfo]
        BodyInfo = bytearray(NodeInfoInfo.body)
        if SelfRef.BodyOffset + SelfRef.WidthInfo > len(BodyInfo):
            raise GrowError(f"count field runs past node {SelfRef.NodeInfoInfo}")
        BodyInfo[SelfRef.BodyOffset : SelfRef.BodyOffset + SelfRef.WidthInfo] = (
            ValueInfo.to_bytes(SelfRef.WidthInfo, "little")
        )
        setattr(NodeInfoInfo, "body", bytes(BodyInfo))

    KAliasNames = {
        "node": "NodeInfoInfo",
        "body_offset": "BodyOffset",
        "width": "WidthInfo",
        "read": "ReadData",
        "write": "Write",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
CountField.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def Locate(ModelInfo: Modellib.Model, Absolute: int, WidthInfo: int) -> CountField:
    Offsets = Modellib.NodeOffsets(ModelInfo)
    for PosInfoInfo, NodeInfoInfo in enumerate(ModelInfo.nodes):
        StartRun = Offsets[PosInfoInfo]
        Header = (
            6 + len(NodeInfoInfo.class_name.encode("ascii"))
            if NodeInfoInfo.kind == "definition"
            else 2
        )
        BodyStart = StartRun + Header
        BodyEnd = BodyStart + len(NodeInfoInfo.body)
        if BodyStart <= Absolute and Absolute + WidthInfo <= BodyEnd:
            return CountField(PosInfoInfo, Absolute - BodyStart, WidthInfo)
    raise GrowError(f"offset {Absolute} does not fall inside any node body")


# needed to keep reverse engineering responsibilities isolated and maintainable
def Relocate(
    FieldInfo: CountField, PlanInfo: tuple[tuple[int, int], ...]
) -> CountField:
    for PosInfoInfo, (Source, CopyId) in enumerate(PlanInfo):
        if Source == FieldInfo.node and CopyId == 0:
            return CountField(PosInfoInfo, FieldInfo.body_offset, FieldInfo.width)
    raise GrowError(f"node {FieldInfo.node} vanished from the growth plan")


# needed to keep reverse engineering responsibilities isolated and maintainable
def GrowInfo(
    ModelInfo: Modellib.Model,
    Blocks: tuple[Renumberlib.Block, ...],
    Copies: int,
    Counts: tuple[tuple[CountField, int], ...],
) -> tuple[Modellib.Model, tuple[tuple[int, int], ...]]:
    Grown, PlanInfo = Renumberlib.Duplicate(ModelInfo, Blocks, Copies)
    for FieldInfo, PerFeat in Counts:
        Moved = Relocate(FieldInfo, PlanInfo)
        Moved.write(Grown, FieldInfo.read(ModelInfo) + PerFeat * Copies)
    return (Grown, PlanInfo)
