<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Version-gated and absorption-hidden runs

PARA-417. This records the per-class serialized field layouts recovered for the classes that carried
an `opaque` run in `re/data/Layouts/ClassLayouts.json` and therefore made the static walk of
`Contents/Config-0-ResolvedFeatures` refuse. Everything here is static reverse engineering out of
the already-decompiled bodies, checked against the nine recorded segmentations in
`re/data/segments/` and the 32 donor fixtures under `tests/fixtures/solidworks/donors/`. The
machine-readable result is `re/data/Layouts/ClassLayoutsVersioned.json`, which
`re/tooling/ghidra/Generation/GenClassLayouts.py` merges after `ClassLayoutsDecompiled.json` and before the
pinned external classes.

## 1. What was actually blocking the walk

`re/tooling/harness/SegmentFixtures.py` names the run that stops each donor. Before this work, with
the shipped table:

```
donors=32 segmented=0 tiled=0 identical=0
  blocked by moNotesAreaFtrFolder_c@4               23
  blocked by moHistoryFolder_c@5                     6
  blocked by external#42@lead                        2
  blocked by moHistoryFolder_c@13                    1
```

That is not the order the task brief predicted, because the parallel `moCompFeature_c` fix had
already moved the wall forward. `moNotesAreaFtrFolder_c@4` was the single run holding 23 of the 32
donors. Closing it exposed `moDefaultRefPlnData_c@0`, which held the same 23. Closing that exposed
`sgSketch@lead`, which is where those 23 now stop:

```
donors=32 segmented=0 tiled=0 identical=0
  blocked by sgSketch@lead                          23
  blocked by moHistoryFolder_c@5                     6
  blocked by external#42@lead                        2
  blocked by moHistoryFolder_c@13                    1
```

So 23 donors advanced past two whole classes and now refuse for a reason this task cannot close
(section 6). The other three blockers are untouched and are not opaque runs at all: two are class-map
accounting divergences inside `moHistoryFolder_c` and one is a missing external-class entry.

## 2. The absorption caveat, restated as arithmetic

`re/solidworks/archive/ExternalClasses.md` section 3 says a traced row's length is the distance to
the next `ReadObject`, so an object that is the last read in its parent's frame absorbs everything
the ancestors read afterwards. `GenClassLayouts.py` makes that concrete: its `TilingSolver` seeds
every object's end with `record_ends`, the offset of the first segment after the object's whole
subtree. That is a correct tiling, but it attributes all trailing bytes to the deepest
last-descendant chain. When the same class appears once as that deepest descendant and once higher
up, the solver sees two different values for the same run key and gives up, writing `opaque`.

Two of the classes here are exactly that shape and needed no new information beyond the decompiled
read order (sections 3.1 and 3.2). Four more close once the child body is measured by its own
`Serialize` rather than by `record_ends` (sections 3.3, 4.2, 4.3, 5.1). Only three runs in the whole
set turned out to be genuinely version gated (section 4).

## 3. Runs closed from the decompiled read order

### 3.1 `moNotesAreaFtrFolder_c` run 4 = 16 — confirmed

`SerializeMap.json` points slot 5 of the vftable at `sldmodu.dll 0x4c280660`,
`moFtrFolder_c::Serialize`. Reading path, in order:

| read                                        | bytes                  | gate                                    |
| ------------------------------------------- | ---------------------- | --------------------------------------- |
| `moFolder_c::Serialize`                     | children and runs 0..3 | none                                    |
| virtual slot `0x1270`                       | 0                      | none                                    |
| `su_CArchive::ReadObject` into `this+0x380` | object slot 4          | none                                    |
| `AR_get_long` `this+0x374`                  | 4                      | none                                    |
| `AR_get_long` `this+0x38c`                  | 4                      | `ver > 0xf61`                           |
| `AR_get_long` `this+0x370`                  | 4                      | virtual slot `0xa28` and `ver > 0x23b9` |
| `AR_get_long` `this+0x394`                  | 4                      | `ver > 0x279b`                          |

`0xf61 = 3937`, `0x23b9 = 9145`, `0x279b = 10139`. Every gate is open at both 14000 and 18000, so the
post-child run is a flat 16 in both generations. No `runs_by_version` entry is needed, and one would
have been wrong.

The arithmetic. Every one of the nine traces carries the same pair: an outer definition and the
nested classref that outer reads in its own slot 4. In `baseline` the outer's own tag ends at 1612,
its slot-4 child tag sits at 1779, the inner body starts at 1781, the inner's slot-4 object reference
ends at 1976, and both rows report `scope_end` 2008. `SolveRuns.py` therefore reports run 4 as 32
for the inner and 0 for the outer, which is the 9x0 and 9x32 the shipped table records. With run 4 =
16 the inner ends at 1992, the outer's slot-4 subtree ends there, the outer ends at 1992 + 16 = 2008,
and 2008 is exactly where the grandparent's next object read begins (`baseline` node 54). 16 is the
only value that satisfies both frames simultaneously, and it holds in all nine traces.

### 3.2 `moDefaultRefPlnData_c` — confirmed, and the one-byte bug that blocked 23 donors

`moDefaultRefPlnData_c::Serialize` is `0x4c2d1cf0`: `su_CObject::Serialize` and then a tail-jump
through virtual slot `0x150`. That slot is index 42 of the `moDefaultRefPlnData_c` vftable at
`4d15a770`, which is `FUN_4c2d6070`. **That function was absent from every dump on disk**
(`sldmodu_serialize.c`, `para417_serialize.c`, `task2.c`, `config0_serialize.c`, `sldmodu.c` and the
rest), so it was recovered with one headless `DumpFunctions` pass over `proj_sldmodu` at depth 1.
That is the only sldmodu function this task had to dump.

Reading path:

| read                                            | bytes         | gate                                               |
| ----------------------------------------------- | ------------- | -------------------------------------------------- |
| `mgPoint_c::restore` root point                 | 24            | none                                               |
| `mgVector_c::restore` normal                    | 24            | none                                               |
| `mgXform_c::restore`                            | 34 or 106     | none                                               |
| four border doubles                             | 32            | `ver >= 0x160`                                     |
| `ReadObject moCompEdge_c`                       | object slot 0 | none                                               |
| `AR_get_long` x3 into `+0x50`, `+0x54`, `+0x58` | 12            | none                                               |
| `AR_get_uchar`                                  | 1             | `ver > 0xe5`                                       |
| `mgPoint_c::restore` display root point         | 24            | `IsKindOf moDefaultRefPlnData_c` and `ver > 0x81d` |
| `AR_get_long` `+0x5c`                           | 4             | `ver > 0xe24`                                      |
| `AR_get_long` `+0x60`                           | 4             | `ver > 0x10da`                                     |
| `AR_get_ushort` `+0x64`                         | 2             | `ver > 0x17dd`                                     |
| `ReadObject moCompFaceMeshFacetFin_c`           | object slot 1 | `ver > 0x2b83`                                     |
| `ReadObject moRefAxis_c`                        | object slot 2 | `ver > 0x2ba5`                                     |
| `ReadObject moCompSketchEntHandle_c`            | object slot 3 | `ver > 0x2ba5`                                     |

Run 0 is therefore `12 + 1 + 24 + 4 + 4 + 2 = 47`, which is exactly the constant `SolveRuns.py`
already had. That agreement is the cross-check that the read order is right.

`mgXform_c::restore` was read off the bytes, not from a decompiled body. In `baseline` node 95 the
root point is `(0,0,0)`, the normal is `(0,0,1)`, the u8 at +48 is 0, a 24-byte translation follows,
then a `1.0` double, then one more u8, then the four border doubles ending at +114. In node 108 the
normal is `(0,1,0)`, the u8 at +48 is 1, nine doubles follow at +49 giving the row-major basis
`(1,0,0),(0,0,1),(0,-1,0)`, then the same translation, scale, u8 and four doubles, ending at +186. So
`mgXform_c::restore` reads `1 + [72] + 24 + 8 + 1`, and the lead is `48 + 1 + 72*flag + 65`.

Highest gate in the whole body is `0x2ba5 = 11173`, open at both 14000 and 18000. This class needs no
`runs_by_version`; below 11173 slots 2 and 3 would disappear entirely, which is a shape change rather
than a length change.

Two corrections come out of this.

**Four object slots, not three.** The trace records three children and two spare bytes. Those two
bytes are the fourth `ReadObject`, recorded by the tracer as a depth-3 null nested under the third
rather than as a fourth sibling — `baseline` node 99 at offset 3765, parent node 98. That misplacement
is why `SolveRuns.py` leaves the last run variable. Declaring four slots with runs 1, 2 and 3 all
zero makes the body end land exactly on the parent's `scope_end` in all 27 traced instances.

**The lead rule was one byte short under the shipped segmenter.** The entry in
`ClassLayoutsDecompiled.json` uses a `conditional` rule with `at = 48`, `predicate_at = 0`,
`predicate_width = 1`, `width = 72`, `tail = 65`. `VerifyClassLayouts.py` adds `predicate_width` to
the run length and gets 114 and 186, which are correct. `_element_length` in
`src/convert/adapters/solidworks/container/Archive.py` returns `element.at + present + element.tail` and does
not add `predicate_width`, so it gets 113 and 185. In donor `arcboss_cut_cut_cut_through` the class
definition tag sits at 4285, the header is 27, the body starts at 4312 and the lead ends at 4426; the
segmenter read its next tag at 4425, one byte early, and reported
`object reference 191 is at or above the base 112 but no such object has been seen`. That single byte
was the wall for 23 of the 32 donors.

The fix used here avoids the disagreement rather than picking a side: the u8 is expressed as a `count`
rule, `at = 48`, `count_width = 1`, `stride = 72`, `tail = 65`. `count` is implemented identically in
both tools (`at + count_width + stride*count + tail`), the flag is only ever 0 or 1, and the result is
114 or 186 in both.

### 3.3 `moCStringHandle_c` leaf = string — confirmed

`moCStringHandle_c` has no entry in `SerializeMap.json` because the class is not in sldmodu. Its
vftable is `sldmfcu.dll 0x3cf1e270` and slot 5 is `FUN_3ca867b0`, which was also absent from every
dump and was recovered with one headless pass over `proj_sldmfcu`. The body is
`su_CObject::Serialize`, which reads nothing, then exactly one
`operator>>(su_CArchive&, CStringT<wchar_t>&)` into `this+0x08`, then a store of the literal 1 into
`this+0x10` that touches no bytes.

So the leaf is the string and nothing else. Decoding `ff fe ff <u8 units>` at the 18 traced heads
gives 4, 4, 4, 4, 4, 4, 4, 14, 16, 32, 38, 208, 214 and so on. In the 9 instances that sit in a
non-final slot of `moExtObject_c` the traced span equals the decoded string length exactly. The 9 in
the final slot measure 79, 87, 87, 87, 97 bytes longer, and those bytes are read by `moExtObject_c`,
`moFR_c` and the enclosing `moFromSktEntSurfIdRep_c` or `moEndFaceSurfIdRep_c` frames after this
object returns. Declaring the string rule also made `moExtObject_c` computable for the first time,
9 instances, with no mismatch.

### 3.4 `moPointBackedUpData_c` leaf = 24, and `moArcBackedUpData_c` run 1 = 12

`moPointBackedUpData_c::Serialize` is `0x4c2cfbb0`: `su_CObject::Serialize` and one
`operator>>(su_CArchive&, mgPoint_c&)` into `this+0x08`, three f64.

24 is witnessed, not merely bounded. In both traced `moArcBackedUpData_c` instances the first and
third point sit in a non-final slot and their tag-to-next-tag distance is exactly `2 + 24`. The
second also sits in a non-final slot and measures `2 + 24 + 12`; those 12 bytes are
`moArcBackedUpData_c` run 1, not part of the point. That is the 24x6 / 36x2 the shipped table
records.

`moArcBackedUpData_c` is declared here only as the other half of that result, and only as `partial`.
Its `Serialize` is `0x4c2c8230`, which reads one i32 then `ReadObject` of
`moPointBackedUpData_c`, `moPointBackedUpData_c`, `moLineBackedUpData_c`, `moLineBackedUpData_c`,
`moPointBackedUpData_c` — five objects preceded by four bytes — while the trace records seven object
slots and a zero lead. The extra slots and the placement of the i32 must come from the unreconciled
base `FUN_4c2d2fb0`, so the runs recorded are the arithmetic that tiles rather than a read-by-read
transcription. With them the class tiles to 98 bytes, exactly the traced `scope_end` of both
instances in `vendor_ring`.

## 4. The runs that really are version gated

Three runs, and only three, split cleanly on the document generation. The corpus carries two:
`_MO_VERSION_18000` in the seven authored parts and `_MO_VERSION_14000` in the two V8 vendor parts.

`runs_by_version` is written in the shape the shipped `ClassLayout` implements, run key first and
then exact document version:

```json
"runs_by_version": { "0": { "14000": 78, "18000": 82 } }
```

`re/solidworks/records/LayoutSchema.md` still describes the older gate-first shape with
greatest-key-below-V fallthrough; the code in `src/convert/adapters/solidworks/container/Archive.py` takes an
exact version match and falls back to `runs`. The entries here follow the code, and where a
generation is genuinely unresolved its version is deliberately left out so the segmenter refuses with
the version named instead of taking the other era's constant.

### 4.1 `moFeatureDimHandle_c` run 0 = 78 at 14000, 82 at 18000 — partial

`moModDimHandle_c::Serialize` at `0x4c86e240` contributes only the final `ReadObject` in slot 5;
everything before it is the base `FUN_4c864440`. Run 0 measures 82 bytes in all ten instances carried
by 18000-era parts and 78 in both instances carried by 14000-era parts, with neither value appearing
in the other generation. The 4-byte difference is a gate inside that base. It is declared as
`runs_by_version` and not as a positional `conditional`, because a predicate for a length difference
that sits inside the run being measured would have to be located at an offset that itself depends on
the answer. Slot 5 is still unwitnessed, so the class stays `partial`.

### 4.2 `moSketchExtRef_w` run 1 = 54 at 14000, 58 at 18000 — partial

The existing note reads the traced spans as "54 bytes in 4 of 5 traced instances and 58 in circle
node 166", which looks like an outlier. Grouping the same five instances by container generation
instead makes the split clean: every 14000-era instance measures 54 and every 18000-era instance
measures 58. `moSketchExtRef_w::Serialize` at `0x4c2d40f0` contributes only the u16 at `this+0xa8` to
this run; the rest is the base `FUN_4c2d2290`, where the gate sits. Five instances and a single
generation-crossing pair is thin evidence, hence `partial`. Slots 0 and 2 remain opaque.

### 4.3 `moCompRefPlane_c` run 0 = 85 at 14000, 89 at 18000 — partial

`FUN_4bc22e00` is the base `FUN_4bc22cb0` followed by one i32 into `this+0x100` for `ver > 0x4bb`.
For `ver >= 0x2d1` that base is `moCompFeature_c::Serialize` at `0x4bc222f0` followed by a single
`operator>>(moRefGeom_c**)`, which is exactly the two object slots the trace records. Run 0 is
therefore `moCompFeature_c`'s own post-child run and it inherits that class's gate.

With the `moUnitComponent_c` classref in slot 0 pinned to its own 4-byte subtree from
`ExternalClasses.json`, run 0 measures 89 in all 17 instances carried by 18000-era parts and 85 in
all 5 carried by 14000-era parts. The generated table records run 0 as 0 because `SolveRuns.py` lets
that classref absorb the bytes, and that is what produced the 22 run mismatches
`VerifyClassLayouts.py` reports for this class against the merged table. Declaring the gate removes
all 22.

Run 1 stays opaque: 42 bytes in 21 of 22 instances and 114 in `planetop` node 211. Slot 1 is not the
last child of the enclosing `moProfileFeature_c` there, so 114 is a hard witness rather than
absorption, and the 72-byte difference is real and unexplained.

### 4.4 The gate that was not a gate: `moICE_c` run 7

Measured the way `SolveRuns.py` measures it, `moICE_c` run 7 comes out 18 bytes in the three
18000-era instances and 22 in the single 14000-era instance in `vendor_ring`. That is a textbook
invitation to write `runs_by_version`, and it was written that way first.

It is wrong. Replaying the layout with the surface-id `suObArray` in slot 7 pinned to its own body
length from `ExternalClasses.json`, as `external#103` and `external#104`, moves 34 bytes back into
the run at 18000 and 30 at 14000, and both land on **52**. The apparent 4-byte generation difference
was an artefact of where the child body ended, and the gate would have been wrong in both eras. Run 7
is declared as a flat constant 52.

The cross-check is `moExtrusion_c`, which shares vftable slot 5 with `moICE_c`
(`0x4bb8eba0`): its own post-surface-id run 6 is also a flat 52 in all nine traced instances and in
both generations. This is the one place where the task's brief was actively misleading, and it is
worth recording as a method note: before declaring a gate, re-measure the run with every child pinned
to its own decompiled body length. A difference that survives that is a gate; a difference that does
not was never in the code.

## 5. Runs closed by re-measuring against pinned child bodies

### 5.1 `moExtrusion_c` runs 0 = 4 and 6 = 52 — partial

Two of the four opaque runs close. With the classref in slot 0 pinned to `external#4` and the
surface-id array in slot 6 pinned to its own body length, run 0 is a flat 4 in all nine traced
instances and run 6 a flat 52, in both generations.

Runs 5 and 8 stay opaque and are not version gated:

- Run 5 measures 587, 705 x3, 707 x3 at 18000 and 1063 and 1161 at 14000. The 18000 side alone spans
  587 to 707, so no version mapping can close it. This is the `moModelFeature_c` and `moFeature_c`
  portion of the base chain; `moBodyFeature_c::Serialize` is `0x4bb8aa10` and its own base is
  `FUN_4bb886c0`, neither reconciled.
- Run 8 is the last slot, holding `moEndSpec_c`, whose own last slot holds `moFromEndSpec_c`. See
  section 6.3.

### 5.2 `moDisplayDistanceDim_c` run 11 = 0 and run 17 = 4 at 18000 — partial

Two of the three opaque runs close. Run 11 is a flat 0 in all 14 traced instances. Run 17 is the last
slot and measures 4 bytes in all ten instances carried by 18000-era parts; the four 14000-era
instances split 0, 0, 0 and 170, so that generation is genuinely unresolved and 14000 is left out of
the mapping on purpose. Run 6 stays opaque: it resolves to 244 bytes in the two `vendor_cojinete`
instances and has no witness in the other twelve, and one value from one part is not enough.

## 6. Negative results

These are real findings. Each is a class that stayed opaque, with the reason.

### 6.1 `sgSketch` — six counted child groups are encoded, the incomplete tail is guarded

`sgSketch::Serialize` is `0x4c5d28c0`, 182 KB of decompiled C. The old single-repeat model was the
wrong abstraction: the serializer carries an ordered sequence of separately counted entity, point,
relation, constraint, list and chain groups. `ClassLayout.groups` now represents those six loops,
including per-generation relation widths and group trailers. Twenty fully bounded traced instances
land on every recorded child offset with no residual.

Four traces let their last nested child absorb unrecovered sketch payload. A terminal guard now
checks the next parent token against the directly witnessed null and vendor class-reference values
without consuming it. Unknown values refuse at `sgSketch@tail` instead of drifting the class map.
Three donor fixtures still stop earlier at `sgSketch@0`; one additional fixture stops at that guarded
tail. The remaining work is therefore specific child-body ownership, not the former inability to
express the serializer's counted loops.

### 6.2 `moFR_c` — CLOSED at 8 wire bytes

`FUN_4bbb1a00` reads `su_CObject::Serialize`, then `operator>>(moExtObject_c**)`, which is the single
traced child, then for `ver >= 0x2cb` calls `FUN_4bbb16e0`, which at both 14000 and 18000 reads only
an i32 and a `su_CTime`. The bytes confirm the pair: at `baseline` offset 8591 the i32 is 32 and the
next dword is `0x6a709324`, a plausible Unix timestamp. So `moFR_c` reads 8 bytes after its child.

`swccu.dll` `0x31eeb5b0` proves that the eight-byte in-memory `su_CTime` writes one `u32`, so the
wire record is one i32 reference id plus one u32 time: exactly 8 bytes at both represented
generations. The enclosing surface-id records now own their 12-, 16- and 20-byte tails separately,
and `moExtObject_c` owns its strings and version-gated remainder. `moFR_c@0 = 8` is therefore
confirmed rather than context-dependent.

### 6.3 `moFromEndSpec_c` — type zero and its enclosing tails are CLOSED

`FUN_4bb900d0` reads `su_CObject::Serialize`, then an i32 type. For type 1 or 2 it reads one object
and returns. For type 3, 4 or 5 it continues; type 5 reads an object, type 4 reads an f64, type 3
reads an object for `ver > 0x1065` and an f64 below it; then an i32. For any other type it returns
immediately after the 4 bytes. The type is `00 00 00 00` in all 13 traced instances, so every traced
`moFromEndSpec_c` body is exactly 4 bytes and has no children — which is also why the trace records 0
children for all 13.

The typed layout now uses a guard that accepts only the exercised type zero and consumes exactly
four bytes; types one through five refuse until their conditional child topology is represented.
The enclosing split comes directly from the two decompiled serializers: `moEndSpec_c` reads four
i32 fields after the child at version 14000 and five at version 18000, while
`moExtrusion_c::Serialize` then reads one f64 and one i32. Those runs are 16/20 and 12 bytes. The
remaining final four zero bytes are the `ResolvedFeatures` stream footer, now preserved by the
archive model instead of being absorbed into the last feature.

### 6.4 `moBBoxCenterData_c` — own body is 36 bytes, parent surplus varies

`FUN_4c2cdb50` reads `su_CObject::Serialize`, an i32 into `this+0x08`, `mgPoint_c::restore` into
`this+0x10`, and for `ver > 0xfc6` an f64 into `this+0x28`: `4 + 24 + 8 = 36`. The traced leaf is 50
in 5 instances and 54 in 11, and the split is not by generation — both values occur at 14000 and at 18000. The 14 or 18 surplus is read by `moPerBodyChooserData_c`, which is itself a last child, so the
attribution has no witness. Left opaque.

### 6.5 `moFaceRef_c`, `sgExtEnt_c`, `sgCircleDim`, `sgLLDist`, `moDisplayRadialDim_c`, `ParallelPlaneDistanceDim_c`

All measured with pinned children, all still open:

- `moFaceRef_c`: lead is a flat 36, but the child count varies 4 to 7 and run 0 spans 30, 32, 34, 36,
  70, 92, 96, 98, 116, 130, 138, 142, 158, 162, 169, 221, 260, 318, 320, 502, 562. Content-dependent.
- `sgExtEnt_c`: runs lead, 1 and 2 are flat 0, run 0 is unresolvable in 5 of 6 instances, run 3 is
  12, 20 or 38. Six instances total, five of them in one generation.
- `sgCircleDim`: runs lead, 0, 1, 2, 3 are flat 4, 0, 16, 14, 0 and run 4 is 32 in 6 of 8; runs 5 to
  10 exist only in the one instance with the widest child list. All eight instances are 14000-era, so
  no generation comparison is even possible.
- `sgLLDist`: run 0 does resolve to a flat 0, which would close the one run the shipped entry marks
  opaque, but the entry's declared run 5 = 24 is contradicted by one instance at 72 and the child
  count reaches 12 slots in `vendor_ring`. Taking the entry over would mean inheriting a known-wrong
  constant, so it was left alone.
- `moDisplayRadialDim_c`: every run resolves to a constant except run 20, which is 0 in two instances
  and 170 in two. All four instances are 14000-era. No 18000 witness exists, so nothing can be
  declared for the generation Kit authors.
- `ParallelPlaneDistanceDim_c`: runs lead, 0 and 1 are flat 4, 0 and 16. At version 18000 the byte
  at run offset 127 is the `mgXform_c` basis marker: value 1 contributes a 72-byte matrix and yields
  475 bytes in nine traces, while value 0 yields 403 bytes in `planetop`. Version 14000 omits the
  preceding `Dimension_c` empty-name byte, moves the marker to offset 126 and is pinned to 474 bytes
  in both traces. This conditional plus generation override is now encoded and verified.

### 6.6 The other three donor blockers

Not opaque runs, listed so they are not mistaken for this work:

- `moHistoryFolder_c@5`, 6 donors, and `moHistoryFolder_c@13`, 1 donor. The walk reaches the right
  offset — in `arcboss_cut_cut_cut_through_rev` the second `moHistoryFeatItemData_c` tag is at 771 and
  the walk arrives at 771 — but the tag decodes as a class reference to index 123 with only 5 class
  definitions created since base 113. The walk has swallowed roughly six real class definitions inside
  earlier runs. That is a class-map accounting divergence, not a length that needs a rule.
- `external#42@lead`, 2 donors: no layout entry recorded for that external class. Resolving it needs
  the class-index mapping work in `ExtclassResolve.py`, and `ExternalClasses.json` owns the result.

## 7. Verification

### 7.1 Merged layout verification

`VerifyClassLayouts.py` against the current merged table covers 29 authored classes and reports
`classes=29 confirmed=12 failures=0`. The important fixed-slot classes have zero run mismatches:
`moDisplayDistanceDim_c` 224 checks, `moExtrusion_c` 54, `moFeatureDimHandle_c` 60,
and `moFR_c` 157. The verifier predates `groups` and `child_count_by_class`, so the conditional
`moICE_c` graph and the three counted `moPerBodyChooserData_c` arrays are verified by the donor
segmenter instead. The tool still prints known mismatches for partial fixed-slot layouts such as
`moCompSolidBody_c`, `moDefaultRefPlnData_c` and `sgLLDist`; those are diagnostic rows and do not
count as claimed-layout failures.

### 7.2 Focused converter tests

The focused archive module has **100 passing tests** and no recorded-layout failures. Runtime COM is
prohibited for this converter; application acceptance must exercise generated files through a
separate non-runtime validation path.

### 7.3 Donor fixtures

`SegmentFixtures.py` over the 32 independent donor streams reaches 18761 objects. Seventeen streams
segment, tile and re-emit byte for byte. The current blockers are `sgSketch@tail` ×6,
stream-level ownership ×4, `moSketchChain_c@0` ×3, `moDetailCabinet_c@3` ×1 and `suObList@0` ×1.
The regression floors are 18761 reached objects and 17 exact round trips.

## 8. Functions dumped for this task

Everything else came from the existing dumps under `C:\Users\odin\kitgh\out`. Two functions were
genuinely absent and were recovered with headless `DumpFunctions` passes, depth 1:

| function       | module                                | why it was needed                                                                                    |
| -------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `FUN_4c2d6070` | `sldmodu.dll`, project `proj_sldmodu` | virtual slot 42 of `moRefPlnData_c`, the entire body of `moDefaultRefPlnData_c`                      |
| `FUN_3ca867b0` | `sldmfcu.dll`, project `proj_sldmfcu` | `moCStringHandle_c::Serialize`; the class is not in sldmodu, so it has no `SerializeMap.json` entry |

`mgPoint_c::restore`, `mgVector_c::restore` and `mgXform_c::restore` were not resolvable by name in
either project and their sizes were read off the stream instead, as set out in section 3.2.
