<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# The `moNode_c` / `moFeature_c` / `moModelFeature_c` base chain

The record that every feature in `Contents/Config-0-ResolvedFeatures` opens with, recovered from
Ghidra 12.1.2 headless decompilation of `sldmodu.dll` (SOLIDWORKS 2025, licensed install). No
SOLIDWORKS process, no COM, no debugger. Dump: `.rescratch/ghidra/out/task2.c`, produced by
`run_dump_task2.ps1` with `spec_task2.txt`; `RenameArchiveApi.java` was already applied and saved
to the project, so widths come from `AR_get_<type>` names rather than from guesses.

Confidence words as in `SERIALIZE.md`: **confirmed** = decompiled _and_ the arithmetic reproduces
real traced bytes; **partial** = decompiled but no data checks it; **not found**.

---

## 0. The actual inheritance chain

`SERIALIZE.md` §4 recorded `moExtrusion_c::Serialize` → `moBodyFeature_c::Serialize` →
`FUN_4bb886c0` (unnamed) and stopped there. `FUN_4bb886c0` opens with
`moModelFeature_c::Serialize(param_1, param_2)`, which resolves the chain in full:

```
moExtrusion_c::Serialize        0x4bb8eba0   3 fields   (SERIALIZE.md §4)
 └ moBodyFeature_c::Serialize   0x4bb8aa10   5 fields   (SERIALIZE.md §4)
    └ FUN_4bb886c0              (unnamed)    1218 lines, many fields
       └ moModelFeature_c::Ser. 0x4bb96700   1 field
          └ moFeature_c::Ser.   0x4bb8efe0   647 lines, many fields
             └ FUN_4c1d9790     (unnamed)    -> moNode_c
```

Because each level calls its base **first**, the bytes come out of the stream in the reverse of
that list: `moNode_c` first, `moExtrusion_c` last. The two `moExtrusion_c` doubles that
`SERIALIZE.md` §2 uses to close the tail budget are genuinely the last 12 bytes of the whole
record, and **the first bytes of the whole record are `moNode_c`'s**.

`moNode_c::Serialize` (`0x4c1db8f0`) is not the function that runs for a modern file. Its first
statement is

```c
if (0xc7c < version) {            /* 3196 */
  (**(code **)(*(longlong *)this + 0x4a8))();
  (**(code **)(*(longlong *)this + 0x4b0))(this, param_1);
  return;
}
```

so for every corpus file it delegates to virtual slots `0x4a8` / `0x4b0` and returns. Those slots
are `moNode_c::SerializeLWData`, `0x4c1dc9b0` and `0x4c1dc9c0`; `0x4c1dc9c0` is the one that takes
the archive and it is the modern node record. The legacy body of `moNode_c::Serialize` reads the
same fields in the same order, which is how the field names below are cross-checked: its store
branch tags them with `su_DBKey`s.

---

## 1. `moNode_c` — CONFIRMED

Function: `moNode_c::SerializeLWData(su_CArchive &)` = `0x4c1dc9c0`.

| #   | `this` offset | width  | archive op                                        | name / meaning                                                                | confidence |
| --- | ------------- | ------ | ------------------------------------------------- | ----------------------------------------------------------------------------- | ---------- |
| 1   | `0x18`        | object | `ReadObject(moNodeName_c)`                        | the **tree node name** — a `moNodeName_c` whose body is one serialised string | confirmed  |
| 2   | `0x0c`        | 4      | `AR_get_long` (ver >= `0x6b` = 107)               | node state bits; see the remap note                                           | confirmed  |
| 3   | `0x28`        | 4      | `AR_get_long` (ver > `0xe1` = 225)                | **the tree-flags word**                                                       | confirmed  |
| 4   | `0x08`        | 4      | `AR_get_long` (ver > `0x147` = 327)               | **the feature id** — `su_DBKey` name `"id"`                                   | confirmed  |
| 5   | `0x2c`        | 4      | `AR_get_long` (ver > `0x143a` = 5178)             | (no accessor bound)                                                           | confirmed  |
| 6   | `0x20`        | string | `::operator>>` `CStringT` (ver > `0x23cd` = 9165) | a second name/label string, empty in every traced part                        | confirmed  |

**16 bytes of scalars, between the node-name object and the trailing string.**

### Where the tree-flags word is written, and its two fixups

Item 3 is the `0x40000140` / `0x400201CA` word. Two reader/writer fixups matter and a writer that
ignores them will have its value silently changed:

- **On load** the reader does `*(uint *)(this + 0x28) |= 0x40000000` unconditionally. Bit 30 is
  therefore always set in memory regardless of what is on disk. That is why every observed flags
  word has `0x40000000` set. (The legacy `moNode_c::Serialize` instead ORs bit 30 back _from the
  pre-read in-memory value_, `|= uVar2 & 0x40000000` — same effect for a fresh load.)
- **On store** the writer saves `this + 0x28`, calls `clearFlag(this, 0x1000)`, writes the word,
  then restores the saved value. So bit 12 is always **clear** on disk even when it is set in
  memory.

### Where the feature id is written

Item 4, `moNode_c + 0x08`, `i32`, immediately after the flags word. Its `su_DBKey` in the store
branch is literally `"id"`. It is gated behind a virtual predicate — the reader calls slot `0x1d0`
and only reads the id when it returns non-zero — and there is a second path for
`hasCondition(0x4000000)` documents that reads the same 4 bytes at the same position, so the
position is unconditional in practice for a part file. Values observed: tree folders take small
ids (1, 7, 8, 9, 10, 11, 16, 17, 18, 21–24, 36), reference planes 2–4, sketches 5 and 25,
extrusions 32/35/40/50, and `moLengthParameter_c` always **`-1`**.

### Byte offsets, for a feature class definition

For a class definition of class `C` the data starts at `marker + 6 + len(C)`. The first thing there
is the node-name object token, then the name string, so with a class-reference token for
`moNodeName_c` (2 bytes) and a short string (`ff fe ff`, 1-byte count, `2 * count` bytes):

| field                   | offset from the feature's class marker |
| ----------------------- | -------------------------------------- |
| node-name token         | `6 + len(C)`                           |
| name string             | `8 + len(C)`                           |
| `+0x0c`                 | `12 + len(C) + 2 * nameLen`            |
| **tree-flags `+0x28`**  | `16 + len(C) + 2 * nameLen`            |
| **feature id `+0x08`**  | `20 + len(C) + 2 * nameLen`            |
| `+0x2c`                 | `24 + len(C) + 2 * nameLen`            |
| trailing string `+0x20` | `28 + len(C) + 2 * nameLen`            |

### Evidence

Worked example, `PADPLANE_rev_d5.SLDPRT`, the second boss extrude, straight out of the stream at
byte 8274:

```
 8274 +6   ff ff 01 00 0d 00                     class definition, schema 1, namelen 13
 8280 +13  moExtrusion_c
 8293 +2   04 80                                 classref 0x8004 -> moNodeName_c
 8295 +4   ff fe ff 0d                            string marker + count 13
 8299 +26  B.o.s.s.-.E.x.t.r.u.d.e.1.            UTF-16LE "Boss-Extrude1"
 8325 +4   00 00 00 00                            moNode_c +0x0c
 8329 +4   40 01 00 40                            moNode_c +0x28   TREE FLAGS = 0x40000140
 8333 +4   20 00 00 00                            moNode_c +0x08   FEATURE ID = 32
 8337 +4   00 00 00 00                            moNode_c +0x2c
 8341 +4   ff fe ff 00                            moNode_c +0x20   empty CString
 8345 +4   00 00 00 00                            moFeature_c +0x290
 8349 +2   00 00                                  next traced object (null)
```

`8329` is byte-for-byte the offset `ANSWERS.md` Q1 reported for `0x40000140` in this part, and
`13586` for the second feature is the same layout with a one-character-longer name. The traced
child span for the `moNodeName_c` class reference is `8293..8349` = **56 bytes**, and
`2 + 4 + 26 + 16 + 4 + 4 = 56` closes exactly — the tracer over-attributes `moNode_c`'s and
`moFeature_c`'s leading scalars to the name object because it derives `scope_end` from the next
sibling's start.

`verify_feature.py` then applies the table to **every** traced `mo*` object in all 9 segmented
parts:

```
moNode_c prefix decoded on 216/216 candidate objects
distinct tree-flags words:
  0x40000000 n=164
  0x40000140 n=8
  0x400201ca n=2
  0xc0000000 n=39
  0xc0000140 n=2
  0xc00201ca n=1
classes covered: 19
```

**216 of 216 decode**, across 19 classes and both authored and V8-production files, with a
self-consistent name / flags / id / trailing-string sequence in every one. The flags values sort
into four groups:

| flags                       | objects                                                               |
| --------------------------- | --------------------------------------------------------------------- |
| `0x40000000`                | tree folders, `moLengthParameter_c` (164)                             |
| `0xc0000000`                | `moRefPlane_c`, `moProfileFeature_c`, `moOriginProfileFeature_c` (39) |
| `0x40000140` / `0xc0000140` | **boss extrude** (`moExtrusion_c`, `moICE_c`) (10)                    |
| `0x400201ca` / `0xc00201ca` | **cut extrude** (3)                                                   |

Bit `0x80000000` is orthogonal to boss/cut: the authored corpus writes `0x40000140` for a boss and
the two V8 production parts write `0xc0000140` for the same operation, so bit 31 is a per-file or
per-build property, not an operation selector. The low half — `0x0140` boss versus `0x01CA` cut —
is the operation-typed part, exactly as `ANSWERS.md` Q1 concluded, and it now has a class, an
offset and a width: `moNode_c + 0x28`, `u32`.

---

## 2. `moFeature_c` — PARTIAL

Function: `0x4bb8efe0`, 647 decompiled lines. It calls `FUN_4c1d9790` (the `moNode_c` entry) first,
then reads its own fields. The modern read order:

| #   | `this` offset    | width      | archive op                                    | condition                 | confidence |
| --- | ---------------- | ---------- | --------------------------------------------- | ------------------------- | ---------- |
| 0   | —                | —          | `FUN_4c1d9790` → `moNode_c` record above      | always                    | confirmed  |
| 1   | `0x290`          | 4          | `AR_get_long`                                 | always                    | confirmed  |
| 2   | `0x284`          | 4          | `AR_get_long`                                 | ver > `0x184` = 388       | partial    |
| 3   | `0x294`          | 4          | `AR_get_ulong`                                | ver > `0x96` = 150        | partial    |
| 4   | —                | 1          | `AR_get_uchar`                                | ver > `0x139` = 313       | partial    |
| 4'  | `0x1e0`          | string     | `::operator>>` `CStringT`                     | only if #4 != 0           | partial    |
| 5   | `0x2a0`          | 4          | `AR_get_long`                                 | ver > `0x17d` = 381       | partial    |
| 6   | `0x2b0`, `0x2b4` | 4, 4       | `AR_get_long` ×2                              | ver >= `0x1dd` = 477      | partial    |
| 7   | `0x2a8`          | 4          | `AR_get_long`                                 | ver >= `0x2fc` = 764      | partial    |
| 8   | `0x1d8`          | 8          | `AR_get_double`                               | ver > `0x3a9` = 937       | partial    |
| 9   | `0x2ac`          | 4          | `AR_get_long`                                 | ver >= `0x3d6` = 982      | partial    |
| 10  | —                | 4, 4       | `AR_get_long` ×2                              | only if `hasCondition(1)` | partial    |
| 11  | `0x250`          | object     | `::operator>>` `moFolder_c*`                  | ver > `0x401` = 1025      | partial    |
| 12  | `0x1f0`          | string     | `::operator>>` `CStringT`                     | ver > `0x7da` = 2010      | partial    |
| 13  | —                | 1          | `AR_get_uchar`                                | ver >= `0x7e8` = 2024     | partial    |
| 14  | `0x2c0`          | sub-record | `moEntVisProp_c::Serialize`                   | ver > `0x808` = 2056      | partial    |
| 15  | —                | 1          | `AR_get_uchar`                                | `helper + 0x7f0 != 0`     | partial    |
| 16  | `0x2e4`          | 4          | `AR_get_long`                                 | ver > `0x925` = 2341      | partial    |
| 17  | `0xa0`           | 4          | `AR_get_long`                                 | ver > `0x99c` = 2460      | partial    |
| 18  | —                | object     | `::operator>>` `moFeatComment_c*`             | ver > `0xa2a` = 2602      | partial    |
| 19  | —                | 1 + string | `AR_get_uchar`, then a `CStringT` if non-zero | ver < `0xa69` only        | partial    |
| 20  | `0x200`          | 4          | `AR_get_ulong`                                | ver > `0xa68` = 2664      | partial    |
| 21  | `0x2f8`, `0x2f9` | 1, 1       | `AR_get_uchar` ×2                             | ver > `0xaca` = 2762      | partial    |
| 22  | —                | 4          | `AR_get_long`                                 | ver < `0xc50` only        | partial    |
| 23  | —                | 4          | `AR_get_long`                                 | ver > `0xc55` = 3157      | partial    |
| 24  | `0x304`          | 4          | `AR_get_long`                                 | ver > `0xf61` = 3937      | partial    |
| 25  | —                | 4, 4       | `AR_get_long` ×2                              | ver > `0x11cc` = 4556     | partial    |
| 26  | —                | 2          | `AR_get_ushort`                               | ver > `0x11da` = 4570     | partial    |
| 27  | `0x2a4`          | 4          | `AR_get_long`                                 | ver > `0x23fa` = 9210     | partial    |
| 28  | `0x33c`          | 4          | `AR_get_long`                                 | ver > `0x279b` = 10139    | partial    |

Only item 1 is confirmed — it is the `00 00 00 00` at 8345 in the worked example, and it is the
last thing before the next traced object token in every one of the 9 parts. Items 2 onwards fall
inside traced runs the tracer does not subdivide, so nothing independently fixes their order; the
`hasCondition` gates on items 10 and 15 in particular change the length and are not exercised by
any available file.

`moFeature_c + 0x290` is read _before_ any version gate and the reader immediately branches on it
(`if (*(int *)(this + 0x290) == 2) hasCondition(0x80)`), and a value of `0` triggers a legacy
fixup below version `0x3b`. It behaves like a feature-kind or feature-state discriminator. It is
`0` in the traced parts.

## 3. `moModelFeature_c` — PARTIAL

Function: `0x4bb96700`. It is a two-liner:

| #   | `this` offset | width | archive op               | condition            | confidence |
| --- | ------------- | ----- | ------------------------ | -------------------- | ---------- |
| 0   | —             | —     | `moFeature_c::Serialize` | always               | confirmed  |
| 1   | `0x354`       | 4     | `AR_get_long`            | ver > `0xdb2` = 3506 | partial    |

## 4. `FUN_4bb886c0` — the unnamed level between `moBodyFeature_c` and `moModelFeature_c` — PARTIAL

1218 decompiled lines. It calls `moModelFeature_c::Serialize` first, then reads a long, mostly
version-gated sequence. The structurally interesting parts, in read order:

| #   | `this` offset    | kind                                                                              | condition                       |
| --- | ---------------- | --------------------------------------------------------------------------------- | ------------------------------- |
| 1   | —                | two slot-5 sub-records on member objects                                          | ver > `0x392` = 914             |
| 2   | —                | `AR_get_ushort`                                                                   |                                 |
| 3   | `0x3a0`          | `::operator>>` `moIdKeeper_c*`                                                    |                                 |
| 4   | `0x360`, `0x380` | two slot-5 sub-records                                                            |                                 |
| 5   | `0x530`          | `::operator>>` `moAtom_c*`                                                        | ver > `0x487` = 1159            |
| 6   | `0x490`, `0x48c` | `AR_get_int` count then a loop of `AR_get_int`                                    | ver > `0x490` = 1168            |
| 7   | `0x53c`          | `AR_get_int`                                                                      | ver > `0x823` = 2083            |
| 8   | —                | `AR_get_ushort` + slot-5 sub-records, three times                                 | ver > `0x82f`, `0x83b`, `0x842` |
| 9   | `0x4b0`          | `AR_get_int` then `AR_get_ushort` + sub-records                                   | ver > `0x10f8` = 4344           |
| 10  | `0x570`          | `AR_get_int`                                                                      | ver > `0x85f` = 2143            |
| 11  | `0x3c8`          | `::operator>>` `moPMarkRecord_c*`, wrapped by `AR_get_int`s into `0x3c0`, `0x578` | ver > `0x8dd` = 2269            |
| 12  | `0x5c8`          | `AR_get_int`                                                                      | ver >= `0x8f3` = 2291           |
| 13  | —                | three `AR_get_int`                                                                | ver > `0x91a` = 2330            |

This is the level that owns the `moIdKeeper_c`, the `moAtom_c` and the int array — i.e. the
feature's persistent-id bookkeeping. It is the bulk of the traced 49/30/52-byte runs and of the
707/873-byte runs. It is **partial**: the field list is transcribed but the run-by-run
reconciliation against the traced spans was not completed, because the tracer does not subdivide
those runs and the branch count (`hasCondition` on `1`, `0x2000`, `0x400000`) is high enough that
several orderings fit the same byte count.

---

## 5. What this means for a from-scratch feature writer

- The feature's **name**, **tree-flags word** and **feature id** are all in the first ~30 bytes of
  the record and are now fully specified, including the two flag fixups. A writer can set the
  operation type (`0x0140` boss / `0x01CA` cut) and the id without a donor.

* The historical field study stopped after `moFeature_c + 0x290`; flipping the flags word alone
  still leaves the derived face-identity records (`moEndFaceSurfIdRep_c`,
  `moFromSktEntSurfIdRep_c`, the `moFR_c` id words) describing the wrong faces. Subsequent
  family-specific programs in `../archive/MULTISTREAM.md` construct those regions from typed fields.
  Families without a complete program are rejected; no region is borrowed from a donor.
