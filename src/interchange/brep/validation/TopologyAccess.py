# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Protocol as TypeProtocol

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


# topology passes need element reads and version pinning without geometry coupling
class TopologyAccess(TypeProtocol):

    # vertex access keeps point diagnostics independent of storage internals
    @property
    def vertices(self) -> tuple[BrepVertex, ...]: ...  # lgtm[py/ineffectual-statement]

    # edge access keeps connectivity diagnostics independent of storage internals
    @property
    def edges(self) -> tuple[BrepEdge, ...]: ...  # lgtm[py/ineffectual-statement]

    # coedge access lets sidedness checks run without storage coupling
    @property
    def coedges(self) -> tuple[BrepCoedge, ...]: ...  # lgtm[py/ineffectual-statement]

    # loop access keeps boundary checks independent of storage internals
    @property
    def loops(self) -> tuple[BrepLoop, ...]: ...  # lgtm[py/ineffectual-statement]

    # wire access keeps free edge checks independent of storage internals
    @property
    def wires(self) -> tuple[BrepWire, ...]: ...  # lgtm[py/ineffectual-statement]

    # face access keeps area checks independent of storage internals
    @property
    def faces(self) -> tuple[BrepFace, ...]: ...  # lgtm[py/ineffectual-statement]

    # face use access keeps sidedness checks independent of storage internals
    @property
    def face_uses(
        self,
    ) -> tuple[BrepFaceUse, ...]: ...  # lgtm[py/ineffectual-statement]

    # shell access keeps containment checks independent of storage internals
    @property
    def shells(self) -> tuple[BrepShell, ...]: ...  # lgtm[py/ineffectual-statement]

    # shell use access keeps polarity checks independent of storage internals
    @property
    def shell_uses(
        self,
    ) -> tuple[BrepShellUse, ...]: ...  # lgtm[py/ineffectual-statement]

    # region access keeps lump checks independent of storage internals
    @property
    def regions(self) -> tuple[BrepRegion, ...]: ...  # lgtm[py/ineffectual-statement]

    # body access keeps whole part checks independent of storage internals
    @property
    def bodies(self) -> tuple[BrepBody, ...]: ...  # lgtm[py/ineffectual-statement]

    # version pinning lets validators reject schemas they cannot reason about
    @property
    def schema_version(self) -> str: ...  # lgtm[py/ineffectual-statement]
