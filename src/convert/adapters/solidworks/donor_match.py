from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType

from interchange import (
    BooleanOperation,
    CadDocument,
    CircleGeometry,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    LineGeometry,
    Parameter,
    ParameterValue,
    Sketch,
    SketchEntity,
    SupportPlane,
    ValueKind,
)

from .donor_library import (
    BOSS_OPERATION,
    BLIND_END,
    CIRCLE_PROFILE,
    CUT_OPERATION,
    GENERATED_CONTAINER_FEATURE_LIMIT,
    Donor,
    FRONT_SUPPORT,
    MID_PLANE_END,
    RECTANGLE_PROFILE,
    RECTANGLE_WITH_CIRCLE_PROFILE,
    RIGHT_SUPPORT,
    TOP_SUPPORT,
    TargetFeature,
    donor_key,
    polyline_profile,
    select_donor,
)
from .resolved import rectangle_corners_mm

_TOLERANCE_MM = 1.0e-9
_AXIS_TOLERANCE = 1.0e-6
_MINIMUM_EXTENT_MM = 1.0e-6
_SYSTEM_OBJECT_IDS = frozenset(range(1, 26))
_VALUE_TOLERANCE = 1.0e-10

FREECAD_FORMAT_ID = "freecad.fcstd"
VERIFIABLE_SOURCE_FORMATS = frozenset({FREECAD_FORMAT_ID})
LENGTH_FACTORS_MM = MappingProxyType(
    {
        "": 1.0,
        "mm": 1.0,
        "millimeter": 1.0,
        "millimeters": 1.0,
        "cm": 10.0,
        "m": 1000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
    }
)
ANGLE_FACTORS_DEGREES = MappingProxyType(
    {
        "": 1.0,
        "deg": 1.0,
        "degree": 1.0,
        "degrees": 1.0,
        "rad": 180.0 / math.pi,
        "radian": 180.0 / math.pi,
        "radians": 180.0 / math.pi,
    }
)
FREECAD_LENGTH_PROPERTIES = (
    ("Length", "length"),
    ("Length2", "second_length"),
    ("Offset", "offset"),
    ("Offset2", "second_offset"),
)
FREECAD_ANGLE_PROPERTIES = (
    ("TaperAngle", "draft_angle"),
    ("TaperAngle2", "second_draft_angle"),
)
FREECAD_BLIND_TYPE_CODE = 0
FREECAD_SYMMETRIC_SIDE_TYPE = 2

BOSS_OPERATIONS = frozenset({BooleanOperation.CREATE, BooleanOperation.JOIN})
CUT_OPERATIONS = frozenset({BooleanOperation.CUT})
END_CONDITION_NAMES = MappingProxyType(
    {
        ExtrusionEndCondition.BLIND: BLIND_END,
        ExtrusionEndCondition.MID_PLANE: MID_PLANE_END,
    }
)
THROUGH_ALL_NAME = "through-all"
PRINCIPAL_PLANE_FRAMES = (
    (FRONT_SUPPORT, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
    (TOP_SUPPORT, (1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    (RIGHT_SUPPORT, (0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
)
NON_SOLID_FEATURE_KINDS = frozenset({FeatureKind.REFERENCE.value})


@dataclass(frozen=True, slots=True)
class _Profile:
    name: str
    points_mm: tuple[tuple[float, float], ...]
    radii_mm: tuple[float, ...]
    arc_centres_mm: tuple[tuple[float, float], ...]


@dataclass(frozen=True, slots=True)
class _Support:
    name: str
    rows: tuple[tuple[float, float], tuple[float, float]]
    normal: tuple[float, float, float]

    def project(self, u: float, v: float) -> tuple[float, float]:
        return (
            u * self.rows[0][0] + v * self.rows[0][1],
            u * self.rows[1][0] + v * self.rows[1][1],
        )


@dataclass(frozen=True, slots=True)
class DonorDecline:
    reasons: tuple[str, ...]
    candidate: bool = True


@dataclass(frozen=True, slots=True)
class DonorMatch:
    donor: Donor
    targets: tuple[TargetFeature, ...]
    sketch_ids: tuple[str, ...]
    feature_ids: tuple[str, ...]
    unexpressed: tuple[str, ...] = ()
    principal_plane_ids: frozenset[str] = frozenset()

    @property
    def object_ids(self) -> tuple[tuple[str, int], ...]:
        pairs: list[tuple[str, int]] = []
        for sketch_id, object_id in zip(
            self.sketch_ids, self.donor.sketch_ids, strict=True
        ):
            pairs.append((f"sketch:{sketch_id}", object_id))
        for feature_id, object_id in zip(
            self.feature_ids, self.donor.feature_ids, strict=True
        ):
            pairs.append((f"feature:{feature_id}", object_id))
        return tuple(pairs)


def match_document(document: CadDocument) -> DonorMatch | DonorDecline:
    blocked: list[str] = []
    if document.source.format_id.casefold() not in VERIFIABLE_SOURCE_FORMATS:
        blocked.append(
            f"a {document.source.format_id or 'source-less'} document carries no "
            f"feature properties the writer can verify a donor against"
        )
    if document.assembly is not None:
        blocked.append("the document is an assembly")
    if document.brep is not None:
        blocked.append("the document carries an imported b-rep body")
    timeline = tuple(sorted(document.feature_timeline, key=lambda item: item.order))
    if not timeline:
        blocked.append("the document has no feature timeline")
    if blocked:
        return DonorDecline(tuple(blocked), candidate=False)
    chains = _body_feature_chains(document, timeline)
    solid: list[FeatureStep] = []
    unexpressed: list[str] = []
    for step in timeline:
        if _is_non_solid(step, step.id in chains, bool(chains)):
            unexpressed.append(f"{step.name} ({step.kind})")
        else:
            solid.append(step)
    if not solid:
        return DonorDecline(
            ("the document has no solid-model feature",), candidate=False
        )
    sketches = {sketch.id: sketch for sketch in document.sketches}
    planes = {plane.id: plane for plane in document.support_planes}
    reasons: list[str] = []
    if len(document.configurations) > 1:
        reasons.append(
            f"the document holds {len(document.configurations)} configurations"
        )
    targets: list[TargetFeature] = []
    sketch_ids: list[str] = []
    feature_ids: list[str] = []
    for index, step in enumerate(solid):
        target, step_reasons = _target_feature(
            step, sketches, planes, first=index == 0, taken=tuple(sketch_ids)
        )
        reasons.extend(step_reasons)
        reasons.extend(_source_disagreements(document, step))
        if target is None:
            continue
        targets.append(target)
        sketch_ids.append(str(step.sketch_id))
        feature_ids.append(step.id)
    bodies = _solid_body_count(document, timeline, chains)
    if bodies > 1:
        reasons.append(f"the document builds {bodies} separate solid bodies")
    if reasons:
        return DonorDecline(tuple(reasons))
    donor = select_donor(targets)
    if donor is None:
        shape = ", ".join("+".join(key) for key in donor_key(targets))
        return DonorDecline((f"no donor holds the feature sequence {shape}",))
    if not donor.container and len(donor.features) > GENERATED_CONTAINER_FEATURE_LIMIT:
        return DonorDecline(
            (
                f"donor {donor.donor_id} holds {len(donor.features)} features, "
                f"carries no SOLIDWORKS container of its own, and the generated "
                f"container describes a tree of "
                f"{GENERATED_CONTAINER_FEATURE_LIMIT}, so SOLIDWORKS refuses the "
                f"document",
            )
        )
    if not donor.measured:
        return DonorDecline(
            (
                f"donor {donor.donor_id} has not been measured in SOLIDWORKS "
                f"and cannot back native geometry records",
            )
        )
    return DonorMatch(
        donor=donor,
        targets=tuple(targets),
        sketch_ids=tuple(sketch_ids),
        feature_ids=tuple(feature_ids),
        unexpressed=tuple(unexpressed),
        principal_plane_ids=principal_plane_ids(document),
    )


def principal_plane_ids(document: CadDocument) -> frozenset[str]:
    return frozenset(
        plane.id for plane in document.support_planes if _support(plane) is not None
    )


def _body_feature_chains(
    document: CadDocument, timeline: tuple[FeatureStep, ...]
) -> frozenset[str]:
    by_id = {step.id: step for step in timeline}
    result: set[str] = set()
    for body in document.bodies:
        pending = [body.final_feature_id] if body.final_feature_id else []
        while pending:
            current = pending.pop()
            if current not in by_id or current in result:
                continue
            result.add(current)
            pending.extend(by_id[current].input_feature_ids)
    return frozenset(result)


def _solid_body_count(
    document: CadDocument, timeline: tuple[FeatureStep, ...], chains: frozenset[str]
) -> int:
    by_id = {step.id: step for step in timeline}
    count = 0
    for body in document.bodies:
        pending = [body.final_feature_id] if body.final_feature_id else []
        seen: set[str] = set()
        while pending:
            current = pending.pop()
            if current not in by_id or current in seen:
                continue
            seen.add(current)
            pending.extend(by_id[current].input_feature_ids)
        if any(not _is_non_solid(by_id[item], False, bool(chains)) for item in seen):
            count += 1
    return count


def _is_non_solid(step: FeatureStep, chained: bool, chains_known: bool) -> bool:
    if chained:
        return False
    kind = str(step.kind).casefold()
    if kind in NON_SOLID_FEATURE_KINDS:
        return True
    native_id = step.attributes.get("native_object_id")
    if (
        isinstance(native_id, int)
        and not isinstance(native_id, bool)
        and native_id in _SYSTEM_OBJECT_IDS
        and kind == FeatureKind.NATIVE.value
    ):
        return True
    return chains_known and kind == FeatureKind.NATIVE.value


def _freecad_properties(
    document: CadDocument, step: FeatureStep
) -> dict[str, Parameter]:
    result: dict[str, Parameter] = {}
    for parameter in document.parameters:
        if parameter.owner_id != step.id:
            continue
        path = parameter.attributes.get("freecad_path")
        if isinstance(path, str) and path:
            result[path] = parameter
    return result


def _source_disagreements(document: CadDocument, step: FeatureStep) -> tuple[str, ...]:
    definition = step.definition
    if not isinstance(definition, ExtrusionFeature):
        return ()
    properties = _freecad_properties(document, step)
    if not properties:
        return ()
    label = step.name or step.id
    result: list[str] = []
    for path, field in FREECAD_LENGTH_PROPERTIES:
        parameter = properties.get(path)
        if parameter is not None and not _scalar_agrees(
            parameter, getattr(definition, field), LENGTH_FACTORS_MM, ValueKind.LENGTH
        ):
            result.append(path)
    for path, field in FREECAD_ANGLE_PROPERTIES:
        parameter = properties.get(path)
        if parameter is not None and not _scalar_agrees(
            parameter,
            getattr(definition, field),
            ANGLE_FACTORS_DEGREES,
            ValueKind.ANGLE,
        ):
            result.append(path)
    reverse = properties.get("Reversed")
    if reverse is not None and _boolean(reverse) is not bool(definition.reversed):
        result.append("Reversed")
    midplane = properties.get("Midplane")
    side_type = _integer(properties.get("SideType"))
    if midplane is not None and (
        _boolean(midplane) or side_type == FREECAD_SYMMETRIC_SIDE_TYPE
    ) is not bool(definition.symmetric):
        result.append("Midplane")
    suppressed = properties.get("Suppressed")
    if suppressed is not None and _boolean(suppressed) is not bool(step.suppressed):
        result.append("Suppressed")
    type_code = _integer(properties.get("Type"))
    blind = str(definition.end_condition).casefold() == (
        ExtrusionEndCondition.BLIND.value
    )
    if type_code is not None and (type_code == FREECAD_BLIND_TYPE_CODE) is not blind:
        result.append("Type")
    if not result:
        return ()
    return (
        f"{label}: the {', '.join(result)} source "
        f"{'property' if len(result) == 1 else 'properties'} disagree"
        f"{'s' if len(result) == 1 else ''} with the feature the document declares",
    )


def _scalar_agrees(
    parameter: Parameter,
    expected: ParameterValue | None,
    factors: MappingProxyType,
    kind: ValueKind,
) -> bool:
    recorded = _scalar(parameter.value, factors, kind)
    if recorded is None:
        return True
    if expected is None:
        return False
    declared = _scalar(expected, factors, kind)
    return declared is not None and math.isclose(
        recorded, declared, rel_tol=0.0, abs_tol=_VALUE_TOLERANCE
    )


def _scalar(
    value: ParameterValue, factors: MappingProxyType, kind: ValueKind
) -> float | None:
    if value.kind is not kind or isinstance(value.value, bool):
        return None
    if not isinstance(value.value, (int, float)):
        return None
    factor = factors.get(value.unit.casefold())
    number = float(value.value)
    if factor is None or not math.isfinite(number):
        return None
    return number * factor


def _boolean(parameter: Parameter) -> bool | None:
    value = parameter.value
    if value.kind is not ValueKind.BOOLEAN or not isinstance(value.value, bool):
        return None
    return value.value


def _integer(parameter: Parameter | None) -> int | None:
    if parameter is None:
        return None
    value = parameter.value
    if value.kind is not ValueKind.INTEGER or isinstance(value.value, bool):
        return None
    return int(value.value) if isinstance(value.value, int) else None


def _target_feature(
    step: FeatureStep,
    sketches: dict[str, Sketch],
    planes: dict[str, SupportPlane],
    *,
    first: bool,
    taken: tuple[str, ...],
) -> tuple[TargetFeature | None, tuple[str, ...]]:
    label = step.name or step.id
    definition = step.definition
    if str(step.kind).casefold() != FeatureKind.EXTRUSION.value:
        return None, (f"{label}: {step.kind} features have no donor",)
    if not isinstance(definition, ExtrusionFeature):
        return None, (f"{label}: the extrusion carries no extrusion definition",)
    if step.suppressed:
        return None, (f"{label}: the feature is suppressed",)
    if step.configuration_states:
        return None, (f"{label}: the feature varies by configuration",)
    sketch = sketches.get(step.sketch_id or "")
    if sketch is None:
        return None, (f"{label}: the extrusion has no resolvable sketch",)
    if sketch.id in taken:
        return None, (f"{label}: sketch {sketch.name} drives more than one feature",)
    plane = planes.get(sketch.support_plane_id)
    if plane is None:
        return None, (f"{label}: sketch {sketch.name} has no support plane",)
    reasons: list[str] = []
    support = _support(plane)
    if support is None:
        reasons.append(
            f"{label}: sketch {sketch.name} is not placed on a principal plane"
        )
    operation = _operation(step, first=first)
    if operation is None:
        reasons.append(
            f"{label}: the {step.operation or 'unspecified'} operation "
            f"cannot be expressed{' in first position' if first else ''}"
        )
    end_condition = _end_condition(definition)
    if end_condition is None:
        reasons.append(
            f"{label}: the {definition.end_condition} end condition has no donor"
        )
    reasons.extend(f"{label}: {item}" for item in _extrusion_extras(definition))
    reverse = (
        None
        if support is None or operation is None
        else _reverse_flag(definition, plane, support, cut=operation == CUT_OPERATION)
    )
    if support is not None and operation is not None and reverse is None:
        reasons.append(
            f"{label}: the extrusion direction is not along the sketch normal"
        )
    profile: _Profile | None = None
    if support is not None:
        profile, profile_reasons = _profile(sketch, support)
        reasons.extend(
            f"{label}: sketch {sketch.name} {item}" for item in profile_reasons
        )
    depth_mm: float | None = None
    if end_condition is not None and end_condition != THROUGH_ALL_NAME:
        depth_mm = _scalar(definition.length, LENGTH_FACTORS_MM, ValueKind.LENGTH)
        if depth_mm is None:
            reasons.append(
                f"{label}: the extrusion depth {definition.length.value} "
                f"{definition.length.unit} is not a millimetre length"
            )
        elif depth_mm <= 0.0:
            reasons.append(
                f"{label}: the extrusion depth {depth_mm} mm is not positive"
            )
            depth_mm = None
    if (
        reasons
        or profile is None
        or support is None
        or operation is None
        or end_condition is None
    ):
        return None, tuple(reasons)
    return (
        TargetFeature(
            operation=operation,
            profile=profile.name,
            support=support.name,
            end_condition=end_condition,
            points_mm=profile.points_mm,
            radii_mm=profile.radii_mm,
            arc_centres_mm=profile.arc_centres_mm,
            depth_mm=depth_mm,
            reversed=None if end_condition == MID_PLANE_END else reverse,
        ),
        (),
    )


def _operation(step: FeatureStep, *, first: bool) -> str | None:
    operation = step.operation
    if operation is None:
        return BOSS_OPERATION if first else None
    if operation in BOSS_OPERATIONS:
        return BOSS_OPERATION
    if operation in CUT_OPERATIONS:
        return None if first else CUT_OPERATION
    return None


def _end_condition(definition: ExtrusionFeature) -> str | None:
    if definition.end_condition == ExtrusionEndCondition.THROUGH_ALL:
        return None if definition.symmetric else THROUGH_ALL_NAME
    if definition.symmetric:
        return MID_PLANE_END
    return END_CONDITION_NAMES.get(definition.end_condition)


def _extrusion_extras(definition: ExtrusionFeature) -> tuple[str, ...]:
    result: list[str] = []
    if definition.second_end_condition is not None:
        result.append("the second extrusion direction cannot be expressed")
    if not _is_zero(definition.offset) or not _is_zero(definition.second_offset):
        result.append("a start offset cannot be expressed")
    if not _is_zero(definition.draft_angle) or not _is_zero(
        definition.second_draft_angle
    ):
        result.append("a draft angle cannot be expressed")
    if definition.up_to_reference or definition.second_up_to_reference:
        result.append("an up-to reference cannot be expressed")
    return tuple(result)


def _is_zero(value) -> bool:
    return value is None or abs(value.value) <= _TOLERANCE_MM


def _support(plane: SupportPlane) -> _Support | None:
    transform = plane.transform
    origin = transform.origin
    if max(abs(origin.x), abs(origin.y), abs(origin.z)) > _TOLERANCE_MM:
        return None
    source = (
        (transform.x_axis.x, transform.x_axis.y, transform.x_axis.z),
        (transform.y_axis.x, transform.y_axis.y, transform.y_axis.z),
        (transform.z_axis.x, transform.z_axis.y, transform.z_axis.z),
    )
    if any(abs(_length(vector) - 1.0) > _AXIS_TOLERANCE for vector in source):
        return None
    for name, x_axis, y_axis, z_axis in PRINCIPAL_PLANE_FRAMES:
        if abs(abs(_dot(source[2], z_axis)) - 1.0) > _AXIS_TOLERANCE:
            continue
        rows = (
            (_dot(source[0], x_axis), _dot(source[1], x_axis)),
            (_dot(source[0], y_axis), _dot(source[1], y_axis)),
        )
        return _Support(name, rows, z_axis)
    return None


def _length(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _reverse_flag(
    definition: ExtrusionFeature,
    plane: SupportPlane,
    support: _Support,
    *,
    cut: bool,
) -> bool | None:
    direction = definition.direction
    if direction is None:
        vector = (
            plane.transform.z_axis.x,
            plane.transform.z_axis.y,
            plane.transform.z_axis.z,
        )
    else:
        vector = (direction.x, direction.y, direction.z)
    length = _length(vector)
    if not math.isfinite(length) or length <= _AXIS_TOLERANCE:
        return None
    unit = tuple(value / length for value in vector)
    dot = _dot(unit, support.normal)
    if abs(abs(dot) - 1.0) > _AXIS_TOLERANCE:
        return None
    along_normal = (dot > 0.0) is not bool(definition.reversed)
    return along_normal if cut else not along_normal


def _profile(
    sketch: Sketch, support: _Support
) -> tuple[_Profile | None, tuple[str, ...]]:
    entities = tuple(item for item in sketch.entities if not item.construction)
    if not entities:
        return None, ("holds no model geometry",)
    unsupported = sorted(
        {
            type(item.geometry).__name__
            for item in entities
            if not isinstance(item.geometry, (LineGeometry, CircleGeometry))
        }
    )
    if unsupported:
        return None, (f"uses unsupported geometry {', '.join(unsupported)}",)
    by_id = {item.id: item for item in entities}
    groups = tuple(
        tuple(group)
        for group in sketch.closed_profile_entity_ids
        if all(identifier in by_id for identifier in group)
    )
    if len(groups) != len(sketch.closed_profile_entity_ids):
        return None, ("closes a profile over construction geometry",)
    if not groups:
        groups = _derived_loops(entities, support)
    if not groups:
        return None, ("holds no closed profile",)
    covered = {identifier for group in groups for identifier in group}
    stray = sorted(set(by_id) - covered)
    if stray:
        return None, (f"leaves {len(stray)} entities outside any closed profile",)
    loops = tuple(tuple(by_id[identifier] for identifier in group) for group in groups)
    circles = tuple(
        loop[0]
        for loop in loops
        if len(loop) == 1 and isinstance(loop[0].geometry, CircleGeometry)
    )
    polylines = tuple(
        loop
        for loop in loops
        if all(isinstance(item.geometry, LineGeometry) for item in loop)
    )
    if len(circles) + len(polylines) != len(loops):
        return None, ("mixes lines and circles inside one closed profile",)
    if len(circles) > 1 or len(polylines) > 1:
        return None, (
            f"holds {len(polylines)} closed polylines and {len(circles)} circles",
        )
    radii = tuple(item.geometry.radius for item in circles)
    centres = tuple(
        support.project(item.geometry.center.x, item.geometry.center.y)
        for item in circles
    )
    if any(not math.isfinite(radius) or radius <= 0.0 for radius in radii):
        return None, ("holds a circle without a positive radius",)
    if not polylines:
        return _Profile(CIRCLE_PROFILE, (), radii, centres), ()
    vertices = _polyline_vertices(polylines[0], support)
    if vertices is None:
        return None, ("holds a polyline that does not close on itself",)
    rectangle = _axis_aligned_rectangle(vertices)
    if circles:
        if rectangle is None:
            return None, ("holds a circle inside a profile that is not a rectangle",)
        if not _circle_inside(rectangle, centres[0], radii[0]):
            return None, ("holds a circle that is not enclosed by its rectangle",)
        return _Profile(RECTANGLE_WITH_CIRCLE_PROFILE, rectangle, radii, centres), ()
    if rectangle is not None:
        return _Profile(RECTANGLE_PROFILE, rectangle, (), ()), ()
    return _Profile(polyline_profile(len(vertices)), vertices, (), ()), ()


def _derived_loops(
    entities: tuple[SketchEntity, ...], support: _Support
) -> tuple[tuple[str, ...], ...]:
    circles = tuple(
        (item.id,) for item in entities if isinstance(item.geometry, CircleGeometry)
    )
    lines = tuple(item for item in entities if isinstance(item.geometry, LineGeometry))
    if not lines:
        return circles
    remaining = list(lines)
    loops: list[tuple[str, ...]] = []
    while remaining:
        head = remaining.pop(0)
        chain = [head]
        start = support.project(head.geometry.start.x, head.geometry.start.y)
        tail = support.project(head.geometry.end.x, head.geometry.end.y)
        while not _same_point(tail, start):
            following = None
            for index, item in enumerate(remaining):
                first = support.project(item.geometry.start.x, item.geometry.start.y)
                last = support.project(item.geometry.end.x, item.geometry.end.y)
                if _same_point(first, tail):
                    following = (index, item, last)
                    break
                if _same_point(last, tail):
                    following = (index, item, first)
                    break
            if following is None:
                return ()
            index, item, tail = following
            remaining.pop(index)
            chain.append(item)
        if len(chain) < 3:
            return ()
        loops.append(tuple(item.id for item in chain))
    return (*loops, *circles)


def _circle_inside(
    rectangle: tuple[tuple[float, float], ...],
    centre: tuple[float, float],
    radius: float,
) -> bool:
    xs = tuple(point[0] for point in rectangle)
    ys = tuple(point[1] for point in rectangle)
    return (
        centre[0] - radius > min(xs) + _TOLERANCE_MM
        and centre[0] + radius < max(xs) - _TOLERANCE_MM
        and centre[1] - radius > min(ys) + _TOLERANCE_MM
        and centre[1] + radius < max(ys) - _TOLERANCE_MM
    )


def _polyline_vertices(
    loop: tuple[SketchEntity, ...], support: _Support
) -> tuple[tuple[float, float], ...] | None:
    if len(loop) < 3:
        return None
    segments = [
        (
            support.project(item.geometry.start.x, item.geometry.start.y),
            support.project(item.geometry.end.x, item.geometry.end.y),
        )
        for item in loop
    ]
    if any(
        not all(math.isfinite(value) for point in segment for value in point)
        for segment in segments
    ):
        return None
    ordered = [segments[0][0], segments[0][1]]
    remaining = segments[1:]
    while remaining:
        tail = ordered[-1]
        found = None
        for index, (start, end) in enumerate(remaining):
            if _same_point(start, tail):
                found = (index, end)
                break
            if _same_point(end, tail):
                found = (index, start)
                break
        if found is None:
            return None
        index, following = found
        remaining.pop(index)
        ordered.append(following)
    if not _same_point(ordered[0], ordered[-1]):
        return None
    vertices = tuple(ordered[:-1])
    if len(vertices) != len(loop):
        return None
    return vertices


def _same_point(left: tuple[float, float], right: tuple[float, float]) -> bool:
    return (
        abs(left[0] - right[0]) <= _TOLERANCE_MM
        and abs(left[1] - right[1]) <= _TOLERANCE_MM
    )


def _axis_aligned_rectangle(
    vertices: tuple[tuple[float, float], ...],
) -> tuple[tuple[float, float], ...] | None:
    if len(vertices) != 4:
        return None
    xs = sorted({round(point[0], 9) for point in vertices})
    ys = sorted({round(point[1], 9) for point in vertices})
    if len(xs) != 2 or len(ys) != 2:
        return None
    if xs[1] - xs[0] <= _MINIMUM_EXTENT_MM or ys[1] - ys[0] <= _MINIMUM_EXTENT_MM:
        return None
    corners = {(round(point[0], 9), round(point[1], 9)) for point in vertices}
    if corners != {(x, y) for x in xs for y in ys}:
        return None
    return rectangle_corners_mm(xs[0], ys[0], xs[1], ys[1])
