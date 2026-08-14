# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import builtins as Builtins
from dataclasses import dataclass as Dataclass, field as Field, replace as Replace
import hashlib as Hashlib
import math as MathValue
import re as RegexLib
import struct as Struct
from sys import float_info as FloatInfo
from typing import Iterable, Mapping, Sequence
import zlib as ZlibLib
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
    Vector3 as VectorThree,
    frozen_mapping as FrozenMapping,
)

# this constant exists because binary encoding requires stable protocol data
KWrapperMagic = bytes.fromhex("231dd571da8148a2a85898b21b89ef99")

# this constant exists because binary encoding requires stable protocol data
KEntityMagic = bytes.fromhex("c2bc928f996e0000")

# this constant exists because binary encoding requires stable protocol data
KInlineTermTail = bytes.fromhex("000000010163435a")

# this constant exists because binary encoding requires stable protocol data
KInlineUvTail = bytes.fromhex("00000002016601")

# this constant exists because binary encoding requires stable protocol data
KMissingParam = -31415800000000.0

# this constant exists because binary encoding requires stable protocol data
KLengthScale = 0.001

# this constant exists because binary encoding requires stable protocol data
KSolidSchema = "SCH_SW_33103_11000"

# this constant exists because binary encoding requires stable protocol data
KSheetSchema = "SCH_SW_32001_11000"

# this constant exists because binary encoding requires stable protocol data
KParaSchema = "SCH_1200000_12006"

# this constant exists because binary encoding requires stable protocol data
KParaPartDesc = b": TRANSMIT FILE (partition) created by modeller version 1200000"

# this constant exists because binary encoding requires stable protocol data
KParaModelDesc = b": TRANSMIT FILE created by modeller version 1200000"

# this constant exists because binary encoding requires stable protocol data
KSolidworksSchema = "SCH_3601228_36001_13006"

# this constant exists because binary encoding requires stable protocol data
KBlankPartBody = bytes.fromhex(
    "00e7000000000065134343434343434349046d65736803ee00014908706f6c796c696e6503f0000149076c61747469636500de00014343490b6174746465665f6c697374004a000143434110696e6465785f6d61705f6f66667365740000000101644109696e6465785f6d6170005200014114736368656d615f656d62656464696e675f6d61700052000141106d6573685f6f66667365745f6461746100ce00015a00020001000100010001000100010001000100010001010001000100000003000000030000000000010001000100010001"
)

# this constant exists because binary encoding requires stable protocol data
KBlankDeltaBody = bytes.fromhex(
    "00e7000000000003ff00030004000000030004ff000400050001000100010000000000000000000000000000000e0000000003000100010001000000010065134343434343434349046d65736803ee00014908706f6c796c696e6503f0000149076c61747469636500de00014343490b6174746465665f6c697374004a000143434110696e6465785f6d61705f6f66667365740000000101644109696e6465785f6d6170005200014114736368656d615f656d62656464696e675f6d61700052000141106d6573685f6f66667365745f6461746100ce00015a0002000101000101000101000101000101000101000101000101000101000101000001010001010000000000000000000000000001010001010001010001000100040005000100040001000100000000000000000000000000000000000000000100010001"
)


# this declaration exists because focused behavior needs one stable owner
class ParaFormatError(ValueError):
    locals()["__slots__"] = ()


# this declaration exists because focused behavior needs one stable owner
class ParaWriteError(ValueError):
    locals()["__slots__"] = ()


# this declaration exists because focused behavior needs one stable owner
def HasParaPayload(DataValue: bytes | bytearray) -> bool:
    Source = bytes(DataValue)
    return Source.startswith(b"PS\x00\x00") or KWrapperMagic in Source


# this declaration exists because focused behavior needs one stable owner
def IsNativePayload(DataValue: bytes | bytearray) -> bool:
    Source = bytes(DataValue)
    if not Source.startswith(b"PS\x00\x00") or len(Source) < 32:
        return False
    Match = RegexLib.search(b"SCH_[0-9A-Z_]+", Source[:8192])
    return Match is not None and len(Source) >= Match.end() + 8


# this declaration exists because focused behavior needs one stable owner
def EncodeBrepModel(
    Model: BrepModel,
    *,
    PartValue: bool = True,
    SolidFeatureIds: Mapping[str, int] | None = None,
) -> bytes:
    DesignBodyIds = frozenset(
        (
            BodyData.design_body_id
            for BodyData in Model.bodies
            if BodyData.design_body_id
        )
    )
    Errors = Model.validate(DesignBodyIds)
    if Errors:
        raise ParaWriteError(Errors[0])
    if any((BodyData.transform != Transform() for BodyData in Model.bodies)):
        raise ParaWriteError(
            "Parasolid B-rep writing requires identity body transforms"
        )
    FeatureIds = dict(SolidFeatureIds or {})
    if FeatureIds:
        BodyIdsData = frozenset((BodyData.id for BodyData in Model.bodies))
        if frozenset(FeatureIds) != BodyIdsData:
            raise ParaWriteError(
                "SOLIDWORKS feature ids must cover every Parasolid body"
            )
        if any(
            (
                type(ValueData) is not int or not 0 < ValueData < 1 << 31
                for ValueData in FeatureIds.values()
            )
        ):
            raise ParaWriteError("SOLIDWORKS feature ids must be positive i32 values")
    ValidateSupport(Model)
    Topology = BrepTopology(Model)
    BodyData, Ignored = EncodeBrepBody(
        Model, Topology, PartValue=PartValue, SolidFeatureIds=FeatureIds
    )
    PayloadData = ParaStream(
        BodyData,
        KParaSchema,
        KParaPartDesc if PartValue else KParaModelDesc,
        UserFieldSize=0,
    )
    VerifyBrepData(Model, PayloadData)
    return PayloadData


# this declaration exists because focused behavior needs one stable owner
def EncodePartData(DataValue: bytes | bytearray) -> bytes:
    PayloadData = bytes(DataValue)
    if not PayloadData.startswith(b"PS\x00\x00"):
        raise ParaWriteError("Parasolid partition data must start with PS\\0\\0")
    ZipValue = ZlibLib.compress(PayloadData, level=1)
    if len(PayloadData) > 4294967295 or len(ZipValue) + 32 > 4294967295:
        raise ParaWriteError("Parasolid partition data is too large")
    return b"".join(
        (
            Struct.pack("<I", len(ZipValue) + 32),
            KWrapperMagic,
            Struct.pack("<II", len(PayloadData), len(ZipValue)),
            ZipValue,
            bytes(8),
        )
    )


# this declaration exists because focused behavior needs one stable owner
def EncodeBlankPart() -> bytes:
    Payloads = (
        ParaStream(
            KBlankPartBody,
            KSolidworksSchema,
            b": TRANSMIT FILE (partition) created by modeller version 3601228",
        ),
        ParaStream(
            KBlankDeltaBody,
            KSolidworksSchema,
            b": TRANSMIT FILE (deltas) created by modeller version 3601228",
        ),
    )
    return b"".join((EncodePartData(PayloadData) for PayloadData in Payloads))


# this declaration exists because focused behavior needs one stable owner
def ValidateSupport(Model: BrepModel) -> None:
    if Model.pcurves or any((Coedge.pcurve_id for Coedge in Model.coedges)):
        raise ParaWriteError("Parasolid B-rep writing does not support pcurves")
    if Model.wires or any((BodyData.wire_ids for BodyData in Model.bodies)):
        raise ParaWriteError("Parasolid B-rep writing does not support wire bodies")
    if any((BodyData.vertex_ids for BodyData in Model.bodies)):
        raise ParaWriteError(
            "Parasolid B-rep writing does not support standalone vertex bodies"
        )
    if any((EdgeData.degenerate for EdgeData in Model.edges)):
        raise ParaWriteError(
            "Parasolid B-rep writing does not support degenerate edges"
        )
    Loops = {LoopDataData.id: LoopDataData for LoopDataData in Model.loops}
    for FaceDataData in Model.faces:
        Outer = tuple((Loops[LoopId].outer for LoopId in FaceDataData.loop_ids))
        if Outer != (True, *(False for Ignored in FaceDataData.loop_ids[1:])):
            raise ParaWriteError(
                f"Parasolid B-rep face {FaceDataData.id} requires its first loop to be the only outer loop"
            )
    Shells = {Shell.id: Shell for Shell in Model.shells}
    ShellUses = {ShellUse.id: ShellUse for ShellUse in Model.shell_uses}
    for Region in Model.regions:
        for ShellUseId in Region.shell_use_ids:
            Shell = Shells[ShellUses[ShellUseId].shell_id]
            if Shell.closed != Region.solid:
                raise ParaWriteError(
                    f"Parasolid B-rep shell {Shell.id} closure contradicts region {Region.id}"
                )


# this declaration exists because focused behavior needs one stable owner
def VerifyBrepData(Model: BrepModel, PayloadData: bytes) -> None:
    Decoded = DecodeBrepModel(PayloadData)
    if Decoded is None:
        raise ParaWriteError("generated Parasolid B-rep cannot be decoded")
    Errors = Decoded.validate()
    if Errors:
        raise ParaWriteError(Errors[0])
    Collections = (
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
        (
            len(getattr(Model, NameValue)) != len(getattr(Decoded, NameValue))
            for NameValue in Collections
        )
    ):
        raise ParaWriteError("generated Parasolid B-rep changes topology counts")
    if any(
        (
            tuple((type(ItemData) for ItemData in getattr(Model, NameValue)))
            != tuple((type(ItemData) for ItemData in getattr(Decoded, NameValue)))
            for NameValue in ("curves", "surfaces")
        )
    ):
        raise ParaWriteError("generated Parasolid B-rep changes geometry classes")
    if tuple((Region.solid for Region in Model.regions)) != tuple(
        (Region.solid for Region in Decoded.regions)
    ):
        raise ParaWriteError("generated Parasolid B-rep changes region solidity")
    if tuple((LoopDataData.outer for LoopDataData in Model.loops)) != tuple(
        (LoopDataData.outer for LoopDataData in Decoded.loops)
    ):
        raise ParaWriteError("generated Parasolid B-rep changes loop roles")
    if any(
        (
            Distance(Source.point, Restored.point) > 1e-09
            for Source, Restored in zip(Model.vertices, Decoded.vertices)
        )
    ):
        raise ParaWriteError("generated Parasolid B-rep changes vertex geometry")
    if any(
        (
            not MathValue.isclose(
                Source.tolerance, Restored.tolerance, rel_tol=1e-12, abs_tol=1e-15
            )
            for NameValue in ("vertices", "edges", "faces")
            for Source, Restored in zip(
                getattr(Model, NameValue), getattr(Decoded, NameValue)
            )
        )
    ):
        raise ParaWriteError("generated Parasolid B-rep changes topology tolerance")


# this declaration exists because focused behavior needs one stable owner
class BrepTopology:
    locals()["__slots__"] = (
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


# topology initialization delegates each ownership phase to a focused helper
def InitTopologyMut(SelfData: BrepTopology, Model: BrepModel) -> None:
    SetTopoMapsMut(SelfData, Model)
    BindFaceOwnMut(SelfData, Model)
    BindShellOwnMut(SelfData, Model)
    CheckTopoOwn(SelfData)


# topology maps provide constant time access without changing public model objects
def SetTopoMapsMut(SelfData: BrepTopology, Model: BrepModel) -> None:
    for AttrName, Values in (
        ("curve_by_id", Model.curves),
        ("surface_by_id", Model.surfaces),
        ("vertex_by_id", Model.vertices),
        ("edges", Model.edges),
        ("coedges", Model.coedges),
        ("loops", Model.loops),
        ("faces", Model.faces),
        ("face_uses", Model.face_uses),
        ("shells", Model.shells),
        ("shell_uses", Model.shell_uses),
        ("regions", Model.regions),
        ("bodies", Model.bodies),
    ):
        setattr(SelfData, AttrName, {ItemData.id: ItemData for ItemData in Values})
    for AttrName in (
        "coedge_loop",
        "loop_face",
        "face_face_use",
        "shell_face_use",
        "shell_shell_use",
        "shell_use_region",
        "region_body",
    ):
        setattr(SelfData, AttrName, {})
    setattr(SelfData, "edge_coedges", {ItemData.id: [] for ItemData in Model.edges})


# face ownership links preserve the model topology hierarchy for deterministic encoding
def BindFaceOwnMut(SelfData: BrepTopology, Model: BrepModel) -> None:
    for LoopData in Model.loops:
        for CoedgeId in LoopData.coedge_ids:
            BindOwnerMut(SelfData.coedge_loop, CoedgeId, LoopData.id, "coedge", "loop")
    for FaceData in Model.faces:
        for LoopId in FaceData.loop_ids:
            BindOwnerMut(SelfData.loop_face, LoopId, FaceData.id, "loop", "face")
    for ShellData in Model.shells:
        for FaceUseId in ShellData.face_use_ids:
            BindOwnerMut(
                SelfData.shell_face_use, FaceUseId, ShellData.id, "face use", "shell"
            )
            FaceUse = SelfData.face_uses[FaceUseId]
            BindOwnerMut(
                SelfData.face_face_use, FaceUse.face_id, FaceUse.id, "face", "face use"
            )


# shell ownership links complete the region body and edge usage relationships
def BindShellOwnMut(SelfData: BrepTopology, Model: BrepModel) -> None:
    for RegionData in Model.regions:
        for ShellUseId in RegionData.shell_use_ids:
            BindOwnerMut(
                SelfData.shell_use_region,
                ShellUseId,
                RegionData.id,
                "shell use",
                "region",
            )
            ShellUse = SelfData.shell_uses[ShellUseId]
            BindOwnerMut(
                SelfData.shell_shell_use,
                ShellUse.shell_id,
                ShellUse.id,
                "shell",
                "shell use",
            )
    for BodyData in Model.bodies:
        for RegionId in BodyData.region_ids:
            BindOwnerMut(SelfData.region_body, RegionId, BodyData.id, "region", "body")
    for CoedgeData in Model.coedges:
        SelfData.edge_coedges[CoedgeData.edge_id].append(CoedgeData.id)


# topology validation rejects incomplete or nonmanifold ownership before serialization
def CheckTopoOwn(SelfData: BrepTopology) -> None:
    for Owners, Items, ItemName, OwnerName in (
        (SelfData.coedge_loop, SelfData.coedges, "coedge", "loop"),
        (SelfData.loop_face, SelfData.loops, "loop", "face"),
        (SelfData.face_face_use, SelfData.faces, "face", "face use"),
        (SelfData.shell_face_use, SelfData.face_uses, "face use", "shell"),
        (SelfData.shell_use_region, SelfData.shell_uses, "shell use", "region"),
        (SelfData.shell_shell_use, SelfData.shells, "shell", "shell use"),
        (SelfData.region_body, SelfData.regions, "region", "body"),
    ):
        RequireComplete(Owners, Items, ItemName, OwnerName)
    for EdgeId, CoedgeIds in SelfData.edge_coedges.items():
        if not CoedgeIds:
            raise ParaWriteError(f"B-rep edge {EdgeId} has no coedge usage")
        if len(CoedgeIds) > 2:
            raise ParaWriteError(f"B-rep edge {EdgeId} has non-manifold coedge usage")


# face orientation combines the nested topology reversals used by parasolid fins
def IsFaceForward(SelfData: BrepTopology, FaceId: str) -> bool:
    FaceData = SelfData.faces[FaceId]
    FaceUse = SelfData.face_uses[SelfData.face_face_use[FaceId]]
    ShellData = SelfData.shells[SelfData.shell_face_use[FaceUse.id]]
    ShellUse = SelfData.shell_uses[SelfData.shell_shell_use[ShellData.id]]
    return FaceData.same_sense ^ FaceUse.reversed ^ ShellUse.reversed


setattr(BrepTopology, "__init__", InitTopologyMut)
setattr(BrepTopology, "IsFaceForward", IsFaceForward)


# this declaration exists because focused behavior needs one stable owner
def BindOwnerMut(
    Owners: dict[str, str], ItemId: str, OwnerId: str, ItemName: str, OwnerName: str
) -> None:
    if ItemId in Owners:
        raise ParaWriteError(
            f"B-rep {ItemName} {ItemId} belongs to multiple {OwnerName} values"
        )
    Owners[ItemId] = OwnerId


# this declaration exists because focused behavior needs one stable owner
def RequireComplete(
    Owners: Mapping[str, str],
    Values: Mapping[str, object],
    ItemName: str,
    OwnerName: str,
) -> None:
    Missing = next((ItemId for ItemId in Values if ItemId not in Owners), None)
    if Missing is not None:
        raise ParaWriteError(f"B-rep {ItemName} {Missing} has no {OwnerName} usage")


# this declaration exists because focused behavior needs one stable owner
def OrderIds(
    Values: Sequence[str], Entities: Mapping[str, object], AttrName: str
) -> list[str]:
    Ranks = [
        getattr(Entities[ValueData], "attributes", {}).get(AttrName)
        for ValueData in Values
    ]
    if all((type(RankValue) is int and RankValue >= 0 for RankValue in Ranks)) and len(
        set(Ranks)
    ) == len(Ranks):

        # this callback exists because local behavior needs one focused transformation
        return [
            ValueData
            for Ignored, ValueData in sorted(
                zip(Ranks, Values), key=lambda ItemData: ItemData[0]
            )
        ]
    return list(Values)


# this declaration exists because focused behavior needs one stable owner
def FinIndex(
    Descriptor: object, Coedges: Mapping[str, int], DummyFins: Mapping[str, int]
) -> int | None:
    if (
        not isinstance(Descriptor, (tuple, list))
        or len(Descriptor) != 2
        or (not all((isinstance(ValueData, str) for ValueData in Descriptor)))
    ):
        return None
    KindValueData, IdValue = Descriptor
    if KindValueData == "coedge":
        return Coedges.get(IdValue)
    if KindValueData == "dummy":
        return DummyFins.get(IdValue)
    return None


# encoder configuration owns vendor mode decisions shared by all output phases
@Dataclass(slots=True)
class EncodeConfig:
    KFeatureIds: dict[str, int]
    KAttrBases: dict[str, int]
    KSolidTri: bool
    KSolidSolid: bool
    KDummyEdges: tuple[BrepEdge, ...]


# index allocation state owns reserved and consumed native record identifiers
@Dataclass(slots=True)
class IndexAllocator:
    KReservedIndices: set[int]
    KReservedTopologyIndices: set[int]
    KUsedIndices: set[int]
    KNextIndex: int


# encoded index storage gives every topology and attribute family one owner
@Dataclass(slots=True)
class EncodeIndices:
    KBodies: dict[str, int]
    KRegions: dict[str, int]
    KShells: dict[str, int]
    KSurfaces: dict[str, int]
    KCurves: dict[str, int]
    KPoints: dict[str, int]
    KVertices: dict[str, int]
    KEdges: dict[str, int]
    KCoedges: dict[str, int]
    KDummyFins: dict[str, int]
    KLoops: dict[str, int]
    KFaces: dict[str, int]
    KExteriorRegions: dict[str, int]
    KExteriorShells: dict[str, int]
    KSolidFaceAttrs: dict[str, tuple[int, int, int]]
    KSolidFaceValues: dict[str, tuple[int, int, int]]
    KSolidFaceDefinitions: dict[str, int]
    KSolidFaceDefNext: dict[str, int]
    KSolidFaceIds: dict[str, int]
    KSolidBodyAttrs: dict[str, int]
    KSolidBodyValues: dict[str, int]
    KSolidBodyDefinitions: dict[str, int]
    KSolidBodyDefNext: dict[str, int]
    KSolidBodyIds: dict[str, int]
    KSheet: bool


# ownership storage centralizes body membership and percarrier linked ordering
@Dataclass(slots=True)
class EncodeOwners:
    KFaceShell: dict[str, str]
    KFaceRegion: dict[str, str]
    KFaceBody: dict[str, str]
    KShellRegion: dict[str, str]
    KShellBody: dict[str, str]
    KEdgeBody: dict[str, str]
    KVertexBody: dict[str, str]
    KSurfFaces: dict[str, list[str]]
    KCurveEdges: dict[str, list[str]]
    KBodySurfaces: dict[str, list[str]]
    KBodyCurves: dict[str, list[str]]
    KBodyPoints: dict[str, list[str]]
    KBodyVertices: dict[str, list[str]]
    KBodyEdges: dict[str, list[str]]


# node storage tracks perbody numbering independently from native record identifiers
@Dataclass(slots=True)
class EncodeNodeState:
    KNodeIds: dict[int, int]
    KNextNodeId: dict[str, int]


# fin storage owns encoded orientations vertex rings and opposite fin relationships
@Dataclass(slots=True)
class EncodeFinState:
    KEncodedLoopCoedges: dict[str, tuple[str, ...]]
    KEncodedCoedgeReversed: dict[str, bool]
    KVertexFins: dict[str, list[int]]
    KFinVertex: dict[int, str]
    KFinOther: dict[int, int]
    KFirstFaceByBody: dict[str, str]


# brep encoding composes allocation ownership topology and focused binary emitters
def EncodeBrepBody(
    Model: BrepModel,
    Topology: BrepTopology,
    *,
    PartValue: bool = True,
    SolidFeatureIds: Mapping[str, int] | None = None,
) -> tuple[bytes, bool]:
    Config = MakeEncConfig(Model, Topology, SolidFeatureIds)
    Allocator = MakeAllocator(Config, PartValue)
    Indices = MakeEncodeIndex(Model, Topology, Config, Allocator)
    Owners = MakeEncOwners(Model, Topology)
    Nodes = MakeNodeState(Model, Topology, Config, Indices, Owners)
    FinState = MakeFinState(Model, Topology, Indices, Owners)
    Output = bytearray()
    WriteHeadMut(Output, Model, PartValue, Indices)
    EmitBodiesMut(Output, Model, Topology, PartValue, Config, Indices, Owners, Nodes)
    EmitRegionsMut(Output, Model, Topology, Indices, Owners, Nodes)
    EmitShellsMut(Output, Model, Topology, Indices, Owners, Nodes)
    EmitSurfacesMut(Output, Model, Config, Indices, Owners, Nodes)
    EmitCurvesMut(Output, Model, Config, Indices, Owners, Nodes)
    EmitPointsMut(Output, Model, Indices, Owners, Nodes)
    EmitVerticesMut(Output, Model, Indices, Owners, Nodes, FinState)
    EmitEdgesMut(Output, Model, Topology, Indices, Owners, Nodes, FinState)
    EmitCoedgesMut(Output, Model, Topology, Indices, Owners, FinState)
    EmitDummyMut(Output, Config, Topology, Indices, FinState)
    EmitLoopsMut(Output, Model, Topology, Indices, Nodes, FinState)
    EmitFacesMut(Output, Model, Topology, Config, Indices, Owners, Nodes, FinState)
    EmitVendorMut(Output, Model, Config, Indices, Nodes, FinState)
    WriteTagMut(Output, 1)
    WritePointerMut(Output, 0)
    Result = (
        OrderTriRecords(bytes(Output))
        if Config.KSolidTri and not PartValue
        else bytes(Output)
    )
    return Result, Indices.KSheet


# encoder configuration derives deterministic vendor layout modes from model topology
def MakeEncConfig(
    Model: BrepModel, Topology: BrepTopology, SolidFeatureIds: Mapping[str, int] | None
) -> EncodeConfig:
    FeatureIds = dict(SolidFeatureIds or {})
    AttrBases = (
        {BodyData.id: Position * 100 for Position, BodyData in enumerate(Model.bodies)}
        if FeatureIds
        else {}
    )
    SolidTri = (
        bool(FeatureIds)
        and len(Model.bodies) == 1
        and len(Model.regions) == 1
        and len(Model.shells) == 1
        and len(Model.surfaces) == 1
        and len(Model.curves) == 3
        and len(Model.vertices) == 3
        and len(Model.edges) == 3
        and len(Model.coedges) == 3
        and len(Model.loops) == 1
        and len(Model.faces) == 1
        and not Model.regions[0].solid
        and isinstance(Model.surfaces[0], PlaneSurface)
        and all((isinstance(Curve, LineCurve) for Curve in Model.curves))
        and all(
            (len(Topology.edge_coedges[EdgeData.id]) == 1 for EdgeData in Model.edges)
        )
    )
    SolidSolid = (
        bool(FeatureIds)
        and len(Model.bodies) == 1
        and all((Region.solid for Region in Model.regions))
    )
    DummyEdges = tuple(
        (
            EdgeData
            for EdgeData in Model.edges
            if len(Topology.edge_coedges[EdgeData.id]) == 1
        )
    )
    return EncodeConfig(FeatureIds, AttrBases, SolidTri, SolidSolid, DummyEdges)


# allocator creation reserves vendor controlled attribute and topology identifier ranges
def MakeAllocator(Config: EncodeConfig, PartValue: bool) -> IndexAllocator:
    Reserved = {
        BaseValue + OffsetData
        for BaseValue in Config.KAttrBases.values()
        for OffsetData in (*range(2, 5), *range(12, 16), *range(32, 60))
    }
    ReservedTopology = set(range(5, 12)) if Config.KFeatureIds else set()
    return IndexAllocator(Reserved, ReservedTopology, set(), 2 if PartValue else 1)


# index allocation selects preferred identifiers without colliding with reserved ranges
def AllocIndexMut(Allocator: IndexAllocator, Preferred: int = 0) -> int:
    if (
        Preferred
        and Preferred not in Allocator.KReservedIndices
        and Preferred not in Allocator.KUsedIndices
    ):
        Allocator.KUsedIndices.add(Preferred)
        return Preferred
    while (
        Allocator.KNextIndex in Allocator.KReservedIndices
        or Allocator.KNextIndex in Allocator.KReservedTopologyIndices
        or Allocator.KNextIndex in Allocator.KUsedIndices
    ):
        Allocator.KNextIndex += 1
    Result = Allocator.KNextIndex
    Allocator.KUsedIndices.add(Result)
    Allocator.KNextIndex += 1
    return Result


# collection allocation maps interchange identifiers to deterministic native record indices
def AllocItemsMut(
    Allocator: IndexAllocator, Values: Iterable[object], Preferred: Sequence[int] = ()
) -> dict[str, int]:
    Result: dict[str, int] = {}
    for Position, ValueData in enumerate(Values):
        ItemId = getattr(ValueData, "id")
        Result[ItemId] = AllocIndexMut(
            Allocator, Preferred[Position] if Position < len(Preferred) else 0
        )
    return Result


# standard index allocation covers all direct topology and geometry record families
def BaseIndexesMut(
    Model: BrepModel, Config: EncodeConfig, Allocator: IndexAllocator
) -> tuple[dict[str, int], ...]:
    Bodies = (
        {BodyData.id: Config.KAttrBases[BodyData.id] + 1 for BodyData in Model.bodies}
        if Config.KAttrBases
        else AllocItemsMut(Allocator, Model.bodies)
    )
    Allocator.KUsedIndices.update(Bodies.values())
    Regions = AllocItemsMut(
        Allocator,
        Model.regions,
        (17,) if Config.KSolidSolid else (9,) if Config.KFeatureIds else (),
    )
    Shells = AllocItemsMut(Allocator, Model.shells, (5,) if Config.KFeatureIds else ())
    Surfaces = AllocItemsMut(
        Allocator, Model.surfaces, (6,) if Config.KFeatureIds else ()
    )
    Curves = AllocItemsMut(
        Allocator,
        Model.curves,
        (7, 17, 31) if Config.KSolidTri else (7,) if Config.KFeatureIds else (),
    )
    Points = AllocItemsMut(
        Allocator,
        Model.vertices,
        (8, 18, 29) if Config.KSolidTri else (8,) if Config.KFeatureIds else (),
    )
    Vertices = AllocItemsMut(
        Allocator,
        Model.vertices,
        (11, 21, 27) if Config.KSolidTri else (11,) if Config.KFeatureIds else (),
    )
    Edges = AllocItemsMut(
        Allocator,
        Model.edges,
        (10, 20, 30) if Config.KSolidTri else (10,) if Config.KFeatureIds else (),
    )
    Coedges = AllocItemsMut(
        Allocator, Model.coedges, (19, 23, 24) if Config.KSolidTri else ()
    )
    DummyFins = AllocItemsMut(
        Allocator, Config.KDummyEdges, (25, 28, 26) if Config.KSolidTri else ()
    )
    Loops = AllocItemsMut(Allocator, Model.loops, (22,) if Config.KSolidTri else ())
    Faces = AllocItemsMut(Allocator, Model.faces, (16,) if Config.KSolidTri else ())
    return (
        Bodies,
        Regions,
        Shells,
        Surfaces,
        Curves,
        Points,
        Vertices,
        Edges,
        Coedges,
        DummyFins,
        Loops,
        Faces,
    )


# exterior index allocation creates complement regions and shells for solid bodies
def ExteriorIndexes(
    Model: BrepModel,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Allocator: IndexAllocator,
) -> tuple[dict[str, int], dict[str, int], bool]:
    ExteriorRegions, ExteriorShells = {}, {}
    Sheet = False
    for BodyData in Model.bodies:
        Kinds = {Topology.regions[RegionId].solid for RegionId in BodyData.region_ids}
        if len(Kinds) != 1:
            raise ParaWriteError(
                f"B-rep body {BodyData.id} mixes solid and sheet regions"
            )
        if Kinds == {False}:
            Sheet = True
            continue
        ExteriorRegions[BodyData.id] = AllocIndexMut(
            Allocator, 9 if Config.KSolidSolid else 0
        )
        for RegionId in BodyData.region_ids:
            for ShellUseId in Topology.regions[RegionId].shell_use_ids:
                ShellId = Topology.shell_uses[ShellUseId].shell_id
                ExteriorShells[ShellId] = AllocIndexMut(Allocator)
    return ExteriorRegions, ExteriorShells, Sheet


# vendor attribute allocation creates solidworks face and body record chains
def SolidIndexes(
    Model: BrepModel, Config: EncodeConfig, Allocator: IndexAllocator
) -> tuple[dict[str, object], ...]:
    FaceAttrs, FaceValues, FaceDefinitions, FaceDefNext, FaceIds = {}, {}, {}, {}, {}
    BodyAttrs, BodyValues, BodyDefinitions, BodyDefNext, BodyIds = {}, {}, {}, {}, {}
    if Config.KSolidSolid:
        for NameValue in ("unchanged", "downstream", "colour"):
            FaceDefinitions[NameValue] = AllocIndexMut(Allocator)
            FaceDefNext[NameValue] = (
                0 if NameValue == "colour" else AllocIndexMut(Allocator)
            )
            FaceIds[NameValue] = AllocIndexMut(Allocator)
        for FaceData in Model.faces:
            FaceAttrs[FaceData.id] = tuple(
                (AllocIndexMut(Allocator) for Ignored in range(3))
            )
            FaceValues[FaceData.id] = tuple(
                (AllocIndexMut(Allocator) for Ignored in range(3))
            )
        BodyAttrs = {
            "timestamp": AllocIndexMut(Allocator),
            "feature": AllocIndexMut(Allocator),
            "implicit": AllocIndexMut(Allocator),
            "match": AllocIndexMut(Allocator),
            "density": AllocIndexMut(Allocator),
            "lightweight": AllocIndexMut(Allocator),
            "recipe": 13,
        }
        for NameValue in (
            "timestamp",
            "feature",
            "implicit",
            "match",
            "density",
            "lightweight",
            "recipe",
        ):
            BodyDefinitions[NameValue] = AllocIndexMut(Allocator)
            BodyDefNext[NameValue] = AllocIndexMut(Allocator)
            BodyIds[NameValue] = AllocIndexMut(Allocator)
        for NameValue in (
            "timestamp",
            "feature",
            "implicit",
            "match",
            "density",
            "lightweight",
        ):
            BodyValues[NameValue] = AllocIndexMut(Allocator)
    return (
        FaceAttrs,
        FaceValues,
        FaceDefinitions,
        FaceDefNext,
        FaceIds,
        BodyAttrs,
        BodyValues,
        BodyDefinitions,
        BodyDefNext,
        BodyIds,
    )


# complete index construction combines standard exterior and vendor attribute families
def MakeEncodeIndex(
    Model: BrepModel,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Allocator: IndexAllocator,
) -> EncodeIndices:
    BaseData = BaseIndexesMut(Model, Config, Allocator)
    ExteriorRegions, ExteriorShells, Sheet = ExteriorIndexes(
        Model, Topology, Config, Allocator
    )
    SolidData = SolidIndexes(Model, Config, Allocator)
    if max((*Allocator.KReservedIndices, *Allocator.KUsedIndices), default=0) >= 32767:
        raise ParaWriteError("Parasolid V12 writer node space is exhausted")
    return EncodeIndices(*BaseData, ExteriorRegions, ExteriorShells, *SolidData, Sheet)


# face ownership mapping links faces shells regions and bodies without duplication
def MakeFaceOwners(
    Model: BrepModel, Topology: BrepTopology
) -> tuple[dict[str, str], ...]:
    FaceShell, FaceRegion, FaceBody, ShellRegion, ShellBody = {}, {}, {}, {}, {}
    for RegionData in Model.regions:
        BodyId = Topology.region_body[RegionData.id]
        for ShellUseId in RegionData.shell_use_ids:
            ShellUse = Topology.shell_uses[ShellUseId]
            ShellData = Topology.shells[ShellUse.shell_id]
            ShellRegion[ShellData.id] = RegionData.id
            ShellBody[ShellData.id] = BodyId
            for FaceUseId in ShellData.face_use_ids:
                FaceId = Topology.face_uses[FaceUseId].face_id
                FaceShell[FaceId] = ShellData.id
                FaceRegion[FaceId] = RegionData.id
                FaceBody[FaceId] = BodyId
    return FaceShell, FaceRegion, FaceBody, ShellRegion, ShellBody


# edge ownership mapping proves each edge and vertex belongs to one body
def MakeEdgeOwners(
    Model: BrepModel, Topology: BrepTopology, FaceBody: Mapping[str, str]
) -> tuple[dict[str, str], dict[str, str]]:
    EdgeBody, VertexBody = {}, {}
    for EdgeData in Model.edges:
        UsesValue = Topology.edge_coedges[EdgeData.id]
        BodyIdsData = {
            FaceBody[Topology.loop_face[Topology.coedge_loop[CoedgeId]]]
            for CoedgeId in UsesValue
        }
        if len(BodyIdsData) != 1:
            raise ParaWriteError(f"Parasolid edge {EdgeData.id} spans multiple bodies")
        BodyId = next(iter(BodyIdsData))
        EdgeBody[EdgeData.id] = BodyId
        for VertexId in (EdgeData.start_vertex_id, EdgeData.end_vertex_id):
            Prior = VertexBody.setdefault(VertexId, BodyId)
            if Prior != BodyId:
                raise ParaWriteError(
                    f"Parasolid vertex {VertexId} spans multiple bodies"
                )
    return EdgeBody, VertexBody


# geometry link construction orders faces per surface and edges per curve
def MakeGeomLinks(
    Model: BrepModel, Topology: BrepTopology
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    SurfFaces = {SurfValue.id: [] for SurfValue in Model.surfaces}
    CurveEdges = {Curve.id: [] for Curve in Model.curves}
    for FaceData in Model.faces:
        SurfFaces[FaceData.surface_id].append(FaceData.id)
    for EdgeData in Model.edges:
        CurveEdges[EdgeData.curve_id].append(EdgeData.id)
    for SurfId, FaceIds in SurfFaces.items():
        SurfFaces[SurfId] = OrderIds(
            FaceIds, Topology.faces, "parasolid.surface_face_order"
        )
    for CurveId, EdgeIds in CurveEdges.items():
        CurveEdges[CurveId] = OrderIds(
            EdgeIds, Topology.edges, "parasolid.curve_edge_order"
        )
    return SurfFaces, CurveEdges


# body group filling proves each geometry record has one owning body
def FillBodyMut(
    Model: BrepModel,
    FaceBody: Mapping[str, str],
    EdgeBody: Mapping[str, str],
    VertexBody: Mapping[str, str],
    SurfFaces: Mapping[str, Sequence[str]],
    CurveEdges: Mapping[str, Sequence[str]],
    BodySurfaces: dict[str, list[str]],
    BodyCurves: dict[str, list[str]],
    BodyPoints: dict[str, list[str]],
    BodyVertices: dict[str, list[str]],
    BodyEdges: dict[str, list[str]],
) -> None:
    for SurfValue in Model.surfaces:
        Owners = {FaceBody[FaceId] for FaceId in SurfFaces[SurfValue.id]}
        if len(Owners) != 1:
            raise ParaWriteError(
                f"Parasolid surface {SurfValue.id} spans multiple bodies"
            )
        BodySurfaces[next(iter(Owners))].append(SurfValue.id)
    for Curve in Model.curves:
        Owners = {EdgeBody[EdgeId] for EdgeId in CurveEdges[Curve.id]}
        if len(Owners) != 1:
            raise ParaWriteError(f"Parasolid curve {Curve.id} spans multiple bodies")
        BodyCurves[next(iter(Owners))].append(Curve.id)
    for Vertex in Model.vertices:
        BodyId = VertexBody.get(Vertex.id)
        if BodyId is None:
            raise ParaWriteError(f"Parasolid vertex {Vertex.id} has no owning body")
        BodyPoints[BodyId].append(Vertex.id)
        BodyVertices[BodyId].append(Vertex.id)
    for EdgeData in Model.edges:
        BodyEdges[EdgeBody[EdgeData.id]].append(EdgeData.id)


# body group ordering applies native metadata independently to every record family
def OrderBodyMut(
    Model: BrepModel,
    Topology: BrepTopology,
    BodySurfaces: dict[str, list[str]],
    BodyCurves: dict[str, list[str]],
    BodyPoints: dict[str, list[str]],
    BodyVertices: dict[str, list[str]],
    BodyEdges: dict[str, list[str]],
) -> None:
    for BodyData in Model.bodies:
        BodySurfaces[BodyData.id] = OrderIds(
            BodySurfaces[BodyData.id], Topology.surface_by_id, "parasolid.surface_order"
        )
        BodyCurves[BodyData.id] = OrderIds(
            BodyCurves[BodyData.id], Topology.curve_by_id, "parasolid.curve_order"
        )
        BodyPoints[BodyData.id] = OrderIds(
            BodyPoints[BodyData.id], Topology.vertex_by_id, "parasolid.point_order"
        )
        BodyVertices[BodyData.id] = OrderIds(
            BodyVertices[BodyData.id], Topology.vertex_by_id, "parasolid.vertex_order"
        )
        BodyEdges[BodyData.id] = OrderIds(
            BodyEdges[BodyData.id], Topology.edges, "parasolid.edge_order"
        )


# body group construction partitions each ordered geometry family by owning body
def MakeBodyGroups(
    Model: BrepModel,
    Topology: BrepTopology,
    FaceBody: Mapping[str, str],
    EdgeBody: Mapping[str, str],
    VertexBody: Mapping[str, str],
    SurfFaces: Mapping[str, Sequence[str]],
    CurveEdges: Mapping[str, Sequence[str]],
) -> tuple[dict[str, list[str]], ...]:
    BodySurfaces = {BodyData.id: [] for BodyData in Model.bodies}
    BodyCurves = {BodyData.id: [] for BodyData in Model.bodies}
    BodyPoints = {BodyData.id: [] for BodyData in Model.bodies}
    BodyVertices = {BodyData.id: [] for BodyData in Model.bodies}
    BodyEdges = {BodyData.id: [] for BodyData in Model.bodies}
    FillBodyMut(
        Model,
        FaceBody,
        EdgeBody,
        VertexBody,
        SurfFaces,
        CurveEdges,
        BodySurfaces,
        BodyCurves,
        BodyPoints,
        BodyVertices,
        BodyEdges,
    )
    OrderBodyMut(
        Model, Topology, BodySurfaces, BodyCurves, BodyPoints, BodyVertices, BodyEdges
    )
    return BodySurfaces, BodyCurves, BodyPoints, BodyVertices, BodyEdges


# ownership construction composes topology membership geometry links and body groups
def MakeEncOwners(Model: BrepModel, Topology: BrepTopology) -> EncodeOwners:
    FaceShell, FaceRegion, FaceBody, ShellRegion, ShellBody = MakeFaceOwners(
        Model, Topology
    )
    EdgeBody, VertexBody = MakeEdgeOwners(Model, Topology, FaceBody)
    SurfFaces, CurveEdges = MakeGeomLinks(Model, Topology)
    BodyGroups = MakeBodyGroups(
        Model, Topology, FaceBody, EdgeBody, VertexBody, SurfFaces, CurveEdges
    )
    return EncodeOwners(
        FaceShell,
        FaceRegion,
        FaceBody,
        ShellRegion,
        ShellBody,
        EdgeBody,
        VertexBody,
        SurfFaces,
        CurveEdges,
        *BodyGroups,
    )


# node allocation records one monotonic perbody identifier with vendor range gaps
def AssignNodeIdMut(
    Index: int, BodyId: str, Config: EncodeConfig, Nodes: EncodeNodeState
) -> int:
    ValueData = Nodes.KNextNodeId[BodyId]
    if BodyId in Config.KAttrBases and 18 <= ValueData <= 28:
        ValueData = 29
    Nodes.KNextNodeId[BodyId] = ValueData + 1
    Nodes.KNodeIds[Index] = ValueData
    return ValueData


# topology node assignment numbers regions shells and their exterior complements
def SetTopoNodesMut(
    Model: BrepModel,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for RegionData in Model.regions:
        AssignNodeIdMut(
            Indices.KRegions[RegionData.id],
            Topology.region_body[RegionData.id],
            Config,
            Nodes,
        )
    for BodyId, Index in Indices.KExteriorRegions.items():
        AssignNodeIdMut(Index, BodyId, Config, Nodes)
    for ShellData in Model.shells:
        AssignNodeIdMut(
            Indices.KShells[ShellData.id],
            Owners.KShellBody[ShellData.id],
            Config,
            Nodes,
        )
    for ShellId, Index in Indices.KExteriorShells.items():
        AssignNodeIdMut(Index, Owners.KShellBody[ShellId], Config, Nodes)


# geometry node assignment numbers carriers vertices edges loops and faces
def SetGeomNodesMut(
    Model: BrepModel,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for SurfValue in Model.surfaces:
        AssignNodeIdMut(
            Indices.KSurfaces[SurfValue.id],
            Owners.KFaceBody[Owners.KSurfFaces[SurfValue.id][0]],
            Config,
            Nodes,
        )
    for Curve in Model.curves:
        AssignNodeIdMut(
            Indices.KCurves[Curve.id],
            Owners.KEdgeBody[Owners.KCurveEdges[Curve.id][0]],
            Config,
            Nodes,
        )
    for Vertex in Model.vertices:
        AssignNodeIdMut(
            Indices.KPoints[Vertex.id], Owners.KVertexBody[Vertex.id], Config, Nodes
        )
        AssignNodeIdMut(
            Indices.KVertices[Vertex.id], Owners.KVertexBody[Vertex.id], Config, Nodes
        )
    for EdgeData in Model.edges:
        AssignNodeIdMut(
            Indices.KEdges[EdgeData.id], Owners.KEdgeBody[EdgeData.id], Config, Nodes
        )
    for LoopData in Model.loops:
        AssignNodeIdMut(
            Indices.KLoops[LoopData.id],
            Owners.KFaceBody[Topology.loop_face[LoopData.id]],
            Config,
            Nodes,
        )
    for FaceData in Model.faces:
        AssignNodeIdMut(
            Indices.KFaces[FaceData.id], Owners.KFaceBody[FaceData.id], Config, Nodes
        )


# vendor attribute node assignment numbers solidworks face and body chains
def SetAttrNodesMut(
    Model: BrepModel,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Nodes: EncodeNodeState,
) -> None:
    if not Config.KSolidSolid:
        return
    BodyId = Model.bodies[0].id
    for FaceData in Model.faces:
        for Index in Indices.KSolidFaceAttrs[FaceData.id]:
            AssignNodeIdMut(Index, BodyId, Config, Nodes)
    for NameValue in (
        "timestamp",
        "feature",
        "implicit",
        "match",
        "density",
        "lightweight",
        "recipe",
    ):
        AssignNodeIdMut(Indices.KSolidBodyAttrs[NameValue], BodyId, Config, Nodes)


# node state construction runs topology geometry and vendor numbering phases
def MakeNodeState(
    Model: BrepModel,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
) -> EncodeNodeState:
    Nodes = EncodeNodeState({}, {BodyData.id: 1 for BodyData in Model.bodies})
    SetTopoNodesMut(Model, Topology, Config, Indices, Owners, Nodes)
    SetGeomNodesMut(Model, Topology, Config, Indices, Owners, Nodes)
    SetAttrNodesMut(Model, Config, Indices, Nodes)
    return Nodes


# loop orientation converts face reversals into encoded coedge traversal directions
def MakeLoopOrder(
    Model: BrepModel, Topology: BrepTopology
) -> tuple[dict[str, tuple[str, ...]], dict[str, bool]]:
    EncodedLoops, EncodedReversed = {}, {}
    for LoopData in Model.loops:
        FaceData = Topology.faces[Topology.loop_face[LoopData.id]]
        FaceForward = Topology.IsFaceForward(FaceData.id)
        EncodedLoops[LoopData.id] = (
            LoopData.coedge_ids
            if FaceForward
            else tuple(Builtins.reversed(LoopData.coedge_ids))
        )
        for CoedgeId in LoopData.coedge_ids:
            EncodedReversed[CoedgeId] = Topology.coedges[CoedgeId].reversed ^ (
                not FaceForward
            )
    return EncodedLoops, EncodedReversed


# edge fin construction assigns opposite fins and their incident vertices
def AddEdgeFinsMut(
    EdgeData: BrepEdge,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    EncodedReversed: Mapping[str, bool],
    VertexFins: dict[str, list[int]],
    FinVertex: dict[int, str],
    FinOther: dict[int, int],
) -> None:
    UsesValue = Topology.edge_coedges[EdgeData.id]
    if len(UsesValue) == 1:
        RealIndex, DummyIndex = (
            Indices.KCoedges[UsesValue[0]],
            Indices.KDummyFins[EdgeData.id],
        )
        FinOther[RealIndex], FinOther[DummyIndex] = DummyIndex, RealIndex
        RealValue = Topology.coedges[UsesValue[0]]
        RealVertex = (
            EdgeData.end_vertex_id
            if EncodedReversed[RealValue.id]
            else EdgeData.start_vertex_id
        )
        DummyVertex = (
            EdgeData.start_vertex_id
            if EncodedReversed[RealValue.id]
            else EdgeData.end_vertex_id
        )
        FinVertex[RealIndex], FinVertex[DummyIndex] = RealVertex, DummyVertex
        VertexFins[RealVertex].append(RealIndex)
        VertexFins[DummyVertex].append(DummyIndex)
        return
    for Position, CoedgeId in enumerate(UsesValue):
        Index = Indices.KCoedges[CoedgeId]
        FinOther[Index] = Indices.KCoedges[UsesValue[(Position + 1) % len(UsesValue)]]
        VertexId = (
            EdgeData.end_vertex_id
            if EncodedReversed[CoedgeId]
            else EdgeData.start_vertex_id
        )
        FinVertex[Index] = VertexId
        VertexFins[VertexId].append(Index)


# requested fin ordering is accepted only when it exactly covers the vertex ring
def SetFinOrderMut(
    Model: BrepModel, Indices: EncodeIndices, VertexFins: dict[str, list[int]]
) -> None:
    for Vertex in Model.vertices:
        Requested = Vertex.attributes.get("parasolid.vertex_fins")
        if not isinstance(Requested, (tuple, list)):
            continue
        OrderData = [
            FinIndex(Descriptor, Indices.KCoedges, Indices.KDummyFins)
            for Descriptor in Requested
        ]
        IsComplete = all((Index is not None for Index in OrderData)) and len(
            set(OrderData)
        ) == len(OrderData)
        if IsComplete and set(OrderData) == set(VertexFins[Vertex.id]):
            VertexFins[Vertex.id] = [Index for Index in OrderData if Index is not None]


# fin state construction combines orientation adjacency ordering and body face anchors
def MakeFinState(
    Model: BrepModel,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
) -> EncodeFinState:
    EncodedLoops, EncodedReversed = MakeLoopOrder(Model, Topology)
    VertexFins = {Vertex.id: [] for Vertex in Model.vertices}
    FinVertex, FinOther = {}, {}
    for EdgeData in Model.edges:
        AddEdgeFinsMut(
            EdgeData,
            Topology,
            Indices,
            EncodedReversed,
            VertexFins,
            FinVertex,
            FinOther,
        )
    SetFinOrderMut(Model, Indices, VertexFins)
    FirstFaceByBody = {}
    for FaceData in Model.faces:
        FirstFaceByBody.setdefault(Owners.KFaceBody[FaceData.id], FaceData.id)
    return EncodeFinState(
        EncodedLoops, EncodedReversed, VertexFins, FinVertex, FinOther, FirstFaceByBody
    )


# partition header emission writes the optional root node and fixed framing values
def WriteHeadMut(
    Output: bytearray, Model: BrepModel, PartValue: bool, Indices: EncodeIndices
) -> None:
    if not PartValue:
        return
    VTwelveNode(Output, 101, 1)
    for ValueData in (
        0,
        0,
        Indices.KBodies[Model.bodies[0].id] if Model.bodies else 0,
        0,
        0,
        0,
        0,
    ):
        WritePointerMut(Output, ValueData)
    Output.append(1)
    WritePointerMut(Output, 0)
    WriteSignedMut(Output, 0)
    WriteSignedMut(Output, 0)


# body emission serializes every body root in deterministic model order
def EmitBodiesMut(
    Output: bytearray,
    Model: BrepModel,
    Topology: BrepTopology,
    PartValue: bool,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for Position, BodyData in enumerate(Model.bodies):
        EmitBodyMut(
            Output,
            Position,
            BodyData,
            Model,
            Topology,
            PartValue,
            Config,
            Indices,
            Owners,
            Nodes,
        )


# body record emission writes node links geometry heads and vendor attribute prefixes
def EmitBodyMut(
    Output: bytearray,
    Position: int,
    BodyData: BrepBody,
    Model: BrepModel,
    Topology: BrepTopology,
    PartValue: bool,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    BodyIndex = Indices.KBodies[BodyData.id]
    RegionValues = [Indices.KRegions[RegionId] for RegionId in BodyData.region_ids]
    Solid = all((Topology.regions[RegionId].solid for RegionId in BodyData.region_ids))
    if Solid:
        RegionValues.insert(0, Indices.KExteriorRegions[BodyData.id])
    BodyShells = [
        ShellId for ShellId, Owner in Owners.KShellBody.items() if Owner == BodyData.id
    ]
    AttrBase = Config.KAttrBases.get(BodyData.id)
    HighestNodeId = max(
        Nodes.KNextNodeId[BodyData.id] - 1, 28 if AttrBase is not None else 0
    )
    VTwelveNode(Output, 12, BodyIndex)
    WriteSignedMut(Output, HighestNodeId)
    for ValueData in (
        AttrBase + 2 if AttrBase is not None else 0,
        AttrBase + 3 if AttrBase is not None else 0,
        0,
        0,
        0,
        0,
    ):
        WritePointerMut(Output, ValueData)
    WriteFloatMut(
        Output,
        MathValue.nextafter(1000.0, MathValue.inf) if Config.KSolidSolid else 1000.0,
    )
    WriteFloatMut(Output, 1e-08)
    NextBody = (
        Indices.KBodies[Model.bodies[Position + 1].id]
        if Position + 1 < len(Model.bodies)
        else AttrBase + 4 if len(Model.bodies) == 1 and AttrBase is not None else 0
    )
    PreviousBody = Indices.KBodies[Model.bodies[Position - 1].id] if Position else 0
    for ValueData in (0, NextBody, PreviousBody):
        WritePointerMut(Output, ValueData)
    Output.append(1)
    WritePointerMut(Output, 1 if PartValue else 0)
    Output.extend((1 if Solid else 3, 1))
    Heads = (
        Indices.KShells[BodyShells[0]] if BodyShells else 0,
        (
            Indices.KSurfaces[Owners.KBodySurfaces[BodyData.id][0]]
            if Owners.KBodySurfaces[BodyData.id]
            else 0
        ),
        (
            Indices.KCurves[Owners.KBodyCurves[BodyData.id][0]]
            if Owners.KBodyCurves[BodyData.id]
            else 0
        ),
        (
            Indices.KPoints[Owners.KBodyPoints[BodyData.id][0]]
            if Owners.KBodyPoints[BodyData.id]
            else 0
        ),
        RegionValues[0] if RegionValues else 0,
        (
            Indices.KEdges[Owners.KBodyEdges[BodyData.id][0]]
            if Owners.KBodyEdges[BodyData.id]
            else 0
        ),
        (
            Indices.KVertices[Owners.KBodyVertices[BodyData.id][0]]
            if Owners.KBodyVertices[BodyData.id]
            else 0
        ),
    )
    for ValueData in Heads:
        WritePointerMut(Output, ValueData)
    if AttrBase is not None:
        WritePrefixMut(Output, AttrBase, BodyIndex, 11 if Config.KSolidSolid else 7)


# region emission writes exterior complements before each body native regions
def EmitRegionsMut(
    Output: bytearray,
    Model: BrepModel,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for BodyData in Model.bodies:
        RegionValues = list(BodyData.region_ids)
        Solid = all(
            (Topology.regions[RegionId].solid for RegionId in BodyData.region_ids)
        )
        if Solid:
            EmitOuterMut(Output, BodyData.id, RegionValues, Indices, Owners, Nodes)
        for Position, RegionId in enumerate(RegionValues):
            EmitRegionMut(
                Output,
                Position,
                RegionId,
                RegionValues,
                BodyData.id,
                Solid,
                Topology,
                Indices,
                Nodes,
            )


# exterior region emission connects solid complement shells to their native body
def EmitOuterMut(
    Output: bytearray,
    BodyId: str,
    RegionValues: Sequence[str],
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    ExteriorIndex = Indices.KExteriorRegions[BodyId]
    VTwelveNode(Output, 19, ExteriorIndex)
    WriteSignedMut(Output, Nodes.KNodeIds[ExteriorIndex])
    for ValueData in (
        0,
        Indices.KBodies[BodyId],
        Indices.KRegions[RegionValues[0]] if RegionValues else 0,
        0,
    ):
        WritePointerMut(Output, ValueData)
    Exterior = [
        Indices.KExteriorShells[ShellId]
        for ShellId, Owner in Owners.KShellBody.items()
        if Owner == BodyId and ShellId in Indices.KExteriorShells
    ]
    WritePointerMut(Output, Exterior[0] if Exterior else 0)
    Output.extend(b"V")


# native region emission writes body sibling and shell relationships
def EmitRegionMut(
    Output: bytearray,
    Position: int,
    RegionId: str,
    RegionValues: Sequence[str],
    BodyId: str,
    Solid: bool,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Nodes: EncodeNodeState,
) -> None:
    RegionData = Topology.regions[RegionId]
    RegionIndex = Indices.KRegions[RegionId]
    ShellIds = [
        Topology.shell_uses[ShellUseId].shell_id
        for ShellUseId in RegionData.shell_use_ids
    ]
    VTwelveNode(Output, 19, RegionIndex)
    WriteSignedMut(Output, Nodes.KNodeIds[RegionIndex])
    Previous = (
        Indices.KExteriorRegions[BodyId]
        if Solid and Position == 0
        else Indices.KRegions[RegionValues[Position - 1]] if Position else 0
    )
    Values = (
        0,
        Indices.KBodies[BodyId],
        (
            Indices.KRegions[RegionValues[Position + 1]]
            if Position + 1 < len(RegionValues)
            else 0
        ),
        Previous,
        Indices.KShells[ShellIds[0]] if ShellIds else 0,
    )
    for ValueData in Values:
        WritePointerMut(Output, ValueData)
    Output.extend(b"S" if RegionData.solid else b"V")


# shell emission writes native shells followed by optional solid complement shells
def EmitShellsMut(
    Output: bytearray,
    Model: BrepModel,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for ShellData in Model.shells:
        FaceIds = EmitShellMut(Output, ShellData, Topology, Indices, Owners, Nodes)
        if ShellData.id in Indices.KExteriorShells:
            EmitOuterShMut(Output, ShellData.id, FaceIds, Indices, Owners, Nodes)


# native shell emission writes region sibling and ordered face relationships
def EmitShellMut(
    Output: bytearray,
    ShellData: BrepShell,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> list[str]:
    ShellIndex = Indices.KShells[ShellData.id]
    RegionId = Owners.KShellRegion[ShellData.id]
    RegionData = Topology.regions[RegionId]
    BodyId = Owners.KShellBody[ShellData.id]
    ShellIds = [
        Topology.shell_uses[ShellUseId].shell_id
        for ShellUseId in RegionData.shell_use_ids
    ]
    Position = ShellIds.index(ShellData.id)
    FaceIds = OrderIds(
        [Topology.face_uses[FaceUseId].face_id for FaceUseId in ShellData.face_use_ids],
        Topology.faces,
        "parasolid.face_order",
    )
    VTwelveNode(Output, 13, ShellIndex)
    WriteSignedMut(Output, Nodes.KNodeIds[ShellIndex])
    Values = (
        0,
        Indices.KBodies[BodyId],
        Indices.KShells[ShellIds[Position + 1]] if Position + 1 < len(ShellIds) else 0,
        Indices.KFaces[FaceIds[0]] if FaceIds else 0,
        0,
        0,
        Indices.KRegions[RegionId],
        0,
    )
    for ValueData in Values:
        WritePointerMut(Output, ValueData)
    return FaceIds


# exterior shell emission writes complement sibling region and face relationships
def EmitOuterShMut(
    Output: bytearray,
    ShellId: str,
    FaceIds: Sequence[str],
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    BodyId = Owners.KShellBody[ShellId]
    ExteriorIndex = Indices.KExteriorShells[ShellId]
    ExteriorIds = [
        ValueData
        for ValueData, Owner in Owners.KShellBody.items()
        if Owner == BodyId and ValueData in Indices.KExteriorShells
    ]
    Position = ExteriorIds.index(ShellId)
    VTwelveNode(Output, 13, ExteriorIndex)
    WriteSignedMut(Output, Nodes.KNodeIds[ExteriorIndex])
    Values = (
        0,
        0,
        (
            Indices.KExteriorShells[ExteriorIds[Position + 1]]
            if Position + 1 < len(ExteriorIds)
            else 0
        ),
        0,
        0,
        0,
        Indices.KExteriorRegions[BodyId],
        Indices.KFaces[FaceIds[0]] if FaceIds else 0,
    )
    for ValueData in Values:
        WritePointerMut(Output, ValueData)


# surface emission serializes analytic carriers in their perbody linked order
def EmitSurfacesMut(
    Output: bytearray,
    Model: BrepModel,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for SurfValue in Model.surfaces:
        if isinstance(SurfValue, NurbsSurface):
            raise ParaWriteError(
                f"Parasolid V12 writer does not support NURBS surface {SurfValue.id}"
            )
        KindValueData, Values = SurfValues(SurfValue)
        FaceIds = Owners.KSurfFaces[SurfValue.id]
        BodyId = Owners.KFaceBody[FaceIds[0]]
        Chain = Owners.KBodySurfaces[BodyId]
        Position = Chain.index(SurfValue.id)
        WriteGeomMut(
            Output,
            KindValueData,
            Indices.KSurfaces[SurfValue.id],
            Nodes.KNodeIds[Indices.KSurfaces[SurfValue.id]],
            Indices.KFaces[FaceIds[0]],
            Indices.KSurfaces[Chain[Position + 1]] if Position + 1 < len(Chain) else 0,
            Indices.KSurfaces[Chain[Position - 1]] if Position else 0,
            Values,
        )


# curve emission serializes analytic carriers in their perbody linked order
def EmitCurvesMut(
    Output: bytearray,
    Model: BrepModel,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for Curve in Model.curves:
        if isinstance(Curve, NurbsCurve):
            raise ParaWriteError(
                f"Parasolid V12 writer does not support NURBS curve {Curve.id}"
            )
        KindValueData, Values = CurveValues(Curve)
        EdgeIds = Owners.KCurveEdges[Curve.id]
        BodyId = Owners.KEdgeBody[EdgeIds[0]]
        Chain = Owners.KBodyCurves[BodyId]
        Position = Chain.index(Curve.id)
        WriteGeomMut(
            Output,
            KindValueData,
            Indices.KCurves[Curve.id],
            Nodes.KNodeIds[Indices.KCurves[Curve.id]],
            Indices.KEdges[EdgeIds[0]],
            Indices.KCurves[Chain[Position + 1]] if Position + 1 < len(Chain) else 0,
            Indices.KCurves[Chain[Position - 1]] if Position else 0,
            Values,
        )


# point emission writes coordinate records and their perbody sibling links
def EmitPointsMut(
    Output: bytearray,
    Model: BrepModel,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
) -> None:
    for Vertex in Model.vertices:
        BodyId = Owners.KVertexBody[Vertex.id]
        Chain = Owners.KBodyPoints[BodyId]
        Position = Chain.index(Vertex.id)
        VTwelveNode(Output, 29, Indices.KPoints[Vertex.id])
        WriteSignedMut(Output, Nodes.KNodeIds[Indices.KPoints[Vertex.id]])
        Values = (
            0,
            Indices.KVertices[Vertex.id],
            Indices.KPoints[Chain[Position + 1]] if Position + 1 < len(Chain) else 0,
            Indices.KPoints[Chain[Position - 1]] if Position else 0,
        )
        for ValueData in Values:
            WritePointerMut(Output, ValueData)
        Vector(Output, Vertex.point, KLengthScale)


# vertex emission writes fin heads tolerance body and perbody sibling links
def EmitVerticesMut(
    Output: bytearray,
    Model: BrepModel,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
    FinState: EncodeFinState,
) -> None:
    for Vertex in Model.vertices:
        BodyId = Owners.KVertexBody[Vertex.id]
        Chain = Owners.KBodyVertices[BodyId]
        Position = Chain.index(Vertex.id)
        FinsValue = FinState.KVertexFins[Vertex.id]
        VTwelveNode(Output, 18, Indices.KVertices[Vertex.id])
        WriteSignedMut(Output, Nodes.KNodeIds[Indices.KVertices[Vertex.id]])
        Values = (
            0,
            FinsValue[0] if FinsValue else 0,
            Indices.KVertices[Chain[Position - 1]] if Position else 0,
            Indices.KVertices[Chain[Position + 1]] if Position + 1 < len(Chain) else 0,
            Indices.KPoints[Vertex.id],
        )
        for ValueData in Values:
            WritePointerMut(Output, ValueData)
        WriteFloatMut(
            Output,
            (
                KMissingParam
                if Vertex.tolerance == 0.0
                else Vertex.tolerance * KLengthScale
            ),
        )
        WritePointerMut(Output, Indices.KBodies[BodyId])


# edge emission writes tolerance fin carrier and both linked ordering dimensions
def EmitEdgesMut(
    Output: bytearray,
    Model: BrepModel,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
    FinState: EncodeFinState,
) -> None:
    for EdgeData in Model.edges:
        BodyId = Owners.KEdgeBody[EdgeData.id]
        Chain = Owners.KBodyEdges[BodyId]
        Position = Chain.index(EdgeData.id)
        CurveChain = Owners.KCurveEdges[EdgeData.curve_id]
        CurvePosition = CurveChain.index(EdgeData.id)
        FirstFin = FinIndex(
            EdgeData.attributes.get("parasolid.first_fin"),
            Indices.KCoedges,
            Indices.KDummyFins,
        )
        if FirstFin is None:
            FirstFin = Indices.KCoedges[Topology.edge_coedges[EdgeData.id][0]]
        VTwelveNode(Output, 16, Indices.KEdges[EdgeData.id])
        WriteSignedMut(Output, Nodes.KNodeIds[Indices.KEdges[EdgeData.id]])
        WritePointerMut(Output, 0)
        WriteFloatMut(
            Output,
            (
                KMissingParam
                if EdgeData.tolerance == 0.0
                else EdgeData.tolerance * KLengthScale
            ),
        )
        Values = (
            FirstFin,
            Indices.KEdges[Chain[Position - 1]] if Position else 0,
            Indices.KEdges[Chain[Position + 1]] if Position + 1 < len(Chain) else 0,
            Indices.KCurves[EdgeData.curve_id],
            (
                Indices.KEdges[CurveChain[CurvePosition + 1]]
                if CurvePosition + 1 < len(CurveChain)
                else 0
            ),
            Indices.KEdges[CurveChain[CurvePosition - 1]] if CurvePosition else 0,
            Indices.KBodies[BodyId],
        )
        for ValueData in Values:
            WritePointerMut(Output, ValueData)


# coedge emission writes oriented loop neighbors opposite fins and vertex rings
def EmitCoedgesMut(
    Output: bytearray,
    Model: BrepModel,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    FinState: EncodeFinState,
) -> None:
    for Coedge in Model.coedges:
        LoopData = Topology.loops[Topology.coedge_loop[Coedge.id]]
        FaceData = Topology.faces[Topology.loop_face[LoopData.id]]
        RegionData = Topology.regions[Owners.KFaceRegion[FaceData.id]]
        LoopCoedges = FinState.KEncodedLoopCoedges[LoopData.id]
        Position = LoopCoedges.index(Coedge.id)
        PreviousId, NextId = (
            LoopCoedges[Position - 1],
            LoopCoedges[(Position + 1) % len(LoopCoedges)],
        )
        FinIndexData = Indices.KCoedges[Coedge.id]
        PreviousFin = (
            Indices.KCoedges[PreviousId]
            if RegionData.solid
            else Indices.KCoedges[NextId]
        )
        NextFin = (
            Indices.KCoedges[NextId]
            if RegionData.solid
            else Indices.KCoedges[PreviousId]
        )
        WriteFinMut(
            Output,
            FinIndexData,
            0,
            Indices.KLoops[LoopData.id],
            PreviousFin,
            NextFin,
            Indices.KVertices[FinState.KFinVertex[FinIndexData]],
            FinState.KFinOther[FinIndexData],
            Indices.KEdges[Coedge.edge_id],
            0,
            NextFinAtVertex(FinIndexData, FinState.KVertexFins),
            not FinState.KEncodedCoedgeReversed[Coedge.id],
        )


# dummy fin emission closes sheet edges that have only one real coedge
def EmitDummyMut(
    Output: bytearray,
    Config: EncodeConfig,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    FinState: EncodeFinState,
) -> None:
    for EdgeData in Config.KDummyEdges:
        FinIndexData = Indices.KDummyFins[EdgeData.id]
        RealValue = Topology.coedges[Topology.edge_coedges[EdgeData.id][0]]
        WriteFinMut(
            Output,
            FinIndexData,
            0,
            0,
            0,
            0,
            Indices.KVertices[FinState.KFinVertex[FinIndexData]],
            FinState.KFinOther[FinIndexData],
            Indices.KEdges[EdgeData.id],
            0,
            NextFinAtVertex(FinIndexData, FinState.KVertexFins),
            FinState.KEncodedCoedgeReversed[RealValue.id],
        )


# loop emission writes first fin face and sibling loop relationships
def EmitLoopsMut(
    Output: bytearray,
    Model: BrepModel,
    Topology: BrepTopology,
    Indices: EncodeIndices,
    Nodes: EncodeNodeState,
    FinState: EncodeFinState,
) -> None:
    for LoopData in Model.loops:
        FaceData = Topology.faces[Topology.loop_face[LoopData.id]]
        Position = FaceData.loop_ids.index(LoopData.id)
        NextLoopId = (
            FaceData.loop_ids[Position + 1]
            if Position + 1 < len(FaceData.loop_ids)
            else ""
        )
        VTwelveNode(Output, 15, Indices.KLoops[LoopData.id])
        WriteSignedMut(Output, Nodes.KNodeIds[Indices.KLoops[LoopData.id]])
        for ValueData in (
            0,
            Indices.KCoedges[FinState.KEncodedLoopCoedges[LoopData.id][0]],
            Indices.KFaces[FaceData.id],
            Indices.KLoops.get(NextLoopId, 0),
        ):
            WritePointerMut(Output, ValueData)


# face chain discovery gathers every linked ordering position and ownership record
def FaceChainData(
    FaceData: BrepFace,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Owners: EncodeOwners,
    FinState: EncodeFinState,
) -> tuple[object, ...]:
    ShellData = Topology.shells[Owners.KFaceShell[FaceData.id]]
    FaceIds = OrderIds(
        [Topology.face_uses[FaceUseId].face_id for FaceUseId in ShellData.face_use_ids],
        Topology.faces,
        "parasolid.face_order",
    )
    Position = FaceIds.index(FaceData.id)
    FrontFaceIds = OrderIds(FaceIds, Topology.faces, "parasolid.front_face_order")
    FrontPosition = FrontFaceIds.index(FaceData.id)
    SurfChain = Owners.KSurfFaces[FaceData.surface_id]
    SurfPosition = SurfChain.index(FaceData.id)
    RegionData = Topology.regions[Owners.KFaceRegion[FaceData.id]]
    AttrBase = Config.KAttrBases.get(Owners.KFaceBody[FaceData.id])
    FirstFaceId = FinState.KFirstFaceByBody.get(Owners.KFaceBody[FaceData.id])
    return (
        ShellData,
        FaceIds,
        Position,
        FrontFaceIds,
        FrontPosition,
        SurfChain,
        SurfPosition,
        RegionData,
        AttrBase,
        FirstFaceId,
    )


# face emission serializes tolerance loops carriers and three linked ordering dimensions
def EmitFaceMut(
    Output: bytearray,
    FaceData: BrepFace,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
    FinState: EncodeFinState,
) -> None:
    (
        ShellData,
        FaceIds,
        Position,
        FrontFaceIds,
        FrontPosition,
        SurfChain,
        SurfPosition,
        RegionData,
        AttrBase,
        FirstFaceId,
    ) = FaceChainData(FaceData, Topology, Config, Owners, FinState)
    VTwelveNode(Output, 14, Indices.KFaces[FaceData.id])
    WriteSignedMut(Output, Nodes.KNodeIds[Indices.KFaces[FaceData.id]])
    FaceAttr = (
        Indices.KSolidFaceAttrs[FaceData.id][0]
        if FaceData.id in Indices.KSolidFaceAttrs
        else AttrBase + 32 if AttrBase is not None and FaceData.id == FirstFaceId else 0
    )
    WritePointerMut(Output, FaceAttr)
    WriteFloatMut(
        Output,
        (
            KMissingParam
            if FaceData.tolerance == 0.0
            else FaceData.tolerance * KLengthScale
        ),
    )
    Values = (
        Indices.KFaces[FaceIds[Position + 1]] if Position + 1 < len(FaceIds) else 0,
        Indices.KFaces[FaceIds[Position - 1]] if Position else 0,
        Indices.KLoops[FaceData.loop_ids[0]],
        Indices.KShells[ShellData.id],
        Indices.KSurfaces[FaceData.surface_id],
    )
    for ValueData in Values:
        WritePointerMut(Output, ValueData)
    Output.extend(b"+" if FaceData.same_sense else b"-")
    Values = (
        (
            Indices.KFaces[SurfChain[SurfPosition + 1]]
            if SurfPosition + 1 < len(SurfChain)
            else 0
        ),
        Indices.KFaces[SurfChain[SurfPosition - 1]] if SurfPosition else 0,
        (
            Indices.KFaces[FrontFaceIds[FrontPosition + 1]]
            if FrontPosition + 1 < len(FrontFaceIds)
            else 0
        ),
        Indices.KFaces[FrontFaceIds[FrontPosition - 1]] if FrontPosition else 0,
        (
            Indices.KExteriorShells[ShellData.id]
            if RegionData.solid
            else Indices.KShells[ShellData.id]
        ),
    )
    for ValueData in Values:
        WritePointerMut(Output, ValueData)


# face collection emission delegates each record after shared state construction
def EmitFacesMut(
    Output: bytearray,
    Model: BrepModel,
    Topology: BrepTopology,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Owners: EncodeOwners,
    Nodes: EncodeNodeState,
    FinState: EncodeFinState,
) -> None:
    for FaceData in Model.faces:
        EmitFaceMut(
            Output, FaceData, Topology, Config, Indices, Owners, Nodes, FinState
        )


# vendor attribute emission writes solidworks body or sheet compatibility records
def EmitVendorMut(
    Output: bytearray,
    Model: BrepModel,
    Config: EncodeConfig,
    Indices: EncodeIndices,
    Nodes: EncodeNodeState,
    FinState: EncodeFinState,
) -> None:
    for BodyData in Model.bodies:
        AttrBase = Config.KAttrBases.get(BodyData.id)
        FirstFaceId = FinState.KFirstFaceByBody.get(BodyData.id)
        if AttrBase is None or FirstFaceId is None:
            continue
        if Config.KSolidSolid:
            Faces = tuple(
                (
                    (
                        FaceData.id,
                        Indices.KFaces[FaceData.id],
                        Indices.KSolidFaceAttrs[FaceData.id],
                        Indices.KSolidFaceValues[FaceData.id],
                        FaceData.attributes.get("solidworks.unchanged_id"),
                        FaceData.attributes,
                    )
                    for FaceData in Model.faces
                )
            )
            WriteSolidAttrs(
                Output,
                AttrBase,
                Indices.KBodies[BodyData.id],
                Faces,
                Indices.KSolidFaceDefinitions,
                Indices.KSolidFaceDefNext,
                Indices.KSolidFaceIds,
                Indices.KSolidBodyAttrs,
                Indices.KSolidBodyValues,
                Indices.KSolidBodyDefinitions,
                Indices.KSolidBodyDefNext,
                Indices.KSolidBodyIds,
                Nodes.KNodeIds,
                Config.KFeatureIds[BodyData.id],
            )
        else:
            WriteBodySuffix(
                Output,
                AttrBase,
                Indices.KBodies[BodyData.id],
                Indices.KFaces[FirstFaceId],
                Config.KFeatureIds[BodyData.id],
            )


# this declaration exists because focused behavior needs one stable owner
def WritePrefixMut(
    Output: bytearray, BaseValue: int, BodyData: int, AttrCount: int
) -> None:
    VTwelveAttr(
        Output,
        BaseValue + 2,
        28,
        BaseValue + 12,
        BodyData,
        BaseValue + 13,
        0,
        0,
        0,
        (0, BaseValue + 14),
    )
    VTwelveNode(Output, 70, BaseValue + 3)
    WriteSignedMut(Output, 0)
    WritePointerMut(Output, BodyData)
    WritePointerMut(Output, 0)
    WritePointerMut(Output, 0)
    for ValueData in (4, AttrCount, 20, 8):
        WriteSignedMut(Output, ValueData)
    WritePointerMut(Output, BaseValue + 15)
    WritePointerMut(Output, BaseValue + 15)
    WriteSignedMut(Output, 1)
    Output.append(1)


# this declaration exists because focused behavior needs one stable owner
def WriteSolidAttrs(
    Output: bytearray,
    BaseValue: int,
    BodyData: int,
    Faces: Sequence[
        tuple[
            str,
            int,
            tuple[int, int, int],
            tuple[int, int, int],
            object,
            Mapping[str, object],
        ]
    ],
    FaceDefinitions: Mapping[str, int],
    FaceDefNext: Mapping[str, int],
    FaceIds: Mapping[str, int],
    BodyAttrs: Mapping[str, int],
    BodyValues: Mapping[str, int],
    BodyDefinitions: Mapping[str, int],
    BodyDefNext: Mapping[str, int],
    BodyIds: Mapping[str, int],
    NodeIds: Mapping[int, int],
    FeatureId: int,
) -> None:
    StandardActions = (0, 0, 0, 0, 3, 5, 0, 0)
    RetainedActions = (1, 1, 1, 1, 1, 1, 1, 1)
    FaceLegal = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ColouredFaceLegal = (0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0)
    BodyLegal = (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ImplicitBodyLegal = (0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0)
    OrderFaces, Neighbors = FaceAttrOrder(Faces)
    WriteFaceAttMut(Output, Faces, FaceDefinitions, NodeIds, Neighbors)
    FirstAttrs = WriteFaceDefMut(
        Output,
        OrderFaces,
        FaceDefinitions,
        FaceDefNext,
        FaceIds,
        StandardActions,
        RetainedActions,
        FaceLegal,
        ColouredFaceLegal,
    )
    WriteBodyAttMut(
        Output,
        BaseValue,
        BodyData,
        FirstAttrs,
        BodyAttrs,
        BodyValues,
        BodyDefinitions,
        BodyDefNext,
        BodyIds,
        NodeIds,
        FeatureId,
        StandardActions,
        RetainedActions,
        BodyLegal,
        ImplicitBodyLegal,
    )


# face attribute ordering preserves optional vendor ranks and linked list neighbors
def FaceAttrOrder(
    Faces: Sequence[tuple[object, ...]],
) -> tuple[
    dict[str, Sequence[tuple[object, ...]]], dict[tuple[str, str], tuple[int, int]]
]:
    OrderFaces: dict[str, Sequence[tuple[object, ...]]] = {}
    Neighbors: dict[tuple[str, str], tuple[int, int]] = {}
    for KindValueData, AttrPosition in (
        ("unchanged", 0),
        ("downstream", 1),
        ("colour", 2),
    ):
        Values = list(Faces)
        Ranks = [
            ValueData[5].get(f"solidworks.{KindValueData}_order")
            for ValueData in Values
        ]
        if all(
            (type(RankValue) is int and RankValue >= 0 for RankValue in Ranks)
        ) and len(set(Ranks)) == len(Ranks):

            # this callback exists because local behavior needs one focused transformation
            Values.sort(
                key=lambda ValueData: ValueData[5][f"solidworks.{KindValueData}_order"]
            )
        OrderFaces[KindValueData] = Values
        for Position, ValueData in enumerate(Values):
            PreviousAttr = Values[Position - 1][2][AttrPosition] if Position else 0
            NextAttrData = (
                Values[Position + 1][2][AttrPosition]
                if Position + 1 < len(Values)
                else 0
            )
            Neighbors[ValueData[0], KindValueData] = (NextAttrData, PreviousAttr)
    return OrderFaces, Neighbors


# face attribute writing emits linked values without owning ordering policy
def WriteFaceAttMut(
    Output: bytearray,
    Faces: Sequence[tuple[object, ...]],
    FaceDefinitions: Mapping[str, int],
    NodeIds: Mapping[int, int],
    Neighbors: Mapping[tuple[str, str], tuple[int, int]],
) -> None:
    for FaceId, Owner, Attrs, Values, UnchangedId, Ignored in Faces:
        Unchanged, Downstream, Colour = Attrs
        UnchangedValue, DownstreamValue, ColourValue = Values
        VTwelveAttr(
            Output,
            Unchanged,
            NodeIds[Unchanged],
            FaceDefinitions["unchanged"],
            Owner,
            Downstream,
            0,
            Neighbors[FaceId, "unchanged"][0],
            Neighbors[FaceId, "unchanged"][1],
            (UnchangedValue,),
        )
        VTwelveAttr(
            Output,
            Downstream,
            NodeIds[Downstream],
            FaceDefinitions["downstream"],
            Owner,
            Colour,
            Unchanged,
            Neighbors[FaceId, "downstream"][0],
            Neighbors[FaceId, "downstream"][1],
            (DownstreamValue, 0, 0),
        )
        VTwelveAttr(
            Output,
            Colour,
            NodeIds[Colour],
            FaceDefinitions["colour"],
            Owner,
            0,
            Downstream,
            Neighbors[FaceId, "colour"][0],
            Neighbors[FaceId, "colour"][1],
            (ColourValue,),
        )
        PreservedUnchangedId = (
            UnchangedId
            if type(UnchangedId) is int and 0 < UnchangedId < 1 << 31
            else ZlibLib.crc32(FaceId.encode("utf-8")) & 2147483647 or 1
        )
        VTwelveIntVals(Output, UnchangedValue, (PreservedUnchangedId,))
        VTwelveIntVals(Output, DownstreamValue, (0, 1671915899, 31269538, 0, 0, 0))
        VTwelveRealVals(
            Output,
            ColourValue,
            (0.792156862745098, 0.8196078431372549, 0.9333333333333333),
        )


# face definition writing emits schemas and returns each linked list head
def WriteFaceDefMut(
    Output: bytearray,
    OrderFaces: Mapping[str, Sequence[tuple[object, ...]]],
    FaceDefinitions: Mapping[str, int],
    FaceDefNext: Mapping[str, int],
    FaceIds: Mapping[str, int],
    StandardActions: Sequence[int],
    RetainedActions: Sequence[int],
    FaceLegal: Sequence[int],
    ColouredFaceLegal: Sequence[int],
) -> tuple[int, int, int]:
    WriteAttrDefMut(
        Output,
        FaceDefinitions["unchanged"],
        FaceDefNext["unchanged"],
        FaceIds["unchanged"],
        9000,
        RetainedActions,
        ColouredFaceLegal,
        (1,),
    )
    WriteAttrIdMut(Output, FaceIds["unchanged"], "SWEntUnchanged")
    WriteAttrDefMut(
        Output,
        FaceDefinitions["downstream"],
        FaceDefNext["downstream"],
        FaceIds["downstream"],
        9000,
        StandardActions,
        FaceLegal,
        (1, 1, 1),
    )
    WriteAttrIdMut(Output, FaceIds["downstream"], "DOWNSTREAM_FACE_ID")
    WriteAttrDefMut(
        Output,
        FaceDefinitions["colour"],
        FaceDefNext["colour"],
        FaceIds["colour"],
        8001,
        StandardActions,
        ColouredFaceLegal,
        (2,),
    )
    WriteAttrIdMut(Output, FaceIds["colour"], "SDL/TYSA_COLOUR")
    FirstUnchanged = OrderFaces["unchanged"][0][2][0]
    FirstDownstream = OrderFaces["downstream"][0][2][1]
    FirstColour = OrderFaces["colour"][0][2][2]
    return FirstUnchanged, FirstDownstream, FirstColour


# body attribute writing emits the body chain definitions and scalar values
def WriteBodyAttMut(
    Output: bytearray,
    BaseValue: int,
    BodyData: int,
    FirstAttrs: tuple[int, int, int],
    BodyAttrs: Mapping[str, int],
    BodyValues: Mapping[str, int],
    BodyDefinitions: Mapping[str, int],
    BodyDefNext: Mapping[str, int],
    BodyIds: Mapping[str, int],
    NodeIds: Mapping[int, int],
    FeatureId: int,
    StandardActions: Sequence[int],
    RetainedActions: Sequence[int],
    BodyLegal: Sequence[int],
    ImplicitBodyLegal: Sequence[int],
) -> None:
    FirstUnchanged, FirstDownstream, FirstColour = FirstAttrs
    VTwelvePtrList(
        Output,
        BaseValue + 15,
        (
            FirstDownstream,
            BodyAttrs["timestamp"],
            BodyAttrs["feature"],
            BodyAttrs["implicit"],
            FirstUnchanged,
            BodyAttrs["match"],
            BodyAttrs["density"],
            BodyAttrs["lightweight"],
            BodyAttrs["recipe"],
            FirstColour,
            BaseValue + 2,
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
    Timestamp, Feature, Implicit = (
        BodyAttrs["timestamp"],
        BodyAttrs["feature"],
        BodyAttrs["implicit"],
    )
    Match, Density = BodyAttrs["match"], BodyAttrs["density"]
    Lightweight, Recipe = BodyAttrs["lightweight"], BodyAttrs["recipe"]
    VTwelveAttr(
        Output,
        Timestamp,
        NodeIds[Timestamp],
        BodyDefinitions["timestamp"],
        BodyData,
        0,
        Feature,
        0,
        0,
        (0, BodyValues["timestamp"]),
    )
    VTwelveAttr(
        Output,
        Feature,
        NodeIds[Feature],
        BodyDefinitions["feature"],
        BodyData,
        Timestamp,
        Implicit,
        0,
        0,
        (0, BodyValues["feature"]),
    )
    VTwelveAttr(
        Output,
        Implicit,
        NodeIds[Implicit],
        BodyDefinitions["implicit"],
        BodyData,
        Feature,
        Match,
        0,
        0,
        (BodyValues["implicit"], 0),
    )
    VTwelveAttr(
        Output,
        Match,
        NodeIds[Match],
        BodyDefinitions["match"],
        BodyData,
        Implicit,
        Density,
        0,
        0,
        (BodyValues["match"],),
    )
    VTwelveAttr(
        Output,
        Density,
        NodeIds[Density],
        BodyDefinitions["density"],
        BodyData,
        Match,
        Lightweight,
        0,
        0,
        (BodyValues["density"], 0),
    )
    VTwelveAttr(
        Output,
        Lightweight,
        NodeIds[Lightweight],
        BodyDefinitions["lightweight"],
        BodyData,
        Density,
        Recipe,
        0,
        0,
        (0, BodyValues["lightweight"]),
    )
    VTwelveAttr(
        Output,
        Recipe,
        NodeIds[Recipe],
        BodyDefinitions["recipe"],
        BodyData,
        Lightweight,
        BaseValue + 2,
        0,
        0,
        (0, 0),
    )
    Definitions = (
        ("recipe", 9000, StandardActions, BodyLegal, (9, 1), "BODY_RECIPE_2001"),
        (
            "lightweight",
            9000,
            StandardActions,
            BodyLegal,
            (9, 1),
            "BODY_IN_LIGHTWEIGHT_PERM",
        ),
        ("density", 8004, StandardActions, BodyLegal, (2, 3), "SDL/TYSA_DENSITY"),
        ("match", 9000, RetainedActions, BodyLegal, (1,), "BODY_MATCH"),
        (
            "implicit",
            9000,
            StandardActions,
            ImplicitBodyLegal,
            (10, 10),
            "SWIMPLICITBODYNAME_ID_U",
        ),
        (
            "feature",
            9000,
            StandardActions,
            BodyLegal,
            (9, 1),
            "LAST_BODY_MODIFYING_FEATURE_ID",
        ),
        ("timestamp", 9000, StandardActions, BodyLegal, (9, 1), "ENT_TIME_STAMP_2001"),
    )
    for NameValue, TypeId, Actions, Legal, Fields, IdValue in Definitions:
        WriteAttrDefMut(
            Output,
            BodyDefinitions[NameValue],
            BodyDefNext[NameValue],
            BodyIds[NameValue],
            TypeId,
            Actions,
            Legal,
            Fields,
        )
        WriteAttrIdMut(Output, BodyIds[NameValue], IdValue)
    VTwelveIntVals(Output, BodyValues["timestamp"], (121,))
    VTwelveIntVals(Output, BodyValues["feature"], (FeatureId,))
    VTwelveIntVals(Output, BodyValues["match"], (27421,))
    VTwelveRealVals(Output, BodyValues["density"], (1000.0,))
    VTwelveIntVals(Output, BodyValues["lightweight"], (1,))
    WriteAttrDefMut(
        Output,
        BaseValue + 12,
        BaseValue + 58,
        BaseValue + 59,
        9000,
        StandardActions,
        BodyLegal,
        (9, 1),
    )
    VTwelveIntVals(Output, BaseValue + 14, (101,))
    WriteAttrIdMut(Output, BaseValue + 59, "ATOM_ID_2001")


# this declaration exists because focused behavior needs one stable owner
def WriteBodySuffix(
    Output: bytearray, BaseValue: int, BodyData: int, FaceDataData: int, FeatureId: int
) -> None:
    StandardActions = (0, 0, 0, 0, 3, 5, 0, 0)
    BodyLegal = (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    VTwelveAttr(
        Output,
        BaseValue + 32,
        26,
        BaseValue + 33,
        FaceDataData,
        BaseValue + 34,
        0,
        0,
        0,
        (BaseValue + 35,),
    )
    WriteAttrDefMut(
        Output,
        BaseValue + 33,
        0,
        BaseValue + 36,
        8001,
        StandardActions,
        (0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0),
        (2,),
    )
    VTwelveAttr(
        Output,
        BaseValue + 34,
        24,
        BaseValue + 37,
        FaceDataData,
        0,
        BaseValue + 32,
        0,
        0,
        (0, 0),
    )
    VTwelveRealVals(
        Output,
        BaseValue + 35,
        (0.792156862745098, 0.8196078431372549, 0.9333333333333333),
    )
    WriteAttrDefMut(
        Output,
        BaseValue + 37,
        BaseValue + 38,
        BaseValue + 39,
        9000,
        (0, 0, 0, 0, 3, 6, 0, 0),
        (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (9, 1),
    )
    WriteAttrIdMut(Output, BaseValue + 39, "ATOM_FACE_ID_2001")
    WriteAttrIdMut(Output, BaseValue + 36, "SDL/TYSA_COLOUR")
    VTwelvePtrList(
        Output,
        BaseValue + 15,
        (
            BaseValue + 40,
            BaseValue + 41,
            BaseValue + 42,
            BaseValue + 34,
            BaseValue + 13,
            BaseValue + 32,
            BaseValue + 2,
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
    VTwelveAttr(
        Output,
        BaseValue + 40,
        19,
        BaseValue + 43,
        BodyData,
        0,
        BaseValue + 41,
        0,
        0,
        (0, BaseValue + 44),
    )
    VTwelveAttr(
        Output,
        BaseValue + 41,
        22,
        BaseValue + 45,
        BodyData,
        BaseValue + 40,
        BaseValue + 42,
        0,
        0,
        (0, BaseValue + 46),
    )
    VTwelveAttr(
        Output,
        BaseValue + 42,
        23,
        BaseValue + 47,
        BodyData,
        BaseValue + 41,
        BaseValue + 13,
        0,
        0,
        (BaseValue + 48, 0),
    )
    VTwelveAttr(
        Output,
        BaseValue + 13,
        25,
        BaseValue + 49,
        BodyData,
        BaseValue + 42,
        BaseValue + 2,
        0,
        0,
        (0, 0),
    )
    WriteAttrDefMut(
        Output,
        BaseValue + 49,
        BaseValue + 50,
        BaseValue + 51,
        9000,
        StandardActions,
        BodyLegal,
        (9, 1),
    )
    WriteAttrIdMut(Output, BaseValue + 51, "BODY_RECIPE_2001")
    WriteAttrDefMut(
        Output,
        BaseValue + 47,
        BaseValue + 52,
        BaseValue + 53,
        9000,
        StandardActions,
        (0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0),
        (10, 10),
    )
    WriteAttrIdMut(Output, BaseValue + 53, "SWIMPLICITBODYNAME_ID_U")
    WriteAttrDefMut(
        Output,
        BaseValue + 45,
        BaseValue + 54,
        BaseValue + 55,
        9000,
        StandardActions,
        BodyLegal,
        (9, 1),
    )
    VTwelveIntVals(Output, BaseValue + 46, (FeatureId,))
    WriteAttrIdMut(Output, BaseValue + 55, "LAST_BODY_MODIFYING_FEATURE_ID")
    WriteAttrDefMut(
        Output,
        BaseValue + 43,
        BaseValue + 56,
        BaseValue + 57,
        9000,
        StandardActions,
        BodyLegal,
        (9, 1),
    )
    VTwelveIntVals(Output, BaseValue + 44, (100,))
    WriteAttrIdMut(Output, BaseValue + 57, "ENT_TIME_STAMP_2001")
    WriteAttrDefMut(
        Output,
        BaseValue + 12,
        BaseValue + 58,
        BaseValue + 59,
        9000,
        StandardActions,
        BodyLegal,
        (9, 1),
    )
    VTwelveIntVals(Output, BaseValue + 14, (101,))
    WriteAttrIdMut(Output, BaseValue + 59, "ATOM_ID_2001")


# this declaration exists because focused behavior needs one stable owner
def OrderTriRecords(DataValue: bytes) -> bytes:
    Records = SplitTriRecords(DataValue)
    Order = (
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
    Ranks = {KeyValue: Position for Position, KeyValue in enumerate(Order)}
    if not set(Order).issubset((KeyValue for KeyValue, Ignored in Records)):
        raise ParaWriteError("SOLIDWORKS Parasolid triangle layout is incomplete")

    # this callback exists because local behavior needs one focused transformation
    OrderData = sorted(
        enumerate(Records),
        key=lambda ItemData: Ranks.get(ItemData[1][0], len(Ranks) + ItemData[0]),
    )
    return b"".join((Record for Ignored, (Ignored, Record) in OrderData))


# triangle record splitting validates framing while retaining every original byte
def SplitTriRecords(DataValue: bytes) -> list[tuple[tuple[int, int], bytes]]:
    Records: list[tuple[tuple[int, int], bytes]] = []
    OffsetData = 0
    while OffsetData < len(DataValue):
        if OffsetData + 4 > len(DataValue) or DataValue[OffsetData] != 0:
            raise ParaWriteError("SOLIDWORKS Parasolid record framing is invalid")
        KindValueData = DataValue[OffsetData + 1]
        SizeValue, IndexOffset = TriRecordSize(DataValue, OffsetData, KindValueData)
        EndValue = OffsetData + SizeValue
        if EndValue > len(DataValue):
            raise ParaWriteError("SOLIDWORKS Parasolid record is truncated")
        EncodedIndex = Struct.unpack_from(">h", DataValue, IndexOffset)[0]
        if EncodedIndex <= 0:
            raise ParaWriteError("SOLIDWORKS Parasolid record index is invalid")
        Records.append(
            ((KindValueData, EncodedIndex - 1), DataValue[OffsetData:EndValue])
        )
        OffsetData = EndValue
    return Records


# triangle record sizing centralizes fixed analytic and counted framing rules
def TriRecordSize(
    DataValue: bytes, OffsetData: int, KindValueData: int
) -> tuple[int, int]:
    FixedSizes = {
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
    GeomValues = {30: 6, 31: 10, 32: 11, 50: 9, 51: 10, 52: 12, 53: 10, 54: 11}

    # this callback exists because local behavior needs one focused transformation
    VarSizes = {
        74: lambda Count: 14 + 2 * Count,
        79: lambda Count: 8 + Count,
        80: lambda Count: 38 + Count,
        81: lambda Count: 24 + 2 * Count,
        82: lambda Count: 8 + 4 * Count,
        83: lambda Count: 8 + 8 * Count,
    }
    if KindValueData in FixedSizes:
        return FixedSizes[KindValueData], OffsetData + 2
    if KindValueData in GeomValues:
        return 19 + 8 * GeomValues[KindValueData], OffsetData + 2
    if KindValueData not in VarSizes:
        raise ParaWriteError(
            f"SOLIDWORKS Parasolid record kind {KindValueData} is unsupported"
        )
    if OffsetData + 8 > len(DataValue):
        raise ParaWriteError("SOLIDWORKS Parasolid record is truncated")
    Count = Struct.unpack_from(">I", DataValue, OffsetData + 2)[0]
    return VarSizes[KindValueData](Count), OffsetData + 6


# this declaration exists because focused behavior needs one stable owner
def VTwelveVarNode(
    Output: bytearray, KindValueData: int, Index: int, Count: int
) -> None:
    WriteTagMut(Output, KindValueData)
    WriteSignedMut(Output, Count)
    WritePointerMut(Output, Index)


# this declaration exists because focused behavior needs one stable owner
def VTwelveAttr(
    Output: bytearray,
    Index: int,
    NodeId: int,
    DefValue: int,
    Owner: int,
    NextIndex: int,
    PreviousIndex: int,
    NextOfType: int,
    PreviousOfType: int,
    Fields: Sequence[int],
) -> None:
    VTwelveVarNode(Output, 81, Index, len(Fields))
    WriteSignedMut(Output, NodeId)
    for ValueData in (
        DefValue,
        Owner,
        NextIndex,
        PreviousIndex,
        NextOfType,
        PreviousOfType,
        *Fields,
    ):
        WritePointerMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def WriteAttrDefMut(
    Output: bytearray,
    Index: int,
    NextIndex: int,
    IdValue: int,
    TypeId: int,
    Actions: Sequence[int],
    LegalOwners: Sequence[int],
    Fields: Sequence[int],
) -> None:
    VTwelveVarNode(Output, 80, Index, len(Fields))
    WritePointerMut(Output, NextIndex)
    WritePointerMut(Output, IdValue)
    WriteSignedMut(Output, TypeId)
    Output.extend(bytes(Actions))
    Output.extend(bytes(LegalOwners))
    Output.extend(bytes(Fields))


# this declaration exists because focused behavior needs one stable owner
def WriteAttrIdMut(Output: bytearray, Index: int, ValueData: str) -> None:
    Encoded = ValueData.encode("ascii")
    VTwelveVarNode(Output, 79, Index, len(Encoded))
    Output.extend(Encoded)


# this declaration exists because focused behavior needs one stable owner
def VTwelvePtrList(
    Output: bytearray, Index: int, Entries: Sequence[int], UsedValue: int
) -> None:
    VTwelveVarNode(Output, 74, Index, len(Entries))
    WriteSignedMut(Output, UsedValue)
    WritePointerMut(Output, 0)
    for ValueData in Entries:
        WritePointerMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def VTwelveIntVals(Output: bytearray, Index: int, Values: Sequence[int]) -> None:
    VTwelveVarNode(Output, 82, Index, len(Values))
    for ValueData in Values:
        WriteSignedMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def VTwelveRealVals(Output: bytearray, Index: int, Values: Sequence[float]) -> None:
    VTwelveVarNode(Output, 83, Index, len(Values))
    for ValueData in Values:
        WriteFloatMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def Allocate(Values: Iterable[object], NextAttr: int) -> tuple[dict[str, int], int]:
    Result: dict[str, int] = {}
    for ValueData in Values:
        ItemId = getattr(ValueData, "id")
        Result[ItemId] = CheckedAttr(NextAttr)
        NextAttr += 1
    return (Result, NextAttr)


# this declaration exists because focused behavior needs one stable owner
def CheckedAttr(ValueData: int) -> int:
    if not 0 < ValueData <= 65535:
        raise ParaWriteError("Parasolid B-rep attribute space is exhausted")
    return ValueData


# this declaration exists because focused behavior needs one stable owner
def WriteBodyTree(
    Model: BrepModel,
    Topology: BrepTopology,
    FaceOwners: Mapping[str, int],
    SheetSchema: bool,
    NextAttr: int,
    Output: bytearray,
) -> int:
    Assigned: set[str] = set()
    for BodyData in Model.bodies:
        NextAttr = WriteOneBodyMut(
            BodyData, Topology, FaceOwners, SheetSchema, NextAttr, Output, Assigned
        )
    if Assigned != set(Topology.faces):
        raise ParaWriteError("B-rep contains a face outside every body")
    return NextAttr


# body hierarchy writing owns each root and its ordered native regions
def WriteOneBodyMut(
    BodyData: BrepBody,
    Topology: BrepTopology,
    FaceOwners: Mapping[str, int],
    SheetSchema: bool,
    NextAttr: int,
    Output: bytearray,
    Assigned: set[str],
) -> int:
    RootValue = CheckedAttr(NextAttr)
    NextAttr += 1
    RegionKinds = {Topology.regions[RegionId].solid for RegionId in BodyData.region_ids}
    if len(RegionKinds) != 1:
        raise ParaWriteError(f"B-rep body {BodyData.id} mixes solid and sheet regions")
    Solid = RegionKinds == {True}
    NativeRegions: list[int] = []
    for RegionId in BodyData.region_ids:
        NativeRegion, NextAttr = WriteRegionMut(
            Topology.regions[RegionId],
            Topology,
            FaceOwners,
            SheetSchema,
            Solid,
            NextAttr,
            Output,
            Assigned,
        )
        NativeRegions.append(NativeRegion)
    if len(NativeRegions) > 5:
        raise ParaWriteError(f"B-rep body {BodyData.id} has more than five regions")
    RootRefs = [0, *NativeRegions]
    RootRefs.extend((0 for Ignored in range(6 - len(RootRefs))))
    EntityFiftyOne(Output, 2, RootValue, 23, tuple(RootRefs))
    return NextAttr


# region hierarchy writing connects one region to its shell records
def WriteRegionMut(
    Region: BrepRegion,
    Topology: BrepTopology,
    FaceOwners: Mapping[str, int],
    SheetSchema: bool,
    Solid: bool,
    NextAttr: int,
    Output: bytearray,
    Assigned: set[str],
) -> tuple[int, int]:
    if not Solid and len(Region.shell_use_ids) != 1:
        raise ParaWriteError(f"B-rep sheet region {Region.id} must contain one shell")
    NativeRegion = CheckedAttr(NextAttr)
    NextAttr += 1
    NativeLumps: list[int] = []
    for ShellUseId in Region.shell_use_ids:
        NextAttr, LumpValue = WriteShellMut(
            ShellUseId,
            NativeRegion,
            Topology,
            FaceOwners,
            SheetSchema,
            Solid,
            NextAttr,
            Output,
            Assigned,
        )
        if LumpValue is not None:
            NativeLumps.append(LumpValue)
    if Solid:
        EntityFiftyOne(
            Output,
            1,
            NativeRegion,
            27,
            FixedRefs(
                NativeLumps, "Parasolid writer regions support at most six shells"
            ),
        )
    return NativeRegion, NextAttr


# shell hierarchy writing validates face ownership and emits native shell links
def WriteShellMut(
    ShellUseId: str,
    NativeRegion: int,
    Topology: BrepTopology,
    FaceOwners: Mapping[str, int],
    SheetSchema: bool,
    Solid: bool,
    NextAttr: int,
    Output: bytearray,
    Assigned: set[str],
) -> tuple[int, int | None]:
    ShellUse = Topology.shell_uses[ShellUseId]
    ShellData = Topology.shells[ShellUse.shell_id]
    Owned: list[int] = []
    for FaceUseId in ShellData.face_use_ids:
        FaceId = Topology.face_uses[FaceUseId].face_id
        if FaceId in Assigned:
            raise ParaWriteError(f"B-rep face {FaceId} belongs to multiple bodies")
        Assigned.add(FaceId)
        Owned.append(FaceOwners[FaceId])
    HeadValue, NextAttr = WriteFaceList(
        Output, Owned, NextAttr, 21 if SheetSchema else 19
    )
    if not Solid:
        EntityFiftyOne(Output, 1, NativeRegion, 29, (HeadValue, 0, 0, 0, 0, 0))
        return NextAttr, None
    LumpValue = CheckedAttr(NextAttr)
    ShellNode, ShellLink = CheckedAttr(NextAttr + 1), CheckedAttr(NextAttr + 2)
    EntityFiftyOne(Output, 2, LumpValue, 31, (ShellNode, 0, 0, 0, 0, 0))
    EntityFiftyOne(Output, 2, ShellNode, 33, (ShellLink, 0, 0, 0, 0, 0))
    EntityFiftyOne(Output, 2, ShellLink, 35, (HeadValue, 0, 0, 0, 0, 0))
    return NextAttr + 3, LumpValue


# this declaration exists because focused behavior needs one stable owner
def WriteFaceList(
    Output: bytearray, Owners: Sequence[int], NextAttr: int, KindValue: int
) -> tuple[int, int]:
    Chunks = tuple(
        (tuple(Owners[Index : Index + 5]) for Index in range(0, len(Owners), 5))
    ) or ((),)
    Attrs = tuple((CheckedAttr(NextAttr + Index) for Index in range(len(Chunks))))
    NextAttr += len(Attrs)
    for Index, AttrValue in enumerate(Attrs):
        RefsValueData = [Attrs[Index + 1] if Index + 1 < len(Attrs) else 0]
        RefsValueData.extend(Chunks[Index])
        RefsValueData.extend((0 for Ignored in range(6 - len(RefsValueData))))
        EntityFiftyOne(Output, 2, AttrValue, KindValue, tuple(RefsValueData))
    return (Attrs[0], NextAttr)


# this declaration exists because focused behavior needs one stable owner
def FixedRefs(Values: Sequence[int], Message: str) -> tuple[int, ...]:
    if len(Values) > 6:
        raise ParaWriteError(Message)
    return tuple((*Values, *(0 for Ignored in range(6 - len(Values)))))


# this declaration exists because focused behavior needs one stable owner
def SurfValues(SurfValue: object) -> tuple[int, tuple[float, ...]]:
    if isinstance(SurfValue, PlaneSurface):
        Normal, RefValue = Frame(
            SurfValue.normal,
            SurfValue.reference_direction,
            f"plane surface {SurfValue.id}",
        )
        return (
            50,
            (
                *ScaledVector(SurfValue.origin),
                *VectorValues(Normal),
                *VectorValues(RefValue),
            ),
        )
    if isinstance(SurfValue, CylinderSurface):
        AxisValue, RefValue = Frame(
            SurfValue.axis,
            SurfValue.reference_direction,
            f"cylinder surface {SurfValue.id}",
        )
        return (
            51,
            (
                *ScaledVector(SurfValue.origin),
                *VectorValues(AxisValue),
                SurfValue.radius * KLengthScale,
                *VectorValues(RefValue),
            ),
        )
    if isinstance(SurfValue, ConeSurface):
        if not 0.0 < SurfValue.half_angle < MathValue.pi / 2.0:
            raise ParaWriteError(
                f"Parasolid cone surface {SurfValue.id} requires a positive acute angle"
            )
        AxisValue, RefValue = Frame(
            SurfValue.axis,
            SurfValue.reference_direction,
            f"cone surface {SurfValue.id}",
        )
        return (
            52,
            (
                *ScaledVector(SurfValue.origin),
                *VectorValues(AxisValue),
                SurfValue.radius * KLengthScale,
                MathValue.sin(SurfValue.half_angle),
                MathValue.cos(SurfValue.half_angle),
                *VectorValues(RefValue),
            ),
        )
    if isinstance(SurfValue, SphereSurface):
        AxisValue, RefValue = Frame(
            SurfValue.axis,
            SurfValue.reference_direction,
            f"sphere surface {SurfValue.id}",
        )
        return (
            53,
            (
                *ScaledVector(SurfValue.center),
                SurfValue.radius * KLengthScale,
                *VectorValues(AxisValue),
                *VectorValues(RefValue),
            ),
        )
    if isinstance(SurfValue, TorusSurface):
        if not SurfValue.major_radius > SurfValue.minor_radius > 0.0:
            raise ParaWriteError(
                f"Parasolid torus surface {SurfValue.id} requires major radius greater than minor radius"
            )
        AxisValue, RefValue = Frame(
            SurfValue.axis,
            SurfValue.reference_direction,
            f"torus surface {SurfValue.id}",
        )
        return (
            54,
            (
                *ScaledVector(SurfValue.center),
                *VectorValues(AxisValue),
                SurfValue.major_radius * KLengthScale,
                SurfValue.minor_radius * KLengthScale,
                *VectorValues(RefValue),
            ),
        )
    if isinstance(SurfValue, OffsetSurface):
        raise ParaWriteError(
            f"Parasolid B-rep writing does not support offset surface {SurfValue.id}"
        )
    if isinstance(SurfValue, NativeSurface):
        raise ParaWriteError(
            f"Parasolid B-rep writing cannot regenerate native surface {SurfValue.id}"
        )
    raise ParaWriteError("Parasolid B-rep contains an unsupported surface")


# this declaration exists because focused behavior needs one stable owner
def CurveValues(Curve: object) -> tuple[int, tuple[float, ...]]:
    if isinstance(Curve, LineCurve):
        DirectData = UnitVector(Curve.direction, f"line curve {Curve.id}")
        return (30, (*ScaledVector(Curve.origin), *VectorValues(DirectData)))
    if isinstance(Curve, CircleCurve):
        AxisValue, RefValue = Frame(
            Curve.axis, Curve.reference_direction, f"circle curve {Curve.id}"
        )
        return (
            31,
            (
                *ScaledVector(Curve.center),
                *VectorValues(AxisValue),
                *VectorValues(RefValue),
                Curve.radius * KLengthScale,
            ),
        )
    if isinstance(Curve, EllipseCurve):
        AxisValue, RefValue = Frame(
            Curve.axis, Curve.reference_direction, f"ellipse curve {Curve.id}"
        )
        return (
            32,
            (
                *ScaledVector(Curve.center),
                *VectorValues(AxisValue),
                *VectorValues(RefValue),
                Curve.major_radius * KLengthScale,
                Curve.minor_radius * KLengthScale,
            ),
        )
    if isinstance(Curve, NativeCurve):
        raise ParaWriteError(
            f"Parasolid B-rep writing cannot regenerate native curve {Curve.id}"
        )
    raise ParaWriteError("Parasolid B-rep contains an unsupported curve")


# this declaration exists because focused behavior needs one stable owner
def WriteNurbsMut(
    Output: bytearray, Wrapper: int, Curve: NurbsCurve, NextAttr: int
) -> int:
    CheckNurbsCurve(Curve)
    Descriptor = CheckedAttr(NextAttr)
    Control = CheckedAttr(NextAttr + 1)
    Multiplicity = CheckedAttr(NextAttr + 2)
    Knots = CheckedAttr(NextAttr + 3)
    NextAttr += 4
    WriteTagMut(Output, 134)
    WriteShortMut(Output, Wrapper)
    WriteShortMut(Output, Descriptor)
    Output.extend(bytes(8))
    WriteTagMut(Output, 136)
    WriteShortMut(Output, Descriptor)
    WriteShortMut(Output, Curve.degree)
    WriteBigIntMut(Output, len(Curve.control_points))
    WriteShortMut(Output, 4 if Curve.weights else 3)
    WriteBigIntMut(Output, 2)
    Output.append(0)
    Output.extend((0, 0, 1 if Curve.weights else 0, 0))
    for AttrValue in (Control, Multiplicity, Knots):
        WriteShortMut(Output, AttrValue)
    Poles = HomogPoints(Curve.control_points, Curve.weights)
    WriteFloatsMut(Output, 45, Control, Poles)
    WriteShortsMut(Output, Multiplicity, Curve.multiplicities)
    WriteFloatsMut(Output, 128, Knots, Curve.knots)
    return NextAttr


# curve validation isolates limits shared by the parasolid nurbs record writer
def CheckNurbsCurve(Curve: NurbsCurve) -> None:
    if Curve.periodic:
        raise ParaWriteError(
            f"Parasolid B-rep writing does not support periodic NURBS curve {Curve.id}"
        )
    if not 1 <= Curve.degree <= 65535:
        raise ParaWriteError(
            f"Parasolid NURBS curve {Curve.id} has an unsupported degree"
        )
    if len(Curve.control_points) > 4294967295:
        raise ParaWriteError(
            f"Parasolid NURBS curve {Curve.id} has too many control points"
        )


# this declaration exists because focused behavior needs one stable owner
def WriteNurbsSMut(
    Output: bytearray, Wrapper: int, SurfValue: NurbsSurface, NextAttr: int
) -> int:
    Poles = NurbsSurfPoles(SurfValue)
    Descriptor = CheckedAttr(NextAttr)
    Control = CheckedAttr(NextAttr + 1)
    UMultiplicity = CheckedAttr(NextAttr + 2)
    VMultiplicity = CheckedAttr(NextAttr + 3)
    UKnots = CheckedAttr(NextAttr + 4)
    VKnots = CheckedAttr(NextAttr + 5)
    NextAttr += 6
    WriteTagMut(Output, 124)
    WriteShortMut(Output, Wrapper)
    WriteBigIntMut(Output, 1)
    Output.extend(bytes(10))
    Output.append(43)
    WriteShortMut(Output, Descriptor)
    WriteShortMut(Output, 0)
    WriteTagMut(Output, 126)
    WriteShortMut(Output, Descriptor)
    Output.extend(bytes(12))
    for AttrValue in (Control, UMultiplicity, VMultiplicity, UKnots, VKnots):
        WriteShortMut(Output, AttrValue)
    WriteFloatsMut(Output, 45, Control, Poles)
    WriteShortsMut(Output, UMultiplicity, SurfValue.multiplicities_u)
    WriteShortsMut(Output, VMultiplicity, SurfValue.multiplicities_v)
    WriteFloatsMut(Output, 128, UKnots, SurfValue.knots_u)
    WriteFloatsMut(Output, 128, VKnots, SurfValue.knots_v)
    return NextAttr


# surface pole preparation validates shape before the binary writer allocates records
def NurbsSurfPoles(SurfValue: NurbsSurface) -> tuple[float, ...]:
    if SurfValue.periodic_u or SurfValue.periodic_v:
        raise ParaWriteError(
            f"Parasolid B-rep writing does not support periodic NURBS surface {SurfValue.id}"
        )
    if not 1 <= SurfValue.degree_u <= 8 or not 1 <= SurfValue.degree_v <= 8:
        raise ParaWriteError(
            f"Parasolid NURBS surface {SurfValue.id} requires degrees from one through eight"
        )
    UCount = len(SurfValue.control_points)
    VCount = len(SurfValue.control_points[0])
    Points = tuple(
        (Point for RowValue in SurfValue.control_points for Point in RowValue)
    )
    Weights = tuple(
        (ValueData for RowValue in SurfValue.weights for ValueData in RowValue)
    )
    Poles = HomogPoints(Points, Weights)
    Intended = (
        UCount,
        VCount,
        SurfValue.degree_u,
        SurfValue.degree_v,
        4 if Weights else 3,
    )
    Inferred = InferSurfShape(
        len(Poles), SurfValue.multiplicities_u, SurfValue.multiplicities_v
    )
    if Inferred != Intended:
        raise ParaWriteError(
            f"Parasolid writer cannot infer NURBS surface {SurfValue.id} shape {Intended}"
        )
    return Poles


# this declaration exists because focused behavior needs one stable owner
def HomogPoints(
    Points: Sequence[VectorThree], Weights: Sequence[float]
) -> tuple[float, ...]:
    if Weights and len(Weights) != len(Points):
        raise ParaWriteError("B-rep NURBS weights do not match control points")
    Result: list[float] = []
    for Index, Point in enumerate(Points):
        Weight = Weights[Index] if Weights else 1.0
        Result.extend(
            (
                Point.x * KLengthScale * Weight,
                Point.y * KLengthScale * Weight,
                Point.z * KLengthScale * Weight,
            )
        )
        if Weights:
            Result.append(Weight)
    return tuple(Result)


# this declaration exists because focused behavior needs one stable owner
def InferSurfShape(
    ControlLength: int, UMultiplicities: Sequence[int], VMultiplicities: Sequence[int]
) -> tuple[int, int, int, int, int] | None:
    USumValue = sum(UMultiplicities)
    VSumValue = sum(VMultiplicities)
    for Dimension in (4, 3):
        if ControlLength % Dimension:
            continue
        PoleCount = ControlLength // Dimension
        for UDegree in range(1, 9):
            UCount = USumValue - UDegree - 1
            if UCount <= 0:
                continue
            for VDegree in range(1, 9):
                VCount = VSumValue - VDegree - 1
                if VCount > 0 and UCount * VCount == PoleCount:
                    return (UCount, VCount, UDegree, VDegree, Dimension)
    return None


# this declaration exists because focused behavior needs one stable owner
def WriteFloatsMut(
    Output: bytearray, KindValueData: int, AttrValue: int, Values: Sequence[float]
) -> None:
    if len(Values) > 4294967295:
        raise ParaWriteError("Parasolid B-rep array is too large")
    WriteTagMut(Output, KindValueData)
    Output.append(43)
    WriteBigIntMut(Output, len(Values))
    WriteShortMut(Output, AttrValue)
    for ValueData in Values:
        WriteFloatMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def WriteShortsMut(Output: bytearray, AttrValue: int, Values: Sequence[int]) -> None:
    if len(Values) > 4294967295 or any(
        (
            type(ValueData) is not int or not 0 < ValueData <= 65535
            for ValueData in Values
        )
    ):
        raise ParaWriteError("Parasolid B-rep multiplicity array is invalid")
    WriteTagMut(Output, 127)
    Output.append(43)
    WriteBigIntMut(Output, len(Values))
    WriteShortMut(Output, AttrValue)
    for ValueData in Values:
        WriteShortMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def WriteCompactMut(
    Output: bytearray, KindValueData: int, AttrValue: int, Values: Sequence[float]
) -> None:
    WriteTagMut(Output, KindValueData)
    WriteShortMut(Output, AttrValue)
    WriteBigIntMut(Output, 0)
    Output.extend(bytes(10))
    Output.append(43)
    for ValueData in Values:
        WriteFloatMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def EntityFiftyOne(
    Output: bytearray,
    Flags: int,
    AttrValue: int,
    KindValue: int,
    RefsValueData: Sequence[int],
) -> None:
    if len(RefsValueData) != 6:
        raise ParaWriteError("Parasolid entity references must contain six values")
    WriteTagMut(Output, 81)
    WriteBigIntMut(Output, Flags)
    WriteShortMut(Output, AttrValue)
    WriteBigIntMut(Output, 1)
    WriteShortMut(Output, KindValue)
    for RefValue in RefsValueData:
        WriteShortMut(Output, RefValue)


# this declaration exists because focused behavior needs one stable owner
def UnitVector(ValueData: VectorThree, Label: str) -> VectorThree:
    Length = MathValue.sqrt(
        ValueData.x * ValueData.x
        + ValueData.y * ValueData.y
        + ValueData.z * ValueData.z
    )
    if not MathValue.isfinite(Length) or Length <= 0.0:
        raise ParaWriteError(f"Parasolid {Label} has an invalid direction")
    return VectorThree(ValueData.x / Length, ValueData.y / Length, ValueData.z / Length)


# this declaration exists because focused behavior needs one stable owner
def Frame(
    AxisValue: VectorThree, RefValue: VectorThree, Label: str
) -> tuple[VectorThree, VectorThree]:
    NormalizedAxis = UnitVector(AxisValue, Label)
    NormalizedRef = UnitVector(RefValue, Label)
    DotProductData = (
        NormalizedAxis.x * NormalizedRef.x
        + NormalizedAxis.y * NormalizedRef.y
        + NormalizedAxis.z * NormalizedRef.z
    )
    if abs(DotProductData) > 1e-09:
        raise ParaWriteError(
            f"Parasolid {Label} axis and reference direction are not orthogonal"
        )
    return (NormalizedAxis, NormalizedRef)


# this declaration exists because focused behavior needs one stable owner
def VectorValues(ValueData: VectorThree) -> tuple[float, float, float]:
    return (ValueData.x, ValueData.y, ValueData.z)


# this declaration exists because focused behavior needs one stable owner
def ScaledVector(ValueData: VectorThree) -> tuple[float, float, float]:
    return (
        ValueData.x * KLengthScale,
        ValueData.y * KLengthScale,
        ValueData.z * KLengthScale,
    )


# this declaration exists because focused behavior needs one stable owner
def Vector(Output: bytearray, ValueData: VectorThree, Scale: float) -> None:
    for Component in (ValueData.x, ValueData.y, ValueData.z):
        WriteFloatMut(Output, Component * Scale)


# this declaration exists because focused behavior needs one stable owner
def ParaStream(
    BodyData: bytes,
    Schema: str,
    DescValue: bytes = b"partition body",
    UserFieldSize: int | None = None,
) -> bytes:
    EncodedSchema = Schema.encode("ascii")
    if len(EncodedSchema) > 255:
        raise ParaWriteError("Parasolid schema name is too long")
    Output = bytearray(b"PS\x00\x00")
    WriteShortMut(Output, len(DescValue))
    Output.extend(DescValue)
    WriteBigIntMut(Output, len(EncodedSchema))
    Output.extend(EncodedSchema)
    if UserFieldSize is not None:
        WriteBigIntMut(Output, UserFieldSize)
    Output.extend(BodyData)
    return bytes(Output)


# this declaration exists because focused behavior needs one stable owner
def VTwelveNode(Output: bytearray, KindValueData: int, Index: int) -> None:
    WriteTagMut(Output, KindValueData)
    WritePointerMut(Output, Index)


# this declaration exists because focused behavior needs one stable owner
def WritePointerMut(Output: bytearray, Index: int) -> None:
    if Index < 0:
        raise ParaWriteError("Parasolid pointer index is negative")
    if Index < 32767:
        Output.extend(Struct.pack(">h", Index + 1))
        return
    Output.extend(Struct.pack(">hH", -(Index % 32767 + 1), Index // 32767))


# this declaration exists because focused behavior needs one stable owner
def WriteSignedMut(Output: bytearray, ValueData: int) -> None:
    if not -(1 << 31) <= ValueData < 1 << 31:
        raise ParaWriteError("Parasolid i32 field is out of range")
    Output.extend(Struct.pack(">i", ValueData))


# this declaration exists because focused behavior needs one stable owner
def WriteGeomMut(
    Output: bytearray,
    KindValueData: int,
    Index: int,
    NodeId: int,
    Owner: int,
    NextIndex: int,
    PreviousIndex: int,
    Values: Sequence[float],
) -> None:
    VTwelveNode(Output, KindValueData, Index)
    WriteSignedMut(Output, NodeId)
    WritePointerMut(Output, 0)
    WritePointerMut(Output, Owner)
    WritePointerMut(Output, NextIndex)
    WritePointerMut(Output, PreviousIndex)
    WritePointerMut(Output, 0)
    Output.extend(b"+")
    for ValueData in Values:
        WriteFloatMut(Output, ValueData)


# this declaration exists because focused behavior needs one stable owner
def WriteFinMut(
    Output: bytearray,
    Index: int,
    Attrs: int,
    LoopDataData: int,
    Forward: int,
    Backward: int,
    Vertex: int,
    Other: int,
    EdgeData: int,
    Curve: int,
    NextAtVertex: int,
    Positive: bool,
) -> None:
    VTwelveNode(Output, 17, Index)
    for ValueData in (
        Attrs,
        LoopDataData,
        Forward,
        Backward,
        Vertex,
        Other,
        EdgeData,
        Curve,
        NextAtVertex,
    ):
        WritePointerMut(Output, ValueData)
    Output.extend(b"+" if Positive else b"-")


# this declaration exists because focused behavior needs one stable owner
def NextFinAtVertex(Index: int, VertexFins: Mapping[str, Sequence[int]]) -> int:
    for Values in VertexFins.values():
        if Index not in Values:
            continue
        Position = Values.index(Index)
        return Values[Position + 1] if Position + 1 < len(Values) else 0
    raise ParaWriteError("Parasolid fin has no vertex chain")


# this declaration exists because focused behavior needs one stable owner
def WriteTagMut(Output: bytearray, KindValueData: int) -> None:
    Output.extend((0, KindValueData))


# this declaration exists because focused behavior needs one stable owner
def WriteShortMut(Output: bytearray, ValueData: int) -> None:
    if not 0 <= ValueData <= 65535:
        raise ParaWriteError("Parasolid u16 field is out of range")
    Output.extend(Struct.pack(">H", ValueData))


# this declaration exists because focused behavior needs one stable owner
def WriteBigIntMut(Output: bytearray, ValueData: int) -> None:
    if not 0 <= ValueData <= 4294967295:
        raise ParaWriteError("Parasolid u32 field is out of range")
    Output.extend(Struct.pack(">I", ValueData))


# this declaration exists because focused behavior needs one stable owner
def WriteFloatMut(Output: bytearray, ValueData: float) -> None:
    if not MathValue.isfinite(ValueData):
        raise ParaWriteError("Parasolid B-rep contains a non-finite value")
    Output.extend(Struct.pack(">d", ValueData))


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ParaPayload:
    locals().setdefault("__annotations__", {}).__setitem__("stream", str)
    locals().setdefault("__annotations__", {}).__setitem__("kind", str)
    locals().setdefault("__annotations__", {}).__setitem__("schema", str)
    locals().setdefault("__annotations__", {}).__setitem__("description", str)
    locals().setdefault("__annotations__", {}).__setitem__("data", bytes)
    locals().setdefault("__annotations__", {}).__setitem__("sha256", str)
    locals().setdefault("__annotations__", {}).__setitem__("wrapper_offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("magic_offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("compressed_offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("compressed_size", int)
    locals().setdefault("__annotations__", {}).__setitem__("uncompressed_size", int)


# this declaration exists because focused behavior needs one stable owner
def DecodePartData(DataValue: bytes, Stream: str = "") -> tuple[ParaPayload, ...]:
    Results: list[ParaPayload] = []
    Cursor = 0
    while True:
        MagicOffset = DataValue.find(KWrapperMagic, Cursor)
        if MagicOffset < 0:
            break
        Cursor = MagicOffset + 1
        HeaderOffset = MagicOffset + len(KWrapperMagic)
        if HeaderOffset + 8 > len(DataValue):
            continue
        RawSize, ZipSize = Struct.unpack_from("<II", DataValue, HeaderOffset)
        ZipOffset = HeaderOffset + 8
        ZipEnd = ZipOffset + ZipSize
        if ZipEnd > len(DataValue):
            continue
        try:
            PayloadData = ZlibLib.decompress(DataValue[ZipOffset:ZipEnd])
        except ZlibLib.error:
            continue
        if len(PayloadData) != RawSize or not PayloadData.startswith(b"PS\x00\x00"):
            continue
        Results.append(
            Payload(
                Stream,
                PayloadData,
                MagicOffset - 4 if MagicOffset >= 4 else MagicOffset,
                MagicOffset,
                ZipOffset,
                ZipSize,
                RawSize,
            )
        )
        Cursor = ZipEnd
    if not Results and DataValue.startswith(b"PS\x00\x00"):
        Results.append(
            Payload(Stream, DataValue, 0, 0, 0, len(DataValue), len(DataValue))
        )
    if not Results:
        raise ParaFormatError(f"no Parasolid payload found in {Stream or 'stream'}")
    return tuple(Results)


# this declaration exists because focused behavior needs one stable owner
def Payload(
    Stream: str,
    DataValue: bytes,
    WrapperOffset: int,
    MagicOffset: int,
    ZipOffset: int,
    ZipSize: int,
    RawSize: int,
) -> ParaPayload:
    Header = DataValue[:8192]
    KindMatch = RegexLib.search(b"TRANSMIT FILE \\(([^)]+)\\)", Header)
    SchemaMatch = RegexLib.search(b"SCH_[0-9A-Z_]+", Header)
    DescMatch = RegexLib.search(b": ([\\x20-\\x7e]{1,512})", Header)
    return ParaPayload(
        stream=Stream,
        kind=KindMatch.group(1).decode("ascii", "replace") if KindMatch else "unknown",
        schema=SchemaMatch.group(0).decode("ascii") if SchemaMatch else "unknown",
        description=(
            DescMatch.group(1).decode("ascii", "replace").strip() if DescMatch else ""
        ),
        data=DataValue,
        sha256=Hashlib.sha256(DataValue).hexdigest(),
        wrapper_offset=WrapperOffset,
        magic_offset=MagicOffset,
        compressed_offset=ZipOffset,
        compressed_size=ZipSize,
        uncompressed_size=RawSize,
    )


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ParaHeader:
    locals().setdefault("__annotations__", {}).__setitem__("description", str)
    locals().setdefault("__annotations__", {}).__setitem__("schema", str)
    locals().setdefault("__annotations__", {}).__setitem__("body_offset", int)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class TopologyRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("reversed", bool)
    locals().__setitem__("reversed", False)
    locals().setdefault("__annotations__", {}).__setitem__("owner", int)
    locals().__setitem__("owner", 0)
    locals().setdefault("__annotations__", {}).__setitem__("point", VectorThree | None)
    locals().__setitem__("point", None)
    locals().setdefault("__annotations__", {}).__setitem__("isolated", bool)
    locals().__setitem__("isolated", False)
    locals().setdefault("__annotations__", {}).__setitem__("tolerance", float)
    locals().__setitem__("tolerance", 0.0)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class EntityRecord:
    locals().setdefault("__annotations__", {}).__setitem__("flags", int)
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("discriminator", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class IntersectRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "header_references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("sense", bool)
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ChartRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("base_parameter", float)
    locals().setdefault("__annotations__", {}).__setitem__("base_scale", float)
    locals().setdefault("__annotations__", {}).__setitem__("chordal_error", float)
    locals().setdefault("__annotations__", {}).__setitem__("angular_error", float)
    locals().setdefault("__annotations__", {}).__setitem__(
        "parameter_errors", tuple[float, float]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "points", tuple[VectorThree, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "parameters", tuple[float, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "tangents", tuple[VectorThree, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "support_uv", tuple[tuple[tuple[float, float], ...], ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("layout", str)
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class TermRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("count", int)
    locals().setdefault("__annotations__", {}).__setitem__("form", str)
    locals().setdefault("__annotations__", {}).__setitem__("point", VectorThree)
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class SupportUvRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("marker", int)
    locals().setdefault("__annotations__", {}).__setitem__("values", tuple[float, ...])
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CompactUvRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("marker", int)
    locals().setdefault("__annotations__", {}).__setitem__("values", tuple[float, ...])
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class BSurfaceRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("state", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "header_references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("descriptor_reference", int)
    locals().setdefault("__annotations__", {}).__setitem__("data_reference", int)
    locals().setdefault("__annotations__", {}).__setitem__("sense", bool)
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NurbsSurfRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "periodic", tuple[bool, bool]
    )
    locals().setdefault("__annotations__", {}).__setitem__("degrees", tuple[int, int])
    locals().setdefault("__annotations__", {}).__setitem__("counts", tuple[int, int])
    locals().setdefault("__annotations__", {}).__setitem__(
        "knot_types", tuple[int, int]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "knot_counts", tuple[int, int]
    )
    locals().setdefault("__annotations__", {}).__setitem__("rational", bool)
    locals().setdefault("__annotations__", {}).__setitem__("closed", tuple[bool, bool])
    locals().setdefault("__annotations__", {}).__setitem__("surface_form", int)
    locals().setdefault("__annotations__", {}).__setitem__("vertex_dimension", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("layout", str)
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class SurfaceRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "intervals", tuple[tuple[float, float], ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("self_intersection", int)
    locals().setdefault("__annotations__", {}).__setitem__("flags", bytes)
    locals().setdefault("__annotations__", {}).__setitem__(
        "references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class BCurveRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("state", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "header_references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("descriptor_reference", int)
    locals().setdefault("__annotations__", {}).__setitem__("data_reference", int)
    locals().setdefault("__annotations__", {}).__setitem__("sense", bool)
    locals().setdefault("__annotations__", {}).__setitem__("layout", str)
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NurbsCurveRec:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("degree", int)
    locals().setdefault("__annotations__", {}).__setitem__("control_count", int)
    locals().setdefault("__annotations__", {}).__setitem__("vertex_dimension", int)
    locals().setdefault("__annotations__", {}).__setitem__("knot_count", int)
    locals().setdefault("__annotations__", {}).__setitem__("knot_type", int)
    locals().setdefault("__annotations__", {}).__setitem__("periodic", bool)
    locals().setdefault("__annotations__", {}).__setitem__("closed", bool)
    locals().setdefault("__annotations__", {}).__setitem__("rational", bool)
    locals().setdefault("__annotations__", {}).__setitem__("curve_form", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CurveRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("self_intersection", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "analytic_form_reference", int
    )
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class TrimCurveRecord:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("state", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "header_references", tuple[int, ...]
    )
    locals().setdefault("__annotations__", {}).__setitem__("basis_reference", int)
    locals().setdefault("__annotations__", {}).__setitem__(
        "points", tuple[VectorThree, VectorThree]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "parameters", tuple[float, float]
    )
    locals().setdefault("__annotations__", {}).__setitem__("sense", bool)
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class FloatArray:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("kind", int)
    locals().setdefault("__annotations__", {}).__setitem__("values", tuple[float, ...])
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ShortArray:
    locals().setdefault("__annotations__", {}).__setitem__("attribute", int)
    locals().setdefault("__annotations__", {}).__setitem__("values", tuple[int, ...])
    locals().setdefault("__annotations__", {}).__setitem__("offset", int)
    locals().setdefault("__annotations__", {}).__setitem__("raw", bytes)


# this declaration exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class RecordTables:
    locals().setdefault("__annotations__", {}).__setitem__(
        "bridges", dict[int, TopologyRecord]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "loops", dict[int, TopologyRecord]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "edge_uses", dict[int, TopologyRecord]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "coedges", dict[int, TopologyRecord]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "vertex_uses", dict[int, TopologyRecord]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "points", dict[int, TopologyRecord]
    )
    locals().setdefault("__annotations__", {}).__setitem__("curves", dict[int, object])
    locals().setdefault("__annotations__", {}).__setitem__(
        "surfaces", dict[int, object]
    )
    locals().setdefault("__annotations__", {}).__setitem__(
        "entities", dict[int, EntityRecord]
    )
    locals().setdefault("__annotations__", {}).__setitem__("v12_partition", bool)
    locals().__setitem__("v12_partition", False)


# this declaration exists because focused behavior needs one stable owner
def DecodeBrepModel(PayloadData: bytes | bytearray) -> BrepModel | None:
    DataValue = bytes(PayloadData)
    Header = ParaHeaderData(DataValue)
    if Header is None:
        return None
    DescValue = Header.description.casefold()
    if "delta" in DescValue or "transmit file" not in DescValue:
        return None
    return DecodePartModel(DataValue, Header)


# this declaration exists because focused behavior needs one stable owner
def ParaHeaderData(DataValue: bytes) -> ParaHeader | None:
    if len(DataValue) < 12 or not DataValue.startswith(b"PS\x00\x00"):
        return None
    DescLength = Struct.unpack_from(">H", DataValue, 4)[0]
    DescStart = 6
    DescEnd = DescStart + DescLength
    if DescEnd + 4 > len(DataValue):
        return None
    SchemaLength = Struct.unpack_from(">I", DataValue, DescEnd)[0]
    SchemaOffset = DescEnd + 4
    SchemaEnd = SchemaOffset + SchemaLength
    if SchemaLength < 4 or SchemaLength > 255 or SchemaEnd > len(DataValue):
        return None
    if DataValue[SchemaOffset : SchemaOffset + 4] != b"SCH_":
        return None
    try:
        DescValue = DataValue[DescStart:DescEnd].decode("ascii")
        Schema = DataValue[SchemaOffset:SchemaEnd].decode("ascii")
    except UnicodeDecodeError:
        return None
    if not Schema.startswith("SCH_"):
        return None
    return ParaHeader(DescValue, Schema, SchemaEnd)


# this declaration exists because focused behavior needs one stable owner
def DecodePartModel(PayloadData: bytes, Header: ParaHeader) -> BrepModel | None:
    BodyData = PayloadData[Header.body_offset :]
    if not BodyData or len(BodyData) > 268435456:
        return None
    Tables = ScanPartRecords(BodyData)
    if Tables is None or not Tables.bridges:
        return None
    UnchangedIds, AttrOrders = SolidFaceData(BodyData)
    try:
        Model = BuildPartModel(Tables, UnchangedIds, AttrOrders)
    except (KeyError, ValueError, OverflowError):
        return None
    if Model.validate():
        return None
    return Model


# this declaration exists because focused behavior needs one stable owner
def SolidUnchIds(BodyData: bytes) -> dict[int, int]:
    return SolidFaceData(BodyData)[0]


# this declaration exists because focused behavior needs one stable owner
def SolidFaceData(BodyData: bytes) -> tuple[dict[int, int], dict[str, dict[int, int]]]:
    Names = {
        "unchanged": b"SWEntUnchanged",
        "downstream": b"DOWNSTREAM_FACE_ID",
        "colour": b"SDL/TYSA_COLOUR",
    }
    IdKinds = ScanFaceIds(BodyData, Names)
    DefKinds = ScanFaceDefs(BodyData, IdKinds)
    if not DefKinds:
        return {}, {}
    ValueRecords = ScanIntValues(BodyData)
    Records = ScanFaceAttrs(BodyData, Names, DefKinds)
    Orders = FaceAttrOrders(Records)
    return FaceUnchanged(Records["unchanged"], ValueRecords), Orders


# face identifier scanning maps vendor names to their encoded identifier records
def ScanFaceIds(BodyData: bytes, Names: Mapping[str, bytes]) -> dict[int, str]:
    IdKinds: dict[int, str] = {}
    Cursor = 0
    while (OffsetData := BodyData.find(b"\x00O", Cursor)) >= 0:
        Cursor = OffsetData + 1
        Count = ReadUnsigned(BodyData, OffsetData + 2)
        Index = ReadShort(BodyData, OffsetData + 6)
        if Count is None or Index is None or OffsetData + 8 + Count > len(BodyData):
            continue
        ValueData = BodyData[OffsetData + 8 : OffsetData + 8 + Count]
        KindValueData = next(
            (NameValue for NameValue, Encoded in Names.items() if ValueData == Encoded),
            None,
        )
        if KindValueData is not None:
            IdKinds[Index] = KindValueData
    return IdKinds


# face definition scanning links schema definitions to recognized identifier kinds
def ScanFaceDefs(BodyData: bytes, IdKinds: Mapping[int, str]) -> dict[int, str]:
    DefKinds: dict[int, str] = {}
    Cursor = 0
    while (OffsetData := BodyData.find(b"\x00P", Cursor)) >= 0:
        Cursor = OffsetData + 1
        Count = ReadUnsigned(BodyData, OffsetData + 2)
        Index = ReadShort(BodyData, OffsetData + 6)
        IdValue = ReadShort(BodyData, OffsetData + 10)
        if (
            Count is None
            or Count > 64
            or OffsetData + 38 + Count > len(BodyData)
            or (Index is None)
            or (IdValue not in IdKinds)
        ):
            continue
        DefKinds[Index] = IdKinds[IdValue]
    return DefKinds


# integer value scanning retains positive unchanged face identifiers only
def ScanIntValues(BodyData: bytes) -> dict[int, int]:
    ValueRecords: dict[int, int] = {}
    Cursor = 0
    while (OffsetData := BodyData.find(b"\x00R", Cursor)) >= 0:
        Cursor = OffsetData + 1
        Count = ReadUnsigned(BodyData, OffsetData + 2)
        Index = ReadShort(BodyData, OffsetData + 6)
        if Count != 1 or Index is None or OffsetData + 12 > len(BodyData):
            continue
        ValueData = Struct.unpack_from(">i", BodyData, OffsetData + 8)[0]
        if ValueData > 0:
            ValueRecords[Index] = ValueData
    return ValueRecords


# face attribute scanning decodes ownership and linked list references
def ScanFaceAttrs(
    BodyData: bytes, Names: Mapping[str, bytes], DefKinds: Mapping[int, str]
) -> dict[str, dict[int, tuple[int, int, int, int]]]:
    Records: dict[str, dict[int, tuple[int, int, int, int]]] = {
        KindValueData: {} for KindValueData in Names
    }
    Cursor = 0
    while (OffsetData := BodyData.find(b"\x00Q", Cursor)) >= 0:
        Cursor = OffsetData + 1
        Count = ReadUnsigned(BodyData, OffsetData + 2)
        Index = ReadShort(BodyData, OffsetData + 6)
        AttrDef = ReadShort(BodyData, OffsetData + 12)
        Owner = ReadShort(BodyData, OffsetData + 14)
        NextOfType = ReadShort(BodyData, OffsetData + 20)
        PreviousOfType = ReadShort(BodyData, OffsetData + 22)
        ValueIndex = ReadShort(BodyData, OffsetData + 24)
        if (
            Count is None
            or Count < 1
            or Count > 64
            or (OffsetData + 24 + Count * 2 > len(BodyData))
            or (Index is None)
            or (AttrDef not in DefKinds)
            or (Owner is None)
            or (NextOfType is None)
            or (PreviousOfType is None)
            or (ValueIndex is None)
        ):
            continue
        KindValueData = DefKinds[AttrDef]
        Records[KindValueData][Index] = (Owner, NextOfType, PreviousOfType, ValueIndex)
    return Records


# face attribute ordering reconstructs each valid nonbranching linked list
def FaceAttrOrders(
    Records: Mapping[str, Mapping[int, tuple[int, int, int, int]]],
) -> dict[str, dict[int, int]]:
    Orders: dict[str, dict[int, int]] = {}
    for KindValueData, Values in Records.items():
        OrderData = LinkedOrder(
            Values,
            {AttrValue: (Record[1], Record[2]) for AttrValue, Record in Values.items()},
        )
        Owners = [Values[AttrValue][0] for AttrValue in OrderData]
        if len(set(Owners)) == len(Owners):
            Orders[KindValueData] = {
                Owner: RankValue for RankValue, Owner in enumerate(Owners)
            }
    return Orders


# unchanged face recovery rejects ambiguous owners before exposing stable identifiers
def FaceUnchanged(
    Records: Mapping[int, tuple[int, int, int, int]], ValueRecords: Mapping[int, int]
) -> dict[int, int]:
    Unchanged: dict[int, int] = {}
    Ambiguous: set[int] = set()
    for Owner, Ignored, Ignored, ValueIndex in Records.values():
        if ValueIndex not in ValueRecords:
            continue
        if Owner in Unchanged:
            Ambiguous.add(Owner)
        else:
            Unchanged[Owner] = ValueRecords[ValueIndex]
    for Owner in Ambiguous:
        Unchanged.pop(Owner, None)
    return Unchanged


# scan record storage separates discovered records from topology destination tables
@Dataclass(slots=True)
class ScanRecords:
    KLoopCandidates: list[TopologyRecord] = Field(default_factory=list)
    KIntersections: dict[int, IntersectRecord] = Field(default_factory=dict)
    KCharts: dict[int, ChartRecord] = Field(default_factory=dict)
    KTerms: dict[int, TermRecord] = Field(default_factory=dict)
    KSupportUv: dict[int, SupportUvRecord] = Field(default_factory=dict)
    KCompactSupportUv: dict[int, CompactUvRecord] = Field(default_factory=dict)
    KBSurfaces: dict[int, BSurfaceRecord] = Field(default_factory=dict)
    KNurbsSurfaces: dict[int, NurbsSurfRecord] = Field(default_factory=dict)
    KSurfData: dict[int, SurfaceRecord] = Field(default_factory=dict)
    KBCurves: dict[int, BCurveRecord] = Field(default_factory=dict)
    KNurbsCurves: dict[int, NurbsCurveRec] = Field(default_factory=dict)
    KCurveData: dict[int, CurveRecord] = Field(default_factory=dict)
    KTrimmedCurves: dict[int, TrimCurveRecord] = Field(default_factory=dict)
    KFloatArrays: dict[int, FloatArray] = Field(default_factory=dict)
    KShortArrays: dict[int, ShortArray] = Field(default_factory=dict)


# ambiguity storage tracks duplicate identifiers without polluting parsed record ownership
@Dataclass(slots=True)
class ScanAmbiguous:
    KIntersections: set[int] = Field(default_factory=set)
    KCharts: set[int] = Field(default_factory=set)
    KTerms: set[int] = Field(default_factory=set)
    KSupportUv: set[int] = Field(default_factory=set)
    KCompactSupportUv: set[int] = Field(default_factory=set)
    KBSurfaces: set[int] = Field(default_factory=set)
    KNurbsSurfaces: set[int] = Field(default_factory=set)
    KSurfData: set[int] = Field(default_factory=set)
    KBCurves: set[int] = Field(default_factory=set)
    KNurbsCurves: set[int] = Field(default_factory=set)
    KCurveData: set[int] = Field(default_factory=set)
    KTrimmedCurves: set[int] = Field(default_factory=set)
    KFloatArrays: set[int] = Field(default_factory=set)
    KShortArrays: set[int] = Field(default_factory=set)


# scan budget storage enforces bounded work across sampled and spline records
@Dataclass(slots=True)
class ScanBudget:
    KChartPointCount: int = 0
    KSplineScalarCount: int = 0
    KIsValid: bool = True


# partition scanning coordinates focused record phases and final geometry resolution
def ScanPartRecords(BodyData: bytes) -> RecordTables | None:
    IsVtwelve = BodyData.startswith(
        b"\x00\x00\x00\x00\x00e\x00\x02"
    ) or BodyData.startswith(b"\x00\x00\x00\x00\x00\x0c\x00\x02")
    Tables = RecordTables({}, {}, {}, {}, {}, {}, {}, {}, {}, IsVtwelve)
    Records, Ambiguous, Budget = ScanRecords(), ScanAmbiguous(), ScanBudget()
    for OffsetData in range(max(0, len(BodyData) - 1)):
        if BodyData[OffsetData] != 0:
            continue
        ScanRecordMut(BodyData, OffsetData, Tables, Records, Ambiguous, Budget)
        if not Budget.KIsValid:
            return None
    ScanInlineMut(BodyData, Records, Ambiguous)
    ResolveScansMut(BodyData, Tables, Records)
    Loops = {
        Record.attribute: Record
        for Record in Records.KLoopCandidates
        if Record.references[2] in Tables.bridges
        and (First := Tables.coedges.get(Record.references[1])) is not None
        and First.references[1] == Record.attribute
    }
    setattr(Tables, "loops", Loops)
    return Tables


# record scanning delegates each binary family while enforcing shared capacity limits
def ScanRecordMut(
    BodyData: bytes,
    OffsetData: int,
    Tables: RecordTables,
    Records: ScanRecords,
    Ambiguous: ScanAmbiguous,
    Budget: ScanBudget,
) -> None:
    KindValueData = BodyData[OffsetData + 1]
    ScanTopoMut(BodyData, OffsetData, KindValueData, Tables, Records)
    ScanChartMut(BodyData, OffsetData, KindValueData, Records, Ambiguous, Budget)
    if not Budget.KIsValid:
        return
    ScanCarrierMut(BodyData, OffsetData, KindValueData, Tables)
    ScanSurfMut(BodyData, OffsetData, KindValueData, Records, Ambiguous)
    ScanCurveMut(BodyData, OffsetData, KindValueData, Records, Ambiguous)
    ScanArrayMut(BodyData, OffsetData, KindValueData, Records, Ambiguous, Budget)
    if Budget.KIsValid and not HasScanCapacity(Tables, Records):
        Budget.KIsValid = False


# topology scanning routes fixed entity kinds into their dedicated ownership tables
def ScanTopoMut(
    BodyData: bytes,
    OffsetData: int,
    KindValueData: int,
    Tables: RecordTables,
    Records: ScanRecords,
) -> None:
    Topology: tuple[dict[int, TopologyRecord], TopologyRecord | None] | None = None
    if KindValueData == 14:
        Topology = (
            Tables.bridges,
            ParseBridge(
                BodyData,
                OffsetData,
                AllowNullOwner=Tables.v12_partition,
                AllowTolerance=Tables.v12_partition,
            ),
        )
    elif KindValueData == 15:
        Record = ParseLoop(BodyData, OffsetData)
        if Record is not None:
            Records.KLoopCandidates.append(Record)
    elif KindValueData == 16:
        Topology = (
            Tables.edge_uses,
            ParseEdgeUse(BodyData, OffsetData, AllowTolerance=Tables.v12_partition),
        )
    elif KindValueData == 17:
        Topology = (Tables.coedges, ParseCoedge(BodyData, OffsetData))
    elif KindValueData == 18:
        Topology = (Tables.vertex_uses, ParseVertexUse(BodyData, OffsetData))
    elif KindValueData == 29:
        Topology = (
            Tables.points,
            ParsePoint(BodyData, OffsetData) or ParsePoint(BodyData, OffsetData, True),
        )
    if Topology is not None:
        Target, Record = Topology
        if Record is not None:
            Target.setdefault(Record.attribute, Record)


# chart scanning owns intersection samples terms and support parameter records
def ScanChartMut(
    BodyData: bytes,
    OffsetData: int,
    KindValueData: int,
    Records: ScanRecords,
    Ambiguous: ScanAmbiguous,
    Budget: ScanBudget,
) -> None:
    Record = ParseCompactUv(BodyData, OffsetData)
    if Record is not None:
        StoreUniqueMut(
            Records.KCompactSupportUv,
            Ambiguous.KCompactSupportUv,
            Record.attribute,
            Record,
        )
    if KindValueData == 38:
        Record = ParseInterRec(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KIntersections,
                Ambiguous.KIntersections,
                Record.attribute,
                Record,
            )
    if KindValueData == 40:
        Record = ParseChart(BodyData, OffsetData)
        if Record is not None:
            Budget.KChartPointCount += len(Record.points)
            if Budget.KChartPointCount > 4000000:
                Budget.KIsValid = False
                return
            StoreUniqueMut(Records.KCharts, Ambiguous.KCharts, Record.attribute, Record)
    if KindValueData == 41:
        Record = ParseTermRecord(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(Records.KTerms, Ambiguous.KTerms, Record.attribute, Record)


# analytic carrier scanning restores direct curves surfaces and entity hierarchy records
def ScanCarrierMut(
    BodyData: bytes, OffsetData: int, KindValueData: int, Tables: RecordTables
) -> None:
    if KindValueData in {30, 31, 32, 50, 51, 52, 53, 54}:
        Carrier = ParseCarrier(BodyData, OffsetData)
        if Carrier is not None:
            Target = Tables.curves if KindValueData < 50 else Tables.surfaces
            Target[Carrier[0]] = Carrier[1]
    if KindValueData == 81:
        Entity = ParseEntity(BodyData, OffsetData)
        if Entity is not None:
            Tables.entities[Entity.attribute] = Entity


# surface record scanning retains unique carriers descriptors and data records
def ScanSurfMut(
    BodyData: bytes,
    OffsetData: int,
    KindValueData: int,
    Records: ScanRecords,
    Ambiguous: ScanAmbiguous,
) -> None:
    if KindValueData == 204:
        Record = ParseSupportRec(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KSupportUv, Ambiguous.KSupportUv, Record.attribute, Record
            )
    if KindValueData == 124:
        Record = ParseBSurface(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KBSurfaces, Ambiguous.KBSurfaces, Record.attribute, Record
            )
    if KindValueData == 126:
        Record = ParseNurbsSurf(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KNurbsSurfaces,
                Ambiguous.KNurbsSurfaces,
                Record.attribute,
                Record,
            )
    if KindValueData == 125:
        Record = ParseSurfaceDat(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KSurfData, Ambiguous.KSurfData, Record.attribute, Record
            )


# curve record scanning retains unique carriers descriptors data and trimming records
def ScanCurveMut(
    BodyData: bytes,
    OffsetData: int,
    KindValueData: int,
    Records: ScanRecords,
    Ambiguous: ScanAmbiguous,
) -> None:
    if KindValueData == 134:
        Record = ParseBCurve(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KBCurves, Ambiguous.KBCurves, Record.attribute, Record
            )
    if KindValueData == 136:
        Record = ParseNurbsCurve(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KNurbsCurves, Ambiguous.KNurbsCurves, Record.attribute, Record
            )
    if KindValueData == 135:
        Record = ParseCurveData(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KCurveData, Ambiguous.KCurveData, Record.attribute, Record
            )
    if KindValueData == 133:
        Record = ParseTrimCurve(BodyData, OffsetData)
        if Record is not None:
            StoreUniqueMut(
                Records.KTrimmedCurves,
                Ambiguous.KTrimmedCurves,
                Record.attribute,
                Record,
            )


# spline array scanning enforces scalar budgets before retaining unique records
def ScanArrayMut(
    BodyData: bytes,
    OffsetData: int,
    KindValueData: int,
    Records: ScanRecords,
    Ambiguous: ScanAmbiguous,
    Budget: ScanBudget,
) -> None:
    if KindValueData in {45, 128}:
        Record = ParseFloatArray(BodyData, OffsetData, KindValueData)
        if Record is not None:
            Budget.KSplineScalarCount += len(Record.values)
            if Budget.KSplineScalarCount > 8000000:
                Budget.KIsValid = False
                return
            StoreUniqueMut(
                Records.KFloatArrays, Ambiguous.KFloatArrays, Record.attribute, Record
            )
    if KindValueData == 127:
        Record = ParseShortArray(BodyData, OffsetData)
        if Record is not None:
            Budget.KSplineScalarCount += len(Record.values)
            if Budget.KSplineScalarCount > 8000000:
                Budget.KIsValid = False
                return
            StoreUniqueMut(
                Records.KShortArrays, Ambiguous.KShortArrays, Record.attribute, Record
            )


# scan capacity bounds aggregate topology and geometry records against resource exhaustion
def HasScanCapacity(Tables: RecordTables, Records: ScanRecords) -> bool:
    Groups = (
        Tables.bridges,
        Tables.loops,
        Tables.edge_uses,
        Tables.coedges,
        Tables.vertex_uses,
        Tables.points,
        Tables.curves,
        Tables.surfaces,
        Tables.entities,
        Records.KIntersections,
        Records.KCharts,
        Records.KTerms,
        Records.KSupportUv,
        Records.KCompactSupportUv,
        Records.KBSurfaces,
        Records.KNurbsSurfaces,
        Records.KSurfData,
        Records.KBCurves,
        Records.KNurbsCurves,
        Records.KCurveData,
        Records.KTrimmedCurves,
        Records.KFloatArrays,
        Records.KShortArrays,
    )
    return sum((len(Values) for Values in Groups)) <= 1000000


# inline scanning recovers embedded term support and intersection data records
def ScanInlineMut(
    BodyData: bytes, Records: ScanRecords, Ambiguous: ScanAmbiguous
) -> None:
    Cursor = 0
    TermDescriptor = b"term_use" + KInlineTermTail
    while (Position := BodyData.find(TermDescriptor, Cursor)) >= 0:
        BaseValue = Position + len(TermDescriptor)
        Record = ParseTermPayloa(BodyData, BaseValue, BaseValue)
        if Record is not None:
            StoreUniqueMut(Records.KTerms, Ambiguous.KTerms, Record.attribute, Record)
        Cursor = Position + 1
    Cursor = 0
    UvDescriptor = b"values" + KInlineUvTail
    while (Position := BodyData.find(UvDescriptor, Cursor)) >= 0:
        BaseValue = Position + len(UvDescriptor)
        Record = ParseSupportUv(BodyData, BaseValue, BaseValue)
        if Record is not None:
            StoreUniqueMut(
                Records.KSupportUv, Ambiguous.KSupportUv, Record.attribute, Record
            )
        Cursor = Position + 1
    Cursor = 0
    while (Position := BodyData.find(b"Z", Cursor)) >= 0:
        Record = ParseInterData(BodyData, Position)
        if Record is not None:
            StoreUniqueMut(
                Records.KIntersections,
                Ambiguous.KIntersections,
                Record.attribute,
                Record,
            )
        Cursor = Position + 1


# geometry resolution builds surfaces curves intersections and trims in dependency order
def ResolveScansMut(
    BodyData: bytes, Tables: RecordTables, Records: ScanRecords
) -> None:
    for AttrValue, Record in Records.KBSurfaces.items():
        if AttrValue in Tables.surfaces:
            continue
        SurfValue = ResolveNurbSurf(
            Record,
            Records.KNurbsSurfaces,
            Records.KSurfData,
            Records.KFloatArrays,
            Records.KShortArrays,
        )
        if SurfValue is not None:
            Tables.surfaces[AttrValue] = SurfValue
    for AttrValue, Record in Records.KBCurves.items():
        if AttrValue in Tables.curves:
            continue
        Curve = ResolveNurbCurv(
            Record,
            Records.KNurbsCurves,
            Records.KCurveData,
            Records.KFloatArrays,
            Records.KShortArrays,
        )
        if Curve is not None:
            Tables.curves[AttrValue] = Curve
    for AttrValue, Record in Records.KIntersections.items():
        if AttrValue in Tables.curves:
            continue
        Curve = ResolveInter(
            BodyData,
            Record,
            Records.KCharts,
            Records.KTerms,
            Records.KSupportUv,
            Records.KCompactSupportUv,
            Tables.surfaces,
        )
        if Curve is not None:
            Tables.curves[AttrValue] = Curve
    for AttrValue, Record in Records.KTrimmedCurves.items():
        if AttrValue in Tables.curves:
            continue
        Curve = ResolveTrimCurv(Record, Tables.curves)
        if Curve is not None:
            Tables.curves[AttrValue] = Curve


# this declaration exists because focused behavior needs one stable owner
def StoreUniqueMut(
    Target: dict[int, object], Ambiguous: set[int], AttrValue: int, Record: object
) -> None:
    if AttrValue in Ambiguous:
        return
    if AttrValue in Target:
        del Target[AttrValue]
        Ambiguous.add(AttrValue)
        return
    Target[AttrValue] = Record


# this declaration exists because focused behavior needs one stable owner
def RecordStart(DataValue: bytes, OffsetData: int, KindValueData: int) -> int | None:
    if DataValue[OffsetData : OffsetData + 2] != bytes((0, KindValueData)):
        return None
    Start = OffsetData + 2
    if Start < len(DataValue) and DataValue[Start] == 255:
        Start += 1
    return Start


# this declaration exists because focused behavior needs one stable owner
def ReadShort(DataValue: bytes, OffsetData: int) -> int | None:
    if OffsetData < 0 or OffsetData + 2 > len(DataValue):
        return None
    return Struct.unpack_from(">H", DataValue, OffsetData)[0]


# this declaration exists because focused behavior needs one stable owner
def ReadUnsigned(DataValue: bytes, OffsetData: int) -> int | None:
    if OffsetData < 0 or OffsetData + 4 > len(DataValue):
        return None
    return Struct.unpack_from(">I", DataValue, OffsetData)[0]


# this declaration exists because focused behavior needs one stable owner
def XmtData(DataValue: bytes, OffsetData: int) -> tuple[int, int] | None:
    if OffsetData < 0 or OffsetData + 2 > len(DataValue):
        return None
    First = Struct.unpack_from(">h", DataValue, OffsetData)[0]
    if First >= 0:
        return (First, 2)
    if First == -32768 or OffsetData + 4 > len(DataValue):
        return None
    Quotient = ReadShort(DataValue, OffsetData + 2)
    if Quotient is None:
        return None
    return (Quotient * 32767 + abs(First), 4)


# this declaration exists because focused behavior needs one stable owner
def XmtSeq(
    DataValue: bytes, OffsetData: int, Count: int
) -> tuple[tuple[int, ...], int] | None:
    Values = []
    Cursor = OffsetData
    for Ignored in range(Count):
        Decoded = XmtData(DataValue, Cursor)
        if Decoded is None:
            return None
        ValueData, Width = Decoded
        Values.append(ValueData)
        Cursor += Width
    return (tuple(Values), Cursor)


# this declaration exists because focused behavior needs one stable owner
def ParseBSurface(DataValue: bytes, OffsetData: int) -> BSurfaceRecord | None:
    Start = RecordStart(DataValue, OffsetData, 124)
    if Start is None:
        return None
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    State = ReadUnsigned(DataValue, Cursor)
    if AttrValue <= 1 or State is None:
        return None
    Cursor += 4
    Header = XmtSeq(DataValue, Cursor, 5)
    if Header is None:
        return None
    HeaderRefs, Cursor = Header
    if Cursor >= len(DataValue) or DataValue[Cursor] not in {43, 45}:
        return None
    Sense = DataValue[Cursor] == 43
    Construction = XmtSeq(DataValue, Cursor + 1, 2)
    if Construction is None:
        return None
    RefsValueData, Cursor = Construction
    NativeLayout = HeaderRefs[0] == 1 and all(
        (ValueData >= 1 for ValueData in HeaderRefs)
    )
    CompactLayout = (
        State == 1
        and HeaderRefs == (0, 0, 0, 0, 0)
        and Sense
        and (RefsValueData[1] == 0)
    )
    if RefsValueData[0] <= 1 or not (NativeLayout or CompactLayout):
        return None
    return BSurfaceRecord(
        AttrValue,
        State,
        HeaderRefs,
        RefsValueData[0],
        RefsValueData[1],
        Sense,
        OffsetData,
        DataValue[OffsetData:Cursor],
    )


# this declaration exists because focused behavior needs one stable owner
def ParseNurbsSurf(DataValue: bytes, OffsetData: int) -> NurbsSurfRecord | None:
    Start = RecordStart(DataValue, OffsetData, 126)
    if Start is None:
        return None
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    if AttrValue <= 1:
        return None
    if DataValue[Cursor : Cursor + 12] == bytes(12):
        return ParseCompSurf(DataValue, OffsetData, AttrValue, Cursor)
    return ParseExtSurf(DataValue, OffsetData, AttrValue, Cursor)


# compact surface parsing preserves the fixed descriptor representation
def ParseCompSurf(
    DataValue: bytes, OffsetData: int, AttrValue: int, Cursor: int
) -> NurbsSurfRecord | None:
    RefsValueData = XmtSeq(DataValue, Cursor + 12, 5)
    if RefsValueData is None or any((ValueData <= 1 for ValueData in RefsValueData[0])):
        return None
    Values, EndValue = RefsValueData
    return NurbsSurfRecord(
        AttrValue,
        (False, False),
        (0, 0),
        (0, 0),
        (0, 0),
        (0, 0),
        False,
        (False, False),
        0,
        0,
        Values,
        "compact",
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# extended surface parsing owns validation of every encoded descriptor field
def ParseExtSurf(
    DataValue: bytes, OffsetData: int, AttrValue: int, Cursor: int
) -> NurbsSurfRecord | None:
    if Cursor + 30 > len(DataValue):
        return None
    PeriodicValues = DataValue[Cursor : Cursor + 2]
    Degrees = (ReadShort(DataValue, Cursor + 2), ReadShort(DataValue, Cursor + 4))
    Counts = (ReadUnsigned(DataValue, Cursor + 6), ReadUnsigned(DataValue, Cursor + 10))
    KnotTypes = (DataValue[Cursor + 14], DataValue[Cursor + 15])
    KnotCounts = (
        ReadUnsigned(DataValue, Cursor + 16),
        ReadUnsigned(DataValue, Cursor + 20),
    )
    RationalValue = DataValue[Cursor + 24]
    ClosedValues = DataValue[Cursor + 25 : Cursor + 27]
    SurfForm = DataValue[Cursor + 27]
    VertexDimension = ReadShort(DataValue, Cursor + 28)
    RefsValueData = XmtSeq(DataValue, Cursor + 30, 5)
    if (
        any((ValueData not in {0, 1} for ValueData in PeriodicValues))
        or any((ValueData is None for ValueData in Degrees))
        or any((ValueData is None for ValueData in Counts))
        or any((ValueData is None for ValueData in KnotCounts))
        or (RationalValue not in {0, 1})
        or any((ValueData not in {0, 1} for ValueData in ClosedValues))
        or (VertexDimension not in {3, 4})
        or (RefsValueData is None)
    ):
        return None
    DegreeU, DegreeV = Degrees
    CountU, CountV = Counts
    KnotCountU, KnotCountV = KnotCounts
    if (
        DegreeU is None
        or DegreeV is None
        or CountU is None
        or (CountV is None)
        or (KnotCountU is None)
        or (KnotCountV is None)
        or (DegreeU < 1)
        or (DegreeV < 1)
        or (CountU <= DegreeU)
        or (CountV <= DegreeV)
        or (CountU > 1000000)
        or (CountV > 1000000)
        or (CountU * CountV > 1000000)
        or (not 2 <= KnotCountU <= 1000000)
        or (not 2 <= KnotCountV <= 1000000)
        or ((VertexDimension == 4) != bool(RationalValue))
        or any((ValueData <= 1 for ValueData in RefsValueData[0]))
    ):
        return None
    Values, EndValue = RefsValueData
    return NurbsSurfRecord(
        AttrValue,
        tuple((bool(ValueData) for ValueData in PeriodicValues)),
        (DegreeU, DegreeV),
        (CountU, CountV),
        KnotTypes,
        (KnotCountU, KnotCountV),
        bool(RationalValue),
        tuple((bool(ValueData) for ValueData in ClosedValues)),
        SurfForm,
        VertexDimension,
        Values,
        "extended",
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# this declaration exists because focused behavior needs one stable owner
def ParseSurfaceDat(DataValue: bytes, OffsetData: int) -> SurfaceRecord | None:
    Start = RecordStart(DataValue, OffsetData, 125)
    if Start is None:
        return None
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    FixedEnd = Cursor + 77
    if AttrValue <= 1 or FixedEnd > len(DataValue):
        return None
    Values = Struct.unpack_from(">8d", DataValue, Cursor)
    if any((not MathValue.isfinite(ValueData) for ValueData in Values)):
        return None
    Intervals = tuple(((Values[Index], Values[Index + 1]) for Index in range(0, 8, 2)))
    SelfInter = DataValue[Cursor + 64]
    Flags = DataValue[Cursor + 65 : FixedEnd]
    RefsValueData = XmtSeq(DataValue, FixedEnd, 4)
    if RefsValueData is None or any((ValueData < 1 for ValueData in RefsValueData[0])):
        return None
    Values, EndValue = RefsValueData
    return SurfaceRecord(
        AttrValue,
        Intervals,
        SelfInter,
        Flags,
        Values,
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# this declaration exists because focused behavior needs one stable owner
def ParseBCurve(DataValue: bytes, OffsetData: int) -> BCurveRecord | None:
    Start = RecordStart(DataValue, OffsetData, 134)
    if Start is None:
        return None
    if Start == OffsetData + 2:
        Compact = ParseCompCurve(DataValue, OffsetData, Start)
        if Compact is not None:
            return Compact
    return ParseExtCurve(DataValue, OffsetData, Start)


# extended curve parsing validates the carrier header and construction references
def ParseExtCurve(DataValue: bytes, OffsetData: int, Start: int) -> BCurveRecord | None:
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    if AttrValue <= 1:
        return None
    State = ReadUnsigned(DataValue, Cursor)
    if State is None:
        return None
    Header = XmtSeq(DataValue, Cursor + 4, 5)
    if Header is None:
        return None
    HeaderRefs, Cursor = Header
    if HeaderRefs[0] != 1 or any((ValueData < 1 for ValueData in HeaderRefs)):
        return None
    if Cursor >= len(DataValue) or DataValue[Cursor] not in {43, 45}:
        return None
    Sense = DataValue[Cursor] == 43
    Construction = XmtSeq(DataValue, Cursor + 1, 2)
    if Construction is None:
        return None
    RefsValueData, EndValue = Construction
    if RefsValueData[0] <= 1 or RefsValueData[1] < 1:
        return None
    return BCurveRecord(
        AttrValue,
        State,
        HeaderRefs,
        RefsValueData[0],
        RefsValueData[1],
        Sense,
        "extended",
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# compact curve parsing isolates the fixed width carrier representation
def ParseCompCurve(
    DataValue: bytes, OffsetData: int, Start: int
) -> BCurveRecord | None:
    CompactAttr = ReadShort(DataValue, Start)
    CompactDescriptor = ReadShort(DataValue, Start + 2)
    CompactEnd = Start + 12
    if CompactAttr is None or CompactDescriptor is None:
        return None
    if CompactAttr <= 1 or CompactDescriptor <= 1 or CompactEnd > len(DataValue):
        return None
    if DataValue[Start + 4 : CompactEnd] != bytes(8):
        return None
    return BCurveRecord(
        CompactAttr,
        0,
        (0, 0, 0, 0, 0),
        CompactDescriptor,
        0,
        True,
        "compact",
        OffsetData,
        DataValue[OffsetData:CompactEnd],
    )


# this declaration exists because focused behavior needs one stable owner
def ParseNurbsCurve(DataValue: bytes, OffsetData: int) -> NurbsCurveRec | None:
    Start = RecordStart(DataValue, OffsetData, 136)
    if Start is None:
        return None
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    if AttrValue <= 1 or Cursor + 17 > len(DataValue):
        return None
    Degree = ReadShort(DataValue, Cursor)
    ControlCount = ReadUnsigned(DataValue, Cursor + 2)
    VertexDimension = ReadShort(DataValue, Cursor + 6)
    KnotCount = ReadUnsigned(DataValue, Cursor + 8)
    KnotType = DataValue[Cursor + 12]
    PeriodicValue = DataValue[Cursor + 13]
    ClosedValue = DataValue[Cursor + 14]
    RationalValue = DataValue[Cursor + 15]
    CurveForm = DataValue[Cursor + 16]
    RefsValueData = XmtSeq(DataValue, Cursor + 17, 3)
    if (
        Degree is None
        or ControlCount is None
        or VertexDimension not in {3, 4}
        or (KnotCount is None)
        or (PeriodicValue not in {0, 1})
        or (ClosedValue not in {0, 1})
        or (RationalValue not in {0, 1})
        or (RefsValueData is None)
        or (Degree < 1)
        or (ControlCount <= Degree)
        or (ControlCount > 1000000)
        or (not 2 <= KnotCount <= 1000000)
        or ((VertexDimension == 4) != bool(RationalValue))
        or any((ValueData <= 1 for ValueData in RefsValueData[0]))
    ):
        return None
    Values, EndValue = RefsValueData
    return NurbsCurveRec(
        AttrValue,
        Degree,
        ControlCount,
        VertexDimension,
        KnotCount,
        KnotType,
        bool(PeriodicValue),
        bool(ClosedValue),
        bool(RationalValue),
        CurveForm,
        Values,
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# this declaration exists because focused behavior needs one stable owner
def ParseCurveData(DataValue: bytes, OffsetData: int) -> CurveRecord | None:
    Start = RecordStart(DataValue, OffsetData, 135)
    if Start is None:
        return None
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    if AttrValue <= 1 or Cursor >= len(DataValue):
        return None
    SelfInter = DataValue[Cursor]
    AnalyticForm = XmtData(DataValue, Cursor + 1)
    if AnalyticForm is None or AnalyticForm[0] < 1:
        return None
    RefValue, RefWidth = AnalyticForm
    EndValue = Cursor + 1 + RefWidth
    return CurveRecord(
        AttrValue, SelfInter, RefValue, OffsetData, DataValue[OffsetData:EndValue]
    )


# this declaration exists because focused behavior needs one stable owner
def ParseTrimCurve(DataValue: bytes, OffsetData: int) -> TrimCurveRecord | None:
    HeaderData = ParseTrimHead(DataValue, OffsetData)
    if HeaderData is None:
        return None
    AttrValue, State, HeaderRefs, BasisRef, Sense, ValuesOffset = HeaderData
    EndValue = ValuesOffset + 64
    if EndValue > len(DataValue):
        return None
    PointOne = PointVector(DataValue, ValuesOffset)
    PointTwo = PointVector(DataValue, ValuesOffset + 24)
    Params = Struct.unpack_from(">2d", DataValue, ValuesOffset + 48)
    if (
        PointOne is None
        or PointTwo is None
        or any((not MathValue.isfinite(ValueData) for ValueData in Params))
    ):
        return None
    return TrimCurveRecord(
        AttrValue,
        State,
        HeaderRefs,
        BasisRef,
        (PointOne, PointTwo),
        Params,
        Sense,
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# trimmed curve header parsing validates references before reading geometric values
def ParseTrimHead(
    DataValue: bytes, OffsetData: int
) -> tuple[int, int, tuple[int, ...], int, bool, int] | None:
    Start = RecordStart(DataValue, OffsetData, 133)
    if Start is None:
        return None
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    State = ReadUnsigned(DataValue, Cursor)
    if AttrValue <= 1 or State is None:
        return None
    Header = XmtSeq(DataValue, Cursor + 4, 5)
    if Header is None:
        return None
    HeaderRefs, Cursor = Header
    if HeaderRefs[0] != 1 or any((ValueData < 1 for ValueData in HeaderRefs)):
        return None
    if Cursor >= len(DataValue) or DataValue[Cursor] not in {43, 45}:
        return None
    Sense = DataValue[Cursor] == 43
    Basis = XmtData(DataValue, Cursor + 1)
    if Basis is None or Basis[0] <= 1:
        return None
    BasisRef, BasisWidth = Basis
    ValuesOffset = Cursor + 1 + BasisWidth
    return AttrValue, State, HeaderRefs, BasisRef, Sense, ValuesOffset


# this declaration exists because focused behavior needs one stable owner
def ArrayFields(
    DataValue: bytes, OffsetData: int, KindValueData: int
) -> tuple[int, int, int] | None:
    if DataValue[OffsetData : OffsetData + 2] != bytes((0, KindValueData)):
        return None
    Cursor = OffsetData + 2
    if Cursor < len(DataValue) and DataValue[Cursor] in {43, 45}:
        Cursor += 1
    if Cursor < len(DataValue) and DataValue[Cursor] == 255:
        Cursor += 1
    Count = ReadUnsigned(DataValue, Cursor)
    Decoded = XmtData(DataValue, Cursor + 4)
    if Count is None or Decoded is None or (not 1 <= Count <= 1000000):
        return None
    AttrValue, Width = Decoded
    if AttrValue <= 1:
        return None
    return (AttrValue, Count, Cursor + 4 + Width)


# this declaration exists because focused behavior needs one stable owner
def ParseFloatArray(
    DataValue: bytes, OffsetData: int, KindValueData: int
) -> FloatArray | None:
    Fields = ArrayFields(DataValue, OffsetData, KindValueData)
    if Fields is None:
        return None
    AttrValue, Count, ValuesOffset = Fields
    EndValue = ValuesOffset + Count * 8
    if EndValue > len(DataValue):
        return None
    Values = Struct.unpack_from(f">{Count}d", DataValue, ValuesOffset)
    if any((not MathValue.isfinite(ValueData) for ValueData in Values)):
        return None
    return FloatArray(
        AttrValue, KindValueData, Values, OffsetData, DataValue[OffsetData:EndValue]
    )


# this declaration exists because focused behavior needs one stable owner
def ParseShortArray(DataValue: bytes, OffsetData: int) -> ShortArray | None:
    Fields = ArrayFields(DataValue, OffsetData, 127)
    if Fields is None:
        return None
    AttrValue, Count, ValuesOffset = Fields
    EndValue = ValuesOffset + Count * 2
    if EndValue > len(DataValue):
        return None
    Values = Struct.unpack_from(f">{Count}H", DataValue, ValuesOffset)
    if any((ValueData == 0 for ValueData in Values)):
        return None
    return ShortArray(AttrValue, Values, OffsetData, DataValue[OffsetData:EndValue])


# this declaration exists because focused behavior needs one stable owner
def CompactNurbSurf(
    ControlCount: int, UMultiplicities: Sequence[int], VMultiplicities: Sequence[int]
) -> tuple[int, int, int, int, int] | None:
    Candidates = []
    USumValue = sum(UMultiplicities)
    VSumValue = sum(VMultiplicities)
    for Dimension in (3, 4):
        if ControlCount % Dimension:
            continue
        PoleCount = ControlCount // Dimension
        for DegreeU in range(1, 9):
            CountU = USumValue - DegreeU - 1
            if CountU <= DegreeU:
                continue
            for DegreeV in range(1, 9):
                CountV = VSumValue - DegreeV - 1
                if CountV > DegreeV and CountU * CountV == PoleCount:
                    Candidates.append((CountU, CountV, DegreeU, DegreeV, Dimension))
    return Candidates[0] if len(Candidates) == 1 else None


# this declaration exists because focused behavior needs one stable owner
def ResolveNurbSurf(
    Record: BSurfaceRecord,
    Descriptors: Mapping[int, NurbsSurfRecord],
    SurfData: Mapping[int, SurfaceRecord],
    FloatArrays: Mapping[int, FloatArray],
    ShortArrays: Mapping[int, ShortArray],
) -> NurbsSurface | None:
    Descriptor = Descriptors.get(Record.descriptor_reference)
    DataRecord = (
        SurfData.get(Record.data_reference) if Record.data_reference > 1 else None
    )
    if (
        Descriptor is None
        or len(set(Descriptor.references)) != 5
        or (Record.data_reference > 1 and DataRecord is None)
    ):
        return None
    Control = FloatArrays.get(Descriptor.references[0])
    UMultiplicities = ShortArrays.get(Descriptor.references[1])
    VMultiplicities = ShortArrays.get(Descriptor.references[2])
    UKnots = FloatArrays.get(Descriptor.references[3])
    VKnots = FloatArrays.get(Descriptor.references[4])
    if (
        Control is None
        or Control.kind != 45
        or UMultiplicities is None
        or (VMultiplicities is None)
        or (UKnots is None)
        or (UKnots.kind != 128)
        or (VKnots is None)
        or (VKnots.kind != 128)
        or (len(UMultiplicities.values) != len(UKnots.values))
        or (len(VMultiplicities.values) != len(VKnots.values))
        or any(
            (
                LeftValue >= Right
                for Values in (UKnots.values, VKnots.values)
                for LeftValue, Right in zip(Values, Values[1:])
            )
        )
    ):
        return None
    Shape = NurbsSurfShape(
        Descriptor, Control, UMultiplicities, VMultiplicities, UKnots, VKnots
    )
    if Shape is None:
        return None
    (
        CountU,
        CountV,
        DegreeU,
        DegreeV,
        Dimension,
        Periodic,
        Closed,
        Rational,
        KnotTypes,
        KnotCounts,
        SurfForm,
    ) = Shape
    PointData = NurbsSurfPoints(Control.values, Dimension, Rational)
    if PointData is None:
        return None
    Points, Weights = PointData
    RowsValue = tuple(
        (
            tuple(Points[Index * CountV : (Index + 1) * CountV])
            for Index in range(CountU)
        )
    )
    WeightRows = (
        tuple(
            (
                tuple(Weights[Index * CountV : (Index + 1) * CountV])
                for Index in range(CountU)
            )
        )
        if Rational
        else ()
    )
    Attrs = FrozenMapping(
        {
            "state": Record.state,
            "sense": Record.sense,
            "header_references": Record.header_references,
            "descriptor_reference": Record.descriptor_reference,
            "data_reference": Record.data_reference,
            "descriptor_layout": Descriptor.layout,
            "degrees": (DegreeU, DegreeV),
            "counts": (CountU, CountV),
            "periodic": Periodic,
            "knot_types": KnotTypes,
            "knot_counts": KnotCounts,
            "array_references": Descriptor.references,
            "rational": Rational,
            "closed": Closed,
            "surface_form": SurfForm,
            "vertex_dimension": Dimension,
            "surface_data_intervals": (
                DataRecord.intervals if DataRecord is not None else ()
            ),
            "surface_data_self_intersection": (
                DataRecord.self_intersection if DataRecord is not None else 0
            ),
            "surface_data_flags": DataRecord.flags if DataRecord is not None else b"",
            "surface_data_references": (
                DataRecord.references if DataRecord is not None else ()
            ),
            "surface_record": Record.raw,
            "descriptor_record": Descriptor.raw,
            "surface_data_record": DataRecord.raw if DataRecord is not None else b"",
            "control_record": Control.raw,
            "u_multiplicity_record": UMultiplicities.raw,
            "v_multiplicity_record": VMultiplicities.raw,
            "u_knot_record": UKnots.raw,
            "v_knot_record": VKnots.raw,
        }
    )
    return NurbsSurface(
        NativeId("surface", Record.attribute),
        DegreeU,
        DegreeV,
        RowsValue,
        UKnots.values,
        VKnots.values,
        UMultiplicities.values,
        VMultiplicities.values,
        WeightRows,
        Periodic[0],
        Periodic[1],
        attributes=Attrs,
    )


# surface shape resolution unifies compact inference with explicit descriptor metadata
def NurbsSurfShape(
    Descriptor: NurbsSurfRecord,
    Control: FloatArray,
    UMultiplicities: ShortArray,
    VMultiplicities: ShortArray,
    UKnots: FloatArray,
    VKnots: FloatArray,
) -> tuple[object, ...] | None:
    if Descriptor.layout == "compact":
        Inferred = CompactNurbSurf(
            len(Control.values), UMultiplicities.values, VMultiplicities.values
        )
        if Inferred is None:
            return None
        CountU, CountV, DegreeU, DegreeV, Dimension = Inferred
        Periodic, Closed = (False, False), (False, False)
        Rational, KnotTypes = Dimension == 4, (0, 0)
        KnotCounts, SurfForm = (len(UKnots.values), len(VKnots.values)), 0
    else:
        CountU, CountV = Descriptor.counts
        DegreeU, DegreeV = Descriptor.degrees
        Dimension, Periodic, Closed = (
            Descriptor.vertex_dimension,
            Descriptor.periodic,
            Descriptor.closed,
        )
        Rational, KnotTypes = Descriptor.rational, Descriptor.knot_types
        KnotCounts, SurfForm = Descriptor.knot_counts, Descriptor.surface_form
    IsValid = len(Control.values) == CountU * CountV * Dimension
    IsValid = (
        IsValid
        and len(UKnots.values) == KnotCounts[0]
        and len(VKnots.values) == KnotCounts[1]
    )
    IsValid = IsValid and sum(UMultiplicities.values) == CountU + DegreeU + 1
    IsValid = IsValid and sum(VMultiplicities.values) == CountV + DegreeV + 1
    return (
        (
            CountU,
            CountV,
            DegreeU,
            DegreeV,
            Dimension,
            Periodic,
            Closed,
            Rational,
            KnotTypes,
            KnotCounts,
            SurfForm,
        )
        if IsValid
        else None
    )


# surface pole decoding restores euclidean points and validated rational weights
def NurbsSurfPoints(
    Values: Sequence[float], Dimension: int, Rational: bool
) -> tuple[tuple[VectorThree, ...], tuple[float, ...]] | None:
    Points, Weights = [], []
    for PoleValue in (
        Values[Index : Index + Dimension] for Index in range(0, len(Values), Dimension)
    ):
        Weight = PoleValue[3] if Rational else 1.0
        if not MathValue.isfinite(Weight) or Weight <= 0.0:
            return None
        Coords = tuple(
            (ValueData / Weight / KLengthScale for ValueData in PoleValue[:3])
        )
        if any((not MathValue.isfinite(ValueData) for ValueData in Coords)):
            return None
        Points.append(VectorThree(*Coords))
        if Rational:
            Weights.append(Weight)
    return tuple(Points), tuple(Weights)


# this declaration exists because focused behavior needs one stable owner
def ResolveNurbCurv(
    Record: BCurveRecord,
    Descriptors: Mapping[int, NurbsCurveRec],
    CurveData: Mapping[int, CurveRecord],
    FloatArrays: Mapping[int, FloatArray],
    ShortArrays: Mapping[int, ShortArray],
) -> NurbsCurve | None:
    Descriptor = Descriptors.get(Record.descriptor_reference)
    DataRecord = (
        CurveData.get(Record.data_reference) if Record.data_reference > 1 else None
    )
    if (
        Descriptor is None
        or len(set(Descriptor.references)) != 3
        or (Record.data_reference > 1 and DataRecord is None)
    ):
        return None
    Control = FloatArrays.get(Descriptor.references[0])
    Multiplicities = ShortArrays.get(Descriptor.references[1])
    Knots = FloatArrays.get(Descriptor.references[2])
    if (
        Control is None
        or Control.kind != 45
        or Multiplicities is None
        or (Knots is None)
        or (Knots.kind != 128)
        or (
            len(Control.values)
            != Descriptor.control_count * Descriptor.vertex_dimension
        )
        or (len(Multiplicities.values) != Descriptor.knot_count)
        or (len(Knots.values) != Descriptor.knot_count)
        or (
            sum(Multiplicities.values)
            != Descriptor.control_count + Descriptor.degree + 1
        )
        or any(
            (
                LeftValue >= Right
                for LeftValue, Right in zip(Knots.values, Knots.values[1:])
            )
        )
    ):
        return None
    Points = []
    Weights = []
    Dimension = Descriptor.vertex_dimension
    for PoleValue in (
        Control.values[Index : Index + Dimension]
        for Index in range(0, len(Control.values), Dimension)
    ):
        Weight = PoleValue[3] if Descriptor.rational else 1.0
        if not MathValue.isfinite(Weight) or Weight <= 0.0:
            return None
        Coords = tuple(
            (ValueData / Weight / KLengthScale for ValueData in PoleValue[:3])
        )
        if any((not MathValue.isfinite(ValueData) for ValueData in Coords)):
            return None
        Points.append(VectorThree(*Coords))
        if Descriptor.rational:
            Weights.append(Weight)
    Attrs = FrozenMapping(
        {
            "state": Record.state,
            "sense": Record.sense,
            "header_references": Record.header_references,
            "descriptor_reference": Record.descriptor_reference,
            "data_reference": Record.data_reference,
            "carrier_layout": Record.layout,
            "control_count": Descriptor.control_count,
            "vertex_dimension": Descriptor.vertex_dimension,
            "knot_count": Descriptor.knot_count,
            "knot_type": Descriptor.knot_type,
            "closed": Descriptor.closed,
            "rational": Descriptor.rational,
            "curve_form": Descriptor.curve_form,
            "array_references": Descriptor.references,
            "curve_data_self_intersection": (
                DataRecord.self_intersection if DataRecord is not None else 0
            ),
            "analytic_form_reference": (
                DataRecord.analytic_form_reference if DataRecord is not None else 0
            ),
            "curve_record": Record.raw,
            "descriptor_record": Descriptor.raw,
            "curve_data_record": DataRecord.raw if DataRecord is not None else b"",
            "control_record": Control.raw,
            "multiplicity_record": Multiplicities.raw,
            "knot_record": Knots.raw,
        }
    )
    return NurbsCurve(
        NativeId("curve", Record.attribute),
        Descriptor.degree,
        tuple(Points),
        Knots.values,
        Multiplicities.values,
        tuple(Weights),
        Descriptor.periodic,
        attributes=Attrs,
    )


# this declaration exists because focused behavior needs one stable owner
def ResolveTrimCurv(
    Record: TrimCurveRecord, Curves: Mapping[int, object]
) -> object | None:
    Basis = Curves.get(Record.basis_reference)
    if (
        not Record.sense
        or Record.attribute == Record.basis_reference
        or (
            not isinstance(
                Basis,
                (LineCurve, CircleCurve, EllipseCurve, NurbsCurve, IntersectionCurve),
            )
        )
    ):
        return None
    ParamOne, ParamTwo = Record.parameters
    BasisSense = Basis.attributes.get("sense", True)
    if type(BasisSense) is not bool:
        return None
    if BasisSense and ParamTwo <= ParamOne or (not BasisSense and ParamTwo >= ParamOne):
        return None
    DomainValues = TrimCurveDomain(Basis, ParamOne, ParamTwo)
    if DomainValues is None:
        return None
    Periodic, Closed = DomainValues
    EvaluationParams = (
        (ParamOne / KLengthScale, ParamTwo / KLengthScale)
        if isinstance(Basis, LineCurve)
        else Record.parameters
    )
    Evaluated = tuple((CurvePoint(Basis, Param) for Param in EvaluationParams))
    TolValue = (
        max(Basis.tolerance, 1e-07) if isinstance(Basis, IntersectionCurve) else 1e-07
    )
    if any((ValueData is None for ValueData in Evaluated)) or any(
        (
            Distance(ValueData, Point) > TolValue
            for ValueData, Point in zip(Evaluated, Record.points)
            if ValueData is not None
        )
    ):
        return None
    if not Periodic and (not Closed) and (Distance(*Record.points) <= TolValue):
        return None
    Attrs = dict(Basis.attributes)
    Attrs.update(
        {
            "trimmed": True,
            "sense": Record.sense,
            "basis_sense": BasisSense,
            "state": Record.state,
            "header_references": Record.header_references,
            "basis_reference": Record.basis_reference,
            "basis_curve_id": Basis.id,
            "trim_points": Record.points,
            "trim_parameters": EvaluationParams,
            "trim_parameters_native": Record.parameters,
            "trim_record": Record.raw,
        }
    )
    return Replace(
        Basis, id=NativeId("curve", Record.attribute), attributes=FrozenMapping(Attrs)
    )


# trimmed curve domain validation isolates periodic and bounded parameter rules
def TrimCurveDomain(
    Basis: object, ParamOne: float, ParamTwo: float
) -> tuple[bool, bool] | None:
    if isinstance(Basis, LineCurve):
        return False, False
    Domain = CurveParamRange(Basis)
    if Domain is None:
        return None
    Lower, Upper, Periodic, Closed = Domain
    Epsilon = max(abs(Lower), abs(Upper), 1.0) * 1e-12
    if Periodic:
        IsValid = Lower - Epsilon <= ParamOne <= Upper + Epsilon
        IsValid = IsValid and abs(ParamTwo - ParamOne) <= Upper - Lower + Epsilon
    else:
        IsValid = Lower - Epsilon <= ParamOne <= Upper + Epsilon
        IsValid = IsValid and Lower - Epsilon <= ParamTwo <= Upper + Epsilon
    return (Periodic, Closed) if IsValid else None


# this declaration exists because focused behavior needs one stable owner
def InterFields(
    DataValue: bytes, OffsetData: int, Start: int
) -> IntersectRecord | None:
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    Cursor = Start + Width
    if AttrValue <= 1 or ReadUnsigned(DataValue, Cursor) is None:
        return None
    Cursor += 4
    Header = XmtSeq(DataValue, Cursor, 5)
    if Header is None:
        return None
    HeaderRefs, Cursor = Header
    if HeaderRefs[0] != 1 or any((ValueData < 1 for ValueData in HeaderRefs)):
        return None
    if Cursor >= len(DataValue) or DataValue[Cursor] not in {43, 45}:
        return None
    Sense = DataValue[Cursor] == 43
    Cursor += 1
    Construction = XmtSeq(DataValue, Cursor, 6)
    if Construction is None:
        return None
    RefsValueData, Cursor = Construction
    if (
        any((ValueData < 1 for ValueData in RefsValueData))
        or RefsValueData[0] <= 1
        or RefsValueData[1] <= 1
        or (RefsValueData[2] <= 1)
    ):
        return None
    return IntersectRecord(
        AttrValue,
        HeaderRefs,
        RefsValueData,
        Sense,
        OffsetData,
        DataValue[OffsetData:Cursor],
    )


# this declaration exists because focused behavior needs one stable owner
def ParseInterRec(DataValue: bytes, OffsetData: int) -> IntersectRecord | None:
    Start = RecordStart(DataValue, OffsetData, 38)
    return InterFields(DataValue, OffsetData, Start) if Start is not None else None


# this declaration exists because focused behavior needs one stable owner
def ParseInterData(DataValue: bytes, OffsetData: int) -> IntersectRecord | None:
    if OffsetData < 0 or OffsetData >= len(DataValue) or DataValue[OffsetData] != 90:
        return None
    Descriptor = b"intersection_data"
    Lower = max(0, OffsetData - 96)
    Position = DataValue.rfind(Descriptor, Lower, OffsetData)
    if Position < 0 or OffsetData - Position - len(Descriptor) > 64:
        return None
    return InterFields(DataValue, OffsetData, OffsetData + 1)


# this declaration exists because focused behavior needs one stable owner
def PointVector(DataValue: bytes, OffsetData: int) -> VectorThree | None:
    if OffsetData < 0 or OffsetData + 24 > len(DataValue):
        return None
    Values = Struct.unpack_from(">3d", DataValue, OffsetData)
    if any((not MathValue.isfinite(ValueData) for ValueData in Values)):
        return None
    Scaled = tuple((ValueData / KLengthScale for ValueData in Values))
    return (
        VectorThree(*Scaled)
        if all((MathValue.isfinite(ValueData) for ValueData in Scaled))
        else None
    )


# this declaration exists because focused behavior needs one stable owner
def ParseChart(DataValue: bytes, OffsetData: int) -> ChartRecord | None:
    HeaderData = ParseChartHead(DataValue, OffsetData)
    if HeaderData is None:
        return None
    (
        Count,
        AttrValue,
        BaseParam,
        BaseScale,
        ChordalError,
        AngularError,
        ParamErrors,
        Block,
    ) = HeaderData
    ExtValue = ParseExtPoints(DataValue, Block, Count)
    if ExtValue is not None:
        Points, Params, Tangents, SupportUv, EndValue = ExtValue
        Layout = "ext11"
    else:
        Compact = ParseCompactPts(DataValue, Block, Count, BaseParam, BaseScale)
        if Compact is None:
            return None
        Points, Params, EndValue = Compact
        Tangents, SupportUv, Layout = (), ((), ()), "xyz3"
    return ChartRecord(
        AttrValue,
        BaseParam,
        BaseScale,
        ChordalError / KLengthScale,
        AngularError,
        ParamErrors,
        Points,
        Params,
        Tangents,
        SupportUv,
        Layout,
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# chart header parsing validates scalar metadata before reading sampled points
def ParseChartHead(
    DataValue: bytes, OffsetData: int
) -> tuple[int, int, float, float, float, float, tuple[float, float], int] | None:
    Start = RecordStart(DataValue, OffsetData, 40)
    if Start is None:
        return None
    Count = ReadUnsigned(DataValue, Start)
    Decoded = XmtData(DataValue, Start + 4)
    if Count is None or not 2 <= Count <= 1024 or Decoded is None:
        return None
    AttrValue, Width = Decoded
    Preamble = Start + 4 + Width
    if AttrValue <= 1 or Preamble + 52 > len(DataValue):
        return None
    BaseParam = Struct.unpack_from(">d", DataValue, Preamble)[0]
    BaseScale = Struct.unpack_from(">d", DataValue, Preamble + 8)[0]
    ChartCount = ReadUnsigned(DataValue, Preamble + 16)
    ChordalError = Struct.unpack_from(">d", DataValue, Preamble + 20)[0]
    AngularError = Struct.unpack_from(">d", DataValue, Preamble + 28)[0]
    ParamErrors = Struct.unpack_from(">2d", DataValue, Preamble + 36)
    if (
        ChartCount != Count
        or not all(
            (
                MathValue.isfinite(ValueData)
                for ValueData in (
                    BaseParam,
                    BaseScale,
                    ChordalError,
                    AngularError,
                    *ParamErrors,
                )
            )
        )
        or BaseScale <= 0.0
        or (ChordalError <= 0.0)
        or (ParamErrors != (KMissingParam, KMissingParam))
    ):
        return None
    Block = Preamble + 52
    return (
        Count,
        AttrValue,
        BaseParam,
        BaseScale,
        ChordalError,
        AngularError,
        ParamErrors,
        Block,
    )


# this declaration exists because focused behavior needs one stable owner
def ParseExtPoints(DataValue: bytes, OffsetData: int, Count: int) -> (
    tuple[
        tuple[VectorThree, ...],
        tuple[float, ...],
        tuple[VectorThree, ...],
        tuple[tuple[tuple[float, float], ...], ...],
        int,
    ]
    | None
):
    EndValue = OffsetData + Count * 88
    if EndValue > len(DataValue):
        return None
    Points = []
    Params = []
    Tangents = []
    FirstUv = []
    SecondUv = []
    for Index in range(Count):
        Cursor = OffsetData + Index * 88
        Point = PointVector(DataValue, Cursor)
        Values = Struct.unpack_from(">8d", DataValue, Cursor + 24)
        Param = Struct.unpack_from(">d", DataValue, Cursor + 80)[0]
        TangentValues = Values[4:7]
        TangentLength = MathValue.sqrt(
            sum((ValueData * ValueData for ValueData in TangentValues))
        )
        if (
            Point is None
            or not all(
                (MathValue.isfinite(ValueData) for ValueData in (*Values, Param))
            )
            or abs(TangentLength - 1.0) > 1e-09
        ):
            return None
        Points.append(Point)
        Params.append(Param)
        Tangents.append(VectorThree(*TangentValues))
        FirstUv.append((Values[0], Values[2]))
        SecondUv.append((Values[1], Values[3]))
    if not IsOrderedChart(Points, Params):
        return None
    return (
        tuple(Points),
        tuple(Params),
        tuple(Tangents),
        (tuple(FirstUv), tuple(SecondUv)),
        EndValue,
    )


# this declaration exists because focused behavior needs one stable owner
def ParseCompactPts(
    DataValue: bytes, OffsetData: int, Count: int, BaseParam: float, BaseScale: float
) -> tuple[tuple[VectorThree, ...], tuple[float, ...], int] | None:
    EndValue = OffsetData + Count * 24
    if EndValue > len(DataValue):
        return None
    Points = tuple(
        (PointVector(DataValue, OffsetData + Index * 24) for Index in range(Count))
    )
    if any((Point is None for Point in Points)):
        return None
    TypedPoints = tuple((Point for Point in Points if Point is not None))
    Params = [BaseParam]
    for LeftValue, Right in zip(TypedPoints, TypedPoints[1:]):
        Chord = Distance(LeftValue, Right) * KLengthScale
        if Chord <= 0.0:
            return None
        Params.append(Params[-1] + Chord * BaseScale)
    if not IsOrderedChart(TypedPoints, tuple(Params)):
        return None
    return (TypedPoints, tuple(Params), EndValue)


# this declaration exists because focused behavior needs one stable owner
def IsOrderedChart(Points: Sequence[VectorThree], Params: Sequence[float]) -> bool:
    return (
        len(Points) >= 2
        and len(Points) == len(Params)
        and all((LeftValue < Right for LeftValue, Right in zip(Params, Params[1:])))
        and all(
            (
                Distance(LeftValue, Right) > 0.0
                for LeftValue, Right in zip(Points, Points[1:])
            )
        )
    )


# this declaration exists because focused behavior needs one stable owner
def ParseTermPayloa(DataValue: bytes, Start: int, OffsetData: int) -> TermRecord | None:
    Count = ReadUnsigned(DataValue, Start)
    Decoded = XmtData(DataValue, Start + 4)
    if Count is None or Decoded is None:
        return None
    AttrValue, Width = Decoded
    PayloadData = Start + 4 + Width
    if PayloadData + 26 > len(DataValue):
        return None
    FormBytes = DataValue[PayloadData : PayloadData + 2]
    if not (
        Count == 1
        and FormBytes == b"L?"
        or (Count == 2 and FormBytes in {b"TF", b"TS"})
    ):
        return None
    Point = PointVector(DataValue, PayloadData + 2)
    if AttrValue <= 1 or Point is None:
        return None
    EndValue = PayloadData + 26
    return TermRecord(
        AttrValue,
        Count,
        FormBytes.decode("ascii"),
        Point,
        OffsetData,
        DataValue[OffsetData:EndValue],
    )


# this declaration exists because focused behavior needs one stable owner
def ParseTermRecord(DataValue: bytes, OffsetData: int) -> TermRecord | None:
    Start = RecordStart(DataValue, OffsetData, 41)
    return ParseTermPayloa(DataValue, Start, OffsetData) if Start is not None else None


# this declaration exists because focused behavior needs one stable owner
def ParseSupportUv(
    DataValue: bytes, Start: int, OffsetData: int
) -> SupportUvRecord | None:
    Count = ReadUnsigned(DataValue, Start)
    Decoded = XmtData(DataValue, Start + 4)
    if Count is None or Count > 4096 or Decoded is None:
        return None
    AttrValue, Width = Decoded
    PayloadData = Start + 4 + Width
    if PayloadData >= len(DataValue):
        return None
    Marker = DataValue[PayloadData]
    Stride = 4 if Marker == 4 else 2
    if Marker not in {2, 3, 4} or Count < Stride * 2 or Count % Stride:
        return None
    ValuesOffset = PayloadData + 1
    EndValue = ValuesOffset + Count * 8
    if AttrValue <= 1 or EndValue > len(DataValue):
        return None
    Values = Struct.unpack_from(f">{Count}d", DataValue, ValuesOffset)
    if any((not MathValue.isfinite(ValueData) for ValueData in Values)):
        return None
    return SupportUvRecord(
        AttrValue, Marker, Values, OffsetData, DataValue[OffsetData:EndValue]
    )


# this declaration exists because focused behavior needs one stable owner
def ParseSupportRec(DataValue: bytes, OffsetData: int) -> SupportUvRecord | None:
    Start = RecordStart(DataValue, OffsetData, 204)
    return ParseSupportUv(DataValue, Start, OffsetData) if Start is not None else None


# this declaration exists because focused behavior needs one stable owner
def ParseCompactUv(DataValue: bytes, OffsetData: int) -> CompactUvRecord | None:
    if OffsetData < 0 or OffsetData + 5 > len(DataValue) or DataValue[OffsetData] != 0:
        return None
    Count = DataValue[OffsetData + 1]
    Start = OffsetData + 2
    Decoded = XmtData(DataValue, Start)
    if Decoded is None:
        return None
    AttrValue, Width = Decoded
    MarkerOffset = Start + Width
    if AttrValue <= 1 or MarkerOffset >= len(DataValue):
        return None
    Marker = DataValue[MarkerOffset]
    Stride = 4 if Marker == 4 else 2
    ValuesOffset = MarkerOffset + 1
    EndValue = ValuesOffset + Count * 8
    if (
        Marker not in {2, 3, 4}
        or Count < Stride * 2
        or Count % Stride
        or (EndValue > len(DataValue))
    ):
        return None
    Values = Struct.unpack_from(f">{Count}d", DataValue, ValuesOffset)
    if any((not MathValue.isfinite(ValueData) for ValueData in Values)):
        return None
    return CompactUvRecord(
        AttrValue, Marker, Values, OffsetData, DataValue[OffsetData:EndValue]
    )


# this declaration exists because focused behavior needs one stable owner
def SupportUvLanes(
    Marker: int, Values: Sequence[float]
) -> tuple[tuple[tuple[float, float], ...], ...] | None:
    Width = 4 if Marker == 4 else 2
    if len(Values) < Width * 2 or len(Values) % Width:
        return None
    First = tuple(
        ((Values[Index], Values[Index + 1]) for Index in range(0, len(Values), Width))
    )
    Second = (
        tuple(
            (
                (Values[Index + 2], Values[Index + 3])
                for Index in range(0, len(Values), 4)
            )
        )
        if Marker == 4
        else ()
    )
    return (First, Second)


# this declaration exists because focused behavior needs one stable owner
def ResolvedSuppUv(
    AttrValue: int,
    Records: Mapping[int, SupportUvRecord],
    CompactRecords: Mapping[int, CompactUvRecord],
) -> tuple[tuple[tuple[tuple[float, float], ...], ...], int, bytes] | None:
    if AttrValue <= 1:
        return (((), ()), 0, b"")
    Candidates = []
    Record = Records.get(AttrValue)
    if Record is not None:
        Lanes = SupportUvLanes(Record.marker, Record.values)
        if Lanes is not None:
            Candidates.append((Lanes, Record.marker, Record.raw))
    Compact = CompactRecords.get(AttrValue)
    if Compact is not None:
        Lanes = SupportUvLanes(Compact.marker, Compact.values)
        if Lanes is not None:
            Candidates.append((Lanes, Compact.marker, Compact.raw))
    if not Candidates:
        return None
    First = Candidates[0]
    if any((Candidate[:2] != First[:2] for Candidate in Candidates[1:])):
        return None
    return First


# this declaration exists because focused behavior needs one stable owner
def ResolveInter(
    DataValue: bytes,
    Record: IntersectRecord,
    Charts: Mapping[int, ChartRecord],
    Terms: Mapping[int, TermRecord],
    SupportUv: Mapping[int, SupportUvRecord],
    CompactSupportUv: Mapping[int, CompactUvRecord],
    Surfaces: Mapping[int, object],
) -> IntersectionCurve | None:
    FirstSurf, SecondSurf, ChartId, StartId, EndId, UvIdValue = Record.references
    Chart = Charts.get(ChartId)
    First = Surfaces.get(FirstSurf)
    Second = Surfaces.get(SecondSurf)
    if Chart is None or First is None or Second is None or (FirstSurf == SecondSurf):
        return None
    Limits = InterLimits(StartId, EndId, Terms, Chart)
    if Limits is None:
        return None
    ResolvedUv = ResolvedSuppUv(UvIdValue, SupportUv, CompactSupportUv)
    if ResolvedUv is None:
        return None
    UvLanes, UvMarker, UvRaw = ResolvedUv
    TolValue = max(Chart.chordal_error, 1e-07)
    if not IsInterSurfFit((First, Second), Chart, UvLanes, TolValue):
        return None
    Attrs = FrozenMapping(
        {
            "base_parameter": Chart.base_parameter,
            "base_scale": Chart.base_scale,
            "chart_layout": Chart.layout,
            "chart_parameters": Chart.parameters,
            "chart_tangents": Chart.tangents,
            "chart_support_uv": Chart.support_uv,
            "support_uv": UvLanes,
            "support_uv_marker": UvMarker,
            "sense": Record.sense,
            "limit_forms": tuple((Limit.form for Limit in Limits)),
            "limit_points": tuple((Limit.point for Limit in Limits)),
            "chordal_error": Chart.chordal_error,
            "angular_error": Chart.angular_error,
            "parameter_errors": Chart.parameter_errors,
            "header_references": Record.header_references,
            "references": Record.references,
            "intersection_record": Record.raw,
            "chart_record": Chart.raw,
            "limit_records": tuple((Limit.raw for Limit in Limits)),
            "support_uv_record": UvRaw,
        }
    )
    return IntersectionCurve(
        NativeId("curve", Record.attribute),
        NativeId("surface", FirstSurf),
        NativeId("surface", SecondSurf),
        Chart.points,
        Chart.chordal_error,
        attributes=Attrs,
    )


# intersection limits validate optional endpoint records against sampled chart endpoints
def InterLimits(
    StartId: int, EndId: int, Terms: Mapping[int, TermRecord], Chart: ChartRecord
) -> tuple[TermRecord, ...] | None:
    if StartId == 1 and EndId == 1:
        return ()
    if StartId <= 1 or EndId <= 1:
        return None
    Start = Terms.get(StartId)
    EndValue = Terms.get(EndId)
    if Start is None or EndValue is None:
        return None
    TolValue = max(Chart.chordal_error, 1e-07)
    if Distance(Start.point, Chart.points[0]) > TolValue:
        return None
    if Distance(EndValue.point, Chart.points[-1]) > TolValue:
        return None
    return Start, EndValue


# intersection surface validation confirms every chart sample lies on both carriers
def IsInterSurfFit(
    Surfaces: Sequence[object],
    Chart: ChartRecord,
    UvLanes: Sequence[Sequence[tuple[float, float]]],
    TolValue: float,
) -> bool:
    for Index, SurfValue in enumerate(Surfaces):
        if isinstance(SurfValue, NurbsSurface):
            CandidateLanes = tuple(
                (
                    Lanes[Index]
                    for Lanes in (UvLanes, Chart.support_uv)
                    if Index < len(Lanes) and len(Lanes[Index]) == len(Chart.points)
                )
            )
            if not CandidateLanes:
                return False
            if not any(
                (
                    all(
                        (
                            (Residual := SurfResidual(SurfValue, Point, Params))
                            is not None
                            and Residual <= TolValue
                            for Point, Params in zip(Chart.points, LaneValue)
                        )
                    )
                    for LaneValue in CandidateLanes
                )
            ):
                return False
        else:
            Residuals = tuple(
                (SurfResidual(SurfValue, Point) for Point in Chart.points)
            )
            if any((Residual is None or Residual > TolValue for Residual in Residuals)):
                return False
    return True


# this declaration exists because focused behavior needs one stable owner
def NurbsBasis(
    Degree: int,
    Count: int,
    Knots: Sequence[float],
    Multiplicities: Sequence[int],
    Param: float,
    Periodic: bool,
) -> tuple[tuple[int, float], ...] | None:
    SpanData = NurbsSpanData(Degree, Count, Knots, Multiplicities, Param, Periodic)
    if SpanData is None:
        return None
    Expanded, Param, SpanValue = SpanData
    return CalcNurbsBasis(Degree, Expanded, Param, SpanValue)


# nurbs span selection validates the knot domain and normalizes periodic parameters
def NurbsSpanData(
    Degree: int,
    Count: int,
    Knots: Sequence[float],
    Multiplicities: Sequence[int],
    Param: float,
    Periodic: bool,
) -> tuple[tuple[float, ...], float, int] | None:
    if not MathValue.isfinite(Param):
        return None
    Expanded = tuple(
        (
            KnotValue
            for KnotValue, Multiplicity in zip(Knots, Multiplicities)
            for Ignored in range(Multiplicity)
        )
    )
    if len(Expanded) != Count + Degree + 1:
        return None
    Lower = Expanded[Degree]
    Upper = Expanded[Count]
    if not MathValue.isfinite(Lower) or not MathValue.isfinite(Upper) or Lower >= Upper:
        return None
    Epsilon = max(abs(Lower), abs(Upper), 1.0) * 1e-12
    if Periodic and (Param < Lower - Epsilon or Param > Upper + Epsilon):
        Param = Lower + (Param - Lower) % (Upper - Lower)
    elif Param < Lower - Epsilon or Param > Upper + Epsilon:
        return None
    Param = min(Upper, max(Lower, Param))
    if Param == Upper:
        SpanValue = Count - 1
    else:
        SpanValue = Degree
        while SpanValue + 1 < Count and Param >= Expanded[SpanValue + 1]:
            SpanValue += 1
    return Expanded, Param, SpanValue


# basis recurrence computes the nonzero functions for one validated knot span
def CalcNurbsBasis(
    Degree: int, Expanded: Sequence[float], Param: float, SpanValue: int
) -> tuple[tuple[int, float], ...] | None:
    Values = [0.0] * (Degree + 1)
    LeftValue = [0.0] * (Degree + 1)
    Right = [0.0] * (Degree + 1)
    Values[0] = 1.0
    for Column in range(1, Degree + 1):
        LeftValue[Column] = Param - Expanded[SpanValue + 1 - Column]
        Right[Column] = Expanded[SpanValue + Column] - Param
        Saved = 0.0
        for RowValue in range(Column):
            Denominator = Right[RowValue + 1] + LeftValue[Column - RowValue]
            Ratio = Values[RowValue] / Denominator if Denominator else 0.0
            Values[RowValue] = Saved + Right[RowValue + 1] * Ratio
            Saved = LeftValue[Column - RowValue] * Ratio
        Values[Column] = Saved
    Basis = tuple(
        (
            (SpanValue - Degree + Index, ValueData)
            for Index, ValueData in enumerate(Values)
            if ValueData != 0.0
        )
    )
    return Basis if Basis else None


# this declaration exists because focused behavior needs one stable owner
def NurbsCurvePoint(Curve: NurbsCurve, Param: float) -> VectorThree | None:
    Basis = NurbsBasis(
        Curve.degree,
        len(Curve.control_points),
        Curve.knots,
        Curve.multiplicities,
        Param,
        Curve.periodic,
    )
    if Basis is None:
        return None
    XValue = 0.0
    YValue = 0.0
    ZValue = 0.0
    Denominator = 0.0
    for Index, ValueData in Basis:
        Weight = Curve.weights[Index] if Curve.weights else 1.0
        Coefficient = ValueData * Weight
        Point = Curve.control_points[Index]
        Denominator += Coefficient
        XValue += Point.x * Coefficient
        YValue += Point.y * Coefficient
        ZValue += Point.z * Coefficient
    if not MathValue.isfinite(Denominator) or Denominator <= 0.0:
        return None
    Values = (XValue / Denominator, YValue / Denominator, ZValue / Denominator)
    return (
        VectorThree(*Values)
        if all((MathValue.isfinite(ValueData) for ValueData in Values))
        else None
    )


# this declaration exists because focused behavior needs one stable owner
def CurveParamRange(Curve: object) -> tuple[float, float, bool, bool] | None:
    if isinstance(Curve, (CircleCurve, EllipseCurve)):
        return (0.0, MathValue.tau, True, True)
    if isinstance(Curve, NurbsCurve):
        Expanded = tuple(
            (
                KnotValue
                for KnotValue, Multiplicity in zip(Curve.knots, Curve.multiplicities)
                for Ignored in range(Multiplicity)
            )
        )
        Count = len(Curve.control_points)
        if len(Expanded) != Count + Curve.degree + 1:
            return None
        Closed = Curve.attributes.get("closed", Curve.periodic)
        if type(Closed) is not bool:
            return None
        return (Expanded[Curve.degree], Expanded[Count], Curve.periodic, Closed)
    if isinstance(Curve, IntersectionCurve):
        Params = Curve.attributes.get("chart_parameters")
        if (
            not isinstance(Params, tuple)
            or len(Params) < 2
            or (
                not all(
                    (
                        type(ValueData) is float and MathValue.isfinite(ValueData)
                        for ValueData in Params
                    )
                )
            )
            or (
                not all(
                    (LeftValue < Right for LeftValue, Right in zip(Params, Params[1:]))
                )
            )
        ):
            return None
        return (Params[0], Params[-1], False, False)
    return None


# this declaration exists because focused behavior needs one stable owner
def CurvePoint(Curve: object, Param: float) -> VectorThree | None:
    if isinstance(Curve, LineCurve):
        return LinePoint(Curve, Param)
    if isinstance(Curve, (CircleCurve, EllipseCurve)):
        return ConicPoint(Curve, Param)
    if isinstance(Curve, NurbsCurve):
        return NurbsCurvePoint(Curve, Param)
    if isinstance(Curve, IntersectionCurve):
        Params = Curve.attributes.get("chart_parameters")
        if not isinstance(Params, tuple) or len(Params) != len(Curve.samples):
            return None
        TolValue = max(abs(Param), 1.0) * 1e-12
        Matches = tuple(
            (
                Point
                for ValueData, Point in zip(Params, Curve.samples)
                if type(ValueData) is float and abs(ValueData - Param) <= TolValue
            )
        )
        return Matches[0] if len(Matches) == 1 else None
    return None


# this declaration exists because focused behavior needs one stable owner
def NurbsSurfPoint(
    SurfValue: NurbsSurface, Params: tuple[float, float]
) -> VectorThree | None:
    RowsValue = SurfValue.control_points
    if not RowsValue or not RowsValue[0]:
        return None
    BasisU = NurbsBasis(
        SurfValue.degree_u,
        len(RowsValue),
        SurfValue.knots_u,
        SurfValue.multiplicities_u,
        Params[0],
        SurfValue.periodic_u,
    )
    BasisV = NurbsBasis(
        SurfValue.degree_v,
        len(RowsValue[0]),
        SurfValue.knots_v,
        SurfValue.multiplicities_v,
        Params[1],
        SurfValue.periodic_v,
    )
    if BasisU is None or BasisV is None:
        return None
    XValue = 0.0
    YValue = 0.0
    ZValue = 0.0
    Denominator = 0.0
    for UIndex, UValue in BasisU:
        for VIndex, VValue in BasisV:
            Weight = SurfValue.weights[UIndex][VIndex] if SurfValue.weights else 1.0
            Coefficient = UValue * VValue * Weight
            Point = RowsValue[UIndex][VIndex]
            Denominator += Coefficient
            XValue += Point.x * Coefficient
            YValue += Point.y * Coefficient
            ZValue += Point.z * Coefficient
    if not MathValue.isfinite(Denominator) or Denominator <= 0.0:
        return None
    Values = (XValue / Denominator, YValue / Denominator, ZValue / Denominator)
    return (
        VectorThree(*Values)
        if all((MathValue.isfinite(ValueData) for ValueData in Values))
        else None
    )


# this declaration exists because focused behavior needs one stable owner
def SurfResidual(
    SurfValue: object, Point: VectorThree, Params: tuple[float, float] | None = None
) -> float | None:
    if isinstance(SurfValue, PlaneSurface):
        return abs(DotProduct(Subtract(Point, SurfValue.origin), SurfValue.normal))
    if isinstance(SurfValue, NurbsSurface):
        Evaluated = NurbsSurfPoint(SurfValue, Params) if Params is not None else None
        return Distance(Evaluated, Point) if Evaluated is not None else None
    Center = SurfValue.center if hasattr(SurfValue, "center") else SurfValue.origin
    Difference = Subtract(Point, Center)
    if isinstance(SurfValue, SphereSurface):
        return abs(
            MathValue.sqrt(DotProduct(Difference, Difference)) - SurfValue.radius
        )
    if not isinstance(SurfValue, (CylinderSurface, ConeSurface, TorusSurface)):
        return None
    Axial = DotProduct(Difference, SurfValue.axis)
    RadialVector = VectorThree(
        Difference.x - Axial * SurfValue.axis.x,
        Difference.y - Axial * SurfValue.axis.y,
        Difference.z - Axial * SurfValue.axis.z,
    )
    Radial = MathValue.sqrt(DotProduct(RadialVector, RadialVector))
    if isinstance(SurfValue, CylinderSurface):
        return abs(Radial - SurfValue.radius)
    if isinstance(SurfValue, ConeSurface):
        return abs(
            Radial - (SurfValue.radius - Axial * MathValue.tan(SurfValue.half_angle))
        )
    return abs(
        MathValue.hypot(Radial - SurfValue.major_radius, Axial) - SurfValue.minor_radius
    )


# this declaration exists because focused behavior needs one stable owner
def RefsValue(DataValue: bytes, OffsetData: int, Count: int) -> tuple[int, ...] | None:
    if OffsetData < 0 or OffsetData + Count * 2 > len(DataValue):
        return None
    return Struct.unpack_from(f">{Count}H", DataValue, OffsetData)


# this declaration exists because focused behavior needs one stable owner
def TripledRefs(
    DataValue: bytes, OffsetData: int, Count: int, Prefix: bool = False
) -> tuple[int, ...] | None:
    Values = []
    for Index in range(Count):
        Position = OffsetData + Index * 3
        if Prefix:
            if Position + 3 > len(DataValue) or DataValue[Position] != 1:
                return None
            ValueData = ReadShort(DataValue, Position + 1)
        else:
            if Position + 3 > len(DataValue) or DataValue[Position + 2] != 1:
                return None
            ValueData = ReadShort(DataValue, Position)
        if ValueData is None:
            return None
        Values.append(ValueData)
    return tuple(Values)


# this declaration exists because focused behavior needs one stable owner
def ParseBridge(
    DataValue: bytes,
    OffsetData: int,
    AllowNullOwner: bool = False,
    AllowTolerance: bool = False,
) -> TopologyRecord | None:
    Start = RecordStart(DataValue, OffsetData, 14)
    if Start is None:
        return None
    AttrValue = ReadShort(DataValue, Start)
    Owner = ReadShort(DataValue, Start + 6)
    Tolerance = 0.0
    DirectTolerance = False
    if (
        DataValue[Start + 8 : Start + 9] == b"\x01"
        and DataValue[Start + 9 : Start + 17] == KEntityMagic
    ):
        RefsValueData = TripledRefs(DataValue, Start + 17, 5)
        MarkerOffset = Start + 32
    elif DataValue[Start + 8 : Start + 16] == KEntityMagic or (
        AllowTolerance
        and (Tolerance := ReadTolerance(DataValue, Start + 8)) is not None
        and (Tolerance > 0.0)
    ):
        DirectTolerance = DataValue[Start + 8 : Start + 16] != KEntityMagic
        Tripled = all(
            (
                DataValue[Start + 18 + Index * 3 : Start + 19 + Index * 3] == b"\x01"
                for Index in range(5)
            )
        )
        RefsValueData = (
            TripledRefs(DataValue, Start + 16, 5)
            if Tripled
            else RefsValue(DataValue, Start + 16, 5)
        )
        MarkerOffset = Start + (31 if Tripled else 26)
    else:
        return None
    if AttrValue is None or Owner is None or RefsValueData is None:
        return None
    if DirectTolerance and (
        len(RefsValueData) < 5
        or RefsValueData[2] <= 1
        or RefsValueData[3] <= 1
        or (RefsValueData[4] <= 1)
    ):
        return None
    if MarkerOffset >= len(DataValue) or DataValue[MarkerOffset] not in {43, 45}:
        return None
    if AttrValue <= 1 or (Owner <= 1 and (not AllowNullOwner)):
        return None
    Trailing = RefsValue(DataValue, MarkerOffset + 1, 5)
    if Trailing is not None:
        RefsValueData += Trailing
    return TopologyRecord(
        AttrValue,
        RefsValueData,
        OffsetData,
        DataValue[MarkerOffset] == 45,
        Owner,
        tolerance=Tolerance,
    )


# this declaration exists because focused behavior needs one stable owner
def ParseLoop(DataValue: bytes, OffsetData: int) -> TopologyRecord | None:
    Start = RecordStart(DataValue, OffsetData, 15)
    if Start is None:
        return None
    AttrValue = ReadShort(DataValue, Start)
    RefsValueData = TripledRefs(DataValue, Start + 6, 4) or RefsValue(
        DataValue, Start + 6, 4
    )
    if AttrValue is None or AttrValue <= 1 or RefsValueData is None:
        return None
    return TopologyRecord(AttrValue, RefsValueData, OffsetData)


# this declaration exists because focused behavior needs one stable owner
def ParseEdgeUse(
    DataValue: bytes, OffsetData: int, AllowTolerance: bool = False
) -> TopologyRecord | None:
    Start = RecordStart(DataValue, OffsetData, 16)
    if Start is None:
        return None
    AttrValue = ReadShort(DataValue, Start)
    Tolerance = (
        ReadTolerance(DataValue, Start + 8)
        if AllowTolerance or DataValue[Start + 8 : Start + 16] == KEntityMagic
        else None
    )
    if Tolerance == 0.0 and DataValue[Start + 8 : Start + 16] != KEntityMagic:
        Tolerance = None
    DirectTolerance = (
        Tolerance is not None and DataValue[Start + 8 : Start + 16] != KEntityMagic
    )
    if Tolerance is not None:
        RefsValueData = RefsValue(DataValue, Start + 16, 6)
    else:
        RefsValueData = EdgeMagicRefs(DataValue, Start)
    if AttrValue is None or AttrValue <= 1 or RefsValueData is None:
        return None
    if DirectTolerance and (
        len(RefsValueData) < 4 or RefsValueData[0] <= 1 or RefsValueData[3] <= 1
    ):
        return None
    return TopologyRecord(
        AttrValue, RefsValueData, OffsetData, tolerance=Tolerance or 0.0
    )


# edge magic decoding supports both observed short reference byte layouts
def EdgeMagicRefs(DataValue: bytes, Start: int) -> tuple[int, ...] | None:
    Magic = next(
        (
            Position
            for Position in range(
                Start + 9, min(Start + 17, len(DataValue) - len(KEntityMagic) + 1)
            )
            if DataValue[Position : Position + len(KEntityMagic)] == KEntityMagic
        ),
        None,
    )
    if Magic is None:
        return None
    Cursor = Magic + len(KEntityMagic)
    Decoded = []
    if Cursor < len(DataValue) and DataValue[Cursor] == 1:
        while (
            Cursor + 3 <= len(DataValue) and DataValue[Cursor] == 1 and len(Decoded) < 8
        ):
            ValueData = ReadShort(DataValue, Cursor + 1)
            if ValueData is None:
                return None
            Decoded.append(ValueData)
            Cursor += 3
    else:
        while (
            Cursor + 3 <= len(DataValue)
            and DataValue[Cursor + 2] == 1
            and len(Decoded) < 8
        ):
            ValueData = ReadShort(DataValue, Cursor)
            if ValueData is None:
                return None
            Decoded.append(ValueData)
            Cursor += 3
    return (0, 0, 0, Decoded[2], 0, 0) if len(Decoded) >= 3 else None


# this declaration exists because focused behavior needs one stable owner
def ParseCoedge(DataValue: bytes, OffsetData: int) -> TopologyRecord | None:
    Start = RecordStart(DataValue, OffsetData, 17)
    if Start is None:
        return None
    AttrValue = ReadShort(DataValue, Start)
    RefsValueData = RefsValue(DataValue, Start + 2, 9)
    MarkerOffset = Start + 20
    Marker = DataValue[MarkerOffset] if MarkerOffset < len(DataValue) else -1
    Isolated = (
        AttrValue is not None
        and RefsValueData is not None
        and (Marker == 63)
        and IsIsolatedFin(AttrValue, RefsValueData)
    )
    if RefsValueData is None or (Marker not in {43, 45} and (not Isolated)):
        RefsValueData = TripledRefs(DataValue, Start + 2, 9)
        MarkerOffset = Start + 29
        Marker = DataValue[MarkerOffset] if MarkerOffset < len(DataValue) else -1
        Isolated = (
            AttrValue is not None
            and RefsValueData is not None
            and (Marker == 63)
            and IsIsolatedFin(AttrValue, RefsValueData)
        )
    if AttrValue is None or AttrValue <= 1 or RefsValueData is None:
        return None
    if Marker not in {43, 45} and (not Isolated):
        return None
    return TopologyRecord(
        AttrValue, RefsValueData, OffsetData, Marker == 45, isolated=Isolated
    )


# this declaration exists because focused behavior needs one stable owner
def IsIsolatedFin(AttrValue: int, RefsValueData: tuple[int, ...]) -> bool:
    return (
        len(RefsValueData) == 9
        and RefsValueData[0] <= 1
        and (RefsValueData[1] > 1)
        and (RefsValueData[2] == AttrValue)
        and (RefsValueData[3] == AttrValue)
        and (RefsValueData[4] > 1)
        and all((RefsValueData[Index] <= 1 for Index in (5, 6, 7, 8)))
    )


# this declaration exists because focused behavior needs one stable owner
def ReadTolerance(DataValueData: bytes, Offset: int) -> float | None:
    if DataValueData[Offset : Offset + 8] == KEntityMagic:
        return 0.0
    if Offset < 0 or Offset + 8 > len(DataValueData):
        return None
    Value = Struct.unpack_from(">d", DataValueData, Offset)[0]
    if (
        not MathValue.isfinite(Value)
        or Value < 0.0
        or Value / KLengthScale > 10000.0
        or (Value != 0.0 and Value < FloatInfo.min)
    ):
        return None
    return Value / KLengthScale


# this declaration exists because focused behavior needs one stable owner
def ParseVertexUse(DataValue: bytes, OffsetData: int) -> TopologyRecord | None:
    Start = RecordStart(DataValue, OffsetData, 18)
    if Start is None:
        return None
    AttrValue = ReadShort(DataValue, Start)
    Tolerance = ReadTolerance(DataValue, Start + 16)
    if Tolerance is not None:
        RefsValueData = RefsValue(DataValue, Start + 6, 5)
    else:
        RefsValueData = None
    if RefsValueData is None:
        Magic = next(
            (
                Position
                for Position in range(
                    Start + 21, min(Start + 33, len(DataValue) - len(KEntityMagic) + 1)
                )
                if DataValue[Position : Position + len(KEntityMagic)] == KEntityMagic
            ),
            None,
        )
        if Magic is None or (Magic - (Start + 6)) % 3:
            return None
        Count = (Magic - (Start + 6)) // 3
        if Count < 5:
            return None
        RefsValueData = TripledRefs(DataValue, Start + 6, Count)
        Tolerance = 0.0
    if (
        AttrValue is None
        or AttrValue <= 1
        or RefsValueData is None
        or (not RefsValueData)
        or (RefsValueData[0] > 1)
        or (len(RefsValueData) < 5)
        or (RefsValueData[4] <= 1)
        or (Tolerance is None)
    ):
        return None
    return TopologyRecord(AttrValue, RefsValueData, OffsetData, tolerance=Tolerance)


# this declaration exists because focused behavior needs one stable owner
def PointRecoFiel(
    DataValue: bytes, OffsetData: int, Prefixed: bool = False
) -> tuple[int, tuple[int, ...], int] | None:
    Start = RecordStart(DataValue, OffsetData, 29)
    if Start is None or Start + 38 > len(DataValue):
        return None
    AttrValue = ReadShort(DataValue, Start)
    if Prefixed:
        Values = []
        Cursor = Start + 6
        while (
            Cursor + 3 <= len(DataValue)
            and DataValue[Cursor + 2] == 1
            and (len(Values) < 16)
        ):
            ValueData = ReadShort(DataValue, Cursor)
            if ValueData is None:
                return None
            Values.append(ValueData)
            Cursor += 3
        if not Values:
            return None
        RefsValueData = tuple(Values)
        ValuesOffset = Cursor
    else:
        RefsValueData = RefsValue(DataValue, Start + 6, 4)
        ValuesOffset = Start + 14
    if AttrValue is None or AttrValue <= 1 or RefsValueData is None:
        return None
    if not RefsValueData or RefsValueData[0] > 1:
        return None
    if ValuesOffset + 24 > len(DataValue):
        return None
    return (AttrValue, RefsValueData, ValuesOffset)


# this declaration exists because focused behavior needs one stable owner
def ParsePoint(
    DataValue: bytes, OffsetData: int, Prefixed: bool = False
) -> TopologyRecord | None:
    Fields = PointRecoFiel(DataValue, OffsetData, Prefixed)
    if Fields is None:
        return None
    AttrValue, RefsValueData, ValuesOffset = Fields
    Values = Struct.unpack_from(">3d", DataValue, ValuesOffset)
    if any(
        (
            not MathValue.isfinite(ValueData) or abs(ValueData) > 10000
            for ValueData in Values
        )
    ):
        return None
    return TopologyRecord(
        AttrValue,
        RefsValueData,
        OffsetData,
        point=VectorThree(*(ValueData / KLengthScale for ValueData in Values)),
    )


# this constant exists because binary encoding requires stable protocol data
KAnalyticValueCounts = {30: 6, 31: 10, 32: 11, 50: 9, 51: 10, 52: 12, 53: 10, 54: 11}


# this declaration exists because focused behavior needs one stable owner
def AnalyticFields(
    DataValue: bytes, OffsetData: int
) -> tuple[int, int, int, int] | None:
    if OffsetData < 0 or OffsetData + 2 > len(DataValue):
        return None
    KindValueData = DataValue[OffsetData + 1]
    ValueCount = KAnalyticValueCounts.get(KindValueData)
    if ValueCount is None:
        return None
    Start = RecordStart(DataValue, OffsetData, KindValueData)
    if Start is None:
        return None
    AttrValue = ReadShort(DataValue, Start)
    MarkerOffset = Start + 16
    if MarkerOffset >= len(DataValue) or DataValue[MarkerOffset] not in {43, 45}:
        MarkerOffset = next(
            (
                Position
                for Position in range(Start + 8, min(Start + 64, len(DataValue)))
                if DataValue[Position] in {43, 45}
                and Position > 0
                and (DataValue[Position - 1] == 1)
            ),
            -1,
        )
        if MarkerOffset < 0:
            return None
    ValuesOffset = MarkerOffset + 1
    ValuesEnd = ValuesOffset + ValueCount * 8
    if AttrValue is None or AttrValue <= 1 or ValuesEnd > len(DataValue):
        return None
    if DataValue[MarkerOffset] not in {43, 45}:
        return None
    return (AttrValue, ValuesOffset, ValuesEnd, MarkerOffset)


# this declaration exists because focused behavior needs one stable owner
def ParseCarrier(DataValue: bytes, OffsetData: int) -> tuple[int, object] | None:
    KindValueData = DataValue[OffsetData + 1]
    ValueCount = KAnalyticValueCounts[KindValueData]
    Fields = AnalyticFields(DataValue, OffsetData)
    if Fields is None:
        return None
    AttrValue, ValuesOffset, ValuesEnd, MarkerOffset = Fields
    Values = Struct.unpack_from(f">{ValueCount}d", DataValue, ValuesOffset)
    if any(
        (
            not MathValue.isfinite(ValueData) or abs(ValueData) > 1000000
            for ValueData in Values
        )
    ):
        return None
    IdValue = NativeId("curve" if KindValueData < 50 else "surface", AttrValue)
    GeomValue = AnalyticGeom(KindValueData, IdValue, Values)
    if GeomValue is not None:
        GeomValue = Replace(
            GeomValue,
            attributes=FrozenMapping(
                {
                    "sense": DataValue[MarkerOffset] == 43,
                    "carrier_record": DataValue[OffsetData:ValuesEnd],
                }
            ),
        )
    return (AttrValue, GeomValue) if GeomValue is not None else None


# this declaration exists because focused behavior needs one stable owner
def AnalyticGeom(
    KindValueData: int, IdValue: str, Values: tuple[float, ...]
) -> object | None:
    if KindValueData == 30:
        Tangent = AnalyticDirect(Values, 3)
        return (
            LineCurve(IdValue, AnalyticPoint(Values), Tangent)
            if Tangent is not None
            else None
        )
    if KindValueData in {31, 32, 50}:
        return RoundAnalytic(KindValueData, IdValue, Values)
    if KindValueData == 51:
        return CylinderGeom(IdValue, Values)
    if KindValueData == 52:
        return ConeGeom(IdValue, Values)
    if KindValueData == 53:
        return SphereGeom(IdValue, Values)
    if KindValueData == 54:
        return TorusGeom(IdValue, Values)
    return None


# analytic point conversion restores model units from encoded parasolid coordinates
def AnalyticPoint(Values: Sequence[float], Index: int = 0) -> VectorThree:
    return VectorThree(
        Values[Index] / KLengthScale,
        Values[Index + 1] / KLengthScale,
        Values[Index + 2] / KLengthScale,
    )


# analytic direction conversion validates encoded unit vectors before construction
def AnalyticDirect(Values: Sequence[float], Index: int) -> VectorThree | None:
    ValueData = VectorThree(Values[Index], Values[Index + 1], Values[Index + 2])
    return ValidDirect(ValueData)


# round analytic construction shares axis validation across circles ellipses and planes
def RoundAnalytic(
    KindValueData: int, IdValue: str, Values: tuple[float, ...]
) -> object | None:
    AxisValue = AnalyticDirect(Values, 3)
    RefValue = AnalyticDirect(Values, 6)
    if AxisValue is None or RefValue is None or not IsOrthogonal(AxisValue, RefValue):
        return None
    if KindValueData == 31 and Values[9] > 0:
        return CircleCurve(
            IdValue,
            AnalyticPoint(Values),
            AxisValue,
            RefValue,
            Values[9] / KLengthScale,
        )
    if KindValueData == 32 and Values[9] >= Values[10] > 0:
        return EllipseCurve(
            IdValue,
            AnalyticPoint(Values),
            AxisValue,
            RefValue,
            Values[9] / KLengthScale,
            Values[10] / KLengthScale,
        )
    if KindValueData == 50:
        return PlaneSurface(IdValue, AnalyticPoint(Values), AxisValue, RefValue)
    return None


# cylinder construction validates its orthogonal frame and positive radius
def CylinderGeom(IdValue: str, Values: tuple[float, ...]) -> CylinderSurface | None:
    AxisValue = AnalyticDirect(Values, 3)
    RefValue = AnalyticDirect(Values, 7)
    if (
        AxisValue is None
        or RefValue is None
        or not IsOrthogonal(AxisValue, RefValue)
        or Values[6] <= 0
    ):
        return None
    return CylinderSurface(
        IdValue, AnalyticPoint(Values), AxisValue, RefValue, Values[6] / KLengthScale
    )


# cone construction validates its frame radius and normalized angular components
def ConeGeom(IdValue: str, Values: tuple[float, ...]) -> ConeSurface | None:
    AxisValue = AnalyticDirect(Values, 3)
    RefValue = AnalyticDirect(Values, 9)
    SineValue, Cosine = Values[7:9]
    if (
        AxisValue is None
        or RefValue is None
        or not IsOrthogonal(AxisValue, RefValue)
        or Values[6] < 0
    ):
        return None
    if (
        SineValue == 0
        or Cosine <= 0
        or abs(SineValue * SineValue + Cosine * Cosine - 1.0) > 1e-09
    ):
        return None
    return ConeSurface(
        IdValue,
        AnalyticPoint(Values),
        AxisValue,
        RefValue,
        Values[6] / KLengthScale,
        MathValue.asin(SineValue),
    )


# sphere construction validates its oriented frame and positive radius
def SphereGeom(IdValue: str, Values: tuple[float, ...]) -> SphereSurface | None:
    AxisValue = AnalyticDirect(Values, 4)
    RefValue = AnalyticDirect(Values, 7)
    if (
        AxisValue is None
        or RefValue is None
        or not IsOrthogonal(AxisValue, RefValue)
        or Values[3] <= 0
    ):
        return None
    return SphereSurface(
        IdValue, AnalyticPoint(Values), AxisValue, RefValue, Values[3] / KLengthScale
    )


# torus construction validates its frame and nondegenerate radii
def TorusGeom(IdValue: str, Values: tuple[float, ...]) -> TorusSurface | None:
    AxisValue = AnalyticDirect(Values, 3)
    RefValue = AnalyticDirect(Values, 8)
    if AxisValue is None or RefValue is None or not IsOrthogonal(AxisValue, RefValue):
        return None
    if Values[6] == 0 or Values[7] <= 0:
        return None
    return TorusSurface(
        IdValue,
        AnalyticPoint(Values),
        AxisValue,
        RefValue,
        abs(Values[6]) / KLengthScale,
        Values[7] / KLengthScale,
    )


# this declaration exists because focused behavior needs one stable owner
def ValidDirect(ValueData: VectorThree) -> VectorThree | None:
    Length = MathValue.sqrt(
        ValueData.x * ValueData.x
        + ValueData.y * ValueData.y
        + ValueData.z * ValueData.z
    )
    if not MathValue.isfinite(Length) or abs(Length - 1.0) > 1e-09:
        return None
    return VectorThree(ValueData.x / Length, ValueData.y / Length, ValueData.z / Length)


# this declaration exists because focused behavior needs one stable owner
def IsOrthogonal(LeftValue: VectorThree, Right: VectorThree) -> bool:
    return (
        abs(LeftValue.x * Right.x + LeftValue.y * Right.y + LeftValue.z * Right.z)
        <= 1e-09
    )


# this declaration exists because focused behavior needs one stable owner
def ParseEntity(DataValue: bytes, OffsetData: int) -> EntityRecord | None:
    Start = RecordStart(DataValue, OffsetData, 81)
    if Start is None:
        return None
    Flags = ReadUnsigned(DataValue, Start)
    AttrValue = ReadShort(DataValue, Start + 4)
    SeqValue = ReadUnsigned(DataValue, Start + 6)
    KindValue = ReadShort(DataValue, Start + 10)
    RefsValueData = RefsValue(DataValue, Start + 12, 6)
    if (
        Flags not in {1, 2}
        or AttrValue is None
        or AttrValue <= 1
        or (SeqValue != 1)
        or (KindValue is None)
        or (RefsValueData is None)
    ):
        return None
    return EntityRecord(Flags, AttrValue, KindValue, RefsValueData, OffsetData)


# this declaration exists because focused behavior needs one stable owner
def LinkedOrder(
    Attrs: Iterable[int], Links: Mapping[int, tuple[int, int]]
) -> tuple[int, ...]:
    Selected = set(Attrs)
    Linked = Selected.intersection(Links)
    if not Linked:
        return tuple(sorted(Selected))
    OrderData: list[int] = []
    Visited: set[int] = set()
    Heads = sorted(
        (
            AttrValue
            for AttrValue, (Ignored, Previous) in Links.items()
            if Previous <= 1 or Previous not in Links
        )
    )
    for HeadValue in Heads:
        AttrValue = HeadValue
        Previous = 0
        Component: set[int] = set()
        while AttrValue > 1 and AttrValue in Links:
            if AttrValue in Component or AttrValue in Visited:
                break
            NextAttrData, PreviousAttr = Links[AttrValue]
            if Previous and PreviousAttr != Previous:
                break
            Component.add(AttrValue)
            Visited.add(AttrValue)
            OrderData.append(AttrValue)
            Previous = AttrValue
            AttrValue = NextAttrData
    Result = tuple((AttrValue for AttrValue in OrderData if AttrValue in Linked))
    if len(Result) != len(Linked):
        Result = tuple(sorted(Linked))
    return Result + tuple(sorted(Selected - Linked))


# this declaration exists because focused behavior needs one stable owner
def GeomChainLinks(Values: Mapping[int, object]) -> dict[int, tuple[int, int]]:
    Result: dict[int, tuple[int, int]] = {}
    for AttrValue, GeomValue in Values.items():
        Attrs = getattr(GeomValue, "attributes", {})
        Header = Attrs.get("header_references")
        if (
            isinstance(Header, tuple)
            and len(Header) >= 4
            and all((type(ValueData) is int for ValueData in Header[:4]))
        ):
            Result[AttrValue] = (Header[3], Header[2])
            continue
        RawData = Attrs.get("carrier_record")
        if not isinstance(RawData, bytes) or len(RawData) < 16:
            continue
        NextAttrData = ReadShort(RawData, 12)
        PreviousAttr = ReadShort(RawData, 14)
        if NextAttrData is not None and PreviousAttr is not None:
            Result[AttrValue] = (NextAttrData, PreviousAttr)
    return Result


# this declaration exists because focused behavior needs one stable owner
def FinDescriptor(
    AttrValue: int, UsedCoedges: set[int], UsedEdges: set[int], Tables: RecordTables
) -> tuple[str, str] | None:
    if AttrValue in UsedCoedges:
        return ("coedge", NativeId("coedge", AttrValue))
    FinRecord = Tables.coedges.get(AttrValue)
    if FinRecord is None or FinRecord.references[6] not in UsedEdges:
        return None
    return ("dummy", NativeId("edge", FinRecord.references[6]))


# this declaration exists because focused behavior needs one stable owner
def VertexFinOrder(
    VertexAttr: int,
    FirstAttr: int,
    UsedCoedges: set[int],
    UsedEdges: set[int],
    Tables: RecordTables,
) -> tuple[tuple[str, str], ...]:
    Result: list[tuple[str, str]] = []
    SeenValue: set[int] = set()
    AttrValue = FirstAttr
    while AttrValue > 1:
        if AttrValue in SeenValue:
            return ()
        SeenValue.add(AttrValue)
        FinRecord = Tables.coedges.get(AttrValue)
        if FinRecord is None or FinRecord.references[4] != VertexAttr:
            return ()
        Descriptor = FinDescriptor(AttrValue, UsedCoedges, UsedEdges, Tables)
        if Descriptor is None:
            return ()
        Result.append(Descriptor)
        AttrValue = FinRecord.references[8]
    return tuple(Result)


# part model construction composes independently validated topology and geometry phases
def BuildPartModel(
    Tables: RecordTables,
    SolidUnchangedIds: Mapping[int, int] | None = None,
    SolidAttrOrders: Mapping[str, Mapping[int, int]] | None = None,
) -> BrepModel:
    UnchangedIds, AttrOrders = SolidUnchangedIds or {}, SolidAttrOrders or {}
    TopoData = CollectPartTopo(Tables)
    (
        FaceLoops,
        EdgeEndpoints,
        EdgeCurves,
        CoedgeEdges,
        UsedCoedges,
        UsedEdges,
        UsedVertices,
        UsedCurves,
        UsedSurfaces,
        SyntheticVertices,
        SyntheticCurves,
        OwnerFaces,
    ) = TopoData
    RankData = MakePartRanks(Tables, FaceLoops, UsedEdges, UsedVertices, UsedCurves)
    (
        FaceOrder,
        FaceSurfOrder,
        FaceFrontOrder,
        EdgeOrder,
        CurveEdgeOrder,
        VertexOrder,
        CurveOrder,
        FaceRanks,
        FaceSurfRanks,
        FaceFrontRanks,
        EdgeRanks,
        CurveEdgeRanks,
        VertexRanks,
        CurveRanks,
    ) = RankData
    PointData = VertexPointData(Tables, VertexOrder, SyntheticVertices)
    PointsByVertex, PointAttrs, VertexTolerances, PointRanks = PointData
    Vertices = MakeVertices(
        Tables,
        VertexOrder,
        SyntheticVertices,
        PointsByVertex,
        PointAttrs,
        VertexTolerances,
        VertexRanks,
        PointRanks,
        UsedCoedges,
        UsedEdges,
    )
    Curves = MakePartCurves(Tables, CurveOrder, SyntheticCurves, CurveRanks)
    AddCurveSurfMut(Curves, Tables, UsedSurfaces)
    SurfOrder = LinkedOrder(UsedSurfaces, GeomChainLinks(Tables.surfaces))
    SurfRanks = {AttrValue: RankValue for RankValue, AttrValue in enumerate(SurfOrder)}
    Edges = MakePartEdges(
        Tables,
        EdgeOrder,
        EdgeEndpoints,
        EdgeCurves,
        SyntheticCurves,
        PointsByVertex,
        VertexTolerances,
        EdgeRanks,
        CurveEdgeRanks,
        UsedCoedges,
        UsedEdges,
    )
    Coedges = tuple(
        (
            BrepCoedge(
                NativeId("coedge", AttrValue),
                NativeId("edge", CoedgeEdges[AttrValue]),
                reversed=Tables.coedges[AttrValue].reversed,
            )
            for AttrValue in sorted(UsedCoedges)
        )
    )
    OuterLoops = FindOuterLoops(FaceLoops, Tables)
    Loops = MakePartLoops(FaceLoops, OuterLoops)
    Surfaces = MakePartSurfs(Tables, SurfOrder, SurfRanks)
    Faces = MakePartFaces(
        Tables,
        FaceLoops,
        FaceOrder,
        FaceRanks,
        FaceSurfRanks,
        FaceFrontRanks,
        UnchangedIds,
        AttrOrders,
    )
    FaceUses, Shells, ShellUses, Regions, Bodies = BuildTreeModel(
        Tables, OwnerFaces, FaceLoops, FaceRanks
    )
    return BrepModel(
        curves=Curves,
        surfaces=Surfaces,
        vertices=Vertices,
        edges=Edges,
        coedges=Coedges,
        loops=Loops,
        faces=Faces,
        face_uses=FaceUses,
        shells=Shells,
        shell_uses=ShellUses,
        regions=Regions,
        bodies=Bodies,
    )


# topology collection gathers every reachable face edge vertex and carrier identifier
def CollectPartTopo(Tables: RecordTables) -> tuple[object, ...]:
    FaceLoops, EdgeEndpoints, EdgeCurves, CoedgeEdges = {}, {}, {}, {}
    UsedCoedges, UsedEdges, UsedVertices, UsedCurves, UsedSurfaces = (
        set(),
        set(),
        set(),
        set(),
        set(),
    )
    SyntheticVertices, SyntheticCurves, OwnerFaces = {}, {}, {}
    for BridgeAttr, Bridge in sorted(Tables.bridges.items()):
        AddBridgeMut(
            BridgeAttr,
            Bridge,
            Tables,
            FaceLoops,
            EdgeEndpoints,
            EdgeCurves,
            CoedgeEdges,
            UsedCoedges,
            UsedEdges,
            UsedVertices,
            UsedCurves,
            UsedSurfaces,
            SyntheticVertices,
            SyntheticCurves,
            OwnerFaces,
        )
    if set(Tables.bridges) != set(FaceLoops):
        raise ValueError("partial face topology")
    return (
        FaceLoops,
        EdgeEndpoints,
        EdgeCurves,
        CoedgeEdges,
        UsedCoedges,
        UsedEdges,
        UsedVertices,
        UsedCurves,
        UsedSurfaces,
        SyntheticVertices,
        SyntheticCurves,
        OwnerFaces,
    )


# bridge collection validates face ownership surface resolution and boundary rings
def AddBridgeMut(
    BridgeAttr: int,
    Bridge: TopologyRecord,
    Tables: RecordTables,
    FaceLoops: dict[int, object],
    EdgeEndpoints: dict[int, tuple[int, int]],
    EdgeCurves: dict[int, int],
    CoedgeEdges: dict[int, int],
    UsedCoedges: set[int],
    UsedEdges: set[int],
    UsedVertices: set[int],
    UsedCurves: set[int],
    UsedSurfaces: set[int],
    SyntheticVertices: dict[int, VectorThree],
    SyntheticCurves: dict[int, NativeCurve],
    OwnerFaces: dict[int, int],
) -> None:
    if Bridge.owner > 1:
        if Bridge.owner in OwnerFaces:
            raise ValueError("ambiguous face owner")
        OwnerFaces[Bridge.owner] = BridgeAttr
    SurfAttr = Bridge.references[4]
    if SurfAttr not in Tables.surfaces:
        raise ValueError("unresolved face surface")
    UsedSurfaces.add(SurfAttr)
    Loops = GetFaceLoops(Tables, BridgeAttr, Bridge)
    FaceLoops[BridgeAttr] = tuple(Loops)
    for Ignored, RingValue in Loops:
        for CoedgeAttr in RingValue:
            AddCoedgeMut(
                CoedgeAttr,
                RingValue,
                Tables,
                EdgeEndpoints,
                EdgeCurves,
                CoedgeEdges,
                UsedCoedges,
                UsedEdges,
                UsedVertices,
                UsedCurves,
                SyntheticVertices,
                SyntheticCurves,
            )


# face loop traversal validates linked ownership and rejects cyclic boundaries
def GetFaceLoops(
    Tables: RecordTables, BridgeAttr: int, Bridge: TopologyRecord
) -> list[tuple[int, tuple[int, ...]]]:
    LoopAttr = Bridge.references[2]
    Loops: list[tuple[int, tuple[int, ...]]] = []
    LoopGuard: set[int] = set()
    while LoopAttr > 1:
        if LoopAttr in LoopGuard:
            raise ValueError("cyclic loop list")
        LoopGuard.add(LoopAttr)
        LoopData = Tables.loops.get(LoopAttr)
        if LoopData is None or LoopData.references[2] != BridgeAttr:
            raise ValueError("invalid loop owner")
        RingValue = WalkCoedgeRing(Tables, LoopAttr, LoopData.references[1])
        Loops.append((LoopAttr, RingValue))
        LoopAttr = LoopData.references[3]
    if not Loops:
        raise ValueError("face boundary is absent")
    return Loops


# coedge collection dispatches isolated and dimensional topology representations
def AddCoedgeMut(
    CoedgeAttr: int,
    RingValue: Sequence[int],
    Tables: RecordTables,
    EdgeEndpoints: dict[int, tuple[int, int]],
    EdgeCurves: dict[int, int],
    CoedgeEdges: dict[int, int],
    UsedCoedges: set[int],
    UsedEdges: set[int],
    UsedVertices: set[int],
    UsedCurves: set[int],
    SyntheticVertices: dict[int, VectorThree],
    SyntheticCurves: dict[int, NativeCurve],
) -> None:
    Coedge = Tables.coedges[CoedgeAttr]
    if Coedge.isolated:
        AddIsolatedMut(
            Coedge,
            RingValue,
            EdgeEndpoints,
            EdgeCurves,
            CoedgeEdges,
            UsedCoedges,
            UsedEdges,
            UsedVertices,
            UsedCurves,
            SyntheticCurves,
        )
        return
    AddNormalMut(
        Coedge,
        Tables,
        EdgeEndpoints,
        EdgeCurves,
        CoedgeEdges,
        UsedCoedges,
        UsedEdges,
        UsedVertices,
        UsedCurves,
        SyntheticVertices,
    )


# isolated coedge collection creates deterministic synthetic edge and curve identifiers
def AddIsolatedMut(
    Coedge: TopologyRecord,
    RingValue: Sequence[int],
    EdgeEndpoints: dict[int, tuple[int, int]],
    EdgeCurves: dict[int, int],
    CoedgeEdges: dict[int, int],
    UsedCoedges: set[int],
    UsedEdges: set[int],
    UsedVertices: set[int],
    UsedCurves: set[int],
    SyntheticCurves: dict[int, NativeCurve],
) -> None:
    if len(RingValue) != 1 or not IsIsolatedFin(Coedge.attribute, Coedge.references):
        raise ValueError("invalid isolated vertex loop")
    EdgeAttr = 65536 + Coedge.attribute
    VertexAttr = Coedge.references[4]
    EdgeEndpoints[EdgeAttr] = (VertexAttr, VertexAttr)
    EdgeCurves[EdgeAttr] = EdgeAttr
    CoedgeEdges[Coedge.attribute] = EdgeAttr
    SyntheticCurves[EdgeAttr] = NativeCurve(
        NativeId("curve", EdgeAttr), "parasolid.xt", "isolated-vertex-loop"
    )
    UsedCoedges.add(Coedge.attribute)
    UsedEdges.add(EdgeAttr)
    UsedVertices.add(VertexAttr)
    UsedCurves.add(EdgeAttr)


# dimensional coedge collection enforces consistent edge orientation and carrier identity
def AddNormalMut(
    Coedge: TopologyRecord,
    Tables: RecordTables,
    EdgeEndpoints: dict[int, tuple[int, int]],
    EdgeCurves: dict[int, int],
    CoedgeEdges: dict[int, int],
    UsedCoedges: set[int],
    UsedEdges: set[int],
    UsedVertices: set[int],
    UsedCurves: set[int],
    SyntheticVertices: dict[int, VectorThree],
) -> None:
    EdgeAttr = Coedge.references[6]
    StartVertex, EndVertex, CurveAttr = GetEdgeUseMut(
        Tables, Coedge, EdgeAttr, SyntheticVertices
    )
    Canonical = (
        (EndVertex, StartVertex) if Coedge.reversed else (StartVertex, EndVertex)
    )
    Previous = EdgeEndpoints.setdefault(EdgeAttr, Canonical)
    if Previous != Canonical:
        raise ValueError("inconsistent edge orientation")
    PreviousCurve = EdgeCurves.setdefault(EdgeAttr, CurveAttr)
    if PreviousCurve != CurveAttr:
        raise ValueError("inconsistent edge curve")
    CoedgeEdges[Coedge.attribute] = EdgeAttr
    UsedCoedges.add(Coedge.attribute)
    UsedEdges.add(EdgeAttr)
    UsedVertices.update(Canonical)
    UsedCurves.add(CurveAttr)


# edge use resolution validates opposite fins carriers and closed conic vertices
def GetEdgeUseMut(
    Tables: RecordTables,
    Coedge: TopologyRecord,
    EdgeAttr: int,
    SyntheticVertices: dict[int, VectorThree],
) -> tuple[int, int, int]:
    StartVertex = Coedge.references[4]
    OtherCoedge = Tables.coedges.get(Coedge.references[5])
    if OtherCoedge is None:
        raise ValueError("missing opposite coedge")
    EndVertex = OtherCoedge.references[4]
    if EdgeAttr <= 1:
        raise ValueError("incomplete coedge topology")
    EdgeUseData = Tables.edge_uses.get(EdgeAttr)
    if EdgeUseData is None:
        raise ValueError("missing edge use")
    CurveAttr = EdgeUseData.references[3]
    Curve = Tables.curves.get(CurveAttr)
    if Curve is None:
        raise ValueError("unresolved edge curve")
    if StartVertex <= 1 or EndVertex <= 1:
        if not (
            StartVertex <= 1
            and EndVertex <= 1
            and isinstance(Curve, (CircleCurve, EllipseCurve))
        ):
            raise ValueError("incomplete coedge topology")
        Synthetic = 65536 + EdgeAttr
        SyntheticVertices[Synthetic] = ConicPoint(Curve, 0.0)
        StartVertex, EndVertex = Synthetic, Synthetic
    return StartVertex, EndVertex, CurveAttr


# ranking reconstruction preserves every native linked list ordering dimension
def MakePartRanks(
    Tables: RecordTables,
    FaceLoops: Mapping[int, object],
    UsedEdges: set[int],
    UsedVertices: set[int],
    UsedCurves: set[int],
) -> tuple[object, ...]:
    FaceOrder = LinkedOrder(
        FaceLoops,
        {
            AttrValue: (Record.references[0], Record.references[1])
            for AttrValue, Record in Tables.bridges.items()
        },
    )
    FaceSurfOrder = LinkedOrder(
        FaceLoops,
        {
            AttrValue: (Record.references[5], Record.references[6])
            for AttrValue, Record in Tables.bridges.items()
            if len(Record.references) >= 7
        },
    )
    FaceFrontOrder = LinkedOrder(
        FaceLoops,
        {
            AttrValue: (Record.references[7], Record.references[8])
            for AttrValue, Record in Tables.bridges.items()
            if len(Record.references) >= 9
        },
    )
    EdgeOrder = LinkedOrder(
        UsedEdges,
        {
            AttrValue: (Record.references[2], Record.references[1])
            for AttrValue, Record in Tables.edge_uses.items()
        },
    )
    CurveEdgeOrder = LinkedOrder(
        UsedEdges,
        {
            AttrValue: (Record.references[4], Record.references[5])
            for AttrValue, Record in Tables.edge_uses.items()
        },
    )
    VertexOrder = LinkedOrder(
        UsedVertices,
        {
            AttrValue: (Record.references[3], Record.references[2])
            for AttrValue, Record in Tables.vertex_uses.items()
        },
    )
    CurveOrder = LinkedOrder(UsedCurves, GeomChainLinks(Tables.curves))
    Orders = (
        FaceOrder,
        FaceSurfOrder,
        FaceFrontOrder,
        EdgeOrder,
        CurveEdgeOrder,
        VertexOrder,
        CurveOrder,
    )
    Ranks = tuple(
        (
            {AttrValue: RankValue for RankValue, AttrValue in enumerate(OrderData)}
            for OrderData in Orders
        )
    )
    return (*Orders, *Ranks)


# vertex point recovery resolves synthetic and native points with their tolerances
def VertexPointData(
    Tables: RecordTables,
    VertexOrder: Sequence[int],
    SyntheticVertices: Mapping[int, VectorThree],
) -> tuple[dict[int, VectorThree], dict[int, int], dict[int, float], dict[int, int]]:
    PointsByVertex, PointAttrs, VertexTolerances, UsedPoints = {}, {}, {}, set()
    for VertexAttr in VertexOrder:
        if VertexAttr in SyntheticVertices:
            PointsByVertex[VertexAttr] = SyntheticVertices[VertexAttr]
            VertexTolerances[VertexAttr] = 0.0
            continue
        VertexUse = Tables.vertex_uses.get(VertexAttr)
        if VertexUse is None:
            raise ValueError("missing vertex use")
        PointAttr = VertexUse.references[4]
        PointRecord = Tables.points.get(PointAttr)
        if PointRecord is None or PointRecord.point is None:
            raise ValueError("missing vertex point")
        UsedPoints.add(PointAttr)
        PointAttrs[VertexAttr] = PointAttr
        PointsByVertex[VertexAttr] = PointRecord.point
        VertexTolerances[VertexAttr] = VertexUse.tolerance
    PointOrder = LinkedOrder(
        UsedPoints,
        {
            AttrValue: (Record.references[2], Record.references[3])
            for AttrValue, Record in Tables.points.items()
            if len(Record.references) >= 4
        },
    )
    PointRanks = {
        AttrValue: RankValue for RankValue, AttrValue in enumerate(PointOrder)
    }
    return PointsByVertex, PointAttrs, VertexTolerances, PointRanks


# vertex construction restores fin ordering metadata for every native vertex
def MakeVertices(
    Tables: RecordTables,
    VertexOrder: Sequence[int],
    SyntheticVertices: Mapping[int, VectorThree],
    PointsByVertex: Mapping[int, VectorThree],
    PointAttrs: Mapping[int, int],
    VertexTolerances: Mapping[int, float],
    VertexRanks: Mapping[int, int],
    PointRanks: Mapping[int, int],
    UsedCoedges: set[int],
    UsedEdges: set[int],
) -> tuple[BrepVertex, ...]:
    Vertices: list[BrepVertex] = []
    for VertexAttr in VertexOrder:
        if VertexAttr in SyntheticVertices:
            Attrs = FrozenMapping({"parasolid.vertex_order": VertexRanks[VertexAttr]})
            Vertices.append(
                BrepVertex(
                    NativeId("vertex", VertexAttr),
                    PointsByVertex[VertexAttr],
                    attributes=Attrs,
                )
            )
            continue
        VertexUse = Tables.vertex_uses[VertexAttr]
        PointAttr = PointAttrs[VertexAttr]
        Attrs: dict[str, object] = {
            "parasolid.vertex_order": VertexRanks[VertexAttr],
            "parasolid.point_order": PointRanks[PointAttr],
        }
        FinOrder = VertexFinOrder(
            VertexAttr, VertexUse.references[1], UsedCoedges, UsedEdges, Tables
        )
        if FinOrder:
            Attrs["parasolid.vertex_fins"] = FinOrder
        Vertices.append(
            BrepVertex(
                NativeId("vertex", VertexAttr),
                PointsByVertex[VertexAttr],
                tolerance=VertexUse.tolerance,
                attributes=FrozenMapping(Attrs),
            )
        )
    return tuple(Vertices)


# curve construction restores native order metadata on direct and synthetic carriers
def MakePartCurves(
    Tables: RecordTables,
    CurveOrder: Sequence[int],
    SyntheticCurves: Mapping[int, NativeCurve],
    CurveRanks: Mapping[int, int],
) -> tuple[object, ...]:
    Curves = []
    for AttrValue in CurveOrder:
        Curve = (
            Tables.curves[AttrValue]
            if AttrValue in Tables.curves
            else SyntheticCurves[AttrValue]
        )
        Attrs = FrozenMapping(
            {
                **dict(getattr(Curve, "attributes", {})),
                "parasolid.curve_order": CurveRanks[AttrValue],
            }
        )
        Curves.append(Replace(Curve, attributes=Attrs))
    return tuple(Curves)


# intersection support collection retains surfaces referenced only by resolved curves
def AddCurveSurfMut(
    Curves: Sequence[object], Tables: RecordTables, UsedSurfaces: set[int]
) -> None:
    for Curve in Curves:
        if not isinstance(Curve, IntersectionCurve):
            continue
        RefsValueData = Curve.attributes.get("references")
        if not isinstance(RefsValueData, tuple) or len(RefsValueData) < 2:
            raise ValueError("intersection support surfaces are unresolved")
        if any(
            (
                type(AttrValue) is not int or AttrValue not in Tables.surfaces
                for AttrValue in RefsValueData[:2]
            )
        ):
            raise ValueError("intersection support surfaces are unresolved")
        UsedSurfaces.update(RefsValueData[:2])


# edge construction proves parameter ranges and restores linked list metadata
def MakePartEdges(
    Tables: RecordTables,
    EdgeOrder: Sequence[int],
    EdgeEndpoints: Mapping[int, tuple[int, int]],
    EdgeCurves: Mapping[int, int],
    SyntheticCurves: Mapping[int, NativeCurve],
    PointsByVertex: Mapping[int, VectorThree],
    VertexTolerances: Mapping[int, float],
    EdgeRanks: Mapping[int, int],
    CurveEdgeRanks: Mapping[int, int],
    UsedCoedges: set[int],
    UsedEdges: set[int],
) -> tuple[BrepEdge, ...]:
    Edges: list[BrepEdge] = []
    for EdgeAttr in EdgeOrder:
        StartVertex, EndVertex = EdgeEndpoints[EdgeAttr]
        CurveAttr = EdgeCurves[EdgeAttr]
        Degenerate = CurveAttr in SyntheticCurves
        if Degenerate:
            StartParam, EndParam = 0.0, 0.0
        else:
            Curve = Tables.curves[CurveAttr]
            StartParam, EndParam = ProveCurveRange(
                Curve,
                PointsByVertex[StartVertex],
                PointsByVertex[EndVertex],
                VertexTolerances[StartVertex],
                VertexTolerances[EndVertex],
            )
        EdgeAttrs: dict[str, object] = {
            "parasolid.edge_order": EdgeRanks[EdgeAttr],
            "parasolid.curve_edge_order": CurveEdgeRanks[EdgeAttr],
        }
        if EdgeAttr in Tables.edge_uses:
            FirstFin = FinDescriptor(
                Tables.edge_uses[EdgeAttr].references[0], UsedCoedges, UsedEdges, Tables
            )
            if FirstFin is not None:
                EdgeAttrs["parasolid.first_fin"] = FirstFin
        EdgeUse = Tables.edge_uses.get(EdgeAttr)
        Tolerance = max(
            EdgeUse.tolerance if EdgeUse is not None else 0.0,
            VertexTolerances[StartVertex],
            VertexTolerances[EndVertex],
        )
        Edges.append(
            BrepEdge(
                NativeId("edge", EdgeAttr),
                NativeId("vertex", StartVertex),
                NativeId("vertex", EndVertex),
                NativeId("curve", CurveAttr),
                StartParam,
                EndParam,
                tolerance=Tolerance,
                degenerate=Degenerate,
                attributes=FrozenMapping(EdgeAttrs),
            )
        )
    return tuple(Edges)


# outer loop discovery selects the first dimensional ring for every face
def FindOuterLoops(
    FaceLoops: Mapping[int, Sequence[tuple[int, Sequence[int]]]], Tables: RecordTables
) -> set[int]:
    OuterLoops: set[int] = set()
    for Values in FaceLoops.values():
        OuterLoop = next(
            (
                LoopAttr
                for LoopAttr, RingValue in Values
                if not any(
                    (Tables.coedges[ValueData].isolated for ValueData in RingValue)
                )
            ),
            0,
        )
        if OuterLoop <= 1:
            raise ValueError("face has no dimensional boundary loop")
        OuterLoops.add(OuterLoop)
    return OuterLoops


# loop construction maps native rings into interchange coedge identifiers
def MakePartLoops(
    FaceLoops: Mapping[int, Sequence[tuple[int, Sequence[int]]]], OuterLoops: set[int]
) -> tuple[BrepLoop, ...]:
    return tuple(
        (
            BrepLoop(
                NativeId("loop", LoopAttr),
                tuple((NativeId("coedge", ValueData) for ValueData in RingValue)),
                LoopAttr in OuterLoops,
            )
            for Values in FaceLoops.values()
            for LoopAttr, RingValue in Values
        )
    )


# surface construction restores native linked list ordering metadata
def MakePartSurfs(
    Tables: RecordTables, SurfOrder: Sequence[int], SurfRanks: Mapping[int, int]
) -> tuple[object, ...]:
    return tuple(
        (
            Replace(
                Tables.surfaces[AttrValue],
                attributes=FrozenMapping(
                    {
                        **dict(getattr(Tables.surfaces[AttrValue], "attributes", {})),
                        "parasolid.surface_order": SurfRanks[AttrValue],
                    }
                ),
            )
            for AttrValue in SurfOrder
        )
    )


# face construction restores topology tolerance orientation and vendor ordering metadata
def MakePartFaces(
    Tables: RecordTables,
    FaceLoops: Mapping[int, Sequence[tuple[int, object]]],
    FaceOrder: Sequence[int],
    FaceRanks: Mapping[int, int],
    FaceSurfRanks: Mapping[int, int],
    FaceFrontRanks: Mapping[int, int],
    UnchangedIds: Mapping[int, int],
    AttrOrders: Mapping[str, Mapping[int, int]],
) -> tuple[BrepFace, ...]:
    return tuple(
        (
            BrepFace(
                NativeId("face", BridgeAttr),
                NativeId("surface", Tables.bridges[BridgeAttr].references[4]),
                tuple(
                    (
                        NativeId("loop", LoopAttr)
                        for LoopAttr, Ignored in FaceLoops[BridgeAttr]
                    )
                ),
                not Tables.bridges[BridgeAttr].reversed,
                tolerance=Tables.bridges[BridgeAttr].tolerance,
                attributes=FrozenMapping(
                    {
                        **(
                            {"solidworks.unchanged_id": UnchangedIds[BridgeAttr]}
                            if BridgeAttr in UnchangedIds
                            else {}
                        ),
                        "parasolid.face_order": FaceRanks[BridgeAttr],
                        "parasolid.surface_face_order": FaceSurfRanks[BridgeAttr],
                        "parasolid.front_face_order": FaceFrontRanks[BridgeAttr],
                        **{
                            f"solidworks.{KindValueData}_order": Ranks[BridgeAttr]
                            for KindValueData, Ranks in AttrOrders.items()
                            if BridgeAttr in Ranks
                        },
                    }
                ),
            )
            for BridgeAttr in FaceOrder
        )
    )


# body tree construction prefers native hierarchy and deterministically orders shell faces
def BuildTreeModel(
    Tables: RecordTables,
    OwnerFaces: Mapping[int, int],
    FaceLoops: Mapping[int, object],
    FaceRanks: Mapping[int, int],
) -> tuple[object, ...]:
    try:
        TreeValue = BuildBodyTree(Tables.entities, OwnerFaces, set(FaceLoops))
    except ValueError:
        TreeValue = DeriveBodyTree(FaceLoops, Tables)
    FaceUses, Shells, ShellUses, Regions, Bodies = TreeValue
    FaceRankById = {
        NativeId("face", AttrValue): RankValue
        for AttrValue, RankValue in FaceRanks.items()
    }
    FaceUseById = {FaceUse.id: FaceUse for FaceUse in FaceUses}

    # this callback exists because local behavior needs one focused transformation
    Shells = tuple(
        (
            Replace(
                Shell,
                face_use_ids=tuple(
                    sorted(
                        Shell.face_use_ids,
                        key=lambda FaceUseId: FaceRankById[
                            FaceUseById[FaceUseId].face_id
                        ],
                    )
                ),
            )
            for Shell in Shells
        )
    )
    return FaceUses, Shells, ShellUses, Regions, Bodies


# this declaration exists because focused behavior needs one stable owner
def WalkCoedgeRing(
    Tables: RecordTables, LoopAttr: int, FirstAttr: int
) -> tuple[int, ...]:
    if FirstAttr <= 1:
        raise ValueError("empty coedge ring")
    if not Tables.v12_partition:
        return WalkRingLinks(Tables, LoopAttr, FirstAttr, 3)
    Candidates: list[tuple[int, ...]] = []
    for LinkValue in (2, 3):
        Candidate = WalkRingLinks(Tables, LoopAttr, FirstAttr, LinkValue)
        if Candidate not in Candidates:
            Candidates.append(Candidate)
    Connected = [
        Candidate for Candidate in Candidates if IsConnectedRing(Tables, Candidate)
    ]
    if not Connected:
        raise ValueError("disconnected coedge ring")
    return Connected[0]


# coedge link traversal validates ownership closure and bounded record counts
def WalkRingLinks(
    Tables: RecordTables, LoopAttr: int, FirstAttr: int, LinkValue: int
) -> tuple[int, ...]:
    RingValue: list[int] = []
    SeenValue: set[int] = set()
    AttrValue = FirstAttr
    while AttrValue not in SeenValue:
        if len(RingValue) >= 1000000:
            raise ValueError("coedge ring exceeds record bound")
        SeenValue.add(AttrValue)
        Record = Tables.coedges.get(AttrValue)
        if Record is None or Record.references[1] != LoopAttr:
            raise ValueError("invalid coedge owner")
        RingValue.append(AttrValue)
        AttrValue = Record.references[LinkValue]
        if AttrValue <= 1:
            raise ValueError("open coedge ring")
    if AttrValue != FirstAttr:
        raise ValueError("coedge ring joins another cycle")
    return tuple(RingValue)


# ring connectivity confirms adjacent fins share the same edge reference
def IsConnectedRing(Tables: RecordTables, Candidate: Sequence[int]) -> bool:
    for Position, AttrValue in enumerate(Candidate):
        Record = Tables.coedges[AttrValue]
        if Record.isolated and len(Candidate) == 1:
            continue
        Other = Tables.coedges.get(Record.references[5])
        NextValue = Tables.coedges[Candidate[(Position + 1) % len(Candidate)]]
        if Other is None or Other.references[4] != NextValue.references[4]:
            return False
    return True


# this declaration exists because focused behavior needs one stable owner
def ProveCurveRange(
    Curve: object,
    Start: VectorThree,
    EndValue: VectorThree,
    StartTol: float = 0.0,
    EndTol: float = 0.0,
) -> tuple[float, float]:
    TrimParams = getattr(Curve, "attributes", {}).get("trim_parameters")
    TrimPoints = getattr(Curve, "attributes", {}).get("trim_points")
    if TrimParams is not None or TrimPoints is not None:
        return TrimmedRange(TrimParams, TrimPoints, Start, EndValue, StartTol, EndTol)
    if isinstance(Curve, LineCurve):
        return LineCurveRange(Curve, Start, EndValue)
    if isinstance(Curve, (CircleCurve, EllipseCurve)):
        return ConicCurveRange(Curve, Start, EndValue)
    if isinstance(Curve, NurbsCurve):
        return NurbsCurveRange(Curve, Start, EndValue)
    if isinstance(Curve, IntersectionCurve):
        return InterCurveRange(Curve, Start, EndValue)
    raise ValueError("curve parameter range is not provable")


# trimmed range validation binds stored parameters to uniquely matched endpoints
def TrimmedRange(
    TrimParams: object,
    TrimPoints: object,
    Start: VectorThree,
    EndValue: VectorThree,
    StartTol: float,
    EndTol: float,
) -> tuple[float, float]:
    if (
        not isinstance(TrimParams, tuple)
        or len(TrimParams) != 2
        or not all(
            (
                type(ValueData) is float and MathValue.isfinite(ValueData)
                for ValueData in TrimParams
            )
        )
    ):
        raise ValueError("trimmed curve range is invalid")
    if (
        not isinstance(TrimPoints, tuple)
        or len(TrimPoints) != 2
        or not all((isinstance(ValueData, VectorThree) for ValueData in TrimPoints))
    ):
        raise ValueError("trimmed curve range is invalid")
    Direct = Distance(Start, TrimPoints[0]) <= max(StartTol, 1e-07) and Distance(
        EndValue, TrimPoints[1]
    ) <= max(EndTol, 1e-07)
    Reverse = Distance(Start, TrimPoints[1]) <= max(StartTol, 1e-07) and Distance(
        EndValue, TrimPoints[0]
    ) <= max(EndTol, 1e-07)
    if Direct == Reverse:
        raise ValueError("trimmed curve endpoints are not uniquely bound")
    return TrimParams if Direct else tuple(Builtins.reversed(TrimParams))


# line range recovery projects and verifies both endpoints on the carrier
def LineCurveRange(
    Curve: LineCurve, Start: VectorThree, EndValue: VectorThree
) -> tuple[float, float]:
    StartParam = DotProduct(Subtract(Start, Curve.origin), Curve.direction)
    EndParam = DotProduct(Subtract(EndValue, Curve.origin), Curve.direction)
    if (
        Distance(LinePoint(Curve, StartParam), Start) > 1e-07
        or Distance(LinePoint(Curve, EndParam), EndValue) > 1e-07
    ):
        raise ValueError("line endpoints do not lie on carrier")
    return StartParam, EndParam


# conic range recovery unwraps the endpoint angles in traversal order
def ConicCurveRange(
    Curve: CircleCurve | EllipseCurve, Start: VectorThree, EndValue: VectorThree
) -> tuple[float, float]:
    StartParam = ConicParam(Curve, Start)
    EndParam = ConicParam(Curve, EndValue)
    if Distance(Start, EndValue) <= 1e-07:
        return StartParam, StartParam + MathValue.tau
    while EndParam <= StartParam:
        EndParam += MathValue.tau
    return StartParam, EndParam


# nurbs range recovery matches endpoints against the provable knot domain
def NurbsCurveRange(
    Curve: NurbsCurve, Start: VectorThree, EndValue: VectorThree
) -> tuple[float, float]:
    Domain = CurveParamRange(Curve)
    if Domain is None:
        raise ValueError("NURBS curve domain is not provable")
    Lower, Upper, Ignored, Ignored = Domain
    LowerPoint, UpperPoint = NurbsCurvePoint(Curve, Lower), NurbsCurvePoint(
        Curve, Upper
    )
    if LowerPoint is None or UpperPoint is None:
        raise ValueError("NURBS curve endpoints are not evaluable")
    Direct = (
        Distance(Start, LowerPoint) <= 1e-07 and Distance(EndValue, UpperPoint) <= 1e-07
    )
    Reverse = (
        Distance(Start, UpperPoint) <= 1e-07 and Distance(EndValue, LowerPoint) <= 1e-07
    )
    if Direct == Reverse:
        raise ValueError("NURBS curve endpoints do not identify its range")
    return (Lower, Upper) if Direct else (Upper, Lower)


# intersection range recovery locates endpoints along monotonic sampled parameters
def InterCurveRange(
    Curve: IntersectionCurve, Start: VectorThree, EndValue: VectorThree
) -> tuple[float, float]:
    Params = Curve.attributes.get("chart_parameters")
    if (
        not isinstance(Params, tuple)
        or len(Params) != len(Curve.samples)
        or len(Params) < 2
    ):
        raise ValueError("intersection chart parameters are not provable")
    if not all(
        (
            isinstance(ValueData, float) and MathValue.isfinite(ValueData)
            for ValueData in Params
        )
    ) or not all((LeftValue < Right for LeftValue, Right in zip(Params, Params[1:]))):
        raise ValueError("intersection chart parameters are not provable")
    TolValue = max(Curve.tolerance, 1e-07)
    StartParam = InterChartParam(Curve.samples, Params, Start, TolValue)
    EndParam = InterChartParam(Curve.samples, Params, EndValue, TolValue)
    if StartParam is None or EndParam is None:
        raise ValueError("intersection endpoints do not identify a chart range")
    if StartParam == EndParam and Distance(Start, EndValue) > TolValue:
        raise ValueError("intersection chart range collapses distinct endpoints")
    return StartParam, EndParam


# this declaration exists because focused behavior needs one stable owner
def InterChartParam(
    Samples: Sequence[VectorThree],
    Params: Sequence[float],
    Point: VectorThree,
    TolValue: float,
) -> float | None:
    Candidates = []
    for Index, (LeftValue, Right) in enumerate(zip(Samples, Samples[1:])):
        Chord = Subtract(Right, LeftValue)
        LengthSquared = DotProduct(Chord, Chord)
        if LengthSquared <= 0.0:
            return None
        Fraction = max(
            0.0, min(1.0, DotProduct(Subtract(Point, LeftValue), Chord) / LengthSquared)
        )
        Projected = VectorThree(
            LeftValue.x + Chord.x * Fraction,
            LeftValue.y + Chord.y * Fraction,
            LeftValue.z + Chord.z * Fraction,
        )
        DistanceData = Distance(Point, Projected)
        if DistanceData <= TolValue:
            Param = Params[Index] + Fraction * (Params[Index + 1] - Params[Index])
            Candidates.append((DistanceData, Param))
    if not Candidates:
        return None
    Candidates.sort()
    BestDistance, BestParam = Candidates[0]
    ParamSpan = abs(Params[-1] - Params[0])
    ParamTol = max(ParamSpan * 1e-12, 1e-12)
    for DistanceData, Param in Candidates[1:]:
        if (
            abs(Param - BestParam) > ParamTol
            and abs(DistanceData - BestDistance) <= 1e-12
        ):
            return None
    return BestParam


# this declaration exists because focused behavior needs one stable owner
def LinePoint(Curve: LineCurve, Param: float) -> VectorThree:
    return VectorThree(
        Curve.origin.x + Curve.direction.x * Param,
        Curve.origin.y + Curve.direction.y * Param,
        Curve.origin.z + Curve.direction.z * Param,
    )


# this declaration exists because focused behavior needs one stable owner
def ConicPoint(Curve: CircleCurve | EllipseCurve, Param: float) -> VectorThree:
    Normal = Cross(Curve.axis, Curve.reference_direction)
    Major = Curve.radius if isinstance(Curve, CircleCurve) else Curve.major_radius
    Minor = Curve.radius if isinstance(Curve, CircleCurve) else Curve.minor_radius
    return VectorThree(
        Curve.center.x
        + Major * MathValue.cos(Param) * Curve.reference_direction.x
        + Minor * MathValue.sin(Param) * Normal.x,
        Curve.center.y
        + Major * MathValue.cos(Param) * Curve.reference_direction.y
        + Minor * MathValue.sin(Param) * Normal.y,
        Curve.center.z
        + Major * MathValue.cos(Param) * Curve.reference_direction.z
        + Minor * MathValue.sin(Param) * Normal.z,
    )


# this declaration exists because focused behavior needs one stable owner
def ConicParam(Curve: CircleCurve | EllipseCurve, Point: VectorThree) -> float:
    Difference = Subtract(Point, Curve.center)
    Normal = Cross(Curve.axis, Curve.reference_direction)
    Major = Curve.radius if isinstance(Curve, CircleCurve) else Curve.major_radius
    Minor = Curve.radius if isinstance(Curve, CircleCurve) else Curve.minor_radius
    XValue = DotProduct(Difference, Curve.reference_direction) / Major
    YValue = DotProduct(Difference, Normal) / Minor
    Param = MathValue.atan2(YValue, XValue)
    if Distance(ConicPoint(Curve, Param), Point) > 1e-07:
        raise ValueError("conic endpoint does not lie on carrier")
    return Param


# this declaration exists because focused behavior needs one stable owner
def Subtract(LeftValue: VectorThree, Right: VectorThree) -> VectorThree:
    return VectorThree(
        LeftValue.x - Right.x, LeftValue.y - Right.y, LeftValue.z - Right.z
    )


# this declaration exists because focused behavior needs one stable owner
def DotProduct(LeftValue: VectorThree, Right: VectorThree) -> float:
    return LeftValue.x * Right.x + LeftValue.y * Right.y + LeftValue.z * Right.z


# this declaration exists because focused behavior needs one stable owner
def Cross(LeftValue: VectorThree, Right: VectorThree) -> VectorThree:
    return VectorThree(
        LeftValue.y * Right.z - LeftValue.z * Right.y,
        LeftValue.z * Right.x - LeftValue.x * Right.z,
        LeftValue.x * Right.y - LeftValue.y * Right.x,
    )


# this declaration exists because focused behavior needs one stable owner
def Distance(LeftValue: VectorThree, Right: VectorThree) -> float:
    Difference = Subtract(LeftValue, Right)
    return MathValue.sqrt(DotProduct(Difference, Difference))


# this declaration exists because focused behavior needs one stable owner
def DeriveBodyTree(
    FaceLoops: Mapping[int, tuple[tuple[int, tuple[int, ...]], ...]],
    Tables: RecordTables,
) -> tuple[
    tuple[BrepFaceUse, ...],
    tuple[BrepShell, ...],
    tuple[BrepShellUse, ...],
    tuple[BrepRegion, ...],
    tuple[BrepBody, ...],
]:
    FacesByEdge, EdgesByFace = FaceEdgeLinks(FaceLoops, Tables)
    Components = FaceComponents(FaceLoops, FacesByEdge)
    FaceUses, Shells, ShellUses, Regions, RegionIds = MakeDerivedTree(
        Components, EdgesByFace
    )
    if not RegionIds:
        raise ValueError("body hierarchy is absent")
    Bodies = (BrepBody("sldprt:brep:body:derived:1", tuple(RegionIds)),)
    return tuple(FaceUses), tuple(Shells), tuple(ShellUses), tuple(Regions), Bodies


# face edge linking gathers adjacency evidence from nonisolated coedges
def FaceEdgeLinks(
    FaceLoops: Mapping[int, tuple[tuple[int, tuple[int, ...]], ...]],
    Tables: RecordTables,
) -> tuple[dict[int, set[int]], dict[int, list[int]]]:
    FacesByEdge: dict[int, set[int]] = {}
    EdgesByFace: dict[int, list[int]] = {}
    for FaceAttr, Loops in FaceLoops.items():
        FaceEdges = []
        for Ignored, RingValue in Loops:
            for CoedgeAttr in RingValue:
                Coedge = Tables.coedges[CoedgeAttr]
                if Coedge.isolated:
                    continue
                EdgeAttr = Coedge.references[6]
                FaceEdges.append(EdgeAttr)
                FacesByEdge.setdefault(EdgeAttr, set()).add(FaceAttr)
        EdgesByFace[FaceAttr] = FaceEdges
    return FacesByEdge, EdgesByFace


# face component discovery groups topology connected through shared edges
def FaceComponents(
    FaceLoops: Mapping[int, object], FacesByEdge: Mapping[int, set[int]]
) -> list[tuple[int, ...]]:
    Neighbors = {FaceAttr: set() for FaceAttr in FaceLoops}
    for FaceAttrs in FacesByEdge.values():
        for FaceAttr in FaceAttrs:
            Neighbors[FaceAttr].update(FaceAttrs - {FaceAttr})
    Components = []
    Remain = set(FaceLoops)
    while Remain:
        SeedValue = min(Remain)
        Pending = [SeedValue]
        Component = set()
        while Pending:
            FaceAttr = Pending.pop()
            if FaceAttr in Component:
                continue
            Component.add(FaceAttr)
            Pending.extend(Neighbors[FaceAttr] - Component)
        Remain -= Component
        Components.append(tuple(sorted(Component)))
    return Components


# derived hierarchy construction creates one shell and region per face component
def MakeDerivedTree(
    Components: Sequence[Sequence[int]], EdgesByFace: Mapping[int, Sequence[int]]
) -> tuple[
    list[BrepFaceUse], list[BrepShell], list[BrepShellUse], list[BrepRegion], list[str]
]:
    FaceUses = []
    Shells = []
    ShellUses = []
    Regions = []
    RegionIds = []
    for Index, Component in enumerate(Components, start=1):
        UseIds = []
        EdgeCounts: dict[int, int] = {}
        for FaceAttr in Component:
            UseId = f"sldprt:brep:face-use:derived:{FaceAttr}"
            FaceUses.append(BrepFaceUse(UseId, NativeId("face", FaceAttr)))
            UseIds.append(UseId)
            for EdgeAttr in EdgesByFace[FaceAttr]:
                EdgeCounts[EdgeAttr] = EdgeCounts.get(EdgeAttr, 0) + 1
        Solid = bool(EdgeCounts) and all(
            (ValueData == 2 for ValueData in EdgeCounts.values())
        )
        ShellId = f"sldprt:brep:shell:derived:{Index}"
        ShellUseId = f"sldprt:brep:shell-use:derived:{Index}"
        RegionId = f"sldprt:brep:region:derived:{Index}"
        Shells.append(BrepShell(ShellId, tuple(UseIds), Solid))
        ShellUses.append(BrepShellUse(ShellUseId, ShellId))
        Regions.append(BrepRegion(RegionId, (ShellUseId,), Solid))
        RegionIds.append(RegionId)
    return FaceUses, Shells, ShellUses, Regions, RegionIds


# this declaration exists because focused behavior needs one stable owner
def BuildBodyTree(
    Entities: Mapping[int, EntityRecord],
    OwnerFaces: Mapping[int, int],
    ExpectedFaces: set[int],
) -> tuple[
    tuple[BrepFaceUse, ...],
    tuple[BrepShell, ...],
    tuple[BrepShellUse, ...],
    tuple[BrepRegion, ...],
    tuple[BrepBody, ...],
]:
    Roots = tuple(
        (Entity for Entity in Entities.values() if Entity.discriminator == 23)
    )
    if not Roots:
        raise ValueError("body hierarchy is absent")
    AssignedFaces: set[int] = set()
    FaceUses: list[BrepFaceUse] = []
    Shells: list[BrepShell] = []
    ShellUses: list[BrepShellUse] = []
    Regions: list[BrepRegion] = []
    Bodies: list[BrepBody] = []

    # this callback exists because local behavior needs one focused transformation
    for RootValue in sorted(Roots, key=lambda ValueData: ValueData.attribute):
        BuildRootMut(
            RootValue,
            Entities,
            OwnerFaces,
            AssignedFaces,
            FaceUses,
            Shells,
            ShellUses,
            Regions,
            Bodies,
        )
    if AssignedFaces != ExpectedFaces:
        raise ValueError("body hierarchy does not own every face")
    return (
        tuple(FaceUses),
        tuple(Shells),
        tuple(ShellUses),
        tuple(Regions),
        tuple(Bodies),
    )


# native root construction connects its validated regions to one body
def BuildRootMut(
    RootValue: EntityRecord,
    Entities: Mapping[int, EntityRecord],
    OwnerFaces: Mapping[int, int],
    AssignedFaces: set[int],
    FaceUses: list[BrepFaceUse],
    Shells: list[BrepShell],
    ShellUses: list[BrepShellUse],
    Regions: list[BrepRegion],
    Bodies: list[BrepBody],
) -> None:
    RegionIds: list[str] = []
    for RegionAttr in Nonnull(RootValue.references):
        RegionId = BuildRegionMut(
            RegionAttr,
            Entities,
            OwnerFaces,
            AssignedFaces,
            FaceUses,
            Shells,
            ShellUses,
            Regions,
        )
        RegionIds.append(RegionId)
    if not RegionIds:
        raise ValueError("empty native body")
    Bodies.append(BrepBody(NativeId("body", RootValue.attribute), tuple(RegionIds)))


# native region construction expands its shell chain and preserves solidity
def BuildRegionMut(
    RegionAttr: int,
    Entities: Mapping[int, EntityRecord],
    OwnerFaces: Mapping[int, int],
    AssignedFaces: set[int],
    FaceUses: list[BrepFaceUse],
    Shells: list[BrepShell],
    ShellUses: list[BrepShellUse],
    Regions: list[BrepRegion],
) -> str:
    Region = Entities.get(RegionAttr)
    if Region is None or Region.discriminator not in {27, 29}:
        raise ValueError("unsupported body region hierarchy")
    Solid = Region.discriminator == 27
    ShellUseIds: list[str] = []
    for ShellAttr, FaceOwners in NativeShellData(Entities, Region, Solid):
        ShellUseId = BuildShellMut(
            ShellAttr,
            FaceOwners,
            Solid,
            OwnerFaces,
            AssignedFaces,
            FaceUses,
            Shells,
            ShellUses,
        )
        ShellUseIds.append(ShellUseId)
    RegionId = NativeId("region", Region.attribute)
    Regions.append(BrepRegion(RegionId, tuple(ShellUseIds), Solid))
    return RegionId


# native shell discovery follows solid lump chains or direct sheet face lists
def NativeShellData(
    Entities: Mapping[int, EntityRecord], Region: EntityRecord, Solid: bool
) -> list[tuple[int, tuple[int, ...]]]:
    NativeShells: list[tuple[int, tuple[int, ...]]] = []
    if Solid:
        for LumpAttr in Nonnull(Region.references):
            LumpValue = RequireEntity(Entities, LumpAttr, 31)
            ShellNode = RequireEntity(Entities, SingleRef(LumpValue), 33)
            ShellLink = RequireEntity(Entities, SingleRef(ShellNode), 35)
            NativeShells.append(
                (LumpAttr, FaceOwnerChain(Entities, SingleRef(ShellLink), 19))
            )
    else:
        NativeShells.append(
            (Region.attribute, FaceOwnerChain(Entities, SingleRef(Region), 21))
        )
    return NativeShells


# native shell construction claims faces and creates matching use records
def BuildShellMut(
    ShellAttr: int,
    FaceOwners: Sequence[int],
    Solid: bool,
    OwnerFaces: Mapping[int, int],
    AssignedFaces: set[int],
    FaceUses: list[BrepFaceUse],
    Shells: list[BrepShell],
    ShellUses: list[BrepShellUse],
) -> str:
    if not FaceOwners:
        raise ValueError("empty native shell")
    FaceAttrs: list[int] = []
    for Owner in FaceOwners:
        FaceAttr = OwnerFaces.get(Owner)
        if FaceAttr is None or FaceAttr in AssignedFaces:
            raise ValueError("ambiguous shell face membership")
        AssignedFaces.add(FaceAttr)
        FaceAttrs.append(FaceAttr)
    FaceUseIds: list[str] = []
    for FaceAttr in FaceAttrs:
        FaceUseId = NativeId("face-use", FaceAttr)
        FaceUses.append(BrepFaceUse(FaceUseId, NativeId("face", FaceAttr)))
        FaceUseIds.append(FaceUseId)
    ShellId, ShellUseId = NativeId("shell", ShellAttr), NativeId("shell-use", ShellAttr)
    Shells.append(BrepShell(ShellId, tuple(FaceUseIds), Solid))
    ShellUses.append(BrepShellUse(ShellUseId, ShellId))
    return ShellUseId


# this declaration exists because focused behavior needs one stable owner
def Nonnull(Values: Sequence[int]) -> tuple[int, ...]:
    return tuple((ValueData for ValueData in Values if ValueData > 1))


# this declaration exists because focused behavior needs one stable owner
def SingleRef(Entity: EntityRecord) -> int:
    RefsValueData = Nonnull(Entity.references)
    if len(RefsValueData) != 1:
        raise ValueError("entity does not contain one child reference")
    return RefsValueData[0]


# this declaration exists because focused behavior needs one stable owner
def RequireEntity(
    Entities: Mapping[int, EntityRecord], AttrValue: int, KindValue: int
) -> EntityRecord:
    Entity = Entities.get(AttrValue)
    if Entity is None or Entity.discriminator != KindValue:
        raise ValueError("entity hierarchy discriminator mismatch")
    return Entity


# this declaration exists because focused behavior needs one stable owner
def FaceOwnerChain(
    Entities: Mapping[int, EntityRecord], HeadValue: int, KindValue: int
) -> tuple[int, ...]:
    Owners: list[int] = []
    SeenValue: set[int] = set()
    AttrValue = HeadValue
    while AttrValue > 1:
        if AttrValue in SeenValue:
            raise ValueError("cyclic face owner list")
        SeenValue.add(AttrValue)
        Entity = RequireEntity(Entities, AttrValue, KindValue)
        NextAttrData, *Values = Entity.references
        Owners.extend((ValueData for ValueData in Values if ValueData > 1))
        AttrValue = NextAttrData
    return tuple(Owners)


# this declaration exists because focused behavior needs one stable owner
def NativeId(KindValueData: str, AttrValue: int) -> str:
    return f"sldprt:brep:{KindValueData}:{AttrValue}"


# this declaration exists because focused behavior needs one stable owner
def HasPayloadMut(DataValue=None, **LegacyValues):
    DataValue = LegacyValues.pop("data", DataValue)
    if LegacyValues:
        raise TypeError(
            f"contains_parasolid_payload got unexpected keyword {next(iter(LegacyValues))!r}"
        )
    return HasParaPayload(DataValue)


# this declaration exists because focused behavior needs one stable owner
def IsPayloadApiMut(DataValue=None, **LegacyValues):
    DataValue = LegacyValues.pop("data", DataValue)
    if LegacyValues:
        raise TypeError(
            f"is_native_parasolid_payload got unexpected keyword {next(iter(LegacyValues))!r}"
        )
    return IsNativePayload(DataValue)


# this declaration exists because focused behavior needs one stable owner
def EncodeBrepMut(
    ModelData=None, *, Partition=True, SolidworksFeatureIds=None, **LegacyValues
):
    ModelData = LegacyValues.pop("model", ModelData)
    Partition = LegacyValues.pop("partition", Partition)
    SolidworksFeatureIds = LegacyValues.pop(
        "solidworks_feature_ids", SolidworksFeatureIds
    )
    if LegacyValues:
        raise TypeError(
            f"encode_brep_model got unexpected keyword {next(iter(LegacyValues))!r}"
        )
    return EncodeBrepModel(
        ModelData, PartValue=Partition, SolidFeatureIds=SolidworksFeatureIds
    )


# this declaration exists because focused behavior needs one stable owner
def EncodePartMut(DataValue=None, **LegacyValues):
    DataValue = LegacyValues.pop("data", DataValue)
    if LegacyValues:
        raise TypeError(
            f"encode_partition_stream got unexpected keyword {next(iter(LegacyValues))!r}"
        )
    return EncodePartData(DataValue)


# this declaration exists because focused behavior needs one stable owner
def EncodeBlankApi():
    return EncodeBlankPart()


# this declaration exists because focused behavior needs one stable owner
def DecodePartMut(DataValue=None, StreamName="", **LegacyValues):
    DataValue = LegacyValues.pop("data", DataValue)
    StreamName = LegacyValues.pop("stream", StreamName)
    if LegacyValues:
        raise TypeError(
            f"decode_partition_stream got unexpected keyword {next(iter(LegacyValues))!r}"
        )
    return DecodePartData(DataValue, StreamName)


# this declaration exists because focused behavior needs one stable owner
def DecodeBrepMut(DataValue=None, **LegacyValues):
    DataValue = LegacyValues.pop("data", DataValue)
    if LegacyValues:
        raise TypeError(
            f"decode_brep_model got unexpected keyword {next(iter(LegacyValues))!r}"
        )
    return DecodeBrepModel(DataValue)


# this mapping preserves established imports for one focused compatibility group
KLegacyExportAlpha = {
    "ParasolidFormatError": ParaFormatError,
    "ParasolidPayload": ParaPayload,
    "ParasolidWriteError": ParaWriteError,
    "_ANALYTIC_VALUE_COUNTS": KAnalyticValueCounts,
    "_BCurveRecord": BCurveRecord,
    "_BLANK_DELTAS_BODY": KBlankDeltaBody,
    "_BLANK_PARTITION_BODY": KBlankPartBody,
    "_BSurfaceRecord": BSurfaceRecord,
    "_BrepTopology": BrepTopology,
    "_ChartRecord": ChartRecord,
    "_CompactSupportUvRecord": CompactUvRecord,
    "_CurveDataRecord": CurveRecord,
    "_ENTITY_MAGIC": KEntityMagic,
    "_EntityRecord": EntityRecord,
    "_FloatArrayRecord": FloatArray,
    "_INLINE_TERM_TAIL": KInlineTermTail,
    "_INLINE_UV_TAIL": KInlineUvTail,
    "_IntersectionRecord": IntersectRecord,
    "_LENGTH_SCALE": KLengthScale,
    "_MISSING_PARAMETER": KMissingParam,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportBravo = {
    "_NurbsCurveRecord": NurbsCurveRec,
    "_NurbsSurfaceRecord": NurbsSurfRecord,
    "_PARASOLID_V12_PARTITION_DESCRIPTION": KParaPartDesc,
    "_PARASOLID_V12_PART_DESCRIPTION": KParaModelDesc,
    "_PARASOLID_V12_SCHEMA": KParaSchema,
    "_ParasolidHeader": ParaHeader,
    "_ReadTolerance": ReadTolerance,
    "_RecordTables": RecordTables,
    "_SHEET_SCHEMA": KSheetSchema,
    "_SOLIDWORKS_2025_SCHEMA": KSolidworksSchema,
    "_SOLID_SCHEMA": KSolidSchema,
    "_ShortArrayRecord": ShortArray,
    "_SupportUvRecord": SupportUvRecord,
    "_SurfaceDataRecord": SurfaceRecord,
    "_TermRecord": TermRecord,
    "_TopologyRecord": TopologyRecord,
    "_TrimmedCurveRecord": TrimCurveRecord,
    "_WRAPPER_MAGIC": KWrapperMagic,
    "_allocate": Allocate,
    "_analytic_geometry": AnalyticGeom,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportCharlie = {
    "_analytic_record_fields": AnalyticFields,
    "_array_record_fields": ArrayFields,
    "_be16": WriteShortMut,
    "_be32": WriteBigIntMut,
    "_bef64": WriteFloatMut,
    "_bind": BindOwnerMut,
    "_build_body_hierarchy": BuildBodyTree,
    "_build_partition_model": BuildPartModel,
    "_checked_attr": CheckedAttr,
    "_compact": WriteCompactMut,
    "_compact_nurbs_surface_shape": CompactNurbSurf,
    "_conic_parameter": ConicParam,
    "_conic_point": ConicPoint,
    "_cross": Cross,
    "_curve_parameter_domain": CurveParamRange,
    "_curve_point_at_parameter": CurvePoint,
    "_curve_values": CurveValues,
    "_decode_partition_model": DecodePartModel,
    "_derive_body_hierarchy": DeriveBodyTree,
    "_distance": Distance,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportDelta = {
    "_dot": DotProduct,
    "_encode_brep_body": EncodeBrepBody,
    "_entity51": EntityFiftyOne,
    "_f64_array": WriteFloatsMut,
    "_face_owner_chain": FaceOwnerChain,
    "_fin_descriptor": FinDescriptor,
    "_fin_index": FinIndex,
    "_fixed_refs": FixedRefs,
    "_frame": Frame,
    "_geometry_chain_links": GeomChainLinks,
    "_homogeneous_points": HomogPoints,
    "_i32": WriteSignedMut,
    "_infer_surface_shape": InferSurfShape,
    "_intersection_chart_parameter": InterChartParam,
    "_isolated_fin": IsIsolatedFin,
    "_line_point": LinePoint,
    "_linked_subset_order": LinkedOrder,
    "_native_id": NativeId,
    "_next_fin_at_vertex": NextFinAtVertex,
    "_nonnull": Nonnull,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportEcho = {
    "_nurbs_basis": NurbsBasis,
    "_nurbs_curve_point": NurbsCurvePoint,
    "_nurbs_surface_point": NurbsSurfPoint,
    "_order_solidworks_triangle_records": OrderTriRecords,
    "_ordered_chart": IsOrderedChart,
    "_ordered_ids": OrderIds,
    "_orthogonal": IsOrthogonal,
    "_parasolid_header": ParaHeaderData,
    "_parasolid_stream": ParaStream,
    "_parse_analytic_carrier": ParseCarrier,
    "_parse_b_curve_record": ParseBCurve,
    "_parse_b_surface_record": ParseBSurface,
    "_parse_bridge": ParseBridge,
    "_parse_chart_record": ParseChart,
    "_parse_coedge": ParseCoedge,
    "_parse_compact_chart_points": ParseCompactPts,
    "_parse_compact_support_uv_record": ParseCompactUv,
    "_parse_curve_data_record": ParseCurveData,
    "_parse_edge_use": ParseEdgeUse,
    "_parse_entity": ParseEntity,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportFoxtrot = {
    "_parse_extended_chart_points": ParseExtPoints,
    "_parse_float_array_record": ParseFloatArray,
    "_parse_intersection_data_record": ParseInterData,
    "_parse_intersection_fields": InterFields,
    "_parse_intersection_record": ParseInterRec,
    "_parse_loop": ParseLoop,
    "_parse_nurbs_curve_record": ParseNurbsCurve,
    "_parse_nurbs_surface_record": ParseNurbsSurf,
    "_parse_point": ParsePoint,
    "_parse_short_array_record": ParseShortArray,
    "_parse_support_uv_payload": ParseSupportUv,
    "_parse_support_uv_record": ParseSupportRec,
    "_parse_surface_data_record": ParseSurfaceDat,
    "_parse_term_payload": ParseTermPayloa,
    "_parse_term_record": ParseTermRecord,
    "_parse_trimmed_curve_record": ParseTrimCurve,
    "_parse_vertex_use": ParseVertexUse,
    "_payload": Payload,
    "_point_record_fields": PointRecoFiel,
    "_point_vector": PointVector,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportGolf = {
    "_provable_curve_range": ProveCurveRange,
    "_record_start": RecordStart,
    "_refs": RefsValue,
    "_require_complete": RequireComplete,
    "_require_entity": RequireEntity,
    "_resolve_intersection_curve": ResolveInter,
    "_resolve_nurbs_curve": ResolveNurbCurv,
    "_resolve_nurbs_surface": ResolveNurbSurf,
    "_resolve_trimmed_curve": ResolveTrimCurv,
    "_resolved_support_uv": ResolvedSuppUv,
    "_scaled_vector": ScaledVector,
    "_scan_partition_records": ScanPartRecords,
    "_single_reference": SingleRef,
    "_solidworks_face_data": SolidFaceData,
    "_solidworks_unchanged_ids": SolidUnchIds,
    "_store_unique_record": StoreUniqueMut,
    "_subtract": Subtract,
    "_support_uv_lanes": SupportUvLanes,
    "_surface_residual": SurfResidual,
    "_surface_values": SurfValues,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportHotel = {
    "_tag": WriteTagMut,
    "_tripled_refs": TripledRefs,
    "_u16": ReadShort,
    "_u16_array": WriteShortsMut,
    "_u32": ReadUnsigned,
    "_unit": UnitVector,
    "_v12_attribute": VTwelveAttr,
    "_v12_attribute_definition": WriteAttrDefMut,
    "_v12_attribute_identifier": WriteAttrIdMut,
    "_v12_fin": WriteFinMut,
    "_v12_geometry_node": WriteGeomMut,
    "_v12_int_values": VTwelveIntVals,
    "_v12_node": VTwelveNode,
    "_v12_pointer": WritePointerMut,
    "_v12_pointer_list": VTwelvePtrList,
    "_v12_real_values": VTwelveRealVals,
    "_v12_variable_node": VTwelveVarNode,
    "_validate_brep_write_support": ValidateSupport,
    "_validated_direction": ValidDirect,
    "_vector": Vector,
}

# this mapping preserves established imports for one focused compatibility group
KLegacyExportIndia = {
    "_vector_values": VectorValues,
    "_verify_encoded_brep": VerifyBrepData,
    "_vertex_fin_order": VertexFinOrder,
    "_walk_coedge_ring": WalkCoedgeRing,
    "_write_body_hierarchy": WriteBodyTree,
    "_write_face_list": WriteFaceList,
    "_write_nurbs_curve": WriteNurbsMut,
    "_write_nurbs_surface": WriteNurbsSMut,
    "_write_solidworks_body_attribute_prefix": WritePrefixMut,
    "_write_solidworks_body_attribute_suffix": WriteBodySuffix,
    "_write_solidworks_solid_attributes": WriteSolidAttrs,
    "_xmt": XmtData,
    "_xmt_sequence": XmtSeq,
    "contains_parasolid_payload": HasPayloadMut,
    "decode_brep_model": DecodeBrepMut,
    "decode_partition_stream": DecodePartMut,
    "encode_blank_partition_stream": EncodeBlankApi,
    "encode_brep_model": EncodeBrepMut,
    "encode_partition_stream": EncodePartMut,
    "is_native_parasolid_payload": IsPayloadApiMut,
}

# this tuple groups compatibility mappings for deterministic installation
KLegacyExportGroups = (
    KLegacyExportAlpha,
    KLegacyExportBravo,
    KLegacyExportCharlie,
    KLegacyExportDelta,
    KLegacyExportEcho,
    KLegacyExportFoxtrot,
    KLegacyExportGolf,
    KLegacyExportHotel,
    KLegacyExportIndia,
)

for ExportGroup in KLegacyExportGroups:
    globals().update(ExportGroup)
