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

from interchange.records.RecordParameter import ParameterValue

if IsTypeCheck:
    from interchange.features.FeatureExtrude import ExtrudeEnd


# two sided extrusion consumers read secondary caps and offsets through one view
class ExtrudeSecond:
    __slots__: tuple[str, ...] = ()

    # second length supports two sided extrudes without synthetic features
    @property
    def SecondLength(self) -> ParameterValue | None:
        return CastValue(ParameterValue | None, getattr(self, "second_length"))

    # second end condition keeps asymmetric caps expressible in one step
    @property
    def SecondEndCondition(self) -> "ExtrudeEnd | str | None":
        return CastValue(
            "ExtrudeEnd | str | None",
            getattr(self, "second_end_condition"),
        )

    # second offset keeps two sided starts independently controllable
    @property
    def SecondOffset(self) -> ParameterValue | None:
        return CastValue(ParameterValue | None, getattr(self, "second_offset"))

    # second draft angle keeps tapered two sided walls expressible
    @property
    def SecondDraftAngle(self) -> ParameterValue | None:
        return CastValue(ParameterValue | None, getattr(self, "second_draft_angle"))

    # second target keeps two sided up to extrudes symmetric in capability
    @property
    def SecondUpToRef(self) -> str:
        return CastValue(str, getattr(self, "second_up_to_reference"))
