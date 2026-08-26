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
from convert.adapters.registry.RegistryState import RegistryHost
from convert.adapters.base.WritePolicy import GetFormatKey


# reader catalog ownership isolates ordering and lookup from registration state transitions
class ReaderCatalog(RegistryHost):

    # deterministic ordering keeps discovery independent from import timing
    def GetReaders(self) -> tuple[CadReaderAdapter, ...]:
        return tuple(
            BindingData.reader
            for BindingData in dict(sorted(self.BindingMap.items())).values()
            if BindingData.reader is not None
        )

    # canonical and aliased lookup share one case insensitive namespace
    def GetReader(self, FormatId: str) -> CadReaderAdapter:
        FormatKey = GetFormatKey(FormatId)
        BindingData = self.BindingMap.get(self.AliasMap.get(FormatKey, FormatKey))
        if BindingData is None or BindingData.reader is None:
            raise NotFoundError(f"no reader registered for {FormatId}")
        return BindingData.reader


# writer catalog ownership isolates ordering and lookup from registration state transitions
class WriterCatalog(RegistryHost):

    # deterministic ordering keeps destination selection independent from import timing
    def GetWriters(self) -> tuple[CadWriterAdapter, ...]:
        return tuple(
            BindingData.writer
            for BindingData in dict(sorted(self.BindingMap.items())).values()
            if BindingData.writer is not None
        )

    # canonical and aliased lookup share one case insensitive namespace
    def GetWriter(self, FormatId: str) -> CadWriterAdapter:
        FormatKey = GetFormatKey(FormatId)
        BindingData = self.BindingMap.get(self.AliasMap.get(FormatKey, FormatKey))
        if BindingData is None or BindingData.writer is None:
            raise NotFoundError(f"no writer registered for {FormatId}")
        return BindingData.writer


# format listing remains separate because public names differ from normalized lookup keys
class FormatCatalog(RegistryHost):

    # canonical ids and aliases remain visible without exposing internal case folded keys
    def GetFormatIds(self) -> tuple[str, ...]:
        FormatNames: set[str] = {
            ValueText
            for BindingData in self.BindingMap.values()
            for AdapterData in (BindingData.reader, BindingData.writer)
            if AdapterData is not None
            for ValueText in (
                AdapterData.info.FormatId,
                *AdapterData.info.AliasNames,
            )
        }
        return tuple(sorted(FormatNames, key=GetNameKey))


# public format ordering stays case insensitive while preserving original spelling ties
def GetNameKey(ValueText: str) -> tuple[str, str]:
    return ValueText.casefold(), ValueText
