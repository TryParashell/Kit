from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from dismiss import start as start_dismisser

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / ".rescratch" / "sw" / "out"
RUNNER = HERE / "measure_one.py"
CONTROL = ROOT / ".rescratch" / "corpus" / "parts" / "BASELINE_40x20x10.SLDPRT"
TIMEOUT_SECONDS = 420.0
MARKER = "@@RESULT@@"

COM_FAILURES = (
    "Server execution failed",
    "The remote procedure call failed",
    "cannot start SOLIDWORKS via COM",
    "call was rejected by callee",
)

PROCESSES = (
    "SLDEXITAPP.exe",
    "SLDWORKS.exe",
    "sldworks_util.exe",
    "swMsgHandler.exe",
    "SLDWORKS_Splash.exe",
    "WerFault.exe",
)


def sweep() -> None:
    for name in PROCESSES:
        subprocess.run(
            ["taskkill", "/F", "/IM", name], capture_output=True, check=False
        )
    time.sleep(12.0)


def attempt(target: pathlib.Path) -> dict:
    sweep()
    started = time.monotonic()
    try:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), str(target)],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        sweep()
        return {
            "path": str(target),
            "status": "timeout",
            "seconds": time.monotonic() - started,
        }
    payload: dict = {
        "path": str(target),
        "returncode": completed.returncode,
        "seconds": time.monotonic() - started,
    }
    for line in completed.stdout.splitlines():
        if line.startswith(MARKER):
            payload.update(json.loads(line[len(MARKER) :]))
            payload["status"] = (
                "solidworks-crashed-on-open"
                if payload.get("open_exception")
                else "measured"
            )
            return payload
    tail = completed.stderr[-4000:]
    payload["stderr_tail"] = tail
    if any(marker in tail for marker in COM_FAILURES):
        payload["status"] = "session-unavailable"
    else:
        payload["status"] = "crashed" if completed.returncode else "no-result"
    return payload


RETRYABLE = ("session-unavailable", "solidworks-crashed-on-open", "no-result")


def measure(target: pathlib.Path, retries: int = 3) -> dict:
    record = attempt(target)
    tries = 1
    history = [record["status"]]
    while record["status"] in RETRYABLE and tries <= retries:
        time.sleep(20.0)
        record = attempt(target)
        tries += 1
        history.append(record["status"])
    record["attempts"] = tries
    record["history"] = history
    return record


def describe(record: dict) -> None:
    print(
        f"{pathlib.Path(record['path']).stem:26s} status={record['status']:26s} "
        f"opened={record.get('opened')} bodies={record.get('body_count')} "
        f"volume={record.get('volume_mm3')} {record['seconds']:.0f}s",
        flush=True,
    )
    if record.get("features"):
        print(
            "    tree: "
            + ", ".join(
                f"{item['name']}[{item['type']}]" for item in record["features"]
            ),
            flush=True,
        )
    if record["status"] != "measured":
        print(f"    detail: {str(record.get('stderr_tail'))[-500:]}", flush=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    stop, dismissed, _thread = start_dismisser()
    label = sys.argv[1]
    targets = [pathlib.Path(item).resolve() for item in sys.argv[2:]]
    records: list[dict] = []
    control_before = measure(CONTROL)
    control_before["role"] = "control-before"
    records.append(control_before)
    describe(control_before)
    for target in targets:
        record = measure(target)
        record["role"] = "candidate"
        records.append(record)
        describe(record)
    control_after = measure(CONTROL)
    control_after["role"] = "control-after"
    records.append(control_after)
    describe(control_after)
    stop.set()
    destination = OUT / f"measure_{label}.json"
    destination.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"startup dialogs dismissed: {len(dismissed)}")
    sweep()
    healthy = (
        control_before["status"] == "measured"
        and control_after["status"] == "measured"
        and control_before.get("volume_mm3") == control_after.get("volume_mm3")
    )
    print(f"\ncontrol healthy: {healthy}")
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
