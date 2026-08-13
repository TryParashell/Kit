# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass

from interchange import CadDocument, Capability

from .adapters import (
    AdapterRegistry,
    CapabilityTransfer,
    Destination,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)
from .engine_reader import EngineRead
from .engine_writer import EngineWrite
from .result_details import ResultDetails
from .result_flags import ResultFlags


# immutable conversion records keep document and attestation evidence together for callers
@dataclass(frozen=True, slots=True)
class ConversionResult:
    document: CadDocument
    output: WriteResult
    source_format: str
    destination_format: str

    # callers need preservation evidence without navigating the nested writer result
    @property
    def transfers(self) -> tuple[CapabilityTransfer, ...]:
        return ResultDetails.GetTransfers(self)

    # callers need loss evidence beside the conversion summary for immediate gating
    @property
    def dropped(self) -> frozenset[Capability]:
        return ResultDetails.GetDropped(self)

    # callers need external requirements exposed where conversion outcomes are inspected
    @property
    def requirements(self) -> tuple[str, ...]:
        return ResultDetails.GetNeeds(self)

    # application gating belongs on the conversion outcome users already inspect
    @property
    def application_usable(self) -> bool:
        return ResultFlags.IsAppUsable(self)

    # vendor loadability remains distinct because usable output requires both attestations
    @property
    def vendor_loadable(self) -> bool:
        return ResultFlags.IsVendorLoad(self)

    # round trip safety remains visible because capability preservation is a primary contract
    @property
    def roundtrip_safe(self) -> bool:
        return ResultFlags.IsRoundtrip(self)

    # lossless status remains delegated so writer evidence has one authoritative calculation
    @property
    def near_lossless(self) -> bool:
        return ResultFlags.IsLossless(self)


# one coordinator keeps registry backed operations independent from format implementations
class ConversionEngine:

    # dependency injection keeps adapter discovery replaceable without cad application coupling
    def __init__(self, registry: AdapterRegistry):
        self.registry = registry

    # registry delegation preserves one validation path for every public document read
    def read(
        self,
        source: Source,
        *,
        format_id: str | None = None,
        options: ReadOptions | None = None,
    ) -> CadDocument:
        return EngineRead.ReadSource(
            self,
            source,
            FormatId=format_id,
            ReadOpts=options,
        )

    # registry delegation preserves one validation path for every public document write
    def write(
        self,
        document: CadDocument,
        destination: Destination,
        *,
        format_id: str | None = None,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return EngineWrite.WriteTarget(
            self,
            document,
            destination,
            FormatId=format_id,
            WriteOpts=options,
        )

    # one neutral document boundary prevents direct coupling between independent format adapters
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
        from .engine_convert import EngineConvert

        return EngineConvert.ConvertData(
            self,
            source,
            destination,
            SourceFormat=source_format,
            DestFormat=destination_format,
            ReadOpts=read_options,
            WriteOpts=write_options,
        )
