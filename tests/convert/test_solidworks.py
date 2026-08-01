from __future__ import annotations

from pathlib import Path

from convert.adapters.solidworks.adapter import SldprtAdapter
from convert.adapters.solidworks.container import SldprtArchive
from interchange import BooleanOperation, Capability, CircleGeometry, LineGeometry


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"


def test_container_recovers_every_integrity_checked_stream() -> None:
    archive = SldprtArchive.open(SAMPLE)
    assert archive.format_version == 4
    assert len(archive.records) == 44
    assert archive.records[0].name == "Contents/3DExperienceExchange2"
    assert archive.records[-1].name == "swXmlContents/KeyWords"
    assert {record.name for record in archive.records} >= {
        "Contents/Config-0-ResolvedFeatures",
        "Contents/Config-0-Partition",
        "PreviewPNG",
        "Header2",
        "Preview",
    }


def test_parametric_history_is_native_and_ordered() -> None:
    document = SldprtAdapter().read(SAMPLE)
    operations = [
        feature
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
    ]
    assert [feature.name for feature in operations] == [
        "Boss-Extrude1",
        "Cut-Extrude1",
        "Boss-Extrude2",
        "Cut-Extrude2",
        "Boss-Extrude3",
        "Fillet1",
    ]
    assert [feature.operation for feature in operations[:-1]] == [
        BooleanOperation.JOIN,
        BooleanOperation.CUT,
        BooleanOperation.JOIN,
        BooleanOperation.CUT,
        BooleanOperation.JOIN,
    ]
    assert [
        document.parameter(feature.parameter_ids[0]).value.value
        for feature in operations
    ] == [20.0, 0.25, 0.75, 9.0, 6.0, 0.25]
    assert Capability.PARAMETRIC_HISTORY in document.capabilities
    assert Capability.EDITABLE_SKETCHES in document.capabilities
    assert document.validate() == ()


def test_sketch_profiles_and_support_planes_are_exact() -> None:
    document = SldprtAdapter().read(SAMPLE)
    assert len(document.sketches) == 5
    first = document.sketch("sldprt:sketch:26")
    first_edges = [
        entity.geometry
        for entity in first.entities
        if entity.id in first.closed_profile_entity_ids[0]
    ]
    assert all(isinstance(edge, LineGeometry) for edge in first_edges)
    assert first_edges[0].start.x == -124.3
    assert first_edges[0].start.y == -89.75
    assert first_edges[2].start.x == 124.3
    assert first_edges[2].start.y == 89.75
    hole = document.sketch("sldprt:sketch:88")
    hole_profile = next(
        entity.geometry
        for entity in hole.entities
        if entity.id == hole.closed_profile_entity_ids[0][0]
    )
    assert isinstance(hole_profile, CircleGeometry)
    assert hole_profile.center.x == 10.0
    assert hole_profile.center.y == 81.631746131982
    assert hole_profile.radius == 2.75
    assert document.plane("sldprt:plane:62").transform.origin.x == 124.30000000000001
    assert document.plane("sldprt:plane:104").transform.origin.x == -115.3


def test_parasolid_brep_is_preserved_byte_for_byte() -> None:
    document = SldprtAdapter().read(SAMPLE)
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
    assert [payload.sha256 for payload in document.brep_payloads] == [
        "8c57db227621a15a0a429cdd65dbe3f374e2c1145ef2f3edc3a25b745513bf3d",
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6",
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7",
    ]
    assert all(
        payload.data is not None and payload.data.startswith(b"PS\0\0")
        for payload in document.brep_payloads
    )


def test_neutral_json_roundtrip_keeps_history_and_brep() -> None:
    source = SldprtAdapter().read(SAMPLE)
    restored = type(source).from_json(source.to_json())
    assert restored == source
