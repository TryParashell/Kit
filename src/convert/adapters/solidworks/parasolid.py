# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.parasolid import (
    ParasolidFormatError,
    ParasolidPayload,
    ParasolidWriteError,
    contains_parasolid_payload,
    decode_brep_model,
    decode_partition_stream as _decode_partition_stream,
    encode_blank_partition_stream,
    encode_brep_model,
    encode_partition_stream,
    is_native_parasolid_payload,
)

from .container import SldprtFormatError


def decode_partition_stream(
    data: bytes, stream: str = ""
) -> tuple[ParasolidPayload, ...]:
    try:
        return _decode_partition_stream(data, stream)
    except ParasolidFormatError as exc:
        raise SldprtFormatError(str(exc)) from exc


__all__ = (
    "ParasolidPayload",
    "ParasolidWriteError",
    "contains_parasolid_payload",
    "decode_brep_model",
    "decode_partition_stream",
    "encode_blank_partition_stream",
    "encode_brep_model",
    "encode_partition_stream",
    "is_native_parasolid_payload",
)
