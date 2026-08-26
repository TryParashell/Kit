# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass

from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter


# one format binding coordinates independently registered reader and writer implementations
@DataClass(slots=True)
class AdapterBinding:
    reader: CadReaderAdapter | None = None
    writer: CadWriterAdapter | None = None

    # legacy attributes remain readable because binding is part of the established public api
    @property
    def ReaderData(self) -> CadReaderAdapter | None:
        return self.reader

    # legacy assignments remain writable because registry coordination mutates binding slots
    @ReaderData.setter
    def ReaderData(self, ReaderValue: CadReaderAdapter | None) -> None:
        self.reader = ReaderValue

    # legacy writer access remains typed because external diagnostics use this established name
    @property
    def WriterData(self) -> CadWriterAdapter | None:
        return self.writer

    # legacy writer mutation remains typed because registration updates existing bindings in place
    @WriterData.setter
    def WriterData(self, WriterValue: CadWriterAdapter | None) -> None:
        self.writer = WriterValue
