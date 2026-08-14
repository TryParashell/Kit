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
from convert.adapters.solidworks import resolved as Resolvedlib


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo() -> int:
    for ItemData in System.argv[1:]:
        PartInfoInfo = PathInfo(ItemData).resolve()
        DonorInfo = Streamlib.LoadDonor(PartInfoInfo)
        ByteBlob = DonorInfo.resolved
        Nodes = Resolvedlib.tree_nodes(ByteBlob)
        FeatInfoInfo = Resolvedlib.locate_features(ByteBlob)
        Entries = Streamlib.CompFeatEntries(ByteBlob)
        print(f'{PartInfoInfo.stem}')
        print('  tree: ' + ', '.join((f'{NodeInfoInfo.name}#{NodeInfoInfo.feature_id}' for NodeInfoInfo in Nodes)))
        print('  features: ' + ', '.join((f'{ItemData.kind}:{ItemData.feature_id}/sketch={ItemData.sketch_id}' for ItemData in FeatInfoInfo)))
        print('  comp ids: ' + ', '.join((str(Entry[2]) for Entry in Entries)))
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRunInfo())
