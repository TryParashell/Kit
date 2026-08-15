# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from interchange.brep.curves.BrepCurves import BrepEntity
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector


# vertices anchor topological incidence to precise spatial points
@ModelDataMut(DefaultMap={"Tolerance": 0.0})
class BrepVertex(BrepEntity):
    Point: SpaceVector
    Tolerance: float
    if TYPE_CHECKING:
        point: ClassVar[SpaceVector]
        tolerance: ClassVar[float]


# edges connect vertices through exact curve parameter intervals
@ModelDataMut(DefaultMap={"Tolerance": 0.0, "IsDegenerate": False})
class BrepEdge(BrepEntity):
    StartVertexId: str
    EndVertexId: str
    CurveId: str
    StartParameter: float
    EndParameter: float
    Tolerance: float
    IsDegenerate: bool
    if TYPE_CHECKING:
        start_vertex_id: ClassVar[str]
        end_vertex_id: ClassVar[str]
        curve_id: ClassVar[str]
        start_parameter: ClassVar[float]
        end_parameter: ClassVar[float]
        tolerance: ClassVar[float]
        degenerate: ClassVar[bool]


# coedges preserve oriented edge use and optional parameter curve bindings
@ModelDataMut(DefaultMap={"PcurveId": "", "IsReversed": False})
class BrepCoedge(BrepEntity):
    EdgeId: str
    PcurveId: str
    IsReversed: bool
    if TYPE_CHECKING:
        edge_id: ClassVar[str]
        pcurve_id: ClassVar[str]
        reversed: ClassVar[bool]


# loops exist because face trimming boundaries require ordered connected coedges
@ModelDataMut(DefaultMap={"IsOuter": False})
class BrepLoop(BrepEntity):
    CoedgeIds: tuple[str, ...]
    IsOuter: bool
    if TYPE_CHECKING:
        coedge_ids: ClassVar[tuple[str, ...]]
        outer: ClassVar[bool]


# some boundaries have no owning face so standalone coedge groups preserve them
@ModelDataMut(DefaultMap={"IsClosed": False})
class BrepWire(BrepEntity):
    CoedgeIds: tuple[str, ...]
    IsClosed: bool
    if TYPE_CHECKING:
        coedge_ids: ClassVar[tuple[str, ...]]
        closed: ClassVar[bool]


# faces bind analytic surfaces to ordered trimming loops
@ModelDataMut(DefaultMap={"HasSameSense": True, "Tolerance": 0.0})
class BrepFace(BrepEntity):
    SurfaceId: str
    LoopIds: tuple[str, ...]
    HasSameSense: bool
    Tolerance: float
    if TYPE_CHECKING:
        surface_id: ClassVar[str]
        loop_ids: ClassVar[tuple[str, ...]]
        same_sense: ClassVar[bool]
        tolerance: ClassVar[float]


# face uses preserve orientation when shells reuse face definitions
@ModelDataMut(DefaultMap={"IsReversed": False})
class BrepFaceUse(BrepEntity):
    FaceId: str
    IsReversed: bool
    if TYPE_CHECKING:
        face_id: ClassVar[str]
        reversed: ClassVar[bool]


# shells collect oriented faces and preserve closure state
@ModelDataMut(DefaultMap={"IsClosed": False})
class BrepShell(BrepEntity):
    FaceUseIds: tuple[str, ...]
    IsClosed: bool
    if TYPE_CHECKING:
        face_use_ids: ClassVar[tuple[str, ...]]
        closed: ClassVar[bool]


# shell uses preserve orientation when regions reuse shell definitions
@ModelDataMut(DefaultMap={"IsReversed": False})
class BrepShellUse(BrepEntity):
    ShellId: str
    IsReversed: bool
    if TYPE_CHECKING:
        shell_id: ClassVar[str]
        reversed: ClassVar[bool]


# regions collect oriented shells and preserve solid classification
@ModelDataMut(DefaultMap={"IsSolid": True})
class BrepRegion(BrepEntity):
    ShellUseIds: tuple[str, ...]
    IsSolid: bool
    if TYPE_CHECKING:
        shell_use_ids: ClassVar[tuple[str, ...]]
        solid: ClassVar[bool]


# bodies connect region wire and vertex topology to document design bodies
@ModelDataMut(
    DefaultMap={
        "Transform": Transform(),
        "DesignBodyId": "",
        "WireIds": (),
        "VertexIds": (),
    }
)
class BrepBody(BrepEntity):
    RegionIds: tuple[str, ...]
    Transform: Transform
    DesignBodyId: str
    WireIds: tuple[str, ...]
    VertexIds: tuple[str, ...]
    if TYPE_CHECKING:
        region_ids: ClassVar[tuple[str, ...]]
        transform: ClassVar[Transform]
        design_body_id: ClassVar[str]
        wire_ids: ClassVar[tuple[str, ...]]
        vertex_ids: ClassVar[tuple[str, ...]]
