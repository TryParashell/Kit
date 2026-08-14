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
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.document.models.DocumentModel import CadDocument

from convert.adapters.base.ContractTypes import KSourceType, KTargetType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.registry import AdapterRegistry

# explicit annotation globals keep reflected legacy signatures resolvable at runtime
globals().update(
    {
        "AdapterRegistry": AdapterRegistry,
        "CadDocument": CadDocument,
        "Destination": KTargetType,
        "ReadOptions": ReadOptions,
        "Source": KSourceType,
        "WriteOptions": WriteOptions,
        "WriteResult": WriteResult,
    }
)


# result resolution is deferred until the engine facade creates its public record class
def SetResultType(ResultType: type) -> None:
    globals()["ConversionResult"] = ResultType


# historical method signatures need exact positional and keyword parameter categories
def MakeCallSig(
    PositionSpecs: tuple[tuple[str, AnyValue], ...],
    KeywordSpecs: tuple[tuple[str, str, AnyValue], ...],
    ReturnAnnot: AnyValue,
) -> FuncSig:
    ParamValues = [
        FuncParam(
            NameValue,
            FuncParam.POSITIONAL_OR_KEYWORD,
            annotation=FuncParam.empty if AnnotValue is None else AnnotValue,
        )
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


# generated methods preserve legacy keyword calls while canonical implementations stay compliant
def MakeEngineCall(
    TargetFunc: AnyValue,
    LegacyName: str,
    ParamMap: TypeMap[str, str],
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
    KwargDefaults: TypeMap[str, AnyValue] | None,
) -> AnyValue:

    # one adapter keeps historical keyword spelling away from canonical implementation identifiers
    def LegacyCall(
        SelfValue: AnyValue,
        *ArgValues: AnyValue,
        **KwargValues: AnyValue,
    ) -> AnyValue:
        MappedKwargs = {
            ParamMap.get(NameValue, NameValue): ItemValue
            for NameValue, ItemValue in KwargValues.items()
        }
        return TargetFunc(SelfValue, *ArgValues, **MappedKwargs)

    LegacyCall.__name__ = LegacyName
    LegacyCall.__qualname__ = f"ConversionEngine.{LegacyName}"
    LegacyCall.__module__ = "convert.engine"
    LegacyCall.__annotations__ = dict(AnnotationMap)
    LegacyCall.__signature__ = SignatureInfo
    LegacyCall.__kwdefaults__ = None if KwargDefaults is None else dict(KwargDefaults)
    return LegacyCall
