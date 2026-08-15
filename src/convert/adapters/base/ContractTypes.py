# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import TextIOBase as TextStream
from pathlib import Path as FilePath
from typing import Protocol
from typing import TypeAlias
from typing import TypeGuard


# binary sources need only the operation consumed by adapters rather than full seekable io
class BinaryReceiver(Protocol):

    # adapters accept one shot binary streams because registry replay preserves their payload
    def read(self, size: int | None = -1, /) -> bytes:
        raise TypeError("binary receivers require a concrete read implementation")


# text sources need only the operation consumed by adapters rather than full seekable io
class TextReceiver(Protocol):

    # adapters accept one shot text streams because registry replay preserves their payload
    def read(self, size: int | None = -1, /) -> str:
        raise TypeError("text receivers require a concrete read implementation")


# binary destinations expose the narrow operation required for complete payload emission
class BinaryWriter(Protocol):

    # writers return counts so short destination writes remain detectable
    def write(self, data: bytes, /) -> int | None:
        raise TypeError("binary writers require a concrete write implementation")


# text destinations expose the narrow operation required for complete payload emission
class TextWriter(Protocol):

    # writers return counts so short destination writes remain detectable
    def write(self, data: str, /) -> int | None:
        raise TypeError("text writers require a concrete write implementation")


# reader contracts accept paths memory payloads and caller owned streams
KSourceType: TypeAlias = (
    str | FilePath | bytes | bytearray | BinaryReceiver | TextReceiver
)


# writer contracts accept filesystem destinations and caller owned streams
KTargetType: TypeAlias = str | FilePath | BinaryWriter | TextWriter


# windows path validation must reject reserved device names before filesystem access
def IsDeviceName(ValueText: str) -> bool:
    StemValue = ValueText.split(".", 1)[0].casefold()
    return StemValue in {"con", "prn", "aux", "nul"} or (
        len(StemValue) == 4
        and StemValue[:3] in {"com", "lpt"}
        and StemValue[3] in "123456789¹²³"
    )


# stream staging needs a reliable distinction between binary and text destinations
def IsBinaryTarget(TargetValue: KTargetType) -> TypeGuard[BinaryWriter]:
    if isinstance(TargetValue, (str, FilePath, TextStream)):
        return False
    WriterValue = getattr(TargetValue, "write", None)
    return callable(WriterValue) and getattr(TargetValue, "encoding", None) is None
