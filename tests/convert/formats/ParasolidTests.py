# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace as Replace
from hashlib import sha256 as ShaTwoFiveSix
from pathlib import Path as PathValue
import math as MathValue
import struct as Struct

import pytest as Pytest

from convert.adapters.freecad.Brep import triangle_mesh_brep as TriangleMeshBrep
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import (
    PARTITION_STREAM as PartitionStream,
)
from convert.geometry.Opencascade import decode_ascii_brep as DecodeAsciiBrep
from convert.geometry.Parasolid import (
    _ENTITY_MAGIC as EntityMagic,
    _RecordTables as RecordTables,
    _TopologyRecord as TopologyRecord,
    _array_record_fields as ArrayRecordFields,
    _curve_parameter_domain as CurveParameterDomain,
    _curve_point_at_parameter as CurvePointAtParameter,
    _linked_subset_order as LinkedSubsetOrder,
    _nurbs_curve_point as NurbsCurvePoint,
    _nurbs_surface_point as NurbsSurfacePoint,
    _parasolid_header as ParasolidHeader,
    _parse_b_curve_record as ParseItemBCurveRecord,
    _parse_chart_record as ParseChartRecord,
    _parse_coedge as ParseCoedge,
    _parse_intersection_data_record as ParseIDR,
    _parse_intersection_record as ParseIntersectionRecord,
    _parse_nurbs_curve_record as ParseNurbsCurveRecord,
    _parse_nurbs_surface_record as ParseNurbsSurfaceRecord,
    _parse_trimmed_curve_record as ParseTrimmedCurveRecord,
    _record_start as RecordStart,
    _resolve_trimmed_curve as ResolveTrimmedCurve,
    _scan_partition_records as ScanPartitionRecords,
    _solidworks_face_data as SolidworksFaceData,
    _u16 as UOneSix,
    _walk_coedge_ring as WalkCoedgeRing,
    _write_nurbs_curve as WriteNurbsCurve,
    _write_nurbs_surface as WriteNurbsSurface,
    _xmt as XmtValue,
    decode_brep_model as DecodeBrepModel,
    decode_partition_stream as DecodePartitionStream,
    encode_blank_partition_stream as EncodeBPS,
    encode_brep_model as EncodeBrepModel,
    encode_partition_stream as EncodePartitionStream,
)
from interchange import (
    CircleCurve,
    IntersectionCurve,
    LineCurve,
    NativeCurve,
    NurbsCurve,
    NurbsSurface,
    Vector3 as VectorThree,
    frozen_mapping as FrozenMapping,
)
from tests.interchange.brep.BrepTests import triangle_brep as TriangleBrep

# this binding exists because shared behavior needs one stable value
KRootValue = PathValue(__file__).parents[3]

# this binding exists because shared behavior needs one stable value
KCrankshaft = KRootValue / "examples" / "Random" / "Crank" / "Crankshaft.SLDPRT"

# this binding exists because shared behavior needs one stable value
KFuelInjector = (
    KRootValue / "examples" / "Random" / "Cylinder_heads" / "Fuel_injector.SLDPRT"
)

# this binding exists because shared behavior needs one stable value
KPoppet = KRootValue / "examples" / "Random" / "Cylinder_heads" / "Poppet.SLDPRT"

# this binding exists because shared behavior needs one stable value
KIntersectionParts = (
    (KRootValue / "examples" / "Random" / "Engine_mount_support.SLDPRT", 27, 2),
    (KRootValue / "examples" / "Random" / "Pistons" / "Conrod.SLDPRT", 43, 2),
)

# this binding exists because shared behavior needs one stable value
KCompactFinParts = (
    (KCrankshaft, 1),
    (
        KRootValue / "examples" / "Random" / "Cylinder_heads" / "Inlet_manifold.SLDPRT",
        16,
    ),
    (KRootValue / "examples" / "Random" / "Engine_Block.SLDPRT", 78),
    (
        KRootValue / "examples" / "Random" / "Supercharger" / "Screw_2.SLDPRT",
        1,
    ),
)

# these cases isolate the cylinder head and valve surface corpus
KNurbsHeadParts = (
    (
        KRootValue / "examples" / "Random" / "Cylinder_heads" / "Cylinder_head.SLDPRT",
        16,
        16,
    ),
    (
        KRootValue
        / "examples"
        / "Random"
        / "Cylinder_heads"
        / "Exhaust_manifold.SLDPRT",
        9,
        9,
    ),
    (
        KRootValue
        / "examples"
        / "Random"
        / "Cylinder_heads"
        / "Exhaust_manifold_2.SLDPRT",
        9,
        9,
    ),
    (KPoppet, 1, 1),
)

# these cases isolate the supercharger surface corpus
KNurbsChargerParts = (
    (KRootValue / "examples" / "Random" / "Supercharger" / "Screw_1.SLDPRT", 6, 6),
    (
        KRootValue / "examples" / "Random" / "Supercharger" / "Screw_2.SLDPRT",
        12,
        12,
    ),
    (
        KRootValue
        / "examples"
        / "Random"
        / "Supercharger"
        / "Supercharger_housing.SLDPRT",
        3,
        1,
    ),
    (
        KRootValue / "examples" / "Random" / "Supercharger" / "Throttle_housing.SLDPRT",
        1,
        1,
    ),
)

# this combined corpus preserves the original surface case execution order
KNurbsSurfaceParts = KNurbsHeadParts + KNurbsChargerParts

# this binding exists because shared behavior needs one stable value
KNurbsCurveParts = (
    (KRootValue / "examples" / "Random" / "Supercharger" / "Screw_1.SLDPRT", 18, 6),
    (KRootValue / "examples" / "Random" / "Supercharger" / "Screw_2.SLDPRT", 30, 12),
)

# this binding exists because shared behavior needs one stable value
KWaterPump = KRootValue / "examples" / "Random" / "Addons" / "Water_pump.SLDPRT"

# this binding exists because shared behavior needs one stable value
KIntersectionSupportParts = (
    (
        KRootValue
        / "examples"
        / "Random"
        / "Cylinder_heads"
        / "Cylinder_head_cover.SLDPRT",
        144,
        99,
        71,
    ),
    (
        KRootValue
        / "examples"
        / "Random"
        / "Cylinder_heads"
        / "Cylinder_head_cover_2.SLDPRT",
        148,
        103,
        72,
    ),
)


# this definition exists because focused behavior needs one stable owner
def Partition(PathValueA: PathValue) -> bytes:
    Stream = SldprtArchive.open(PathValueA).require(PartitionStream)
    return next(
        Payload.data
        for Payload in DecodePartitionStream(Stream, PartitionStream)
        if Payload.kind == "partition"
    )


# this definition exists because focused behavior needs one stable owner
def Tables(PathValueA: PathValue) -> RecordTables:
    Payload = Partition(PathValueA)
    Header = ParasolidHeader(Payload)
    assert Header is not None
    TablesA = ScanPartitionRecords(Payload[Header.body_offset :])
    assert TablesA is not None
    return TablesA


# this definition exists because focused behavior needs one stable owner
def Coordinates(Value: VectorThree) -> tuple[float, float, float]:
    return Value.x, Value.y, Value.z


# this definition exists because focused behavior needs one stable owner
def SolidT():
    Model = DecodeAsciiBrep(
        TriangleMeshBrep(
            (
                (0.0, 0.0, 0.0),
                (2.0, 0.0, 0.0),
                (0.0, 3.0, 0.0),
                (0.0, 0.0, 4.0),
            ),
            ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
        ),
        id_prefix="solidworks:ring",
    )
    assert Model is not None
    return Replace(
        Model,
        pcurves=(),
        vertices=tuple(Replace(VertexA, tolerance=0.0) for VertexA in Model.vertices),
        edges=tuple(Replace(EdgeValue, tolerance=0.0) for EdgeValue in Model.edges),
        coedges=tuple(Replace(Coedge, pcurve_id="") for Coedge in Model.coedges),
        faces=tuple(Replace(FaceValue, tolerance=0.0) for FaceValue in Model.faces),
    )


# this definition exists because focused behavior needs one stable owner
def TestPSERRP() -> None:
    RawValue = b"PS\x00\x00partition"
    Encoded = EncodePartitionStream(RawValue)
    Decoded = DecodePartitionStream(Encoded, PartitionStream)
    assert len(Encoded) == Decoded[0].compressed_size + 36
    assert Struct.unpack_from("<I", Encoded)[0] == len(Encoded) - 4
    assert Decoded[0].data == RawValue
    assert Decoded[0].wrapper_offset == 0
    assert Encoded[-8:] == bytes(8)


# this definition exists because focused behavior needs one stable owner
def TestPSERNPD() -> None:
    with Pytest.raises(ValueError, match="must start"):
        EncodePartitionStream(b"not parasolid")


# this definition exists because focused behavior needs one stable owner
def TestBPSMSTP() -> None:
    Encoded = EncodeBPS()
    Decoded = DecodePartitionStream(Encoded, PartitionStream)
    assert Encoded == EncodeBPS()
    assert len(Encoded) == 577
    assert ShaTwoFiveSix(Encoded).hexdigest() == (
        "97c3bc3b7aa7219186bc61dfe8e5f9f26a61e5f54853280406d9abd5ece1ad26"
    )
    assert tuple(Payload.kind for Payload in Decoded) == ("partition", "deltas")
    assert tuple(Payload.schema for Payload in Decoded) == (
        "SCH_3601228_36001_13006",
        "SCH_3601228_36001_13006",
    )
    assert tuple(Payload.uncompressed_size for Payload in Decoded) == (307, 411)
    assert tuple(Payload.compressed_size for Payload in Decoded) == (236, 269)
    assert tuple(Payload.wrapper_offset for Payload in Decoded) == (0, 272)
    assert tuple(Payload.sha256 for Payload in Decoded) == (
        "8ff1cd4d3369dd45b2f9a3bc9df280b4358d61ec38682dc605bc29c64af77942",
        "adca164ebfcb9dc73683bc121e0682a0d15346e59bad67fd921febe9046ef7d8",
    )
    assert tuple(Payload.description for Payload in Decoded) == (
        "TRANSMIT FILE (partition) created by modeller version 3601228",
        "TRANSMIT FILE (deltas) created by modeller version 3601228",
    )
    assert all(ParasolidHeader(Payload.data) is not None for Payload in Decoded)


# this definition exists because focused behavior needs one stable owner
def TestNBHUBESL() -> None:
    Payload = EncodeBrepModel(TriangleBrep())
    DescriptionLength = Struct.unpack_from(">H", Payload, 4)[0]
    SchemaLengthOffset = 6 + DescriptionLength
    SchemaLength = Struct.unpack_from(">I", Payload, SchemaLengthOffset)[0]
    Header = ParasolidHeader(Payload)
    assert Header is not None
    assert SchemaLength == len(Header.schema.encode("ascii"))
    Malformed = Payload[:SchemaLengthOffset] + Payload[SchemaLengthOffset + 1 :]
    assert ParasolidHeader(Malformed) is None


# this helper verifies the versioned header and exposes its record body
def VersionBody(Payload: bytes) -> bytes:
    Header = ParasolidHeader(Payload)
    assert Header is not None
    assert Header.description == (
        ": TRANSMIT FILE (partition) created by modeller version 1200000"
    )
    assert Header.schema == "SCH_1200000_12006"
    return Payload[Header.body_offset :]


# this helper verifies every expected versioned partition table
def AssertVTables(BodyValue: bytes) -> None:
    assert BodyValue[:8] == bytes.fromhex("0000000000650002")
    assert BodyValue[12:14] == bytes.fromhex("0003")
    assert BodyValue[33:37] == bytes.fromhex("000c0003")
    assert BodyValue[-4:] == bytes.fromhex("00010001")
    TablesA = ScanPartitionRecords(BodyValue)
    assert TablesA is not None
    assert TablesA.v12_partition is True
    assert len(TablesA.bridges) == 1
    assert len(TablesA.loops) == 1
    assert len(TablesA.edge_uses) == 3
    assert len(TablesA.coedges) == 6
    assert len(TablesA.vertex_uses) == 3
    assert len(TablesA.points) == 3
    assert len(TablesA.curves) == 3
    assert len(TablesA.surfaces) == 1


# this helper verifies that versioned tolerance data survives decoding
def AssertVModel(Payload: bytes) -> None:
    Restored = DecodeBrepModel(Payload)
    assert Restored is not None
    assert Restored.validate() == ()
    assert len(Restored.bodies) == 1
    assert len(Restored.regions) == 1
    assert len(Restored.shells) == 1
    assert len(Restored.faces) == 1
    assert len(Restored.edges) == 3
    assert len(Restored.vertices) == 3
    assert {Vertex.tolerance for Vertex in Restored.vertices} == {1e-7}
    assert {EdgeValueA.tolerance for EdgeValueA in Restored.edges} == {2e-7}
    assert {FaceValueA.tolerance for FaceValueA in Restored.faces} == {3e-7}


# this test covers versioned binary output and its complete model round trip
def TestNBWUVOPT() -> None:
    SourceModel = TriangleBrep()
    SourceModel = Replace(
        SourceModel,
        vertices=tuple(
            Replace(Vertex, tolerance=1e-7) for Vertex in SourceModel.vertices
        ),
        edges=tuple(
            Replace(EdgeValueA, tolerance=2e-7) for EdgeValueA in SourceModel.edges
        ),
        faces=tuple(
            Replace(FaceValueA, tolerance=3e-7) for FaceValueA in SourceModel.faces
        ),
    )
    Payload = EncodeBrepModel(SourceModel)
    AssertVTables(VersionBody(Payload))
    AssertVModel(Payload)


# this definition exists because focused behavior needs one stable owner
def TestNBWUVOBAFT() -> None:
    Payload = EncodeBrepModel(TriangleBrep(), partition=False)
    Header = ParasolidHeader(Payload)
    assert Header is not None
    assert Header.description == (": TRANSMIT FILE created by modeller version 1200000")
    assert Header.schema == "SCH_1200000_12006"
    BodyValue = Payload[Header.body_offset :]
    assert BodyValue[:8] == bytes.fromhex("00000000000c0002")
    assert BodyValue[-4:] == bytes.fromhex("00010001")
    TablesA = ScanPartitionRecords(BodyValue)
    assert TablesA is not None
    LoopValue = next(iter(TablesA.loops.values()))
    RingValue = WalkCoedgeRing(TablesA, LoopValue.attribute, LoopValue.references[1])
    assert len(RingValue) == 3
    for Position, Attribute in enumerate(RingValue):
        FinValue = TablesA.coedges[Attribute]
        assert FinValue.references[2] == RingValue[(Position + 1) % len(RingValue)]
        assert FinValue.references[3] == RingValue[Position - 1]
    Restored = DecodeBrepModel(Payload)
    assert Restored is not None
    assert Restored.validate() == ()
    assert len(Restored.bodies) == 1
    assert len(Restored.faces) == 1
    assert len(Restored.edges) == 3
    assert len(Restored.vertices) == 3


# this definition exists because focused behavior needs one stable owner
def TestVOLDISFFVC() -> None:
    LoopValue = 10
    FinsValue = {
        20: TopologyRecord(20, (1, LoopValue, 21, 22, 100, 30, 40, 1, 1), 0),
        21: TopologyRecord(21, (1, LoopValue, 22, 20, 101, 31, 41, 1, 1), 0),
        22: TopologyRecord(22, (1, LoopValue, 20, 21, 102, 32, 42, 1, 1), 0),
        30: TopologyRecord(30, (1, 1, 1, 1, 102, 20, 40, 1, 1), 0),
        31: TopologyRecord(31, (1, 1, 1, 1, 100, 21, 41, 1, 1), 0),
        32: TopologyRecord(32, (1, 1, 1, 1, 101, 22, 42, 1, 1), 0),
    }
    TablesA = RecordTables({}, {}, {}, FinsValue, {}, {}, {}, {}, {}, True)
    assert WalkCoedgeRing(TablesA, LoopValue, 20) == (20, 22, 21)


# this definition exists because focused behavior needs one stable owner
def TestLSOFLWRO() -> None:
    Links = {
        40: (1, 30),
        99: (1, 1),
        20: (30, 10),
        10: (20, 1),
        30: (40, 20),
    }
    assert LinkedSubsetOrder((40, 10, 30, 20), Links) == (10, 20, 30, 40)
    assert LinkedSubsetOrder((30, 10), Links) == (10, 30)


# this helper assigns deliberately reversed topology and face order metadata
def BuildOrdered(Decoded):
    VertexCount = len(Decoded.vertices)
    FaceCount = len(Decoded.faces)
    Vertices = tuple(
        Replace(
            VertexA,
            attributes=FrozenMapping(
                {
                    **dict(VertexA.attributes),
                    "parasolid.point_order": VertexCount - Position - 1,
                }
            ),
        )
        for Position, VertexA in enumerate(Decoded.vertices)
    )
    Faces = tuple(
        Replace(
            FaceValue,
            attributes=FrozenMapping(
                {
                    **dict(FaceValue.attributes),
                    "solidworks.unchanged_order": FaceCount - Position - 1,
                    "solidworks.downstream_order": (Position + 2) % FaceCount,
                    "solidworks.colour_order": (Position + 1) % FaceCount,
                }
            ),
        )
        for Position, FaceValue in enumerate(Decoded.faces)
    )
    ExpectedFaceOrders = {
        FaceValue.attributes["solidworks.unchanged_id"]: (
            FaceValue.attributes["solidworks.unchanged_order"],
            FaceValue.attributes["solidworks.downstream_order"],
            FaceValue.attributes["solidworks.colour_order"],
        )
        for FaceValue in Faces
    }
    return (
        Replace(Decoded, vertices=Vertices, faces=Faces),
        ExpectedFaceOrders,
        VertexCount,
        FaceCount,
    )


# this helper serializes and restores the reordered model for inspection
def EncodeOrdered(Changed):
    Encoded = EncodeBrepModel(
        Changed,
        partition=False,
        solidworks_feature_ids={Changed.bodies[0].id: 32},
    )
    Header = ParasolidHeader(Encoded)
    assert Header is not None
    BodyValue = Encoded[Header.body_offset :]
    TablesA = ScanPartitionRecords(BodyValue)
    Restored = DecodeBrepModel(Encoded)
    assert TablesA is not None
    assert Restored is not None
    return BodyValue, TablesA, Restored


# this helper normalizes fin identifiers into stable positional signatures
def NormalizedFins(Value):
    CoedgePositions = {
        Coedge.id: Position for Position, Coedge in enumerate(Value.coedges)
    }
    EdgePositions = {
        EdgeValue.id: Position for Position, EdgeValue in enumerate(Value.edges)
    }

    # this helper maps a typed identifier to its stable collection position
    def Normalize(Descriptor):
        KindValue, Identifier = Descriptor
        return (
            (KindValue, CoedgePositions[Identifier])
            if KindValue == "coedge"
            else (KindValue, EdgePositions[Identifier])
        )

    return (
        tuple(
            tuple(
                Normalize(ItemValue)
                for ItemValue in VertexA.attributes["parasolid.vertex_fins"]
            )
            for VertexA in Value.vertices
        ),
        tuple(
            Normalize(EdgeValue.attributes["parasolid.first_fin"])
            for EdgeValue in Value.edges
        ),
    )


# this helper follows a topology record chain while rejecting cycles
def RecordChain(
    HeadValue: int, Records: dict[int, TopologyRecord], LinkValue: int
) -> tuple[int, ...]:
    Result = []
    Attribute = HeadValue
    while Attribute > 1:
        assert Attribute not in Result
        Result.append(Attribute)
        Attribute = Records[Attribute].references[LinkValue]
    return tuple(Result)


# this helper verifies point vertex and edge ordering in topology chains
def AssertTopoOrder(BodyValue, TablesA, Restored, VertexCount) -> None:
    VertexByAttribute = {
        int(VertexA.id.rsplit(":", 1)[1]): VertexA for VertexA in Restored.vertices
    }
    EdgeByAttribute = {
        int(EdgeValue.id.rsplit(":", 1)[1]): EdgeValue for EdgeValue in Restored.edges
    }
    BodyOffset = BodyValue.index(b"\x00\x0c")
    PointChain = RecordChain(UOneSix(BodyValue, BodyOffset + 53), TablesA.points, 2)
    VertexChain = RecordChain(
        UOneSix(BodyValue, BodyOffset + 59), TablesA.vertex_uses, 3
    )
    EdgeChain = RecordChain(UOneSix(BodyValue, BodyOffset + 57), TablesA.edge_uses, 2)
    assert [
        VertexByAttribute[TablesA.points[Attribute].references[1]].attributes[
            "parasolid.point_order"
        ]
        for Attribute in PointChain
    ] == list(range(VertexCount))
    assert [
        VertexByAttribute[Attribute].attributes["parasolid.vertex_order"]
        for Attribute in VertexChain
    ] == list(range(VertexCount))
    assert [
        EdgeByAttribute[Attribute].attributes["parasolid.edge_order"]
        for Attribute in EdgeChain
    ] == list(range(len(Restored.edges)))


# this helper follows a geometry link chain while rejecting cycles
def LinkChain(HeadValue: int, Links: dict[int, tuple[int | None]]) -> tuple[int, ...]:
    Result = []
    Attribute = HeadValue
    while Attribute > 1:
        assert Attribute not in Result
        Result.append(Attribute)
        NextAttribute = Links[Attribute][0]
        assert NextAttribute is not None
        Attribute = NextAttribute
    return tuple(Result)


# this helper verifies curve and surface ordering in geometry chains
def AssertGeomOrder(BodyValue, Restored) -> None:
    CurveByAttribute = {
        int(Curve.id.rsplit(":", 1)[1]): Curve for Curve in Restored.curves
    }
    SurfaceByAttribute = {
        int(Surface.id.rsplit(":", 1)[1]): Surface for Surface in Restored.surfaces
    }
    BodyOffset = BodyValue.index(b"\x00\x0c")
    CurveHead = UOneSix(BodyValue, BodyOffset + 51)
    SurfaceHead = UOneSix(BodyValue, BodyOffset + 49)
    assert CurveHead is not None
    assert SurfaceHead is not None
    CurveLinks = {
        Attribute: (UOneSix(Curve.attributes["carrier_record"], 12),)
        for Attribute, Curve in CurveByAttribute.items()
    }
    SurfaceLinks = {
        Attribute: (UOneSix(Surface.attributes["carrier_record"], 12),)
        for Attribute, Surface in SurfaceByAttribute.items()
    }
    assert [
        CurveByAttribute[Attribute].attributes["parasolid.curve_order"]
        for Attribute in LinkChain(CurveHead, CurveLinks)
    ] == list(range(len(Restored.curves)))
    assert [
        SurfaceByAttribute[Attribute].attributes["parasolid.surface_order"]
        for Attribute in LinkChain(SurfaceHead, SurfaceLinks)
    ] == list(range(len(Restored.surfaces)))


# this helper verifies native face order metadata and encoded order tables
def AssertFaceOrder(BodyValue, Restored, ExpectedFaceOrders, FaceCount) -> None:
    ActualFaceOrders = {
        FaceValue.attributes["solidworks.unchanged_id"]: (
            FaceValue.attributes["solidworks.unchanged_order"],
            FaceValue.attributes["solidworks.downstream_order"],
            FaceValue.attributes["solidworks.colour_order"],
        )
        for FaceValue in Restored.faces
    }
    assert ActualFaceOrders == ExpectedFaceOrders
    Unchanged, Orders = SolidworksFaceData(BodyValue)
    assert len(Unchanged) == FaceCount
    assert {
        NameValue: sorted(Values.values()) for NameValue, Values in Orders.items()
    } == {
        "unchanged": list(range(FaceCount)),
        "downstream": list(range(FaceCount)),
        "colour": list(range(FaceCount)),
    }


# this test verifies every native order chain survives a binary round trip
def TestVOBHALFDSO() -> None:
    Model = SolidT()
    Payload = EncodeBrepModel(
        Model,
        partition=False,
        solidworks_feature_ids={Model.bodies[0].id: 32},
    )
    Decoded = DecodeBrepModel(Payload)
    assert Decoded is not None
    Changed, ExpectedFaceOrders, VertexCount, FaceCount = BuildOrdered(Decoded)
    BodyValue, TablesA, Restored = EncodeOrdered(Changed)
    assert NormalizedFins(Restored) == NormalizedFins(Changed)
    AssertTopoOrder(BodyValue, TablesA, Restored, VertexCount)
    AssertGeomOrder(BodyValue, Restored)
    AssertFaceOrder(BodyValue, Restored, ExpectedFaceOrders, FaceCount)


# this definition exists because focused behavior needs one stable owner
def TestVONFRDTRD() -> None:
    Solid = SolidT()
    for Model, LinkValue in ((TriangleBrep(), 2), (Solid, 3)):
        Payload = EncodeBrepModel(
            Model,
            partition=False,
            solidworks_feature_ids={Model.bodies[0].id: 26},
        )
        Header = ParasolidHeader(Payload)
        assert Header is not None
        TablesA = ScanPartitionRecords(Payload[Header.body_offset :])
        assert TablesA is not None
        for FaceValue in TablesA.bridges.values():
            LoopAttribute = FaceValue.references[2]
            FirstAttribute = TablesA.loops[LoopAttribute].references[1]
            Expected = []
            Attribute = FirstAttribute
            while Attribute not in Expected:
                Expected.append(Attribute)
                Attribute = TablesA.coedges[Attribute].references[LinkValue]
            assert Attribute == FirstAttribute
            assert WalkCoedgeRing(TablesA, LoopAttribute, FirstAttribute) == tuple(
                Expected
            )


# this definition exists because focused behavior needs one stable owner
def TestVOSBABTMF() -> None:
    Model = TriangleBrep()
    BodyId = Model.bodies[0].id
    Payload = EncodeBrepModel(
        Model,
        partition=False,
        solidworks_feature_ids={BodyId: 26},
    )
    Header = ParasolidHeader(Payload)
    assert Header is not None
    BodyValue = Payload[Header.body_offset :]
    assert len(Payload) == 1797
    assert ShaTwoFiveSix(BodyValue).hexdigest() == (
        "5f4e997ad967fc770c11d999f6c7267a8f7fed05738c6701d022936d0ff21de6"
    )
    assert BodyValue[12:16] == bytes.fromhex("00030004")
    assert b"BODY_RECIPE_2001" in BodyValue
    assert b"SWIMPLICITBODYNAME_ID_U" in BodyValue
    assert b"LAST_BODY_MODIFYING_FEATURE_ID" in BodyValue
    assert b"ENT_TIME_STAMP_2001" in BodyValue
    assert b"ATOM_ID_2001" in BodyValue
    assert b"ATOM_FACE_ID_2001" in BodyValue
    assert b"SDL/TYSA_COLOUR" in BodyValue
    assert bytes.fromhex("005200000001002f0000001a") in BodyValue
    Restored = DecodeBrepModel(Payload)
    assert Restored is not None
    assert Restored.validate() == ()
    Changed = EncodeBrepModel(
        Model,
        partition=False,
        solidworks_feature_ids={BodyId: 314},
    )
    assert bytes.fromhex("005200000001002f0000013a") in Changed


# this definition exists because focused behavior needs one stable owner
def TestVOSBARCFI() -> None:
    Model = TriangleBrep()
    PartitionA = EncodeBrepModel(
        Model,
        solidworks_feature_ids={Model.bodies[0].id: 26},
    )
    assert b"LAST_BODY_MODIFYING_FEATURE_ID" in PartitionA
    assert DecodeBrepModel(PartitionA) is not None
    with Pytest.raises(ValueError, match="cover every"):
        EncodeBrepModel(
            Model,
            partition=False,
            solidworks_feature_ids={"missing": 26},
        )
    with Pytest.raises(ValueError, match="positive i32"):
        EncodeBrepModel(
            Model,
            partition=False,
            solidworks_feature_ids={Model.bodies[0].id: 0},
        )


# this definition exists because focused behavior needs one stable owner
def TestVOSSACBAFI() -> None:
    Encoded = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 4.0)),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )
    Model = DecodeAsciiBrep(Encoded, id_prefix="solidworks:solid")
    assert Model is not None
    Model = Replace(
        Model,
        pcurves=(),
        vertices=tuple(Replace(VertexA, tolerance=0.0) for VertexA in Model.vertices),
        edges=tuple(Replace(EdgeValue, tolerance=0.0) for EdgeValue in Model.edges),
        coedges=tuple(Replace(Coedge, pcurve_id="") for Coedge in Model.coedges),
        faces=tuple(Replace(FaceValue, tolerance=0.0) for FaceValue in Model.faces),
    )
    Payload = EncodeBrepModel(
        Model,
        partition=False,
        solidworks_feature_ids={Model.bodies[0].id: 26},
    )
    for Identifier in (
        b"SWEntUnchanged",
        b"DOWNSTREAM_FACE_ID",
        b"SDL/TYSA_COLOUR",
        b"BODY_IN_LIGHTWEIGHT_PERM",
        b"SDL/TYSA_DENSITY",
        b"BODY_MATCH",
        b"LAST_BODY_MODIFYING_FEATURE_ID",
    ):
        assert Identifier in Payload
    Restored = DecodeBrepModel(Payload)
    assert Restored is not None
    assert Restored.validate() == ()
    assert len(Restored.bodies) == 1
    assert len(Restored.faces) == 4
    assert len(Restored.edges) == 6
    assert all(
        type(FaceValue.attributes.get("solidworks.unchanged_id")) is int
        for FaceValue in Restored.faces
    )
    assert (
        EncodeBrepModel(
            Restored,
            partition=False,
            solidworks_feature_ids={Restored.bodies[0].id: 26},
        )
        == Payload
    )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(("PathValueA", "Expected"), KCompactFinParts)
def TestCIVFADFC(PathValueA: PathValue, Expected: int) -> None:
    Payload = Partition(PathValueA)
    Header = ParasolidHeader(Payload)
    assert Header is not None
    BodyValue = Payload[Header.body_offset :]
    Records = tuple(
        Record
        for Offset in range(len(BodyValue) - 1)
        if BodyValue[Offset : Offset + 2] == b"\x00\x11"
        and (Record := ParseCoedge(BodyValue, Offset)) is not None
        and Record.isolated
    )
    assert len(Records) == Expected
    assert all(Record.references[2] == Record.attribute for Record in Records)
    assert all(Record.references[3] == Record.attribute for Record in Records)
    assert all(Record.references[4] > 1 for Record in Records)
    assert all(max(Record.references[5:]) <= 1 for Record in Records)


# this definition exists because focused behavior needs one stable owner
def TestCIVFRTET() -> None:
    Attribute = 7
    References = (1, 8, Attribute, Attribute, 9, 1, 1, 1, 1)
    Encoded = b"\x00\x11" + Struct.pack(">H9HB", Attribute, *References, 0x3F)
    Decoded = ParseCoedge(Encoded, 0)
    assert Decoded is not None
    assert Decoded.isolated is True
    for Index in (0, 5, 6, 7, 8):
        Broken = list(References)
        Broken[Index] = 2
        Candidate = b"\x00\x11" + Struct.pack(">H9HB", Attribute, *Broken, 0x3F)
        assert ParseCoedge(Candidate, 0) is None
    for Index in (2, 3):
        Broken = list(References)
        Broken[Index] = Attribute + 1
        Candidate = b"\x00\x11" + Struct.pack(">H9HB", Attribute, *Broken, 0x3F)
        assert ParseCoedge(Candidate, 0) is None


# this definition exists because focused behavior needs one stable owner
def TestCPDILWTL() -> None:
    Model = DecodeBrepModel(Partition(KCrankshaft))
    assert Model is not None
    assert Model.validate() == ()
    assert len(Model.faces) == 82
    assert len(Model.loops) == 109
    assert len(Model.edges) == 176
    assert len(Model.vertices) == 124
    Degenerate = tuple(EdgeValue for EdgeValue in Model.edges if EdgeValue.degenerate)
    assert len(Degenerate) == 1
    assert Degenerate[0].start_vertex_id == Degenerate[0].end_vertex_id
    CurveById = {Curve.id: Curve for Curve in Model.curves}
    Curve = CurveById[Degenerate[0].curve_id]
    assert isinstance(Curve, NativeCurve)
    assert Curve.format_id == "parasolid.xt"
    assert Curve.entity_type == "isolated-vertex-loop"


# this definition exists because focused behavior needs one stable owner
def TestNELERFC() -> None:
    assert DecodeBrepModel(Partition(KFuelInjector)) is None


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(("PathValueA", "FaceCount", "CurveCount"), KIntersectionParts)
def TestCBIDWCNL(PathValueA: PathValue, FaceCount: int, CurveCount: int) -> None:
    Model = DecodeBrepModel(Partition(PathValueA))
    assert Model is not None
    assert Model.validate() == ()
    assert len(Model.faces) == FaceCount
    Curves = tuple(
        Curve for Curve in Model.curves if isinstance(Curve, IntersectionCurve)
    )
    assert len(Curves) == CurveCount
    for Curve in Curves:
        Attributes = Curve.attributes
        assert len(Curve.samples) == len(Attributes["chart_parameters"])
        assert len(Curve.samples) == len(Attributes["support_uv"][0])
        assert len(Curve.samples) == len(Attributes["support_uv"][1])
        assert Attributes["limit_forms"] == ("L?", "L?")
        assert Attributes["intersection_record"]
        assert Attributes["chart_record"]
        assert len(Attributes["limit_records"]) == 2
        assert Attributes["support_uv_record"]


# this definition exists because focused behavior needs one stable owner
def TestIRCDADF() -> None:
    Payload = Partition(KIntersectionParts[0][0])
    Header = ParasolidHeader(Payload)
    assert Header is not None
    BodyValue = Payload[Header.body_offset :]
    Direct = tuple(
        Record
        for Offset in range(len(BodyValue) - 1)
        if BodyValue[Offset : Offset + 2] == b"\x00\x26"
        and (Record := ParseIntersectionRecord(BodyValue, Offset)) is not None
    )
    Descriptor = tuple(
        Record
        for Offset, Value in enumerate(BodyValue)
        if Value == 0x5A and (Record := ParseIDR(BodyValue, Offset)) is not None
    )
    assert Direct
    assert Descriptor
    assert not set(Record.attribute for Record in Direct).intersection(
        Record.attribute for Record in Descriptor
    )


# this definition exists because focused behavior needs one stable owner
def TestCPSIFC() -> None:
    Payload = Partition(KIntersectionParts[0][0])
    Header = ParasolidHeader(Payload)
    assert Header is not None
    BodyValue = Payload[Header.body_offset :]
    Chart = next(
        Record
        for Offset in range(len(BodyValue) - 1)
        if BodyValue[Offset : Offset + 2] == b"\x00\x28"
        and (Record := ParseChartRecord(BodyValue, Offset)) is not None
    )
    Encoded = bytearray(Chart.raw)
    Sentinel = Encoded.find(EntityMagic)
    assert Sentinel >= 0
    Encoded[Sentinel : Sentinel + len(EntityMagic)] = bytes(len(EntityMagic))
    assert ParseChartRecord(bytes(Encoded), 0) is None


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("PathValueA", "SurfaceCount", "UsedCount"), KNurbsSurfaceParts
)
def TestNISDCNDAA(PathValueA: PathValue, SurfaceCount: int, UsedCount: int) -> None:
    TablesA = Tables(PathValueA)
    Surfaces = tuple(
        Surface
        for Surface in TablesA.surfaces.values()
        if isinstance(Surface, NurbsSurface)
    )
    UsedIds = {
        f"sldprt:brep:surface:{Record.references[4]}"
        for Record in TablesA.bridges.values()
    }
    assert len(Surfaces) == SurfaceCount
    assert sum(Surface.id in UsedIds for Surface in Surfaces) == UsedCount
    for Surface in Surfaces:
        Attributes = Surface.attributes
        assert Attributes["descriptor_layout"] == "extended"
        assert Attributes["rational"] == bool(Surface.weights)
        assert Attributes["vertex_dimension"] == (4 if Surface.weights else 3)
        assert Attributes["surface_record"]
        assert Attributes["descriptor_record"]
        assert Attributes["surface_data_record"]
        assert Attributes["control_record"]
        assert Attributes["u_multiplicity_record"]
        assert Attributes["v_multiplicity_record"]
        assert Attributes["u_knot_record"]
        assert Attributes["v_knot_record"]


# this helper verifies the complete extended rational curve descriptor
def AssertCurveData(Curve: NurbsCurve) -> None:
    Attributes = Curve.attributes
    assert Attributes["carrier_layout"] == "extended"
    assert Attributes["rational"] is True
    assert Attributes["vertex_dimension"] == 4
    assert Attributes["control_count"] == len(Curve.control_points)
    assert Attributes["knot_count"] == len(Curve.knots)
    assert len(Attributes["array_references"]) == 3
    assert Attributes["curve_record"]
    assert Attributes["descriptor_record"]
    assert Attributes["curve_data_record"]
    assert Attributes["control_record"]
    assert Attributes["multiplicity_record"]
    assert Attributes["knot_record"]
    assert len(Curve.weights) == len(Curve.control_points)
    assert all(Weight > 0.0 for Weight in Curve.weights)
    Domain = CurveParameterDomain(Curve)
    assert Domain is not None
    assert Domain[:2] == (0.0, 1.0)


# this helper verifies a rational curve meets its referenced edge vertices
def AssertCurveEnds(Curve: NurbsCurve, EdgeValue, Vertices) -> None:
    Start = NurbsCurvePoint(Curve, EdgeValue.start_parameter)
    EndValue = NurbsCurvePoint(Curve, EdgeValue.end_parameter)
    assert Start is not None
    assert EndValue is not None
    assert (
        MathValue.dist(
            (Start.x, Start.y, Start.z),
            Coordinates(Vertices[EdgeValue.start_vertex_id].point),
        )
        <= 1e-7
    )
    assert (
        MathValue.dist(
            (EndValue.x, EndValue.y, EndValue.z),
            Coordinates(Vertices[EdgeValue.end_vertex_id].point),
        )
        <= 1e-7
    )


# this test verifies extended rational curves decode with exact topology
@Pytest.mark.parametrize(("PathValueA", "FaceCount", "CurveCount"), KNurbsCurveParts)
def TestNICDEDAAER(PathValueA: PathValue, FaceCount: int, CurveCount: int) -> None:
    Model = DecodeBrepModel(Partition(PathValueA))
    assert Model is not None
    assert Model.validate() == ()
    assert len(Model.faces) == FaceCount
    Curves = tuple(Curve for Curve in Model.curves if isinstance(Curve, NurbsCurve))
    assert len(Curves) == CurveCount
    Vertices = {VertexA.id: VertexA for VertexA in Model.vertices}
    EdgesByCurve = {
        Curve.id: tuple(
            EdgeValue for EdgeValue in Model.edges if EdgeValue.curve_id == Curve.id
        )
        for Curve in Curves
    }
    for Curve in Curves:
        AssertCurveData(Curve)
        Edges = EdgesByCurve[Curve.id]
        assert len(Edges) == 1
        AssertCurveEnds(Curve, Edges[0], Vertices)


# this definition exists because focused behavior needs one stable owner
def TestNICDAWCFC() -> None:
    Payload = Partition(KNurbsCurveParts[0][0])
    Model = DecodeBrepModel(Payload)
    assert Model is not None
    Curve = next(Curve for Curve in Model.curves if isinstance(Curve, NurbsCurve))
    Descriptor = bytearray(Curve.attributes["descriptor_record"])
    Start = RecordStart(Descriptor, 0, 0x88)
    assert Start is not None
    Decoded = XmtValue(Descriptor, Start)
    assert Decoded is not None
    DescriptorCursor = Start + Decoded[1]
    assert Descriptor[DescriptorCursor + 15] == 1
    Descriptor[DescriptorCursor + 15] = 0
    assert ParseNurbsCurveRecord(bytes(Descriptor), 0) is None
    DescriptorOffset = Payload.find(Curve.attributes["descriptor_record"])
    assert DescriptorOffset >= 0
    CorruptedDescriptor = bytearray(Payload)
    CorruptedDescriptor[DescriptorOffset : DescriptorOffset + len(Descriptor)] = (
        Descriptor
    )
    assert DecodeBrepModel(CorruptedDescriptor) is None
    Control = bytearray(Curve.attributes["control_record"])
    Fields = ArrayRecordFields(Control, 0, 0x2D)
    assert Fields is not None
    ValuesOffset = Fields[2]
    Control[ValuesOffset + 24 : ValuesOffset + 32] = bytes(8)
    ControlOffset = Payload.find(Curve.attributes["control_record"])
    assert ControlOffset >= 0
    CorruptedControl = bytearray(Payload)
    CorruptedControl[ControlOffset : ControlOffset + len(Control)] = Control
    assert DecodeBrepModel(CorruptedControl) is None


# this definition exists because focused behavior needs one stable owner
def TestCICREWL() -> None:
    Generated = NurbsCurve(
        "curve:generated",
        2,
        (
            VectorThree(0.0, 0.0, 0.0),
            VectorThree(1.0, 2.0, 0.0),
            VectorThree(3.0, 2.0, 1.0),
        ),
        (0.0, 1.0),
        (3, 3),
        (1.0, 0.75, 1.0),
    )
    Encoded = bytearray()
    assert WriteNurbsCurve(Encoded, 2, Generated, 3) == 7
    TablesA = ScanPartitionRecords(bytes(Encoded))
    assert TablesA is not None
    Decoded = TablesA.curves[2]
    assert isinstance(Decoded, NurbsCurve)
    assert Decoded.degree == Generated.degree
    assert Decoded.knots == Generated.knots
    assert Decoded.multiplicities == Generated.multiplicities
    assert Decoded.weights == Generated.weights
    assert Decoded.attributes["carrier_layout"] == "compact"
    assert all(
        MathValue.dist(Coordinates(Actual), Coordinates(Expected)) <= 1e-12
        for Actual, Expected in zip(Decoded.control_points, Generated.control_points)
    )
    LongAttribute = b"\x00\x86\xff\xff\xff\x00\x02\x00\x03" + bytes(8)
    LongDescriptor = b"\x00\x86\x00\x02\xff\xff" + bytes(8)
    assert ParseItemBCurveRecord(LongAttribute, 0) is None
    HighDescriptor = ParseItemBCurveRecord(LongDescriptor, 0)
    assert HighDescriptor is not None
    assert HighDescriptor.descriptor_reference == 0xFFFF


# this definition exists because focused behavior needs one stable owner
def TestUTCPNRAVG() -> None:
    TablesA = Tables(KWaterPump)
    UsedCurveAttributes = {
        Record.references[3]
        for Record in TablesA.edge_uses.values()
        if len(Record.references) > 3
    }
    Curves = tuple(
        Curve
        for Attribute, Curve in TablesA.curves.items()
        if Attribute in UsedCurveAttributes and Curve.attributes.get("trimmed") is True
    )
    assert len(Curves) == 5
    assert sum(isinstance(Curve, LineCurve) for Curve in Curves) == 3
    assert sum(isinstance(Curve, CircleCurve) for Curve in Curves) == 2
    for Curve in Curves:
        Attributes = Curve.attributes
        assert len(Attributes["header_references"]) == 5
        assert Attributes["basis_reference"] > 1
        assert Attributes["basis_curve_id"]
        assert Attributes["trim_record"]
        Evaluated = tuple(
            CurvePointAtParameter(Curve, Parameter)
            for Parameter in Attributes["trim_parameters"]
        )
        assert all(Point is not None for Point in Evaluated)
        assert all(
            MathValue.dist(Coordinates(Actual), Coordinates(Expected)) <= 1e-7
            for Actual, Expected in zip(Evaluated, Attributes["trim_points"])
            if Actual is not None
        )
        if isinstance(Curve, LineCurve):
            assert Attributes["trim_parameters"] == Pytest.approx(
                tuple(Value * 1000.0 for Value in Attributes["trim_parameters_native"])
            )
        else:
            assert Attributes["trim_parameters"] == Attributes["trim_parameters_native"]


# this definition exists because focused behavior needs one stable owner
def TestTCRAPCFC() -> None:
    TablesA = Tables(KWaterPump)
    Curve = next(
        Curve
        for Curve in TablesA.curves.values()
        if isinstance(Curve, LineCurve) and Curve.attributes.get("trimmed") is True
    )
    RawValue = Curve.attributes["trim_record"]
    Record = ParseTrimmedCurveRecord(RawValue, 0)
    assert Record is not None
    Basis = TablesA.curves[Record.basis_reference]
    ReversedRange = bytearray(RawValue)
    Struct.pack_into(
        ">d", ReversedRange, len(RawValue) - 8, Record.parameters[0] - 0.001
    )
    RangeRecord = ParseTrimmedCurveRecord(bytes(ReversedRange), 0)
    assert RangeRecord is not None
    assert ResolveTrimmedCurve(RangeRecord, {Record.basis_reference: Basis}) is None
    DisplacedPoint = bytearray(RawValue)
    Struct.pack_into(
        ">d", DisplacedPoint, len(RawValue) - 64, Record.points[0].x / 1000.0 + 0.001
    )
    PointRecord = ParseTrimmedCurveRecord(bytes(DisplacedPoint), 0)
    assert PointRecord is not None
    assert ResolveTrimmedCurve(PointRecord, {Record.basis_reference: Basis}) is None


# this definition exists because focused behavior needs one stable owner
def TestPNSPTPI() -> None:
    Model = DecodeBrepModel(Partition(KPoppet))
    assert Model is not None
    assert Model.validate() == ()
    assert len(Model.faces) == 12
    Surface = next(
        Surface for Surface in Model.surfaces if isinstance(Surface, NurbsSurface)
    )
    Curve = next(
        Curve for Curve in Model.curves if isinstance(Curve, IntersectionCurve)
    )
    assert Surface.id == Curve.second_surface_id
    assert Surface.periodic_u is True
    assert Surface.periodic_v is False
    assert Surface.degree_u == 3
    assert Surface.degree_v == 2
    assert len(Surface.control_points) == 7
    assert len(Surface.control_points[0]) == 97
    LaneValue = Curve.attributes["support_uv"][1]
    assert len(LaneValue) == len(Curve.samples) == 21
    Evaluated = tuple(
        NurbsSurfacePoint(Surface, Parameters) for Parameters in LaneValue
    )
    assert all(Point is not None for Point in Evaluated)
    assert all(
        MathValue.dist(
            (Point.x, Point.y, Point.z),
            (Sample.x, Sample.y, Sample.z),
        )
        <= Curve.tolerance
        for Point, Sample in zip(Evaluated, Curve.samples)
        if Point is not None
    )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("PathValueA", "FaceCount", "SurfaceCount", "IntersectionCount"),
    KIntersectionSupportParts,
)
def TestISSRRWOF(
    PathValueA: PathValue, FaceCount: int, SurfaceCount: int, IntersectionCount: int
) -> None:
    Model = DecodeBrepModel(Partition(PathValueA))
    assert Model is not None
    assert Model.validate() == ()
    assert len(Model.faces) == FaceCount
    assert len(Model.surfaces) == SurfaceCount
    Intersections = tuple(
        Curve for Curve in Model.curves if isinstance(Curve, IntersectionCurve)
    )
    assert len(Intersections) == IntersectionCount
    SurfaceIds = frozenset(Surface.id for Surface in Model.surfaces)
    assert all(
        Curve.first_surface_id in SurfaceIds and Curve.second_surface_id in SurfaceIds
        for Curve in Intersections
    )


# this definition exists because focused behavior needs one stable owner
def TestNSDAWCFC() -> None:
    Payload = Partition(KPoppet)
    Model = DecodeBrepModel(Payload)
    assert Model is not None
    Surface = next(
        Surface for Surface in Model.surfaces if isinstance(Surface, NurbsSurface)
    )
    Descriptor = bytearray(Surface.attributes["descriptor_record"])
    Start = RecordStart(Descriptor, 0, 0x7E)
    assert Start is not None
    Decoded = XmtValue(Descriptor, Start)
    assert Decoded is not None
    DescriptorCursor = Start + Decoded[1]
    assert Descriptor[DescriptorCursor + 24] == 1
    Descriptor[DescriptorCursor + 24] = 0
    assert ParseNurbsSurfaceRecord(bytes(Descriptor), 0) is None
    DescriptorOffset = Payload.find(Surface.attributes["descriptor_record"])
    assert DescriptorOffset >= 0
    CorruptedDescriptor = bytearray(Payload)
    CorruptedDescriptor[DescriptorOffset : DescriptorOffset + len(Descriptor)] = (
        Descriptor
    )
    assert DecodeBrepModel(CorruptedDescriptor) is None
    Control = bytearray(Surface.attributes["control_record"])
    Fields = ArrayRecordFields(Control, 0, 0x2D)
    assert Fields is not None
    ValuesOffset = Fields[2]
    Control[ValuesOffset + 24 : ValuesOffset + 32] = bytes(8)
    ControlOffset = Payload.find(Surface.attributes["control_record"])
    assert ControlOffset >= 0
    CorruptedControl = bytearray(Payload)
    CorruptedControl[ControlOffset : ControlOffset + len(Control)] = Control
    assert DecodeBrepModel(CorruptedControl) is None


# this definition exists because focused behavior needs one stable owner
def TestCGNSRWIA() -> None:
    Surface = NurbsSurface(
        "surface:generated",
        1,
        1,
        (
            (VectorThree(0.0, 0.0, 0.0), VectorThree(0.0, 1.0, 0.0)),
            (VectorThree(1.0, 0.0, 0.0), VectorThree(1.0, 1.0, 0.0)),
        ),
        (0.0, 1.0),
        (0.0, 1.0),
        (2, 2),
        (2, 2),
    )
    Encoded = bytearray()
    assert WriteNurbsSurface(Encoded, 2, Surface, 3) == 9
    TablesA = ScanPartitionRecords(bytes(Encoded))
    assert TablesA is not None
    Decoded = TablesA.surfaces[2]
    assert isinstance(Decoded, NurbsSurface)
    assert Decoded.degree_u == Decoded.degree_v == 1
    assert Decoded.control_points == Surface.control_points
    assert Decoded.knots_u == Decoded.knots_v == (0.0, 1.0)
    assert Decoded.multiplicities_u == Decoded.multiplicities_v == (2, 2)
    assert Decoded.attributes["descriptor_layout"] == "compact"
