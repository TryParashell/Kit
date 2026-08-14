<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# The `moFeature_c`-onward record bodies, recovered from the code

Source: Ghidra 12.1.2 headless decompilation of `sldmodu.dll` from the licensed SOLIDWORKS 2025
install, read out of `out/sldmodu_serialize.c` after `RenameArchiveApi.java` had renamed every
`su_CArchive::operator>>` overload, so every width below is the width the archive actually reads.
No SOLIDWORKS process, no COM, no debugger.

`re/solidworks/README.md` records this territory as partial and donor-driven. This document says
which parts of it are now closed, and for each part that is still open, the address that would
close it.

Byte evidence is the nine recorded segmentations in `re/data/segments/segments_*.json` replayed by
`re/tooling/ghidra/Validation/VerifyClassLayouts.py` against `re/data/Layouts/ClassLayoutsDecompiled.json`.
Confidence vocabulary is `Serialize.md`'s.

---

## 1. `moDefaultRefPlnData_c` — the lead run is CLOSED

Function: `sldmodu.dll` `0x4c2d1cf0`. It is two calls: `su_CObject::Serialize` and then a tail-jump
through virtual slot `0x150` that Ghidra cannot resolve ("Could not recover jumptable"). So the
whole record is produced by that indirect callee and the field list below is derived from the bytes,
with the class's identity as the only structural prior.

The record is the default Front / Top / Right reference-plane data. Every one of the nine traced
parts has exactly three instances, all with three `null` children.

| offset in `lead` | width | type     | name                                                        | role                         | confidence |
| ---------------- | ----- | -------- | ----------------------------------------------------------- | ---------------------------- | ---------- |
| `+0`             | 24    | `f64[3]` | `Origin`                                                    | constant `(0, 0, 0)`         | confirmed  |
| `+24`            | 24    | `f64[3]` | `Normal`                                                    | constant, `+Z` / `+Y` / `+X` | confirmed  |
| `+48`            | 1     | `u8`     | `HasBasis`                                                  | constant                     | confirmed  |
| `+49`            | 72    | `f64[9]` | `Basis`, row-major orthonormal, **only if `HasBasis == 1`** | derived                      | confirmed  |
| next             | 32    | `f64[4]` | plane extents                                               | constant                     | partial    |
| next             | 1     | `u8`     | —                                                           | constant `0`                 | partial    |
| next             | 32    | `f64[4]` | plane extents                                               | constant                     | partial    |

So

```
lead = 49 + (72 if HasBasis else 0) + 65
```

which is **114 or 186**, and the conditional field is exactly the omission the earlier sessions had
attributed to `moSketchChain_c`:

| instance                                  | `Normal`          | `HasBasis` | measured `lead` | instances   |
| ----------------------------------------- | ----------------- | ---------- | --------------- | ----------- |
| first `moDefaultRefPlnData_c` of the part | `(0, 0, 1)` Front | `0`        | 114             | 9 / 9 files |
| second                                    | `(0, 1, 0)` Top   | `1`        | 186             | 9 / 9 files |
| third                                     | `(1, 0, 0)` Right | `1`        | 186             | 9 / 9 files |

**Front omits the basis because it is the identity.** `VerifyClassLayouts.py` predicts the offset
of child 0 from this rule and of children 1 and 2 from the constant runs `@0 = 47` and `@1 = 0`, and
gets all 81 boundaries right across the nine traces with zero mismatches.

Applied statically to the 32 donor streams, the rule places the three `null` child tokens correctly
in all 32 `moDefaultRefPlnData_c` class definitions. Those 32 are all `HasBasis == 0`, because the
class definition is always the Front plane; Top and Right arrive as classrefs and finding them
statically needs the stream's class map, so the donor check exercises only the short branch.

**Still open:** `@2`, the run after the last child. All 27 traced instances leave exactly 2 bytes
between the end of their last child and their recorded `scope_end`, so 2 is the only value that
tiles — but a non-top-level object's `scope_end` is an upper bound, not a witness, and those 2 bytes
may belong to the parent `moRefPlane_c`. The indirect call at `0x4c2d1cf0` through virtual slot
`0x150` is where the answer is. The layout keeps `@2` `opaque` rather than adopting the fitted 2.

---

## 2. `moSketchChain_c` — the lead run is CLOSED

Function: `sldmodu.dll` `0x4c2d3af0`. Read order, complete:

| #   | width / kind       | condition     | `this` offset  | name                                                    | role          | confidence          |
| --- | ------------------ | ------------- | -------------- | ------------------------------------------------------- | ------------- | ------------------- |
| 1   | sub-record, slot 5 | always        | `0x08`         | `u16 count` then `count` × `u32` entity index           | authored      | confirmed           |
| 2   | sub-record, slot 5 | always        | `0x60`         | `u16 count` then `count` × `u32`; count is 1 everywhere | authored      | confirmed           |
| 3   | 4                  | always        | `0x28`         | `u32`                                                   | authored      | confirmed           |
| 4   | 4                  | always        | `0x38`         | `i32`                                                   | authored      | confirmed           |
| 5   | 4                  | always        | `0x50`         | `i32`                                                   | authored      | confirmed           |
| 6   | 4                  | always        | `0x54`         | `i32`                                                   | authored      | confirmed           |
| 7   | 4                  | always        | `0x58`         | `u32`                                                   | authored      | confirmed           |
| 8   | 4                  | always        | `0x5c`         | `u32`                                                   | authored      | confirmed           |
| 9   | string             | always        | `0x80`         | `operator>>(CString)`, empty in all 16                  | authored      | confirmed           |
| 10  | 2                  | always        | —              | handle-presence flags, must be `< 4`                    | authored      | confirmed           |
| 11  | object             | flags bit 0   | `0x30`         | `sg3DPlaneHandle*`                                      | authored      | partial (never set) |
| 12  | object ×2          | flags bit 1   | `0x40`, `0x48` | `sgPointHandle*` pair                                   | authored      | partial (never set) |
| 13  | 4                  | ver > `0xb95` | `0xd0`         | `u32`                                                   | authored      | confirmed           |
| 14  | 4                  | ver > `0xc8d` | —              | `u32` pair-array length, `0` in all 16                  | derived       | confirmed           |
| 15  | 8 × length         | ver > `0xc8d` | `0xb8`         | `su_CMapPtrToPtr` `(u32, u32)` pairs                    | derived       | confirmed (empty)   |
| 16  | object             | ver > `0xc8d` | `0xc0`         | `ReadObject(contourTrimData_c)`                         | authored      | confirmed           |
| 17  | object             | ver > `0xc8d` | `0xc8`         | `ReadObject(contourTrimData_c)`                         | authored      | confirmed           |
| 18  | 4                  | ver > `0xddc` | `0x90`         | `i32`                                                   | uninitialised | partial             |
| 19  | 4                  | ver > `0xddc` | `0xa0`         | `i32`                                                   | uninitialised | partial             |
| 20  | 4                  | ver >= 4000   | `0xa4`         | `i32`                                                   | uninitialised | partial             |

Items 1 to 15 are the `lead` run, items 16 and 17 are the two traced children, and items 18 to 20
are the run after the last child. With the flags at `0` and both counted arrays present:

```
lead = 2 + 4*count1 + 2 + 4*count2 + 24 + string + 2 + 4 + 4
     = 46 + 4*count1        (count2 == 1, string == "" == 4 bytes, in all 16 instances)
```

Measured `lead` is **62 in 13 instances** (`count1 = 4`, the rectangle chains) and **50 in 3**
(`count1 = 1`, the circle chains). The rule reproduces all 16 exactly, and `@0 = 0` — the two
`contourTrimData_c` reads are back to back — is reproduced in all 16 as well. `@1 = 12` from items
18 to 20 gives a total body of `lead + 16`, which never overruns its bound and lands exactly on it
once.

### Independent check on the 32 donor streams

`tests/fixtures/solidworks/donors/*/resolved.bin` are 32 real resolved-features streams, none of
them among the nine traces. Applying the rule statically to every `moSketchChain_c` class
definition in them:

```
donor files 32
string_ok 32            the ff fe ff 00 empty-string marker lands exactly where the rule predicts
tail_00000000 32        the 4 bytes after the computed lead are the two null contourTrimData_c tokens
c1,c2,units: {(4, 1, 0): 28, (1, 1, 0): 1, (6, 1, 0): 3}
```

32 / 32, and `count1 = 6` appears — a six-edge chain the traced corpus never produced. The same 32
streams carry 30 `moSketchRegion_c` definitions whose `u16` boundary count decodes to 4, 1 and 6
with every element landing on a valid object token under the 12-bytes-per-handle model.

**The 209 / 197 marker offsets and the plane-id / axis-code pair recorded in earlier sessions are
not inside `moSketchChain_c`.** Its traced scope is at most 120 bytes, so `marker + 209` is past the
end of the object. Nothing in `0x4c2d3af0` reads a plane object id or an axis code, and the 9-double
basis those sessions expected here is in `moDefaultRefPlnData_c` (§1).

**Still open:** `@1` is 12 by the code but has no witness — `moSketchChain_c` is never at depth 0
and is always the last child of its parent, so the traces bound it to at most 33 bytes without
pinning it. That is the only reason the class is `partial` and not `confirmed`.

---

## 3. `moSketchRegion_c` — CLOSED, and the variability is not its own

Function: `sldmodu.dll` `0x4b9d81e0`. The whole body is:

```c
su_CObject::Serialize(this, ar);
if (0x2398 < version) { operator>>(ar, (suObList **)(this + 8)); }
```

and the store branch names the member: `ScopedObjContext(ar, "BoundaryEnts", this->0x08)`.

So `lead = 0`, one child, `@0 = 0`, and the body length **is** the child's span. The child is a
classref into a class map inherited from an earlier stream, so the traces name it
`external#82`..`external#85`; its own body is a `u16` count followed by `count` `sgEntHandle`
objects at 12 bytes each (a 2-byte classref token plus the 10-byte handle record of
`SketchHandles.md` §2). Decoded on real bytes:

| part / node                | count | child body | `moSketchRegion_c` body |
| -------------------------- | ----- | ---------- | ----------------------- |
| `vendor_cojinete` node 428 | 1     | 14         | 16                      |
| `circle` node 192          | 1     | 14         | 16                      |
| `baseline` node 201        | 4     | 50         | 52                      |

The traced body lengths of 16, 54 and 90 that `SolveRuns.py` reports are these plus a 38-byte
ancestor run that the traced scope absorbs; the 16-byte instances are the ones where the ancestor
run happens to be empty.

`moSketchRegion_c` is `partial` in `ClassLayoutsDecompiled.json` only because the length of the
boundary list is carried by a class whose name is not stable inside a single stream, so it cannot be
keyed in this file. Both of `moSketchRegion_c`'s own runs are `0` and neither varies.

---

## 4. `moCompFeature_c` — the array geometry is measured, the entry body is OPEN

Function: `sldmodu.dll` `0x4bc222f0`. Read order:

| #   | width / kind | condition                                      | name                                                | confidence            |
| --- | ------------ | ---------------------------------------------- | --------------------------------------------------- | --------------------- |
| 1   | base         | always                                         | `moCompRef_c::Serialize`                            | not found             |
| 2   | —            | ver < `0x2c9`                                  | `FUN_4bc28cf0` legacy path, then return             | confirmed (not taken) |
| 3   | 4            | `hasCondition(1) && hasCondition(0x10000)`     | `i32` external flag                                 | partial               |
| 4   | 4            | the guard chain in `LAB_4bc22456` is not taken | `i32` presence flag; `0` ends the record            | partial               |
| 5   | sub-record   | always reached                                 | `FUN_4bbb16e0` on the `moFRData_c` at `this + 0xf0` | confirmed             |

`FUN_4bbb16e0` is the history-item record, and for every corpus version it is exactly two fields:

| offset    | width | type  | name                                          | role     | confidence |
| --------- | ----- | ----- | --------------------------------------------- | -------- | ---------- |
| `end - 8` | 4     | `u32` | tree-node id, `moFRData_c + 0`                | authored | confirmed  |
| `end - 4` | 4     | `u32` | `su_CTime`, a Unix `time_t`, `moFRData_c + 8` | derived  | confirmed  |

Its three legacy branches — a `CString` name for ver < `0x4a5`, a discarded `u32` for
ver < `0xd7b`, an `i32` for `0xa63 < ver < 0xc77` — are all skipped by 13000, 14000 and 18000.

Measured across all nine traces, for all 30 instances:

- `lead = 0` in 30 / 30. The first thing read is the `external#43` classref that
  `moCompRef_c::Serialize` pulls in, with nothing in front of it.
- the traced scope from the end of the instance's own tag is **93 bytes in the seven authored parts
  (24 instances) and 89 bytes in the two vendor parts (6 instances)**,
- consecutive instances start **119 bytes** apart in the authored parts and **115** in the vendor
  parts, so the per-entry stride is `2` (classref tag) `+ scope` `+ 24` (inter-entry bytes). The
  first entry of a stream is 19 bytes longer (138 or 134) because it is a class definition rather
  than a classref, and `ff ff 01 00 10 00` plus `"moCompFeature_c"` is 19 bytes more than a tag.

The `93 + 119 * (n - 1)` array length recorded by earlier sessions therefore holds for the
18000-era streams only. The 13000/14000-era streams are `89 + 115 * (n - 1)`, and a writer that
assumes 119 unconditionally will mis-segment every older stream. This is the same 4-byte
generational gate as `moFeatureDimHandle_c@0` in §6. `n = 2 * feature_count`, one entry per sketch
interleaved with one per feature, is reproduced: the parts with one, two and three features carry
2, 4 and 6 instances respectively.

**Still open:** `@0`, the class's only run. The child is the `external#43` object read inside
`moCompRef_c::Serialize`, and its body end has no witness in any trace, so the split of the 93 bytes
between the child and the run is undetermined. `moCompRef_c::Serialize` is the specific next step;
the two `i32` flags of items 3 and 4 are also unresolved because both guards depend on
`moArchiveHelper_c::hasCondition` bits that are set by the caller, not by the stream.

The `u16` at stream offset 604 holding `2 * feature_count`, and the constant `0x00004650` (18000,
the version stamp) at `end - 12` of each entry, are recorded here as prior measurements. Neither is
read by `0x4bc222f0`; the stamp is written by `moCompRef_c::Serialize` or above it, and offset 604
is in the stream prologue, not in any `moCompFeature_c` body.

---

## 5. `moICE_c` — the former 9.6 KB content wall is structurally CLOSED

Function: `sldmodu.dll` `0x4bb8eba0`, shared with `moExtrusion_c`. The old `moICE_c@7` run was not a
9.6 KB scalar or constant record. It was a trace-ownership error that had absorbed a complete
result-body object graph. The corrected record exposes as many as **64 direct tagged children** and
has no opaque variable run.

The modern prefix is:

| position    | child / bytes                                                                      | recovered meaning                                           |
| ----------- | ---------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| slots 0–6   | the already recovered base objects and runs `4, 2, 45, 30, 52, 6, 0`               | feature/base chain                                          |
| run 7       | 18 bytes at version 18000, 22 at 14000                                             | generation-gated framing before the result body             |
| slot 8      | `moCompSolidBody_c`                                                                | result-body graph owner                                     |
| slots 9–10  | `moICE_c` references                                                               | shared owner/back references; both are real archive objects |
| slot 11     | `moPMarkRecord_c` after 20 bytes                                                   | surface identifier                                          |
| slots 12–14 | one wildcard, a second `moPMarkRecord_c`, and `moEndSpec_c`                        | end specification entry                                     |
| slots 15–63 | the recovered end-specification, display-dimension, handle and chooser descendants | parametric feature payload                                  |

The child at slot 9 selects the native serializer branch and therefore the actual arity:

| slot-9 runtime class     | total children |
| ------------------------ | -------------: |
| `moICE_c`                |             15 |
| `moCompSolidBody_c`      |             15 |
| `moFaceRef_c`            |             15 |
| `null`                   |             60 |
| `moPerBodyChooserData_c` |             64 |

These are content-driven branches, not fixture offsets. The same table handles the three modern
traces, the older vendor-ring graph with two chooser records, and all authored donors that reach
the record. The archive walker now segments, tiles and re-emits **17 of 32** independent donor
streams byte for byte; `boss_boss_cut_cut` traverses **955 archive objects**. This proves complete
structural ownership and re-emission for those streams. It does not prove first-principles
synthesis or SOLIDWORKS acceptance: several descendant classes still have only partially named
scalar fields, and no donor-free feature constructor emits this graph yet.

The nested result-body grammar is now:

- `moCompSolidBody_c`: component reference, face reference, `u32` body-id array and a `u16`
  per-body chooser count;
- `moFaceRef_c`: 36-byte lead, `u32 EntityCount`, one tagged `moEntityIdRep_c` per entity and a
  20-byte modern tail;
- `moPerBodyChooserData_c`: three native `suObArray` records followed by two `i32` fields, a native
  `su_CDWordArray` (`u16 count` plus `count × u32`) and one final `i32`;
- `moBBoxCenterData_c`: `i32 CenterType`, three `f64` centre coordinates and one `f64` scale.

The `su_CDWordArray` point matters: its count is not a boolean state flag. Counts zero and one are
witnessed, but the layout now accepts every native count and sizes the tail algorithmically.
`moExtrusion_c@5` remains a separate, older fixed-slot layout problem and must not be used to
reintroduce an opaque run into `moICE_c`.

---

## 6. `moFeatureDimHandle_c` — eight children with a closed generation gate

Function: `sldmodu.dll` `0x4c86e240` = `moModDimHandle_c::Serialize`, shared by the whole
`mo*DimHandle_c` family. Its own contribution on a modern file is one object read:

| #   | width / kind        | condition          | `this` offset | name                                  | confidence            |
| --- | ------------------- | ------------------ | ------------- | ------------------------------------- | --------------------- |
| 1   | base                | always             | —             | `FUN_4c864440`                        | not found             |
| 2   | 1 + object + string | ver < `0x322`      | `0xe8`        | legacy `moExtObject_c` + name path    | confirmed (not taken) |
| 3   | object              | `this + 0xe8 == 0` | `0xf0`        | `operator>>`, must be a `Dimension_c` | confirmed             |

Reparenting all 12 instances exposes eight children, not six. The constant runs are `lead = 0`,
`@1 = @2 = @3 = 0`, `@4 = 1`, `@5 = 0`, `@6 = 10`, `@7 = 0`, and

| run  | value | parts                                                 |
| ---- | ----- | ----------------------------------------------------- |
| `@0` | 82    | the seven authored parts, 10 instances                |
|      | 78    | `vendor_cojinete` node 543 and `vendor_ring` node 400 |

The 4-byte difference falls cleanly in the two older-generation parts, so run 0 is encoded as a
`runs_by_version` gate: 78 at 14000 and 82 at 18000. The old `@4 = 15` had absorbed two null tags and
their one- and ten-byte following runs. Run 7 now places the final `ParallelPlaneDistanceDim_c` at
the exact recorded offset in both generations.

---

## 7. `moDisplayDistanceDim_c` — twenty children with one older-generation tail open

Function: `sldmodu.dll` `0x4c86acd0`. Reparenting all 14 traced instances exposes 20 children. The
old run 5 = 378 had absorbed a null child and its following 102-byte run; it is now run 5 = 274,
slot 6, and run 6 = 102. Runs 0 through 18 are constant across every instance:

`lead 2, @0 0, @1 0, @2 33, @3 48, @4 83, @5 274, @6 102, @7 0, @8 0, @9 44,
@10 0, @11 40, @12 0, @13 0, @14 0, @15 4, @16 0, @17 12, @18 168`.

Run 19 is four bytes in all ten 18000-era instances. The four 14000-era instances measure 0, 0, 0
and 170, so that generation remains deliberately absent from the gate and refuses instead of
guessing. `VerifyClassLayouts.py` checks 224 run boundaries for this class with zero mismatches.

---

## 8. `moSketchExtRef_w` — OPEN

Function: `sldmodu.dll` `0x4c2d40f0`. Read order:

| #   | width / kind | condition      | `this` offset | confidence                                                           |
| --- | ------------ | -------------- | ------------- | -------------------------------------------------------------------- |
| 1   | base         | always         | —             | `FUN_4c2d2290`, not found                                            |
| 2   | 2            | ver >= `0x94`  | `0xa8`        | confirmed; the reader throws unless the signed value is in `[-2, 0]` |
| 3   | object       | ver >= `0x8fd` | `0xb0`        | `moBackedUpData_c*`, confirmed                                       |

Three traced children in all five instances, `lead = 0`. `@1`, which is where item 2's `u16`
lives, measures **54 bytes in four instances and 58 in `circle` node 166**, so 52 or 56 of those
bytes come from `FUN_4c2d2290`, not from `moSketchExtRef_w`. `@0` and `@2` follow children
(`moCompSketchEntHandle_c` or `moCompEdge_c`, and `moArcBackedUpData_c` or
`moPointBackedUpData_c`) whose body ends have no witness. All three runs are `opaque`.
`FUN_4c2d2290` is the address that would close `@0` and `@1`.

---

## 9. What is closed and what is not

| class                    | claim     | what closed                                                           | what blocks the rest                                                          |
| ------------------------ | --------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `moDefaultRefPlnData_c`  | partial   | `lead` = 114 or 186 by a `u8` predicate, 27 / 27                      | `@2`, bounded to 2 bytes; virtual slot `0x150` off `0x4c2d1cf0`               |
| `moSketchChain_c`        | partial   | `lead` = 46 + 4·count, 16 / 16; `@0` = 0                              | `@1` = 12 has no witness                                                      |
| `moSketchRegion_c`       | partial   | both runs are 0; body is the `BoundaryEnts` list                      | the list class is not keyable in this file                                    |
| `moCompFeature_c`        | partial   | `lead` = 0; 93-byte scope, 119-byte stride, 30 / 30                   | `@0`; `moCompRef_c::Serialize`                                                |
| `moExtrusion_c`          | partial   | `lead`, `@1`–`@4`, `@7`                                               | `@5`; `FUN_4bb886c0`, then `moModelFeature_c/moFeature_c/moNode_c::Serialize` |
| `moICE_c`                | partial   | complete conditional 15/60/64-child graph; 17 exact donor round trips | descendant field semantics and donor-free synthesis                           |
| `moPerBodyChooserData_c` | confirmed | three counted object arrays and counted `u32` tail                    | —                                                                             |
| `moFeatureDimHandle_c`   | partial   | `lead`, `@1`–`@4`                                                     | `@0` version gate in `FUN_4c864440`                                           |
| `moDisplayDistanceDim_c` | partial   | 16 constant runs, 224 / 224 boundaries                                | `@17`, `@6`, `@11` have no witness                                            |
| `moSketchExtRef_w`       | partial   | `lead` = 0                                                            | `@0`, `@1`; `FUN_4c2d2290`                                                    |

---

## 10. Evidence

```
classes=76
donors=32 segmented=17 tiled=17 identical=17
boss_boss_cut_cut objects=955
focused archive tests: 100 passed
```

Reproduce the group-aware static walk and byte-identity check with:

```powershell
uv run python re/tooling/harness/SegmentFixtures.py --out .rescratch/re/census.json
```

`VerifyClassLayouts.py` remains useful for fixed-slot run tables, but it predates `groups` and
`child_count_by_class`; it deliberately does not validate the 64-child `moICE_c` or the three
counted arrays in `moPerBodyChooserData_c`. The donor segmenter executes those rules directly and
then requires a gap-free tiling and byte-identical `Model.emit()` result. The former
`sgSketch`/`suObList` recorded-layout failures are now encoded by the counted-group and guarded-tail
rules and the focused suite is clean.
