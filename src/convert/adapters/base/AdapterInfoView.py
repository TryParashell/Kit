# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange import Capability


# registry internals read adapter metadata through typed accessors rather than raw storage
class AdapterInfoView:
    __slots__ = ()

    # canonical format access remains typed because registry internals read this storage field
    @property
    def FormatId(self) -> str:
        return CastValue(str, getattr(self, "format_id"))

    # canonical display access remains typed because catalogs render this storage field
    @property
    def DisplayName(self) -> str:
        return CastValue(str, getattr(self, "name"))

    # canonical version access remains typed because plugin diagnostics expose this storage field
    @property
    def VersionText(self) -> str:
        return CastValue(str, getattr(self, "version"))

    # canonical alias access remains typed because registry namespaces consume this storage field
    @property
    def AliasNames(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "aliases"))

    # canonical capability access remains typed because policy callers compare this storage field
    @property
    def Capabilities(self) -> frozenset[Capability]:
        return CastValue(frozenset[Capability], getattr(self, "capabilities"))

    # canonical media access remains typed because discovery consumers inspect this storage field
    @property
    def MediaTypes(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "media_types"))

    # canonical native capability access remains typed because transfer policy consumes this field
    @property
    def NativeCaps(self) -> frozenset[Capability]:
        return CastValue(
            frozenset[Capability],
            getattr(self, "native_capabilities"),
        )

    # canonical part extension access remains typed because document routing consumes this field
    @property
    def PartExts(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "part_extensions"))

    # canonical assembly extension access remains typed because document routing consumes this field
    @property
    def AssemblyExts(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "assembly_extensions"))
