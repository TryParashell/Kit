# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from collections.abc import Mapping, Sequence
import json as JsonLib
from pathlib import Path as FilePath
import struct as StructLib
from typing import TypedDict
import pytest as PytestLib
from convert.adapters.solidworks.container.Archive import (
    BIG_CLASS_TAG_BIT as BitInfo,
    BIG_OBJECT_TAG as TagInfo,
    CLASS_REFERENCE_KIND as KindInfo,
    CLASS_TAG_BIT as BitInfoA,
    ClassLayout,
    DEFINITION_KIND as KindInfoA,
    IsLayoutObject,
    IsLayoutSequence,
    LayoutObject,
    LayoutTable,
    LayoutValue,
    Model,
    NULL_KIND as KindInfoB,
    NULL_TAG as TagInfoA,
    Node as NodeInfo,
    OBJECT_REFERENCE_KIND as KindInfoC,
    STREAM_HEADER_SIZE as SizeInfo,
    SegmentationError,
    StaticSegment,
    ArchiveError,
    build_model as BuildModel,
    container_mo_version as ContainerMoVersion,
    encode_class_definition as EncodeClassDefinition,
    encode_class_reference as EncodeClassReference,
    encode_null as EncodeNull,
    encode_object_reference as EncodeObjectReference,
    encode_string as EncodeString,
    implied_bases as ImpliedBases,
    read_string as ReadString,
    read_tag as ReadTag,
    resolve_base as ResolveBase,
    segment as Segment,
    verify as Verify,
)
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    RESOLVED_FEATURES_STREAM as Stream,
)
from tests.convert.solidworks.core.SolidworksDonorVersion import GetDonorVer


# preserves recorded archive segmentation with fields required by reconstruction checks
class SegmentRecord(TypedDict):
    index: int
    offset: int
    header: int
    end: int
    kind: str
    tag: int
    class_name: str
    class_index: int
    object_index: int
    depth: int
    parent: int
    map_index: int


# keeps recorded fixture metadata concrete after untyped json decoding
class RecordedArchive(TypedDict):
    part: str
    stream_length: int
    base_map_index: int
    object_count: int
    segments: list[SegmentRecord]


# centralizes shared evidence so every related assertion uses one value
KRootInfo = FilePath(__file__).parents[4]

# centralizes shared evidence so every related assertion uses one value
KLayouts = KRootInfo / "re" / "data" / "Layouts" / "ClassLayouts.json"

# centralizes shared evidence so every related assertion uses one value
KSegments = KRootInfo / "re" / "data" / "segments"

# centralizes shared evidence so every related assertion uses one value
KDonors = KRootInfo / "examples" / "Fixtures" / "SolidWorks" / "donors"

# centralizes shared evidence so every related assertion uses one value
KLabels = (
    "baseline",
    "circle",
    "cutbase",
    "padplane",
    "planetop",
    "three",
    "twopad",
    "vendor_cojinete",
    "vendor_ring",
)

# centralizes shared evidence so every related assertion uses one value
KIdentically = 17

# centralizes shared evidence so every related assertion uses one value
KFloor = 54

# centralizes shared evidence so every related assertion uses one value
KFloorA = 18761

# centralizes shared evidence so every related assertion uses one value
KSeedInfo = 109


# keeps this focused behavior isolated so regressions remain immediately visible
def Layouts() -> LayoutTable:
    return LayoutTable.load(KLayouts)


# rejects malformed recorded json before fixture reconstruction consumes its fields
def RecordedString(Payload: LayoutObject, KeyValue: str) -> str:
    Value = Payload.get(KeyValue)
    if not isinstance(Value, str):
        raise TypeError(f"recorded archive field {KeyValue!r} must be a string")
    return Value


# rejects malformed recorded json before numeric offsets enter archive operations
def RecordedInteger(Payload: LayoutObject, KeyValue: str) -> int:
    Value = Payload.get(KeyValue)
    if not isinstance(Value, int) or isinstance(Value, bool):
        raise TypeError(f"recorded archive field {KeyValue!r} must be an integer")
    return Value


# converts each json segment into the concrete record used by static reconstruction
def RecordedSegment(Value: LayoutValue) -> SegmentRecord:
    if not IsLayoutObject(Value):
        raise TypeError("recorded archive segment must be an object")
    return {
        "index": RecordedInteger(Value, "index"),
        "offset": RecordedInteger(Value, "offset"),
        "header": RecordedInteger(Value, "header"),
        "end": RecordedInteger(Value, "end"),
        "kind": RecordedString(Value, "kind"),
        "tag": RecordedInteger(Value, "tag"),
        "class_name": RecordedString(Value, "class_name"),
        "class_index": RecordedInteger(Value, "class_index"),
        "object_index": RecordedInteger(Value, "object_index"),
        "depth": RecordedInteger(Value, "depth"),
        "parent": RecordedInteger(Value, "parent"),
        "map_index": RecordedInteger(Value, "map_index"),
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def Recorded(Label: str) -> RecordedArchive:
    TargetPath = KSegments / f"segments_{Label}.json"
    if not TargetPath.is_file():
        PytestLib.skip(f"no recorded segmentation for {Label}")
    RawPayload: object = JsonLib.loads(TargetPath.read_text(encoding="utf-8"))
    if not IsLayoutObject(RawPayload):
        raise TypeError(f"recorded archive {TargetPath} must be a json object")
    RawSegments = RawPayload.get("segments")
    if not IsLayoutSequence(RawSegments):
        raise TypeError(f"recorded archive {TargetPath} must contain a segments list")
    return {
        "part": RecordedString(RawPayload, "part"),
        "stream_length": RecordedInteger(RawPayload, "stream_length"),
        "base_map_index": RecordedInteger(RawPayload, "base_map_index"),
        "object_count": RecordedInteger(RawPayload, "object_count"),
        "segments": [RecordedSegment(Value) for Value in RawSegments],
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def RecordedPart(Payload: RecordedArchive) -> tuple[bytes, int | None]:
    PartDoc = FilePath(Payload["part"])
    if not PartDoc.is_file():
        PytestLib.skip(f"traced part {PartDoc} is not present in this checkout")
    Archive = SldprtArchive.from_bytes(PartDoc.read_bytes())
    BlobInfo = Archive.streams[Stream]
    assert len(BlobInfo) == Payload["stream_length"]
    return (BlobInfo, ContainerMoVersion(Archive.streams))


# keeps this focused behavior isolated so regressions remain immediately visible
def AuthoredMV() -> int | None:
    Found: set[int] = set()
    for Label in KLabels:
        if Label.startswith("vendor_"):
            continue
        TargetPath = KSegments / f"segments_{Label}.json"
        if not TargetPath.is_file():
            continue
        PartDoc = FilePath(Recorded(Label)["part"])
        if not PartDoc.is_file():
            continue
        Version = ContainerMoVersion(
            SldprtArchive.from_bytes(PartDoc.read_bytes()).streams
        )
        if Version is not None:
            Found.add(Version)
    if len(Found) != 1:
        return None
    return Found.pop()


# keeps this focused behavior isolated so regressions remain immediately visible
def StaticSegments(
    BlobInfo: bytes, Payload: RecordedArchive
) -> tuple[StaticSegment, ...]:
    RowsInfo: list[StaticSegment] = []
    for ItemValue in Payload["segments"]:
        Offset = ItemValue["offset"]
        Schema = (
            StructLib.unpack_from("<H", BlobInfo, Offset + 2)[0]
            if ItemValue["kind"] == KindInfoA
            else 0
        )
        RowsInfo.append(
            StaticSegment(
                index=ItemValue["index"],
                offset=Offset,
                header=ItemValue["header"],
                end=ItemValue["end"],
                kind=ItemValue["kind"],
                token=ItemValue["tag"],
                wide=False,
                schema=Schema,
                class_name=ItemValue["class_name"],
                class_index=ItemValue["class_index"],
                object_index=ItemValue["object_index"],
                depth=ItemValue["depth"],
                parent=ItemValue["parent"],
            )
        )
    return tuple(RowsInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
def DonorStreams() -> tuple[tuple[str, bytes], ...]:
    RowsInfo: list[tuple[str, bytes]] = []
    for Donor in sorted(KDonors.iterdir()):
        StreamA = Donor / "resolved.bin"
        if StreamA.is_file():
            RowsInfo.append((Donor.name, StreamA.read_bytes()))
    return tuple(RowsInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestRSRTBI(Label: str) -> None:
    Payload = Recorded(Label)
    BlobInfo = RecordedPart(Payload)[0]
    Segments = StaticSegments(BlobInfo, Payload)
    ModelDoc = BuildModel(
        BlobInfo, Segments, Payload["base_map_index"], Segments[0].offset
    )
    assert len(ModelDoc.nodes) == Payload["object_count"]
    assert ModelDoc.emit() == BlobInfo


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestSSAWTRO(Label: str) -> None:
    Payload = Recorded(Label)
    BlobInfo, Version = RecordedPart(Payload)
    LayoutsA = Layouts()
    Expected = [ItemValue["offset"] for ItemValue in Payload["segments"]]
    Header = Payload["segments"][0]["offset"]
    try:
        Produced = Segment(
            BlobInfo,
            Payload["base_map_index"],
            LayoutsA,
            header_size=Header,
            mo_version=Version,
        )
        Reached = [ItemValue.offset for ItemValue in Produced]
    except SegmentationError as Failure:
        Reached = [ItemValue.offset for ItemValue in Failure.reached]
        assert Failure.offset in Expected, (Label, Failure.offset)
    assert Reached
    assert Reached == Expected[: len(Reached)], Label


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestRSMTCR(Label: str) -> None:
    Payload = Recorded(Label)
    BaseInfo = Payload["base_map_index"]
    Counter = BaseInfo
    for ItemValue in Payload["segments"]:
        assert ItemValue["map_index"] == Counter, (Label, ItemValue["offset"])
        if ItemValue["kind"] == KindInfoA:
            Counter += 2
        elif ItemValue["kind"] == KindInfo:
            Counter += 1


# keeps this focused behavior isolated so regressions remain immediately visible
def TestNTRT() -> None:
    Encoded = EncodeNull()
    assert Encoded == b"\x00\x00"
    TagInfoB = ReadTag(Encoded, 0)
    assert TagInfoB.kind == KindInfoB
    assert TagInfoB.size == 2
    assert TagInfoB.token == TagInfoA


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCDTRT() -> None:
    Encoded = EncodeClassDefinition("moExtrusion_c", 1)
    TagInfoB = ReadTag(Encoded, 0)
    assert TagInfoB.kind == KindInfoA
    assert TagInfoB.class_name == "moExtrusion_c"
    assert TagInfoB.schema == 1
    assert TagInfoB.size == len(Encoded)
    assert EncodeClassDefinition(TagInfoB.class_name, TagInfoB.schema) == Encoded


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCDRAEN() -> None:
    with PytestLib.raises(ArchiveError, match="empty name"):
        ReadTag(StructLib.pack("<HHH", 65535, 1, 0), 0)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCRTRT() -> None:
    Encoded = EncodeClassReference(109)
    assert StructLib.unpack_from("<H", Encoded, 0)[0] == BitInfoA | 109
    TagInfoB = ReadTag(Encoded, 0)
    assert TagInfoB.kind == KindInfo
    assert TagInfoB.index == 109
    assert TagInfoB.wide is False
    assert EncodeClassReference(TagInfoB.index, wide=TagInfoB.wide) == Encoded


# keeps this focused behavior isolated so regressions remain immediately visible
def TestORTRT() -> None:
    Encoded = EncodeObjectReference(230)
    TagInfoB = ReadTag(Encoded, 0)
    assert TagInfoB.kind == KindInfoC
    assert TagInfoB.index == 230
    assert TagInfoB.wide is False
    assert EncodeObjectReference(TagInfoB.index, wide=TagInfoB.wide) == Encoded


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBOTERT() -> None:
    Encoded = EncodeObjectReference(TagInfo)
    assert StructLib.unpack_from("<H", Encoded, 0)[0] == TagInfo
    assert StructLib.unpack_from("<I", Encoded, 2)[0] == TagInfo
    TagInfoB = ReadTag(Encoded, 0)
    assert TagInfoB.kind == KindInfoC
    assert TagInfoB.wide is True
    assert TagInfoB.index == TagInfo
    assert TagInfoB.size == 6
    assert EncodeObjectReference(TagInfoB.index, wide=True) == Encoded


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCTERT() -> None:
    Encoded = EncodeClassReference(74565)
    assert StructLib.unpack_from("<I", Encoded, 2)[0] == 74565 | BitInfo
    TagInfoB = ReadTag(Encoded, 0)
    assert TagInfoB.kind == KindInfo
    assert TagInfoB.wide is True
    assert TagInfoB.index == 74565
    assert EncodeClassReference(TagInfoB.index, wide=True) == Encoded


# keeps this focused behavior isolated so regressions remain immediately visible
def TestNIMBFW() -> None:
    Encoded = EncodeClassReference(7, wide=True)
    assert len(Encoded) == 6
    TagInfoB = ReadTag(Encoded, 0)
    assert TagInfoB.index == 7
    assert TagInfoB.wide is True


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSSRT() -> None:
    Encoded = EncodeString("Boss-Extrude1")
    assert Encoded[:3] == b"\xff\xfe\xff"
    assert Encoded[3] == 13
    TextInfo, Consumed = ReadString(Encoded, 0)
    assert TextInfo == "Boss-Extrude1"
    assert Consumed == len(Encoded)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestLSRT() -> None:
    TextInfo = "n" * 300
    Encoded = EncodeString(TextInfo)
    assert Encoded[:4] == b"\xff\xfe\xff\xff"
    assert StructLib.unpack_from("<H", Encoded, 4)[0] == 300
    Decoded, Consumed = ReadString(Encoded, 0)
    assert Decoded == TextInfo
    assert Consumed == len(Encoded)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestESRT() -> None:
    Encoded = EncodeString("")
    assert Encoded == b"\xff\xfe\xff\x00"
    assert ReadString(Encoded, 0) == ("", 4)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAASUTNSALP() -> None:
    assert ReadString(b"\x00", 0) == ("", 1)
    assert ReadString(b"\x03abc", 0) == ("abc", 4)
    Encoded = b"\xff,\x01" + b"n" * 300
    assert ReadString(Encoded, 0) == ("n" * 300, len(Encoded))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestUASUTNELP() -> None:
    TextInfo = "n" * 65534
    Encoded = EncodeString(TextInfo)
    assert Encoded[:10] == b"\xff\xfe\xff\xff\xff\xff\xfe\xff\x00\x00"
    assert ReadString(Encoded, 0) == (TextInfo, len(Encoded))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestUVRIOT() -> None:
    with PytestLib.raises(ArchiveError):
        EncodeClassDefinition("cläss", 1)
    with PytestLib.raises(ArchiveError):
        EncodeClassDefinition("", 1)
    with PytestLib.raises(ArchiveError):
        EncodeObjectReference(-1)
    with PytestLib.raises(ArchiveError):
        EncodeClassReference(1073741824)
    with PytestLib.raises(ArchiveError):
        ReadTag(b"\xff\xff\x01", 0)
    with PytestLib.raises(ArchiveError):
        ReadString(b"\x04\x01", 0)
    assert issubclass(ArchiveError, SldprtFormatError)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCRAIFTB() -> None:
    ModelDoc = Model(header=b"\x00" * SizeInfo, base=109)
    ModelDoc.nodes.append(
        NodeInfo(kind=KindInfoA, body=b"\x01\x00\x00\x00", class_name="alpha")
    )
    ModelDoc.nodes.append(NodeInfo(kind=KindInfoB, body=b""))
    ModelDoc.nodes.append(
        NodeInfo(kind=KindInfoA, body=b"\x02\x00\x00\x00", class_name="beta")
    )
    ModelDoc.nodes.append(NodeInfo(kind=KindInfo, body=b"", target=0))
    ModelDoc.nodes.append(NodeInfo(kind=KindInfoC, body=b"", target=2))
    ModelDoc.assign()
    assert [NodeInfoA.class_index for NodeInfoA in ModelDoc.nodes] == [
        109,
        0,
        111,
        0,
        0,
    ]
    assert [NodeInfoA.object_index for NodeInfoA in ModelDoc.nodes] == [
        110,
        0,
        112,
        113,
        0,
    ]
    Emitted = ModelDoc.emit()
    Expected = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("alpha", 0)
        + b"\x01\x00\x00\x00"
        + EncodeNull()
        + EncodeClassDefinition("beta", 0)
        + b"\x02\x00\x00\x00"
        + EncodeClassReference(109)
        + EncodeObjectReference(112)
    )
    assert Emitted == Expected


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBBTSAL() -> None:
    ModelDoc = Model(header=b"", base=109)
    ModelDoc.nodes.append(NodeInfo(kind=KindInfo, body=b"", literal=4))
    ModelDoc.nodes.append(NodeInfo(kind=KindInfoC, body=b"", literal=2))
    Emitted = ModelDoc.emit()
    assert Emitted == EncodeClassReference(4) + EncodeObjectReference(2)
    assert ModelDoc.nodes[0].object_index == 109


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMRAUNK() -> None:
    ModelDoc = Model(header=b"", base=1)
    ModelDoc.nodes.append(NodeInfo(kind="bogus", body=b""))
    with PytestLib.raises(ArchiveError):
        ModelDoc.emit()


# keeps this focused behavior isolated so regressions remain immediately visible
def SingleCT(Entry: LayoutObject) -> LayoutTable:
    Classes: dict[str, LayoutValue] = {"solo": dict(Entry)}
    return LayoutTable.from_mapping({"version": 1, "classes": Classes})


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSRAOLR() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [
                {"slot": "leaf", "rule": "opaque", "note": "needs a trace"}
            ],
        }
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + b"\x00" * 8
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert Failure.value.class_name == "solo"
    assert Failure.value.slot == "leaf"
    assert Failure.value.offset == SizeInfo
    assert "opaque" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSRAVCC() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": ["*", "..."],
            "runs": {"lead": 0},
            "variable_runs": [
                {
                    "slot": "lead",
                    "rule": "opaque",
                    "note": "child count varies across instances",
                }
            ],
        }
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1)
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert Failure.value.class_name == "solo"
    assert "child count" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSRACWALE() -> None:
    LayoutsA = LayoutTable.from_mapping({"version": 1, "classes": {}})
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1)
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert Failure.value.class_name == "solo"
    assert "no layout entry" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSRARPTEOTS() -> None:
    LayoutsA = SingleCT(
        {"confidence": "confirmed", "child_slots": [], "runs": {"leaf": 64}}
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1)
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert "past" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSRAURAOATB() -> None:
    LayoutsA = SingleCT(
        {"confidence": "confirmed", "child_slots": [], "runs": {"leaf": 0}}
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassReference(120)
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert "no definition has been seen" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestABBCIBFTDS() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["owned"],
                    "runs": {"lead": 0, "0": 0},
                },
                "owned": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 3},
                },
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("parent", 1)
        + EncodeClassReference(42)
        + bytes(range(3))
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.class_name for ItemValue in Segments] == ["parent", "owned"]
    assert Segments[1].class_index == 42
    assert Segments[1].end == len(BlobInfo)
    assert Verify(BlobInfo, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def NamedTABBCIKIAW() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["owned"],
                    "runs": {"lead": 0, "0": 0},
                },
                "owned": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 9},
                },
                "external#42": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 3},
                },
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("parent", 1)
        + EncodeClassReference(42)
        + bytes(range(3))
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.class_name for ItemValue in Segments] == ["parent", "external#42"]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAPSLABBIU() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["*"],
                    "runs": {"lead": 0, "0": 0},
                }
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("parent", 1)
        + EncodeClassReference(42)
    )
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert Failure.value.class_name == "external#42"
    assert "no layout entry" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def BaseRT() -> LayoutTable:
    return LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "first": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 0},
                },
                "second": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 0},
                },
            },
        }
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRBRFAUCR() -> None:
    LayoutsA = BaseRT()
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("first", 1)
        + EncodeClassDefinition("second", 1)
        + EncodeClassReference(203)
        + EncodeClassReference(201)
    )
    Resolution = ResolveBase(BlobInfo, 109, LayoutsA)
    assert Resolution.base == 201
    assert Resolution.segmented
    assert Resolution.seed == 109
    assert 201 in Resolution.implied
    assert Resolution.tried[0] == 109
    assert Verify(BlobInfo, Resolution.base, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRBKASTAS() -> None:
    LayoutsA = BaseRT()
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("first", 1)
        + EncodeClassReference(109)
    )
    Resolution = ResolveBase(BlobInfo, 109, LayoutsA)
    assert Resolution.base == 109
    assert Resolution.tried == (109,)
    assert Resolution.implied == ()
    assert Resolution.segmented


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRBRAUSOL() -> None:
    LayoutsA = BaseRT()
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("first", 1)
    with PytestLib.raises(ArchiveError):
        ResolveBase(BlobInfo, 0, LayoutsA)
    with PytestLib.raises(ArchiveError):
        ResolveBase(BlobInfo, 109, LayoutsA, limit=0)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestIBIAUOR() -> None:
    LayoutsA = BaseRT()
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("first", 1)
        + EncodeObjectReference(18000)
    )
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert Failure.value.unresolved_index == 18000
    assert Failure.value.unresolved_kind == KindInfoC
    assert ImpliedBases(Failure.value, 109) == ()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSTAREASS() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["child", "*"],
                    "runs": {"lead": 4, "0": 2, "1": 6},
                },
                "child": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 8},
                },
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("parent", 1)
        + bytes(range(4))
        + EncodeClassDefinition("child", 1)
        + bytes(range(8))
        + bytes(range(2))
        + EncodeNull()
        + bytes(range(6))
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.class_name for ItemValue in Segments] == [
        "parent",
        "child",
        "null",
    ]
    assert [ItemValue.depth for ItemValue in Segments] == [0, 1, 1]
    assert [ItemValue.parent for ItemValue in Segments] == [-1, 0, 0]
    Report = Verify(BlobInfo, 109, LayoutsA)
    assert Report.segmented
    assert Report.tiled
    assert Report.identical
    assert Report.object_count == 3
    assert Report.definition_count == 2
    assert Report.gaps == ()
    assert Report.overlaps == ()
    assert Report.trailing_bytes == 0


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCCBCSACB() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["child", "*", "known"],
                    "child_count_by_class": {
                        "slot": 0,
                        "counts": {"child": 2, "null": 3},
                    },
                    "runs": {"lead": 0, "0": 0, "2": 0},
                    "runs_by_child_class": {"1": {"null": 0}},
                },
                "child": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 0},
                },
                "known": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 0},
                },
            },
        }
    )
    ShortBlob = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("parent", 1)
        + EncodeClassDefinition("child", 1)
        + EncodeNull()
    )
    LongBlob = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("parent", 1)
        + EncodeNull()
        + EncodeNull()
        + EncodeClassReference(200)
    )
    assert [ItemInfo.class_name for ItemInfo in Segment(ShortBlob, 109, LayoutsA)] == [
        "parent",
        "child",
        "null",
    ]
    assert [ItemInfo.class_name for ItemInfo in Segment(LongBlob, 109, LayoutsA)] == [
        "parent",
        "null",
        "null",
        "known",
    ]
    assert Verify(ShortBlob, 109, LayoutsA).identical
    assert Verify(LongBlob, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSACACRMAR() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [
                {
                    "slot": "leaf",
                    "rule": "count",
                    "at": 2,
                    "count_width": 2,
                    "stride": 4,
                },
                {"slot": "leaf", "rule": "string", "at": 1, "tail": 0},
                {
                    "slot": "leaf",
                    "rule": "conditional",
                    "at": 4,
                    "width": 8,
                    "predicate": "flag",
                    "predicate_at": 0,
                    "predicate_width": 1,
                    "values": [1],
                    "tail": 3,
                },
                {
                    "slot": "leaf",
                    "rule": "guard",
                    "at": 4,
                    "predicate": "variant",
                    "predicate_at": 0,
                    "predicate_width": 4,
                    "values": [305419896],
                },
            ],
        }
    )
    BodyInfo = (
        b"\x00\x00"
        + StructLib.pack("<H", 3)
        + b"\x00" * 12
        + b"\x00"
        + EncodeString("ab")
        + b"\x01\x00\x00\x00"
        + b"\x00" * 8
        + b"\x00" * 3
        + StructLib.pack("<I", 305419896)
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + BodyInfo
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert len(Segments) == 1
    assert Segments[0].end == len(BlobInfo)
    assert Verify(BlobInfo, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCROAAE() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [
                {
                    "slot": "leaf",
                    "rule": "conditional",
                    "at": 1,
                    "width": 16,
                    "predicate": "flag",
                    "predicate_at": 0,
                    "predicate_width": 1,
                    "values": [1],
                    "tail": 2,
                }
            ],
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + b"\x00" + b"\x00\x00"
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert Segments[0].end == len(BlobInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestURCIR() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": ["*"],
            "runs": {"lead": 0, "0": 0},
            "repeat_count": "unresolved",
        }
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1)
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert "child count" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def PrefixTable(
    Prefix: int, TailInfo: Mapping[str, LayoutValue] | None = None
) -> LayoutTable:
    Entry: dict[str, LayoutValue] = {
        "confidence": "partial",
        "child_slots": ["*", "*", "..."],
        "runs": {"lead": 4, "0": 2, "1": 6},
        "repeat_count": None,
        "repeat_prefix": Prefix,
    }
    if TailInfo is not None:
        Entry["variable_runs"] = [dict(TailInfo)]
    return LayoutTable.from_mapping({"version": 1, "classes": {"solo": Entry}})


# keeps this focused behavior isolated so regressions remain immediately visible
def PrefixStream() -> bytes:
    return (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("solo", 1)
        + bytes(range(4))
        + EncodeNull()
        + bytes(range(2))
        + EncodeNull()
        + bytes(range(6))
        + EncodeNull()
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARPWTKCARTT() -> None:
    LayoutsA = PrefixTable(
        2, {"slot": "tail", "rule": "opaque", "note": "the child count is not pinned"}
    )
    Layout = LayoutsA["solo"]
    assert Layout.walks_a_prefix
    assert not Layout.repeats
    assert Layout.run_keys() == ("lead", "0", "tail")
    assert Layout.run_key(0) == "0"
    assert Layout.run_key(1) == "tail"
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(PrefixStream(), 109, LayoutsA)
    assert Failure.value.class_name == "solo"
    assert Failure.value.slot == "tail"
    assert Failure.value.offset == SizeInfo
    assert "not pinned" in str(Failure.value)
    assert [ItemValue.kind for ItemValue in Failure.value.reached] == [
        KindInfoA,
        KindInfoB,
        KindInfoB,
    ]
    assert [ItemValue.offset for ItemValue in Failure.value.reached[1:]] == [
        SizeInfo + 10 + 4,
        SizeInfo + 10 + 4 + 2 + 2,
    ]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAPOORBTSC() -> None:
    LayoutsA = PrefixTable(1)
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(PrefixStream(), 109, LayoutsA)
    assert Failure.value.slot == "tail"
    assert len(Failure.value.reached) == 2


# keeps this focused behavior isolated so regressions remain immediately visible
def TestACWNPISRAIL() -> None:
    LayoutsA = PrefixTable(0)
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(PrefixStream(), 109, LayoutsA)
    assert Failure.value.slot == "lead"
    assert "child count" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPIV() -> None:
    with PytestLib.raises(ArchiveError):
        PrefixTable(-1)
    with PytestLib.raises(ArchiveError):
        PrefixTable(4)
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {
                    "solo": {
                        "confidence": "confirmed",
                        "child_slots": ["*"],
                        "runs": {"lead": 0, "0": 0},
                        "repeat_prefix": 1,
                    }
                },
            }
        )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARCOZRNC() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "list": {
                    "confidence": "confirmed",
                    "child_slots": ["*", "..."],
                    "runs": {"lead": 2, "0": 0},
                    "repeat_count": {"run": "lead", "at": 0, "width": 2},
                }
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("list", 1)
        + StructLib.pack("<H", 0)
        + EncodeClassDefinition("list", 1)
        + StructLib.pack("<H", 1)
        + EncodeNull()
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.depth for ItemValue in Segments] == [0, 0, 1]
    assert Segments[0].end == Segments[1].offset
    assert Verify(BlobInfo, 109, LayoutsA).identical
    BackLayouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "list": {
                    "confidence": "confirmed",
                    "child_slots": ["*", "..."],
                    "runs": {"lead": 4, "0": 0},
                    "repeat_count": {"run": "lead", "back": 2, "width": 2},
                }
            },
        }
    )
    BackBlob = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("list", 1)
        + b"\xaa\xbb\x01\x00"
        + EncodeNull()
    )
    BackSegments = Segment(BackBlob, 109, BackLayouts)
    assert [ItemValue.depth for ItemValue in BackSegments] == [0, 1]
    assert Verify(BackBlob, 109, BackLayouts).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def AssertSkMeta(Layout: ClassLayout) -> None:
    assert Layout.walks_groups
    assert Layout.child_slots == ()
    assert Layout.repeat_count is None
    assert Layout.repeat_prefix == 0
    assert not Layout.repeats
    assert not Layout.walks_a_prefix
    assert Layout.run_keys() == ("lead", "tail")
    assert Layout.constant_run("lead", 18000) == 49
    assert Layout.variable_runs["tail"][0].predicate == "NextParentToken"


# keeps this focused behavior isolated so regressions remain immediately visible
def AssertSkGeom(Layout: ClassLayout) -> None:
    assert [Group.name for Group in Layout.groups] == [
        "entity",
        "point",
        "relation",
        "constraint",
        "lists",
        "chain",
    ]
    Shape = {Group.name: Group for Group in Layout.groups}
    assert Shape["entity"].element == (8, 39, 0, 87)
    assert (Shape["entity"].count_back, Shape["entity"].count_width) == (49, 2)
    assert Shape["entity"].trailer == 4
    assert Shape["point"].element == (8, 80)
    assert (Shape["point"].count_back, Shape["point"].count_width) == (12, 2)
    assert Shape["point"].CountByChildClass["null"].At == 0
    assert Shape["point"].CountByChildClass["null"].Lead == 12
    assert Shape["point"].trailer == 13
    assert len(Shape["point"].ElementRunVariants) == 12


# keeps this focused behavior isolated so regressions remain immediately visible
def AssertSkRels(Layout: ClassLayout) -> None:
    Shape = {Group.name: Group for Group in Layout.groups}
    assert Shape["relation"].element_runs(18000) == (0, 16, 17, 4)
    assert Shape["relation"].element_runs(14000) == (0, 16, 16, 4)
    assert len(Shape["relation"].ElementRunVariants) == 8
    assert Shape["relation"].CountVariants[0].Count == 1
    assert Shape["relation"].ElementRunVariants[-1].StopGroups
    assert Shape["relation"].trailer == 2
    assert Shape["constraint"].element == (0, 16, 17, 0, 4, 26, 0, 0, 6)
    assert Shape["constraint"].trailer == 8
    assert Shape["lists"].repeat == 1
    assert Shape["lists"].element == (170, 38)
    assert Shape["lists"].slots == ("suObList", "suObList")
    assert Shape["chain"].element == (0,)
    assert Shape["chain"].slots == ("moSketchChain_c",)
    assert (Shape["chain"].count_back, Shape["chain"].count_width) == (4, 2)
    assert Shape["chain"].trailer == 21
    for Group in Layout.groups:
        assert Group.note
        assert len(Group.slots) == len(Group.element)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTSTDSSFRG() -> None:
    Layout = Layouts()["sgSketch"]
    AssertSkMeta(Layout)
    AssertSkGeom(Layout)
    AssertSkRels(Layout)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTSTDPBCAFC() -> None:
    Layout = Layouts()["moPerBodyChooserData_c"]
    assert Layout.confidence == "confirmed"
    assert Layout.walks_groups
    assert Layout.child_slots == ()
    assert Layout.constant_run("lead", 18000) == 2
    assert [Group.name for Group in Layout.groups] == [
        "primary_face_refs",
        "secondary_face_refs",
        "bounding_box_centres",
    ]
    assert [Group.slots for Group in Layout.groups] == [
        ("moFaceRef_c",),
        ("moFaceRef_c",),
        ("moBBoxCenterData_c",),
    ]
    assert [Group.trailer for Group in Layout.groups] == [2, 2, 0]
    TailInfo = Layout.variable_runs["tail"][0]
    assert TailInfo.rule == "count"
    assert (TailInfo.at, TailInfo.count_width, TailInfo.stride, TailInfo.tail) == (
        8,
        2,
        4,
        4,
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPBCAGNAC() -> None:
    LayoutsA = Layouts()
    BodyInfo = (
        StructLib.pack("<H", 2)
        + EncodeNull()
        + EncodeNull()
        + StructLib.pack("<H", 0)
        + StructLib.pack("<H", 3)
        + EncodeNull()
        + EncodeNull()
        + EncodeNull()
        + StructLib.pack("<iiHIIIi", 7, 11, 3, 13, 17, 19, 23)
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("moPerBodyChooserData_c", 1)
        + BodyInfo
    )
    Segments = Segment(BlobInfo, 109, LayoutsA, mo_version=18000)
    assert [ItemValue.class_name for ItemValue in Segments] == [
        "moPerBodyChooserData_c",
        "null",
        "null",
        "null",
        "null",
        "null",
    ]
    assert Segments[-1].end == len(BlobInfo)
    assert Verify(BlobInfo, 109, LayoutsA, mo_version=18000).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def MakeLayout(
    GroupData: Mapping[str, LayoutValue],
    ChildSlots: Sequence[LayoutValue] = (),
    RunData: Mapping[str, LayoutValue] | None = None,
) -> LayoutTable:
    if RunData is None:
        RunData = {"lead": 0}
    Entry: dict[str, LayoutValue] = {
        "confidence": "partial",
        "child_slots": list(ChildSlots),
        "runs": dict(RunData),
        "groups": [dict(GroupData)],
    }
    return LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {"solo": Entry},
        }
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRGAV() -> None:
    Sound: dict[str, LayoutValue] = {
        "name": "loop",
        "count": {"back": 2, "width": 2},
        "slots": ["*"],
        "element": [0],
    }
    assert MakeLayout(Sound)["solo"].walks_groups
    InvalidGroups: tuple[Mapping[str, LayoutValue], ...] = (
        {**Sound, "name": ""},
        {**Sound, "element": []},
        {**Sound, "element": [-1]},
        {**Sound, "slots": ["*", "*"]},
        {**Sound, "trailer": -1},
        {**Sound, "count": {"back": 1, "width": 2}},
        {**Sound, "count": {"back": 2, "width": 3}},
        {"name": "loop", "slots": ["*"], "element": [0]},
        {**Sound, "repeat": 1},
        {"name": "loop", "repeat": 0, "slots": ["*"], "element": [0]},
        {**Sound, "element_by_version": {"nope": [0]}},
        {**Sound, "element_by_version": {"18000": [0, 0]}},
        {**Sound, "element_run_variants": {}},
        {**Sound, "count_variants": {}},
        {**Sound, "trailer_variants": {}},
        {
            **Sound,
            "element_run_variants": [
                {
                    "slot": 1,
                    "predicate_at": 0,
                    "predicate_width": 1,
                    "values": [1],
                    "run": 0,
                }
            ],
        },
    )
    for GroupData in InvalidGroups:
        with PytestLib.raises(ArchiveError):
            MakeLayout(GroupData)
    for ChildSlots, RunData in ((["*"], {"lead": 0, "0": 0}), ([], {})):
        with PytestLib.raises(ArchiveError):
            MakeLayout(Sound, ChildSlots, RunData)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARGWICEAT() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "partial",
                    "child_slots": [],
                    "runs": {"lead": 2},
                    "groups": [
                        {
                            "name": "pairs",
                            "count": {"back": 2, "width": 2},
                            "slots": ["*", "*"],
                            "element": [1, 3],
                            "trailer": 5,
                        },
                        {
                            "name": "singles",
                            "count": {"back": 5, "width": 1},
                            "slots": ["*"],
                            "element": [0],
                            "trailer": 0,
                        },
                    ],
                }
            },
        }
    )
    BodyInfo = (
        StructLib.pack("<H", 2)
        + EncodeNull()
        + b"\x00"
        + EncodeNull()
        + b"\x00" * 3
        + EncodeNull()
        + b"\x00"
        + EncodeNull()
        + b"\x00" * 3
        + b"\x01\x00\x00\x00\x00"
        + EncodeNull()
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + BodyInfo
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.depth for ItemValue in Segments] == [0, 1, 1, 1, 1, 1]
    assert Segments[-1].end == len(BlobInfo)
    assert Verify(BlobInfo, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARGSAVERFAP() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"lead": 2},
                    "groups": [
                        {
                            "name": "items",
                            "count": {"back": 2, "width": 2},
                            "slots": ["*"],
                            "element": [1],
                            "element_run_variants": [
                                {
                                    "slot": 0,
                                    "predicate_at": 0,
                                    "predicate_width": 1,
                                    "values": [122],
                                    "run": 3,
                                    "runs_by_version": {"18000": 5},
                                }
                            ],
                        }
                    ],
                }
            },
        }
    )
    HeadInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("solo", 1)
        + StructLib.pack("<H", 1)
        + EncodeNull()
    )
    Modern = Segment(HeadInfo + b"z\x01\x02\x03\x04", 109, LayoutsA, mo_version=18000)
    Legacy = Segment(HeadInfo + b"z\x01\x02", 109, LayoutsA, mo_version=14000)
    Default = Segment(HeadInfo + b"\x01", 109, LayoutsA, mo_version=18000)
    assert Modern[-1].end == len(HeadInfo) + 5
    assert Legacy[-1].end == len(HeadInfo) + 3
    assert Default[-1].end == len(HeadInfo) + 1
    assert Verify(
        HeadInfo + b"z\x01\x02\x03\x04", 109, LayoutsA, mo_version=18000
    ).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARGSCCATTV() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"lead": 2},
                    "groups": [
                        {
                            "name": "items",
                            "count": {"back": 2, "width": 2},
                            "slots": ["*"],
                            "element": [1],
                            "element_run_variants": [
                                {
                                    "slot": 0,
                                    "last": True,
                                    "child_classes": ["null"],
                                    "run": 3,
                                    "trailer": 0,
                                },
                                {"slot": 0, "child_classes": ["null"], "run": 2},
                            ],
                            "trailer": 4,
                        }
                    ],
                }
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("solo", 1)
        + StructLib.pack("<H", 2)
        + EncodeNull()
        + b"\x01\x02"
        + EncodeNull()
        + b"\x03\x04\x05"
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.class_name for ItemValue in Segments] == ["solo", "null", "null"]
    assert Segments[-1].end == len(BlobInfo)
    assert Verify(BlobInfo, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARGCVCSATFB() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"lead": 0},
                    "groups": [
                        {
                            "name": "fixed_branch",
                            "count": {"back": 2, "width": 2},
                            "count_variants": [
                                {
                                    "predicate_at": 0,
                                    "predicate_width": 2,
                                    "values": [0],
                                    "count": 1,
                                }
                            ],
                            "slots": ["*"],
                            "element": [0],
                            "element_run_variants": [
                                {
                                    "slot": 0,
                                    "last": True,
                                    "child_classes": ["null"],
                                    "run": 1,
                                    "trailer": 0,
                                    "stop_groups": True,
                                }
                            ],
                        },
                        {
                            "name": "unreached",
                            "repeat": 1,
                            "slots": ["*"],
                            "element": [99],
                        },
                    ],
                }
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + EncodeNull() + b"z"
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.class_name for ItemValue in Segments] == ["solo", "null"]
    assert Segments[-1].end == len(BlobInfo)
    assert Verify(BlobInfo, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARGCCBAANC() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "partial",
                    "child_slots": [],
                    "runs": {"lead": 0},
                    "groups": [
                        {"name": "first", "repeat": 1, "slots": ["*"], "element": [0]},
                        {
                            "name": "second",
                            "count": {"back": 2, "width": 2},
                            "count_by_child_class": {
                                "null": {"at": 0, "width": 2, "lead": 4}
                            },
                            "slots": ["*"],
                            "element": [0],
                        },
                    ],
                }
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("solo", 1)
        + EncodeNull()
        + StructLib.pack("<H", 1)
        + b"\x00\x00"
        + EncodeNull()
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert [ItemValue.offset for ItemValue in Segments] == [6, 16, 22]
    assert Verify(BlobInfo, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARGWCAAZRNC() -> None:
    LayoutsA = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "partial",
                    "child_slots": [],
                    "runs": {"lead": 2},
                    "groups": [
                        {
                            "name": "loop",
                            "count": {"back": 2, "width": 2},
                            "slots": ["*"],
                            "element": [0],
                            "trailer": 3,
                        }
                    ],
                }
            },
        }
    )
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("solo", 1)
        + StructLib.pack("<H", 0)
        + b"\x00" * 3
    )
    Segments = Segment(BlobInfo, 109, LayoutsA)
    assert len(Segments) == 1
    assert Segments[0].end == len(BlobInfo)
    assert Verify(BlobInfo, 109, LayoutsA).identical


# keeps this focused behavior isolated so regressions remain immediately visible
def TestACRWAWIR() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [{"slot": "leaf", "rule": "count", "at": 0}],
        }
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + b"\x00" * 4
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert "count width" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestACRWAPIR() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [{"slot": "leaf", "rule": "conditional", "at": 0}],
        }
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + b"\x00" * 4
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(BlobInfo, 109, LayoutsA)
    assert "predicate" in str(Failure.value)
    Guarded = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [
                {
                    "slot": "leaf",
                    "rule": "guard",
                    "at": 4,
                    "predicate": "variant",
                    "predicate_at": 0,
                    "predicate_width": 4,
                    "values": [0],
                }
            ],
        }
    )
    Rejected = (
        b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + StructLib.pack("<I", 1)
    )
    with PytestLib.raises(SegmentationError) as Failure:
        Segment(Rejected, 109, Guarded)
    assert "rejected value 1" in str(Failure.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCMVRTSN() -> None:
    NameList = (
        "Contents/Config-0-ResolvedFeatures",
        "_DL_VERSION_11000/DLUpdateStamp",
        "_MO_VERSION_14000/Biography",
        "_MO_VERSION_14000/History",
    )
    assert ContainerMoVersion(NameList) == 14000
    assert ContainerMoVersion(("_MO_VERSION_18000\\History",)) == 18000
    assert ContainerMoVersion(("_MO_VERSION_18000",)) == 18000
    assert ContainerMoVersion(("_MO_VERSION_14000/H", "_MO_VERSION_18000/H")) == 18000
    assert ContainerMoVersion(("Contents/Definition", "Header2")) is None
    assert ContainerMoVersion(("_MO_VERSION_beta/History",)) is None
    assert ContainerMoVersion(()) is None


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("Label", KLabels)
def TestRPCARDV(Label: str) -> None:
    Payload = Recorded(Label)
    Version = RecordedPart(Payload)[1]
    assert Version == (14000 if Label.startswith("vendor_") else 18000), Label


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAVGRITFAVIN() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "runs_by_version": {"leaf": {"18000": 8, "14000": 4}},
        }
    )
    Entry = LayoutsA["solo"]
    assert Entry.constant_run("leaf", 18000) == 8
    assert Entry.constant_run("leaf", 14000) == 4
    assert Entry.constant_run_keys == frozenset({"leaf"})
    HeadInfoA = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1)
    WideInfo = Segment(HeadInfoA + b"\x00" * 8, 109, LayoutsA, mo_version=18000)
    assert WideInfo[0].end == len(HeadInfoA) + 8
    Narrow = Segment(HeadInfoA + b"\x00" * 4, 109, LayoutsA, mo_version=14000)
    assert Narrow[0].end == len(HeadInfoA) + 4


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAVTGOFBTTPR() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": ["*"],
            "runs": {"lead": 2, "0": 6},
            "runs_by_version": {"0": {"18000": 10}},
        }
    )
    Entry = LayoutsA["solo"]
    assert Entry.constant_run("0", 18000) == 10
    assert Entry.constant_run("0", 14000) == 6
    assert Entry.constant_run("0", None) == 6
    assert Entry.constant_run("lead", 18000) == 2
    assert Entry.constant_run("missing", 18000) is None
    BlobInfo = (
        b"\x00" * SizeInfo
        + EncodeClassDefinition("solo", 1)
        + b"\x00" * 2
        + EncodeNull()
        + b"\x00" * 6
    )
    assert Segment(BlobInfo, 109, LayoutsA, mo_version=14000)[-1].end == len(BlobInfo)
    assert Segment(BlobInfo, 109, LayoutsA)[-1].end == len(BlobInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAVGRWAFIR() -> None:
    LayoutsA = SingleCT(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "runs_by_version": {"leaf": {"18000": 4}},
        }
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1) + b"\x00" * 4
    assert Segment(BlobInfo, 109, LayoutsA, mo_version=18000)[0].end == len(BlobInfo)
    with PytestLib.raises(SegmentationError) as Missed:
        Segment(BlobInfo, 109, LayoutsA, mo_version=14000)
    assert Missed.value.class_name == "solo"
    assert Missed.value.slot == "leaf"
    assert "document version 14000" in str(Missed.value)
    with PytestLib.raises(SegmentationError) as Unknown:
        Segment(BlobInfo, 109, LayoutsA)
    assert "no document version was supplied" in str(Unknown.value)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSRANDV() -> None:
    LayoutsA = SingleCT(
        {"confidence": "confirmed", "child_slots": [], "runs": {"leaf": 0}}
    )
    BlobInfo = b"\x00" * SizeInfo + EncodeClassDefinition("solo", 1)
    with PytestLib.raises(ArchiveError):
        Segment(BlobInfo, 109, LayoutsA, mo_version=-1)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRBVIV() -> None:
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs_by_version": []}}}
        )
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs_by_version": {"leaf": 4}}}}
        )
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs_by_version": {"leaf": {}}}}}
        )
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {"solo": {"runs_by_version": {"leaf": {"v8": 4}}}},
            }
        )
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {"solo": {"runs_by_version": {"leaf": {"18000": -1}}}},
            }
        )


# keeps this focused behavior isolated so regressions remain immediately visible
def NamedTTSTGMCFCO() -> None:
    Entry = Layouts()["moCompFeature_c"]
    assert Entry.child_slots == ("moUnitComponent_c",)
    assert Entry.runs == {"lead": 0}
    assert Entry.runs_by_version == {"0": {18000: 89, 14000: 85, 13000: 85}}
    assert Entry.constant_run("0", 18000) == 89
    assert Entry.constant_run("0", 14000) == 85
    assert Entry.constant_run("0", 13000) == 85
    assert Entry.constant_run("0", None) is None
    assert not Entry.variable_runs


# keeps this focused behavior isolated so regressions remain immediately visible
def TestLTVII() -> None:
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping({"version": 1})
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping({"version": 1, "classes": {"solo": 3}})
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"child_slots": "abc"}}}
        )
    with PytestLib.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs": {"leaf": -1}}}}
        )
    with PytestLib.raises(ArchiveError):
        LayoutTable.load(KRootInfo / "re" / "data" / "class_layouts_missing.json")


# keeps this focused behavior isolated so regressions remain immediately visible
def AssertLayoutRow(NameText: str, Entry: ClassLayout) -> None:
    assert Entry.confidence in {"confirmed", "partial", "not found"}
    assert Entry.source
    assert set(Entry.runs_by_version) <= set(Entry.run_keys()), NameText
    for LookupKey, Gated in Entry.runs_by_version.items():
        assert Gated, (NameText, LookupKey)
        for Version, Length in Gated.items():
            assert Version > 0, (NameText, LookupKey)
            assert Length >= 0, (NameText, LookupKey)
    if Entry.confidence == "confirmed":
        assert not Entry.repeats
        for LookupKey in Entry.run_keys():
            Elements = Entry.variable_runs.get(LookupKey, ())
            assert LookupKey in Entry.constant_run_keys or Elements, (
                NameText,
                LookupKey,
            )
            assert all((Element.rule != "opaque" for Element in Elements)), (
                NameText,
                LookupKey,
            )
    for SlotInfo, Elements in Entry.variable_runs.items():
        assert Elements
        assert SlotInfo in set(Entry.run_keys()) | {"lead"}
        for Element in Elements:
            assert Element.rule in {"string", "count", "conditional", "guard", "opaque"}


# keeps this focused behavior isolated so regressions remain immediately visible
def GetRecordedSet() -> set[str]:
    RecordedNames = set[str]()
    for Label in KLabels:
        TargetPath = KSegments / f"segments_{Label}.json"
        if not TargetPath.is_file():
            continue
        for ItemValue in Recorded(Label)["segments"]:
            if ItemValue["kind"] in {KindInfoA, KindInfo}:
                RecordedNames.add(ItemValue["class_name"])
    return RecordedNames


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLTMTRC() -> None:
    LayoutsA = Layouts()
    assert LayoutsA.version == 1
    Confirmed = [
        NameText
        for NameText, Entry in LayoutsA.classes.items()
        if Entry.confidence == "confirmed"
    ]
    assert len(Confirmed) >= KFloor
    for NameText, Entry in LayoutsA.classes.items():
        AssertLayoutRow(NameText, Entry)
    assert GetRecordedSet() <= set(LayoutsA.classes)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFVCDNR() -> None:
    LayoutsA = Layouts()
    Streams = DonorStreams()
    assert len(Streams) == 32
    Version = GetDonorVer(KDonors, AuthoredMV())
    Identical = 0
    for NameText, BlobInfo in Streams:
        Features = DonorFC(NameText)
        SeedInfo = KSeedInfo + Features - 1 if Features > 0 else KSeedInfo
        Resolution = ResolveBase(
            BlobInfo, SeedInfo, LayoutsA, header_size=SizeInfo, mo_version=Version
        )
        Report = Verify(
            BlobInfo,
            Resolution.base,
            LayoutsA,
            header_size=SizeInfo,
            mo_version=Version,
        )
        if Report.identical:
            Identical += 1
    assert Identical >= KIdentically


# keeps this focused behavior isolated so regressions remain immediately visible
def DonorFC(NameText: str) -> int:
    MetaInfo = KDonors / NameText / "meta.json"
    if not MetaInfo.is_file():
        return -1
    RawMeta: object = JsonLib.loads(MetaInfo.read_text(encoding="utf-8"))
    if not IsLayoutObject(RawMeta):
        return -1
    Features = RawMeta.get("features")
    return len(Features) if IsLayoutSequence(Features) else -1


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFORDNR() -> None:
    LayoutsA = Layouts()
    Version = GetDonorVer(KDonors, AuthoredMV())
    Reached = 0
    for NameText, BlobInfo in DonorStreams():
        Features = DonorFC(NameText)
        SeedInfo = KSeedInfo + Features - 1 if Features > 0 else KSeedInfo
        Resolution = ResolveBase(
            BlobInfo, SeedInfo, LayoutsA, header_size=SizeInfo, mo_version=Version
        )
        Report = Verify(
            BlobInfo,
            Resolution.base,
            LayoutsA,
            header_size=SizeInfo,
            mo_version=Version,
        )
        assert Report.object_count > 0, NameText
        Reached += Report.object_count
    assert Reached >= KFloorA


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRECCMR() -> None:
    LayoutsA = Layouts()
    Resolved = {
        NameText: Entry
        for NameText, Entry in LayoutsA.classes.items()
        if Entry.source == "re/data/Layouts/ExternalClasses.json"
    }
    assert Resolved
    for NameText, Entry in Resolved.items():
        assert not Entry.repeats, NameText
        for LookupKey in Entry.run_keys():
            Elements = Entry.variable_runs.get(LookupKey, ())
            assert LookupKey in Entry.constant_run_keys or Elements, (
                NameText,
                LookupKey,
            )
            for Element in Elements:
                assert Element.rule != "opaque", (NameText, LookupKey)
    Aliases = {NameText for NameText in Resolved if NameText.startswith("external#")}
    assert Aliases
    for Alias in Aliases:
        assert LayoutsA.classes[Alias].child_slots == Resolved[Alias].child_slots


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFSFNTBC() -> None:
    LayoutsA = Layouts()
    Version = GetDonorVer(KDonors, AuthoredMV())
    for NameText, BlobInfo in DonorStreams():
        Report = Verify(
            BlobInfo, 109, LayoutsA, header_size=SizeInfo, mo_version=Version
        )
        if Report.identical:
            continue
        assert Report.blocking_class, NameText
        assert Report.blocking_slot, NameText
        assert Report.blocking_offset >= SizeInfo, NameText
        assert (
            Report.blocking_class in LayoutsA.classes
            or Report.blocking_class.startswith("external#")
            or Report.blocking_class == "<stream>"
        ), NameText
