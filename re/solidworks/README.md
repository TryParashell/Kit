<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# The SOLIDWORKS story: what was cracked, what was not

SOLIDWORKS 2025 (`33.5.0.0053`), `.SLDPRT` / `.SLDASM`. Everything here was derived from a licensed
local install by three methods, in this order of increasing certainty: static differencing of a
corpus, headless decompilation of the vendor DLLs, and a runtime trace of the actual reader with a
measured rebuild volume as the acceptance test.

Confidence words are the ones defined in `records/SERIALIZE.md`: **confirmed** = decompiled _and_
cross-checked against real bytes / a traced span / a measured volume; **partial** = decompiled but
not exercised by any available file; **not found**.

## The headline

A `.SLDPRT` is a zip-like container of named streams. The container framing and the load-critical
streams used by Kit's supported feature families are fully constructive: the writer emits typed
fields and does not copy, embed, patch, or read a vendor stream. Eighteen resolved-feature programs
currently reconstruct their declared lengths with zero opaque bytes. The format is not fully
inverted for arbitrary modeling histories; unsupported FCStd documents fail closed. The exact
repository-wide boundary is measured in `CORPUS_COVERAGE.md`.

| layer                                                                  | status                                                                                                                                                                   |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| container: header, file id, three signatures, stream directory         | **cracked.** Any of 1000 legal ids is written from declared format constants.                                                                                            |
| archive framing: class tags, object tags, map counter, string encoding | **cracked.** Confirmed against the real reader at runtime.                                                                                                               |
| object segmentation and map renumbering                                | **cracked.** Traced streams tile with zero gaps and re-emit byte-identically.                                                                                            |
| `Definition`, `CMgr`, `Config-0`, `ModelHeader`, assembly core         | **cracked for the supported programs.** Every reference byte has a typed owner; opaque count is zero.                                                                    |
| supported feature records                                              | **constructive.** Exact boxes, pad, pocket chains, pad→pad, revolution, groove, fillet, chamfer, shell, linear pattern, and circular pattern have typed native programs. |
| boss versus cut                                                        | **constructive by family.** Each recovered operation has its own typed tree; Kit does not mutate an arbitrary foreign feature record.                                    |
| arbitrary feature records and sketch profiles                          | **partial.** No donor fallback is allowed; unrecovered histories are rejected.                                                                                           |
| repository FCStd corpus                                                | **38/163 accepted**, zero errors and zero vendor-only results; see `CORPUS_COVERAGE.md`.                                                                                 |
| repository FCStd assemblies                                            | **0/5 accepted.** The assembly core is typed, but these component histories or assembly semantics remain unsupported.                                                    |

## Read in this order

1. **`CORPUS_COVERAGE.md`** — the current production boundary, including every recursively audited
   FCStd and the unsupported feature-family counts.
2. **`container/`** — how a file is framed, and the 1000-entry `file_id` -> signature-triplet table.
   Start here: nothing else is reachable until a file opens.
3. **`archive/`** — `GRAMMAR.md` for the tag grammar and the field anchors, `WINDBG.md` for the
   proof that the reader is `su_CArchive` in `swccu.dll` and not MFC, `SEGMENTATION.md` for object
   segmentation and the map-counter rule, `MULTISTREAM.md` for the four other load-critical streams
   and their exact per-feature growth.
4. **`records/`** — per-class field layouts out of the decompiler: `SERIALIZE.md` (end spec,
   from-end spec, rev end spec, extrusion, length parameter, handles), `FEATURE.md` (the
   `moNode_c` / `moFeature_c` base chain and the tree-flags word), `SKETCH.md` (the `sg*` geometry
   classes), `ANSWERS.md` (seven specific open questions, resolved or explicitly not).
5. **`features/`** — what all of that means per feature type: extrude (`RESULTS.md`), revolve
   (`REVOLVE.md` + specs + defects), arcs (`ARC.md`, then `ARC_LAYOUT.md` which supersedes its
   negative result), multi-body documents (`BODIES.md`).
6. **`corpus/`** — the three corpora and what each proves.
7. **`measurements/`** — every volume measurement, with its controls. This is the evidence layer for
   every claim above that says "measured".

`GROUND_TRUTH.md` (real-world 63-file corpus baseline; the document that proved Kit's feature-flag
constants missed ~99% of real features) and `REPORT_resolved.md` (the reader-module fixes that came
out of it) sit at this level because they cut across all of the above.

## The load-bearing facts, in one place

These are the things that must not be lost. Each links to where it is established.

### Container

- The `file_id` -> signature triplet is **not** an algorithm. It is a **1000-entry lookup table** in
  `sldmfcu.dll` `.rdata`: ids at file offset `0x566c40`, triplets at `0x567be0`, big-endian `u32`,
  parallel arrays, initialiser `FUN_3cc4e200` with the loop bound `1000` written as a literal.
  Verified **184/184** real files. **No arithmetic relation exists** — which is why every XOR key,
  affine map over GF(2), LCG, CRC32 and bit-permutation search failed. They were searching for
  something that is not there. (`records/ANSWERS.md` Q7, `container/README.md`, `../data/signature_table.json`)
- A wrong `(file_id, local, central, end)` triplet **hard-crashes SOLIDWORKS** on open, not a clean
  error. (`archive/GRAMMAR.md` §1)

### The archive

- SOLIDWORKS does **not** use MFC's `CArchive`. It uses its own **`su_CArchive` in `swccu.dll`**,
  whose API is exported _undecorated by name_, so it is breakpointable with no PDB. A full
  instrumented startup plus part open recorded 0 `CArchive::ReadObject` calls. Any plan that hooks
  `mfc140u.dll` fails silently. (`archive/WINDBG.md`)
- `su_CArchive::ReadObject` dispatches the object's **vtable slot 5** (byte offset `0x28`) — that
  slot is `virtual void Serialize(su_CArchive&)`. Slot 2 is MFC's `Serialize(CArchive&)` and is the
  wrong one. (`records/SERIALIZE.md` §0)
- `su_CArchive` field offsets: `m_lpBufCur 0x38`, `m_lpBufMax 0x40`, `m_lpBufStart 0x48`,
  `m_nMapCount 0x50`. Taken from `dt mfc140u!CArchive` and then solved independently from the
  runtime dumps with `candidates: 1`. (`archive/WINDBG.md`, `archive/SEGMENTATION.md` §1)
- **Map-counter increment rule: class definition +2, class reference +1, null tag 0, object
  reference 0.** Zero mismatches across 4503 objects. (`archive/SEGMENTATION.md`)
- **The counter does not start at 1.** Base is 109/110/111 for 1/2/3-feature `ResolvedFeatures`
  streams, and 3 (`CMgr`, `ModelHeader`) or 4 (`Config-0`). Tokens below the base belong to earlier
  streams and must not be renumbered. (`archive/SEGMENTATION.md`, `archive/MULTISTREAM.md`)
- Object segmentation **tiles and re-emits byte-identically** on 16 traced parts. That re-emit is the
  correctness proof for any segmentation model — build it, then require the re-emit.
  (`archive/SEGMENTATION.md`, `archive/MULTISTREAM.md`)
- A **marker walk is not an object segmentation.** `ff ff 01 00` is a class _definition_ tag; the
  second object of a class carries only a 2-byte class reference. Marker-relative addressing works
  for object 1 and silently fails for the rest. (`corpus/CORPUS1.md` §2, `corpus/CORPUS2.md` §7.3)
- `carchive.class_definitions` **over-approximates** on large streams — 3 static false positives on
  `THREEFEATURE_pad_cut_pad`. (`archive/SEGMENTATION.md`)
- `ThirdPtyStore/VisualStates` tiles but does **not** re-emit: its archive does not share the combined
  index space. It is droppable and the writer never emits it. (`archive/MULTISTREAM.md`)

### The three feature-count fields

All three must agree with the tree, and all three are outside the obvious place:

| stream                                        | offset          | value     |
| --------------------------------------------- | --------------- | --------- |
| `Contents/Config-0-ResolvedFeatures`          | **604**, `u16`  | `2n`      |
| `Contents/Config-0-ModelHeader` and `Header2` | **77**, `u16`   | `24 + 2n` |
| `Contents/CMgr`                               | **1414**, `u16` | `n`       |

`ResolvedFeatures@604` is the single byte that separates a hard crash from a file that opens
(`G4_four_boss` `04` vs `T4_4_boss` `08`). And **patching a count without growing the list body
crashes**: `T3H`, `T4H`, `T4cmgr`, `T4all` all died on open. (`archive/SEGMENTATION.md`)

### Derived values

- **A guessed derived cache is unsafe.** The typed programs retain fields proven stable and update
  only the depth, angle, profile, direction, and topology copies covered by differential and oracle
  tests. A history needing an unrecovered derived field is rejected; production never copies a
  donor cache. (`archive/GRAMMAR.md` §6, `features/RESULTS.md`, `features/REVOLVE.md` §3.3,
  `corpus/CORPUS2.md` §3)
- Several historical `moEndSpec_c` samples exposed process-memory noise in tail fields. That finding
  prohibits inventing values and prohibits copying the sample. Supported typed programs emit the
  recovered field semantics; other end-spec variants remain unsupported. (`records/ANSWERS.md` Q5)

### Feature semantics

- **Boss vs cut is not an opcode.** It is the 32-bit tree-flags word at `moNode_c + 0x28`
  (`0x40000140` boss, `0x400201CA` cut) **plus** the derived face-identity records that follow
  (`moEndFaceSurfIdRep_c`, `moFromSktEntSurfIdRep_c`, `moEndFace3IntSurfIdRep_c`, the `moFR_c` id
  words — about 40 changed bytes in an 873-byte run). Flipping the word alone crashes. Kit therefore
  selects a complete typed boss or cut family program; it never borrows the operation from a donor.
  (`records/ANSWERS.md` Q1, `records/FEATURE.md`)

* Two silent fixups on that word: on load the reader ORs `|= 0x40000000` unconditionally, and on
  store it clears bit `0x1000`. So bit 30 is always set in memory and bit 12 always clear on disk.
  Bit 31 is orthogonal to the operation — mask it before classifying. (`records/FEATURE.md` §1,
  `GROUND_TRUTH.md` §2)
* Blind -> ThroughAll is **not a byte flip**: it deletes the whole dimension object (-1723 bytes) and
  the `moEndFace3IntSurfIdRep_c` class. (`corpus/CORPUS2.md` §5.5)
* A modern `moRevEndSpec_c` stores **no angle at all** — `getAngle` returns the literal
  `6.2831853071796` when the dimension is null, which is exactly why all 67 corpus revolves are 360°
  with a byte-identical 52-byte record. (`records/SERIALIZE.md` §3, `features/REVOLVE.md` §4)
* Lines and arcs store **point-handle indices, not coordinates**. A full circle and an arc use the
  same record and it contains neither an angle nor a radius. (`records/SKETCH.md` §2/§4)
* An arc centre is an ordinary sketch-coordinate record whose trailer is `role = 0`,
  **`geometry_class = 1`** — the discriminator the static pass looked for and did not find.
  (`features/ARC_LAYOUT.md`, superseding `features/ARC.md` §3/§4)

### `swXmlContents/KeyWords`

- Plain XML, present in every part, and the cheapest authoritative oracle: its `id` is the same
  feature id as the binary tree-node record, and `<Dimension Name="D1">` is the authored value as
  text. Use it to cross-check every decode for free, with no COM. (`GROUND_TRUTH.md` §1)
- It **starts with a single `0x86` byte** and uses **CRLF**. A UTF-8 BOM **crashes SOLIDWORKS**, and
  `\n\n` line endings crashed it reproducibly three times before the fix. (`archive/GRAMMAR.md`,
  `features/RESULTS.md`)
- `KeyWords` and the binary stream must agree. A ThroughAll feature's `<Extrusion>` has no
  `<Dimension>` child, matching the missing scalar in the stream. (`corpus/CORPUS2.md` §8)

## Negative results and traps

Kept because they cost real time and they are as valuable as the wins.

| trap                                | detail                                                                                                                                                                                                                                                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| searching for a signature mixer     | There is no relation. It is a table. (`records/ANSWERS.md` Q7)                                                                                                                                                                                                                                                         |
| hooking MFC                         | 0 `CArchive::ReadObject` calls. Hook `swccu!su_CArchive`. (`archive/WINDBG.md`)                                                                                                                                                                                                                                        |
| `cdb` script inclusion              | Use `-c "$$<file"`, **never** `$$><file` — `.sympath` swallows the following commands. (`archive/WINDBG.md`)                                                                                                                                                                                                           |
| `cdb` symbol load                   | `.symopt+0x4000` must be the **first** line, or 620+ module symbol lookups stall the run. (`archive/WINDBG.md`)                                                                                                                                                                                                        |
| `cdb` symbol spelling               | Use the **undecorated** name `swccu!su_CArchive::ReadObject`. cdb rejects the mangled spelling because of the `@` characters (`Syntax error`). (`archive/SEGMENTATION.md`)                                                                                                                                             |
| the `cdb` binary                    | The WinDbg MSIX ships **`cdbX64.exe`**, not `cdb.exe`. (`archive/WINDBG.md`)                                                                                                                                                                                                                                           |
| `sxe ld:mfc140u`                    | Never fires — the DLL loads before the initial debugger break. Use `.reload /f`. (`archive/WINDBG.md`)                                                                                                                                                                                                                 |
| Ghidra + dot directories            | `analyzeHeadless` throws `Path element starting with '.' is not permitted` for any path component beginning with `.`. Fixed with a directory junction: `mklink /J C:\Users\odin\kitgh <...>\.rescratch\ghidra`. (`../tooling/ghidra/SETUP.md` §3)                                                                      |
| Ghidra without the rename pass      | Every `operator>>` overload prints identically, so a `double` read is indistinguishable from a `char` read. Run `RenameArchiveApi.java` first. (`../tooling/ghidra/SETUP.md` §6)                                                                                                                                       |
| trusting a `crashed-on-open` result | After ~25 SOLIDWORKS launches the install degraded so that a **pristine donor also crashed** (`com_error(-2147023170)`). Read `features/RESULTS.md` §4 before concluding anything from a crash. Recovery needs a reboot or a settings reset.                                                                           |
| COM early binding                   | `gencache.EnsureDispatch` fails on the 2025 interface. Use late binding, integer args to `NewDocument`, `SaveAs4` not `SaveAs2`, and a `VARIANT(VT_DISPATCH, None)` for `SelectByID2`'s callout. (`corpus/CORPUS1.md` §0)                                                                                              |
| guessing COM arity                  | `FeatureCut4` takes **27** arguments, not 24, and `FeatureCut5` does not exist on `IFeatureManager`. Read arity out of `sldworks.tlb` first — guessing costs a whole session. (`corpus/CORPUS2.md` §0)                                                                                                                 |
| stream length as a fingerprint      | Face-supported layouts carry ±3 bytes of noise from a nondeterministic zlib-compressed Parasolid blob. (`corpus/CORPUS2.md` §2)                                                                                                                                                                                        |
| `moICE_c` means "cut"               | It does not. It means "feature 2 or later". There is no `moCut_c` in any authored corpus. (`corpus/CORPUS2.md` §7.1)                                                                                                                                                                                                   |
| the 17° circle rule                 | It is how COM `CreateCircleByRadius` places the rim point, and it generalises to diametrally-dimensioned circles (578/817) but **not** to radially-dimensioned ones (20/362), and it finds **0** arcs in every production revolve profile. (`features/ARC.md`, `REPORT_resolved.md` §4)                                |
| treating merge-result as one flag   | The donor-era experiment produced 32,000 mm³ and two bodies instead of 28,800 mm³ and one. The typed boss→boss program later closed the feature scope: the current file opens and rebuilds as one body at 28,800 mm³, and changing `D1@Boss-Extrude2` from 25 to 30 rebuilds to 30,400 mm³. (`archive/MULTISTREAM.md`) |

## What is superseded

Read these together or you will draw the wrong conclusion:

- `archive/GRAMMAR.md` §8 lists object segmentation and map renumbering as blockers, and reads as
  "arbitrary feature trees are impossible". Both were then solved byte-exactly in
  `archive/SEGMENTATION.md` and `archive/MULTISTREAM.md`, and the 3-feature ceiling is lifted —
  `nboss1..nboss6` build 1 to 6 solid features with exact volumes.
- `features/ARC.md` §3/§4 concludes a partial arc cannot be located. Correct for the static corpus,
  and superseded by `features/ARC_LAYOUT.md`, which located it by COM-authoring a differential family.
- `features/DECODER_DEFECTS.md` D1-D3 describe revolve defects in the reader module. The prose says
  `locate-features-drops-revolve`; the machine-readable counter in `../data/revolve_inventory.json`
  is spelled `locate-features-includes-revolve` because the module was subsequently fixed. Trust the
  JSON for current state and the prose for the reasoning.
