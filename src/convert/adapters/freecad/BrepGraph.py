# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any as AnyInfo, Never

from interchange import (
    BrepBody,
    BrepCoedge,
    BrepCurve,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepPcurve,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    BrepWire,
)


# writer errors retain one stable reason because adapter fallbacks inspect the public marker
class FreeCadBrep(ValueError):
    reason: str = "writer_unimplemented"


# unsupported topology fails explicitly because silent approximation would violate lossless output
def Unsupported(MessageText: str) -> Never:
    raise FreeCadBrep(f"writer_unimplemented: {MessageText}")


# unique ownership stays centralized because topology records may not belong to multiple parents
def BindOnceMut(
    OwnerMap: dict[str, str],
    ValueId: str,
    OwnerId: str,
    ValueName: str,
    OwnerName: str,
) -> None:
    if ValueId in OwnerMap:
        Unsupported(
            f"B-rep {ValueName} {ValueId} belongs to multiple {OwnerName} values"
        )
    OwnerMap[ValueId] = OwnerId


# complete ownership remains mandatory because orphan topology cannot produce a valid native shape
def RequireOwned(
    OwnerMap: Mapping[str, object],
    ValueMap: Mapping[str, object],
    ValueName: str,
    OwnerName: str,
) -> None:
    MissingId = next((ValueId for ValueId in ValueMap if ValueId not in OwnerMap), None)
    if MissingId is not None:
        Unsupported(f"B-rep {ValueName} {MissingId} has no {OwnerName}")


# record maps stay data driven because every topology family follows the same identifier contract
def SetMapsMut(Instance: AnyInfo, Model: BrepModel) -> None:
    MapNames = (
        "vertices",
        "curves",
        "edges",
        "coedges",
        "loops",
        "wires",
        "faces",
        "face_uses",
        "shells",
        "shell_uses",
        "regions",
        "bodies",
        "pcurves",
        "surfaces",
    )
    for NameText in MapNames:
        Values = getattr(Model, NameText)
        setattr(Instance, NameText, {Value.id: Value for Value in Values})


# ownership maps start independently because each topology relation has a distinct validation rule
def SetOwnersMut(Instance: AnyInfo, Model: BrepModel) -> None:
    setattr(Instance, "coedge_owner", {})
    setattr(Instance, "loop_face", {})
    setattr(
        Instance,
        "shell_owners",
        {ShellValue.id: [] for ShellValue in Model.shells},
    )
    setattr(Instance, "region_body", {})
    setattr(Instance, "wire_body", {})
    setattr(
        Instance,
        "edge_uses",
        {EdgeValue.id: [] for EdgeValue in Model.edges},
    )


# coedge ownership stays isolated because loops and wires are mutually exclusive parent families
def BindCoedgesMut(Instance: AnyInfo, Model: BrepModel) -> None:
    for LoopValue in Model.loops:
        for CoedgeId in LoopValue.coedge_ids:
            Instance._bind_coedge(CoedgeId, "loop", LoopValue.id)
    for WireValue in Model.wires:
        for CoedgeId in WireValue.coedge_ids:
            Instance._bind_coedge(CoedgeId, "wire", WireValue.id)


# face ownership stays isolated because loops and face uses validate separate hierarchy edges
def BindFacesMut(Instance: AnyInfo, Model: BrepModel) -> dict[str, str]:
    for FaceValue in Model.faces:
        for LoopId in FaceValue.loop_ids:
            BindOnceMut(Instance.loop_face, LoopId, FaceValue.id, "loop", "face")
    FaceOwners: dict[str, str] = {}
    for ShellValue in Model.shells:
        for FaceUseId in ShellValue.face_use_ids:
            BindOnceMut(FaceOwners, FaceUseId, ShellValue.id, "face use", "shell")
            FaceUse = Instance.face_uses[FaceUseId]
            Instance.shell_owners.setdefault(ShellValue.id, []).append(
                (FaceUse.id, FaceUse.face_id)
            )
    return FaceOwners


# region ownership stays isolated because shells regions and bodies form the outer hierarchy
def BindRegionsMut(Instance: AnyInfo, Model: BrepModel) -> dict[str, str]:
    ShellOwners: dict[str, str] = {}
    for RegionValue in Model.regions:
        for ShellUseId in RegionValue.shell_use_ids:
            BindOnceMut(ShellOwners, ShellUseId, RegionValue.id, "shell use", "region")
    for BodyValue in Model.bodies:
        for RegionId in BodyValue.region_ids:
            BindOnceMut(Instance.region_body, RegionId, BodyValue.id, "region", "body")
        for WireId in BodyValue.wire_ids:
            BindOnceMut(Instance.wire_body, WireId, BodyValue.id, "wire", "body")
    return ShellOwners


# orphan checks stay grouped because every graph layer must have exactly one structural owner
def CheckOwners(
    Instance: AnyInfo,
    FaceOwners: Mapping[str, object],
    ShellOwners: Mapping[str, object],
) -> None:
    RequireOwned(Instance.coedge_owner, Instance.coedges, "coedge", "loop or wire")
    RequireOwned(Instance.loop_face, Instance.loops, "loop", "face")
    RequireOwned(FaceOwners, Instance.face_uses, "face use", "shell")
    RequireOwned(ShellOwners, Instance.shell_uses, "shell use", "region")
    RequireOwned(Instance.region_body, Instance.regions, "region", "body")
    RequireOwned(Instance.wire_body, Instance.wires, "wire", "body")


# unreferenced face checks stay explicit because native topology cannot serialize orphan surfaces
def CheckFaces(Instance: AnyInfo, Model: BrepModel) -> None:
    UsedFaces = {FaceUse.face_id for FaceUse in Model.face_uses}
    MissingFace = next(
        (FaceId for FaceId in Instance.faces if FaceId not in UsedFaces), None
    )
    if MissingFace is not None:
        Unsupported(f"B-rep face {MissingFace} has no face use")
    UsedShells = {ShellUse.shell_id for ShellUse in Model.shell_uses}
    MissingShell = next(
        (ShellId for ShellId in Instance.shells if ShellId not in UsedShells), None
    )
    if MissingShell is not None:
        Unsupported(f"B-rep shell {MissingShell} has no shell use")


# edge incidence stays isolated because native output only supports manifold edge ownership
def IndexEdgesMut(Instance: AnyInfo, Model: BrepModel) -> None:
    for CoedgeValue in Model.coedges:
        Instance.edge_uses[CoedgeValue.edge_id].append(CoedgeValue.id)
    for EdgeId, UsesValue in Instance.edge_uses.items():
        if not UsesValue:
            Unsupported(f"B-rep edge {EdgeId} has no coedge use")
        if len(UsesValue) > 2:
            Unsupported(f"B-rep edge {EdgeId} is non-manifold")


# graph construction composes focused phases because each topology relation validates independently
def InitGraph(Instance: AnyInfo, Model: BrepModel) -> None:
    SetMapsMut(Instance, Model)
    SetOwnersMut(Instance, Model)
    BindCoedgesMut(Instance, Model)
    FaceOwners = BindFacesMut(Instance, Model)
    ShellOwners = BindRegionsMut(Instance, Model)
    CheckOwners(Instance, FaceOwners, ShellOwners)
    CheckFaces(Instance, Model)
    IndexEdgesMut(Instance, Model)


# coedge binding remains a graph method because later queries consume its parent identity directly
def BindCoedge(Instance: AnyInfo, CoedgeId: str, KindValue: str, OwnerId: str) -> None:
    OwnerMap = Instance.coedge_owner
    if CoedgeId in OwnerMap:
        Unsupported(f"B-rep coedge {CoedgeId} belongs to multiple loop or wire values")
    OwnerMap[CoedgeId] = (KindValue, OwnerId)


# face lookup remains a graph method because wire coedges intentionally have no owning face
def GetFace(Instance: ModelGraph, CoedgeId: str) -> BrepFace | None:
    KindValue, OwnerId = Instance.coedge_owner[CoedgeId]
    if KindValue == "wire":
        return None
    return Instance.faces[Instance.loop_face[OwnerId]]


# graph state stays focused because native topology validation shares one indexed ownership view
class ModelGraph:
    __slots__ = (
        "bodies",
        "coedge_owner",
        "coedges",
        "curves",
        "edge_uses",
        "edges",
        "face_uses",
        "faces",
        "loop_face",
        "loops",
        "pcurves",
        "region_body",
        "regions",
        "shell_owners",
        "shell_uses",
        "shells",
        "surfaces",
        "vertices",
        "wire_body",
        "wires",
    )
    bodies: dict[str, BrepBody]
    coedge_owner: dict[str, tuple[str, str]]
    coedges: dict[str, BrepCoedge]
    curves: dict[str, BrepCurve]
    edge_uses: dict[str, list[str]]
    edges: dict[str, BrepEdge]
    face_uses: dict[str, BrepFaceUse]
    faces: dict[str, BrepFace]
    loop_face: dict[str, str]
    loops: dict[str, BrepLoop]
    pcurves: dict[str, BrepPcurve]
    region_body: dict[str, str]
    regions: dict[str, BrepRegion]
    shell_owners: dict[str, list[tuple[str, str]]]
    shell_uses: dict[str, BrepShellUse]
    shells: dict[str, BrepShell]
    surfaces: dict[str, BrepSurface]
    vertices: dict[str, BrepVertex]
    wire_body: dict[str, str]
    wires: dict[str, BrepWire]

    # graph consumers need initialized ownership indexes before topology queries begin
    def __init__(self, Model: BrepModel) -> None:
        InitGraph(self, Model)

    # graph construction keeps this binding private so parent ownership cannot diverge
    def _bind_coedge(self, CoedgeId: str, KindValue: str, OwnerId: str) -> None:
        BindCoedge(self, CoedgeId, KindValue, OwnerId)

    # topology emitters need one typed route from coedges back to faces
    def face_for_coedge(self, CoedgeId: str) -> BrepFace | None:
        return GetFace(self, CoedgeId)
