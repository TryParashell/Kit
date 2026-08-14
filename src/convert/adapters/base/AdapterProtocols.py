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
from typing import Protocol
from typing import runtime_checkable as RuntimeCheck

from interchange import CadDocument

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.ProbeResult import ProbeResult
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult

# historical source annotations need local resolution after protocol declarations move from the facade
globals()["Source"] = KSourceType

# historical destination annotations need local resolution after protocol declarations move from the facade
globals()["Destination"] = KTargetType


# reader discovery needs one explicit structural contract that type checkers can inspect
@RuntimeCheck
class ReaderProtocol(Protocol):

    # metadata access lets discovery validate formats before any source data is consumed
    @property
    def GetInfo(SelfValue) -> AdapterInfo:
        raise TypeError("reader info requires a concrete implementation")

    # probing lets registries select readers without consuming the source
    def ProbeSource(SelfValue, SourceData: KSourceType) -> ProbeResult:
        raise TypeError("reader probing requires a concrete implementation")

    # reading returns the neutral document boundary shared by independent adapters
    def ReadSource(
        SelfValue,
        SourceData: KSourceType,
        OptionsData: ReadOptions | None = None,
    ) -> CadDocument:
        raise TypeError("reader loading requires a concrete implementation")

    locals()["info"] = locals().pop("GetInfo")
    locals()["probe"] = locals().pop("ProbeSource")
    locals()["read"] = locals().pop("ReadSource")


# writer discovery needs one explicit structural contract that type checkers can inspect
@RuntimeCheck
class WriterProtocol(Protocol):

    # metadata access lets selection validate formats before any destination is mutated
    @property
    def GetInfo(SelfValue) -> AdapterInfo:
        raise TypeError("writer info requires a concrete implementation")

    # destination checks let registries select writers before staging output
    def CanWrite(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: KTargetType,
    ) -> bool:
        raise TypeError("writer support requires a concrete implementation")

    # writing returns structured preservation evidence for registry policy checks
    def WriteTarget(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: KTargetType,
        OptionsData: WriteOptions | None = None,
    ) -> WriteResult:
        raise TypeError("writer output requires a concrete implementation")

    locals()["info"] = locals().pop("GetInfo")
    locals()["supports"] = locals().pop("CanWrite")
    locals()["write"] = locals().pop("WriteTarget")


# combined adapters remain distinguishable for callers that require both directions
@RuntimeCheck
class AdapterProtocol(ReaderProtocol, WriterProtocol, Protocol):
    locals()["__slots__"] = ()


for ProtocolType, PublicName in (
    (ReaderProtocol, "CadReaderAdapter"),
    (WriterProtocol, "CadWriterAdapter"),
    (AdapterProtocol, "CadAdapter"),
):
    setattr(ProtocolType, "__module__", "convert.adapters.base")
    setattr(ProtocolType, "__name__", PublicName)
    setattr(ProtocolType, "__qualname__", PublicName)

for MethodValue in (
    ReaderProtocol.info.fget,
    ReaderProtocol.probe,
    ReaderProtocol.read,
    WriterProtocol.info.fget,
    WriterProtocol.supports,
    WriterProtocol.write,
):
    setattr(MethodValue, "__module__", "convert.adapters.base")

for MethodValue, QualName in (
    (ReaderProtocol.info.fget, "CadReaderAdapter.info"),
    (ReaderProtocol.probe, "CadReaderAdapter.probe"),
    (ReaderProtocol.read, "CadReaderAdapter.read"),
    (WriterProtocol.info.fget, "CadWriterAdapter.info"),
    (WriterProtocol.supports, "CadWriterAdapter.supports"),
    (WriterProtocol.write, "CadWriterAdapter.write"),
):
    setattr(MethodValue, "__qualname__", QualName)

for MethodValue, PublicName in (
    (ReaderProtocol.info.fget, "info"),
    (ReaderProtocol.probe, "probe"),
    (ReaderProtocol.read, "read"),
    (WriterProtocol.info.fget, "info"),
    (WriterProtocol.supports, "supports"),
    (WriterProtocol.write, "write"),
):
    setattr(MethodValue, "__name__", PublicName)

setattr(
    ReaderProtocol.probe,
    "__annotations__",
    {"source": "Source", "return": "ProbeResult"},
)
setattr(
    ReaderProtocol.read,
    "__annotations__",
    {
        "source": "Source",
        "options": "ReadOptions | None",
        "return": "CadDocument",
    },
)
setattr(
    WriterProtocol.supports,
    "__annotations__",
    {
        "document": "CadDocument",
        "destination": "Destination",
        "return": "bool",
    },
)
setattr(
    WriterProtocol.write,
    "__annotations__",
    {
        "document": "CadDocument",
        "destination": "Destination",
        "options": "WriteOptions | None",
        "return": "WriteResult",
    },
)

for MethodValue, ParamValues, ReturnType in (
    (
        ReaderProtocol.probe,
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam("source", SigParam.POSITIONAL_OR_KEYWORD, annotation="Source"),
        ),
        "ProbeResult",
    ),
    (
        ReaderProtocol.read,
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam("source", SigParam.POSITIONAL_OR_KEYWORD, annotation="Source"),
            SigParam(
                "options",
                SigParam.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation="ReadOptions | None",
            ),
        ),
        "CadDocument",
    ),
    (
        WriterProtocol.supports,
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam(
                "document",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="CadDocument",
            ),
            SigParam(
                "destination",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="Destination",
            ),
        ),
        "bool",
    ),
    (
        WriterProtocol.write,
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam(
                "document",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="CadDocument",
            ),
            SigParam(
                "destination",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="Destination",
            ),
            SigParam(
                "options",
                SigParam.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation="WriteOptions | None",
            ),
        ),
        "WriteResult",
    ),
):
    setattr(
        MethodValue,
        "__signature__",
        CallSignature(ParamValues, return_annotation=ReturnType),
    )

setattr(
    ReaderProtocol.info.fget,
    "__annotations__",
    {"return": "AdapterInfo"},
)
setattr(
    WriterProtocol.info.fget,
    "__annotations__",
    {"return": "AdapterInfo"},
)


# public reader protocol name stays stable because annotations and runtime checks depend on it
globals()["CadReaderAdapter"] = ReaderProtocol

# public writer protocol name stays stable because annotations and runtime checks depend on it
globals()["CadWriterAdapter"] = WriterProtocol

# public combined protocol name stays stable because existing callers import it directly
globals()["CadAdapter"] = AdapterProtocol
