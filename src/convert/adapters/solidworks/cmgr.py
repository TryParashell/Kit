# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
import struct

from .archive import (
    CLASS_REFERENCE_KIND,
    DEFINITION_KIND,
    NULL_KIND,
    OBJECT_REFERENCE_KIND,
    Model,
    Node,
    encode_class_definition,
    encode_string,
)
from .container import SldprtFormatError

CONFIGURATION_MANAGER_STREAM = "Contents/CMgr"

ROOT_CLASS = "moConfigurationMgr_c"
CONFIGURATION_CLASS = "moPartConfiguration_c"
NODE_NAME_CLASS = "moNodeName_c"
VISUAL_CLASS = "moVisualProperties_c"
LINK_CLASS = "moLinkedAtomIdNode_c"
EXT_OBJECT_CLASS = "moExtObject_c"
STRING_HANDLE_CLASS = "moCStringHandle_c"
OBJECT_LIST_CLASS = "suObList"
CLASS_SCHEMA = 1
MAP_BASE = 3

DOCUMENT_GENERATION = 18000
DOCUMENT_BUILD = 2025268
SESSION_COUNTER = 360108
FIRST_ATOM_ID = 101
DISPLAY_STATE_KIND = 5
DISPLAY_STATE_REVISION = 2
DISPLAY_STATE_MASK = 0x80400180
DISPLAY_TAIL = (0x00, 0x00, 0x80, 0x9D, 0x9E, 0x25)
DISPLAY_CHORD_RATIO = 0.99
VIEW_STYLE_MODE = 3
LINK_TERMINATOR = 2
LINK_FLAG = 1
OBJECT_LIST_KIND = 2
NODE_NAME_SCALE = 2.0
NODE_NAME_FLAGS = 512
MANAGER_SCALE = 2.0
STRING_HANDLE_KIND = 2
DEFAULT_CONFIGURATION_NAME = "Default"
DEFAULT_PART_NAME = "Part1"
DEFAULT_RENDER_STYLE = 5

FIRST_TREE_ID = 32
TREE_ID_STEP = 8
DOCUMENT_STAMP_HIGH = 0x01DD2399
DOCUMENT_STAMP_LOW = 0x10000000

DISPLAY_GEOMETRY_CACHE_BYTES = 96
DISPLAY_GEOMETRY_CACHE_DEFAULT = bytes(DISPLAY_GEOMETRY_CACHE_BYTES)

RESIDUAL_SPANS = (("display_geometry_cache", ROOT_CLASS, DISPLAY_GEOMETRY_CACHE_BYTES),)

VISUAL_PROPERTIES = (
    ("appearance_id", "u32", 15651274),
    ("reserved_4", "zeros", 8),
    ("appearance_library", "str", ""),
    ("material_name", "str", "Steel"),
    ("diffuse", "f64", 1.0),
    ("specular", "f64", 1.0),
    ("ambient", "f64", 0.5),
    ("emission", "f64", 0.3125),
    ("reserved_64", "zeros", 20),
    ("use_material", "u32", 1),
    ("reserved_86", "u32", 0),
    ("use_appearance", "u32", 1),
    ("use_texture", "u32", 1),
    ("use_display", "u32", 1),
    ("display_name", "str", ""),
    ("visible", "u32", 1),
    ("selectable", "u32", 1),
    ("render_style", "u32", DEFAULT_RENDER_STYLE),
    ("reserved_118", "u32", 0),
    ("appearance_name", "str", "defaultplastic"),
    ("optics_kind_and_id", "u32", 4006726147),
    ("optics_head", "u32", 2147483648),
    ("optics_scale", "u32", 63),
    ("optics_zero_166", "zeros", 11),
    ("optics_one_177", "u32", 16256),
    ("optics_zero_181", "zeros", 16),
    ("optics_one_197", "u32", 81792),
    ("optics_highlight_201", "u32", 2577006592),
    ("optics_highlight_205", "u32", 15897),
    ("optics_zero_209", "u32", 0),
    ("optics_minus_213", "u32", 49024),
    ("optics_minus_217", "u32", 49024),
    ("optics_minus_221", "u32", 49024),
    ("optics_zero_225", "zeros", 10),
    (
        "texture_path",
        "str",
        "C:\\PROGRA~1\\SOLIDW~1\\SOLIDW~1\\data\\graphics\\materials\\color.p2m",
    ),
    ("texture_head", "f64", 9.765627351043803e-05),
    ("texture_weight", "f32", 1.0),
    ("texture_name", "str", ""),
    ("texture_scale_u", "f32", 0.0010000000474974513),
    ("texture_scale_v", "f32", 0.0010000000474974513),
    ("texture_zero", "u32", 0),
    ("texture_rows", "u32", 320),
    ("matrix_zero_a", "zeros", 10),
    ("matrix_one_a", "u32", 16256),
    ("matrix_zero_b", "zeros", 12),
    ("matrix_one_b", "u32", 16256),
    ("matrix_zero_c", "zeros", 12),
    ("matrix_one_c", "u32", 16256),
    ("matrix_scale", "u32", 17076),
    ("edge_one", "u32", 16256),
    ("edge_minus_a", "u32", 49024),
    ("edge_minus_b", "u8", 128),
    ("edge_minus_c", "u16", 65471),
    ("edge_pad_a", "u32", 65534),
    ("edge_pad_b", "u16", 0),
    ("edge_pad_c", "u16", 65280),
    ("edge_pad_d", "u16", 65534),
    ("edge_pad_e", "u16", 65280),
    ("edge_pad_f", "u16", 65534),
    ("edge_pad_g", "u16", 65280),
    ("edge_pad_h", "u32", 65534),
    ("reserved_478", "zeros", 91),
    ("decal_name", "str", ""),
    ("reserved_573", "zeros", 8),
    ("scene_name", "str", ""),
    ("scene_zero", "u32", 0),
    ("scene_flag", "u32", 1),
    ("light_name", "str", ""),
    ("light_zero", "u32", 0),
    ("light_flag", "u32", 1),
    ("owner_handle", "u32", 4294967295),
    ("identity_zero_a", "zeros", 20),
    ("identity_atom", "u32", FIRST_ATOM_ID),
    ("identity_zero_b", "zeros", 13),
    ("identity_generation", "u32", DOCUMENT_GENERATION),
    ("identity_zero_c", "zeros", 8),
    ("identity_build", "u32", DOCUMENT_BUILD),
)

ATOM_TABLE_HEAD = (
    ("table_flags", "u32", 0),
    ("table_kind", "u32", 65536),
    ("table_zero_a", "zeros", 10),
    ("table_chord", "f64", -0.007812500000000002),
    ("table_minus_one", "f32", -1.0),
    ("table_zero_b", "zeros", 8),
    ("table_flag_a", "u32", 1),
    ("table_zero_c", "zeros", 28),
    ("table_flag_b", "u32", 1),
    ("table_zero_d", "u32", 0),
    ("table_owner", "u32", 4294967295),
    ("table_flag_c", "u32", 1),
    ("table_zero_e", "zeros", 12),
)

VIEW_STYLE = (
    ("style_name", "str", ""),
    ("style_zero", "u8", 0),
    ("style_mask", "u16", 65535),
    ("style_pad", "u16", 0),
    ("style_mode", "u8", VIEW_STYLE_MODE),
    ("style_owner_a", "u32", 4294967295),
    ("style_owner_b", "u32", 4294967295),
    ("style_scale", "f32", -1.0),
    ("style_offset", "f64", 0.0),
)

OBJECT_LIST_TAIL = (
    ("list_zero_a", "zeros", 28),
    ("list_kind", "u32", OBJECT_LIST_KIND),
    ("list_zero_b", "zeros", 4),
    ("list_name", "str", ""),
    ("list_zero_c", "zeros", 12),
    ("list_owner", "u32", 4294967295),
    ("list_zero_d", "zeros", 8),
)


@dataclass(frozen=True, slots=True)
class Stamp:
    high: int
    low: int

    def pack(self) -> bytes:
        return struct.pack("<II", self.high, self.low)


ZERO_STAMP = Stamp(0, 0)
DOCUMENT_STAMP = Stamp(DOCUMENT_STAMP_HIGH, DOCUMENT_STAMP_LOW)
DEFAULT_FEATURE_TREE_IDS = (FIRST_TREE_ID,)


@dataclass(frozen=True, slots=True)
class FeatureStamp:
    tree_id: int
    stamp: Stamp = ZERO_STAMP


@dataclass(frozen=True, slots=True)
class CMgrParameters:
    configuration_name: str
    part_name: str
    name_stamp: int
    atom_ids: tuple[int, ...]
    link_atom_ids: tuple[int, ...]
    link_tree_ids: tuple[int, ...]
    reverse_atom_ids: tuple[int, ...]
    feature_stamps: tuple[FeatureStamp, ...]
    display_stamp: Stamp
    view_stamp: Stamp
    max_tree_id: int
    next_id_a: int
    next_id_b: int
    render_style: int
    atom_head_count: int
    chord_ratio: float
    generation: int
    build: int
    session_counter: int
    display_geometry_cache: bytes

    def validate(self) -> None:
        if not self.atom_ids:
            raise SldprtFormatError(
                "a SOLIDWORKS configuration manager needs at least one atom id"
            )
        if len(self.link_tree_ids) != len(self.link_atom_ids):
            raise SldprtFormatError(
                f"{len(self.link_atom_ids)} linked atoms need "
                f"{len(self.link_atom_ids)} tree ids, got {len(self.link_tree_ids)}"
            )
        if len(self.display_geometry_cache) != DISPLAY_GEOMETRY_CACHE_BYTES:
            raise SldprtFormatError(
                "display_geometry_cache is a "
                f"{DISPLAY_GEOMETRY_CACHE_BYTES} byte span, got "
                f"{len(self.display_geometry_cache)}"
            )
        if self.generation != DOCUMENT_GENERATION:
            raise SldprtFormatError(
                f"the recovered Contents/CMgr tables describe generation "
                f"{DOCUMENT_GENERATION}, not {self.generation}"
            )


def _pack(kind: str, value: object) -> bytes:
    if kind == "u8":
        return struct.pack("<B", int(value))
    if kind == "u16":
        return struct.pack("<H", int(value))
    if kind == "u32":
        return struct.pack("<I", int(value))
    if kind == "f32":
        return struct.pack("<f", float(value))
    if kind == "f64":
        return struct.pack("<d", float(value))
    if kind == "str":
        return encode_string(str(value))
    if kind == "zeros":
        return bytes(int(value))
    raise SldprtFormatError(f"unsupported Contents/CMgr field kind {kind!r}")


def _table(
    fields: tuple[tuple[str, str, object], ...],
    overrides: dict[str, object] | None = None,
) -> bytes:
    out = bytearray()
    for name, kind, value in fields:
        if overrides is not None and name in overrides:
            value = overrides[name]
        out += _pack(kind, value)
    return bytes(out)


def _manager_head() -> bytes:
    return (
        _pack("f64", MANAGER_SCALE)
        + _pack("u32", 0xFFFFFFFF)
        + _pack("u32", 0)
        + encode_string("")
        + _pack("u32", 0)
    )


def _identity_block(atom_id: int, generation: int, build: int) -> bytes:
    return (
        _pack("u32", 0)
        + _pack("u32", 0)
        + _pack("u32", atom_id)
        + _pack("u32", 0)
        + _pack("u32", 0)
        + _pack("u32", 0)
        + _pack("u8", 0)
        + _pack("u32", generation)
        + _pack("u32", 0)
        + _pack("u32", 0)
        + _pack("u32", build)
    )


def _display_state(stamp: Stamp, session: int) -> bytes:
    return (
        _pack("u32", 0)
        + _pack("u32", DISPLAY_STATE_KIND)
        + _pack("u32", 0)
        + _pack("u16", 0)
        + _pack("u32", 0xFFFFFFFF)
        + stamp.pack()
        + _pack("u16", DISPLAY_STATE_REVISION)
        + _pack("u32", session)
        + _pack("u32", 1)
    )


def _display_state_full(params: CMgrParameters) -> bytes:
    return (
        _display_state(params.view_stamp, params.session_counter)
        + encode_string("")
        + _pack("u32", 0xFFFFFFFF)
        + _pack("u32", DISPLAY_STATE_MASK)
        + encode_string("")
        + _pack("u32", params.max_tree_id)
        + _pack("u32", params.next_id_a)
        + _pack("u32", params.next_id_b)
        + bytes(params.display_geometry_cache)
        + _pack("u32", 1)
        + bytes(16)
        + _pack("f64", params.chord_ratio)
        + bytes(16)
        + encode_string("")
        + encode_string("")
        + bytes(28)
        + _pack("f64", 1.0)
        + bytes(24)
        + _pack("f64", 1.0)
        + bytes(24)
        + _pack("f64", 1.0)
        + _pack("u32", 1)
        + bytes(DISPLAY_TAIL)
    )


def _node_name(name: str) -> bytes:
    return (
        encode_string(name)
        + _pack("f64", NODE_NAME_SCALE)
        + _pack("u32", 0)
        + _pack("u32", NODE_NAME_FLAGS)
        + encode_string("")
        + _pack("u32", 0)
    )


def _visual_properties(params: CMgrParameters) -> bytes:
    return _table(
        VISUAL_PROPERTIES,
        {
            "render_style": params.render_style,
            "identity_atom": params.atom_ids[0],
            "identity_generation": params.generation,
            "identity_build": params.build,
        },
    )


def _atom_head(count: int, generation: int) -> bytes:
    return (
        _pack("u16", 0)
        + _pack("u16", count)
        + _pack("u32", 0)
        + _pack("u16", 0)
        + _pack("u16", generation)
        + _pack("u16", 0)
        + _pack("u16", 1)
    )


def _atom_table(atom_ids: tuple[int, ...]) -> bytes:
    out = bytearray(_table(ATOM_TABLE_HEAD))
    out += _pack("u32", len(atom_ids))
    for atom in atom_ids:
        out += _pack("u32", atom) + _pack("u32", 0)
    out += bytes(30)
    return bytes(out)


def _link_head(atom_ids: tuple[int, ...]) -> bytes:
    return (
        _pack("u32", 0)
        + _pack("u32", 0)
        + _pack("u32", len(atom_ids))
        + _pack("u32", atom_ids[0] if atom_ids else 0)
    )


def _link_body(atom_id: int, tree_id: int, next_id: int | None) -> bytes:
    head = _pack("u32", atom_id) + _pack("u16", LINK_FLAG) + _pack("u32", tree_id)
    if next_id is None:
        return head + bytes(34) + _pack("u32", LINK_TERMINATOR) + bytes(8)
    return head + bytes(18) + _pack("u32", next_id)


def _reverse_table(atom_ids: tuple[int, ...]) -> bytes:
    out = bytearray()
    out += _pack("u32", 0)
    out += _pack("u32", 0xFFFFFFFF)
    out += _pack("u32", len(atom_ids))
    for atom in atom_ids:
        out += _pack("u32", atom) + _pack("u32", 0)
    out += bytes(8)
    out += _pack("u32", 0xFFFFFFFF)
    out += _pack("u32", 0xFFFFFFFF)
    out += bytes(8)
    return bytes(out)


def _string_handle_body(params: CMgrParameters) -> bytes:
    return (
        encode_string(params.part_name)
        + _pack("u16", STRING_HANDLE_KIND)
        + _pack("u8", 0)
        + _pack("u32", params.name_stamp)
        + encode_string("")
        + encode_string("")
        + encode_string("")
        + bytes(18)
        + encode_string(params.configuration_name)
        + bytes(20)
        + encode_string("")
        + bytes(4)
    )


def _stamp_list(stamps: tuple[FeatureStamp, ...]) -> bytes:
    out = bytearray()
    out += _pack("u16", 0)
    out += _pack("u32", len(stamps))
    for entry in stamps:
        out += _pack("u32", entry.tree_id) + entry.stamp.pack()
    out += bytes(8)
    out += _pack("u32", 1)
    out += bytes(8)
    return bytes(out)


def build_model(params: CMgrParameters) -> Model:
    params.validate()
    nodes: list[Node] = []

    def null(body: bytes) -> None:
        nodes.append(Node(kind=NULL_KIND, body=body))

    def definition(name: str, body: bytes) -> int:
        nodes.append(
            Node(
                kind=DEFINITION_KIND,
                body=body,
                schema=CLASS_SCHEMA,
                class_name=name,
            )
        )
        return len(nodes) - 1

    def classref(target: int, body: bytes) -> None:
        nodes.append(
            Node(
                kind=CLASS_REFERENCE_KIND,
                body=body,
                class_name=nodes[target].class_name,
                target=target,
            )
        )

    def objectref(target: int, body: bytes) -> None:
        nodes.append(Node(kind=OBJECT_REFERENCE_KIND, body=body, target=target))

    null(_manager_head())
    null(_identity_block(params.atom_ids[0], params.generation, params.build))
    null(_table(VIEW_STYLE))
    null(_display_state(params.display_stamp, params.session_counter))
    configuration = definition(CONFIGURATION_CLASS, b"")
    definition(NODE_NAME_CLASS, _node_name(params.configuration_name))
    definition(VISUAL_CLASS, _visual_properties(params))
    null(_table(VIEW_STYLE))
    null(_display_state_full(params))
    null(_atom_head(params.atom_head_count, params.generation))
    null(_atom_table(params.atom_ids))
    null(_link_head(params.link_atom_ids))
    total = len(params.link_atom_ids)
    link = -1
    for position, atom in enumerate(params.link_atom_ids):
        following = params.link_atom_ids[position + 1] if position + 1 < total else None
        body = _link_body(atom, params.link_tree_ids[position], following)
        if position == 0:
            link = definition(LINK_CLASS, body)
        else:
            classref(link, body)
    null(_pack("u32", 0) + _pack("u32", 1) + _pack("u32", 0xFFFFFFFF))
    null(b"")
    null(bytes(36))
    null(b"")
    null(_pack("f64", -1.0))
    null(_pack("f64", 0.0))
    null(b"")
    null(_reverse_table(params.reverse_atom_ids))
    objectref(configuration, _pack("u32", 1) + _pack("u16", 1))
    objectref(configuration, _pack("u32", 1))
    definition(EXT_OBJECT_CLASS, b"")
    handle = definition(STRING_HANDLE_CLASS, encode_string(""))
    classref(handle, _string_handle_body(params))
    obj_list = definition(OBJECT_LIST_CLASS, _stamp_list(params.feature_stamps))
    classref(obj_list, _table(OBJECT_LIST_TAIL))
    return Model(
        header=encode_class_definition(ROOT_CLASS, CLASS_SCHEMA),
        base=MAP_BASE,
        nodes=nodes,
    )


def atom_ids_for(feature_count: int) -> tuple[int, ...]:
    if feature_count < 1:
        raise SldprtFormatError("a SOLIDWORKS part carries at least one solid feature")
    return tuple(FIRST_ATOM_ID + index for index in range(feature_count))


def tree_ids_for(feature_count: int) -> tuple[int, ...]:
    if feature_count < 1:
        raise SldprtFormatError("a SOLIDWORKS part carries at least one solid feature")
    return tuple(FIRST_TREE_ID + TREE_ID_STEP * index for index in range(feature_count))


def encode_cmgr_stream(
    *,
    feature_tree_ids: tuple[int, ...] = DEFAULT_FEATURE_TREE_IDS,
    configuration_name: str = DEFAULT_CONFIGURATION_NAME,
    part_name: str = DEFAULT_PART_NAME,
    name_stamp: int = 0,
    atom_ids: tuple[int, ...] | None = None,
    link_atom_ids: tuple[int, ...] | None = None,
    link_tree_ids: tuple[int, ...] | None = None,
    reverse_atom_ids: tuple[int, ...] | None = None,
    feature_stamps: tuple[FeatureStamp, ...] | None = None,
    document_stamp: Stamp = DOCUMENT_STAMP,
    display_stamp: Stamp | None = None,
    view_stamp: Stamp | None = None,
    max_tree_id: int | None = None,
    next_id_a: int = 0,
    next_id_b: int = 0,
    render_style: int = DEFAULT_RENDER_STYLE,
    atom_head_count: int | None = None,
    chord_ratio: float = DISPLAY_CHORD_RATIO,
    session_counter: int = SESSION_COUNTER,
    generation: int = DOCUMENT_GENERATION,
    build: int = DOCUMENT_BUILD,
    display_geometry_cache: bytes = DISPLAY_GEOMETRY_CACHE_DEFAULT,
) -> bytes:
    trees = tuple(feature_tree_ids)
    if not trees:
        raise SldprtFormatError(
            "Contents/CMgr needs at least one solid feature tree id"
        )
    resolved_atoms = tuple(atom_ids) if atom_ids else atom_ids_for(len(trees))
    resolved_chain = (
        tuple(link_atom_ids) if link_atom_ids is not None else resolved_atoms
    )
    resolved_trees = tuple(link_tree_ids) if link_tree_ids is not None else trees
    resolved_reverse = (
        tuple(reverse_atom_ids)
        if reverse_atom_ids is not None
        else tuple(reversed(resolved_atoms))
    )
    resolved_stamps = (
        tuple(feature_stamps)
        if feature_stamps is not None
        else tuple(
            FeatureStamp(
                tree_id=tree_id,
                stamp=Stamp(document_stamp.high, document_stamp.low + index),
            )
            for index, tree_id in enumerate(trees)
        )
    )
    params = CMgrParameters(
        configuration_name=configuration_name,
        part_name=part_name,
        name_stamp=name_stamp,
        atom_ids=resolved_atoms,
        link_atom_ids=resolved_chain,
        link_tree_ids=resolved_trees,
        reverse_atom_ids=resolved_reverse,
        feature_stamps=resolved_stamps,
        display_stamp=document_stamp if display_stamp is None else display_stamp,
        view_stamp=document_stamp if view_stamp is None else view_stamp,
        max_tree_id=max(trees) if max_tree_id is None else max_tree_id,
        next_id_a=next_id_a,
        next_id_b=next_id_b,
        render_style=render_style,
        atom_head_count=(
            len(resolved_atoms) if atom_head_count is None else atom_head_count
        ),
        chord_ratio=chord_ratio,
        generation=generation,
        build=build,
        session_counter=session_counter,
        display_geometry_cache=bytes(display_geometry_cache),
    )
    return build_model(params).emit()


def declared_opaque_split(**kwargs: object) -> dict[str, int]:
    stream = encode_cmgr_stream(**kwargs)
    opaque = sum(length for _, _, length in RESIDUAL_SPANS)
    return {
        "stream_bytes": len(stream),
        "declared": len(stream) - opaque,
        "opaque": opaque,
        "accounted": len(stream),
        "residual_spans": len(RESIDUAL_SPANS),
    }
