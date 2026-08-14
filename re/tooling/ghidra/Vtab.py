# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import pathlib as Pathlib
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[3]

# needed to keep reverse engineering responsibilities isolated and maintainable
KPathInfo = KRootInfo / ".rescratch/ghidra/out/sldmodu_vtables.txt"


# needed to keep reverse engineering responsibilities isolated and maintainable
def Tables():
    CurInfo = None
    GetRows = []
    for LineText in KPathInfo.read_text(errors="replace").splitlines():
        if LineText.startswith("=== VFTABLE "):
            if CurInfo is not None:
                yield (CurInfo, GetRows)
            BodyInfo = LineText[len("=== VFTABLE ") :]
            NameTextInfo, SpareValue, AddrInfo = BodyInfo.rpartition(" @ ")
            CurInfo = (NameTextInfo.strip(), AddrInfo.strip())
            GetRows = []
        elif CurInfo is not None and LineText.startswith("  "):
            Parts = LineText.split()
            if len(Parts) >= 3:
                GetRows.append((int(Parts[0]), Parts[1], Parts[2]))
    if CurInfo is not None:
        yield (CurInfo, GetRows)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    Wanted = System.argv[1:]
    ModeSlot = None
    if Wanted and Wanted[0].startswith("slot="):
        ModeSlot = int(Wanted[0].split("=", 1)[1])
        Wanted = Wanted[1:]
    for (NameTextInfo, AddrInfo), GetRows in Tables():
        if Wanted and NameTextInfo not in Wanted:
            continue
        if ModeSlot is not None:
            HitInfo = [
                ResultData for ResultData in GetRows if ResultData[0] == ModeSlot
            ]
            if HitInfo:
                print(
                    f"{NameTextInfo:34s} @{AddrInfo} slot{ModeSlot} {HitInfo[0][1]} {HitInfo[0][2]}"
                )
            continue
        print(f"=== {NameTextInfo} @ {AddrInfo}  slots={len(GetRows)}")
        for SlotIndex, Target, FnInfo in GetRows:
            print(f"  {SlotIndex:4d} {Target} {FnInfo}")


if __name__ == "__main__":
    MainRun()
