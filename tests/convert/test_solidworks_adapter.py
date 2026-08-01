from __future__ import annotations

from pathlib import Path

import pytest

from convert.adapters.solidworks import SldprtAdapter, SldprtArchive, read_sldprt
from interchange import (
    BooleanOperation,
    ExtrusionFeature,
    FilletFeature,
    LineGeometry,
    NativeGeometry,
)


SAMPLE = Path(__file__).resolve().parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
CORPUS = Path(__file__).resolve().parents[2] / "examples" / "Random"


def test_container_recovers_native_streams() -> None:
    archive = SldprtArchive.open(SAMPLE)
    assert archive.file_id == 1901848975
    assert archive.format_version == 4
    assert archive.require("Contents/Config-0-ResolvedFeatures")
    assert b"<?xml" in archive.require("swXmlContents/KeyWords")
    assert archive.require("Contents/Config-0-Partition")


def test_container_accepts_variable_record_signature_data() -> None:
    source = bytearray(SAMPLE.read_bytes())
    original = SldprtArchive.from_bytes(source)
    replacement = bytes.fromhex("01020304")
    for record in original.records:
        source[record.offset + 6 : record.offset + 10] = replacement
    recovered = SldprtArchive.from_bytes(source)
    assert len(recovered.records) == len(original.records)
    assert {record.signature[6:] for record in recovered.records} == {replacement}
    assert recovered.require("Contents/Config-0-ResolvedFeatures") == original.require(
        "Contents/Config-0-ResolvedFeatures"
    )


def test_adapter_recovers_parametric_history_and_brep() -> None:
    document = read_sldprt(SAMPLE)
    assert document.validate() == ()
    assert len(document.configurations) == 1
    assert len(document.parameters) == 26
    assert len(document.support_planes) == 7
    assert len(document.sketches) == 5
    assert len(document.feature_timeline) == 38
    assert len(document.brep_payloads) == 3
    assert [payload.kind for payload in document.brep_payloads] == [
        "partition",
        "partition",
        "deltas",
    ]
    assert [len(payload.data or b"") for payload in document.brep_payloads] == [
        1513,
        30850,
        23150,
    ]
    assert document.brep_payloads[1].sha256 == (
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6"
    )
    assert document.brep_payloads[2].sha256 == (
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7"
    )


def test_adapter_recovers_feature_operations_and_dimensions() -> None:
    document = read_sldprt(SAMPLE, include_brep=False)
    operations = {
        feature.name: feature
        for feature in document.feature_timeline
        if feature.name
        in {
            "Boss-Extrude1",
            "Cut-Extrude1",
            "Boss-Extrude2",
            "Cut-Extrude2",
            "Boss-Extrude3",
            "Fillet1",
        }
    }
    assert operations["Boss-Extrude1"].operation == BooleanOperation.JOIN
    assert operations["Cut-Extrude1"].operation == BooleanOperation.CUT
    assert operations["Boss-Extrude2"].operation == BooleanOperation.JOIN
    assert operations["Cut-Extrude2"].operation == BooleanOperation.CUT
    assert operations["Boss-Extrude3"].operation == BooleanOperation.JOIN
    assert isinstance(operations["Boss-Extrude1"].definition, ExtrusionFeature)
    assert isinstance(operations["Fillet1"].definition, FilletFeature)
    assert operations["Boss-Extrude1"].definition.length.value == 20.0
    assert operations["Cut-Extrude1"].definition.length.value == 0.25
    assert operations["Boss-Extrude2"].definition.length.value == 0.75
    assert operations["Cut-Extrude2"].definition.length.value == 9.0
    assert operations["Boss-Extrude3"].definition.length.value == 6.0
    assert operations["Fillet1"].definition.radius.value == 0.25
    assert operations["Boss-Extrude1"].attributes["length_mm"] == 20.0
    assert operations["Cut-Extrude1"].attributes["length_mm"] == 0.25
    assert operations["Boss-Extrude2"].attributes["length_mm"] == 0.75
    assert operations["Cut-Extrude2"].attributes["length_mm"] == 9.0
    assert operations["Boss-Extrude3"].attributes["length_mm"] == 6.0
    assert operations["Fillet1"].attributes["radius_mm"] == 0.25
    assert operations["Fillet1"].selection_ids == ("sldprt:selection:116:edge:1",)
    assert document.parameter("sldprt:parameter:88:D1").value.value == 5.5
    assert document.parameter("sldprt:parameter:106:D1").value.value == 2.1


def test_adapter_recovers_support_frames_and_profiles() -> None:
    document = read_sldprt(SAMPLE, include_brep=False)
    plane2 = document.plane("sldprt:plane:62")
    assert plane2.transform.origin.x == pytest.approx(124.3)
    assert plane2.transform.x_axis.z == -1.0
    assert plane2.transform.y_axis.y == 1.0
    assert plane2.transform.z_axis.x == 1.0
    sketch1 = document.sketch("sldprt:sketch:26")
    profile = [
        entity
        for entity in sketch1.entities
        if entity.id in sketch1.closed_profile_entity_ids[0]
    ]
    assert len(profile) == 4
    assert isinstance(profile[0].geometry, LineGeometry)
    assert profile[0].geometry.start.x == pytest.approx(-124.3)
    assert profile[0].geometry.start.y == pytest.approx(-89.75)
    sketch3 = document.sketch("sldprt:sketch:63")
    assert len(sketch3.closed_profile_entity_ids) == 3
    sketch4 = document.sketch("sldprt:sketch:88")
    circle = next(
        entity
        for entity in sketch4.entities
        if entity.id == sketch4.closed_profile_entity_ids[0][0]
    )
    assert circle.geometry.center.x == pytest.approx(10.0)
    assert circle.geometry.center.y == pytest.approx(81.631746131982)
    assert circle.geometry.radius == pytest.approx(2.75)


def test_adapter_recovers_construction_geometry_without_guessing() -> None:
    document = read_sldprt(SAMPLE, include_brep=False)
    expected_line_counts = {
        "Sketch1": 2,
        "Sketch2": 2,
        "Sketch3": 7,
        "Sketch4": 1,
        "Sketch6": 2,
    }
    for sketch in document.sketches:
        lines = [
            entity.geometry
            for entity in sketch.entities
            if entity.construction and isinstance(entity.geometry, LineGeometry)
        ]
        assert len(lines) == expected_line_counts[sketch.name]
    sketch1 = document.sketch("sldprt:sketch:26")
    diagonals = [
        entity.geometry
        for entity in sketch1.entities
        if entity.construction and isinstance(entity.geometry, LineGeometry)
    ]
    assert {
        (
            line.start.x,
            line.start.y,
            line.end.x,
            line.end.y,
        )
        for line in diagonals
    } == {
        (124.3, 89.75, -124.3, -89.75),
        (124.3, -89.75, -124.3, 89.75),
    }
    assert any(
        isinstance(entity.geometry, NativeGeometry) for entity in sketch1.entities
    )


def test_adapter_resolves_line_endpoints_by_native_marker_index() -> None:
    document = read_sldprt(CORPUS / "Engine_Block.SLDPRT", include_brep=False)
    sketch = document.sketch("sldprt:sketch:139")
    expected = {
        145018: (
            (-98.287842584929, 161.92745289172),
            (-130.107647738324, 130.107647738326),
        ),
        145110: (
            (-130.107647738324, 130.107647738326),
            (-48.790367901871, 48.790367901872),
        ),
        145202: (
            (-48.790367901871, 48.790367901872),
            (-16.970562748477, 80.610173055267),
        ),
        145294: (
            (-16.970562748477, 80.610173055267),
            (-98.287842584929, 161.92745289172),
        ),
    }
    entities = {entity.provenance.spans[0].offset: entity for entity in sketch.entities}
    for offset, (start, end) in expected.items():
        geometry = entities[offset].geometry
        assert isinstance(geometry, LineGeometry)
        assert (geometry.start.x, geometry.start.y) == pytest.approx(start)
        assert (geometry.end.x, geometry.end.y) == pytest.approx(end)


def test_adapter_does_not_resolve_line_through_noncoordinate_marker() -> None:
    document = read_sldprt(CORPUS / "Engine_Block.SLDPRT", include_brep=False)
    sketch = document.sketch("sldprt:sketch:200")
    entity = next(
        entity
        for entity in sketch.entities
        if entity.provenance and entity.provenance.spans[0].offset == 198158
    )
    assert isinstance(entity.geometry, NativeGeometry)


def test_adapter_accepts_memory_and_roundtrips_neutral_json() -> None:
    source = SAMPLE.read_bytes()
    adapter = SldprtAdapter()
    assert adapter.probe(source).confidence == 1.0
    document = read_sldprt(source, include_brep=False)
    restored = type(document).from_json(document.to_json())
    assert restored.validate() == ()
    assert restored.source.path == "<memory>"
    assert restored.feature("sldprt:feature:116").name == "Fillet1"


def test_entire_local_solidworks_corpus_decodes() -> None:
    examples = Path(__file__).resolve().parents[2] / "examples"
    parts = sorted(
        path
        for path in examples.rglob("*")
        if path.is_file() and path.suffix.lower() == ".sldprt"
    )
    documents = [read_sldprt(path) for path in parts]
    assert len(parts) == 54
    assert all(document.validate() == () for document in documents)
    assert sum(len(document.brep_payloads) for document in documents) == 162


def test_adapter_handles_positive_zero_plane_frame_variant() -> None:
    document = read_sldprt(CORPUS / "Addons" / "Alternator.SLDPRT", include_brep=False)
    plane = document.plane("sldprt:plane:289")
    assert plane.transform.origin.z == pytest.approx(50.0)
    assert plane.transform.z_axis.z == 1.0
    assert document.sketch("sldprt:sketch:292").support_plane_id == plane.id
    assert document.validate() == ()


def test_adapter_assigns_occurrence_ids_to_duplicate_dimensions() -> None:
    document = read_sldprt(
        CORPUS / "Cylinder_heads" / "Spark_plug.SLDPRT",
        include_brep=False,
    )
    assert document.parameter("sldprt:parameter:107:D5").value.value == 2.0
    assert document.parameter("sldprt:parameter:107:D5:2").value.value == 2.0
    assert document.validate() == ()
