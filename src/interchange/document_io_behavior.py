# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
from typing import Any as AnyValue
from typing import Mapping as TypeMap


# document io methods preserve the historical codec surface without owning serialization
class DocumentIo:
    locals()["__slots__"] = ()

    # mapping output remains a method so historical document callers need no codec knowledge
    def ToMapping(SelfValue) -> dict[str, AnyValue]:
        from .document_io import ToMapping

        return ToMapping(SelfValue)

    # mapping construction remains typed so incompatible root records fail immediately
    @classmethod
    def FromMapping(ClassType, SourceValues: TypeMap[str, AnyValue]) -> DocumentIo:
        from .document_io import FromMapping

        return FromMapping(ClassType, SourceValues)

    # json output remains a method so stable options stay consistent for callers
    def ToJson(
        SelfValue,
        *,
        IndentSize: int | None = 2,
        **LegacyValues: int | None,
    ) -> str:
        from .document_io import ToJson

        RemainingValues = dict(LegacyValues)
        if "indent" in RemainingValues:
            IndentSize = RemainingValues.pop("indent")
        if RemainingValues:
            UnknownName = next(iter(RemainingValues))
            raise TypeError(
                f"ToJson got an unexpected keyword argument {UnknownName!r}"
            )
        return ToJson(SelfValue, IndentSize=IndentSize)

    # json construction remains typed so incompatible root records fail immediately
    @classmethod
    def FromJson(ClassType, SourceValue: str) -> DocumentIo:
        from .document_io import FromJson

        return FromJson(ClassType, SourceValue)

    # file output remains discoverable on documents while path logic stays focused elsewhere
    def WriteJson(SelfValue, PathValue: str | FilePath) -> FilePath:
        from .document_io import WriteJson

        return WriteJson(SelfValue, PathValue)

    # file input remains discoverable on document types while decoding stays focused elsewhere
    @classmethod
    def ReadJson(ClassType, PathValue: str | FilePath) -> DocumentIo:
        from .document_io import ReadJson

        return ReadJson(ClassType, PathValue)
