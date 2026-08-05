# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
from io import BytesIO

import math

import pytest

from convert.adapters.solidworks import read_sldprt, write_sldprt
from convert.adapters.solidworks.adapter import _document_without_source
from convert.adapters.solidworks.container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.donor_library import (
    BOSS_OPERATION,
    CUT_OPERATION,
    DONOR_LIBRARY,
    FULL_REVOLUTION_END,
    RECTANGLE_PROFILE,
    FRONT_SKETCH_AXIS_SUPPORT,
    REVOLVE_BOSS_OPERATION,
    REVOLVE_CUT_OPERATION,
    RIGHT_SUPPORT,
    SUPPORTED_END_CONDITIONS,
    DEPTHLESS_END_CONDITIONS,
    TargetFeature,
    donor_by_id,
    patch_donor,
)
from convert.adapters.solidworks.parasolid import encode_blank_partition_stream
from convert.adapters.solidworks.donor_match import (
    DonorDecline,
    DonorMatch,
    _body_groups,
    _model_bodies,
    _reverse_flag,
    _support,
    _target_feature,
    match_document,
)
from convert.adapters.solidworks.format import (
    KEYWORDS_STREAM,
    KIT_DOCUMENT_STREAM,
    KIT_RESOLVED_STREAM,
    PARTITION_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.resolved import locate_features, rectangle_corners_mm
from interchange import (
    Body,
    BooleanOperation,
    CadDocument,
    CircleGeometry,
    ArcGeometry,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    GeometryKind,
    LineGeometry,
    NativeFeatureDefinition,
    Parameter,
    ParameterValue,
    RevolutionFeature,
    Sketch,
    SketchEntity,
    SupportPlane,
    Transform,
    ValueKind,
    Vector2,
    Vector3,
    frozen_mapping,
)

from tests.interchange.test_document import document

FRONT_PLANE = SupportPlane("plane:front", "Front", Transform())
FREECAD_YZ_PLANE = SupportPlane(
    "plane:yz",
    "YZ_Plane",
    Transform(
        x_axis=Vector3(0.0, 1.0, 0.0),
        y_axis=Vector3(0.0, 0.0, 1.0),
        z_axis=Vector3(1.0, 0.0, 0.0),
    ),
)


def _rectangle_entities(
    prefix: str,
    minimum_x: float,
    minimum_y: float,
    maximum_x: float,
    maximum_y: float,
) -> tuple[SketchEntity, ...]:
    points = (
        Vector2(minimum_x, minimum_y),
        Vector2(maximum_x, minimum_y),
        Vector2(maximum_x, maximum_y),
        Vector2(minimum_x, maximum_y),
    )
    return tuple(
        SketchEntity(
            f"{prefix}:edge:{index}",
            GeometryKind.LINE,
            LineGeometry(points[index], points[(index + 1) % 4]),
        )
        for index in range(4)
    )


def _sketch(
    identifier: str,
    plane_id: str,
    entities: tuple[SketchEntity, ...],
    *,
    loop: tuple[str, ...] | None = None,
    suppressed: bool = False,
) -> Sketch:
    model = tuple(item.id for item in entities if not item.construction)
    return Sketch(
        identifier,
        identifier,
        plane_id,
        entities,
        closed_profile_entity_ids=(loop if loop is not None else model,),
        suppressed=suppressed,
    )


def _extrusion(
    identifier: str,
    order: int,
    sketch_id: str,
    depth_mm: float,
    *,
    operation: BooleanOperation,
    reversed_flag: bool = False,
    direction: Vector3 | None = Vector3(0.0, 0.0, 1.0),
    inputs: tuple[str, ...] = (),
) -> FeatureStep:
    return FeatureStep(
        identifier,
        identifier,
        FeatureKind.EXTRUSION,
        order,
        sketch_id=sketch_id,
        operation=operation,
        input_feature_ids=inputs,
        definition=ExtrusionFeature(
            ParameterValue(depth_mm, ValueKind.LENGTH, "mm"),
            reversed=reversed_flag,
            direction=direction,
        ),
    )


def _document(
    planes: tuple[SupportPlane, ...],
    sketches: tuple[Sketch, ...],
    timeline: tuple[FeatureStep, ...],
    bodies: tuple[Body, ...],
) -> CadDocument:
    source = document()
    return replace(
        source,
        source=replace(source.source, format_id="freecad.fcstd", path="Donor.FCStd"),
        support_planes=planes,
        sketches=sketches,
        feature_timeline=timeline,
        bodies=bodies,
    )


def _single_boss(**overrides: object) -> CadDocument:
    entities = _rectangle_entities("boss", -20.0, -10.0, 20.0, 10.0)
    sketch = _sketch(
        "sketch:boss",
        FRONT_PLANE.id,
        entities,
        suppressed=bool(overrides.get("hidden_sketch", False)),
    )
    feature = _extrusion(
        "feature:boss",
        0,
        sketch.id,
        10.0,
        operation=BooleanOperation.CREATE,
        reversed_flag=bool(overrides.get("reversed_flag", False)),
    )
    return _document(
        (FRONT_PLANE,),
        (sketch,),
        (feature,),
        (Body("body:1", "Body", feature.id),),
    )


def test_donor_match_accepts_a_hidden_consumed_sketch() -> None:
    outcome = match_document(_single_boss(hidden_sketch=True))
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "boss1_front_rect_blind"
    assert outcome.targets[0].profile == RECTANGLE_PROFILE
    assert outcome.targets[0].operation == BOSS_OPERATION


def test_donor_match_ignores_construction_geometry() -> None:
    entities = _rectangle_entities("boss", -20.0, -10.0, 20.0, 10.0)
    guide = SketchEntity(
        "boss:guide",
        GeometryKind.LINE,
        LineGeometry(Vector2(-20.0, 0.0), Vector2(20.0, 0.0)),
        construction=True,
    )
    sketch = _sketch("sketch:boss", FRONT_PLANE.id, (*entities, guide))
    feature = _extrusion(
        "feature:boss", 0, sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (sketch,),
            (feature,),
            (Body("body:1", "Body", feature.id),),
        )
    )
    assert isinstance(outcome, DonorMatch)
    assert outcome.targets[0].points_mm == (
        (-20.0, -10.0),
        (20.0, 10.0),
        (-20.0, 10.0),
        (20.0, -10.0),
    )


def test_reverse_flag_maps_a_cut_against_the_boss_frame() -> None:
    support = _support(FRONT_PLANE)
    assert support is not None
    forward = ExtrusionFeature(
        ParameterValue(10.0, ValueKind.LENGTH, "mm"),
        direction=Vector3(0.0, 0.0, 1.0),
    )
    backward = replace(forward, reversed=True)
    downward = replace(forward, direction=Vector3(0.0, 0.0, -1.0))
    assert _reverse_flag(forward, FRONT_PLANE, support, cut=False) is False
    assert _reverse_flag(backward, FRONT_PLANE, support, cut=False) is True
    assert _reverse_flag(forward, FRONT_PLANE, support, cut=True) is True
    assert _reverse_flag(backward, FRONT_PLANE, support, cut=True) is False
    assert _reverse_flag(downward, FRONT_PLANE, support, cut=True) is False
    assert (
        _reverse_flag(replace(downward, reversed=True), FRONT_PLANE, support, cut=True)
        is True
    )


def _boss_cut_document() -> CadDocument:
    boss_sketch = _sketch(
        "sketch:boss", FRONT_PLANE.id, _rectangle_entities("boss", -25, -15, 25, 15)
    )
    cut_sketch = _sketch(
        "sketch:cut", FRONT_PLANE.id, _rectangle_entities("cut", -10, -10, 10, 10)
    )
    boss = _extrusion(
        "feature:boss",
        0,
        boss_sketch.id,
        12.0,
        operation=BooleanOperation.CREATE,
        reversed_flag=True,
    )
    cut = _extrusion(
        "feature:cut",
        1,
        cut_sketch.id,
        8.0,
        operation=BooleanOperation.CUT,
        reversed_flag=False,
        direction=Vector3(0.0, 0.0, -1.0),
        inputs=(boss.id,),
    )
    return _document(
        (FRONT_PLANE,),
        (boss_sketch, cut_sketch),
        (boss, cut),
        (Body("body:1", "Body", cut.id),),
    )


def test_donor_match_accepts_a_boss_and_cut_hosted_by_the_donor_container() -> None:
    outcome = match_document(_boss_cut_document())
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "boss_cut"
    assert outcome.donor.measured is True
    assert sorted(outcome.donor.container) == [
        "Contents/CMgr",
        "Contents/Config-0",
        "Contents/Config-0-ModelHeader",
        "Contents/Definition",
        "Header2",
    ]


def test_every_donor_container_hosts_a_tree_of_its_own_feature_count() -> None:
    for donor in DONOR_LIBRARY:
        container = donor.container
        assert sorted(container) == [
            "Contents/CMgr",
            "Contents/Config-0",
            "Contents/Config-0-ModelHeader",
            "Contents/Definition",
            "Header2",
        ], donor.donor_id
        assert container["Contents/Config-0-ModelHeader"] == container["Header2"]
        header = container["Header2"]
        for name in (*donor.feature_names, *donor.sketch_names):
            assert name.encode("utf-16-le") in header, (donor.donor_id, name)


def test_donor_containers_grow_with_the_hosted_feature_count() -> None:
    family = tuple(
        donor_by_id(f"boss{count}_front_rect_blind") for count in range(1, 9)
    )
    assert tuple(len(donor.features) for donor in family) == (1, 2, 3, 4, 5, 6, 7, 8)
    for name in ("Contents/CMgr", "Header2"):
        sizes = tuple(len(donor.container[name]) for donor in family)
        steps = {right - left for left, right in zip(sizes, sizes[1:])}
        assert len(steps) == 1 and steps.pop() > 0, name
    growth = tuple(len(donor.container["Contents/Config-0"]) for donor in family)
    assert growth == tuple(sorted(growth)) and len(set(growth)) == 8


def test_the_boss_stack_donors_carry_the_measured_feature_identifiers() -> None:
    for count in range(1, 9):
        donor = donor_by_id(f"boss{count}_front_rect_blind")
        assert donor.sketch_ids[0] == 26
        assert donor.feature_ids[0] == 32
        assert donor.sketch_names == tuple(
            f"Sketch{index + 1}" for index in range(count)
        )
        assert donor.feature_names == tuple(
            f"Boss-Extrude{index + 1}" for index in range(count)
        )
        for ordinal in range(1, count):
            assert donor.sketch_ids[ordinal] == donor.feature_ids[ordinal - 1] + 1
        for ordinal in range(2, count):
            assert donor.sketch_ids[ordinal] - donor.sketch_ids[ordinal - 1] in (7, 8)
            assert donor.feature_ids[ordinal] - donor.feature_ids[ordinal - 1] == 7


def test_the_measured_boss_stack_reaches_six_features() -> None:
    measured = tuple(
        count
        for count in range(1, 9)
        if donor_by_id(f"boss{count}_front_rect_blind").measured
    )
    assert measured == (1, 2, 3, 4, 5, 6)


def test_donor_match_declines_an_unmeasured_donor() -> None:
    planes = (FRONT_PLANE,)
    sketches: list[Sketch] = []
    timeline: list[FeatureStep] = []
    for index in range(7):
        sketch = _sketch(
            f"sketch:boss{index}",
            FRONT_PLANE.id,
            _rectangle_entities(f"boss{index}", -20.0, -10.0, 20.0, 10.0),
        )
        sketches.append(sketch)
        timeline.append(
            _extrusion(
                f"feature:boss{index}",
                index,
                sketch.id,
                10.0 + index,
                operation=(
                    BooleanOperation.CREATE if index == 0 else BooleanOperation.JOIN
                ),
                inputs=() if index == 0 else (f"feature:boss{index - 1}",),
            )
        )
    outcome = match_document(
        _document(
            planes,
            tuple(sketches),
            tuple(timeline),
            (Body("body:1", "Body", timeline[-1].id),),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "donor boss7_front_rect_blind has not been measured in SOLIDWORKS and "
        "cannot back native geometry records",
    )


def test_donor_match_records_non_solid_timeline_entries_without_declining() -> None:
    source = _single_boss()
    tool = FeatureStep(
        "feature:toolbit",
        "Endmill005",
        FeatureKind.NATIVE,
        1,
        definition=NativeFeatureDefinition("freecad.fcstd", "Part::FeaturePython"),
    )
    clone = FeatureStep(
        "feature:clone",
        "Clone",
        FeatureKind.NATIVE,
        2,
        input_feature_ids=("feature:boss",),
        definition=NativeFeatureDefinition("freecad.fcstd", "Part::FeaturePython"),
    )
    outcome = match_document(
        replace(source, feature_timeline=(*source.feature_timeline, tool, clone))
    )
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "boss1_front_rect_blind"
    assert outcome.unexpressed == ("Endmill005 (native)", "Clone (native)")


def _revolution(
    identifier: str,
    order: int,
    sketch_id: str,
    *,
    angle_degrees: float = 360.0,
    axis_entity_id: str = "V_Axis",
    operation: BooleanOperation | None = None,
    inputs: tuple[str, ...] = (),
) -> FeatureStep:
    return FeatureStep(
        identifier,
        identifier,
        FeatureKind.REVOLUTION,
        order,
        sketch_id=sketch_id,
        operation=operation,
        input_feature_ids=inputs,
        definition=RevolutionFeature(
            ParameterValue(angle_degrees, ValueKind.ANGLE, "deg"),
            axis_entity_id,
        ),
    )


def _revolved_boss_document() -> CadDocument:
    sketch = _sketch(
        "sketch:revolve",
        FRONT_PLANE.id,
        _rectangle_entities("revolve", 9.0, -8.0, 21.0, 8.0),
    )
    revolution = _revolution("feature:revolve", 0, sketch.id)
    return _document(
        (FRONT_PLANE,),
        (sketch,),
        (revolution,),
        (Body("body:1", "Body", revolution.id),),
    )


def test_donor_match_selects_the_measured_revolve_boss_donor() -> None:
    outcome = match_document(_revolved_boss_document())
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "revolve_full"
    assert outcome.donor.measured
    assert outcome.feature_ids == ("feature:revolve",)


def test_revolve_target_carries_the_angle_the_axis_and_the_profile() -> None:
    source = _revolved_boss_document()
    sketches = {item.id: item for item in source.sketches}
    planes = {item.id: item for item in source.support_planes}
    target, reasons = _target_feature(
        source.feature_timeline[0],
        sketches,
        planes,
        {},
        first=True,
        taken=(),
    )
    assert reasons == ()
    assert target is not None
    assert target.operation == REVOLVE_BOSS_OPERATION
    assert target.profile == RECTANGLE_PROFILE
    assert target.support == FRONT_SKETCH_AXIS_SUPPORT
    assert target.end_condition == FULL_REVOLUTION_END
    assert target.angle_degrees == 360.0
    assert target.axis_direction == (0.0, 1.0)
    assert target.depth_mm is None
    assert target.reversed is None
    assert target.points_mm == ((9.0, -8.0), (21.0, 8.0), (9.0, 8.0), (21.0, -8.0))


def test_donor_match_declines_a_mid_plane_revolution() -> None:
    source = _revolved_boss_document()
    revolution = replace(
        source.feature_timeline[0],
        definition=RevolutionFeature(
            ParameterValue(360.0, ValueKind.ANGLE, "deg"),
            "V_Axis",
            symmetric=True,
        ),
    )
    outcome = match_document(replace(source, feature_timeline=(revolution,)))
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "feature:revolve: a mid-plane revolution carries a two-direction end "
        "specification whose records are not located",
    )


def test_donor_match_declines_a_revolution_up_to_a_reference() -> None:
    source = _revolved_boss_document()
    revolution = source.feature_timeline[0]
    kind = Parameter(
        "parameter:revolve:type",
        "Type",
        ParameterValue(3, ValueKind.INTEGER, ""),
        owner_id=revolution.id,
        attributes=frozen_mapping({"freecad_path": "Type"}),
    )
    outcome = match_document(replace(source, parameters=(kind,)))
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "feature:revolve: only a revolution driven by a swept angle has a donor and "
        "this one revolves up to a reference",
    )


def test_donor_match_declines_a_partial_revolution() -> None:
    source = _revolved_boss_document()
    revolution = _revolution("feature:revolve", 0, "sketch:revolve", angle_degrees=90.0)
    outcome = match_document(replace(source, feature_timeline=(revolution,)))
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "feature:revolve: only a 360 degree revolution has a donor and this one "
        "sweeps 90 degrees",
    )


def test_donor_match_declines_a_revolution_whose_profile_crosses_the_axis() -> None:
    sketch = _sketch(
        "sketch:revolve",
        FRONT_PLANE.id,
        _rectangle_entities("revolve", -9.0, -8.0, 21.0, 8.0),
    )
    revolution = _revolution("feature:revolve", 0, sketch.id)
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (sketch,),
            (revolution,),
            (Body("body:1", "Body", revolution.id),),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "feature:revolve: the profile crosses the revolution axis",
    )


def test_donor_match_declines_a_revolution_with_an_unresolvable_axis() -> None:
    source = _revolved_boss_document()
    revolution = FeatureStep(
        "feature:revolve",
        "Revolution",
        FeatureKind.REVOLUTION,
        0,
        sketch_id="sketch:revolve",
        definition=NativeFeatureDefinition("freecad.fcstd", "PartDesign::Revolution"),
    )
    outcome = match_document(replace(source, feature_timeline=(revolution,)))
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "Revolution: the revolution angle is not a readable angle",
        "Revolution: the revolution axis is not a sketch axis through the "
        "sketch origin",
    )


def test_donor_match_reads_a_freecad_revolution_angle_and_reference_axis() -> None:
    source = _revolved_boss_document()
    revolution = replace(
        source.feature_timeline[0],
        definition=NativeFeatureDefinition("freecad.fcstd", "PartDesign::Revolution"),
        attributes=frozen_mapping(
            {
                "freecad": {
                    "name": "Revolution",
                    "properties": {
                        "ReferenceAxis": {
                            "attributes": {"name": "ReferenceAxis"},
                            "children": [
                                {
                                    "attributes": {"value": "Sketch004"},
                                    "children": [
                                        {"attributes": {"value": "V_Axis"}},
                                    ],
                                }
                            ],
                        }
                    },
                }
            }
        ),
    )
    angle = Parameter(
        "parameter:revolve:angle",
        "Angle",
        ParameterValue(360.0, ValueKind.ANGLE, "deg"),
        owner_id=revolution.id,
        attributes=frozen_mapping({"freecad_path": "Angle"}),
    )
    outcome = match_document(
        replace(
            source,
            feature_timeline=(revolution,),
            parameters=(angle,),
        )
    )
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "revolve_full"
    assert outcome.targets[0].angle_degrees == 360.0
    assert outcome.targets[0].axis_direction == (0.0, 1.0)


def _two_boss_document() -> CadDocument:
    first_sketch = _sketch(
        "sketch:one", FRONT_PLANE.id, _rectangle_entities("one", -10, -10, 10, 10)
    )
    second_sketch = _sketch(
        "sketch:two", FRONT_PLANE.id, _rectangle_entities("two", 30, -10, 50, 10)
    )
    first = _extrusion(
        "feature:one", 0, first_sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    second = _extrusion(
        "feature:two", 1, second_sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    return _document(
        (FRONT_PLANE,),
        (first_sketch, second_sketch),
        (first, second),
        (Body("body:1", "Body", first.id), Body("body:2", "Body001", second.id)),
    )


def test_donor_match_translates_two_independent_solid_bodies() -> None:
    outcome = match_document(_two_boss_document())
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "boss2_front_rect_blind"
    assert outcome.feature_ids == ("feature:one", "feature:two")
    assert outcome.unexpressed == ()


def test_donor_match_declines_two_bodies_that_share_a_feature() -> None:
    source = _two_boss_document()
    shared = replace(
        source.bodies[1],
        final_feature_id="feature:one",
    )
    outcome = match_document(replace(source, bodies=(source.bodies[0], shared)))
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "body Body001 shares feature:one with body Body, so the 2 bodies are not "
        "built independently",
    )


def _two_body_document(consumer_dependency: str) -> CadDocument:
    part_sketch = _sketch(
        "sketch:part", FRONT_PLANE.id, _rectangle_entities("part", -20, -10, 20, 10)
    )
    tool_sketch = _sketch(
        "sketch:tool", FRONT_PLANE.id, _rectangle_entities("tool", 9, -8, 21, 8)
    )
    part = _extrusion(
        "feature:part", 0, part_sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    tool = _revolution(
        "feature:tool", 1, tool_sketch.id, operation=BooleanOperation.CREATE
    )
    consumer = FeatureStep(
        "feature:toolbit",
        "Endmill005",
        FeatureKind.NATIVE,
        2,
        definition=NativeFeatureDefinition("freecad.fcstd", "Part::FeaturePython"),
        attributes=frozen_mapping(
            {"freecad": {"name": "Endmill", "dependencies": [consumer_dependency]}}
        ),
    )
    return _document(
        (FRONT_PLANE,),
        (part_sketch, tool_sketch),
        (part, tool, consumer),
        (
            Body(
                "body:1",
                "Body",
                part.id,
                attributes=frozen_mapping({"freecad": {"name": "Body"}}),
            ),
            Body(
                "body:2",
                "Endmill006",
                tool.id,
                attributes=frozen_mapping({"freecad": {"name": "Body001"}}),
            ),
        ),
    )


def test_donor_match_keeps_the_body_a_non_model_feature_references() -> None:
    outcome = match_document(_two_body_document("Body001"))
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "no donor holds the feature sequence boss+rectangle+front+blind, "
        "revolve-boss+rectangle+front-sketch-axis+full-revolution",
    )


def test_donor_match_orders_the_solid_features_body_by_body() -> None:
    source = _two_body_document("Body001")
    timeline = tuple(sorted(source.feature_timeline, key=lambda item: item.order))
    solid = (timeline[0], timeline[1])
    bodies = _model_bodies(source, timeline, solid)
    groups, reasons = _body_groups(bodies, solid)
    assert reasons == ()
    assert [[step.id for step in group] for group in groups] == [
        ["feature:part"],
        ["feature:tool"],
    ]


def test_donor_match_reports_a_native_feature_as_unexpressed() -> None:
    source = _two_body_document("Body001")
    timeline = tuple(sorted(source.feature_timeline, key=lambda item: item.order))
    outcome = match_document(
        replace(
            source,
            feature_timeline=(timeline[0], timeline[2]),
            bodies=source.bodies[:1],
        )
    )
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "boss1_front_rect_blind"
    assert outcome.feature_ids == ("feature:part",)
    assert outcome.unexpressed == ("Endmill005 (native)",)


def test_donor_match_projects_a_freecad_right_plane_into_solidworks_axes() -> None:
    entities = _rectangle_entities("boss", -20.0, -10.0, 20.0, 10.0)
    sketch = _sketch("sketch:boss", FREECAD_YZ_PLANE.id, entities)
    feature = _extrusion(
        "feature:boss",
        0,
        sketch.id,
        10.0,
        operation=BooleanOperation.CREATE,
        direction=Vector3(1.0, 0.0, 0.0),
    )
    outcome = match_document(
        _document(
            (FREECAD_YZ_PLANE,),
            (sketch,),
            (feature,),
            (Body("body:1", "Body", feature.id),),
        )
    )
    assert isinstance(outcome, DonorMatch)
    assert outcome.donor.donor_id == "boss_right_plane"
    assert outcome.targets[0].support == RIGHT_SUPPORT
    assert outcome.targets[0].points_mm == (
        (-10.0, -20.0),
        (10.0, 20.0),
        (-10.0, 20.0),
        (10.0, -20.0),
    )
    assert outcome.targets[0].reversed is False


def _arc_profile_entities(
    prefix: str,
    minimum_x: float,
    minimum_y: float,
    maximum_x: float,
    maximum_y: float,
) -> tuple[SketchEntity, ...]:
    corners = (
        Vector2(maximum_x, maximum_y),
        Vector2(minimum_x, maximum_y),
        Vector2(minimum_x, minimum_y),
        Vector2(maximum_x, minimum_y),
    )
    lines = tuple(
        SketchEntity(
            f"{prefix}:edge:{index}",
            GeometryKind.LINE,
            LineGeometry(corners[index], corners[index + 1]),
        )
        for index in range(3)
    )
    centre = Vector2(maximum_x, 0.5 * (minimum_y + maximum_y))
    radius = 0.5 * (maximum_y - minimum_y)
    arc = SketchEntity(
        f"{prefix}:arc",
        GeometryKind.ARC,
        ArcGeometry(centre, radius, -0.5 * math.pi, 0.5 * math.pi),
    )
    return (*lines, arc)


def test_donor_match_declines_an_arc_profile_that_does_not_close() -> None:
    lines = _rectangle_entities("boss", -20.0, -10.0, 20.0, 10.0)[:3]
    arc = SketchEntity(
        "boss:arc",
        GeometryKind.ARC,
        ArcGeometry(Vector2(20.0, 0.0), 10.0, 90.0, 270.0),
    )
    entities = (*lines, arc)
    sketch = _sketch("sketch:boss", FRONT_PLANE.id, entities)
    feature = _extrusion(
        "feature:boss", 0, sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (sketch,),
            (feature,),
            (Body("body:1", "Body", feature.id),),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "feature:boss: sketch sketch:boss holds an arc profile that does not close "
        "on itself",
    )


def test_donor_match_names_a_closed_arc_profile() -> None:
    entities = _arc_profile_entities("boss", -20.0, -10.0, 20.0, 10.0)
    sketch = _sketch("sketch:boss", FRONT_PLANE.id, entities)
    feature = _extrusion(
        "feature:boss", 0, sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (sketch,),
            (feature,),
            (Body("body:1", "Body", feature.id),),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "no donor holds the feature sequence " "boss+polyline-3-arc-1-ccw+front+blind",
    )


def test_donor_match_declines_two_arcs_in_one_profile() -> None:
    corners = (
        Vector2(20.0, 10.0),
        Vector2(-20.0, 10.0),
        Vector2(-20.0, -10.0),
        Vector2(20.0, -10.0),
    )
    lines = tuple(
        SketchEntity(
            f"boss:edge:{index}",
            GeometryKind.LINE,
            LineGeometry(corners[index], corners[index + 1]),
        )
        for index in range(2)
    )
    first = SketchEntity(
        "boss:arc:0",
        GeometryKind.ARC,
        ArcGeometry(Vector2(-20.0, 0.0), 10.0, 0.5 * math.pi, 1.5 * math.pi),
    )
    second = SketchEntity(
        "boss:arc:1",
        GeometryKind.ARC,
        ArcGeometry(Vector2(20.0, 0.0), 10.0, -0.5 * math.pi, 0.5 * math.pi),
    )
    entities = (lines[0], first, lines[1], second)
    sketch = _sketch("sketch:boss", FRONT_PLANE.id, entities)
    feature = _extrusion(
        "feature:boss", 0, sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (sketch,),
            (feature,),
            (Body("body:1", "Body", feature.id),),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "feature:boss: sketch sketch:boss holds 2 arcs and only a profile with "
        "exactly one arc has a donor",
    )


def test_donor_match_declines_a_circle_outside_its_rectangle() -> None:
    rectangle = _rectangle_entities("boss", -20.0, -10.0, 20.0, 10.0)
    circle = SketchEntity(
        "boss:hole",
        GeometryKind.CIRCLE,
        CircleGeometry(Vector2(40.0, 0.0), 4.0),
    )
    sketch = Sketch(
        "sketch:boss",
        "sketch:boss",
        FRONT_PLANE.id,
        (*rectangle, circle),
        closed_profile_entity_ids=(
            tuple(item.id for item in rectangle),
            (circle.id,),
        ),
    )
    feature = _extrusion(
        "feature:boss", 0, sketch.id, 10.0, operation=BooleanOperation.CREATE
    )
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (sketch,),
            (feature,),
            (Body("body:1", "Body", feature.id),),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == (
        "feature:boss: sketch sketch:boss holds a circle that is not enclosed "
        "by its rectangle",
    )


def test_patch_donor_writes_the_extrusion_direction_and_its_mirror() -> None:
    donor = donor_by_id("boss1_front_rect_blind")
    target = TargetFeature(
        operation=BOSS_OPERATION,
        profile=RECTANGLE_PROFILE,
        support="front",
        end_condition="blind",
        points_mm=((-20.0, -10.0), (20.0, 10.0), (-20.0, 10.0), (20.0, -10.0)),
        depth_mm=10.0,
        reversed=True,
    )
    stream = patch_donor(donor, (target,))
    features = locate_features(stream)
    assert len(features) == 1
    assert features[0].reversed is True
    assert features[0].depth_mm == 10.0
    mirror = features[0].from_reverse_offset
    assert mirror is not None
    assert stream[mirror] == 1


def test_donor_write_reports_the_decline_reason_in_the_diagnostics() -> None:
    entities = _rectangle_entities("profile", 0.0, 0.0, 10.0, 40.0)
    sketch = _sketch("sketch:profile", FRONT_PLANE.id, entities)
    revolution = FeatureStep(
        "feature:revolution",
        "Revolution",
        FeatureKind.REVOLUTION,
        0,
        sketch_id=sketch.id,
        definition=NativeFeatureDefinition("freecad.fcstd", "PartDesign::Revolution"),
    )
    source = _document(
        (FRONT_PLANE,),
        (sketch,),
        (revolution,),
        (Body("body:1", "Body", revolution.id),),
    )
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    declines = [
        item for item in result.diagnostics if item.code == "sldprt.donor_declined"
    ]
    assert len(declines) == 1
    assert (
        "Revolution: the revolution angle is not a readable angle"
        in declines[0].message
    )
    assert result.vendor_loadable is False
    assert result.application_usable is False
    assert KIT_RESOLVED_STREAM in archive.streams


def test_donor_write_emits_real_resolved_features_for_a_reversed_boss() -> None:
    output = BytesIO()
    result = write_sldprt(_single_boss(reversed_flag=True), output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    resolved = archive.require(RESOLVED_FEATURES_STREAM)
    features = locate_features(resolved)
    assert result.vendor_loadable is True
    assert result.application_usable is True
    assert KIT_RESOLVED_STREAM not in archive.streams
    assert len(features) == 1
    assert features[0].kind == "boss"
    assert features[0].reversed is True
    assert features[0].depth_mm == 10.0
    assert features[0].corners_mm == (
        (-20.0, -10.0),
        (20.0, 10.0),
        (-20.0, 10.0),
        (20.0, -10.0),
    )
    keywords = archive.require(KEYWORDS_STREAM)
    assert keywords.startswith(b"\x86")
    assert b'Name="Boss-Extrude1"' in keywords


def test_donor_write_emits_the_donor_container_for_a_boss_and_cut() -> None:
    output = BytesIO()
    result = write_sldprt(_boss_cut_document(), output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    donor = donor_by_id("boss_cut")
    assert result.vendor_loadable is True
    assert result.application_usable is True
    for name, blob in donor.container.items():
        assert archive.require(name) == blob
    assert KIT_DOCUMENT_STREAM in archive.streams
    assert archive.require(PARTITION_STREAM) == encode_blank_partition_stream()
    features = locate_features(archive.require(RESOLVED_FEATURES_STREAM))
    assert tuple(item.kind for item in features) == ("boss", "cut")
    assert tuple(item.depth_mm for item in features) == (12.0, 8.0)


def test_donor_write_round_trips_a_boss_and_cut_through_the_kit_stream() -> None:
    source = _boss_cut_document()
    output = BytesIO()
    write_sldprt(source, output)
    payload = output.getvalue()
    archive = SldprtArchive.from_bytes(payload)
    embedded = CadDocument.from_json(
        archive.require(KIT_DOCUMENT_STREAM).decode("utf-8")
    )
    portable = _document_without_source(source)
    assert embedded.to_json(indent=None) == portable.to_json(indent=None)
    replayed = read_sldprt(BytesIO(payload))
    assert replayed.metadata["embedded_source_format_id"] == "freecad.fcstd"
    assert replayed.support_planes == source.support_planes
    assert replayed.sketches == source.sketches
    assert replayed.feature_timeline == source.feature_timeline
    assert replayed.bodies == source.bodies


def _revolve_boss_target(**overrides: object) -> TargetFeature:
    return replace(
        TargetFeature(
            operation=REVOLVE_BOSS_OPERATION,
            profile=RECTANGLE_PROFILE,
            support=FRONT_SKETCH_AXIS_SUPPORT,
            end_condition=FULL_REVOLUTION_END,
            points_mm=rectangle_corners_mm(9.0, -8.0, 21.0, 8.0),
            angle_degrees=360.0,
            axis_direction=(0.0, 1.0),
        ),
        **overrides,
    )


def test_full_revolution_end_condition_stays_out_of_the_extrude_gates() -> None:
    assert FULL_REVOLUTION_END not in SUPPORTED_END_CONDITIONS
    assert FULL_REVOLUTION_END not in DEPTHLESS_END_CONDITIONS


def test_measured_revolve_donors_carry_a_plane_qualified_axis_support() -> None:
    expected = {
        "revolve_full": "front-sketch-axis",
        "revolve_pin_top_full": "top-sketch-axis",
        "revolve_pin_front_full": "front-sketch-axis",
        "boss_disjoint_revolve": "top-sketch-axis",
        "arcboss_cut_cut_cut_through_rev": "top-sketch-axis",
    }
    for donor_id, support in expected.items():
        donor = donor_by_id(donor_id)
        assert donor.measured
        revolves = tuple(
            item for item in donor.features if item.operation.startswith("revolve")
        )
        assert len(revolves) == 1
        assert revolves[0].support == support
        assert revolves[0].end_condition == FULL_REVOLUTION_END


def test_the_revolved_cut_donor_is_measured() -> None:
    donor = donor_by_id("boss_revcut")
    assert donor.measured
    assert donor.features[1].operation == REVOLVE_CUT_OPERATION
    assert donor.features[1].support == FRONT_SKETCH_AXIS_SUPPORT


def test_patch_donor_writes_the_revolution_profile_and_the_full_angle() -> None:
    stream = patch_donor(donor_by_id("revolve_full"), (_revolve_boss_target(),))
    features = locate_features(stream)
    assert len(features) == 1
    assert features[0].kind == "revolve"
    assert features[0].corners_mm == (
        (9.0, -8.0),
        (21.0, 8.0),
        (9.0, 8.0),
        (21.0, -8.0),
    )
    assert features[0].angle_degrees == 360.0
    assert features[0].depth_mm is None


def test_patch_donor_refuses_a_partial_angle_on_a_full_revolution_donor() -> None:
    donor = donor_by_id("revolve_full")
    for angle in (90.0, 270.0):
        with pytest.raises(SldprtFormatError) as error:
            patch_donor(donor, (_revolve_boss_target(angle_degrees=angle),))
        assert "carries no display dimension" in str(error.value)


def test_patch_donor_writes_a_revolved_cut_after_a_boss() -> None:
    boss = TargetFeature(
        operation=BOSS_OPERATION,
        profile=RECTANGLE_PROFILE,
        support="front",
        end_condition="blind",
        points_mm=rectangle_corners_mm(-23.0, -12.0, 23.0, 12.0),
        depth_mm=12.0,
        reversed=False,
    )
    cut = TargetFeature(
        operation=REVOLVE_CUT_OPERATION,
        profile=RECTANGLE_PROFILE,
        support=FRONT_SKETCH_AXIS_SUPPORT,
        end_condition=FULL_REVOLUTION_END,
        points_mm=rectangle_corners_mm(-28.0, 0.0, 28.0, 4.0),
        angle_degrees=360.0,
        axis_direction=(1.0, 0.0),
    )
    stream = patch_donor(donor_by_id("boss_revcut"), (boss, cut))
    features = locate_features(stream)
    assert [item.kind for item in features] == ["boss", "revolve-cut"]
    assert features[0].depth_mm == 12.0
    assert features[1].angle_degrees == 360.0
    assert features[1].corners_mm == (
        (-28.0, 0.0),
        (28.0, 4.0),
        (-28.0, 4.0),
        (28.0, 0.0),
    )


def test_patch_donor_rejects_a_revolution_edit_the_stream_cannot_hold() -> None:
    donor = donor_by_id("revolve_full")
    rejected = (
        _revolve_boss_target(axis_direction=(1.0, 0.0)),
        _revolve_boss_target(axis_direction=None),
        _revolve_boss_target(angle_degrees=None),
        _revolve_boss_target(angle_degrees=0.0),
        _revolve_boss_target(angle_degrees=400.0),
        _revolve_boss_target(depth_mm=5.0),
        _revolve_boss_target(reversed=True),
        _revolve_boss_target(end_condition="blind"),
        _revolve_boss_target(support="front"),
    )
    for target in rejected:
        with pytest.raises(SldprtFormatError):
            patch_donor(donor, (target,))


def test_arc_donor_stream_carries_one_swept_arc() -> None:
    donor = donor_by_id("arcboss_cut_cut_cut_through")
    assert donor.measured
    assert donor.swept_arc_counts == (1, 0, 0, 0)
    assert donor.point_counts == (4, 4, 0, 12)
    assert donor.arc_counts == (0, 0, 1, 0)
    assert donor.inherited_directions == (None, None, None, False)
    located = locate_features(donor.stream)
    assert len(located) == 4
    arcs = located[0].swept_arcs
    assert len(arcs) == 1
    assert arcs[0].consistent
    assert arcs[0].radius_mm == pytest.approx(35.0, abs=1.0e-6)
    assert arcs[0].centre_mm == pytest.approx((55.0, 15.0), abs=1.0e-4)
    assert not located[1].swept_arcs
    assert not located[2].swept_arcs
    assert not located[3].swept_arcs


def test_patch_donor_moves_a_swept_arc_centre() -> None:
    donor = donor_by_id("arcboss_cut_cut_cut_through")
    vertices = (
        (18.0, 24.0),
        (-60.0, 24.0),
        (-60.0, -16.0),
        (58.0, -16.0),
    )
    centre = (58.0, 24.0)
    targets = (
        TargetFeature(
            operation=BOSS_OPERATION,
            profile="polyline-3-arc-1-ccw",
            support="front",
            end_condition="blind",
            points_mm=vertices,
            swept_arc_centres_mm=(centre,),
            depth_mm=120.0,
            reversed=True,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile=RECTANGLE_PROFILE,
            support="front",
            end_condition="blind",
            points_mm=rectangle_corners_mm(-40.0, -8.0, 50.0, 8.0),
            depth_mm=12.0,
            reversed=False,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile="circle",
            support="front",
            end_condition="blind",
            radii_mm=(20.0,),
            arc_centres_mm=((40.0, 10.0),),
            depth_mm=40.0,
            reversed=False,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile="polyline-12",
            support="top",
            end_condition="through-all",
            points_mm=tuple(
                (x * 1.1, y * 1.1)
                for x, y in locate_features(donor.stream)[3].corners_mm
            ),
            reversed=False,
        ),
    )
    patched = patch_donor(donor, targets)
    located = locate_features(patched)
    for got, want in zip(located[0].corners_mm, vertices, strict=True):
        assert got == pytest.approx(want)
    arcs = located[0].swept_arcs
    assert len(arcs) == 1
    assert arcs[0].centre_mm == pytest.approx(centre)
    assert arcs[0].consistent
    assert arcs[0].radius_mm == pytest.approx(40.0, abs=1.0e-9)
    assert located[0].depth_mm == pytest.approx(120.0)
    assert located[0].reversed is True
    assert located[2].arcs[0].radius_mm == pytest.approx(20.0)


def test_patch_donor_rejects_an_inconsistent_swept_arc_centre() -> None:
    donor = donor_by_id("arcboss_cut_cut_cut_through")
    located = locate_features(donor.stream)
    targets = (
        TargetFeature(
            operation=BOSS_OPERATION,
            profile="polyline-3-arc-1-ccw",
            support="front",
            end_condition="blind",
            points_mm=located[0].corners_mm,
            swept_arc_centres_mm=((0.0, 0.0),),
            depth_mm=100.0,
            reversed=False,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile=RECTANGLE_PROFILE,
            support="front",
            end_condition="blind",
            points_mm=located[1].corners_mm,
            depth_mm=15.0,
            reversed=True,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile="circle",
            support="front",
            end_condition="blind",
            radii_mm=(25.0,),
            arc_centres_mm=(located[2].arcs[0].centre_mm,),
            depth_mm=50.0,
            reversed=True,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile="polyline-12",
            support="top",
            end_condition="through-all",
            points_mm=located[3].corners_mm,
            reversed=False,
        ),
    )
    with pytest.raises(SldprtFormatError):
        patch_donor(donor, targets)


def test_patch_donor_rejects_an_unwritable_through_all_direction() -> None:
    donor = donor_by_id("arcboss_cut_cut_cut_through")
    located = locate_features(donor.stream)
    targets = (
        TargetFeature(
            operation=BOSS_OPERATION,
            profile="polyline-3-arc-1-ccw",
            support="front",
            end_condition="blind",
            points_mm=located[0].corners_mm,
            swept_arc_centres_mm=(located[0].swept_arcs[0].centre_mm,),
            depth_mm=100.0,
            reversed=False,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile=RECTANGLE_PROFILE,
            support="front",
            end_condition="blind",
            points_mm=located[1].corners_mm,
            depth_mm=15.0,
            reversed=True,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile="circle",
            support="front",
            end_condition="blind",
            radii_mm=(25.0,),
            arc_centres_mm=(located[2].arcs[0].centre_mm,),
            depth_mm=50.0,
            reversed=True,
        ),
        TargetFeature(
            operation=CUT_OPERATION,
            profile="polyline-12",
            support="top",
            end_condition="through-all",
            points_mm=located[3].corners_mm,
            reversed=True,
        ),
    )
    with pytest.raises(SldprtFormatError):
        patch_donor(donor, targets)
