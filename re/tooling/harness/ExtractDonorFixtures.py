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
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "solidworks" / "donors"
MANIFEST_NAME = "manifest.json"
META_NAME = "meta.json"
RESOLVED_NAME = "resolved.bin"
CONTAINER_DIRECTORY = "container"
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


def sanitised_stream_name(name: str) -> str:
    return name.replace("/", "__")


def container_file_name(name: str) -> str:
    return f"{sanitised_stream_name(name)}.bin"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_record(
    path: Path, record: dict[str, object], expected_file: str
) -> tuple[int, list[str]]:
    failures: list[str] = []
    if record.get("file") != expected_file:
        failures.append(f"{path}: manifest names {record.get('file')!r}")
    if not path.is_file():
        failures.append(f"{path}: missing")
        return 0, failures
    payload = path.read_bytes()
    if record.get("length") != len(payload):
        failures.append(
            f"{path}: manifest length {record.get('length')} but {len(payload)} on disk"
        )
    actual = digest(payload)
    if record.get("sha256") != actual:
        failures.append(f"{path}: manifest sha256 {record.get('sha256')} but {actual}")
    return len(payload), failures


def verify_metadata(
    directory: Path, donor_id: str, container: dict[str, object]
) -> tuple[int, list[str]]:
    path = directory / META_NAME
    failures: list[str] = []
    if not path.is_file():
        return 0, [f"{path}: missing"]
    encoded = path.read_bytes()
    meta = read_json(path)
    if not isinstance(meta, dict):
        return len(encoded), [f"{path}: not an object"]
    if meta.get("donor_id") != donor_id:
        failures.append(f"{path}: describes {meta.get('donor_id')!r}")
    features = meta.get("features")
    if not isinstance(features, list) or not features:
        failures.append(f"{path}: lists no features")
    else:
        for key in PER_FEATURE_KEYS:
            value = meta.get(key)
            if not isinstance(value, list) or len(value) != len(features):
                failures.append(f"{path}: {key} does not hold one entry per feature")
    streams = meta.get("container_streams")
    if not isinstance(streams, list):
        failures.append(f"{path}: lists no container streams")
    else:
        named = {item["name"]: item["file"] for item in streams}
        if sorted(named) != sorted(container):
            failures.append(f"{path}: container stream names differ from the manifest")
        for name, file_name in named.items():
            if file_name != container_file_name(name):
                failures.append(f"{path}: stream {name} names {file_name!r}")
    return len(encoded), failures


def verify(fixture_root: Path) -> dict[str, object]:
    manifest_path = fixture_root / MANIFEST_NAME
    if not manifest_path.is_file():
        return {
            "fixture_root": str(fixture_root),
            "donor_count": 0,
            "failures": [f"{manifest_path}: missing"],
        }
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        return {
            "fixture_root": str(fixture_root),
            "donor_count": 0,
            "failures": [f"{manifest_path}: not an object"],
        }
    donors = manifest.get("donors")
    if not isinstance(donors, dict):
        return {
            "fixture_root": str(fixture_root),
            "donor_count": 0,
            "failures": [f"{manifest_path}: carries no donor index"],
        }
    failures: list[str] = []
    resolved_bytes = 0
    container_bytes = 0
    metadata_bytes = len(manifest_path.read_bytes())
    files = 1
    for donor_id in sorted(donors):
        record = donors[donor_id]
        directory = fixture_root / donor_id
        if not directory.is_dir():
            failures.append(f"{directory}: missing")
            continue
        length, problems = verify_record(
            directory / RESOLVED_NAME, record["resolved"], RESOLVED_NAME
        )
        resolved_bytes += length
        failures.extend(problems)
        files += 1
        container = record["container"]
        for name in sorted(container):
            expected = f"{CONTAINER_DIRECTORY}/{container_file_name(name)}"
            length, problems = verify_record(
                directory / CONTAINER_DIRECTORY / container_file_name(name),
                container[name],
                expected,
            )
            container_bytes += length
            failures.extend(problems)
            files += 1
        length, problems = verify_metadata(directory, donor_id, container)
        metadata_bytes += length
        failures.extend(problems)
        files += 1
    declared_resolved = manifest.get("resolved_bytes")
    if declared_resolved != resolved_bytes:
        failures.append(
            f"{manifest_path}: declares {declared_resolved} resolved bytes but "
            f"{resolved_bytes} are on disk"
        )
    declared_container = manifest.get("container_bytes")
    if declared_container != container_bytes:
        failures.append(
            f"{manifest_path}: declares {declared_container} container bytes but "
            f"{container_bytes} are on disk"
        )
    declared_count = manifest.get("donor_count")
    if declared_count != len(donors):
        failures.append(
            f"{manifest_path}: declares {declared_count} donors but indexes "
            f"{len(donors)}"
        )
    on_disk = sorted(path.name for path in fixture_root.iterdir() if path.is_dir())
    if on_disk != sorted(donors):
        failures.append(
            f"{fixture_root}: directories on disk differ from the manifest index"
        )
    return {
        "fixture_root": str(fixture_root),
        "donor_count": len(donors),
        "directories": len(on_disk),
        "files": files,
        "resolved_bytes": resolved_bytes,
        "container_bytes": container_bytes,
        "metadata_bytes": metadata_bytes,
        "total_bytes": resolved_bytes + container_bytes + metadata_bytes,
        "failures": failures,
    }


def main() -> int:
    summary = verify(FIXTURE_ROOT)
    sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return 1 if summary["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
