# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import math
import re
import struct
from typing import Iterable, Mapping, Sequence
import zlib

from interchange import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
    CircleCurve,
    ConeSurface,
    CylinderSurface,
    EllipseCurve,
    IntersectionCurve,
    LineCurve,
    NativeCurve,
    NativeSurface,
    NurbsCurve,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
    Transform,
    Vector3,
    frozen_mapping,
)

_WRAPPER_MAGIC = bytes.fromhex("231dd571da8148a2a85898b21b89ef99")
_SOLIDWORKS_RECTANGLE_PARTITION_SHA256 = (
    "56df5b4e4ccac3158b60ea75dd57959b991660d6d9c7bc05cbff795e56f44439"
)
_SOLIDWORKS_RECTANGLE_PRIMARY_SHA256 = (
    "472872dbe3f562c633ad1bc33a52bd78f10cc3c264f987bbc090e5794309bcca"
)
_SOLIDWORKS_RECTANGLE_DELTAS_SHA256 = (
    "17e7adf822244b6d3f17e7fa5fd891d74e2230d9aad265a0f86b30d8eee3506a"
)
_SOLIDWORKS_RECTANGLE_SCHEMA = "SCH_3601228_36001_13006"
_SOLIDWORKS_RECTANGLE_SOURCE_BOUNDS = (-20.0, -10.0, 20.0, 10.0, 10.0)
_ENTITY_MAGIC = bytes.fromhex("c2bc928f996e0000")
_INLINE_TERM_TAIL = bytes.fromhex("000000010163435a")
_INLINE_UV_TAIL = bytes.fromhex("00000002016601")
_MISSING_PARAMETER = -31_415_800_000_000.0
_LENGTH_SCALE = 0.001
_SOLID_SCHEMA = "SCH_SW_33103_11000"
_SHEET_SCHEMA = "SCH_SW_32001_11000"
_PARASOLID_V12_SCHEMA = "SCH_1200000_12006"
_PARASOLID_V12_PARTITION_DESCRIPTION = (
    b": TRANSMIT FILE (partition) created by modeller version 1200000"
)
_PARASOLID_V12_PART_DESCRIPTION = b": TRANSMIT FILE created by modeller version 1200000"
_SOLIDWORKS_2025_SCHEMA = "SCH_3601228_36001_13006"
_BLANK_PARTITION_BODY = bytes.fromhex(
    "00e7000000000065134343434343434349046d65736803ee00014908706f6c79"
    "6c696e6503f0000149076c61747469636500de00014343490b6174746465665f"
    "6c697374004a000143434110696e6465785f6d61705f6f666673657400000001"
    "01644109696e6465785f6d6170005200014114736368656d615f656d62656464"
    "696e675f6d61700052000141106d6573685f6f66667365745f6461746100ce00"
    "015a000200010001000100010001000100010001000100010100010001000000"
    "03000000030000000000010001000100010001"
)
_BLANK_DELTAS_BODY = bytes.fromhex(
    "00e7000000000003ff00030004000000030004ff000400050001000100010000"
    "000000000000000000000000000e000000000300010001000100000001006513"
    "4343434343434349046d65736803ee00014908706f6c796c696e6503f0000149"
    "076c61747469636500de00014343490b6174746465665f6c697374004a000143"
    "434110696e6465785f6d61705f6f66667365740000000101644109696e646578"
    "5f6d6170005200014114736368656d615f656d62656464696e675f6d61700052"
    "000141106d6573685f6f66667365745f6461746100ce00015a00020001010001"
    "0100010100010100010100010100010100010100010100010100000101000101"
    "0000000000000000000000000001010001010001010001000100040005000100"
    "040001000100000000000000000000000000000000000000000100010001"
)


class ParasolidFormatError(ValueError):
    __slots__ = ()


class ParasolidWriteError(ValueError):
    __slots__ = ()


def contains_parasolid_payload(data: bytes | bytearray) -> bool:
    source = bytes(data)
    return source.startswith(b"PS\x00\x00") or _WRAPPER_MAGIC in source


def is_native_parasolid_payload(data: bytes | bytearray) -> bool:
    source = bytes(data)
    if not source.startswith(b"PS\x00\x00") or len(source) < 32:
        return False
    match = re.search(rb"SCH_[0-9A-Z_]+", source[:8192])
    return match is not None and len(source) >= match.end() + 8


def encode_brep_model(
    model: BrepModel,
    *,
    partition: bool = True,
    solidworks_feature_ids: Mapping[str, int] | None = None,
) -> bytes:
    design_body_ids = frozenset(
        body.design_body_id for body in model.bodies if body.design_body_id
    )
    errors = model.validate(design_body_ids)
    if errors:
        raise ParasolidWriteError(errors[0])
    if any(body.transform != Transform() for body in model.bodies):
        raise ParasolidWriteError(
            "Parasolid B-rep writing requires identity body transforms"
        )
    feature_ids = dict(solidworks_feature_ids or {})
    if feature_ids:
        if partition:
            raise ParasolidWriteError(
                "SOLIDWORKS body attributes require a body-root Parasolid stream"
            )
        body_ids = frozenset(body.id for body in model.bodies)
        if frozenset(feature_ids) != body_ids:
            raise ParasolidWriteError(
                "SOLIDWORKS feature ids must cover every Parasolid body"
            )
        if any(
            type(value) is not int or not 0 < value < 1 << 31
            for value in feature_ids.values()
        ):
            raise ParasolidWriteError(
                "SOLIDWORKS feature ids must be positive i32 values"
            )
    _validate_brep_write_support(model)
    topology = _BrepTopology(model)
    body, _ = _encode_brep_body(
        model,
        topology,
        partition=partition,
        solidworks_feature_ids=feature_ids,
    )
    payload = _parasolid_stream(
        body,
        _PARASOLID_V12_SCHEMA,
        (
            _PARASOLID_V12_PARTITION_DESCRIPTION
            if partition
            else _PARASOLID_V12_PART_DESCRIPTION
        ),
        user_field_size=0,
    )
    _verify_encoded_brep(model, payload)
    return payload


def encode_partition_stream(data: bytes | bytearray) -> bytes:
    payload = bytes(data)
    if not payload.startswith(b"PS\x00\x00"):
        raise ParasolidWriteError("Parasolid partition data must start with PS\\0\\0")
    compressed = zlib.compress(payload, level=1)
    if len(payload) > 0xFFFFFFFF or len(compressed) + 32 > 0xFFFFFFFF:
        raise ParasolidWriteError("Parasolid partition data is too large")
    return b"".join(
        (
            struct.pack("<I", len(compressed) + 32),
            _WRAPPER_MAGIC,
            struct.pack("<II", len(payload), len(compressed)),
            compressed,
            bytes(8),
        )
    )


def encode_blank_partition_stream() -> bytes:
    payloads = (
        _parasolid_stream(
            _BLANK_PARTITION_BODY,
            _SOLIDWORKS_2025_SCHEMA,
            b": TRANSMIT FILE (partition) created by modeller version 3601228",
        ),
        _parasolid_stream(
            _BLANK_DELTAS_BODY,
            _SOLIDWORKS_2025_SCHEMA,
            b": TRANSMIT FILE (deltas) created by modeller version 3601228",
        ),
    )
    return b"".join(encode_partition_stream(payload) for payload in payloads)


def _validate_brep_write_support(model: BrepModel) -> None:
    if model.pcurves or any(coedge.pcurve_id for coedge in model.coedges):
        raise ParasolidWriteError("Parasolid B-rep writing does not support pcurves")
    if model.wires or any(body.wire_ids for body in model.bodies):
        raise ParasolidWriteError(
            "Parasolid B-rep writing does not support wire bodies"
        )
    if any(body.vertex_ids for body in model.bodies):
        raise ParasolidWriteError(
            "Parasolid B-rep writing does not support standalone vertex bodies"
        )
    if any(edge.degenerate for edge in model.edges):
        raise ParasolidWriteError(
            "Parasolid B-rep writing does not support degenerate edges"
        )
    if any(
        item.tolerance != 0.0
        for values in (model.vertices, model.edges, model.faces)
        for item in values
    ):
        raise ParasolidWriteError(
            "Parasolid B-rep writing does not support explicit topology tolerances"
        )
    loops = {loop.id: loop for loop in model.loops}
    for face in model.faces:
        outer = tuple(loops[loop_id].outer for loop_id in face.loop_ids)
        if outer != (True, *(False for _ in face.loop_ids[1:])):
            raise ParasolidWriteError(
                f"Parasolid B-rep face {face.id} requires its first loop to be the only outer loop"
            )
    shells = {shell.id: shell for shell in model.shells}
    shell_uses = {shell_use.id: shell_use for shell_use in model.shell_uses}
    for region in model.regions:
        for shell_use_id in region.shell_use_ids:
            shell = shells[shell_uses[shell_use_id].shell_id]
            if shell.closed != region.solid:
                raise ParasolidWriteError(
                    f"Parasolid B-rep shell {shell.id} closure contradicts region {region.id}"
                )


def _verify_encoded_brep(model: BrepModel, payload: bytes) -> None:
    decoded = decode_brep_model(payload)
    if decoded is None:
        raise ParasolidWriteError("generated Parasolid B-rep cannot be decoded")
    errors = decoded.validate()
    if errors:
        raise ParasolidWriteError(errors[0])
    collections = (
        "curves",
        "surfaces",
        "vertices",
        "edges",
        "coedges",
        "loops",
        "faces",
        "face_uses",
        "shells",
        "shell_uses",
        "regions",
        "bodies",
    )
    if any(
        len(getattr(model, name)) != len(getattr(decoded, name)) for name in collections
    ):
        raise ParasolidWriteError("generated Parasolid B-rep changes topology counts")
    if any(
        tuple(type(item) for item in getattr(model, name))
        != tuple(type(item) for item in getattr(decoded, name))
        for name in ("curves", "surfaces")
    ):
        raise ParasolidWriteError("generated Parasolid B-rep changes geometry classes")
    if tuple(region.solid for region in model.regions) != tuple(
        region.solid for region in decoded.regions
    ):
        raise ParasolidWriteError("generated Parasolid B-rep changes region solidity")
    if tuple(loop.outer for loop in model.loops) != tuple(
        loop.outer for loop in decoded.loops
    ):
        raise ParasolidWriteError("generated Parasolid B-rep changes loop roles")
    if any(
        _distance(source.point, restored.point) > 1e-9
        for source, restored in zip(model.vertices, decoded.vertices)
    ):
        raise ParasolidWriteError("generated Parasolid B-rep changes vertex geometry")


class _BrepTopology:
    __slots__ = (
        "bodies",
        "coedge_loop",
        "coedges",
        "edge_coedges",
        "edges",
        "face_face_use",
        "face_uses",
        "faces",
        "loop_face",
        "loops",
        "region_body",
        "regions",
        "shell_face_use",
        "shell_shell_use",
        "shell_use_region",
        "shell_uses",
        "shells",
        "surface_by_id",
        "curve_by_id",
        "vertex_by_id",
    )

    def __init__(self, model: BrepModel) -> None:
        self.curve_by_id = {item.id: item for item in model.curves}
        self.surface_by_id = {item.id: item for item in model.surfaces}
        self.vertex_by_id = {item.id: item for item in model.vertices}
        self.edges = {item.id: item for item in model.edges}
        self.coedges = {item.id: item for item in model.coedges}
        self.loops = {item.id: item for item in model.loops}
        self.faces = {item.id: item for item in model.faces}
        self.face_uses = {item.id: item for item in model.face_uses}
        self.shells = {item.id: item for item in model.shells}
        self.shell_uses = {item.id: item for item in model.shell_uses}
        self.regions = {item.id: item for item in model.regions}
        self.bodies = {item.id: item for item in model.bodies}
        self.coedge_loop: dict[str, str] = {}
        self.loop_face: dict[str, str] = {}
        self.face_face_use: dict[str, str] = {}
        self.shell_face_use: dict[str, str] = {}
        self.shell_shell_use: dict[str, str] = {}
        self.shell_use_region: dict[str, str] = {}
        self.region_body: dict[str, str] = {}
        self.edge_coedges: dict[str, list[str]] = {item.id: [] for item in model.edges}
        for loop in model.loops:
            for coedge_id in loop.coedge_ids:
                _bind(self.coedge_loop, coedge_id, loop.id, "coedge", "loop")
        for face in model.faces:
            for loop_id in face.loop_ids:
                _bind(self.loop_face, loop_id, face.id, "loop", "face")
        for shell in model.shells:
            for face_use_id in shell.face_use_ids:
                _bind(
                    self.shell_face_use,
                    face_use_id,
                    shell.id,
                    "face use",
                    "shell",
                )
                face_use = self.face_uses[face_use_id]
                _bind(
                    self.face_face_use,
                    face_use.face_id,
                    face_use.id,
                    "face",
                    "face use",
                )
        for region in model.regions:
            for shell_use_id in region.shell_use_ids:
                _bind(
                    self.shell_use_region,
                    shell_use_id,
                    region.id,
                    "shell use",
                    "region",
                )
                shell_use = self.shell_uses[shell_use_id]
                _bind(
                    self.shell_shell_use,
                    shell_use.shell_id,
                    shell_use.id,
                    "shell",
                    "shell use",
                )
        for body in model.bodies:
            for region_id in body.region_ids:
                _bind(self.region_body, region_id, body.id, "region", "body")
        for coedge in model.coedges:
            self.edge_coedges[coedge.edge_id].append(coedge.id)
        _require_complete(self.coedge_loop, self.coedges, "coedge", "loop")
        _require_complete(self.loop_face, self.loops, "loop", "face")
        _require_complete(self.face_face_use, self.faces, "face", "face use")
        _require_complete(
            self.shell_face_use,
            self.face_uses,
            "face use",
            "shell",
        )
        _require_complete(
            self.shell_use_region,
            self.shell_uses,
            "shell use",
            "region",
        )
        _require_complete(
            self.shell_shell_use,
            self.shells,
            "shell",
            "shell use",
        )
        _require_complete(self.region_body, self.regions, "region", "body")
        for edge_id, coedge_ids in self.edge_coedges.items():
            if not coedge_ids:
                raise ParasolidWriteError(f"B-rep edge {edge_id} has no coedge usage")
            if len(coedge_ids) > 2:
                raise ParasolidWriteError(
                    f"B-rep edge {edge_id} has non-manifold coedge usage"
                )

    def face_forward(self, face_id: str) -> bool:
        face = self.faces[face_id]
        face_use = self.face_uses[self.face_face_use[face_id]]
        shell = self.shells[self.shell_face_use[face_use.id]]
        shell_use = self.shell_uses[self.shell_shell_use[shell.id]]
        return face.same_sense ^ face_use.reversed ^ shell_use.reversed


def _bind(
    owners: dict[str, str],
    item_id: str,
    owner_id: str,
    item_name: str,
    owner_name: str,
) -> None:
    if item_id in owners:
        raise ParasolidWriteError(
            f"B-rep {item_name} {item_id} belongs to multiple {owner_name} values"
        )
    owners[item_id] = owner_id


def _require_complete(
    owners: Mapping[str, str],
    values: Mapping[str, object],
    item_name: str,
    owner_name: str,
) -> None:
    missing = next((item_id for item_id in values if item_id not in owners), None)
    if missing is not None:
        raise ParasolidWriteError(
            f"B-rep {item_name} {missing} has no {owner_name} usage"
        )


def _ordered_ids(
    values: Sequence[str],
    entities: Mapping[str, object],
    attribute_name: str,
) -> list[str]:
    ranks = [
        getattr(entities[value], "attributes", {}).get(attribute_name)
        for value in values
    ]
    if all(type(rank) is int and rank >= 0 for rank in ranks) and len(
        set(ranks)
    ) == len(ranks):
        return [
            value
            for _, value in sorted(
                zip(ranks, values),
                key=lambda item: item[0],
            )
        ]
    return list(values)


def _fin_index(
    descriptor: object,
    coedges: Mapping[str, int],
    dummy_fins: Mapping[str, int],
) -> int | None:
    if (
        not isinstance(descriptor, (tuple, list))
        or len(descriptor) != 2
        or not all(isinstance(value, str) for value in descriptor)
    ):
        return None
    kind, identifier = descriptor
    if kind == "coedge":
        return coedges.get(identifier)
    if kind == "dummy":
        return dummy_fins.get(identifier)
    return None


def _encode_brep_body(
    model: BrepModel,
    topology: _BrepTopology,
    *,
    partition: bool = True,
    solidworks_feature_ids: Mapping[str, int] | None = None,
) -> tuple[bytes, bool]:
    feature_ids = dict(solidworks_feature_ids or {})
    attribute_bases = (
        {body.id: position * 100 for position, body in enumerate(model.bodies)}
        if feature_ids
        else {}
    )
    solidworks_triangle = bool(feature_ids) and (
        len(model.bodies) == 1
        and len(model.regions) == 1
        and len(model.shells) == 1
        and len(model.surfaces) == 1
        and len(model.curves) == 3
        and len(model.vertices) == 3
        and len(model.edges) == 3
        and len(model.coedges) == 3
        and len(model.loops) == 1
        and len(model.faces) == 1
        and not model.regions[0].solid
        and isinstance(model.surfaces[0], PlaneSurface)
        and all(isinstance(curve, LineCurve) for curve in model.curves)
        and all(len(topology.edge_coedges[edge.id]) == 1 for edge in model.edges)
    )
    solidworks_solid = (
        bool(feature_ids)
        and len(model.bodies) == 1
        and all(region.solid for region in model.regions)
    )
    reserved_indices = {
        base + offset
        for base in attribute_bases.values()
        for offset in (*range(2, 5), *range(12, 16), *range(32, 60))
    }
    reserved_topology_indices = set(range(5, 12)) if feature_ids else set()
    used_indices: set[int] = set()
    next_index = 2 if partition else 1

    def allocate_index(preferred: int = 0) -> int:
        nonlocal next_index
        if (
            preferred
            and preferred not in reserved_indices
            and preferred not in used_indices
        ):
            used_indices.add(preferred)
            return preferred
        while (
            next_index in reserved_indices
            or next_index in reserved_topology_indices
            or next_index in used_indices
        ):
            next_index += 1
        result = next_index
        used_indices.add(result)
        next_index += 1
        return result

    def allocate(
        values: Iterable[object],
        preferred: Sequence[int] = (),
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        for position, value in enumerate(values):
            item_id = getattr(value, "id")
            result[item_id] = allocate_index(
                preferred[position] if position < len(preferred) else 0
            )
        return result

    bodies = (
        {body.id: attribute_bases[body.id] + 1 for body in model.bodies}
        if attribute_bases
        else allocate(model.bodies)
    )
    used_indices.update(bodies.values())
    regions = allocate(
        model.regions,
        (17,) if solidworks_solid else (9,) if feature_ids else (),
    )
    shells = allocate(model.shells, (5,) if feature_ids else ())
    surfaces = allocate(model.surfaces, (6,) if feature_ids else ())
    curves = allocate(
        model.curves,
        (7, 17, 31) if solidworks_triangle else (7,) if feature_ids else (),
    )
    points = allocate(
        model.vertices,
        (8, 18, 29) if solidworks_triangle else (8,) if feature_ids else (),
    )
    vertices = allocate(
        model.vertices,
        (11, 21, 27) if solidworks_triangle else (11,) if feature_ids else (),
    )
    edges = allocate(
        model.edges,
        (10, 20, 30) if solidworks_triangle else (10,) if feature_ids else (),
    )
    coedges = allocate(model.coedges, (19, 23, 24) if solidworks_triangle else ())
    dummy_edges = tuple(
        edge for edge in model.edges if len(topology.edge_coedges[edge.id]) == 1
    )
    dummy_fins = allocate(dummy_edges, (25, 28, 26) if solidworks_triangle else ())
    loops = allocate(model.loops, (22,) if solidworks_triangle else ())
    faces = allocate(model.faces, (16,) if solidworks_triangle else ())
    exterior_regions: dict[str, int] = {}
    exterior_shells: dict[str, int] = {}
    sheet = False
    for body in model.bodies:
        kinds = {topology.regions[region_id].solid for region_id in body.region_ids}
        if len(kinds) != 1:
            raise ParasolidWriteError(
                f"B-rep body {body.id} mixes solid and sheet regions"
            )
        if kinds == {False}:
            sheet = True
            continue
        exterior_regions[body.id] = allocate_index(9 if solidworks_solid else 0)
        for region_id in body.region_ids:
            region = topology.regions[region_id]
            for shell_use_id in region.shell_use_ids:
                shell_id = topology.shell_uses[shell_use_id].shell_id
                exterior_shells[shell_id] = allocate_index()
    solidworks_face_attributes: dict[str, tuple[int, int, int]] = {}
    solidworks_face_values: dict[str, tuple[int, int, int]] = {}
    solidworks_face_definitions: dict[str, int] = {}
    solidworks_face_definition_next: dict[str, int] = {}
    solidworks_face_identifiers: dict[str, int] = {}
    solidworks_body_attributes: dict[str, int] = {}
    solidworks_body_values: dict[str, int] = {}
    solidworks_body_definitions: dict[str, int] = {}
    solidworks_body_definition_next: dict[str, int] = {}
    solidworks_body_identifiers: dict[str, int] = {}
    if solidworks_solid:
        for name in ("unchanged", "downstream", "colour"):
            solidworks_face_definitions[name] = allocate_index()
            solidworks_face_definition_next[name] = (
                0 if name == "colour" else allocate_index()
            )
            solidworks_face_identifiers[name] = allocate_index()
        for face in model.faces:
            solidworks_face_attributes[face.id] = tuple(
                allocate_index() for _ in range(3)
            )
            solidworks_face_values[face.id] = tuple(allocate_index() for _ in range(3))
        solidworks_body_attributes = {
            "timestamp": allocate_index(),
            "feature": allocate_index(),
            "implicit": allocate_index(),
            "match": allocate_index(),
            "density": allocate_index(),
            "lightweight": allocate_index(),
            "recipe": 13,
        }
        for name in (
            "timestamp",
            "feature",
            "implicit",
            "match",
            "density",
            "lightweight",
            "recipe",
        ):
            solidworks_body_definitions[name] = allocate_index()
            solidworks_body_definition_next[name] = allocate_index()
            solidworks_body_identifiers[name] = allocate_index()
        for name in (
            "timestamp",
            "feature",
            "implicit",
            "match",
            "density",
            "lightweight",
        ):
            solidworks_body_values[name] = allocate_index()
    if max((*reserved_indices, *used_indices), default=0) >= 32767:
        raise ParasolidWriteError("Parasolid V12 writer node space is exhausted")

    face_shell: dict[str, str] = {}
    face_region: dict[str, str] = {}
    face_body: dict[str, str] = {}
    shell_region: dict[str, str] = {}
    shell_body: dict[str, str] = {}
    for region in model.regions:
        body_id = topology.region_body[region.id]
        for shell_use_id in region.shell_use_ids:
            shell_use = topology.shell_uses[shell_use_id]
            shell = topology.shells[shell_use.shell_id]
            shell_region[shell.id] = region.id
            shell_body[shell.id] = body_id
            for face_use_id in shell.face_use_ids:
                face_id = topology.face_uses[face_use_id].face_id
                face_shell[face_id] = shell.id
                face_region[face_id] = region.id
                face_body[face_id] = body_id

    edge_body: dict[str, str] = {}
    vertex_body: dict[str, str] = {}
    for edge in model.edges:
        uses = topology.edge_coedges[edge.id]
        body_ids = {
            face_body[topology.loop_face[topology.coedge_loop[coedge_id]]]
            for coedge_id in uses
        }
        if len(body_ids) != 1:
            raise ParasolidWriteError(f"Parasolid edge {edge.id} spans multiple bodies")
        body_id = next(iter(body_ids))
        edge_body[edge.id] = body_id
        for vertex_id in (edge.start_vertex_id, edge.end_vertex_id):
            prior = vertex_body.setdefault(vertex_id, body_id)
            if prior != body_id:
                raise ParasolidWriteError(
                    f"Parasolid vertex {vertex_id} spans multiple bodies"
                )

    surface_faces: dict[str, list[str]] = {surface.id: [] for surface in model.surfaces}
    curve_edges: dict[str, list[str]] = {curve.id: [] for curve in model.curves}
    for face in model.faces:
        surface_faces[face.surface_id].append(face.id)
    for edge in model.edges:
        curve_edges[edge.curve_id].append(edge.id)
    for surface_id, face_ids in surface_faces.items():
        surface_faces[surface_id] = _ordered_ids(
            face_ids,
            topology.faces,
            "parasolid.surface_face_order",
        )
    for curve_id, edge_ids in curve_edges.items():
        curve_edges[curve_id] = _ordered_ids(
            edge_ids,
            topology.edges,
            "parasolid.curve_edge_order",
        )

    body_surfaces: dict[str, list[str]] = {body.id: [] for body in model.bodies}
    body_curves: dict[str, list[str]] = {body.id: [] for body in model.bodies}
    body_points: dict[str, list[str]] = {body.id: [] for body in model.bodies}
    body_vertices: dict[str, list[str]] = {body.id: [] for body in model.bodies}
    body_edges: dict[str, list[str]] = {body.id: [] for body in model.bodies}
    for surface in model.surfaces:
        owners = {face_body[face_id] for face_id in surface_faces[surface.id]}
        if len(owners) != 1:
            raise ParasolidWriteError(
                f"Parasolid surface {surface.id} spans multiple bodies"
            )
        body_surfaces[next(iter(owners))].append(surface.id)
    for curve in model.curves:
        owners = {edge_body[edge_id] for edge_id in curve_edges[curve.id]}
        if len(owners) != 1:
            raise ParasolidWriteError(
                f"Parasolid curve {curve.id} spans multiple bodies"
            )
        body_curves[next(iter(owners))].append(curve.id)
    for vertex in model.vertices:
        body_id = vertex_body.get(vertex.id)
        if body_id is None:
            raise ParasolidWriteError(
                f"Parasolid vertex {vertex.id} has no owning body"
            )
        body_points[body_id].append(vertex.id)
        body_vertices[body_id].append(vertex.id)
    for edge in model.edges:
        body_edges[edge_body[edge.id]].append(edge.id)
    for body in model.bodies:
        body_surfaces[body.id] = _ordered_ids(
            body_surfaces[body.id],
            topology.surface_by_id,
            "parasolid.surface_order",
        )
        body_curves[body.id] = _ordered_ids(
            body_curves[body.id],
            topology.curve_by_id,
            "parasolid.curve_order",
        )
        body_points[body.id] = _ordered_ids(
            body_points[body.id],
            topology.vertex_by_id,
            "parasolid.point_order",
        )
        body_vertices[body.id] = _ordered_ids(
            body_vertices[body.id],
            topology.vertex_by_id,
            "parasolid.vertex_order",
        )
        body_edges[body.id] = _ordered_ids(
            body_edges[body.id],
            topology.edges,
            "parasolid.edge_order",
        )

    node_ids: dict[int, int] = {}
    next_node_id: dict[str, int] = {body.id: 1 for body in model.bodies}

    def node_id(index: int, body_id: str) -> int:
        value = next_node_id[body_id]
        if body_id in attribute_bases and 18 <= value <= 28:
            value = 29
        next_node_id[body_id] = value + 1
        node_ids[index] = value
        return value

    for region in model.regions:
        node_id(regions[region.id], topology.region_body[region.id])
    for body_id, index in exterior_regions.items():
        node_id(index, body_id)
    for shell in model.shells:
        node_id(shells[shell.id], shell_body[shell.id])
    for shell_id, index in exterior_shells.items():
        node_id(index, shell_body[shell_id])
    for surface in model.surfaces:
        node_id(surfaces[surface.id], face_body[surface_faces[surface.id][0]])
    for curve in model.curves:
        node_id(curves[curve.id], edge_body[curve_edges[curve.id][0]])
    for vertex in model.vertices:
        node_id(points[vertex.id], vertex_body[vertex.id])
        node_id(vertices[vertex.id], vertex_body[vertex.id])
    for edge in model.edges:
        node_id(edges[edge.id], edge_body[edge.id])
    for loop in model.loops:
        node_id(loops[loop.id], face_body[topology.loop_face[loop.id]])
    for face in model.faces:
        node_id(faces[face.id], face_body[face.id])
    if solidworks_solid:
        body_id = model.bodies[0].id
        for face in model.faces:
            for index in solidworks_face_attributes[face.id]:
                node_id(index, body_id)
        for name in (
            "timestamp",
            "feature",
            "implicit",
            "match",
            "density",
            "lightweight",
            "recipe",
        ):
            node_id(solidworks_body_attributes[name], body_id)

    vertex_fins: dict[str, list[int]] = {vertex.id: [] for vertex in model.vertices}
    fin_vertex: dict[int, str] = {}
    fin_other: dict[int, int] = {}
    for edge in model.edges:
        uses = topology.edge_coedges[edge.id]
        if len(uses) == 1:
            real_index = coedges[uses[0]]
            dummy_index = dummy_fins[edge.id]
            fin_other[real_index] = dummy_index
            fin_other[dummy_index] = real_index
            real = topology.coedges[uses[0]]
            real_vertex = edge.end_vertex_id if real.reversed else edge.start_vertex_id
            dummy_vertex = edge.start_vertex_id if real.reversed else edge.end_vertex_id
            fin_vertex[real_index] = real_vertex
            fin_vertex[dummy_index] = dummy_vertex
            vertex_fins[real_vertex].append(real_index)
            vertex_fins[dummy_vertex].append(dummy_index)
        else:
            for position, coedge_id in enumerate(uses):
                index = coedges[coedge_id]
                other = coedges[uses[(position + 1) % len(uses)]]
                fin_other[index] = other
                coedge = topology.coedges[coedge_id]
                vertex_id = (
                    edge.end_vertex_id if coedge.reversed else edge.start_vertex_id
                )
                fin_vertex[index] = vertex_id
                vertex_fins[vertex_id].append(index)
    for vertex in model.vertices:
        requested = vertex.attributes.get("parasolid.vertex_fins")
        if not isinstance(requested, (tuple, list)):
            continue
        ordered = [
            _fin_index(descriptor, coedges, dummy_fins) for descriptor in requested
        ]
        if (
            all(index is not None for index in ordered)
            and len(set(ordered)) == len(ordered)
            and set(ordered) == set(vertex_fins[vertex.id])
        ):
            vertex_fins[vertex.id] = [index for index in ordered if index is not None]

    first_face_by_body: dict[str, str] = {}
    for face in model.faces:
        first_face_by_body.setdefault(face_body[face.id], face.id)

    output = bytearray()
    if partition:
        _v12_node(output, 101, 1)
        for value in (
            0,
            0,
            bodies[model.bodies[0].id] if model.bodies else 0,
            0,
            0,
            0,
            0,
        ):
            _v12_pointer(output, value)
        output.append(1)
        _v12_pointer(output, 0)
        _i32(output, 0)
        _i32(output, 0)

    for position, body in enumerate(model.bodies):
        body_index = bodies[body.id]
        region_values = [regions[region_id] for region_id in body.region_ids]
        solid = all(topology.regions[region_id].solid for region_id in body.region_ids)
        if solid:
            region_values.insert(0, exterior_regions[body.id])
        body_shells = [
            shell_id for shell_id, owner in shell_body.items() if owner == body.id
        ]
        attribute_base = attribute_bases.get(body.id)
        highest_node_id = max(
            next_node_id[body.id] - 1,
            28 if attribute_base is not None else 0,
        )
        _v12_node(output, 12, body_index)
        _i32(output, highest_node_id)
        for value in (
            attribute_base + 2 if attribute_base is not None else 0,
            attribute_base + 3 if attribute_base is not None else 0,
            0,
            0,
            0,
            0,
        ):
            _v12_pointer(output, value)
        _bef64(
            output,
            math.nextafter(1000.0, math.inf) if solidworks_solid else 1000.0,
        )
        _bef64(output, 1e-8)
        for value in (
            0,
            (
                bodies[model.bodies[position + 1].id]
                if position + 1 < len(model.bodies)
                else (
                    attribute_base + 4
                    if len(model.bodies) == 1 and attribute_base is not None
                    else 0
                )
            ),
            bodies[model.bodies[position - 1].id] if position else 0,
        ):
            _v12_pointer(output, value)
        output.append(1)
        _v12_pointer(output, 1 if partition else 0)
        output.append(1 if solid else 3)
        output.append(1)
        _v12_pointer(output, shells[body_shells[0]] if body_shells else 0)
        _v12_pointer(
            output,
            surfaces[body_surfaces[body.id][0]] if body_surfaces[body.id] else 0,
        )
        _v12_pointer(
            output,
            curves[body_curves[body.id][0]] if body_curves[body.id] else 0,
        )
        _v12_pointer(
            output,
            points[body_points[body.id][0]] if body_points[body.id] else 0,
        )
        _v12_pointer(output, region_values[0] if region_values else 0)
        _v12_pointer(
            output,
            edges[body_edges[body.id][0]] if body_edges[body.id] else 0,
        )
        _v12_pointer(
            output,
            vertices[body_vertices[body.id][0]] if body_vertices[body.id] else 0,
        )
        if attribute_base is not None:
            _write_solidworks_body_attribute_prefix(
                output,
                attribute_base,
                body_index,
                11 if solidworks_solid else 7,
            )

    for body in model.bodies:
        region_values = list(body.region_ids)
        solid = all(topology.regions[region_id].solid for region_id in body.region_ids)
        if solid:
            exterior_index = exterior_regions[body.id]
            _v12_node(output, 19, exterior_index)
            _i32(output, node_ids[exterior_index])
            _v12_pointer(output, 0)
            _v12_pointer(output, bodies[body.id])
            _v12_pointer(output, regions[region_values[0]] if region_values else 0)
            _v12_pointer(output, 0)
            exterior = [
                exterior_shells[shell_id]
                for shell_id, owner in shell_body.items()
                if owner == body.id and shell_id in exterior_shells
            ]
            _v12_pointer(output, exterior[0] if exterior else 0)
            output.extend(b"V")
        for position, region_id in enumerate(region_values):
            region = topology.regions[region_id]
            region_index = regions[region_id]
            shell_ids = [
                topology.shell_uses[shell_use_id].shell_id
                for shell_use_id in region.shell_use_ids
            ]
            _v12_node(output, 19, region_index)
            _i32(output, node_ids[region_index])
            _v12_pointer(output, 0)
            _v12_pointer(output, bodies[body.id])
            _v12_pointer(
                output,
                (
                    regions[region_values[position + 1]]
                    if position + 1 < len(region_values)
                    else 0
                ),
            )
            _v12_pointer(
                output,
                (
                    exterior_regions[body.id]
                    if solid and position == 0
                    else regions[region_values[position - 1]] if position else 0
                ),
            )
            _v12_pointer(output, shells[shell_ids[0]] if shell_ids else 0)
            output.extend(b"S" if region.solid else b"V")

    for shell in model.shells:
        shell_index = shells[shell.id]
        region_id = shell_region[shell.id]
        region = topology.regions[region_id]
        body_id = shell_body[shell.id]
        shell_ids = [
            topology.shell_uses[shell_use_id].shell_id
            for shell_use_id in region.shell_use_ids
        ]
        position = shell_ids.index(shell.id)
        face_ids = _ordered_ids(
            [
                topology.face_uses[face_use_id].face_id
                for face_use_id in shell.face_use_ids
            ],
            topology.faces,
            "parasolid.face_order",
        )
        _v12_node(output, 13, shell_index)
        _i32(output, node_ids[shell_index])
        _v12_pointer(output, 0)
        _v12_pointer(output, bodies[body_id])
        _v12_pointer(
            output,
            shells[shell_ids[position + 1]] if position + 1 < len(shell_ids) else 0,
        )
        _v12_pointer(output, faces[face_ids[0]] if face_ids else 0)
        _v12_pointer(output, 0)
        _v12_pointer(output, 0)
        _v12_pointer(output, regions[region_id])
        _v12_pointer(output, 0)
        if shell.id in exterior_shells:
            exterior_index = exterior_shells[shell.id]
            exterior_ids = [
                shell_id
                for shell_id, owner in shell_body.items()
                if owner == body_id and shell_id in exterior_shells
            ]
            exterior_position = exterior_ids.index(shell.id)
            _v12_node(output, 13, exterior_index)
            _i32(output, node_ids[exterior_index])
            _v12_pointer(output, 0)
            _v12_pointer(output, 0)
            _v12_pointer(
                output,
                (
                    exterior_shells[exterior_ids[exterior_position + 1]]
                    if exterior_position + 1 < len(exterior_ids)
                    else 0
                ),
            )
            _v12_pointer(output, 0)
            _v12_pointer(output, 0)
            _v12_pointer(output, 0)
            _v12_pointer(output, exterior_regions[body_id])
            _v12_pointer(output, faces[face_ids[0]] if face_ids else 0)

    for surface in model.surfaces:
        if isinstance(surface, NurbsSurface):
            raise ParasolidWriteError(
                f"Parasolid V12 writer does not support NURBS surface {surface.id}"
            )
        kind, values = _surface_values(surface)
        face_ids = surface_faces[surface.id]
        body_id = face_body[face_ids[0]]
        chain = body_surfaces[body_id]
        position = chain.index(surface.id)
        _v12_geometry_node(
            output,
            kind,
            surfaces[surface.id],
            node_ids[surfaces[surface.id]],
            faces[face_ids[0]],
            surfaces[chain[position + 1]] if position + 1 < len(chain) else 0,
            surfaces[chain[position - 1]] if position else 0,
            values,
        )
    for curve in model.curves:
        if isinstance(curve, NurbsCurve):
            raise ParasolidWriteError(
                f"Parasolid V12 writer does not support NURBS curve {curve.id}"
            )
        kind, values = _curve_values(curve)
        edge_ids = curve_edges[curve.id]
        body_id = edge_body[edge_ids[0]]
        chain = body_curves[body_id]
        position = chain.index(curve.id)
        _v12_geometry_node(
            output,
            kind,
            curves[curve.id],
            node_ids[curves[curve.id]],
            edges[edge_ids[0]],
            curves[chain[position + 1]] if position + 1 < len(chain) else 0,
            curves[chain[position - 1]] if position else 0,
            values,
        )
    for vertex in model.vertices:
        body_id = vertex_body[vertex.id]
        chain = body_points[body_id]
        position = chain.index(vertex.id)
        _v12_node(output, 29, points[vertex.id])
        _i32(output, node_ids[points[vertex.id]])
        _v12_pointer(output, 0)
        _v12_pointer(output, vertices[vertex.id])
        _v12_pointer(
            output,
            points[chain[position + 1]] if position + 1 < len(chain) else 0,
        )
        _v12_pointer(output, points[chain[position - 1]] if position else 0)
        _vector(output, vertex.point, _LENGTH_SCALE)
    for vertex in model.vertices:
        body_id = vertex_body[vertex.id]
        chain = body_vertices[body_id]
        position = chain.index(vertex.id)
        fins = vertex_fins[vertex.id]
        _v12_node(output, 18, vertices[vertex.id])
        _i32(output, node_ids[vertices[vertex.id]])
        _v12_pointer(output, 0)
        _v12_pointer(output, fins[0] if fins else 0)
        _v12_pointer(output, vertices[chain[position - 1]] if position else 0)
        _v12_pointer(
            output,
            vertices[chain[position + 1]] if position + 1 < len(chain) else 0,
        )
        _v12_pointer(output, points[vertex.id])
        _bef64(output, _MISSING_PARAMETER)
        _v12_pointer(output, bodies[body_id])
    for edge in model.edges:
        body_id = edge_body[edge.id]
        chain = body_edges[body_id]
        position = chain.index(edge.id)
        curve_chain = curve_edges[edge.curve_id]
        curve_position = curve_chain.index(edge.id)
        first_fin = _fin_index(
            edge.attributes.get("parasolid.first_fin"),
            coedges,
            dummy_fins,
        )
        if first_fin is None:
            first_fin = coedges[topology.edge_coedges[edge.id][0]]
        _v12_node(output, 16, edges[edge.id])
        _i32(output, node_ids[edges[edge.id]])
        _v12_pointer(output, 0)
        _bef64(output, _MISSING_PARAMETER)
        _v12_pointer(output, first_fin)
        _v12_pointer(output, edges[chain[position - 1]] if position else 0)
        _v12_pointer(
            output,
            edges[chain[position + 1]] if position + 1 < len(chain) else 0,
        )
        _v12_pointer(output, curves[edge.curve_id])
        _v12_pointer(
            output,
            (
                edges[curve_chain[curve_position + 1]]
                if curve_position + 1 < len(curve_chain)
                else 0
            ),
        )
        _v12_pointer(
            output,
            edges[curve_chain[curve_position - 1]] if curve_position else 0,
        )
        _v12_pointer(output, bodies[body_id])
    for coedge in model.coedges:
        loop = topology.loops[topology.coedge_loop[coedge.id]]
        face = topology.faces[topology.loop_face[loop.id]]
        region = topology.regions[face_region[face.id]]
        position = loop.coedge_ids.index(coedge.id)
        previous_id = loop.coedge_ids[position - 1]
        next_id = loop.coedge_ids[(position + 1) % len(loop.coedge_ids)]
        fin_index = coedges[coedge.id]
        _v12_fin(
            output,
            fin_index,
            0,
            loops[loop.id],
            coedges[previous_id] if region.solid else coedges[next_id],
            coedges[next_id] if region.solid else coedges[previous_id],
            vertices[fin_vertex[fin_index]],
            fin_other[fin_index],
            edges[coedge.edge_id],
            0,
            _next_fin_at_vertex(fin_index, vertex_fins),
            not coedge.reversed,
        )
    for edge in dummy_edges:
        fin_index = dummy_fins[edge.id]
        real = topology.coedges[topology.edge_coedges[edge.id][0]]
        _v12_fin(
            output,
            fin_index,
            0,
            0,
            0,
            0,
            vertices[fin_vertex[fin_index]],
            fin_other[fin_index],
            edges[edge.id],
            0,
            _next_fin_at_vertex(fin_index, vertex_fins),
            real.reversed,
        )
    for loop in model.loops:
        face = topology.faces[topology.loop_face[loop.id]]
        position = face.loop_ids.index(loop.id)
        next_loop_id = (
            face.loop_ids[position + 1] if position + 1 < len(face.loop_ids) else ""
        )
        _v12_node(output, 15, loops[loop.id])
        _i32(output, node_ids[loops[loop.id]])
        for value in (
            0,
            coedges[loop.coedge_ids[0]],
            faces[face.id],
            loops.get(next_loop_id, 0),
        ):
            _v12_pointer(output, value)
    for face in model.faces:
        shell = topology.shells[face_shell[face.id]]
        face_ids = _ordered_ids(
            [
                topology.face_uses[face_use_id].face_id
                for face_use_id in shell.face_use_ids
            ],
            topology.faces,
            "parasolid.face_order",
        )
        position = face_ids.index(face.id)
        front_face_ids = _ordered_ids(
            face_ids,
            topology.faces,
            "parasolid.front_face_order",
        )
        front_position = front_face_ids.index(face.id)
        surface_chain = surface_faces[face.surface_id]
        surface_position = surface_chain.index(face.id)
        region = topology.regions[face_region[face.id]]
        _v12_node(output, 14, faces[face.id])
        _i32(output, node_ids[faces[face.id]])
        attribute_base = attribute_bases.get(face_body[face.id])
        first_face_id = first_face_by_body.get(face_body[face.id])
        _v12_pointer(
            output,
            (
                solidworks_face_attributes[face.id][0]
                if face.id in solidworks_face_attributes
                else (
                    attribute_base + 32
                    if attribute_base is not None and face.id == first_face_id
                    else 0
                )
            ),
        )
        _bef64(output, _MISSING_PARAMETER)
        for value in (
            faces[face_ids[position + 1]] if position + 1 < len(face_ids) else 0,
            faces[face_ids[position - 1]] if position else 0,
            loops[face.loop_ids[0]],
            shells[shell.id],
            surfaces[face.surface_id],
        ):
            _v12_pointer(output, value)
        output.extend(b"+" if face.same_sense else b"-")
        _v12_pointer(
            output,
            (
                faces[surface_chain[surface_position + 1]]
                if surface_position + 1 < len(surface_chain)
                else 0
            ),
        )
        _v12_pointer(
            output,
            faces[surface_chain[surface_position - 1]] if surface_position else 0,
        )
        _v12_pointer(
            output,
            (
                faces[front_face_ids[front_position + 1]]
                if front_position + 1 < len(front_face_ids)
                else 0
            ),
        )
        _v12_pointer(
            output,
            faces[front_face_ids[front_position - 1]] if front_position else 0,
        )
        _v12_pointer(
            output,
            exterior_shells[shell.id] if region.solid else shells[shell.id],
        )
    for body in model.bodies:
        attribute_base = attribute_bases.get(body.id)
        first_face_id = first_face_by_body.get(body.id)
        if attribute_base is None or first_face_id is None:
            continue
        if solidworks_solid:
            _write_solidworks_solid_attributes(
                output,
                attribute_base,
                bodies[body.id],
                tuple(
                    (
                        face.id,
                        faces[face.id],
                        solidworks_face_attributes[face.id],
                        solidworks_face_values[face.id],
                        face.attributes.get("solidworks.unchanged_id"),
                        face.attributes,
                    )
                    for face in model.faces
                ),
                solidworks_face_definitions,
                solidworks_face_definition_next,
                solidworks_face_identifiers,
                solidworks_body_attributes,
                solidworks_body_values,
                solidworks_body_definitions,
                solidworks_body_definition_next,
                solidworks_body_identifiers,
                node_ids,
                feature_ids[body.id],
            )
            continue
        _write_solidworks_body_attribute_suffix(
            output,
            attribute_base,
            bodies[body.id],
            faces[first_face_id],
            feature_ids[body.id],
        )
    _tag(output, 1)
    _v12_pointer(output, 0)
    if solidworks_triangle:
        output = bytearray(_order_solidworks_triangle_records(bytes(output)))
    return bytes(output), sheet


def _write_solidworks_body_attribute_prefix(
    output: bytearray,
    base: int,
    body: int,
    attribute_count: int,
) -> None:
    _v12_attribute(
        output,
        base + 2,
        28,
        base + 12,
        body,
        base + 13,
        0,
        0,
        0,
        (0, base + 14),
    )
    _v12_node(output, 70, base + 3)
    _i32(output, 0)
    _v12_pointer(output, body)
    _v12_pointer(output, 0)
    _v12_pointer(output, 0)
    for value in (4, attribute_count, 20, 8):
        _i32(output, value)
    _v12_pointer(output, base + 15)
    _v12_pointer(output, base + 15)
    _i32(output, 1)
    output.append(1)


def _write_solidworks_solid_attributes(
    output: bytearray,
    base: int,
    body: int,
    faces: Sequence[
        tuple[
            str,
            int,
            tuple[int, int, int],
            tuple[int, int, int],
            object,
            Mapping[str, object],
        ]
    ],
    face_definitions: Mapping[str, int],
    face_definition_next: Mapping[str, int],
    face_identifiers: Mapping[str, int],
    body_attributes: Mapping[str, int],
    body_values: Mapping[str, int],
    body_definitions: Mapping[str, int],
    body_definition_next: Mapping[str, int],
    body_identifiers: Mapping[str, int],
    node_ids: Mapping[int, int],
    feature_id: int,
) -> None:
    standard_actions = (0, 0, 0, 0, 3, 5, 0, 0)
    retained_actions = (1, 1, 1, 1, 1, 1, 1, 1)
    face_legal = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    coloured_face_legal = (0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0)
    body_legal = (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    implicit_body_legal = (0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0)
    ordered_faces: dict[str, Sequence[tuple[object, ...]]] = {}
    neighbors: dict[tuple[str, str], tuple[int, int]] = {}
    for kind, attribute_position in (
        ("unchanged", 0),
        ("downstream", 1),
        ("colour", 2),
    ):
        values = list(faces)
        ranks = [value[5].get(f"solidworks.{kind}_order") for value in values]
        if all(type(rank) is int and rank >= 0 for rank in ranks) and len(
            set(ranks)
        ) == len(ranks):
            values.sort(key=lambda value: value[5][f"solidworks.{kind}_order"])
        ordered_faces[kind] = values
        for position, value in enumerate(values):
            previous_attribute = (
                values[position - 1][2][attribute_position] if position else 0
            )
            next_attribute = (
                values[position + 1][2][attribute_position]
                if position + 1 < len(values)
                else 0
            )
            neighbors[(value[0], kind)] = next_attribute, previous_attribute
    for face_id, owner, attributes, values, unchanged_id, _ in faces:
        unchanged, downstream, colour = attributes
        unchanged_value, downstream_value, colour_value = values
        _v12_attribute(
            output,
            unchanged,
            node_ids[unchanged],
            face_definitions["unchanged"],
            owner,
            downstream,
            0,
            neighbors[(face_id, "unchanged")][0],
            neighbors[(face_id, "unchanged")][1],
            (unchanged_value,),
        )
        _v12_attribute(
            output,
            downstream,
            node_ids[downstream],
            face_definitions["downstream"],
            owner,
            colour,
            unchanged,
            neighbors[(face_id, "downstream")][0],
            neighbors[(face_id, "downstream")][1],
            (downstream_value, 0, 0),
        )
        _v12_attribute(
            output,
            colour,
            node_ids[colour],
            face_definitions["colour"],
            owner,
            0,
            downstream,
            neighbors[(face_id, "colour")][0],
            neighbors[(face_id, "colour")][1],
            (colour_value,),
        )
        preserved_unchanged_id = (
            unchanged_id
            if type(unchanged_id) is int and 0 < unchanged_id < 1 << 31
            else zlib.crc32(face_id.encode("utf-8")) & 0x7FFFFFFF or 1
        )
        _v12_int_values(output, unchanged_value, (preserved_unchanged_id,))
        _v12_int_values(
            output,
            downstream_value,
            (0, 1671915899, 31269538, 0, 0, 0),
        )
        _v12_real_values(
            output,
            colour_value,
            (0.792156862745098, 0.8196078431372549, 0.9333333333333333),
        )
    _v12_attribute_definition(
        output,
        face_definitions["unchanged"],
        face_definition_next["unchanged"],
        face_identifiers["unchanged"],
        9000,
        retained_actions,
        coloured_face_legal,
        (1,),
    )
    _v12_attribute_identifier(
        output,
        face_identifiers["unchanged"],
        "SWEntUnchanged",
    )
    _v12_attribute_definition(
        output,
        face_definitions["downstream"],
        face_definition_next["downstream"],
        face_identifiers["downstream"],
        9000,
        standard_actions,
        face_legal,
        (1, 1, 1),
    )
    _v12_attribute_identifier(
        output,
        face_identifiers["downstream"],
        "DOWNSTREAM_FACE_ID",
    )
    _v12_attribute_definition(
        output,
        face_definitions["colour"],
        face_definition_next["colour"],
        face_identifiers["colour"],
        8001,
        standard_actions,
        coloured_face_legal,
        (2,),
    )
    _v12_attribute_identifier(
        output,
        face_identifiers["colour"],
        "SDL/TYSA_COLOUR",
    )
    first_unchanged = ordered_faces["unchanged"][0][2][0]
    first_downstream = ordered_faces["downstream"][0][2][1]
    first_colour = ordered_faces["colour"][0][2][2]
    _v12_pointer_list(
        output,
        base + 15,
        (
            first_downstream,
            body_attributes["timestamp"],
            body_attributes["feature"],
            body_attributes["implicit"],
            first_unchanged,
            body_attributes["match"],
            body_attributes["density"],
            body_attributes["lightweight"],
            body_attributes["recipe"],
            first_colour,
            base + 2,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ),
        11,
    )
    timestamp = body_attributes["timestamp"]
    feature = body_attributes["feature"]
    implicit = body_attributes["implicit"]
    match = body_attributes["match"]
    density = body_attributes["density"]
    lightweight = body_attributes["lightweight"]
    recipe = body_attributes["recipe"]
    _v12_attribute(
        output,
        timestamp,
        node_ids[timestamp],
        body_definitions["timestamp"],
        body,
        0,
        feature,
        0,
        0,
        (0, body_values["timestamp"]),
    )
    _v12_attribute(
        output,
        feature,
        node_ids[feature],
        body_definitions["feature"],
        body,
        timestamp,
        implicit,
        0,
        0,
        (0, body_values["feature"]),
    )
    _v12_attribute(
        output,
        implicit,
        node_ids[implicit],
        body_definitions["implicit"],
        body,
        feature,
        match,
        0,
        0,
        (body_values["implicit"], 0),
    )
    _v12_attribute(
        output,
        match,
        node_ids[match],
        body_definitions["match"],
        body,
        implicit,
        density,
        0,
        0,
        (body_values["match"],),
    )
    _v12_attribute(
        output,
        density,
        node_ids[density],
        body_definitions["density"],
        body,
        match,
        lightweight,
        0,
        0,
        (body_values["density"], 0),
    )
    _v12_attribute(
        output,
        lightweight,
        node_ids[lightweight],
        body_definitions["lightweight"],
        body,
        density,
        recipe,
        0,
        0,
        (0, body_values["lightweight"]),
    )
    _v12_attribute(
        output,
        recipe,
        node_ids[recipe],
        body_definitions["recipe"],
        body,
        lightweight,
        base + 2,
        0,
        0,
        (0, 0),
    )
    definitions = (
        (
            "recipe",
            9000,
            standard_actions,
            body_legal,
            (9, 1),
            "BODY_RECIPE_2001",
        ),
        (
            "lightweight",
            9000,
            standard_actions,
            body_legal,
            (9, 1),
            "BODY_IN_LIGHTWEIGHT_PERM",
        ),
        (
            "density",
            8004,
            standard_actions,
            body_legal,
            (2, 3),
            "SDL/TYSA_DENSITY",
        ),
        (
            "match",
            9000,
            retained_actions,
            body_legal,
            (1,),
            "BODY_MATCH",
        ),
        (
            "implicit",
            9000,
            standard_actions,
            implicit_body_legal,
            (10, 10),
            "SWIMPLICITBODYNAME_ID_U",
        ),
        (
            "feature",
            9000,
            standard_actions,
            body_legal,
            (9, 1),
            "LAST_BODY_MODIFYING_FEATURE_ID",
        ),
        (
            "timestamp",
            9000,
            standard_actions,
            body_legal,
            (9, 1),
            "ENT_TIME_STAMP_2001",
        ),
    )
    for name, type_id, actions, legal, fields, identifier in definitions:
        _v12_attribute_definition(
            output,
            body_definitions[name],
            body_definition_next[name],
            body_identifiers[name],
            type_id,
            actions,
            legal,
            fields,
        )
        _v12_attribute_identifier(output, body_identifiers[name], identifier)
    _v12_int_values(output, body_values["timestamp"], (121,))
    _v12_int_values(output, body_values["feature"], (feature_id,))
    _v12_int_values(output, body_values["match"], (27421,))
    _v12_real_values(output, body_values["density"], (1000.0,))
    _v12_int_values(output, body_values["lightweight"], (1,))
    _v12_attribute_definition(
        output,
        base + 12,
        base + 58,
        base + 59,
        9000,
        standard_actions,
        body_legal,
        (9, 1),
    )
    _v12_int_values(output, base + 14, (101,))
    _v12_attribute_identifier(output, base + 59, "ATOM_ID_2001")


def _write_solidworks_body_attribute_suffix(
    output: bytearray,
    base: int,
    body: int,
    face: int,
    feature_id: int,
) -> None:
    standard_actions = (0, 0, 0, 0, 3, 5, 0, 0)
    body_legal = (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    _v12_attribute(
        output,
        base + 32,
        26,
        base + 33,
        face,
        base + 34,
        0,
        0,
        0,
        (base + 35,),
    )
    _v12_attribute_definition(
        output,
        base + 33,
        0,
        base + 36,
        8001,
        standard_actions,
        (0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0),
        (2,),
    )
    _v12_attribute(
        output,
        base + 34,
        24,
        base + 37,
        face,
        0,
        base + 32,
        0,
        0,
        (0, 0),
    )
    _v12_real_values(
        output,
        base + 35,
        (0.792156862745098, 0.8196078431372549, 0.9333333333333333),
    )
    _v12_attribute_definition(
        output,
        base + 37,
        base + 38,
        base + 39,
        9000,
        (0, 0, 0, 0, 3, 6, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (9, 1),
    )
    _v12_attribute_identifier(output, base + 39, "ATOM_FACE_ID_2001")
    _v12_attribute_identifier(output, base + 36, "SDL/TYSA_COLOUR")
    _v12_pointer_list(
        output,
        base + 15,
        (
            base + 40,
            base + 41,
            base + 42,
            base + 34,
            base + 13,
            base + 32,
            base + 2,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ),
        7,
    )
    _v12_attribute(
        output,
        base + 40,
        19,
        base + 43,
        body,
        0,
        base + 41,
        0,
        0,
        (0, base + 44),
    )
    _v12_attribute(
        output,
        base + 41,
        22,
        base + 45,
        body,
        base + 40,
        base + 42,
        0,
        0,
        (0, base + 46),
    )
    _v12_attribute(
        output,
        base + 42,
        23,
        base + 47,
        body,
        base + 41,
        base + 13,
        0,
        0,
        (base + 48, 0),
    )
    _v12_attribute(
        output,
        base + 13,
        25,
        base + 49,
        body,
        base + 42,
        base + 2,
        0,
        0,
        (0, 0),
    )
    _v12_attribute_definition(
        output,
        base + 49,
        base + 50,
        base + 51,
        9000,
        standard_actions,
        body_legal,
        (9, 1),
    )
    _v12_attribute_identifier(output, base + 51, "BODY_RECIPE_2001")
    _v12_attribute_definition(
        output,
        base + 47,
        base + 52,
        base + 53,
        9000,
        standard_actions,
        (0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0),
        (10, 10),
    )
    _v12_attribute_identifier(output, base + 53, "SWIMPLICITBODYNAME_ID_U")
    _v12_attribute_definition(
        output,
        base + 45,
        base + 54,
        base + 55,
        9000,
        standard_actions,
        body_legal,
        (9, 1),
    )
    _v12_int_values(output, base + 46, (feature_id,))
    _v12_attribute_identifier(
        output,
        base + 55,
        "LAST_BODY_MODIFYING_FEATURE_ID",
    )
    _v12_attribute_definition(
        output,
        base + 43,
        base + 56,
        base + 57,
        9000,
        standard_actions,
        body_legal,
        (9, 1),
    )
    _v12_int_values(output, base + 44, (100,))
    _v12_attribute_identifier(output, base + 57, "ENT_TIME_STAMP_2001")
    _v12_attribute_definition(
        output,
        base + 12,
        base + 58,
        base + 59,
        9000,
        standard_actions,
        body_legal,
        (9, 1),
    )
    _v12_int_values(output, base + 14, (101,))
    _v12_attribute_identifier(output, base + 59, "ATOM_ID_2001")


def _order_solidworks_triangle_records(data: bytes) -> bytes:
    fixed_sizes = {
        1: 4,
        12: 61,
        13: 24,
        14: 39,
        15: 16,
        16: 32,
        17: 23,
        18: 28,
        19: 19,
        29: 40,
        70: 39,
    }
    geometry_values = {
        30: 6,
        31: 10,
        32: 11,
        50: 9,
        51: 10,
        52: 12,
        53: 10,
        54: 11,
    }
    variable_sizes = {
        74: lambda count: 14 + 2 * count,
        79: lambda count: 8 + count,
        80: lambda count: 38 + count,
        81: lambda count: 24 + 2 * count,
        82: lambda count: 8 + 4 * count,
        83: lambda count: 8 + 8 * count,
    }
    records: list[tuple[tuple[int, int], bytes]] = []
    offset = 0
    while offset < len(data):
        if offset + 4 > len(data) or data[offset] != 0:
            raise ParasolidWriteError("SOLIDWORKS Parasolid record framing is invalid")
        kind = data[offset + 1]
        if kind in fixed_sizes:
            size = fixed_sizes[kind]
            index_offset = offset + 2
        elif kind in geometry_values:
            size = 19 + 8 * geometry_values[kind]
            index_offset = offset + 2
        elif kind in variable_sizes:
            if offset + 8 > len(data):
                raise ParasolidWriteError("SOLIDWORKS Parasolid record is truncated")
            count = struct.unpack_from(">I", data, offset + 2)[0]
            size = variable_sizes[kind](count)
            index_offset = offset + 6
        else:
            raise ParasolidWriteError(
                f"SOLIDWORKS Parasolid record kind {kind} is unsupported"
            )
        end = offset + size
        if end > len(data):
            raise ParasolidWriteError("SOLIDWORKS Parasolid record is truncated")
        encoded_index = struct.unpack_from(">h", data, index_offset)[0]
        if encoded_index <= 0:
            raise ParasolidWriteError("SOLIDWORKS Parasolid record index is invalid")
        records.append(((kind, encoded_index - 1), data[offset:end]))
        offset = end
    order = (
        (12, 1),
        (81, 2),
        (70, 3),
        (13, 5),
        (50, 6),
        (30, 7),
        (29, 8),
        (19, 9),
        (16, 10),
        (18, 11),
        (17, 19),
        (18, 21),
        (17, 25),
        (18, 27),
        (29, 18),
        (29, 29),
        (17, 28),
        (17, 23),
        (16, 20),
        (17, 24),
        (15, 22),
        (17, 26),
        (16, 30),
        (30, 31),
        (30, 17),
        (14, 16),
    )
    ranks = {key: position for position, key in enumerate(order)}
    if not set(order).issubset(key for key, _ in records):
        raise ParasolidWriteError("SOLIDWORKS Parasolid triangle layout is incomplete")
    ordered = sorted(
        enumerate(records),
        key=lambda item: ranks.get(item[1][0], len(ranks) + item[0]),
    )
    return b"".join(record for _, (_, record) in ordered)


def _v12_variable_node(
    output: bytearray,
    kind: int,
    index: int,
    count: int,
) -> None:
    _tag(output, kind)
    _i32(output, count)
    _v12_pointer(output, index)


def _v12_attribute(
    output: bytearray,
    index: int,
    node_id: int,
    definition: int,
    owner: int,
    next_index: int,
    previous_index: int,
    next_of_type: int,
    previous_of_type: int,
    fields: Sequence[int],
) -> None:
    _v12_variable_node(output, 81, index, len(fields))
    _i32(output, node_id)
    for value in (
        definition,
        owner,
        next_index,
        previous_index,
        next_of_type,
        previous_of_type,
        *fields,
    ):
        _v12_pointer(output, value)


def _v12_attribute_definition(
    output: bytearray,
    index: int,
    next_index: int,
    identifier: int,
    type_id: int,
    actions: Sequence[int],
    legal_owners: Sequence[int],
    fields: Sequence[int],
) -> None:
    _v12_variable_node(output, 80, index, len(fields))
    _v12_pointer(output, next_index)
    _v12_pointer(output, identifier)
    _i32(output, type_id)
    output.extend(bytes(actions))
    output.extend(bytes(legal_owners))
    output.extend(bytes(fields))


def _v12_attribute_identifier(
    output: bytearray,
    index: int,
    value: str,
) -> None:
    encoded = value.encode("ascii")
    _v12_variable_node(output, 79, index, len(encoded))
    output.extend(encoded)


def _v12_pointer_list(
    output: bytearray,
    index: int,
    entries: Sequence[int],
    used: int,
) -> None:
    _v12_variable_node(output, 74, index, len(entries))
    _i32(output, used)
    _v12_pointer(output, 0)
    for value in entries:
        _v12_pointer(output, value)


def _v12_int_values(
    output: bytearray,
    index: int,
    values: Sequence[int],
) -> None:
    _v12_variable_node(output, 82, index, len(values))
    for value in values:
        _i32(output, value)


def _v12_real_values(
    output: bytearray,
    index: int,
    values: Sequence[float],
) -> None:
    _v12_variable_node(output, 83, index, len(values))
    for value in values:
        _bef64(output, value)


def _allocate(values: Iterable[object], next_attr: int) -> tuple[dict[str, int], int]:
    result: dict[str, int] = {}
    for value in values:
        item_id = getattr(value, "id")
        result[item_id] = _checked_attr(next_attr)
        next_attr += 1
    return result, next_attr


def _checked_attr(value: int) -> int:
    if not 0 < value <= 0xFFFF:
        raise ParasolidWriteError("Parasolid B-rep attribute space is exhausted")
    return value


def _write_body_hierarchy(
    model: BrepModel,
    topology: _BrepTopology,
    face_owners: Mapping[str, int],
    sheet_schema: bool,
    next_attr: int,
    output: bytearray,
) -> int:
    assigned: set[str] = set()
    for body in model.bodies:
        root = _checked_attr(next_attr)
        next_attr += 1
        region_kinds = {
            topology.regions[region_id].solid for region_id in body.region_ids
        }
        if len(region_kinds) != 1:
            raise ParasolidWriteError(
                f"B-rep body {body.id} mixes solid and sheet regions"
            )
        solid = region_kinds == {True}
        native_regions: list[int] = []
        for region_id in body.region_ids:
            region = topology.regions[region_id]
            if not solid and len(region.shell_use_ids) != 1:
                raise ParasolidWriteError(
                    f"B-rep sheet region {region.id} must contain one shell"
                )
            native_region = _checked_attr(next_attr)
            next_attr += 1
            native_regions.append(native_region)
            native_lumps: list[int] = []
            for shell_use_id in region.shell_use_ids:
                shell_use = topology.shell_uses[shell_use_id]
                shell = topology.shells[shell_use.shell_id]
                owned: list[int] = []
                for face_use_id in shell.face_use_ids:
                    face_id = topology.face_uses[face_use_id].face_id
                    if face_id in assigned:
                        raise ParasolidWriteError(
                            f"B-rep face {face_id} belongs to multiple bodies"
                        )
                    assigned.add(face_id)
                    owned.append(face_owners[face_id])
                head, next_attr = _write_face_list(
                    output,
                    owned,
                    next_attr,
                    0x0015 if sheet_schema else 0x0013,
                )
                if not solid:
                    _entity51(
                        output,
                        1,
                        native_region,
                        0x001D,
                        (head, 0, 0, 0, 0, 0),
                    )
                    continue
                lump = _checked_attr(next_attr)
                shell_node = _checked_attr(next_attr + 1)
                shell_link = _checked_attr(next_attr + 2)
                next_attr += 3
                native_lumps.append(lump)
                _entity51(
                    output,
                    2,
                    lump,
                    0x001F,
                    (shell_node, 0, 0, 0, 0, 0),
                )
                _entity51(
                    output,
                    2,
                    shell_node,
                    0x0021,
                    (shell_link, 0, 0, 0, 0, 0),
                )
                _entity51(
                    output,
                    2,
                    shell_link,
                    0x0023,
                    (head, 0, 0, 0, 0, 0),
                )
            if solid:
                _entity51(
                    output,
                    1,
                    native_region,
                    0x001B,
                    _fixed_refs(
                        native_lumps,
                        "Parasolid writer regions support at most six shells",
                    ),
                )
        if len(native_regions) > 5:
            raise ParasolidWriteError(
                f"B-rep body {body.id} has more than five regions"
            )
        root_refs = [0, *native_regions]
        root_refs.extend(0 for _ in range(6 - len(root_refs)))
        _entity51(output, 2, root, 0x0017, tuple(root_refs))
    if assigned != set(topology.faces):
        raise ParasolidWriteError("B-rep contains a face outside every body")
    return next_attr


def _write_face_list(
    output: bytearray,
    owners: Sequence[int],
    next_attr: int,
    discriminator: int,
) -> tuple[int, int]:
    chunks = tuple(
        tuple(owners[index : index + 5]) for index in range(0, len(owners), 5)
    ) or ((),)
    attributes = tuple(_checked_attr(next_attr + index) for index in range(len(chunks)))
    next_attr += len(attributes)
    for index, attribute in enumerate(attributes):
        references = [attributes[index + 1] if index + 1 < len(attributes) else 0]
        references.extend(chunks[index])
        references.extend(0 for _ in range(6 - len(references)))
        _entity51(
            output,
            2,
            attribute,
            discriminator,
            tuple(references),
        )
    return attributes[0], next_attr


def _fixed_refs(values: Sequence[int], message: str) -> tuple[int, ...]:
    if len(values) > 6:
        raise ParasolidWriteError(message)
    return tuple((*values, *(0 for _ in range(6 - len(values)))))


def _surface_values(surface: object) -> tuple[int, tuple[float, ...]]:
    if isinstance(surface, PlaneSurface):
        normal, reference = _frame(
            surface.normal,
            surface.reference_direction,
            f"plane surface {surface.id}",
        )
        return 0x32, (
            *_scaled_vector(surface.origin),
            *_vector_values(normal),
            *_vector_values(reference),
        )
    if isinstance(surface, CylinderSurface):
        axis, reference = _frame(
            surface.axis,
            surface.reference_direction,
            f"cylinder surface {surface.id}",
        )
        return 0x33, (
            *_scaled_vector(surface.origin),
            *_vector_values(axis),
            surface.radius * _LENGTH_SCALE,
            *_vector_values(reference),
        )
    if isinstance(surface, ConeSurface):
        if not 0.0 < surface.half_angle < math.pi / 2.0:
            raise ParasolidWriteError(
                f"Parasolid cone surface {surface.id} requires a positive acute angle"
            )
        axis, reference = _frame(
            surface.axis,
            surface.reference_direction,
            f"cone surface {surface.id}",
        )
        return 0x34, (
            *_scaled_vector(surface.origin),
            *_vector_values(axis),
            surface.radius * _LENGTH_SCALE,
            math.sin(surface.half_angle),
            math.cos(surface.half_angle),
            *_vector_values(reference),
        )
    if isinstance(surface, SphereSurface):
        axis, reference = _frame(
            surface.axis,
            surface.reference_direction,
            f"sphere surface {surface.id}",
        )
        return 0x35, (
            *_scaled_vector(surface.center),
            surface.radius * _LENGTH_SCALE,
            *_vector_values(axis),
            *_vector_values(reference),
        )
    if isinstance(surface, TorusSurface):
        if not surface.major_radius > surface.minor_radius > 0.0:
            raise ParasolidWriteError(
                f"Parasolid torus surface {surface.id} requires major radius greater than minor radius"
            )
        axis, reference = _frame(
            surface.axis,
            surface.reference_direction,
            f"torus surface {surface.id}",
        )
        return 0x36, (
            *_scaled_vector(surface.center),
            *_vector_values(axis),
            surface.major_radius * _LENGTH_SCALE,
            surface.minor_radius * _LENGTH_SCALE,
            *_vector_values(reference),
        )
    if isinstance(surface, OffsetSurface):
        raise ParasolidWriteError(
            f"Parasolid B-rep writing does not support offset surface {surface.id}"
        )
    if isinstance(surface, NativeSurface):
        raise ParasolidWriteError(
            f"Parasolid B-rep writing cannot regenerate native surface {surface.id}"
        )
    raise ParasolidWriteError("Parasolid B-rep contains an unsupported surface")


def _curve_values(curve: object) -> tuple[int, tuple[float, ...]]:
    if isinstance(curve, LineCurve):
        direction = _unit(curve.direction, f"line curve {curve.id}")
        return 0x1E, (
            *_scaled_vector(curve.origin),
            *_vector_values(direction),
        )
    if isinstance(curve, CircleCurve):
        axis, reference = _frame(
            curve.axis,
            curve.reference_direction,
            f"circle curve {curve.id}",
        )
        return 0x1F, (
            *_scaled_vector(curve.center),
            *_vector_values(axis),
            *_vector_values(reference),
            curve.radius * _LENGTH_SCALE,
        )
    if isinstance(curve, EllipseCurve):
        axis, reference = _frame(
            curve.axis,
            curve.reference_direction,
            f"ellipse curve {curve.id}",
        )
        return 0x20, (
            *_scaled_vector(curve.center),
            *_vector_values(axis),
            *_vector_values(reference),
            curve.major_radius * _LENGTH_SCALE,
            curve.minor_radius * _LENGTH_SCALE,
        )
    if isinstance(curve, NativeCurve):
        raise ParasolidWriteError(
            f"Parasolid B-rep writing cannot regenerate native curve {curve.id}"
        )
    raise ParasolidWriteError("Parasolid B-rep contains an unsupported curve")


def _write_nurbs_curve(
    output: bytearray,
    wrapper: int,
    curve: NurbsCurve,
    next_attr: int,
) -> int:
    if curve.periodic:
        raise ParasolidWriteError(
            f"Parasolid B-rep writing does not support periodic NURBS curve {curve.id}"
        )
    if not 1 <= curve.degree <= 0xFFFF:
        raise ParasolidWriteError(
            f"Parasolid NURBS curve {curve.id} has an unsupported degree"
        )
    if len(curve.control_points) > 0xFFFFFFFF:
        raise ParasolidWriteError(
            f"Parasolid NURBS curve {curve.id} has too many control points"
        )
    descriptor = _checked_attr(next_attr)
    control = _checked_attr(next_attr + 1)
    multiplicity = _checked_attr(next_attr + 2)
    knots = _checked_attr(next_attr + 3)
    next_attr += 4
    _tag(output, 0x86)
    _be16(output, wrapper)
    _be16(output, descriptor)
    output.extend(bytes(8))
    _tag(output, 0x88)
    _be16(output, descriptor)
    _be16(output, curve.degree)
    _be32(output, len(curve.control_points))
    _be16(output, 4 if curve.weights else 3)
    _be32(output, 2)
    output.append(0)
    output.extend((0, 0, 1 if curve.weights else 0, 0))
    for attribute in (control, multiplicity, knots):
        _be16(output, attribute)
    poles = _homogeneous_points(curve.control_points, curve.weights)
    _f64_array(output, 0x2D, control, poles)
    _u16_array(output, multiplicity, curve.multiplicities)
    _f64_array(output, 0x80, knots, curve.knots)
    return next_attr


def _write_nurbs_surface(
    output: bytearray,
    wrapper: int,
    surface: NurbsSurface,
    next_attr: int,
) -> int:
    if surface.periodic_u or surface.periodic_v:
        raise ParasolidWriteError(
            f"Parasolid B-rep writing does not support periodic NURBS surface {surface.id}"
        )
    if not 1 <= surface.degree_u <= 8 or not 1 <= surface.degree_v <= 8:
        raise ParasolidWriteError(
            f"Parasolid NURBS surface {surface.id} requires degrees from one through eight"
        )
    u_count = len(surface.control_points)
    v_count = len(surface.control_points[0])
    points = tuple(point for row in surface.control_points for point in row)
    weights = tuple(value for row in surface.weights for value in row)
    poles = _homogeneous_points(points, weights)
    intended = (
        u_count,
        v_count,
        surface.degree_u,
        surface.degree_v,
        4 if weights else 3,
    )
    inferred = _infer_surface_shape(
        len(poles),
        surface.multiplicities_u,
        surface.multiplicities_v,
    )
    if inferred != intended:
        raise ParasolidWriteError(
            f"Parasolid writer cannot infer NURBS surface {surface.id} shape {intended}"
        )
    descriptor = _checked_attr(next_attr)
    control = _checked_attr(next_attr + 1)
    u_multiplicity = _checked_attr(next_attr + 2)
    v_multiplicity = _checked_attr(next_attr + 3)
    u_knots = _checked_attr(next_attr + 4)
    v_knots = _checked_attr(next_attr + 5)
    next_attr += 6
    _tag(output, 0x7C)
    _be16(output, wrapper)
    _be32(output, 1)
    output.extend(bytes(10))
    output.append(0x2B)
    _be16(output, descriptor)
    _be16(output, 0)
    _tag(output, 0x7E)
    _be16(output, descriptor)
    output.extend(bytes(12))
    for attribute in (
        control,
        u_multiplicity,
        v_multiplicity,
        u_knots,
        v_knots,
    ):
        _be16(output, attribute)
    _f64_array(output, 0x2D, control, poles)
    _u16_array(output, u_multiplicity, surface.multiplicities_u)
    _u16_array(output, v_multiplicity, surface.multiplicities_v)
    _f64_array(output, 0x80, u_knots, surface.knots_u)
    _f64_array(output, 0x80, v_knots, surface.knots_v)
    return next_attr


def _homogeneous_points(
    points: Sequence[Vector3], weights: Sequence[float]
) -> tuple[float, ...]:
    if weights and len(weights) != len(points):
        raise ParasolidWriteError("B-rep NURBS weights do not match control points")
    result: list[float] = []
    for index, point in enumerate(points):
        weight = weights[index] if weights else 1.0
        result.extend(
            (
                point.x * _LENGTH_SCALE * weight,
                point.y * _LENGTH_SCALE * weight,
                point.z * _LENGTH_SCALE * weight,
            )
        )
        if weights:
            result.append(weight)
    return tuple(result)


def _infer_surface_shape(
    control_length: int,
    u_multiplicities: Sequence[int],
    v_multiplicities: Sequence[int],
) -> tuple[int, int, int, int, int] | None:
    u_sum = sum(u_multiplicities)
    v_sum = sum(v_multiplicities)
    for dimension in (4, 3):
        if control_length % dimension:
            continue
        pole_count = control_length // dimension
        for u_degree in range(1, 9):
            u_count = u_sum - u_degree - 1
            if u_count <= 0:
                continue
            for v_degree in range(1, 9):
                v_count = v_sum - v_degree - 1
                if v_count > 0 and u_count * v_count == pole_count:
                    return u_count, v_count, u_degree, v_degree, dimension
    return None


def _f64_array(
    output: bytearray, kind: int, attribute: int, values: Sequence[float]
) -> None:
    if len(values) > 0xFFFFFFFF:
        raise ParasolidWriteError("Parasolid B-rep array is too large")
    _tag(output, kind)
    output.append(0x2B)
    _be32(output, len(values))
    _be16(output, attribute)
    for value in values:
        _bef64(output, value)


def _u16_array(output: bytearray, attribute: int, values: Sequence[int]) -> None:
    if len(values) > 0xFFFFFFFF or any(
        type(value) is not int or not 0 < value <= 0xFFFF for value in values
    ):
        raise ParasolidWriteError("Parasolid B-rep multiplicity array is invalid")
    _tag(output, 0x7F)
    output.append(0x2B)
    _be32(output, len(values))
    _be16(output, attribute)
    for value in values:
        _be16(output, value)


def _compact(
    output: bytearray,
    kind: int,
    attribute: int,
    values: Sequence[float],
) -> None:
    _tag(output, kind)
    _be16(output, attribute)
    _be32(output, 0)
    output.extend(bytes(10))
    output.append(0x2B)
    for value in values:
        _bef64(output, value)


def _entity51(
    output: bytearray,
    flags: int,
    attribute: int,
    discriminator: int,
    references: Sequence[int],
) -> None:
    if len(references) != 6:
        raise ParasolidWriteError("Parasolid entity references must contain six values")
    _tag(output, 0x51)
    _be32(output, flags)
    _be16(output, attribute)
    _be32(output, 1)
    _be16(output, discriminator)
    for reference in references:
        _be16(output, reference)


def _unit(value: Vector3, label: str) -> Vector3:
    length = math.sqrt(value.x * value.x + value.y * value.y + value.z * value.z)
    if not math.isfinite(length) or length <= 0.0:
        raise ParasolidWriteError(f"Parasolid {label} has an invalid direction")
    return Vector3(value.x / length, value.y / length, value.z / length)


def _frame(axis: Vector3, reference: Vector3, label: str) -> tuple[Vector3, Vector3]:
    normalized_axis = _unit(axis, label)
    normalized_reference = _unit(reference, label)
    dot = (
        normalized_axis.x * normalized_reference.x
        + normalized_axis.y * normalized_reference.y
        + normalized_axis.z * normalized_reference.z
    )
    if abs(dot) > 1e-9:
        raise ParasolidWriteError(
            f"Parasolid {label} axis and reference direction are not orthogonal"
        )
    return normalized_axis, normalized_reference


def _vector_values(value: Vector3) -> tuple[float, float, float]:
    return value.x, value.y, value.z


def _scaled_vector(value: Vector3) -> tuple[float, float, float]:
    return (
        value.x * _LENGTH_SCALE,
        value.y * _LENGTH_SCALE,
        value.z * _LENGTH_SCALE,
    )


def _vector(output: bytearray, value: Vector3, scale: float) -> None:
    for component in (value.x, value.y, value.z):
        _bef64(output, component * scale)


def _parasolid_stream(
    body: bytes,
    schema: str,
    description: bytes = b"partition body",
    user_field_size: int | None = None,
) -> bytes:
    encoded_schema = schema.encode("ascii")
    if len(encoded_schema) > 0xFF:
        raise ParasolidWriteError("Parasolid schema name is too long")
    output = bytearray(b"PS\x00\x00")
    _be16(output, len(description))
    output.extend(description)
    _be32(output, len(encoded_schema))
    output.extend(encoded_schema)
    if user_field_size is not None:
        _be32(output, user_field_size)
    output.extend(body)
    return bytes(output)


def _v12_node(output: bytearray, kind: int, index: int) -> None:
    _tag(output, kind)
    _v12_pointer(output, index)


def _v12_pointer(output: bytearray, index: int) -> None:
    if index < 0:
        raise ParasolidWriteError("Parasolid pointer index is negative")
    if index < 32767:
        output.extend(struct.pack(">h", index + 1))
        return
    output.extend(struct.pack(">hH", -(index % 32767 + 1), index // 32767))


def _i32(output: bytearray, value: int) -> None:
    if not -(1 << 31) <= value < 1 << 31:
        raise ParasolidWriteError("Parasolid i32 field is out of range")
    output.extend(struct.pack(">i", value))


def _v12_geometry_node(
    output: bytearray,
    kind: int,
    index: int,
    node_id: int,
    owner: int,
    next_index: int,
    previous_index: int,
    values: Sequence[float],
) -> None:
    _v12_node(output, kind, index)
    _i32(output, node_id)
    _v12_pointer(output, 0)
    _v12_pointer(output, owner)
    _v12_pointer(output, next_index)
    _v12_pointer(output, previous_index)
    _v12_pointer(output, 0)
    output.extend(b"+")
    for value in values:
        _bef64(output, value)


def _v12_fin(
    output: bytearray,
    index: int,
    attributes: int,
    loop: int,
    forward: int,
    backward: int,
    vertex: int,
    other: int,
    edge: int,
    curve: int,
    next_at_vertex: int,
    positive: bool,
) -> None:
    _v12_node(output, 17, index)
    for value in (
        attributes,
        loop,
        forward,
        backward,
        vertex,
        other,
        edge,
        curve,
        next_at_vertex,
    ):
        _v12_pointer(output, value)
    output.extend(b"+" if positive else b"-")


def _next_fin_at_vertex(index: int, vertex_fins: Mapping[str, Sequence[int]]) -> int:
    for values in vertex_fins.values():
        if index not in values:
            continue
        position = values.index(index)
        return values[position + 1] if position + 1 < len(values) else 0
    raise ParasolidWriteError("Parasolid fin has no vertex chain")


def _tag(output: bytearray, kind: int) -> None:
    output.extend((0, kind))


def _be16(output: bytearray, value: int) -> None:
    if not 0 <= value <= 0xFFFF:
        raise ParasolidWriteError("Parasolid u16 field is out of range")
    output.extend(struct.pack(">H", value))


def _be32(output: bytearray, value: int) -> None:
    if not 0 <= value <= 0xFFFFFFFF:
        raise ParasolidWriteError("Parasolid u32 field is out of range")
    output.extend(struct.pack(">I", value))


def _bef64(output: bytearray, value: float) -> None:
    if not math.isfinite(value):
        raise ParasolidWriteError("Parasolid B-rep contains a non-finite value")
    output.extend(struct.pack(">d", value))


@dataclass(frozen=True, slots=True)
class ParasolidPayload:
    stream: str
    kind: str
    schema: str
    description: str
    data: bytes
    sha256: str
    wrapper_offset: int
    magic_offset: int
    compressed_offset: int
    compressed_size: int
    uncompressed_size: int


def decode_partition_stream(
    data: bytes, stream: str = ""
) -> tuple[ParasolidPayload, ...]:
    results: list[ParasolidPayload] = []
    cursor = 0
    while True:
        magic_offset = data.find(_WRAPPER_MAGIC, cursor)
        if magic_offset < 0:
            break
        cursor = magic_offset + 1
        header_offset = magic_offset + len(_WRAPPER_MAGIC)
        if header_offset + 8 > len(data):
            continue
        uncompressed_size, compressed_size = struct.unpack_from(
            "<II", data, header_offset
        )
        compressed_offset = header_offset + 8
        compressed_end = compressed_offset + compressed_size
        if compressed_end > len(data):
            continue
        try:
            payload = zlib.decompress(data[compressed_offset:compressed_end])
        except zlib.error:
            continue
        if len(payload) != uncompressed_size or not payload.startswith(b"PS\x00\x00"):
            continue
        results.append(
            _payload(
                stream,
                payload,
                magic_offset - 4 if magic_offset >= 4 else magic_offset,
                magic_offset,
                compressed_offset,
                compressed_size,
                uncompressed_size,
            )
        )
        cursor = compressed_end
    if not results and data.startswith(b"PS\x00\x00"):
        results.append(_payload(stream, data, 0, 0, 0, len(data), len(data)))
    if not results:
        raise ParasolidFormatError(
            f"no Parasolid payload found in {stream or 'stream'}"
        )
    return tuple(results)


def _payload(
    stream: str,
    data: bytes,
    wrapper_offset: int,
    magic_offset: int,
    compressed_offset: int,
    compressed_size: int,
    uncompressed_size: int,
) -> ParasolidPayload:
    header = data[:8192]
    kind_match = re.search(rb"TRANSMIT FILE \(([^)]+)\)", header)
    schema_match = re.search(rb"SCH_[0-9A-Z_]+", header)
    description_match = re.search(rb": ([\x20-\x7e]{1,512})", header)
    return ParasolidPayload(
        stream=stream,
        kind=(
            kind_match.group(1).decode("ascii", "replace") if kind_match else "unknown"
        ),
        schema=(schema_match.group(0).decode("ascii") if schema_match else "unknown"),
        description=(
            description_match.group(1).decode("ascii", "replace").strip()
            if description_match
            else ""
        ),
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
        wrapper_offset=wrapper_offset,
        magic_offset=magic_offset,
        compressed_offset=compressed_offset,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
    )


@dataclass(frozen=True, slots=True)
class _ParasolidHeader:
    description: str
    schema: str
    body_offset: int


@dataclass(frozen=True, slots=True)
class _TopologyRecord:
    attribute: int
    references: tuple[int, ...]
    offset: int
    reversed: bool = False
    owner: int = 0
    point: Vector3 | None = None
    isolated: bool = False
    tolerance: float = 0.0


@dataclass(frozen=True, slots=True)
class _EntityRecord:
    flags: int
    attribute: int
    discriminator: int
    references: tuple[int, ...]
    offset: int


@dataclass(frozen=True, slots=True)
class _IntersectionRecord:
    attribute: int
    header_references: tuple[int, ...]
    references: tuple[int, ...]
    sense: bool
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _ChartRecord:
    attribute: int
    base_parameter: float
    base_scale: float
    chordal_error: float
    angular_error: float
    parameter_errors: tuple[float, float]
    points: tuple[Vector3, ...]
    parameters: tuple[float, ...]
    tangents: tuple[Vector3, ...]
    support_uv: tuple[tuple[tuple[float, float], ...], ...]
    layout: str
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _TermRecord:
    attribute: int
    count: int
    form: str
    point: Vector3
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _SupportUvRecord:
    attribute: int
    marker: int
    values: tuple[float, ...]
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _CompactSupportUvRecord:
    attribute: int
    marker: int
    values: tuple[float, ...]
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _BSurfaceRecord:
    attribute: int
    state: int
    header_references: tuple[int, ...]
    descriptor_reference: int
    data_reference: int
    sense: bool
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _NurbsSurfaceRecord:
    attribute: int
    periodic: tuple[bool, bool]
    degrees: tuple[int, int]
    counts: tuple[int, int]
    knot_types: tuple[int, int]
    knot_counts: tuple[int, int]
    rational: bool
    closed: tuple[bool, bool]
    surface_form: int
    vertex_dimension: int
    references: tuple[int, ...]
    layout: str
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _SurfaceDataRecord:
    attribute: int
    intervals: tuple[tuple[float, float], ...]
    self_intersection: int
    flags: bytes
    references: tuple[int, ...]
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _BCurveRecord:
    attribute: int
    state: int
    header_references: tuple[int, ...]
    descriptor_reference: int
    data_reference: int
    sense: bool
    layout: str
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _NurbsCurveRecord:
    attribute: int
    degree: int
    control_count: int
    vertex_dimension: int
    knot_count: int
    knot_type: int
    periodic: bool
    closed: bool
    rational: bool
    curve_form: int
    references: tuple[int, ...]
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _CurveDataRecord:
    attribute: int
    self_intersection: int
    analytic_form_reference: int
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _TrimmedCurveRecord:
    attribute: int
    state: int
    header_references: tuple[int, ...]
    basis_reference: int
    points: tuple[Vector3, Vector3]
    parameters: tuple[float, float]
    sense: bool
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _FloatArrayRecord:
    attribute: int
    kind: int
    values: tuple[float, ...]
    offset: int
    raw: bytes


@dataclass(frozen=True, slots=True)
class _ShortArrayRecord:
    attribute: int
    values: tuple[int, ...]
    offset: int
    raw: bytes


@dataclass(slots=True)
class _RecordTables:
    bridges: dict[int, _TopologyRecord]
    loops: dict[int, _TopologyRecord]
    edge_uses: dict[int, _TopologyRecord]
    coedges: dict[int, _TopologyRecord]
    vertex_uses: dict[int, _TopologyRecord]
    points: dict[int, _TopologyRecord]
    curves: dict[int, object]
    surfaces: dict[int, object]
    entities: dict[int, _EntityRecord]
    v12_partition: bool = False


def decode_brep_model(
    payload: bytes | bytearray,
) -> BrepModel | None:
    data = bytes(payload)
    header = _parasolid_header(data)
    if header is None:
        return None
    description = header.description.casefold()
    if "delta" in description or "transmit file" not in description:
        return None
    return _decode_partition_model(data, header)


def transform_solidworks_rectangle_partition_stream(
    data: bytes | bytearray,
    *,
    minimum_x_mm: float,
    minimum_y_mm: float,
    maximum_x_mm: float,
    maximum_y_mm: float,
    depth_mm: float,
) -> bytes:
    bounds = _solidworks_rectangle_bounds(
        minimum_x_mm,
        minimum_y_mm,
        maximum_x_mm,
        maximum_y_mm,
        depth_mm,
    )
    source = bytes(data)
    if hashlib.sha256(source).hexdigest() != _SOLIDWORKS_RECTANGLE_PARTITION_SHA256:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition does not match the validated donor"
        )
    payloads = decode_partition_stream(source, "Contents/Config-0-Partition")
    if not _is_solidworks_rectangle_partition(payloads):
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition donor framing is invalid"
        )
    primary = payloads[0].data
    header = _parasolid_header(primary)
    if header is None or header.body_offset != 96:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition donor header is invalid"
        )
    original_body = primary[header.body_offset :]
    tables = _scan_partition_records(original_body)
    source_model = decode_brep_model(primary)
    if tables is None or source_model is None:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition donor cannot be decoded"
        )
    _validate_solidworks_rectangle_source(source_model, tables)
    if bounds == _SOLIDWORKS_RECTANGLE_SOURCE_BOUNDS:
        return source
    body = bytearray(original_body)
    point_records = tuple(tables.points.values())
    used_curve_attributes = frozenset(
        record.references[3] for record in tables.edge_uses.values()
    )
    used_surface_attributes = frozenset(
        record.references[4] for record in tables.bridges.values()
    )
    for record in point_records:
        values_offset = _solidworks_rectangle_point_offset(original_body, record)
        transformed = _solidworks_rectangle_vector(record.point, bounds)
        _pack_solidworks_rectangle_vector(body, values_offset, transformed)
    for attribute in sorted(used_curve_attributes):
        geometry = tables.curves[attribute]
        values_offset = _solidworks_rectangle_carrier_offset(
            original_body,
            attribute,
            geometry,
        )
        transformed = _solidworks_rectangle_vector(geometry.origin, bounds)
        _pack_solidworks_rectangle_vector(body, values_offset, transformed)
    for attribute in sorted(used_surface_attributes):
        geometry = tables.surfaces[attribute]
        values_offset = _solidworks_rectangle_carrier_offset(
            original_body,
            attribute,
            geometry,
        )
        transformed = _solidworks_rectangle_vector(geometry.origin, bounds)
        _pack_solidworks_rectangle_vector(body, values_offset, transformed)
    patched_primary = primary[: header.body_offset] + bytes(body)
    transformed_stream = (
        encode_partition_stream(patched_primary) + source[payloads[1].wrapper_offset :]
    )
    transformed_payloads = decode_partition_stream(
        transformed_stream,
        "Contents/Config-0-Partition",
    )
    if (
        len(transformed_payloads) != 2
        or transformed_payloads[0].data != patched_primary
        or transformed_payloads[1].sha256 != _SOLIDWORKS_RECTANGLE_DELTAS_SHA256
        or transformed_payloads[1].data != payloads[1].data
    ):
        raise ParasolidWriteError(
            "transformed SOLIDWORKS rectangle Partition framing is invalid"
        )
    transformed_model = decode_brep_model(patched_primary)
    if transformed_model is None:
        raise ParasolidWriteError(
            "transformed SOLIDWORKS rectangle Partition cannot be decoded"
        )
    _validate_solidworks_rectangle_transform(
        source_model,
        transformed_model,
        bounds,
    )
    return transformed_stream


def _solidworks_rectangle_bounds(
    minimum_x_mm: float,
    minimum_y_mm: float,
    maximum_x_mm: float,
    maximum_y_mm: float,
    depth_mm: float,
) -> tuple[float, float, float, float, float]:
    values = (
        minimum_x_mm,
        minimum_y_mm,
        maximum_x_mm,
        maximum_y_mm,
        depth_mm,
    )
    if any(isinstance(value, bool) for value in values):
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle bounds and depth must be finite numbers"
        )
    try:
        bounds = tuple(float(value) for value in values)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle bounds and depth must be finite numbers"
        ) from exc
    if any(not math.isfinite(value) for value in bounds):
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle bounds and depth must be finite numbers"
        )
    minimum_x, minimum_y, maximum_x, maximum_y, depth = bounds
    if minimum_x >= maximum_x or minimum_y >= maximum_y or depth <= 0.0:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle bounds must have positive width, height, and depth"
        )
    return minimum_x, minimum_y, maximum_x, maximum_y, depth


def _is_solidworks_rectangle_partition(
    payloads: tuple[ParasolidPayload, ...],
) -> bool:
    if len(payloads) != 2:
        return False
    primary, deltas = payloads
    return (
        primary.wrapper_offset == 0
        and primary.magic_offset == 4
        and primary.compressed_offset == 28
        and primary.compressed_size == 3076
        and primary.uncompressed_size == 6730
        and primary.kind == "partition"
        and primary.schema == _SOLIDWORKS_RECTANGLE_SCHEMA
        and primary.sha256 == _SOLIDWORKS_RECTANGLE_PRIMARY_SHA256
        and deltas.wrapper_offset == 3112
        and deltas.kind == "deltas"
        and deltas.schema == _SOLIDWORKS_RECTANGLE_SCHEMA
        and deltas.uncompressed_size == 1124
        and deltas.sha256 == _SOLIDWORKS_RECTANGLE_DELTAS_SHA256
    )


def _validate_solidworks_rectangle_source(
    model: BrepModel,
    tables: _RecordTables,
) -> None:
    counts = (
        len(model.bodies),
        len(model.regions),
        len(model.shells),
        len(model.shell_uses),
        len(model.faces),
        len(model.face_uses),
        len(model.loops),
        len(model.coedges),
        len(model.edges),
        len(model.vertices),
        len(model.curves),
        len(model.surfaces),
        len(model.pcurves),
        len(model.wires),
    )
    expected_counts = (1, 1, 1, 1, 6, 6, 6, 24, 12, 8, 12, 6, 0, 0)
    expected_vertices = frozenset(
        (x, y, z) for x in (-20.0, 20.0) for y in (-10.0, 10.0) for z in (0.0, 10.0)
    )
    vertices = frozenset(
        (vertex.point.x, vertex.point.y, vertex.point.z) for vertex in model.vertices
    )
    used_curve_attributes = frozenset(
        record.references[3] for record in tables.edge_uses.values()
    )
    used_surface_attributes = frozenset(
        record.references[4] for record in tables.bridges.values()
    )
    if (
        counts != expected_counts
        or model.validate()
        or model.bodies[0].transform != Transform()
        or not model.regions[0].solid
        or not model.shells[0].closed
        or vertices != expected_vertices
        or len(tables.points) != 8
        or len(used_curve_attributes) != 12
        or len(used_surface_attributes) != 6
        or any(
            attribute not in tables.curves
            or not isinstance(tables.curves[attribute], LineCurve)
            for attribute in used_curve_attributes
        )
        or any(
            attribute not in tables.surfaces
            or not isinstance(tables.surfaces[attribute], PlaneSurface)
            for attribute in used_surface_attributes
        )
    ):
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition donor geometry is invalid"
        )


def _solidworks_rectangle_point_offset(
    body: bytes,
    record: _TopologyRecord,
) -> int:
    for prefixed in (False, True):
        fields = _point_record_fields(body, record.offset, prefixed)
        parsed = _parse_point(body, record.offset, prefixed)
        if (
            fields is not None
            and parsed is not None
            and parsed.attribute == record.attribute
            and parsed.references == record.references
            and parsed.point == record.point
        ):
            return fields[2]
    raise ParasolidWriteError("SOLIDWORKS rectangle Partition point record is invalid")


def _solidworks_rectangle_carrier_offset(
    body: bytes,
    attribute: int,
    geometry: object,
) -> int:
    attributes = getattr(geometry, "attributes", {})
    carrier = attributes.get("carrier_record")
    if not isinstance(carrier, bytes) or not carrier:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition analytic record is invalid"
        )
    offset = body.find(carrier)
    if offset < 0 or body.find(carrier, offset + 1) >= 0:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition analytic record is ambiguous"
        )
    fields = _analytic_record_fields(body, offset)
    if fields is None or fields[0] != attribute:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition analytic record is invalid"
        )
    return fields[1]


def _solidworks_rectangle_vector(
    vector: Vector3 | None,
    bounds: tuple[float, float, float, float, float],
) -> tuple[float, float, float]:
    if vector is None:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle Partition coordinate is missing"
        )
    minimum_x, minimum_y, maximum_x, maximum_y, depth = bounds
    return (
        _solidworks_rectangle_axis(vector.x, -20.0, 20.0, minimum_x, maximum_x),
        _solidworks_rectangle_axis(vector.y, -10.0, 10.0, minimum_y, maximum_y),
        _solidworks_rectangle_axis(vector.z, 0.0, 10.0, 0.0, depth),
    )


def _solidworks_rectangle_axis(
    value: float,
    source_minimum: float,
    source_maximum: float,
    target_minimum: float,
    target_maximum: float,
) -> float:
    if value == source_minimum:
        return target_minimum
    if value == source_maximum:
        return target_maximum
    if value == (source_minimum + source_maximum) / 2.0:
        return target_minimum / 2.0 + target_maximum / 2.0
    raise ParasolidWriteError(
        "SOLIDWORKS rectangle Partition contains an unexpected coordinate"
    )


def _pack_solidworks_rectangle_vector(
    body: bytearray,
    offset: int,
    vector: tuple[float, float, float],
) -> None:
    try:
        values = tuple(value / 1000.0 for value in vector)
        if any(not math.isfinite(value) for value in values):
            raise OverflowError
        struct.pack_into(">3d", body, offset, *values)
    except (OverflowError, struct.error) as exc:
        raise ParasolidWriteError(
            "SOLIDWORKS rectangle bounds exceed the Parasolid coordinate range"
        ) from exc


def _validate_solidworks_rectangle_transform(
    source: BrepModel,
    transformed: BrepModel,
    bounds: tuple[float, float, float, float, float],
) -> None:
    if transformed.validate():
        raise ParasolidWriteError(
            "transformed SOLIDWORKS rectangle Partition geometry is invalid"
        )
    collection_names = (
        "bodies",
        "regions",
        "shells",
        "shell_uses",
        "faces",
        "face_uses",
        "loops",
        "coedges",
        "edges",
        "vertices",
        "curves",
        "surfaces",
    )
    if any(
        tuple(item.id for item in getattr(source, name))
        != tuple(item.id for item in getattr(transformed, name))
        for name in collection_names
    ):
        raise ParasolidWriteError(
            "transformed SOLIDWORKS rectangle Partition changes topology"
        )
    transformed_vertices = {item.id: item for item in transformed.vertices}
    transformed_curves = {item.id: item for item in transformed.curves}
    transformed_surfaces = {item.id: item for item in transformed.surfaces}
    for vertex in source.vertices:
        expected = _solidworks_rectangle_vector(vertex.point, bounds)
        if not _solidworks_rectangle_vector_matches(
            transformed_vertices[vertex.id].point,
            expected,
        ):
            raise ParasolidWriteError(
                "transformed SOLIDWORKS rectangle Partition changes a vertex"
            )
    for curve in source.curves:
        target = transformed_curves[curve.id]
        expected = _solidworks_rectangle_vector(curve.origin, bounds)
        if (
            not isinstance(curve, LineCurve)
            or not isinstance(target, LineCurve)
            or target.direction != curve.direction
            or not _solidworks_rectangle_vector_matches(target.origin, expected)
        ):
            raise ParasolidWriteError(
                "transformed SOLIDWORKS rectangle Partition changes a curve"
            )
    for surface in source.surfaces:
        target = transformed_surfaces[surface.id]
        expected = _solidworks_rectangle_vector(surface.origin, bounds)
        if (
            not isinstance(surface, PlaneSurface)
            or not isinstance(target, PlaneSurface)
            or target.normal != surface.normal
            or target.reference_direction != surface.reference_direction
            or not _solidworks_rectangle_vector_matches(target.origin, expected)
        ):
            raise ParasolidWriteError(
                "transformed SOLIDWORKS rectangle Partition changes a surface"
            )


def _solidworks_rectangle_vector_matches(
    vector: Vector3,
    expected: tuple[float, float, float],
) -> bool:
    return all(
        math.isclose(actual, intended, rel_tol=1e-12, abs_tol=1e-9)
        for actual, intended in zip(
            (vector.x, vector.y, vector.z),
            expected,
            strict=True,
        )
    )


def _parasolid_header(data: bytes) -> _ParasolidHeader | None:
    if len(data) < 12 or not data.startswith(b"PS\x00\x00"):
        return None
    description_length = struct.unpack_from(">H", data, 4)[0]
    description_start = 6
    description_end = description_start + description_length
    if description_end + 4 > len(data):
        return None
    schema_length = struct.unpack_from(">I", data, description_end)[0]
    schema_offset = description_end + 4
    schema_end = schema_offset + schema_length
    if schema_length < 4 or schema_length > 255 or schema_end > len(data):
        return None
    if data[schema_offset : schema_offset + 4] != b"SCH_":
        return None
    try:
        description = data[description_start:description_end].decode("ascii")
        schema = data[schema_offset:schema_end].decode("ascii")
    except UnicodeDecodeError:
        return None
    if not schema.startswith("SCH_"):
        return None
    return _ParasolidHeader(description, schema, schema_end)


def _decode_partition_model(
    payload: bytes,
    header: _ParasolidHeader,
) -> BrepModel | None:
    body = payload[header.body_offset :]
    if not body or len(body) > 268_435_456:
        return None
    tables = _scan_partition_records(body)
    if tables is None or not tables.bridges:
        return None
    unchanged_ids, attribute_orders = _solidworks_face_data(body)
    try:
        model = _build_partition_model(tables, unchanged_ids, attribute_orders)
    except (KeyError, ValueError, OverflowError):
        return None
    if model.validate():
        return None
    return model


def _solidworks_unchanged_ids(body: bytes) -> dict[int, int]:
    return _solidworks_face_data(body)[0]


def _solidworks_face_data(
    body: bytes,
) -> tuple[dict[int, int], dict[str, dict[int, int]]]:
    names = {
        "unchanged": b"SWEntUnchanged",
        "downstream": b"DOWNSTREAM_FACE_ID",
        "colour": b"SDL/TYSA_COLOUR",
    }
    identifier_kinds: dict[int, str] = {}
    cursor = 0
    while (offset := body.find(b"\x00\x4f", cursor)) >= 0:
        cursor = offset + 1
        count = _u32(body, offset + 2)
        index = _u16(body, offset + 6)
        if count is None or index is None or offset + 8 + count > len(body):
            continue
        value = body[offset + 8 : offset + 8 + count]
        kind = next((name for name, encoded in names.items() if value == encoded), None)
        if kind is not None:
            identifier_kinds[index] = kind
    definition_kinds: dict[int, str] = {}
    cursor = 0
    while (offset := body.find(b"\x00\x50", cursor)) >= 0:
        cursor = offset + 1
        count = _u32(body, offset + 2)
        index = _u16(body, offset + 6)
        identifier = _u16(body, offset + 10)
        if (
            count is None
            or count > 64
            or offset + 38 + count > len(body)
            or index is None
            or identifier not in identifier_kinds
        ):
            continue
        definition_kinds[index] = identifier_kinds[identifier]
    if not definition_kinds:
        return {}, {}
    value_records: dict[int, int] = {}
    cursor = 0
    while (offset := body.find(b"\x00\x52", cursor)) >= 0:
        cursor = offset + 1
        count = _u32(body, offset + 2)
        index = _u16(body, offset + 6)
        if count != 1 or index is None or offset + 12 > len(body):
            continue
        value = struct.unpack_from(">i", body, offset + 8)[0]
        if value > 0:
            value_records[index] = value
    records: dict[str, dict[int, tuple[int, int, int, int]]] = {
        kind: {} for kind in names
    }
    cursor = 0
    while (offset := body.find(b"\x00\x51", cursor)) >= 0:
        cursor = offset + 1
        count = _u32(body, offset + 2)
        index = _u16(body, offset + 6)
        attribute_definition = _u16(body, offset + 12)
        owner = _u16(body, offset + 14)
        next_of_type = _u16(body, offset + 20)
        previous_of_type = _u16(body, offset + 22)
        value_index = _u16(body, offset + 24)
        if (
            count is None
            or count < 1
            or count > 64
            or offset + 24 + count * 2 > len(body)
            or index is None
            or attribute_definition not in definition_kinds
            or owner is None
            or next_of_type is None
            or previous_of_type is None
            or value_index is None
        ):
            continue
        kind = definition_kinds[attribute_definition]
        records[kind][index] = owner, next_of_type, previous_of_type, value_index
    orders: dict[str, dict[int, int]] = {}
    for kind, values in records.items():
        ordered = _linked_subset_order(
            values,
            {attribute: (record[1], record[2]) for attribute, record in values.items()},
        )
        owners = [values[attribute][0] for attribute in ordered]
        if len(set(owners)) == len(owners):
            orders[kind] = {owner: rank for rank, owner in enumerate(owners)}
    unchanged: dict[int, int] = {}
    ambiguous: set[int] = set()
    for owner, _, _, value_index in records["unchanged"].values():
        if value_index not in value_records:
            continue
        if owner in unchanged:
            ambiguous.add(owner)
        else:
            unchanged[owner] = value_records[value_index]
    for owner in ambiguous:
        unchanged.pop(owner, None)
    return unchanged, orders


def _scan_partition_records(body: bytes) -> _RecordTables | None:
    tables = _RecordTables(
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        {},
        body.startswith(b"\x00\x00\x00\x00\x00\x65\x00\x02")
        or body.startswith(b"\x00\x00\x00\x00\x00\x0c\x00\x02"),
    )
    loop_candidates: list[_TopologyRecord] = []
    intersections: dict[int, _IntersectionRecord] = {}
    charts: dict[int, _ChartRecord] = {}
    terms: dict[int, _TermRecord] = {}
    support_uv: dict[int, _SupportUvRecord] = {}
    compact_support_uv: dict[int, _CompactSupportUvRecord] = {}
    b_surfaces: dict[int, _BSurfaceRecord] = {}
    nurbs_surfaces: dict[int, _NurbsSurfaceRecord] = {}
    surface_data: dict[int, _SurfaceDataRecord] = {}
    b_curves: dict[int, _BCurveRecord] = {}
    nurbs_curves: dict[int, _NurbsCurveRecord] = {}
    curve_data: dict[int, _CurveDataRecord] = {}
    trimmed_curves: dict[int, _TrimmedCurveRecord] = {}
    float_arrays: dict[int, _FloatArrayRecord] = {}
    short_arrays: dict[int, _ShortArrayRecord] = {}
    ambiguous_intersections: set[int] = set()
    ambiguous_charts: set[int] = set()
    ambiguous_terms: set[int] = set()
    ambiguous_support_uv: set[int] = set()
    ambiguous_compact_support_uv: set[int] = set()
    ambiguous_b_surfaces: set[int] = set()
    ambiguous_nurbs_surfaces: set[int] = set()
    ambiguous_surface_data: set[int] = set()
    ambiguous_b_curves: set[int] = set()
    ambiguous_nurbs_curves: set[int] = set()
    ambiguous_curve_data: set[int] = set()
    ambiguous_trimmed_curves: set[int] = set()
    ambiguous_float_arrays: set[int] = set()
    ambiguous_short_arrays: set[int] = set()
    chart_point_count = 0
    spline_scalar_count = 0
    for offset in range(max(0, len(body) - 1)):
        if body[offset] != 0:
            continue
        kind = body[offset + 1]
        topology: tuple[dict[int, _TopologyRecord], _TopologyRecord | None] | None = (
            None
        )
        if kind == 0x0E:
            topology = tables.bridges, _parse_bridge(
                body,
                offset,
                allow_null_owner=tables.v12_partition,
            )
        elif kind == 0x0F:
            record = _parse_loop(body, offset)
            if record is not None:
                loop_candidates.append(record)
        elif kind == 0x10:
            topology = tables.edge_uses, _parse_edge_use(body, offset)
        elif kind == 0x11:
            topology = tables.coedges, _parse_coedge(body, offset)
        elif kind == 0x12:
            topology = tables.vertex_uses, _parse_vertex_use(body, offset)
        elif kind == 0x1D:
            topology = tables.points, (
                _parse_point(body, offset) or _parse_point(body, offset, True)
            )
        if topology is not None:
            target, record = topology
            if record is not None:
                target.setdefault(record.attribute, record)
        record = _parse_compact_support_uv_record(body, offset)
        if record is not None:
            _store_unique_record(
                compact_support_uv,
                ambiguous_compact_support_uv,
                record.attribute,
                record,
            )
        if kind == 0x26:
            record = _parse_intersection_record(body, offset)
            if record is not None:
                _store_unique_record(
                    intersections,
                    ambiguous_intersections,
                    record.attribute,
                    record,
                )
        if kind == 0x28:
            record = _parse_chart_record(body, offset)
            if record is not None:
                chart_point_count += len(record.points)
                if chart_point_count > 4_000_000:
                    return None
                _store_unique_record(
                    charts,
                    ambiguous_charts,
                    record.attribute,
                    record,
                )
        if kind == 0x29:
            record = _parse_term_record(body, offset)
            if record is not None:
                _store_unique_record(
                    terms,
                    ambiguous_terms,
                    record.attribute,
                    record,
                )
        if kind in {0x1E, 0x1F, 0x20, 0x32, 0x33, 0x34, 0x35, 0x36}:
            carrier = _parse_analytic_carrier(body, offset)
            if carrier is not None:
                target = tables.curves if kind < 0x32 else tables.surfaces
                target[carrier[0]] = carrier[1]
        if kind == 0x51:
            entity = _parse_entity(body, offset)
            if entity is not None:
                tables.entities[entity.attribute] = entity
        if kind == 0xCC:
            record = _parse_support_uv_record(body, offset)
            if record is not None:
                _store_unique_record(
                    support_uv,
                    ambiguous_support_uv,
                    record.attribute,
                    record,
                )
        if kind == 0x7C:
            record = _parse_b_surface_record(body, offset)
            if record is not None:
                _store_unique_record(
                    b_surfaces,
                    ambiguous_b_surfaces,
                    record.attribute,
                    record,
                )
        if kind == 0x7E:
            record = _parse_nurbs_surface_record(body, offset)
            if record is not None:
                _store_unique_record(
                    nurbs_surfaces,
                    ambiguous_nurbs_surfaces,
                    record.attribute,
                    record,
                )
        if kind == 0x7D:
            record = _parse_surface_data_record(body, offset)
            if record is not None:
                _store_unique_record(
                    surface_data,
                    ambiguous_surface_data,
                    record.attribute,
                    record,
                )
        if kind == 0x86:
            record = _parse_b_curve_record(body, offset)
            if record is not None:
                _store_unique_record(
                    b_curves,
                    ambiguous_b_curves,
                    record.attribute,
                    record,
                )
        if kind == 0x88:
            record = _parse_nurbs_curve_record(body, offset)
            if record is not None:
                _store_unique_record(
                    nurbs_curves,
                    ambiguous_nurbs_curves,
                    record.attribute,
                    record,
                )
        if kind == 0x87:
            record = _parse_curve_data_record(body, offset)
            if record is not None:
                _store_unique_record(
                    curve_data,
                    ambiguous_curve_data,
                    record.attribute,
                    record,
                )
        if kind == 0x85:
            record = _parse_trimmed_curve_record(body, offset)
            if record is not None:
                _store_unique_record(
                    trimmed_curves,
                    ambiguous_trimmed_curves,
                    record.attribute,
                    record,
                )
        if kind in {0x2D, 0x80}:
            record = _parse_float_array_record(body, offset, kind)
            if record is not None:
                spline_scalar_count += len(record.values)
                if spline_scalar_count > 8_000_000:
                    return None
                _store_unique_record(
                    float_arrays,
                    ambiguous_float_arrays,
                    record.attribute,
                    record,
                )
        if kind == 0x7F:
            record = _parse_short_array_record(body, offset)
            if record is not None:
                spline_scalar_count += len(record.values)
                if spline_scalar_count > 8_000_000:
                    return None
                _store_unique_record(
                    short_arrays,
                    ambiguous_short_arrays,
                    record.attribute,
                    record,
                )
        if (
            sum(
                len(values)
                for values in (
                    tables.bridges,
                    tables.loops,
                    tables.edge_uses,
                    tables.coedges,
                    tables.vertex_uses,
                    tables.points,
                    tables.curves,
                    tables.surfaces,
                    tables.entities,
                    intersections,
                    charts,
                    terms,
                    support_uv,
                    compact_support_uv,
                    b_surfaces,
                    nurbs_surfaces,
                    surface_data,
                    b_curves,
                    nurbs_curves,
                    curve_data,
                    trimmed_curves,
                    float_arrays,
                    short_arrays,
                )
            )
            > 1_000_000
        ):
            return None
    cursor = 0
    term_descriptor = b"term_use" + _INLINE_TERM_TAIL
    while (position := body.find(term_descriptor, cursor)) >= 0:
        base = position + len(term_descriptor)
        record = _parse_term_payload(body, base, base)
        if record is not None:
            _store_unique_record(
                terms,
                ambiguous_terms,
                record.attribute,
                record,
            )
        cursor = position + 1
    cursor = 0
    uv_descriptor = b"values" + _INLINE_UV_TAIL
    while (position := body.find(uv_descriptor, cursor)) >= 0:
        base = position + len(uv_descriptor)
        record = _parse_support_uv_payload(body, base, base)
        if record is not None:
            _store_unique_record(
                support_uv,
                ambiguous_support_uv,
                record.attribute,
                record,
            )
        cursor = position + 1
    cursor = 0
    while (position := body.find(b"\x5a", cursor)) >= 0:
        record = _parse_intersection_data_record(body, position)
        if record is not None:
            _store_unique_record(
                intersections,
                ambiguous_intersections,
                record.attribute,
                record,
            )
        cursor = position + 1
    for attribute, record in b_surfaces.items():
        if attribute in tables.surfaces:
            continue
        surface = _resolve_nurbs_surface(
            record,
            nurbs_surfaces,
            surface_data,
            float_arrays,
            short_arrays,
        )
        if surface is not None:
            tables.surfaces[attribute] = surface
    for attribute, record in b_curves.items():
        if attribute in tables.curves:
            continue
        curve = _resolve_nurbs_curve(
            record,
            nurbs_curves,
            curve_data,
            float_arrays,
            short_arrays,
        )
        if curve is not None:
            tables.curves[attribute] = curve
    for attribute, record in intersections.items():
        if attribute in tables.curves:
            continue
        curve = _resolve_intersection_curve(
            body,
            record,
            charts,
            terms,
            support_uv,
            compact_support_uv,
            tables.surfaces,
        )
        if curve is not None:
            tables.curves[attribute] = curve
    for attribute, record in trimmed_curves.items():
        if attribute in tables.curves:
            continue
        curve = _resolve_trimmed_curve(record, tables.curves)
        if curve is not None:
            tables.curves[attribute] = curve
    tables.loops = {
        record.attribute: record
        for record in loop_candidates
        if record.references[2] in tables.bridges
        and (first := tables.coedges.get(record.references[1])) is not None
        and first.references[1] == record.attribute
    }
    return tables


def _store_unique_record(
    target: dict[int, object],
    ambiguous: set[int],
    attribute: int,
    record: object,
) -> None:
    if attribute in ambiguous:
        return
    if attribute in target:
        del target[attribute]
        ambiguous.add(attribute)
        return
    target[attribute] = record


def _record_start(data: bytes, offset: int, kind: int) -> int | None:
    if data[offset : offset + 2] != bytes((0, kind)):
        return None
    start = offset + 2
    if start < len(data) and data[start] == 0xFF:
        start += 1
    return start


def _u16(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 2 > len(data):
        return None
    return struct.unpack_from(">H", data, offset)[0]


def _u32(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 4 > len(data):
        return None
    return struct.unpack_from(">I", data, offset)[0]


def _xmt(data: bytes, offset: int) -> tuple[int, int] | None:
    if offset < 0 or offset + 2 > len(data):
        return None
    first = struct.unpack_from(">h", data, offset)[0]
    if first >= 0:
        return first, 2
    if first == -32768 or offset + 4 > len(data):
        return None
    quotient = _u16(data, offset + 2)
    if quotient is None:
        return None
    return quotient * 32767 + abs(first), 4


def _xmt_sequence(
    data: bytes, offset: int, count: int
) -> tuple[tuple[int, ...], int] | None:
    values = []
    cursor = offset
    for _ in range(count):
        decoded = _xmt(data, cursor)
        if decoded is None:
            return None
        value, width = decoded
        values.append(value)
        cursor += width
    return tuple(values), cursor


def _parse_b_surface_record(data: bytes, offset: int) -> _BSurfaceRecord | None:
    start = _record_start(data, offset, 0x7C)
    if start is None:
        return None
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    state = _u32(data, cursor)
    if attribute <= 1 or state is None:
        return None
    cursor += 4
    header = _xmt_sequence(data, cursor, 5)
    if header is None:
        return None
    header_references, cursor = header
    if cursor >= len(data) or data[cursor] not in {0x2B, 0x2D}:
        return None
    sense = data[cursor] == 0x2B
    construction = _xmt_sequence(data, cursor + 1, 2)
    if construction is None:
        return None
    references, cursor = construction
    native_layout = header_references[0] == 1 and all(
        value >= 1 for value in header_references
    )
    compact_layout = (
        state == 1
        and header_references == (0, 0, 0, 0, 0)
        and sense
        and references[1] == 0
    )
    if references[0] <= 1 or not (native_layout or compact_layout):
        return None
    return _BSurfaceRecord(
        attribute,
        state,
        header_references,
        references[0],
        references[1],
        sense,
        offset,
        data[offset:cursor],
    )


def _parse_nurbs_surface_record(data: bytes, offset: int) -> _NurbsSurfaceRecord | None:
    start = _record_start(data, offset, 0x7E)
    if start is None:
        return None
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    if attribute <= 1:
        return None
    if data[cursor : cursor + 12] == bytes(12):
        references = _xmt_sequence(data, cursor + 12, 5)
        if references is None or any(value <= 1 for value in references[0]):
            return None
        values, end = references
        return _NurbsSurfaceRecord(
            attribute,
            (False, False),
            (0, 0),
            (0, 0),
            (0, 0),
            (0, 0),
            False,
            (False, False),
            0,
            0,
            values,
            "compact",
            offset,
            data[offset:end],
        )
    if cursor + 30 > len(data):
        return None
    periodic_values = data[cursor : cursor + 2]
    degrees = (_u16(data, cursor + 2), _u16(data, cursor + 4))
    counts = (_u32(data, cursor + 6), _u32(data, cursor + 10))
    knot_types = (data[cursor + 14], data[cursor + 15])
    knot_counts = (_u32(data, cursor + 16), _u32(data, cursor + 20))
    rational_value = data[cursor + 24]
    closed_values = data[cursor + 25 : cursor + 27]
    surface_form = data[cursor + 27]
    vertex_dimension = _u16(data, cursor + 28)
    references = _xmt_sequence(data, cursor + 30, 5)
    if (
        any(value not in {0, 1} for value in periodic_values)
        or any(value is None for value in degrees)
        or any(value is None for value in counts)
        or any(value is None for value in knot_counts)
        or rational_value not in {0, 1}
        or any(value not in {0, 1} for value in closed_values)
        or vertex_dimension not in {3, 4}
        or references is None
    ):
        return None
    degree_u, degree_v = degrees
    count_u, count_v = counts
    knot_count_u, knot_count_v = knot_counts
    if (
        degree_u is None
        or degree_v is None
        or count_u is None
        or count_v is None
        or knot_count_u is None
        or knot_count_v is None
        or degree_u < 1
        or degree_v < 1
        or count_u <= degree_u
        or count_v <= degree_v
        or count_u > 1_000_000
        or count_v > 1_000_000
        or count_u * count_v > 1_000_000
        or not 2 <= knot_count_u <= 1_000_000
        or not 2 <= knot_count_v <= 1_000_000
        or (vertex_dimension == 4) != bool(rational_value)
        or any(value <= 1 for value in references[0])
    ):
        return None
    values, end = references
    return _NurbsSurfaceRecord(
        attribute,
        tuple(bool(value) for value in periodic_values),
        (degree_u, degree_v),
        (count_u, count_v),
        knot_types,
        (knot_count_u, knot_count_v),
        bool(rational_value),
        tuple(bool(value) for value in closed_values),
        surface_form,
        vertex_dimension,
        values,
        "extended",
        offset,
        data[offset:end],
    )


def _parse_surface_data_record(data: bytes, offset: int) -> _SurfaceDataRecord | None:
    start = _record_start(data, offset, 0x7D)
    if start is None:
        return None
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    fixed_end = cursor + 77
    if attribute <= 1 or fixed_end > len(data):
        return None
    values = struct.unpack_from(">8d", data, cursor)
    if any(not math.isfinite(value) for value in values):
        return None
    intervals = tuple((values[index], values[index + 1]) for index in range(0, 8, 2))
    self_intersection = data[cursor + 64]
    flags = data[cursor + 65 : fixed_end]
    references = _xmt_sequence(data, fixed_end, 4)
    if references is None or any(value < 1 for value in references[0]):
        return None
    values, end = references
    return _SurfaceDataRecord(
        attribute,
        intervals,
        self_intersection,
        flags,
        values,
        offset,
        data[offset:end],
    )


def _parse_b_curve_record(data: bytes, offset: int) -> _BCurveRecord | None:
    start = _record_start(data, offset, 0x86)
    if start is None:
        return None
    if start == offset + 2:
        compact_attribute = _u16(data, start)
        compact_descriptor = _u16(data, start + 2)
        compact_end = start + 12
        if (
            compact_attribute is not None
            and compact_descriptor is not None
            and compact_attribute > 1
            and compact_descriptor > 1
            and compact_end <= len(data)
            and data[start + 4 : compact_end] == bytes(8)
        ):
            return _BCurveRecord(
                compact_attribute,
                0,
                (0, 0, 0, 0, 0),
                compact_descriptor,
                0,
                True,
                "compact",
                offset,
                data[offset:compact_end],
            )
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    if attribute <= 1:
        return None
    state = _u32(data, cursor)
    if state is None:
        return None
    header = _xmt_sequence(data, cursor + 4, 5)
    if header is None:
        return None
    header_references, cursor = header
    if header_references[0] != 1 or any(value < 1 for value in header_references):
        return None
    if cursor >= len(data) or data[cursor] not in {0x2B, 0x2D}:
        return None
    sense = data[cursor] == 0x2B
    construction = _xmt_sequence(data, cursor + 1, 2)
    if construction is None:
        return None
    references, end = construction
    if references[0] <= 1 or references[1] < 1:
        return None
    return _BCurveRecord(
        attribute,
        state,
        header_references,
        references[0],
        references[1],
        sense,
        "extended",
        offset,
        data[offset:end],
    )


def _parse_nurbs_curve_record(data: bytes, offset: int) -> _NurbsCurveRecord | None:
    start = _record_start(data, offset, 0x88)
    if start is None:
        return None
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    if attribute <= 1 or cursor + 17 > len(data):
        return None
    degree = _u16(data, cursor)
    control_count = _u32(data, cursor + 2)
    vertex_dimension = _u16(data, cursor + 6)
    knot_count = _u32(data, cursor + 8)
    knot_type = data[cursor + 12]
    periodic_value = data[cursor + 13]
    closed_value = data[cursor + 14]
    rational_value = data[cursor + 15]
    curve_form = data[cursor + 16]
    references = _xmt_sequence(data, cursor + 17, 3)
    if (
        degree is None
        or control_count is None
        or vertex_dimension not in {3, 4}
        or knot_count is None
        or periodic_value not in {0, 1}
        or closed_value not in {0, 1}
        or rational_value not in {0, 1}
        or references is None
        or degree < 1
        or control_count <= degree
        or control_count > 1_000_000
        or not 2 <= knot_count <= 1_000_000
        or (vertex_dimension == 4) != bool(rational_value)
        or any(value <= 1 for value in references[0])
    ):
        return None
    values, end = references
    return _NurbsCurveRecord(
        attribute,
        degree,
        control_count,
        vertex_dimension,
        knot_count,
        knot_type,
        bool(periodic_value),
        bool(closed_value),
        bool(rational_value),
        curve_form,
        values,
        offset,
        data[offset:end],
    )


def _parse_curve_data_record(data: bytes, offset: int) -> _CurveDataRecord | None:
    start = _record_start(data, offset, 0x87)
    if start is None:
        return None
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    if attribute <= 1 or cursor >= len(data):
        return None
    self_intersection = data[cursor]
    analytic_form = _xmt(data, cursor + 1)
    if analytic_form is None or analytic_form[0] < 1:
        return None
    reference, reference_width = analytic_form
    end = cursor + 1 + reference_width
    return _CurveDataRecord(
        attribute,
        self_intersection,
        reference,
        offset,
        data[offset:end],
    )


def _parse_trimmed_curve_record(data: bytes, offset: int) -> _TrimmedCurveRecord | None:
    start = _record_start(data, offset, 0x85)
    if start is None:
        return None
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    state = _u32(data, cursor)
    if attribute <= 1 or state is None:
        return None
    header = _xmt_sequence(data, cursor + 4, 5)
    if header is None:
        return None
    header_references, cursor = header
    if header_references[0] != 1 or any(value < 1 for value in header_references):
        return None
    if cursor >= len(data) or data[cursor] not in {0x2B, 0x2D}:
        return None
    sense = data[cursor] == 0x2B
    basis = _xmt(data, cursor + 1)
    if basis is None or basis[0] <= 1:
        return None
    basis_reference, basis_width = basis
    values_offset = cursor + 1 + basis_width
    end = values_offset + 64
    if end > len(data):
        return None
    point_1 = _point_vector(data, values_offset)
    point_2 = _point_vector(data, values_offset + 24)
    parameters = struct.unpack_from(">2d", data, values_offset + 48)
    if (
        point_1 is None
        or point_2 is None
        or any(not math.isfinite(value) for value in parameters)
    ):
        return None
    return _TrimmedCurveRecord(
        attribute,
        state,
        header_references,
        basis_reference,
        (point_1, point_2),
        parameters,
        sense,
        offset,
        data[offset:end],
    )


def _array_record_fields(
    data: bytes, offset: int, kind: int
) -> tuple[int, int, int] | None:
    if data[offset : offset + 2] != bytes((0, kind)):
        return None
    cursor = offset + 2
    if cursor < len(data) and data[cursor] in {0x2B, 0x2D}:
        cursor += 1
    if cursor < len(data) and data[cursor] == 0xFF:
        cursor += 1
    count = _u32(data, cursor)
    decoded = _xmt(data, cursor + 4)
    if count is None or decoded is None or not 1 <= count <= 1_000_000:
        return None
    attribute, width = decoded
    if attribute <= 1:
        return None
    return attribute, count, cursor + 4 + width


def _parse_float_array_record(
    data: bytes, offset: int, kind: int
) -> _FloatArrayRecord | None:
    fields = _array_record_fields(data, offset, kind)
    if fields is None:
        return None
    attribute, count, values_offset = fields
    end = values_offset + count * 8
    if end > len(data):
        return None
    values = struct.unpack_from(f">{count}d", data, values_offset)
    if any(not math.isfinite(value) for value in values):
        return None
    return _FloatArrayRecord(
        attribute,
        kind,
        values,
        offset,
        data[offset:end],
    )


def _parse_short_array_record(data: bytes, offset: int) -> _ShortArrayRecord | None:
    fields = _array_record_fields(data, offset, 0x7F)
    if fields is None:
        return None
    attribute, count, values_offset = fields
    end = values_offset + count * 2
    if end > len(data):
        return None
    values = struct.unpack_from(f">{count}H", data, values_offset)
    if any(value == 0 for value in values):
        return None
    return _ShortArrayRecord(attribute, values, offset, data[offset:end])


def _compact_nurbs_surface_shape(
    control_count: int,
    u_multiplicities: Sequence[int],
    v_multiplicities: Sequence[int],
) -> tuple[int, int, int, int, int] | None:
    candidates = []
    u_sum = sum(u_multiplicities)
    v_sum = sum(v_multiplicities)
    for dimension in (3, 4):
        if control_count % dimension:
            continue
        pole_count = control_count // dimension
        for degree_u in range(1, 9):
            count_u = u_sum - degree_u - 1
            if count_u <= degree_u:
                continue
            for degree_v in range(1, 9):
                count_v = v_sum - degree_v - 1
                if count_v > degree_v and count_u * count_v == pole_count:
                    candidates.append((count_u, count_v, degree_u, degree_v, dimension))
    return candidates[0] if len(candidates) == 1 else None


def _resolve_nurbs_surface(
    record: _BSurfaceRecord,
    descriptors: Mapping[int, _NurbsSurfaceRecord],
    surface_data: Mapping[int, _SurfaceDataRecord],
    float_arrays: Mapping[int, _FloatArrayRecord],
    short_arrays: Mapping[int, _ShortArrayRecord],
) -> NurbsSurface | None:
    descriptor = descriptors.get(record.descriptor_reference)
    data_record = (
        surface_data.get(record.data_reference) if record.data_reference > 1 else None
    )
    if (
        descriptor is None
        or len(set(descriptor.references)) != 5
        or (record.data_reference > 1 and data_record is None)
    ):
        return None
    control = float_arrays.get(descriptor.references[0])
    u_multiplicities = short_arrays.get(descriptor.references[1])
    v_multiplicities = short_arrays.get(descriptor.references[2])
    u_knots = float_arrays.get(descriptor.references[3])
    v_knots = float_arrays.get(descriptor.references[4])
    if (
        control is None
        or control.kind != 0x2D
        or u_multiplicities is None
        or v_multiplicities is None
        or u_knots is None
        or u_knots.kind != 0x80
        or v_knots is None
        or v_knots.kind != 0x80
        or len(u_multiplicities.values) != len(u_knots.values)
        or len(v_multiplicities.values) != len(v_knots.values)
        or any(
            left >= right
            for values in (u_knots.values, v_knots.values)
            for left, right in zip(values, values[1:])
        )
    ):
        return None
    if descriptor.layout == "compact":
        inferred = _compact_nurbs_surface_shape(
            len(control.values),
            u_multiplicities.values,
            v_multiplicities.values,
        )
        if inferred is None:
            return None
        count_u, count_v, degree_u, degree_v, dimension = inferred
        periodic = (False, False)
        closed = (False, False)
        rational = dimension == 4
        knot_types = (0, 0)
        knot_counts = (len(u_knots.values), len(v_knots.values))
        surface_form = 0
    else:
        count_u, count_v = descriptor.counts
        degree_u, degree_v = descriptor.degrees
        dimension = descriptor.vertex_dimension
        periodic = descriptor.periodic
        closed = descriptor.closed
        rational = descriptor.rational
        knot_types = descriptor.knot_types
        knot_counts = descriptor.knot_counts
        surface_form = descriptor.surface_form
    if (
        len(control.values) != count_u * count_v * dimension
        or len(u_knots.values) != knot_counts[0]
        or len(v_knots.values) != knot_counts[1]
        or sum(u_multiplicities.values) != count_u + degree_u + 1
        or sum(v_multiplicities.values) != count_v + degree_v + 1
    ):
        return None
    points = []
    weights = []
    for pole in (
        control.values[index : index + dimension]
        for index in range(0, len(control.values), dimension)
    ):
        weight = pole[3] if rational else 1.0
        if not math.isfinite(weight) or weight <= 0.0:
            return None
        coordinates = tuple(value / weight / _LENGTH_SCALE for value in pole[:3])
        if any(not math.isfinite(value) for value in coordinates):
            return None
        points.append(Vector3(*coordinates))
        if rational:
            weights.append(weight)
    rows = tuple(
        tuple(points[index * count_v : (index + 1) * count_v])
        for index in range(count_u)
    )
    weight_rows = (
        tuple(
            tuple(weights[index * count_v : (index + 1) * count_v])
            for index in range(count_u)
        )
        if rational
        else ()
    )
    attributes = frozen_mapping(
        {
            "state": record.state,
            "sense": record.sense,
            "header_references": record.header_references,
            "descriptor_reference": record.descriptor_reference,
            "data_reference": record.data_reference,
            "descriptor_layout": descriptor.layout,
            "degrees": (degree_u, degree_v),
            "counts": (count_u, count_v),
            "periodic": periodic,
            "knot_types": knot_types,
            "knot_counts": knot_counts,
            "array_references": descriptor.references,
            "rational": rational,
            "closed": closed,
            "surface_form": surface_form,
            "vertex_dimension": dimension,
            "surface_data_intervals": (
                data_record.intervals if data_record is not None else ()
            ),
            "surface_data_self_intersection": (
                data_record.self_intersection if data_record is not None else 0
            ),
            "surface_data_flags": data_record.flags if data_record is not None else b"",
            "surface_data_references": (
                data_record.references if data_record is not None else ()
            ),
            "surface_record": record.raw,
            "descriptor_record": descriptor.raw,
            "surface_data_record": data_record.raw if data_record is not None else b"",
            "control_record": control.raw,
            "u_multiplicity_record": u_multiplicities.raw,
            "v_multiplicity_record": v_multiplicities.raw,
            "u_knot_record": u_knots.raw,
            "v_knot_record": v_knots.raw,
        }
    )
    return NurbsSurface(
        _native_id("surface", record.attribute),
        degree_u,
        degree_v,
        rows,
        u_knots.values,
        v_knots.values,
        u_multiplicities.values,
        v_multiplicities.values,
        weight_rows,
        periodic[0],
        periodic[1],
        attributes=attributes,
    )


def _resolve_nurbs_curve(
    record: _BCurveRecord,
    descriptors: Mapping[int, _NurbsCurveRecord],
    curve_data: Mapping[int, _CurveDataRecord],
    float_arrays: Mapping[int, _FloatArrayRecord],
    short_arrays: Mapping[int, _ShortArrayRecord],
) -> NurbsCurve | None:
    descriptor = descriptors.get(record.descriptor_reference)
    data_record = (
        curve_data.get(record.data_reference) if record.data_reference > 1 else None
    )
    if (
        descriptor is None
        or len(set(descriptor.references)) != 3
        or (record.data_reference > 1 and data_record is None)
    ):
        return None
    control = float_arrays.get(descriptor.references[0])
    multiplicities = short_arrays.get(descriptor.references[1])
    knots = float_arrays.get(descriptor.references[2])
    if (
        control is None
        or control.kind != 0x2D
        or multiplicities is None
        or knots is None
        or knots.kind != 0x80
        or len(control.values) != descriptor.control_count * descriptor.vertex_dimension
        or len(multiplicities.values) != descriptor.knot_count
        or len(knots.values) != descriptor.knot_count
        or sum(multiplicities.values)
        != descriptor.control_count + descriptor.degree + 1
        or any(left >= right for left, right in zip(knots.values, knots.values[1:]))
    ):
        return None
    points = []
    weights = []
    dimension = descriptor.vertex_dimension
    for pole in (
        control.values[index : index + dimension]
        for index in range(0, len(control.values), dimension)
    ):
        weight = pole[3] if descriptor.rational else 1.0
        if not math.isfinite(weight) or weight <= 0.0:
            return None
        coordinates = tuple(value / weight / _LENGTH_SCALE for value in pole[:3])
        if any(not math.isfinite(value) for value in coordinates):
            return None
        points.append(Vector3(*coordinates))
        if descriptor.rational:
            weights.append(weight)
    attributes = frozen_mapping(
        {
            "state": record.state,
            "sense": record.sense,
            "header_references": record.header_references,
            "descriptor_reference": record.descriptor_reference,
            "data_reference": record.data_reference,
            "carrier_layout": record.layout,
            "control_count": descriptor.control_count,
            "vertex_dimension": descriptor.vertex_dimension,
            "knot_count": descriptor.knot_count,
            "knot_type": descriptor.knot_type,
            "closed": descriptor.closed,
            "rational": descriptor.rational,
            "curve_form": descriptor.curve_form,
            "array_references": descriptor.references,
            "curve_data_self_intersection": (
                data_record.self_intersection if data_record is not None else 0
            ),
            "analytic_form_reference": (
                data_record.analytic_form_reference if data_record is not None else 0
            ),
            "curve_record": record.raw,
            "descriptor_record": descriptor.raw,
            "curve_data_record": data_record.raw if data_record is not None else b"",
            "control_record": control.raw,
            "multiplicity_record": multiplicities.raw,
            "knot_record": knots.raw,
        }
    )
    return NurbsCurve(
        _native_id("curve", record.attribute),
        descriptor.degree,
        tuple(points),
        knots.values,
        multiplicities.values,
        tuple(weights),
        descriptor.periodic,
        attributes=attributes,
    )


def _resolve_trimmed_curve(
    record: _TrimmedCurveRecord, curves: Mapping[int, object]
) -> object | None:
    basis = curves.get(record.basis_reference)
    if (
        not record.sense
        or record.attribute == record.basis_reference
        or not isinstance(
            basis,
            (LineCurve, CircleCurve, EllipseCurve, NurbsCurve, IntersectionCurve),
        )
    ):
        return None
    parameter_1, parameter_2 = record.parameters
    basis_sense = basis.attributes.get("sense", True)
    if type(basis_sense) is not bool:
        return None
    if (basis_sense and parameter_2 <= parameter_1) or (
        not basis_sense and parameter_2 >= parameter_1
    ):
        return None
    if isinstance(basis, LineCurve):
        periodic = False
        closed = False
    else:
        domain = _curve_parameter_domain(basis)
        if domain is None:
            return None
        lower, upper, periodic, closed = domain
        epsilon = max(abs(lower), abs(upper), 1.0) * 1e-12
        if periodic:
            if (
                parameter_1 < lower - epsilon
                or parameter_1 > upper + epsilon
                or abs(parameter_2 - parameter_1) > upper - lower + epsilon
            ):
                return None
        elif (
            parameter_1 < lower - epsilon
            or parameter_1 > upper + epsilon
            or parameter_2 < lower - epsilon
            or parameter_2 > upper + epsilon
        ):
            return None
    evaluation_parameters = (
        (
            parameter_1 / _LENGTH_SCALE,
            parameter_2 / _LENGTH_SCALE,
        )
        if isinstance(basis, LineCurve)
        else record.parameters
    )
    evaluated = tuple(
        _curve_point_at_parameter(basis, parameter)
        for parameter in evaluation_parameters
    )
    tolerance = (
        max(basis.tolerance, 1e-7) if isinstance(basis, IntersectionCurve) else 1e-7
    )
    if any(value is None for value in evaluated) or any(
        _distance(value, point) > tolerance
        for value, point in zip(evaluated, record.points)
        if value is not None
    ):
        return None
    if not periodic and not closed and _distance(*record.points) <= tolerance:
        return None
    attributes = dict(basis.attributes)
    attributes.update(
        {
            "trimmed": True,
            "sense": record.sense,
            "basis_sense": basis_sense,
            "state": record.state,
            "header_references": record.header_references,
            "basis_reference": record.basis_reference,
            "basis_curve_id": basis.id,
            "trim_points": record.points,
            "trim_parameters": evaluation_parameters,
            "trim_parameters_native": record.parameters,
            "trim_record": record.raw,
        }
    )
    return replace(
        basis,
        id=_native_id("curve", record.attribute),
        attributes=frozen_mapping(attributes),
    )


def _parse_intersection_fields(
    data: bytes, offset: int, start: int
) -> _IntersectionRecord | None:
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    cursor = start + width
    if attribute <= 1 or _u32(data, cursor) is None:
        return None
    cursor += 4
    header = _xmt_sequence(data, cursor, 5)
    if header is None:
        return None
    header_references, cursor = header
    if header_references[0] != 1 or any(value < 1 for value in header_references):
        return None
    if cursor >= len(data) or data[cursor] not in {0x2B, 0x2D}:
        return None
    sense = data[cursor] == 0x2B
    cursor += 1
    construction = _xmt_sequence(data, cursor, 6)
    if construction is None:
        return None
    references, cursor = construction
    if (
        any(value < 1 for value in references)
        or references[0] <= 1
        or references[1] <= 1
        or references[2] <= 1
    ):
        return None
    return _IntersectionRecord(
        attribute,
        header_references,
        references,
        sense,
        offset,
        data[offset:cursor],
    )


def _parse_intersection_record(data: bytes, offset: int) -> _IntersectionRecord | None:
    start = _record_start(data, offset, 0x26)
    return (
        _parse_intersection_fields(data, offset, start) if start is not None else None
    )


def _parse_intersection_data_record(
    data: bytes, offset: int
) -> _IntersectionRecord | None:
    if offset < 0 or offset >= len(data) or data[offset] != 0x5A:
        return None
    descriptor = b"intersection_data"
    lower = max(0, offset - 96)
    position = data.rfind(descriptor, lower, offset)
    if position < 0 or offset - position - len(descriptor) > 64:
        return None
    return _parse_intersection_fields(data, offset, offset + 1)


def _point_vector(data: bytes, offset: int) -> Vector3 | None:
    if offset < 0 or offset + 24 > len(data):
        return None
    values = struct.unpack_from(">3d", data, offset)
    if any(not math.isfinite(value) for value in values):
        return None
    scaled = tuple(value / _LENGTH_SCALE for value in values)
    return Vector3(*scaled) if all(math.isfinite(value) for value in scaled) else None


def _parse_chart_record(data: bytes, offset: int) -> _ChartRecord | None:
    start = _record_start(data, offset, 0x28)
    if start is None:
        return None
    count = _u32(data, start)
    decoded = _xmt(data, start + 4)
    if count is None or not 2 <= count <= 1024 or decoded is None:
        return None
    attribute, width = decoded
    preamble = start + 4 + width
    if attribute <= 1 or preamble + 52 > len(data):
        return None
    base_parameter = struct.unpack_from(">d", data, preamble)[0]
    base_scale = struct.unpack_from(">d", data, preamble + 8)[0]
    chart_count = _u32(data, preamble + 16)
    chordal_error = struct.unpack_from(">d", data, preamble + 20)[0]
    angular_error = struct.unpack_from(">d", data, preamble + 28)[0]
    parameter_errors = struct.unpack_from(">2d", data, preamble + 36)
    if (
        chart_count != count
        or not all(
            math.isfinite(value)
            for value in (
                base_parameter,
                base_scale,
                chordal_error,
                angular_error,
                *parameter_errors,
            )
        )
        or base_scale <= 0.0
        or chordal_error <= 0.0
        or parameter_errors != (_MISSING_PARAMETER, _MISSING_PARAMETER)
    ):
        return None
    block = preamble + 52
    extended = _parse_extended_chart_points(data, block, count)
    if extended is not None:
        points, parameters, tangents, support_uv, end = extended
        layout = "ext11"
    else:
        compact = _parse_compact_chart_points(
            data,
            block,
            count,
            base_parameter,
            base_scale,
        )
        if compact is None:
            return None
        points, parameters, end = compact
        tangents = ()
        support_uv = ((), ())
        layout = "xyz3"
    return _ChartRecord(
        attribute,
        base_parameter,
        base_scale,
        chordal_error / _LENGTH_SCALE,
        angular_error,
        parameter_errors,
        points,
        parameters,
        tangents,
        support_uv,
        layout,
        offset,
        data[offset:end],
    )


def _parse_extended_chart_points(data: bytes, offset: int, count: int) -> (
    tuple[
        tuple[Vector3, ...],
        tuple[float, ...],
        tuple[Vector3, ...],
        tuple[tuple[tuple[float, float], ...], ...],
        int,
    ]
    | None
):
    end = offset + count * 88
    if end > len(data):
        return None
    points = []
    parameters = []
    tangents = []
    first_uv = []
    second_uv = []
    for index in range(count):
        cursor = offset + index * 88
        point = _point_vector(data, cursor)
        values = struct.unpack_from(">8d", data, cursor + 24)
        parameter = struct.unpack_from(">d", data, cursor + 80)[0]
        tangent_values = values[4:7]
        tangent_length = math.sqrt(sum(value * value for value in tangent_values))
        if (
            point is None
            or not all(math.isfinite(value) for value in (*values, parameter))
            or abs(tangent_length - 1.0) > 1e-9
        ):
            return None
        points.append(point)
        parameters.append(parameter)
        tangents.append(Vector3(*tangent_values))
        first_uv.append((values[0], values[2]))
        second_uv.append((values[1], values[3]))
    if not _ordered_chart(points, parameters):
        return None
    return (
        tuple(points),
        tuple(parameters),
        tuple(tangents),
        (tuple(first_uv), tuple(second_uv)),
        end,
    )


def _parse_compact_chart_points(
    data: bytes,
    offset: int,
    count: int,
    base_parameter: float,
    base_scale: float,
) -> tuple[tuple[Vector3, ...], tuple[float, ...], int] | None:
    end = offset + count * 24
    if end > len(data):
        return None
    points = tuple(_point_vector(data, offset + index * 24) for index in range(count))
    if any(point is None for point in points):
        return None
    typed_points = tuple(point for point in points if point is not None)
    parameters = [base_parameter]
    for left, right in zip(typed_points, typed_points[1:]):
        chord = _distance(left, right) * _LENGTH_SCALE
        if chord <= 0.0:
            return None
        parameters.append(parameters[-1] + chord * base_scale)
    if not _ordered_chart(typed_points, tuple(parameters)):
        return None
    return typed_points, tuple(parameters), end


def _ordered_chart(points: Sequence[Vector3], parameters: Sequence[float]) -> bool:
    return (
        len(points) >= 2
        and len(points) == len(parameters)
        and all(left < right for left, right in zip(parameters, parameters[1:]))
        and all(_distance(left, right) > 0.0 for left, right in zip(points, points[1:]))
    )


def _parse_term_payload(data: bytes, start: int, offset: int) -> _TermRecord | None:
    count = _u32(data, start)
    decoded = _xmt(data, start + 4)
    if count is None or decoded is None:
        return None
    attribute, width = decoded
    payload = start + 4 + width
    if payload + 26 > len(data):
        return None
    form_bytes = data[payload : payload + 2]
    if not (
        (count == 1 and form_bytes == b"L?")
        or (count == 2 and form_bytes in {b"TF", b"TS"})
    ):
        return None
    point = _point_vector(data, payload + 2)
    if attribute <= 1 or point is None:
        return None
    end = payload + 26
    return _TermRecord(
        attribute,
        count,
        form_bytes.decode("ascii"),
        point,
        offset,
        data[offset:end],
    )


def _parse_term_record(data: bytes, offset: int) -> _TermRecord | None:
    start = _record_start(data, offset, 0x29)
    return _parse_term_payload(data, start, offset) if start is not None else None


def _parse_support_uv_payload(
    data: bytes, start: int, offset: int
) -> _SupportUvRecord | None:
    count = _u32(data, start)
    decoded = _xmt(data, start + 4)
    if count is None or count > 4096 or decoded is None:
        return None
    attribute, width = decoded
    payload = start + 4 + width
    if payload >= len(data):
        return None
    marker = data[payload]
    stride = 4 if marker == 4 else 2
    if marker not in {2, 3, 4} or count < stride * 2 or count % stride:
        return None
    values_offset = payload + 1
    end = values_offset + count * 8
    if attribute <= 1 or end > len(data):
        return None
    values = struct.unpack_from(f">{count}d", data, values_offset)
    if any(not math.isfinite(value) for value in values):
        return None
    return _SupportUvRecord(attribute, marker, values, offset, data[offset:end])


def _parse_support_uv_record(data: bytes, offset: int) -> _SupportUvRecord | None:
    start = _record_start(data, offset, 0xCC)
    return _parse_support_uv_payload(data, start, offset) if start is not None else None


def _parse_compact_support_uv_record(
    data: bytes, offset: int
) -> _CompactSupportUvRecord | None:
    if offset < 0 or offset + 5 > len(data) or data[offset] != 0:
        return None
    count = data[offset + 1]
    start = offset + 2
    decoded = _xmt(data, start)
    if decoded is None:
        return None
    attribute, width = decoded
    marker_offset = start + width
    if attribute <= 1 or marker_offset >= len(data):
        return None
    marker = data[marker_offset]
    stride = 4 if marker == 4 else 2
    values_offset = marker_offset + 1
    end = values_offset + count * 8
    if (
        marker not in {2, 3, 4}
        or count < stride * 2
        or count % stride
        or end > len(data)
    ):
        return None
    values = struct.unpack_from(f">{count}d", data, values_offset)
    if any(not math.isfinite(value) for value in values):
        return None
    return _CompactSupportUvRecord(
        attribute,
        marker,
        values,
        offset,
        data[offset:end],
    )


def _support_uv_lanes(
    marker: int, values: Sequence[float]
) -> tuple[tuple[tuple[float, float], ...], ...] | None:
    width = 4 if marker == 4 else 2
    if len(values) < width * 2 or len(values) % width:
        return None
    first = tuple(
        (values[index], values[index + 1]) for index in range(0, len(values), width)
    )
    second = (
        tuple(
            (values[index + 2], values[index + 3]) for index in range(0, len(values), 4)
        )
        if marker == 4
        else ()
    )
    return first, second


def _resolved_support_uv(
    attribute: int,
    records: Mapping[int, _SupportUvRecord],
    compact_records: Mapping[int, _CompactSupportUvRecord],
) -> tuple[tuple[tuple[tuple[float, float], ...], ...], int, bytes] | None:
    if attribute <= 1:
        return ((), ()), 0, b""
    candidates = []
    record = records.get(attribute)
    if record is not None:
        lanes = _support_uv_lanes(record.marker, record.values)
        if lanes is not None:
            candidates.append((lanes, record.marker, record.raw))
    compact = compact_records.get(attribute)
    if compact is not None:
        lanes = _support_uv_lanes(compact.marker, compact.values)
        if lanes is not None:
            candidates.append((lanes, compact.marker, compact.raw))
    if not candidates:
        return None
    first = candidates[0]
    if any(candidate[:2] != first[:2] for candidate in candidates[1:]):
        return None
    return first


def _resolve_intersection_curve(
    data: bytes,
    record: _IntersectionRecord,
    charts: Mapping[int, _ChartRecord],
    terms: Mapping[int, _TermRecord],
    support_uv: Mapping[int, _SupportUvRecord],
    compact_support_uv: Mapping[int, _CompactSupportUvRecord],
    surfaces: Mapping[int, object],
) -> IntersectionCurve | None:
    first_surface, second_surface, chart_id, start_id, end_id, uv_id = record.references
    chart = charts.get(chart_id)
    first = surfaces.get(first_surface)
    second = surfaces.get(second_surface)
    if (
        chart is None
        or first is None
        or second is None
        or first_surface == second_surface
    ):
        return None
    limits: tuple[_TermRecord, ...]
    if start_id == 1 and end_id == 1:
        limits = ()
    elif start_id > 1 and end_id > 1:
        start = terms.get(start_id)
        end = terms.get(end_id)
        if start is None or end is None:
            return None
        tolerance = max(chart.chordal_error, 1e-7)
        if (
            _distance(start.point, chart.points[0]) > tolerance
            or _distance(end.point, chart.points[-1]) > tolerance
        ):
            return None
        limits = start, end
    else:
        return None
    resolved_uv = _resolved_support_uv(
        uv_id,
        support_uv,
        compact_support_uv,
    )
    if resolved_uv is None:
        return None
    uv_lanes, uv_marker, uv_raw = resolved_uv
    tolerance = max(chart.chordal_error, 1e-7)
    for index, surface in enumerate((first, second)):
        if isinstance(surface, NurbsSurface):
            candidate_lanes = tuple(
                lanes[index]
                for lanes in (uv_lanes, chart.support_uv)
                if index < len(lanes) and len(lanes[index]) == len(chart.points)
            )
            if not candidate_lanes or not any(
                all(
                    (residual := _surface_residual(surface, point, parameters))
                    is not None
                    and residual <= tolerance
                    for point, parameters in zip(chart.points, lane)
                )
                for lane in candidate_lanes
            ):
                return None
        else:
            residuals = tuple(
                _surface_residual(surface, point) for point in chart.points
            )
            if any(residual is None or residual > tolerance for residual in residuals):
                return None
    attributes = frozen_mapping(
        {
            "base_parameter": chart.base_parameter,
            "base_scale": chart.base_scale,
            "chart_layout": chart.layout,
            "chart_parameters": chart.parameters,
            "chart_tangents": chart.tangents,
            "chart_support_uv": chart.support_uv,
            "support_uv": uv_lanes,
            "support_uv_marker": uv_marker,
            "sense": record.sense,
            "limit_forms": tuple(limit.form for limit in limits),
            "limit_points": tuple(limit.point for limit in limits),
            "chordal_error": chart.chordal_error,
            "angular_error": chart.angular_error,
            "parameter_errors": chart.parameter_errors,
            "header_references": record.header_references,
            "references": record.references,
            "intersection_record": record.raw,
            "chart_record": chart.raw,
            "limit_records": tuple(limit.raw for limit in limits),
            "support_uv_record": uv_raw,
        }
    )
    return IntersectionCurve(
        _native_id("curve", record.attribute),
        _native_id("surface", first_surface),
        _native_id("surface", second_surface),
        chart.points,
        chart.chordal_error,
        attributes=attributes,
    )


def _nurbs_basis(
    degree: int,
    count: int,
    knots: Sequence[float],
    multiplicities: Sequence[int],
    parameter: float,
    periodic: bool,
) -> tuple[tuple[int, float], ...] | None:
    if not math.isfinite(parameter):
        return None
    expanded = tuple(
        knot
        for knot, multiplicity in zip(knots, multiplicities)
        for _ in range(multiplicity)
    )
    if len(expanded) != count + degree + 1:
        return None
    lower = expanded[degree]
    upper = expanded[count]
    if not math.isfinite(lower) or not math.isfinite(upper) or lower >= upper:
        return None
    epsilon = max(abs(lower), abs(upper), 1.0) * 1e-12
    if periodic and (parameter < lower - epsilon or parameter > upper + epsilon):
        parameter = lower + (parameter - lower) % (upper - lower)
    elif parameter < lower - epsilon or parameter > upper + epsilon:
        return None
    parameter = min(upper, max(lower, parameter))
    if parameter == upper:
        span = count - 1
    else:
        span = degree
        while span + 1 < count and parameter >= expanded[span + 1]:
            span += 1
    values = [0.0] * (degree + 1)
    left = [0.0] * (degree + 1)
    right = [0.0] * (degree + 1)
    values[0] = 1.0
    for column in range(1, degree + 1):
        left[column] = parameter - expanded[span + 1 - column]
        right[column] = expanded[span + column] - parameter
        saved = 0.0
        for row in range(column):
            denominator = right[row + 1] + left[column - row]
            ratio = values[row] / denominator if denominator else 0.0
            values[row] = saved + right[row + 1] * ratio
            saved = left[column - row] * ratio
        values[column] = saved
    basis = tuple(
        (span - degree + index, value)
        for index, value in enumerate(values)
        if value != 0.0
    )
    return basis if basis else None


def _nurbs_curve_point(curve: NurbsCurve, parameter: float) -> Vector3 | None:
    basis = _nurbs_basis(
        curve.degree,
        len(curve.control_points),
        curve.knots,
        curve.multiplicities,
        parameter,
        curve.periodic,
    )
    if basis is None:
        return None
    x_value = 0.0
    y_value = 0.0
    z_value = 0.0
    denominator = 0.0
    for index, value in basis:
        weight = curve.weights[index] if curve.weights else 1.0
        coefficient = value * weight
        point = curve.control_points[index]
        denominator += coefficient
        x_value += point.x * coefficient
        y_value += point.y * coefficient
        z_value += point.z * coefficient
    if not math.isfinite(denominator) or denominator <= 0.0:
        return None
    values = (
        x_value / denominator,
        y_value / denominator,
        z_value / denominator,
    )
    return Vector3(*values) if all(math.isfinite(value) for value in values) else None


def _curve_parameter_domain(
    curve: object,
) -> tuple[float, float, bool, bool] | None:
    if isinstance(curve, (CircleCurve, EllipseCurve)):
        return 0.0, math.tau, True, True
    if isinstance(curve, NurbsCurve):
        expanded = tuple(
            knot
            for knot, multiplicity in zip(curve.knots, curve.multiplicities)
            for _ in range(multiplicity)
        )
        count = len(curve.control_points)
        if len(expanded) != count + curve.degree + 1:
            return None
        closed = curve.attributes.get("closed", curve.periodic)
        if type(closed) is not bool:
            return None
        return expanded[curve.degree], expanded[count], curve.periodic, closed
    if isinstance(curve, IntersectionCurve):
        parameters = curve.attributes.get("chart_parameters")
        if (
            not isinstance(parameters, tuple)
            or len(parameters) < 2
            or not all(
                type(value) is float and math.isfinite(value) for value in parameters
            )
            or not all(left < right for left, right in zip(parameters, parameters[1:]))
        ):
            return None
        return parameters[0], parameters[-1], False, False
    return None


def _curve_point_at_parameter(curve: object, parameter: float) -> Vector3 | None:
    if isinstance(curve, LineCurve):
        return _line_point(curve, parameter)
    if isinstance(curve, (CircleCurve, EllipseCurve)):
        return _conic_point(curve, parameter)
    if isinstance(curve, NurbsCurve):
        return _nurbs_curve_point(curve, parameter)
    if isinstance(curve, IntersectionCurve):
        parameters = curve.attributes.get("chart_parameters")
        if not isinstance(parameters, tuple) or len(parameters) != len(curve.samples):
            return None
        tolerance = max(abs(parameter), 1.0) * 1e-12
        matches = tuple(
            point
            for value, point in zip(parameters, curve.samples)
            if type(value) is float and abs(value - parameter) <= tolerance
        )
        return matches[0] if len(matches) == 1 else None
    return None


def _nurbs_surface_point(
    surface: NurbsSurface, parameters: tuple[float, float]
) -> Vector3 | None:
    rows = surface.control_points
    if not rows or not rows[0]:
        return None
    basis_u = _nurbs_basis(
        surface.degree_u,
        len(rows),
        surface.knots_u,
        surface.multiplicities_u,
        parameters[0],
        surface.periodic_u,
    )
    basis_v = _nurbs_basis(
        surface.degree_v,
        len(rows[0]),
        surface.knots_v,
        surface.multiplicities_v,
        parameters[1],
        surface.periodic_v,
    )
    if basis_u is None or basis_v is None:
        return None
    x_value = 0.0
    y_value = 0.0
    z_value = 0.0
    denominator = 0.0
    for u_index, u_value in basis_u:
        for v_index, v_value in basis_v:
            weight = surface.weights[u_index][v_index] if surface.weights else 1.0
            coefficient = u_value * v_value * weight
            point = rows[u_index][v_index]
            denominator += coefficient
            x_value += point.x * coefficient
            y_value += point.y * coefficient
            z_value += point.z * coefficient
    if not math.isfinite(denominator) or denominator <= 0.0:
        return None
    values = (
        x_value / denominator,
        y_value / denominator,
        z_value / denominator,
    )
    return Vector3(*values) if all(math.isfinite(value) for value in values) else None


def _surface_residual(
    surface: object,
    point: Vector3,
    parameters: tuple[float, float] | None = None,
) -> float | None:
    if isinstance(surface, PlaneSurface):
        return abs(_dot(_subtract(point, surface.origin), surface.normal))
    if isinstance(surface, NurbsSurface):
        evaluated = (
            _nurbs_surface_point(surface, parameters)
            if parameters is not None
            else None
        )
        return _distance(evaluated, point) if evaluated is not None else None
    center = surface.center if hasattr(surface, "center") else surface.origin
    difference = _subtract(point, center)
    if isinstance(surface, SphereSurface):
        return abs(math.sqrt(_dot(difference, difference)) - surface.radius)
    if not isinstance(surface, (CylinderSurface, ConeSurface, TorusSurface)):
        return None
    axial = _dot(difference, surface.axis)
    radial_vector = Vector3(
        difference.x - axial * surface.axis.x,
        difference.y - axial * surface.axis.y,
        difference.z - axial * surface.axis.z,
    )
    radial = math.sqrt(_dot(radial_vector, radial_vector))
    if isinstance(surface, CylinderSurface):
        return abs(radial - surface.radius)
    if isinstance(surface, ConeSurface):
        return abs(radial - (surface.radius - axial * math.tan(surface.half_angle)))
    return abs(math.hypot(radial - surface.major_radius, axial) - surface.minor_radius)


def _refs(data: bytes, offset: int, count: int) -> tuple[int, ...] | None:
    if offset < 0 or offset + count * 2 > len(data):
        return None
    return struct.unpack_from(f">{count}H", data, offset)


def _tripled_refs(
    data: bytes, offset: int, count: int, prefix: bool = False
) -> tuple[int, ...] | None:
    values = []
    for index in range(count):
        position = offset + index * 3
        if prefix:
            if position + 3 > len(data) or data[position] != 1:
                return None
            value = _u16(data, position + 1)
        else:
            if position + 3 > len(data) or data[position + 2] != 1:
                return None
            value = _u16(data, position)
        if value is None:
            return None
        values.append(value)
    return tuple(values)


def _parse_bridge(
    data: bytes,
    offset: int,
    allow_null_owner: bool = False,
) -> _TopologyRecord | None:
    start = _record_start(data, offset, 0x0E)
    if start is None:
        return None
    attribute = _u16(data, start)
    owner = _u16(data, start + 6)
    if (
        data[start + 8 : start + 9] == b"\x01"
        and data[start + 9 : start + 17] == _ENTITY_MAGIC
    ):
        references = _tripled_refs(data, start + 17, 5)
        marker_offset = start + 32
    elif data[start + 8 : start + 16] == _ENTITY_MAGIC:
        tripled = all(
            data[start + 18 + index * 3 : start + 19 + index * 3] == b"\x01"
            for index in range(5)
        )
        references = (
            _tripled_refs(data, start + 16, 5)
            if tripled
            else _refs(data, start + 16, 5)
        )
        marker_offset = start + (31 if tripled else 26)
    else:
        return None
    if attribute is None or owner is None or references is None:
        return None
    if marker_offset >= len(data) or data[marker_offset] not in {0x2B, 0x2D}:
        return None
    if attribute <= 1 or (owner <= 1 and not allow_null_owner):
        return None
    trailing = _refs(data, marker_offset + 1, 5)
    if trailing is not None:
        references += trailing
    return _TopologyRecord(
        attribute,
        references,
        offset,
        data[marker_offset] == 0x2D,
        owner,
    )


def _parse_loop(data: bytes, offset: int) -> _TopologyRecord | None:
    start = _record_start(data, offset, 0x0F)
    if start is None:
        return None
    attribute = _u16(data, start)
    references = _tripled_refs(data, start + 6, 4) or _refs(data, start + 6, 4)
    if attribute is None or attribute <= 1 or references is None:
        return None
    return _TopologyRecord(attribute, references, offset)


def _parse_edge_use(data: bytes, offset: int) -> _TopologyRecord | None:
    start = _record_start(data, offset, 0x10)
    if start is None:
        return None
    attribute = _u16(data, start)
    if data[start + 8 : start + 16] == _ENTITY_MAGIC:
        references = _refs(data, start + 16, 6)
    else:
        magic = next(
            (
                position
                for position in range(
                    start + 9,
                    min(start + 17, len(data) - len(_ENTITY_MAGIC) + 1),
                )
                if data[position : position + len(_ENTITY_MAGIC)] == _ENTITY_MAGIC
            ),
            None,
        )
        if magic is None:
            return None
        cursor = magic + len(_ENTITY_MAGIC)
        decoded = []
        if cursor < len(data) and data[cursor] == 1:
            while cursor + 3 <= len(data) and data[cursor] == 1 and len(decoded) < 8:
                value = _u16(data, cursor + 1)
                if value is None:
                    return None
                decoded.append(value)
                cursor += 3
        else:
            while (
                cursor + 3 <= len(data) and data[cursor + 2] == 1 and len(decoded) < 8
            ):
                value = _u16(data, cursor)
                if value is None:
                    return None
                decoded.append(value)
                cursor += 3
        if len(decoded) < 3:
            return None
        references = (0, 0, 0, decoded[2], 0, 0)
    if attribute is None or attribute <= 1 or references is None:
        return None
    return _TopologyRecord(attribute, references, offset)


def _parse_coedge(data: bytes, offset: int) -> _TopologyRecord | None:
    start = _record_start(data, offset, 0x11)
    if start is None:
        return None
    attribute = _u16(data, start)
    references = _refs(data, start + 2, 9)
    marker_offset = start + 20
    marker = data[marker_offset] if marker_offset < len(data) else -1
    isolated = (
        attribute is not None
        and references is not None
        and marker == 0x3F
        and _isolated_fin(attribute, references)
    )
    if references is None or (marker not in {0x2B, 0x2D} and not isolated):
        references = _tripled_refs(data, start + 2, 9)
        marker_offset = start + 29
        marker = data[marker_offset] if marker_offset < len(data) else -1
        isolated = (
            attribute is not None
            and references is not None
            and marker == 0x3F
            and _isolated_fin(attribute, references)
        )
    if attribute is None or attribute <= 1 or references is None:
        return None
    if marker not in {0x2B, 0x2D} and not isolated:
        return None
    return _TopologyRecord(
        attribute,
        references,
        offset,
        marker == 0x2D,
        isolated=isolated,
    )


def _isolated_fin(attribute: int, references: tuple[int, ...]) -> bool:
    return (
        len(references) == 9
        and references[0] <= 1
        and references[1] > 1
        and references[2] == attribute
        and references[3] == attribute
        and references[4] > 1
        and all(references[index] <= 1 for index in (5, 6, 7, 8))
    )


def _parse_vertex_use(data: bytes, offset: int) -> _TopologyRecord | None:
    start = _record_start(data, offset, 0x12)
    if start is None:
        return None
    attribute = _u16(data, start)
    tolerance = 0.0
    if data[start + 16 : start + 24] == _ENTITY_MAGIC:
        references = _refs(data, start + 6, 5)
    elif start + 24 <= len(data):
        direct = _refs(data, start + 6, 5)
        value = struct.unpack_from(">d", data, start + 16)[0]
        if direct is not None and math.isfinite(value) and value >= 0.0:
            references = direct
            tolerance = value / _LENGTH_SCALE
        else:
            references = None
    else:
        references = None
    if references is None:
        magic = next(
            (
                position
                for position in range(
                    start + 21,
                    min(start + 33, len(data) - len(_ENTITY_MAGIC) + 1),
                )
                if data[position : position + len(_ENTITY_MAGIC)] == _ENTITY_MAGIC
            ),
            None,
        )
        if magic is None or (magic - (start + 6)) % 3:
            return None
        count = (magic - (start + 6)) // 3
        if count < 5:
            return None
        references = _tripled_refs(data, start + 6, count)
    if (
        attribute is None
        or attribute <= 1
        or references is None
        or not references
        or references[0] > 1
        or len(references) < 5
        or references[4] <= 1
        or not math.isfinite(tolerance)
    ):
        return None
    return _TopologyRecord(attribute, references, offset, tolerance=tolerance)


def _point_record_fields(
    data: bytes, offset: int, prefixed: bool = False
) -> tuple[int, tuple[int, ...], int] | None:
    start = _record_start(data, offset, 0x1D)
    if start is None or start + 38 > len(data):
        return None
    attribute = _u16(data, start)
    if prefixed:
        values = []
        cursor = start + 6
        while cursor + 3 <= len(data) and data[cursor + 2] == 1 and len(values) < 16:
            value = _u16(data, cursor)
            if value is None:
                return None
            values.append(value)
            cursor += 3
        if not values:
            return None
        references = tuple(values)
        values_offset = cursor
    else:
        references = _refs(data, start + 6, 4)
        values_offset = start + 14
    if attribute is None or attribute <= 1 or references is None:
        return None
    if not references or references[0] > 1:
        return None
    if values_offset + 24 > len(data):
        return None
    return attribute, references, values_offset


def _parse_point(
    data: bytes, offset: int, prefixed: bool = False
) -> _TopologyRecord | None:
    fields = _point_record_fields(data, offset, prefixed)
    if fields is None:
        return None
    attribute, references, values_offset = fields
    values = struct.unpack_from(">3d", data, values_offset)
    if any(not math.isfinite(value) or abs(value) > 10_000 for value in values):
        return None
    return _TopologyRecord(
        attribute,
        references,
        offset,
        point=Vector3(*(value / _LENGTH_SCALE for value in values)),
    )


_ANALYTIC_VALUE_COUNTS = {
    0x1E: 6,
    0x1F: 10,
    0x20: 11,
    0x32: 9,
    0x33: 10,
    0x34: 12,
    0x35: 10,
    0x36: 11,
}


def _analytic_record_fields(
    data: bytes, offset: int
) -> tuple[int, int, int, int] | None:
    if offset < 0 or offset + 2 > len(data):
        return None
    kind = data[offset + 1]
    value_count = _ANALYTIC_VALUE_COUNTS.get(kind)
    if value_count is None:
        return None
    start = _record_start(data, offset, kind)
    if start is None:
        return None
    attribute = _u16(data, start)
    marker_offset = start + 16
    if marker_offset >= len(data) or data[marker_offset] not in {0x2B, 0x2D}:
        marker_offset = next(
            (
                position
                for position in range(start + 8, min(start + 64, len(data)))
                if data[position] in {0x2B, 0x2D}
                and position > 0
                and data[position - 1] == 1
            ),
            -1,
        )
        if marker_offset < 0:
            return None
    values_offset = marker_offset + 1
    values_end = values_offset + value_count * 8
    if attribute is None or attribute <= 1 or values_end > len(data):
        return None
    if data[marker_offset] not in {0x2B, 0x2D}:
        return None
    return attribute, values_offset, values_end, marker_offset


def _parse_analytic_carrier(data: bytes, offset: int) -> tuple[int, object] | None:
    kind = data[offset + 1]
    value_count = _ANALYTIC_VALUE_COUNTS[kind]
    fields = _analytic_record_fields(data, offset)
    if fields is None:
        return None
    attribute, values_offset, values_end, marker_offset = fields
    values = struct.unpack_from(f">{value_count}d", data, values_offset)
    if any(not math.isfinite(value) or abs(value) > 1_000_000 for value in values):
        return None
    identifier = _native_id("curve" if kind < 0x32 else "surface", attribute)
    geometry = _analytic_geometry(kind, identifier, values)
    if geometry is not None:
        geometry = replace(
            geometry,
            attributes=frozen_mapping(
                {
                    "sense": data[marker_offset] == 0x2B,
                    "carrier_record": data[offset:values_end],
                }
            ),
        )
    return (attribute, geometry) if geometry is not None else None


def _analytic_geometry(
    kind: int, identifier: str, values: tuple[float, ...]
) -> object | None:
    def point(index: int = 0) -> Vector3:
        return Vector3(
            values[index] / _LENGTH_SCALE,
            values[index + 1] / _LENGTH_SCALE,
            values[index + 2] / _LENGTH_SCALE,
        )

    def direction(index: int) -> Vector3 | None:
        value = Vector3(values[index], values[index + 1], values[index + 2])
        return _validated_direction(value)

    if kind == 0x1E:
        tangent = direction(3)
        return LineCurve(identifier, point(), tangent) if tangent is not None else None
    if kind in {0x1F, 0x20, 0x32}:
        axis = direction(3)
        reference = direction(6)
        if axis is None or reference is None or not _orthogonal(axis, reference):
            return None
        if kind == 0x1F and values[9] > 0:
            return CircleCurve(
                identifier,
                point(),
                axis,
                reference,
                values[9] / _LENGTH_SCALE,
            )
        if kind == 0x20 and values[9] >= values[10] > 0:
            return EllipseCurve(
                identifier,
                point(),
                axis,
                reference,
                values[9] / _LENGTH_SCALE,
                values[10] / _LENGTH_SCALE,
            )
        if kind == 0x32:
            return PlaneSurface(identifier, point(), axis, reference)
        return None
    if kind == 0x33:
        axis = direction(3)
        reference = direction(7)
        if (
            axis is None
            or reference is None
            or not _orthogonal(axis, reference)
            or values[6] <= 0
        ):
            return None
        return CylinderSurface(
            identifier,
            point(),
            axis,
            reference,
            values[6] / _LENGTH_SCALE,
        )
    if kind == 0x34:
        axis = direction(3)
        reference = direction(9)
        sine, cosine = values[7:9]
        if (
            axis is None
            or reference is None
            or not _orthogonal(axis, reference)
            or values[6] < 0
            or sine == 0
            or cosine <= 0
            or abs(sine * sine + cosine * cosine - 1.0) > 1e-9
        ):
            return None
        return ConeSurface(
            identifier,
            point(),
            axis,
            reference,
            values[6] / _LENGTH_SCALE,
            math.asin(sine),
        )
    if kind == 0x35:
        axis = direction(4)
        reference = direction(7)
        if (
            axis is None
            or reference is None
            or not _orthogonal(axis, reference)
            or values[3] <= 0
        ):
            return None
        return SphereSurface(
            identifier,
            point(),
            axis,
            reference,
            values[3] / _LENGTH_SCALE,
        )
    if kind == 0x36:
        axis = direction(3)
        reference = direction(8)
        if (
            axis is None
            or reference is None
            or not _orthogonal(axis, reference)
            or values[6] == 0
            or values[7] <= 0
        ):
            return None
        return TorusSurface(
            identifier,
            point(),
            axis,
            reference,
            abs(values[6]) / _LENGTH_SCALE,
            values[7] / _LENGTH_SCALE,
        )
    return None


def _validated_direction(value: Vector3) -> Vector3 | None:
    length = math.sqrt(value.x * value.x + value.y * value.y + value.z * value.z)
    if not math.isfinite(length) or abs(length - 1.0) > 1e-9:
        return None
    return Vector3(value.x / length, value.y / length, value.z / length)


def _orthogonal(left: Vector3, right: Vector3) -> bool:
    return abs(left.x * right.x + left.y * right.y + left.z * right.z) <= 1e-9


def _parse_entity(data: bytes, offset: int) -> _EntityRecord | None:
    start = _record_start(data, offset, 0x51)
    if start is None:
        return None
    flags = _u32(data, start)
    attribute = _u16(data, start + 4)
    sequence = _u32(data, start + 6)
    discriminator = _u16(data, start + 10)
    references = _refs(data, start + 12, 6)
    if (
        flags not in {1, 2}
        or attribute is None
        or attribute <= 1
        or sequence != 1
        or discriminator is None
        or references is None
    ):
        return None
    return _EntityRecord(flags, attribute, discriminator, references, offset)


def _linked_subset_order(
    attributes: Iterable[int],
    links: Mapping[int, tuple[int, int]],
) -> tuple[int, ...]:
    selected = set(attributes)
    linked = selected.intersection(links)
    if not linked:
        return tuple(sorted(selected))
    ordered: list[int] = []
    visited: set[int] = set()
    heads = sorted(
        attribute
        for attribute, (_, previous) in links.items()
        if previous <= 1 or previous not in links
    )
    for head in heads:
        attribute = head
        previous = 0
        component: set[int] = set()
        while attribute > 1 and attribute in links:
            if attribute in component or attribute in visited:
                break
            next_attribute, previous_attribute = links[attribute]
            if previous and previous_attribute != previous:
                break
            component.add(attribute)
            visited.add(attribute)
            ordered.append(attribute)
            previous = attribute
            attribute = next_attribute
    result = tuple(attribute for attribute in ordered if attribute in linked)
    if len(result) != len(linked):
        result = tuple(sorted(linked))
    return result + tuple(sorted(selected - linked))


def _geometry_chain_links(values: Mapping[int, object]) -> dict[int, tuple[int, int]]:
    result: dict[int, tuple[int, int]] = {}
    for attribute, geometry in values.items():
        attributes = getattr(geometry, "attributes", {})
        header = attributes.get("header_references")
        if (
            isinstance(header, tuple)
            and len(header) >= 4
            and all(type(value) is int for value in header[:4])
        ):
            result[attribute] = header[3], header[2]
            continue
        raw = attributes.get("carrier_record")
        if not isinstance(raw, bytes) or len(raw) < 16:
            continue
        next_attribute = _u16(raw, 12)
        previous_attribute = _u16(raw, 14)
        if next_attribute is not None and previous_attribute is not None:
            result[attribute] = next_attribute, previous_attribute
    return result


def _fin_descriptor(
    attribute: int,
    used_coedges: set[int],
    used_edges: set[int],
    tables: _RecordTables,
) -> tuple[str, str] | None:
    if attribute in used_coedges:
        return "coedge", _native_id("coedge", attribute)
    fin = tables.coedges.get(attribute)
    if fin is None or fin.references[6] not in used_edges:
        return None
    return "dummy", _native_id("edge", fin.references[6])


def _vertex_fin_order(
    vertex_attribute: int,
    first_attribute: int,
    used_coedges: set[int],
    used_edges: set[int],
    tables: _RecordTables,
) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    seen: set[int] = set()
    attribute = first_attribute
    while attribute > 1:
        if attribute in seen:
            return ()
        seen.add(attribute)
        fin = tables.coedges.get(attribute)
        if fin is None or fin.references[4] != vertex_attribute:
            return ()
        descriptor = _fin_descriptor(attribute, used_coedges, used_edges, tables)
        if descriptor is None:
            return ()
        result.append(descriptor)
        attribute = fin.references[8]
    return tuple(result)


def _build_partition_model(
    tables: _RecordTables,
    solidworks_unchanged_ids: Mapping[int, int] | None = None,
    solidworks_attribute_orders: Mapping[str, Mapping[int, int]] | None = None,
) -> BrepModel:
    unchanged_ids = solidworks_unchanged_ids or {}
    attribute_orders = solidworks_attribute_orders or {}
    face_loops: dict[int, tuple[tuple[int, tuple[int, ...]], ...]] = {}
    edge_endpoints: dict[int, tuple[int, int]] = {}
    edge_curves: dict[int, int] = {}
    coedge_edges: dict[int, int] = {}
    used_coedges: set[int] = set()
    used_edges: set[int] = set()
    used_vertices: set[int] = set()
    used_points: set[int] = set()
    used_curves: set[int] = set()
    used_surfaces: set[int] = set()
    synthetic_vertices: dict[int, Vector3] = {}
    synthetic_curves: dict[int, NativeCurve] = {}
    vertex_tolerances: dict[int, float] = {}
    owner_faces: dict[int, int] = {}
    for bridge_attribute, bridge in sorted(tables.bridges.items()):
        if bridge.owner > 1:
            if bridge.owner in owner_faces:
                raise ValueError("ambiguous face owner")
            owner_faces[bridge.owner] = bridge_attribute
        surface_attribute = bridge.references[4]
        if surface_attribute not in tables.surfaces:
            raise ValueError("unresolved face surface")
        used_surfaces.add(surface_attribute)
        loop_attribute = bridge.references[2]
        loops: list[tuple[int, tuple[int, ...]]] = []
        loop_guard: set[int] = set()
        while loop_attribute > 1:
            if loop_attribute in loop_guard:
                raise ValueError("cyclic loop list")
            loop_guard.add(loop_attribute)
            loop = tables.loops.get(loop_attribute)
            if loop is None or loop.references[2] != bridge_attribute:
                raise ValueError("invalid loop owner")
            ring = _walk_coedge_ring(tables, loop_attribute, loop.references[1])
            loops.append((loop_attribute, ring))
            loop_attribute = loop.references[3]
        if not loops:
            raise ValueError("face boundary is absent")
        face_loops[bridge_attribute] = tuple(loops)
        for _, ring in loops:
            for coedge_attribute in ring:
                coedge = tables.coedges[coedge_attribute]
                if coedge.isolated:
                    if len(ring) != 1 or not _isolated_fin(
                        coedge.attribute, coedge.references
                    ):
                        raise ValueError("invalid isolated vertex loop")
                    edge_attribute = 0x10000 + coedge_attribute
                    curve_attribute = edge_attribute
                    vertex_attribute = coedge.references[4]
                    edge_endpoints[edge_attribute] = (
                        vertex_attribute,
                        vertex_attribute,
                    )
                    edge_curves[edge_attribute] = curve_attribute
                    coedge_edges[coedge_attribute] = edge_attribute
                    synthetic_curves[curve_attribute] = NativeCurve(
                        _native_id("curve", curve_attribute),
                        "parasolid.xt",
                        "isolated-vertex-loop",
                    )
                    used_coedges.add(coedge_attribute)
                    used_edges.add(edge_attribute)
                    used_vertices.add(vertex_attribute)
                    used_curves.add(curve_attribute)
                    continue
                edge_attribute = coedge.references[6]
                start_vertex = coedge.references[4]
                other_coedge = tables.coedges.get(coedge.references[5])
                if other_coedge is None:
                    raise ValueError("missing opposite coedge")
                end_vertex = other_coedge.references[4]
                if edge_attribute <= 1:
                    raise ValueError("incomplete coedge topology")
                edge_use = tables.edge_uses.get(edge_attribute)
                if edge_use is None:
                    raise ValueError("missing edge use")
                curve_attribute = edge_use.references[3]
                curve = tables.curves.get(curve_attribute)
                if curve is None:
                    raise ValueError("unresolved edge curve")
                if start_vertex <= 1 or end_vertex <= 1:
                    if not (
                        start_vertex <= 1
                        and end_vertex <= 1
                        and isinstance(curve, (CircleCurve, EllipseCurve))
                    ):
                        raise ValueError("incomplete coedge topology")
                    synthetic = 0x10000 + edge_attribute
                    synthetic_vertices[synthetic] = _conic_point(curve, 0.0)
                    start_vertex = synthetic
                    end_vertex = synthetic
                canonical = (
                    (end_vertex, start_vertex)
                    if coedge.reversed
                    else (start_vertex, end_vertex)
                )
                previous = edge_endpoints.setdefault(edge_attribute, canonical)
                if previous != canonical:
                    raise ValueError("inconsistent edge orientation")
                previous_curve = edge_curves.setdefault(edge_attribute, curve_attribute)
                if previous_curve != curve_attribute:
                    raise ValueError("inconsistent edge curve")
                coedge_edges[coedge_attribute] = edge_attribute
                used_coedges.add(coedge_attribute)
                used_edges.add(edge_attribute)
                used_vertices.update(canonical)
                used_curves.add(curve_attribute)
    if set(tables.bridges) != set(face_loops):
        raise ValueError("partial face topology")
    face_order = _linked_subset_order(
        face_loops,
        {
            attribute: (record.references[0], record.references[1])
            for attribute, record in tables.bridges.items()
        },
    )
    face_surface_order = _linked_subset_order(
        face_loops,
        {
            attribute: (record.references[5], record.references[6])
            for attribute, record in tables.bridges.items()
            if len(record.references) >= 7
        },
    )
    face_front_order = _linked_subset_order(
        face_loops,
        {
            attribute: (record.references[7], record.references[8])
            for attribute, record in tables.bridges.items()
            if len(record.references) >= 9
        },
    )
    edge_order = _linked_subset_order(
        used_edges,
        {
            attribute: (record.references[2], record.references[1])
            for attribute, record in tables.edge_uses.items()
        },
    )
    curve_edge_order = _linked_subset_order(
        used_edges,
        {
            attribute: (record.references[4], record.references[5])
            for attribute, record in tables.edge_uses.items()
        },
    )
    vertex_order = _linked_subset_order(
        used_vertices,
        {
            attribute: (record.references[3], record.references[2])
            for attribute, record in tables.vertex_uses.items()
        },
    )
    curve_order = _linked_subset_order(
        used_curves,
        _geometry_chain_links(tables.curves),
    )
    face_ranks = {attribute: rank for rank, attribute in enumerate(face_order)}
    face_surface_ranks = {
        attribute: rank for rank, attribute in enumerate(face_surface_order)
    }
    face_front_ranks = {
        attribute: rank for rank, attribute in enumerate(face_front_order)
    }
    edge_ranks = {attribute: rank for rank, attribute in enumerate(edge_order)}
    curve_edge_ranks = {
        attribute: rank for rank, attribute in enumerate(curve_edge_order)
    }
    vertex_ranks = {attribute: rank for rank, attribute in enumerate(vertex_order)}
    curve_ranks = {attribute: rank for rank, attribute in enumerate(curve_order)}
    points_by_vertex: dict[int, Vector3] = {}
    point_attributes: dict[int, int] = {}
    for vertex_attribute in vertex_order:
        if vertex_attribute in synthetic_vertices:
            point = synthetic_vertices[vertex_attribute]
            points_by_vertex[vertex_attribute] = point
            vertex_tolerances[vertex_attribute] = 0.0
            continue
        vertex_use = tables.vertex_uses.get(vertex_attribute)
        if vertex_use is None:
            raise ValueError("missing vertex use")
        point_attribute = vertex_use.references[4]
        point_record = tables.points.get(point_attribute)
        if point_record is None or point_record.point is None:
            raise ValueError("missing vertex point")
        used_points.add(point_attribute)
        point_attributes[vertex_attribute] = point_attribute
        points_by_vertex[vertex_attribute] = point_record.point
        vertex_tolerances[vertex_attribute] = vertex_use.tolerance
    point_order = _linked_subset_order(
        used_points,
        {
            attribute: (record.references[2], record.references[3])
            for attribute, record in tables.points.items()
            if len(record.references) >= 4
        },
    )
    point_ranks = {attribute: rank for rank, attribute in enumerate(point_order)}
    vertices: list[BrepVertex] = []
    for vertex_attribute in vertex_order:
        if vertex_attribute in synthetic_vertices:
            vertices.append(
                BrepVertex(
                    _native_id("vertex", vertex_attribute),
                    points_by_vertex[vertex_attribute],
                    attributes=frozen_mapping(
                        {"parasolid.vertex_order": vertex_ranks[vertex_attribute]}
                    ),
                )
            )
            continue
        vertex_use = tables.vertex_uses[vertex_attribute]
        point_attribute = point_attributes[vertex_attribute]
        attributes: dict[str, object] = {
            "parasolid.vertex_order": vertex_ranks[vertex_attribute],
            "parasolid.point_order": point_ranks[point_attribute],
        }
        fin_order = _vertex_fin_order(
            vertex_attribute,
            vertex_use.references[1],
            used_coedges,
            used_edges,
            tables,
        )
        if fin_order:
            attributes["parasolid.vertex_fins"] = fin_order
        vertices.append(
            BrepVertex(
                _native_id("vertex", vertex_attribute),
                points_by_vertex[vertex_attribute],
                tolerance=vertex_use.tolerance,
                attributes=frozen_mapping(attributes),
            )
        )
    curves = tuple(
        replace(
            (
                tables.curves[attribute]
                if attribute in tables.curves
                else synthetic_curves[attribute]
            ),
            attributes=frozen_mapping(
                {
                    **dict(
                        getattr(
                            (
                                tables.curves[attribute]
                                if attribute in tables.curves
                                else synthetic_curves[attribute]
                            ),
                            "attributes",
                            {},
                        )
                    ),
                    "parasolid.curve_order": curve_ranks[attribute],
                }
            ),
        )
        for attribute in curve_order
    )
    for curve in curves:
        if not isinstance(curve, IntersectionCurve):
            continue
        references = curve.attributes.get("references")
        if (
            not isinstance(references, tuple)
            or len(references) < 2
            or any(
                type(attribute) is not int or attribute not in tables.surfaces
                for attribute in references[:2]
            )
        ):
            raise ValueError("intersection support surfaces are unresolved")
        used_surfaces.update(references[:2])
    surface_order = _linked_subset_order(
        used_surfaces,
        _geometry_chain_links(tables.surfaces),
    )
    surface_ranks = {attribute: rank for rank, attribute in enumerate(surface_order)}
    edges: list[BrepEdge] = []
    for edge_attribute in edge_order:
        start_vertex, end_vertex = edge_endpoints[edge_attribute]
        curve_attribute = edge_curves[edge_attribute]
        degenerate = curve_attribute in synthetic_curves
        if degenerate:
            start_parameter, end_parameter = 0.0, 0.0
        else:
            curve = tables.curves[curve_attribute]
            start_parameter, end_parameter = _provable_curve_range(
                curve,
                points_by_vertex[start_vertex],
                points_by_vertex[end_vertex],
                vertex_tolerances[start_vertex],
                vertex_tolerances[end_vertex],
            )
        edge_attributes: dict[str, object] = {
            "parasolid.edge_order": edge_ranks[edge_attribute],
            "parasolid.curve_edge_order": curve_edge_ranks[edge_attribute],
        }
        if edge_attribute in tables.edge_uses:
            first_fin = _fin_descriptor(
                tables.edge_uses[edge_attribute].references[0],
                used_coedges,
                used_edges,
                tables,
            )
            if first_fin is not None:
                edge_attributes["parasolid.first_fin"] = first_fin
        edges.append(
            BrepEdge(
                _native_id("edge", edge_attribute),
                _native_id("vertex", start_vertex),
                _native_id("vertex", end_vertex),
                _native_id("curve", curve_attribute),
                start_parameter,
                end_parameter,
                tolerance=max(
                    vertex_tolerances[start_vertex],
                    vertex_tolerances[end_vertex],
                ),
                degenerate=degenerate,
                attributes=frozen_mapping(edge_attributes),
            )
        )
    coedges = tuple(
        BrepCoedge(
            _native_id("coedge", attribute),
            _native_id("edge", coedge_edges[attribute]),
            reversed=tables.coedges[attribute].reversed,
        )
        for attribute in sorted(used_coedges)
    )
    outer_loops: set[int] = set()
    for values in face_loops.values():
        outer_loop = next(
            (
                loop_attribute
                for loop_attribute, ring in values
                if not any(tables.coedges[value].isolated for value in ring)
            ),
            0,
        )
        if outer_loop <= 1:
            raise ValueError("face has no dimensional boundary loop")
        outer_loops.add(outer_loop)
    loops = tuple(
        BrepLoop(
            _native_id("loop", loop_attribute),
            tuple(_native_id("coedge", value) for value in ring),
            loop_attribute in outer_loops,
        )
        for values in face_loops.values()
        for loop_attribute, ring in values
    )
    surfaces = tuple(
        replace(
            tables.surfaces[attribute],
            attributes=frozen_mapping(
                {
                    **dict(getattr(tables.surfaces[attribute], "attributes", {})),
                    "parasolid.surface_order": surface_ranks[attribute],
                }
            ),
        )
        for attribute in surface_order
    )
    faces = tuple(
        BrepFace(
            _native_id("face", bridge_attribute),
            _native_id("surface", tables.bridges[bridge_attribute].references[4]),
            tuple(
                _native_id("loop", loop_attribute)
                for loop_attribute, _ in face_loops[bridge_attribute]
            ),
            not tables.bridges[bridge_attribute].reversed,
            attributes=frozen_mapping(
                {
                    **(
                        {
                            "solidworks.unchanged_id": unchanged_ids[bridge_attribute],
                        }
                        if bridge_attribute in unchanged_ids
                        else {}
                    ),
                    "parasolid.face_order": face_ranks[bridge_attribute],
                    "parasolid.surface_face_order": face_surface_ranks[
                        bridge_attribute
                    ],
                    "parasolid.front_face_order": face_front_ranks[bridge_attribute],
                    **{
                        f"solidworks.{kind}_order": ranks[bridge_attribute]
                        for kind, ranks in attribute_orders.items()
                        if bridge_attribute in ranks
                    },
                }
            ),
        )
        for bridge_attribute in face_order
    )
    try:
        hierarchy = _build_body_hierarchy(tables.entities, owner_faces, set(face_loops))
    except ValueError:
        hierarchy = _derive_body_hierarchy(face_loops, tables)
    face_uses, shells, shell_uses, regions, bodies = hierarchy
    face_rank_by_id = {
        _native_id("face", attribute): rank for attribute, rank in face_ranks.items()
    }
    face_use_by_id = {face_use.id: face_use for face_use in face_uses}
    shells = tuple(
        replace(
            shell,
            face_use_ids=tuple(
                sorted(
                    shell.face_use_ids,
                    key=lambda face_use_id: face_rank_by_id[
                        face_use_by_id[face_use_id].face_id
                    ],
                )
            ),
        )
        for shell in shells
    )
    model = BrepModel(
        curves=curves,
        surfaces=surfaces,
        vertices=tuple(vertices),
        edges=tuple(edges),
        coedges=coedges,
        loops=loops,
        faces=faces,
        face_uses=face_uses,
        shells=shells,
        shell_uses=shell_uses,
        regions=regions,
        bodies=bodies,
    )
    return model


def _walk_coedge_ring(
    tables: _RecordTables, loop_attribute: int, first_attribute: int
) -> tuple[int, ...]:
    if first_attribute <= 1:
        raise ValueError("empty coedge ring")

    def walk(link: int) -> tuple[int, ...]:
        ring: list[int] = []
        seen: set[int] = set()
        attribute = first_attribute
        while attribute not in seen:
            if len(ring) >= 1_000_000:
                raise ValueError("coedge ring exceeds record bound")
            seen.add(attribute)
            record = tables.coedges.get(attribute)
            if record is None or record.references[1] != loop_attribute:
                raise ValueError("invalid coedge owner")
            ring.append(attribute)
            attribute = record.references[link]
            if attribute <= 1:
                raise ValueError("open coedge ring")
        if attribute != first_attribute:
            raise ValueError("coedge ring joins another cycle")
        return tuple(ring)

    if not tables.v12_partition:
        return walk(3)
    candidates: list[tuple[int, ...]] = []
    for link in (2, 3):
        candidate = walk(link)
        if candidate not in candidates:
            candidates.append(candidate)
    connected = []
    for candidate in candidates:
        valid = True
        for position, attribute in enumerate(candidate):
            record = tables.coedges[attribute]
            if record.isolated and len(candidate) == 1:
                continue
            other = tables.coedges.get(record.references[5])
            following = tables.coedges[candidate[(position + 1) % len(candidate)]]
            if other is None or other.references[4] != following.references[4]:
                valid = False
                break
        if valid:
            connected.append(candidate)
    if not connected:
        raise ValueError("disconnected coedge ring")
    return connected[0]


def _provable_curve_range(
    curve: object,
    start: Vector3,
    end: Vector3,
    start_tolerance: float = 0.0,
    end_tolerance: float = 0.0,
) -> tuple[float, float]:
    trim_parameters = getattr(curve, "attributes", {}).get("trim_parameters")
    trim_points = getattr(curve, "attributes", {}).get("trim_points")
    if trim_parameters is not None or trim_points is not None:
        if (
            not isinstance(trim_parameters, tuple)
            or len(trim_parameters) != 2
            or not all(
                type(value) is float and math.isfinite(value)
                for value in trim_parameters
            )
            or not isinstance(trim_points, tuple)
            or len(trim_points) != 2
            or not all(isinstance(value, Vector3) for value in trim_points)
        ):
            raise ValueError("trimmed curve range is invalid")
        direct = _distance(start, trim_points[0]) <= max(
            start_tolerance, 1e-7
        ) and _distance(end, trim_points[1]) <= max(end_tolerance, 1e-7)
        reverse = _distance(start, trim_points[1]) <= max(
            start_tolerance, 1e-7
        ) and _distance(end, trim_points[0]) <= max(end_tolerance, 1e-7)
        if direct == reverse:
            raise ValueError("trimmed curve endpoints are not uniquely bound")
        return trim_parameters if direct else tuple(reversed(trim_parameters))
    if isinstance(curve, LineCurve):
        start_parameter = _dot(_subtract(start, curve.origin), curve.direction)
        end_parameter = _dot(_subtract(end, curve.origin), curve.direction)
        if (
            _distance(_line_point(curve, start_parameter), start) > 1e-7
            or _distance(_line_point(curve, end_parameter), end) > 1e-7
        ):
            raise ValueError("line endpoints do not lie on carrier")
        return start_parameter, end_parameter
    if isinstance(curve, (CircleCurve, EllipseCurve)):
        start_parameter = _conic_parameter(curve, start)
        end_parameter = _conic_parameter(curve, end)
        if _distance(start, end) <= 1e-7:
            return start_parameter, start_parameter + math.tau
        while end_parameter <= start_parameter:
            end_parameter += math.tau
        return start_parameter, end_parameter
    if isinstance(curve, NurbsCurve):
        domain = _curve_parameter_domain(curve)
        if domain is None:
            raise ValueError("NURBS curve domain is not provable")
        lower, upper, _, _ = domain
        lower_point = _nurbs_curve_point(curve, lower)
        upper_point = _nurbs_curve_point(curve, upper)
        if lower_point is None or upper_point is None:
            raise ValueError("NURBS curve endpoints are not evaluable")
        direct = (
            _distance(start, lower_point) <= 1e-7
            and _distance(end, upper_point) <= 1e-7
        )
        reverse = (
            _distance(start, upper_point) <= 1e-7
            and _distance(end, lower_point) <= 1e-7
        )
        if direct == reverse:
            raise ValueError("NURBS curve endpoints do not identify its range")
        return (lower, upper) if direct else (upper, lower)
    if isinstance(curve, IntersectionCurve):
        parameters = curve.attributes.get("chart_parameters")
        if (
            not isinstance(parameters, tuple)
            or len(parameters) != len(curve.samples)
            or len(parameters) < 2
            or not all(
                isinstance(value, float) and math.isfinite(value)
                for value in parameters
            )
            or not all(left < right for left, right in zip(parameters, parameters[1:]))
        ):
            raise ValueError("intersection chart parameters are not provable")
        tolerance = max(curve.tolerance, 1e-7)
        start_parameter = _intersection_chart_parameter(
            curve.samples,
            parameters,
            start,
            tolerance,
        )
        end_parameter = _intersection_chart_parameter(
            curve.samples,
            parameters,
            end,
            tolerance,
        )
        if start_parameter is None or end_parameter is None:
            raise ValueError("intersection endpoints do not identify a chart range")
        if start_parameter == end_parameter and _distance(start, end) > tolerance:
            raise ValueError("intersection chart range collapses distinct endpoints")
        return start_parameter, end_parameter
    raise ValueError("curve parameter range is not provable")


def _intersection_chart_parameter(
    samples: Sequence[Vector3],
    parameters: Sequence[float],
    point: Vector3,
    tolerance: float,
) -> float | None:
    candidates = []
    for index, (left, right) in enumerate(zip(samples, samples[1:])):
        chord = _subtract(right, left)
        length_squared = _dot(chord, chord)
        if length_squared <= 0.0:
            return None
        fraction = max(
            0.0,
            min(1.0, _dot(_subtract(point, left), chord) / length_squared),
        )
        projected = Vector3(
            left.x + chord.x * fraction,
            left.y + chord.y * fraction,
            left.z + chord.z * fraction,
        )
        distance = _distance(point, projected)
        if distance <= tolerance:
            parameter = parameters[index] + fraction * (
                parameters[index + 1] - parameters[index]
            )
            candidates.append((distance, parameter))
    if not candidates:
        return None
    candidates.sort()
    best_distance, best_parameter = candidates[0]
    parameter_span = abs(parameters[-1] - parameters[0])
    parameter_tolerance = max(parameter_span * 1e-12, 1e-12)
    for distance, parameter in candidates[1:]:
        if (
            abs(parameter - best_parameter) > parameter_tolerance
            and abs(distance - best_distance) <= 1e-12
        ):
            return None
    return best_parameter


def _line_point(curve: LineCurve, parameter: float) -> Vector3:
    return Vector3(
        curve.origin.x + curve.direction.x * parameter,
        curve.origin.y + curve.direction.y * parameter,
        curve.origin.z + curve.direction.z * parameter,
    )


def _conic_point(curve: CircleCurve | EllipseCurve, parameter: float) -> Vector3:
    normal = _cross(curve.axis, curve.reference_direction)
    major = curve.radius if isinstance(curve, CircleCurve) else curve.major_radius
    minor = curve.radius if isinstance(curve, CircleCurve) else curve.minor_radius
    return Vector3(
        curve.center.x
        + major * math.cos(parameter) * curve.reference_direction.x
        + minor * math.sin(parameter) * normal.x,
        curve.center.y
        + major * math.cos(parameter) * curve.reference_direction.y
        + minor * math.sin(parameter) * normal.y,
        curve.center.z
        + major * math.cos(parameter) * curve.reference_direction.z
        + minor * math.sin(parameter) * normal.z,
    )


def _conic_parameter(curve: CircleCurve | EllipseCurve, point: Vector3) -> float:
    difference = _subtract(point, curve.center)
    normal = _cross(curve.axis, curve.reference_direction)
    major = curve.radius if isinstance(curve, CircleCurve) else curve.major_radius
    minor = curve.radius if isinstance(curve, CircleCurve) else curve.minor_radius
    x_value = _dot(difference, curve.reference_direction) / major
    y_value = _dot(difference, normal) / minor
    parameter = math.atan2(y_value, x_value)
    if _distance(_conic_point(curve, parameter), point) > 1e-7:
        raise ValueError("conic endpoint does not lie on carrier")
    return parameter


def _subtract(left: Vector3, right: Vector3) -> Vector3:
    return Vector3(left.x - right.x, left.y - right.y, left.z - right.z)


def _dot(left: Vector3, right: Vector3) -> float:
    return left.x * right.x + left.y * right.y + left.z * right.z


def _cross(left: Vector3, right: Vector3) -> Vector3:
    return Vector3(
        left.y * right.z - left.z * right.y,
        left.z * right.x - left.x * right.z,
        left.x * right.y - left.y * right.x,
    )


def _distance(left: Vector3, right: Vector3) -> float:
    difference = _subtract(left, right)
    return math.sqrt(_dot(difference, difference))


def _derive_body_hierarchy(
    face_loops: Mapping[int, tuple[tuple[int, tuple[int, ...]], ...]],
    tables: _RecordTables,
) -> tuple[
    tuple[BrepFaceUse, ...],
    tuple[BrepShell, ...],
    tuple[BrepShellUse, ...],
    tuple[BrepRegion, ...],
    tuple[BrepBody, ...],
]:
    faces_by_edge: dict[int, set[int]] = {}
    edges_by_face: dict[int, list[int]] = {}
    for face_attribute, loops in face_loops.items():
        face_edges = []
        for _, ring in loops:
            for coedge_attribute in ring:
                coedge = tables.coedges[coedge_attribute]
                if coedge.isolated:
                    continue
                edge_attribute = coedge.references[6]
                face_edges.append(edge_attribute)
                faces_by_edge.setdefault(edge_attribute, set()).add(face_attribute)
        edges_by_face[face_attribute] = face_edges
    neighbors = {face_attribute: set() for face_attribute in face_loops}
    for face_attributes in faces_by_edge.values():
        for face_attribute in face_attributes:
            neighbors[face_attribute].update(face_attributes - {face_attribute})
    components = []
    remaining = set(face_loops)
    while remaining:
        seed = min(remaining)
        pending = [seed]
        component = set()
        while pending:
            face_attribute = pending.pop()
            if face_attribute in component:
                continue
            component.add(face_attribute)
            pending.extend(neighbors[face_attribute] - component)
        remaining -= component
        components.append(tuple(sorted(component)))
    face_uses = []
    shells = []
    shell_uses = []
    regions = []
    region_ids = []
    for index, component in enumerate(components, start=1):
        use_ids = []
        edge_counts: dict[int, int] = {}
        for face_attribute in component:
            use_id = f"sldprt:brep:face-use:derived:{face_attribute}"
            face_uses.append(BrepFaceUse(use_id, _native_id("face", face_attribute)))
            use_ids.append(use_id)
            for edge_attribute in edges_by_face[face_attribute]:
                edge_counts[edge_attribute] = edge_counts.get(edge_attribute, 0) + 1
        solid = bool(edge_counts) and all(value == 2 for value in edge_counts.values())
        shell_id = f"sldprt:brep:shell:derived:{index}"
        shell_use_id = f"sldprt:brep:shell-use:derived:{index}"
        region_id = f"sldprt:brep:region:derived:{index}"
        shells.append(BrepShell(shell_id, tuple(use_ids), solid))
        shell_uses.append(BrepShellUse(shell_use_id, shell_id))
        regions.append(BrepRegion(region_id, (shell_use_id,), solid))
        region_ids.append(region_id)
    if not region_ids:
        raise ValueError("body hierarchy is absent")
    return (
        tuple(face_uses),
        tuple(shells),
        tuple(shell_uses),
        tuple(regions),
        (BrepBody("sldprt:brep:body:derived:1", tuple(region_ids)),),
    )


def _build_body_hierarchy(
    entities: Mapping[int, _EntityRecord],
    owner_faces: Mapping[int, int],
    expected_faces: set[int],
) -> tuple[
    tuple[BrepFaceUse, ...],
    tuple[BrepShell, ...],
    tuple[BrepShellUse, ...],
    tuple[BrepRegion, ...],
    tuple[BrepBody, ...],
]:
    roots = tuple(
        entity for entity in entities.values() if entity.discriminator == 0x0017
    )
    if not roots:
        raise ValueError("body hierarchy is absent")
    assigned_faces: set[int] = set()
    face_uses: list[BrepFaceUse] = []
    shells: list[BrepShell] = []
    shell_uses: list[BrepShellUse] = []
    regions: list[BrepRegion] = []
    bodies: list[BrepBody] = []
    for root in sorted(roots, key=lambda value: value.attribute):
        region_ids: list[str] = []
        for region_attribute in _nonnull(root.references):
            region = entities.get(region_attribute)
            if region is None or region.discriminator not in {0x001B, 0x001D}:
                raise ValueError("unsupported body region hierarchy")
            solid = region.discriminator == 0x001B
            native_shells: list[tuple[int, tuple[int, ...]]] = []
            if solid:
                for lump_attribute in _nonnull(region.references):
                    lump = _require_entity(entities, lump_attribute, 0x001F)
                    shell_node = _require_entity(
                        entities, _single_reference(lump), 0x0021
                    )
                    shell_link = _require_entity(
                        entities, _single_reference(shell_node), 0x0023
                    )
                    face_owners = _face_owner_chain(
                        entities, _single_reference(shell_link), 0x0013
                    )
                    native_shells.append((lump_attribute, face_owners))
            else:
                head = _single_reference(region)
                native_shells.append(
                    (region.attribute, _face_owner_chain(entities, head, 0x0015))
                )
            shell_use_ids: list[str] = []
            for shell_attribute, face_owners in native_shells:
                if not face_owners:
                    raise ValueError("empty native shell")
                face_attributes: list[int] = []
                for owner in face_owners:
                    face_attribute = owner_faces.get(owner)
                    if face_attribute is None or face_attribute in assigned_faces:
                        raise ValueError("ambiguous shell face membership")
                    assigned_faces.add(face_attribute)
                    face_attributes.append(face_attribute)
                face_use_ids: list[str] = []
                for face_attribute in face_attributes:
                    face_use_id = _native_id("face-use", face_attribute)
                    face_uses.append(
                        BrepFaceUse(
                            face_use_id,
                            _native_id("face", face_attribute),
                        )
                    )
                    face_use_ids.append(face_use_id)
                shell_id = _native_id("shell", shell_attribute)
                shell_use_id = _native_id("shell-use", shell_attribute)
                shells.append(BrepShell(shell_id, tuple(face_use_ids), solid))
                shell_uses.append(BrepShellUse(shell_use_id, shell_id))
                shell_use_ids.append(shell_use_id)
            region_id = _native_id("region", region.attribute)
            regions.append(BrepRegion(region_id, tuple(shell_use_ids), solid))
            region_ids.append(region_id)
        if not region_ids:
            raise ValueError("empty native body")
        bodies.append(BrepBody(_native_id("body", root.attribute), tuple(region_ids)))
    if assigned_faces != expected_faces:
        raise ValueError("body hierarchy does not own every face")
    return (
        tuple(face_uses),
        tuple(shells),
        tuple(shell_uses),
        tuple(regions),
        tuple(bodies),
    )


def _nonnull(values: Sequence[int]) -> tuple[int, ...]:
    return tuple(value for value in values if value > 1)


def _single_reference(entity: _EntityRecord) -> int:
    references = _nonnull(entity.references)
    if len(references) != 1:
        raise ValueError("entity does not contain one child reference")
    return references[0]


def _require_entity(
    entities: Mapping[int, _EntityRecord], attribute: int, discriminator: int
) -> _EntityRecord:
    entity = entities.get(attribute)
    if entity is None or entity.discriminator != discriminator:
        raise ValueError("entity hierarchy discriminator mismatch")
    return entity


def _face_owner_chain(
    entities: Mapping[int, _EntityRecord], head: int, discriminator: int
) -> tuple[int, ...]:
    owners: list[int] = []
    seen: set[int] = set()
    attribute = head
    while attribute > 1:
        if attribute in seen:
            raise ValueError("cyclic face owner list")
        seen.add(attribute)
        entity = _require_entity(entities, attribute, discriminator)
        next_attribute, *values = entity.references
        owners.extend(value for value in values if value > 1)
        attribute = next_attribute
    return tuple(owners)


def _native_id(kind: str, attribute: int) -> str:
    return f"sldprt:brep:{kind}:{attribute}"
