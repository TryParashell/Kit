# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.base.WritePolicy import GetFormatKey


# reader catalog ownership isolates ordering and lookup from registration state transitions
class ReaderCatalog:

    # deterministic ordering keeps discovery independent from import timing
    def GetReaders(SelfValue) -> tuple[CadReaderAdapter, ...]:
        return tuple(
            BindingData.ReaderData
            for FormatKey, BindingData in sorted(SelfValue.BindingMap.items())
            if BindingData.ReaderData is not None
        )

    # canonical and aliased lookup share one case insensitive namespace
    def GetReader(SelfValue, FormatId: str) -> CadReaderAdapter:
        FormatKey = GetFormatKey(FormatId)
        BindingData = SelfValue.BindingMap.get(
            SelfValue.AliasMap.get(FormatKey, FormatKey)
        )
        if BindingData is None or BindingData.ReaderData is None:
            raise NotFoundError(f"no reader registered for {FormatId}")
        return BindingData.ReaderData


# writer catalog ownership isolates ordering and lookup from registration state transitions
class WriterCatalog:

    # deterministic ordering keeps destination selection independent from import timing
    def GetWriters(SelfValue) -> tuple[CadWriterAdapter, ...]:
        return tuple(
            BindingData.WriterData
            for FormatKey, BindingData in sorted(SelfValue.BindingMap.items())
            if BindingData.WriterData is not None
        )

    # canonical and aliased lookup share one case insensitive namespace
    def GetWriter(SelfValue, FormatId: str) -> CadWriterAdapter:
        FormatKey = GetFormatKey(FormatId)
        BindingData = SelfValue.BindingMap.get(
            SelfValue.AliasMap.get(FormatKey, FormatKey)
        )
        if BindingData is None or BindingData.WriterData is None:
            raise NotFoundError(f"no writer registered for {FormatId}")
        return BindingData.WriterData


# format listing remains separate because public names differ from normalized lookup keys
class FormatCatalog:

    # canonical ids and aliases remain visible without exposing internal case folded keys
    def GetFormatIds(SelfValue) -> tuple[str, ...]:
        FormatNames = {
            ValueText
            for BindingData in SelfValue.BindingMap.values()
            for AdapterData in (BindingData.ReaderData, BindingData.WriterData)
            if AdapterData is not None
            for ValueText in (
                AdapterData.info.format_id,
                *AdapterData.info.aliases,
            )
        }
        return tuple(sorted(FormatNames, key=GetNameKey))


# public format ordering stays case insensitive while preserving original spelling ties
def GetNameKey(ValueText: str) -> tuple[str, str]:
    return ValueText.casefold(), ValueText
