# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.serialization import DumpJson, FromData, LoadJson, ToData


# mapping output gives callers a portable structure without exposing codec internals
def ToMapping(DocumentValue: AnyValue) -> dict[str, AnyValue]:
    return ToData(DocumentValue)


# mapping input enforces the requested model type before callers receive data
def FromMapping(
    ClassType: type[AnyValue], SourceValues: TypeMap[str, AnyValue]
) -> AnyValue:
    ResultValue = FromData(dict(SourceValues))
    if not isinstance(ResultValue, ClassType):
        raise TypeError("data does not describe a CadDocument")
    ResultValue.AssertValid()
    return ResultValue


# json output centralizes deterministic serialization options for document methods
def ToJson(DocumentValue: AnyValue, *, IndentSize: int | None = 2) -> str:
    return DumpJson(DocumentValue, IndentSize=IndentSize)


# json input validates document identity before returning decoded data
def FromJson(ClassType: type[AnyValue], SourceValue: str) -> AnyValue:
    ResultValue = LoadJson(SourceValue)
    if not isinstance(ResultValue, ClassType):
        raise TypeError("JSON does not describe a CadDocument")
    ResultValue.AssertValid()
    return ResultValue


# file output provides atomic ownership of path normalization and parent creation
def WriteJson(DocumentValue: AnyValue, PathValue: str | FilePath) -> FilePath:
    OutputPath = FilePath(PathValue).expanduser().resolve()
    OutputPath.parent.mkdir(parents=True, exist_ok=True)
    OutputPath.write_text(ToJson(DocumentValue) + "\n", encoding="utf-8")
    return OutputPath


# file input shares validated json decoding rather than duplicating codec rules
def ReadJson(ClassType: type[AnyValue], PathValue: str | FilePath) -> AnyValue:
    SourceText = FilePath(PathValue).expanduser().resolve().read_text("utf-8")
    return FromJson(ClassType, SourceText)
