# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
import json as JsonLib
from pathlib import Path as FilePath
from convert.adapters.solidworks.core.Topology import (
    BOSS_OPERATION as Operation,
    CUT_OPERATION as OperationA,
    FeatureTopology,
    FULL_REVOLUTION_END as EndInfo,
    REVOLVE_BOSS_OPERATION as OperationB,
    REVOLVE_CUT_OPERATION as OperationC,
    REVOLVE_SUPPORTS as Supports,
    SUPPORTED_END_CONDITIONS as ConditionsA,
)

# centralizes shared evidence so every related assertion uses one value
KRootInfo = (
    FilePath(__file__).resolve().parents[4]
    / "examples"
    / "Fixtures"
    / "SolidWorks"
    / "donors"
)

# centralizes shared evidence so every related assertion uses one value
KPathInfo = KRootInfo / "manifest.json"

# centralizes shared evidence so every related assertion uses one value
KNameInfoA = "resolved.bin"

# centralizes shared evidence so every related assertion uses one value
KNameInfo = "meta.json"

# centralizes shared evidence so every related assertion uses one value
KDirectory = "container"

# centralizes shared evidence so every related assertion uses one value
KCount = 32

# centralizes shared evidence so every related assertion uses one value
KOperations = frozenset({Operation, OperationA, OperationB, OperationC})

# centralizes shared evidence so every related assertion uses one value
KConditions = ConditionsA | {EndInfo}

# centralizes shared evidence so every related assertion uses one value
KeysInfo = (
    "features",
    "feature_ids",
    "sketch_ids",
    "feature_names",
    "sketch_names",
    "point_counts",
    "arc_counts",
    "depth_present",
)


# keeps this focused behavior isolated so regressions remain immediately visible
def Manifest() -> dict[str, object]:
    assert KPathInfo.is_file(), f"missing donor fixture manifest {KPathInfo}"
    return JsonLib.loads(KPathInfo.read_text(encoding="utf-8"))


# keeps this focused behavior isolated so regressions remain immediately visible
def ManifestDonors() -> dict[str, dict[str, object]]:
    Donors = Manifest()["donors"]
    assert isinstance(Donors, dict)
    return Donors


# keeps this focused behavior isolated so regressions remain immediately visible
def ContainerFN(NameText: str) -> str:
    return f"{NameText.replace('/', '__')}.bin"


# keeps this focused behavior isolated so regressions remain immediately visible
def MetaInfo(DonorId: str) -> dict[str, object]:
    TargetPath = KRootInfo / DonorId / KNameInfo
    return JsonLib.loads(TargetPath.read_text(encoding="utf-8"))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEMDHAFD() -> None:
    for DonorId in ManifestDonors():
        Directory = KRootInfo / DonorId
        assert Directory.is_dir(), f"missing fixture directory for {DonorId}"
        assert (Directory / KNameInfoA).is_file(), DonorId
        assert (Directory / KNameInfo).is_file(), DonorId


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTMLETCFD() -> None:
    Donors = ManifestDonors()
    assert len(Donors) == KCount
    assert Manifest()["donor_count"] == KCount
    OnDisk = sorted(
        (TargetPath.name for TargetPath in KRootInfo.iterdir() if TargetPath.is_dir())
    )
    assert sorted(Donors) == OnDisk


# keeps this focused behavior isolated so regressions remain immediately visible
def TestERFMIMD() -> None:
    for DonorId, RecordInfo in ManifestDonors().items():
        Resolved = RecordInfo["resolved"]
        Payload = (KRootInfo / DonorId / KNameInfoA).read_bytes()
        assert Resolved["length"] == len(Payload), DonorId
        assert Resolved["sha256"] == Hashlib.sha256(Payload).hexdigest(), DonorId
        assert Resolved["file"] == KNameInfoA, DonorId


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTMTTCFB() -> None:
    Donors = ManifestDonors()
    ResolvedBytes = sum(
        (len((KRootInfo / DonorId / KNameInfoA).read_bytes()) for DonorId in Donors)
    )
    ContainerBytes = 0
    for DonorId, RecordInfo in Donors.items():
        for NameText in RecordInfo["container"]:
            TargetPath = KRootInfo / DonorId / KDirectory
            ContainerBytes += len((TargetPath / ContainerFN(NameText)).read_bytes())
    assert Manifest()["resolved_bytes"] == ResolvedBytes
    assert Manifest()["container_bytes"] == ContainerBytes


# keeps this focused behavior isolated so regressions remain immediately visible
def TestECFMIMD() -> None:
    for DonorId, RecordInfo in ManifestDonors().items():
        Index = RecordInfo["container"]
        assert Index, DonorId
        for NameText, Entry in Index.items():
            TargetPath = KRootInfo / DonorId / KDirectory
            TargetPath = TargetPath / ContainerFN(NameText)
            Payload = TargetPath.read_bytes()
            assert Entry["length"] == len(Payload), (DonorId, NameText)
            assert Entry["sha256"] == Hashlib.sha256(Payload).hexdigest(), (
                DonorId,
                NameText,
            )
            assert Entry["file"] == f"{KDirectory}/{TargetPath.name}", (
                DonorId,
                NameText,
            )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEMFAWTMAIS() -> None:
    for DonorId, RecordInfo in ManifestDonors().items():
        MetaInfoA = MetaInfo(DonorId)
        assert MetaInfoA["donor_id"] == DonorId
        assert MetaInfoA["stream_bytes"] == RecordInfo["resolved"]["length"]
        assert isinstance(MetaInfoA["measured"], bool)
        Streams = {
            ItemValue["name"]: ItemValue["file"]
            for ItemValue in MetaInfoA["container_streams"]
        }
        assert sorted(Streams) == sorted(RecordInfo["container"])
        for NameText, FileName in Streams.items():
            assert FileName == ContainerFN(NameText), DonorId


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEMFDOEPF() -> None:
    for DonorId in ManifestDonors():
        MetaInfoA = MetaInfo(DonorId)
        Count = len(MetaInfoA["features"])
        assert Count >= 1, DonorId
        for LookupKey in KeysInfo:
            assert len(MetaInfoA[LookupKey]) == Count, (DonorId, LookupKey)
        for LookupKey in (
            "axis_directions",
            "swept_arc_counts",
            "inherited_directions",
        ):
            assert len(MetaInfoA[LookupKey]) <= Count, (DonorId, LookupKey)
        assert len(MetaInfoA["spare_plane_names"]) == len(
            MetaInfoA["spare_plane_ids"]
        ), DonorId
        assert len(MetaInfoA["spare_plane_frames"]) == len(
            MetaInfoA["spare_plane_ids"]
        ), DonorId
        assert len(set(MetaInfoA["spare_equations"])) == len(
            MetaInfoA["spare_equations"]
        ), DonorId


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEMFUTNTV() -> None:
    for DonorId in ManifestDonors():
        MetaInfoA = MetaInfo(DonorId)
        for Entry, DepthPresent in zip(
            MetaInfoA["features"], MetaInfoA["depth_present"], strict=True
        ):
            Topology = FeatureTopology(*Entry)
            assert list(Topology.key) == Entry, DonorId
            assert Topology.operation in KOperations, DonorId
            assert Topology.end_condition in KConditions, DonorId
            assert Topology.profile, DonorId
            if Topology.end_condition == EndInfo:
                assert Topology.support in Supports, DonorId
                assert DepthPresent is False, DonorId
