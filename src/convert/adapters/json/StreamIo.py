# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import TextIOBase as TextIoBase
from pathlib import Path as FilePath
from typing import Protocol
from typing import runtime_checkable as RuntimeCheck

from convert.adapters.base import Destination
from convert.adapters.base import Source


# position preservation needs a runtime detectable contract for optional stream support
@RuntimeCheck
class TellSource(Protocol):

    # temporary reads need the original offset when a stream can report it
    def tell(self) -> int:
        raise TypeError("position sources require a concrete tell implementation")


# position restoration needs a separate contract because some readable streams cannot seek
@RuntimeCheck
class SeekSource(Protocol):

    # temporary reads restore offsets only when the source explicitly supports seeking
    def seek(self, offset: int, whence: int = 0) -> int:
        raise TypeError("seekable sources require a concrete seek implementation")


# this function enforces the destination complete write contract
def WriteStream(Target: Destination, TextValue: str, Payload: bytes) -> None:
    Writer = getattr(Target, "write", None)
    if not callable(Writer):
        raise TypeError("JSON destination must be a path or writable stream")
    if isinstance(Target, TextIoBase):
        Written = Writer(TextValue)
        Expected = len(TextValue)
    else:
        try:
            Written = Writer(Payload)
            Expected = len(Payload)
        except TypeError:
            Written = Writer(TextValue)
            Expected = len(TextValue)
    if Written is not None and Written != Expected:
        raise OSError(f"short JSON write: expected {Expected}, wrote {Written}")


# this function restores seekable sources after its temporary position mutation
def ReadPrefixMut(SourceValue: Source, Limit: int) -> bytes:
    if isinstance(SourceValue, (bytes, bytearray)):
        return bytes(SourceValue[:Limit])
    if isinstance(SourceValue, (str, FilePath)):
        with FilePath(SourceValue).expanduser().open("rb") as Handle:
            return Handle.read(Limit)
    Position = SourceValue.tell() if isinstance(SourceValue, TellSource) else None
    Value = SourceValue.read(Limit)
    if Position is not None and isinstance(SourceValue, SeekSource):
        SourceValue.seek(Position)
    return Value.encode("utf-8") if isinstance(Value, str) else bytes(Value)


# this function normalizes paths bytes and streams to unicode json text
def ReadText(SourceValue: Source) -> str:
    if isinstance(SourceValue, (bytes, bytearray)):
        return bytes(SourceValue).decode("utf-8")
    if isinstance(SourceValue, (str, FilePath)):
        return FilePath(SourceValue).expanduser().read_text("utf-8")
    Value = SourceValue.read()
    return Value.decode("utf-8") if isinstance(Value, bytes) else Value
