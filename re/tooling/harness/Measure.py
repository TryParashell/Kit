# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import json as JsonData
import pathlib as Pathlib
import subprocess as Subprocess
import sys as System
import time as TimeInfo
System.path.insert(0, str(Pathlib.Path(__file__).resolve().parent))
from Dismiss import StartRun as StartDismisser

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = Pathlib.Path(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = KHereInfo.parents[2]

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KRootInfo / '.rescratch' / 'sw' / 'out'

# needed to keep reverse engineering responsibilities isolated and maintainable
KRunner = KHereInfo / 'MeasureOne.py'

# needed to keep reverse engineering responsibilities isolated and maintainable
KControl = KRootInfo / '.rescratch' / 'corpus' / 'parts' / 'BASELINE_40x20x10.SLDPRT'

# needed to keep reverse engineering responsibilities isolated and maintainable
KTimeoutSeconds = 420.0

# needed to keep reverse engineering responsibilities isolated and maintainable
KMarker = '@@RESULT@@'

# needed to keep reverse engineering responsibilities isolated and maintainable
KComFailures = ('Server execution failed', 'The remote procedure call failed', 'cannot start SOLIDWORKS via COM', 'call was rejected by callee')

# needed to keep reverse engineering responsibilities isolated and maintainable
KProcesses = ('SLDEXITAPP.exe', 'SLDWORKS.exe', 'sldworks_util.exe', 'swMsgHandler.exe', 'SLDWORKS_Splash.exe', 'WerFault.exe')


# needed to keep reverse engineering responsibilities isolated and maintainable
def Sweep() -> None:
    for NameTextInfo in KProcesses:
        Subprocess.run(['taskkill', '/F', '/IM', NameTextInfo], capture_output=True, check=False)
    TimeInfo.sleep(12.0)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Attempt(Target: Pathlib.Path) -> dict:
    Sweep()
    Started = TimeInfo.monotonic()
    try:
        Completed = Subprocess.run([System.executable, str(KRunner), str(Target)], capture_output=True, text=True, timeout=KTimeoutSeconds, cwd=str(KRootInfo))
    except Subprocess.TimeoutExpired:
        Sweep()
        return {'path': str(Target), 'status': 'timeout', 'seconds': TimeInfo.monotonic() - Started}
    PayloadInfo: dict = {'path': str(Target), 'returncode': Completed.returncode, 'seconds': TimeInfo.monotonic() - Started}
    for LineText in Completed.stdout.splitlines():
        if LineText.startswith(KMarker):
            PayloadInfo.update(JsonData.loads(LineText[len(KMarker):]))
            PayloadInfo['status'] = 'solidworks-crashed-on-open' if PayloadInfo.get('open_exception') else 'measured'
            return PayloadInfo
    TailInfo = Completed.stderr[-4000:]
    PayloadInfo['stderr_tail'] = TailInfo
    if any((Marker in TailInfo for Marker in KComFailures)):
        PayloadInfo['status'] = 'session-unavailable'
    else:
        PayloadInfo['status'] = 'crashed' if Completed.returncode else 'no-result'
    return PayloadInfo

# needed to keep reverse engineering responsibilities isolated and maintainable
KRetryable = ('session-unavailable', 'solidworks-crashed-on-open', 'no-result')


# needed to keep reverse engineering responsibilities isolated and maintainable
def Measure(Target: Pathlib.Path, Retries: int=3) -> dict:
    Record = Attempt(Target)
    Tries = 1
    History = [Record['status']]
    while Record['status'] in KRetryable and Tries <= Retries:
        TimeInfo.sleep(20.0)
        Record = Attempt(Target)
        Tries += 1
        History.append(Record['status'])
    Record['attempts'] = Tries
    Record['history'] = History
    return Record


# needed to keep reverse engineering responsibilities isolated and maintainable
def Describe(Record: dict) -> None:
    print(f"{Pathlib.Path(Record['path']).stem:26s} status={Record['status']:26s} opened={Record.get('opened')} bodies={Record.get('body_count')} volume={Record.get('volume_mm3')} {Record['seconds']:.0f}s", flush=True)
    if Record.get('features'):
        print('    tree: ' + ', '.join((f"{ItemData['name']}[{ItemData['type']}]" for ItemData in Record['features'])), flush=True)
    if Record['status'] != 'measured':
        print(f"    detail: {str(Record.get('stderr_tail'))[-500:]}", flush=True)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    KOutInfo.mkdir(parents=True, exist_ok=True)
    StopInfo, Dismissed, Thread = StartDismisser()
    LabelInfo = System.argv[1]
    Targets = [Pathlib.Path(ItemData).resolve() for ItemData in System.argv[2:]]
    RecordsInfo: list[dict] = []
    ControlBefore = Measure(KControl)
    ControlBefore['role'] = 'control-before'
    RecordsInfo.append(ControlBefore)
    Describe(ControlBefore)
    for Target in Targets:
        Record = Measure(Target)
        Record['role'] = 'candidate'
        RecordsInfo.append(Record)
        Describe(Record)
    ControlAfter = Measure(KControl)
    ControlAfter['role'] = 'control-after'
    RecordsInfo.append(ControlAfter)
    Describe(ControlAfter)
    StopInfo.set()
    Destination = KOutInfo / f'measure_{LabelInfo}.json'
    Destination.write_text(JsonData.dumps(RecordsInfo, indent=2), encoding='utf-8')
    print(f'startup dialogs dismissed: {len(Dismissed)}')
    Sweep()
    Healthy = ControlBefore['status'] == 'measured' and ControlAfter['status'] == 'measured' and (ControlBefore.get('volume_mm3') == ControlAfter.get('volume_mm3'))
    print(f'\ncontrol healthy: {Healthy}')
    print(f'wrote {Destination}')
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRun())
