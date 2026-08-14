# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import struct as StructLib
import pytest as PytestLib
from convert.adapters.solidworks import SldprtArchive, build_sldprt as BuildSldprt
from convert.adapters.solidworks.container.Container import container_signatures as ContainerSignatures

# centralizes shared evidence so every related assertion uses one value
KMarker = bytes.fromhex('140006000800')

# centralizes shared evidence so every related assertion uses one value
KSignatureB = bytes.fromhex('a1909b1f')

# centralizes shared evidence so every related assertion uses one value
KSignature = bytes.fromhex('a576970f')

# centralizes shared evidence so every related assertion uses one value
KSignatureA = bytes.fromhex('7a004720')

# centralizes shared evidence so every related assertion uses one value
KIdInfo = 1901848975

# centralizes shared evidence so every related assertion uses one value
KSignatures = (KSignatureB, KSignature, KSignatureA)

# keeps this focused behavior isolated so regressions remain immediately visible
def DecodedName(ItemValue: bytes) -> str:
    return bytes((ByteInfo >> 4 | (ByteInfo & 15) << 4 for ByteInfo in ItemValue)).decode('utf-8')

# keeps this focused behavior isolated so regressions remain immediately visible
def ReadDirMeta(BlobInfo: bytes, Streams: tuple) -> tuple[int, int]:
    EndOffset = len(BlobInfo) - 22
    DiskNumber, DirectoryDisk, DiskEntries, TotalEntries, DirectorySize, DirectoryOffset, CommentSize = StructLib.unpack_from('<HHHHIIH', BlobInfo, EndOffset + 4)
    assert BlobInfo[EndOffset:EndOffset + 4] == KSignatureA
    assert (DiskNumber, DirectoryDisk, DiskEntries, TotalEntries, CommentSize) == (0, 0, len(Streams), len(Streams), 0)
    assert 8 + DirectoryOffset + DirectorySize == EndOffset
    return (8 + DirectoryOffset, EndOffset)

# keeps this focused behavior isolated so regressions remain immediately visible
def AssertDirEntry(BlobInfo: bytes, Archive, Cursor: int, ExpectedName: str, ExpectedData: bytes) -> tuple[int, int]:
    assert BlobInfo[Cursor:Cursor + 4] == KSignature
    assert BlobInfo[Cursor + 6:Cursor + 12] == KMarker
    TypeId, CrcThreeTwoValue, CompressedSize, SizeInfo = StructLib.unpack_from('<IIII', BlobInfo, Cursor + 12)
    NameSize, ExtraSize = StructLib.unpack_from('<HH', BlobInfo, Cursor + 28)
    EntryCommentSize, EntryDisk, InternalAttributes, ExternalAttributes, LocalOffset = StructLib.unpack_from('<HHHII', BlobInfo, Cursor + 32)
    EncodedName = BlobInfo[Cursor + 46:Cursor + 46 + NameSize]
    assert DecodedName(EncodedName) == ExpectedName
    assert (ExtraSize, EntryCommentSize, EntryDisk, ExternalAttributes) == (0, 0, 0, 0)
    assert InternalAttributes == int(ExpectedName.startswith('swXmlContents/'))
    LocalCursor = 8 + LocalOffset
    assert BlobInfo[LocalCursor:LocalCursor + 4] == KSignatureB
    assert BlobInfo[LocalCursor + 4:LocalCursor + 10] == KMarker
    assert StructLib.unpack_from('<IIII', BlobInfo, LocalCursor + 10) == (TypeId, CrcThreeTwoValue, CompressedSize, SizeInfo)
    assert StructLib.unpack_from('<HH', BlobInfo, LocalCursor + 26) == (NameSize, 0)
    assert DecodedName(BlobInfo[LocalCursor + 30:LocalCursor + 30 + NameSize]) == ExpectedName
    assert Archive.require(ExpectedName) == ExpectedData
    return (Cursor + 46 + NameSize, TypeId)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCHCND() -> None:
    Streams = (('Contents/Config-0-Partition', b'PS\x00\x00native body'), ('swXmlContents/KeyWords', b"<?xml version='1.0'?><KeyWords/>"), ('Contents/OleItems', b''))
    BlobInfo = BuildSldprt(Streams, file_id=KIdInfo, signatures=KSignatures)
    Archive = SldprtArchive.from_bytes(BlobInfo)
    assert Archive.file_id == KIdInfo
    assert Archive.streams == dict(Streams)
    Cursor, EndOffset = ReadDirMeta(BlobInfo, Streams)
    Timestamps = set()
    for ExpectedName, ExpectedData in Streams:
        Cursor, TypeId = AssertDirEntry(BlobInfo, Archive, Cursor, ExpectedName, ExpectedData)
        Timestamps.add(TypeId)
    assert Cursor == EndOffset
    assert Timestamps == {473223809}

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCID() -> None:
    Streams = {'Contents/SolidWorks': b'<swSolidWorks/>', 'Contents/Config-0-Partition': b'PS\x00\x00body'}
    assert BuildSldprt(Streams) == BuildSldprt(Streams)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCUCSLI() -> None:
    BlobInfo = BuildSldprt({'Contents/SolidWorks': b'<swSolidWorks/>'})
    assert BlobInfo[:8] == bytes.fromhex('ec6e238600000004')
    Archive = SldprtArchive.from_bytes(BlobInfo)
    RecordInfo = Archive.records[0]
    assert BlobInfo[RecordInfo.offset - 4:RecordInfo.offset] == bytes.fromhex('64d80045')
    assert BlobInfo[-22:-18] == bytes.fromhex('54ce179a')

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCUNHSTI() -> None:
    BlobInfo = BuildSldprt({'Header2': b'header', 'Preview': b'preview', 'Contents/SolidWorks': b'model'})
    Archive = SldprtArchive.from_bytes(BlobInfo)
    TypeIds = {RecordInfo.name: StructLib.unpack_from('<I', BlobInfo, RecordInfo.offset + 6)[0] for RecordInfo in Archive.records}
    assert TypeIds == {'Header2': 477418028, 'Preview': 477418028, 'Contents/SolidWorks': 473223809}

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCSVSSAC() -> None:
    Streams = {'Contents/SolidWorks': b'<swSolidWorks/>' + b'x' * 4096, 'ThirdPty/KitData': bytes(range(256)) * 3, 'swXmlContents/KeyWords': b'<KeyWords/>' + b'y' * 127}
    BlobInfo = BuildSldprt(Streams)
    assert SldprtArchive.from_bytes(BlobInfo).streams == Streams

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCRTI() -> None:
    Template = BuildSldprt({'Contents/SolidWorks': b'<swSolidWorks/>'}, file_id=KIdInfo, signatures=KSignatures)
    assert ContainerSignatures(Template) == KSignatures
    Streams = {'Contents/SolidWorks': b"<swSolidWorks version='2'/>", 'ThirdPty/KitData': b'kit'}
    BlobInfo = BuildSldprt(Streams, template=Template)
    assert BlobInfo[:4] == Template[:4]
    assert BlobInfo[8:12] == Template[8:12]
    assert BlobInfo[-22:-18] == Template[-22:-18]
    assert SldprtArchive.from_bytes(BlobInfo).streams == Streams

# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCRUFI() -> None:
    with PytestLib.raises(ValueError, match='native template'):
        BuildSldprt({'Contents/SolidWorks': b'<swSolidWorks/>'}, file_id=1)
