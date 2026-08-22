# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    FieldValue as FieldType,
)

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    EncodeValue,
    KPrimitiveFormats,
    ReplayAssembly,
)

from .Registry import (  # lgtm[py/unused-import]
    FieldOwners as FieldOwners,
    KFieldOwners as KFieldOwners,
    StreamPrograms as StreamPrograms,
)


# legacy format access remains available while shared encoding owns the mapping
PrimitiveFormats = KPrimitiveFormats


# each operation serializes one recovered value through its typed contract
def EncodeField(KindName: str, FieldValue: FieldType) -> bytes:
    return EncodeValue(KindName, FieldValue, "assembly")


# callers may replace semantic fields while source offsets preserve field order
def EncodeProgram(
    StreamName: str, Overrides: Mapping[int, FieldType] | None = None
) -> bytes:
    try:
        Operations = StreamPrograms[StreamName]
    except KeyError as ErrorData:
        raise SldprtFormatError(
            f"unknown assembly stream {StreamName!r}"
        ) from ErrorData
    return ReplayAssembly(Operations, Overrides)
