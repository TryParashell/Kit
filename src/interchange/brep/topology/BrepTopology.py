# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField

from interchange.brep.curves.BrepCurves import BrepEntity
from interchange.records.RecordProvenance import Provenance
from typing import Mapping as TypeMap
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelDataMut
from interchange.geometry.models.Transform import Transform, KTransformIdentity
from interchange.geometry.models.VectorSpace import SpaceVector


# vertices anchor topological incidence to precise spatial points
@ModelDataMut
class BrepVertex(BrepEntity):
    id: str
    point: SpaceVector
    tolerance: float = 0.0
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stored position keeps vertices self contained without coordinate lookups
    @property
    def Point(self) -> SpaceVector:
        return self.point

     # tolerance bounds approximation error so consumers can trust comparisons
    @property
    def Tolerance(self) -> float:
        return self.tolerance


# edges connect vertices through exact curve parameter intervals
@ModelDataMut
class BrepEdge(BrepEntity):
    id: str
    start_vertex_id: str
    end_vertex_id: str
    curve_id: str
    start_parameter: float
    end_parameter: float
    tolerance: float = 0.0
    degenerate: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # endpoint links keep edge traversal possible without geometric matching
    @property
    def StartVertexId(self) -> str:
        return self.start_vertex_id

     # closing endpoint keeps edge ranges complete without geometric matching
    @property
    def EndVertexId(self) -> str:
        return self.end_vertex_id

     # curve link keeps edges defined once and shared across faces
    @property
    def CurveId(self) -> str:
        return self.curve_id

     # trim range bounds the used portion so shared curves stay reusable
    @property
    def StartParameter(self) -> float:
        return self.start_parameter

     # trim end completes the range so trimming needs no heuristics
    @property
    def EndParameter(self) -> float:
        return self.end_parameter

     # tolerance bounds approximation error so consumers can trust comparisons
    @property
    def Tolerance(self) -> float:
        return self.tolerance

     # degeneracy flag protects downstream math from zero length edges
    @property
    def IsDegenerate(self) -> bool:
        return self.degenerate


# coedges preserve oriented edge use and optional parameter curve bindings
@ModelDataMut
class BrepCoedge(BrepEntity):
    id: str
    edge_id: str
    pcurve_id: str = ""
    reversed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # owning edge keeps pcurves attached to their carrier topology
    @property
    def EdgeId(self) -> str:
        return self.edge_id

     # pcurve link ties each surface side to its own parametric curve
    @property
    def PcurveId(self) -> str:
        return self.pcurve_id

     # orientation flag preserves which side of the topology is used
    @property
    def IsReversed(self) -> bool:
        return self.reversed


# loops exist because face trimming boundaries require ordered connected coedges
@ModelDataMut
class BrepLoop(BrepEntity):
    id: str
    coedge_ids: tuple[str, ...]
    outer: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # coedge ordering keeps loop traversal deterministic for validation passes
    @property
    def CoedgeIds(self) -> tuple[str, ...]:
        return self.coedge_ids

     # outer flag distinguishes material boundaries from holes during face classification
    @property
    def IsOuter(self) -> bool:
        return self.outer


# some boundaries have no owning face so standalone coedge groups preserve them
@ModelDataMut
class BrepWire(BrepEntity):
    id: str
    coedge_ids: tuple[str, ...]
    closed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # coedge ordering keeps loop traversal deterministic for validation passes
    @property
    def CoedgeIds(self) -> tuple[str, ...]:
        return self.coedge_ids

     # closure flag tells solids apart from open shells without searching
    @property
    def IsClosed(self) -> bool:
        return self.closed


# faces bind analytic surfaces to ordered trimming loops
@ModelDataMut
class BrepFace(BrepEntity):
    id: str
    surface_id: str
    loop_ids: tuple[str, ...]
    same_sense: bool = True
    tolerance: float = 0.0
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # surface link attaches faces to their geometry without duplication
    @property
    def SurfaceId(self) -> str:
        return self.surface_id

     # loop list keeps face boundaries enumerable in stable order
    @property
    def LoopIds(self) -> tuple[str, ...]:
        return self.loop_ids

     # sense agreement keeps normal orientation consistent between face and surface
    @property
    def HasSameSense(self) -> bool:
        return self.same_sense

     # tolerance bounds approximation error so consumers can trust comparisons
    @property
    def Tolerance(self) -> float:
        return self.tolerance


# face uses preserve orientation when shells reuse face definitions
@ModelDataMut
class BrepFaceUse(BrepEntity):
    id: str
    face_id: str
    reversed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # face link anchors shell uses to concrete boundary elements
    @property
    def FaceId(self) -> str:
        return self.face_id

     # orientation flag preserves which side of the topology is used
    @property
    def IsReversed(self) -> bool:
        return self.reversed


# shells collect oriented faces and preserve closure state
@ModelDataMut
class BrepShell(BrepEntity):
    id: str
    face_use_ids: tuple[str, ...]
    closed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # face use list keeps shell composition explicit and ordered
    @property
    def FaceUseIds(self) -> tuple[str, ...]:
        return self.face_use_ids

     # closure flag tells solids apart from open shells without searching
    @property
    def IsClosed(self) -> bool:
        return self.closed


# shell uses preserve orientation when regions reuse shell definitions
@ModelDataMut
class BrepShellUse(BrepEntity):
    id: str
    shell_id: str
    reversed: bool = False
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # shell link keeps lump composition explicit for solid classification
    @property
    def ShellId(self) -> str:
        return self.shell_id

     # orientation flag preserves which side of the topology is used
    @property
    def IsReversed(self) -> bool:
        return self.reversed


# regions collect oriented shells and preserve solid classification
@ModelDataMut
class BrepRegion(BrepEntity):
    id: str
    shell_use_ids: tuple[str, ...]
    solid: bool = True
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # shell use list keeps region composition explicit and ordered
    @property
    def ShellUseIds(self) -> tuple[str, ...]:
        return self.shell_use_ids

     # solidity flag separates watertight lumps from open shells quickly
    @property
    def IsSolid(self) -> bool:
        return self.solid


# bodies connect region wire and vertex topology to document design bodies
@ModelDataMut
class BrepBody(BrepEntity):
    id: str
    region_ids: tuple[str, ...]
    transform: Transform = KTransformIdentity
    design_body_id: str = ""
    wire_ids: tuple[str, ...] = ()
    vertex_ids: tuple[str, ...] = ()
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # region list keeps disjoint lumps enumerable within one body
    @property
    def RegionIds(self) -> tuple[str, ...]:
        return self.region_ids

     # local transform keeps world placement composable through parent chains
    @property
    def Transform(self) -> Transform:
        return self.transform

     # design body link connects analytic brep back to consumer models
    @property
    def DesignBodyId(self) -> str:
        return self.design_body_id

     # wire list keeps free edges visible outside face boundaries
    @property
    def WireIds(self) -> tuple[str, ...]:
        return self.wire_ids

     # vertex list keeps isolated points addressable inside bodies
    @property
    def VertexIds(self) -> tuple[str, ...]:
        return self.vertex_ids
