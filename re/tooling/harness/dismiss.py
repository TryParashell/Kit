from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import threading
import time

USER32 = ctypes.windll.user32
CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
BM_CLICK = 0x00F5
DIALOG_CLASS = "#32770"
DIALOG_TITLE = "SOLIDWORKS"
BUTTON_LABELS = ("OK", "&OK")


def _class_name(handle: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    USER32.GetClassNameW(handle, buffer, 256)
    return buffer.value


def _window_text(handle: int) -> str:
    length = USER32.GetWindowTextLengthW(handle)
    buffer = ctypes.create_unicode_buffer(length + 1)
    USER32.GetWindowTextW(handle, buffer, length + 1)
    return buffer.value


def _startup_dialogs() -> list[int]:
    found: list[int] = []

    def visit(handle: int, _: int) -> bool:
        if (
            _class_name(handle) == DIALOG_CLASS
            and USER32.IsWindowVisible(handle)
            and _window_text(handle) == DIALOG_TITLE
        ):
            found.append(handle)
        return True

    USER32.EnumWindows(CALLBACK(visit), 0)
    return found


def _confirm_button(dialog: int) -> int | None:
    found: list[int] = []

    def visit(handle: int, _: int) -> bool:
        if _class_name(handle) == "Button" and _window_text(handle) in BUTTON_LABELS:
            found.append(handle)
        return True

    USER32.EnumChildWindows(dialog, CALLBACK(visit), 0)
    return found[0] if found else None


def dismiss_once() -> list[str]:
    dismissed: list[str] = []
    for dialog in _startup_dialogs():
        button = _confirm_button(dialog)
        if button is None:
            continue
        USER32.SendMessageW(button, BM_CLICK, 0, 0)
        dismissed.append(f"hwnd={dialog}")
    return dismissed


def watcher(stop: threading.Event, log: list[str]) -> None:
    while not stop.is_set():
        try:
            for item in dismiss_once():
                log.append(item)
        except Exception:
            pass
        stop.wait(0.5)


def start() -> tuple[threading.Event, list[str], threading.Thread]:
    stop = threading.Event()
    log: list[str] = []
    thread = threading.Thread(target=watcher, args=(stop, log), daemon=True)
    thread.start()
    return stop, log, thread


if __name__ == "__main__":
    deadline = time.monotonic() + 120.0
    while time.monotonic() < deadline:
        for item in dismiss_once():
            print(f"dismissed {item}", flush=True)
        time.sleep(0.5)
