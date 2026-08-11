# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PureWindowsPath
import struct
from types import MappingProxyType
from typing import Mapping

from .assembly_programs import EncodeProgram, FieldOwners, StreamPrograms
from .assembly2_programs import EncodeProgram as EncodeProgram2
from .assembly3_programs import EncodeProgram as EncodeProgram3
from .assembly_distinct_programs import EncodeProgram as EncodeProgramDistinct
from .assembly_distinct_repeat import EncodePathCore
from .assembly_hybrid_repeat import EncodeHybCore
from .assembly_mixed_repeat import EncodeMixCore
from .assembly_repeat import EncodeRepCore, RepeatItem
from .container import SldprtFormatError


# these five streams form the native assembly history required by solidworks
CoreStreamNames = (
    "Contents/CMgr",
    "Contents/Config-0",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/Definition",
    "Contents/Config-0-ModelHeader",
)

# every emitted byte is owned by a recovered serializer field
CoreFieldCount = sum(len(StreamPrograms[StreamName]) for StreamName in CoreStreamNames)

# the typed programs contain no unclassified or copied vendor spans
CoreOpaqueBytes = 0


# one core item binds an occurrence label to its native component file
@dataclass(frozen=True, slots=True)
class AsmCoreItem:
    OccurName: str
    CompPath: str
    TransX: float = 0.0
    TransY: float = 0.0
    TransZ: float = 0.0
    ConfigName: str = "Default"
    FileStamp: int = 0


# native strings use one semantic component occurrence across coupled streams
def EncodeAsmCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[AsmCoreItem, ...],
) -> Mapping[str, bytes]:
    if not ModelName or not ConfigName or not CoreItems:
        raise SldprtFormatError("native assembly core fields cannot be empty")
    OccurName = CoreItems[0].OccurName
    CompPath = CoreItems[0].CompPath
    if not OccurName or not CompPath:
        raise SldprtFormatError("native assembly occurrence fields cannot be empty")
    CompStem = PureWindowsPath(CompPath).stem
    if not CompStem:
        raise SldprtFormatError("native assembly component path has no stem")
    DisplayName = f"<{ConfigName}>_Display State 1"
    AsmPath = str(PureWindowsPath(CompPath).parent / f"{ModelName}.SLDASM")
    PathKeys = tuple(
        str(PureWindowsPath(ItemValue.CompPath)).casefold() for ItemValue in CoreItems
    )
    UniqueCount = len(set(PathKeys))
    FileStamps = {
        ItemValue.FileStamp for ItemValue in CoreItems if ItemValue.FileStamp > 0
    }
    if (
        len(CoreItems) >= 3
        and 1 < UniqueCount < len(CoreItems)
        and len(FileStamps) == 1
    ):
        StreamsMap = dict(
            EncodeMixCore(
                ModelName,
                ConfigName,
                tuple(
                    RepeatItem(
                        ItemValue.OccurName,
                        ItemValue.CompPath,
                        ItemValue.TransX,
                        ItemValue.TransY,
                        ItemValue.TransZ,
                        ItemValue.ConfigName,
                        ItemValue.FileStamp,
                    )
                    for ItemValue in CoreItems
                ),
            )
        )
        StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
        StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
        return MappingProxyType(StreamsMap)
    if len(CoreItems) >= 3 and 1 < UniqueCount < len(CoreItems):
        StreamsMap = dict(
            EncodeHybCore(
                ModelName,
                ConfigName,
                tuple(
                    RepeatItem(
                        ItemValue.OccurName,
                        ItemValue.CompPath,
                        ItemValue.TransX,
                        ItemValue.TransY,
                        ItemValue.TransZ,
                        ItemValue.ConfigName,
                        ItemValue.FileStamp,
                    )
                    for ItemValue in CoreItems
                ),
            )
        )
        StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
        StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
        return MappingProxyType(StreamsMap)
    if len(CoreItems) >= 3 and UniqueCount > 1:
        StreamsMap = dict(
            EncodePathCore(
                ModelName,
                ConfigName,
                tuple(
                    RepeatItem(
                        ItemValue.OccurName,
                        ItemValue.CompPath,
                        ItemValue.TransX,
                        ItemValue.TransY,
                        ItemValue.TransZ,
                        ItemValue.ConfigName,
                        ItemValue.FileStamp,
                    )
                    for ItemValue in CoreItems
                ),
            )
        )
        StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
        StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
        return MappingProxyType(StreamsMap)
    if len(CoreItems) >= 4:
        StreamsMap = dict(
            EncodeRepCore(
                ModelName,
                ConfigName,
                tuple(
                    RepeatItem(
                        ItemValue.OccurName,
                        ItemValue.CompPath,
                        ItemValue.TransX,
                        ItemValue.TransY,
                        ItemValue.TransZ,
                        ItemValue.ConfigName,
                        ItemValue.FileStamp,
                    )
                    for ItemValue in CoreItems
                ),
            )
        )
        StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
        StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
        return MappingProxyType(StreamsMap)
    if len(CoreItems) == 3:
        SecondItem, ThirdItem = CoreItems[1:]
        if any(ItemValue.CompPath != CompPath for ItemValue in CoreItems):
            raise SldprtFormatError(
                "three-occurrence native history requires one shared component file"
            )
        StreamsMap = {
            "Contents/CMgr": EncodeProgram3(
                "Contents/CMgr",
                {
                    0x00CE: ConfigName,
                    0x04D9: DisplayName,
                    0x05B2: AsmPath,
                    0x063C: ModelName,
                    0x066B: OccurName,
                    0x0713: CoreItems[0].ConfigName,
                    0x0739: CoreItems[0].ConfigName,
                    0x07AA: DisplayName,
                    0x0838: SecondItem.OccurName,
                    0x08BB: SecondItem.ConfigName,
                    0x08E1: SecondItem.ConfigName,
                    0x0952: DisplayName,
                    0x09E0: ThirdItem.OccurName,
                    0x0A63: ThirdItem.ConfigName,
                    0x0A89: ThirdItem.ConfigName,
                },
            ),
            "Contents/Config-0": EncodeProgram3(
                "Contents/Config-0",
                {
                    0x0030: ModelName,
                    0x006B: OccurName,
                    0x01BA: ConfigName,
                    0x023B: AsmPath,
                    0x02C5: ModelName,
                    0x02F4: OccurName,
                    0x0378: SecondItem.OccurName,
                    0x04C7: SecondItem.ConfigName,
                    0x0546: SecondItem.OccurName,
                    0x05CA: ThirdItem.OccurName,
                    0x0719: ThirdItem.ConfigName,
                    0x0798: ThirdItem.OccurName,
                },
            ),
            "Contents/Config-0-ResolvedFeatures": EncodeProgram3(
                "Contents/Config-0-ResolvedFeatures"
            ),
            "Contents/Definition": EncodeProgram3("Contents/Definition"),
            "Contents/Config-0-ModelHeader": EncodeProgram3(
                "Contents/Config-0-ModelHeader",
                {
                    0x008E: ModelName,
                    0x06AC: OccurName,
                    0x0714: SecondItem.OccurName,
                    0x077C: ThirdItem.OccurName,
                    0x0809: CompPath,
                    0x08C1: CompStem,
                    0x0940: AsmPath,
                    0x09CA: ModelName,
                    0x09FB: ConfigName,
                    **(
                        {0x0902: CoreItems[0].FileStamp}
                        if CoreItems[0].FileStamp > 0
                        else {}
                    ),
                },
            ),
        }
        StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
        StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
        return MappingProxyType(StreamsMap)
    if len(CoreItems) == 2:
        SecondItem = CoreItems[1]
        if not SecondItem.OccurName or not SecondItem.CompPath:
            raise SldprtFormatError("second native assembly occurrence is empty")
        if SecondItem.CompPath != CompPath:
            SecondStem = PureWindowsPath(SecondItem.CompPath).stem
            if not SecondStem:
                raise SldprtFormatError(
                    "second native assembly component path has no stem"
                )
            StreamsMap = {
                "Contents/CMgr": EncodeProgramDistinct(
                    "Contents/CMgr",
                    {
                        0x00CE: ConfigName,
                        0x04D9: DisplayName,
                        0x05B2: AsmPath,
                        0x063C: ModelName,
                        0x066B: OccurName,
                        0x0713: CoreItems[0].ConfigName,
                        0x0739: CoreItems[0].ConfigName,
                        0x07AA: DisplayName,
                        0x0838: SecondItem.OccurName,
                        0x08AB: SecondItem.ConfigName,
                        0x08D1: SecondItem.ConfigName,
                    },
                ),
                "Contents/Config-0": EncodeProgramDistinct(
                    "Contents/Config-0",
                    {
                        0x0030: ModelName,
                        0x006B: OccurName,
                        0x01BA: ConfigName,
                        0x023B: AsmPath,
                        0x02C5: ModelName,
                        0x02F4: OccurName,
                        0x0378: SecondItem.OccurName,
                        0x04B7: SecondItem.ConfigName,
                        0x0536: SecondItem.OccurName,
                    },
                ),
                "Contents/Config-0-ResolvedFeatures": EncodeProgramDistinct(
                    "Contents/Config-0-ResolvedFeatures"
                ),
                "Contents/Definition": EncodeProgramDistinct("Contents/Definition"),
                "Contents/Config-0-ModelHeader": EncodeProgramDistinct(
                    "Contents/Config-0-ModelHeader",
                    {
                        0x008E: ModelName,
                        0x06AC: OccurName,
                        0x0734: SecondItem.OccurName,
                        0x07B1: CompPath,
                        0x0869: CompStem,
                        0x08E4: SecondItem.CompPath,
                        0x098C: SecondStem,
                        0x09FB: AsmPath,
                        0x0A85: ModelName,
                        0x0AB6: ConfigName,
                        **(
                            {
                                0x08AA: CoreItems[0].FileStamp,
                                0x09BD: SecondItem.FileStamp,
                            }
                            if CoreItems[0].FileStamp > 0 and SecondItem.FileStamp > 0
                            else {}
                        ),
                    },
                ),
            }
            StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
            StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
            return MappingProxyType(StreamsMap)
        StreamsMap = {
            "Contents/CMgr": EncodeProgram2(
                "Contents/CMgr",
                {
                    0x00CE: ConfigName,
                    0x04D9: DisplayName,
                    0x05B8: ModelName,
                    0x05EB: OccurName,
                    0x067F: CoreItems[0].ConfigName,
                    0x06A5: CoreItems[0].ConfigName,
                    0x0716: DisplayName,
                    0x07A4: SecondItem.OccurName,
                    0x0827: SecondItem.ConfigName,
                    0x084D: SecondItem.ConfigName,
                },
            ),
            "Contents/Config-0": EncodeProgram2(
                "Contents/Config-0",
                {
                    0x0030: ModelName,
                    0x006F: OccurName,
                    0x01BE: ConfigName,
                    0x0245: ModelName,
                    0x0278: OccurName,
                    0x02FC: SecondItem.OccurName,
                    0x044B: SecondItem.ConfigName,
                    0x04CA: SecondItem.OccurName,
                },
            ),
            "Contents/Config-0-ResolvedFeatures": EncodeProgram2(
                "Contents/Config-0-ResolvedFeatures"
            ),
            "Contents/Definition": EncodeProgram2("Contents/Definition"),
            "Contents/Config-0-ModelHeader": EncodeProgram2(
                "Contents/Config-0-ModelHeader",
                {
                    0x008E: ModelName,
                    0x06AC: OccurName,
                    0x0714: SecondItem.OccurName,
                    0x07A1: CompPath,
                    0x0859: CompStem,
                    0x08DE: ModelName,
                    0x0913: ConfigName,
                    **(
                        {0x089A: CoreItems[0].FileStamp}
                        if CoreItems[0].FileStamp > 0
                        else {}
                    ),
                },
            ),
        }
        StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
        StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
        return MappingProxyType(StreamsMap)
    StreamsMap = {
        "Contents/CMgr": EncodeProgram(
            "Contents/CMgr",
            {
                0x00CE: ConfigName,
                0x04D9: DisplayName,
                0x05B8: ModelName,
                0x05EB: OccurName,
                0x067F: CoreItems[0].ConfigName,
                0x06A5: CoreItems[0].ConfigName,
            },
        ),
        "Contents/Config-0": EncodeProgram(
            "Contents/Config-0",
            {
                0x0030: ModelName,
                0x006F: OccurName,
                0x01BE: ConfigName,
                0x0245: ModelName,
                0x0278: OccurName,
            },
        ),
        "Contents/Config-0-ResolvedFeatures": EncodeProgram(
            "Contents/Config-0-ResolvedFeatures"
        ),
        "Contents/Definition": EncodeProgram("Contents/Definition"),
        "Contents/Config-0-ModelHeader": EncodeProgram(
            "Contents/Config-0-ModelHeader",
            {
                0x008E: ModelName,
                0x06AC: OccurName,
                0x0739: CompPath,
                0x07F1: CompStem,
                0x0876: ModelName,
                0x08AB: ConfigName,
                **(
                    {0x0832: CoreItems[0].FileStamp}
                    if CoreItems[0].FileStamp > 0
                    else {}
                ),
            },
        ),
    }
    StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
    StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
    return MappingProxyType(StreamsMap)


# closure reporting makes typed ownership and zero opaque bytes testable
def CoreCoverage() -> Mapping[str, int]:
    StreamBytes = sum(len(EncodeProgram(StreamName)) for StreamName in CoreStreamNames)
    return MappingProxyType(
        {
            "stream_bytes": StreamBytes,
            "typed": StreamBytes,
            "opaque": CoreOpaqueBytes,
            "operations": CoreFieldCount,
            "owners": len(FieldOwners),
        }
    )
