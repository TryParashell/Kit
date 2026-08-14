# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import json as JsonData
from pathlib import Path as PathInfo
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = KHereInfo.parents[2]

# needed to keep reverse engineering responsibilities isolated and maintainable
KScratch = KRootInfo / '.rescratch'

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / 'harness'
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KParts = KScratch / 'donors' / 'parts'

# needed to keep reverse engineering responsibilities isolated and maintainable
KFixtures = KRootInfo / 'tests' / 'fixtures' / 'solidworks' / 'donors'

# needed to keep reverse engineering responsibilities isolated and maintainable
KManifest = KFixtures / 'manifest.json'

# needed to keep reverse engineering responsibilities isolated and maintainable
KResolvedName = 'resolved.bin'

# needed to keep reverse engineering responsibilities isolated and maintainable
KContainDir = 'container'


# needed to keep reverse engineering responsibilities isolated and maintainable
def ContainFileName(NameTextInfo: str) -> str:
    return f"{NameTextInfo.replace('/', '__')}.bin"


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain() -> int:
    Manifest = JsonData.loads(KManifest.read_text(encoding='utf-8'))
    Donors = Manifest['donors']
    Mismatches = 0
    MissingInfo = 0
    for DonorId in sorted(Donors):
        DirInfo = KFixtures / DonorId
        PartInfoInfo = KParts / f'{DonorId}.SLDPRT'
        if not PartInfoInfo.is_file():
            print(f'{DonorId:38s} no authored part on disk')
            MissingInfo += 1
            continue
        RealInfo = Streamlib.LoadDonor(PartInfoInfo)
        Resolved = (DirInfo / KResolvedName).read_bytes()
        GetRows = [f'{DonorId:38s}']
        State = 'same' if Resolved == RealInfo.resolved else 'DIFFERS'
        if State != 'same':
            Mismatches += 1
        GetRows.append(f'resolved={State}')
        for NameTextInfo in sorted(Donors[DonorId]['container']):
            PathInfoData = DirInfo / KContainDir / ContainFileName(NameTextInfo)
            Expect = PathInfoData.read_bytes() if PathInfoData.is_file() else None
            ActualInfo = RealInfo.streams.get(NameTextInfo)
            State = 'same' if Expect is not None and Expect == ActualInfo else 'DIFFERS'
            if State != 'same':
                Mismatches += 1
            GetRows.append(f"{NameTextInfo.split('/')[-1]}={State}")
        print(' '.join(GetRows))
    print(f'fixtures={len(Donors)} parts_missing={MissingInfo} stream_mismatches={Mismatches}')
    return 1 if Mismatches else 0


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    if not KManifest.is_file():
        print(f'missing fixture manifest {KManifest}')
        return 1
    return FinishMain()
if __name__ == '__main__':
    raise SystemExit(MainRun())
