# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from interchange import BrepModel
from convert.geometry.Parasolid import (
    DecodeBrepMut,
    DecodePartMut,
    EncodeBlankApi,
    ParaPayload,
    ParaFormatError,
    ParaWriteError,
    EncodeBrepMut,
    EncodePartMut,
    HasPayloadMut,
    IsPayloadApiMut,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

# this alias preserves the established solidworks payload import with a concrete type
ParasolidPayload = ParaPayload

# this alias preserves the established solidworks error import with a concrete type
ParasolidFormatError = ParaFormatError

# this alias preserves the established solidworks error import with a concrete type
ParasolidWriteError = ParaWriteError


# this definition exists because focused behavior needs one stable owner
def DecodePartition(DataValue: bytes, Stream: str = "") -> tuple[ParaPayload, ...]:
    try:
        return DecodePartMut(DataValue, Stream)
    except ParasolidFormatError as ErrorInfo:
        raise SldprtFormatError(str(ErrorInfo)) from ErrorInfo


# this wrapper preserves the typed public decoding contract for solidworks callers
def DecodeBrep(DataValue: bytes | bytearray) -> BrepModel | None:
    return DecodeBrepMut(DataValue)


# this wrapper preserves the typed public encoding contract for solidworks callers
def EncodeBrep(
    ModelData: BrepModel,
    *,
    partition: bool = True,
    solidworks_feature_ids: dict[str, int] | None = None,
) -> bytes:
    return EncodeBrepMut(
        ModelData,
        Partition=partition,
        SolidworksFeatureIds=solidworks_feature_ids,
    )


# this wrapper preserves the typed blank partition contract for solidworks callers
def EncodeBlank() -> bytes:
    return EncodeBlankApi()


# this wrapper preserves the typed partition encoding contract for solidworks callers
def EncodePartition(DataValue: bytes | bytearray) -> bytes:
    return EncodePartMut(DataValue)


# this wrapper preserves the typed payload recognition contract for solidworks callers
def ContainsPayload(DataValue: bytes | bytearray) -> bool:
    return HasPayloadMut(DataValue)


# this wrapper preserves the typed native payload contract for solidworks callers
def IsNativePayload(DataValue: bytes | bytearray) -> bool:
    return IsPayloadApiMut(DataValue)


# this binding exists because shared behavior needs one stable value
KAllValue = (
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

# this binding exists because shared behavior needs one stable value
_decode_partition_stream = DecodePartMut

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
contains_parasolid_payload = ContainsPayload

# this binding exists because shared behavior needs one stable value
decode_brep_model = DecodeBrep

# this binding exists because shared behavior needs one stable value
decode_partition_stream = DecodePartition

# this binding exists because shared behavior needs one stable value
encode_blank_partition_stream = EncodeBlank

# this binding exists because shared behavior needs one stable value
encode_brep_model = EncodeBrep

# this binding exists because shared behavior needs one stable value
encode_partition_stream = EncodePartition

# this binding exists because shared behavior needs one stable value
is_native_parasolid_payload = IsNativePayload
