# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
from typing import Any as AnyValue

from tools.audit.FcstdContext import EnableSource
from tools.audit.FcstdFeatures import FeatureTypes
from tools.audit.FcstdResult import GetDisplayPath, MakeFailure, MakeUnsupported


EnableSource()

from convert import write_document as WriteDocument
from convert.adapters.freecad.Init import read_freecad as ReadFreecad
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks.core.Native import HasVendorPartEncoding


# isolated source auditing exercises parsing first principles writing and container readback
def AuditSource(
    SourcePath: FilePath,
    OutputRoot: FilePath,
    SourceIndex: int,
) -> dict[str, AnyValue]:
    try:
        DocumentData = ReadFreecad(SourcePath)
        SourceTypes = FeatureTypes(DocumentData)
        if DocumentData.assembly is None and not HasVendorPartEncoding(DocumentData):
            return MakeUnsupported(SourcePath, SourceTypes)
        TargetSuffix = ".SLDASM" if DocumentData.assembly is not None else ".SLDPRT"
        TargetPath = OutputRoot / f"audit-{SourceIndex:04d}{TargetSuffix}"
        ResultData = WriteDocument(DocumentData, TargetPath, allow_carrier=True)
        TargetData = TargetPath.read_bytes()
        ArchiveData = SldprtArchive.from_bytes(TargetData)
        NativeCapabilities = tuple(
            sorted(ItemData.value for ItemData in ResultData.native_capabilities)
        )
        return {
            "path": GetDisplayPath(SourcePath),
            "kind": "assembly" if DocumentData.assembly is not None else "part",
            "feature_types": SourceTypes,
            "application_usable": ResultData.application_usable,
            "vendor_loadable": ResultData.vendor_loadable,
            "near_lossless": ResultData.near_lossless,
            "native_capabilities": NativeCapabilities,
            "requirements": ResultData.requirements,
            "bytes": len(TargetData),
            "streams": len(ArchiveData.streams),
            "error": "",
        }
    except Exception as ErrorInfo:
        ErrorText = f"{type(ErrorInfo).__name__}: {ErrorInfo}"
        return MakeFailure(SourcePath, ErrorText)
