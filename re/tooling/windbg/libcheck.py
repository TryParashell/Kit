from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

from convert.adapters.solidworks import donor_library

PARTS = SCRATCH / "donors" / "parts"


def main() -> int:
    for donor in donor_library.DONOR_LIBRARY:
        part = PARTS / f"{donor.donor_id}.SLDPRT"
        if not part.is_file():
            print(f"{donor.donor_id:30s} no authored part")
            continue
        real = streamlib.load_donor(part)
        rows = [f"{donor.donor_id:30s} features={len(donor.features)}"]
        rows.append(
            f"resolved={'same' if donor.stream == real.resolved else 'DIFFERS'}"
        )
        container = donor.container
        for name in sorted(container):
            actual = real.streams.get(name)
            state = "same" if actual == container[name] else "DIFFERS"
            rows.append(f"{name.split('/')[-1]}={state}")
        print(" ".join(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
