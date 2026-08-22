# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass

from interchange.enums.EnumBase import WireEnum
from interchange.features.FeatureContract import FeatureDef
from interchange.records.RecordParameter import ParameterValue
from interchange.geometry.models.VectorSpace import SpaceVector


# extrusion bounds preserve editable termination intent instead of only distance
class ExtrudeEnd(WireEnum):
    BLIND = "blind"
    THROUGH_ALL = "through_all"
    UP_TO_FIRST = "up_to_first"
    UP_TO_LAST = "up_to_last"
    UP_TO_FACE = "up_to_face"
    UP_TO_SHAPE = "up_to_shape"
    UP_TO_VERTEX = "up_to_vertex"
    TWO_LENGTHS = "two_lengths"
    MID_PLANE = "mid_plane"
    OFFSET_FROM_SURFACE = "offset_from_surface"
    NATIVE = "native"
    KBlind = "blind"
    KThroughAll = "through_all"
    KUpToFirst = "up_to_first"
    KUpToLast = "up_to_last"
    KUpToFace = "up_to_face"
    KUpToShape = "up_to_shape"
    KUpToVertex = "up_to_vertex"
    KTwoLengths = "two_lengths"
    KMidPlane = "mid_plane"
    KOffsetSurface = "offset_from_surface"
    KNative = "native"


# extrusions retain directional and termination choices needed for reconstruction
@MakeDataClass(frozen=True, slots=True)
class ExtrudeFeature(FeatureDef):
    length: ParameterValue
    end_condition: ExtrudeEnd | str = ExtrudeEnd.KBlind
    reversed: bool = False
    symmetric: bool = False
    direction: SpaceVector | None = None
    second_length: ParameterValue | None = None
    second_end_condition: ExtrudeEnd | str | None = None
    offset: ParameterValue | None = None
    second_offset: ParameterValue | None = None
    draft_angle: ParameterValue | None = None
    second_draft_angle: ParameterValue | None = None
    up_to_reference: str = ""
    second_up_to_reference: str = ""

    @property
    def Length(self) -> ParameterValue:
        return self.length

    @property
    def EndCondition(self) -> ExtrudeEnd | str:
        return self.end_condition

    @property
    def IsReversed(self) -> bool:
        return self.reversed

    @property
    def IsSymmetric(self) -> bool:
        return self.symmetric

    @property
    def Direction(self) -> SpaceVector | None:
        return self.direction

    @property
    def SecondLength(self) -> ParameterValue | None:
        return self.second_length

    @property
    def SecondEndCondition(self) -> ExtrudeEnd | str | None:
        return self.second_end_condition

    @property
    def Offset(self) -> ParameterValue | None:
        return self.offset

    @property
    def SecondOffset(self) -> ParameterValue | None:
        return self.second_offset

    @property
    def DraftAngle(self) -> ParameterValue | None:
        return self.draft_angle

    @property
    def SecondDraftAngle(self) -> ParameterValue | None:
        return self.second_draft_angle

    @property
    def UpToReference(self) -> str:
        return self.up_to_reference

    @property
    def SecondUpToRef(self) -> str:
        return self.second_up_to_reference
