from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

EVENT = re.compile(
    r"^(RO|RC) ([0-9a-fA-F`]+) ([0-9a-fA-F]+) (\d+) ([0-9a-fA-F`]+)"
    r"(?: ([0-9a-fA-F`]+))?\s*$"
)
CALIB = re.compile(r"^CALIB (\d+) this=([0-9a-fA-F`]+)\s*$")
DUMP = re.compile(r"^([0-9a-fA-F`]+)\s+((?:[0-9a-fA-F`]{17}\s*)+)$")
QWORD = re.compile(r"([0-9a-fA-F]{8})`([0-9a-fA-F]{8})")


@dataclass(frozen=True, slots=True)
class Event:
    kind: str
    buffer: int
    offset: int
    counter: int
    rsp: int
    span: int = 0


@dataclass(frozen=True, slots=True)
class Dump:
    index: int
    this: int
    words: tuple[int, ...]

    def u64(self, offset: int) -> int:
        return int.from_bytes(self.raw[offset : offset + 8], "little")

    def u32(self, offset: int) -> int:
        return int.from_bytes(self.raw[offset : offset + 4], "little")

    @property
    def raw(self) -> bytes:
        out = bytearray()
        for word in self.words:
            out += word.to_bytes(8, "little")
        return bytes(out)


def _hexint(text: str) -> int:
    return int(text.replace("`", ""), 16)


def read_events(log: Path) -> tuple[Event, ...]:
    result: list[Event] = []
    for raw in log.read_text(errors="replace").splitlines():
        match = EVENT.match(raw.strip())
        if match is None:
            continue
        result.append(
            Event(
                kind=match.group(1),
                buffer=_hexint(match.group(2)),
                offset=int(match.group(3), 16),
                counter=int(match.group(4)),
                rsp=_hexint(match.group(5)),
                span=_hexint(match.group(6)) if match.group(6) else 0,
            )
        )
    return tuple(result)


def buffers_for_span(events: tuple[Event, ...], span: int) -> dict[int, int]:
    counts: dict[int, int] = {}
    for event in events:
        if event.kind != "RO" or event.span != span:
            continue
        counts[event.buffer] = counts.get(event.buffer, 0) + 1
    return counts


def busiest_buffer(events: tuple[Event, ...], span: int) -> int:
    counts = buffers_for_span(events, span)
    if not counts:
        raise ValueError(f"no ReadObject events for span {span}")
    return max(counts, key=lambda key: counts[key])


def read_dumps(log: Path) -> tuple[Dump, ...]:
    result: list[Dump] = []
    index = 0
    this = 0
    words: list[int] = []
    active = False
    for raw in log.read_text(errors="replace").splitlines():
        line = raw.strip()
        head = CALIB.match(line)
        if head is not None:
            if active:
                result.append(Dump(index, this, tuple(words)))
            index = int(head.group(1))
            this = _hexint(head.group(2))
            words = []
            active = True
            continue
        if not active:
            continue
        row = DUMP.match(line)
        if row is None:
            continue
        for high, low in QWORD.findall(row.group(2)):
            words.append(int(high + low, 16))
    if active:
        result.append(Dump(index, this, tuple(words)))
    return tuple(result)


def dominant_buffer(events: tuple[Event, ...]) -> int:
    counts: dict[int, int] = {}
    for event in events:
        counts[event.buffer] = counts.get(event.buffer, 0) + 1
    if not counts:
        raise ValueError("no trace events in log")
    return max(counts, key=lambda key: counts[key])
