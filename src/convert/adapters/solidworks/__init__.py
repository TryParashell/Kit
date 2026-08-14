# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.solidworks.core.Adapter import SldprtAdapter, read_sldprt, write_sldprt
from convert.adapters.solidworks.assembly.Assembly import NativeAssembly, NativeAssemblyConfiguration, NativeAssemblyDefinition, NativeAssemblyFile, NativeAssemblyOccurrence, NativeDisplayComponent, NativeDisplayState, NativeMate, NativeMateEntity, NativeMateList, NativeOccurrencePath, NativeTessellationFace, decode_display_lists, decode_mate_list, decode_native_assembly, decode_tessellation_faces, expand_occurrence_paths
from convert.adapters.solidworks.container.Container import SldprtArchive, SldprtFormatError, StreamRecord, build_sldprt
from convert.adapters.solidworks.core.Display import neutral_meshes
from convert.adapters.solidworks.core.Native import NativeClass, NativeConfiguration, NativeConstraint, NativeDimension, NativeEndSpec, NativeFeature, NativeMarker, NativeModel, NativeName, NativeOperand, NativeOperation, NativePlane, NativeProfile, NativeScalar, NativeSketch, decode_native_model
from convert.adapters.solidworks.container.Parasolid import ParasolidPayload, ParasolidWriteError, contains_parasolid_payload, decode_brep_model, decode_partition_stream, encode_blank_partition_stream, encode_brep_model, encode_partition_stream, is_native_parasolid_payload

__all__ = [name for name in globals() if not name.startswith("_")]
