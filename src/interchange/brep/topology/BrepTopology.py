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
@ModelDataMut(DefaultMap={"tolerance": 0.0})
class BrepVertex(BrepEntity):
    point: SpaceVector
    tolerance: float
    if TYPE_CHECKING:
        Point: ClassVar[SpaceVector]
        Tolerance: ClassVar[float]


# edges connect vertices through exact curve parameter intervals
@ModelDataMut(DefaultMap={"tolerance": 0.0, "degenerate": False})
class BrepEdge(BrepEntity):
    start_vertex_id: str
    end_vertex_id: str
    curve_id: str
    start_parameter: float
    end_parameter: float
    tolerance: float
    degenerate: bool
    if TYPE_CHECKING:
        StartVertexId: ClassVar[str]
        EndVertexId: ClassVar[str]
        CurveId: ClassVar[str]
        StartParameter: ClassVar[float]
        EndParameter: ClassVar[float]
        Tolerance: ClassVar[float]
        IsDegenerate: ClassVar[bool]


# coedges preserve oriented edge use and optional parameter curve bindings
@ModelDataMut(DefaultMap={"pcurve_id": "", "reversed": False})
class BrepCoedge(BrepEntity):
    edge_id: str
    pcurve_id: str
    reversed: bool
    if TYPE_CHECKING:
        EdgeId: ClassVar[str]
        PcurveId: ClassVar[str]
        IsReversed: ClassVar[bool]


# loops exist because face trimming boundaries require ordered connected coedges
@ModelDataMut(DefaultMap={"outer": False})
class BrepLoop(BrepEntity):
    coedge_ids: tuple[str, ...]
    outer: bool
    if TYPE_CHECKING:
        CoedgeIds: ClassVar[tuple[str, ...]]
        IsOuter: ClassVar[bool]


# some boundaries have no owning face so standalone coedge groups preserve them
@ModelDataMut(DefaultMap={"closed": False})
class BrepWire(BrepEntity):
    coedge_ids: tuple[str, ...]
    closed: bool
    if TYPE_CHECKING:
        CoedgeIds: ClassVar[tuple[str, ...]]
        IsClosed: ClassVar[bool]


# faces bind analytic surfaces to ordered trimming loops
@ModelDataMut(DefaultMap={"same_sense": True, "tolerance": 0.0})
class BrepFace(BrepEntity):
    surface_id: str
    loop_ids: tuple[str, ...]
    same_sense: bool
    tolerance: float
    if TYPE_CHECKING:
        SurfaceId: ClassVar[str]
        LoopIds: ClassVar[tuple[str, ...]]
        HasSameSense: ClassVar[bool]
        Tolerance: ClassVar[float]


# face uses preserve orientation when shells reuse face definitions
@ModelDataMut(DefaultMap={"reversed": False})
class BrepFaceUse(BrepEntity):
    face_id: str
    reversed: bool
    if TYPE_CHECKING:
        FaceId: ClassVar[str]
        IsReversed: ClassVar[bool]


# shells collect oriented faces and preserve closure state
@ModelDataMut(DefaultMap={"closed": False})
class BrepShell(BrepEntity):
    face_use_ids: tuple[str, ...]
    closed: bool
    if TYPE_CHECKING:
        FaceUseIds: ClassVar[tuple[str, ...]]
        IsClosed: ClassVar[bool]


# shell uses preserve orientation when regions reuse shell definitions
@ModelDataMut(DefaultMap={"reversed": False})
class BrepShellUse(BrepEntity):
    shell_id: str
    reversed: bool
    if TYPE_CHECKING:
        ShellId: ClassVar[str]
        IsReversed: ClassVar[bool]


# regions collect oriented shells and preserve solid classification
@ModelDataMut(DefaultMap={"solid": True})
class BrepRegion(BrepEntity):
    shell_use_ids: tuple[str, ...]
    solid: bool
    if TYPE_CHECKING:
        ShellUseIds: ClassVar[tuple[str, ...]]
        IsSolid: ClassVar[bool]


# bodies connect region wire and vertex topology to document design bodies
@ModelDataMut(
    DefaultMap={
        "transform": Transform(),
        "design_body_id": "",
        "wire_ids": (),
        "vertex_ids": (),
    }
)
class BrepBody(BrepEntity):
    region_ids: tuple[str, ...]
    transform: Transform
    design_body_id: str
    wire_ids: tuple[str, ...]
    vertex_ids: tuple[str, ...]
    if TYPE_CHECKING:
        RegionIds: ClassVar[tuple[str, ...]]
        Transform: ClassVar[Transform]
        DesignBodyId: ClassVar[str]
        WireIds: ClassVar[tuple[str, ...]]
        VertexIds: ClassVar[tuple[str, ...]]
