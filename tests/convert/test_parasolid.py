from __future__ import annotations

from pathlib import Path
import struct

import pytest

from convert.adapters.solidworks.container import SldprtArchive
from convert.adapters.solidworks.format import PARTITION_STREAM
from convert.parasolid import (
    _parasolid_header,
    _parse_coedge,
    decode_brep_model,
    decode_partition_stream,
)
from interchange import NativeCurve


ROOT = Path(__file__).parents[2]
CRANKSHAFT = ROOT / "examples" / "Random" / "Crank" / "Crankshaft.SLDPRT"
FUEL_INJECTOR = ROOT / "examples" / "Random" / "Cylinder_heads" / "Fuel_injector.SLDPRT"
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


def _partition(path: Path) -> bytes:
    stream = SldprtArchive.open(path).require(PARTITION_STREAM)
    return next(
        payload.data
        for payload in decode_partition_stream(stream, PARTITION_STREAM)
        if payload.kind == "partition"
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
