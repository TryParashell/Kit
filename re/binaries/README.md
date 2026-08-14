<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# The four SOLIDWORKS binaries every finding in `re/solidworks/` was derived from

## The binaries in this directory are tracked — read this first

The four `.dll` files here are **committed to the repository**, deliberately, so that an agent or
machine with no SOLIDWORKS install can run Ghidra against the exact bytes every finding came from.
That is a real convenience and it has a real cost:

- They are **unmodified proprietary Dassault Systèmes binaries** taken from a licensed local
  install. Committing them is redistribution of vendor code, and the SOLIDWORKS licence agreement
  governs whether that is permitted — including to other people inside Parashell. This repository is
  marked internal-use-only (`LICENSE`, PolyForm Strict; `README.md`, "Internal use only"), which
  limits but does not by itself resolve the question.
- They add **~52.6 MB** to the repository, against ~6.9 MB for everything else in `re/`.

**If you would rather not carry them,** nothing in `re/` depends on their presence except re-running
the decompilation. Delete them, add `*.dll` to a `.gitignore` in this directory, and use `Fetch.ps1`
to reproduce them byte for byte from a local install:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File re\binaries\Fetch.ps1
```

`Manifest.json` records the byte size, SHA-256 and PE file version of each, so a fetched copy is
verifiable against the one these findings were derived from.

Everything else here — the manifest, the fetch script, the offsets in `re/solidworks/`, the
extracted tables in `re/data/` — is our own work.

## Getting the binaries

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File re\binaries\Fetch.ps1
```

Copies all four out of the install named in `Manifest.json` (`install_root`), then checks byte
size, SHA-256 and the PE file version of each. Exit code 0 means all four match.

| flag                  | effect                                                                 |
| --------------------- | ---------------------------------------------------------------------- |
| `-InstallRoot <path>` | copy from a different install location                                 |
| `-VerifyOnly`         | skip the copy, just check what is already on disk against the manifest |

A version mismatch is not a script failure, it is a real warning: every address, file offset and
`this`-relative field offset recorded in `re/solidworks/` was read out of **SOLIDWORKS 2025,
`33.5.0.0053`**. Against a different release the addresses move and have to be re-derived. The
grammar-level facts (token shapes, map-counter rule, field _order_) have held across `_MO_VERSION`
generations 11000, 13000, 14000 and 18000; the absolute addresses have not been checked on any
other build.

## What each one is, and why it matters

| file              | bytes      | role                                                                                                                                                                                                                                                                                                                                                                        |
| ----------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `swccu.dll`       | 251 776    | Implements **`su_CArchive`** — the archive class SOLIDWORKS actually reads with. `su_CArchive::ReadObject` `0x31eda570`, `su_CArchive::ReadClass` `0x31eda2f0`. Both, and `MapObject`/`ftell`/`getMapCount`/`setMapCount`/`ReadCount`/`ReadString`, are exported **undecorated by name**, which is the single fact that makes the whole runtime trace possible with no PDB. |
| `sldarchiveu.dll` | 229 760    | Exports the `su_CArchive::operator>>` overloads. `RenameArchiveApi.java` renames each to `AR_get_<type>` before decompiling; without that pass every overload prints as `operator>>` and a `double` read is indistinguishable from a `char` read.                                                                                                                           |
| `sldmodu.dll`     | 45 877 632 | 219 exported per-class `Serialize` symbols, 9395 RTTI vftables, and the 2607-class vtable-slot-5 map extracted to `re/data/Serialization/SerializeMap.json`. Every `mo*` and `sg*` field layout in `re/solidworks/records/` came out of this file.                                                                                                                          |
| `sldmfcu.dll`     | 8 094 592  | Holds the **1000-entry `file_id` -> signature-triplet lookup table** in `.rdata`. Extracted to `re/data/Serialization/SignatureTable.json`; see `re/solidworks/container/README.md`.                                                                                                                                                                                        |

## SOLIDWORKS does not use MFC's `CArchive`

Worth stating here because it decides which binary you attack. A full instrumented startup plus
part open recorded **0** `CArchive::ReadObject` calls and **1** `CArchive::CArchive` construction.
The reader is `su_CArchive` in `swccu.dll`. Any plan that hooks `mfc140u.dll` fails silently.

What MFC _is_ good for is the struct layout: `dt mfc140u!CArchive` on x64 MFC 14.5 gives
`m_lpBufCur +0x38`, `m_lpBufMax +0x40`, `m_lpBufStart +0x48`, `m_nMapCount +0x50`, and those
offsets were then confirmed against `su_CArchive` instances at runtime with `candidates: 1`.
`su_CArchive` is layout-compatible with `CArchive` even though it is not `CArchive`.

## Not in this directory

The Ghidra 12.1.2 distribution (3.4 GB) and its release zip (573 MB) are not migrated. The zip is a
public download; `re/tooling/ghidra/Setup.md` has the URL, the exact filename, its byte size and
the expand command.
