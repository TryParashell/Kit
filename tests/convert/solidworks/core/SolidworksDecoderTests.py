# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import math
from pathlib import Path

import pytest

from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import KEYWORDS_STREAM, RESOLVED_FEATURES_STREAM
from convert.adapters.solidworks.core.Native import DERIVED_SUPPORT_KIND, FACE_SUPPORT_KIND, PLANE_SUPPORT_KIND, NativeModel, NativeProfile, NativeSketch, decode_native_model
from convert.adapters.solidworks.resolved.Core import CIRCLE_POINT_ANGLE_DEGREES, DEPTH_COPY_DELTAS, DEPTH_COPY_SIGNS, FROM_END_SPEC_CLASS, FROM_REVERSE_RELATIVE, class_records, first_class_offset

ROOT = Path(__file__).resolve().parents[4]
CORPUS_PARTS = ROOT / ".rescratch" / "corpus" / "parts"
CORPUS2_PARTS = ROOT / ".rescratch" / "corpus2" / "parts"

corpus_parts = pytest.mark.skipif(
    not CORPUS_PARTS.is_dir(),
    reason="the SOLIDWORKS single-feature corpus is not present in this checkout",
)
corpus2_parts = pytest.mark.skipif(
    not CORPUS2_PARTS.is_dir(),
    reason="the SOLIDWORKS multi-feature corpus is not present in this checkout",
)

FRONT_PLANE_OBJECT_ID = 2
TOP_PLANE_OBJECT_ID = 3
RIGHT_PLANE_OBJECT_ID = 4

FRONT_BASIS = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
TOP_BASIS = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))
RIGHT_BASIS = ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))

PLANE_SUPPORTS = (
    ("PLANE_FRONT", FRONT_PLANE_OBJECT_ID, 3, FRONT_BASIS),
    ("PLANE_TOP", TOP_PLANE_OBJECT_ID, 2, TOP_BASIS),
    ("PLANE_RIGHT", RIGHT_PLANE_OBJECT_ID, 1, RIGHT_BASIS),
)

CIRCLE_RADII = (("CIRCLE_r10", 10.0), ("CIRCLE_r11", 11.0), ("CIRCLE_r20", 20.0))
CIRCLE_CUT_RADII = (("CIRCLECUT_r4", 4.0), ("CIRCLECUT_r6", 6.0))

FRONT_DEPTH_PARTS = (
    ("BASELINE_40x20x10", 10.0),
    ("DEPTH_d11", 11.0),
    ("DEPTH_d20", 20.0),
    ("DEPTH_d50", 50.0),
)

BOUNDING_BOXES = (
    ("BASELINE_40x20x10", (0.0, 0.0, 5.0), 45.82575694955841),
    ("OFFSET_x10_y7", (10.0, 7.0, 5.0), 45.82575694955841),
    ("DEPTH_d50", (0.0, 0.0, 25.0), 67.08203932499369),
    ("MIDPLANE_d10", (0.0, 0.0, 0.0), 45.82575694955841),
    ("REVERSED_d10", (0.0, 0.0, -5.0), 45.82575694955841),
    ("PLANE_TOP", (0.0, 5.0, 0.0), 45.82575694955841),
    ("PLANE_RIGHT", (5.0, 0.0, 0.0), 45.82575694955841),
    ("CIRCLE_r10", (0.0, 0.0, 5.0), 30.0),
)

FACE_SUPPORTED_SKETCHES = (
    ("TWOFEATURES_pad_pad", "Sketch2", CORPUS_PARTS),
    ("TWOPAD_d5", "Sketch2", CORPUS2_PARTS),
    ("CUTFACE_d5", "Sketch2", CORPUS2_PARTS),
    ("THREEFEATURE_pad_cut_pad", "Sketch3", CORPUS2_PARTS),
)

PLANE_SUPPORTED_SECOND_SKETCHES = (
    ("CUTBASE_cd5", "Sketch2"),
    ("CUTMID_d5", "Sketch2"),
    ("PADPLANE_rev_d5", "Sketch2"),
    ("CIRCLECUT_r4", "Sketch2"),
    ("THREEFEATURE_pad_cut_pad", "Sketch2"),
)


def _decode(directory: Path, name: str) -> tuple[NativeModel, bytes]:
    archive = SldprtArchive.from_bytes((directory / f"{name}.SLDPRT").read_bytes())
    resolved = archive.require(RESOLVED_FEATURES_STREAM)
    return decode_native_model(archive.require(KEYWORDS_STREAM), resolved), resolved


def _sketch(model: NativeModel, name: str) -> NativeSketch:
    return next(sketch for sketch in model.sketches if sketch.name == name)


def _circles(sketch: NativeSketch) -> tuple[NativeProfile, ...]:
    return tuple(profile for profile in sketch.profiles if profile.kind == "circle")


@corpus_parts
@pytest.mark.parametrize(("name", "plane_id", "axis_code", "basis"), PLANE_SUPPORTS)
def test_principal_plane_sketches_report_the_stored_support_plane(
    name: str,
    plane_id: int,
    axis_code: int,
    basis: tuple[tuple[float, float, float], ...],
) -> None:
    model, _ = _decode(CORPUS_PARTS, name)
    sketch = _sketch(model, "Sketch1")
    assert sketch.support_plane_id == plane_id
    assert sketch.support_kind == PLANE_SUPPORT_KIND
    reference = sketch.support_plane
    assert reference is not None
    assert reference.plane_object_id == plane_id
    assert reference.axis_code == axis_code
    assert (reference.u_axis, reference.v_axis, reference.normal) == basis
    assert {plane.object_id for plane in model.planes} >= {plane_id}


@corpus_parts
def test_top_and_right_plane_sketches_no_longer_collapse_onto_the_front_plane() -> None:
    reported = {}
    for name, plane_id, _, _ in PLANE_SUPPORTS:
        model, _ = _decode(CORPUS_PARTS, name)
        reported[name] = _sketch(model, "Sketch1").support_plane_id
        assert reported[name] == plane_id
    assert len(set(reported.values())) == len(PLANE_SUPPORTS)


@corpus_parts
def test_the_support_plane_reference_is_read_from_the_sketch_chain_record() -> None:
    model, resolved = _decode(CORPUS_PARTS, "PLANE_TOP")
    reference = _sketch(model, "Sketch1").support_plane
    assert reference is not None
    chain = first_class_offset(class_records(resolved), "moSketchChain_c")
    assert chain is not None
    assert reference.offset == chain + 209
    assert reference.basis_offset == chain + 224


@corpus_parts
@pytest.mark.parametrize(("name", "radius_mm"), CIRCLE_RADII)
def test_circle_radii_are_reconstructed_from_the_stored_circumference_point(
    name: str, radius_mm: float
) -> None:
    model, _ = _decode(CORPUS_PARTS, name)
    circles = _circles(_sketch(model, "Sketch1"))
    assert len(circles) == 1
    center_x, center_y, decoded = circles[0].coordinates
    assert (center_x, center_y) == (0.0, 0.0)
    assert abs(decoded - radius_mm) <= 1.8e-15
    assert circles[0].start_angle_degrees is not None
    assert circles[0].start_angle_degrees == pytest.approx(
        CIRCLE_POINT_ANGLE_DEGREES, abs=1e-12
    )


@corpus2_parts
@pytest.mark.parametrize(("name", "radius_mm"), CIRCLE_CUT_RADII)
def test_second_feature_circle_radii_are_exact(name: str, radius_mm: float) -> None:
    model, _ = _decode(CORPUS2_PARTS, name)
    circles = _circles(_sketch(model, "Sketch2"))
    assert len(circles) == 1
    assert abs(circles[0].coordinates[2] - radius_mm) <= 1.8e-15
    assert circles[0].start_angle_degrees == pytest.approx(
        CIRCLE_POINT_ANGLE_DEGREES, abs=1e-12
    )


@corpus_parts
def test_rectangular_profiles_carry_no_arc_start_angle() -> None:
    model, _ = _decode(CORPUS_PARTS, "BASELINE_40x20x10")
    profiles = _sketch(model, "Sketch1").profiles
    assert [profile.kind for profile in profiles] == ["rectangle"]
    assert profiles[0].start_angle_degrees is None


@corpus_parts
@pytest.mark.parametrize(("name", "depth_mm"), FRONT_DEPTH_PARTS)
def test_all_six_depth_copies_are_modelled(name: str, depth_mm: float) -> None:
    model, _ = _decode(CORPUS_PARTS, name)
    operation = model.operations[0]
    assert operation.length_mm == pytest.approx(depth_mm)
    copies = operation.depth_copies
    assert len(copies) == len(DEPTH_COPY_DELTAS)
    anchor = copies[0].offset
    assert tuple(copy.offset - anchor for copy in copies) == DEPTH_COPY_DELTAS
    assert tuple(copy.sign for copy in copies) == DEPTH_COPY_SIGNS
    for copy in copies:
        assert copy.value_mm == pytest.approx(copy.sign * depth_mm, abs=1e-9)


@corpus2_parts
def test_the_second_feature_depth_copies_use_the_same_layout() -> None:
    model, _ = _decode(CORPUS2_PARTS, "CUTBASE_cd7")
    second = model.operations[1]
    assert second.length_mm == pytest.approx(7.0)
    copies = second.depth_copies
    anchor = copies[0].offset
    assert tuple(copy.offset - anchor for copy in copies) == DEPTH_COPY_DELTAS
    assert tuple(copy.sign for copy in copies) == DEPTH_COPY_SIGNS
    for copy in copies:
        assert copy.value_mm == pytest.approx(copy.sign * 7.0, abs=1e-9)


@corpus2_parts
def test_a_face_supported_second_feature_stores_the_absolute_end_plane_copy() -> None:
    model, _ = _decode(CORPUS2_PARTS, "TWOPAD_d8")
    second = model.operations[1]
    anchor = second.depth_copies[0].offset
    by_delta = {copy.offset - anchor: copy for copy in second.depth_copies}
    assert set(by_delta) == set(DEPTH_COPY_DELTAS)
    assert by_delta[0].value_mm == pytest.approx(8.0, abs=1e-9)
    assert by_delta[72].value_mm == pytest.approx(18.0, abs=1e-9)


@corpus_parts
@pytest.mark.parametrize(("name", "center_mm", "diameter_mm"), BOUNDING_BOXES)
def test_the_bounding_box_cache_is_decoded(
    name: str, center_mm: tuple[float, float, float], diameter_mm: float
) -> None:
    model, resolved = _decode(CORPUS_PARTS, name)
    box = model.bounding_box
    assert box is not None
    offset = first_class_offset(class_records(resolved), "moBBoxCenterData_c")
    assert offset is not None
    assert box.offset == offset + 28
    assert box.center_mm == pytest.approx(center_mm, abs=1e-9)
    assert box.diameter_mm == pytest.approx(diameter_mm, abs=1e-6)


@corpus_parts
def test_the_bounding_sphere_diameter_matches_the_body_half_extents() -> None:
    model, _ = _decode(CORPUS_PARTS, "WIDTH_w100")
    box = model.bounding_box
    assert box is not None
    assert box.diameter_mm == pytest.approx(
        2.0 * math.sqrt(50.0**2 + 10.0**2 + 5.0**2), abs=1e-9
    )


@corpus_parts
@pytest.mark.parametrize(
    ("name", "mirrored"),
    (("BASELINE_40x20x10", 0), ("REVERSED_d10", 1), ("MIDPLANE_d10", 0)),
)
def test_the_mirrored_direction_flag_is_read(name: str, mirrored: int) -> None:
    model, resolved = _decode(CORPUS_PARTS, name)
    operation = model.operations[0]
    offset = first_class_offset(class_records(resolved), FROM_END_SPEC_CLASS)
    assert offset is not None
    assert operation.mirrored_direction_offset == offset + FROM_REVERSE_RELATIVE
    assert operation.mirrored_direction_code == mirrored
    assert operation.mirrored_direction_code == operation.direction_code


@corpus_parts
@pytest.mark.parametrize(
    ("name", "record_end"),
    (
        ("BASELINE_40x20x10", 8280),
        ("PLANE_TOP", 8352),
        ("PLANE_RIGHT", 8352),
        ("CIRCLE_r10", 7881),
    ),
)
def test_the_extrusion_operation_reports_the_record_end(
    name: str, record_end: int
) -> None:
    model, resolved = _decode(CORPUS_PARTS, name)
    operation = model.operations[0]
    assert operation.native_end == record_end
    assert operation.native_end < len(resolved)
    assert operation.native_offset < operation.native_end


@corpus_parts
def test_the_extrusion_record_end_is_the_next_class_marker() -> None:
    model, resolved = _decode(CORPUS_PARTS, "BASELINE_40x20x10")
    operation = model.operations[0]
    records = class_records(resolved)
    extrusion = next(record for record in records if record.name == "moExtrusion_c")
    following = min(
        record.offset for record in records if record.offset > extrusion.offset
    )
    assert operation.native_offset == extrusion.data_offset
    assert operation.native_end == following


@corpus2_parts
@pytest.mark.parametrize(("name", "sketch_name"), PLANE_SUPPORTED_SECOND_SKETCHES)
def test_plane_supported_second_sketches_report_a_plane_support(
    name: str, sketch_name: str
) -> None:
    model, _ = _decode(CORPUS2_PARTS, name)
    sketch = _sketch(model, sketch_name)
    assert sketch.support_kind == PLANE_SUPPORT_KIND
    assert sketch.support_plane_id == FRONT_PLANE_OBJECT_ID
    reference = sketch.support_plane
    assert reference is not None
    assert reference.plane_object_id == FRONT_PLANE_OBJECT_ID
    assert reference.axis_code == 3
    assert reference.basis_offset is None
    assert sketch.native_offset < reference.offset < sketch.native_end


@pytest.mark.parametrize(("name", "sketch_name", "directory"), FACE_SUPPORTED_SKETCHES)
def test_face_supported_sketches_are_not_reported_as_plane_supported(
    name: str, sketch_name: str, directory: Path
) -> None:
    if not directory.is_dir():
        pytest.skip("the SOLIDWORKS corpus is not present in this checkout")
    model, _ = _decode(directory, name)
    sketch = _sketch(model, sketch_name)
    assert sketch.support_kind == FACE_SUPPORT_KIND
    assert sketch.support_plane is None


@corpus_parts
def test_every_corpus_part_decodes_without_diagnostics() -> None:
    for path in sorted(CORPUS_PARTS.glob("*.SLDPRT")):
        if path.name.startswith("~$"):
            continue
        archive = SldprtArchive.from_bytes(path.read_bytes())
        model = decode_native_model(
            archive.require(KEYWORDS_STREAM),
            archive.require(RESOLVED_FEATURES_STREAM),
        )
        assert model.diagnostics == ()
        assert model.bounding_box is not None
        assert model.sketches
        for sketch in model.sketches:
            assert sketch.support_kind in {
                PLANE_SUPPORT_KIND,
                FACE_SUPPORT_KIND,
                DERIVED_SUPPORT_KIND,
            }
