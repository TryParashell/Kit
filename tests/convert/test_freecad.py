from __future__ import annotations

import hashlib
import io
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile

import pytest

from convert import convert, open_document
from convert.adapters.freecad import FreeCADAdapter


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
FREECAD_EXAMPLES = (
    Path(__file__).parents[3]
    / "Parashell"
    / ".pixi"
    / "envs"
    / "default"
    / "Library"
    / "data"
    / "examples"
)


def test_direct_fcstd_roundtrip_preserves_interchange_and_brep(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    result = convert(SAMPLE, output)
    restored = open_document(output)
    assert restored == result.document
    assert restored.validate() == ()
    assert [payload.sha256 for payload in restored.brep_payloads] == [
        "8c57db227621a15a0a429cdd65dbe3f374e2c1145ef2f3edc3a25b745513bf3d",
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6",
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7",
    ]
    with zipfile.ZipFile(output) as archive:
        archive.testzip()
        names = set(archive.namelist())
        assert "Document.xml" in names
        assert "interchange/document.json" in names
        assert "Fillet1.Edges" in names
        assert (
            len(
                names
                & {
                    "interchange/native/sldprt_brep_0.x_b",
                    "interchange/native/sldprt_brep_1.x_b",
                    "interchange/native/sldprt_brep_2.x_b",
                }
            )
            == 3
        )
        for payload in restored.brep_payloads:
            entry = f"interchange/native/{payload.id.replace(':', '_')}.x_b"
            assert hashlib.sha256(archive.read(entry)).hexdigest() == payload.sha256


def test_fcstd_contains_editable_native_history(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    convert(SAMPLE, output)
    with zipfile.ZipFile(output) as archive:
        root = ET.fromstring(archive.read("Document.xml"))
        objects = root.findall("./Objects/Object")
        types = [item.get("type") for item in objects]
        names = {item.get("name") for item in objects}
        assert types.count("Spreadsheet::Sheet") == 1
        assert types.count("Sketcher::SketchObject") == 5
        assert types.count("Part::Extrusion") == 5
        assert types.count("Part::Cut") == 2
        assert types.count("Part::MultiFuse") == 2
        assert types.count("Part::Fillet") == 1
        assert {
            "Parameters",
            "Sketch1",
            "Sketch2",
            "Sketch3",
            "Sketch4",
            "Sketch6",
            "Boss_Extrude1",
            "Cut_Extrude1",
            "Boss_Extrude2",
            "Cut_Extrude2",
            "Boss_Extrude3",
            "Fillet1",
        } <= names
        count, edge, start_radius, end_radius = struct.unpack(
            "<IIdd", archive.read("Fillet1.Edges")
        )
        assert (count, edge, start_radius, end_radius) == (1, 3, 0.25, 0.25)
        xml = archive.read("Document.xml")
        assert b"KitMetadata" in xml


def test_fcstd_output_is_deterministic(tmp_path) -> None:
    first = tmp_path / "first.FCStd"
    second = tmp_path / "second.FCStd"
    convert(SAMPLE, first)
    convert(SAMPLE, second)
    assert first.read_bytes() == second.read_bytes()


def test_fcstd_stream_probe_does_not_consume_input(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    result = convert(SAMPLE, output)
    stream = io.BytesIO(output.read_bytes())
    assert FreeCADAdapter().probe(stream).confidence == 1.0
    assert stream.tell() == 0
    assert open_document(stream) == result.document


def test_generic_fcstd_is_not_claimed_as_readable() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("Document.xml", "<Document/>")
    assert FreeCADAdapter().probe(stream.getvalue()).confidence == 0.0


def test_native_partdesign_fcstd_restores_history_sketches_and_brep() -> None:
    source = FREECAD_EXAMPLES / "PartDesignExample.FCStd"
    if not source.is_file():
        pytest.skip("bundled FreeCAD PartDesign example is unavailable")
    adapter = FreeCADAdapter()
    assert adapter.probe(source).confidence == 0.95
    document = adapter.read(source)
    assert document.validate() == ()
    assert [
        (sketch.name, len(sketch.entities), len(sketch.constraints))
        for sketch in document.sketches
    ] == [
        ("Sketch", 4, 12),
        ("Sketch001", 4, 11),
        ("Sketch003", 1, 2),
        ("Sketch002", 12, 32),
    ]
    assert [feature.name for feature in document.feature_timeline] == [
        "Pad",
        "Pocket",
        "Pocket001",
        "Pocket002",
    ]
    assert document.bodies[0].final_feature_id == "freecad:feature:Pocket002"
    final_payload = next(
        payload
        for payload in document.brep_payloads
        if payload.source_stream == "Pocket002.Shape.brp"
    )
    assert final_payload.sha256 == (
        "285ae851c79757d7252b67236637f52c776b45b8c42d1e5749109b048d0430c9"
    )
    assert len(final_payload.data or b"") == 51454
