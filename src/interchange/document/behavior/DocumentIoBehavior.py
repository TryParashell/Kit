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

    # mapping output remains a method so historical document callers need no codec knowledge
    def ToMapping(self) -> dict[str, WireData]:
        from interchange.document.behavior.DocumentIo import ToMapping

        return ToMapping(self)

    # mapping construction remains typed so incompatible root records fail immediately
    @classmethod
    def FromMapping(cls, SourceValues: TypeMap[str, WireData]) -> Self:
        from interchange.document.behavior.DocumentIo import FromMapping

        return FromMapping(cls, SourceValues)

    # json output remains a method so stable options stay consistent for callers
    def ToJson(
        self,
        *,
        IndentSize: int | None = 2,
        **LegacyValues: int | None,
    ) -> str:
        from interchange.document.behavior.DocumentIo import ToJson

        RemainingValues = dict(LegacyValues)
        if "indent" in RemainingValues:
            IndentSize = RemainingValues.pop("indent")
        if RemainingValues:
            UnknownName = next(iter(RemainingValues))
            raise TypeError(
                f"ToJson got an unexpected keyword argument {UnknownName!r}"
            )
        return ToJson(self, IndentSize=IndentSize)

    # json construction remains typed so incompatible root records fail immediately
    @classmethod
    def FromJson(cls, SourceValue: str) -> Self:
        from interchange.document.behavior.DocumentIo import FromJson

        return FromJson(cls, SourceValue)

    # file output remains discoverable on documents while path logic stays focused elsewhere
    def WriteJson(self, PathValue: str | FilePath) -> FilePath:
        from interchange.document.behavior.DocumentIo import WriteJson

        return WriteJson(self, PathValue)

    # file input remains discoverable on document types while decoding stays focused elsewhere
    @classmethod
    def ReadJson(cls, PathValue: str | FilePath) -> Self:
        from interchange.document.behavior.DocumentIo import ReadJson

        return ReadJson(cls, PathValue)
