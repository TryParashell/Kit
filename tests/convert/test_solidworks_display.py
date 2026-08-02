from __future__ import annotations

from pathlib import Path

import pytest

from convert.adapters.solidworks.container import SldprtArchive
from convert.adapters.solidworks.display import (
    decode_display_lists,
    decode_tessellation_faces,
    is_component_path,
    neutral_meshes,
)


ASSEMBLY = Path(__file__).parents[2] / "examples" / "Random" / "V8_engine.SLDASM"


@pytest.mark.parametrize(
    "value",
    (
        "Rotor@Assembly",
        "Custom instance name@Root/Nested occurrence@Subassembly",
        "Part-1@Assembly",
    ),
)
def test_component_paths_do_not_require_generated_numeric_suffixes(value: str) -> None:
    assert is_component_path(value)


@pytest.mark.parametrize(
    "value",
    (
        "Top Plane@Rotor@Assembly",
        "Belt1-1^Assembly-1@Assembly",
        "C:/Parts/Rotor.SLDPRT",
        "@Assembly",
    ),
)
def test_component_path_detection_rejects_entity_references_and_files(
    value: str,
) -> None:
    assert not is_component_path(value)


def test_display_lists_recovers_every_face_and_geometry_group() -> None:
    data = SldprtArchive.open(ASSEMBLY).require("Contents/DisplayLists")
    faces = decode_tessellation_faces(data)
    components = decode_display_lists(data)
    assert len(faces) == 4391
    assert sum(len(face.positions_mm) for face in faces) == 492148
    assert sum(len(face.triangle_indices) for face in faces) == 391218
    assert len(components) == 65
    assert sum(len(component.faces) for component in components) == 4391


def test_display_geometry_is_scaled_to_millimeters_and_mapped_to_source() -> None:
    data = SldprtArchive.open(ASSEMBLY).require("Contents/DisplayLists")
    component = decode_display_lists(data)[0]
    face = component.faces[0]
    assert component.occurrence_path == "Journal_bearig_crank-1@V8_engine"
    assert component.source_path.endswith("Journal_bearig_crank.SLDPRT")
    assert face.face_id == 33
    assert face.positions_mm[0] == pytest.approx(
        (-13.599040918052197, 7.011139299720526, -0.9284935076721013)
    )
    assert face.normals[0] == pytest.approx(
        (0.8888262510299683, -0.4582444131374359, 0.0)
    )
    assert max(index for triangle in face.triangle_indices for index in triangle) < len(
        face.positions_mm
    )
    mesh = neutral_meshes((component,))[0]
    assert mesh.vertices[0].x == pytest.approx(-13.599040918052197)
    assert mesh.attributes["occurrence_path"] == component.occurrence_path
    assert mesh.provenance is not None
    assert mesh.provenance.spans[0].stream == "Contents/DisplayLists"
