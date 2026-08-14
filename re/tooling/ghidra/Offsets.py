# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import pathlib as Pathlib
import re as Regex
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = Pathlib.Path(__file__).resolve().parents[3] / '.rescratch/ghidra/out'


# needed to keep reverse engineering responsibilities isolated and maintainable
def Blocks(PathInfoData):
    TextValueData = PathInfoData.read_text(errors='replace')
    for PartInfoInfo in TextValueData.split('\n=== FUNCTION ')[1:]:
        HeadInfo, SpareValue, BodyInfo = PartInfoInfo.partition('\n')
        yield (HeadInfo.strip(), BodyInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    PathInfoData = KOutInfo / (System.argv[1] if len(System.argv) > 1 else 'sldmodu_accessors.c')
    KeysInfo = System.argv[2:]
    for NameTextInfo, BodyInfo in Blocks(PathInfoData):
        if KeysInfo and (not any((KeyIndex in NameTextInfo for KeyIndex in KeysInfo))):
            continue
        OffsInfo = []
        for Match in Regex.finditer('(?:this|param_1)\\s*\\+\\s*(0x[0-9a-f]+|\\d+)', BodyInfo):
            ValueInfo = int(Match.group(1), 0)
            if ValueInfo not in OffsInfo:
                OffsInfo.append(ValueInfo)
        Types = sorted(set(Regex.findall('\\*\\((u?int|double|float|short|ushort|char|byte|longlong|undefined\\d?)\\s?\\*\\)', BodyInfo)))
        Lines = len(BodyInfo.splitlines())
        print(f'{NameTextInfo:56s} lines={Lines:4d} offs={[hex(OInfo) for OInfo in OffsInfo[:8]]} types={Types}')
if __name__ == '__main__':
    MainRunInfo()
