# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.core.ModelBase import ModelBase, ModelDataMut


# spatial vectors give every geometry subsystem one coordinate contract
@ModelDataMut
class SpaceVector(ModelBase):
    x: float
    y: float
    z: float

    # component access keeps vector math readable without tuple indexing
    @property
    def XCoord(self) -> float:
        return self.x

    # component access keeps vector math readable without tuple indexing
    @property
    def YCoord(self) -> float:
        return self.y

    # component access keeps vector math readable without tuple indexing
    @property
    def ZCoord(self) -> float:
        return self.z
