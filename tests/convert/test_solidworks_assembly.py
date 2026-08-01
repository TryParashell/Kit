from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from convert.adapters.base import ReadOptions
from convert.adapters.solidworks import SldprtAdapter
from convert.adapters.solidworks.adapter import _companion_payloads
from interchange import ComponentKind, MateAlignment, MateKind, ValueKind


RANDOM = Path(__file__).resolve().parents[2] / "examples" / "Random"
ASSEMBLY = RANDOM / "V8_engine.SLDASM"


@pytest.fixture(scope="module")
def document():
    return SldprtAdapter().read(ASSEMBLY, ReadOptions(include_brep=False))


def test_massive_assembly_recovers_hierarchy_documents_and_history(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    assert document.validate() == ()
    assert len(assembly.definitions) == 68
    assert Counter(definition.kind for definition in assembly.definitions) == {
        ComponentKind.PART: 65,
        ComponentKind.ASSEMBLY: 3,
    }
    assert len(assembly.instances) == 288
    assert assembly.attributes["flattened_occurrence_count"] == 358
    assert len(assembly.documents) == 53
    assert assembly.attributes["linked_part_document_count"] == 51
    assert assembly.attributes["linked_assembly_document_count"] == 2
    assert assembly.attributes["linked_sketch_count"] == 391
    assert assembly.attributes["linked_feature_count"] == 2064
    assert len(document.sketches) == 3
    assert len(document.feature_timeline) == 48
    assert len(document.support_planes) == 6


def test_massive_assembly_recovers_exact_transforms_and_state(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    ring = next(
        instance
        for instance in assembly.instances
        if instance.id == "sldasm:instance:223"
    )
    assert ring.transform.values == (
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        46.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    piston = next(
        instance
        for instance in assembly.instances
        if instance.id == "sldasm:instance:217"
    )
    assert piston.transform.values[3] == pytest.approx(-1.209188127289168e-15)
    assert piston.transform.values[7] == pytest.approx(79.99530923564972)
    assert piston.transform.values[11] == pytest.approx(-79.99530923564954)
    assert next(
        instance
        for instance in assembly.instances
        if instance.id == "sldasm:instance:211"
    ).fixed
    assert all(not instance.suppressed for instance in assembly.instances)


def test_massive_assembly_recovers_root_and_nested_mates_losslessly(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    assert len(assembly.mates) == 632
    assert len(assembly.mate_entities) == 1261
    assert Counter(mate.kind for mate in assembly.mates) == {
        MateKind.CONCENTRIC: 301,
        MateKind.COINCIDENT: 280,
        MateKind.CAM: 32,
        MateKind.BELT: 14,
        MateKind.LOCK: 3,
        MateKind.GEAR: 1,
        MateKind.DISTANCE: 1,
    }
    assert len(assembly.mate_groups) == 3
    assert [len(group.mate_ids) for group in assembly.mate_groups] == [6, 2, 9]
    assert assembly.attributes["flattened_mate_occurrence_count"] == 765
    payloads = [
        payload
        for payload in document.brep_payloads
        if payload.format_id == "solidworks.mates"
    ]
    assert [len(payload.data or b"") for payload in payloads] == [
        2202551,
        18893,
        43184,
    ]
    assert sum(payload.attributes["declared_count"] for payload in payloads) == 638
    assert all(mate.attributes["native_payload_id"] for mate in assembly.mates)


def test_massive_assembly_recovers_distance_mate_value_and_alignment(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    distance = next(mate for mate in assembly.mates if mate.kind == MateKind.DISTANCE)
    assert distance.name == "Distance1"
    assert distance.value is not None
    assert distance.value.value == pytest.approx(20.0)
    assert distance.value.kind == ValueKind.LENGTH
    assert distance.value.unit == "mm"
    assert distance.alignment == MateAlignment.ANTI_ALIGNED
    assert not distance.suppressed
    assert distance.attributes["native_alignment_code"] == 2
    assert distance.attributes["native_value_m"] == pytest.approx(0.02)
    assert distance.attributes["native_value_offset"] == 1640514
    gear = next(mate for mate in assembly.mates if mate.kind == MateKind.GEAR)
    assert gear.value is None
    assert gear.alignment == MateAlignment.UNKNOWN
    assert all(
        mate.value is None and mate.alignment == MateAlignment.UNKNOWN
        for mate in assembly.mates
        if mate.kind == MateKind.BELT
    )


def test_massive_assembly_recovers_every_reusable_mesh(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    assert len(document.meshes) == 65
    assert sum(len(mesh.attributes["faces"]) for mesh in document.meshes) == 4391
    assert sum(len(mesh.vertices) for mesh in document.meshes) == 492148
    assert sum(len(mesh.triangles) for mesh in document.meshes) == 391218
    part_definitions = {
        definition.id
        for definition in assembly.definitions
        if definition.kind == ComponentKind.PART
    }
    meshed_definitions = {
        definition.id for definition in assembly.definitions if definition.mesh_ids
    }
    assert meshed_definitions == part_definitions


def test_nested_assembly_documents_preserve_their_own_timelines(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    nested = [
        linked.document
        for linked in assembly.documents
        if linked.document.source.format_id == "solidworks.sldasm"
    ]
    assert sorted(len(item.feature_timeline) for item in nested) == [22, 22]
    assert sorted(len(item.assembly.mates) for item in nested) == [6, 13]
    assert all(not item.assembly.documents for item in nested)


def test_resolved_assembly_companions_are_retained_exactly() -> None:
    payloads = _companion_payloads(str(ASSEMBLY))
    assert [(payload.format_id, len(payload.data or b"")) for payload in payloads] == [
        ("acis.sat", 62444621),
        ("parasolid.x_t", 8036848),
    ]
    assert payloads[0].attributes["body_count"] == 391
