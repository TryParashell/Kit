# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from types import MappingProxyType as FrozenMap
from typing import Any as AnyValue
from typing import Mapping as TypeMap


# recursive scalar typing exists because payload contracts must reject unsupported primitive values
KJsonScalar = str | int | float | bool | None


# recursive container typing exists because adapters retain nested native metadata losslessly
KJsonValue = KJsonScalar | list["KJsonValue"] | dict[str, "KJsonValue"]


# immutable mappings prevent accidental mutation of frozen interchange records
def FreezeMapping(
    SourceValues: TypeMap[str, AnyValue] | None = None,
) -> TypeMap[str, AnyValue]:
    return FrozenMap(dict(SourceValues or {}))
