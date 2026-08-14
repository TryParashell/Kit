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
KBossOperation = 'boss'

# this binding exists because shared behavior needs one stable value
KCutOperation = 'cut'

# this binding exists because shared behavior needs one stable value
KRevolveBossOperation = 'revolve-boss'

# this binding exists because shared behavior needs one stable value
KRevolveCutOperation = 'revolve-cut'

# this binding exists because shared behavior needs one stable value
KBlindEnd = 'blind'

# this binding exists because shared behavior needs one stable value
KThroughAllEnd = 'through-all'

# this binding exists because shared behavior needs one stable value
KMidPlaneEnd = 'mid-plane'

# this binding exists because shared behavior needs one stable value
KFullRevolutionEnd = 'full-revolution'

# this binding exists because shared behavior needs one stable value
KFrontSupport = 'front'

# this binding exists because shared behavior needs one stable value
KTopSupport = 'top'

# this binding exists because shared behavior needs one stable value
KRightSupport = 'right'

# this binding exists because shared behavior needs one stable value
KFaceSupport = 'face'

# this binding exists because shared behavior needs one stable value
KSketchAxisSupport = 'sketch-axis'

# this binding exists because shared behavior needs one stable value
KRefAxisSupport = 'reference-axis'

# this binding exists because shared behavior needs one stable value
KFrontSketchAxisSupport = f'{KFrontSupport}-{KSketchAxisSupport}'

# this binding exists because shared behavior needs one stable value
KTopSketchAxisSupport = f'{KTopSupport}-{KSketchAxisSupport}'

# this binding exists because shared behavior needs one stable value
KRightSketchAxisSupport = f'{KRightSupport}-{KSketchAxisSupport}'

# this binding exists because shared behavior needs one stable value
KRevolveSupportByPlane = MappingProxyType({KFrontSupport: KFrontSketchAxisSupport, KTopSupport: KTopSketchAxisSupport, KRightSupport: KRightSketchAxisSupport})

# this binding exists because shared behavior needs one stable value
KRectangleProfile = 'rectangle'

# this binding exists because shared behavior needs one stable value
KCircleProfile = 'circle'

# this binding exists because shared behavior needs one stable value
KRectangleWithCircle = 'rectangle+circle'

# this binding exists because shared behavior needs one stable value
KPolylineProfilePrefix = 'polyline-'

# this binding exists because shared behavior needs one stable value
KArcProfileInfix = '-arc-'

# this binding exists because shared behavior needs one stable value
KCounterclockwiseSuffix = '-ccw'

# this binding exists because shared behavior needs one stable value
KClockwiseSuffix = '-cw'

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
    return f'{KPolylineProfilePrefix}{LineCount}{KArcProfileInfix}{ArcCount}{Suffix}'

# this definition exists because focused behavior needs one stable owner
def PolylineProfile(SegmentCount: int) -> str:
    return f'{KPolylineProfilePrefix}{SegmentCount}'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class FeatureTopology:
    locals().setdefault('__annotations__', {})
    __annotations__['operation'] = 'str'
    __annotations__['profile'] = 'str'
    __annotations__['support'] = 'str'
    __annotations__['end_condition'] = 'str'

    # this definition exists because focused behavior needs one stable owner
    @property
    def KeyAction(Instance) -> tuple[str, str, str, str]:
        return (Instance.operation, Instance.profile, Instance.support, Instance.end_condition)
    locals()['key'] = KeyAction

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class TargetFeature:
    locals().setdefault('__annotations__', {})
    __annotations__['operation'] = 'str'
    __annotations__['profile'] = 'str'
    __annotations__['support'] = 'str'
    __annotations__['end_condition'] = 'str'
    __annotations__['points_mm'] = 'tuple[tuple[float, float], ...]'
    locals()['points_mm'] = ()
    __annotations__['radii_mm'] = 'tuple[float, ...]'
    locals()['radii_mm'] = ()
    __annotations__['arc_centres_mm'] = 'tuple[tuple[float, float], ...]'
    locals()['arc_centres_mm'] = ()
    __annotations__['swept_arc_centres_mm'] = 'tuple[tuple[float, float], ...]'
    locals()['swept_arc_centres_mm'] = ()
    __annotations__['depth_mm'] = 'float | None'
    locals()['depth_mm'] = None
    __annotations__['reversed'] = 'bool | None'
    locals()['reversed'] = None
    __annotations__['angle_degrees'] = 'float | None'
    locals()['angle_degrees'] = None
    __annotations__['axis_direction'] = 'tuple[float, float] | None'
    locals()['axis_direction'] = None

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsRevolve(Instance) -> bool:
        return Instance.operation in KRevolveOperations

    # this definition exists because focused behavior needs one stable owner
    @property
    def Topology(Instance) -> FeatureTopology:
        return FeatureTopology(Instance.operation, Instance.profile, Instance.support, Instance.end_condition)
    locals()['revolve'] = IsRevolve
    locals()['topology'] = Topology
    locals()['Revolve'] = IsRevolve

# this binding exists because shared behavior needs one stable value
globals()['ARC_PROFILE_INFIX'] = KArcProfileInfix

# this binding exists because shared behavior needs one stable value
globals()['BLIND_END'] = KBlindEnd

# this binding exists because shared behavior needs one stable value
globals()['BOSS_OPERATION'] = KBossOperation

# this binding exists because shared behavior needs one stable value
globals()['CIRCLE_PROFILE'] = KCircleProfile

# this binding exists because shared behavior needs one stable value
globals()['CLOCKWISE_SUFFIX'] = KClockwiseSuffix

# this binding exists because shared behavior needs one stable value
globals()['COUNTERCLOCKWISE_SUFFIX'] = KCounterclockwiseSuffix

# this binding exists because shared behavior needs one stable value
globals()['CUT_OPERATION'] = KCutOperation

# this binding exists because shared behavior needs one stable value
globals()['DEPTHLESS_END_CONDITIONS'] = KDepthlessEndConditions

# this binding exists because shared behavior needs one stable value
globals()['END_CONDITION_CODES'] = KEndConditionCodes

# this binding exists because shared behavior needs one stable value
globals()['FACE_SUPPORT'] = KFaceSupport

# this binding exists because shared behavior needs one stable value
globals()['FRONT_SKETCH_AXIS_SUPPORT'] = KFrontSketchAxisSupport

# this binding exists because shared behavior needs one stable value
globals()['FRONT_SUPPORT'] = KFrontSupport

# this binding exists because shared behavior needs one stable value
globals()['FULL_REVOLUTION_DEGREES'] = KFullRevolutionDegrees

# this binding exists because shared behavior needs one stable value
globals()['FULL_REVOLUTION_END'] = KFullRevolutionEnd

# this binding exists because shared behavior needs one stable value
globals()['MAXIMUM_REVOLUTION_DEGREES'] = KMaximumRevolutionDegrees

# this binding exists because shared behavior needs one stable value
globals()['MID_PLANE_END'] = KMidPlaneEnd

# this binding exists because shared behavior needs one stable value
globals()['POLYLINE_PROFILE_PREFIX'] = KPolylineProfilePrefix

# this binding exists because shared behavior needs one stable value
globals()['RECTANGLE_PROFILE'] = KRectangleProfile

# this binding exists because shared behavior needs one stable value
globals()['RECTANGLE_WITH_CIRCLE_PROFILE'] = KRectangleWithCircle

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_AXIS_SUPPORT'] = KRefAxisSupport

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_BOSS_OPERATION'] = KRevolveBossOperation

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_CUT_OPERATION'] = KRevolveCutOperation

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_END_CONDITIONS'] = KRevolveEndConditions

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_OPERATIONS'] = KRevolveOperations

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_SUPPORTS'] = KRevolveSupports

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_SUPPORT_BY_PLANE'] = KRevolveSupportByPlane

# this binding exists because shared behavior needs one stable value
globals()['RIGHT_SKETCH_AXIS_SUPPORT'] = KRightSketchAxisSupport

# this binding exists because shared behavior needs one stable value
globals()['RIGHT_SUPPORT'] = KRightSupport

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_AXIS_SUPPORT'] = KSketchAxisSupport

# this binding exists because shared behavior needs one stable value
globals()['SUPPORTED_END_CONDITIONS'] = KSupportedEndConditions

# this binding exists because shared behavior needs one stable value
globals()['THROUGH_ALL_END'] = KThroughAllEnd

# this binding exists because shared behavior needs one stable value
globals()['TOP_SKETCH_AXIS_SUPPORT'] = KTopSketchAxisSupport

# this binding exists because shared behavior needs one stable value
globals()['TOP_SUPPORT'] = KTopSupport

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['arc_profile'] = ArcProfile

# this binding exists because shared behavior needs one stable value
globals()['dataclass'] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()['polyline_profile'] = PolylineProfile
