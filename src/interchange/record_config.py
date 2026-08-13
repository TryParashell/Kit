# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .common import FreezeMapping
from .model_base import ModelBase, ModelDataMut
from .record_parameter import ParameterValue


# configuration overrides preserve variant values without duplicating parameter definitions
@ModelDataMut
class ParamOverride(ModelBase):
    ParameterId: str
    Value: ParameterValue


# configurations retain product variants and suppression state within one portable document
@ModelDataMut(
    DefaultMap={
        "IsActive": False,
        "ParentId": None,
        "Overrides": (),
        "SuppressedFeatureIds": (),
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class Configuration(ModelBase):
    EntityId: str
    EntityName: str
    IsActive: bool
    ParentId: str | None
    Overrides: tuple[ParamOverride, ...]
    SuppressedFeatureIds: tuple[str, ...]
    Attributes: TypeMap[str, AnyValue]
