# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import ClassVar, TYPE_CHECKING

from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# orthogonal frames preserve placement without assuming one vendor coordinate convention
@ModelDataMut(
    DefaultMap={
        "origin": SpaceVector(0.0, 0.0, 0.0),
        "x_axis": SpaceVector(1.0, 0.0, 0.0),
        "y_axis": SpaceVector(0.0, 1.0, 0.0),
        "z_axis": SpaceVector(0.0, 0.0, 1.0),
    }
)
class Transform(ModelBase):
    origin: SpaceVector
    x_axis: SpaceVector
    y_axis: SpaceVector
    z_axis: SpaceVector
    if TYPE_CHECKING:
        Origin: ClassVar[SpaceVector]
        XAxis: ClassVar[SpaceVector]
        YAxis: ClassVar[SpaceVector]
        ZAxis: ClassVar[SpaceVector]
