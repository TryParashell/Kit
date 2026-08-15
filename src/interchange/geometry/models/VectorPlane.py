# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import ClassVar, TYPE_CHECKING

from interchange.core.ModelBase import ModelBase, ModelDataMut


# planar vectors keep sketch coordinates distinct from spatial geometry
@ModelDataMut
class PlaneVector(ModelBase):
    x: float
    y: float
    if TYPE_CHECKING:
        XCoord: ClassVar[float]
        YCoord: ClassVar[float]
