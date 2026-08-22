# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations


from interchange.brep.curves.BrepCurves import BrepEntity
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.Transform import Transform, KTransformIdentity
from interchange.geometry.models.VectorSpace import SpaceVector


# vertices anchor topological incidence to precise spatial points
@ModelDataMut
class BrepVertex(BrepEntity):
    point: SpaceVector
    tolerance: float = 0.0

    @property
    def Point(self) -> SpaceVector:
        return self.point

    @property
    def Tolerance(self) -> float:
        return self.tolerance


# edges connect vertices through exact curve parameter intervals
@ModelDataMut
class BrepEdge(BrepEntity):
    start_vertex_id: str
    end_vertex_id: str
    curve_id: str
    start_parameter: float
    end_parameter: float
    tolerance: float = 0.0
    degenerate: bool = False

    @property
    def StartVertexId(self) -> str:
        return self.start_vertex_id

    @property
    def EndVertexId(self) -> str:
        return self.end_vertex_id

    @property
    def CurveId(self) -> str:
        return self.curve_id

    @property
    def StartParameter(self) -> float:
        return self.start_parameter

    @property
    def EndParameter(self) -> float:
        return self.end_parameter

    @property
    def Tolerance(self) -> float:
        return self.tolerance

    @property
    def IsDegenerate(self) -> bool:
        return self.degenerate


# coedges preserve oriented edge use and optional parameter curve bindings
@ModelDataMut
class BrepCoedge(BrepEntity):
    edge_id: str
    pcurve_id: str = ""
    reversed: bool = False

    @property
    def EdgeId(self) -> str:
        return self.edge_id

    @property
    def PcurveId(self) -> str:
        return self.pcurve_id

    @property
    def IsReversed(self) -> bool:
        return self.reversed


# loops exist because face trimming boundaries require ordered connected coedges
@ModelDataMut
class BrepLoop(BrepEntity):
    coedge_ids: tuple[str, ...]
    outer: bool = False

    @property
    def CoedgeIds(self) -> tuple[str, ...]:
        return self.coedge_ids

    @property
    def IsOuter(self) -> bool:
        return self.outer


# some boundaries have no owning face so standalone coedge groups preserve them
@ModelDataMut
class BrepWire(BrepEntity):
    coedge_ids: tuple[str, ...]
    closed: bool = False

    @property
    def CoedgeIds(self) -> tuple[str, ...]:
        return self.coedge_ids

    @property
    def IsClosed(self) -> bool:
        return self.closed


# faces bind analytic surfaces to ordered trimming loops
@ModelDataMut
class BrepFace(BrepEntity):
    surface_id: str
    loop_ids: tuple[str, ...]
    same_sense: bool = True
    tolerance: float = 0.0

    @property
    def SurfaceId(self) -> str:
        return self.surface_id

    @property
    def LoopIds(self) -> tuple[str, ...]:
        return self.loop_ids

    @property
    def HasSameSense(self) -> bool:
        return self.same_sense

    @property
    def Tolerance(self) -> float:
        return self.tolerance


# face uses preserve orientation when shells reuse face definitions
@ModelDataMut
class BrepFaceUse(BrepEntity):
    face_id: str
    reversed: bool = False

    @property
    def FaceId(self) -> str:
        return self.face_id

    @property
    def IsReversed(self) -> bool:
        return self.reversed


# shells collect oriented faces and preserve closure state
@ModelDataMut
class BrepShell(BrepEntity):
    face_use_ids: tuple[str, ...]
    closed: bool = False

    @property
    def FaceUseIds(self) -> tuple[str, ...]:
        return self.face_use_ids

    @property
    def IsClosed(self) -> bool:
        return self.closed


# shell uses preserve orientation when regions reuse shell definitions
@ModelDataMut
class BrepShellUse(BrepEntity):
    shell_id: str
    reversed: bool = False

    @property
    def ShellId(self) -> str:
        return self.shell_id

    @property
    def IsReversed(self) -> bool:
        return self.reversed


# regions collect oriented shells and preserve solid classification
@ModelDataMut
class BrepRegion(BrepEntity):
    shell_use_ids: tuple[str, ...]
    solid: bool = True

    @property
    def ShellUseIds(self) -> tuple[str, ...]:
        return self.shell_use_ids

    @property
    def IsSolid(self) -> bool:
        return self.solid


# bodies connect region wire and vertex topology to document design bodies
@ModelDataMut
class BrepBody(BrepEntity):
    region_ids: tuple[str, ...]
    transform: Transform = KTransformIdentity
    design_body_id: str = ""
    wire_ids: tuple[str, ...] = ()
    vertex_ids: tuple[str, ...] = ()

    @property
    def RegionIds(self) -> tuple[str, ...]:
        return self.region_ids

    @property
    def Transform(self) -> Transform:
        return self.transform

    @property
    def DesignBodyId(self) -> str:
        return self.design_body_id

    @property
    def WireIds(self) -> tuple[str, ...]:
        return self.wire_ids

    @property
    def VertexIds(self) -> tuple[str, ...]:
        return self.vertex_ids
