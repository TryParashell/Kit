# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue
from typing import Mapping as TypeMap
from typing import TypeAlias

# wire values need one recursive contract shared by every serialization boundary
WireData: TypeAlias = (
    None | bool | int | float | str | list["WireData"] | dict[str, "WireData"]
)


# untrusted parser output must satisfy the recursive wire contract before decoding
def ValidateWireData(SourceValue: object) -> WireData:
    if SourceValue is None or isinstance(SourceValue, (bool, int, float, str)):
        return SourceValue
    if isinstance(SourceValue, list):
        ListItems = CastValue(list[object], SourceValue)
        return [ValidateWireData(ItemValue) for ItemValue in ListItems]
    if isinstance(SourceValue, dict):
        DictItems = CastValue(dict[object, object], SourceValue)
        ResultValue: dict[str, WireData] = {}
        for KeyValue, ItemValue in DictItems.items():
            if not isinstance(KeyValue, str):
                raise TypeError("wire object keys must be strings")
            ResultValue[KeyValue] = ValidateWireData(ItemValue)
        return ResultValue
    raise TypeError(f"unsupported wire value type {type(SourceValue).__name__}")


# document restoration requires a recursive object root rather than an arbitrary wire scalar
def ValidateWireMap(SourceValue: object) -> TypeMap[str, WireData]:
    DataValue = ValidateWireData(SourceValue)
    if not isinstance(DataValue, dict):
        raise TypeError("wire document root must be an object")
    return DataValue
