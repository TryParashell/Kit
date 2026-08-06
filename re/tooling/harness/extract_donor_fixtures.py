from __future__ import annotations

from collections.abc import Iterable, Mapping
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for candidate in (ROOT, ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from convert.adapters.solidworks.donor_library import DONOR_LIBRARY, Donor

FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "solidworks" / "donors"
MANIFEST_NAME = "manifest.json"
META_NAME = "meta.json"
RESOLVED_NAME = "resolved.bin"
CONTAINER_DIRECTORY = "container"


def sanitised_stream_name(name: str) -> str:
    return name.replace("/", "__")


def container_file_name(name: str) -> str:
    return f"{sanitised_stream_name(name)}.bin"


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def donor_metadata(donor: Donor, container: Mapping[str, bytes]) -> dict[str, object]:
    return {
        "donor_id": donor.donor_id,
        "features": [list(feature.key) for feature in donor.features],
        "feature_ids": list(donor.feature_ids),
        "sketch_ids": list(donor.sketch_ids),
        "feature_names": list(donor.feature_names),
        "sketch_names": list(donor.sketch_names),
        "point_counts": list(donor.point_counts),
        "arc_counts": list(donor.arc_counts),
        "depth_present": list(donor.depth_present),
        "stream_bytes": donor.stream_bytes,
        "measured": donor.measured,
        "axis_directions": [
            None if direction is None else list(direction)
            for direction in donor.axis_directions
        ],
        "swept_arc_counts": list(donor.swept_arc_counts),
        "inherited_directions": list(donor.inherited_directions),
        "spare_plane_ids": list(donor.spare_plane_ids),
        "spare_plane_names": list(donor.spare_plane_names),
        "spare_plane_frames": list(donor.spare_plane_frames),
        "spare_equations": list(donor.spare_equations),
        "container_streams": [
            {"name": name, "file": container_file_name(name)}
            for name in sorted(container)
        ],
    }


def write_bytes(path: Path, payload: bytes) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return len(payload)


def write_json(path: Path, payload: object) -> int:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return write_bytes(path, encoded)


def prune(fixture_root: Path, keep: Iterable[Path]) -> list[Path]:
    retained = set(keep)
    removed: list[Path] = []
    for path in sorted(fixture_root.rglob("*")):
        if path.is_file() and path not in retained:
            path.unlink()
            removed.append(path)
    for path in sorted(fixture_root.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return removed


def extract(fixture_root: Path) -> dict[str, object]:
    written: set[Path] = set()
    donors: dict[str, object] = {}
    resolved_bytes = 0
    container_bytes = 0
    metadata_bytes = 0
    for donor in DONOR_LIBRARY:
        if donor.donor_id in donors:
            raise ValueError(f"donor {donor.donor_id} appears twice in DONOR_LIBRARY")
        directory = fixture_root / donor.donor_id
        resolved = donor.stream
        resolved_path = directory / RESOLVED_NAME
        resolved_bytes += write_bytes(resolved_path, resolved)
        written.add(resolved_path)
        container = donor.container
        container_index: dict[str, object] = {}
        for name in sorted(container):
            blob = container[name]
            stream_path = directory / CONTAINER_DIRECTORY / container_file_name(name)
            container_bytes += write_bytes(stream_path, blob)
            written.add(stream_path)
            container_index[name] = {
                "file": f"{CONTAINER_DIRECTORY}/{container_file_name(name)}",
                "sha256": digest(blob),
                "length": len(blob),
            }
        meta_path = directory / META_NAME
        metadata_bytes += write_json(meta_path, donor_metadata(donor, container))
        written.add(meta_path)
        donors[donor.donor_id] = {
            "resolved": {
                "file": RESOLVED_NAME,
                "sha256": digest(resolved),
                "length": len(resolved),
            },
            "container": container_index,
        }
    manifest_path = fixture_root / MANIFEST_NAME
    manifest = {
        "donor_count": len(donors),
        "resolved_bytes": resolved_bytes,
        "container_bytes": container_bytes,
        "donors": donors,
    }
    manifest_bytes = write_json(manifest_path, manifest)
    written.add(manifest_path)
    removed = prune(fixture_root, written)
    return {
        "directories": len(DONOR_LIBRARY),
        "files": len(written),
        "resolved_bytes": resolved_bytes,
        "container_bytes": container_bytes,
        "metadata_bytes": metadata_bytes + manifest_bytes,
        "total_bytes": resolved_bytes + container_bytes + metadata_bytes
        + manifest_bytes,
        "removed": [str(path.relative_to(fixture_root)) for path in removed],
    }


def main() -> int:
    summary = extract(FIXTURE_ROOT)
    sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
