# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass
from types import MappingProxyType

# this binding exists because shared behavior needs one stable value
KBossOperation = "boss"

# this binding exists because shared behavior needs one stable value
KCutOperation = "cut"

# this binding exists because shared behavior needs one stable value
KRevolveBossOperation = "revolve-boss"

# this binding exists because shared behavior needs one stable value
KRevolveCutOperation = "revolve-cut"

# this binding exists because shared behavior needs one stable value
KBlindEnd = "blind"

# this binding exists because shared behavior needs one stable value
KThroughAllEnd = "through-all"

# this binding exists because shared behavior needs one stable value
KMidPlaneEnd = "mid-plane"

# this binding exists because shared behavior needs one stable value
KFullRevolutionEnd = "full-revolution"

# this binding exists because shared behavior needs one stable value
KFrontSupport = "front"

# this binding exists because shared behavior needs one stable value
KTopSupport = "top"

# this binding exists because shared behavior needs one stable value
KRightSupport = "right"

# this binding exists because shared behavior needs one stable value
KFaceSupport = "face"

# this binding exists because shared behavior needs one stable value
KSketchAxisSupport = "sketch-axis"

# this binding exists because shared behavior needs one stable value
KRefAxisSupport = "reference-axis"

# this binding exists because shared behavior needs one stable value
KFrontSketchAxisSupport = f"{KFrontSupport}-{KSketchAxisSupport}"

# this binding exists because shared behavior needs one stable value
KTopSketchAxisSupport = f"{KTopSupport}-{KSketchAxisSupport}"

# this binding exists because shared behavior needs one stable value
KRightSketchAxisSupport = f"{KRightSupport}-{KSketchAxisSupport}"

# this binding exists because shared behavior needs one stable value
KRevolveSupportByPlane = MappingProxyType(
    {
        KFrontSupport: KFrontSketchAxisSupport,
        KTopSupport: KTopSketchAxisSupport,
        KRightSupport: KRightSketchAxisSupport,
    }
)

# this binding exists because shared behavior needs one stable value
KRectangleProfile = "rectangle"

# this binding exists because shared behavior needs one stable value
KCircleProfile = "circle"

# this binding exists because shared behavior needs one stable value
KRectangleWithCircle = "rectangle+circle"

# this binding exists because shared behavior needs one stable value
KPolylineProfilePrefix = "polyline-"

# this binding exists because shared behavior needs one stable value
KArcProfileInfix = "-arc-"

# this binding exists because shared behavior needs one stable value
KCounterclockwiseSuffix = "-ccw"

# this binding exists because shared behavior needs one stable value
KClockwiseSuffix = "-cw"

# this binding exists because shared behavior needs one stable value
KSupportedEndConditions = frozenset({KBlindEnd, KThroughAllEnd, KMidPlaneEnd})

# this binding exists because shared behavior needs one stable value
KDepthlessEndConditions = frozenset({KThroughAllEnd})

# this binding exists because shared behavior needs one stable value
KRevolveOperations = frozenset({KRevolveBossOperation, KRevolveCutOperation})

# this binding exists because shared behavior needs one stable value
KRevolveSupports = frozenset(KRevolveSupportByPlane.values())

# this binding exists because shared behavior needs one stable value
KRevolveEndConditions = frozenset({KFullRevolutionEnd})

# this binding exists because shared behavior needs one stable value
KFullRevolutionDegrees = 360.0

# this binding exists because shared behavior needs one stable value
KMaximumRevolutionDegrees = KFullRevolutionDegrees

# this binding exists because shared behavior needs one stable value
KEndConditionCodes = MappingProxyType({KBlindEnd: 0, KMidPlaneEnd: 6})


# this definition exists because focused behavior needs one stable owner
def ArcProfile(LineCount: int, ArcCount: int, *, Counterclockwise: bool) -> str:
    Suffix = KCounterclockwiseSuffix if Counterclockwise else KClockwiseSuffix
    return f"{KPolylineProfilePrefix}{LineCount}{KArcProfileInfix}{ArcCount}{Suffix}"


# this definition exists because focused behavior needs one stable owner
def PolylineProfile(SegmentCount: int) -> str:
    return f"{KPolylineProfilePrefix}{SegmentCount}"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class FeatureTopology:
    operation: str
    profile: str
    support: str
    end_condition: str

    # lowercase access preserves the public topology tuple contract for callers
    @property
    def key(self) -> tuple[str, str, str, str]:
        return (
            self.operation,
            self.profile,
            self.support,
            self.end_condition,
        )


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
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

    # lowercase access exposes revolution classification without analyzer opaque aliases
    @property
    def revolve(self) -> bool:
        return self.operation in KRevolveOperations

    # lowercase access exposes the normalized topology without analyzer opaque aliases
    @property
    def topology(self) -> FeatureTopology:
        return FeatureTopology(
            self.operation,
            self.profile,
            self.support,
            self.end_condition,
        )

    # pascal compatibility preserves historical callers during lowercase model restoration
    @property
    def Revolve(self) -> bool:
        return self.revolve


# this binding exists because shared behavior needs one stable value
ARC_PROFILE_INFIX = KArcProfileInfix

# this binding exists because shared behavior needs one stable value
BLIND_END = KBlindEnd

# this binding exists because shared behavior needs one stable value
BOSS_OPERATION = KBossOperation

# this binding exists because shared behavior needs one stable value
CIRCLE_PROFILE = KCircleProfile

# this binding exists because shared behavior needs one stable value
CLOCKWISE_SUFFIX = KClockwiseSuffix

# this binding exists because shared behavior needs one stable value
COUNTERCLOCKWISE_SUFFIX = KCounterclockwiseSuffix

# this binding exists because shared behavior needs one stable value
CUT_OPERATION = KCutOperation

# this binding exists because shared behavior needs one stable value
DEPTHLESS_END_CONDITIONS = KDepthlessEndConditions

# this binding exists because shared behavior needs one stable value
END_CONDITION_CODES = KEndConditionCodes

# this binding exists because shared behavior needs one stable value
FACE_SUPPORT = KFaceSupport

# this binding exists because shared behavior needs one stable value
FRONT_SKETCH_AXIS_SUPPORT = KFrontSketchAxisSupport

# this binding exists because shared behavior needs one stable value
FRONT_SUPPORT = KFrontSupport

# this binding exists because shared behavior needs one stable value
FULL_REVOLUTION_DEGREES = KFullRevolutionDegrees

# this binding exists because shared behavior needs one stable value
FULL_REVOLUTION_END = KFullRevolutionEnd

# this binding exists because shared behavior needs one stable value
MAXIMUM_REVOLUTION_DEGREES = KMaximumRevolutionDegrees

# this binding exists because shared behavior needs one stable value
MID_PLANE_END = KMidPlaneEnd

# this binding exists because shared behavior needs one stable value
POLYLINE_PROFILE_PREFIX = KPolylineProfilePrefix

# this binding exists because shared behavior needs one stable value
RECTANGLE_PROFILE = KRectangleProfile

# this binding exists because shared behavior needs one stable value
RECTANGLE_WITH_CIRCLE_PROFILE = KRectangleWithCircle

# this binding exists because shared behavior needs one stable value
REFERENCE_AXIS_SUPPORT = KRefAxisSupport

# this binding exists because shared behavior needs one stable value
REVOLVE_BOSS_OPERATION = KRevolveBossOperation

# this binding exists because shared behavior needs one stable value
REVOLVE_CUT_OPERATION = KRevolveCutOperation

# this binding exists because shared behavior needs one stable value
REVOLVE_END_CONDITIONS = KRevolveEndConditions

# this binding exists because shared behavior needs one stable value
REVOLVE_OPERATIONS = KRevolveOperations

# this binding exists because shared behavior needs one stable value
REVOLVE_SUPPORTS = KRevolveSupports

# this binding exists because shared behavior needs one stable value
REVOLVE_SUPPORT_BY_PLANE = KRevolveSupportByPlane

# this binding exists because shared behavior needs one stable value
RIGHT_SKETCH_AXIS_SUPPORT = KRightSketchAxisSupport

# this binding exists because shared behavior needs one stable value
RIGHT_SUPPORT = KRightSupport

# this binding exists because shared behavior needs one stable value
SKETCH_AXIS_SUPPORT = KSketchAxisSupport

# this binding exists because shared behavior needs one stable value
SUPPORTED_END_CONDITIONS = KSupportedEndConditions

# this binding exists because shared behavior needs one stable value
THROUGH_ALL_END = KThroughAllEnd

# this binding exists because shared behavior needs one stable value
TOP_SKETCH_AXIS_SUPPORT = KTopSketchAxisSupport

# this binding exists because shared behavior needs one stable value
TOP_SUPPORT = KTopSupport

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
arc_profile = ArcProfile

# this binding exists because shared behavior needs one stable value
dataclass = Dataclass

# this binding exists because shared behavior needs one stable value
polyline_profile = PolylineProfile
