# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass
from pathlib import Path as FilePath
import struct as Struct
from typing import Iterable, Mapping
import zlib as ZlibValue
from convert.adapters.solidworks.container.Format import CONTENT_TYPES_STREAM as ContentTypesStream, CONTAINER_VERSIONS as ContainerVersions, RELATIONSHIPS_STREAM as RelationshipsStream

# this binding exists because shared behavior needs one stable value
KLocalSignaturePrefix = bytes.fromhex('140006000800')

# this binding exists because shared behavior needs one stable value
KLocalSignatureSize = 10

# this binding exists because shared behavior needs one stable value
KDefaultFileIdA = 3966641030

# this binding exists because shared behavior needs one stable value
KDefaultTypeId = 473223809

# this binding exists because shared behavior needs one stable value
KTypeIdsByName = {'Header2': 477418028, 'Preview': 477418028}

# this binding exists because shared behavior needs one stable value
KDefaultFileId = KDefaultFileIdA

# this binding exists because shared behavior needs one stable value
KDefaultSignatures = (bytes.fromhex('64d80045'), bytes.fromhex('ae0d4ef6'), bytes.fromhex('54ce179a'))

# this binding exists because shared behavior needs one stable value
KArchiveOffset = 8

# this binding exists because shared behavior needs one stable value
KMaxStreamCount = 100000

# this binding exists because shared behavior needs one stable value
KMaxFolderStreamCount = 65535

# this binding exists because shared behavior needs one stable value
KMaxNameBytes = 16384

# this binding exists because shared behavior needs one stable value
KMaxUncompressedStream = 1 << 31

# this binding exists because shared behavior needs one stable value
KMaxArchiveOffset = 4294967295

# this definition exists because focused behavior needs one stable owner
class SldprtFormat(ValueError):
    KSlots = ()

# this definition exists because focused behavior needs one stable owner
def Signature(FileId: int) -> tuple[bytes, bytes, bytes] | None:
    if FileId == KDefaultFileId:
        return KDefaultSignatures
    return None

# this definition exists because focused behavior needs one stable owner
def Container(BlobValue: bytes | bytearray) -> tuple[bytes, bytes, bytes]:
    DataValue = bytes(BlobValue)
    Signatures, Ignored = TemplateFields(DataValue, SldprtArchive.from_bytes(DataValue))
    return Signatures

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class StreamRecord:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['data'] = 'bytes'
    __annotations__['offset'] = 'int'
    __annotations__['payload_offset'] = 'int'
    __annotations__['compressed_size'] = 'int'
    __annotations__['uncompressed_size'] = 'int'
    __annotations__['crc32'] = 'int'
    __annotations__['signature'] = 'bytes'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class SldprtArchive:
    locals().setdefault('__annotations__', {})
    __annotations__['path'] = 'Path'
    __annotations__['file_id'] = 'int'
    __annotations__['format_version'] = 'int'
    __annotations__['records'] = 'tuple[StreamRecord, ...]'

    # this definition exists because focused behavior needs one stable owner
    @classmethod
    def OpenAction(ClassType, SourcePath: str | FilePath) -> SldprtArchive:
        return OpenArchive(ClassType, SourcePath)

    # this definition exists because focused behavior needs one stable owner
    @classmethod
    def FromBytes(ClassType, BlobValue: bytes | bytearray, SourcePath: str | FilePath='<memory>') -> SldprtArchive:
        return ParseArchive(ClassType, BlobValue, SourcePath)

    # this definition exists because focused behavior needs one stable owner
    @property
    def Streams(Instance) -> dict[str, bytes]:
        return {Record.name: Record.data for Record in Instance.records}

    # this definition exists because focused behavior needs one stable owner
    def GetAction(Instance, NameValue: str) -> bytes | None:
        return next((Record.data for Record in Instance.records if Record.name == NameValue), None)

    # this definition exists because focused behavior needs one stable owner
    def Require(Instance, NameValue: str) -> bytes:
        DataValue = Instance.get(NameValue)
        if DataValue is None:
            raise SldprtFormat(f'required stream is missing: {NameValue}')
        return DataValue
    locals()['from_bytes'] = FromBytes
    locals()['get'] = GetAction
    locals()['open'] = OpenAction
    locals()['require'] = Require
    locals()['streams'] = Streams

# this definition exists because archive loading needs one filesystem boundary
def OpenArchive(ClassType, SourcePath: str | FilePath) -> SldprtArchive:
    Source = FilePath(SourcePath).expanduser().resolve()
    try:
        BlobValue = Source.read_bytes()
    except OSError as ErrorInfo:
        raise SldprtFormat(f'cannot read {Source}: {ErrorInfo}') from ErrorInfo
    return ClassType.from_bytes(BlobValue, Source)

# this definition exists because archive parsing needs one validated construction boundary
def ParseArchive(ClassType, BlobValue: bytes | bytearray, SourcePath: str | FilePath='<memory>') -> SldprtArchive:
    Source = FilePath(SourcePath)
    DataValue = bytes(BlobValue)
    if len(DataValue) < 8:
        raise SldprtFormat('file is too short to contain an SLDPRT header')
    FileId, FormatVersion = Struct.unpack_from('>II', DataValue, 0)
    if FormatVersion not in ContainerVersions:
        raise SldprtFormat(f'unsupported SLDPRT container version {FormatVersion}')
    Records = ScanRecords(DataValue)
    return ClassType(Source, FileId, FormatVersion, Records)

# this definition exists because focused behavior needs one stable owner
def BuildSldprt(Streams: Mapping[str, bytes] | Iterable[tuple[str, bytes]], *, FileId: int | None=None, FormatVersion: int=4, Template: bytes | bytearray | None=None, Signatures: tuple[bytes, bytes, bytes] | None=None, **Options: object) -> bytes:
    FileId = Options.pop('file_id', FileId)
    FormatVersion = Options.pop('format_version', FormatVersion)
    Template = Options.pop('template', Template)
    Signatures = Options.pop('signatures', Signatures)
    if Options:
        Unknown = next(iter(Options))
        raise TypeError(f"BuildSldprt() got an unexpected keyword argument '{Unknown}'")
    FileId, SignatureSet, TypeIds = ResolveBuild(FileId, Template, Signatures)
    if not 0 <= FileId <= 4294967295:
        raise ValueError('SLDPRT file id must fit in 32 bits')
    if FormatVersion not in ContainerVersions:
        raise ValueError('SLDPRT container version must be 3 or 4')
    Items = list(Streams.items() if isinstance(Streams, Mapping) else Streams)
    ValidateStreams(Items)
    return EmitSldprt(Items, FileId, FormatVersion, SignatureSet, TypeIds)

# this definition exists because build configuration needs one validation boundary
def ResolveBuild(FileId: int | None, Template: bytes | bytearray | None, Signatures: tuple[bytes, bytes, bytes] | None) -> tuple[int, tuple[bytes, bytes, bytes], dict[str, int]]:
    TypeIds: dict[str, int] = {}
    if Template is not None and Signatures is not None:
        raise ValueError('SLDPRT signatures cannot be given alongside a template')
    if Template is None and Signatures is not None:
        if len(Signatures) != 3 or any((len(Value) != 4 for Value in Signatures)):
            raise ValueError('SLDPRT signatures must be three four byte values')
        if FileId is None:
            raise ValueError('SLDPRT signatures require the paired file id')
        Signatures = tuple((bytes(Value) for Value in Signatures))
    elif Template is None:
        if FileId is None:
            FileId = KDefaultFileId
        Signatures = Signature(FileId)
        if Signatures is None:
            raise ValueError('SLDPRT file id has no known container signatures; a native template with matching signatures is required')
    else:
        TemplateData = bytes(Template)
        Archive = SldprtArchive.from_bytes(TemplateData)
        if FileId is None:
            FileId = Archive.file_id
        elif FileId != Archive.file_id:
            raise ValueError('SLDPRT template file id does not match the requested file id')
        Signatures, TypeIds = TemplateFields(TemplateData, Archive)
    return (FileId, Signatures, TypeIds)

# this definition exists because stream validation must precede any emitted bytes
def ValidateStreams(Items: list[tuple[str, bytes]]) -> None:
    Names = [NameValue for NameValue, Ignored in Items]
    if len(Names) != len(set(Names)):
        raise ValueError('SLDPRT stream names must be unique')
    if len(Items) > KMaxFolderStreamCount:
        raise ValueError('SLDPRT stream count must fit in the native directory')

# this definition exists because local record emission is separate from directory finalization
def EmitSldprt(Items: list[tuple[str, bytes]], FileId: int, FormatVersion: int, Signatures: tuple[bytes, bytes, bytes], TypeIds: dict[str, int]) -> bytes:
    LocalSignature, CentralSignature, EndBytes = Signatures
    Output = bytearray(Struct.pack('>II', FileId, FormatVersion))
    Encoded: list[tuple[int, str, int, int, int, int]] = []
    for NameValue, Payload in Items:
        TypeId = TypeIds.get(NameValue, KTypeIdsByName.get(NameValue, KDefaultTypeId))
        DataValue = bytes(Payload)
        LocalOffset = len(Output) - KArchiveOffset
        Record, CrcThreeTwoValue, CompressedSize = EncodeRecord(NameValue, DataValue, TypeId)
        Output.extend(LocalSignature)
        Output.extend(Record)
        Encoded.append((TypeId, NameValue, CrcThreeTwoValue, CompressedSize, len(DataValue), LocalOffset))
    return FinishArcMut(Output, Encoded, CentralSignature, EndBytes)

# this definition exists because directory finalization enforces native offset bounds centrally
def FinishArcMut(Output: bytearray, Encoded: list[tuple[int, str, int, int, int, int]], CentralSignature: bytes, EndBytes: bytes) -> bytes:
    CentralOffset = len(Output) - KArchiveOffset
    if CentralOffset > KMaxArchiveOffset:
        raise ValueError('SLDPRT local records exceed the native offset range')
    for Record in Encoded:
        Output.extend(EncodeFolder(*Record, CentralSignature))
    CentralSize = len(Output) - KArchiveOffset - CentralOffset
    if CentralSize > KMaxArchiveOffset:
        raise ValueError('SLDPRT directory exceeds the native size range')
    Output.extend(EndBytes)
    Output.extend(Struct.pack('<HHHHIIH', 0, 0, len(Encoded), len(Encoded), CentralSize, CentralOffset, 0))
    return bytes(Output)

# this definition exists because focused behavior needs one stable owner
def ScanRecords(BlobValue: bytes) -> tuple[StreamRecord, ...]:
    Candidates: list[StreamRecord] = []
    Cursor = 0
    while True:
        Offset = BlobValue.find(KLocalSignaturePrefix, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        SignatureEnd = Offset + KLocalSignatureSize
        if SignatureEnd > len(BlobValue):
            continue
        Signature = BlobValue[Offset:SignatureEnd]
        Record = DecodeScanned(BlobValue, Offset, Signature)
        if Record is None:
            continue
        Candidates.append(Record)
        if len(Candidates) > KMaxStreamCount:
            raise SldprtFormat('unreasonable number of streams')
    if not Candidates:
        raise SldprtFormat('no valid compressed SLDPRT streams were found')
    return UniqueRecMut(Candidates)

# this definition exists because duplicate stream arbitration is independent from record scanning
def UniqueRecMut(Candidates: list[StreamRecord]) -> tuple[StreamRecord, ...]:

    # this callback exists because local behavior needs one focused transformation
    Candidates.sort(key=lambda Record: Record.offset)
    Records: list[StreamRecord] = []
    ByName: dict[str, StreamRecord] = {}
    for Choice in Candidates:
        Prior = ByName.get(Choice.name)
        if Prior is None:
            ByName[Choice.name] = Choice
            Records.append(Choice)
            continue
        SameValue = Prior.crc32 == Choice.crc32 and Prior.uncompressed_size == Choice.uncompressed_size and (Prior.data == Choice.data)
        if not SameValue:
            raise SldprtFormat(f'ambiguous valid stream records for {Choice.name!r}')
    return tuple(Records)

# this definition exists because focused behavior needs one stable owner
def DecodeScanned(BlobValue: bytes, Offset: int, Signature: bytes) -> StreamRecord | None:
    HeaderOffset = Offset + len(Signature)
    if HeaderOffset + 16 > len(BlobValue):
        return None
    CrcThreeTwoValue, CompressedSize, UncompressedSize, NameSize = Struct.unpack_from('<IIII', BlobValue, HeaderOffset)
    if not 0 < NameSize <= KMaxNameBytes:
        return None
    if not 0 <= UncompressedSize <= KMaxUncompressedStream:
        return None
    NameOffset = HeaderOffset + 16
    PayloadOffset = NameOffset + NameSize
    PayloadEnd = PayloadOffset + CompressedSize
    if PayloadEnd > len(BlobValue):
        return None
    try:
        NameValue = NibbleSwap(BlobValue[NameOffset:PayloadOffset]).decode('utf-8')
    except UnicodeDecodeError:
        return None
    if not NameValue or any((ord(Character) < 32 for Character in NameValue)):
        return None
    try:
        DataValue = ZlibValue.decompress(BlobValue[PayloadOffset:PayloadEnd], wbits=-15)
    except ZlibValue.error:
        return None
    if len(DataValue) != UncompressedSize:
        return None
    if ZlibValue.crc32(DataValue) & 4294967295 != CrcThreeTwoValue:
        return None
    return StreamRecord(name=NameValue, data=DataValue, offset=Offset, payload_offset=PayloadOffset, compressed_size=CompressedSize, uncompressed_size=UncompressedSize, crc32=CrcThreeTwoValue, signature=Signature)

# this definition exists because focused behavior needs one stable owner
def NibbleSwap(DataValue: bytes) -> bytes:
    return bytes((Value >> 4 | (Value & 15) << 4 for Value in DataValue))

# this definition exists because focused behavior needs one stable owner
def EncodedName(NameValue: str) -> bytes:
    if not NameValue or any((ord(Character) < 32 for Character in NameValue)):
        raise ValueError('SLDPRT stream name must contain printable characters')
    Value = NameValue.encode('utf-8')
    if len(Value) > KMaxNameBytes:
        raise ValueError('SLDPRT stream name is too long')
    return NibbleSwap(Value)

# this definition exists because focused behavior needs one stable owner
def EncodeRecord(NameValue: str, DataValue: bytes, TypeId: int) -> tuple[bytes, int, int]:
    if len(DataValue) > KMaxUncompressedStream:
        raise ValueError('SLDPRT stream is too large')
    Compressor = ZlibValue.compressobj(level=1, wbits=-15)
    Compressed = Compressor.compress(DataValue) + Compressor.flush()
    EncodedBytes = EncodedName(NameValue)
    CrcThreeTwoValue = ZlibValue.crc32(DataValue) & 4294967295
    Record = b''.join((KLocalSignaturePrefix, Struct.pack('<I', TypeId), Struct.pack('<IIIHH', CrcThreeTwoValue, len(Compressed), len(DataValue), len(EncodedBytes), 0), EncodedBytes, Compressed))
    return (Record, CrcThreeTwoValue, len(Compressed))

# this definition exists because focused behavior needs one stable owner
def EncodeFolder(TypeId: int, NameValue: str, CrcThreeTwoValue: int, CompressedSize: int, SizeValue: int, LocalOffset: int, Signature: bytes) -> bytes:
    EncodedBytes = EncodedName(NameValue)
    PackageSection = int(NameValue == ContentTypesStream or NameValue == RelationshipsStream or NameValue.startswith('docProps/') or NameValue.startswith('swXmlContents/'))
    return b''.join((Signature, Struct.pack('<H', 0), KLocalSignaturePrefix, Struct.pack('<I', TypeId), Struct.pack('<IIIHH', CrcThreeTwoValue, CompressedSize, SizeValue, len(EncodedBytes), 0), Struct.pack('<HHHII', 0, 0, PackageSection, 0, LocalOffset), EncodedBytes))

# this definition exists because focused behavior needs one stable owner
def TemplateFields(BlobValue: bytes, Archive: SldprtArchive) -> tuple[tuple[bytes, bytes, bytes], dict[str, int]]:

    # this callback exists because local behavior needs one focused transformation
    Records = tuple(sorted(Archive.records, key=lambda ItemValue: ItemValue.offset))
    LocalSignatures = {BlobValue[ItemValue.offset - 4:ItemValue.offset] for ItemValue in Records}
    if len(LocalSignatures) != 1 or any((len(Value) != 4 for Value in LocalSignatures)):
        raise ValueError('SLDPRT template has inconsistent local signatures')
    Expected = {(ItemValue.name, ItemValue.crc32, ItemValue.compressed_size, ItemValue.uncompressed_size) for ItemValue in Records}
    CentralMarkers = CentralMarks(BlobValue, Records, Expected)
    if len(CentralMarkers) != len(Records):
        raise ValueError('SLDPRT template central directory is incomplete')
    CentralSignatures = {BlobValue[Marker - 6:Marker - 2] for Marker in CentralMarkers if BlobValue[Marker - 2:Marker] == b'\x00\x00'}
    if len(CentralSignatures) != 1:
        raise ValueError('SLDPRT template has inconsistent central signatures')
    CentralStart = CentralMarkers[0] - 6
    EndBytes = EndSignature(BlobValue, CentralStart, len(Records))
    TypeIds = {ItemValue.name: Struct.unpack_from('<I', ItemValue.signature, 6)[0] for ItemValue in Records}
    return ((next(iter(LocalSignatures)), next(iter(CentralSignatures)), EndBytes), TypeIds)

# this definition exists because central directory discovery needs isolated candidate filtering
def CentralMarks(BlobValue: bytes, Records: tuple[StreamRecord, ...], Expected: set[tuple[str, int, int, int]]) -> list[int]:
    CentralMarkers: list[int] = []
    Cursor = max((ItemValue.payload_offset + ItemValue.compressed_size for ItemValue in Records))
    while True:
        Marker = BlobValue.find(KLocalSignaturePrefix, Cursor)
        if Marker < 0:
            break
        Cursor = Marker + 1
        if Marker + 40 > len(BlobValue):
            continue
        CrcThreeTwoValue, CompressedSize, SizeValue, NameSize = Struct.unpack_from('<IIII', BlobValue, Marker + 10)
        if not 0 < NameSize <= KMaxNameBytes:
            continue
        NameStart = Marker + 40
        NameEnd = NameStart + NameSize
        if NameEnd > len(BlobValue):
            continue
        try:
            NameValue = NibbleSwap(BlobValue[NameStart:NameEnd]).decode('utf-8')
        except UnicodeDecodeError:
            continue
        if (NameValue, CrcThreeTwoValue, CompressedSize, SizeValue) in Expected:
            CentralMarkers.append(Marker)
    return CentralMarkers

# this definition exists because focused behavior needs one stable owner
def EndSignature(BlobValue: bytes, CentralStart: int, Count: int) -> bytes:
    CentralOffset = CentralStart - KArchiveOffset
    for Offset in range(CentralStart, len(BlobValue) - 21):
        DiskNumber, FolderDisk, DiskEntries, TotalEntries, FolderSize, FolderOffset, CommentSize = Struct.unpack_from('<HHHHIIH', BlobValue, Offset + 4)
        if DiskNumber == 0 and FolderDisk == 0 and (DiskEntries == Count) and (TotalEntries == Count) and (FolderOffset == CentralOffset) and (KArchiveOffset + FolderOffset + FolderSize == Offset) and (Offset + 22 + CommentSize <= len(BlobValue)):
            return BlobValue[Offset:Offset + 4]
    raise ValueError('SLDPRT template end directory is missing')

# this binding exists because shared behavior needs one stable value
globals()['CONTAINER_VERSIONS'] = ContainerVersions

# this binding exists because shared behavior needs one stable value
globals()['CONTENT_TYPES_STREAM'] = ContentTypesStream

# this binding exists because shared behavior needs one stable value
globals()['DEFAULT_FILE_ID'] = KDefaultFileId

# this binding exists because shared behavior needs one stable value
globals()['DEFAULT_SIGNATURES'] = KDefaultSignatures

# this binding exists because shared behavior needs one stable value
globals()['Path'] = FilePath

# this binding exists because shared behavior needs one stable value
globals()['RELATIONSHIPS_STREAM'] = RelationshipsStream

# this binding exists because shared behavior needs one stable value
globals()['SldprtFormatError'] = SldprtFormat

# this binding exists because shared behavior needs one stable value
globals()['_ARCHIVE_OFFSET'] = KArchiveOffset

# this binding exists because shared behavior needs one stable value
globals()['_DEFAULT_FILE_ID'] = KDefaultFileIdA

# this binding exists because shared behavior needs one stable value
globals()['_DEFAULT_TYPE_ID'] = KDefaultTypeId

# this binding exists because shared behavior needs one stable value
globals()['_LOCAL_SIGNATURE_PREFIX'] = KLocalSignaturePrefix

# this binding exists because shared behavior needs one stable value
globals()['_LOCAL_SIGNATURE_SIZE'] = KLocalSignatureSize

# this binding exists because shared behavior needs one stable value
globals()['_MAX_ARCHIVE_OFFSET'] = KMaxArchiveOffset

# this binding exists because shared behavior needs one stable value
globals()['_MAX_DIRECTORY_STREAM_COUNT'] = KMaxFolderStreamCount

# this binding exists because shared behavior needs one stable value
globals()['_MAX_NAME_BYTES'] = KMaxNameBytes

# this binding exists because shared behavior needs one stable value
globals()['_MAX_STREAM_COUNT'] = KMaxStreamCount

# this binding exists because shared behavior needs one stable value
globals()['_MAX_UNCOMPRESSED_STREAM'] = KMaxUncompressedStream

# this binding exists because shared behavior needs one stable value
globals()['_TYPE_IDS_BY_NAME'] = KTypeIdsByName

# this binding exists because shared behavior needs one stable value
globals()['_decode_scanned_candidate'] = DecodeScanned

# this binding exists because shared behavior needs one stable value
globals()['_encode_directory_entry'] = EncodeFolder

# this binding exists because shared behavior needs one stable value
globals()['_encode_record'] = EncodeRecord

# this binding exists because shared behavior needs one stable value
globals()['_encoded_name'] = EncodedName

# this binding exists because shared behavior needs one stable value
globals()['_end_signature'] = EndSignature

# this binding exists because shared behavior needs one stable value
globals()['_nibble_swap'] = NibbleSwap

# this binding exists because shared behavior needs one stable value
globals()['_scan_records'] = ScanRecords

# this binding exists because shared behavior needs one stable value
globals()['_template_fields'] = TemplateFields

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['build_sldprt'] = BuildSldprt

# this binding exists because shared behavior needs one stable value
globals()['container_signatures'] = Container

# this binding exists because shared behavior needs one stable value
globals()['dataclass'] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()['signature_triplet'] = Signature

# this binding exists because shared behavior needs one stable value
globals()['struct'] = Struct

# this binding exists because shared behavior needs one stable value
globals()['zlib'] = ZlibValue
