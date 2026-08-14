from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

TARGETS = (
    "Contents/Config-0-ResolvedFeatures",
    "Contents/CMgr",
    "Contents/Config-0-ModelHeader",
    "Header2",
    "Contents/Config-0",
    "ThirdPtyStore/VisualStates",
)


def main() -> int:
    for item in sys.argv[1:]:
        part = Path(item).resolve()
        donor = streamlib.load_donor(part)
        features = len(streamlib.comp_feature_entries(donor.resolved)) // 2
        sizes = {name: len(donor.streams[name]) for name in donor.streams}
        collisions = {
            name: sorted(
                other
                for other, length in sizes.items()
                if length == sizes[name] and other != name
            )
            for name in TARGETS
            if name in sizes
        }
        print(f"{part.stem} features={features}")
        for name in TARGETS:
            if name not in sizes:
                print(f"    {name:38s} absent")
                continue
            print(
                f"    {name:38s} {sizes[name]:7d} 0x{sizes[name]:x} "
                f"collides={collisions[name]}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
