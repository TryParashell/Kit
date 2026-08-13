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
from typing import Any as AnyValue
from typing import Mapping as TypeMap
from typing import get_origin as GetOrigin
from typing import get_type_hints as GetTypeHints

from .wire import ResolveField


# record reconstruction applies migrations and mapping immutability before model construction
def DecodeRecord(
    SourceValue: dict[str, AnyValue],
    TargetType: type,
    DecoderFunc: AnyValue,
) -> AnyValue:
    from .serialization import KMigrationRegistry

    WireArguments = {
        KeyValue: DecoderFunc(ItemValue)
        for KeyValue, ItemValue in SourceValue.items()
        if KeyValue != "$type"
    }
    MigrationFunc = KMigrationRegistry.get(TargetType)
    if MigrationFunc is not None:
        WireArguments = dict(MigrationFunc(FrozenMap(WireArguments)))
    Arguments = {
        ResolveField(TargetType, KeyValue): ItemValue
        for KeyValue, ItemValue in WireArguments.items()
    }
    TypeHints = GetTypeHints(TargetType)
    for FieldValue in GetFields(TargetType):
        FieldHint = TypeHints.get(FieldValue.name)
        if (
            FieldValue.name in Arguments
            and isinstance(Arguments[FieldValue.name], dict)
            and GetOrigin(FieldHint) in {TypeMap, MappingBase}
        ):
            Arguments[FieldValue.name] = FrozenMap(dict(Arguments[FieldValue.name]))
    return TargetType(**Arguments)
