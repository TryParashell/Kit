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


# explicit coordinator methods replace runtime class generation while retaining public call signatures
class ConversionEngine:

    # registry injection keeps adapters replaceable without coupling conversion to discovery
    def __init__(self, registry: AdapterRegistry) -> None:
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
ConversionEngine.__init__.__annotations__ = {"registry": "AdapterRegistry"}
