# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordParameter import ParameterValue


# configuration overrides preserve variant values without duplicating parameter definitions
@ModelDataMut
class ParamOverride(ModelBase):
    parameter_id: str
    value: ParameterValue

    # optional parameter link makes dimensions editable through records
    @property
    def ParameterId(self) -> str:
        return self.parameter_id

    # typed value keeps configuration usable without parsing conventions
    @property
    def Value(self) -> ParameterValue:
        return self.value


# configurations retain product variants and suppression state within one portable document
@ModelDataMut
class Configuration(ModelBase):
    id: str
    name: str
    active: bool = False
    parent_id: str | None = None
    overrides: tuple[ParamOverride, ...] = ()
    suppressed_feature_ids: tuple[str, ...] = ()
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

    # active flag marks the working configuration without deletion churn
    @property
    def IsActive(self) -> bool:
        return self.active

    # parent link keeps configuration inheritance resolvable in one walk
    @property
    def ParentId(self) -> str | None:
        return self.parent_id

    # override list isolates deltas instead of duplicating whole configurations
    @property
    def Overrides(self) -> tuple[ParamOverride, ...]:
        return self.overrides

    # suppression list captures configuration differences without cloned feature trees
    @property
    def SuppressedFeatureIds(self) -> tuple[str, ...]:
        return self.suppressed_feature_ids

    # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
