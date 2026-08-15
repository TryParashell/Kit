# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import TYPE_CHECKING, ClassVar

from interchange.core.ModelBase import ModelBase, ModelDataMut


# spatial vectors give every geometry subsystem one coordinate contract
@ModelDataMut
class SpaceVector(ModelBase):
    XCoord: float
    YCoord: float
    ZCoord: float
    if TYPE_CHECKING:
        x: ClassVar[float]
        y: ClassVar[float]
        z: ClassVar[float]
