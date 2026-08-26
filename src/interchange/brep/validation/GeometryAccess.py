# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Protocol as TypeProtocol

from interchange.brep.curves.BrepCurves import BrepCurve
from interchange.brep.curves.BrepPcurves import BrepPcurve
from interchange.brep.surfaces.BrepSurfaces import BrepSurface


# geometry passes need curve and surface reads without any topology storage coupling
class GeometryAccess(TypeProtocol):

    # curve access lets validation passes read topology without touching storage
    @property
    def curves(self) -> tuple[BrepCurve, ...]: ...  # lgtm[py/ineffectual-statement]

    # pcurve access keeps parametric checks independent of storage internals
    @property
    def pcurves(self) -> tuple[BrepPcurve, ...]: ...  # lgtm[py/ineffectual-statement]

    # surface access lets validation passes read geometry without touching storage
    @property
    def surfaces(self) -> tuple[BrepSurface, ...]: ...  # lgtm[py/ineffectual-statement]
