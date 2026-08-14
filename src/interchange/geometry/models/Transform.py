# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# orthogonal frames preserve placement without assuming one vendor coordinate convention
@ModelDataMut(
    DefaultMap={
        "Origin": SpaceVector(0.0, 0.0, 0.0),
        "XAxis": SpaceVector(1.0, 0.0, 0.0),
        "YAxis": SpaceVector(0.0, 1.0, 0.0),
        "ZAxis": SpaceVector(0.0, 0.0, 1.0),
    }
)
class Transform(ModelBase):
    Origin: SpaceVector
    XAxis: SpaceVector
    YAxis: SpaceVector
    ZAxis: SpaceVector
