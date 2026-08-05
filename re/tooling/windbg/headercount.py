from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

MODEL_HEADER = "Contents/Config-0-ModelHeader"
HEADER2 = "Header2"
CMGR = "Contents/CMgr"
NODE_COUNT_OFFSET = 77
CMGR_COUNT_OFFSET = 1414
BASE_NODES = 24


@dataclass(frozen=True, slots=True)
class Field:
    stream: str
    offset: int
    width: int
    label: str

    def read(self, blob: bytes) -> int:
        return int.from_bytes(blob[self.offset : self.offset + self.width], "little")

    def write(self, blob: bytes, value: int) -> bytes:
        output = bytearray(blob)
        output[self.offset : self.offset + self.width] = value.to_bytes(
            self.width, "little"
        )
        return bytes(output)

    def expected(self, features: int) -> int:
        if self.label == "24+2n":
            return BASE_NODES + 2 * features
        if self.label == "n":
            return features
        raise KeyError(self.label)


FIELDS = (
    Field(MODEL_HEADER, NODE_COUNT_OFFSET, 2, "24+2n"),
    Field(HEADER2, NODE_COUNT_OFFSET, 2, "24+2n"),
    Field(CMGR, CMGR_COUNT_OFFSET, 2, "n"),
)

GROUPS = {
    "header": (FIELDS[0], FIELDS[1]),
    "cmgr": (FIELDS[2],),
    "all": FIELDS,
    "none": (),
}


def node_count(blob: bytes) -> int:
    return FIELDS[0].read(blob)


def patch(blob: bytes, value: int) -> bytes:
    return FIELDS[0].write(blob, value)


def patched_streams(
    donor: streamlib.Donor, features: int, group: str
) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for field in GROUPS[group]:
        source = result.get(field.stream, donor.streams[field.stream])
        result[field.stream] = field.write(source, field.expected(features))
    return result


def main() -> int:
    for item in sys.argv[1:]:
        part = Path(item).resolve()
        donor = streamlib.load_donor(part)
        features = len(streamlib.comp_feature_entries(donor.resolved)) // 2
        row = [f"{part.stem:30s} features={features}"]
        for field in FIELDS:
            blob = donor.streams[field.stream]
            row.append(
                f"{field.stream.split('/')[-1]}[{field.offset}]={field.read(blob)}"
                f"/{field.expected(features)}"
            )
        print(" ".join(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
