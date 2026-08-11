# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib
from pathlib import Path

from convert.adapters.freecad.brep import triangle_mesh_brep
from convert.adapters.freecad.native import _decoded_document_brep, read_native_fcstd
from convert.opencascade import decode_ascii_brep, is_structurally_valid_ascii_brep
from interchange import Body, BrepPayload, PayloadRole

EXAMPLES = Path(__file__).parents[2] / "examples" / "Random" / "V8_engine"


def _replace_geometry_line(data: bytes, table: bytes, replacement: bytes) -> bytes:
    lines = data.splitlines(keepends=True)
    table_index = next(
        index for index, line in enumerate(lines) if line.startswith(table)
    )
    lines[table_index + 1] = replacement + b"\n"
    return b"".join(lines)


def _located_triangle_brep() -> bytes:
    data = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    )
    data = data.replace(
        b"Locations 0\n",
        b"Locations 1\n1\n1 0 0 0\n0 1 0 0\n0 0 1 0\n",
        1,
    )
    head, separator, tail = data.rpartition(b"+1 0")
    assert separator
    return head + b"+1 1" + tail


def _face_triangulation_fixture(surface: int, tail: bytes) -> bytes:
    surfaces = (
        b"Surfaces 0\n" if surface == 0 else b"Surfaces 1\n1 0 0 0 0 0 1 1 0 0 0 1 0\n"
    )
    return b"".join(
        (
            b"DBRep_DrawableShape\n\n"
            b"CASCADE Topology V1, (c) Matra-Datavision\n"
            b"Locations 0\nCurve2ds 0\nCurves 0\nPolygon3D 0\n"
            b"PolygonOnTriangulations 0\n",
            surfaces,
            b"Triangulations 1\n"
            b"3 1 0 0\n"
            b"0 0 0 1 0 0 0 1 0 1 2 3\n"
            b"TShapes 1\nFa\n",
            f"0 0 {surface} 0".encode("ascii"),
            tail,
            b"0101000\n*\n+1 0\n",
        )
    )


def _polygon_triangulation_fixture() -> bytes:
    return b"".join(
        (
            b"DBRep_DrawableShape\n\n"
            b"CASCADE Topology V1, (c) Matra-Datavision\n"
            b"Locations 0\nCurve2ds 0\nCurves 0\nPolygon3D 0\n"
            b"PolygonOnTriangulations 1\n"
            b"2 1 4\np 0 0\n"
            b"Surfaces 0\nTriangulations 2\n"
            b"4 1 0 0\n"
            b"0 0 0 1 0 0 1 1 0 0 1 0 1 2 3\n"
            b"3 1 0 0\n"
            b"0 0 0 1 0 0 0 1 0 1 2 3\n"
            b"TShapes 3\n"
            b"Ve\n0 0 0 0 0 0\n0101101\n*\n"
            b"Ve\n0 1 0 0 0 0\n0101101\n*\n"
            b"Ed\n0 1 1 0\n6 1 1 0\n0\n0101000\n+3 0 -2 0 *\n"
            b"+1 0\n",
        )
    )


def test_ascii_brep_decoder_normalizes_open_shell_topology() -> None:
    data = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    )
    model = decode_ascii_brep(data, id_prefix="test:triangle")
    assert model is not None
    assert len(model.curves) == 3
    assert len(model.surfaces) == 1
    assert len(model.vertices) == 3
    assert len(model.edges) == 3
    assert len(model.faces) == 1
    assert len(model.shells) == 1
    assert len(model.regions) == 1
    assert not model.regions[0].solid
    assert model.validate() == ()


def test_ascii_brep_decoder_normalizes_closed_solid_topology() -> None:
    data = triangle_mesh_brep(
        ((0, 0, 0), (2, 0, 0), (0, 3, 0), (0, 0, 4)),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )
    model = decode_ascii_brep(data, id_prefix="test:solid")
    assert model is not None
    assert len(model.faces) == 4
    assert len(model.shells) == 1
    assert model.shells[0].closed
    assert len(model.regions) == 1
    assert model.regions[0].solid
    assert model.validate() == ()


def test_ascii_brep_decoder_rejects_non_unit_line_direction() -> None:
    data = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    malformed = _replace_geometry_line(data, b"Curves ", b"1 0 0 0 2 0 0 ")
    assert decode_ascii_brep(malformed) is None


def test_ascii_brep_decoder_accepts_indirect_plane_frame() -> None:
    data = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    indirect = _replace_geometry_line(
        data,
        b"Surfaces ",
        b"1 0 0 0 0 0 1 1 0 0 0 -1 0 ",
    )
    assert decode_ascii_brep(indirect) is not None


def test_ascii_brep_decoder_rejects_nonorthogonal_plane_frame() -> None:
    data = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    malformed = _replace_geometry_line(
        data,
        b"Surfaces ",
        b"1 0 0 0 0 0 1 1 0 0 1 0 0 ",
    )
    assert decode_ascii_brep(malformed) is None


def test_ascii_brep_decoder_rejects_unsupported_curve_family() -> None:
    data = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    malformed = _replace_geometry_line(
        data,
        b"Curves ",
        b"3 0 0 0 0 0 1 1 0 0 0 1 0 2 1 ",
    )
    assert decode_ascii_brep(malformed) is None


def test_ascii_brep_decoder_applies_complete_native_location() -> None:
    data = _located_triangle_brep()
    assert is_structurally_valid_ascii_brep(data)
    model = decode_ascii_brep(data)
    assert model is not None
    assert model.validate() == ()
    assert {
        (vertex.point.x, vertex.point.y, vertex.point.z) for vertex in model.vertices
    } == {
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (0.0, 3.0, 0.0),
    }


def test_ascii_brep_decoder_applies_location_translation() -> None:
    data = _located_triangle_brep().replace(
        b"1 0 0 0\n0 1 0 0\n0 0 1 0\n",
        b"1 0 0 11\n0 1 0 -7\n0 0 1 5\n",
        1,
    )
    model = decode_ascii_brep(data)
    assert model is not None
    assert {
        (vertex.point.x, vertex.point.y, vertex.point.z) for vertex in model.vertices
    } == {
        (11.0, -7.0, 5.0),
        (13.0, -7.0, 5.0),
        (11.0, -4.0, 5.0),
    }
    ChildData = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    ).replace(
        b"Locations 0\n",
        b"Locations 1\n1\n1 0 0 11\n0 1 0 -7\n0 0 1 5\n",
        1,
    )
    ShellHead, ShellMarker, ShellTail = ChildData.rpartition(b"+2 0 *")
    assert ShellMarker
    ChildModel = decode_ascii_brep(ShellHead + b"+2 1 *" + ShellTail)
    assert ChildModel is not None
    assert ChildModel.validate() == ()
    assert {
        (Vertex.point.x, Vertex.point.y, Vertex.point.z)
        for Vertex in ChildModel.vertices
    } == {
        (11.0, -7.0, 5.0),
        (13.0, -7.0, 5.0),
        (11.0, -4.0, 5.0),
    }


# nested placements use OpenCascade's child-before-parent composition convention
def test_ascii_brep_decoder_composes_nested_locations_in_native_order() -> None:
    DataValue = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    )
    DataValue = DataValue.replace(
        b"Locations 0\n",
        b"Locations 2\n"
        b"1\n0 -1 0 0\n1 0 0 0\n0 0 1 0\n"
        b"1\n1 0 0 10\n0 1 0 0\n0 0 1 0\n",
        1,
    )
    DataValue = DataValue.replace(b"+2 0 *", b"+2 2 *", 1)
    HeadData, MarkerData, TailData = DataValue.rpartition(b"+1 0")
    assert MarkerData
    DecodedData = decode_ascii_brep(HeadData + b"+1 1" + TailData)
    assert DecodedData is not None
    assert DecodedData.validate() == ()
    assert {
        (VertexData.point.x, VertexData.point.y, VertexData.point.z)
        for VertexData in DecodedData.vertices
    } == {
        (10.0, 0.0, 0.0),
        (10.0, 2.0, 0.0),
        (7.0, 0.0, 0.0),
    }


def test_structural_validator_requires_exact_physical_version_line() -> None:
    data = _located_triangle_brep()
    version = b"CASCADE Topology V1, (c) Matra-Datavision"
    split = data.replace(
        version,
        b"CASCADE\nTopology V1, (c) Matra-Datavision",
        1,
    )
    unsupported_first = data.replace(
        version,
        b"CASCADE Topology V2, (c) Matra-Datavision\n" + version,
        1,
    )
    payload = data[data.index(version) :]
    bare_carriage_return = b"junk\r" + payload
    assert not is_structurally_valid_ascii_brep(split)
    assert not is_structurally_valid_ascii_brep(unsupported_first)
    assert not is_structurally_valid_ascii_brep(bare_carriage_return)


def test_structural_validator_matches_location_table_normalization() -> None:
    data = _located_triangle_brep()
    location = b"1\n1 0 0 0\n0 1 0 0\n0 0 1 0\n"
    unique = data.replace(
        b"Locations 1\n" + location,
        b"Locations 2\n" + location + b"2 1 2 0\n",
        1,
    )
    duplicate = unique.replace(b"2 1 2 0", b"2 1 1 0", 1)
    identity = unique.replace(b"2 1 2 0", b"2 1 1 1 -1 0", 1)
    singular = data.replace(
        location,
        b"1\n0 0 0 0\n0 0 0 0\n0 0 0 0\n",
        1,
    )
    assert is_structurally_valid_ascii_brep(unique)
    assert not is_structurally_valid_ascii_brep(duplicate)
    assert not is_structurally_valid_ascii_brep(identity)
    assert not is_structurally_valid_ascii_brep(singular)


def test_structural_validator_requires_face_triangulation_line_position() -> None:
    immediate = _face_triangulation_fixture(1, b"\n2 1\n\n")
    same_line = _face_triangulation_fixture(1, b" 2 1\n\n")
    blank_line = _face_triangulation_fixture(1, b"\n\n2 1\n\n")
    indented = _face_triangulation_fixture(1, b"\n 2 1\n\n")
    split_index = _face_triangulation_fixture(1, b"\n2\n1\n\n")
    trailing = _face_triangulation_fixture(1, b"\n2 1 0101000\n\n")
    surface_zero_valid = _face_triangulation_fixture(0, b"\n2 1\n\n")
    surface_zero_missing = _face_triangulation_fixture(0, b"\n\n")
    assert is_structurally_valid_ascii_brep(immediate)
    assert not is_structurally_valid_ascii_brep(same_line)
    assert not is_structurally_valid_ascii_brep(blank_line)
    assert not is_structurally_valid_ascii_brep(indented)
    assert not is_structurally_valid_ascii_brep(split_index)
    assert not is_structurally_valid_ascii_brep(trailing)
    assert is_structurally_valid_ascii_brep(surface_zero_valid)
    assert not is_structurally_valid_ascii_brep(surface_zero_missing)


def test_structural_validator_binds_polygon_nodes_to_triangulation() -> None:
    data = _polygon_triangulation_fixture()
    wrong = data.replace(b"6 1 1 0", b"6 1 2 0", 1)
    closed = data.replace(
        b"PolygonOnTriangulations 1\n2 1 4\np 0 0\n",
        b"PolygonOnTriangulations 2\n" b"2 1 2\np 0 0\n" b"2 1 4\np 0 0\n",
        1,
    ).replace(b"6 1 1 0", b"7 1 2 1 0", 1)
    closed_wrong = closed.replace(b"7 1 2 1 0", b"7 1 2 2 0", 1)
    assert is_structurally_valid_ascii_brep(data)
    assert not is_structurally_valid_ascii_brep(wrong)
    assert is_structurally_valid_ascii_brep(closed)
    assert not is_structurally_valid_ascii_brep(closed_wrong)


def test_structural_validator_rejects_incomplete_or_ambiguous_brep() -> None:
    data = _located_triangle_brep()
    tshapes = next(line for line in data.splitlines() if line.startswith(b"TShapes "))
    shape_count = int(tshapes.split()[1])
    surface_line = next(
        line
        for index, line in enumerate(data.splitlines())
        if index > 0 and data.splitlines()[index - 1].startswith(b"Surfaces ")
    )
    surface_tokens = surface_line.split()
    surface_tokens[-1] = b"0" * 40
    long_number = data.replace(
        surface_line,
        b" ".join(surface_tokens),
        1,
    )
    root_head, root_separator, root_tail = data.rpartition(b"+1 1")
    assert root_separator
    malformed = (
        b"CASCADE Topology V1, (c) Matra-Datavision\n",
        data[: len(data) // 2],
        data[:-10],
        data + b" trailing",
        data.replace(b"V1,", b"V2,", 1),
        data.replace(tshapes, f"TShapes {shape_count + 1}".encode("ascii"), 1),
        data.replace(b"+1 1", b"+999999 1", 1),
        data.replace(b"Locations 1\n1\n1 ", b"Locations 1\n1\nnan ", 1),
        long_number,
        root_head + b"+2 1" + root_tail,
    )
    assert all(not is_structurally_valid_ascii_brep(value) for value in malformed)


def test_native_fcstd_decodes_only_provable_final_shape_and_keeps_raw() -> None:
    path = EXAMPLES / "Piston_shaft.FCStd"
    document = read_native_fcstd(path.read_bytes(), str(path))
    payloads = tuple(
        value for value in document.brep_payloads if value.role == PayloadRole.BREP
    )
    assert len(payloads) == 1
    assert payloads[0].data is not None
    assert document.brep is not None
    assert document.brep.bodies[0].design_body_id == document.bodies[0].id
    assert document.brep.bodies[0].attributes["brep_payload_id"] == payloads[0].id
    assert document.brep.validate(frozenset({document.bodies[0].id})) == ()


def test_native_fcstd_leaves_intermediate_shape_raw_only() -> None:
    path = EXAMPLES / "Alternator.FCStd"
    document = read_native_fcstd(path.read_bytes(), str(path))
    payloads = tuple(
        value for value in document.brep_payloads if value.role == PayloadRole.BREP
    )
    assert len(payloads) == 1
    assert payloads[0].data is not None
    assert payloads[0].attributes["feature_id"] != document.bodies[0].final_feature_id
    assert document.brep is None


def test_final_shape_ownership_merges_multiple_design_bodies() -> None:
    data = triangle_mesh_brep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    digest = hashlib.sha256(data).hexdigest()
    bodies = (
        Body("body:first", "First", "feature:first"),
        Body("body:second", "Second", "feature:second"),
    )
    payloads = tuple(
        BrepPayload(
            f"payload:{index}",
            "opencascade",
            "shape",
            "CASCADE Topology V1",
            digest,
            data=data,
            attributes={"feature_id": body.final_feature_id},
            role=PayloadRole.BREP,
            file_extension=".brep",
        )
        for index, body in enumerate(bodies, 1)
    )
    model = _decoded_document_brep(payloads, bodies)
    assert model is not None
    assert {value.design_body_id for value in model.bodies} == {
        "body:first",
        "body:second",
    }
    assert model.validate(frozenset(value.id for value in bodies)) == ()
    OwnedPayload = BrepPayload(
        "payload:owned",
        "opencascade",
        "shape",
        "CASCADE Topology V1",
        digest,
        data=data,
        attributes={"body_id": bodies[0].id},
        role=PayloadRole.BREP,
        file_extension=".brep",
    )
    SelectedModel = _decoded_document_brep(
        (OwnedPayload, *payloads),
        bodies,
    )
    assert SelectedModel is not None
    assert len(SelectedModel.bodies) == 2
