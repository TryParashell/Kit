# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

import pytest as Pytest

from convert import extract_brep as ExtractLegacy
from convert import open_document as OpenLegacy
from convert.adapters import is_windows_device_name as IsDeviceName
from interchange import BrepPayload, PayloadRole
from tests.convert.api_test_paths import KSamplePath


# extraction must emit exact brep bytes while ignoring history and missing payload data
def CheckExactBrep(TmpPath: FilePath) -> None:
    SourceData = OpenLegacy(KSamplePath)
    DocumentData = ReplaceData(
        SourceData,
        brep_payloads=(
            *SourceData.brep_payloads,
            BrepPayload("history", "vendor", "native", "", "", data=b"history"),
            BrepPayload(
                "missing",
                "vendor",
                "geometry",
                "",
                "",
                role=PayloadRole.BREP,
                file_extension=".geo",
            ),
        ),
    )
    OutputPaths = ExtractLegacy(DocumentData, TmpPath)
    assert len(OutputPaths) == 3
    assert [OutputPath.read_bytes() for OutputPath in OutputPaths] == [
        PayloadData.data
        for PayloadData in DocumentData.brep_payloads
        if PayloadData.role == PayloadRole.BREP and PayloadData.data is not None
    ]
    assert {OutputPath.suffix for OutputPath in OutputPaths} == {".x_b"}
    with Pytest.raises(FileExistsError):
        ExtractLegacy(DocumentData, TmpPath)


# reserved device names need prefixes because extraction must work safely on windows filesystems
def CheckDeviceBrep(TmpPath: FilePath) -> None:
    PayloadData = BrepPayload(
        "CON",
        "kernel",
        "shape",
        "",
        "",
        data=b"shape",
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    DocumentData = ReplaceData(
        OpenLegacy(KSamplePath),
        brep_payloads=(PayloadData,),
    )
    assert ExtractLegacy(DocumentData, TmpPath)[0].name == "_CON.x_b"


# device recognition must cover canonical and unicode digit aliases without false positives
def CheckDeviceName() -> None:
    ReservedNames = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{IndexValue}" for IndexValue in range(1, 10)),
        *(f"LPT{IndexValue}" for IndexValue in range(1, 10)),
        *(f"COM{IndexValue}" for IndexValue in "¹²³"),
        *(f"LPT{IndexValue}" for IndexValue in "¹²³"),
    }
    assert all(IsDeviceName(NameText) for NameText in ReservedNames)
    assert all(IsDeviceName(f"{NameText}.x_b") for NameText in ReservedNames)
    assert not any(
        IsDeviceName(NameText)
        for NameText in ("COM0", "COM10", "LPT0", "LPT10", "CONTOUR")
    )
