# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
from typing import TypeGuard, TypedDict, cast

from tools.audit.FcstdContext import KRepositoryRoot


# audit records need a shared shape across direct and isolated source processing
class AuditRecord(TypedDict):
    path: str
    kind: str
    feature_types: tuple[str, ...]
    application_usable: bool
    vendor_loadable: bool
    near_lossless: bool
    native_capabilities: tuple[str, ...]
    requirements: tuple[str, ...]
    bytes: int
    streams: int
    error: str


# serialized tuple fields require validated string lists before reconstructing audit records
def IsStringList(ValueData: object) -> TypeGuard[list[str]]:
    if not isinstance(ValueData, list):
        return False
    CandidateData = cast(list[object], ValueData)
    return all(isinstance(ItemData, str) for ItemData in CandidateData)


# isolated json needs every field validated before it rejoins typed report processing
def ParseAuditRecord(ValueData: object) -> AuditRecord | None:
    if not isinstance(ValueData, dict):
        return None
    CandidateData = cast(dict[object, object], ValueData)
    PathData = CandidateData.get("path")
    KindData = CandidateData.get("kind")
    FeatureTypesData = CandidateData.get("feature_types")
    ApplicationUsableData = CandidateData.get("application_usable")
    VendorLoadableData = CandidateData.get("vendor_loadable")
    NearLosslessData = CandidateData.get("near_lossless")
    NativeCapabilitiesData = CandidateData.get("native_capabilities")
    RequirementsData = CandidateData.get("requirements")
    BytesData = CandidateData.get("bytes")
    StreamsData = CandidateData.get("streams")
    ErrorData = CandidateData.get("error")
    if not isinstance(PathData, str) or not isinstance(KindData, str):
        return None
    if not IsStringList(FeatureTypesData):
        return None
    if not isinstance(ApplicationUsableData, bool):
        return None
    if not isinstance(VendorLoadableData, bool):
        return None
    if not isinstance(NearLosslessData, bool):
        return None
    if not IsStringList(NativeCapabilitiesData):
        return None
    if not IsStringList(RequirementsData):
        return None
    if not isinstance(BytesData, int) or not isinstance(StreamsData, int):
        return None
    if not isinstance(ErrorData, str):
        return None
    return {
        "path": PathData,
        "kind": KindData,
        "feature_types": tuple(FeatureTypesData),
        "application_usable": ApplicationUsableData,
        "vendor_loadable": VendorLoadableData,
        "near_lossless": NearLosslessData,
        "native_capabilities": tuple(NativeCapabilitiesData),
        "requirements": tuple(RequirementsData),
        "bytes": BytesData,
        "streams": StreamsData,
        "error": ErrorData,
    }


# stable path rendering keeps audit records portable inside and outside the repository
def GetDisplayPath(SourcePath: FilePath) -> str:
    if SourcePath.is_relative_to(KRepositoryRoot):
        return str(SourcePath.relative_to(KRepositoryRoot))
    return str(SourcePath)


# unsupported records distinguish missing native grammar from parser or writer failures
def MakeUnsupported(SourcePath: FilePath, TypeNames: tuple[str, ...]) -> AuditRecord:
    return {
        "path": GetDisplayPath(SourcePath),
        "kind": "part",
        "feature_types": TypeNames,
        "application_usable": False,
        "vendor_loadable": False,
        "near_lossless": False,
        "native_capabilities": (),
        "requirements": ("no_typed_native_feature_program",),
        "bytes": 0,
        "streams": 0,
        "error": "",
    }


# failure records preserve batch progress because one malformed source must not hide others
def MakeFailure(SourcePath: FilePath, ErrorText: str) -> AuditRecord:
    return {
        "path": GetDisplayPath(SourcePath),
        "kind": "unknown",
        "feature_types": (),
        "application_usable": False,
        "vendor_loadable": False,
        "near_lossless": False,
        "native_capabilities": (),
        "requirements": (),
        "bytes": 0,
        "streams": 0,
        "error": ErrorText,
    }
