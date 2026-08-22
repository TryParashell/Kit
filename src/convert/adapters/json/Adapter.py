# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.base.ContractTypes import KSourceType as Source
from convert.adapters.base.ContractTypes import KTargetType as Destination
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.json.Metadata import JsonMetadata
from convert.adapters.json.Reader import JsonReader
from convert.adapters.json.Writer import JsonWriter
from interchange.document.models.DocumentModel import CadDocument


# this adapter composes focused reading writing and metadata responsibilities
class JsonAdapter(JsonMetadata, JsonReader, JsonWriter):
    KAdapterSlots = ()

    locals()["__slots__"] = KAdapterSlots

    # public probing keywords need exact names because structural callers may pass them directly
    def probe(self, source: Source) -> ProbeResult:
        return self.Probe(source)

    # public reading keywords need exact names because structural callers may pass them directly
    def read(
        self,
        source: Source,
        options: ReadOptions | None = None,
    ) -> CadDocument:
        return self.ReadAction(source, options)

    # public support keywords need exact names because structural callers may pass them directly
    def supports(self, document: CadDocument, destination: Destination) -> bool:
        return self.CanSupport(document, destination)

    # public writing keywords need exact names because structural callers may pass them directly
    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.Write(document, destination, options)
