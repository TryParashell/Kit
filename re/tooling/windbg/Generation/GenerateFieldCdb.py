# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import argparse
from pathlib import Path


# primitive entry points expose every archive field width used by the native reader
FieldBreakpoints = (
    ("char", "0x4290"),
    ("uchar", "0x42a0"),
    ("short", "0x4300"),
    ("ushort", "0x4310"),
    ("int", "0x4370"),
    ("long", "0x4380"),
    ("ulong", "0x43e0"),
    ("float", "0x4440"),
    ("double", "0x44a0"),
    ("dbkey", "0x4500"),
    ("int64", "0x4510"),
    ("uint64", "0x4570"),
)


# command arguments bind one stream length to one reproducible debugger script
def ParseArguments() -> argparse.Namespace:
    Parser = argparse.ArgumentParser()
    Parser.add_argument("stream_bytes", type=int)
    Parser.add_argument("output", type=Path)
    return Parser.parse_args()


# script generation keeps the stream guard identical across every corpus family
def GenerateScript(StreamBytes: int) -> str:
    if StreamBytes <= 0:
        raise ValueError("resolved stream length must be positive")
    GuardText = hex(StreamBytes)
    LinesData = [
        "$$ SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0",
        "$$ SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin",
        "$$",
        "$$ This SPDX license identifier and copyright notice must not be",
        "$$ removed, altered, or obscured. Doing so is a material breach of",
        "$$ the PolyForm Strict License 1.0.0 and voids all licenses granted",
        "$$ to you under it immediately and permanently.",
        ".symopt+0x4000",
        ".symopt-0x20000",
        ".exepath+ C:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS",
        ".reload /f swccu.dll",
        "sxi 80090016",
        "sxi 80290410",
        "sxi e06d7363",
        "sxi e0434352",
        "sxi 04242420",
    ]
    for TypeName, EntryPoint in FieldBreakpoints:
        LinesData.append(
            f'bu swccu+{EntryPoint} ".if '
            f"((poi(@rcx+0x40)-poi(@rcx+0x48))=={GuardText}) "
            '{ .printf \\"F ' + TypeName + ' %x %p %y %p %p\\\\n\\", '
            "poi(@rcx+0x38)-poi(@rcx+0x48), poi(@rsp), poi(@rsp), "
            '@rdx, @rsp }; gc"'
        )
    LinesData.extend(("bl", "g"))
    return "\n".join(LinesData) + "\n"


# the command writes only oracle tooling and never participates in conversion runtime
def RunMain() -> int:
    Arguments = ParseArguments()
    Arguments.output.write_text(
        GenerateScript(Arguments.stream_bytes),
        encoding="ascii",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(RunMain())
