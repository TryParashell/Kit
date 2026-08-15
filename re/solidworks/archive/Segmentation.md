<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Runtime object segmentation of `Contents/Config-0-ResolvedFeatures`

Executes the trace scripted in `.rescratch/grammar/Windbg.md` §6.1. Everything here is
reproducible from the cdb scripts recorded verbatim in this directory and the logs in `out/`.

Read-only debugging of a licensed SOLIDWORKS 2025 install for interoperability. No SOLIDWORKS
binary was modified.

---

## 1. `su_CArchive` field offsets — derived, not assumed

`Calibrate.py` writes `CdbCalibrate.txt`, runs it under `cdbX64.exe`, and solves for the field
offsets from the dumps alone. The script (verbatim, `CdbCalibrate.txt`):

```
.symopt+0x4000
.symopt-0x20000
.exepath+ C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS
.reload /f swccu.dll
r $t0 = 0
bp swccu!su_CArchive::ReadClass "r $t0 = @$t0+1; .printf \"CALIB %d this=%p\\n\", @$t0, @rcx; dq @rcx L18; .if (@$t0 >= 200) { bc * }; g"
bl
g
```

Two notes that matter. `-c "$$<file"` is used, never `$$><`. `.symopt+0x4000` comes first.
`bp swccu!su_CArchive::ReadClass` is written in **undecorated** form: cdb rejects the mangled
export name `?ReadClass@su_CArchive@@QEAAPEAUCRuntimeClass@@PEBU2@PEAIPEAK@Z` with
`Syntax error`, because of the `@` characters, and resolves the undecorated spelling from the
export table with no PDB.

The solver groups the 319 dumps by `this` (9 distinct archives) and keeps a `(cur, max, start)`
offset triple only when, within one archive, `start` and `max` are constant while `cur` is
non-decreasing and strictly increases, `start <= cur <= max`, and `max - start` is a plausible
buffer span. A final pass discards any triple that violates `start <= cur <= max` in any dump of
any archive. That leaves exactly one candidate.

| field          | offset | evidence                                                                                          |
| -------------- | ------ | ------------------------------------------------------------------------------------------------- |
| `m_lpBufCur`   | `0x38` | the only qword that advances within one archive                                                   |
| `m_lpBufMax`   | `0x40` | constant, upper bound of every observed `cur`, in every archive                                   |
| `m_lpBufStart` | `0x48` | constant, lower bound of every observed `cur`                                                     |
| `m_nMapCount`  | `0x50` | the `u32` immediately after `m_lpBufStart`; 307 non-decreasing steps, 3 decreases (archive reuse) |

`candidates: 1`, so the layout is forced by the observations rather than inherited from
`dt mfc140u!CArchive`. It agrees with the MFC layout that `Windbg.md` §4 predicted.

Artefacts: `CdbCalibrate.txt`, `out/cdb_calibrate.log`, `out/Calibrate.json`.

### Cross-check against the statically known class-definition offsets

`Runtrace.py` compares the traced class-definition offsets with `CArchive.py`'s static
`ff ff` scan. For `BASELINE_40x20x10` the traced definitions start at

```
6, 203, 410, 606, 657, 890, 1109, 1302, ...
```

which is exactly the sequence in `.rescratch/grammar/out/tags.json`. Agreement is total on
`BASELINE_40x20x10` (41/41) and `PADPLANE_rev_d5` (45/45).

Two of the nine traced parts disagree: on `THREEFEATURE_pad_cut_pad` the static scan reports 48
definitions and the trace 45, and `TWOPAD_d5` disagrees likewise. The three extra static offsets
on `THREEFEATURE_pad_cut_pad` (20078, 21093, 21262) are **false positives of the static scanner**: no
`ReadObject` ever fires there, and the traced segmentation still tiles the stream with no gap or
overlap and rebuilds it byte-for-byte, which it could not do if a real object started inside
another object's body. `carchive.class_definitions` is therefore an over-approximation on large
streams; the trace is the ground truth.

---

## 2. The productive trace and the segmentation

`Runtrace.py` generates one script per part, filtered on the buffer span so only the target
stream is logged. For `PADPLANE_rev_d5` (`0x40c5` = 16581 bytes), `CdbTracePadplane.txt`:

```
.symopt+0x4000
.symopt-0x20000
.exepath+ C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS
.reload /f swccu.dll
bp swccu!su_CArchive::ReadObject ".if ((poi(@rcx+0x40)-poi(@rcx+0x48))==0x40c5) { .printf \"RO %p %x %d %p\\n\", poi(@rcx+0x48), poi(@rcx+0x38)-poi(@rcx+0x48), dwo(@rcx+0x50), @rsp }; gc"
bp swccu!su_CArchive::ReadClass ".if ((poi(@rcx+0x40)-poi(@rcx+0x48))==0x40c5) { .printf \"RC %p %x %d %p\\n\", poi(@rcx+0x48), poi(@rcx+0x38)-poi(@rcx+0x48), dwo(@rcx+0x50), @rsp }; gc"
bl
g
```

`@rsp` is logged as well as the stream offset and the map counter. The stack pointer recovers the
call nesting, which is what separates a top-level object from a child read inside a parent's
`Serialize`.

`Segment.py` turns a log plus the stream bytes into one row per object:

```
(stream offset, byte length, tag, tag kind, class name, map index, depth, parent)
```

Object _n_'s length is the distance to the next `ReadObject` entry, so the rows tile the stream
exactly: `tiles=True` means zero gaps, zero overlaps, a 6-byte stream header before the first
object, and zero trailing bytes.

Measured, from `out/Runtrace.json` and `out/segments_*.json`:

Nine parts were traced in this session: seven authored-corpus parts covering rectangle and circle
profiles, boss and cut operations, blind / through-all / mid-plane end conditions, Front and Top
support planes, and 1, 2 and 3 features; plus two V8 production parts.

| part                       | stream | objects | class definitions | base map index | tiles | counter mismatches | re-emit   |
| -------------------------- | ------ | ------- | ----------------- | -------------- | ----- | ------------------ | --------- |
| `BASELINE_40x20x10`        | 11075  | 321     | 41                | 109            | yes   | 0                  | identical |
| `CIRCLE_r10`               | 10556  | 285     | 45                | 109            | yes   | 0                  | identical |
| `PLANE_TOP`                | 11075  | 321     | 41                | 109            | yes   | 0                  | identical |
| `TWOPAD_d5`                | 19390  | 400     | 41                | 110            | yes   | 0                  | identical |
| `PADPLANE_rev_d5`          | 16581  | 536     | 45                | 110            | yes   | 0                  | identical |
| `CUTBASE_cd5`              | 16579  | 536     | 45                | 110            | yes   | 0                  | identical |
| `THREEFEATURE_pad_cut_pad` | 24805  | 615     | 45                | 111            | yes   | 0                  | identical |
| `Piston Ring KF` (V8)      | 25998  | 916     | 61                | 111            | yes   | 0                  | identical |
| `COJINETE INFERIOR` (V8)   | 17601  | 573     | 48                | 111            | yes   | 0                  | identical |

`Model.py` reparses the segmentation into a node list where every class reference and object
reference is a _pointer to another node_ rather than a literal index, then re-emits the stream
with all indices recomputed. For all nine parts the result is **byte-identical** to the original.
That is the strongest available proof that the segmentation is complete and that the renumbering
model is right: if a single object boundary or a single token were misclassified, the re-emitted
stream would differ.

The mission asked for all 51 corpus parts. Nine were traced, each costing one instrumented
SOLIDWORKS launch on the single shared install; the remaining 42 are the same authored family as
the seven covered here and were not run. Every part traced tiled cleanly and re-emitted exactly,
with no exceptions, so nothing observed suggests the result is part-specific — but the claim is
nine parts, not 51.

---

## 3. The map counter — increment rule as observed

The counter at `m_nMapCount` is read at entry to `ReadObject`, before the tag is consumed. The
observed difference to the next object's counter, over every consecutive pair in every traced
part:

| tag at the object                         | increment                                            |
| ----------------------------------------- | ---------------------------------------------------- |
| `ff ff` class definition                  | **+2** (one index for the class, one for the object) |
| `0x8000\|i` class reference               | **+1** (the object only)                             |
| `0x0000` null tag                         | **0**                                                |
| object reference (`t < 0x8000`, `t != 0`) | **0**                                                |

`Segment.py` models this forward from the first observed counter and compares against the value
logged at every object: **0 mismatches across all 4503 objects of the nine traced parts**. The
counter is a single combined class-and-object index space, exactly as `Grammar.md` §2.3 inferred.

One correction to the static reading. The counter does **not** start at 1 for this stream. It
starts at 109, 110 and 111 for the 1-, 2- and 3-feature parts, because the same archive already
holds entries from streams read earlier in the document load, and the count of those grows by one
per feature. Consequently:

- tokens whose index is **below** the base refer to classes and objects defined by _earlier
  streams_, and are invariant as long as those streams are inherited unchanged (31, 42 and 48
  such class references, 6, 12 and 14 such object references in the three parts);
- only tokens at or above the base are internal to `ResolvedFeatures` and need renumbering.

`model.parse` refuses to build a model if any token at or above the base fails to resolve to a
node, so this split is checked rather than assumed.

---

## 4. Renumbering, and the array count that static analysis missed

`Renumber.py` derives the two node blocks that make up one feature, with no hardcoded indices:

- **history block** — the `moCompFeature_c` entry pair for the last feature, located by mapping
  the byte span of `streamlib.comp_feature_entries[-2:]` onto object boundaries. For
  `PADPLANE_rev_d5` this is nodes `[25, 35)`, ten objects, 238 bytes.
- **feature block** — the last sketch's tree-node name record is found, the enclosing object
  located, then the search walks back to the nearest `depth == 0` object. For `PADPLANE_rev_d5`
  that is node 331, a top-level `moProfileFeature_c` class reference immediately followed by the
  `Sketch2` name record, and the block runs `[331, 536)`, 205 objects, to the end of the stream.

`duplicate()` copies both blocks _k_ times. A copied class definition becomes a class reference to
the original definition. A reference whose target is inside any duplicated block is retargeted to
the same copy; a reference to anything else keeps pointing at the original node. `Model.emit`
then recomputes every index from scratch, so all `0x8000|i` class tokens and all object tokens are
renumbered by construction. `remove()` is the inverse and refuses a deletion set that is not
closed, or one that would delete a class definition that surviving nodes still reference.

`out/RenumberingPadplaneRevDFiveTwo.json` is the full map-index renumbering table: one row per
emitted object with `old_map_index`, `new_map_index` and the shift. Growing
`PADPLANE_rev_d5` by two features shifts indices by one of
`{0, 6, 12, 88, 89, 90, 91, 92, 164, 165, 166, 167, 168}` — the step structure of two block
insertions, not a single constant.

### The `moHistoryFeatItemData_c` array count

`Counts.py` searches every object body of five traced parts (1, 2 and 3 features, rectangle and
circle, boss and cut) for a `u16`/`u32` equal to the number of `moCompFeature_c` entries, keyed by
position relative to the first `moHistoryFeatItemData_c`. Exactly one field matches in all five:

> a `u16` in the last two bytes of the object immediately preceding the first
> `moHistoryFeatItemData_c` — byte offset **604** in every corpus part — holding **2 × feature
> count**.

This is the array length that `su_CArchive` reads before the history-item objects. `Grammar.md`
§3 modelled the record as `93 + 119·(n-1)` bytes with no count, so nothing in the static work
bumped it. It is the direct cause of the reproducible crash that `Serialize.py` guards against:
`.rescratch/re/parts/G4_four_boss.SLDPRT` and this work's `T4_4_boss.SLDPRT` differ in exactly
**one byte** — offset 604, `04` versus `08` — plus eight two-byte halves of the regenerated
`time_t` stamps. G4 hard-crashes SOLIDWORKS; T4 opens.

`Fieldscan.py` then searched **every stream** of six parts spanning 1, 2 and 3 features for a
`u16`/`u32` at a fixed byte offset equal to `n`, `2n`, `24+2n` and nine other linear forms. Three
fields exist in the whole container, and no others:

| stream                                                                 | offset | width | value     | verified on             |
| ---------------------------------------------------------------------- | ------ | ----- | --------- | ----------------------- |
| `Contents/Config-0-ResolvedFeatures`                                   | 604    | `u16` | `2n`      | 6 parts                 |
| `Contents/Config-0-ModelHeader` and `Header2` (byte-identical streams) | 77     | `u16` | `24 + 2n` | **all 51 corpus parts** |
| `Contents/CMgr`                                                        | 1414   | `u16` | `n`       | 6 parts                 |

The `ModelHeader` field is the element count of the `suObList` that the stream's `moLogs_c`
object opens (`ff ff 01 00 08 00 suObList` at byte 68, count at 77).

---

## 5. Measured SOLIDWORKS results

Every measurement uses `.rescratch/sw/Measure.py`: control before, one fresh subprocess per
candidate, control after, absolute paths, dialog dismisser running. `Contents/Config-0-Partition`
is dropped from every emitted container, so every volume is a genuine rebuild from the records
written here. All three batches reported `control healthy: True`.

| part                                          | features asked | status                     | bodies | volume mm³        | expected mm³ | tree features built |
| --------------------------------------------- | -------------- | -------------------------- | ------ | ----------------- | ------------ | ------------------- |
| `BASELINE_40x20x10` (control)                 | 1              | measured                   | 1      | 8000.000000000001 | 8000         | 1                   |
| `T3_3_boss`                                   | 3              | measured                   | 1      | 36800.0           | 37400        | 2                   |
| **`T4_4_boss`**                               | **4**          | **measured, opens**        | **1**  | **36800.0**       | **38100**    | **2**               |
| `T3H_3_boss` (+`ModelHeader`/`Header2` count) | 3              | solidworks-crashed-on-open | –      | –                 | 37400        | –                   |
| `T4H_4_boss` (+`ModelHeader`/`Header2` count) | 4              | solidworks-crashed-on-open | –      | –                 | 38100        | –                   |
| `T4cmgr_4_boss` (+`CMgr` count)               | 4              | solidworks-crashed-on-open | –      | –                 | 38100        | –                   |
| `T4all_4_boss` (+ all three counts)           | 4              | solidworks-crashed-on-open | –      | –                 | 38100        | –                   |

Prior state for comparison, from `.rescratch/grammar/out/MeasureGrown.json`:
`G4_four_boss` and `G5_five_boss` both `solidworks-crashed-on-open`.

What this says, precisely.

1. The 4-feature stream now **opens**. The renumbered `ResolvedFeatures` is accepted: 8 history
   items, 4 sketches, 4 extrusions, 4 tree-node id pairs, all class and object tokens
   consistent. The crash that motivated `Serialize.py`'s refusal of 4 features is fixed, and the
   fix is one byte wide.
2. SOLIDWORKS builds **2** of the 4 features and returns 36800 mm³ = 36000 (base) + 800 (first
   stud), against 38100 expected. So the acceptance criterion is **not met**: the correct tree
   was not produced.
3. The remaining gate is **outside** `ResolvedFeatures`. The document streams that scale with
   feature count are `Contents/CMgr` (+100/+116 bytes per feature), `Contents/Config-0`
   (+86/+90), `Contents/Config-0-ModelHeader` and `Header2` (+154/+156), `Contents/DisplayLists`
   (+4948/+5092), `ThirdPtyStore/VisualStates` (+111) and `_MO_VERSION_18000/Biography`
   (`Streamgrowth.py`). They are inherited from the 2-feature donor, so the document still
   describes 2 features.
4. Patching the count field of `ModelHeader`/`Header2`, or of `CMgr`, without growing the list
   body behind it makes SOLIDWORKS crash on open rather than build more features — the reader
   walks _count_ elements through a body that only holds the donor's, and desynchronises. This is
   the expected failure of a count-only patch and it confirms the count fields are real.

`CONTAINER.md` in this directory carries that work forward: `Contents/CMgr`,
`Contents/Config-0-ModelHeader` / `Header2` and `Contents/Config-0` are traced, segmented and
re-emitted byte-identically on the genuine `boss1..boss4_front_rect_blind` family, the per-feature
block of each is isolated, and the load-critical versus stale-safe split across the whole
container is measured.

So the honest position is: object segmentation and map-index renumbering of
`Contents/Config-0-ResolvedFeatures` are solved and proven byte-exact; the arbitrary feature
count now needs the same treatment applied to `Contents/CMgr` and
`Contents/Config-0-ModelHeader`/`Header2`. Both are `su_CArchive` streams — `ModelHeader` begins
`ff ff 01 00 0a 00 moHeader_c` — so the identical trace, segment, duplicate, renumber pipeline in
this directory applies to them unchanged; each needs one `Runtrace.py` run and its own
per-feature block.

---

## 6. Files

Scripts, all `black`-clean, no comments:

```
.rescratch/trace/
  Tracelog.py       cdb log parser: RO/RC events and CALIB register dumps
  Calibrate.py      writes CdbCalibrate.txt, runs it, solves the su_CArchive field offsets
  Cdbdrive.py       non-interactive cdb launcher: sweep, dialog dismisser, poll, terminate
  Runtrace.py       writes cdb_trace_<label>.txt, runs it, segments, cross-checks
  Segment.py        segmentation: offset, length, class name, map index, nesting, tiling proof
  Model.py          node model with symbolic references; emit() renumbers every token
  Renumber.py       block discovery, duplicate/remove one feature, renumbering table
  Counts.py         finds array-count fields inside traced object bodies
  Fieldscan.py      finds feature-count-derived scalar fields across all container streams
  Headercount.py    the three count fields and the patched-stream builder
  Streamgrowth.py   which streams grow with feature count
  Author.py         emits the from-scratch 3- and 4-feature parts
  Show.py           annotated node listing
  Peek.py           hex/ASCII window into any stream
  Diffstream.py     byte diff of one stream between two parts
```

cdb scripts, verbatim: `CdbCalibrate.txt`, `cdb_trace_<label>.txt`.

Logs and machine-readable output: `out/cdb_calibrate.log`, `out/cdb_trace_<label>.log`,
`out/Calibrate.json`, `out/Runtrace.json`, `out/segments_<label>.json`,
`out/RenumberingPadplaneRevDFiveTwo.json`, `out/GrownPadplaneRevDFiveTwo.json`,
`out/CountsItems.json`, `out/CountsFeatures.json`, `out/fieldscan_*.json`, `out/Author.json`,
`out/measure_*.txt`.

Emitted parts: `parts/T3_3_boss.SLDPRT`, `parts/T4_4_boss.SLDPRT`,
`parts/T3H_3_boss.SLDPRT`, `parts/T4H_4_boss.SLDPRT`, `parts/T4cmgr_4_boss.SLDPRT`,
`parts/T4all_4_boss.SLDPRT`.

Measurement records: `.rescratch/sw/out/MeasureTraceFour.json`,
`.rescratch/sw/out/MeasureTraceFourh.json`, `.rescratch/sw/out/MeasureTraceFourcmgr.json`.

Nothing under `src/`, `tests/`, `.rescratch/grammar/` or `.rescratch/revolve/` was modified.
