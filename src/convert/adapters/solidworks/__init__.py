# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.core.Adapter import SldprtAdapter, read_sldprt as ReadSldprt, write_sldprt as WriteSldprt
from convert.adapters.solidworks.assembly.Assembly import NativeAssembly as NativeAsm, NativeAssemblyConfiguration as NativeAsmConfig, NativeAssemblyDefinition as NativeAsmDefinition, NativeAssemblyFile as NativeAsmFile, NativeAssemblyOccurrence as NativeAsmItem, NativeDisplayComponent, NativeDisplayState, NativeMate, NativeMateEntity, NativeMateList, NativeOccurrencePath as NativeItemPath, NativeTessellationFace, decode_display_lists as DecodeDisplayLists, decode_mate_list as DecodeMateList, decode_native_assembly as DecodeNativeAsm, decode_tessellation_faces as DecodeTessellationFaces, expand_occurrence_paths as ExpandItemPaths
from convert.adapters.solidworks.container.Container import SldprtArchive, SldprtFormatError, StreamRecord, build_sldprt as BuildSldprt
from convert.adapters.solidworks.core.Display import neutral_meshes as NeutralMeshes
from convert.adapters.solidworks.core.Native import NativeClass, NativeConfiguration as NativeConfig, NativeConstraint as NativeRule, NativeDimension, NativeEndSpec, NativeFeature, NativeMarker, NativeModel, NativeName, NativeOperand, NativeOperation, NativePlane, NativeProfile, NativeScalar, NativeSketch, decode_native_model as DecodeNativeModel
from convert.adapters.solidworks.container.Parasolid import ParasolidPayload, ParasolidWriteError, contains_parasolid_payload as ContainsParasolidPayload, decode_brep_model as DecodeBrepModel, decode_partition_stream as DecodePartitionStream, encode_blank_partition_stream as EncodeBlankPartition, encode_brep_model as EncodeBrepModel, encode_partition_stream as EncodePartitionStream, is_native_parasolid_payload as IsNativeParasolidPayload

# this binding exists because shared behavior needs one stable value
KAllValue = [NameValue for NameValue in globals() if not NameValue.startswith('_')]

# this binding exists because shared behavior needs one stable value
globals()['NativeAssembly'] = NativeAsm

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyConfiguration'] = NativeAsmConfig

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyDefinition'] = NativeAsmDefinition

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyFile'] = NativeAsmFile

# this binding exists because shared behavior needs one stable value
globals()['NativeAssemblyOccurrence'] = NativeAsmItem

# this binding exists because shared behavior needs one stable value
globals()['NativeConfiguration'] = NativeConfig

# this binding exists because shared behavior needs one stable value
globals()['NativeConstraint'] = NativeRule

# this binding exists because shared behavior needs one stable value
globals()['NativeOccurrencePath'] = NativeItemPath

# this binding exists because shared behavior needs one stable value
globals()['build_sldprt'] = BuildSldprt

# this binding exists because shared behavior needs one stable value
globals()['contains_parasolid_payload'] = ContainsParasolidPayload

# this binding exists because shared behavior needs one stable value
globals()['decode_brep_model'] = DecodeBrepModel

# this binding exists because shared behavior needs one stable value
globals()['decode_display_lists'] = DecodeDisplayLists

# this binding exists because shared behavior needs one stable value
globals()['decode_mate_list'] = DecodeMateList

# this binding exists because shared behavior needs one stable value
globals()['decode_native_assembly'] = DecodeNativeAsm

# this binding exists because shared behavior needs one stable value
globals()['decode_native_model'] = DecodeNativeModel

# this binding exists because shared behavior needs one stable value
globals()['decode_partition_stream'] = DecodePartitionStream

# this binding exists because shared behavior needs one stable value
globals()['decode_tessellation_faces'] = DecodeTessellationFaces

# this binding exists because shared behavior needs one stable value
globals()['encode_blank_partition_stream'] = EncodeBlankPartition

# this binding exists because shared behavior needs one stable value
globals()['encode_brep_model'] = EncodeBrepModel

# this binding exists because shared behavior needs one stable value
globals()['encode_partition_stream'] = EncodePartitionStream

# this binding exists because shared behavior needs one stable value
globals()['expand_occurrence_paths'] = ExpandItemPaths

# this binding exists because shared behavior needs one stable value
globals()['is_native_parasolid_payload'] = IsNativeParasolidPayload

# this binding exists because shared behavior needs one stable value
globals()['neutral_meshes'] = NeutralMeshes

# this binding exists because shared behavior needs one stable value
globals()['read_sldprt'] = ReadSldprt

# this binding exists because shared behavior needs one stable value
globals()['write_sldprt'] = WriteSldprt
