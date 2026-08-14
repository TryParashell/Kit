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
KeepInfo = Regex.compile('AR_get_|AR_put_|operator>>|operator<<|ReadObject|WriteObject|IsStoring|hasCondition|Serialize|getCurrentFileVerion|0x780|goto|LAB_|if \\(|\\} else|while|for \\(|su_DBKey|CStringT<wchar_t.*\\"|code \\*\\*\\)\\(\\*')


# needed to keep reverse engineering responsibilities isolated and maintainable
def Blocks(PathInfoData):
    TextValueData = PathInfoData.read_text(errors='replace').splitlines()
    Starts = [IndexInfo for IndexInfo, LineText in enumerate(TextValueData) if LineText.startswith('=== FUNCTION')]
    Starts.append(len(TextValueData))
    for PosInfo in range(len(Starts) - 1):
        HeadInfo = Starts[PosInfo]
        BodyInfo = TextValueData[HeadInfo:Starts[PosInfo + 1]]
        Address = ''
        for LineText in BodyInfo[:5]:
            if LineText.startswith('=== ADDRESS '):
                Address = LineText.split()[-1]
        yield (Address, BodyInfo[0], BodyInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    PathInfoData = KOutInfo / System.argv[1]
    Wanted = System.argv[2]
    ModeInfo = System.argv[3] if len(System.argv) > 3 else 'skeleton'
    for Address, Header, BodyInfo in Blocks(PathInfoData):
        if Wanted.lower() not in Address.lower() and Wanted not in Header:
            continue
        print(f'##### {Header} @ {Address} lines={len(BodyInfo)}')
        for IndexData, LineText in enumerate(BodyInfo):
            Stripped = LineText.strip()
            if ModeInfo == 'full' or KeepInfo.search(Stripped):
                print(f'{IndexData:5d} {Stripped[:160]}')
        print()
if __name__ == '__main__':
    MainRun()
