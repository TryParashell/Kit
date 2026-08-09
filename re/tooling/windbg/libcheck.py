# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRATCH = ROOT / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

PARTS = SCRATCH / "donors" / "parts"
FIXTURES = ROOT / "tests" / "fixtures" / "solidworks" / "donors"
MANIFEST = FIXTURES / "manifest.json"
RESOLVED_NAME = "resolved.bin"
CONTAINER_DIRECTORY = "container"


def container_file_name(name: str) -> str:
    return f"{name.replace('/', '__')}.bin"


def main() -> int:
    if not MANIFEST.is_file():
        print(f"missing fixture manifest {MANIFEST}")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    donors = manifest["donors"]
    mismatches = 0
    missing = 0
    for donor_id in sorted(donors):
        directory = FIXTURES / donor_id
        part = PARTS / f"{donor_id}.SLDPRT"
        if not part.is_file():
            print(f"{donor_id:38s} no authored part on disk")
            missing += 1
            continue
        real = streamlib.load_donor(part)
        resolved = (directory / RESOLVED_NAME).read_bytes()
        rows = [f"{donor_id:38s}"]
        state = "same" if resolved == real.resolved else "DIFFERS"
        if state != "same":
            mismatches += 1
        rows.append(f"resolved={state}")
        for name in sorted(donors[donor_id]["container"]):
            path = directory / CONTAINER_DIRECTORY / container_file_name(name)
            expected = path.read_bytes() if path.is_file() else None
            actual = real.streams.get(name)
            state = "same" if expected is not None and expected == actual else "DIFFERS"
            if state != "same":
                mismatches += 1
            rows.append(f"{name.split('/')[-1]}={state}")
        print(" ".join(rows))
    print(
        f"fixtures={len(donors)} parts_missing={missing} stream_mismatches={mismatches}"
    )
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
