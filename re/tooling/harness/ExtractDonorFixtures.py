# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
import json as JsonData
from pathlib import Path as PathInfo
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = KHereInfo.parents[2]

# needed to keep reverse engineering responsibilities isolated and maintainable
KFixtureRoot = KRootInfo / 'tests' / 'fixtures' / 'solidworks' / 'donors'

# needed to keep reverse engineering responsibilities isolated and maintainable
KManifestName = 'manifest.json'

# needed to keep reverse engineering responsibilities isolated and maintainable
KMetaName = 'meta.json'

# needed to keep reverse engineering responsibilities isolated and maintainable
KResolvedName = 'resolved.bin'

# needed to keep reverse engineering responsibilities isolated and maintainable
KContainDir = 'container'

# needed to keep reverse engineering responsibilities isolated and maintainable
KPerFeatKeys = ('features', 'feature_ids', 'sketch_ids', 'feature_names', 'sketch_names', 'point_counts', 'arc_counts', 'depth_present')


# needed to keep reverse engineering responsibilities isolated and maintainable
def SanitisedName(NameTextInfo: str) -> str:
    return NameTextInfo.replace('/', '__')


# needed to keep reverse engineering responsibilities isolated and maintainable
def ContainFileName(NameTextInfo: str) -> str:
    return f'{SanitisedName(NameTextInfo)}.bin'


# needed to keep reverse engineering responsibilities isolated and maintainable
def Digest(PayloadInfo: bytes) -> str:
    return Hashlib.sha256(PayloadInfo).hexdigest()


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadJson(PathInfoData: PathInfo) -> object:
    return JsonData.loads(PathInfoData.read_text(encoding='utf-8'))


# needed to keep reverse engineering responsibilities isolated and maintainable
def VerifyRecord(PathInfoData: PathInfo, Record: dict[str, object], ExpectFile: str) -> tuple[int, list[str]]:
    Failures: list[str] = []
    if Record.get('file') != ExpectFile:
        Failures.append(f"{PathInfoData}: manifest names {Record.get('file')!r}")
    if not PathInfoData.is_file():
        Failures.append(f'{PathInfoData}: missing')
        return (0, Failures)
    PayloadInfo = PathInfoData.read_bytes()
    if Record.get('length') != len(PayloadInfo):
        Failures.append(f"{PathInfoData}: manifest length {Record.get('length')} but {len(PayloadInfo)} on disk")
    ActualInfo = Digest(PayloadInfo)
    if Record.get('sha256') != ActualInfo:
        Failures.append(f"{PathInfoData}: manifest sha256 {Record.get('sha256')} but {ActualInfo}")
    return (len(PayloadInfo), Failures)


# needed to keep reverse engineering responsibilities isolated and maintainable
def VerifyMeta(DirInfo: PathInfo, DonorId: str, Contain: dict[str, object]) -> tuple[int, list[str]]:
    PathInfoData = DirInfo / KMetaName
    Failures: list[str] = []
    if not PathInfoData.is_file():
        return (0, [f'{PathInfoData}: missing'])
    Encoded = PathInfoData.read_bytes()
    MetaInfo = ReadJson(PathInfoData)
    if not isinstance(MetaInfo, dict):
        return (len(Encoded), [f'{PathInfoData}: not an object'])
    if MetaInfo.get('donor_id') != DonorId:
        Failures.append(f"{PathInfoData}: describes {MetaInfo.get('donor_id')!r}")
    FeatInfoInfo = MetaInfo.get('features')
    if not isinstance(FeatInfoInfo, list) or not FeatInfoInfo:
        Failures.append(f'{PathInfoData}: lists no features')
    else:
        for KeyName in KPerFeatKeys:
            ValueInfo = MetaInfo.get(KeyName)
            if not isinstance(ValueInfo, list) or len(ValueInfo) != len(FeatInfoInfo):
                Failures.append(f'{PathInfoData}: {KeyName} does not hold one entry per feature')
    StreamsInfo = MetaInfo.get('container_streams')
    if not isinstance(StreamsInfo, list):
        Failures.append(f'{PathInfoData}: lists no container streams')
    else:
        Named = {ItemData['name']: ItemData['file'] for ItemData in StreamsInfo}
        if sorted(Named) != sorted(Contain):
            Failures.append(f'{PathInfoData}: container stream names differ from the manifest')
        for NameTextInfo, FileName in Named.items():
            if FileName != ContainFileName(NameTextInfo):
                Failures.append(f'{PathInfoData}: stream {NameTextInfo} names {FileName!r}')
    return (len(Encoded), Failures)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Verify(FixtureRoot: PathInfo) -> dict[str, object]:
    ManifestInfo = FixtureRoot / KManifestName
    if not ManifestInfo.is_file():
        return {'fixture_root': str(FixtureRoot), 'donor_count': 0, 'failures': [f'{ManifestInfo}: missing']}
    Manifest = ReadJson(ManifestInfo)
    if not isinstance(Manifest, dict):
        return {'fixture_root': str(FixtureRoot), 'donor_count': 0, 'failures': [f'{ManifestInfo}: not an object']}
    Donors = Manifest.get('donors')
    if not isinstance(Donors, dict):
        return {'fixture_root': str(FixtureRoot), 'donor_count': 0, 'failures': [f'{ManifestInfo}: carries no donor index']}
    Failures: list[str] = []
    ResolvedBytes = 0
    ContainBytes = 0
    MetaBytes = len(ManifestInfo.read_bytes())
    Files = 1
    for DonorId in sorted(Donors):
        Record = Donors[DonorId]
        DirInfo = FixtureRoot / DonorId
        if not DirInfo.is_dir():
            Failures.append(f'{DirInfo}: missing')
            continue
        Length, Problems = VerifyRecord(DirInfo / KResolvedName, Record['resolved'], KResolvedName)
        ResolvedBytes += Length
        Failures.extend(Problems)
        Files += 1
        Contain = Record['container']
        for NameTextInfo in sorted(Contain):
            Expect = f'{KContainDir}/{ContainFileName(NameTextInfo)}'
            Length, Problems = VerifyRecord(DirInfo / KContainDir / ContainFileName(NameTextInfo), Contain[NameTextInfo], Expect)
            ContainBytes += Length
            Failures.extend(Problems)
            Files += 1
        Length, Problems = VerifyMeta(DirInfo, DonorId, Contain)
        MetaBytes += Length
        Failures.extend(Problems)
        Files += 1
    DeclaredInfo = Manifest.get('resolved_bytes')
    if DeclaredInfo != ResolvedBytes:
        Failures.append(f'{ManifestInfo}: declares {DeclaredInfo} resolved bytes but {ResolvedBytes} are on disk')
    DeclaredContain = Manifest.get('container_bytes')
    if DeclaredContain != ContainBytes:
        Failures.append(f'{ManifestInfo}: declares {DeclaredContain} container bytes but {ContainBytes} are on disk')
    DeclaredCount = Manifest.get('donor_count')
    if DeclaredCount != len(Donors):
        Failures.append(f'{ManifestInfo}: declares {DeclaredCount} donors but indexes {len(Donors)}')
    OnDisk = sorted((PathInfoData.name for PathInfoData in FixtureRoot.iterdir() if PathInfoData.is_dir()))
    if OnDisk != sorted(Donors):
        Failures.append(f'{FixtureRoot}: directories on disk differ from the manifest index')
    return {'fixture_root': str(FixtureRoot), 'donor_count': len(Donors), 'directories': len(OnDisk), 'files': Files, 'resolved_bytes': ResolvedBytes, 'container_bytes': ContainBytes, 'metadata_bytes': MetaBytes, 'total_bytes': ResolvedBytes + ContainBytes + MetaBytes, 'failures': Failures}


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo() -> int:
    Summary = Verify(KFixtureRoot)
    System.stdout.write(JsonData.dumps(Summary, indent=2, sort_keys=True) + '\n')
    return 1 if Summary['failures'] else 0
if __name__ == '__main__':
    raise SystemExit(MainRunInfo())
