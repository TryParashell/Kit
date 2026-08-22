# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath

from interchange import CadDocument

from convert.adapters.base.ContractTypes import KSourceType as Source
from convert.api.ApiOpen import OpenDocument
from convert.geometry.BrepNames import MakeBrepNameMut
from convert.geometry.BrepPayloads import GetBrepPayloads


# exact brep extraction gives callers native geometry bytes without invoking cad software
def ExtractBrep(
    SourceData: Source | CadDocument,
    FolderPath: str | FilePath,
    *,
    SourceFormat: str | None = None,
    Overwrite: bool = False,
) -> tuple[FilePath, ...]:
    DocumentData = (
        SourceData
        if isinstance(SourceData, CadDocument)
        else OpenDocument(SourceData, SourceFormat=SourceFormat, IncludeBrep=True)
    )
    TargetPath = FilePath(FolderPath).expanduser().resolve()
    TargetPath.mkdir(parents=True, exist_ok=True)
    OutputPaths: list[FilePath] = []
    UsedNames: set[str] = set()
    for IndexValue, PayloadData in enumerate(GetBrepPayloads(DocumentData), start=1):
        OutputName = MakeBrepNameMut(PayloadData, IndexValue, UsedNames)
        OutputPath = TargetPath / f"{OutputName}{PayloadData.FileExtension}"
        if OutputPath.exists() and not Overwrite:
            raise FileExistsError(OutputPath)
        PayloadBytes = PayloadData.PayloadData
        if PayloadBytes is None:
            continue
        OutputPath.write_bytes(PayloadBytes)
        OutputPaths.append(OutputPath)
    return tuple(OutputPaths)
