# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector


# spatial bounds support planning without forcing complete geometry traversal
@ModelDataMut
class BoundingBox(ModelBase):
    minimum: SpaceVector
    maximum: SpaceVector

     # lower corner keeps box tests allocation free and branch simple
    @property
    def Minimum(self) -> SpaceVector:
        return self.minimum

     # upper corner completes the extent so containment tests stay trivial
    @property
    def Maximum(self) -> SpaceVector:
        return self.maximum
