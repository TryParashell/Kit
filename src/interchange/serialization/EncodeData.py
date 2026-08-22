# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import base64 as BaseCodec
from collections.abc import Mapping as MappingBase
from collections.abc import Set as SetBase
from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
import json as JsonCodec
from typing import cast as CastValue

from interchange.serialization.Wire import GetWireField, GetWireType
from interchange.serialization.WireData import WireData


# unordered collections need canonical ordering so output remains stable across hash seeds
def OrderData(SourceValues: SetBase[object]) -> list[WireData]:
    EncodedValues = [ToData(ItemValue) for ItemValue in SourceValues]

    # canonical text ordering avoids dependence on collection hash iteration order
    def GetSortKey(ItemValue: WireData) -> str:
        return JsonCodec.dumps(
            ItemValue, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )

    return sorted(EncodedValues, key=GetSortKey)


# recursive encoding preserves every supported container and model type losslessly
def ToData(SourceValue: object) -> WireData:
    if IsDataClass(SourceValue) and not isinstance(SourceValue, type):
        ResultValue: dict[str, WireData] = {"$type": GetWireType(type(SourceValue))}
        for FieldValue in GetFields(SourceValue):
            ResultValue[GetWireField(FieldValue.name, type(SourceValue))] = ToData(
                CastValue(object, getattr(SourceValue, FieldValue.name))
            )
        return ResultValue
    if isinstance(SourceValue, EnumBase):
        return {
            "$enum": GetWireType(type(SourceValue)),
            "value": ToData(CastValue(object, SourceValue.value)),
        }
    if isinstance(SourceValue, bytes):
        return {"$bytes": BaseCodec.b64encode(SourceValue).decode("ascii")}
    if isinstance(SourceValue, tuple):
        TupleValue = CastValue(tuple[object, ...], SourceValue)
        return {"$tuple": [ToData(ItemValue) for ItemValue in TupleValue]}
    if isinstance(SourceValue, frozenset):
        FrozenValues = CastValue(frozenset[object], SourceValue)
        return {"$frozenset": OrderData(FrozenValues)}
    if isinstance(SourceValue, set):
        MutableValues = CastValue(set[object], SourceValue)
        return {"$set": OrderData(MutableValues)}
    if isinstance(SourceValue, list):
        ListValue = CastValue(list[object], SourceValue)
        return [ToData(ItemValue) for ItemValue in ListValue]
    if isinstance(SourceValue, MappingBase):
        MapValue = CastValue(MappingBase[object, object], SourceValue)
        ResultValue = {}
        for KeyValue, ItemValue in MapValue.items():
            if not isinstance(KeyValue, str):
                raise TypeError("wire object keys must be strings")
            ResultValue[KeyValue] = ToData(ItemValue)
        return ResultValue
    if SourceValue is None or isinstance(SourceValue, (str, int, float, bool)):
        return SourceValue
    raise TypeError(f"cannot serialize value of type {type(SourceValue).__name__}")
