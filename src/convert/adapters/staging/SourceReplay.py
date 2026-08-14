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

from convert.adapters.base.ContractTypes import KSourceType


# probing must not consume one shot sources before the selected reader receives them
def GetReplayMut(SourceData: KSourceType) -> KSourceType:
    if isinstance(SourceData, (str, FilePath, bytes, bytearray)):
        return SourceData
    try:
        StreamPos = SourceData.tell()
        SourceData.seek(StreamPos)
        return SourceData
    except (AttributeError, OSError, TypeError, ValueError):
        SourceValue = SourceData.read()
    if isinstance(SourceValue, str):
        return TextStream(SourceValue)
    if isinstance(SourceValue, (bytes, bytearray)):
        return ByteStream(bytes(SourceValue))
    raise TypeError("source stream must yield text or bytes")
