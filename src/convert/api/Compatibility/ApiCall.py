# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig
from pathlib import Path as FilePath
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.document.models.DocumentModel import CadDocument

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KSourceType, KTargetType
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry
from convert.engine import ConversionResult

globals().update(
    {
        "Any": AnyValue,
        "Destination": KTargetType,
        "Mapping": TypeMap,
        "Path": FilePath,
        "Source": KSourceType,
    }
)


# historical call signatures need exact positional and keyword parameter categories
def MakeCallSig(
    PositionSpecs: tuple[tuple[str, str], ...],
    KeywordSpecs: tuple[tuple[str, str, AnyValue], ...],
    ReturnAnnot: str,
) -> FuncSig:
    ParamValues = [
        FuncParam(NameValue, FuncParam.POSITIONAL_OR_KEYWORD, annotation=AnnotValue)
        for NameValue, AnnotValue in PositionSpecs
    ]
    ParamValues.extend(
        FuncParam(
            NameValue,
            FuncParam.KEYWORD_ONLY,
            default=DefaultValue,
            annotation=AnnotValue,
        )
        for NameValue, AnnotValue, DefaultValue in KeywordSpecs
    )
    return FuncSig(ParamValues, return_annotation=ReturnAnnot)


# generated wrappers preserve legacy keyword calls while canonical implementations stay compliant
def MakeApiCall(
    TargetFunc: AnyValue,
    LegacyName: str,
    ParamMap: TypeMap[str, str],
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
    KwargDefaults: TypeMap[str, AnyValue] | None,
) -> AnyValue:

    # one adapter keeps historical keyword spelling away from canonical implementation identifiers
    def LegacyCall(*ArgValues: AnyValue, **KwargValues: AnyValue) -> AnyValue:
        MappedKwargs = {
            ParamMap.get(NameValue, NameValue): ItemValue
            for NameValue, ItemValue in KwargValues.items()
        }
        return TargetFunc(*ArgValues, **MappedKwargs)

    LegacyCall.__name__ = LegacyName
    LegacyCall.__qualname__ = LegacyName
    LegacyCall.__module__ = "convert.api"
    LegacyCall.__annotations__ = dict(AnnotationMap)
    LegacyCall.__signature__ = SignatureInfo
    LegacyCall.__kwdefaults__ = None if KwargDefaults is None else dict(KwargDefaults)
    return LegacyCall
