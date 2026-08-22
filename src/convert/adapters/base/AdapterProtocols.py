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

# compatibility annotations retain their public contract names for reflection
Source = KSourceType

# compatibility annotations retain their public contract names for reflection
Destination = KTargetType


# reader registration needs a statically visible structural adapter boundary
@RuntimeCheck
class CadReaderAdapter(Protocol):

    # discovery needs metadata before it attempts to consume source data
    @property
    def info(self) -> AdapterInfo:
        raise TypeError("reader info requires a concrete implementation")

    # selection needs a non destructive source compatibility assessment
    def probe(self, source: Source) -> ProbeResult:
        raise TypeError("reader probing requires a concrete implementation")

    # conversion needs one neutral document result across reader implementations
    def read(
        self,
        source: Source,
        options: ReadOptions | None = None,
    ) -> CadDocument:
        raise TypeError("reader loading requires a concrete implementation")


# writer registration needs a statically visible structural adapter boundary
@RuntimeCheck
class CadWriterAdapter(Protocol):

    # discovery needs metadata before it attempts to stage destination output
    @property
    def info(self) -> AdapterInfo:
        raise TypeError("writer info requires a concrete implementation")

    # selection needs a non mutating destination compatibility assessment
    def supports(self, document: CadDocument, destination: Destination) -> bool:
        raise TypeError("writer support requires a concrete implementation")

    # conversion needs structured preservation evidence from every writer
    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        raise TypeError("writer output requires a concrete implementation")


# bidirectional integrations need one contract combining both adapter directions
@RuntimeCheck
class CadAdapter(CadReaderAdapter, CadWriterAdapter, Protocol):
    __slots__ = ()


CadReaderAdapter.__module__ = "convert.adapters.base"
CadWriterAdapter.__module__ = "convert.adapters.base"
CadAdapter.__module__ = "convert.adapters.base"
CadReaderAdapter.read.__module__ = "convert.adapters.base"
CadWriterAdapter.write.__module__ = "convert.adapters.base"

setattr(
    CadReaderAdapter.probe,
    "__signature__",
    CallSignature(
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam("source", SigParam.POSITIONAL_OR_KEYWORD, annotation="Source"),
        ),
        return_annotation="ProbeResult",
    ),
)
setattr(
    CadReaderAdapter.read,
    "__signature__",
    CallSignature(
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
        return_annotation="CadDocument",
    ),
)
setattr(
    CadWriterAdapter.supports,
    "__signature__",
    CallSignature(
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
        return_annotation="bool",
    ),
)
setattr(
    CadWriterAdapter.write,
    "__signature__",
    CallSignature(
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
        return_annotation="WriteResult",
    ),
)
