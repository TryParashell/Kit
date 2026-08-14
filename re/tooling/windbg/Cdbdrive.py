# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import contextlib as Contextlib
from dataclasses import dataclass as DataClass
from pathlib import Path as PathInfo
import re as Regex
import subprocess as Subprocess
import threading as Threading
import time as TimeInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLegacyAttr(SelfRef, NameText):
    AliasName = SelfRef.KAliasNames.get(NameText)
    if AliasName is None:
        raise AttributeError(NameText)
    return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetLegacyMut(SelfRef, NameText, ValueData):
    TargetName = SelfRef.KAliasNames.get(NameText, NameText)
    object.__setattr__(SelfRef, TargetName, ValueData)

# needed to keep reverse engineering responsibilities isolated and maintainable
KCdbInfo = PathInfo('C:\\Users\\odin\\AppData\\Local\\Microsoft\\WindowsApps\\cdbX64.exe')

# needed to keep reverse engineering responsibilities isolated and maintainable
KSldworks = PathInfo('C:\\Program Files\\SOLIDWORKS Corp\\SOLIDWORKS\\SLDWORKS.exe')

# needed to keep reverse engineering responsibilities isolated and maintainable
KSolidworksDir = KSldworks.parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KProcesses = ('cdb.exe', 'cdbX64.exe', 'SLDWORKS.exe', 'sldworks_util.exe', 'swMsgHandler.exe', 'SLDWORKS_Splash.exe', 'SLDEXITAPP.exe', 'WerFault.exe')

# needed to keep reverse engineering responsibilities isolated and maintainable
KDialogClass = '#32770'

# needed to keep reverse engineering responsibilities isolated and maintainable
KButtons = ('OK', '&OK', 'Yes', '&Yes')


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class RunResult:
    LogInfo: PathInfo
    Seconds: float
    Markers: int
    Reason: str
    KAliasNames = {'log': 'LogInfo', 'seconds': 'Seconds', 'markers': 'Markers', 'reason': 'Reason'}

# needed to keep reverse engineering responsibilities isolated and maintainable
RunResult.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def Sweep(Settle: float=4.0) -> None:
    for NameTextInfo in KProcesses:
        Subprocess.run(['taskkill', '/F', '/IM', NameTextInfo], capture_output=True, check=False)
    TimeInfo.sleep(Settle)


# needed to keep reverse engineering responsibilities isolated and maintainable
def WatchDialogs(StopInfo: Threading.Event) -> None:
    import ctypes as Ctypes
    import ctypes.wintypes as Wintypes
    UserThirtyTwo = Ctypes.windll.user32
    Prototype = Ctypes.WINFUNCTYPE(Ctypes.c_bool, Wintypes.HWND, Wintypes.LPARAM)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def ClassNameData(Handle: int) -> str:
        Buffer = Ctypes.create_unicode_buffer(256)
        UserThirtyTwo.GetClassNameW(Handle, Buffer, 256)
        return Buffer.value


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def WindowTextInfo(Handle: int) -> str:
        Length = UserThirtyTwo.GetWindowTextLengthW(Handle)
        Buffer = Ctypes.create_unicode_buffer(Length + 1)
        UserThirtyTwo.GetWindowTextW(Handle, Buffer, Length + 1)
        return Buffer.value


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Press(Dialog: int) -> None:
        Buttons: list[int] = []


        # needed to keep reverse engineering responsibilities isolated and maintainable
        def IsChild(Handle: int, SpareValue: int) -> bool:
            if ClassNameData(Handle) == 'Button' and WindowTextInfo(Handle) in KButtons:
                Buttons.append(Handle)
            return True
        UserThirtyTwo.EnumChildWindows(Dialog, Prototype(IsChild), 0)
        for Handle in Buttons[:1]:
            UserThirtyTwo.SendMessageW(Handle, 245, 0, 0)
    while not StopInfo.is_set():
        Dialogs: list[int] = []


        # needed to keep reverse engineering responsibilities isolated and maintainable
        def IsTopInfo(Handle: int, SpareValue: int) -> bool:
            if ClassNameData(Handle) == KDialogClass and UserThirtyTwo.IsWindowVisible(Handle):
                Dialogs.append(Handle)
            return True
        with Contextlib.suppress(OSError):
            UserThirtyTwo.EnumWindows(Prototype(IsTopInfo), 0)
            for Dialog in Dialogs:
                Press(Dialog)
        StopInfo.wait(0.75)


# needed to keep reverse engineering responsibilities isolated and maintainable
def RunTask(Script: PathInfo, LogInfo: PathInfo, PartInfoInfo: PathInfo | None, *, Marker: str, TargetMarkers: int=0, HardDeadline: float=600.0, QuietSeconds: float=45.0) -> RunResult:
    Sweep()
    LogInfo.parent.mkdir(parents=True, exist_ok=True)
    if LogInfo.exists():
        LogInfo.unlink()
    Command = [str(KCdbInfo), '-logo', str(LogInfo), '-c', f'$$<{Script.name}', str(KSldworks)]
    if PartInfoInfo is not None:
        Command.append(str(PartInfoInfo.resolve()))
    StopInfo = Threading.Event()
    WatcherMut = Threading.Thread(target=WatchDialogs, args=(StopInfo,), daemon=True)
    WatcherMut.start()
    Started = TimeInfo.monotonic()
    Process = Subprocess.Popen(Command, cwd=str(Script.parent), stdout=Subprocess.DEVNULL, stderr=Subprocess.DEVNULL, stdin=Subprocess.DEVNULL)
    Pattern = Regex.compile(Marker, Regex.MULTILINE)
    CountInfo = 0
    LastChange = TimeInfo.monotonic()
    Reason = 'deadline'
    try:
        while True:
            TimeInfo.sleep(2.0)
            TextValueData = LogInfo.read_text(errors='replace') if LogInfo.exists() else ''
            Found = len(Pattern.findall(TextValueData))
            if Found != CountInfo:
                CountInfo = Found
                LastChange = TimeInfo.monotonic()
            if Process.poll() is not None:
                Reason = 'cdb-exited'
                break
            if TargetMarkers and CountInfo >= TargetMarkers:
                Reason = 'target-markers'
                break
            if CountInfo and TimeInfo.monotonic() - LastChange >= QuietSeconds:
                Reason = 'quiet'
                break
            if TimeInfo.monotonic() - Started >= HardDeadline:
                Reason = 'deadline'
                break
    finally:
        StopInfo.set()
        with Contextlib.suppress(OSError):
            Process.terminate()
        TimeInfo.sleep(1.0)
        Sweep()
    return RunResult(LogInfo=LogInfo, Seconds=TimeInfo.monotonic() - Started, Markers=CountInfo, Reason=Reason)
