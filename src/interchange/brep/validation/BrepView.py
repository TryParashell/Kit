# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Protocol as TypeProtocol

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


# the validation view decouples topology storage from independent diagnostic passes
class BrepView(TypeProtocol):
    @property
    def curves(self) -> tuple[BrepCurve, ...]: ...
    @property
    def pcurves(self) -> tuple[BrepPcurve, ...]: ...
    @property
    def surfaces(self) -> tuple[BrepSurface, ...]: ...
    @property
    def vertices(self) -> tuple[BrepVertex, ...]: ...
    @property
    def edges(self) -> tuple[BrepEdge, ...]: ...
    @property
    def coedges(self) -> tuple[BrepCoedge, ...]: ...
    @property
    def loops(self) -> tuple[BrepLoop, ...]: ...
    @property
    def wires(self) -> tuple[BrepWire, ...]: ...
    @property
    def faces(self) -> tuple[BrepFace, ...]: ...
    @property
    def face_uses(self) -> tuple[BrepFaceUse, ...]: ...
    @property
    def shells(self) -> tuple[BrepShell, ...]: ...
    @property
    def shell_uses(self) -> tuple[BrepShellUse, ...]: ...
    @property
    def regions(self) -> tuple[BrepRegion, ...]: ...
    @property
    def bodies(self) -> tuple[BrepBody, ...]: ...
    @property
    def schema_version(self) -> str: ...
