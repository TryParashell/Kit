# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.base.ContractTypes import (
    KSourceType as Source,
    KTargetType as Destination,
)
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.engine.EngineResult import ConversionResult as ConvertResult
from convert.formats.SourceFormat import ResolveFormat


# conversion orchestration stays isolated so registry read and write contracts remain reusable
class EngineConvert:

    # one neutral document boundary prevents direct coupling between independent format adapters
    def ConvertData(
        self,
        SourceData: Source,
        TargetData: Destination,
        *,
        SourceFormat: str | None = None,
        DestFormat: str | None = None,
        ReadOpts: ReadOptions | None = None,
        WriteOpts: WriteOptions | None = None,
    ) -> ConvertResult:
        RegistryData = getattr(self, "registry")
        DocumentData, ReaderData = RegistryData.read_with_adapter(
            SourceData,
            format_id=SourceFormat,
            options=ReadOpts or ReadOptions(),
        )
        OutputResult = RegistryData.write(
            DocumentData,
            TargetData,
            format_id=DestFormat,
            options=WriteOpts or WriteOptions(),
        )
        return ConvertResult(
            document=DocumentData,
            output=OutputResult,
            source_format=ResolveFormat(DocumentData, ReaderData),
            destination_format=OutputResult.adapter,
        )
