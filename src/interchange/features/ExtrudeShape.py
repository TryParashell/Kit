# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as IsTypeCheck
from typing import cast as CastValue

from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordParameter import ParameterValue

if IsTypeCheck:
    from interchange.features.FeatureExtrude import ExtrudeEnd


# single sided extrusion consumers read primary direction bounds through one view
class ExtrudeShape:
    __slots__: tuple[str, ...] = ()

    # extrusion length defines prism height without evaluating geometry
    @property
    def Length(self) -> ParameterValue:
        return CastValue(ParameterValue, getattr(self, "length"))

    # end condition captures blind through all and up to semantics in one field
    @property
    def EndCondition(self) -> "ExtrudeEnd | str":
        return CastValue("ExtrudeEnd | str", getattr(self, "end_condition"))

    # orientation flag preserves which side of the topology is used
    @property
    def IsReversed(self) -> bool:
        return CastValue(bool, getattr(self, "reversed"))

    # symmetric mode doubles length automatically so writers need no second value
    @property
    def IsSymmetric(self) -> bool:
        return CastValue(bool, getattr(self, "symmetric"))

    # unit heading keeps linear geometry orientation explicit for writers
    @property
    def Direction(self) -> SpaceVector | None:
        return CastValue(SpaceVector | None, getattr(self, "direction"))

    # start offset lets extrudes begin away from the sketch plane
    @property
    def Offset(self) -> ParameterValue | None:
        return CastValue(ParameterValue | None, getattr(self, "offset"))

    # draft angle encodes mold pull so solids survive manufacturing review
    @property
    def DraftAngle(self) -> ParameterValue | None:
        return CastValue(ParameterValue | None, getattr(self, "draft_angle"))

    # target reference makes length follow existing geometry instead of magic numbers
    @property
    def UpToReference(self) -> str:
        return CastValue(str, getattr(self, "up_to_reference"))
