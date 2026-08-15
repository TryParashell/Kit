# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange.brep.curves.BrepCurves import BrepCurve
from interchange.brep.curves.BrepPcurves import BrepPcurve
from interchange.brep.surfaces.BrepSurfaces import BrepSurface
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
    BrepWire,
)
from interchange.core.ModelBase import ModelBase, ModelDataMut


# boundary models aggregate analytic geometry and incidence into one neutral graph
@ModelDataMut(
    DefaultMap={
        "curves": (),
        "pcurves": (),
        "surfaces": (),
        "vertices": (),
        "edges": (),
        "coedges": (),
        "loops": (),
        "wires": (),
        "faces": (),
        "face_uses": (),
        "shells": (),
        "shell_uses": (),
        "regions": (),
        "bodies": (),
        "schema_version": "1.0",
    }
)
class BrepModel(ModelBase):
    curves: tuple[BrepCurve, ...]
    pcurves: tuple[BrepPcurve, ...]
    surfaces: tuple[BrepSurface, ...]
    vertices: tuple[BrepVertex, ...]
    edges: tuple[BrepEdge, ...]
    coedges: tuple[BrepCoedge, ...]
    loops: tuple[BrepLoop, ...]
    wires: tuple[BrepWire, ...]
    faces: tuple[BrepFace, ...]
    face_uses: tuple[BrepFaceUse, ...]
    shells: tuple[BrepShell, ...]
    shell_uses: tuple[BrepShellUse, ...]
    regions: tuple[BrepRegion, ...]
    bodies: tuple[BrepBody, ...]
    schema_version: str

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Curves(self) -> tuple[BrepCurve, ...]:
        return self.curves

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Pcurves(self) -> tuple[BrepPcurve, ...]:
        return self.pcurves

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Surfaces(self) -> tuple[BrepSurface, ...]:
        return self.surfaces

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Vertices(self) -> tuple[BrepVertex, ...]:
        return self.vertices

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Edges(self) -> tuple[BrepEdge, ...]:
        return self.edges

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Coedges(self) -> tuple[BrepCoedge, ...]:
        return self.coedges

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Loops(self) -> tuple[BrepLoop, ...]:
        return self.loops

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Wires(self) -> tuple[BrepWire, ...]:
        return self.wires

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Faces(self) -> tuple[BrepFace, ...]:
        return self.faces

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def FaceUses(self) -> tuple[BrepFaceUse, ...]:
        return self.face_uses

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Shells(self) -> tuple[BrepShell, ...]:
        return self.shells

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def ShellUses(self) -> tuple[BrepShellUse, ...]:
        return self.shell_uses

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Regions(self) -> tuple[BrepRegion, ...]:
        return self.regions

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def Bodies(self) -> tuple[BrepBody, ...]:
        return self.bodies

    # pascal consumers remain typed while lowercase fields own dataclass storage
    @property
    def SchemaVersion(self) -> str:
        return self.schema_version

    # model validation delegates because topology checks change independently from storage
    def GetErrors(self, DesignBodyIds: frozenset[str] = frozenset()) -> tuple[str, ...]:
        from interchange.brep.validation.BrepValidate import GetBrepErrors

        return GetBrepErrors(self, DesignBodyIds)
