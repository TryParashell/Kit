from __future__ import annotations

from dataclasses import replace
from io import BytesIO

from convert.adapters.solidworks import read_sldprt, write_sldprt
from convert.adapters.solidworks.adapter import _document_without_source
from convert.adapters.solidworks.container import SldprtArchive
from convert.adapters.solidworks.donor_library import (
    BOSS_OPERATION,
    CUT_OPERATION,
    DONOR_LIBRARY,
    RECTANGLE_PROFILE,
    RIGHT_SUPPORT,
    TargetFeature,
    donor_by_id,
    patch_donor,
)
from convert.adapters.solidworks.parasolid import encode_blank_partition_stream
from convert.adapters.solidworks.donor_match import (
    DonorDecline,
    DonorMatch,
    _reverse_flag,
    _support,
    match_document,
)
from convert.adapters.solidworks.format import (
    KEYWORDS_STREAM,
    KIT_DOCUMENT_STREAM,
    KIT_RESOLVED_STREAM,
    PARTITION_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.resolved import locate_features
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
    ParameterValue,
    Sketch,
    SketchEntity,
    SupportPlane,
    Transform,
    ValueKind,
    Vector2,
    Vector3,
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
        donor_by_id(f"boss{count}_front_rect_blind") for count in range(1, 5)
    )
    assert tuple(len(donor.features) for donor in family) == (1, 2, 3, 4)
    for name in ("Contents/CMgr", "Header2", "Contents/Config-0"):
        sizes = tuple(len(donor.container[name]) for donor in family)
        assert sizes == tuple(sorted(sizes)) and len(set(sizes)) == 4, name


def test_donor_match_declines_an_unmeasured_donor() -> None:
    planes = (FRONT_PLANE,)
    sketches: list[Sketch] = []
    timeline: list[FeatureStep] = []
    for index in range(4):
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
        "donor boss4_front_rect_blind has not been measured in SOLIDWORKS and "
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


def test_donor_match_declines_and_names_the_blocking_revolution() -> None:
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
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (sketch,),
            (revolution,),
            (Body("body:1", "Body", revolution.id),),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == ("Revolution: revolution features have no donor",)


def test_donor_match_declines_a_document_with_two_solid_bodies() -> None:
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
    outcome = match_document(
        _document(
            (FRONT_PLANE,),
            (first_sketch, second_sketch),
            (first, second),
            (Body("body:1", "Body", first.id), Body("body:2", "Body001", second.id)),
        )
    )
    assert isinstance(outcome, DonorDecline)
    assert outcome.reasons == ("the document builds 2 separate solid bodies",)


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


def test_donor_match_declines_a_profile_with_arc_segments() -> None:
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
        "feature:boss: sketch sketch:boss uses unsupported geometry ArcGeometry",
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
    assert "Revolution: revolution features have no donor" in declines[0].message
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
