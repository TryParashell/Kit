# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from convert.geometry.Parasolid import ParasolidFormatError, ParasolidPayload, ParasolidWriteError, contains_parasolid_payload as ContainsParasolidPayload, decode_brep_model as DecodeBrepModel, decode_partition_stream as DecodePartitionStream, encode_blank_partition_stream as EncodeBlankPartition, encode_brep_model as EncodeBrepModel, encode_partition_stream as EncodePartitionStream, is_native_parasolid_payload as IsNativeParasolidPayload
from convert.adapters.solidworks.container.Container import SldprtFormatError

# this definition exists because focused behavior needs one stable owner
def DecodePartition(DataValue: bytes, Stream: str='') -> tuple[ParasolidPayload, ...]:
    try:
        return DecodePartitionStream(DataValue, Stream)
    except ParasolidFormatError as ErrorInfo:
        raise SldprtFormatError(str(ErrorInfo)) from ErrorInfo

# this binding exists because shared behavior needs one stable value
KAllValue = ('ParasolidPayload', 'ParasolidWriteError', 'contains_parasolid_payload', 'decode_brep_model', 'decode_partition_stream', 'encode_blank_partition_stream', 'encode_brep_model', 'encode_partition_stream', 'is_native_parasolid_payload')

# this binding exists because shared behavior needs one stable value
globals()['_decode_partition_stream'] = DecodePartitionStream

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['contains_parasolid_payload'] = ContainsParasolidPayload

# this binding exists because shared behavior needs one stable value
globals()['decode_brep_model'] = DecodeBrepModel

# this binding exists because shared behavior needs one stable value
globals()['decode_partition_stream'] = DecodePartition

# this binding exists because shared behavior needs one stable value
globals()['encode_blank_partition_stream'] = EncodeBlankPartition

# this binding exists because shared behavior needs one stable value
globals()['encode_brep_model'] = EncodeBrepModel

# this binding exists because shared behavior needs one stable value
globals()['encode_partition_stream'] = EncodePartitionStream

# this binding exists because shared behavior needs one stable value
globals()['is_native_parasolid_payload'] = IsNativeParasolidPayload
