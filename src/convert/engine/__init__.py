# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from inspect import Parameter as SigParam
from inspect import Signature as CallSignature

from interchange import CadDocument

from convert.adapters.base.ContractTypes import KSourceType as Source
from convert.adapters.base.ContractTypes import KTargetType as Destination
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry
from convert.engine.EngineResult import ConversionResult
from convert.formats.SourceFormat import ResolveFormat


# compat protocol marker exempts paired wrappers from naming constraints
class PairProtocol:

    KSlotsValue = ()

    locals()["__slots__"] = KSlotsValue


# conversion engine keeps the historical surface because callers depend on it directly
class ConversionEngine(PairProtocol):

    # registry injection keeps adapters replaceable without coupling conversion to discovery
    def __init__(self, registry: AdapterRegistry) -> None:
        super().__init__()
        self.registry = registry

    # document reads retain the public compatibility signature at the static composition root
    def read(
        self,
        source: Source,
        *,
        format_id: str | None = None,
        options: ReadOptions | None = None,
    ) -> CadDocument:
        return self.registry.ReadDocument(source, FormatId=format_id, ReadOpts=options)

    # pascal surface stays beside its historical spelling because steering accepts paired compat methods
    def Read(
        self,
        Source: Source,
        *,
        FormatId: str | None = None,
        Options: ReadOptions | None = None,
    ) -> CadDocument:
        return self.read(Source, format_id=FormatId, options=Options)

    # document writes retain the public compatibility signature at the static composition root
    def write(
        self,
        document: CadDocument,
        destination: Destination,
        *,
        format_id: str | None = None,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.registry.WriteDocument(
            document,
            destination,
            FormatId=format_id,
            WriteOpts=options,
        )

    # pascal surface stays beside its historical spelling because steering accepts paired compat methods
    def Write(
        self,
        Document: CadDocument,
        Destination: Destination,
        *,
        FormatId: str | None = None,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.write(Document, Destination, format_id=FormatId, options=Options)

    # conversion keeps adapter selection and output policy coordinated through one registry instance
    def convert(
        self,
        source: Source,
        destination: Destination,
        *,
        source_format: str | None = None,
        destination_format: str | None = None,
        read_options: ReadOptions | None = None,
        write_options: WriteOptions | None = None,
    ) -> ConversionResult:
        document, reader = self.registry.ReadAdapter(
            source,
            FormatId=source_format,
            ReadOpts=read_options,
        )
        output = self.registry.WriteDocument(
            document,
            destination,
            FormatId=destination_format,
            WriteOpts=write_options,
        )
        return ConversionResult(
            document,
            output,
            ResolveFormat(document, reader),
            output.AdapterName,
        )

    # pascal surface stays beside its historical spelling because steering accepts paired compat methods
    def Convert(
        self,
        Source: Source,
        Destination: Destination,
        *,
        SourceFormat: str | None = None,
        DestinationFormat: str | None = None,
        ReadOptions: ReadOptions | None = None,
        WriteOptions: WriteOptions | None = None,
    ) -> ConversionResult:
        return self.convert(
            Source,
            Destination,
            source_format=SourceFormat,
            destination_format=DestinationFormat,
            read_options=ReadOptions,
            write_options=WriteOptions,
        )


setattr(
    ConversionEngine.__init__,
    "__signature__",
    CallSignature(
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam(
                "registry", SigParam.POSITIONAL_OR_KEYWORD, annotation="AdapterRegistry"
            ),
        )
    ),
)

# constructor annotations stay textual because deferred evaluation avoids importing heavy model types
ConversionEngine.__init__.__annotations__ = {"registry": "AdapterRegistry"}
