# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import fields as GetFields

from .wire_fields import KTypeWireFields, KWireFields
from .wire_types import KWireTypes


# canonical slots across inheritance preserve storage access after historical reflection mutation
def GetSlotNames(ClassType: type) -> tuple[str, ...]:
    SlotNames: list[str] = []
    for BaseType in reversed(ClassType.__mro__):
        BaseSlots = BaseType.__dict__.get("__slots__", ())
        SlotNames.extend(
            SlotName
            for SlotName in BaseSlots
            if isinstance(SlotName, str) and not SlotName.startswith("__")
        )
    return tuple(SlotNames)


# type registration needs stable names independent of internal model naming
def GetWireType(ClassType: type) -> str:
    CanonicalName = getattr(ClassType, "__canonical_name__", ClassType.__name__)
    return KWireTypes.get(CanonicalName, ClassType.__name__)


# field serialization needs predictable snake case without exposing it in source identifiers
def FormatWireName(FieldName: str) -> str:
    NameParts: list[str] = []
    for IndexValue, Character in enumerate(FieldName):
        PriorChar = FieldName[IndexValue - 1] if IndexValue else ""
        NextChar = FieldName[IndexValue + 1] if IndexValue + 1 < len(FieldName) else ""
        if (
            IndexValue
            and Character.isupper()
            and (PriorChar.islower() or PriorChar.isupper() and NextChar.islower())
        ):
            NameParts.append("_")
        NameParts.append(Character.casefold())
    return "".join(NameParts)


# boolean model fields omit their source marker on the historical wire format
def GetWireField(FieldName: str, ClassType: type | None = None) -> str:
    if ClassType is not None:
        TypeFields = KTypeWireFields.get(ClassType.__name__, {})
        if FieldName in TypeFields:
            return TypeFields[FieldName]
    if FieldName in KWireFields:
        return KWireFields[FieldName]
    SourceName = FieldName[2:] if FieldName.startswith("Is") else FieldName
    return FormatWireName(SourceName)


# deserialization needs the compliant field name corresponding to each historical wire key
def GetModelField(WireName: str) -> str:
    if WireName and WireName[0].isupper() and "_" not in WireName:
        return WireName
    ExplicitNames = {
        WireField: ModelField for ModelField, WireField in KWireFields.items()
    }
    return ExplicitNames.get(
        WireName,
        "".join(NamePart.title() for NamePart in WireName.split("_")),
    )


# target records disambiguate shared wire keys by their actual dataclass fields
def ResolveField(ClassType: type, WireName: str) -> str:
    FieldNames = GetSlotNames(ClassType)
    TypeFields = KTypeWireFields.get(
        getattr(ClassType, "__canonical_name__", ClassType.__name__),
        {},
    )
    for FieldName in FieldNames:
        if TypeFields.get(FieldName, GetWireField(FieldName)) == WireName:
            return FieldName
    ReflectedNames = {FieldValue.name for FieldValue in GetFields(ClassType)}
    if WireName in ReflectedNames:
        return WireName
    return GetModelField(WireName)
