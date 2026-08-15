# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping as MappingBase
from dataclasses import fields as GetFields
from types import MappingProxyType as FrozenMap
from typing import Callable as CallableType
from typing import cast as CastValue
from typing import get_origin as GetOrigin
from typing import get_type_hints as GetTypeHints

from interchange.serialization.MigrationRegistry import KMigrationRegistry
from interchange.serialization.RecordType import DataRecord
from interchange.serialization.Wire import ResolveField
from interchange.serialization.WireData import WireData


# record reconstruction applies migrations and mapping immutability before model construction
def DecodeRecord(
    SourceValue: dict[str, WireData],
    TargetType: type[DataRecord],
    DecoderFunc: CallableType[[object], object],
) -> object:
    WireArguments: dict[str, object] = {
        KeyValue: DecoderFunc(ItemValue)
        for KeyValue, ItemValue in SourceValue.items()
        if KeyValue != "$type"
    }
    MigrationFunc = KMigrationRegistry.get(TargetType)
    if MigrationFunc is not None:
        WireArguments = dict(MigrationFunc(FrozenMap(WireArguments)))
    Arguments: dict[str, object] = {
        ResolveField(TargetType, KeyValue): ItemValue
        for KeyValue, ItemValue in WireArguments.items()
    }
    TypeHints = CastValue(dict[str, object], GetTypeHints(TargetType))
    for FieldValue in GetFields(TargetType):
        FieldHint = TypeHints.get(FieldValue.name)
        ArgumentValue = Arguments.get(FieldValue.name)
        if isinstance(ArgumentValue, dict) and GetOrigin(FieldHint) is MappingBase:
            MapValue = CastValue(dict[object, object], ArgumentValue)
            Arguments[FieldValue.name] = FrozenMap(MapValue)
    RecordFactory = CastValue(CallableType[..., object], TargetType)
    return RecordFactory(**Arguments)
