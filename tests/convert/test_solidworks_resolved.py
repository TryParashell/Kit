from __future__ import annotations

import math
from pathlib import Path

import pytest

from convert import write_document
from convert.adapters.solidworks.container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.format import RESOLVED_FEATURES_STREAM
from convert.adapters.solidworks.resolved import (
    BLIND_END_CONDITION,
    BOSS_FLAGS,
    BOSS_KIND,
    CUT_FLAGS,
    CUT_KIND,
    FEATURE_KIND_BY_FLAGS,
    FIRST_FEATURE_END_CONDITION_DISTANCE,
    FIRST_FEATURE_REVERSE_DISTANCE,
    LATER_FEATURE_END_CONDITION_DISTANCE,
    LATER_FEATURE_REVERSE_DISTANCE,
    MID_PLANE_END_CONDITION,
    PLANE_FLAGS,
    SKETCH_FLAGS,
    FeatureEdit,
    circle_circumference_point_mm,
    circle_radius_mm,
    class_records,
    dimension_scalars,
    locate_features,
    locate_rectangle_pad,
    name_records,
    patch_features,
    rectangle_corners_mm,
    sketch_points,
    tree_nodes,
)

from tests.convert.test_solidworks_writer import _freecad_rectangle_pad_document


CORPUS = Path(__file__).resolve().parents[2] / ".rescratch" / "corpus2"
PARTS = CORPUS / "parts"
PATCHED = CORPUS / "patched"

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


def _patched_stream(name: str) -> bytes:
    archive = SldprtArchive.from_bytes((PATCHED / f"{name}.SLDPRT").read_bytes())
    return archive.require(RESOLVED_FEATURES_STREAM)


def _written_rectangle_pad_stream(tmp_path: Path) -> bytes:
    target = tmp_path / "GeneralLocator.SLDPRT"
    write_document(_freecad_rectangle_pad_document(), target, allow_carrier=False)
    archive = SldprtArchive.from_bytes(target.read_bytes())
    return archive.require(RESOLVED_FEATURES_STREAM)


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
    assert dict(FEATURE_KIND_BY_FLAGS) == {BOSS_FLAGS: BOSS_KIND, CUT_FLAGS: CUT_KIND}
    with pytest.raises(TypeError):
        FEATURE_KIND_BY_FLAGS[SKETCH_FLAGS] = BOSS_KIND


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


def test_written_rectangle_pad_is_reachable_through_the_general_locator(
    tmp_path: Path,
) -> None:
    resolved = _written_rectangle_pad_stream(tmp_path)
    features = locate_features(resolved)
    layout = locate_rectangle_pad(resolved)
    assert layout is not None
    assert len(features) == 1
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
    assert feature.bounds_mm == (-30.0, -15.0, 30.0, 15.0)
    assert feature.depth_mm == pytest.approx(12.0)
    assert feature.reversed is False
    assert feature.end_condition_code == BLIND_END_CONDITION


def test_name_records_expose_the_tree_nodes_and_dimension_scalars(
    tmp_path: Path,
) -> None:
    resolved = _written_rectangle_pad_stream(tmp_path)
    records = name_records(resolved)
    nodes = tree_nodes(resolved)
    assert {node.name for node in nodes} >= {"Sketch1", "Boss-Extrude1"}
    assert {node.offset for node in nodes} <= {record.offset for record in records}
    assert [node.flags for node in nodes if node.name == "Boss-Extrude1"] == [
        BOSS_FLAGS
    ]
    assert [node.flags for node in nodes if node.name == "Sketch1"] == [SKETCH_FLAGS]
    scalars = dimension_scalars(resolved)
    depths = [scalar for scalar in scalars if scalar.name.startswith("D")]
    assert [scalar.value_mm for scalar in depths] == [pytest.approx(12.0)]
    assert len(sketch_points(resolved)) == 4


def test_patch_features_rewrites_a_written_rectangle_pad(tmp_path: Path) -> None:
    resolved = _written_rectangle_pad_stream(tmp_path)
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


def test_patch_features_rejects_edits_the_stream_cannot_hold(tmp_path: Path) -> None:
    resolved = _written_rectangle_pad_stream(tmp_path)
    rejected = (
        {1: FeatureEdit(depth_mm=5.0)},
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
