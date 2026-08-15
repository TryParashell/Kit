# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from typing import Callable as ValueFactory
from typing import cast as CastValue
from typing import Mapping as TypeMap
from typing import Protocol as TypeProtocol
from typing import runtime_checkable as RuntimeCheck
from typing import TypeVar

from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData
from interchange.serialization.JsonCodec import DumpJson, LoadJson
from interchange.serialization.WireData import WireData


# decoded documents must expose validation before they cross the public construction boundary
@RuntimeCheck
class ValidDocument(TypeProtocol):
    AssertValid: ValueFactory[[], None]


# generic decoding preserves the concrete document subtype requested by each class method
DocumentType = TypeVar("DocumentType")


# mapping output gives callers a portable structure without exposing codec internals
def ToMapping(DocumentValue: object) -> dict[str, WireData]:
    ResultValue = ToData(DocumentValue)
    if not isinstance(ResultValue, dict):
        raise TypeError("document serialization did not produce a mapping")
    return ResultValue


# mapping input enforces the requested model type before callers receive data
def FromMapping(
    ClassType: type[DocumentType], SourceValues: TypeMap[str, WireData]
) -> DocumentType:
    ResultValue = FromData(dict(SourceValues))
    if not isinstance(ResultValue, ClassType) or not isinstance(
        ResultValue, ValidDocument
    ):
        raise TypeError("data does not describe a CadDocument")
    ResultValue.AssertValid()
    return CastValue(DocumentType, ResultValue)


# json output centralizes deterministic serialization options for document methods
def ToJson(DocumentValue: object, *, IndentSize: int | None = 2) -> str:
    return DumpJson(DocumentValue, IndentSize=IndentSize)


# json input validates document identity before returning decoded data
def FromJson(ClassType: type[DocumentType], SourceValue: str) -> DocumentType:
    ResultValue = LoadJson(SourceValue)
    if not isinstance(ResultValue, ClassType) or not isinstance(
        ResultValue, ValidDocument
    ):
        raise TypeError("JSON does not describe a CadDocument")
    ResultValue.AssertValid()
    return CastValue(DocumentType, ResultValue)


# file output provides atomic ownership of path normalization and parent creation
def WriteJson(DocumentValue: object, PathValue: str | FilePath) -> FilePath:
    OutputPath = FilePath(PathValue).expanduser().resolve()
    OutputPath.parent.mkdir(parents=True, exist_ok=True)
    OutputPath.write_text(ToJson(DocumentValue) + "\n", encoding="utf-8")
    return OutputPath


# file input shares validated json decoding rather than duplicating codec rules
def ReadJson(ClassType: type[DocumentType], PathValue: str | FilePath) -> DocumentType:
    SourceText = FilePath(PathValue).expanduser().resolve().read_text("utf-8")
    return FromJson(ClassType, SourceText)
