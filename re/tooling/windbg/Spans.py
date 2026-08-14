# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as PathInfo
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / 'harness'
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KTargets = ('Contents/Config-0-ResolvedFeatures', 'Contents/CMgr', 'Contents/Config-0-ModelHeader', 'Header2', 'Contents/Config-0', 'ThirdPtyStore/VisualStates')


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo() -> int:
    for ItemData in System.argv[1:]:
        PartInfoInfo = PathInfo(ItemData).resolve()
        DonorInfo = Streamlib.LoadDonor(PartInfoInfo)
        FeatInfoInfo = len(Streamlib.CompFeatEntries(DonorInfo.resolved)) // 2
        Sizes = {NameTextInfo: len(DonorInfo.streams[NameTextInfo]) for NameTextInfo in DonorInfo.streams}
        Collisions = {NameTextInfo: sorted((Other for Other, Length in Sizes.items() if Length == Sizes[NameTextInfo] and Other != NameTextInfo)) for NameTextInfo in KTargets if NameTextInfo in Sizes}
        print(f'{PartInfoInfo.stem} features={FeatInfoInfo}')
        for NameTextInfo in KTargets:
            if NameTextInfo not in Sizes:
                print(f'    {NameTextInfo:38s} absent')
                continue
            print(f'    {NameTextInfo:38s} {Sizes[NameTextInfo]:7d} 0x{Sizes[NameTextInfo]:x} collides={Collisions[NameTextInfo]}')
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRunInfo())
