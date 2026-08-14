# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from interchange import CadDocument

from .adapter_protocols import CadReaderAdapter
from .adapter_protocols import CadWriterAdapter
from .contract_types import KSourceType
from .contract_types import KTargetType
from .probe_result import ProbeResult
from .registry_errors import AmbiguousError
from .registry_errors import NotFoundError
from .registry_errors import RegistryError
from .write_policy import GetFormatKey
from .write_policy import GetFormatKeys


# probe validation protects reader ranking from malformed or misattributed results
def GetProbeResult(
    AdapterData: CadReaderAdapter,
    SourceData: KSourceType,
) -> ProbeResult:
    ResultData = AdapterData.probe(SourceData)
    if not isinstance(ResultData, ProbeResult):
        raise RegistryError(
            f"reader {AdapterData.info.format_id} returned an invalid probe result"
        )
    if GetFormatKey(ResultData.FormatId) not in GetFormatKeys(AdapterData.info):
        raise RegistryError(
            f"reader {AdapterData.info.format_id} returned probe format {ResultData.FormatId}"
        )
    return ResultData


# reader selection resolves the strongest unique probe while reporting every tied format
def SelectReader(
    ReaderValues: tuple[CadReaderAdapter, ...],
    SourceData: KSourceType,
) -> CadReaderAdapter:
    ProbeValues = tuple(
        (ResultData, AdapterData)
        for AdapterData in ReaderValues
        if (ResultData := GetProbeResult(AdapterData, SourceData)).Confidence > 0
    )
    if not ProbeValues:
        raise NotFoundError("no reader recognizes the source")
    SortedValues = sorted(
        ProbeValues,
        key=GetProbeScore,
        reverse=True,
    )
    TopConfidence = SortedValues[0][0].Confidence
    TiedNames = tuple(
        AdapterData.info.format_id
        for ResultData, AdapterData in SortedValues
        if ResultData.Confidence == TopConfidence
    )
    if len(TiedNames) > 1:
        raise AmbiguousError("reader probe tied between " + ", ".join(TiedNames))
    return SortedValues[0][1]


# confidence ordering stays focused because tie reporting consumes the same score
def GetProbeScore(
    ItemData: tuple[ProbeResult, CadReaderAdapter],
) -> float:
    return ItemData[0].Confidence


# writer selection prefers the unique exact extension when several writers report support
def SelectWriter(
    WriterValues: tuple[CadWriterAdapter, ...],
    DocumentData: CadDocument,
    TargetData: KTargetType,
) -> CadWriterAdapter:
    CandidateValues = tuple(
        AdapterData
        for AdapterData in WriterValues
        if AdapterData.supports(DocumentData, TargetData)
    )
    if not CandidateValues:
        raise NotFoundError("no writer supports the destination")
    if len(CandidateValues) == 1:
        return CandidateValues[0]
    ExtensionText = (
        FilePath(TargetData).suffix.casefold()
        if isinstance(TargetData, (str, FilePath))
        else ""
    )
    ExactValues = tuple(
        AdapterData
        for AdapterData in CandidateValues
        if ExtensionText
        in {ValueText.casefold() for ValueText in AdapterData.info.extensions}
    )
    if len(ExactValues) == 1:
        return ExactValues[0]
    raise AmbiguousError("multiple writers support the destination")
