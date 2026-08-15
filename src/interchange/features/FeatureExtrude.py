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
    Length: ParameterValue
    EndCondition: ExtrudeEnd | str = ExtrudeEnd.KBlind
    IsReversed: bool = False
    IsSymmetric: bool = False
    Direction: SpaceVector | None = None
    SecondLength: ParameterValue | None = None
    SecondEndCondition: ExtrudeEnd | str | None = None
    Offset: ParameterValue | None = None
    SecondOffset: ParameterValue | None = None
    DraftAngle: ParameterValue | None = None
    SecondDraftAngle: ParameterValue | None = None
    UpToReference: str = ""
    SecondUpToRef: str = ""
