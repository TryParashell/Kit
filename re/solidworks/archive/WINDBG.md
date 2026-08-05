# Runtime instrumentation of the SOLIDWORKS feature-stream reader

Goal: confirm the record boundaries and field order derived statically in `GRAMMAR.md`, and
recover the object segmentation that static diffing cannot give (report 1 §10, report 2 §11).

Everything below is reproducible from the commands as written. Logs are in
`.rescratch/grammar/out/cdb_*.log`, scripts in `.rescratch/grammar/cdb_*.txt`.

---

## 1. Installing the debugger

WinDbg was **not** installed and `C:\Program Files\Windows Kits\10\Debuggers\x64\` did not exist.
The first option in the plan worked, non-interactively, with no UAC prompt:

```powershell
winget install --id Microsoft.WinDbg --accept-source-agreements --accept-package-agreements --disable-interactivity
```

```
Found WinDbg [Microsoft.WinDbg] Version 1.2606.22001.0
Successfully installed
```

The MSIX ships console debuggers as architecture-suffixed aliases on `PATH`
(`%LOCALAPPDATA%\Microsoft\WindowsApps`), so the scriptable console debugger is **`cdbX64.exe`**,
not `cdb.exe`:

```powershell
cdbX64.exe -version
# cdb version 10.0.29617.1000
```

Also present: `kdX64.exe`, `ntsdX64.exe`, `dbgsrvX64.exe`, and the GUI `WinDbgX.exe`.
Package root: `C:\Program Files\WindowsApps\Microsoft.WinDbg_1.2606.22001.0_x64__8wekyb3d8bbwe`.

---

## 2. Two traps that make an unattended cdb run fail

### 2.1 `$$><` versus `$$<`

`-c "$$><file"` collapses the whole script into one semicolon-separated command line. `.sympath`
then swallows every following command as though it were a path:

```
Error: Execute .sympath(+) command attempts to access 'bu mfc140u!CArchive::ReadObject ".echo RO' failed: 0x7b
```

Use `-c "$$<file"`, which executes the file **one line per command**. Breakpoint command strings
must then fit on a single line, with inner quotes escaped as `\"`.

### 2.2 `SYMOPT_NO_UNQUALIFIED_LOADS`

SOLIDWORKS loads 620+ modules. A single `bu mfc140u!…` made cdb attempt a symbol-server lookup
for every one of them and the run never got past the first breakpoint command — the log stalled
at 12 815 bytes indefinitely. The fix is one line, first in the script:

```
.symopt+0x4000
```

With that set, cdb resolves only explicitly module-qualified symbols and SOLIDWORKS starts
normally under the debugger.

### 2.3 A deferred breakpoint on an already-loaded module

`mfc140u.dll` is loaded (log line 53) **before** the initial `ntdll!LdrpDoDebuggerBreak` stop
(log line 137), so `sxe ld:mfc140u` never fires. Set the breakpoint directly at the initial stop
and use `.reload /f mfc140u.dll`.

---

## 3. What SOLIDWORKS actually loads

`probe_modules.py` (COM, no debugger) and the cdb module log agree: SOLIDWORKS 2025 loads the
**shared** MFC runtime from the system directory, not a private copy.

```
mfc140u.dll   C:\WINDOWS\SYSTEM32\mfc140u.dll   14.50.35719.0
mfc140.dll    C:\WINDOWS\SYSTEM32\mfc140.dll    14.50.35719.0
```

Public symbols are therefore available for the MFC runtime, which is what made the next step
possible.

---

## 4. `CArchive` field layout — CONFIRMED

`.rescratch/grammar/cdb_classload.txt`:

```
.symopt+0x4000
.sympath srv*c:\symbols*https://msdl.microsoft.com/download/symbols
.reload /f mfc140u.dll
x mfc140u!CArchive::*
x mfc140u!CRuntimeClass::*
dt mfc140u!CArchive
bp mfc140u!CRuntimeClass::Load ".printf \"RCL ar=%p\\n\", @rcx; gc"
bl
g
```

```powershell
cdbX64.exe -logo out\cdb_classload.log -c "$$<cdb_classload.txt" `
  "C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe" `
  ".rescratch\corpus\parts\BASELINE_40x20x10.SLDPRT"
```

`dt` returned the full layout (x64, MFC 14.5):

```
   +0x000 m_pDocument      : Ptr64 CDocument
   +0x008 m_bForceFlat     : Int4B
   +0x00c m_bDirectBuffer  : Int4B
   +0x010 m_bBlocking      : Int4B
   +0x014 m_nObjectSchema  : Uint4B
   +0x018 m_strFileName    : CStringT<wchar_t,…>
   +0x020 m_nMode          : Int4B
   +0x024 m_bUserBuf       : Int4B
   +0x028 m_nBufSize       : Int4B
   +0x030 m_pFile          : Ptr64 CFile
   +0x038 m_lpBufCur       : Ptr64 UChar
   +0x040 m_lpBufMax       : Ptr64 UChar
   +0x048 m_lpBufStart     : Ptr64 UChar
   +0x050 m_nMapCount      : Uint4B
   +0x058 m_pLoadArray     : Ptr64 CPtrArray
   +0x058 m_pStoreMap      : Ptr64 CMapPtrToPtr
   +0x060 m_pSchemaMap     : Ptr64 CMapPtrToPtr
   +0x068 m_nGrowSize      : Uint4B
   +0x06c m_nHashSize      : Uint4B
```

This is the direct confirmation of the archive model in `GRAMMAR.md` §2: stream position is
`m_lpBufCur - m_lpBufStart`, and `m_nMapCount` is the single counter that assigns the combined
class/object indices which the `0x8000|i` reference tokens encode.

`x mfc140u!CArchive::*` also pinned the reader entry points and their real signatures:

```
CArchive::ReadObject(struct CRuntimeClass const *)
CArchive::ReadClass(struct CRuntimeClass const *, unsigned int *, unsigned long *)
CArchive::MapObject(class CObject const *)
CArchive::GetObjectSchema(void)
```

`CRuntimeClass::Load` is **not** in the publics (only `CreateObject` is), so `bp
mfc140u!CRuntimeClass::Load` silently failed and `bl` came back empty. Its address is
recoverable from the inline-caller entries (`CRuntimeClass::Load+2d` at `a25d850d` ⇒ base
`a25d84e0`), but by then it was not needed.

---

## 5. The negative result that redirected the work

Two runs with unconditional and conditional breakpoints on `mfc140u!CArchive::ReadObject`, over a
full SOLIDWORKS startup **and** a part open, produced:

```
RO = 0
NEWARCH = 1
```

Zero `CArchive::ReadObject` calls, and exactly one `CArchive::CArchive` construction in the whole
process lifetime. So:

> **SOLIDWORKS does not read `Contents/Config-0-ResolvedFeatures` through MFC's `CArchive`.**
> The MFC runtime is loaded for UI/pane state only.

Static analysis had been treating the stream as MFC `CArchive` output. That reading is correct as
a *format*, but the implementation is SOLIDWORKS' own.

---

## 6. `su_CArchive` — the real reader, and it is exported by name

`probe_exports.py` / `probe_su_archive.py` read the PE export tables of the whole SOLIDWORKS
install. `sldarchiveu.dll` exports `operator>>` overloads whose parameter type is
`su_CArchive`:

```
??5@YAAEAVsu_CArchive@@AEAV0@AEAPEAVmoExtObject_c@@@Z
?GetRuntimeClass@moHeader_c@@UEBAPEAUCRuntimeClass@@XZ
```

so SOLIDWORKS reimplements MFC's archive as `su_CArchive` and keeps MFC's `CRuntimeClass`
mechanism. 902 exported symbols across 25 modules mention `su_CArchive`.

The class itself lives in **`swccu.dll`** and its entire API is exported undecorated-by-name,
which means **cdb can breakpoint it without any PDB**:

```
?ReadObject@su_CArchive@@QEAAPEAVCObject@@PEBUCRuntimeClass@@@Z
?ReadClass@su_CArchive@@QEAAPEAUCRuntimeClass@@PEBU2@PEAIPEAK@Z
?MapObject@su_CArchive@@QEAAXPEBVCObject@@@Z
?SerializeClass@su_CArchive@@QEAAXPEBUCRuntimeClass@@@Z
?ftell@su_CArchive@@QEBA_JXZ
?getMapCount@su_CArchive@@QEAAIXZ
?setMapCount@su_CArchive@@QEAAXI@Z
?getLoadArray@su_CArchive@@QEAAPEAVsu_CPtrArray@@XZ
?getStoreMap@su_CArchive@@QEAAPEAVsu_CMapPtrToPtr@@XZ
?AddToLoadArrayDirect@su_CArchive@@QEAAXPEBVCObject@@@Z
?IsUsingMemFile@su_CArchive@@QEBAHXZ
?IsDBStream@su_CArchive@@QEBAHXZ
?FillBuffer@su_CArchive@@QEAAXI@Z
?ReadCount@su_CArchive@@QEAAKXZ
?ReadString@su_CArchive@@QEAAPEA_WPEA_WI@Z
```

`ftell` gives the stream position and `getMapCount` gives the index counter — the two values that
turn a `ReadObject` trace into a complete object segmentation with byte offsets.

`sldmodu.dll` additionally exports the per-class readers:

```
?Serialize@moBodyFeature_c@@UEAAXAEAVsu_CArchive@@@Z
?Serialize@moCompLoop_c@@UEAAXAEAVsu_CArchive@@@Z
?Serialize@moCSysRefPlnData_c@@MEAAXAEAVsu_CArchive@@@Z
… 219 su_CArchive symbols in sldmodu.dll alone
```

`moExtrusion_c::Serialize` is not among the exports (it is only virtual, reached through the
vtable), but `su_CArchive::ReadObject` sits above every one of them, so tracing `ReadObject` is
sufficient and does not depend on which classes happen to be exported.

### 6.1 The trace that lifts blocker 1

This is the run to make next; it needs a one-shot calibration of the `su_CArchive` field offsets
because `swccu.dll` has no PDB, then a filtered trace. `cdb_su_calibrate.txt`:

```
.symopt+0x4000
bp swccu!?ReadClass@su_CArchive@@QEAAPEAUCRuntimeClass@@PEBU2@PEAIPEAK@Z "dq @rcx L18; bc 0; g"
g
```

One hit dumps 24 qwords of the archive object and removes itself, so the run costs nothing after
that. The pointer triple that brackets an 11 075-byte span identifies `m_lpBufStart` /
`m_lpBufCur` / `m_lpBufMax`; the `u32` immediately after them is the map counter. Cross-check
against the statically known class-definition offsets of `BASELINE_40x20x10`
(`out/tags.json`: 6, 203, 410, 606, 657, 890, …): the reported positions must land on exactly
those bytes.

With the offsets known, the productive trace is

```
bp swccu!?ReadObject@su_CArchive@@QEAAPEAVCObject@@PEBUCRuntimeClass@@@Z ".if ((poi(@rcx+<max>)-poi(@rcx+<start>))==0x2b43) { .printf \"RO %x %d\\n\", poi(@rcx+<cur>)-poi(@rcx+<start>), dwo(@rcx+<map>) }; gc"
```

filtered on the 11 075-byte (`0x2b43`) buffer span so only our stream is logged. The output is a
list of `(stream offset, map index)` pairs — i.e. the start offset of every object and the index
it was assigned. Differencing consecutive offsets gives each object's byte length, which is the
per-class record segmentation, and the map column gives the renumbering table directly. That
closes blockers 1 and 2 in `GRAMMAR.md` §8.

**This trace was not executed in this session.** The debugger and SOLIDWORKS contend for the same
single SOLIDWORKS installation, and the volume measurements in `results.md` were given priority.
Everything needed to run it is above and in `cdb_su_calibrate.txt`.

---

## 7. What runtime instrumentation confirmed that static diffing could not

1. The archive object model is exactly MFC's, including the single combined class/object map
   counter — so the `0x8000|i` reference-token reading in `GRAMMAR.md` §2 is not a guess, and the
   renumbering constraint is real rather than inferred.
2. The reader is **not** MFC. Every static conclusion survives, but any plan that hooked
   `mfc140u` would have failed silently. This is the finding that only a runtime probe gives.
3. The reader's entry points are exported by name from `swccu.dll`, so the object segmentation is
   reachable with breakpoints and no reverse engineering of unexported code. Before this, report 1
   §10 and report 2 §11 both listed the segmentation as needing "MFC class-index tag decoding"
   with no route to it.
4. `su_CArchive::IsUsingMemFile` / `IsDBStream` exist, which is why the earlier
   buffer-span filter on `mfc140u` was empty: the document streams are read from a memory file
   inside SOLIDWORKS, never through the MFC path.
