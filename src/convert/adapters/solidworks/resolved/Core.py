# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections.abc import Mapping, Sequence
from dataclasses import dataclass as Dataclass
import math as MathValue
import struct as Struct
from types import MappingProxyType
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.container.Format import CLASS_MARKER as ClassMarker, SERIALIZED_STRING_MARKER as SerializedStringMarker, dimension_scalar_value_offset as DimensionScalarValue

# this binding exists because shared behavior needs one stable value
KProfileClass = 'moProfileFeature_c'

# this binding exists because shared behavior needs one stable value
KLengthParamClass = 'moLengthParameter_c'

# this binding exists because shared behavior needs one stable value
KEndSpecClass = 'moEndSpec_c'

# this binding exists because shared behavior needs one stable value
KFromEndSpecClass = 'moFromEndSpec_c'

# this binding exists because shared behavior needs one stable value
KSketchChainClass = 'moSketchChain_c'

# this binding exists because shared behavior needs one stable value
KRevolutionClass = 'moRevolution_c'

# this binding exists because shared behavior needs one stable value
KRevolutionCutClass = 'moRevCut_c'

# this binding exists because shared behavior needs one stable value
KRevolutionEndSpecClass = 'moRevEndSpec_c'

# this binding exists because shared behavior needs one stable value
KAngleParamClass = 'moAngleParameter_c'

# this binding exists because shared behavior needs one stable value
KDepthRelative = 57

# this binding exists because shared behavior needs one stable value
KReverseRelative = 27

# this binding exists because shared behavior needs one stable value
KEndConditionRelative = 33

# this binding exists because shared behavior needs one stable value
KFromReverseRelative = 29

# this binding exists because shared behavior needs one stable value
KRectanglePointRelative = (283, 461, 623, 785)

# this binding exists because shared behavior needs one stable value
KBlindEndCondition = 0

# this binding exists because shared behavior needs one stable value
KMidPlaneEndCondition = 6

# this binding exists because shared behavior needs one stable value
KSupportedEndConditions = frozenset({KBlindEndCondition, KMidPlaneEndCondition})

# this binding exists because shared behavior needs one stable value
KFeatureFlagsMask = 2147483647

# this binding exists because shared behavior needs one stable value
KBossFlags = 1073742144

# this binding exists because shared behavior needs one stable value
KCutFlags = 1073873354

# this binding exists because shared behavior needs one stable value
KSketchFlags = 1073741824

# this binding exists because shared behavior needs one stable value
KPlaneFlags = 3221225472

# this binding exists because shared behavior needs one stable value
KRoundFlags = 1073741825

# this binding exists because shared behavior needs one stable value
KSweepFlags = 1073758211

# this binding exists because shared behavior needs one stable value
KSweepSingleProfileFlags = 1073758210

# this binding exists because shared behavior needs one stable value
KLoftFlags = 1073759236

# this binding exists because shared behavior needs one stable value
KBossKind = 'boss'

# this binding exists because shared behavior needs one stable value
KCutKind = 'cut'

# this binding exists because shared behavior needs one stable value
KRoundKind = 'round'

# this binding exists because shared behavior needs one stable value
KSweepKind = 'sweep'

# this binding exists because shared behavior needs one stable value
KLoftKind = 'loft'

# this binding exists because shared behavior needs one stable value
KRevolveKind = 'revolve'

# this binding exists because shared behavior needs one stable value
KRevolveCutKind = 'revolve-cut'

# this binding exists because shared behavior needs one stable value
KRevolveKinds = frozenset({KRevolveKind, KRevolveCutKind})

# this binding exists because shared behavior needs one stable value
KFeatureKindByFlags = MappingProxyType({KBossFlags: KBossKind, KCutFlags: KCutKind, KRoundFlags: KRoundKind, KSweepFlags: KSweepKind, KSweepSingleProfileFlags: KSweepKind, KLoftFlags: KLoftKind})

# this binding exists because shared behavior needs one stable value
KTreeNodeFlags = frozenset(KFeatureKindByFlags) | {KSketchFlags, KPlaneFlags}

# this binding exists because shared behavior needs one stable value
KRevolutionEndSpecData = Struct.pack('<I', 1) + bytes(24) + Struct.pack('<d', 0.01) + Struct.pack('<d', 0.01) + bytes(8)

# this binding exists because shared behavior needs one stable value
KRevolutionEndSpecHeader = ClassMarker + Struct.pack('<H', len(KRevolutionEndSpecClass)) + KRevolutionEndSpecClass.encode('ascii')

# this binding exists because shared behavior needs one stable value
KRevolutionEndSpecClassA = len(KRevolutionEndSpecHeader)

# this binding exists because shared behavior needs one stable value
KRevolutionClassRefBytes = 2

# this binding exists because shared behavior needs one stable value
KRevolutionAxisSketchA = -145

# this binding exists because shared behavior needs one stable value
KRevolutionAxisRefRelatiA = -131

# this binding exists because shared behavior needs one stable value
KRevolutionAxisSketch = 'sketch'

# this binding exists because shared behavior needs one stable value
KRevolutionAxisRef = 'reference-axis'

# this binding exists because shared behavior needs one stable value
KRevolutionStampLow = 1000000000

# this binding exists because shared behavior needs one stable value
KRevolutionStampHigh = 2000000000

# this binding exists because shared behavior needs one stable value
KAngleCopyDeltas = (0, 513, 537)

# this binding exists because shared behavior needs one stable value
KFullRevolutionRadians = 2.0 * MathValue.pi

# this binding exists because shared behavior needs one stable value
KAngleToleranceRadians = 1e-09

# this binding exists because shared behavior needs one stable value
KRevolveCutNameStems = ('cut-revolve', 'cortar-revolucion', 'cortar-revolución')

# this binding exists because shared behavior needs one stable value
KRevolveNameStems = ('revolve', 'revolucion', 'revolución')

# this binding exists because shared behavior needs one stable value
KRadiansToDegrees = 180.0 / MathValue.pi

# this binding exists because shared behavior needs one stable value
KSketchCoordinatePrefix = bytes.fromhex('000000000000f03f00000000000000001e00')

# this binding exists because shared behavior needs one stable value
KSketchPointPrefix = KSketchCoordinatePrefix

# this binding exists because shared behavior needs one stable value
KSketchFreeRole = 0

# this binding exists because shared behavior needs one stable value
KSketchOnCurveRole = 2

# this binding exists because shared behavior needs one stable value
KSketchPointClass = 2

# this binding exists because shared behavior needs one stable value
KSketchPointSuffix = bytes((KSketchFreeRole, 0, KSketchPointClass, 0))

# this binding exists because shared behavior needs one stable value
KSketchNamePrefix = 'Sketch'

# this binding exists because shared behavior needs one stable value
KDepthScalarNamePrefix = 'D'

# this binding exists because shared behavior needs one stable value
KDepthCopyDeltas = (0, 72, 398, 422, 560, 584)

# this binding exists because shared behavior needs one stable value
KDepthCopySigns = (1, 1, -1, -1, 1, 1)

# this binding exists because shared behavior needs one stable value
KFirstFeatureReverse = 824

# this binding exists because shared behavior needs one stable value
KFirstFeatureEndCondition = 818

# this binding exists because shared behavior needs one stable value
KLaterFeatureReverse = 721

# this binding exists because shared behavior needs one stable value
KLaterFeatureEndCondition = 715

# this binding exists because shared behavior needs one stable value
KCirclePointAngleDegrees = 17.0

# this binding exists because shared behavior needs one stable value
KCirclePointAngleToleranA = 1e-06

# this binding exists because shared behavior needs one stable value
KFullCircleDegrees = 360.0

# this binding exists because shared behavior needs one stable value
KSketchArcCentreClass = 1

# this binding exists because shared behavior needs one stable value
KArcRadiusToleranceMm = 1e-06

# this binding exists because shared behavior needs one stable value
KNameMarkerClassToken = 32772

# this binding exists because shared behavior needs one stable value
KMaxClassName = 64

# this binding exists because shared behavior needs one stable value
KMaxNameUnits = 128

# this binding exists because shared behavior needs one stable value
KMaxFeatureId = 4096

# this binding exists because shared behavior needs one stable value
KNameTrailerBytes = 12

# this binding exists because shared behavior needs one stable value
KMetres = 1000.0

# this binding exists because shared behavior needs one stable value
KCoordinateTrailerBytes = 4

# this binding exists because shared behavior needs one stable value
KMinimumRadiusMm = 1e-09

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ClassRecord:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['data_offset'] = 'int'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NameRecord:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['text_end'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['flags'] = 'int'
    __annotations__['feature_id'] = 'int'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class DimensionScalar:
    locals().setdefault('__annotations__', {})
    __annotations__['name'] = 'str'
    __annotations__['name_offset'] = 'int'
    __annotations__['value_offset'] = 'int'
    __annotations__['value_mm'] = 'float'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class SketchPoint:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['x_mm'] = 'float'
    __annotations__['y_mm'] = 'float'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class Sketch:
    locals().setdefault('__annotations__', {})
    __annotations__['offset'] = 'int'
    __annotations__['x_mm'] = 'float'
    __annotations__['y_mm'] = 'float'
    __annotations__['role'] = 'int'
    __annotations__['geometry_class'] = 'int'

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class SketchArc:
    locals().setdefault('__annotations__', {})
    __annotations__['centre_offset'] = 'int'
    __annotations__['point_offset'] = 'int'
    __annotations__['centre_x_mm'] = 'float'
    __annotations__['centre_y_mm'] = 'float'
    __annotations__['radius_mm'] = 'float'
    __annotations__['start_angle_degrees'] = 'float'
    __annotations__['sweep_angle_degrees'] = 'float'

    # this definition exists because focused behavior needs one stable owner
    @property
    def CentreMm(Instance) -> tuple[float, float]:
        return (Instance.centre_x_mm, Instance.centre_y_mm)

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsFullCircle(Instance) -> bool:
        return Instance.sweep_angle_degrees == KFullCircleDegrees
    locals()['centre_mm'] = CentreMm
    locals()['full_circle'] = IsFullCircle
    locals()['FullCircle'] = IsFullCircle

# this definition exists because swept arc coordinate properties form one geometric interface
class ArcGeometry:

    # this definition exists because focused behavior needs one stable owner
    @property
    def CentreMm(Instance) -> tuple[float, float]:
        return (Instance.centre_x_mm, Instance.centre_y_mm)

    # this definition exists because focused behavior needs one stable owner
    @property
    def StartMm(Instance) -> tuple[float, float]:
        return (Instance.start_x_mm, Instance.start_y_mm)

    # this definition exists because focused behavior needs one stable owner
    @property
    def EndMm(Instance) -> tuple[float, float]:
        return (Instance.end_x_mm, Instance.end_y_mm)

    # this definition exists because focused behavior needs one stable owner
    @property
    def RadiusMm(Instance) -> float:
        return MathValue.hypot(Instance.start_x_mm - Instance.centre_x_mm, Instance.start_y_mm - Instance.centre_y_mm)

    # this definition exists because focused behavior needs one stable owner
    @property
    def EndRadiusMm(Instance) -> float:
        return MathValue.hypot(Instance.end_x_mm - Instance.centre_x_mm, Instance.end_y_mm - Instance.centre_y_mm)

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsConsistent(Instance) -> bool:
        Radius = Instance.radius_mm
        if Radius <= KMinimumRadiusMm:
            return False
        return abs(Instance.end_radius_mm - Radius) <= max(KArcRadiusToleranceMm, Radius * 1e-09)
    locals()['centre_mm'] = CentreMm
    locals()['consistent'] = IsConsistent
    locals()['end_mm'] = EndMm
    locals()['end_radius_mm'] = EndRadiusMm
    locals()['radius_mm'] = RadiusMm
    locals()['start_mm'] = StartMm
    locals()['Consistent'] = IsConsistent

# this definition exists because swept arc angular properties form one directional interface
class ArcAngles:

    # this definition exists because focused behavior needs one stable owner
    @property
    def StartAngle(Instance) -> float:
        return MathValue.degrees(MathValue.atan2(Instance.start_y_mm - Instance.centre_y_mm, Instance.start_x_mm - Instance.centre_x_mm))

    # this definition exists because focused behavior needs one stable owner
    @property
    def EndAngleDegrees(Instance) -> float:
        return MathValue.degrees(MathValue.atan2(Instance.end_y_mm - Instance.centre_y_mm, Instance.end_x_mm - Instance.centre_x_mm))

    # this definition exists because focused behavior needs one stable owner
    def SweepAngle(Instance, Counterclockwise: bool) -> float:
        SpanValue = Instance.end_angle_degrees - Instance.start_angle_degrees
        if not Counterclockwise:
            SpanValue = -SpanValue
        while SpanValue <= 0.0:
            SpanValue += KFullCircleDegrees
        while SpanValue > KFullCircleDegrees:
            SpanValue -= KFullCircleDegrees
        return SpanValue
    locals()['end_angle_degrees'] = EndAngleDegrees
    locals()['start_angle_degrees'] = StartAngle
    locals()['sweep_angle_degrees'] = SweepAngle

# this definition exists because swept arc storage composes geometric and angular behavior
@Dataclass(frozen=True, slots=True)
class SweptArc(ArcGeometry, ArcAngles):
    locals().setdefault('__annotations__', {})
    __annotations__['centre_offset'] = 'int'
    __annotations__['start_offset'] = 'int'
    __annotations__['end_offset'] = 'int'
    __annotations__['centre_x_mm'] = 'float'
    __annotations__['centre_y_mm'] = 'float'
    __annotations__['start_x_mm'] = 'float'
    __annotations__['start_y_mm'] = 'float'
    __annotations__['end_x_mm'] = 'float'
    __annotations__['end_y_mm'] = 'float'

# this definition exists because core feature identity fields share one immutable record
@Dataclass(frozen=True, slots=True)
class FeatureCore:
    locals().setdefault('__annotations__', {})
    __annotations__['ordinal'] = 'int'
    __annotations__['name'] = 'str'
    __annotations__['kind'] = 'str'
    __annotations__['feature_id'] = 'int'
    __annotations__['flags'] = 'int'
    __annotations__['flags_offset'] = 'int'
    __annotations__['sketch_name'] = 'str | None'
    __annotations__['sketch_id'] = 'int | None'
    __annotations__['points'] = 'tuple[SketchPoint, ...]'
    __annotations__['arcs'] = 'tuple[SketchArc, ...]'

# this definition exists because derived feature geometry belongs outside immutable field storage
class LayoutMath:

    # this definition exists because focused behavior needs one stable owner
    @property
    def IsRevolution(Instance) -> bool:
        return Instance.kind in KRevolveKinds

    # this definition exists because focused behavior needs one stable owner
    @property
    def AngleDegrees(Instance) -> float | None:
        if Instance.angle_radians is None:
            return None
        return Instance.angle_radians * KRadiansToDegrees

    # this definition exists because focused behavior needs one stable owner
    @property
    def CornersMm(Instance) -> tuple[tuple[float, float], ...]:
        return tuple(((Point.x_mm, Point.y_mm) for Point in Instance.points))

    # this definition exists because focused behavior needs one stable owner
    @property
    def RadiiMm(Instance) -> tuple[float, ...]:
        return tuple((ArcValue.radius_mm for ArcValue in Instance.arcs))
    locals()['angle_degrees'] = AngleDegrees
    locals()['corners_mm'] = CornersMm
    locals()['is_revolution'] = IsRevolution
    locals()['radii_mm'] = RadiiMm

# this definition exists because feature bounds derive independently from other layout properties
class LayoutBounds:

    # this definition exists because focused behavior needs one stable owner
    @property
    def BoundsMm(Instance) -> tuple[float, float, float, float] | None:
        if Instance.points:
            XsValue = tuple((Point.x_mm for Point in Instance.points))
            YsValue = tuple((Point.y_mm for Point in Instance.points))
            return (min(XsValue), min(YsValue), max(XsValue), max(YsValue))
        if Instance.arcs:
            XsValue = tuple((Value for ArcValue in Instance.arcs for Value in (ArcValue.centre_x_mm - ArcValue.radius_mm, ArcValue.centre_x_mm + ArcValue.radius_mm)))
            YsValue = tuple((Value for ArcValue in Instance.arcs for Value in (ArcValue.centre_y_mm - ArcValue.radius_mm, ArcValue.centre_y_mm + ArcValue.radius_mm)))
            return (min(XsValue), min(YsValue), max(XsValue), max(YsValue))
        return None
    locals()['bounds_mm'] = BoundsMm

# this definition exists because required depth metadata extends stable feature identity fields
@Dataclass(frozen=True, slots=True)
class FeatureDepth(FeatureCore):
    locals().setdefault('__annotations__', {})
    __annotations__['depth_offset'] = 'int | None'
    __annotations__['depth_mm'] = 'float | None'
    __annotations__['depth_copy_offsets'] = 'tuple[int, ...]'
    __annotations__['reverse_offset'] = 'int | None'
    __annotations__['end_condition_offset'] = 'int | None'
    __annotations__['reversed'] = 'bool | None'
    __annotations__['end_condition_code'] = 'int | None'

# this definition exists because optional feature geometry extends the stable identity record
@Dataclass(frozen=True, slots=True)
class FeatureLayout(LayoutMath, LayoutBounds, FeatureDepth):
    locals().setdefault('__annotations__', {})
    __annotations__['from_reverse_offset'] = 'int | None'
    locals()['from_reverse_offset'] = None
    __annotations__['angle_offset'] = 'int | None'
    locals()['angle_offset'] = None
    __annotations__['angle_radians'] = 'float | None'
    locals()['angle_radians'] = None
    __annotations__['angle_copy_offsets'] = 'tuple[int, ...]'
    locals()['angle_copy_offsets'] = ()
    __annotations__['end_spec_offset'] = 'int | None'
    locals()['end_spec_offset'] = None
    __annotations__['axis_kind'] = 'str | None'
    locals()['axis_kind'] = None
    __annotations__['axis_offset'] = 'int | None'
    locals()['axis_offset'] = None
    __annotations__['axis_feature_id'] = 'int | None'
    locals()['axis_feature_id'] = None
    __annotations__['swept_arcs'] = 'tuple[SweptArc, ...]'
    locals()['swept_arcs'] = ()
    __annotations__['SketchDimensionOffsets'] = 'tuple[int, ...]'
    locals()['SketchDimensionOffsets'] = ()
    __annotations__['SketchDimensionsMm'] = 'tuple[float, ...]'
    locals()['SketchDimensionsMm'] = ()

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class FeatureEdit:
    locals().setdefault('__annotations__', {})
    __annotations__['corners_mm'] = 'Sequence[tuple[float, float]] | None'
    locals()['corners_mm'] = None
    __annotations__['depth_mm'] = 'float | None'
    locals()['depth_mm'] = None
    __annotations__['reversed'] = 'bool | None'
    locals()['reversed'] = None
    __annotations__['end_condition_code'] = 'int | None'
    locals()['end_condition_code'] = None
    __annotations__['update_depth_copies'] = 'bool'
    locals()['update_depth_copies'] = False
    __annotations__['radii_mm'] = 'Sequence[float] | None'
    locals()['radii_mm'] = None
    __annotations__['arc_centres_mm'] = 'Sequence[tuple[float, float]] | None'
    locals()['arc_centres_mm'] = None
    __annotations__['angle_radians'] = 'float | None'
    locals()['angle_radians'] = None
    __annotations__['swept_arc_centres_mm'] = 'Sequence[tuple[float, float]] | None'
    locals()['swept_arc_centres_mm'] = None
    __annotations__['SketchDimensionsMm'] = 'Sequence[float] | None'
    locals()['SketchDimensionsMm'] = None
    __annotations__['sketch_dimensions_mm'] = 'Sequence[float] | None'
    locals()['sketch_dimensions_mm'] = None

    # this definition exists because legacy and current sketch dimension names must stay synchronized
    def PostInit(Instance) -> None:
        SyncEditMut(Instance)
    locals()['__post_init__'] = PostInit

# this definition exists because feature edit aliases must resolve before patch validation
def SyncEditMut(EditValue: FeatureEdit) -> None:
    Dimensions = EditValue.SketchDimensionsMm if EditValue.SketchDimensionsMm is not None else EditValue.sketch_dimensions_mm
    if EditValue.SketchDimensionsMm is not None and EditValue.sketch_dimensions_mm is not None and EditValue.SketchDimensionsMm != EditValue.sketch_dimensions_mm:
        raise SldprtFormatError('sketch dimension aliases must describe the same values')
    object.__setattr__(EditValue, 'SketchDimensionsMm', Dimensions)
    object.__setattr__(EditValue, 'sketch_dimensions_mm', Dimensions)

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RectanglePad:
    locals().setdefault('__annotations__', {})
    __annotations__['point_offsets'] = 'tuple[tuple[int, int], ...]'
    __annotations__['depth_offset'] = 'int'
    __annotations__['reverse_offset'] = 'int'
    __annotations__['end_condition_offset'] = 'int'
    __annotations__['from_reverse_offset'] = 'int | None'
    __annotations__['corners_mm'] = 'tuple[tuple[float, float], ...]'
    __annotations__['depth_mm'] = 'float'
    __annotations__['reversed'] = 'bool'
    __annotations__['end_condition_code'] = 'int'

    # this definition exists because focused behavior needs one stable owner
    @property
    def BoundsMm(Instance) -> tuple[float, float, float, float]:
        XsValue = tuple((Point[0] for Point in Instance.corners_mm))
        YsValue = tuple((Point[1] for Point in Instance.corners_mm))
        return (min(XsValue), min(YsValue), max(XsValue), max(YsValue))
    locals()['bounds_mm'] = BoundsMm

# this definition exists because focused behavior needs one stable owner
def FeatureKind(Flags: int) -> str | None:
    return KFeatureKindByFlags.get(Flags & KFeatureFlagsMask)

# this definition exists because focused behavior needs one stable owner
def RevolutionEnd(DataValue: bytes | bytearray) -> tuple[int, ...]:
    BlobValue = bytes(DataValue)
    Result: list[int] = []
    Cursor = 0
    while True:
        Found = BlobValue.find(KRevolutionEndSpecData, Cursor)
        if Found < 0:
            break
        Cursor = Found + 1
        Header = Found - KRevolutionEndSpecClassA
        if Header >= 0 and BlobValue[Header:Found] == KRevolutionEndSpecHeader:
            Result.append(Header)
            continue
        Result.append(Found - KRevolutionClassRefBytes)
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def RevolutionAxis(DataValue: bytes | bytearray, Token: int, FeatureIds: frozenset[int]) -> tuple[str, int, int] | None:
    BlobValue = bytes(DataValue)
    for KindValue, Relative in ((KRevolutionAxisSketch, KRevolutionAxisSketchA), (KRevolutionAxisRef, KRevolutionAxisRefRelatiA)):
        Offset = Token + Relative
        if Offset < 0 or Offset + 8 > len(BlobValue):
            continue
        IdValue = Struct.unpack_from('<I', BlobValue, Offset)[0]
        Stamp = Struct.unpack_from('<I', BlobValue, Offset + 4)[0]
        if IdValue not in FeatureIds:
            continue
        if not KRevolutionStampLow <= Stamp <= KRevolutionStampHigh:
            continue
        return (KindValue, Offset, IdValue)
    return None

# this definition exists because focused behavior needs one stable owner
def RevolutionKind(NameValue: str, BossValue: bool, CutValue: bool) -> str:
    Folded = NameValue.casefold()
    if CutValue and any((Folded.startswith(StemValue) for StemValue in KRevolveCutNameStems)):
        return KRevolveCutKind
    if BossValue and any((Folded.startswith(StemValue) for StemValue in KRevolveNameStems)):
        return KRevolveKind
    if CutValue and (not BossValue):
        return KRevolveCutKind
    return KRevolveKind

# this definition exists because focused behavior needs one stable owner
def IsTreeNodeFlags(Flags: int) -> bool:
    return Flags & KFeatureFlagsMask in KTreeNodeFlags

# this definition exists because focused behavior needs one stable owner
def ClassRecords(DataValue: bytes | bytearray) -> tuple[ClassRecord, ...]:
    BlobValue = bytes(DataValue)
    Result: list[ClassRecord] = []
    Cursor = 0
    while True:
        Offset = BlobValue.find(ClassMarker, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        HeaderEnd = Offset + len(ClassMarker) + 2
        if HeaderEnd > len(BlobValue):
            continue
        Length = Struct.unpack_from('<H', BlobValue, Offset + len(ClassMarker))[0]
        if not 0 < Length <= KMaxClassName:
            continue
        Start = HeaderEnd
        EndValue = Start + Length
        if EndValue > len(BlobValue):
            continue
        try:
            NameValue = BlobValue[Start:EndValue].decode('ascii')
        except UnicodeDecodeError:
            continue
        if not NameValue.replace('_', '').isalnum():
            continue
        Result.append(ClassRecord(Offset, NameValue, EndValue))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def FirstClass(Records: tuple[ClassRecord, ...], NameValue: str) -> int | None:
    for Record in Records:
        if Record.name == NameValue:
            return Record.offset
    return None

# this definition exists because focused behavior needs one stable owner
def NameMarker(DataValue: bytes | bytearray) -> bytes:
    BlobValue = bytes(DataValue)
    for Record in ClassRecords(BlobValue):
        EndValue = Record.data_offset
        if EndValue + 5 > len(BlobValue):
            continue
        Token = Struct.unpack_from('<H', BlobValue, EndValue)[0]
        if Token & 32768 and Token != 65535 and (BlobValue[EndValue + 2:EndValue + 5] == SerializedStringMarker):
            return Struct.pack('<H', Token) + SerializedStringMarker
    return Struct.pack('<H', KNameMarkerClassToken) + SerializedStringMarker

# this definition exists because focused behavior needs one stable owner
def NameRecordsA(DataValue: bytes | bytearray) -> tuple[NameRecord, ...]:
    BlobValue = bytes(DataValue)
    return NameRecords(BlobValue, NameMarker(BlobValue))

# this definition exists because focused behavior needs one stable owner
def TreeNodesA(DataValue: bytes | bytearray) -> tuple[NameRecord, ...]:
    BlobValue = bytes(DataValue)
    return TreeNodes(BlobValue, NameRecordsA(BlobValue))

# this definition exists because focused behavior needs one stable owner
def DimensionA(DataValue: bytes | bytearray) -> tuple[DimensionScalar, ...]:
    BlobValue = bytes(DataValue)
    return Dimension(BlobValue, NameRecordsA(BlobValue))

# this definition exists because focused behavior needs one stable owner
def SketchA(DataValue: bytes | bytearray) -> tuple[Sketch, ...]:
    BlobValue = bytes(DataValue)
    Result: list[Sketch] = []
    Cursor = 0
    while True:
        Offset = BlobValue.find(KSketchCoordinatePrefix, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        Start = Offset + len(KSketchCoordinatePrefix)
        TrailerEnd = Start + 16 + KCoordinateTrailerBytes
        if TrailerEnd > len(BlobValue):
            continue
        Trailer = BlobValue[Start + 16:TrailerEnd]
        if Trailer[1] or Trailer[3]:
            continue
        FirstCoord = ReadDouble(BlobValue, Start)
        SecondCoord = ReadDouble(BlobValue, Start + 8)
        if FirstCoord is None or SecondCoord is None:
            continue
        Result.append(Sketch(offset=Start, x_mm=FirstCoord * KMetres, y_mm=SecondCoord * KMetres, role=Trailer[0], geometry_class=Trailer[2]))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def SketchPoints(DataValue: bytes | bytearray) -> tuple[SketchPoint, ...]:
    return tuple((SketchPoint(offset=Coordinate.offset, x_mm=Coordinate.x_mm, y_mm=Coordinate.y_mm) for Coordinate in SketchA(DataValue) if Coordinate.role == KSketchFreeRole and Coordinate.geometry_class == KSketchPointClass))

# this definition exists because focused behavior needs one stable owner
def SketchArcs(DataValue: bytes | bytearray) -> tuple[SketchArc, ...]:
    Coordinates = SketchA(DataValue)
    Result: list[SketchArc] = []
    for Centre, Point in zip(Coordinates, Coordinates[1:], strict=False):
        if Point.role != KSketchOnCurveRole or Point.geometry_class != KSketchPointClass:
            continue
        ArcValue = SketchArcA(Centre, Point)
        if ArcValue is not None:
            Result.append(ArcValue)
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def SweptArcs(DataValue: bytes | bytearray) -> tuple[SweptArc, ...]:
    Coordinates = SketchA(DataValue)
    CircleCentres = {ArcValue.centre_offset for ArcValue in SketchArcs(DataValue)}
    Result: list[SweptArc] = []
    for Index, Centre in enumerate(Coordinates):
        if Centre.role != KSketchFreeRole or Centre.geometry_class != KSketchArcCentreClass or Centre.offset in CircleCentres:
            continue
        RunValue: list[Sketch] = []
        Cursor = Index - 1
        while Cursor >= 0:
            Choice = Coordinates[Cursor]
            if Choice.role != KSketchFreeRole or Choice.geometry_class != KSketchPointClass:
                break
            RunValue.append(Choice)
            Cursor -= 1
        if len(RunValue) < 2:
            continue
        Start = RunValue[0]
        EndValue = RunValue[-1]
        ArcValue = SweptArc(centre_offset=Centre.offset, start_offset=Start.offset, end_offset=EndValue.offset, centre_x_mm=Centre.x_mm, centre_y_mm=Centre.y_mm, start_x_mm=Start.x_mm, start_y_mm=Start.y_mm, end_x_mm=EndValue.x_mm, end_y_mm=EndValue.y_mm)
        if ArcValue.consistent:
            Result.append(ArcValue)
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def PatchSketchArcs(DataValue: bytes | bytearray, RadiiMm: Mapping[int, float]) -> bytes:
    ArcsValue = SketchArcs(DataValue)
    Unknown = sorted(set(RadiiMm) - set(range(len(ArcsValue))))
    if Unknown:
        raise SldprtFormatError(f'resolved-features stream has no sketch arc at indices {Unknown}')
    Output = bytearray(DataValue)
    for Index in sorted(RadiiMm):
        WriteArcRadius(Output, ArcsValue[Index], RadiiMm[Index])
    Patched = bytes(Output)
    Verification = SketchArcs(Patched)
    if len(Verification) != len(ArcsValue):
        raise SldprtFormatError('patched resolved-features stream cannot be relocated')
    for Index, RadiusMm in sorted(RadiiMm.items()):
        VerifyArc(Verification[Index], ArcsValue[Index], RadiusMm, Index)
    return Patched

# this definition exists because focused behavior needs one stable owner
def LocateFeatures(DataValue: bytes | bytearray) -> tuple[FeatureLayout, ...]:
    BlobValue = bytes(DataValue)
    Records = NameRecordsA(BlobValue)
    Nodes = TreeNodes(BlobValue, Records)
    Classes = ClassRecords(BlobValue)
    Revolutions = RevolutionNodes(BlobValue, Nodes, Classes)
    Features = tuple((NodeValue for NodeValue in Nodes if FeatureKind(NodeValue.flags) is not None or NodeValue.offset in Revolutions))
    Profiles = tuple((NodeValue for NodeValue in Nodes if FeatureKind(NodeValue.flags) is None and NodeValue.offset not in Revolutions))
    FromReverse = ReverseMirror(BlobValue, Classes)
    Points = SketchPoints(BlobValue)
    ArcsValue = SketchArcs(BlobValue)
    Swept = SweptArcs(BlobValue)
    Scalars = tuple((Scalar for Scalar in Dimension(BlobValue, Records) if Scalar.name.startswith(KDepthScalarNamePrefix)))
    Result: list[FeatureLayout] = []
    Extrusions = 0
    for Ordinal, Feature in enumerate(Features):
        Start = Features[Ordinal - 1].offset if Ordinal else 0
        Limit = Features[Ordinal + 1].offset if Ordinal + 1 < len(Features) else len(BlobValue)
        Sketch = LastNodeInRange(Profiles, Start, Feature.offset)
        SketchScalars = SketchScalarsIn(Scalars, Sketch, Feature)
        Scalar = next((Choice for Choice in Scalars if Feature.offset < Choice.value_offset < Limit), None)
        RevolutionData = Revolutions.get(Feature.offset)
        if RevolutionData is not None:
            Result.append(Revolution(BlobValue, Ordinal, Feature, Sketch, Scalar, RevolutionData, () if Sketch is None else PointsInRange(Points, Sketch, Feature), () if Sketch is None else ArcsInRange(ArcsValue, Sketch, Feature), SweptArcs=() if Sketch is None else SweptInRange(Swept, Sketch, Feature), SketchScalars=SketchScalars))
            continue
        Result.append(FeatureLayoutA(BlobValue, Ordinal, Extrusions, Feature, Sketch, () if Sketch is None else PointsInRange(Points, Sketch, Feature), () if Sketch is None else ArcsInRange(ArcsValue, Sketch, Feature), Scalar, FromReverse if Extrusions == 0 else None, SweptArcs=() if Sketch is None else SweptInRange(Swept, Sketch, Feature), SketchScalars=SketchScalars))
        Extrusions += 1
    return tuple(Result)

# this definition exists because mirrored direction discovery has one bounds checked location
def ReverseMirror(BlobValue: bytes, Classes: tuple[ClassRecord, ...]) -> int | None:
    FromEndSpec = FirstClass(Classes, KFromEndSpecClass)
    FromReverse = None if FromEndSpec is None else FromEndSpec + KFromReverseRelative
    if FromReverse is not None and FromReverse >= len(BlobValue):
        return None
    return FromReverse

# this definition exists because focused behavior needs one stable owner
def RectangleMm(MinimumXMm: float, MinimumYMm: float, MaximumXMm: float, MaximumYMm: float) -> tuple[tuple[float, float], ...]:
    return ((MinimumXMm, MinimumYMm), (MaximumXMm, MaximumYMm), (MinimumXMm, MaximumYMm), (MaximumXMm, MinimumYMm))

# this definition exists because focused behavior needs one stable owner
def CircleRadiusMm(XMmValue: float, YMmValue: float) -> float:
    return MathValue.hypot(XMmValue, YMmValue)

# this definition exists because focused behavior needs one stable owner
def CirclePointMm(RadiusMm: float) -> tuple[float, float]:
    if not MathValue.isfinite(RadiusMm) or RadiusMm <= 0.0:
        raise SldprtFormatError('circular profile requires a positive finite radius')
    Angle = MathValue.radians(KCirclePointAngleDegrees)
    return (RadiusMm * MathValue.cos(Angle), RadiusMm * MathValue.sin(Angle))

# this definition exists because focused behavior needs one stable owner
def PatchFeatures(DataValue: bytes | bytearray, Edits: Mapping[int, FeatureEdit]) -> bytes:
    Features = LocateFeatures(DataValue)
    Ordinals = {Feature.ordinal for Feature in Features}
    Unknown = sorted(set(Edits) - Ordinals)
    if Unknown:
        raise SldprtFormatError(f'resolved-features stream has no feature at ordinals {Unknown}')
    Output = bytearray(DataValue)
    for Ordinal in sorted(Edits):
        Feature = Features[Ordinal]
        EditValue = Edits[Ordinal]
        ValidateEdit(Feature, EditValue)
        PatchPointsMut(Output, Feature, EditValue)
        PatchArcsMut(Output, Feature, EditValue)
        PatchSweptMut(Output, Feature, EditValue)
        PatchScalarsMut(Output, Feature, EditValue)
        PatchFlagsMut(Output, Feature, EditValue)
    Patched = bytes(Output)
    VerifyFeatures(Patched, Features, Edits)
    return Patched

# this definition exists because sketch point writes share coordinate unit conversion
def PatchPointsMut(Output: bytearray, Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.corners_mm is None:
        return
    for Point, (FirstCoord, SecondCoord) in zip(Feature.points, EditValue.corners_mm, strict=True):
        Struct.pack_into('<d', Output, Point.offset, FirstCoord / KMetres)
        Struct.pack_into('<d', Output, Point.offset + 8, SecondCoord / KMetres)

# this definition exists because circular arc writes must move centres and rim points together
def PatchArcsMut(Output: bytearray, Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.radii_mm is not None:
        for ArcValue, RadiusMm in zip(Feature.arcs, EditValue.radii_mm, strict=True):
            if not MathValue.isclose(RadiusMm, ArcValue.radius_mm, rel_tol=0.0, abs_tol=1e-12):
                WriteArcRadius(Output, ArcValue, RadiusMm)
    if EditValue.arc_centres_mm is None:
        return
    for ArcValue, (FirstCoord, SecondCoord) in zip(Feature.arcs, EditValue.arc_centres_mm, strict=True):
        if MathValue.isclose(FirstCoord, ArcValue.centre_x_mm, rel_tol=0.0, abs_tol=1e-12) and MathValue.isclose(SecondCoord, ArcValue.centre_y_mm, rel_tol=0.0, abs_tol=1e-12):
            continue
        DeltaX = (FirstCoord - ArcValue.centre_x_mm) / KMetres
        DeltaY = (SecondCoord - ArcValue.centre_y_mm) / KMetres
        RimXValue, RimYValue = Struct.unpack_from('<2d', Output, ArcValue.point_offset)
        Struct.pack_into('<d', Output, ArcValue.centre_offset, FirstCoord / KMetres)
        Struct.pack_into('<d', Output, ArcValue.centre_offset + 8, SecondCoord / KMetres)
        Struct.pack_into('<d', Output, ArcValue.point_offset, RimXValue + DeltaX)
        Struct.pack_into('<d', Output, ArcValue.point_offset + 8, RimYValue + DeltaY)

# this definition exists because swept arc centres occupy a distinct coordinate record
def PatchSweptMut(Output: bytearray, Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.swept_arc_centres_mm is None:
        return
    for ArcValue, Centre in zip(Feature.swept_arcs, EditValue.swept_arc_centres_mm, strict=True):
        Struct.pack_into('<d', Output, ArcValue.centre_offset, Centre[0] / KMetres)
        Struct.pack_into('<d', Output, ArcValue.centre_offset + 8, Centre[1] / KMetres)

# this definition exists because scalar edits share native double precision encoding
def PatchScalarsMut(Output: bytearray, Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.SketchDimensionsMm is not None:
        for DimensionOffset, DimensionValue in zip(Feature.SketchDimensionOffsets, EditValue.SketchDimensionsMm, strict=True):
            Struct.pack_into('<d', Output, DimensionOffset, DimensionValue / KMetres)
    if EditValue.angle_radians is not None:
        Struct.pack_into('<d', Output, Feature.angle_offset, EditValue.angle_radians)
    if EditValue.depth_mm is None:
        return
    Struct.pack_into('<d', Output, Feature.depth_offset, EditValue.depth_mm / KMetres)
    if EditValue.update_depth_copies:
        for Delta, SignValue in zip(KDepthCopyDeltas, KDepthCopySigns, strict=True):
            Target = Feature.depth_offset + Delta
            if Target + 8 <= len(Output):
                Struct.pack_into('<d', Output, Target, SignValue * EditValue.depth_mm / KMetres)

# this definition exists because direction and termination flags share byte sized storage
def PatchFlagsMut(Output: bytearray, Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.reversed is not None:
        Output[Feature.reverse_offset] = 1 if EditValue.reversed else 0
        if Feature.from_reverse_offset is not None:
            Output[Feature.from_reverse_offset] = 1 if EditValue.reversed else 0
    if EditValue.end_condition_code is not None:
        Output[Feature.end_condition_offset] = EditValue.end_condition_code

# this definition exists because focused behavior needs one stable owner
def LocateRectangle(DataValue: bytes | bytearray) -> RectanglePad | None:
    BlobValue = bytes(DataValue)
    Records = ClassRecords(BlobValue)
    Profile = FirstClass(Records, KProfileClass)
    Param = FirstClass(Records, KLengthParamClass)
    EndSpec = FirstClass(Records, KEndSpecClass)
    if Profile is None or Param is None or EndSpec is None:
        return None
    PointData = RectPoints(BlobValue, Profile)
    if PointData is None:
        return None
    PointOffsets, Corners = PointData
    DepthOffset = Param + KDepthRelative
    Depth = ReadDouble(BlobValue, DepthOffset)
    if Depth is None or Depth <= 0.0:
        return None
    ReverseOffset = EndSpec + KReverseRelative
    EndConditionOffset = EndSpec + KEndConditionRelative
    if EndConditionOffset >= len(BlobValue):
        return None
    FromEndSpec = FirstClass(Records, KFromEndSpecClass)
    FromReverseOffset = None if FromEndSpec is None else FromEndSpec + KFromReverseRelative
    if FromReverseOffset is not None and FromReverseOffset >= len(BlobValue):
        FromReverseOffset = None
    return RectanglePad(point_offsets=tuple(PointOffsets), depth_offset=DepthOffset, reverse_offset=ReverseOffset, end_condition_offset=EndConditionOffset, from_reverse_offset=FromReverseOffset, corners_mm=tuple(Corners), depth_mm=Depth * KMetres, reversed=bool(BlobValue[ReverseOffset]), end_condition_code=BlobValue[EndConditionOffset])

# this definition exists because rectangle point recovery validates one complete corner set
def RectPoints(BlobValue: bytes, Profile: int) -> tuple[list[tuple[int, int]], list[tuple[float, float]]] | None:
    PointOffsets: list[tuple[int, int]] = []
    Corners: list[tuple[float, float]] = []
    for Relative in KRectanglePointRelative:
        XOffset = Profile + Relative
        YOffset = XOffset + 8
        FirstCoord = ReadDouble(BlobValue, XOffset)
        SecondCoord = ReadDouble(BlobValue, YOffset)
        if FirstCoord is None or SecondCoord is None:
            return None
        PointOffsets.append((XOffset, YOffset))
        Corners.append((FirstCoord * KMetres, SecondCoord * KMetres))
    XsValue = sorted({round(Point[0], 9) for Point in Corners})
    YsValue = sorted({round(Point[1], 9) for Point in Corners})
    if len(XsValue) != 2 or len(YsValue) != 2:
        return None
    return (PointOffsets, Corners)

# this definition exists because focused behavior needs one stable owner
def SketchPlaneId(DataValue: bytes | bytearray) -> int | None:
    BlobValue = bytes(DataValue)
    Chain = FirstClass(ClassRecords(BlobValue), KSketchChainClass)
    if Chain is None:
        return None
    for Offset in range(Chain, min(Chain + 320, len(BlobValue) - 14)):
        Choice = Struct.unpack_from('<I', BlobValue, Offset)[0]
        if Choice not in {2, 3, 4}:
            continue
        AxisValue = Struct.unpack_from('<I', BlobValue, Offset + 10)[0]
        if AxisValue == 5 - Choice:
            return Choice
    return None

# this definition exists because focused behavior needs one stable owner
def PatchSketch(DataValue: bytes | bytearray, PlaneObjectId: int) -> bytes:
    if PlaneObjectId not in {2, 3, 4}:
        raise SldprtFormatError('sketch support requires a principal plane object id')
    OutputData = bytearray(DataValue)
    ChainOffset = FirstClass(ClassRecords(OutputData), KSketchChainClass)
    if ChainOffset is None:
        raise SldprtFormatError('resolved feature stream has no sketch chain')
    PlaneOffset = None
    for OffsetValue in range(ChainOffset, min(ChainOffset + 320, len(OutputData) - 14)):
        ChoiceValue = Struct.unpack_from('<I', OutputData, OffsetValue)[0]
        if ChoiceValue not in {2, 3, 4}:
            continue
        AxisValue = Struct.unpack_from('<I', OutputData, OffsetValue + 10)[0]
        if AxisValue == 5 - ChoiceValue:
            PlaneOffset = OffsetValue
            break
    if PlaneOffset is None:
        raise SldprtFormatError('resolved feature stream has no principal-plane reference')
    Struct.pack_into('<I', OutputData, PlaneOffset, PlaneObjectId)
    Struct.pack_into('<I', OutputData, PlaneOffset + 10, 5 - PlaneObjectId)
    if OutputData[PlaneOffset + 14] == 1:
        PrincipalFrames = {2: ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)), 3: ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)), 4: ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0))}
        UAxisValue, VAxisValue, NormalValue = PrincipalFrames[PlaneObjectId]
        MatrixRows = tuple((ComponentValue for AxisIndex in range(3) for ComponentValue in (UAxisValue[AxisIndex], VAxisValue[AxisIndex], NormalValue[AxisIndex])))
        Struct.pack_into('<9d', OutputData, PlaneOffset + 15, *MatrixRows)
    PatchedData = bytes(OutputData)
    if SketchPlaneId(PatchedData) != PlaneObjectId:
        raise SldprtFormatError('resolved sketch support plane did not patch consistently')
    return PatchedData

# this definition exists because focused behavior needs one stable owner
def NameRecords(BlobValue: bytes, Marker: bytes) -> tuple[NameRecord, ...]:
    Result: list[NameRecord] = []
    Cursor = 0
    while True:
        Offset = BlobValue.find(Marker, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        UnitsOffset = Offset + len(Marker)
        if UnitsOffset >= len(BlobValue):
            continue
        Units = BlobValue[UnitsOffset]
        TextStart = UnitsOffset + 1
        TextEnd = TextStart + Units * 2
        if not 1 <= Units <= KMaxNameUnits:
            continue
        if TextEnd + KNameTrailerBytes > len(BlobValue):
            continue
        try:
            TextValue = BlobValue[TextStart:TextEnd].decode('utf-16le')
        except UnicodeDecodeError:
            continue
        if not TextValue or any((not Character.isprintable() for Character in TextValue)):
            continue
        Result.append(NameRecord(offset=Offset, text_end=TextEnd, name=TextValue, flags=Struct.unpack_from('<I', BlobValue, TextEnd + 4)[0], feature_id=Struct.unpack_from('<I', BlobValue, TextEnd + 8)[0]))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def TreeNodes(BlobValue: bytes, Records: tuple[NameRecord, ...]) -> tuple[NameRecord, ...]:
    return tuple((Record for Record in Records if BlobValue[Record.text_end:Record.text_end + 4] == bytes(4) and 0 < Record.feature_id < KMaxFeatureId and IsTreeNodeFlags(Record.flags)))

# this definition exists because focused behavior needs one stable owner
def Dimension(BlobValue: bytes, Records: tuple[NameRecord, ...]) -> tuple[DimensionScalar, ...]:
    Result: list[DimensionScalar] = []
    for Record in Records:
        ValueOffset = DimensionScalarValue(BlobValue, Record.text_end, len(BlobValue), TrailingBytes=7)
        if ValueOffset is None:
            continue
        Value = ReadDouble(BlobValue, ValueOffset)
        if Value is None:
            continue
        Result.append(DimensionScalar(name=Record.name, name_offset=Record.offset, value_offset=ValueOffset, value_mm=Value * KMetres))
    return tuple(Result)

# this definition exists because focused behavior needs one stable owner
def SketchArcA(Centre: SketchCoordinate, Point: SketchCoordinate) -> SketchArc | None:
    DxValue = Point.x_mm - Centre.x_mm
    DyValue = Point.y_mm - Centre.y_mm
    Radius = MathValue.hypot(DxValue, DyValue)
    if Radius <= KMinimumRadiusMm:
        return None
    Angle = MathValue.degrees(MathValue.atan2(DyValue, DxValue))
    if abs(Angle - KCirclePointAngleDegrees) > KCirclePointAngleToleranA:
        return None
    return SketchArc(centre_offset=Centre.offset, point_offset=Point.offset, centre_x_mm=Centre.x_mm, centre_y_mm=Centre.y_mm, radius_mm=Radius, start_angle_degrees=Angle, sweep_angle_degrees=KFullCircleDegrees)

# this definition exists because focused behavior needs one stable owner
def WriteArcRadius(Output: bytearray, ArcValue: SketchArc, RadiusMm: float) -> None:
    if not MathValue.isfinite(RadiusMm) or RadiusMm <= 0.0:
        raise SldprtFormatError('circular profile requires a positive finite radius')
    XMmValue, YMmValue = CirclePointMm(RadiusMm)
    CentreX = Struct.unpack_from('<d', Output, ArcValue.centre_offset)[0]
    CentreY = Struct.unpack_from('<d', Output, ArcValue.centre_offset + 8)[0]
    Struct.pack_into('<d', Output, ArcValue.point_offset, CentreX + XMmValue / KMetres)
    Struct.pack_into('<d', Output, ArcValue.point_offset + 8, CentreY + YMmValue / KMetres)

# this definition exists because focused behavior needs one stable owner
def VerifyArc(After: SketchArc, Before: SketchArc, RadiusMm: float, Index: int) -> None:
    if After.centre_offset != Before.centre_offset or After.point_offset != Before.point_offset:
        raise SldprtFormatError(f'patched sketch arc {Index} does not relocate to the same layout')
    if not MathValue.isclose(After.radius_mm, RadiusMm, rel_tol=1e-12, abs_tol=1e-09):
        raise SldprtFormatError(f'patched sketch arc {Index} radius does not verify')

# this definition exists because focused behavior needs one stable owner
def LastNodeInRange(Nodes: tuple[NameRecord, ...], Start: int, Limit: int) -> NameRecord | None:
    Candidates = tuple((NodeValue for NodeValue in Nodes if Start < NodeValue.offset < Limit))
    return Candidates[-1] if Candidates else None

# this definition exists because focused behavior needs one stable owner
def PointsInRange(Points: tuple[SketchPoint, ...], Sketch: NameRecord, Feature: NameRecord) -> tuple[SketchPoint, ...]:
    return tuple((Point for Point in Points if Sketch.offset < Point.offset < Feature.offset))

# this definition exists because focused behavior needs one stable owner
def ArcsInRange(ArcsValue: tuple[SketchArc, ...], Sketch: NameRecord, Feature: NameRecord) -> tuple[SketchArc, ...]:
    return tuple((ArcValue for ArcValue in ArcsValue if Sketch.offset < ArcValue.centre_offset < Feature.offset))

# this definition exists because focused behavior needs one stable owner
def SweptInRange(ArcsValue: tuple[SweptArc, ...], Sketch: NameRecord, Feature: NameRecord) -> tuple[SweptArc, ...]:
    return tuple((ArcValue for ArcValue in ArcsValue if Sketch.offset < ArcValue.centre_offset < Feature.offset and Sketch.offset < ArcValue.start_offset < Feature.offset and (Sketch.offset < ArcValue.end_offset < Feature.offset)))

# this definition exists because focused behavior needs one stable owner
def SketchScalarsIn(ScalarData: tuple[DimensionScalar, ...], SketchData: NameRecord | None, FeatureData: NameRecord) -> tuple[DimensionScalar, ...]:
    if SketchData is None:
        return ()
    return tuple((ItemData for ItemData in ScalarData if SketchData.offset < ItemData.value_offset < FeatureData.offset))

# this definition exists because focused behavior needs one stable owner
def RevolutionNodes(BlobValue: bytes, Nodes: tuple[NameRecord, ...], Classes: tuple[ClassRecord, ...]) -> dict[int, tuple[str, int, tuple[str, int, int] | None]]:
    Names = {Record.name for Record in Classes}
    BossValue = KRevolutionClass in Names
    CutValue = KRevolutionCutClass in Names
    if not BossValue and (not CutValue):
        return {}
    Tokens = RevolutionEnd(BlobValue)
    if not Tokens:
        return {}
    FeatureIds = frozenset((NodeValue.feature_id for NodeValue in Nodes))
    Candidates = tuple((NodeValue for NodeValue in Nodes if FeatureKind(NodeValue.flags) is None and NodeValue.flags & KFeatureFlagsMask == KSketchFlags))
    Result: dict[int, tuple[str, int, tuple[str, int, int] | None]] = {}
    for Token in sorted(Tokens):
        NodeValue = LastNodeInRange(Candidates, -1, Token)
        if NodeValue is None or NodeValue.offset in Result:
            continue
        Result[NodeValue.offset] = (RevolutionKind(NodeValue.name, BossValue, CutValue), Token, RevolutionAxis(BlobValue, Token, FeatureIds))
    return Result

# this definition exists because focused behavior needs one stable owner
def Revolution(BlobValue: bytes, Ordinal: int, Feature: NameRecord, Sketch: NameRecord | None, Scalar: DimensionScalar | None, Revolution: tuple[str, int, tuple[str, int, int] | None], Points: tuple[SketchPoint, ...], ArcsValue: tuple[SketchArc, ...], *, SweptArcs: tuple[SweptArc, ...]=(), SketchScalars: tuple[DimensionScalar, ...]=()) -> FeatureLayout:
    KindValue, Token, AxisValue = Revolution
    AngleOffset = None if Scalar is None else Scalar.value_offset
    return FeatureLayout(ordinal=Ordinal, name=Feature.name, kind=KindValue, feature_id=Feature.feature_id, flags=Feature.flags, flags_offset=Feature.text_end + 4, sketch_name=None if Sketch is None else Sketch.name, sketch_id=None if Sketch is None else Sketch.feature_id, points=Points, arcs=ArcsValue, swept_arcs=SweptArcs, depth_offset=None, depth_mm=None, depth_copy_offsets=(), reverse_offset=None, end_condition_offset=None, reversed=None, end_condition_code=None, angle_offset=AngleOffset, angle_radians=None if AngleOffset is None else ReadDouble(BlobValue, AngleOffset), angle_copy_offsets=() if AngleOffset is None else tuple((AngleOffset + Delta for Delta in KAngleCopyDeltas if AngleOffset + Delta + 8 <= len(BlobValue))), end_spec_offset=Token, axis_kind=None if AxisValue is None else AxisValue[0], axis_offset=None if AxisValue is None else AxisValue[1], axis_feature_id=None if AxisValue is None else AxisValue[2], SketchDimensionOffsets=tuple((ItemData.value_offset for ItemData in SketchScalars)), SketchDimensionsMm=tuple((ItemData.value_mm for ItemData in SketchScalars)))

# this definition exists because focused behavior needs one stable owner
def FeatureLayoutA(BlobValue: bytes, Ordinal: int, ExtrusionOrdinal: int, Feature: NameRecord, Sketch: NameRecord | None, Points: tuple[SketchPoint, ...], ArcsValue: tuple[SketchArc, ...], Scalar: DimensionScalar | None, FromReverseOffset: int | None, *, SweptArcs: tuple[SweptArc, ...]=(), SketchScalars: tuple[DimensionScalar, ...]=()) -> FeatureLayout:
    DepthOffset = None if Scalar is None else Scalar.value_offset
    DepthMm = None if Scalar is None else Scalar.value_mm
    Copies: tuple[int, ...] = ()
    ReverseOffset: int | None = None
    EndConditionOffset: int | None = None
    if DepthOffset is not None:
        Copies = tuple((DepthOffset + Delta for Delta in KDepthCopyDeltas if DepthOffset + Delta + 8 <= len(BlobValue)))
        ReverseDistance, EndConditionDistance = (KFirstFeatureReverse, KFirstFeatureEndCondition) if ExtrusionOrdinal == 0 else (KLaterFeatureReverse, KLaterFeatureEndCondition)
        ReverseOffset = FlagOffset(BlobValue, DepthOffset - ReverseDistance)
        EndConditionOffset = FlagOffset(BlobValue, DepthOffset - EndConditionDistance)
    KindValue = FeatureKind(Feature.flags)
    if KindValue is None:
        raise SldprtFormatError(f'tree node {Feature.name!r} is not a recognised feature')
    return FeatureLayout(ordinal=Ordinal, name=Feature.name, kind=KindValue, feature_id=Feature.feature_id, flags=Feature.flags, flags_offset=Feature.text_end + 4, sketch_name=None if Sketch is None else Sketch.name, sketch_id=None if Sketch is None else Sketch.feature_id, points=Points, arcs=ArcsValue, depth_offset=DepthOffset, depth_mm=DepthMm, depth_copy_offsets=Copies, reverse_offset=ReverseOffset, end_condition_offset=EndConditionOffset, reversed=None if ReverseOffset is None else bool(BlobValue[ReverseOffset]), end_condition_code=None if EndConditionOffset is None else BlobValue[EndConditionOffset], from_reverse_offset=FromReverseOffset, swept_arcs=SweptArcs, SketchDimensionOffsets=tuple((ItemData.value_offset for ItemData in SketchScalars)), SketchDimensionsMm=tuple((ItemData.value_mm for ItemData in SketchScalars)))

# this definition exists because focused behavior needs one stable owner
def FlagOffset(BlobValue: bytes, Offset: int) -> int | None:
    return Offset if 0 <= Offset < len(BlobValue) else None

# this definition exists because focused behavior needs one stable owner
def ValidateEditA(Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.depth_mm is not None or EditValue.update_depth_copies:
        raise SldprtFormatError(f'feature {Feature.ordinal} is a {Feature.kind} and carries an angle, not a depth')
    if EditValue.reversed is not None:
        raise SldprtFormatError(f'feature {Feature.ordinal} is a {Feature.kind} and its direction flag is not located, so a direction cannot be written')
    if EditValue.end_condition_code is not None:
        raise SldprtFormatError(f'feature {Feature.ordinal} is a {Feature.kind} and its end specification is a constant, so an end condition cannot be written')
    if EditValue.angle_radians is None:
        return
    if Feature.angle_offset is None:
        raise SldprtFormatError(f'feature {Feature.ordinal} has no dimension scalar to hold an angle')
    if not MathValue.isfinite(EditValue.angle_radians) or EditValue.angle_radians <= 0.0 or EditValue.angle_radians > KFullRevolutionRadians + KAngleToleranceRadians:
        raise SldprtFormatError('revolution angle must be finite and inside (0, 2*pi] radians')

# this definition exists because focused behavior needs one stable owner
def ValidateEdit(Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if Feature.is_revolution:
        ValidateEditA(Feature, EditValue)
    elif EditValue.angle_radians is not None:
        raise SldprtFormatError(f'feature {Feature.ordinal} is a {Feature.kind} and carries a depth, not a revolution angle')
    if EditValue.reversed is not None and Feature.reverse_offset is None:
        raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable direction flag')
    if EditValue.end_condition_code is not None and Feature.end_condition_offset is None:
        raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable end condition')
    ValidatePoints(Feature, EditValue)
    ValidateArcs(Feature, EditValue)
    ValidateSwept(Feature, EditValue)
    ValidateScalar(Feature, EditValue)

# this definition exists because sketch point validation has one coordinate contract
def ValidatePoints(Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.corners_mm is not None:
        if len(EditValue.corners_mm) != len(Feature.points):
            raise SldprtFormatError(f'feature {Feature.ordinal} has {len(Feature.points)} sketch points and {len(EditValue.corners_mm)} corners were supplied')
        if not Feature.points:
            raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable sketch points')
        if not all((MathValue.isfinite(Value) for Corner in EditValue.corners_mm for Value in Corner)):
            raise SldprtFormatError('sketch corner values must be finite')

# this definition exists because circular arc edits share radius and centre invariants
def ValidateArcs(Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.radii_mm is not None:
        if not Feature.arcs:
            raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable sketch arcs')
        if len(EditValue.radii_mm) != len(Feature.arcs):
            raise SldprtFormatError(f'feature {Feature.ordinal} has {len(Feature.arcs)} sketch arcs and {len(EditValue.radii_mm)} radii were supplied')
        if not all((MathValue.isfinite(Radius) and Radius > 0.0 for Radius in EditValue.radii_mm)):
            raise SldprtFormatError('sketch radii must be finite and positive')
    if EditValue.arc_centres_mm is not None:
        if EditValue.radii_mm is None:
            raise SldprtFormatError('sketch arc centres can only be moved together with their radii')
        if len(EditValue.arc_centres_mm) != len(Feature.arcs):
            raise SldprtFormatError(f'feature {Feature.ordinal} has {len(Feature.arcs)} sketch arcs and {len(EditValue.arc_centres_mm)} centres were supplied')
        if not all((MathValue.isfinite(Value) for Centre in EditValue.arc_centres_mm for Value in Centre)):
            raise SldprtFormatError('sketch arc centre values must be finite')

# this definition exists because swept arc centres depend on matching profile vertices
def ValidateSwept(Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.swept_arc_centres_mm is not None:
        if not Feature.swept_arcs:
            raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable swept sketch arcs')
        if len(EditValue.swept_arc_centres_mm) != len(Feature.swept_arcs):
            raise SldprtFormatError(f'feature {Feature.ordinal} has {len(Feature.swept_arcs)} swept sketch arcs and {len(EditValue.swept_arc_centres_mm)} centres were supplied')
        if not all((MathValue.isfinite(Value) for Centre in EditValue.swept_arc_centres_mm for Value in Centre)):
            raise SldprtFormatError('swept sketch arc centre values must be finite')
        if EditValue.corners_mm is None:
            raise SldprtFormatError('swept sketch arc centres can only be moved together with the profile vertices that carry their endpoints')

# this definition exists because scalar and flag edits share finite range validation
def ValidateScalar(Feature: FeatureLayout, EditValue: FeatureEdit) -> None:
    if EditValue.SketchDimensionsMm is not None:
        if len(EditValue.SketchDimensionsMm) != len(Feature.SketchDimensionOffsets):
            raise SldprtFormatError(f'feature {Feature.ordinal} has {len(Feature.SketchDimensionOffsets)} sketch dimension scalars and {len(EditValue.SketchDimensionsMm)} values were supplied')
        if not Feature.SketchDimensionOffsets:
            raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable sketch dimensions')
        if not all((MathValue.isfinite(ItemData) and ItemData > 0.0 for ItemData in EditValue.SketchDimensionsMm)):
            raise SldprtFormatError('sketch dimensions must be finite and positive')
    if EditValue.depth_mm is not None:
        if Feature.depth_offset is None:
            raise SldprtFormatError(f'feature {Feature.ordinal} has no dimension scalar to hold a depth')
        if not MathValue.isfinite(EditValue.depth_mm) or EditValue.depth_mm <= 0.0:
            raise SldprtFormatError('extrusion depth must be finite and positive')
    if EditValue.update_depth_copies and EditValue.depth_mm is None:
        raise SldprtFormatError('depth copies can only be updated together with a depth')
    if EditValue.reversed is not None and Feature.reverse_offset is None:
        raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable direction flag')
    if EditValue.end_condition_code is not None:
        if Feature.end_condition_offset is None:
            raise SldprtFormatError(f'feature {Feature.ordinal} has no locatable end condition flag')
        if EditValue.end_condition_code not in KSupportedEndConditions:
            raise SldprtFormatError(f'unsupported SOLIDWORKS end condition code {EditValue.end_condition_code}')

# this definition exists because focused behavior needs one stable owner
def VerifyFeatures(Patched: bytes, Features: tuple[FeatureLayout, ...], Edits: Mapping[int, FeatureEdit]) -> None:
    Verification = LocateFeatures(Patched)
    if len(Verification) != len(Features):
        raise SldprtFormatError('patched resolved-features stream cannot be relocated')
    for Ordinal in sorted(Edits):
        EditValue = Edits[Ordinal]
        Before = Features[Ordinal]
        After = Verification[Ordinal]
        VerifyLayout(Before, After, Ordinal)
        VerifyProfile(Before, After, EditValue, Ordinal)
        VerifyScalars(Patched, After, EditValue, Ordinal)

# this definition exists because relocated features must retain every native field offset
def VerifyLayout(Before: FeatureLayout, After: FeatureLayout, Ordinal: int) -> None:
    if After.feature_id != Before.feature_id or After.kind != Before.kind or After.depth_offset != Before.depth_offset or (After.angle_offset != Before.angle_offset) or (tuple((Point.offset for Point in After.points)) != tuple((Point.offset for Point in Before.points))) or (tuple((ArcValue.centre_offset for ArcValue in After.arcs)) != tuple((ArcValue.centre_offset for ArcValue in Before.arcs))) or (tuple((ArcValue.centre_offset for ArcValue in After.swept_arcs)) != tuple((ArcValue.centre_offset for ArcValue in Before.swept_arcs))) or (After.SketchDimensionOffsets != Before.SketchDimensionOffsets):
        raise SldprtFormatError(f'patched feature {Ordinal} does not relocate to the same layout')

# this definition exists because patched profile geometry needs one verification boundary
def VerifyProfile(Before: FeatureLayout, After: FeatureLayout, EditValue: FeatureEdit, Ordinal: int) -> None:
    if EditValue.swept_arc_centres_mm is not None:
        if not IsMatches(tuple((ArcValue.centre_mm for ArcValue in After.swept_arcs)), tuple(EditValue.swept_arc_centres_mm)):
            raise SldprtFormatError(f'patched feature {Ordinal} swept arc centres do not verify')
        for Index, ArcValue in enumerate(After.swept_arcs):
            if not ArcValue.consistent:
                raise SldprtFormatError(f'patched feature {Ordinal} swept arc {Index} endpoints are not equidistant from its centre')
    if EditValue.SketchDimensionsMm is not None and (not all((MathValue.isclose(ActualValue, ExpectedValue, rel_tol=1e-12, abs_tol=1e-09) for ActualValue, ExpectedValue in zip(After.SketchDimensionsMm, EditValue.SketchDimensionsMm, strict=True)))):
        raise SldprtFormatError(f'patched feature {Ordinal} sketch dimensions do not verify')
    if EditValue.corners_mm is not None and (not IsMatches(After.corners_mm, tuple(EditValue.corners_mm))):
        raise SldprtFormatError(f'patched feature {Ordinal} corners do not verify')
    if EditValue.radii_mm is not None:
        for Index, (ArcValue, RadiusMm) in enumerate(zip(After.arcs, EditValue.radii_mm, strict=True)):
            VerifyArc(ArcValue, Before.arcs[Index], RadiusMm, Index)
    if EditValue.arc_centres_mm is not None and (not IsMatches(tuple((ArcValue.centre_mm for ArcValue in After.arcs)), tuple(EditValue.arc_centres_mm))):
        raise SldprtFormatError(f'patched feature {Ordinal} arc centres do not verify')

# this definition exists because patched scalar and flag values share one verification boundary
def VerifyScalars(Patched: bytes, After: FeatureLayout, EditValue: FeatureEdit, Ordinal: int) -> None:
    if EditValue.angle_radians is not None and (After.angle_radians is None or not MathValue.isclose(After.angle_radians, EditValue.angle_radians, rel_tol=1e-12, abs_tol=1e-12)):
        raise SldprtFormatError(f'patched feature {Ordinal} angle does not verify')
    if EditValue.depth_mm is not None:
        if After.depth_mm is None or not MathValue.isclose(After.depth_mm, EditValue.depth_mm, rel_tol=1e-12, abs_tol=1e-09):
            raise SldprtFormatError(f'patched feature {Ordinal} depth does not verify')
        if EditValue.update_depth_copies and (not IsDepthCopies(Patched, After, EditValue.depth_mm)):
            raise SldprtFormatError(f'patched feature {Ordinal} depth copies do not verify')
    if EditValue.reversed is not None:
        if After.reversed is not bool(EditValue.reversed):
            raise SldprtFormatError(f'patched feature {Ordinal} direction does not verify')
        Mirror = After.from_reverse_offset
        if Mirror is not None and bool(Patched[Mirror]) is not bool(EditValue.reversed):
            raise SldprtFormatError(f'patched feature {Ordinal} mirrored direction does not verify')
    if EditValue.end_condition_code is not None and After.end_condition_code != EditValue.end_condition_code:
        raise SldprtFormatError(f'patched feature {Ordinal} end condition does not verify')

# this definition exists because focused behavior needs one stable owner
def IsDepthCopies(Patched: bytes, Feature: FeatureLayout, DepthMm: float) -> bool:
    for Offset, SignValue in zip(Feature.depth_copy_offsets, KDepthCopySigns, strict=False):
        Value = ReadDouble(Patched, Offset)
        if Value is None or not MathValue.isclose(Value * KMetres, SignValue * DepthMm, rel_tol=1e-12, abs_tol=1e-09):
            return False
    return True

# this definition exists because focused behavior needs one stable owner
def ReadDouble(BlobValue: bytes, Offset: int) -> float | None:
    if Offset < 0 or Offset + 8 > len(BlobValue):
        return None
    Value = Struct.unpack_from('<d', BlobValue, Offset)[0]
    if not MathValue.isfinite(Value):
        return None
    return Value

# this definition exists because focused behavior needs one stable owner
def IsMatches(Actual: tuple[tuple[float, float], ...], Expected: tuple[tuple[float, float], ...]) -> bool:
    if len(Actual) != len(Expected):
        return False
    return all((MathValue.isclose(LeftValue, Right, rel_tol=1e-12, abs_tol=1e-09) for PairValue, Target in zip(Actual, Expected, strict=True) for LeftValue, Right in zip(PairValue, Target, strict=True)))

# this binding exists because shared behavior needs one stable value
globals()['ANGLE_COPY_DELTAS'] = KAngleCopyDeltas

# this binding exists because shared behavior needs one stable value
globals()['ANGLE_PARAMETER_CLASS'] = KAngleParamClass

# this binding exists because shared behavior needs one stable value
globals()['BLIND_END_CONDITION'] = KBlindEndCondition

# this binding exists because shared behavior needs one stable value
globals()['BOSS_FLAGS'] = KBossFlags

# this binding exists because shared behavior needs one stable value
globals()['BOSS_KIND'] = KBossKind

# this binding exists because shared behavior needs one stable value
globals()['CIRCLE_POINT_ANGLE_DEGREES'] = KCirclePointAngleDegrees

# this binding exists because shared behavior needs one stable value
globals()['CIRCLE_POINT_ANGLE_TOLERANCE_DEGREES'] = KCirclePointAngleToleranA

# this binding exists because shared behavior needs one stable value
globals()['CLASS_MARKER'] = ClassMarker

# this binding exists because shared behavior needs one stable value
globals()['CUT_FLAGS'] = KCutFlags

# this binding exists because shared behavior needs one stable value
globals()['CUT_KIND'] = KCutKind

# this binding exists because shared behavior needs one stable value
globals()['DEPTH_COPY_DELTAS'] = KDepthCopyDeltas

# this binding exists because shared behavior needs one stable value
globals()['DEPTH_COPY_SIGNS'] = KDepthCopySigns

# this binding exists because shared behavior needs one stable value
globals()['DEPTH_RELATIVE'] = KDepthRelative

# this binding exists because shared behavior needs one stable value
globals()['DEPTH_SCALAR_NAME_PREFIX'] = KDepthScalarNamePrefix

# this binding exists because shared behavior needs one stable value
globals()['END_CONDITION_RELATIVE'] = KEndConditionRelative

# this binding exists because shared behavior needs one stable value
globals()['END_SPEC_CLASS'] = KEndSpecClass

# this binding exists because shared behavior needs one stable value
globals()['FEATURE_FLAGS_MASK'] = KFeatureFlagsMask

# this binding exists because shared behavior needs one stable value
globals()['FEATURE_KIND_BY_FLAGS'] = KFeatureKindByFlags

# this binding exists because shared behavior needs one stable value
globals()['FIRST_FEATURE_END_CONDITION_DISTANCE'] = KFirstFeatureEndCondition

# this binding exists because shared behavior needs one stable value
globals()['FIRST_FEATURE_REVERSE_DISTANCE'] = KFirstFeatureReverse

# this binding exists because shared behavior needs one stable value
globals()['FROM_END_SPEC_CLASS'] = KFromEndSpecClass

# this binding exists because shared behavior needs one stable value
globals()['FROM_REVERSE_RELATIVE'] = KFromReverseRelative

# this binding exists because shared behavior needs one stable value
globals()['FULL_CIRCLE_DEGREES'] = KFullCircleDegrees

# this binding exists because shared behavior needs one stable value
globals()['FULL_REVOLUTION_RADIANS'] = KFullRevolutionRadians

# this binding exists because shared behavior needs one stable value
globals()['LATER_FEATURE_END_CONDITION_DISTANCE'] = KLaterFeatureEndCondition

# this binding exists because shared behavior needs one stable value
globals()['LATER_FEATURE_REVERSE_DISTANCE'] = KLaterFeatureReverse

# this binding exists because shared behavior needs one stable value
globals()['LENGTH_PARAMETER_CLASS'] = KLengthParamClass

# this binding exists because shared behavior needs one stable value
globals()['LOFT_FLAGS'] = KLoftFlags

# this binding exists because shared behavior needs one stable value
globals()['LOFT_KIND'] = KLoftKind

# this binding exists because shared behavior needs one stable value
globals()['MID_PLANE_END_CONDITION'] = KMidPlaneEndCondition

# this binding exists because shared behavior needs one stable value
globals()['PLANE_FLAGS'] = KPlaneFlags

# this binding exists because shared behavior needs one stable value
globals()['PROFILE_CLASS'] = KProfileClass

# this binding exists because shared behavior needs one stable value
globals()['PatchSketchPlane'] = PatchSketch

# this binding exists because shared behavior needs one stable value
globals()['RECTANGLE_POINT_RELATIVE'] = KRectanglePointRelative

# this binding exists because shared behavior needs one stable value
globals()['REVERSE_RELATIVE'] = KReverseRelative

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_AXIS_REFERENCE'] = KRevolutionAxisRef

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_AXIS_REFERENCE_RELATIVE'] = KRevolutionAxisRefRelatiA

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_AXIS_SKETCH'] = KRevolutionAxisSketch

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_AXIS_SKETCH_RELATIVE'] = KRevolutionAxisSketchA

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_CLASS'] = KRevolutionClass

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_CLASS_REFERENCE_BYTES'] = KRevolutionClassRefBytes

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_CUT_CLASS'] = KRevolutionCutClass

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_END_SPEC_CLASS'] = KRevolutionEndSpecClass

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_END_SPEC_CLASS_BYTES'] = KRevolutionEndSpecClassA

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_END_SPEC_DATA'] = KRevolutionEndSpecData

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_END_SPEC_HEADER'] = KRevolutionEndSpecHeader

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_STAMP_HIGH'] = KRevolutionStampHigh

# this binding exists because shared behavior needs one stable value
globals()['REVOLUTION_STAMP_LOW'] = KRevolutionStampLow

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_CUT_KIND'] = KRevolveCutKind

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_CUT_NAME_STEMS'] = KRevolveCutNameStems

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_KIND'] = KRevolveKind

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_KINDS'] = KRevolveKinds

# this binding exists because shared behavior needs one stable value
globals()['REVOLVE_NAME_STEMS'] = KRevolveNameStems

# this binding exists because shared behavior needs one stable value
globals()['ROUND_FLAGS'] = KRoundFlags

# this binding exists because shared behavior needs one stable value
globals()['ROUND_KIND'] = KRoundKind

# this binding exists because shared behavior needs one stable value
globals()['RectanglePadLayout'] = RectanglePad

# this binding exists because shared behavior needs one stable value
globals()['SERIALIZED_STRING_MARKER'] = SerializedStringMarker

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_ARC_CENTRE_CLASS'] = KSketchArcCentreClass

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_CHAIN_CLASS'] = KSketchChainClass

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_COORDINATE_PREFIX'] = KSketchCoordinatePrefix

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_FLAGS'] = KSketchFlags

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_FREE_ROLE'] = KSketchFreeRole

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_NAME_PREFIX'] = KSketchNamePrefix

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_ON_CURVE_ROLE'] = KSketchOnCurveRole

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_POINT_CLASS'] = KSketchPointClass

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_POINT_PREFIX'] = KSketchPointPrefix

# this binding exists because shared behavior needs one stable value
globals()['SKETCH_POINT_SUFFIX'] = KSketchPointSuffix

# this binding exists because shared behavior needs one stable value
globals()['SUPPORTED_END_CONDITIONS'] = KSupportedEndConditions

# this binding exists because shared behavior needs one stable value
globals()['SWEEP_FLAGS'] = KSweepFlags

# this binding exists because shared behavior needs one stable value
globals()['SWEEP_KIND'] = KSweepKind

# this binding exists because shared behavior needs one stable value
globals()['SWEEP_SINGLE_PROFILE_FLAGS'] = KSweepSingleProfileFlags

# this binding exists because shared behavior needs one stable value
globals()['SketchCoordinate'] = Sketch

# this binding exists because shared behavior needs one stable value
globals()['TREE_NODE_FLAGS'] = KTreeNodeFlags

# this binding exists because shared behavior needs one stable value
globals()['_ANGLE_TOLERANCE_RADIANS'] = KAngleToleranceRadians

# this binding exists because shared behavior needs one stable value
globals()['_ARC_RADIUS_TOLERANCE_MM'] = KArcRadiusToleranceMm

# this binding exists because shared behavior needs one stable value
globals()['_COORDINATE_TRAILER_BYTES'] = KCoordinateTrailerBytes

# this binding exists because shared behavior needs one stable value
globals()['_MAX_CLASS_NAME'] = KMaxClassName

# this binding exists because shared behavior needs one stable value
globals()['_MAX_FEATURE_ID'] = KMaxFeatureId

# this binding exists because shared behavior needs one stable value
globals()['_MAX_NAME_UNITS'] = KMaxNameUnits

# this binding exists because shared behavior needs one stable value
globals()['_METRES'] = KMetres

# this binding exists because shared behavior needs one stable value
globals()['_MINIMUM_RADIUS_MM'] = KMinimumRadiusMm

# this binding exists because shared behavior needs one stable value
globals()['_NAME_MARKER_CLASS_TOKEN'] = KNameMarkerClassToken

# this binding exists because shared behavior needs one stable value
globals()['_NAME_TRAILER_BYTES'] = KNameTrailerBytes

# this binding exists because shared behavior needs one stable value
globals()['_RADIANS_TO_DEGREES'] = KRadiansToDegrees

# this binding exists because shared behavior needs one stable value
globals()['_SketchScalarsInRange'] = SketchScalarsIn

# this binding exists because shared behavior needs one stable value
globals()['_arcs_in_range'] = ArcsInRange

# this binding exists because shared behavior needs one stable value
globals()['_depth_copies_verify'] = IsDepthCopies

# this binding exists because shared behavior needs one stable value
globals()['_dimension_scalars'] = Dimension

# this binding exists because shared behavior needs one stable value
globals()['_feature_layout'] = FeatureLayoutA

# this binding exists because shared behavior needs one stable value
globals()['_flag_offset'] = FlagOffset

# this binding exists because shared behavior needs one stable value
globals()['_last_node_in_range'] = LastNodeInRange

# this binding exists because shared behavior needs one stable value
globals()['_matches'] = IsMatches

# this binding exists because shared behavior needs one stable value
globals()['_name_records'] = NameRecords

# this binding exists because shared behavior needs one stable value
globals()['_points_in_range'] = PointsInRange

# this binding exists because shared behavior needs one stable value
globals()['_read_double'] = ReadDouble

# this binding exists because shared behavior needs one stable value
globals()['_revolution_layout'] = Revolution

# this binding exists because shared behavior needs one stable value
globals()['_revolution_nodes'] = RevolutionNodes

# this binding exists because shared behavior needs one stable value
globals()['_sketch_arc'] = SketchArcA

# this binding exists because shared behavior needs one stable value
globals()['_swept_in_range'] = SweptInRange

# this binding exists because shared behavior needs one stable value
globals()['_tree_nodes'] = TreeNodes

# this binding exists because shared behavior needs one stable value
globals()['_validate_edit'] = ValidateEdit

# this binding exists because shared behavior needs one stable value
globals()['_validate_revolution_edit'] = ValidateEditA

# this binding exists because shared behavior needs one stable value
globals()['_verify_arc'] = VerifyArc

# this binding exists because shared behavior needs one stable value
globals()['_verify_features'] = VerifyFeatures

# this binding exists because shared behavior needs one stable value
globals()['_write_arc_radius'] = WriteArcRadius

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['circle_circumference_point_mm'] = CirclePointMm

# this binding exists because shared behavior needs one stable value
globals()['circle_radius_mm'] = CircleRadiusMm

# this binding exists because shared behavior needs one stable value
globals()['class_records'] = ClassRecords

# this binding exists because shared behavior needs one stable value
globals()['dataclass'] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()['dimension_scalar_value_offset'] = DimensionScalarValue

# this binding exists because shared behavior needs one stable value
globals()['dimension_scalars'] = DimensionA

# this binding exists because shared behavior needs one stable value
globals()['feature_kind'] = FeatureKind

# this binding exists because shared behavior needs one stable value
globals()['first_class_offset'] = FirstClass

# this binding exists because shared behavior needs one stable value
globals()['is_tree_node_flags'] = IsTreeNodeFlags

# this binding exists because shared behavior needs one stable value
globals()['locate_features'] = LocateFeatures

# this binding exists because shared behavior needs one stable value
globals()['locate_rectangle_pad'] = LocateRectangle

# this binding exists because shared behavior needs one stable value
globals()['math'] = MathValue

# this binding exists because shared behavior needs one stable value
globals()['name_marker'] = NameMarker

# this binding exists because shared behavior needs one stable value
globals()['name_records'] = NameRecordsA

# this binding exists because shared behavior needs one stable value
globals()['patch_features'] = PatchFeatures

# this binding exists because shared behavior needs one stable value
globals()['patch_sketch_arcs'] = PatchSketchArcs

# this binding exists because shared behavior needs one stable value
globals()['rectangle_corners_mm'] = RectangleMm

# this binding exists because shared behavior needs one stable value
globals()['revolution_axis_source'] = RevolutionAxis

# this binding exists because shared behavior needs one stable value
globals()['revolution_end_spec_objects'] = RevolutionEnd

# this binding exists because shared behavior needs one stable value
globals()['revolution_kind_by_name'] = RevolutionKind

# this binding exists because shared behavior needs one stable value
globals()['sketch_arcs'] = SketchArcs

# this binding exists because shared behavior needs one stable value
globals()['sketch_coordinates'] = SketchA

# this binding exists because shared behavior needs one stable value
globals()['sketch_plane_object_id'] = SketchPlaneId

# this binding exists because shared behavior needs one stable value
globals()['sketch_points'] = SketchPoints

# this binding exists because shared behavior needs one stable value
globals()['struct'] = Struct

# this binding exists because shared behavior needs one stable value
globals()['swept_arcs'] = SweptArcs

# this binding exists because shared behavior needs one stable value
globals()['tree_nodes'] = TreeNodesA

# this binding exists because shared behavior needs one stable value
globals()['DepthCopies'] = IsDepthCopies

# this binding exists because shared behavior needs one stable value
globals()['Matches'] = IsMatches
