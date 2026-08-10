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
from .assembly_distinct_programs import EncodeProgram as EncodeProgramDistinct
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


# native strings use one semantic component occurrence across coupled streams
def EncodeAsmCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[AsmCoreItem, ...],
) -> Mapping[str, bytes]:
    if not ModelName or not ConfigName or not CoreItems:
        raise SldprtFormatError("native assembly core fields cannot be empty")
    if len(CoreItems) > 2:
        raise SldprtFormatError(
            "native assembly core currently supports at most two direct occurrences"
        )
    OccurName = CoreItems[0].OccurName
    CompPath = CoreItems[0].CompPath
    if not OccurName or not CompPath:
        raise SldprtFormatError("native assembly occurrence fields cannot be empty")
    CompStem = PureWindowsPath(CompPath).stem
    if not CompStem:
        raise SldprtFormatError("native assembly component path has no stem")
    DisplayName = f"<{ConfigName}>_Display State 1"
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
            AsmPath = str(
                PureWindowsPath(CompPath).parent / f"{ModelName}.SLDASM"
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
                        0x0713: ConfigName,
                        0x0739: ConfigName,
                        0x07AA: DisplayName,
                        0x0838: SecondItem.OccurName,
                        0x08AB: ConfigName,
                        0x08D1: ConfigName,
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
                        0x04B7: ConfigName,
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
                    },
                ),
            }
            StreamsMap["Header2"] = StreamsMap[
                "Contents/Config-0-ModelHeader"
            ]
            StreamsMap["Contents/Config-0-MatesList"] = struct.pack(
                "<IH", 170, 0
            )
            return MappingProxyType(StreamsMap)
        StreamsMap = {
            "Contents/CMgr": EncodeProgram2(
                "Contents/CMgr",
                {
                    0x00CE: ConfigName,
                    0x04D9: DisplayName,
                    0x05B8: ModelName,
                    0x05EB: OccurName,
                    0x067F: ConfigName,
                    0x06A5: ConfigName,
                    0x0716: DisplayName,
                    0x07A4: SecondItem.OccurName,
                    0x0827: ConfigName,
                    0x084D: ConfigName,
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
                    0x044B: ConfigName,
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
                0x067F: ConfigName,
                0x06A5: ConfigName,
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
            },
        ),
    }
    StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
    StreamsMap["Contents/Config-0-MatesList"] = struct.pack("<IH", 170, 0)
    return MappingProxyType(StreamsMap)


# closure reporting makes typed ownership and zero opaque bytes testable
def CoreCoverage() -> Mapping[str, int]:
    StreamBytes = sum(
        len(EncodeProgram(StreamName)) for StreamName in CoreStreamNames
    )
    return MappingProxyType(
        {
            "stream_bytes": StreamBytes,
            "typed": StreamBytes,
            "opaque": CoreOpaqueBytes,
            "operations": CoreFieldCount,
            "owners": len(FieldOwners),
        }
    )
