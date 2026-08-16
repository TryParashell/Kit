# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from types import MappingProxyType as FrozenMap
from typing import Mapping as TypeMap
from typing import overload as TypeOverload
from typing import TypeVar


# recursive scalar typing exists because payload contracts must reject unsupported primitive values
KJsonScalar = str | int | float | bool | None


# recursive container typing exists because adapters retain nested native metadata losslessly
KJsonValue = KJsonScalar | list["KJsonValue"] | dict[str, "KJsonValue"]


# mapping factories preserve each caller value type without widening it to any
MapValue = TypeVar("MapValue")


# empty immutable mappings provide a concrete object value contract for default factories
@TypeOverload
def FreezeMapping() -> TypeMap[str, object]: ...  # lgtm[py/ineffectual-statement]


# populated immutable mappings retain their precise member type for model fields
@TypeOverload
def FreezeMapping(  # lgtm[py/ineffectual-statement]
    SourceValues: TypeMap[str, MapValue],
) -> TypeMap[str, MapValue]: ...


# immutable mappings prevent accidental mutation of frozen interchange records
def FreezeMapping(
    SourceValues: TypeMap[str, MapValue] | None = None,
) -> TypeMap[str, MapValue] | TypeMap[str, object]:
    return FrozenMap(dict(SourceValues or {}))
