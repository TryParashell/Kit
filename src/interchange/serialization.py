# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import base64 as BaseCodec
from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from enum import Enum as EnumBase
import json as JsonCodec
from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig
from typing import Any as AnyValue
from typing import Callable as CallableType
from typing import Mapping as TypeMap
from .wire import GetWireField, GetWireType

# registered types allow wire data to reconstruct concrete immutable records safely
KTypeRegistry: dict[str, type] = {}

# migrations preserve old documents when record schemas evolve compatibly
KMigrationRegistry: dict[
    type, CallableType[[TypeMap[str, AnyValue]], TypeMap[str, AnyValue]]
] = {}


# explicit registration prevents deserialization from importing arbitrary classes by name
def RegisterTypes(*ClassTypes: type) -> None:
    for ClassType in ClassTypes:
        WireType = GetWireType(ClassType)
        ExistingType = KTypeRegistry.get(WireType)
        if ExistingType is not None and ExistingType is not ClassType:
            raise ValueError(f"duplicate interchange type name {WireType!r}")
        KTypeRegistry[WireType] = ClassType


# schema migrations belong beside registration so decoding applies them consistently
def RegMigration(
    TargetType: type,
    MigrationFunc: CallableType[[TypeMap[str, AnyValue]], TypeMap[str, AnyValue]],
) -> None:
    ExistingFunc = KMigrationRegistry.get(TargetType)
    if ExistingFunc is not None and ExistingFunc is not MigrationFunc:
        raise ValueError(
            f"duplicate interchange migration for {GetWireType(TargetType)!r}"
        )
    KMigrationRegistry[TargetType] = MigrationFunc


# unordered collections need canonical ordering so output remains stable across hash seeds
def OrderData(SourceValues: set[AnyValue] | frozenset[AnyValue]) -> list[AnyValue]:
    EncodedValues = [ToData(ItemValue) for ItemValue in SourceValues]

    # canonical text ordering avoids dependence on collection hash iteration order
    def GetSortKey(ItemValue: AnyValue) -> str:
        return JsonCodec.dumps(
            ItemValue, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )

    return sorted(EncodedValues, key=GetSortKey)


# recursive encoding preserves every supported container and model type losslessly
def ToData(SourceValue: AnyValue) -> AnyValue:
    if IsDataClass(SourceValue):
        ResultValue = {"$type": GetWireType(type(SourceValue))}
        for FieldValue in GetFields(SourceValue):
            ResultValue[GetWireField(FieldValue.name, type(SourceValue))] = ToData(
                getattr(SourceValue, FieldValue.name)
            )
        return ResultValue
    if isinstance(SourceValue, EnumBase):
        return {"$enum": GetWireType(type(SourceValue)), "value": SourceValue.value}
    if isinstance(SourceValue, bytes):
        return {"$bytes": BaseCodec.b64encode(SourceValue).decode("ascii")}
    if isinstance(SourceValue, tuple):
        return {"$tuple": [ToData(ItemValue) for ItemValue in SourceValue]}
    if isinstance(SourceValue, frozenset):
        return {"$frozenset": OrderData(SourceValue)}
    if isinstance(SourceValue, set):
        return {"$set": OrderData(SourceValue)}
    if isinstance(SourceValue, list):
        return [ToData(ItemValue) for ItemValue in SourceValue]
    if isinstance(SourceValue, TypeMap):
        return {
            str(KeyValue): ToData(ItemValue)
            for KeyValue, ItemValue in SourceValue.items()
        }
    if SourceValue is None or isinstance(SourceValue, (str, int, float, bool)):
        return SourceValue
    raise TypeError(f"cannot serialize value of type {type(SourceValue).__name__}")


from .deserialize import FromData


# json output provides deterministic portable text for storage and hashing
def DumpJson(SourceValue: AnyValue, *, IndentSize: int | None = 2) -> str:
    return JsonCodec.dumps(
        ToData(SourceValue), indent=IndentSize, sort_keys=True, ensure_ascii=False
    )


# json input shares the validated recursive decoder used by mapping based callers
def LoadJson(SourceText: str) -> AnyValue:
    return FromData(JsonCodec.loads(SourceText))


globals().update(
    {
        "dumps": DumpJson,
        "from_data": FromData,
        "loads": LoadJson,
        "register_migration": RegMigration,
        "register_types": RegisterTypes,
        "to_data": ToData,
    }
)

DumpJson.__module__ = __name__
FromData.__module__ = __name__
LoadJson.__module__ = __name__
RegMigration.__module__ = __name__
RegisterTypes.__module__ = __name__
ToData.__module__ = __name__

DumpJson.__name__ = "dumps"
DumpJson.__qualname__ = "dumps"
FromData.__name__ = "from_data"
FromData.__qualname__ = "from_data"
LoadJson.__name__ = "loads"
LoadJson.__qualname__ = "loads"
RegMigration.__name__ = "register_migration"
RegMigration.__qualname__ = "register_migration"
RegisterTypes.__name__ = "register_types"
RegisterTypes.__qualname__ = "register_types"
ToData.__name__ = "to_data"
ToData.__qualname__ = "to_data"

DumpJson.__annotations__ = {
    "value": "Any",
    "indent": "int | None",
    "return": "str",
}
FromData.__annotations__ = {
    "value": "Any",
    "return": "Any",
}
LoadJson.__annotations__ = {
    "source": "str",
    "return": "Any",
}
RegMigration.__annotations__ = {
    "target": "type",
    "migration": "Callable[[Mapping[str, Any]], Mapping[str, Any]]",
    "return": "None",
}
RegisterTypes.__annotations__ = {
    "types": "type",
    "return": "None",
}
ToData.__annotations__ = {
    "value": "Any",
    "return": "Any",
}

DumpJson.__signature__ = FuncSig(
    (
        FuncParam("value", FuncParam.POSITIONAL_OR_KEYWORD, annotation="Any"),
        FuncParam(
            "indent",
            FuncParam.KEYWORD_ONLY,
            default=2,
            annotation="int | None",
        ),
    ),
    return_annotation="str",
)
FromData.__signature__ = FuncSig(
    (FuncParam("value", FuncParam.POSITIONAL_OR_KEYWORD, annotation="Any"),),
    return_annotation="Any",
)
LoadJson.__signature__ = FuncSig(
    (FuncParam("source", FuncParam.POSITIONAL_OR_KEYWORD, annotation="str"),),
    return_annotation="Any",
)
RegMigration.__signature__ = FuncSig(
    (
        FuncParam("target", FuncParam.POSITIONAL_OR_KEYWORD, annotation="type"),
        FuncParam(
            "migration",
            FuncParam.POSITIONAL_OR_KEYWORD,
            annotation="Callable[[Mapping[str, Any]], Mapping[str, Any]]",
        ),
    ),
    return_annotation="None",
)
RegisterTypes.__signature__ = FuncSig(
    (FuncParam("types", FuncParam.VAR_POSITIONAL, annotation="type"),),
    return_annotation="None",
)
ToData.__signature__ = FuncSig(
    (FuncParam("value", FuncParam.POSITIONAL_OR_KEYWORD, annotation="Any"),),
    return_annotation="Any",
)

# serialization consumers need one intentional historical public contract
__all__ = (
    "dumps",
    "from_data",
    "loads",
    "register_migration",
    "register_types",
    "to_data",
)
