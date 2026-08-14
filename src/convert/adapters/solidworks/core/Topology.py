# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

BOSS_OPERATION = "boss"
CUT_OPERATION = "cut"
REVOLVE_BOSS_OPERATION = "revolve-boss"
REVOLVE_CUT_OPERATION = "revolve-cut"

BLIND_END = "blind"
THROUGH_ALL_END = "through-all"
MID_PLANE_END = "mid-plane"
FULL_REVOLUTION_END = "full-revolution"

FRONT_SUPPORT = "front"
TOP_SUPPORT = "top"
RIGHT_SUPPORT = "right"
FACE_SUPPORT = "face"
SKETCH_AXIS_SUPPORT = "sketch-axis"
REFERENCE_AXIS_SUPPORT = "reference-axis"
FRONT_SKETCH_AXIS_SUPPORT = f"{FRONT_SUPPORT}-{SKETCH_AXIS_SUPPORT}"
TOP_SKETCH_AXIS_SUPPORT = f"{TOP_SUPPORT}-{SKETCH_AXIS_SUPPORT}"
RIGHT_SKETCH_AXIS_SUPPORT = f"{RIGHT_SUPPORT}-{SKETCH_AXIS_SUPPORT}"
REVOLVE_SUPPORT_BY_PLANE = MappingProxyType(
    {
        FRONT_SUPPORT: FRONT_SKETCH_AXIS_SUPPORT,
        TOP_SUPPORT: TOP_SKETCH_AXIS_SUPPORT,
        RIGHT_SUPPORT: RIGHT_SKETCH_AXIS_SUPPORT,
    }
)

RECTANGLE_PROFILE = "rectangle"
CIRCLE_PROFILE = "circle"
RECTANGLE_WITH_CIRCLE_PROFILE = "rectangle+circle"
POLYLINE_PROFILE_PREFIX = "polyline-"
ARC_PROFILE_INFIX = "-arc-"
COUNTERCLOCKWISE_SUFFIX = "-ccw"
CLOCKWISE_SUFFIX = "-cw"

SUPPORTED_END_CONDITIONS = frozenset({BLIND_END, THROUGH_ALL_END, MID_PLANE_END})
DEPTHLESS_END_CONDITIONS = frozenset({THROUGH_ALL_END})
REVOLVE_OPERATIONS = frozenset({REVOLVE_BOSS_OPERATION, REVOLVE_CUT_OPERATION})
REVOLVE_SUPPORTS = frozenset(REVOLVE_SUPPORT_BY_PLANE.values())
REVOLVE_END_CONDITIONS = frozenset({FULL_REVOLUTION_END})
FULL_REVOLUTION_DEGREES = 360.0
MAXIMUM_REVOLUTION_DEGREES = FULL_REVOLUTION_DEGREES
END_CONDITION_CODES = MappingProxyType({BLIND_END: 0, MID_PLANE_END: 6})


def arc_profile(line_count: int, arc_count: int, *, counterclockwise: bool) -> str:
    suffix = COUNTERCLOCKWISE_SUFFIX if counterclockwise else CLOCKWISE_SUFFIX
    return (
        f"{POLYLINE_PROFILE_PREFIX}{line_count}{ARC_PROFILE_INFIX}{arc_count}{suffix}"
    )


def polyline_profile(segment_count: int) -> str:
    return f"{POLYLINE_PROFILE_PREFIX}{segment_count}"


@dataclass(frozen=True, slots=True)
class FeatureTopology:
    operation: str
    profile: str
    support: str
    end_condition: str

    @property
    def key(self) -> tuple[str, str, str, str]:
        return self.operation, self.profile, self.support, self.end_condition


@dataclass(frozen=True, slots=True)
class TargetFeature:
    operation: str
    profile: str
    support: str
    end_condition: str
    points_mm: tuple[tuple[float, float], ...] = ()
    radii_mm: tuple[float, ...] = ()
    arc_centres_mm: tuple[tuple[float, float], ...] = ()
    swept_arc_centres_mm: tuple[tuple[float, float], ...] = ()
    depth_mm: float | None = None
    reversed: bool | None = None
    angle_degrees: float | None = None
    axis_direction: tuple[float, float] | None = None

    @property
    def revolve(self) -> bool:
        return self.operation in REVOLVE_OPERATIONS

    @property
    def topology(self) -> FeatureTopology:
        return FeatureTopology(
            self.operation, self.profile, self.support, self.end_condition
        )
