# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector

# shared frame defaults stay precomputed constants so parameter defaults never call constructors
KOriginZero: SpaceVector = SpaceVector(0.0, 0.0, 0.0)
KAxisX: SpaceVector = SpaceVector(1.0, 0.0, 0.0)
KAxisY: SpaceVector = SpaceVector(0.0, 1.0, 0.0)
KAxisZ: SpaceVector = SpaceVector(0.0, 0.0, 1.0)


# orthogonal frames preserve placement without assuming one vendor coordinate convention
@ModelDataMut
class Transform(ModelBase):
    origin: SpaceVector = KOriginZero
    x_axis: SpaceVector = KAxisX
    y_axis: SpaceVector = KAxisY
    z_axis: SpaceVector = KAxisZ

    @property
    def Origin(self) -> SpaceVector:
        return self.origin

    @property
    def XAxis(self) -> SpaceVector:
        return self.x_axis

    @property
    def YAxis(self) -> SpaceVector:
        return self.y_axis

    @property
    def ZAxis(self) -> SpaceVector:
        return self.z_axis


# one identity transform keeps placement defaults free of repeated constructor calls
KTransformIdentity: Transform = Transform()
