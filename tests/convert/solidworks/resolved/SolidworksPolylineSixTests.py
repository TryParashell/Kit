# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import replace as ReplaceData
import hashlib as Hashlib
import math as MathInfo
from pathlib import Path as FilePath
import pytest as PytestLib
from convert import write_document as WriteDocument
from convert.adapters.freecad import read_freecad as ReadFreecad
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as Stream,
    KEYWORDS_STREAM as StreamA,
    RESOLVED_FEATURES_STREAM as StreamB,
)
from convert.adapters.solidworks.core.Native import (
    HasVendorPartEncoding,
    decode_native_model as DecodeNativeModel,
)
from convert.adapters.solidworks.programs.resolved.polyline.sixpoint.Program import (
    EncodeProgram,
    KDepthOffset,
    KFieldOwners,
    KPointOffsets,
    KResolvedOps,
    PadFieldMap,
)

# centralizes shared evidence so every related assertion uses one value
KRepoRoot = FilePath(__file__).resolve().parents[4]

# centralizes shared evidence so every related assertion uses one value
KDonorStream = (
    KRepoRoot
    / "examples"
    / "Fixtures"
    / "SolidWorks"
    / "donors"
    / "poly6_boss"
    / "resolved.bin"
)

# centralizes shared evidence so every related assertion uses one value
KGateDigest = "b973bd5326bbdb65b8e8b5e8345e0bdbdef20d345bf70d9f7562e5a74077bfb4"

# centralizes shared evidence so every related assertion uses one value
KDonorPoints = (
    (0.0, 0.0),
    (40.0, 0.0),
    (40.0, 10.0),
    (15.0, 10.0),
    (15.0, 25.0),
    (0.0, 25.0),
)

# centralizes shared evidence so every related assertion uses one value
KFreeCadPolyline = KRepoRoot / ".rescratch" / "gates" / "fcstd" / "gate_polyline6.FCStd"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSPCETF() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == 12283
    assert Hashlib.sha256(PayloadData).hexdigest() == KGateDigest
    assert len(KResolvedOps) == 3022
    assert len(KFieldOwners) == 516
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, IgnoredValue in KResolvedOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
        } or KindName.startswith(("primitive:", "direct:"))
        ObjectCount += KindName in {"definition", "classref", "objectref", "null"}
        DefineCount += KindName == "definition"
        CursorPos += FieldWidth
    assert CursorPos == len(PayloadData)
    assert ObjectCount == 380
    assert DefineCount == 45


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSPRCO() -> None:
    OracleData = KDonorStream.read_bytes()
    ProgramData = EncodeProgram(PadFieldMap(KDonorPoints, 8.0))
    assert ProgramData == OracleData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSPRVWO() -> None:
    with PytestLib.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({32: "a deliberately incompatible comment width"})


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSPVIS() -> None:
    with PytestLib.raises(SldprtFormatError, match="exactly six"):
        PadFieldMap(KDonorPoints[:5], 8.0)
    with PytestLib.raises(SldprtFormatError, match="finite"):
        PadFieldMap((*KDonorPoints[:5], (MathInfo.inf, 25.0)), 8.0)
    with PytestLib.raises(SldprtFormatError, match="unique"):
        PadFieldMap((*KDonorPoints[:5], KDonorPoints[0]), 8.0)
    with PytestLib.raises(SldprtFormatError, match="intersect"):
        PadFieldMap(
            ((0.0, 0.0), (2.0, 2.0), (0.0, 2.0), (2.0, 0.0), (3.0, 0.0), (3.0, 3.0)),
            8.0,
        )
    with PytestLib.raises(SldprtFormatError, match="positive"):
        PadFieldMap(KDonorPoints, 0.0)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSPOANF() -> None:
    FieldValues = PadFieldMap(KDonorPoints, 8.0)
    assert tuple(FieldValues) == (*KPointOffsets, KDepthOffset)
    assert tuple((FieldValues[OffsetPos] for OffsetPos in KPointOffsets)) == (
        0.0,
        0.0,
        0.04,
        0.0,
        0.04,
        0.01,
        0.015,
        0.01,
        0.015,
        0.025,
        0.0,
        0.025,
    )
    assert FieldValues[KDepthOffset] == 0.008


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KFreeCadPolyline.is_file(), reason="six line FreeCAD corpus unavailable"
)
def TestFCPSWNPSWP(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KFreeCadPolyline)
    TargetPath = TmpPath / "FreeCadPolylineSix.SLDPRT"
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=True)
    ArchiveData = SldprtArchive.from_bytes(TargetPath.read_bytes())
    ResolvedData = ArchiveData.require(StreamB)
    NativeData = DecodeNativeModel(
        ArchiveData.require(StreamA),
        ResolvedData,
        ArchiveData.require(Stream),
        resolved_stream=StreamB,
    )
    assert HasVendorPartEncoding(SourceData)
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.near_lossless is True
    assert len(ResolvedData) == 12283
    assert Hashlib.sha256(ResolvedData).hexdigest() == KGateDigest
    assert tuple(
        (
            (ItemData.kind, ItemData.coordinates)
            for ItemData in NativeData.sketches[0].profiles
        )
    ) == (
        (
            "polyline",
            (-20.0, -20.0, 20.0, -20.0, 20.0, 0.0, 0.0, 0.0, 0.0, 20.0, -20.0, 20.0),
        ),
    )
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 32
    assert NativeData.operations[0].profile_id == 26
    assert NativeData.operations[0].direction_code == 0
    assert NativeData.operations[0].termination_code == 0
    assert NativeData.operations[0].length_mm == PytestLib.approx(10.0)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KFreeCadPolyline.is_file(), reason="six line FreeCAD corpus unavailable"
)
def TestFCPSROSC() -> None:
    SourceData = ReadFreecad(KFreeCadPolyline)
    SketchData = SourceData.sketches[0]
    ProfileData = SketchData.closed_profile_entity_ids[0]
    FiveLineData = ReplaceData(
        SourceData,
        sketches=(
            ReplaceData(
                SketchData,
                entities=SketchData.entities[:-1],
                closed_profile_entity_ids=(ProfileData[:-1],),
            ),
        ),
    )
    assert not HasVendorPartEncoding(FiveLineData)
