# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordParameter import ParameterValue


# configuration overrides preserve variant values without duplicating parameter definitions
@ModelDataMut
class ParamOverride(ModelBase):
    parameter_id: str
    value: ParameterValue
    if TYPE_CHECKING:
        ParameterId: ClassVar[str]
        Value: ClassVar[ParameterValue]


# configurations retain product variants and suppression state within one portable document
@ModelDataMut(
    DefaultMap={
        "active": False,
        "parent_id": None,
        "overrides": (),
        "suppressed_feature_ids": (),
    },
    FactoryMap={"attributes": FreezeMapping},
)
class Configuration(ModelBase):
    id: str
    name: str
    active: bool
    parent_id: str | None
    overrides: tuple[ParamOverride, ...]
    suppressed_feature_ids: tuple[str, ...]
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        IsActive: ClassVar[bool]
        ParentId: ClassVar[str | None]
        Overrides: ClassVar[tuple[ParamOverride, ...]]
        SuppressedFeatureIds: ClassVar[tuple[str, ...]]
        Attributes: ClassVar[TypeMap[str, object]]
