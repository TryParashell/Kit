# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
import json as JsonLib
from pathlib import Path as FilePath
import pytest as PytestLib
from convert.adapters.solidworks.container.Container import DEFAULT_FILE_ID as IdInfo, DEFAULT_SIGNATURES as Signatures, SldprtArchive, _template_fields as TemplateFields, build_sldprt as BuildSldprt, signature_triplet as SignatureTriplet

# centralizes shared evidence so every related assertion uses one value
KEntries = 1000

# centralizes shared evidence so every related assertion uses one value
KSuffixes = frozenset({'.SLDPRT', '.SLDASM'})

# centralizes shared evidence so every related assertion uses one value
KRootInfo = FilePath(__file__).resolve().parents[4]

# centralizes shared evidence so every related assertion uses one value
KExamples = KRootInfo / 'examples'

# centralizes shared evidence so every related assertion uses one value
KDllInfo = KRootInfo / 're' / 'binaries' / 'sldmfcu.dll'

# centralizes shared evidence so every related assertion uses one value
KManifest = KRootInfo / 're' / 'binaries' / 'Manifest.json'

# centralizes shared evidence so every related assertion uses one value
KProvenance = KRootInfo / 're' / 'data' / 'SignatureTable.json'

# centralizes shared evidence so every related assertion uses one value
KNameInfo = 'sldmfcu.dll'

# centralizes shared evidence so every related assertion uses one value
KOffset = 5663808

# centralizes shared evidence so every related assertion uses one value
KRowInfo = ('64d80045', 'ae0d4ef6', '54ce179a')

# centralizes shared evidence so every related assertion uses one value
KIndex = 711

# keeps this focused behavior isolated so regressions remain immediately visible
def LoadHostDll() -> bytes:
    assert KDllInfo.is_file(), KDllInfo
    HostData = KDllInfo.read_bytes()
    if HostData.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        PytestLib.skip('sldmfcu.dll content is unavailable because Git LFS is not hydrated')
    assert Hashlib.sha256(HostData).hexdigest() == RecordedHD()
    return HostData

# keeps this focused behavior isolated so regressions remain immediately visible
def ExampleD() -> list[FilePath]:
    if not KExamples.is_dir():
        return []
    return sorted((TargetPath for TargetPath in KExamples.rglob('*') if TargetPath.is_file() and TargetPath.suffix.upper() in KSuffixes))

# keeps this focused behavior isolated so regressions remain immediately visible
def HostRows(BlobInfo: bytes) -> list[tuple[int, tuple[str, str, str]]]:
    SigBase = KOffset + KEntries * 4
    RowsInfo: list[tuple[int, tuple[str, str, str]]] = []
    for Index in range(KEntries):
        HeadInfo = KOffset + 4 * Index
        FileId = int.from_bytes(BlobInfo[HeadInfo:HeadInfo + 4], 'big')
        Magics = tuple((bytes(reversed(BlobInfo[Start:Start + 4])).hex() for Start in (SigBase + 12 * Index + 4 * SlotInfo for SlotInfo in range(3))))
        RowsInfo.append((FileId, Magics))
    return RowsInfo

# keeps this focused behavior isolated so regressions remain immediately visible
def RecordedHD() -> str:
    Payload = JsonLib.loads(KManifest.read_text(encoding='utf-8'))
    Entries = Payload if isinstance(Payload, list) else Payload.get('binaries', ())
    for Entry in Entries:
        if isinstance(Entry, dict) and Entry.get('name') == KNameInfo:
            return str(Entry['sha256'])
    raise AssertionError(f'{KNameInfo} is absent from {KManifest}')

# keeps this focused behavior isolated so regressions remain immediately visible
def TestOOSRICIS() -> None:
    assert len(Signatures) == 3
    assert all((len(ItemValue) == 4 for ItemValue in Signatures))
    assert tuple((ItemValue.hex() for ItemValue in Signatures)) == KRowInfo
    assert 0 < IdInfo <= 4294967295
    Carried = 4 + sum((len(ItemValue) for ItemValue in Signatures))
    assert Carried == 16

# keeps this focused behavior isolated so regressions remain immediately visible
def TestTCRIAGROTVT() -> None:
    HostInfo = LoadHostDll()
    RowsInfo = HostRows(HostInfo)
    assert len(RowsInfo) == KEntries
    assert len({FileId for FileId, IgnoredValue in RowsInfo}) == KEntries
    assert RowsInfo[KIndex] == (IdInfo, KRowInfo)
    Matches = [Index for Index, (FileId, Magics) in enumerate(RowsInfo) if FileId == IdInfo and Magics == KRowInfo]
    assert Matches == [KIndex]

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPRDTWTATCR() -> None:
    RecordInfo = JsonLib.loads(KProvenance.read_text(encoding='utf-8'))
    assert RecordInfo['host'] == KNameInfo
    assert RecordInfo['host_sha256'] == RecordedHD()
    assert RecordInfo['block_file_offset'] == KOffset
    assert RecordInfo['entry_count'] == KEntries
    assert RecordInfo['shipped_rows'] == 1
    Entries = RecordInfo['entries']
    assert len(Entries) == KEntries
    Carried = Entries[KIndex]
    assert Carried['file_id'] == f'{IdInfo:08x}'
    assert (Carried['local'], Carried['central'], Carried['end']) == KRowInfo

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCUTCR() -> None:
    Streams = {'Contents/SolidWorks': b'<swSolidWorks/>', 'Contents/Config-0-Partition': b'PS\x00\x00body'}
    BlobInfo = BuildSldprt(Streams)
    assert BlobInfo[:4] == IdInfo.to_bytes(4, 'big')
    Archive = SldprtArchive.from_bytes(BlobInfo)
    assert Archive.file_id == IdInfo
    assert Archive.streams == Streams
    SignaturesA, IgnoredValue = TemplateFields(BlobInfo, Archive)
    assert SignaturesA == Signatures

# keeps this focused behavior isolated so regressions remain immediately visible
def TestFIWACRRTIS() -> None:
    Absent = next((ItemValue for ItemValue in range(1, 1 << 20) if ItemValue != IdInfo))
    with PytestLib.raises(ValueError, match='native template'):
        BuildSldprt({'Contents/SolidWorks': b'<swSolidWorks/>'}, file_id=Absent)
    assert SignatureTriplet(Absent) is None
    assert SignatureTriplet(IdInfo) == Signatures

# keeps this focused behavior isolated so regressions remain immediately visible
def TestEDPTOIWTOS() -> None:
    Documents = ExampleD()
    assert Documents
    HostRowsA = dict(HostRows(LoadHostDll()))
    Covered = 0
    for TargetPath in Documents:
        BlobInfo = TargetPath.read_bytes()
        Archive = SldprtArchive.from_bytes(BlobInfo, TargetPath)
        SignaturesA, IgnoredValue = TemplateFields(BlobInfo, Archive)
        assert Archive.file_id in HostRowsA, TargetPath.name
        Recorded = HostRowsA[Archive.file_id]
        assert tuple((ItemValue.hex() for ItemValue in SignaturesA)) == Recorded, TargetPath.name
        Covered += 1
    assert Covered == len(Documents)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestTPPADIWAST() -> None:
    Documents = ExampleD()
    assert Documents
    Template = Documents[0].read_bytes()
    SourceDoc = SldprtArchive.from_bytes(Template, Documents[0])
    assert SourceDoc.file_id != IdInfo or len(Documents) > 1
    Rebuilt = BuildSldprt(SourceDoc.streams, template=Template)
    Archive = SldprtArchive.from_bytes(Rebuilt)
    assert Archive.file_id == SourceDoc.file_id
    Expected, IgnoredValue = TemplateFields(Template, SourceDoc)
    Actual, IgnoredValue = TemplateFields(Rebuilt, Archive)
    assert Actual == Expected
