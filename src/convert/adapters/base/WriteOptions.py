# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.ContractCompat import ContractBase


# write policy stays immutable so staging and adapters share one transactional intent
@DataClass(frozen=True, slots=True)
class WriteOptions(ContractBase):
    ConfigName: str | None = None
    Overwrite: bool = False
    Validate: bool = True
    TargetFormat: str | None = None
    OptionValues: TypeMap[str, AnyValue] = DataField(default_factory=FreezeMapping)
