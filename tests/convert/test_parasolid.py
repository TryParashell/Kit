# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import math
import struct

import pytest

from convert.adapters.freecad.brep import triangle_mesh_brep
from convert.adapters.solidworks.container import SldprtArchive
from convert.adapters.solidworks.format import PARTITION_STREAM
from convert.opencascade import decode_ascii_brep
from convert.parasolid import (
    _ENTITY_MAGIC,
    _RecordTables,
    _TopologyRecord,
    _array_record_fields,
    _curve_parameter_domain,
    _curve_point_at_parameter,
    _linked_subset_order,
    _nurbs_curve_point,
    _nurbs_surface_point,
    _parasolid_header,
    _parse_b_curve_record,
    _parse_chart_record,
    _parse_coedge,
    _parse_intersection_data_record,
    _parse_intersection_record,
    _parse_nurbs_curve_record,
    _parse_nurbs_surface_record,
    _parse_trimmed_curve_record,
    _record_start,
    _resolve_trimmed_curve,
    _scan_partition_records,
    _solidworks_face_data,
    _u16,
    _walk_coedge_ring,
    _write_nurbs_curve,
    _write_nurbs_surface,
    _xmt,
    decode_brep_model,
    decode_partition_stream,
    encode_blank_partition_stream,
    encode_brep_model,
    encode_partition_stream,
)
from interchange import (
    CircleCurve,
    IntersectionCurve,
    LineCurve,
    NativeCurve,
    NurbsCurve,
    NurbsSurface,
    Vector3,
    frozen_mapping,
)
from tests.interchange.test_brep import triangle_brep

ROOT = Path(__file__).parents[2]
CRANKSHAFT = ROOT / "examples" / "Random" / "Crank" / "Crankshaft.SLDPRT"
FUEL_INJECTOR = ROOT / "examples" / "Random" / "Cylinder_heads" / "Fuel_injector.SLDPRT"
POPPET = ROOT / "examples" / "Random" / "Cylinder_heads" / "Poppet.SLDPRT"
INTERSECTION_PARTS = (
    (ROOT / "examples" / "Random" / "Engine_mount_support.SLDPRT", 27, 2),
    (ROOT / "examples" / "Random" / "Pistons" / "Conrod.SLDPRT", 43, 2),
)
COMPACT_FIN_PARTS = (
    (CRANKSHAFT, 1),
    (
        ROOT / "examples" / "Random" / "Cylinder_heads" / "Inlet_manifold.SLDPRT",
        16,
    ),
    (ROOT / "examples" / "Random" / "Engine_Block.SLDPRT", 78),
    (
        ROOT / "examples" / "Random" / "Supercharger" / "Screw_2.SLDPRT",
        1,
    ),
)
NURBS_SURFACE_PARTS = (
    (
        ROOT / "examples" / "Random" / "Cylinder_heads" / "Cylinder_head.SLDPRT",
        16,
        16,
    ),
    (
        ROOT / "examples" / "Random" / "Cylinder_heads" / "Exhaust_manifold.SLDPRT",
        9,
        9,
    ),
    (
        ROOT / "examples" / "Random" / "Cylinder_heads" / "Exhaust_manifold_2.SLDPRT",
        9,
        9,
    ),
    (POPPET, 1, 1),
    (ROOT / "examples" / "Random" / "Supercharger" / "Screw_1.SLDPRT", 6, 6),
    (
        ROOT / "examples" / "Random" / "Supercharger" / "Screw_2.SLDPRT",
        12,
        12,
    ),
    (
        ROOT / "examples" / "Random" / "Supercharger" / "Supercharger_housing.SLDPRT",
        3,
        1,
    ),
    (
        ROOT / "examples" / "Random" / "Supercharger" / "Throttle_housing.SLDPRT",
        1,
        1,
    ),
)
NURBS_CURVE_PARTS = (
    (ROOT / "examples" / "Random" / "Supercharger" / "Screw_1.SLDPRT", 18, 6),
    (ROOT / "examples" / "Random" / "Supercharger" / "Screw_2.SLDPRT", 30, 12),
)
WATER_PUMP = ROOT / "examples" / "Random" / "Addons" / "Water_pump.SLDPRT"
INTERSECTION_SUPPORT_PARTS = (
    (
        ROOT / "examples" / "Random" / "Cylinder_heads" / "Cylinder_head_cover.SLDPRT",
        144,
        99,
        71,
    ),
    (
        ROOT
        / "examples"
        / "Random"
        / "Cylinder_heads"
        / "Cylinder_head_cover_2.SLDPRT",
        148,
        103,
        72,
    ),
)


def _partition(path: Path) -> bytes:
    stream = SldprtArchive.open(path).require(PARTITION_STREAM)
    return next(
        payload.data
        for payload in decode_partition_stream(stream, PARTITION_STREAM)
        if payload.kind == "partition"
    )


def _tables(path: Path) -> _RecordTables:
    payload = _partition(path)
    header = _parasolid_header(payload)
    assert header is not None
    tables = _scan_partition_records(payload[header.body_offset :])
    assert tables is not None
    return tables


def _coordinates(value: Vector3) -> tuple[float, float, float]:
    return value.x, value.y, value.z


def _solid_tetrahedron():
    model = decode_ascii_brep(
        triangle_mesh_brep(
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
    assert model is not None
    return replace(
        model,
        pcurves=(),
        vertices=tuple(replace(vertex, tolerance=0.0) for vertex in model.vertices),
        edges=tuple(replace(edge, tolerance=0.0) for edge in model.edges),
        coedges=tuple(replace(coedge, pcurve_id="") for coedge in model.coedges),
        faces=tuple(replace(face, tolerance=0.0) for face in model.faces),
    )


def test_partition_stream_encoder_roundtrips_raw_parasolid() -> None:
    raw = b"PS\x00\x00partition"
    encoded = encode_partition_stream(raw)
    decoded = decode_partition_stream(encoded, PARTITION_STREAM)
    assert len(encoded) == decoded[0].compressed_size + 36
    assert struct.unpack_from("<I", encoded)[0] == len(encoded) - 4
    assert decoded[0].data == raw
    assert decoded[0].wrapper_offset == 0
    assert encoded[-8:] == bytes(8)


def test_partition_stream_encoder_rejects_non_parasolid_data() -> None:
    with pytest.raises(ValueError, match="must start"):
        encode_partition_stream(b"not parasolid")


def test_blank_partition_stream_matches_solidworks_2025_protocol() -> None:
    encoded = encode_blank_partition_stream()
    decoded = decode_partition_stream(encoded, PARTITION_STREAM)
    assert encoded == encode_blank_partition_stream()
    assert len(encoded) == 577
    assert sha256(encoded).hexdigest() == (
        "97c3bc3b7aa7219186bc61dfe8e5f9f26a61e5f54853280406d9abd5ece1ad26"
    )
    assert tuple(payload.kind for payload in decoded) == ("partition", "deltas")
    assert tuple(payload.schema for payload in decoded) == (
        "SCH_3601228_36001_13006",
        "SCH_3601228_36001_13006",
    )
    assert tuple(payload.uncompressed_size for payload in decoded) == (307, 411)
    assert tuple(payload.compressed_size for payload in decoded) == (236, 269)
    assert tuple(payload.wrapper_offset for payload in decoded) == (0, 272)
    assert tuple(payload.sha256 for payload in decoded) == (
        "8ff1cd4d3369dd45b2f9a3bc9df280b4358d61ec38682dc605bc29c64af77942",
        "adca164ebfcb9dc73683bc121e0682a0d15346e59bad67fd921febe9046ef7d8",
    )
    assert tuple(payload.description for payload in decoded) == (
        "TRANSMIT FILE (partition) created by modeller version 3601228",
        "TRANSMIT FILE (deltas) created by modeller version 3601228",
    )
    assert all(_parasolid_header(payload.data) is not None for payload in decoded)


def test_neutral_binary_header_uses_big_endian_schema_length() -> None:
    payload = encode_brep_model(triangle_brep())
    description_length = struct.unpack_from(">H", payload, 4)[0]
    schema_length_offset = 6 + description_length
    schema_length = struct.unpack_from(">I", payload, schema_length_offset)[0]
    header = _parasolid_header(payload)
    assert header is not None
    assert schema_length == len(header.schema.encode("ascii"))
    malformed = payload[:schema_length_offset] + payload[schema_length_offset + 1 :]
    assert _parasolid_header(malformed) is None


def test_neutral_binary_writer_uses_v12_partition_topology() -> None:
    SourceModel = triangle_brep()
    SourceModel = replace(
        SourceModel,
        vertices=tuple(
            replace(Vertex, tolerance=1e-7) for Vertex in SourceModel.vertices
        ),
        edges=tuple(replace(Edge, tolerance=2e-7) for Edge in SourceModel.edges),
        faces=tuple(replace(Face, tolerance=3e-7) for Face in SourceModel.faces),
    )
    payload = encode_brep_model(SourceModel)
    header = _parasolid_header(payload)
    assert header is not None
    assert header.description == (
        ": TRANSMIT FILE (partition) created by modeller version 1200000"
    )
    assert header.schema == "SCH_1200000_12006"
    body = payload[header.body_offset :]
    assert body[:8] == bytes.fromhex("0000000000650002")
    assert body[12:14] == bytes.fromhex("0003")
    assert body[33:37] == bytes.fromhex("000c0003")
    assert body[-4:] == bytes.fromhex("00010001")
    tables = _scan_partition_records(body)
    assert tables is not None
    assert tables.v12_partition is True
    assert len(tables.bridges) == 1
    assert len(tables.loops) == 1
    assert len(tables.edge_uses) == 3
    assert len(tables.coedges) == 6
    assert len(tables.vertex_uses) == 3
    assert len(tables.points) == 3
    assert len(tables.curves) == 3
    assert len(tables.surfaces) == 1
    restored = decode_brep_model(payload)
    assert restored is not None
    assert restored.validate() == ()
    assert len(restored.bodies) == 1
    assert len(restored.regions) == 1
    assert len(restored.shells) == 1
    assert len(restored.faces) == 1
    assert len(restored.edges) == 3
    assert len(restored.vertices) == 3
    assert {Vertex.tolerance for Vertex in restored.vertices} == {1e-7}
    assert {Edge.tolerance for Edge in restored.edges} == {2e-7}
    assert {Face.tolerance for Face in restored.faces} == {3e-7}


def test_neutral_binary_writer_uses_v12_body_and_fin_topology() -> None:
    payload = encode_brep_model(triangle_brep(), partition=False)
    header = _parasolid_header(payload)
    assert header is not None
    assert header.description == (": TRANSMIT FILE created by modeller version 1200000")
    assert header.schema == "SCH_1200000_12006"
    body = payload[header.body_offset :]
    assert body[:8] == bytes.fromhex("00000000000c0002")
    assert body[-4:] == bytes.fromhex("00010001")
    tables = _scan_partition_records(body)
    assert tables is not None
    loop = next(iter(tables.loops.values()))
    ring = _walk_coedge_ring(tables, loop.attribute, loop.references[1])
    assert len(ring) == 3
    for position, attribute in enumerate(ring):
        fin = tables.coedges[attribute]
        assert fin.references[2] == ring[(position + 1) % len(ring)]
        assert fin.references[3] == ring[position - 1]
    restored = decode_brep_model(payload)
    assert restored is not None
    assert restored.validate() == ()
    assert len(restored.bodies) == 1
    assert len(restored.faces) == 1
    assert len(restored.edges) == 3
    assert len(restored.vertices) == 3


def test_v12_loop_direction_is_selected_from_fin_vertex_connectivity() -> None:
    loop = 10
    fins = {
        20: _TopologyRecord(20, (1, loop, 21, 22, 100, 30, 40, 1, 1), 0),
        21: _TopologyRecord(21, (1, loop, 22, 20, 101, 31, 41, 1, 1), 0),
        22: _TopologyRecord(22, (1, loop, 20, 21, 102, 32, 42, 1, 1), 0),
        30: _TopologyRecord(30, (1, 1, 1, 1, 102, 20, 40, 1, 1), 0),
        31: _TopologyRecord(31, (1, 1, 1, 1, 100, 21, 41, 1, 1), 0),
        32: _TopologyRecord(32, (1, 1, 1, 1, 101, 22, 42, 1, 1), 0),
    }
    tables = _RecordTables({}, {}, {}, fins, {}, {}, {}, {}, {}, True)
    assert _walk_coedge_ring(tables, loop, 20) == (20, 22, 21)


def test_linked_subset_order_follows_links_without_record_order() -> None:
    links = {
        40: (1, 30),
        99: (1, 1),
        20: (30, 10),
        10: (20, 1),
        30: (40, 20),
    }
    assert _linked_subset_order((40, 10, 30, 20), links) == (10, 20, 30, 40)
    assert _linked_subset_order((30, 10), links) == (10, 30)


def test_v12_body_heads_and_lists_follow_decoded_semantic_orders() -> None:
    model = _solid_tetrahedron()
    payload = encode_brep_model(
        model,
        partition=False,
        solidworks_feature_ids={model.bodies[0].id: 32},
    )
    decoded = decode_brep_model(payload)
    assert decoded is not None
    vertex_count = len(decoded.vertices)
    face_count = len(decoded.faces)
    vertices = tuple(
        replace(
            vertex,
            attributes=frozen_mapping(
                {
                    **dict(vertex.attributes),
                    "parasolid.point_order": vertex_count - position - 1,
                }
            ),
        )
        for position, vertex in enumerate(decoded.vertices)
    )
    faces = tuple(
        replace(
            face,
            attributes=frozen_mapping(
                {
                    **dict(face.attributes),
                    "solidworks.unchanged_order": face_count - position - 1,
                    "solidworks.downstream_order": (position + 2) % face_count,
                    "solidworks.colour_order": (position + 1) % face_count,
                }
            ),
        )
        for position, face in enumerate(decoded.faces)
    )
    expected_face_orders = {
        face.attributes["solidworks.unchanged_id"]: (
            face.attributes["solidworks.unchanged_order"],
            face.attributes["solidworks.downstream_order"],
            face.attributes["solidworks.colour_order"],
        )
        for face in faces
    }
    changed = replace(decoded, vertices=vertices, faces=faces)
    encoded = encode_brep_model(
        changed,
        partition=False,
        solidworks_feature_ids={changed.bodies[0].id: 32},
    )
    header = _parasolid_header(encoded)
    assert header is not None
    body = encoded[header.body_offset :]
    tables = _scan_partition_records(body)
    restored = decode_brep_model(encoded)
    assert tables is not None
    assert restored is not None

    def normalized_fins(value):
        coedge_positions = {
            coedge.id: position for position, coedge in enumerate(value.coedges)
        }
        edge_positions = {
            edge.id: position for position, edge in enumerate(value.edges)
        }

        def normalize(descriptor):
            kind, identifier = descriptor
            return (
                (kind, coedge_positions[identifier])
                if kind == "coedge"
                else (kind, edge_positions[identifier])
            )

        return (
            tuple(
                tuple(
                    normalize(item)
                    for item in vertex.attributes["parasolid.vertex_fins"]
                )
                for vertex in value.vertices
            ),
            tuple(
                normalize(edge.attributes["parasolid.first_fin"])
                for edge in value.edges
            ),
        )

    assert normalized_fins(restored) == normalized_fins(changed)

    def chain(
        head: int, records: dict[int, _TopologyRecord], link: int
    ) -> tuple[int, ...]:
        result = []
        attribute = head
        while attribute > 1:
            assert attribute not in result
            result.append(attribute)
            attribute = records[attribute].references[link]
        return tuple(result)

    vertex_by_attribute = {
        int(vertex.id.rsplit(":", 1)[1]): vertex for vertex in restored.vertices
    }
    edge_by_attribute = {
        int(edge.id.rsplit(":", 1)[1]): edge for edge in restored.edges
    }
    curve_by_attribute = {
        int(curve.id.rsplit(":", 1)[1]): curve for curve in restored.curves
    }
    surface_by_attribute = {
        int(surface.id.rsplit(":", 1)[1]): surface for surface in restored.surfaces
    }
    body_offset = body.index(b"\x00\x0c")
    point_chain = chain(_u16(body, body_offset + 53), tables.points, 2)
    vertex_chain = chain(_u16(body, body_offset + 59), tables.vertex_uses, 3)
    edge_chain = chain(_u16(body, body_offset + 57), tables.edge_uses, 2)
    assert [
        vertex_by_attribute[tables.points[attribute].references[1]].attributes[
            "parasolid.point_order"
        ]
        for attribute in point_chain
    ] == list(range(vertex_count))
    assert [
        vertex_by_attribute[attribute].attributes["parasolid.vertex_order"]
        for attribute in vertex_chain
    ] == list(range(vertex_count))
    assert [
        edge_by_attribute[attribute].attributes["parasolid.edge_order"]
        for attribute in edge_chain
    ] == list(range(len(restored.edges)))
    curve_head = _u16(body, body_offset + 51)
    surface_head = _u16(body, body_offset + 49)
    assert curve_head is not None
    assert surface_head is not None
    curve_links = {
        attribute: (_u16(curve.attributes["carrier_record"], 12),)
        for attribute, curve in curve_by_attribute.items()
    }
    surface_links = {
        attribute: (_u16(surface.attributes["carrier_record"], 12),)
        for attribute, surface in surface_by_attribute.items()
    }

    def geometry_chain(
        head: int, links: dict[int, tuple[int | None]]
    ) -> tuple[int, ...]:
        result = []
        attribute = head
        while attribute > 1:
            assert attribute not in result
            result.append(attribute)
            next_attribute = links[attribute][0]
            assert next_attribute is not None
            attribute = next_attribute
        return tuple(result)

    assert [
        curve_by_attribute[attribute].attributes["parasolid.curve_order"]
        for attribute in geometry_chain(curve_head, curve_links)
    ] == list(range(len(restored.curves)))
    assert [
        surface_by_attribute[attribute].attributes["parasolid.surface_order"]
        for attribute in geometry_chain(surface_head, surface_links)
    ] == list(range(len(restored.surfaces)))
    actual_face_orders = {
        face.attributes["solidworks.unchanged_id"]: (
            face.attributes["solidworks.unchanged_order"],
            face.attributes["solidworks.downstream_order"],
            face.attributes["solidworks.colour_order"],
        )
        for face in restored.faces
    }
    assert actual_face_orders == expected_face_orders
    unchanged, orders = _solidworks_face_data(body)
    assert len(unchanged) == face_count
    assert {name: sorted(values.values()) for name, values in orders.items()} == {
        "unchanged": list(range(face_count)),
        "downstream": list(range(face_count)),
        "colour": list(range(face_count)),
    }


def test_v12_native_fin_ring_direction_tracks_region_dimension() -> None:
    solid = _solid_tetrahedron()
    for model, link in ((triangle_brep(), 2), (solid, 3)):
        payload = encode_brep_model(
            model,
            partition=False,
            solidworks_feature_ids={model.bodies[0].id: 26},
        )
        header = _parasolid_header(payload)
        assert header is not None
        tables = _scan_partition_records(payload[header.body_offset :])
        assert tables is not None
        for face in tables.bridges.values():
            loop_attribute = face.references[2]
            first_attribute = tables.loops[loop_attribute].references[1]
            expected = []
            attribute = first_attribute
            while attribute not in expected:
                expected.append(attribute)
                attribute = tables.coedges[attribute].references[link]
            assert attribute == first_attribute
            assert _walk_coedge_ring(tables, loop_attribute, first_attribute) == tuple(
                expected
            )


def test_v12_solidworks_body_attributes_bind_the_modifying_feature() -> None:
    model = triangle_brep()
    body_id = model.bodies[0].id
    payload = encode_brep_model(
        model,
        partition=False,
        solidworks_feature_ids={body_id: 26},
    )
    header = _parasolid_header(payload)
    assert header is not None
    body = payload[header.body_offset :]
    assert len(payload) == 1797
    assert sha256(body).hexdigest() == (
        "5f4e997ad967fc770c11d999f6c7267a8f7fed05738c6701d022936d0ff21de6"
    )
    assert body[12:16] == bytes.fromhex("00030004")
    assert b"BODY_RECIPE_2001" in body
    assert b"SWIMPLICITBODYNAME_ID_U" in body
    assert b"LAST_BODY_MODIFYING_FEATURE_ID" in body
    assert b"ENT_TIME_STAMP_2001" in body
    assert b"ATOM_ID_2001" in body
    assert b"ATOM_FACE_ID_2001" in body
    assert b"SDL/TYSA_COLOUR" in body
    assert bytes.fromhex("005200000001002f0000001a") in body
    restored = decode_brep_model(payload)
    assert restored is not None
    assert restored.validate() == ()
    changed = encode_brep_model(
        model,
        partition=False,
        solidworks_feature_ids={body_id: 314},
    )
    assert bytes.fromhex("005200000001002f0000013a") in changed


def test_v12_solidworks_body_attributes_require_complete_feature_ids() -> None:
    model = triangle_brep()
    partition = encode_brep_model(
        model,
        solidworks_feature_ids={model.bodies[0].id: 26},
    )
    assert b"LAST_BODY_MODIFYING_FEATURE_ID" in partition
    assert decode_brep_model(partition) is not None
    with pytest.raises(ValueError, match="cover every"):
        encode_brep_model(
            model,
            partition=False,
            solidworks_feature_ids={"missing": 26},
        )
    with pytest.raises(ValueError, match="positive i32"):
        encode_brep_model(
            model,
            partition=False,
            solidworks_feature_ids={model.bodies[0].id: 0},
        )


def test_v12_solidworks_solid_attributes_cover_body_and_face_identity() -> None:
    encoded = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0), (0.0, 0.0, 4.0)),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )
    model = decode_ascii_brep(encoded, id_prefix="solidworks:solid")
    assert model is not None
    model = replace(
        model,
        pcurves=(),
        vertices=tuple(replace(vertex, tolerance=0.0) for vertex in model.vertices),
        edges=tuple(replace(edge, tolerance=0.0) for edge in model.edges),
        coedges=tuple(replace(coedge, pcurve_id="") for coedge in model.coedges),
        faces=tuple(replace(face, tolerance=0.0) for face in model.faces),
    )
    payload = encode_brep_model(
        model,
        partition=False,
        solidworks_feature_ids={model.bodies[0].id: 26},
    )
    for identifier in (
        b"SWEntUnchanged",
        b"DOWNSTREAM_FACE_ID",
        b"SDL/TYSA_COLOUR",
        b"BODY_IN_LIGHTWEIGHT_PERM",
        b"SDL/TYSA_DENSITY",
        b"BODY_MATCH",
        b"LAST_BODY_MODIFYING_FEATURE_ID",
    ):
        assert identifier in payload
    restored = decode_brep_model(payload)
    assert restored is not None
    assert restored.validate() == ()
    assert len(restored.bodies) == 1
    assert len(restored.faces) == 4
    assert len(restored.edges) == 6
    assert all(
        type(face.attributes.get("solidworks.unchanged_id")) is int
        for face in restored.faces
    )
    assert (
        encode_brep_model(
            restored,
            partition=False,
            solidworks_feature_ids={restored.bodies[0].id: 26},
        )
        == payload
    )


@pytest.mark.parametrize(("path", "expected"), COMPACT_FIN_PARTS)
def test_compact_isolated_vertex_fins_are_decoded_fail_closed(
    path: Path, expected: int
) -> None:
    payload = _partition(path)
    header = _parasolid_header(payload)
    assert header is not None
    body = payload[header.body_offset :]
    records = tuple(
        record
        for offset in range(len(body) - 1)
        if body[offset : offset + 2] == b"\x00\x11"
        and (record := _parse_coedge(body, offset)) is not None
        and record.isolated
    )
    assert len(records) == expected
    assert all(record.references[2] == record.attribute for record in records)
    assert all(record.references[3] == record.attribute for record in records)
    assert all(record.references[4] > 1 for record in records)
    assert all(max(record.references[5:]) <= 1 for record in records)


def test_compact_isolated_vertex_fin_requires_the_exact_topology() -> None:
    attribute = 7
    references = (1, 8, attribute, attribute, 9, 1, 1, 1, 1)
    encoded = b"\x00\x11" + struct.pack(">H9HB", attribute, *references, 0x3F)
    decoded = _parse_coedge(encoded, 0)
    assert decoded is not None
    assert decoded.isolated is True
    for index in (0, 5, 6, 7, 8):
        broken = list(references)
        broken[index] = 2
        candidate = b"\x00\x11" + struct.pack(">H9HB", attribute, *broken, 0x3F)
        assert _parse_coedge(candidate, 0) is None
    for index in (2, 3):
        broken = list(references)
        broken[index] = attribute + 1
        candidate = b"\x00\x11" + struct.pack(">H9HB", attribute, *broken, 0x3F)
        assert _parse_coedge(candidate, 0) is None


def test_crankshaft_partition_decodes_isolated_loop_without_topology_loss() -> None:
    model = decode_brep_model(_partition(CRANKSHAFT))
    assert model is not None
    assert model.validate() == ()
    assert len(model.faces) == 82
    assert len(model.loops) == 109
    assert len(model.edges) == 176
    assert len(model.vertices) == 124
    degenerate = tuple(edge for edge in model.edges if edge.degenerate)
    assert len(degenerate) == 1
    assert degenerate[0].start_vertex_id == degenerate[0].end_vertex_id
    curve_by_id = {curve.id: curve for curve in model.curves}
    curve = curve_by_id[degenerate[0].curve_id]
    assert isinstance(curve, NativeCurve)
    assert curve.format_id == "parasolid.xt"
    assert curve.entity_type == "isolated-vertex-loop"


def test_null_ended_line_edge_remains_fail_closed() -> None:
    assert decode_brep_model(_partition(FUEL_INJECTOR)) is None


@pytest.mark.parametrize(("path", "face_count", "curve_count"), INTERSECTION_PARTS)
def test_chart_backed_intersections_decode_with_complete_native_lanes(
    path: Path, face_count: int, curve_count: int
) -> None:
    model = decode_brep_model(_partition(path))
    assert model is not None
    assert model.validate() == ()
    assert len(model.faces) == face_count
    curves = tuple(
        curve for curve in model.curves if isinstance(curve, IntersectionCurve)
    )
    assert len(curves) == curve_count
    for curve in curves:
        attributes = curve.attributes
        assert len(curve.samples) == len(attributes["chart_parameters"])
        assert len(curve.samples) == len(attributes["support_uv"][0])
        assert len(curve.samples) == len(attributes["support_uv"][1])
        assert attributes["limit_forms"] == ("L?", "L?")
        assert attributes["intersection_record"]
        assert attributes["chart_record"]
        assert len(attributes["limit_records"]) == 2
        assert attributes["support_uv_record"]


def test_intersection_records_cover_direct_and_descriptor_forms() -> None:
    payload = _partition(INTERSECTION_PARTS[0][0])
    header = _parasolid_header(payload)
    assert header is not None
    body = payload[header.body_offset :]
    direct = tuple(
        record
        for offset in range(len(body) - 1)
        if body[offset : offset + 2] == b"\x00\x26"
        and (record := _parse_intersection_record(body, offset)) is not None
    )
    descriptor = tuple(
        record
        for offset, value in enumerate(body)
        if value == 0x5A
        and (record := _parse_intersection_data_record(body, offset)) is not None
    )
    assert direct
    assert descriptor
    assert not set(record.attribute for record in direct).intersection(
        record.attribute for record in descriptor
    )


def test_chart_parameter_sentinel_is_fail_closed() -> None:
    payload = _partition(INTERSECTION_PARTS[0][0])
    header = _parasolid_header(payload)
    assert header is not None
    body = payload[header.body_offset :]
    chart = next(
        record
        for offset in range(len(body) - 1)
        if body[offset : offset + 2] == b"\x00\x28"
        and (record := _parse_chart_record(body, offset)) is not None
    )
    encoded = bytearray(chart.raw)
    sentinel = encoded.find(_ENTITY_MAGIC)
    assert sentinel >= 0
    encoded[sentinel : sentinel + len(_ENTITY_MAGIC)] = bytes(len(_ENTITY_MAGIC))
    assert _parse_chart_record(bytes(encoded), 0) is None


@pytest.mark.parametrize(("path", "surface_count", "used_count"), NURBS_SURFACE_PARTS)
def test_native_b_surfaces_decode_complete_nurbs_descriptors_and_arrays(
    path: Path, surface_count: int, used_count: int
) -> None:
    tables = _tables(path)
    surfaces = tuple(
        surface
        for surface in tables.surfaces.values()
        if isinstance(surface, NurbsSurface)
    )
    used_ids = {
        f"sldprt:brep:surface:{record.references[4]}"
        for record in tables.bridges.values()
    }
    assert len(surfaces) == surface_count
    assert sum(surface.id in used_ids for surface in surfaces) == used_count
    for surface in surfaces:
        attributes = surface.attributes
        assert attributes["descriptor_layout"] == "extended"
        assert attributes["rational"] == bool(surface.weights)
        assert attributes["vertex_dimension"] == (4 if surface.weights else 3)
        assert attributes["surface_record"]
        assert attributes["descriptor_record"]
        assert attributes["surface_data_record"]
        assert attributes["control_record"]
        assert attributes["u_multiplicity_record"]
        assert attributes["v_multiplicity_record"]
        assert attributes["u_knot_record"]
        assert attributes["v_knot_record"]


@pytest.mark.parametrize(("path", "face_count", "curve_count"), NURBS_CURVE_PARTS)
def test_native_b_curves_decode_exact_descriptors_arrays_and_edge_ranges(
    path: Path, face_count: int, curve_count: int
) -> None:
    model = decode_brep_model(_partition(path))
    assert model is not None
    assert model.validate() == ()
    assert len(model.faces) == face_count
    curves = tuple(curve for curve in model.curves if isinstance(curve, NurbsCurve))
    assert len(curves) == curve_count
    vertices = {vertex.id: vertex for vertex in model.vertices}
    edges_by_curve = {
        curve.id: tuple(edge for edge in model.edges if edge.curve_id == curve.id)
        for curve in curves
    }
    for curve in curves:
        attributes = curve.attributes
        assert attributes["carrier_layout"] == "extended"
        assert attributes["rational"] is True
        assert attributes["vertex_dimension"] == 4
        assert attributes["control_count"] == len(curve.control_points)
        assert attributes["knot_count"] == len(curve.knots)
        assert len(attributes["array_references"]) == 3
        assert attributes["curve_record"]
        assert attributes["descriptor_record"]
        assert attributes["curve_data_record"]
        assert attributes["control_record"]
        assert attributes["multiplicity_record"]
        assert attributes["knot_record"]
        assert len(curve.weights) == len(curve.control_points)
        assert all(weight > 0.0 for weight in curve.weights)
        domain = _curve_parameter_domain(curve)
        assert domain is not None
        assert domain[:2] == (0.0, 1.0)
        edges = edges_by_curve[curve.id]
        assert len(edges) == 1
        edge = edges[0]
        start = _nurbs_curve_point(curve, edge.start_parameter)
        end = _nurbs_curve_point(curve, edge.end_parameter)
        assert start is not None
        assert end is not None
        assert (
            math.dist(
                (start.x, start.y, start.z),
                _coordinates(vertices[edge.start_vertex_id].point),
            )
            <= 1e-7
        )
        assert (
            math.dist(
                (end.x, end.y, end.z),
                _coordinates(vertices[edge.end_vertex_id].point),
            )
            <= 1e-7
        )


def test_native_b_curve_descriptor_and_weight_corruption_fail_closed() -> None:
    payload = _partition(NURBS_CURVE_PARTS[0][0])
    model = decode_brep_model(payload)
    assert model is not None
    curve = next(curve for curve in model.curves if isinstance(curve, NurbsCurve))
    descriptor = bytearray(curve.attributes["descriptor_record"])
    start = _record_start(descriptor, 0, 0x88)
    assert start is not None
    decoded = _xmt(descriptor, start)
    assert decoded is not None
    descriptor_cursor = start + decoded[1]
    assert descriptor[descriptor_cursor + 15] == 1
    descriptor[descriptor_cursor + 15] = 0
    assert _parse_nurbs_curve_record(bytes(descriptor), 0) is None
    descriptor_offset = payload.find(curve.attributes["descriptor_record"])
    assert descriptor_offset >= 0
    corrupted_descriptor = bytearray(payload)
    corrupted_descriptor[descriptor_offset : descriptor_offset + len(descriptor)] = (
        descriptor
    )
    assert decode_brep_model(corrupted_descriptor) is None
    control = bytearray(curve.attributes["control_record"])
    fields = _array_record_fields(control, 0, 0x2D)
    assert fields is not None
    values_offset = fields[2]
    control[values_offset + 24 : values_offset + 32] = bytes(8)
    control_offset = payload.find(curve.attributes["control_record"])
    assert control_offset >= 0
    corrupted_control = bytearray(payload)
    corrupted_control[control_offset : control_offset + len(control)] = control
    assert decode_brep_model(corrupted_control) is None


def test_compact_b_curve_requires_exact_writer_layout() -> None:
    generated = NurbsCurve(
        "curve:generated",
        2,
        (
            Vector3(0.0, 0.0, 0.0),
            Vector3(1.0, 2.0, 0.0),
            Vector3(3.0, 2.0, 1.0),
        ),
        (0.0, 1.0),
        (3, 3),
        (1.0, 0.75, 1.0),
    )
    encoded = bytearray()
    assert _write_nurbs_curve(encoded, 2, generated, 3) == 7
    tables = _scan_partition_records(bytes(encoded))
    assert tables is not None
    decoded = tables.curves[2]
    assert isinstance(decoded, NurbsCurve)
    assert decoded.degree == generated.degree
    assert decoded.knots == generated.knots
    assert decoded.multiplicities == generated.multiplicities
    assert decoded.weights == generated.weights
    assert decoded.attributes["carrier_layout"] == "compact"
    assert all(
        math.dist(_coordinates(actual), _coordinates(expected)) <= 1e-12
        for actual, expected in zip(decoded.control_points, generated.control_points)
    )
    long_attribute = b"\x00\x86\xff\xff\xff\x00\x02\x00\x03" + bytes(8)
    long_descriptor = b"\x00\x86\x00\x02\xff\xff" + bytes(8)
    assert _parse_b_curve_record(long_attribute, 0) is None
    high_descriptor = _parse_b_curve_record(long_descriptor, 0)
    assert high_descriptor is not None
    assert high_descriptor.descriptor_reference == 0xFFFF


def test_used_trimmed_curves_preserve_native_ranges_and_validate_geometry() -> None:
    tables = _tables(WATER_PUMP)
    used_curve_attributes = {
        record.references[3]
        for record in tables.edge_uses.values()
        if len(record.references) > 3
    }
    curves = tuple(
        curve
        for attribute, curve in tables.curves.items()
        if attribute in used_curve_attributes
        and curve.attributes.get("trimmed") is True
    )
    assert len(curves) == 5
    assert sum(isinstance(curve, LineCurve) for curve in curves) == 3
    assert sum(isinstance(curve, CircleCurve) for curve in curves) == 2
    for curve in curves:
        attributes = curve.attributes
        assert len(attributes["header_references"]) == 5
        assert attributes["basis_reference"] > 1
        assert attributes["basis_curve_id"]
        assert attributes["trim_record"]
        evaluated = tuple(
            _curve_point_at_parameter(curve, parameter)
            for parameter in attributes["trim_parameters"]
        )
        assert all(point is not None for point in evaluated)
        assert all(
            math.dist(_coordinates(actual), _coordinates(expected)) <= 1e-7
            for actual, expected in zip(evaluated, attributes["trim_points"])
            if actual is not None
        )
        if isinstance(curve, LineCurve):
            assert attributes["trim_parameters"] == pytest.approx(
                tuple(value * 1000.0 for value in attributes["trim_parameters_native"])
            )
        else:
            assert attributes["trim_parameters"] == attributes["trim_parameters_native"]


def test_trimmed_curve_range_and_point_corruption_fail_closed() -> None:
    tables = _tables(WATER_PUMP)
    curve = next(
        curve
        for curve in tables.curves.values()
        if isinstance(curve, LineCurve) and curve.attributes.get("trimmed") is True
    )
    raw = curve.attributes["trim_record"]
    record = _parse_trimmed_curve_record(raw, 0)
    assert record is not None
    basis = tables.curves[record.basis_reference]
    reversed_range = bytearray(raw)
    struct.pack_into(">d", reversed_range, len(raw) - 8, record.parameters[0] - 0.001)
    range_record = _parse_trimmed_curve_record(bytes(reversed_range), 0)
    assert range_record is not None
    assert _resolve_trimmed_curve(range_record, {record.basis_reference: basis}) is None
    displaced_point = bytearray(raw)
    struct.pack_into(
        ">d", displaced_point, len(raw) - 64, record.points[0].x / 1000.0 + 0.001
    )
    point_record = _parse_trimmed_curve_record(bytes(displaced_point), 0)
    assert point_record is not None
    assert _resolve_trimmed_curve(point_record, {record.basis_reference: basis}) is None


def test_periodic_nurbs_support_proves_the_poppet_intersection() -> None:
    model = decode_brep_model(_partition(POPPET))
    assert model is not None
    assert model.validate() == ()
    assert len(model.faces) == 12
    surface = next(
        surface for surface in model.surfaces if isinstance(surface, NurbsSurface)
    )
    curve = next(
        curve for curve in model.curves if isinstance(curve, IntersectionCurve)
    )
    assert surface.id == curve.second_surface_id
    assert surface.periodic_u is True
    assert surface.periodic_v is False
    assert surface.degree_u == 3
    assert surface.degree_v == 2
    assert len(surface.control_points) == 7
    assert len(surface.control_points[0]) == 97
    lane = curve.attributes["support_uv"][1]
    assert len(lane) == len(curve.samples) == 21
    evaluated = tuple(_nurbs_surface_point(surface, parameters) for parameters in lane)
    assert all(point is not None for point in evaluated)
    assert all(
        math.dist(
            (point.x, point.y, point.z),
            (sample.x, sample.y, sample.z),
        )
        <= curve.tolerance
        for point, sample in zip(evaluated, curve.samples)
        if point is not None
    )


@pytest.mark.parametrize(
    ("path", "face_count", "surface_count", "intersection_count"),
    INTERSECTION_SUPPORT_PARTS,
)
def test_intersection_support_surfaces_remain_reachable_without_owning_faces(
    path: Path, face_count: int, surface_count: int, intersection_count: int
) -> None:
    model = decode_brep_model(_partition(path))
    assert model is not None
    assert model.validate() == ()
    assert len(model.faces) == face_count
    assert len(model.surfaces) == surface_count
    intersections = tuple(
        curve for curve in model.curves if isinstance(curve, IntersectionCurve)
    )
    assert len(intersections) == intersection_count
    surface_ids = frozenset(surface.id for surface in model.surfaces)
    assert all(
        curve.first_surface_id in surface_ids and curve.second_surface_id in surface_ids
        for curve in intersections
    )


def test_nurbs_surface_descriptor_and_weight_corruption_fail_closed() -> None:
    payload = _partition(POPPET)
    model = decode_brep_model(payload)
    assert model is not None
    surface = next(
        surface for surface in model.surfaces if isinstance(surface, NurbsSurface)
    )
    descriptor = bytearray(surface.attributes["descriptor_record"])
    start = _record_start(descriptor, 0, 0x7E)
    assert start is not None
    decoded = _xmt(descriptor, start)
    assert decoded is not None
    descriptor_cursor = start + decoded[1]
    assert descriptor[descriptor_cursor + 24] == 1
    descriptor[descriptor_cursor + 24] = 0
    assert _parse_nurbs_surface_record(bytes(descriptor), 0) is None
    descriptor_offset = payload.find(surface.attributes["descriptor_record"])
    assert descriptor_offset >= 0
    corrupted_descriptor = bytearray(payload)
    corrupted_descriptor[descriptor_offset : descriptor_offset + len(descriptor)] = (
        descriptor
    )
    assert decode_brep_model(corrupted_descriptor) is None
    control = bytearray(surface.attributes["control_record"])
    fields = _array_record_fields(control, 0, 0x2D)
    assert fields is not None
    values_offset = fields[2]
    control[values_offset + 24 : values_offset + 32] = bytes(8)
    control_offset = payload.find(surface.attributes["control_record"])
    assert control_offset >= 0
    corrupted_control = bytearray(payload)
    corrupted_control[control_offset : control_offset + len(control)] = control
    assert decode_brep_model(corrupted_control) is None


def test_compact_generated_nurbs_surface_redecodes_without_inference_ambiguity() -> (
    None
):
    surface = NurbsSurface(
        "surface:generated",
        1,
        1,
        (
            (Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
            (Vector3(1.0, 0.0, 0.0), Vector3(1.0, 1.0, 0.0)),
        ),
        (0.0, 1.0),
        (0.0, 1.0),
        (2, 2),
        (2, 2),
    )
    encoded = bytearray()
    assert _write_nurbs_surface(encoded, 2, surface, 3) == 9
    tables = _scan_partition_records(bytes(encoded))
    assert tables is not None
    decoded = tables.surfaces[2]
    assert isinstance(decoded, NurbsSurface)
    assert decoded.degree_u == decoded.degree_v == 1
    assert decoded.control_points == surface.control_points
    assert decoded.knots_u == decoded.knots_v == (0.0, 1.0)
    assert decoded.multiplicities_u == decoded.multiplicities_v == (2, 2)
    assert decoded.attributes["descriptor_layout"] == "compact"
