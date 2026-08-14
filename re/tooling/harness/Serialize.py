# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass, field as FieldInfo
import math as MathLib
from pathlib import Path as PathInfo
import struct as Struct
import sys as System
import time as TimeInfo

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KScratch = KHereInfo.parents[2] / '.rescratch'
if str(KHereInfo) not in System.path:
    System.path.insert(0, str(KHereInfo))
import Carchive as Carchive
import Streamlib as Streamlib
from convert.adapters.solidworks import resolved as Resolvedlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KSkeletons = KScratch / 'grammar' / 'skeletons'

# needed to keep reverse engineering responsibilities isolated and maintainable
KMetre = 1000.0

# needed to keep reverse engineering responsibilities isolated and maintainable
KCircleDegrees = 17.0

# needed to keep reverse engineering responsibilities isolated and maintainable
KPlaneMargin = 1.1

# needed to keep reverse engineering responsibilities isolated and maintainable
KPlaneIds = {'front': 2, 'top': 3, 'right': 4}

# needed to keep reverse engineering responsibilities isolated and maintainable
KEndConditions = {'blind': 0, 'throughall': 1, 'midplane': 6}

# needed to keep reverse engineering responsibilities isolated and maintainable
KeywordsPrefix = b'\x86'

# needed to keep reverse engineering responsibilities isolated and maintainable
KSketchIdBase = 26

# needed to keep reverse engineering responsibilities isolated and maintainable
KFeatIdBase = 32

# needed to keep reverse engineering responsibilities isolated and maintainable
KIdStride = 7

# needed to keep reverse engineering responsibilities isolated and maintainable
KBboxClass = 'moBBoxCenterData_c'

# needed to keep reverse engineering responsibilities isolated and maintainable
KBboxRelative = 28

# needed to keep reverse engineering responsibilities isolated and maintainable
KBboxInfo = 52

# needed to keep reverse engineering responsibilities isolated and maintainable
KRefClassInfo = 'moDefaultRefPlnData_c'

# needed to keep reverse engineering responsibilities isolated and maintainable
KRefPlaneClass = 'moRefPlane_c'


# needed to keep reverse engineering responsibilities isolated and maintainable
class SerializeError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Rectangle:
    WidthMm: float
    HeightMm: float
    CentreXMm: float = 0.0
    CentreYMm: float = 0.0


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def KindNameInfo(SelfRef) -> str:
        return 'rectangle'


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def AreaMmTwo(SelfRef) -> float:
        return SelfRef.WidthMm * SelfRef.HeightMm


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def CornersMm(SelfRef) -> tuple[tuple[float, float], ...]:
        HalfX = SelfRef.WidthMm / 2.0
        HalfY = SelfRef.HeightMm / 2.0
        return Resolvedlib.rectangle_corners_mm(SelfRef.CentreXMm - HalfX, SelfRef.CentreYMm - HalfY, SelfRef.CentreXMm + HalfX, SelfRef.CentreYMm + HalfY)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def BoundsMm(SelfRef) -> tuple[float, float, float, float]:
        HalfX = SelfRef.WidthMm / 2.0
        HalfY = SelfRef.HeightMm / 2.0
        return (SelfRef.CentreXMm - HalfX, SelfRef.CentreYMm - HalfY, SelfRef.CentreXMm + HalfX, SelfRef.CentreYMm + HalfY)
    KAliasNames = {'width_mm': 'WidthMm', 'height_mm': 'HeightMm', 'centre_x_mm': 'CentreXMm', 'centre_y_mm': 'CentreYMm', 'kind': 'KindNameInfo', 'area_mm2': 'AreaMmTwo', 'corners_mm': 'CornersMm', 'bounds_mm': 'BoundsMm'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Circle:
    RadiusMm: float
    CentreXMm: float = 0.0
    CentreYMm: float = 0.0


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def KindNameInfo(SelfRef) -> str:
        return 'circle'


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def AreaMmTwo(SelfRef) -> float:
        return MathLib.pi * SelfRef.RadiusMm * SelfRef.RadiusMm


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def BoundsMm(SelfRef) -> tuple[float, float, float, float]:
        return (SelfRef.CentreXMm - SelfRef.RadiusMm, SelfRef.CentreYMm - SelfRef.RadiusMm, SelfRef.CentreXMm + SelfRef.RadiusMm, SelfRef.CentreYMm + SelfRef.RadiusMm)
    KAliasNames = {'radius_mm': 'RadiusMm', 'centre_x_mm': 'CentreXMm', 'centre_y_mm': 'CentreYMm', 'kind': 'KindNameInfo', 'area_mm2': 'AreaMmTwo', 'bounds_mm': 'BoundsMm'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Extrude:
    Profile: Rectangle | Circle
    DepthMm: float
    OpInfo: str = 'boss'
    Plane: str = 'front'
    EndCondition: str = 'blind'
    Reversed: bool = False
    Support: str = 'plane'


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def Shape(SelfRef) -> tuple[str, str, str, bool]:
        return (SelfRef.OpInfo, SelfRef.Profile.kind, SelfRef.Support, SelfRef.EndCondition != 'throughall')
    KAliasNames = {'profile': 'Profile', 'depth_mm': 'DepthMm', 'operation': 'OpInfo', 'plane': 'Plane', 'end_condition': 'EndCondition', 'reversed': 'Reversed', 'support': 'Support', 'shape': 'Shape'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class PartInfo:
    FeatInfoInfo: tuple[Extrude, ...]
    NameTextInfo: str = 'KitAuthored'
    DocumentName: str = 'Part1'
    AuthorIds: bool = False
    DedupeIds: bool = False
    WriteCopies: bool = False
    WriteBboxCache: bool = False


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def Shape(SelfRef) -> tuple[tuple[str, str, str, bool], ...]:
        return tuple((FeatInfo.shape for FeatInfo in SelfRef.FeatInfoInfo))
    KAliasNames = {'features': 'FeatInfoInfo', 'name': 'NameTextInfo', 'document_name': 'DocumentName', 'author_ids': 'AuthorIds', 'dedupe_ids': 'DedupeIds', 'write_depth_copies': 'WriteCopies', 'write_bbox_cache': 'WriteBboxCache', 'shape': 'Shape'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Skeleton:
    Shape: tuple[tuple[str, str, str, bool], ...]
    Source: PathInfo
    Resolved: bytes
    Keywords: bytes
    FeatXml: bytes
    DonorInfo: Streamlib.Donor
    Grown: bool = False
    LabelInfo: str = ''


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def NameTextInfo(SelfRef) -> str:
        return SelfRef.LabelInfo or SelfRef.Source.name
    KAliasNames = {'shape': 'Shape', 'source': 'Source', 'resolved': 'Resolved', 'keywords': 'Keywords', 'features_xml': 'FeatXml', 'donor': 'DonorInfo', 'grown': 'Grown', 'label': 'LabelInfo', 'name': 'NameTextInfo'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(slots=True)
class Emission:
    Resolved: bytes
    Keywords: bytes
    FeatXml: bytes
    Writes: list[str] = FieldInfo(default_factory=list)
    SkeletonInfo: str = ''
    KAliasNames = {'resolved': 'Resolved', 'keywords': 'Keywords', 'features_xml': 'FeatXml', 'writes': 'Writes', 'skeleton': 'SkeletonInfo'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __setattr__(SelfRef, NameText, ValueData):
        TargetName = SelfRef.KAliasNames.get(NameText, NameText)
        object.__setattr__(SelfRef, TargetName, ValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SignedExtent(FeatInfo: Extrude) -> tuple[float, float]:
    Depth = FeatInfo.depth_mm
    CodeInfo = KEndConditions[FeatInfo.end_condition]
    if CodeInfo == KEndConditions['midplane']:
        LowValue, HighValue = (-Depth / 2.0, Depth / 2.0)
    else:
        LowValue, HighValue = (0.0, Depth)
    if FeatInfo.reversed:
        LowValue, HighValue = (-HighValue, -LowValue)
    return (LowValue, HighValue)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SolidThree(PartInfoInfo: PartInfo) -> float:
    Total = 0.0
    for FeatInfo in PartInfoInfo.features:
        LowValue, HighValue = SignedExtent(FeatInfo)
        Length = abs(HighValue - LowValue)
        Volume = FeatInfo.profile.area_mm2 * Length
        Total += -Volume if FeatInfo.operation == 'cut' else Volume
    return Total


# needed to keep reverse engineering responsibilities isolated and maintainable
def SketchIds(CountInfo: int) -> tuple[tuple[int, int], ...]:
    return tuple(((KSketchIdBase + IndexData * KIdStride, KFeatIdBase + IndexData * KIdStride) for IndexData in range(CountInfo)))


# needed to keep reverse engineering responsibilities isolated and maintainable
def FeatNames(PartInfoInfo: PartInfo) -> tuple[tuple[str, str], ...]:
    BossInfo = 0
    CutInfo = 0
    Result: list[tuple[str, str]] = []
    for IndexData, FeatInfo in enumerate(PartInfoInfo.features):
        if FeatInfo.operation == 'cut':
            CutInfo += 1
            NameTextInfo = f'Cut-Extrude{CutInfo}'
        else:
            BossInfo += 1
            NameTextInfo = f'Boss-Extrude{BossInfo}'
        Result.append((f'Sketch{IndexData + 1}', NameTextInfo))
    return tuple(Result)

# needed to keep reverse engineering responsibilities isolated and maintainable
KReservedIds = frozenset(range(1, 26))


# needed to keep reverse engineering responsibilities isolated and maintainable
def DedupeIdents(Pairs: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    UsedInfo = {ValueInfo for PairInfo in Pairs for ValueInfo in PairInfo} | set(KReservedIds)
    Cursor = max(UsedInfo) + 1
    SeenInfo: set[int] = set()
    Result: list[tuple[int, int]] = []
    for SketchId, FeatId in Pairs:
        if SketchId in SeenInfo or FeatId in SeenInfo:
            SketchId = Cursor
            FeatId = Cursor + 1
            Cursor += 2
        SeenInfo.add(SketchId)
        SeenInfo.add(FeatId)
        Result.append((SketchId, FeatId))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FeatIdents(ByteBlob: bytes, PartInfoInfo: PartInfo) -> tuple[tuple[int, int], ...]:
    if PartInfoInfo.author_ids:
        return SketchIds(len(PartInfoInfo.features))
    Entries = Streamlib.CompFeatEntries(ByteBlob)
    Pairs = tuple(((Entries[IndexData * 2][2], Entries[IndexData * 2 + 1][2]) for IndexData in range(len(PartInfoInfo.features))))
    return DedupeIdents(Pairs) if PartInfoInfo.dedupe_ids else Pairs


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadSkeletons() -> tuple[Skeleton, ...]:
    Manifest = KSkeletons / 'manifest.json'
    if not Manifest.is_file():
        raise SerializeError(f'skeleton manifest is missing: run build_skeletons.py first ({Manifest})')
    import json as JsonData
    Entries = JsonData.loads(Manifest.read_text(encoding='utf-8'))
    Result: list[Skeleton] = []
    for Entry in Entries:
        Source = PathInfo(Entry['source'])
        DonorInfo = Streamlib.LoadDonor(Source)
        Result.append(Skeleton(Shape=tuple(((ItemData[0], ItemData[1], ItemData[2], bool(ItemData[3])) for ItemData in Entry['shape'])), Source=Source, Resolved=DonorInfo.resolved, Keywords=DonorInfo.streams[Streamlib.KEYWORDS], FeatXml=DonorInfo.streams[Streamlib.KFeatInfo], DonorInfo=DonorInfo))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def GrowSkeleton(Shape: tuple[tuple[str, str, str, bool], ...]) -> Skeleton:
    Scratch = KScratch / 're'
    if str(Scratch) not in System.path:
        System.path.insert(0, str(Scratch))
    import skeletongrow as Skeletongrow
    Resolved, DonorInfo, LabelInfo = Skeletongrow.grow(Shape)
    return Skeleton(Shape=Shape, Source=DonorInfo.path, Resolved=Resolved, Keywords=DonorInfo.streams[Streamlib.KEYWORDS], FeatXml=DonorInfo.streams[Streamlib.KFeatInfo], DonorInfo=DonorInfo, Grown=True, LabelInfo=LabelInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SelectSkeleton(PartInfoInfo: PartInfo, Skeletons: tuple[Skeleton, ...]) -> Skeleton:
    Wanted = PartInfoInfo.shape
    for SkeletonInfo in Skeletons:
        if SkeletonInfo.shape == Wanted:
            return SkeletonInfo
    Scratch = KScratch / 're'
    if str(Scratch) not in System.path:
        System.path.insert(0, str(Scratch))
    import skeletongrow as Skeletongrow
    if Skeletongrow.match(Wanted) is not None:
        return GrowSkeleton(Wanted)
    Available = '; '.join((str(SkeletonInfo.shape) for SkeletonInfo in Skeletons))
    raise SerializeError(f'no skeleton matches shape {Wanted}; available: {Available}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def EmitData(PartInfoInfo: PartInfo, Skeletons: tuple[Skeleton, ...] | None=None) -> Emission:
    Catalogue = LoadSkeletons() if Skeletons is None else Skeletons
    SkeletonInfo = SelectSkeleton(PartInfoInfo, Catalogue)
    if SkeletonInfo.grown and (not PartInfoInfo.author_ids):
        from dataclasses import replace as Replace
        PartInfoInfo = Replace(PartInfoInfo, dedupe_ids=True)
    Output = bytearray(SkeletonInfo.resolved)
    Writes: list[str] = []
    WriteFeatMut(Output, PartInfoInfo, Writes)
    WriteNodesMut(Output, PartInfoInfo, Writes)
    WriteInfoMut(Output, PartInfoInfo, Writes)
    WriteMut(Output, PartInfoInfo, Writes)
    WriteRefMut(Output, PartInfoInfo, Writes)
    WriteCacheMut(Output, PartInfoInfo, Writes)
    WriteDisplayMut(Output, PartInfoInfo, Writes)
    Final = bytes(Output)
    Names = StreamNamesInfo(Final)
    return Emission(Resolved=Final, Keywords=EmitKeywords(PartInfoInfo, Names, FeatIdents(Final, PartInfoInfo)), FeatXml=EmitFeatXml(PartInfoInfo), Writes=Writes, SkeletonInfo=SkeletonInfo.name)


# needed to keep reverse engineering responsibilities isolated and maintainable
def StreamNamesInfo(ByteBlob: bytes) -> tuple[tuple[str, str], ...]:
    Nodes = Streamlib.TreeNodes(ByteBlob)
    Sketches = [NodeInfoInfo.name for NodeInfoInfo in Nodes if NodeInfoInfo.name.startswith('Sketch')]
    FeatInfoInfo = [NodeInfoInfo.name for NodeInfoInfo in Nodes if Resolvedlib.feature_kind(NodeInfoInfo.flags) is not None]
    return tuple(zip(Sketches, FeatInfoInfo, strict=True))


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteFeatMut(Output: bytearray, PartInfoInfo: PartInfo, Writes: list[str]) -> None:
    Entries = Streamlib.CompFeatEntries(bytes(Output))
    Expect = 2 * len(PartInfoInfo.features)
    if len(Entries) != Expect:
        raise SerializeError(f'skeleton has {len(Entries)} moCompFeature_c entries, {Expect} required for {len(PartInfoInfo.features)} features')
    Stamp = int(TimeInfo.time())
    FlatInfo = [ValueInfo for PairInfo in FeatIdents(bytes(Output), PartInfoInfo) for ValueInfo in PairInfo]
    for Entry, Ident in zip(Entries, FlatInfo, strict=True):
        Streamlib.WriteUThirtyTwo(Output, Entry[1] - Streamlib.KCompBack, Ident)
        Streamlib.WriteUThirtyTwo(Output, Entry[1] - Streamlib.KCompBackInfo, Stamp)
    Writes.append(f"moCompFeature_c ids={FlatInfo} stamp={Stamp} ({('authored' if PartInfoInfo.author_ids else 'inherited')})")


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteNodesMut(Output: bytearray, PartInfoInfo: PartInfo, Writes: list[str]) -> None:
    Idents = FeatIdents(bytes(Output), PartInfoInfo)
    Nodes = Streamlib.TreeNodes(bytes(Output))
    Sketches = [NodeInfoInfo for NodeInfoInfo in Nodes if NodeInfoInfo.name.startswith('Sketch')]
    FeatInfoInfo = [NodeInfoInfo for NodeInfoInfo in Nodes if Resolvedlib.feature_kind(NodeInfoInfo.flags) is not None]
    if len(Sketches) != len(PartInfoInfo.features) or len(FeatInfoInfo) != len(PartInfoInfo.features):
        raise SerializeError(f'skeleton exposes {len(Sketches)} sketches and {len(FeatInfoInfo)} features, {len(PartInfoInfo.features)} of each required')
    for IndexData, FeatInfo in enumerate(PartInfoInfo.features):
        SketchId, FeatId = Idents[IndexData]
        Streamlib.WriteUThirtyTwo(Output, Sketches[IndexData].text_end + 8, SketchId)
        NodeInfoInfo = FeatInfoInfo[IndexData]
        Flags = Streamlib.KCutFlags if FeatInfo.operation == 'cut' else Streamlib.KBossFlags
        if Resolvedlib.feature_kind(NodeInfoInfo.flags) != FeatInfo.operation:
            raise SerializeError(f'skeleton feature {IndexData} is a {Resolvedlib.feature_kind(NodeInfoInfo.flags)} and {FeatInfo.operation} was requested; the operation is not writable, see results.md E1/E2/A3')
        Preserved = NodeInfoInfo.flags & 2147483648
        Streamlib.WriteUThirtyTwo(Output, NodeInfoInfo.text_end + 4, Flags | Preserved)
        Streamlib.WriteUThirtyTwo(Output, NodeInfoInfo.text_end + 8, FeatId)
        Writes.append(f'tree[{IndexData}] {NodeInfoInfo.name!r} flags=0x{Flags:08x} at {NodeInfoInfo.text_end + 4}, id={FeatId} at {NodeInfoInfo.text_end + 8}, sketch id={SketchId} at {Sketches[IndexData].text_end + 8}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteInfoMut(Output: bytearray, PartInfoInfo: PartInfo, Writes: list[str]) -> None:
    ByteBlob = bytes(Output)
    Nodes = Streamlib.TreeNodes(ByteBlob)
    Sketches = [NodeInfoInfo for NodeInfoInfo in Nodes if NodeInfoInfo.name.startswith('Sketch')]
    FeatInfoInfo = [NodeInfoInfo for NodeInfoInfo in Nodes if Resolvedlib.feature_kind(NodeInfoInfo.flags) is not None]
    Points = Resolvedlib.sketch_points(ByteBlob)
    ArcsInfo = Resolvedlib.sketch_arcs(ByteBlob)
    for IndexData, FeatInfo in enumerate(PartInfoInfo.features):
        LowValue = Sketches[IndexData].offset
        HighValue = FeatInfoInfo[IndexData].offset
        if isinstance(FeatInfo.profile, Rectangle):
            Owned = [Point for Point in Points if LowValue < Point.offset < HighValue]
            if len(Owned) != 4:
                raise SerializeError(f'skeleton sketch {IndexData} has {len(Owned)} points, 4 required')
            for Point, (Xcoord, Ycoord) in zip(Owned, FeatInfo.profile.corners_mm(), strict=True):
                Streamlib.WriteDouble(Output, Point.offset, Xcoord / KMetre)
                Streamlib.WriteDouble(Output, Point.offset + 8, Ycoord / KMetre)
            Writes.append(f'sketch[{IndexData}] rectangle {FeatInfo.profile.corners_mm()} at {[Point.offset for Point in Owned]}')
            continue
        OwnedArcs = [ArcInfo for ArcInfo in ArcsInfo if LowValue < ArcInfo.centre_offset < HighValue]
        if len(OwnedArcs) != 1:
            raise SerializeError(f'skeleton sketch {IndexData} has {len(OwnedArcs)} arcs, 1 required')
        ArcInfo = OwnedArcs[0]
        CentreX = FeatInfo.profile.centre_x_mm / KMetre
        CentreY = FeatInfo.profile.centre_y_mm / KMetre
        Angle = MathLib.radians(KCircleDegrees)
        Radius = FeatInfo.profile.radius_mm / KMetre
        Streamlib.WriteDouble(Output, ArcInfo.centre_offset, CentreX)
        Streamlib.WriteDouble(Output, ArcInfo.centre_offset + 8, CentreY)
        Streamlib.WriteDouble(Output, ArcInfo.point_offset, CentreX + Radius * MathLib.cos(Angle))
        Streamlib.WriteDouble(Output, ArcInfo.point_offset + 8, CentreY + Radius * MathLib.sin(Angle))
        Writes.append(f'sketch[{IndexData}] circle r={FeatInfo.profile.radius_mm} centre@{ArcInfo.centre_offset} point@{ArcInfo.point_offset}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteMut(Output: bytearray, PartInfoInfo: PartInfo, Writes: list[str]) -> None:
    Layouts = Resolvedlib.locate_features(bytes(Output))
    if len(Layouts) != len(PartInfoInfo.features):
        raise SerializeError(f'skeleton exposes {len(Layouts)} extrusions, {len(PartInfoInfo.features)} required')
    for IndexData, FeatInfo in enumerate(PartInfoInfo.features):
        Layout = Layouts[IndexData]
        CodeInfo = KEndConditions[FeatInfo.end_condition]
        if Layout.depth_offset is None:
            if CodeInfo != KEndConditions['throughall']:
                raise SerializeError(f'skeleton feature {IndexData} has no dimension scalar, only ThroughAll can be emitted')
            Writes.append(f'extrude[{IndexData}] ThroughAll, no scalar in skeleton')
            continue
        BaseInfo = FeatInfo.depth_mm / KMetre
        Deltas = Resolvedlib.DEPTH_COPY_DELTAS if PartInfoInfo.write_depth_copies else (0,)
        Signs = Resolvedlib.DEPTH_COPY_SIGNS if PartInfoInfo.write_depth_copies else (1,)
        for Delta, SignInfo in zip(Deltas, Signs, strict=True):
            Target = Layout.depth_offset + Delta
            if Target + 8 <= len(Output):
                Streamlib.WriteDouble(Output, Target, SignInfo * BaseInfo)
        Output[Layout.reverse_offset] = 1 if FeatInfo.reversed else 0
        Output[Layout.end_condition_offset] = CodeInfo
        Writes.append(f'extrude[{IndexData}] depth={FeatInfo.depth_mm} at {Layout.depth_offset} copies={list(Deltas)}, reverse={int(FeatInfo.reversed)} at {Layout.reverse_offset}, end={CodeInfo} at {Layout.end_condition_offset}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteRefMut(Output: bytearray, PartInfoInfo: PartInfo, Writes: list[str]) -> None:
    ByteBlob = bytes(Output)
    RecordsInfo = Resolvedlib.class_records(ByteBlob)
    Chain = Resolvedlib.first_class_offset(RecordsInfo, Resolvedlib.SKETCH_CHAIN_CLASS)
    if Chain is None:
        return
    Wanted = KPlaneIds[PartInfoInfo.features[0].plane]
    for Offset in range(Chain, min(Chain + 400, len(ByteBlob) - 14)):
        CandInfo = Struct.unpack_from('<I', ByteBlob, Offset)[0]
        if CandInfo not in {2, 3, 4}:
            continue
        if Struct.unpack_from('<I', ByteBlob, Offset + 10)[0] != 5 - CandInfo:
            continue
        Streamlib.WriteUThirtyTwo(Output, Offset, Wanted)
        Streamlib.WriteUThirtyTwo(Output, Offset + 10, 5 - Wanted)
        Writes.append(f'sketch plane id={Wanted} axis={5 - Wanted} at {Offset}/{Offset + 10}')
        return


# needed to keep reverse engineering responsibilities isolated and maintainable
def BodyBoundsMm(PartInfoInfo: PartInfo) -> tuple[float, float, float, float, float, float]:
    MinimumX = MinimumY = MinimumZ = MathLib.inf
    MaximumX = MaximumY = MaximumZ = -MathLib.inf
    for FeatInfo in PartInfoInfo.features:
        if FeatInfo.operation == 'cut':
            continue
        LowXInfo, LowYInfo, HighX, HighY = FeatInfo.profile.bounds_mm()
        LowZInfo, HighZ = SignedExtent(FeatInfo)
        MinimumX = min(MinimumX, LowXInfo)
        MaximumX = max(MaximumX, HighX)
        MinimumY = min(MinimumY, LowYInfo)
        MaximumY = max(MaximumY, HighY)
        MinimumZ = min(MinimumZ, LowZInfo)
        MaximumZ = max(MaximumZ, HighZ)
    if not MathLib.isfinite(MinimumX):
        raise SerializeError('a part needs at least one additive feature')
    Plane = PartInfoInfo.features[0].plane
    if Plane == 'front':
        return (MinimumX, MaximumX, MinimumY, MaximumY, MinimumZ, MaximumZ)
    if Plane == 'top':
        return (MinimumX, MaximumX, MinimumZ, MaximumZ, MinimumY, MaximumY)
    return (MinimumZ, MaximumZ, MinimumY, MaximumY, MinimumX, MaximumX)


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteCacheMut(Output: bytearray, PartInfoInfo: PartInfo, Writes: list[str]) -> None:
    ByteBlob = bytes(Output)
    RecordsInfo = Resolvedlib.class_records(ByteBlob)
    Offset = Resolvedlib.first_class_offset(RecordsInfo, KBboxClass)
    if Offset is None:
        return
    if not PartInfoInfo.write_bbox_cache:
        Writes.append(f'{KBboxClass} left stale (derived body bounding cache)')
        return
    if any((FeatInfo.support != 'plane' for FeatInfo in PartInfoInfo.features)):
        Writes.append(f'{KBboxClass} left stale: a face-supported feature makes the sketch-frame extent unknown to the writer')
        return
    if len({FeatInfo.plane for FeatInfo in PartInfoInfo.features}) != 1:
        Writes.append(f'{KBboxClass} left stale: features span several planes')
        return
    LowXInfo, HighX, LowYInfo, HighY, LowZInfo, HighZ = BodyBoundsMm(PartInfoInfo)
    Centre = ((LowXInfo + HighX) / 2.0, (LowYInfo + HighY) / 2.0, (LowZInfo + HighZ) / 2.0)
    HalfInfo = ((HighX - LowXInfo) / 2.0, (HighY - LowYInfo) / 2.0, (HighZ - LowZInfo) / 2.0)
    Diameter = 2.0 * MathLib.sqrt(sum((ValueInfo * ValueInfo for ValueInfo in HalfInfo)))
    BaseInfo = Offset + KBboxRelative
    for IndexData, ValueInfo in enumerate(Centre):
        Streamlib.WriteDouble(Output, BaseInfo + IndexData * 8, ValueInfo / KMetre)
    Streamlib.WriteDouble(Output, Offset + KBboxInfo, Diameter / KMetre)
    Writes.append(f'{KBboxClass} centre={Centre} diameter={Diameter} at {BaseInfo}/{Offset + KBboxInfo}')


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteDisplayMut(Output: bytearray, PartInfoInfo: PartInfo, Writes: list[str]) -> None:
    ByteBlob = bytes(Output)
    RecordsInfo = Resolvedlib.class_records(ByteBlob)
    Offset = Resolvedlib.first_class_offset(RecordsInfo, KRefClassInfo)
    if Offset is None:
        return
    LowXInfo, HighX, LowYInfo, HighY, LowZInfo, HighZ = BodyBoundsMm(PartInfoInfo)
    SpanInfo = max(HighX - LowXInfo, HighY - LowYInfo, HighZ - LowZInfo)
    Writes.append(f'{KRefClassInfo} left stale (derived display extents, span={SpanInfo})')


# needed to keep reverse engineering responsibilities isolated and maintainable
def EmitKeywords(PartInfoInfo: PartInfo, Names: tuple[tuple[str, str], ...], Idents: tuple[tuple[int, int], ...]) -> bytes:
    Stamp = int(TimeInfo.time())
    Pieces: list[str] = ['<?xml version="1.0" encoding="UTF-8"?>\r\n', f'<Keywords id="{Stamp}" Name="{PartInfoInfo.document_name}">', '<Configuration id="0" Name="Default" Type="ConfigurationManager" Material="Material &lt;not specified&gt;"/>']
    for IndexData, FeatInfo in enumerate(PartInfoInfo.features):
        SketchId, FeatId = Idents[IndexData]
        DimInfo = '' if FeatInfo.end_condition == 'throughall' else f'<Dimension Name="D1">{Number(FeatInfo.depth_mm)}</Dimension>'
        if IndexData == 0:
            Attrs = ' Type="Boss-Extrude"'
        else:
            Attrs = f' Dissectable="true" DissectableChildren="{SketchId}" DissectableRoot="true"'
        if DimInfo:
            Pieces.append(f'<Extrusion id="{FeatId}" Name="{Names[IndexData][1]}"{Attrs}>{DimInfo}</Extrusion>')
        else:
            Pieces.append(f'<Extrusion id="{FeatId}" Name="{Names[IndexData][1]}"{Attrs}/>')
    for Ident, NameTextInfo, KindNameInfo in KBoilerplate:
        Pieces.append(f'<Feature id="{Ident}" Name="{NameTextInfo}" Type="{KindNameInfo}"/>')
    for IndexData in range(len(PartInfoInfo.features)):
        Pieces.append(f'<Sketch id="{Idents[IndexData][0]}" Name="{Names[IndexData][0]}" Dissectable="true"/>')
    Pieces.append('<Sketch id="5" Name="Origin" Type="Origin"/>')
    Pieces.append('</Keywords>\r\n')
    return KeywordsPrefix + ''.join(Pieces).encode('utf-8')


# needed to keep reverse engineering responsibilities isolated and maintainable
def EmitFeatXml(PartInfoInfo: PartInfo) -> bytes:
    Stamp = int(TimeInfo.time())
    Document = f'<?xml version="1.0" encoding="UTF-8"?>\r\n<swSolidWorks xmlns="http://www.solidworks.com/sw2003/schema" swObjCount="3" swVersion="18000"><swHeader swObjCount="1"><swFile id="3" swDocType="PART" swCreationTime="{Stamp}" swPath="{PartInfoInfo.name}.sldprt"/></swHeader><swModelList swObjCount="1"><swModel id="2" swName="{PartInfoInfo.name}" swConfigurationName="Default" swConfigurationId="0" swLastModifiedStamp="106" swConfigurationFlags="-2143288960" swFileRef="3"/></swModelList><swConfigurationList swObjCount="1"><swConfiguration id="1" swName="Default" swID="0" swReference="{PartInfoInfo.document_name}" swMostRecentConfiguration="YES" swConfigurationNeedsUpdate="NO" swDefeatureConfiguration="NO" swModelRef="2"/></swConfigurationList><swExtFeatureList swObjCount="0"/></swSolidWorks>\r\n'
    return Document.encode('utf-8')


# needed to keep reverse engineering responsibilities isolated and maintainable
def Number(ValueInfo: float) -> str:
    if float(ValueInfo).is_integer():
        return str(int(ValueInfo))
    return repr(float(ValueInfo))

# needed to keep reverse engineering responsibilities isolated and maintainable
KBoilerplate: tuple[tuple[int, str, str], ...] = ((1, 'Annotations', 'Annotations'), (10, 'Surface Bodies', 'Surface Bodies'), (11, 'Material &lt;not specified&gt;', 'SOLIDWORKS Materials'), (12, 'Ambient', 'Ambient'), (13, 'Directional1', 'Directional'), (14, 'Directional2', 'Directional'), (15, 'Directional3', 'Directional'), (16, 'Equations', 'Equations'), (17, 'Notes', 'Notes'), (18, 'Notes1___EndTag___', 'Notes'), (19, '', 'Exploded Views'), (2, 'Front Plane', 'Plane'), (21, 'Markups', 'Markups'), (22, 'Sensors', 'Sensors'), (23, 'Favorites', 'Favorites'), (24, 'History', 'History'), (25, 'Selection Sets', 'Selection Sets'), (3, 'Top Plane', 'Plane'), (4, 'Right Plane', 'Plane'), (6, 'Lights and Cameras', 'Lights and Cameras'), (7, 'Design Binder', 'Design Binder'), (8, 'Comments', 'Comments'), (9, 'Solid Bodies', 'Solid Bodies'))


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuildPart(PartInfoInfo: PartInfo, Target: PathInfo, Skeletons: tuple[Skeleton, ...] | None=None):
    Catalogue = LoadSkeletons() if Skeletons is None else Skeletons
    SkeletonInfo = SelectSkeleton(PartInfoInfo, Catalogue)
    EmissionInfo = EmitData(PartInfoInfo, (SkeletonInfo,) + tuple(Catalogue))
    Contain = Streamlib.Rebuild(SkeletonInfo.donor, {Streamlib.KResolved: EmissionInfo.resolved, Streamlib.KEYWORDS: EmissionInfo.keywords, Streamlib.KFeatInfo: EmissionInfo.features_xml})
    Target.parent.mkdir(parents=True, exist_ok=True)
    Target.write_bytes(Contain)
    return (EmissionInfo, len(Contain))
