# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import ctypes as Ctypes
import ctypes.wintypes as Wintypes
import threading as Threading
import time as TimeInfo

# needed to keep reverse engineering responsibilities isolated and maintainable
KUserThirtyTwo = Ctypes.windll.user32

# needed to keep reverse engineering responsibilities isolated and maintainable
KCallback = Ctypes.WINFUNCTYPE(Ctypes.c_bool, Wintypes.HWND, Wintypes.LPARAM)

# needed to keep reverse engineering responsibilities isolated and maintainable
KBmClick = 245

# needed to keep reverse engineering responsibilities isolated and maintainable
KDialogClass = "#32770"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDialogTitle = "SOLIDWORKS"

# needed to keep reverse engineering responsibilities isolated and maintainable
KButtonLabels = ("OK", "&OK")


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassNameInfo(Handle: int) -> str:
    Buffer = Ctypes.create_unicode_buffer(256)
    KUserThirtyTwo.GetClassNameW(Handle, Buffer, 256)
    return Buffer.value


# needed to keep reverse engineering responsibilities isolated and maintainable
def WindowText(Handle: int) -> str:
    Length = KUserThirtyTwo.GetWindowTextLengthW(Handle)
    Buffer = Ctypes.create_unicode_buffer(Length + 1)
    KUserThirtyTwo.GetWindowTextW(Handle, Buffer, Length + 1)
    return Buffer.value


# needed to keep reverse engineering responsibilities isolated and maintainable
def StartupDialogs() -> list[int]:
    Found: list[int] = []

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def IsVisit(Handle: int, SpareValue: int) -> bool:
        if (
            ClassNameInfo(Handle) == KDialogClass
            and KUserThirtyTwo.IsWindowVisible(Handle)
            and (WindowText(Handle) == KDialogTitle)
        ):
            Found.append(Handle)
        return True

    KUserThirtyTwo.EnumWindows(KCallback(IsVisit), 0)
    return Found


# needed to keep reverse engineering responsibilities isolated and maintainable
def ConfirmButton(Dialog: int) -> int | None:
    Found: list[int] = []

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def IsVisit(Handle: int, SpareValue: int) -> bool:
        if ClassNameInfo(Handle) == "Button" and WindowText(Handle) in KButtonLabels:
            Found.append(Handle)
        return True

    KUserThirtyTwo.EnumChildWindows(Dialog, KCallback(IsVisit), 0)
    return Found[0] if Found else None


# needed to keep reverse engineering responsibilities isolated and maintainable
def DismissOnce() -> list[str]:
    Dismissed: list[str] = []
    for Dialog in StartupDialogs():
        Button = ConfirmButton(Dialog)
        if Button is None:
            continue
        KUserThirtyTwo.SendMessageW(Button, KBmClick, 0, 0)
        Dismissed.append(f"hwnd={Dialog}")
    return Dismissed


# needed to keep reverse engineering responsibilities isolated and maintainable
def WatcherMut(StopInfo: Threading.Event, LogInfo: list[str]) -> None:
    while not StopInfo.is_set():
        try:
            for ItemData in DismissOnce():
                LogInfo.append(ItemData)
        except Exception:
            pass
        StopInfo.wait(0.5)


# needed to keep reverse engineering responsibilities isolated and maintainable
def StartRun() -> tuple[Threading.Event, list[str], Threading.Thread]:
    StopInfo = Threading.Event()
    LogInfo: list[str] = []
    ThreadInfo = Threading.Thread(
        target=WatcherMut, args=(StopInfo, LogInfo), daemon=True
    )
    ThreadInfo.start()
    return (StopInfo, LogInfo, ThreadInfo)


if __name__ == "__main__":

    # needed to keep reverse engineering responsibilities isolated and maintainable
    KDeadline = TimeInfo.monotonic() + 120.0
    while TimeInfo.monotonic() < KDeadline:
        for ItemData in DismissOnce():
            print(f"dismissed {ItemData}", flush=True)
        TimeInfo.sleep(0.5)
