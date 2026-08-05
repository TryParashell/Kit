from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import threading
import time

CDB = Path(r"C:\Users\odin\AppData\Local\Microsoft\WindowsApps\cdbX64.exe")
SLDWORKS = Path(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe")
SOLIDWORKS_DIR = SLDWORKS.parent

PROCESSES = (
    "cdbX64.exe",
    "SLDWORKS.exe",
    "sldworks_util.exe",
    "swMsgHandler.exe",
    "SLDWORKS_Splash.exe",
    "SLDEXITAPP.exe",
    "WerFault.exe",
)

DIALOG_CLASS = "#32770"
BUTTONS = ("OK", "&OK", "Yes", "&Yes")


@dataclass(frozen=True, slots=True)
class RunResult:
    log: Path
    seconds: float
    markers: int
    reason: str


def sweep(settle: float = 4.0) -> None:
    for name in PROCESSES:
        subprocess.run(
            ["taskkill", "/F", "/IM", name], capture_output=True, check=False
        )
    time.sleep(settle)


def _watch_dialogs(stop: threading.Event) -> None:
    import ctypes
    import ctypes.wintypes as wintypes

    user32 = ctypes.windll.user32
    prototype = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def class_name(handle: int) -> str:
        buffer = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(handle, buffer, 256)
        return buffer.value

    def window_text(handle: int) -> str:
        length = user32.GetWindowTextLengthW(handle)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(handle, buffer, length + 1)
        return buffer.value

    def press(dialog: int) -> None:
        buttons: list[int] = []

        def child(handle: int, _: int) -> bool:
            if class_name(handle) == "Button" and window_text(handle) in BUTTONS:
                buttons.append(handle)
            return True

        user32.EnumChildWindows(dialog, prototype(child), 0)
        for handle in buttons[:1]:
            user32.SendMessageW(handle, 0x00F5, 0, 0)

    while not stop.is_set():
        dialogs: list[int] = []

        def top(handle: int, _: int) -> bool:
            if class_name(handle) == DIALOG_CLASS and user32.IsWindowVisible(handle):
                dialogs.append(handle)
            return True

        try:
            user32.EnumWindows(prototype(top), 0)
            for dialog in dialogs:
                press(dialog)
        except OSError:
            pass
        stop.wait(0.75)


def run(
    script: Path,
    log: Path,
    part: Path | None,
    *,
    marker: str,
    target_markers: int = 0,
    hard_deadline: float = 600.0,
    quiet_seconds: float = 45.0,
) -> RunResult:
    sweep()
    log.parent.mkdir(parents=True, exist_ok=True)
    if log.exists():
        log.unlink()
    command = [str(CDB), "-logo", str(log), "-c", f"$$<{script.name}", str(SLDWORKS)]
    if part is not None:
        command.append(str(part.resolve()))
    stop = threading.Event()
    watcher = threading.Thread(target=_watch_dialogs, args=(stop,), daemon=True)
    watcher.start()
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=str(script.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    pattern = re.compile(marker, re.MULTILINE)
    count = 0
    last_change = time.monotonic()
    reason = "deadline"
    try:
        while True:
            time.sleep(2.0)
            text = log.read_text(errors="replace") if log.exists() else ""
            found = len(pattern.findall(text))
            if found != count:
                count = found
                last_change = time.monotonic()
            if process.poll() is not None:
                reason = "cdb-exited"
                break
            if target_markers and count >= target_markers:
                reason = "target-markers"
                break
            if count and time.monotonic() - last_change >= quiet_seconds:
                reason = "quiet"
                break
            if time.monotonic() - started >= hard_deadline:
                reason = "deadline"
                break
    finally:
        stop.set()
        try:
            process.terminate()
        except OSError:
            pass
        time.sleep(1.0)
        sweep()
    return RunResult(
        log=log,
        seconds=time.monotonic() - started,
        markers=count,
        reason=reason,
    )
