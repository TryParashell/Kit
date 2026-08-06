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

from convert.adapters.solidworks.donor_library import DONOR_LIBRARY

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[1] / "fixtures" / "solidworks" / "donors"
)
MANIFEST_PATH = FIXTURE_ROOT / "manifest.json"
RESOLVED_NAME = "resolved.bin"
META_NAME = "meta.json"
CONTAINER_DIRECTORY = "container"
EXPECTED_DONOR_COUNT = 32


def _manifest() -> dict[str, object]:
    assert MANIFEST_PATH.is_file(), f"missing donor fixture manifest {MANIFEST_PATH}"
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _manifest_donors() -> dict[str, dict[str, object]]:
    donors = _manifest()["donors"]
    assert isinstance(donors, dict)
    return donors


def _container_file_name(name: str) -> str:
    return f"{name.replace('/', '__')}.bin"


def test_every_donor_has_a_fixture_directory() -> None:
    for donor in DONOR_LIBRARY:
        directory = FIXTURE_ROOT / donor.donor_id
        assert directory.is_dir(), f"missing fixture directory for {donor.donor_id}"
        assert (directory / RESOLVED_NAME).is_file(), donor.donor_id
        assert (directory / META_NAME).is_file(), donor.donor_id


def test_the_manifest_lists_exactly_the_library_donor_ids() -> None:
    donors = _manifest_donors()
    assert len(donors) == EXPECTED_DONOR_COUNT
    assert sorted(donors) == sorted(donor.donor_id for donor in DONOR_LIBRARY)
    assert _manifest()["donor_count"] == EXPECTED_DONOR_COUNT


def test_every_resolved_fixture_matches_its_manifest_digest() -> None:
    donors = _manifest_donors()
    for donor in DONOR_LIBRARY:
        record = donors[donor.donor_id]["resolved"]
        payload = (FIXTURE_ROOT / donor.donor_id / RESOLVED_NAME).read_bytes()
        assert record["length"] == len(payload), donor.donor_id
        assert record["sha256"] == hashlib.sha256(payload).hexdigest(), donor.donor_id
        assert record["file"] == RESOLVED_NAME, donor.donor_id


def test_every_resolved_fixture_is_byte_identical_to_the_donor_stream() -> None:
    total = 0
    for donor in DONOR_LIBRARY:
        payload = (FIXTURE_ROOT / donor.donor_id / RESOLVED_NAME).read_bytes()
        assert payload == donor.stream, donor.donor_id
        assert len(payload) == donor.stream_bytes, donor.donor_id
        total += len(payload)
    assert total == sum(donor.stream_bytes for donor in DONOR_LIBRARY)


def test_every_container_fixture_is_byte_identical_to_the_donor_container() -> None:
    donors = _manifest_donors()
    for donor in DONOR_LIBRARY:
        container = donor.container
        index = donors[donor.donor_id]["container"]
        assert sorted(index) == sorted(container), donor.donor_id
        for name, blob in container.items():
            record = index[name]
            path = FIXTURE_ROOT / donor.donor_id / CONTAINER_DIRECTORY
            path = path / _container_file_name(name)
            payload = path.read_bytes()
            assert payload == blob, (donor.donor_id, name)
            assert record["length"] == len(blob), (donor.donor_id, name)
            assert record["sha256"] == hashlib.sha256(blob).hexdigest(), (
                donor.donor_id,
                name,
            )
            assert record["file"] == f"{CONTAINER_DIRECTORY}/{path.name}", (
                donor.donor_id,
                name,
            )


def test_every_meta_file_round_trips_the_donor_description() -> None:
    for donor in DONOR_LIBRARY:
        meta = json.loads(
            (FIXTURE_ROOT / donor.donor_id / META_NAME).read_text(encoding="utf-8")
        )
        assert meta["donor_id"] == donor.donor_id
        assert meta["stream_bytes"] == donor.stream_bytes
        assert meta["measured"] is donor.measured
        assert meta["features"] == [list(item.key) for item in donor.features]
        assert meta["feature_ids"] == list(donor.feature_ids)
        assert meta["sketch_ids"] == list(donor.sketch_ids)
        assert meta["feature_names"] == list(donor.feature_names)
        assert meta["sketch_names"] == list(donor.sketch_names)
        assert meta["point_counts"] == list(donor.point_counts)
        assert meta["arc_counts"] == list(donor.arc_counts)
        assert meta["depth_present"] == list(donor.depth_present)
        assert meta["swept_arc_counts"] == list(donor.swept_arc_counts)
        assert meta["inherited_directions"] == list(donor.inherited_directions)
        assert meta["spare_plane_ids"] == list(donor.spare_plane_ids)
        assert meta["spare_plane_names"] == list(donor.spare_plane_names)
        assert meta["spare_plane_frames"] == list(donor.spare_plane_frames)
        assert meta["spare_equations"] == list(donor.spare_equations)
        assert meta["axis_directions"] == [
            None if direction is None else list(direction)
            for direction in donor.axis_directions
        ]
        streams = {item["name"]: item["file"] for item in meta["container_streams"]}
        assert sorted(streams) == sorted(donor.container)
        for name, file_name in streams.items():
            assert file_name == _container_file_name(name), donor.donor_id
