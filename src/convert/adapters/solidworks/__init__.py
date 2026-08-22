# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.core.Adapter import (
    SldprtAdapter as SldprtAdapter,
    read_sldprt as ReadSldprt,
    write_sldprt as WriteSldprt,
)
from convert.adapters.solidworks.assembly.Assembly import (
    NativeAssembly as NativeAsm,
    NativeAssemblyConfiguration as NativeAsmConfig,
    NativeAssemblyDefinition as NativeAsmDefinition,
    NativeAssemblyFile as NativeAsmFile,
    NativeAssemblyOccurrence as NativeAsmItem,
    NativeDisplayComponent as NativeDisplayComponent,
    NativeDisplayState as NativeDisplayState,
    NativeMate as NativeMate,
    NativeMateEntity as NativeMateEntity,
    NativeMateList as NativeMateList,
    NativeOccurrencePath as NativeItemPath,
    NativeTessellationFace as NativeTessellationFace,
    decode_display_lists as DecodeDisplayLists,
    decode_mate_list as DecodeMateList,
    decode_native_assembly as DecodeNativeAsm,
    decode_tessellation_faces as DecodeTessellationFaces,
    expand_occurrence_paths as ExpandItemPaths,
)
from convert.adapters.solidworks.container.Container import (
    SldprtArchive as SldprtArchive,
    SldprtFormatError as SldprtFormatError,
    StreamRecord as StreamRecord,
    build_sldprt as BuildSldprt,
)
from convert.adapters.solidworks.core.Display import neutral_meshes as NeutralMeshes
from convert.adapters.solidworks.core.Native import (
    NativeClass as NativeClass,
    NativeConfiguration as NativeConfig,
    NativeConstraint as NativeRule,
    NativeDimension as NativeDimension,
    NativeEndSpec as NativeEndSpec,
    NativeFeature as NativeFeature,
    NativeMarker as NativeMarker,
    NativeModel as NativeModel,
    NativeName as NativeName,
    NativeOperand as NativeOperand,
    NativeOperation as NativeOperation,
    NativePlane as NativePlane,
    NativeProfile as NativeProfile,
    NativeScalar as NativeScalar,
    NativeSketch as NativeSketch,
    decode_native_model as DecodeNativeModel,
)
from convert.adapters.solidworks.container.Parasolid import (
    ParasolidPayload as ParasolidPayload,
    ParasolidWriteError as ParasolidWriteError,
    contains_parasolid_payload as ContainsParasolidPayload,
    decode_brep_model as DecodeBrepModel,
    decode_partition_stream as DecodePartitionStream,
    encode_blank_partition_stream as EncodeBlankPartition,
    encode_brep_model as EncodeBrepModel,
    encode_partition_stream as EncodePartitionStream,
    is_native_parasolid_payload as IsNativeParasolidPayload,
)

# this binding exists because shared behavior needs one stable value
KAllValue = [NameValue for NameValue in globals() if not NameValue.startswith("_")]

# this binding exists because shared behavior needs one stable value
NativeAssembly = NativeAsm

# this binding exists because shared behavior needs one stable value
NativeAssemblyConfiguration = NativeAsmConfig

# this binding exists because shared behavior needs one stable value
NativeAssemblyDefinition = NativeAsmDefinition

# this binding exists because shared behavior needs one stable value
NativeAssemblyFile = NativeAsmFile

# this binding exists because shared behavior needs one stable value
NativeAssemblyOccurrence = NativeAsmItem

# this binding exists because shared behavior needs one stable value
NativeConfiguration = NativeConfig

# this binding exists because shared behavior needs one stable value
NativeConstraint = NativeRule

# this binding exists because shared behavior needs one stable value
NativeOccurrencePath = NativeItemPath

# this binding exists because shared behavior needs one stable value
build_sldprt = BuildSldprt

# this binding exists because shared behavior needs one stable value
contains_parasolid_payload = ContainsParasolidPayload

# this binding exists because shared behavior needs one stable value
decode_brep_model = DecodeBrepModel

# this binding exists because shared behavior needs one stable value
decode_display_lists = DecodeDisplayLists

# this binding exists because shared behavior needs one stable value
decode_mate_list = DecodeMateList

# this binding exists because shared behavior needs one stable value
decode_native_assembly = DecodeNativeAsm

# this binding exists because shared behavior needs one stable value
decode_native_model = DecodeNativeModel

# this binding exists because shared behavior needs one stable value
decode_partition_stream = DecodePartitionStream

# this binding exists because shared behavior needs one stable value
decode_tessellation_faces = DecodeTessellationFaces

# this binding exists because shared behavior needs one stable value
encode_blank_partition_stream = EncodeBlankPartition

# this binding exists because shared behavior needs one stable value
encode_brep_model = EncodeBrepModel

# this binding exists because shared behavior needs one stable value
encode_partition_stream = EncodePartitionStream

# this binding exists because shared behavior needs one stable value
expand_occurrence_paths = ExpandItemPaths

# this binding exists because shared behavior needs one stable value
is_native_parasolid_payload = IsNativeParasolidPayload

# this binding exists because shared behavior needs one stable value
neutral_meshes = NeutralMeshes

# this binding exists because shared behavior needs one stable value
read_sldprt = ReadSldprt

# this binding exists because shared behavior needs one stable value
write_sldprt = WriteSldprt
