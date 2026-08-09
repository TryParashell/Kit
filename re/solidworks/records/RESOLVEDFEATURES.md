# `Contents/Config-0-ResolvedFeatures` — segmentation, header semantics, and the field-program debt

Status: **partial**. The stream's tag framing, its 6-byte header, its tree-node name records and its
per-feature authored fields are decoded and gated against vendor bytes. Its class field program is
not: 9653 of the 9877 run bytes a single-feature pad carries are invariant bytes nobody has read
yet. **No Kit-generated part with a body opens.** A candidate built from Kit's 25 streams plus a
from-scratch resolved stream refused with `com_error(-2147023170)`; the same container with the
stream deleted opened with **0 bodies, no mass and 12 document-state folders**.

Everything below is measured. Controls measured 8000.000000000001 mm³, centre `[0.0, 0.0, 5.0]`,
1 body before and after every oracle batch, and every batch reported `control healthy: True`.

## 1. What landed in shipped code and data

| change                                                      | file                                        | effect                                     |
| ----------------------------------------------------------- | ------------------------------------------- | ------------------------------------------ |
| `moCompRefPlane_c` run 1 becomes a `conditional` rule       | `re/data/class_layouts_versioned.json`      | unblocks all 32 donor fixtures             |
| `moProfileFeature_c` gets ten fixed child slots             | `re/data/class_layouts_decompiled.json`     | `boss1_front_rect_blind` 148 → 223 objects |
| `moExtrusion_c` gets the sixteen children the traces record | `re/data/class_layouts_versioned.json`      | replaces a nine-slot absorption            |
| `moCompSketchEntHandle_c` run 0 gets the 89/85 version gate | `re/data/class_layouts_decompiled.json`     | its `sgPointHandle` was 89 bytes early     |
| donor object floor                                          | `tests/convert/test_solidworks_archive.py`  | 5244 → **7487**                            |
| `_name_record` flag word per node kind                      | `src/convert/adapters/solidworks/native.py` | correct for planes, Origin and cuts        |
| `_resolved_payload` first `u32`                             | `src/convert/adapters/solidworks/native.py` | base map index, not the object count       |

`archive.py` needed no change: `CONDITIONAL_RULE` and `_element_length` already implement the rule.

The last two layout rows are not new findings, they are the price of the first two. Unblocking
`moCompRefPlane_c` lets the static walk reach into `moExtrusion_c` and `moCompSketchEntHandle_c` for
the first time, and both of those disagreed with the recorded WinDbg segmentations about where their
children start (§7.9, §7.12). The recorded object offsets are ground truth, so the layouts were
corrected to them rather than left to mis-walk. The two layout findings alone take the donors to
**7257**; with these two corrections the shipped table reaches **7487**, and all nine recorded
segmentations agree with the static walk for every object it reaches.

The `moCompRefPlane_c` finding lives in `class_layouts_versioned.json` rather than
`class_layouts_decompiled.json` because `gen_class_layouts.py` merges the versioned table **after**
the decompiled one and replaces whole class entries, so a decompiled entry for a class the versioned
table owns is silently dropped. `moCompRefPlane_c` is owned there for its `runs_by_version` gate.

## 2. `moCompRefPlane_c` run 1 — a conditional basis block, not an opaque run

This single run blocked all 32 donors. The table recorded it as `opaque`: 42 bytes in 21 of the 22
traced instances, 114 in `planetop` node 211, "the 72-byte difference is real and unexplained".

`BASELINE_40x20x10` (Front-plane sketch) and `PLANE_TOP` (Top-plane sketch) are both **11075
bytes**, and the diff isolates the whole difference to one 72-byte insertion:

| stream offset | `BASELINE` (Front) | `PLANE_TOP` (Top) | field                                                                  |
| ------------- | ------------------ | ----------------- | ---------------------------------------------------------------------- |
| 7954          | `50 46 00 00`      | `50 46 00 00`     | `u32` 18000, the generation stamp                                      |
| 7958          | `02 00 00 00`      | `03 00 00 00`     | `u32` support plane object id                                          |
| 7962          | `f6 5a 1a 69`      | `f6 5a 1a 69`     | `u32` constant `0x691a5af6`                                            |
| 7966          | `00 00`            | `00 00`           | `u16` 0, consumed as the slot-1 null tag                               |
| 7968          | `03 00 00 00`      | `02 00 00 00`     | `u32` axis code, `5 - plane id`                                        |
| **7972**      | **`00`**           | **`01`**          | **`u8` basis-present flag**                                            |
| 7973          | —                  | 72 bytes          | 9 × `float64` row-major basis, present only when the flag is 1         |
| 7997 / 8069   | `double 1.0`       | `double 1.0`      |                                                                        |
| 8008 / 8080   | `04 00 00 00`      | `04 00 00 00`     | the word that closes the run; the streams realign here, 72 bytes apart |

So run 1 is 42 bytes when the flag is clear and 114 when it is set:

```json
{
  "slot": "1",
  "rule": "conditional",
  "at": 0,
  "predicate_at": 4,
  "predicate_width": 1,
  "values": [1],
  "width": 72,
  "tail": 42
}
```

The predicate sits at a **fixed offset inside the run itself**, `+4`, so it is read before the
length it selects is computed. This is the same 72-byte basis `../archive/GRAMMAR.md` §5.4 records
for `moSketchChain_c` as "omitted entirely for Front", now with its discriminator named.

The measured bases, read out of the vendor streams at 7973:

| plane | id  | flag | basis, row major                     |
| ----- | --- | ---- | ------------------------------------ |
| Front | 2   | 0    | absent; the identity is implicit     |
| Top   | 3   | 1    | `(1, 0, 0), (0, 0, 1), (0, -1, 0)`   |
| Right | 4   | 1    | `(-0, 0, 1), (-0, 1, 0), (-1, 0, 0)` |

The negative zeros in the Right basis are real bytes: `-0.0` is `00 00 00 00 00 00 00 80` and `0.0`
is eight zeros, so an emitter that writes `0.0` there is one bit wrong in three doubles. The gate
compares the raw 72 bytes, not the floats.

`moProfileFeature_c` is the second change and needs no new machinery: `moOriginProfileFeature_c` is
`confirmed` with ten fixed child slots and the runs `lead 0, 0 4, 1 47, 2 30, 3 44, 4 4, 5 0, 6 0,
7 0, 8 14, 9 8`, and every single-feature part in the corpus carries the same ten children in the
same order with the same runs, with `sgLineHandle` in slot 6 where the origin class takes a
wildcard. The generated table had derived `repeat_prefix: 6` from a 6×2 / 10×13 child-count split
and appended a `...` slot, which made the segmenter refuse the run after slot 5 in every instance.

## 3. The 6-byte header

```
u32 base map index      the Contents/Config-0 final map counter
u16 top-level nodes - 1
```

Both readings are pinned by the oracle, one vendor control with only those 6 bytes changed:

| candidate     | change          | result                                                                      |
| ------------- | --------------- | --------------------------------------------------------------------------- |
| control       | —               | opened, 1 body, 8000.000000000001 mm³                                       |
| `p1_count_18` | `u16` 19 → 18   | **crashed** `-2147023170`                                                   |
| `p2_count_20` | `u16` 19 → 20   | **crashed** `-2147023170`                                                   |
| `p3_base_110` | `u32` 109 → 110 | **opened**, 1 body, 8000.000000000001 mm³, `[0.0, 0.0, 5.0]`, 19 tree nodes |

The `u16` is a hard **node count minus one** and is **load-critical**: off by one in either
direction is fatal. That pins the 20-node reading of the baseline exactly — 14 folders, 3 planes,
Origin, Sketch1, Boss-Extrude1.

The `u32` is **not reader-critical**. 110 in place of 109 opens with the correct volume. It is the
`Contents/Config-0` final map counter — `re/data/external_classes.json::config0_continuation`
measures 109 for `boss1`, 110 for `boss2` and 111 for `boss3`, so it is `109 + features - 1` — and
`resolve_base()` needs it to walk the stream statically, but SOLIDWORKS tolerates it being wrong.
`native.py` writes it because a static walk of Kit's own output has to work, not because the reader
demands it.

## 4. The reader cannot be grown incrementally

Vendor control with the resolved stream truncated at a clean top-level node boundary and the header
count patched down to match. Donor instruments, not Kit output.

| candidate              | resolved bytes | header count | result                    |
| ---------------------- | -------------- | ------------ | ------------------------- |
| `t1_header_only`       | 6              | 0            | **crashed** `-2147023170` |
| `t2_folders_only`      | 3248           | 13           | **crashed** `-2147023170` |
| `t3_planes_and_origin` | 5862           | 17           | **crashed** `-2147023170` |
| `t4_through_sketch`    | 8057           | 18           | **crashed** `-2147023170` |
| `t5_through_extrusion` | 8506           | 19           | **crashed** `-2147023170` |

All five crash, while `para417_partdesign` §3.2 `b1` and this session's `k3_kit_without_resolved`
both show that **deleting** the stream outright opens the part with 0 bodies and 12 folders. The
reader commits to the full object graph the moment the stream exists. **A synthesis has to be
complete and self-consistent on the first attempt; the oracle cannot be used to grow the stream node
by node.** Plan accordingly: no ladder, no bisection against a partial stream.

## 5. Segmentation and re-emission of the single-feature family

With the two rules above plus three corpus-fitted run lengths that are **not shipped** (§7), the
whole stream of a single-feature rectangular pad segments to **265 objects**, `tiling()` reports
`gaps: []`, `overlaps: []`, `trailing_bytes: 0`, and `Model.emit()` — which recomputes every class
and object index from the base — returns the input **byte for byte**.

| part                                                   | objects | tiles | re-emits identically                     |
| ------------------------------------------------------ | ------- | ----- | ---------------------------------------- |
| `BASELINE_40x20x10`, `CONTROL_A`, `CONTROL_B`          | 265     | yes   | **yes**                                  |
| `WIDTH_w40`, `WIDTH_w41`, `WIDTH_w60`                  | 265     | yes   | **yes**                                  |
| `DEPTH_d10`, `DEPTH_d20`, `HEIGHT_h20`, `OFFSET_x5_y0` | 265     | yes   | **yes**                                  |
| `PLANE_FRONT`, `REVERSED_d10`                          | 265     | yes   | **yes**                                  |
| `PLANE_TOP`, `PLANE_RIGHT`                             | 248     | no    | no — `moDisplayDistanceDim_c@7` at 10002 |
| `MIDPLANE_d10`                                         | 248     | no    | no — `moDisplayDistanceDim_c@7` at 9930  |

**12 of 15.** Before this work, zero parts segmented completely.

On the 32 donor fixtures under `tests/fixtures/solidworks/donors/`, with the shipped table:

| table                                   | objects reached | blockers                                                        |
| --------------------------------------- | --------------- | --------------------------------------------------------------- |
| before                                  | **5244**        | `moCompRefPlane_c@1` ×32                                        |
| the two layout findings alone           | **7257**        | `moExtrusion_c@5` ×23, `moSketchExtRef_w@0` ×6, `sgSketch@0` ×3 |
| shipped, with the two trace corrections | **7487**        | `moSketchExtRef_w@0`, `sgSketch@0`, `moExtrusion_c@9`           |

Every donor advanced, +42.8 % overall. `FIXTURE_OBJECT_FLOOR` in
`tests/convert/test_solidworks_archive.py` is 7487 so it cannot silently regress.

Against the nine recorded segmentations the static walk now reaches 234 of 321 objects on
`baseline`, 244 of 536 on `cutbase` and `padplane`, 254 of 615 on `three`, 244 of 400 on `twopad`,
234 of 321 on `planetop`, 171 of 285 on `circle`, 171 of 573 on `vendor_cojinete` and 181 of 916 on
`vendor_ring`, and **every offset it produces equals the recorded offset**. It stops on `moFR_c@0`
in the six pad parts and `moSketchExtRef_w@0` in the other three, and both stop offsets are recorded
object offsets rather than a mis-step.

Field-level facts gated against the vendor stream while getting there:

- `encode_tree_node_name` reproduces the vendor bytes for all **20** tree nodes: name, `u32 0`,
  `u32 flags`, `u32 node id`. Flags are `0x40000000` for the folders **and the sketch**,
  `0xC0000000` for the three planes and Origin, `0x40000140` for `Boss-Extrude1` and `0x400201CA`
  for a cut. The twelve bytes are three `u32`s, not a `double` and a `u32`: writing `double 2.0`
  there is byte-correct for folders only by coincidence, because `2.0` is
  `00 00 00 00 00 00 00 40` and therefore reads back as `u32 0` then `u32 0x40000000`.
- The four rectangle coordinate records occur verbatim at measured strides **`178, 162, 162`**, so
  `../archive/GRAMMAR.md` §5.1's uniform 162 is right for the last two gaps and wrong for the first.
- `moCompFeature_c` holds **2 entries per feature**, one sketch and one extrusion — two entries in
  the 20-node baseline, for ids 26 and 32 — and its 93-byte body opens
  `2b 80` classref, `02 00` objectref, then 41 zero bytes. The `02 00 00 00` that
  `../archive/GRAMMAR.md` §3.1 read as a `u32` = 2 is an object-reference tag plus the first two
  bytes of that zero run. The other two 89-byte hits in the baseline are `moCompRefPlane_c`
  instances, which carry the identical run because `moCompRefPlane_c::Serialize`
  (`sldmodu.dll 0x4bc22e00`) calls `moCompFeature_c::Serialize` (`0x4bc222f0`) as its base.
- The direction and end-condition bytes at `scalar - 824` and `scalar - 818` read `(0, 0)` in
  `BASELINE_40x20x10`, `(1, 0)` in `REVERSED_d10` and `(0, 6)` in `MIDPLANE_d10`, pinning
  `swEndConditions_e` blind 0 and mid-plane 6 and the reverse flag.
- The circle on-curve point sits at **17.000000000000032°**; its x is byte-identical to
  `centre + r·cos 17°` and its y agrees to `5.33e-15 mm`. A circle centre carries entity class
  **1**, where a rectangle corner carries 2.

## 6. The census: what the undecoded bytes are

A single-feature pad is 11075 bytes, of which **9877** are class run bytes across the 265 nodes.
Diffing the tag-level programs:

| comparison                           | parts                                                                       | run bytes | varying | invariant |
| ------------------------------------ | --------------------------------------------------------------------------- | --------- | ------- | --------- |
| two identically-authored documents   | `CONTROL_A`, `CONTROL_B`                                                    | 9877      | **50**  | 9827      |
| eight differently-parameterised pads | `WIDTH_w40/41/60`, `HEIGHT_h20`, `DEPTH_d10/20`, `OFFSET_x5_y0`, `BASELINE` | 9877      | **224** | **9653**  |

Session noise between two authorings of the same part is a `u32` `time_t` at run offset `+22` in
nine node bodies, one byte at `+85` in two `objectref` runs, and 12 bytes inside `moExtrusion_c@5`.
**50 bytes.**

The 224 parameter-varying bytes sit in 33 of the 265 nodes and are exactly the fields
`../archive/GRAMMAR.md` already documents: nodes 158/162/166/170 are the four sketch coordinates,
93/95/96/106/108/109/119/121/122 are the three plane display rectangles (`moDefaultRefPlnData_c`, a
derived cache), and 245/247/249/257/261/262 are the depth scalar and its five annotation copies.

**So the topology's field program is 9653 invariant bytes.** That is the debt, and it is why no
donor-free stream exists yet: a 9653-byte constant table is a donor block by the sizing test in
`.kiro/steering/no-donor-blocks.md`, whatever it is named. The census gives it per node and per
class with the varying positions already separated, so it is an enumerated list of runs rather than
a wall. The highest-leverage item is the folder tail: 139 bytes identical across 13 different folder
classes except for a `u32` `time_t` pair and one byte, so decoding `moNode_c` / `moModelNode_c` once
buys roughly 1800 bytes.

## 7. Refuted hypotheses

Each of these was believed, tested and killed. They are recorded so nobody pays for them twice.

1. **The stream can be grown incrementally under the oracle.** Refuted, §4. All five truncations at
   clean node boundaries with the count patched down crash `-2147023170`, while deleting the stream
   entirely opens with 0 bodies.
2. **The `u16` in the header is advisory.** Refuted, §3. 18 and 20 both crash a 20-node stream; only
   19 opens.
3. **The `u32` in the header must equal the `Contents/Config-0` final map counter for the reader.**
   Refuted, §3. 110 in place of 109 opens with the correct volume. It is required for _static
   walking_, not by the reader.
4. **`moCompRefPlane_c@1`'s 72-byte difference is unexplained** — the layout table's own note.
   Refuted, §2: a `u8` flag at run offset `+4` selects a 9-double basis.
5. **`moCompFeature_c` holds one entry per tree node.** Refuted, §5: two entries in the 20-node
   baseline, one per sketch and one per extrusion. An encoder that emitted 20 was caught by the gate.
6. **`../archive/GRAMMAR.md` §3.1's `02 00 00 00` is a `u32` = 2.** Refuted, §5: an object-reference
   tag plus the first two bytes of a 41-byte zero run.
7. **The rectangle coordinate stride is a uniform 162 bytes** (`../archive/GRAMMAR.md` §5.1).
   Refuted, §5: the measured strides are `178, 162, 162`.
8. **The 72-byte basis block holds the same matrix as `native.py::_principal_plane_ids`.** Refuted
   by the vendor bytes at 7973: the block is Top `((1,0,0),(0,0,1),(0,-1,0))` and Right
   `((-0,0,1),(-0,1,0),(-1,0,0))`, negative zeros included, while the matching table carries Top
   `x=(1,0,0), y=(0,0,-1), z=(0,1,0)` and Right `x=(0,0,-1), y=(0,1,0), z=(1,0,0)`.
9. **…and therefore `_principal_plane_ids` carries the wrong signs and must be replaced by the
   measured rows.** Also refuted, this time by arithmetic and by the suite. The measured block is
   exactly the **transpose** of the matching table's frame: transposing
   `[[1,0,0],[0,0,-1],[0,1,0]]` gives `[[1,0,0],[0,0,1],[0,-1,0]]`, and transposing
   `[[0,0,-1],[0,1,0],[1,0,0]]` gives `[[0,0,1],[0,1,0],[-1,0,0]]`, which is the Right block up to
   the signed zeros. The two matrices are the plane-to-world and world-to-plane forms of the same
   rotation, and each is already in the right place: `_plane_frame_block` writes
   `rows = zip(x_axis, y_axis, z_axis)`, i.e. the transpose, behind a basis-present flag at `+48`,
   which is the vendor layout; and `_principal_plane_ids` matches the plane-to-world frame that
   `_principal_plane_frames` hands back on the read path, where Top round-trips as
   `u=(1,0,0), n=(0,1,0), v=cross(n,u)=(0,0,-1)`. Substituting the measured rows into the matching
   table double-transposes: measured, it dropped Top and Right from the principal set entirely
   (`_principal_plane_ids` returned one plane instead of three) and a piston-ring round trip emitted
   `Top Plane` as authored object 26 in place of `Sketch1`. The change was reverted; the measured
   byte order stands as a fact about the block, not about the matching table.
10. **One `moExtrusion_c@5` length closes the class.** Refuted twice over. 707 is the best of
    `{587, 635, 705, 707, 779}` for `PLANE_TOP` and still stalls, **and 707 demonstrably absorbs a
    `moPerBodyChooserData_c` class definition at `+30`** — `ff ff 01 00 16 00
   moPerBodyChooserData_c` — so it swallows child objects. It re-emits byte-identically only
    because `Model.emit()` copies run bytes verbatim; the swallowed class tags would not be
    renumbered if the object count changed. **This is an absorption artifact, not a field program,
    and it is deliberately not shipped.** The class has more child slots than the nine declared, and
    splitting run 5 at that boundary is the next move: it unblocks 23 of the 32 donors.
    `moExtrusion_c::Serialize` and the `moBodyFeature_c` / `FUN_4bb886c0` base chain named in
    `external_classes.json::pmark_record` are the entry points.
11. **One `moDisplayDistanceDim_c@6` length closes the three stalling parts.** Refuted: no value in
    `{0, 4, …, 80, 91}` segments `PLANE_TOP`, the best reaching 256 of 265, and the fitted 19 is
    refuted for `PLANE_TOP`, `PLANE_RIGHT` and `MIDPLANE_d10`. The record is the depth dimension's
    annotation and its witness geometry moves with the sketch plane and the end condition, which is
    why those three parts are exactly the three that stall. It needs field decoding, not a length.
12. **`moCompSketchEntHandle_c` run 0 is zero, as the generated table records.** Refuted: with the
    `moUnitComponent_c` classref in slot 0 pinned to its own 4-byte subtree, the recorded gap from
    the end of that object reference to the `sgPointHandle` classref is 89 bytes in `CIRCLE_r10` at
    18000 and 85 in both `vendor_cojinete` and `vendor_ring` at 14000 — the same gate
    `moCompFeature_c` already declares, for the same reason, because the class shares that base.
    Zero put the `sgPointHandle` 89 or 85 bytes early in all three traced instances.
13. **The nine-slot `moExtrusion_c` entry places objects correctly.** Refuted: the nine traced
    instances carry 14 or 16 children. The nine-slot walk skipped the object reference at 8115 in
    `baseline` — its run 1 of 49 is the traced `2 + 2 + 45` with a real child in the middle — and
    every object it produced after that was at an offset the trace contradicts.
14. **The blocker is `sgSketch@tail` ×32 at 4892 objects**, as an earlier brief recorded. Not
    reproducible: the measured blocker on the shipped table was `moCompRefPlane_c@1` ×32 at 5244
    objects, and the `groups` rule that brief asked for already existed in `archive.py` and was
    already wired into `sgSketch`.

## 8. What is deliberately not shipped

- The three corpus-fitted run lengths `moExtrusion_c@5 = 707`, `moExtrusion_c@8 = 767` and
  `moDisplayDistanceDim_c@6 = 19`. The first two are absorption artifacts (§7.10) and shipping them
  would tell the next agent that `moExtrusion_c` is decoded when it is swallowing child objects; the
  third is refuted for three of the fifteen corpus parts. The shipped `moExtrusion_c` entry does not
  carry a length for that region at all: it declares the children the traces record and refuses runs
  9, 11 and 12.
- Any from-scratch 11075-byte emitter. The honest form of one today is 9653 bytes of constant table,
  which is a donor block.

## 9. Reproduction

```powershell
uv run python re\tooling\ghidra\gen_class_layouts.py
uv run python re\tooling\harness\segment_fixtures.py --out <out.json>
uv run python -m pytest tests\convert\test_solidworks_archive.py -q
```

The fixture harness prints the per-donor blockers; the object total is the sum of `object_count`
over its `donors` array and must be 7257.
