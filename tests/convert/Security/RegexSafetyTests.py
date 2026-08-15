# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as PathInfo
import sys as System

# repository discovery keeps regression tests independent from the invocation directory
KRootInfo = PathInfo(__file__).resolve().parents[3]

# generation discovery exercises the exact production regular expressions and scanners
KGeneration = KRootInfo / "re" / "tooling" / "ghidra" / "Generation"
System.path.insert(0, str(KGeneration))
import ExtractSerialize as ExtractSerialize
import MineAccessors as MineAccessors


# adversarial comments prove both scanners use deterministic bounded delimiter searches
def TestCommentScan() -> None:
    PayloadInfo = "left/*" + ("a" * 100_000) + "*/right/*unterminated"
    assert MineAccessors.StripComments(PayloadInfo) == "left right "
    assert ExtractSerialize.StripComments(PayloadInfo) == "left right "


# accessor samples preserve captured layout facts after possessive quantifier hardening
def TestAccessMatch() -> None:
    BodyInfo = "return *(unsigned int *)(this + (longlong)param_2 * 4 + 0x20);"
    assert MineAccessors.Classify(BodyInfo) == {
        "kind": "get",
        "width": 4,
        "ctype": "unsigned int",
        "stride": 4,
        "offset": 32,
    }


# long near misses prove the hardened accessor patterns terminate without partial matches
def TestNoBacktrack() -> None:
    PayloadInfo = "return *(" + ("unsigned " * 20_000) + ")"
    assert MineAccessors.Classify(PayloadInfo) is None
