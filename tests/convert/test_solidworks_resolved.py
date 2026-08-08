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
import xml.etree.ElementTree as ElementTree

import pytest

from convert.adapters.solidworks.container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.format import KEYWORDS_STREAM, RESOLVED_FEATURES_STREAM
from convert.adapters.solidworks.resolved import (
    BLIND_END_CONDITION,
    BOSS_FLAGS,
    BOSS_KIND,
    CIRCLE_POINT_ANGLE_DEGREES,
    CUT_FLAGS,
    CUT_KIND,
    FEATURE_FLAGS_MASK,
    FEATURE_KIND_BY_FLAGS,
    FIRST_FEATURE_END_CONDITION_DISTANCE,
    FIRST_FEATURE_REVERSE_DISTANCE,
    FULL_CIRCLE_DEGREES,
    LATER_FEATURE_END_CONDITION_DISTANCE,
    LATER_FEATURE_REVERSE_DISTANCE,
    LOFT_FLAGS,
    LOFT_KIND,
    MID_PLANE_END_CONDITION,
    PLANE_FLAGS,
    ROUND_FLAGS,
    ROUND_KIND,
    SKETCH_FLAGS,
    SKETCH_ON_CURVE_ROLE,
    SKETCH_POINT_CLASS,
    SWEEP_FLAGS,
    SWEEP_KIND,
    SWEEP_SINGLE_PROFILE_FLAGS,
    TREE_NODE_FLAGS,
    FeatureEdit,
    circle_circumference_point_mm,
    circle_radius_mm,
    class_records,
    dimension_scalars,
    feature_kind,
    is_tree_node_flags,
    locate_features,
    locate_rectangle_pad,
    name_records,
    patch_features,
    patch_sketch_arcs,
    rectangle_corners_mm,
    sketch_arcs,
    sketch_coordinates,
    sketch_points,
    tree_nodes,
)

CORPUS = Path(__file__).resolve().parents[2] / ".rescratch" / "corpus2"
PARTS = CORPUS / "parts"
PATCHED = CORPUS / "patched"
AUTHORED_CORPUS = (
    Path(__file__).resolve().parents[2]
    / "examples"
    / "Single Turbo Dual Overhead Cam V8 - KDP - 2024"
)
DIAMETER_PREFIX = "<MOD-DIAM>"
RADIUS_PREFIX = "R"
RECTANGLE_PAD_PART = "CUTBASE_cd5"

BIELA_EXTRUSIONS = (
    (35, BOSS_KIND, 38.0),
    (188, BOSS_KIND, 18.0),
    (204, BOSS_KIND, 30.7),
    (214, CUT_KIND, 46.7),
    (228, CUT_KIND, 5.0),
    (250, CUT_KIND, 9.0),
)
BIELA_CHAMFERS = ((231, 2.0), (236, 1.0), (253, 1.0), (256, 2.0))
TURBO_TUBE_SWEPT_FEATURES = {
    45: LOFT_KIND,
    48: LOFT_KIND,
    64: SWEEP_KIND,
    189: SWEEP_KIND,
    210: SWEEP_KIND,
    234: SWEEP_KIND,
    240: SWEEP_KIND,
}
AUTHORED_KIND_BY_TYPE = {
    "Sweep": SWEEP_KIND,
    "Cut-Sweep": SWEEP_KIND,
    "Loft": LOFT_KIND,
    "Cut-Loft": LOFT_KIND,
    "Chamfer": ROUND_KIND,
    "Fillet": ROUND_KIND,
}

corpus_parts = pytest.mark.skipif(
    not PARTS.is_dir(),
    reason="the SOLIDWORKS multi-feature corpus is not present in this checkout",
)
corpus_patched = pytest.mark.skipif(
    not PATCHED.is_dir(),
    reason="the proven round-trip artefacts are not present in this checkout",
)

CORPUS_FEATURES = {
    "CUTBASE_cd3": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 3.0, 4)),
    "CUTBASE_cd5": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "CUTBASE_cd7": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 7.0, 4)),
    "CUTBASE_s8": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "CUTBASE_s10": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "CUTBASE_s14": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "CUTTHROUGH_s10": ((BOSS_KIND, 10.0, 4), (CUT_KIND, None, 4)),
    "CUTFACE_d5": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "CUTMID_d5": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "PADPLANE_rev_d5": ((BOSS_KIND, 10.0, 4), (BOSS_KIND, 5.0, 4)),
    "TWOPAD_d3": ((BOSS_KIND, 10.0, 4), (BOSS_KIND, 3.0, 4)),
    "TWOPAD_d5": ((BOSS_KIND, 10.0, 4), (BOSS_KIND, 5.0, 4)),
    "TWOPAD_d8": ((BOSS_KIND, 10.0, 4), (BOSS_KIND, 8.0, 4)),
    "THREEFEATURE_pad_cut_pad": (
        (BOSS_KIND, 10.0, 4),
        (CUT_KIND, 5.0, 4),
        (BOSS_KIND, 4.0, 4),
    ),
    "CIRCLECUT_r4": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 0)),
    "CIRCLECUT_r6": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 0)),
    "CONTROL2_A": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "CONTROL2_B": ((BOSS_KIND, 10.0, 4), (CUT_KIND, 5.0, 4)),
    "CONTROL2PAD_A": ((BOSS_KIND, 10.0, 4), (BOSS_KIND, 5.0, 4)),
    "CONTROL2PAD_B": ((BOSS_KIND, 10.0, 4), (BOSS_KIND, 5.0, 4)),
}

CORPUS_END_CONDITIONS = {
    "CUTBASE_cd5": ((False, BLIND_END_CONDITION), (True, BLIND_END_CONDITION)),
    "CUTMID_d5": ((False, BLIND_END_CONDITION), (True, MID_PLANE_END_CONDITION)),
    "CUTFACE_d5": ((False, BLIND_END_CONDITION), (False, BLIND_END_CONDITION)),
    "PADPLANE_rev_d5": ((False, BLIND_END_CONDITION), (True, BLIND_END_CONDITION)),
    "TWOPAD_d5": ((False, BLIND_END_CONDITION), (False, BLIND_END_CONDITION)),
    "CIRCLECUT_r4": ((False, BLIND_END_CONDITION), (True, BLIND_END_CONDITION)),
    "THREEFEATURE_pad_cut_pad": (
        (False, BLIND_END_CONDITION),
        (True, BLIND_END_CONDITION),
        (False, BLIND_END_CONDITION),
    ),
}

PROVEN_ROUND_TRIPS = (
    (
        "A_cutbase_both_features",
        "CUTBASE_cd5",
        {0: (50.0, 30.0, 12.0), 1: (14.0, 14.0, 7.0)},
    ),
    ("B_cutbase_second_feature_only", "CUTBASE_cd5", {1: (8.0, 8.0, 3.0)}),
    (
        "C_twopad_both_features",
        "TWOPAD_d5",
        {0: (45.0, 25.0, 11.0), 1: (12.0, 12.0, 6.0)},
    ),
    (
        "D_threefeature_all_three",
        "THREEFEATURE_pad_cut_pad",
        {0: (60.0, 25.0, 14.0), 1: (12.0, 12.0, 6.0), 2: (6.0, 6.0, 3.0)},
    ),
)


def _corpus_stream(name: str) -> bytes:
    archive = SldprtArchive.from_bytes((PARTS / f"{name}.SLDPRT").read_bytes())
    return archive.require(RESOLVED_FEATURES_STREAM)


def _authored_parts() -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in AUTHORED_CORPUS.glob("*.SLDPRT")
            if not path.name.startswith("~$")
        )
    )


def _authored_resolved_stream(name: str) -> bytes:
    archive = SldprtArchive.from_bytes(
        (AUTHORED_CORPUS / f"{name}.SLDPRT").read_bytes()
    )
    return archive.require(RESOLVED_FEATURES_STREAM)


def _keywords(blob: bytes) -> ElementTree.Element:
    text = blob.decode("utf-8", errors="replace")
    return ElementTree.fromstring(text[text.index("<?xml") :])


def _authored_keywords(name: str) -> ElementTree.Element:
    archive = SldprtArchive.from_bytes(
        (AUTHORED_CORPUS / f"{name}.SLDPRT").read_bytes()
    )
    return _keywords(archive.require(KEYWORDS_STREAM))


def _authored_nodes(keywords: ElementTree.Element) -> dict[int, ElementTree.Element]:
    return {
        int(element.get("id", "-1")): element
        for element in keywords
        if element.get("id", "").isdigit()
    }


def _authored_dimension(element: ElementTree.Element, name: str) -> str | None:
    for dimension in element:
        if dimension.tag == "Dimension" and dimension.get("Name") == name:
            return dimension.text
    return None


def _authored_radii_mm(element: ElementTree.Element) -> tuple[float, ...]:
    radii: list[float] = []
    for dimension in element:
        text = (dimension.text or "").strip()
        if dimension.tag != "Dimension" or not text:
            continue
        if text.startswith(DIAMETER_PREFIX):
            radii.append(float(text[len(DIAMETER_PREFIX) :]) / 2.0)
        elif (
            text.startswith(RADIUS_PREFIX)
            and text[len(RADIUS_PREFIX) :].replace(".", "", 1).isdigit()
        ):
            radii.append(float(text[len(RADIUS_PREFIX) :]))
    return tuple(radii)


def _authored_radii_by_file(keywords: ElementTree.Element) -> tuple[float, ...]:
    return tuple(
        radius for element in keywords for radius in _authored_radii_mm(element)
    )


def _patched_stream(name: str) -> bytes:
    archive = SldprtArchive.from_bytes((PATCHED / f"{name}.SLDPRT").read_bytes())
    return archive.require(RESOLVED_FEATURES_STREAM)


def _rectangle_pad_stream() -> bytes:
    return _corpus_stream(RECTANGLE_PAD_PART)


def _centred_corners(
    width_mm: float, height_mm: float
) -> tuple[tuple[float, float], ...]:
    return rectangle_corners_mm(
        -width_mm / 2.0, -height_mm / 2.0, width_mm / 2.0, height_mm / 2.0
    )


def test_feature_flag_words_have_one_definition_and_map_to_kinds() -> None:
    assert BOSS_FLAGS == 0x40000140
    assert CUT_FLAGS == 0x400201CA
    assert SKETCH_FLAGS == 0x40000000
    assert PLANE_FLAGS == 0xC0000000
    assert ROUND_FLAGS == 0x40000001
    assert SWEEP_FLAGS == 0x40004003
    assert SWEEP_SINGLE_PROFILE_FLAGS == 0x40004002
    assert LOFT_FLAGS == 0x40004404
    assert FEATURE_FLAGS_MASK == 0x7FFFFFFF
    assert dict(FEATURE_KIND_BY_FLAGS) == {
        BOSS_FLAGS: BOSS_KIND,
        CUT_FLAGS: CUT_KIND,
        ROUND_FLAGS: ROUND_KIND,
        SWEEP_FLAGS: SWEEP_KIND,
        SWEEP_SINGLE_PROFILE_FLAGS: SWEEP_KIND,
        LOFT_FLAGS: LOFT_KIND,
    }
    assert TREE_NODE_FLAGS == frozenset(FEATURE_KIND_BY_FLAGS) | {
        SKETCH_FLAGS,
        PLANE_FLAGS,
    }
    with pytest.raises(TypeError):
        FEATURE_KIND_BY_FLAGS[SKETCH_FLAGS] = BOSS_KIND


def test_the_high_flag_bit_is_not_part_of_the_feature_kind() -> None:
    for flags, kind in FEATURE_KIND_BY_FLAGS.items():
        assert feature_kind(flags) == kind
        assert feature_kind(flags | 0x80000000) == kind
        assert is_tree_node_flags(flags)
        assert is_tree_node_flags(flags | 0x80000000)
    assert feature_kind(SKETCH_FLAGS) is None
    assert feature_kind(PLANE_FLAGS) is None
    assert is_tree_node_flags(SKETCH_FLAGS)
    assert is_tree_node_flags(PLANE_FLAGS)
    assert not is_tree_node_flags(0x40001234)


def test_flag_byte_anchors_differ_between_the_first_and_later_features() -> None:
    assert FIRST_FEATURE_REVERSE_DISTANCE == 824
    assert FIRST_FEATURE_END_CONDITION_DISTANCE == 818
    assert LATER_FEATURE_REVERSE_DISTANCE == 721
    assert LATER_FEATURE_END_CONDITION_DISTANCE == 715
    assert (
        FIRST_FEATURE_REVERSE_DISTANCE - FIRST_FEATURE_END_CONDITION_DISTANCE
        == LATER_FEATURE_REVERSE_DISTANCE - LATER_FEATURE_END_CONDITION_DISTANCE
    )


def test_rectangle_corner_order_is_the_proven_sequence() -> None:
    assert rectangle_corners_mm(-20.0, -10.0, 20.0, 10.0) == (
        (-20.0, -10.0),
        (20.0, 10.0),
        (-20.0, 10.0),
        (20.0, -10.0),
    )


def test_circle_geometry_round_trips_through_the_seventeen_degree_point() -> None:
    x, y = circle_circumference_point_mm(4.0)
    assert math.degrees(math.atan2(y, x)) == pytest.approx(17.0)
    assert circle_radius_mm(x, y) == pytest.approx(4.0)
    for radius in (0.0, -1.0, math.nan, math.inf):
        with pytest.raises(SldprtFormatError):
            circle_circumference_point_mm(radius)


@corpus_parts
def test_written_rectangle_pad_is_reachable_through_the_general_locator() -> None:
    resolved = _rectangle_pad_stream()
    features = locate_features(resolved)
    layout = locate_rectangle_pad(resolved)
    assert layout is not None
    assert len(features) == 2
    feature = features[0]
    assert feature.kind == BOSS_KIND
    assert feature.flags == BOSS_FLAGS
    assert feature.feature_id == 32
    assert feature.sketch_name == "Sketch1"
    assert feature.sketch_id == 26
    assert feature.depth_offset == layout.depth_offset
    assert feature.reverse_offset == layout.reverse_offset
    assert feature.end_condition_offset == layout.end_condition_offset
    assert tuple(point.offset for point in feature.points) == tuple(
        x_offset for x_offset, _ in layout.point_offsets
    )
    assert feature.corners_mm == layout.corners_mm
    assert feature.bounds_mm == (-20.0, -10.0, 20.0, 10.0)
    assert feature.depth_mm == pytest.approx(10.0)
    assert feature.reversed is False
    assert feature.end_condition_code == BLIND_END_CONDITION
    assert features[1].kind == CUT_KIND
    assert features[1].depth_offset != layout.depth_offset
    assert features[1].corners_mm != layout.corners_mm


@corpus_parts
def test_name_records_expose_the_tree_nodes_and_dimension_scalars() -> None:
    resolved = _rectangle_pad_stream()
    records = name_records(resolved)
    nodes = tree_nodes(resolved)
    assert {node.name for node in nodes} >= {
        "Sketch1",
        "Boss-Extrude1",
        "Sketch2",
        "Cut-Extrude1",
    }
    assert {node.offset for node in nodes} <= {record.offset for record in records}
    assert [node.flags for node in nodes if node.name == "Boss-Extrude1"] == [
        BOSS_FLAGS
    ]
    assert [node.flags for node in nodes if node.name == "Cut-Extrude1"] == [CUT_FLAGS]
    assert [node.flags for node in nodes if node.name == "Sketch1"] == [SKETCH_FLAGS]
    assert [node.flags for node in nodes if node.name == "Sketch2"] == [SKETCH_FLAGS]
    scalars = dimension_scalars(resolved)
    depths = [scalar for scalar in scalars if scalar.name.startswith("D")]
    assert [scalar.value_mm for scalar in depths] == [
        pytest.approx(10.0),
        pytest.approx(5.0),
    ]
    assert len(sketch_points(resolved)) == 8


@corpus_parts
def test_patch_features_rewrites_a_written_rectangle_pad() -> None:
    resolved = _rectangle_pad_stream()
    corners = rectangle_corners_mm(-11.0, -6.0, 19.0, 8.0)
    patched = patch_features(
        resolved,
        {
            0: FeatureEdit(
                corners_mm=corners,
                depth_mm=7.5,
                reversed=True,
                end_condition_code=MID_PLANE_END_CONDITION,
                update_depth_copies=True,
            )
        },
    )
    assert len(patched) == len(resolved)
    feature = locate_features(patched)[0]
    assert feature.corners_mm == corners
    assert feature.depth_mm == pytest.approx(7.5)
    assert feature.reversed is True
    assert feature.end_condition_code == MID_PLANE_END_CONDITION
    layout = locate_rectangle_pad(patched)
    assert layout is not None
    assert layout.corners_mm == corners
    assert layout.depth_mm == pytest.approx(7.5)
    assert layout.reversed is True
    assert layout.end_condition_code == MID_PLANE_END_CONDITION
    assert patch_features(resolved, {}) == resolved


@corpus_parts
def test_patch_features_rejects_edits_the_stream_cannot_hold() -> None:
    resolved = _rectangle_pad_stream()
    rejected = (
        {9: FeatureEdit(depth_mm=5.0)},
        {0: FeatureEdit(corners_mm=((0.0, 0.0),))},
        {0: FeatureEdit(corners_mm=_centred_corners(math.inf, 4.0))},
        {0: FeatureEdit(depth_mm=0.0)},
        {0: FeatureEdit(depth_mm=math.nan)},
        {0: FeatureEdit(end_condition_code=1)},
        {0: FeatureEdit(update_depth_copies=True)},
    )
    for edits in rejected:
        with pytest.raises(SldprtFormatError):
            patch_features(resolved, edits)


@corpus_parts
@pytest.mark.parametrize("name", sorted(CORPUS_FEATURES))
def test_corpus_parts_locate_every_feature_with_its_measured_parameters(
    name: str,
) -> None:
    features = locate_features(_corpus_stream(name))
    expected = CORPUS_FEATURES[name]
    assert len(features) == len(expected)
    for feature, (kind, depth_mm, point_count) in zip(features, expected, strict=True):
        assert feature.kind == kind
        assert len(feature.points) == point_count
        if depth_mm is None:
            assert feature.depth_mm is None
            assert feature.depth_offset is None
        else:
            assert feature.depth_mm == pytest.approx(depth_mm)


@corpus_parts
def test_cutbase_s14_locates_both_rectangles_and_both_depths() -> None:
    features = locate_features(_corpus_stream("CUTBASE_s14"))
    assert [feature.kind for feature in features] == [BOSS_KIND, CUT_KIND]
    assert [feature.feature_id for feature in features] == [32, 40]
    assert [feature.sketch_name for feature in features] == ["Sketch1", "Sketch2"]
    assert [feature.sketch_id for feature in features] == [26, 33]
    assert features[0].corners_mm == rectangle_corners_mm(-20.0, -10.0, 20.0, 10.0)
    assert features[0].depth_mm == pytest.approx(10.0)
    assert features[1].corners_mm == rectangle_corners_mm(-7.0, -7.0, 7.0, 7.0)
    assert features[1].depth_mm == pytest.approx(5.0)
    assert features[0].depth_offset < features[1].depth_offset


@corpus_parts
def test_third_feature_is_reachable_without_a_class_marker() -> None:
    resolved = _corpus_stream("THREEFEATURE_pad_cut_pad")
    features = locate_features(resolved)
    assert len(features) == 3
    assert [feature.kind for feature in features] == [BOSS_KIND, CUT_KIND, BOSS_KIND]
    assert [feature.feature_id for feature in features] == [32, 40, 47]
    assert [feature.sketch_id for feature in features] == [26, 33, 41]
    assert [feature.depth_mm for feature in features] == [
        pytest.approx(10.0),
        pytest.approx(5.0),
        pytest.approx(4.0),
    ]
    assert features[2].corners_mm == rectangle_corners_mm(-4.0, -4.0, 4.0, 4.0)
    names = [record.name for record in class_records(resolved)]
    assert names.count("moICE_c") == 1
    assert names.count("moExtrusion_c") == 1
    assert "moCut_c" not in names


@corpus_parts
def test_through_all_feature_has_no_depth_scalar_but_keeps_its_sketch() -> None:
    resolved = _corpus_stream("CUTTHROUGH_s10")
    features = locate_features(resolved)
    assert len(features) == 2
    assert features[1].depth_offset is None
    assert features[1].depth_mm is None
    assert features[1].depth_copy_offsets == ()
    assert features[1].reverse_offset is None
    assert features[1].end_condition_offset is None
    assert features[1].corners_mm == rectangle_corners_mm(-5.0, -5.0, 5.0, 5.0)
    corners = rectangle_corners_mm(-6.0, -6.0, 6.0, 6.0)
    patched = patch_features(resolved, {1: FeatureEdit(corners_mm=corners)})
    assert locate_features(patched)[1].corners_mm == corners
    with pytest.raises(SldprtFormatError):
        patch_features(resolved, {1: FeatureEdit(depth_mm=4.0)})


@corpus_parts
@pytest.mark.parametrize("name", sorted(CORPUS_END_CONDITIONS))
def test_direction_and_end_condition_flags_read_back_from_the_corpus(
    name: str,
) -> None:
    features = locate_features(_corpus_stream(name))
    expected = CORPUS_END_CONDITIONS[name]
    assert len(features) == len(expected)
    for feature, (reverse, code) in zip(features, expected, strict=True):
        assert feature.reversed is reverse
        assert feature.end_condition_code == code
        distance = feature.depth_offset - feature.reverse_offset
        assert distance == (
            FIRST_FEATURE_REVERSE_DISTANCE
            if feature.ordinal == 0
            else LATER_FEATURE_REVERSE_DISTANCE
        )


@corpus_parts
def test_patched_flag_bytes_verify_against_the_corpus() -> None:
    resolved = _corpus_stream("CUTMID_d5")
    patched = patch_features(
        resolved,
        {
            1: FeatureEdit(
                depth_mm=9.0,
                reversed=False,
                end_condition_code=BLIND_END_CONDITION,
                update_depth_copies=True,
            )
        },
    )
    assert len(patched) == len(resolved)
    features = locate_features(patched)
    assert features[1].depth_mm == pytest.approx(9.0)
    assert features[1].reversed is False
    assert features[1].end_condition_code == BLIND_END_CONDITION
    assert features[0].depth_mm == pytest.approx(10.0)
    assert features[0].end_condition_code == BLIND_END_CONDITION


@corpus_parts
@corpus_patched
@pytest.mark.parametrize(("name", "donor", "spec"), PROVEN_ROUND_TRIPS)
def test_patch_features_reproduces_the_proven_round_trip_streams(
    name: str, donor: str, spec: dict[int, tuple[float, float, float]]
) -> None:
    resolved = _corpus_stream(donor)
    edits = {
        ordinal: FeatureEdit(
            corners_mm=_centred_corners(width_mm, height_mm), depth_mm=depth_mm
        )
        for ordinal, (width_mm, height_mm, depth_mm) in spec.items()
    }
    assert patch_features(resolved, edits) == _patched_stream(name)


def test_the_authored_corpus_is_present_in_the_checkout() -> None:
    assert AUTHORED_CORPUS.is_dir()
    assert len(_authored_parts()) >= 57


def test_biela_boss_and_cut_features_match_the_keywords_dimensions() -> None:
    features = locate_features(_authored_resolved_stream("BIELA"))
    authored = _authored_nodes(_authored_keywords("BIELA"))
    extrusions = tuple(
        feature for feature in features if feature.kind in {BOSS_KIND, CUT_KIND}
    )
    assert tuple((feature.feature_id, feature.kind) for feature in extrusions) == tuple(
        (identifier, kind) for identifier, kind, _ in BIELA_EXTRUSIONS
    )
    for feature, (identifier, _, depth_mm) in zip(
        extrusions, BIELA_EXTRUSIONS, strict=True
    ):
        element = authored[identifier]
        assert element.tag == "Extrusion"
        assert float(_authored_dimension(element, "D1") or "nan") == pytest.approx(
            depth_mm
        )
        assert feature.depth_mm == pytest.approx(depth_mm)
        assert feature.flags & FEATURE_FLAGS_MASK == (
            BOSS_FLAGS if feature.kind == BOSS_KIND else CUT_FLAGS
        )
        assert feature.flags & 0x80000000
        assert feature.sketch_id is not None
        assert authored[feature.sketch_id].tag == "Sketch"


def test_biela_chamfers_are_classified_as_round_features() -> None:
    features = locate_features(_authored_resolved_stream("BIELA"))
    authored = _authored_nodes(_authored_keywords("BIELA"))
    rounds = tuple(feature for feature in features if feature.kind == ROUND_KIND)
    assert tuple(feature.feature_id for feature in rounds) == tuple(
        identifier for identifier, _ in BIELA_CHAMFERS
    )
    for feature, (identifier, distance_mm) in zip(rounds, BIELA_CHAMFERS, strict=True):
        element = authored[identifier]
        assert AUTHORED_KIND_BY_TYPE[element.get("Type", "")] == ROUND_KIND
        assert float(_authored_dimension(element, "D1") or "nan") == pytest.approx(
            distance_mm
        )
        assert feature.depth_mm == pytest.approx(distance_mm)


def test_turbo_tube_sweeps_and_lofts_match_the_keywords_types() -> None:
    features = locate_features(_authored_resolved_stream("Turbo Tube"))
    authored = _authored_nodes(_authored_keywords("Turbo Tube"))
    swept = {
        feature.feature_id: feature
        for feature in features
        if feature.kind in {SWEEP_KIND, LOFT_KIND}
    }
    assert {
        identifier: feature.kind for identifier, feature in swept.items()
    } == TURBO_TUBE_SWEPT_FEATURES
    for identifier, feature in swept.items():
        element = authored[identifier]
        assert AUTHORED_KIND_BY_TYPE[element.get("Type", "")] == feature.kind
        assert feature.flags & FEATURE_FLAGS_MASK in {
            SWEEP_FLAGS,
            SWEEP_SINGLE_PROFILE_FLAGS,
            LOFT_FLAGS,
        }


def test_biela_circular_profiles_decode_the_authored_diameters() -> None:
    resolved = _authored_resolved_stream("BIELA")
    authored = _authored_nodes(_authored_keywords("BIELA"))
    features = locate_features(resolved)
    circular = {
        feature.feature_id: feature.radii_mm for feature in features if feature.arcs
    }
    assert circular == {
        35: (pytest.approx(22.2), pytest.approx(17.8)),
        214: (pytest.approx(4.5), pytest.approx(4.5)),
        250: (pytest.approx(1.25),),
    }
    for feature in features:
        if not feature.arcs:
            continue
        assert feature.sketch_id is not None
        expected = _authored_radii_mm(authored[feature.sketch_id])
        assert expected
        for arc in feature.arcs:
            assert any(
                math.isclose(arc.radius_mm, radius, rel_tol=1e-9, abs_tol=1e-9)
                for radius in expected
            )
            assert arc.start_angle_degrees == pytest.approx(CIRCLE_POINT_ANGLE_DEGREES)
            assert arc.sweep_angle_degrees == FULL_CIRCLE_DEGREES
            assert arc.full_circle
    assert len(sketch_arcs(resolved)) == 5


def test_arc_records_are_a_centre_followed_by_a_seventeen_degree_rim_point() -> None:
    resolved = _authored_resolved_stream("BIELA")
    coordinates = {
        coordinate.offset: coordinate for coordinate in sketch_coordinates(resolved)
    }
    for arc in sketch_arcs(resolved):
        centre = coordinates[arc.centre_offset]
        rim = coordinates[arc.point_offset]
        assert arc.point_offset > arc.centre_offset
        assert rim.role == SKETCH_ON_CURVE_ROLE
        assert rim.geometry_class == SKETCH_POINT_CLASS
        assert (centre.x_mm, centre.y_mm) == arc.centre_mm
        assert circle_radius_mm(
            rim.x_mm - centre.x_mm, rim.y_mm - centre.y_mm
        ) == pytest.approx(arc.radius_mm)
        offset_x, offset_y = circle_circumference_point_mm(arc.radius_mm)
        assert rim.x_mm == pytest.approx(centre.x_mm + offset_x)
        assert rim.y_mm == pytest.approx(centre.y_mm + offset_y)


def test_authored_corpus_circle_radii_agree_with_the_authored_dimensions() -> None:
    decoded = 0
    matched = 0
    files_with_arcs = 0
    for path in _authored_parts():
        archive = SldprtArchive.from_bytes(path.read_bytes())
        streams = archive.streams
        resolved = streams.get(RESOLVED_FEATURES_STREAM)
        keywords = streams.get(KEYWORDS_STREAM)
        if resolved is None or keywords is None:
            continue
        expected = _authored_radii_by_file(_keywords(keywords))
        arcs = sketch_arcs(resolved)
        files_with_arcs += 1 if arcs else 0
        for arc in arcs:
            decoded += 1
            assert arc.radius_mm > 0.0
            assert math.isfinite(arc.radius_mm)
            matched += any(
                math.isclose(arc.radius_mm, radius, rel_tol=1e-9, abs_tol=1e-9)
                for radius in expected
            )
    assert decoded >= 480
    assert files_with_arcs >= 49
    assert matched / decoded >= 0.85


def test_patch_sketch_arcs_rewrites_an_authored_corpus_radius() -> None:
    resolved = _authored_resolved_stream("BIELA")
    arcs = sketch_arcs(resolved)
    patched = patch_sketch_arcs(resolved, {0: 25.0, 4: 3.5})
    assert len(patched) == len(resolved)
    relocated = sketch_arcs(patched)
    assert len(relocated) == len(arcs)
    assert relocated[0].radius_mm == pytest.approx(25.0)
    assert relocated[4].radius_mm == pytest.approx(3.5)
    assert relocated[1].radius_mm == pytest.approx(arcs[1].radius_mm)
    assert relocated[0].centre_mm == arcs[0].centre_mm
    assert patch_sketch_arcs(resolved, {}) == resolved
    for radii in ({len(arcs): 5.0}, {0: 0.0}, {0: math.inf}, {0: math.nan}):
        with pytest.raises(SldprtFormatError):
            patch_sketch_arcs(resolved, radii)


def test_patch_features_rewrites_the_radii_of_a_circular_profile() -> None:
    resolved = _authored_resolved_stream("BIELA")
    features = locate_features(resolved)
    circular = next(feature for feature in features if feature.feature_id == 214)
    patched = patch_features(
        resolved, {circular.ordinal: FeatureEdit(radii_mm=(6.0, 6.5), depth_mm=44.0)}
    )
    assert len(patched) == len(resolved)
    relocated = locate_features(patched)[circular.ordinal]
    assert relocated.feature_id == 214
    assert relocated.radii_mm == (pytest.approx(6.0), pytest.approx(6.5))
    assert relocated.depth_mm == pytest.approx(44.0)
    assert relocated.bounds_mm is not None
    rejected = (
        {circular.ordinal: FeatureEdit(radii_mm=(6.0,))},
        {circular.ordinal: FeatureEdit(radii_mm=(6.0, -1.0))},
        {circular.ordinal: FeatureEdit(radii_mm=(6.0, math.nan))},
        {features[5].ordinal: FeatureEdit(radii_mm=(6.0,))},
    )
    for edits in rejected:
        with pytest.raises(SldprtFormatError):
            patch_features(resolved, edits)


@corpus_parts
@pytest.mark.parametrize(
    ("name", "radius_mm"), (("CIRCLECUT_r4", 4.0), ("CIRCLECUT_r6", 6.0))
)
def test_circular_cut_reports_its_radius_through_locate_features(
    name: str, radius_mm: float
) -> None:
    resolved = _corpus_stream(name)
    features = locate_features(resolved)
    assert [feature.kind for feature in features] == [BOSS_KIND, CUT_KIND]
    circular = features[1]
    assert circular.points == ()
    assert len(circular.arcs) == 1
    arc = circular.arcs[0]
    assert arc.radius_mm == pytest.approx(radius_mm)
    assert arc.centre_mm == (pytest.approx(0.0), pytest.approx(0.0))
    assert circular.bounds_mm == (
        pytest.approx(-radius_mm),
        pytest.approx(-radius_mm),
        pytest.approx(radius_mm),
        pytest.approx(radius_mm),
    )
    patched = patch_features(resolved, {1: FeatureEdit(radii_mm=(radius_mm + 1.5,))})
    assert locate_features(patched)[1].arcs[0].radius_mm == pytest.approx(
        radius_mm + 1.5
    )
