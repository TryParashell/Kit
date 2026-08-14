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
def Blocks(PathInfoData):
    TextValueData = Pathlib.Path(PathInfoData).read_text(errors='replace')
    Parts = TextValueData.split('\n=== FUNCTION ')
    for PartInfoInfo in Parts[1:]:
        HeadInfo, SpareValue, BodyInfo = PartInfoInfo.partition('\n')
        yield (HeadInfo.strip(), '=== FUNCTION ' + HeadInfo + '\n' + BodyInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    PathInfoData = System.argv[1]
    PatsInfo = System.argv[2:]
    for NameTextInfo, BodyInfo in Blocks(PathInfoData):
        if not PatsInfo or any((PathInfoInfo in NameTextInfo for PathInfoInfo in PatsInfo)):
            print(BodyInfo)
            print('-' * 78)
if __name__ == '__main__':
    MainRun()
