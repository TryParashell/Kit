<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# The `sg*` handle and constraint classes, recovered from the code

Source: Ghidra 12.1.2 headless decompilation of `sldmodu.dll` from the licensed SOLIDWORKS 2025
install, read out of `out/sldmodu_serialize.c` after `RenameArchiveApi.java` had renamed every
`su_CArchive::operator>>` overload, so every width below is the width the archive actually reads.
No SOLIDWORKS process, no COM, no debugger. `re/tooling/ghidra/Setup.md` has the commands.

Byte evidence comes from the nine recorded segmentations in `re/data/segments/segments_*.json` and
the corresponding `Contents/Config-0-ResolvedFeatures` streams.
`re/tooling/ghidra/Validation/VerifyClassLayouts.py` replays the declared layout in
`re/data/Layouts/ClassLayoutsDecompiled.json` against every instance in all nine.

Confidence vocabulary is the one `Serialize.md` uses: **confirmed** = read out of the decompiled
`Serialize` _and_ the byte arithmetic reproduces a real traced span exactly; **partial** = read out
of the decompiler but nothing available pins it; **not found** = not recovered.

---

## 0. The one structural correction this document makes

`re/solidworks/archive/Segmentation.md`-style traces attribute each object read to the stack frame
that was active when the read happened. For the `sg*` handle classes that attribution is **wrong**,
and it is the direct cause of the 43 `sgLineHandle@end` and 40 `sgLLDist@end` conflicts that
`re/tooling/ghidra/Generation/SolveRuns.py` reports.

`sgEntHandle::Serialize` (`0x4c5c91a0`) is the slot-5 serialiser of `sgLineHandle`,
`sgArcHandle`, `sgPointHandle`, `sgEntHandle` and sixteen further classes — `SerializeMap.json`
lists twenty in total. On every file version in play (13000, 14000, 18000) it reads **three
scalars and no objects at all**. So every traced "child" of a `sgLineHandle` node is a read that
happened _after_ `sgEntHandle::Serialize` returned, at a stack depth the tracer could not
distinguish from deeper. 103 of the 232 traced `sgLineHandle` instances, 14 of 39 `sgPointHandle`,
6 of 30 `sgArcHandle` and 2 of 8 `sgEntHandle` carry such phantom children.

The consequence for segmentation is the useful part: these classes are **fixed-length leaves**, and
the solver's per-slot run keys for them (48 of them for `sgLineHandle` alone) are artefacts that
must be discarded, not modelled. `ClassLayoutsDecompiled.json` declares
`"child_slots": []` for all four, which is what makes them close.

---

## 1. `sgEntHandle` — the shared base record — CONFIRMED for the fields, PARTIAL for the total

Function: `sldmodu.dll` `0x4c5c91a0`. The store branch names all three fields with a `su_DBKey`,
so the names are authoritative rather than inferred:

```c
CStringT(&local_res18, "EntIndex");
if (*(uint *)(this + 0x18) < 0x777f) { AR_put_ushort(ar, *(ushort *)(this + 0x18)); }
else { AR_put_ushort(ar, 0x777f); ... AR_put_long(ar, *(long *)(this + 0x18)); }
CStringT(&local_res18, "RefId");   AR_put_long(ar, *(long *)(this + 0x1c));
CStringT(&local_res18, "DimOnCM"); AR_put_long(ar, *(long *)(this + 8));
```

| #   | offset in body | `this` offset | width | archive op                                | name               | role     | confidence |
| --- | -------------- | ------------- | ----- | ----------------------------------------- | ------------------ | -------- | ---------- |
| 1   | `+0`           | `0x18`        | 2     | `AR_get_ushort`                           | `EntIndex`         | authored | confirmed  |
| 2   | `+2`           | `0x18`        | 4     | `AR_get_long`, **only if #1 == `0x777f`** | `EntIndex` escaped | authored | confirmed  |
| 3   | `+2` / `+6`    | `0x1c`        | 4     | `AR_get_long`                             | `RefId`            | authored | confirmed  |
| 4   | `+6` / `+10`   | `0x08`        | 4     | `AR_get_long`                             | `DimOnCM`          | derived  | confirmed  |

So the record is **10 bytes normally and 14 bytes when the index escapes**. That is the whole
record; `su_CObject::Serialize` at the top contributes nothing.

### Version gates

| gate                          | effect                                                                    |
| ----------------------------- | ------------------------------------------------------------------------- |
| `ver < 0x5b` (91)             | a legacy pre-amble that also demands the object pointer read back as null |
| `ver < 0x77e` (1918)          | a bare `u16` with no `su_DBKey`, and the record may end after it          |
| `0x77e <= ver < 0xa84` (2692) | `EntIndex` is sign-extended from `i16` unless it is in `[-99, -37]`       |
| `ver >= 0xa84`                | `EntIndex` is a plain `u16`                                               |
| `ver < 0x17d7` (6103)         | `DimOnCM` is not read; the record is 6 or 10 bytes                        |

All corpus versions are above every gate, so the modern three-field form is the only one the corpus
exercises. The legacy widths are recorded here so a reader of a 13000-era file does not have to
rediscover them; they are **partial** because nothing on disk exercises them.

### The escape, measured

Across all nine traces the sentinel `0x777f` appears in the first two bytes of a handle body in
**exactly the 8 `sgEntHandle` instances and in none of the 232 `sgLineHandle`, 39 `sgPointHandle`
or 30 `sgArcHandle` instances**. Those 8 all carry `EntIndex = -2`.

`sgEntHandle` itself is therefore recorded as `partial`: its record is 14 bytes by the code, and
every traced instance is consistent with 14, but the smallest distance from a body start to the
next traced object is 46 bytes, so no instance pins the total. `ClassLayoutsDecompiled.json`
expresses this as a `conditional` variable run rather than a constant.

---

## 2. `sgLineHandle`, `sgArcHandle`, `sgPointHandle` — CONFIRMED, 10 bytes

All three inherit `sgEntHandle::Serialize` unchanged — `SerializeMap.json` gives the same slot-5
address for all of them — and none of the 301 traced instances takes the escape. The body is
therefore the fixed 10-byte `EntIndex` / `RefId` / `DimOnCM` triple.

| class           | traced instances | instances whose body ends exactly on the next traced object | body overruns |
| --------------- | ---------------- | ----------------------------------------------------------- | ------------- |
| `sgLineHandle`  | 232              | 105                                                         | 0             |
| `sgArcHandle`   | 30               | 22                                                          | 0             |
| `sgPointHandle` | 39               | 12                                                          | 0             |

Not one of the 301 instances has less than 10 bytes before the next traced object, and 139 of them
have exactly 10. That is what upgrades 10 from "what the decompiler says" to confirmed.

`SolveRuns.py` derives `sgPointHandle@leaf = 2` with 114 witnesses. **That value is wrong.** It
comes from propagating through the phantom-child structure of §0; the 12 instances whose next
traced object sits exactly 10 bytes past the body start rule it out.

`RefId` is the sketch-relative reference id and `DimOnCM` is `0` in every corpus instance and is
recomputed by the reader when the handle is attached to a dimension, so it is labelled `derived`.
`EntIndex` is the authored payload: this is the confirmation, from the write branch, of the earlier
finding that **lines and arcs store point-handle indices, not coordinates** — a `sgLineHandle`
body has room for nothing else.

---

## 3. `sgLLDist` — PARTIAL, and there is no constraint-list count field

Function: `sldmodu.dll` `0x4c5e0090`. Read order, with the gates:

| #   | width / kind | condition               | `this` offset | name                                             | role     | confidence            |
| --- | ------------ | ----------------------- | ------------- | ------------------------------------------------ | -------- | --------------------- |
| 0   | base         | always                  | —             | `FUN_4c5dfab0` (the `sgDim` chain)               | —        | not found             |
| 1   | object       | always                  | `0x130`       | `ReadObject(sgEntHandle)` — `Entity0`            | authored | confirmed             |
| 2   | object       | always                  | `0x158`       | `ReadObject(sgEntHandle)` — `Entity1`            | authored | confirmed             |
| 3   | 2            | ver >= `0xc9`           | `0x180`       | `ArcDimType0`                                    | authored | confirmed             |
| 4   | 2            | ver >= `0xc9`           | `0x184`       | `ArcDimType1`                                    | authored | confirmed             |
| 5   | 2            | ver > `0x2dc`           | `0x1b8`       | `Quadrant`                                       | authored | confirmed             |
| 6   | 2            | ver > `0x760`           | `0x1bc`       | `Chamfer`                                        | authored | confirmed             |
| 7   | object       | ver > `0x10a4`          | `0x1e0`       | `ReadObject(sg3DPlaneHandle)` — `ActivePlane`    | authored | confirmed             |
| 8   | 24           | ver > `0x1c27`          | `0x1c8`       | `mgVector_c::restore` — `Direction`, three `f64` | derived  | confirmed             |
| 9   | 2            | `0x2f79 < ver < 0x2fa0` | —             | a discarded `u16`                                | —        | partial (never taken) |

Fields 3 to 6 are named by the `su_DBKey` writes in the store branch (`ArcDimType0`,
`ArcDimType1`, `Quadrant`, `Chamfer`, `ActivePlane`, `Direction`).

Against the traces this closes almost exactly. In the four six-child instances the measured runs
are `lead = 4`, `@1 = 16`, `@2 = 14`, `@3 = 0`, `@4 = 8`, `@5 = 24`, and:

- `@3 = 0` is the gap between the two `sgEntHandle` reads — the code reads them back to back.
- `@4 = 8` is exactly `ArcDimType0 + ArcDimType1 + Quadrant + Chamfer`.
- `@5 = 24` is exactly `mgVector_c::restore`, and it lands **on the traced `scope_end`**, so the
  six-child form tiles with zero residual.

What is still open is `@0`, the run between the `moLengthParameter_c` dimension object and the next
base-class object. It is not variable — it is unmeasured, because `moLengthParameter_c`'s own body
end has no witness in any trace. Closing it needs `moParameter_c::Serialize`, the base called from
`moLengthParameter_c::Serialize` at `0x4c1d9b70` as `FUN_4c1dbf20`.

### The specific negative result about the count field

**There is no count-driven constraint list in `sgLLDist`.** The 40 `sgLLDist@end` conflicts that
`SolveRuns.py` reports are the same trace-attribution artefact as §0. One instance,
`vendor_ring` node 637, carries **twelve** traced children instead of six: five extra
`sgLineHandle` classrefs and one `suObArray` classref appear after the `ActivePlane` slot.
`FUN_4c5e0090` reads nothing after `mgVector_c::restore`, so those six objects are not
`sgLLDist`'s. `VerifyClassLayouts.py` reports exactly one mismatch across all nine traces and it
is this instance's `@5`, where the trace-implied run is 72 rather than the 24 the code reads —
48 bytes of a caller's frame absorbed into the run because the following object is not a sibling.

So the answer to "where does the constraint-list count field live" is: not in `sgLLDist`, and not
in `sgLineHandle`. Both are fixed-length in their own right. The list belongs to the caller, and
for the sketch that caller is `sgSketch`, whose entity count is the `u16` at the start of its own
49-byte lead run (§4), and the `suObList` inside `moSketchRegion_c`
(`re/solidworks/records/FeatureBody.md` §3), whose count is a `u16` at the start of the list
object's own body.

---

## 4. `sgSketch` — PARTIAL

Function: `sldmodu.dll` `0x4c5d28c0`, 182 KB of decompiled C — the largest `Serialize` in the
corpus and the only one in this document that has not been read end to end.

Measured, across all 24 traced instances:

| run         | value           | instances | confidence |
| ----------- | --------------- | --------- | ---------- |
| `lead`      | 49              | 24 / 24   | confirmed  |
| `@0`        | 8               | 24 / 24   | confirmed  |
| `@1`        | 39              | 24 / 24   | confirmed  |
| `@2`        | 0               | 24 / 24   | confirmed  |
| `@3` onward | the entity list | —         | opaque     |

Child counts observed are 5, 10, 12, 13, 22 and 26. From slot 3 onward the structure is a
**repeating pair**: a handle object, then a run of 0, then a second handle object, then a payload
run. Reading the four line entities of the rectangular sketches gives exactly four such pairs
(`0, 138, 0, 138, 0, 138, 0`), which is the strongest independent corroboration of the 10-byte
handle body in §2 — the alternation only comes out constant if each handle is exactly 10 bytes.

### The entity count, and where it lives — CONFIRMED

**The `u16` at `lead + 0` is the entity count.** It equals the number of traced entity pairs in
**24 of 24 instances**:

| file / node            | `u16` at `lead+0` | traced children | leading pair-free children | trailing list / chain children | pairs |
| ---------------------- | ----------------- | --------------- | -------------------------- | ------------------------------ | ----- |
| every origin sketch    | 1                 | 5               | 2                          | 1                              | 1     |
| `circle` node 156      | 3                 | 10              | 2                          | 2                              | 3     |
| every rectangle sketch | 4                 | 12              | 2                          | 2                              | 4     |
| `vendor_ring` node 166 | 4                 | 13              | 2                          | 3                              | 4     |

That is the count field the `sg*` work needed, and it is in `sgSketch`, not in `sgLineHandle` and
not in `sgLLDist`.

It is still **not enough to segment**, and the layout keeps `@3` onward `opaque` for that reason:
the per-entity payload is 138 bytes for a line but 360, 461, 507, 968, 1075, 6016 and 6622 bytes
were also measured, so there is no stride. Knowing how many entities there are does not tell you
how long each one is. The 18-byte fixed prefix (`double 1.0`, `double 0.0`, `u16 30`), the
`double x` / `double y` pair in metres and the `<u8 role> 00 <u8 class> 00` trailer already recorded
for 2-D sketch coordinates account for 38 of the 138, and the remainder is not resolved.
`sgSketch::Serialize` at `0x4c5d28c0` is the single specific next step.

---

## 5. Negative results

- **`sgEntHandle::Serialize` reads no objects on any modern version.** Every traced child of a
  `sgLineHandle`, `sgArcHandle`, `sgPointHandle` or `sgEntHandle` node is a mis-attribution. Any
  model that gives these classes child slots will mis-segment.
- **`sgLineHandle`'s variable traced spans are not caused by the `EntIndex` escape.**
  `Serialize.md` §6 attributes the 12 / 16 / 99-byte spans to the `0x777f` escape. Measured: the
  escape occurs in 0 of 232 `sgLineHandle` instances. The spans vary because the traced scope of a
  handle absorbs its ancestors' trailing runs, not because the record varies.
- **`SolveRuns.py`'s `sgPointHandle@leaf = 2` is wrong**; the record is 10 bytes.
- **`sgLLDist` has no count field and no repeating slot.** Its six-child form is fixed and tiles
  exactly; its one twelve-child instance is an artefact.
- **No `sgLineHandle` or `sgArcHandle` body contains a coordinate, an angle or a radius.** A
  10-byte body has no room for one. A full circle and an arc use the same 10-byte handle record.
- `moSketchRegion_c`'s boundary list stores `sgEntHandle` objects at 12 bytes each — a 2-byte
  classref token plus the 10-byte body — with a `u16` count in front. That is the only place in
  the sketch records where a handle count is written down.
- The revolve-angle result recorded in `Serialize.md` §3 is unaffected by anything here: there is
  still no angle scalar in a modern `moRevEndSpec_c`, and `getAngle` still returns the literal
  `6.2831853071796` through a null dimension pointer.

---

## 6. Evidence

```
class                    claim      inst  comp exact unres runchk  runX  over
sgArcHandle              confirmed    30    30    22     0      0     0     0
sgEntHandle              partial       8     8     0     0      0     0     0
sgLLDist                 partial       5     0     0     5     26     1     0
sgLineHandle             confirmed   232   232   105     0      0     0     0
sgPointHandle            confirmed    39    39    12     0      0     0     0
sgSketch                 partial      24     0     0    24     96     0     0
MISMATCH sgLLDist               vendor_ring      node=637  run=5    expected=20231  computed=20183
```

`inst` is instances found across the nine traces, `comp` instances whose body length the layout
computes, `exact` instances whose computed body end falls exactly on the next traced object or on
the traced `scope_end`, `runchk` individual run boundaries predicted and compared against a
recorded object offset, `runX` those that disagreed, `over` computed bodies that ran past their
bound. Reproduce with:

```powershell
uv run python re/tooling/ghidra/Validation/VerifyClassLayouts.py
```
