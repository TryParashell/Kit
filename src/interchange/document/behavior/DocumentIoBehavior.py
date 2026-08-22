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
from typing import Self

from interchange.serialization.WireData import WireData


# document io methods preserve the historical codec surface without owning serialization
class DocumentIo:
    locals()["__slots__"] = ()

    # mapping output remains concrete so callers receive a fully typed document contract
    def to_dict(self) -> dict[str, WireData]:
        from interchange.document.behavior.DocumentIo import ToMapping

        return ToMapping(self)

    # mapping construction remains concrete so replacement callers avoid generated compatibility
    @classmethod
    def from_dict(cls, value: TypeMap[str, WireData]) -> Self:
        from interchange.document.behavior.DocumentIo import FromMapping

        return FromMapping(cls, value)

    # json output uses its public spelling so static callers see the runtime signature
    def to_json(
        self,
        *,
        indent: int | None = 2,
    ) -> str:
        from interchange.document.behavior.DocumentIo import ToJson

        return ToJson(self, IndentSize=indent)

    # json construction uses its public spelling so decoded subtypes remain statically exact
    @classmethod
    def from_json(cls, source: str) -> Self:
        from interchange.document.behavior.DocumentIo import FromJson

        return FromJson(cls, source)

    # file output uses its public spelling while path ownership remains in focused behavior
    def write_json(self, path: str | FilePath) -> FilePath:
        from interchange.document.behavior.DocumentIo import WriteJson

        return WriteJson(self, path)

    # file input uses its public spelling so concrete subtype returns remain visible
    @classmethod
    def read_json(cls, path: str | FilePath) -> Self:
        from interchange.document.behavior.DocumentIo import ReadJson

        return ReadJson(cls, path)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def ToMapping(self) -> dict[str, WireData]:
        return self.to_dict()

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    @classmethod
    def FromMapping(cls, SourceValues: TypeMap[str, WireData]) -> Self:
        return cls.from_dict(SourceValues)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def ToJson(self, *, IndentSize: int | None = 2) -> str:
        return self.to_json(indent=IndentSize)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    @classmethod
    def FromJson(cls, SourceValue: str) -> Self:
        return cls.from_json(SourceValue)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def WriteJson(self, PathValue: str | FilePath) -> FilePath:
        return self.write_json(PathValue)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    @classmethod
    def ReadJson(cls, PathValue: str | FilePath) -> Self:
        return cls.read_json(PathValue)
