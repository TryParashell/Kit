from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import cdbdrive
import tracelog

import streamlib

OUT = SCRATCH / "trace" / "out"

CONTROL = (SCRATCH / "corpus" / "parts" / "BASELINE_40x20x10.SLDPRT").resolve()

SCRIPT = """.symopt+0x4000
.symopt-0x20000
.exepath+ {solidworks}
.reload /f swccu.dll
r $t0 = 0
bp swccu!su_CArchive::ReadClass "r $t0 = @$t0+1; .printf \\"CALIB %d this=%p\\\\n\\", @$t0, @rcx; dq @rcx L18; .if (@$t0 >= {hits}) {{ bc * }}; g"
bl
g
"""

MIN_BUFFER = 256
MAX_BUFFER = 1 << 26


class CalibrationError(RuntimeError):
    __slots__ = ()


def write_script(path: Path, hits: int) -> None:
    path.write_text(
        SCRIPT.format(solidworks=cdbdrive.SOLIDWORKS_DIR, hits=hits), encoding="ascii"
    )


def group(dumps: tuple[tracelog.Dump, ...]) -> dict[int, list[tracelog.Dump]]:
    table: dict[int, list[tracelog.Dump]] = {}
    for dump in dumps:
        table.setdefault(dump.this, []).append(dump)
    return table


def _globally_ordered(
    dumps: tuple[tracelog.Dump, ...], key: tuple[int, int, int]
) -> bool:
    cursor, top, start = key
    for dump in dumps:
        base = dump.u64(start)
        if base == 0:
            continue
        if not base <= dump.u64(cursor) <= dump.u64(top):
            return False
    return True


def solve(dumps: tuple[tracelog.Dump, ...], expected: int) -> dict[str, int]:
    width = min(len(dump.raw) for dump in dumps)
    slots = range(0, width - 7, 8)
    votes: dict[tuple[int, int, int], int] = {}
    anchored: set[tuple[int, int, int]] = set()
    for series in group(dumps).values():
        if len(series) < 2:
            continue
        for start in slots:
            fixed_start = {dump.u64(start) for dump in series}
            if len(fixed_start) != 1:
                continue
            base = next(iter(fixed_start))
            if base == 0:
                continue
            for top in slots:
                if top == start:
                    continue
                fixed_top = {dump.u64(top) for dump in series}
                if len(fixed_top) != 1:
                    continue
                span = next(iter(fixed_top)) - base
                if not MIN_BUFFER <= span <= MAX_BUFFER:
                    continue
                for cursor in slots:
                    if cursor in (start, top):
                        continue
                    values = [dump.u64(cursor) for dump in series]
                    if len(set(values)) < 2:
                        continue
                    if any(left > right for left, right in zip(values, values[1:])):
                        continue
                    if any(value < base or value > base + span for value in values):
                        continue
                    key = (cursor, top, start)
                    votes[key] = votes.get(key, 0) + 1
                    if span == expected:
                        anchored.add(key)
    votes = {
        key: score for key, score in votes.items() if _globally_ordered(dumps, key)
    }
    if not votes:
        raise CalibrationError("no self-consistent buffer pointer triple was observed")
    pool = {key for key in anchored if key in votes} or set(votes)
    best = max(pool, key=lambda key: votes[key])
    cursor, top, start = best
    return {
        "cur": cursor,
        "max": top,
        "start": start,
        "map": start + 8,
        "votes": votes[best],
        "candidates": len(votes),
        "anchored_candidates": len(anchored),
        "anchor_span": expected,
    }


def verify(
    dumps: tuple[tracelog.Dump, ...], layout: dict[str, int]
) -> dict[str, object]:
    monotonic = 0
    breaks = 0
    for series in group(dumps).values():
        values = [dump.u32(layout["map"]) for dump in series]
        for left, right in zip(values, values[1:]):
            if right >= left:
                monotonic += 1
            else:
                breaks += 1
    return {"map_non_decreasing": monotonic, "map_decreases": breaks}


def main() -> int:
    hits = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    mode = sys.argv[2] if len(sys.argv) > 2 else "run"
    OUT.mkdir(parents=True, exist_ok=True)
    script = HERE / "CdbCalibrate.txt"
    log = OUT / "cdb_calibrate.log"
    write_script(script, hits)
    if mode == "run":
        result = cdbdrive.run(
            script,
            log,
            CONTROL,
            marker=r"^CALIB ",
            target_markers=hits,
            hard_deadline=420.0,
            quiet_seconds=40.0,
        )
        print(
            f"cdb finished reason={result.reason} CALIB={result.markers} "
            f"seconds={result.seconds:.1f}"
        )
    dumps = tracelog.read_dumps(log)
    print(f"dumps={len(dumps)} archives={len(group(dumps))}")
    expected = len(streamlib.load_donor(CONTROL).resolved)
    layout = solve(dumps, expected)
    checks = verify(dumps, layout)
    payload = {
        "log": str(log),
        "script": str(script),
        "dumps": len(dumps),
        "archives": len(group(dumps)),
        "layout": layout,
        "checks": checks,
    }
    (OUT / "Calibrate.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
