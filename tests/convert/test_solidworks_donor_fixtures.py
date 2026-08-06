# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from convert.adapters.solidworks.topology import (
    BOSS_OPERATION,
    CUT_OPERATION,
    FeatureTopology,
    FULL_REVOLUTION_END,
    REVOLVE_BOSS_OPERATION,
    REVOLVE_CUT_OPERATION,
    REVOLVE_SUPPORTS,
    SUPPORTED_END_CONDITIONS,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "solidworks" / "donors"
)
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"
RESOLVED_NAME = "resolved.bin"
META_NAME = "meta.json"
CONTAINER_DIRECTORY = "container"
EXPECTED_DONOR_COUNT = 32
KNOWN_OPERATIONS = frozenset(
    {BOSS_OPERATION, CUT_OPERATION, REVOLVE_BOSS_OPERATION, REVOLVE_CUT_OPERATION}
)
KNOWN_END_CONDITIONS = SUPPORTED_END_CONDITIONS | {FULL_REVOLUTION_END}
PER_FEATURE_KEYS = (
    "features",
    "feature_ids",
    "sketch_ids",
    "feature_names",
    "sketch_names",
    "point_counts",
    "arc_counts",
    "depth_present",
)


def _manifest() -> dict[str, object]:
    assert MANIFEST_PATH.is_file(), f"missing donor fixture manifest {MANIFEST_PATH}"
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _manifest_donors() -> dict[str, dict[str, object]]:
    donors = _manifest()["donors"]
    assert isinstance(donors, dict)
    return donors


def _container_file_name(name: str) -> str:
    return f"{name.replace('/', '__')}.bin"


def _meta(donor_id: str) -> dict[str, object]:
    path = FIXTURE_ROOT / donor_id / META_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_manifest_donor_has_a_fixture_directory() -> None:
    for donor_id in _manifest_donors():
        directory = FIXTURE_ROOT / donor_id
        assert directory.is_dir(), f"missing fixture directory for {donor_id}"
        assert (directory / RESOLVED_NAME).is_file(), donor_id
        assert (directory / META_NAME).is_file(), donor_id


def test_the_manifest_lists_exactly_the_committed_fixture_directories() -> None:
    donors = _manifest_donors()
    assert len(donors) == EXPECTED_DONOR_COUNT
    assert _manifest()["donor_count"] == EXPECTED_DONOR_COUNT
    on_disk = sorted(path.name for path in FIXTURE_ROOT.iterdir() if path.is_dir())
    assert sorted(donors) == on_disk


def test_every_resolved_fixture_matches_its_manifest_digest() -> None:
    for donor_id, record in _manifest_donors().items():
        resolved = record["resolved"]
        payload = (FIXTURE_ROOT / donor_id / RESOLVED_NAME).read_bytes()
        assert resolved["length"] == len(payload), donor_id
        assert resolved["sha256"] == hashlib.sha256(payload).hexdigest(), donor_id
        assert resolved["file"] == RESOLVED_NAME, donor_id


def test_the_manifest_totals_the_committed_fixture_bytes() -> None:
    donors = _manifest_donors()
    resolved_bytes = sum(
        len((FIXTURE_ROOT / donor_id / RESOLVED_NAME).read_bytes())
        for donor_id in donors
    )
    container_bytes = 0
    for donor_id, record in donors.items():
        for name in record["container"]:
            path = FIXTURE_ROOT / donor_id / CONTAINER_DIRECTORY
            container_bytes += len((path / _container_file_name(name)).read_bytes())
    assert _manifest()["resolved_bytes"] == resolved_bytes
    assert _manifest()["container_bytes"] == container_bytes


def test_every_container_fixture_matches_its_manifest_digest() -> None:
    for donor_id, record in _manifest_donors().items():
        index = record["container"]
        assert index, donor_id
        for name, entry in index.items():
            path = FIXTURE_ROOT / donor_id / CONTAINER_DIRECTORY
            path = path / _container_file_name(name)
            payload = path.read_bytes()
            assert entry["length"] == len(payload), (donor_id, name)
            assert entry["sha256"] == hashlib.sha256(payload).hexdigest(), (
                donor_id,
                name,
            )
            assert entry["file"] == f"{CONTAINER_DIRECTORY}/{path.name}", (
                donor_id,
                name,
            )


def test_every_meta_file_agrees_with_the_manifest_and_its_streams() -> None:
    for donor_id, record in _manifest_donors().items():
        meta = _meta(donor_id)
        assert meta["donor_id"] == donor_id
        assert meta["stream_bytes"] == record["resolved"]["length"]
        assert isinstance(meta["measured"], bool)
        streams = {item["name"]: item["file"] for item in meta["container_streams"]}
        assert sorted(streams) == sorted(record["container"])
        for name, file_name in streams.items():
            assert file_name == _container_file_name(name), donor_id


def test_every_meta_file_describes_one_entry_per_feature() -> None:
    for donor_id in _manifest_donors():
        meta = _meta(donor_id)
        count = len(meta["features"])
        assert count >= 1, donor_id
        for key in PER_FEATURE_KEYS:
            assert len(meta[key]) == count, (donor_id, key)
        for key in ("axis_directions", "swept_arc_counts", "inherited_directions"):
            assert len(meta[key]) <= count, (donor_id, key)
        assert len(meta["spare_plane_names"]) == len(meta["spare_plane_ids"]), donor_id
        assert len(meta["spare_plane_frames"]) == len(meta["spare_plane_ids"]), donor_id
        assert len(set(meta["spare_equations"])) == len(
            meta["spare_equations"]
        ), donor_id


def test_every_meta_feature_uses_the_native_topology_vocabulary() -> None:
    for donor_id in _manifest_donors():
        meta = _meta(donor_id)
        for entry, depth_present in zip(
            meta["features"], meta["depth_present"], strict=True
        ):
            topology = FeatureTopology(*entry)
            assert list(topology.key) == entry, donor_id
            assert topology.operation in KNOWN_OPERATIONS, donor_id
            assert topology.end_condition in KNOWN_END_CONDITIONS, donor_id
            assert topology.profile, donor_id
            if topology.end_condition == FULL_REVOLUTION_END:
                assert topology.support in REVOLVE_SUPPORTS, donor_id
                assert depth_present is False, donor_id
