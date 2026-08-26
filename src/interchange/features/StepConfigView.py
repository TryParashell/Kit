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

from interchange.enums.EnumFeatures import BooleanOp

if IsTypeCheck:
    from interchange.features.FeatureContract import FeatureDef
    from interchange.features.FeatureStep import (
        FeatureCfgState,  # lgtm[py/unsafe-cyclic-import]
    )


# rebuild engines read parameters definitions and state through one typed view
class StepConfigView:
    __slots__ = ()

    # parameter links keep mate values driven by configurable expressions
    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "parameter_ids"))

    # boolean operation names the combine subtract or keep intent explicitly
    @property
    def Operation(self) -> BooleanOp | str | None:
        return CastValue(BooleanOp | str | None, getattr(self, "operation"))

    # linked definition keeps feature configuration editable after creation
    @property
    def Definition(self) -> FeatureDef | None:
        return CastValue("FeatureDef | None", getattr(self, "definition"))

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return CastValue(bool, getattr(self, "suppressed"))

    # per configuration states capture suppression without duplicated features
    @property
    def ConfigStates(self) -> "tuple[FeatureCfgState, ...]":
        return CastValue(
            "tuple[FeatureCfgState, ...]", getattr(self, "configuration_states")
        )
