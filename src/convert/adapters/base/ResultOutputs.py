# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
from typing import Mapping as TypeMap
from typing import cast as CastValue

from interchange import Diagnostic

from convert.adapters.base.TransferContract import CapTransfer


# result consumers read transactional output facts through one typed view
class ResultOutputs:
    __slots__ = ()

    # legacy callers need the output path without losing its path type
    @property
    def OutputPath(self) -> "FilePath | None":
        return CastValue("FilePath | None", getattr(self, "path"))

    # legacy callers need the adapter identity without losing its string type
    @property
    def AdapterName(self) -> str:
        return CastValue(str, getattr(self, "adapter"))

    # legacy callers need byte accounting without losing its integer type
    @property
    def ByteCount(self) -> int:
        return CastValue(int, getattr(self, "bytes_written"))

    # legacy callers need diagnostics to retain their public record type
    @property
    def Diagnostics(self) -> "tuple[Diagnostic, ...]":
        return CastValue("tuple[Diagnostic, ...]", getattr(self, "diagnostics"))

    # legacy callers need metadata indexing without degrading the mapping to object
    @property
    def MetadataMap(self) -> TypeMap[str, object]:
        return CastValue(TypeMap[str, object], getattr(self, "metadata"))

    # legacy callers need transfer iteration to retain capability evidence types
    @property
    def Transfers(self) -> tuple[CapTransfer, ...]:
        return CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
