<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Ghidra setup and headless analysis — reproducible

Everything below runs on the machine as configured, with no SOLIDWORKS process, no COM and no
debugger. Only the DLL bytes on disk are read.

## 1. JDK

JDK 21 was already installed and is not on `PATH`, so every command sets `JAVA_HOME` explicitly:

```powershell
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot"
& 'C:\Program Files\Microsoft\jdk-21.0.12.8-hotspot\bin\java.exe' -version
# openjdk version "21.0.12" 2026-07-21 LTS
```

## 2. Ghidra

`winget install --id Ghidra.Ghidra` was not used. The official release zip was already present in
this directory from an earlier session and is expanded in place:

```
.rescratch/ghidra/ghidra_12.1.2_PUBLIC_20260605.zip   572803866 bytes
.rescratch/ghidra/ghidra_12.1.2_PUBLIC/               expanded distribution
```

To reproduce from nothing:

```powershell
$url = "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_12.1.2_build/ghidra_12.1.2_PUBLIC_20260605.zip"
Invoke-WebRequest -Uri $url -OutFile .rescratch\ghidra\ghidra_12.1.2_PUBLIC_20260605.zip
Get-FileHash .rescratch\ghidra\ghidra_12.1.2_PUBLIC_20260605.zip -Algorithm SHA256
Expand-Archive .rescratch\ghidra\ghidra_12.1.2_PUBLIC_20260605.zip -DestinationPath .rescratch\ghidra
```

## 3. The one non-obvious obstacle: Ghidra rejects dot-directories

`analyzeHeadless` validates the project path and throws

```
java.lang.IllegalArgumentException: Path element starting with '.' is not permitted
```

for any path containing a component that begins with `.`, which rules out `.rescratch` directly.
The fix is a directory junction so Ghidra sees a dot-free path while the files physically live
inside `.rescratch/ghidra`:

```powershell
cmd /c mklink /J "C:\Users\odin\kitgh" "C:\Users\odin\Documents\Parashell\Kit\.rescratch\ghidra"
```

Every Ghidra invocation below uses `C:\Users\odin\kitgh\...`. Nothing is stored outside
`.rescratch/ghidra`.

## 4. DLL copies

The targets are copied out of `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS` into
`.rescratch/ghidra/bin/` and analysed there. Reading and copying is all that happens; nothing is
executed.

| file              | bytes    |
| ----------------- | -------- |
| `swccu.dll`       | 251776   |
| `sldarchiveu.dll` | 229760   |
| `sldmodu.dll`     | 45877632 |
| `sldmfcu.dll`     | 8094592  |

## 5. Import and analyse

Three projects, one per workload, so they do not contend for the project lock:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\odin\kitgh\RunImportSwccu.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\odin\kitgh\RunImportSldmodu.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\odin\kitgh\RunImportSldmfcu.ps1
```

Each script is a thin wrapper around

```
ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat <projectDir> <projectName>
    -import <dll> -scriptPath <scripts> -analysisTimeoutPerFile <seconds>
```

with `GHIDRA_HEADLESS_MAXMEM` raised (6G for the small DLLs, 12G for `sldmodu.dll`). The project
directory must already exist; `analyzeHeadless` does not create it.

## 6. Extract

Decompilation is driven by scripts, never the GUI:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\odin\kitgh\RunDumpSwccu.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\odin\kitgh\RunDumpSldmodu.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\odin\kitgh\RunDumpSldmfcu.ps1
```

These re-open the saved project with `-process <file> -noanalysis` and run, in order:

1. `RenameArchiveApi.java` — renames every `su_CArchive::operator>>` / `operator<<` overload and
   every import thunk to `AR_get_<type>` / `AR_put_<type>` using the demangled parameter type, so
   the decompiled call sites are unambiguous about field width. Without this every overload prints
   as `operator>>` and a `double` read is indistinguishable from a `char` read.
2. `DumpVtableSlot.java` — dumps every RTTI-named `vftable` with its first 40 slots.
3. `DumpFunctions.java` — decompiles every function named by a spec file, expanding callees to a
   requested depth, and writes the C to `out/`.

Spec files accept either `0x<address>` or a function-name substring per line.

## 7. Timings, measured

| workload                                               | wall time           | note                                  |
| ------------------------------------------------------ | ------------------- | ------------------------------------- |
| `swccu.dll` + `sldarchiveu.dll` import + full analysis | **92 s**            | one project, two programs             |
| `sldmfcu.dll` import + full analysis                   | **329 s**           |                                       |
| `sldmodu.dll` import + full analysis                   | **3022 s** (50 min) | 45.9 MB, `GHIDRA_HEADLESS_MAXMEM=12G` |
| `swccu` extract (111 functions)                        | ~40 s               |                                       |
| `sldmodu` rename + 9395 vftables + 436 functions       | ~150 s              |                                       |
| `sldmodu` accessor extract (325 functions)             | ~100 s              |                                       |
| `sldmfcu` data-reference extract                       | ~60 s               |                                       |

All four analyses reported `Analysis succeeded` / `Import succeeded` and exit code 0.

## 8. Exact run list, in order

```powershell
# analysis, once per DLL
powershell -File C:\Users\odin\kitgh\RunImportSwccu.ps1
powershell -File C:\Users\odin\kitgh\RunImportSldmodu.ps1
powershell -File C:\Users\odin\kitgh\RunImportSldmfcu.ps1

# extraction
powershell -File C:\Users\odin\kitgh\RunDumpSwccu.ps1        # out\swccu_archive.c, out\sldarchiveu_ops.c
powershell -File C:\Users\odin\kitgh\RunDumpSldmodu.ps1      # out\sldmodu_vtslots.txt, out\sldmodu_serialize.c
powershell -File C:\Users\odin\kitgh\RunDumpAccessors.ps1    # out\sldmodu_accessors.c
powershell -File C:\Users\odin\kitgh\RunDumpAccessorsTwo.ps1   # out\sldmodu_accessors2.c
powershell -File C:\Users\odin\kitgh\RunDumpAccessorsThree.ps1   # out\sldmodu_accessors3.c
powershell -File C:\Users\odin\kitgh\RunDumpSldmfcu.ps1      # out\SldmfcuSigtableRefs.txt
```

Each `run_dump_*.ps1` names a spec file; regenerate `SpecSldmodu.txt` from the class list with
`uv run python .rescratch\ghidra\MakeSpec.py`, and get any further class's `Serialize` address from
`out\SerializeMap.json` (built by `SerializeMap.py` from `out\sldmodu_vtslots.txt`).

## 9. Analysis and cross-check scripts

Run from anywhere; they resolve paths from the repository root.

| script                                                                                  | what it does                                                                                                                                     |
| --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `SerializeMap.py`                                                                       | vtable slot 5 → per-class `Serialize` address, for 2607 RTTI-named classes                                                                       |
| `MakeSpec.py`                                                                           | turns the classes observed in the traced streams into a `DumpFunctions` spec                                                                     |
| `Exports.py`                                                                            | PE export table: mangled name → RVA → virtual address (needed when Ghidra folded a getter under another class's name)                            |
| `Pemap.py`                                                                              | PE sections; file offset → RVA → virtual address                                                                                                 |
| `Vtab.py`                                                                               | queries a vtable dump by class or by slot                                                                                                        |
| `Getfn.py`                                                                              | pulls one function out of a `DumpFunctions` output                                                                                               |
| `Offsets.py`                                                                            | summarises the `this + off` accesses of each dumped accessor                                                                                     |
| `Layout.py`                                                                             | loads a `segments_*.json` plus the real stream bytes and produces, per object, the exact interleaving of nested object reads and own scalar runs |
| `Compare.py`, `Bytediff.py`, `Threeway.py`, `Classdiff.py`, `SegSpans.py`, `Segtree.py` | shape and byte comparisons of one class across parts                                                                                             |
| **`VerifyLayout.py`**                                                                   | walks a declared field table against the traced spans; fails if any scalar gap is not exactly filled. Also decodes the shared tail run.          |
| **`ScanEndspec.py`**                                                                    | decodes the first `moEndSpec_c` of every corpus/example part statically                                                                          |
| **`ScanRevendspec.py`**                                                                 | same for `moRevEndSpec_c`                                                                                                                        |
| **`Sigtable.py`**                                                                       | extracts the 1000-entry `file_id` → signature table from `sldmfcu.dll` and checks it against every real part                                     |
| `ScanConsts.py`                                                                         | locates the signature constants across every SOLIDWORKS module                                                                                   |
| `Findtable.py`                                                                          | derives the table geometry from the constants by entropy bounds                                                                                  |
| `Dumpbytes.py`, `Kwdump.py`                                                             | hex window into a DLL; `swXmlContents/KeyWords` dump                                                                                             |

All are `black`-clean and comment-free; `black --check .rescratch\ghidra\*.py` exits 0.

## 10. Ghidra scripts

| script                                                | purpose                                                                                                                                         |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/RenameArchiveApi.java`                       | renames every `su_CArchive::operator>>` / `<<` overload and import thunk to `AR_get_<type>` / `AR_put_<type>` from the demangled parameter type |
| `scripts/DumpFunctions.java`                          | decompiles every function named by a spec file (`0x<addr>` or name substring), expanding callees to a given depth                               |
| `scripts/DumpVtableSlot.java`                         | dumps every RTTI-named `vftable` with its first N slots                                                                                         |
| `scripts/DumpRefs.java`                               | lists every reference into an address range and decompiles the referencing functions                                                            |
| `scripts/DumpDecomp.java`, `scripts/DumpVtables.java` | the earlier session's pattern-matching dumpers, kept because `out/sldmodu.c` and `out/sldmodu_vtables.txt` came from them                       |
