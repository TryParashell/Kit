# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from io import StringIO as TextStream
from pathlib import Path as FilePath
from typing import Protocol
from typing import runtime_checkable as RuntimeCheck

from convert.adapters.base.ContractTypes import KSourceType


# replay detects reusable streams without requiring one shot receivers to support seeking
@RuntimeCheck
class ReplaySource(Protocol):

    # reusable streams need a concrete offset so probing can preserve caller state
    def tell(self) -> int:
        raise TypeError("replay sources require a concrete tell implementation")

    # reusable streams must restore their position before registry probing begins
    def seek(self, offset: int, whence: int = 0, /) -> int:
        raise TypeError("replay sources require a concrete seek implementation")


# probing must not consume one shot sources before the selected reader receives them
def GetReplayMut(SourceData: KSourceType) -> KSourceType:
    if isinstance(SourceData, (str, FilePath, bytes, bytearray)):
        return SourceData
    if isinstance(SourceData, ReplaySource):
        CanReplay = True
        try:
            StreamPos = SourceData.tell()
            SourceData.seek(StreamPos)
        except (OSError, TypeError, ValueError):
            CanReplay = False
        if CanReplay:
            return SourceData
    SourceValue = SourceData.read()
    if isinstance(SourceValue, str):
        return TextStream(SourceValue)
    return ByteStream(SourceValue)
