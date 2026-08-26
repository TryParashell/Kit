# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib.machinery import SourceFileLoader
from pathlib import Path as PathInfo
from types import ModuleType
from typing import Callable, cast, Protocol, TypedDict


# accessor classification needs one stable mapping contract for security regression assertions
class AccessorResult(TypedDict):
    kind: str
    width: int
    ctype: str
    stride: int
    offset: int


# comment scanner modules need a typed boundary despite their nonpackage tooling location
class CommentScanner(Protocol):
    StripComments: Callable[[str], str]


# accessor tooling needs its classification operation in addition to shared comment scanning
class AccessorScanner(CommentScanner, Protocol):
    Classify: Callable[[str], AccessorResult | None]


# repository discovery keeps regression tests independent from the invocation directory
KRootInfo = PathInfo(__file__).resolve().parents[3]

# generation discovery exercises the exact production regular expressions and scanners
KGeneration = KRootInfo / "re" / "tooling" / "ghidra" / "Generation"


# source loading avoids mutating global import search state while retaining exact tool behavior
def LoadTool(ModuleName: str) -> ModuleType:
    LoaderData = SourceFileLoader(ModuleName, str(KGeneration / f"{ModuleName}.py"))
    ModuleData = ModuleType(ModuleName)
    LoaderData.exec_module(ModuleData)
    return ModuleData


# serialize scanner typing keeps adversarial comment tests free from unknown module members
KExtractSerialize = cast(CommentScanner, LoadTool("ExtractSerialize"))


# accessor scanner typing keeps regex behavior directly checked without broad dynamic values
KMineAccessors = cast(AccessorScanner, LoadTool("MineAccessors"))


# adversarial comments prove both scanners use deterministic bounded delimiter searches
def TestCommentScan() -> None:
    PayloadInfo = "left/*" + ("a" * 100_000) + "*/right/*unterminated"
    assert KMineAccessors.StripComments(PayloadInfo) == "left right "
    assert KExtractSerialize.StripComments(PayloadInfo) == "left right "


# accessor samples preserve captured layout facts after possessive quantifier hardening
def TestAccessMatch() -> None:
    BodyInfo = "return *(unsigned int *)(this + (longlong)param_2 * 4 + 0x20);"
    assert KMineAccessors.Classify(BodyInfo) == {
        "kind": "get",
        "width": 4,
        "ctype": "unsigned int",
        "stride": 4,
        "offset": 32,
    }


# long near misses prove the hardened accessor patterns terminate without partial matches
def TestNoBacktrack() -> None:
    PayloadInfo = "return *(" + ("unsigned " * 20_000) + ")"
    assert KMineAccessors.Classify(PayloadInfo) is None
