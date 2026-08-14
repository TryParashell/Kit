# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse as Argparse
import hashlib as Hashlib
import json as JsonData
import pathlib as Pathlib
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[4]

# needed to keep reverse engineering responsibilities isolated and maintainable
KVendored = KRootInfo / 're/binaries/sldmfcu.dll'

# needed to keep reverse engineering responsibilities isolated and maintainable
KManifest = KRootInfo / 're/binaries/Manifest.json'

# needed to keep reverse engineering responsibilities isolated and maintainable
KInstalled = Pathlib.Path('C:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS\\sldmfcu.dll')

# needed to keep reverse engineering responsibilities isolated and maintainable
KRecord = KRootInfo / 're/data/Serialization/SignatureTable.json'

# needed to keep reverse engineering responsibilities isolated and maintainable
KHostName = 'sldmfcu.dll'

# needed to keep reverse engineering responsibilities isolated and maintainable
KBlockOffset = 5663808

# needed to keep reverse engineering responsibilities isolated and maintainable
KEntryCount = 1000

# needed to keep reverse engineering responsibilities isolated and maintainable
KIdStride = 4

# needed to keep reverse engineering responsibilities isolated and maintainable
KSigStride = 12


# needed to keep reverse engineering responsibilities isolated and maintainable
def HostDll(Explicit: str | None) -> Pathlib.Path:
    if Explicit:
        return Pathlib.Path(Explicit)
    if KVendored.is_file():
        return KVendored
    return KInstalled


# needed to keep reverse engineering responsibilities isolated and maintainable
def RecordedDigest() -> str | None:
    if not KManifest.is_file():
        return None
    PayloadInfo = JsonData.loads(KManifest.read_text(encoding='utf-8'))
    Entries = PayloadInfo if isinstance(PayloadInfo, list) else PayloadInfo.get('binaries', ())
    for Entry in Entries:
        if isinstance(Entry, dict) and Entry.get('name') == KHostName:
            Digest = Entry.get('sha256')
            return str(Digest) if Digest else None
    return None


# needed to keep reverse engineering responsibilities isolated and maintainable
def Extract(PathInfoData: Pathlib.Path) -> list[tuple[int, bytes]]:
    ByteBlob = PathInfoData.read_bytes()
    IdsBase = KBlockOffset
    SigBase = KBlockOffset + KEntryCount * KIdStride
    EndIndex = SigBase + KEntryCount * KSigStride
    if EndIndex > len(ByteBlob):
        raise SystemExit(f'{PathInfoData} is too small to hold the signature table')
    GetRows: list[tuple[int, bytes]] = []
    for IndexData in range(KEntryCount):
        HeadInfo = IdsBase + KIdStride * IndexData
        FileId = int.from_bytes(ByteBlob[HeadInfo:HeadInfo + KIdStride], 'big')
        Triplet = bytearray()
        for SlotIndex in range(3):
            StartRun = SigBase + KSigStride * IndexData + 4 * SlotIndex
            Triplet.extend(Reversed(ByteBlob[StartRun:StartRun + 4]))
        GetRows.append((FileId, bytes(Triplet)))
    return GetRows


# needed to keep reverse engineering responsibilities isolated and maintainable
def PackInfo(GetRows: list[tuple[int, bytes]]) -> bytes:
    return b''.join((FileId.to_bytes(KIdStride, 'big') + Triplet for FileId, Triplet in GetRows))


# needed to keep reverse engineering responsibilities isolated and maintainable
def Provenance(PathInfoData: Pathlib.Path, GetRows: list[tuple[int, bytes]], Digest: str) -> dict[str, object]:
    return {'host': KHostName, 'host_sha256': Digest, 'host_bytes': PathInfoData.stat().st_size, 'block_file_offset': KBlockOffset, 'entry_count': KEntryCount, 'id_array_file_offset': KBlockOffset, 'signature_array_file_offset': KBlockOffset + KEntryCount * KIdStride, 'id_encoding': 'big-endian u32', 'signature_encoding': 'little-endian u32 stored big-endian', 'reader': 'FUN_3cc4d270 keys on file_id, caches the row magics at +0x88/+0x8c/+0x90', 'comparison_sites': {'local': 'FUN_3cc528b0 unz+0xc8', 'central': 'FUN_3cc52ac0 unz+0xcc', 'end': 'FUN_3cc51900 backward scan on unz+0xd0'}, 'writer': 'FUN_3cc4a8c0 draws a random index in [0,1000) and emits that row', 'shipped_rows': 1, 'entries': [{'index': IndexData, 'file_id': f'{FileId:08x}', 'local': Triplet[0:4].hex(), 'central': Triplet[4:8].hex(), 'end': Triplet[8:12].hex()} for IndexData, (FileId, Triplet) in enumerate(GetRows)]}


# needed to keep reverse engineering responsibilities isolated and maintainable
def ShippedRow() -> tuple[int, bytes] | None:
    System.path.insert(0, str(KRootInfo / 'src'))
    try:
        from convert.adapters.solidworks import container as Contain
    except ImportError:
        return None
    FileId = getattr(Contain, 'DEFAULT_FILE_ID', None)
    Triplet = getattr(Contain, 'DEFAULT_SIGNATURES', None)
    if FileId is None or Triplet is None:
        return None
    return (int(FileId), b''.join(Triplet))


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument('--dll')
    ParserInfo.add_argument('--check', action='store_true')
    ArgValues = ParserInfo.parse_args()
    PathInfoData = HostDll(ArgValues.dll)
    if not PathInfoData.is_file():
        print(f'host dll {PathInfoData} is not present')
        return 1
    Digest = Hashlib.sha256(PathInfoData.read_bytes()).hexdigest()
    Expect = RecordedDigest()
    GetRows = Extract(PathInfoData)
    IdsInfo = [FileId for FileId, SpareValue in GetRows]
    if len(set(IdsInfo)) != KEntryCount:
        print('signature table ids are not distinct')
        return 1
    Table = PackInfo(GetRows)
    print(f'host {PathInfoData}')
    print(f'host_sha256 {Digest}')
    print(f'entries {KEntryCount} distinct_ids {len(set(IdsInfo))} raw_bytes {len(Table)}')
    if Expect is not None and Expect != Digest:
        print(f'MISMATCH host digest differs from {KManifest.name} {Expect}')
        return 1
    if ArgValues.check:
        Shipped = ShippedRow()
        if Shipped is None:
            print('Container.py exposes no default signature row')
            return 1
        FileId, Triplet = Shipped
        IndexData = next((PosInfoInfo for PosInfoInfo, (CandInfo, PayloadInfo) in enumerate(GetRows) if CandInfo == FileId and PayloadInfo == Triplet), None)
        if IndexData is None:
            print(f'MISMATCH 0x{FileId:08x} {Triplet.hex()} is not a row of the DLL')
            return 1
        print(f'shipped row 0x{FileId:08x} is DLL table index {IndexData}')
        print(f'shipped vendor bytes {4 + len(Triplet)} of {len(Table)}')
        return 0
    KRecord.parent.mkdir(parents=True, exist_ok=True)
    KRecord.write_text(JsonData.dumps(Provenance(PathInfoData, GetRows, Digest), indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'wrote {KRecord.relative_to(KRootInfo)}')
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRun())
