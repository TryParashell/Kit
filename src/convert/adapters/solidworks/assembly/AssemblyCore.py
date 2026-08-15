# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as DataClass
from pathlib import PureWindowsPath
import struct as Struct
from types import MappingProxyType
from typing import Callable as CallableType, Mapping
from convert.adapters.solidworks.programs.assembly.default.Program import (
    EncodeProgram,
    FieldOwners,
    StreamPrograms,
)
from convert.adapters.solidworks.programs.assembly.pairs.Program import (
    EncodeProgram as EncodeProgramTwo,
)
from convert.adapters.solidworks.programs.assembly.triples.Program import (
    EncodeProgram as EncodeProgramThree,
)
from convert.adapters.solidworks.programs.assembly.distinct.default.Program import (
    EncodeProgram as EncodeProgramDistinct,
)
from convert.adapters.solidworks.programs.assembly.distinct.default.Repeat import (
    EncodePathCore,
)
from convert.adapters.solidworks.programs.assembly.hybrid.quintuples.Repeat import (
    EncodeHybCore,
)
from convert.adapters.solidworks.programs.assembly.mixed.sextuples.Repeat import (
    EncodeMixCore,
)
from convert.adapters.solidworks.programs.assembly.default.Repeat import (
    EncodeRepCore,
    RepeatItem,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

# this binding exists because shared behavior needs one stable value
KCoreStreamNames = (
    "Contents/CMgr",
    "Contents/Config-0",
    "Contents/Config-0-ResolvedFeatures",
    "Contents/Definition",
    "Contents/Config-0-ModelHeader",
)

# this binding exists because shared behavior needs one stable value
KCoreFieldCount = sum(
    (len(StreamPrograms[StreamName]) for StreamName in KCoreStreamNames)
)

# this binding exists because shared behavior needs one stable value
KCoreOpaqueBytes = 0


# this definition exists because focused behavior needs one stable owner
@DataClass(frozen=True, slots=True)
class AsmCoreItem:
    OccurName: str
    CompPath: str
    TransX: float = 0.0
    TransY: float = 0.0
    TransZ: float = 0.0
    ConfigName: str = "Default"
    FileStamp: int = 0
    BasisVals: tuple[float, ...] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


# completed core maps always carry the model header alias and an explicit empty mate lane
def FinishCoreMut(StreamsMap: dict[str, bytes]) -> Mapping[str, bytes]:
    StreamsMap["Header2"] = StreamsMap["Contents/Config-0-ModelHeader"]
    StreamsMap["Contents/Config-0-MatesList"] = Struct.pack("<IH", 170, 0)
    return MappingProxyType(StreamsMap)


# repeated assembly histories share one adapter because only their recovered program family differs
def BuildRepeatCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[AsmCoreItem, ...],
    Encoder: CallableType[[str, str, tuple[RepeatItem, ...]], Mapping[str, bytes]],
) -> Mapping[str, bytes]:
    RepeatItems = tuple(
        (
            RepeatItem(
                ItemValue.OccurName,
                ItemValue.CompPath,
                ItemValue.TransX,
                ItemValue.TransY,
                ItemValue.TransZ,
                ItemValue.ConfigName,
                ItemValue.FileStamp,
                ItemValue.BasisVals,
            )
            for ItemValue in CoreItems
        )
    )
    return FinishCoreMut(dict(Encoder(ModelName, ConfigName, RepeatItems)))


# three occurrence history owns its recovered offsets independently from other cardinalities
def BuildTripleCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[AsmCoreItem, ...],
    DisplayName: str,
    AsmPath: str,
    CompStem: str,
) -> Mapping[str, bytes]:
    OccurName = CoreItems[0].OccurName
    CompPath = CoreItems[0].CompPath
    SecondItem, ThirdItem = CoreItems[1:]
    if any((ItemValue.CompPath != CompPath for ItemValue in CoreItems)):
        raise SldprtFormatError(
            "three-occurrence native history requires one shared component file"
        )
    StreamsMap = {
        "Contents/CMgr": EncodeProgramThree(
            "Contents/CMgr",
            {
                206: ConfigName,
                1241: DisplayName,
                1458: AsmPath,
                1596: ModelName,
                1643: OccurName,
                1811: CoreItems[0].ConfigName,
                1849: CoreItems[0].ConfigName,
                1962: DisplayName,
                2104: SecondItem.OccurName,
                2235: SecondItem.ConfigName,
                2273: SecondItem.ConfigName,
                2386: DisplayName,
                2528: ThirdItem.OccurName,
                2659: ThirdItem.ConfigName,
                2697: ThirdItem.ConfigName,
            },
        ),
        "Contents/Config-0": EncodeProgramThree(
            "Contents/Config-0",
            {
                48: ModelName,
                107: OccurName,
                318: CoreItems[0].TransX,
                326: CoreItems[0].TransY,
                334: CoreItems[0].TransZ,
                442: ConfigName,
                571: AsmPath,
                709: ModelName,
                756: OccurName,
                888: SecondItem.OccurName,
                1099: SecondItem.TransX,
                1107: SecondItem.TransY,
                1115: SecondItem.TransZ,
                1223: SecondItem.ConfigName,
                1350: SecondItem.OccurName,
                1482: ThirdItem.OccurName,
                1693: ThirdItem.TransX,
                1701: ThirdItem.TransY,
                1709: ThirdItem.TransZ,
                1817: ThirdItem.ConfigName,
                1944: ThirdItem.OccurName,
            },
        ),
        "Contents/Config-0-ResolvedFeatures": EncodeProgramThree(
            "Contents/Config-0-ResolvedFeatures"
        ),
        "Contents/Definition": EncodeProgramThree("Contents/Definition"),
        "Contents/Config-0-ModelHeader": EncodeProgramThree(
            "Contents/Config-0-ModelHeader",
            {
                142: ModelName,
                1708: OccurName,
                1812: SecondItem.OccurName,
                1916: ThirdItem.OccurName,
                2057: CompPath,
                2241: CompStem,
                2368: AsmPath,
                2506: ModelName,
                2555: ConfigName,
                **(
                    {2306: CoreItems[0].FileStamp} if CoreItems[0].FileStamp > 0 else {}
                ),
            },
        ),
    }
    return FinishCoreMut(StreamsMap)


# two occurrence history selects shared or distinct component programs without affecting callers
def BuildPairCore(
    ModelName: str,
    ConfigName: str,
    CoreItems: tuple[AsmCoreItem, ...],
    DisplayName: str,
    AsmPath: str,
    CompStem: str,
) -> Mapping[str, bytes]:
    OccurName = CoreItems[0].OccurName
    CompPath = CoreItems[0].CompPath
    SecondItem = CoreItems[1]
    if not SecondItem.OccurName or not SecondItem.CompPath:
        raise SldprtFormatError("second native assembly occurrence is empty")
    if SecondItem.CompPath != CompPath:
        SecondStem = PureWindowsPath(SecondItem.CompPath).stem
        if not SecondStem:
            raise SldprtFormatError("second native assembly component path has no stem")
        StreamsMap = {
            "Contents/CMgr": EncodeProgramDistinct(
                "Contents/CMgr",
                {
                    206: ConfigName,
                    1241: DisplayName,
                    1458: AsmPath,
                    1596: ModelName,
                    1643: OccurName,
                    1811: CoreItems[0].ConfigName,
                    1849: CoreItems[0].ConfigName,
                    1962: DisplayName,
                    2104: SecondItem.OccurName,
                    2219: SecondItem.ConfigName,
                    2257: SecondItem.ConfigName,
                },
            ),
            "Contents/Config-0": EncodeProgramDistinct(
                "Contents/Config-0",
                {
                    48: ModelName,
                    107: OccurName,
                    318: CoreItems[0].TransX,
                    326: CoreItems[0].TransY,
                    334: CoreItems[0].TransZ,
                    442: ConfigName,
                    571: AsmPath,
                    709: ModelName,
                    756: OccurName,
                    888: SecondItem.OccurName,
                    1083: SecondItem.TransX,
                    1091: SecondItem.TransY,
                    1099: SecondItem.TransZ,
                    1207: SecondItem.ConfigName,
                    1334: SecondItem.OccurName,
                },
            ),
            "Contents/Config-0-ResolvedFeatures": EncodeProgramDistinct(
                "Contents/Config-0-ResolvedFeatures"
            ),
            "Contents/Definition": EncodeProgramDistinct("Contents/Definition"),
            "Contents/Config-0-ModelHeader": EncodeProgramDistinct(
                "Contents/Config-0-ModelHeader",
                {
                    142: ModelName,
                    1708: OccurName,
                    1844: SecondItem.OccurName,
                    1969: CompPath,
                    2153: CompStem,
                    2276: SecondItem.CompPath,
                    2444: SecondStem,
                    2555: AsmPath,
                    2693: ModelName,
                    2742: ConfigName,
                    **(
                        {2218: CoreItems[0].FileStamp, 2493: SecondItem.FileStamp}
                        if CoreItems[0].FileStamp > 0 and SecondItem.FileStamp > 0
                        else {}
                    ),
                },
            ),
        }
        return FinishCoreMut(StreamsMap)
    StreamsMap = {
        "Contents/CMgr": EncodeProgramTwo(
            "Contents/CMgr",
            {
                206: ConfigName,
                1241: DisplayName,
                1464: ModelName,
                1515: OccurName,
                1663: CoreItems[0].ConfigName,
                1701: CoreItems[0].ConfigName,
                1814: DisplayName,
                1956: SecondItem.OccurName,
                2087: SecondItem.ConfigName,
                2125: SecondItem.ConfigName,
            },
        ),
        "Contents/Config-0": EncodeProgramTwo(
            "Contents/Config-0",
            {
                48: ModelName,
                111: OccurName,
                322: CoreItems[0].TransX,
                330: CoreItems[0].TransY,
                338: CoreItems[0].TransZ,
                446: ConfigName,
                581: ModelName,
                632: OccurName,
                764: SecondItem.OccurName,
                975: SecondItem.TransX,
                983: SecondItem.TransY,
                991: SecondItem.TransZ,
                1099: SecondItem.ConfigName,
                1226: SecondItem.OccurName,
            },
        ),
        "Contents/Config-0-ResolvedFeatures": EncodeProgramTwo(
            "Contents/Config-0-ResolvedFeatures"
        ),
        "Contents/Definition": EncodeProgramTwo("Contents/Definition"),
        "Contents/Config-0-ModelHeader": EncodeProgramTwo(
            "Contents/Config-0-ModelHeader",
            {
                142: ModelName,
                1708: OccurName,
                1812: SecondItem.OccurName,
                1953: CompPath,
                2137: CompStem,
                2270: ModelName,
                2323: ConfigName,
                **(
                    {2202: CoreItems[0].FileStamp} if CoreItems[0].FileStamp > 0 else {}
                ),
            },
        ),
    }
    return FinishCoreMut(StreamsMap)


# one occurrence history remains isolated because its recovered offsets form the base program
def BuildSingleCore(
    ModelName: str, ConfigName: str, CoreItems: tuple[AsmCoreItem, ...], CompStem: str
) -> Mapping[str, bytes]:
    OccurName = CoreItems[0].OccurName
    CompPath = CoreItems[0].CompPath
    StreamsMap = {
        "Contents/CMgr": EncodeProgram(
            "Contents/CMgr",
            {
                206: ConfigName,
                1241: f"<{ConfigName}>_Display State 1",
                1464: ModelName,
                1515: OccurName,
                1663: CoreItems[0].ConfigName,
                1701: CoreItems[0].ConfigName,
            },
        ),
        "Contents/Config-0": EncodeProgram(
            "Contents/Config-0",
            {
                48: ModelName,
                111: OccurName,
                322: CoreItems[0].TransX,
                330: CoreItems[0].TransY,
                338: CoreItems[0].TransZ,
                446: ConfigName,
                581: ModelName,
                632: OccurName,
            },
        ),
        "Contents/Config-0-ResolvedFeatures": EncodeProgram(
            "Contents/Config-0-ResolvedFeatures"
        ),
        "Contents/Definition": EncodeProgram("Contents/Definition"),
        "Contents/Config-0-ModelHeader": EncodeProgram(
            "Contents/Config-0-ModelHeader",
            {
                142: ModelName,
                1708: OccurName,
                1849: CompPath,
                2033: CompStem,
                2166: ModelName,
                2219: ConfigName,
                **(
                    {2098: CoreItems[0].FileStamp} if CoreItems[0].FileStamp > 0 else {}
                ),
            },
        ),
    }
    return FinishCoreMut(StreamsMap)


# public core encoding selects one independently recovered program family after shared validation
def EncodeAsmCore(
    ModelName: str, ConfigName: str, CoreItems: tuple[AsmCoreItem, ...]
) -> Mapping[str, bytes]:
    if not ModelName or not ConfigName or (not CoreItems):
        raise SldprtFormatError("native assembly core fields cannot be empty")
    CompPath = CoreItems[0].CompPath
    if not CoreItems[0].OccurName or not CompPath:
        raise SldprtFormatError("native assembly occurrence fields cannot be empty")
    CompStem = PureWindowsPath(CompPath).stem
    if not CompStem:
        raise SldprtFormatError("native assembly component path has no stem")
    PathKeys = tuple(
        (str(PureWindowsPath(ItemValue.CompPath)).casefold() for ItemValue in CoreItems)
    )
    UniqueCount = len(set(PathKeys))
    FileStamps = {
        ItemValue.FileStamp for ItemValue in CoreItems if ItemValue.FileStamp > 0
    }
    if len(CoreItems) >= 3 and 1 < UniqueCount < len(CoreItems):
        Encoder = EncodeMixCore if len(FileStamps) == 1 else EncodeHybCore
        return BuildRepeatCore(ModelName, ConfigName, CoreItems, Encoder)
    if len(CoreItems) >= 3 and UniqueCount > 1:
        return BuildRepeatCore(ModelName, ConfigName, CoreItems, EncodePathCore)
    if len(CoreItems) >= 4:
        return BuildRepeatCore(ModelName, ConfigName, CoreItems, EncodeRepCore)
    IdentityVals = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    if any((tuple(ItemValue.BasisVals) != IdentityVals for ItemValue in CoreItems)):
        raise SldprtFormatError(
            "static native assembly history requires identity component bases"
        )
    DisplayName = f"<{ConfigName}>_Display State 1"
    AsmPath = str(PureWindowsPath(CompPath).parent / f"{ModelName}.SLDASM")
    if len(CoreItems) == 3:
        return BuildTripleCore(
            ModelName, ConfigName, CoreItems, DisplayName, AsmPath, CompStem
        )
    if len(CoreItems) == 2:
        return BuildPairCore(
            ModelName, ConfigName, CoreItems, DisplayName, AsmPath, CompStem
        )
    return BuildSingleCore(ModelName, ConfigName, CoreItems, CompStem)


# this definition exists because focused behavior needs one stable owner
def CoreCoverage() -> Mapping[str, int]:
    StreamBytes = sum(
        (len(EncodeProgram(StreamName)) for StreamName in KCoreStreamNames)
    )
    return MappingProxyType(
        {
            "stream_bytes": StreamBytes,
            "typed": StreamBytes,
            "opaque": KCoreOpaqueBytes,
            "operations": KCoreFieldCount,
            "owners": len(FieldOwners),
        }
    )


# this binding exists because shared behavior needs one stable value
CoreFieldCount = KCoreFieldCount

# this binding exists because shared behavior needs one stable value
CoreOpaqueBytes = KCoreOpaqueBytes

# this binding exists because shared behavior needs one stable value
CoreStreamNames = KCoreStreamNames

# this binding exists because shared behavior needs one stable value
EncodeProgram2 = EncodeProgramTwo

# this binding exists because shared behavior needs one stable value
EncodeProgram3 = EncodeProgramThree

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
dataclass = DataClass

# this binding exists because shared behavior needs one stable value
struct = Struct
