# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Mapping
from typing import TypeGuard


# tuple narrowing prevents recursive metadata from leaking unknown element types
def IsObjectTuple(Value: object) -> TypeGuard[tuple[object, ...]]:
    return isinstance(Value, tuple)


# mapping narrowing prevents recursive metadata from leaking unknown key and value types
def IsObjectMap(Value: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(Value, Mapping)


# recursive metadata rows need runtime validation before tests inspect nested fields
def GetObjectRows(Value: object) -> tuple[Mapping[str, object], ...]:
    if not IsObjectTuple(Value):
        raise TypeError("metadata rows must be a tuple")
    Rows: list[Mapping[str, object]] = []
    for RowValue in Value:
        if not IsObjectMap(RowValue):
            raise TypeError("metadata rows must contain mappings")
        CheckedRow: dict[str, object] = {}
        for KeyValue, ItemValue in RowValue.items():
            if not isinstance(KeyValue, str):
                raise TypeError("metadata row keys must be strings")
            CheckedRow[KeyValue] = ItemValue
        Rows.append(CheckedRow)
    return tuple(Rows)


# recursive symbol metadata needs runtime validation before membership checks remain typed
def GetStringTuple(Value: object) -> tuple[str, ...]:
    if not IsObjectTuple(Value):
        raise TypeError("metadata strings must be a tuple")
    Strings: list[str] = []
    for ItemValue in Value:
        if not isinstance(ItemValue, str):
            raise TypeError("metadata string tuples must contain strings")
        Strings.append(ItemValue)
    return tuple(Strings)


# recursive scalar metadata needs runtime validation before path construction remains typed
def GetString(Value: object) -> str:
    if not isinstance(Value, str):
        raise TypeError("metadata value must be a string")
    return Value
