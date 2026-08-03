from __future__ import annotations

from dataclasses import dataclass
import math
import struct

from .container import SldprtFormatError
from .format import CLASS_MARKER

PROFILE_CLASS = "moProfileFeature_c"
LENGTH_PARAMETER_CLASS = "moLengthParameter_c"
END_SPEC_CLASS = "moEndSpec_c"
FROM_END_SPEC_CLASS = "moFromEndSpec_c"
SKETCH_CHAIN_CLASS = "moSketchChain_c"

DEPTH_RELATIVE = 57
REVERSE_RELATIVE = 27
END_CONDITION_RELATIVE = 33
FROM_REVERSE_RELATIVE = 29
RECTANGLE_POINT_RELATIVE = (283, 461, 623, 785)

BLIND_END_CONDITION = 0
MID_PLANE_END_CONDITION = 6
SUPPORTED_END_CONDITIONS = frozenset({BLIND_END_CONDITION, MID_PLANE_END_CONDITION})

_MAX_CLASS_NAME = 64
_METRES = 1000.0


@dataclass(frozen=True, slots=True)
class ClassRecord:
    offset: int
    name: str
    data_offset: int


@dataclass(frozen=True, slots=True)
class RectanglePadLayout:
    point_offsets: tuple[tuple[int, int], ...]
    depth_offset: int
    reverse_offset: int
    end_condition_offset: int
    from_reverse_offset: int | None
    corners_mm: tuple[tuple[float, float], ...]
    depth_mm: float
    reversed: bool
    end_condition_code: int

    @property
    def bounds_mm(self) -> tuple[float, float, float, float]:
        xs = tuple(point[0] for point in self.corners_mm)
        ys = tuple(point[1] for point in self.corners_mm)
        return min(xs), min(ys), max(xs), max(ys)


def class_records(data: bytes | bytearray) -> tuple[ClassRecord, ...]:
    blob = bytes(data)
    result: list[ClassRecord] = []
    cursor = 0
    while True:
        offset = blob.find(CLASS_MARKER, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        header_end = offset + len(CLASS_MARKER) + 2
        if header_end > len(blob):
            continue
        length = struct.unpack_from("<H", blob, offset + len(CLASS_MARKER))[0]
        if not 0 < length <= _MAX_CLASS_NAME:
            continue
        start = header_end
        end = start + length
        if end > len(blob):
            continue
        try:
            name = blob[start:end].decode("ascii")
        except UnicodeDecodeError:
            continue
        if not name.replace("_", "").isalnum():
            continue
        result.append(ClassRecord(offset, name, end))
    return tuple(result)


def first_class_offset(records: tuple[ClassRecord, ...], name: str) -> int | None:
    for record in records:
        if record.name == name:
            return record.offset
    return None


def _read_double(blob: bytes, offset: int) -> float | None:
    if offset < 0 or offset + 8 > len(blob):
        return None
    value = struct.unpack_from("<d", blob, offset)[0]
    if not math.isfinite(value):
        return None
    return value


def locate_rectangle_pad(data: bytes | bytearray) -> RectanglePadLayout | None:
    blob = bytes(data)
    records = class_records(blob)
    profile = first_class_offset(records, PROFILE_CLASS)
    parameter = first_class_offset(records, LENGTH_PARAMETER_CLASS)
    end_spec = first_class_offset(records, END_SPEC_CLASS)
    if profile is None or parameter is None or end_spec is None:
        return None
    point_offsets: list[tuple[int, int]] = []
    corners: list[tuple[float, float]] = []
    for relative in RECTANGLE_POINT_RELATIVE:
        x_offset = profile + relative
        y_offset = x_offset + 8
        x = _read_double(blob, x_offset)
        y = _read_double(blob, y_offset)
        if x is None or y is None:
            return None
        point_offsets.append((x_offset, y_offset))
        corners.append((x * _METRES, y * _METRES))
    depth_offset = parameter + DEPTH_RELATIVE
    depth = _read_double(blob, depth_offset)
    if depth is None or depth <= 0.0:
        return None
    reverse_offset = end_spec + REVERSE_RELATIVE
    end_condition_offset = end_spec + END_CONDITION_RELATIVE
    if end_condition_offset >= len(blob):
        return None
    from_end_spec = first_class_offset(records, FROM_END_SPEC_CLASS)
    from_reverse_offset = (
        None if from_end_spec is None else from_end_spec + FROM_REVERSE_RELATIVE
    )
    if from_reverse_offset is not None and from_reverse_offset >= len(blob):
        from_reverse_offset = None
    xs = sorted({round(point[0], 9) for point in corners})
    ys = sorted({round(point[1], 9) for point in corners})
    if len(xs) != 2 or len(ys) != 2:
        return None
    return RectanglePadLayout(
        point_offsets=tuple(point_offsets),
        depth_offset=depth_offset,
        reverse_offset=reverse_offset,
        end_condition_offset=end_condition_offset,
        from_reverse_offset=from_reverse_offset,
        corners_mm=tuple(corners),
        depth_mm=depth * _METRES,
        reversed=bool(blob[reverse_offset]),
        end_condition_code=blob[end_condition_offset],
    )


def sketch_plane_object_id(data: bytes | bytearray) -> int | None:
    blob = bytes(data)
    chain = first_class_offset(class_records(blob), SKETCH_CHAIN_CLASS)
    if chain is None:
        return None
    for offset in range(chain, min(chain + 320, len(blob) - 14)):
        candidate = struct.unpack_from("<I", blob, offset)[0]
        if candidate not in {2, 3, 4}:
            continue
        axis = struct.unpack_from("<I", blob, offset + 10)[0]
        if axis == 5 - candidate:
            return candidate
    return None


def patch_rectangle_pad(
    data: bytes | bytearray,
    *,
    minimum_x_mm: float,
    minimum_y_mm: float,
    maximum_x_mm: float,
    maximum_y_mm: float,
    depth_mm: float,
    reversed: bool = False,
    end_condition_code: int = BLIND_END_CONDITION,
) -> bytes:
    layout = locate_rectangle_pad(data)
    if layout is None:
        raise SldprtFormatError(
            "donor resolved-features stream is not a rectangular pad layout"
        )
    if end_condition_code not in SUPPORTED_END_CONDITIONS:
        raise SldprtFormatError(
            f"unsupported SOLIDWORKS end condition code {end_condition_code}"
        )
    values = (
        minimum_x_mm,
        minimum_y_mm,
        maximum_x_mm,
        maximum_y_mm,
        depth_mm,
    )
    if not all(math.isfinite(value) for value in values):
        raise SldprtFormatError("rectangular pad values must be finite")
    if maximum_x_mm <= minimum_x_mm or maximum_y_mm <= minimum_y_mm:
        raise SldprtFormatError("rectangular pad requires a positive extent")
    if depth_mm <= 0.0:
        raise SldprtFormatError("rectangular pad requires a positive depth")
    corners = (
        (minimum_x_mm, minimum_y_mm),
        (maximum_x_mm, maximum_y_mm),
        (minimum_x_mm, maximum_y_mm),
        (maximum_x_mm, minimum_y_mm),
    )
    output = bytearray(data)
    for (x_offset, y_offset), (x, y) in zip(layout.point_offsets, corners, strict=True):
        struct.pack_into("<d", output, x_offset, x / _METRES)
        struct.pack_into("<d", output, y_offset, y / _METRES)
    struct.pack_into("<d", output, layout.depth_offset, depth_mm / _METRES)
    output[layout.reverse_offset] = 1 if reversed else 0
    output[layout.end_condition_offset] = end_condition_code
    if layout.from_reverse_offset is not None:
        output[layout.from_reverse_offset] = 1 if reversed else 0
    patched = bytes(output)
    verification = locate_rectangle_pad(patched)
    if verification is None:
        raise SldprtFormatError("patched resolved-features stream cannot be relocated")
    if not _matches(verification.corners_mm, corners):
        raise SldprtFormatError("patched rectangular pad geometry does not verify")
    if not math.isclose(verification.depth_mm, depth_mm, rel_tol=1e-12, abs_tol=1e-9):
        raise SldprtFormatError("patched rectangular pad depth does not verify")
    if verification.reversed is not bool(reversed):
        raise SldprtFormatError("patched rectangular pad direction does not verify")
    if verification.end_condition_code != end_condition_code:
        raise SldprtFormatError("patched rectangular pad end condition does not verify")
    return patched


def _matches(
    actual: tuple[tuple[float, float], ...],
    expected: tuple[tuple[float, float], ...],
) -> bool:
    if len(actual) != len(expected):
        return False
    return all(
        math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-9)
        for pair, target in zip(actual, expected, strict=True)
        for left, right in zip(pair, target, strict=True)
    )
