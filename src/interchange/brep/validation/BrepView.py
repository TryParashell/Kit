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
    def curves(self) -> tuple[BrepCurve, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def pcurves(self) -> tuple[BrepPcurve, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def surfaces(self) -> tuple[BrepSurface, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def vertices(self) -> tuple[BrepVertex, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def edges(self) -> tuple[BrepEdge, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def coedges(self) -> tuple[BrepCoedge, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def loops(self) -> tuple[BrepLoop, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def wires(self) -> tuple[BrepWire, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def faces(self) -> tuple[BrepFace, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def face_uses(
        self,
    ) -> tuple[BrepFaceUse, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def shells(self) -> tuple[BrepShell, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def shell_uses(
        self,
    ) -> tuple[BrepShellUse, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def regions(self) -> tuple[BrepRegion, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def bodies(self) -> tuple[BrepBody, ...]: ...  # lgtm[py/ineffectual-statement]
    @property
    def schema_version(self) -> str: ...  # lgtm[py/ineffectual-statement]
