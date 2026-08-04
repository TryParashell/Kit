# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
import math
from pathlib import PureWindowsPath
import struct

from interchange import Mesh, Provenance, ProvenanceSpan, Vector3, frozen_mapping

from .format import (
    ASSEMBLY_FORMAT_ID,
    DISPLAY_LISTS_STREAM,
    SERIALIZED_STRING_MARKER,
    is_cad_path,
    is_component_path,
)

_ARRAY_MARKER = struct.pack("<I", 4)


@dataclass(frozen=True, slots=True)
class NativeTessellationFace:
    offset: int
    record_length: int
    face_id: int
    strip_lengths: tuple[int, ...]
    positions_mm: tuple[tuple[float, float, float], ...]
    normals: tuple[tuple[float, float, float], ...]
    triangle_indices: tuple[tuple[int, int, int], ...]

    @property
    def positions(self) -> tuple[tuple[float, float, float], ...]:
        return self.positions_mm

    def triangles(self) -> tuple[tuple[int, int, int], ...]:
        return self.triangle_indices


@dataclass(frozen=True, slots=True)
class NativeDisplayComponent:
    occurrence_path: str
    source_path: str
    record_offset: int
    record_length: int
    faces: tuple[NativeTessellationFace, ...]


def decode_tessellation_faces(data: bytes) -> tuple[NativeTessellationFace, ...]:
    result: list[NativeTessellationFace] = []
    cursor = 8
    while True:
        header = data.find(_ARRAY_MARKER, cursor)
        if header < 0:
            break
        face = _decode_face(data, header - 8)
        if face is None:
            cursor = header + len(_ARRAY_MARKER)
            continue
        result.append(face)
        cursor = face.offset + face.record_length
    return tuple(result)


def decode_display_lists(data: bytes) -> tuple[NativeDisplayComponent, ...]:
    faces = decode_tessellation_faces(data)
    strings = _serialized_strings(data)
    records: list[tuple[int, str, str]] = []
    for index, (offset, value, _) in enumerate(strings):
        if not is_component_path(value):
            continue
        next_component = next(
            (
                other_offset
                for other_offset, other_value, _ in strings[index + 1 :]
                if is_component_path(other_value)
            ),
            len(data),
        )
        source_path = next(
            (
                other_value
                for other_offset, other_value, _ in strings[index + 1 :]
                if other_offset < next_component and is_cad_path(other_value)
            ),
            "",
        )
        records.append((offset, value, source_path))
    offsets = [record[0] for record in records]
    grouped: list[list[NativeTessellationFace]] = [[] for _ in records]
    for face in faces:
        index = bisect_right(offsets, face.offset) - 1
        if index >= 0:
            grouped[index].append(face)
    result: list[NativeDisplayComponent] = []
    for index, ((offset, occurrence_path, source_path), component_faces) in enumerate(
        zip(records, grouped)
    ):
        if not component_faces:
            continue
        end = records[index + 1][0] if index + 1 < len(records) else len(data)
        result.append(
            NativeDisplayComponent(
                occurrence_path=occurrence_path,
                source_path=source_path,
                record_offset=offset,
                record_length=end - offset,
                faces=tuple(component_faces),
            )
        )
    return tuple(result)


def neutral_meshes(
    components: tuple[NativeDisplayComponent, ...],
) -> tuple[Mesh, ...]:
    result: list[Mesh] = []
    for component in components:
        component_name = (
            PureWindowsPath(component.source_path).stem
            if component.source_path
            else component.occurrence_path.split("@", 1)[0]
        )
        for face in component.faces:
            mesh_id = f"sldasm:mesh:{face.offset}"
            result.append(
                Mesh(
                    id=mesh_id,
                    name=f"{component_name} face {face.face_id}",
                    vertices=tuple(Vector3(*point) for point in face.positions_mm),
                    triangles=face.triangle_indices,
                    normals=tuple(Vector3(*normal) for normal in face.normals),
                    provenance=Provenance(
                        adapter=ASSEMBLY_FORMAT_ID,
                        native_id=str(face.face_id),
                        spans=(
                            ProvenanceSpan(
                                DISPLAY_LISTS_STREAM,
                                face.offset,
                                face.record_length,
                                "tessellation-face",
                            ),
                        ),
                    ),
                    attributes=frozen_mapping(
                        {
                            "occurrence_path": component.occurrence_path,
                            "source_path": component.source_path,
                            "face_id": face.face_id,
                            "strip_lengths": face.strip_lengths,
                        }
                    ),
                )
            )
    return tuple(result)


def _decode_face(data: bytes, start: int) -> NativeTessellationFace | None:
    if start < 0 or start + 8 > len(data):
        return None
    face_id, strip_count = struct.unpack_from("<II", data, start)
    if not 0 < strip_count <= 100_000:
        return None
    channels: list[tuple[tuple[int, int, int, int], bytes]] = []
    cursor = start + 8
    for _ in range(6):
        if cursor + 16 > len(data):
            return None
        header = struct.unpack_from("<IIII", data, cursor)
        item_size, _, _, count = header
        if not 0 < item_size <= 64 or count > 10_000_000:
            return None
        payload_start = cursor + 16
        payload_end = payload_start + item_size * count
        if payload_end > len(data):
            return None
        channels.append((header, data[payload_start:payload_end]))
        cursor = payload_end
    first_header, first_data = channels[0]
    if first_header != (4, 8, 2, strip_count):
        return None
    strip_lengths = struct.unpack(f"<{strip_count}I", first_data)
    if min(strip_lengths) < 3:
        return None
    vertex_count = sum(strip_lengths)
    if vertex_count > 10_000_000:
        return None
    third_count = channels[3][0][3]
    expected_headers = (
        (4, 8, 2, strip_count),
        (12, 100, 2, vertex_count),
        (12, 100, 2, vertex_count),
        (4, 8, 2, third_count),
        (4, 8, 2, strip_count),
        (1, 8, 2, third_count),
    )
    if tuple(channel[0] for channel in channels) != expected_headers:
        return None
    position_values = struct.unpack(f"<{vertex_count * 3}f", channels[1][1])
    normal_values = struct.unpack(f"<{vertex_count * 3}f", channels[2][1])
    if not all(math.isfinite(value) for value in (*position_values, *normal_values)):
        return None
    positions_mm = _vectors(position_values, 1000.0)
    normals = _vectors(normal_values, 1.0)
    return NativeTessellationFace(
        offset=start,
        record_length=cursor - start,
        face_id=face_id,
        strip_lengths=strip_lengths,
        positions_mm=positions_mm,
        normals=normals,
        triangle_indices=_triangles(strip_lengths),
    )


def _triangles(
    strip_lengths: tuple[int, ...],
) -> tuple[tuple[int, int, int], ...]:
    result: list[tuple[int, int, int]] = []
    first = 0
    for length in strip_lengths:
        for index in range(length - 2):
            if index % 2:
                result.append((first + index + 1, first + index, first + index + 2))
            else:
                result.append((first + index, first + index + 1, first + index + 2))
        first += length
    return tuple(result)


def _vectors(
    values: tuple[float, ...], scale: float
) -> tuple[tuple[float, float, float], ...]:
    return tuple(
        (
            values[index] * scale,
            values[index + 1] * scale,
            values[index + 2] * scale,
        )
        for index in range(0, len(values), 3)
    )


def _serialized_strings(data: bytes) -> tuple[tuple[int, str, int], ...]:
    result: list[tuple[int, str, int]] = []
    cursor = 0
    while True:
        offset = data.find(SERIALIZED_STRING_MARKER, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        length_offset = offset + len(SERIALIZED_STRING_MARKER)
        if length_offset >= len(data):
            continue
        length = data[length_offset]
        string_start = length_offset + 1
        string_end = string_start + length * 2
        if string_end > len(data):
            continue
        try:
            value = data[string_start:string_end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if any(ord(character) < 0x20 for character in value):
            continue
        result.append((offset, value, string_end))
    return tuple(result)
