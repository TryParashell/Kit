# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.configuration.default.Program import (
    EncodeField,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

from .Registry import (
    FieldOwners,
    AnnotationOps,
)


# the source interval records where the reusable manager was observed
SourceRange = (24328, 24840)

# exact closure rejects any future field-width or ordering drift
ReferenceLength = 512


# typed field replay emits the two-view manager without retaining vendor byte spans
def EncodeTwoViewAnnotationManager() -> bytes:
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, FieldValue in AnnotationOps:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"annotation field program drifted at {StartPos}")
        FieldData = EncodeField(KindName, FieldValue)
        if len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"annotation field width changed at {StartPos}")
        OutputData.extend(FieldData)
        SourceCursor += FieldWidth
    if SourceCursor != ReferenceLength:
        raise SldprtFormatError("annotation field program did not close its source")
    return bytes(OutputData)
