# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import ClassVar, TYPE_CHECKING

from interchange.enums.EnumBase import WireEnum
from interchange.features.FeatureContract import FeatureDef
from interchange.records.RecordParameter import ParameterValue
from interchange.geometry.models.VectorSpace import SpaceVector


# extrusion bounds preserve editable termination intent instead of only distance
class ExtrudeEnd(WireEnum):
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
    if TYPE_CHECKING:
        Length: ClassVar[ParameterValue]
        EndCondition: ClassVar[ExtrudeEnd | str]
        IsReversed: ClassVar[bool]
        IsSymmetric: ClassVar[bool]
        Direction: ClassVar[SpaceVector | None]
        SecondLength: ClassVar[ParameterValue | None]
        SecondEndCondition: ClassVar[ExtrudeEnd | str | None]
        Offset: ClassVar[ParameterValue | None]
        SecondOffset: ClassVar[ParameterValue | None]
        DraftAngle: ClassVar[ParameterValue | None]
        SecondDraftAngle: ClassVar[ParameterValue | None]
        UpToReference: ClassVar[str]
        SecondUpToRef: ClassVar[str]
