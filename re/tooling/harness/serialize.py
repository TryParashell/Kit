from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
import struct
import sys
import time

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import carchive
import streamlib

from convert.adapters.solidworks import resolved as resolvedlib

SKELETONS = SCRATCH / "grammar" / "skeletons"

METRE = 1000.0
CIRCLE_ANGLE_DEGREES = 17.0
PLANE_DISPLAY_MARGIN = 1.1

PLANE_IDS = {"front": 2, "top": 3, "right": 4}
END_CONDITIONS = {"blind": 0, "throughall": 1, "midplane": 6}

KEYWORDS_PREFIX = b"\x86"

SKETCH_ID_BASE = 26
FEATURE_ID_BASE = 32
ID_STRIDE = 7

BBOX_CLASS = "moBBoxCenterData_c"
BBOX_CENTRE_RELATIVE = 28
BBOX_DIAMETER_RELATIVE = 52

REF_PLANE_DATA_CLASS = "moDefaultRefPlnData_c"
REF_PLANE_CLASS = "moRefPlane_c"


class SerializeError(RuntimeError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Rectangle:
    width_mm: float
    height_mm: float
    centre_x_mm: float = 0.0
    centre_y_mm: float = 0.0

    @property
    def kind(self) -> str:
        return "rectangle"

    @property
    def area_mm2(self) -> float:
        return self.width_mm * self.height_mm

    def corners_mm(self) -> tuple[tuple[float, float], ...]:
        half_x = self.width_mm / 2.0
        half_y = self.height_mm / 2.0
        return resolvedlib.rectangle_corners_mm(
            self.centre_x_mm - half_x,
            self.centre_y_mm - half_y,
            self.centre_x_mm + half_x,
            self.centre_y_mm + half_y,
        )

    def bounds_mm(self) -> tuple[float, float, float, float]:
        half_x = self.width_mm / 2.0
        half_y = self.height_mm / 2.0
        return (
            self.centre_x_mm - half_x,
            self.centre_y_mm - half_y,
            self.centre_x_mm + half_x,
            self.centre_y_mm + half_y,
        )


@dataclass(frozen=True, slots=True)
class Circle:
    radius_mm: float
    centre_x_mm: float = 0.0
    centre_y_mm: float = 0.0

    @property
    def kind(self) -> str:
        return "circle"

    @property
    def area_mm2(self) -> float:
        return math.pi * self.radius_mm * self.radius_mm

    def bounds_mm(self) -> tuple[float, float, float, float]:
        return (
            self.centre_x_mm - self.radius_mm,
            self.centre_y_mm - self.radius_mm,
            self.centre_x_mm + self.radius_mm,
            self.centre_y_mm + self.radius_mm,
        )


@dataclass(frozen=True, slots=True)
class Extrude:
    profile: Rectangle | Circle
    depth_mm: float
    operation: str = "boss"
    plane: str = "front"
    end_condition: str = "blind"
    reversed: bool = False
    support: str = "plane"

    @property
    def shape(self) -> tuple[str, str, str, bool]:
        return (
            self.operation,
            self.profile.kind,
            self.support,
            self.end_condition != "throughall",
        )


@dataclass(frozen=True, slots=True)
class Part:
    features: tuple[Extrude, ...]
    name: str = "KitAuthored"
    document_name: str = "Part1"
    author_ids: bool = False
    dedupe_ids: bool = False
    write_depth_copies: bool = False
    write_bbox_cache: bool = False

    @property
    def shape(self) -> tuple[tuple[str, str, str, bool], ...]:
        return tuple(feature.shape for feature in self.features)


@dataclass(frozen=True, slots=True)
class Skeleton:
    shape: tuple[tuple[str, str, str, bool], ...]
    source: Path
    resolved: bytes
    keywords: bytes
    features_xml: bytes
    donor: streamlib.Donor
    grown: bool = False
    label: str = ""

    @property
    def name(self) -> str:
        return self.label or self.source.name


@dataclass(slots=True)
class Emission:
    resolved: bytes
    keywords: bytes
    features_xml: bytes
    writes: list[str] = field(default_factory=list)
    skeleton: str = ""


def signed_extent(feature: Extrude) -> tuple[float, float]:
    depth = feature.depth_mm
    code = END_CONDITIONS[feature.end_condition]
    if code == END_CONDITIONS["midplane"]:
        low, high = -depth / 2.0, depth / 2.0
    else:
        low, high = 0.0, depth
    if feature.reversed:
        low, high = -high, -low
    return low, high


def solid_volume_mm3(part: Part) -> float:
    total = 0.0
    for feature in part.features:
        low, high = signed_extent(feature)
        length = abs(high - low)
        volume = feature.profile.area_mm2 * length
        total += -volume if feature.operation == "cut" else volume
    return total


def sketch_ids(count: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (SKETCH_ID_BASE + index * ID_STRIDE, FEATURE_ID_BASE + index * ID_STRIDE)
        for index in range(count)
    )


def feature_names(part: Part) -> tuple[tuple[str, str], ...]:
    boss = 0
    cut = 0
    result: list[tuple[str, str]] = []
    for index, feature in enumerate(part.features):
        if feature.operation == "cut":
            cut += 1
            name = f"Cut-Extrude{cut}"
        else:
            boss += 1
            name = f"Boss-Extrude{boss}"
        result.append((f"Sketch{index + 1}", name))
    return tuple(result)


RESERVED_IDS = frozenset(range(1, 26))


def dedupe_identifiers(
    pairs: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, int], ...]:
    used = {value for pair in pairs for value in pair} | set(RESERVED_IDS)
    cursor = max(used) + 1
    seen: set[int] = set()
    result: list[tuple[int, int]] = []
    for sketch_id, feature_id in pairs:
        if sketch_id in seen or feature_id in seen:
            sketch_id = cursor
            feature_id = cursor + 1
            cursor += 2
        seen.add(sketch_id)
        seen.add(feature_id)
        result.append((sketch_id, feature_id))
    return tuple(result)


def feature_identifiers(blob: bytes, part: Part) -> tuple[tuple[int, int], ...]:
    if part.author_ids:
        return sketch_ids(len(part.features))
    entries = streamlib.comp_feature_entries(blob)
    pairs = tuple(
        (entries[index * 2][2], entries[index * 2 + 1][2])
        for index in range(len(part.features))
    )
    return dedupe_identifiers(pairs) if part.dedupe_ids else pairs


def load_skeletons() -> tuple[Skeleton, ...]:
    manifest = SKELETONS / "manifest.json"
    if not manifest.is_file():
        raise SerializeError(
            f"skeleton manifest is missing: run build_skeletons.py first ({manifest})"
        )
    import json

    entries = json.loads(manifest.read_text(encoding="utf-8"))
    result: list[Skeleton] = []
    for entry in entries:
        source = Path(entry["source"])
        donor = streamlib.load_donor(source)
        result.append(
            Skeleton(
                shape=tuple(
                    (item[0], item[1], item[2], bool(item[3]))
                    for item in entry["shape"]
                ),
                source=source,
                resolved=donor.resolved,
                keywords=donor.streams[streamlib.KEYWORDS],
                features_xml=donor.streams[streamlib.FEATURES],
                donor=donor,
            )
        )
    return tuple(result)


def grow_skeleton(shape: tuple[tuple[str, str, str, bool], ...]) -> Skeleton:
    scratch = SCRATCH / "re"
    if str(scratch) not in sys.path:
        sys.path.insert(0, str(scratch))
    import skeletongrow

    resolved, donor, label = skeletongrow.grow(shape)
    return Skeleton(
        shape=shape,
        source=donor.path,
        resolved=resolved,
        keywords=donor.streams[streamlib.KEYWORDS],
        features_xml=donor.streams[streamlib.FEATURES],
        donor=donor,
        grown=True,
        label=label,
    )


def select_skeleton(part: Part, skeletons: tuple[Skeleton, ...]) -> Skeleton:
    wanted = part.shape
    for skeleton in skeletons:
        if skeleton.shape == wanted:
            return skeleton
    scratch = SCRATCH / "re"
    if str(scratch) not in sys.path:
        sys.path.insert(0, str(scratch))
    import skeletongrow

    if skeletongrow.match(wanted) is not None:
        return grow_skeleton(wanted)
    available = "; ".join(str(skeleton.shape) for skeleton in skeletons)
    raise SerializeError(f"no skeleton matches shape {wanted}; available: {available}")


def emit(part: Part, skeletons: tuple[Skeleton, ...] | None = None) -> Emission:
    catalogue = load_skeletons() if skeletons is None else skeletons
    skeleton = select_skeleton(part, catalogue)
    if skeleton.grown and not part.author_ids:
        from dataclasses import replace

        part = replace(part, dedupe_ids=True)
    output = bytearray(skeleton.resolved)
    writes: list[str] = []
    _write_comp_features(output, part, writes)
    _write_tree_nodes(output, part, writes)
    _write_sketches(output, part, writes)
    _write_extrusions(output, part, writes)
    _write_plane_reference(output, part, writes)
    _write_bbox_cache(output, part, writes)
    _write_plane_display(output, part, writes)
    final = bytes(output)
    names = stream_names(final)
    return Emission(
        resolved=final,
        keywords=emit_keywords(part, names, feature_identifiers(final, part)),
        features_xml=emit_features_xml(part),
        writes=writes,
        skeleton=skeleton.name,
    )


def stream_names(blob: bytes) -> tuple[tuple[str, str], ...]:
    nodes = streamlib.tree_nodes(blob)
    sketches = [node.name for node in nodes if node.name.startswith("Sketch")]
    features = [
        node.name for node in nodes if resolvedlib.feature_kind(node.flags) is not None
    ]
    return tuple(zip(sketches, features, strict=True))


def _write_comp_features(output: bytearray, part: Part, writes: list[str]) -> None:
    entries = streamlib.comp_feature_entries(bytes(output))
    expected = 2 * len(part.features)
    if len(entries) != expected:
        raise SerializeError(
            f"skeleton has {len(entries)} moCompFeature_c entries, "
            f"{expected} required for {len(part.features)} features"
        )
    stamp = int(time.time())
    flat = [
        value for pair in feature_identifiers(bytes(output), part) for value in pair
    ]
    for entry, identifier in zip(entries, flat, strict=True):
        streamlib.write_u32(output, entry[1] - streamlib.COMP_ENTRY_ID_BACK, identifier)
        streamlib.write_u32(output, entry[1] - streamlib.COMP_ENTRY_TIME_BACK, stamp)
    writes.append(
        f"moCompFeature_c ids={flat} stamp={stamp} "
        f"({'authored' if part.author_ids else 'inherited'})"
    )


def _write_tree_nodes(output: bytearray, part: Part, writes: list[str]) -> None:
    identifiers = feature_identifiers(bytes(output), part)
    nodes = streamlib.tree_nodes(bytes(output))
    sketches = [node for node in nodes if node.name.startswith("Sketch")]
    features = [
        node for node in nodes if resolvedlib.feature_kind(node.flags) is not None
    ]
    if len(sketches) != len(part.features) or len(features) != len(part.features):
        raise SerializeError(
            f"skeleton exposes {len(sketches)} sketches and {len(features)} features, "
            f"{len(part.features)} of each required"
        )
    for index, feature in enumerate(part.features):
        sketch_id, feature_id = identifiers[index]
        streamlib.write_u32(output, sketches[index].text_end + 8, sketch_id)
        node = features[index]
        flags = (
            streamlib.CUT_FLAGS if feature.operation == "cut" else streamlib.BOSS_FLAGS
        )
        if resolvedlib.feature_kind(node.flags) != feature.operation:
            raise SerializeError(
                f"skeleton feature {index} is a "
                f"{resolvedlib.feature_kind(node.flags)} and {feature.operation} "
                f"was requested; the operation is not writable, see results.md E1/E2/A3"
            )
        preserved = node.flags & 0x80000000
        streamlib.write_u32(output, node.text_end + 4, flags | preserved)
        streamlib.write_u32(output, node.text_end + 8, feature_id)
        writes.append(
            f"tree[{index}] {node.name!r} flags=0x{flags:08x} "
            f"at {node.text_end + 4}, id={feature_id} at {node.text_end + 8}, "
            f"sketch id={sketch_id} at {sketches[index].text_end + 8}"
        )


def _write_sketches(output: bytearray, part: Part, writes: list[str]) -> None:
    blob = bytes(output)
    nodes = streamlib.tree_nodes(blob)
    sketches = [node for node in nodes if node.name.startswith("Sketch")]
    features = [
        node for node in nodes if resolvedlib.feature_kind(node.flags) is not None
    ]
    points = resolvedlib.sketch_points(blob)
    arcs = resolvedlib.sketch_arcs(blob)
    for index, feature in enumerate(part.features):
        low = sketches[index].offset
        high = features[index].offset
        if isinstance(feature.profile, Rectangle):
            owned = [point for point in points if low < point.offset < high]
            if len(owned) != 4:
                raise SerializeError(
                    f"skeleton sketch {index} has {len(owned)} points, 4 required"
                )
            for point, (x, y) in zip(owned, feature.profile.corners_mm(), strict=True):
                streamlib.write_double(output, point.offset, x / METRE)
                streamlib.write_double(output, point.offset + 8, y / METRE)
            writes.append(
                f"sketch[{index}] rectangle {feature.profile.corners_mm()} "
                f"at {[point.offset for point in owned]}"
            )
            continue
        owned_arcs = [arc for arc in arcs if low < arc.centre_offset < high]
        if len(owned_arcs) != 1:
            raise SerializeError(
                f"skeleton sketch {index} has {len(owned_arcs)} arcs, 1 required"
            )
        arc = owned_arcs[0]
        centre_x = feature.profile.centre_x_mm / METRE
        centre_y = feature.profile.centre_y_mm / METRE
        angle = math.radians(CIRCLE_ANGLE_DEGREES)
        radius = feature.profile.radius_mm / METRE
        streamlib.write_double(output, arc.centre_offset, centre_x)
        streamlib.write_double(output, arc.centre_offset + 8, centre_y)
        streamlib.write_double(
            output, arc.point_offset, centre_x + radius * math.cos(angle)
        )
        streamlib.write_double(
            output, arc.point_offset + 8, centre_y + radius * math.sin(angle)
        )
        writes.append(
            f"sketch[{index}] circle r={feature.profile.radius_mm} "
            f"centre@{arc.centre_offset} point@{arc.point_offset}"
        )


def _write_extrusions(output: bytearray, part: Part, writes: list[str]) -> None:
    layouts = resolvedlib.locate_features(bytes(output))
    if len(layouts) != len(part.features):
        raise SerializeError(
            f"skeleton exposes {len(layouts)} extrusions, "
            f"{len(part.features)} required"
        )
    for index, feature in enumerate(part.features):
        layout = layouts[index]
        code = END_CONDITIONS[feature.end_condition]
        if layout.depth_offset is None:
            if code != END_CONDITIONS["throughall"]:
                raise SerializeError(
                    f"skeleton feature {index} has no dimension scalar, "
                    f"only ThroughAll can be emitted"
                )
            writes.append(f"extrude[{index}] ThroughAll, no scalar in skeleton")
            continue
        base = feature.depth_mm / METRE
        deltas = resolvedlib.DEPTH_COPY_DELTAS if part.write_depth_copies else (0,)
        signs = resolvedlib.DEPTH_COPY_SIGNS if part.write_depth_copies else (1,)
        for delta, sign in zip(deltas, signs, strict=True):
            target = layout.depth_offset + delta
            if target + 8 <= len(output):
                streamlib.write_double(output, target, sign * base)
        output[layout.reverse_offset] = 1 if feature.reversed else 0
        output[layout.end_condition_offset] = code
        writes.append(
            f"extrude[{index}] depth={feature.depth_mm} at {layout.depth_offset} "
            f"copies={list(deltas)}, "
            f"reverse={int(feature.reversed)} at {layout.reverse_offset}, "
            f"end={code} at {layout.end_condition_offset}"
        )


def _write_plane_reference(output: bytearray, part: Part, writes: list[str]) -> None:
    blob = bytes(output)
    records = resolvedlib.class_records(blob)
    chain = resolvedlib.first_class_offset(records, resolvedlib.SKETCH_CHAIN_CLASS)
    if chain is None:
        return
    wanted = PLANE_IDS[part.features[0].plane]
    for offset in range(chain, min(chain + 400, len(blob) - 14)):
        candidate = struct.unpack_from("<I", blob, offset)[0]
        if candidate not in {2, 3, 4}:
            continue
        if struct.unpack_from("<I", blob, offset + 10)[0] != 5 - candidate:
            continue
        streamlib.write_u32(output, offset, wanted)
        streamlib.write_u32(output, offset + 10, 5 - wanted)
        writes.append(
            f"sketch plane id={wanted} axis={5 - wanted} at {offset}/{offset + 10}"
        )
        return


def body_bounds_mm(part: Part) -> tuple[float, float, float, float, float, float]:
    minimum_x = minimum_y = minimum_z = math.inf
    maximum_x = maximum_y = maximum_z = -math.inf
    for feature in part.features:
        if feature.operation == "cut":
            continue
        low_x, low_y, high_x, high_y = feature.profile.bounds_mm()
        low_z, high_z = signed_extent(feature)
        minimum_x = min(minimum_x, low_x)
        maximum_x = max(maximum_x, high_x)
        minimum_y = min(minimum_y, low_y)
        maximum_y = max(maximum_y, high_y)
        minimum_z = min(minimum_z, low_z)
        maximum_z = max(maximum_z, high_z)
    if not math.isfinite(minimum_x):
        raise SerializeError("a part needs at least one additive feature")
    plane = part.features[0].plane
    if plane == "front":
        return minimum_x, maximum_x, minimum_y, maximum_y, minimum_z, maximum_z
    if plane == "top":
        return minimum_x, maximum_x, minimum_z, maximum_z, minimum_y, maximum_y
    return minimum_z, maximum_z, minimum_y, maximum_y, minimum_x, maximum_x


def _write_bbox_cache(output: bytearray, part: Part, writes: list[str]) -> None:
    blob = bytes(output)
    records = resolvedlib.class_records(blob)
    offset = resolvedlib.first_class_offset(records, BBOX_CLASS)
    if offset is None:
        return
    if not part.write_bbox_cache:
        writes.append(f"{BBOX_CLASS} left stale (derived body bounding cache)")
        return
    if any(feature.support != "plane" for feature in part.features):
        writes.append(
            f"{BBOX_CLASS} left stale: a face-supported feature makes the "
            f"sketch-frame extent unknown to the writer"
        )
        return
    if len({feature.plane for feature in part.features}) != 1:
        writes.append(f"{BBOX_CLASS} left stale: features span several planes")
        return
    low_x, high_x, low_y, high_y, low_z, high_z = body_bounds_mm(part)
    centre = (
        (low_x + high_x) / 2.0,
        (low_y + high_y) / 2.0,
        (low_z + high_z) / 2.0,
    )
    half = (
        (high_x - low_x) / 2.0,
        (high_y - low_y) / 2.0,
        (high_z - low_z) / 2.0,
    )
    diameter = 2.0 * math.sqrt(sum(value * value for value in half))
    base = offset + BBOX_CENTRE_RELATIVE
    for index, value in enumerate(centre):
        streamlib.write_double(output, base + index * 8, value / METRE)
    streamlib.write_double(output, offset + BBOX_DIAMETER_RELATIVE, diameter / METRE)
    writes.append(
        f"{BBOX_CLASS} centre={centre} diameter={diameter} at {base}"
        f"/{offset + BBOX_DIAMETER_RELATIVE}"
    )


def _write_plane_display(output: bytearray, part: Part, writes: list[str]) -> None:
    blob = bytes(output)
    records = resolvedlib.class_records(blob)
    offset = resolvedlib.first_class_offset(records, REF_PLANE_DATA_CLASS)
    if offset is None:
        return
    low_x, high_x, low_y, high_y, low_z, high_z = body_bounds_mm(part)
    span = max(
        high_x - low_x,
        high_y - low_y,
        high_z - low_z,
    )
    writes.append(
        f"{REF_PLANE_DATA_CLASS} left stale (derived display extents, span={span})"
    )


def emit_keywords(
    part: Part,
    names: tuple[tuple[str, str], ...],
    identifiers: tuple[tuple[int, int], ...],
) -> bytes:
    stamp = int(time.time())
    pieces: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>\r\n',
        f'<Keywords id="{stamp}" Name="{part.document_name}">',
        '<Configuration id="0" Name="Default" Type="ConfigurationManager" '
        'Material="Material &lt;not specified&gt;"/>',
    ]
    for index, feature in enumerate(part.features):
        sketch_id, feature_id = identifiers[index]
        dimension = (
            ""
            if feature.end_condition == "throughall"
            else f'<Dimension Name="D1">{_number(feature.depth_mm)}</Dimension>'
        )
        if index == 0:
            attributes = ' Type="Boss-Extrude"'
        else:
            attributes = (
                f' Dissectable="true" DissectableChildren="{sketch_id}"'
                ' DissectableRoot="true"'
            )
        if dimension:
            pieces.append(
                f'<Extrusion id="{feature_id}" Name="{names[index][1]}"'
                f"{attributes}>{dimension}</Extrusion>"
            )
        else:
            pieces.append(
                f'<Extrusion id="{feature_id}" Name="{names[index][1]}"'
                f"{attributes}/>"
            )
    for identifier, name, kind in _BOILERPLATE_FEATURES:
        pieces.append(f'<Feature id="{identifier}" Name="{name}" Type="{kind}"/>')
    for index in range(len(part.features)):
        pieces.append(
            f'<Sketch id="{identifiers[index][0]}" Name="{names[index][0]}" '
            'Dissectable="true"/>'
        )
    pieces.append('<Sketch id="5" Name="Origin" Type="Origin"/>')
    pieces.append("</Keywords>\r\n")
    return KEYWORDS_PREFIX + "".join(pieces).encode("utf-8")


def emit_features_xml(part: Part) -> bytes:
    stamp = int(time.time())
    document = (
        '<?xml version="1.0" encoding="UTF-8"?>\r\n'
        '<swSolidWorks xmlns="http://www.solidworks.com/sw2003/schema" '
        'swObjCount="3" swVersion="18000"><swHeader swObjCount="1">'
        f'<swFile id="3" swDocType="PART" swCreationTime="{stamp}" '
        f'swPath="{part.name}.sldprt"/></swHeader>'
        '<swModelList swObjCount="1">'
        f'<swModel id="2" swName="{part.name}" swConfigurationName="Default" '
        'swConfigurationId="0" swLastModifiedStamp="106" '
        'swConfigurationFlags="-2143288960" swFileRef="3"/></swModelList>'
        '<swConfigurationList swObjCount="1">'
        '<swConfiguration id="1" swName="Default" swID="0" '
        f'swReference="{part.document_name}" swMostRecentConfiguration="YES" '
        'swConfigurationNeedsUpdate="NO" swDefeatureConfiguration="NO" '
        'swModelRef="2"/></swConfigurationList>'
        '<swExtFeatureList swObjCount="0"/></swSolidWorks>\r\n'
    )
    return document.encode("utf-8")


def _number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return repr(float(value))


_BOILERPLATE_FEATURES: tuple[tuple[int, str, str], ...] = (
    (1, "Annotations", "Annotations"),
    (10, "Surface Bodies", "Surface Bodies"),
    (11, "Material &lt;not specified&gt;", "SOLIDWORKS Materials"),
    (12, "Ambient", "Ambient"),
    (13, "Directional1", "Directional"),
    (14, "Directional2", "Directional"),
    (15, "Directional3", "Directional"),
    (16, "Equations", "Equations"),
    (17, "Notes", "Notes"),
    (18, "Notes1___EndTag___", "Notes"),
    (19, "", "Exploded Views"),
    (2, "Front Plane", "Plane"),
    (21, "Markups", "Markups"),
    (22, "Sensors", "Sensors"),
    (23, "Favorites", "Favorites"),
    (24, "History", "History"),
    (25, "Selection Sets", "Selection Sets"),
    (3, "Top Plane", "Plane"),
    (4, "Right Plane", "Plane"),
    (6, "Lights and Cameras", "Lights and Cameras"),
    (7, "Design Binder", "Design Binder"),
    (8, "Comments", "Comments"),
    (9, "Solid Bodies", "Solid Bodies"),
)


def build_part(part: Part, target: Path, skeletons: tuple[Skeleton, ...] | None = None):
    catalogue = load_skeletons() if skeletons is None else skeletons
    skeleton = select_skeleton(part, catalogue)
    emission = emit(part, (skeleton,) + tuple(catalogue))
    container = streamlib.rebuild(
        skeleton.donor,
        {
            streamlib.RESOLVED: emission.resolved,
            streamlib.KEYWORDS: emission.keywords,
            streamlib.FEATURES: emission.features_xml,
        },
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(container)
    return emission, len(container)
