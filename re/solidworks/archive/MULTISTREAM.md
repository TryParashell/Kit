# Runtime object segmentation of the remaining feature-count streams

Extends `REPORT.md` from `Contents/Config-0-ResolvedFeatures` to `Contents/CMgr`,
`Contents/Config-0-ModelHeader` / `Header2`, `Contents/Config-0` and
`ThirdPtyStore/VisualStates`. Read-only debugging of a licensed SOLIDWORKS 2025 install for
interoperability. No SOLIDWORKS binary was modified.

## 1. One launch, five streams

`multitrace.py` writes a single cdb script whose `ReadObject` / `ReadClass` breakpoints fire when
the archive's buffer span equals **any** of the five target stream lengths, and logs the span
alongside the buffer base, the offset, the map counter and `@rsp`:

```
bp swccu!su_CArchive::ReadObject ".if (((poi(@rcx+0x40)-poi(@rcx+0x48))==0x7e3) | ...) { .printf
\"RO %p %x %d %p %x\\n\", poi(@rcx+0x48), poi(@rcx+0x38)-poi(@rcx+0x48), dwo(@rcx+0x50), @rsp,
poi(@rcx+0x40)-poi(@rcx+0x48) }; gc"
```

The span identifies the stream, so one instrumented launch segments all five. `tracelog.Event`
carries the span; `segment.build(..., span=n)` selects the busiest buffer for that span, which is
what separates `Contents/Config-0-ModelHeader` from the byte-identical `Header2` (they are read
into two different buffers of equal length).

`.symopt+0x4000` first, `-c "$$<file"`, undecorated `swccu!su_CArchive::ReadObject`, exactly as
`REPORT.md` §1 established.

## 2. Segmentation and the byte-identical re-emit proof

Seven parts were traced. `boss1..boss4_front_rect_blind` are the genuine SOLIDWORKS-authored
donor parts in `.rescratch/donors/parts` — one family, 1 to 4 blind rectangular bosses on the
Front Plane, disjoint tiles along X. That family is what makes the per-feature block fall out of a
plain diff: two parts of the *same* family differ only by the repeated unit.

`tiles` means the segmentation covers the stream with zero gaps, zero overlaps and zero trailing
bytes. `mismatches` is the number of objects where the modelled map counter disagrees with the
counter cdb logged at that object. `re-emit` is `model.parse` followed by `Model.emit`, which
recomputes every class and object token from scratch.

| part | stream | bytes | objects | base | tiles | mismatches | re-emit |
|---|---|---|---|---|---|---|---|
| `boss1_front_rect_blind` | `ResolvedFeatures` | 11073 | 321 | 109 | yes | 0 | identical |
| | `CMgr` | 1957 | 28 | 3 | yes | 0 | identical |
| | `Config-0-ModelHeader` | 2315 | 67 | 3 | yes | 0 | identical |
| | `Config-0` | 25212 | 123 | 4 | yes | 0 | identical |
| `boss2_front_rect_blind` | `ResolvedFeatures` | 16174 | 500 | 110 | yes | 0 | identical |
| | `CMgr` | 2019 | 29 | 3 | yes | 0 | identical |
| | `Config-0-ModelHeader` | 2471 | 72 | 3 | yes | 0 | identical |
| | `Config-0` | 25316 | 126 | 4 | yes | 0 | identical |
| `boss3_front_rect_blind` | `ResolvedFeatures` | 21205 | 679 | 111 | yes | 0 | identical |
| | `CMgr` | 2081 | 30 | 3 | yes | 0 | identical |
| | `Config-0-ModelHeader` | 2627 | 77 | 3 | yes | 0 | identical |
| | `Config-0` | 25420 | 129 | 4 | yes | 0 | identical |
| `boss4_front_rect_blind` | `ResolvedFeatures` | 26236 | 858 | 112 | yes | 0 | identical |
| | `CMgr` | 2143 | 31 | 3 | yes | 0 | identical |
| | `Config-0-ModelHeader` | 2783 | 82 | 3 | yes | 0 | identical |
| | `Config-0` | 25524 | 132 | 4 | yes | 0 | identical |
| `boss_face` | `ResolvedFeatures` | 19281 | 391 | 110 | yes | 0 | identical |
| | `CMgr` | 2059 | 33 | 3 | yes | 0 | identical |
| | `Config-0-ModelHeader` | 2471 | 72 | 3 | yes | 0 | identical |
| | `Config-0` | 25300 | 126 | 4 | yes | 0 | identical |
| `BASELINE_40x20x10` | all four | | 321 / 28 / 67 / 123 | | yes | 0 | identical |
| `TWOPAD_d5` | all four | | 400 / 33 / 72 / 126 | | yes | 0 | identical |
| `THREEFEATURE_pad_cut_pad` | all four | | 615 / 40 / 77 / 129 | | yes | 0 | identical |

So `CMgr`, `ModelHeader` and `Config-0` are ordinary `su_CArchive` streams and the segmentation
model built for `ResolvedFeatures` transfers to them unchanged, with the same
`+2 / +1 / 0 / 0` map-counter increment rule and the same 6-byte stream header. Their map counter
starts at **3** (`CMgr`, `ModelHeader`) or **4** (`Config-0`), not at 109-112: each is opened by
its own archive, and only two or three entries precede the first object.

Seven parts were traced, not the whole corpus. Every part traced tiled cleanly and re-emitted
exactly, with no exceptions, but the claim is seven parts.

`ThirdPtyStore/VisualStates` tiles as well (33 / 38 / 43 objects for 1 / 2 / 3 features) but
reports a counter mismatch at every object after the first and does **not** re-emit. Its archive
does not share the combined class-and-object index space the other four use, so the node model
does not apply to it as written. It is left alone; see §4.

## 3. The per-feature block, per stream

`nodediff.py` aligns the node sequences of the three same-family parts on
`(kind, class name)` and prints each node's body length in all three, which separates a node that
is *inserted* per feature from a node whose *body grows* per feature.

### `Contents/CMgr` — +62 bytes, +1 object per feature

```
node  kind        class                    boss1 boss2 boss3
 10   null        -                          140   148   156   grows +8
 12   definition  moLinkedAtomIdNode_c        56    32    32
 13   classref    moLinkedAtomIdNode_c         -    56    32   inserted
 14   classref    moLinkedAtomIdNode_c         -     -    56
 22   null        -                           44    52    60   grows +8
 28   definition  suObList                    38    50    62   grows +12
```

* node 10 holds `u32 count` followed by `count` entries of `(u32 atom id, u32 0)`; the ids run
  101, 102, 103, … (`0x65`, `0x66`, `0x67`). +8 bytes.
* nodes 12..14 are a singly linked list of `moLinkedAtomIdNode_c`. Every node but the last has a
  32-byte body ending in the *next* id; the last has a 56-byte body. Growth inserts one 32-byte
  link, so the per-feature block is one object, 34 bytes on the wire. +34 bytes.
* node 22 holds `u32 0, u32 0xffffffff, u32 count`, then `count` entries of
  `(u32 atom id, u32 0)` in **reverse** id order, then a fixed 24-byte trailer. +8 bytes.
* node 28 holds `u16 0, u32 count`, then `count` entries of `(u32 feature id, u64 stamp)`; the
  feature ids are the tree ids of the extrusions (40, 47, 32 on `boss3`). +12 bytes.

8 + 34 + 8 + 12 = **62**, which is exactly the measured stream growth
(1957 → 2019 → 2081 → 2143 → 2205 → … on `boss1..boss8`, constant +62).

The `u16` at `CMgr` byte 1414 that `REPORT.md` §4 found equal to *n* is the `u32 count` of node 10
read as a `u16`.

### `Contents/Config-0-ModelHeader` and `Header2` — +156 bytes, +5 objects per feature

The stream is a `suObList` of `moLogs_c` entries, each followed by its `moStamp_c` records. Every
`moStamp_c` body is `u32 flag, u32 0, time_t, "Created"|"Modified" (UTF-16), u32 tree id,
node name (UTF-16)`. The repeated unit is five objects:

```
classref moLogs_c   (2)   0200
classref moStamp_c  (28)  Created
classref moStamp_c  (52)  Modified  id=<sketch id>   "SketchK"
classref moLogs_c   (2)   0100
classref moStamp_c  (62)  Created   id=<feature id>  "Boss-ExtrudeK"
```

(2+2) + (2+28) + (2+52) + (2+2) + (2+62) = **156**, exactly the measured growth
(2315 → 2471 → 2627 → 2783 → 2939, constant +156). The last `moStamp_c` in the stream carries an
extra 8-byte `time_t, u32 id` tail (70 bytes instead of 62), so growth moves that tail onto the
new final copy.

The `u16` at byte 77 equal to `24 + 2n` is the `suObList` element count: 24 fixed log entries plus
two per feature, which is the two `moLogs_c` objects in the unit.

### `Contents/Config-0` — +104 bytes, +3 objects per feature

```
node  kind        class          boss1 boss2 boss3
 34   null        -                  -     -    24   inserted
 35   null        -                  -     -    58   inserted
 36   classref    moAtom_c           -     -     0   inserted
121   null        -                299   315   331   grows +16
```

(2+24) + (2+58) + (2+0) + 16 = **104**, matching 25212 → 25316 → 25420 → 25524. The step is not
constant beyond four features (`boss5` is 25562, +38), so `Config-0` growth is regular only over
the range where it was observed.

## 4. Which streams are load-critical

Measured through `.rescratch/sw/measure.py`, control before and after, one fresh subprocess per
candidate, absolute paths, dialog dismisser running. Every batch reported `control healthy: True`
with the control at 8000.000000000001 mm³ on both sides.

The emitted container that produced every volume in §5 holds 27 streams. Reading them back with
`SldprtArchive` shows which of the feature-count-scaling streams the writer actually ships:

| stream | in the emitted container | status | evidence |
|---|---|---|---|
| `Contents/Config-0-ResolvedFeatures` | patched donor copy | load-critical | the tree, the sketches and the dimensions live here |
| `Contents/CMgr` | verbatim donor copy | load-critical | its count field patched without growing the body crashes SOLIDWORKS on open (`REPORT.md` §5, `T4cmgr`) |
| `Contents/Config-0-ModelHeader` + `Header2` | verbatim donor copy | load-critical | same, `T3H` / `T4H` |
| `Contents/Config-0` | verbatim donor copy | load-critical | inherited unchanged in every measured write |
| `Contents/Definition` | verbatim donor copy | load-critical | inherited unchanged in every measured write |
| `Contents/Config-0-Partition` | Kit-synthesised blank | **droppable** | every §5 volume is a genuine rebuild from the records, not a cached body |
| `Contents/Config-0-LWDATA`, `Contents/DisplayLists` | Kit-synthesised | **stale-safe** | present but never feature-count-shaped; 17 correct volumes across 1 to 6 features, plus `cvB` / `cvC` in `.rescratch/sw/out/measure_cv1.json` |
| `_MO_VERSION_18000/Biography` | Kit-synthesised | **stale-safe** | same: one fixed shape, 1 to 6 features all build correctly |
| `ThirdPtyStore/VisualStates` | **absent** | **droppable** | the writer never emits it and every measured write opens and rebuilds |

So `VisualStates` and `Biography` never needed the segmentation work, and `DisplayLists` /
`LWDATA` / `Partition` do not scale with the feature count in the shipped writer at all. The three
streams that do have to be feature-count-correct are `CMgr`, `ModelHeader` / `Header2` and
`Config-0`, which is exactly the set §3 characterises. That is why the `VisualStates` counter
mismatch in §2 is recorded rather than chased.

## 5. Measured results

Through the shipped `write_sldprt` path, with `.rescratch/sw/measure.py`. `nbossN` is a
FreeCAD-format document of *N* disjoint blind rectangular pads on the front plane, built by
`.rescratch/sw/nboss.py`; `kit_*` are the authored FreeCAD sources in `.rescratch/sw/fcstd`. The
control is `BASELINE_40x20x10` at 8000.000000000001 mm³ before and after every batch.

| candidate | donor | expected mm³ | measured mm³ | bodies | solid features built |
|---|---|---|---|---|---|
| `nboss1` | `boss1_front_rect_blind` | 1476 | 1476.0000000000002 | 1 | 1 |
| `nboss2` | `boss2_front_rect_blind` | 4066 | 4065.9999999999995 | 2 | 2 |
| `nboss3` | `boss3_front_rect_blind` | 11954 | 11954.0 | 3 | 3 |
| `nboss4` | `boss4_front_rect_blind` | 33896 | 33895.999999999985 | 4 | **4** |
| `nboss5` | `boss5_front_rect_blind` | 57546 | 57545.999999999985 | 5 | **5** |
| `nboss6` | `boss6_front_rect_blind` | 80610 | 80609.99999999996 | 6 | **6** |
| `kit_boss_cut_cut_cut` | `boss_cut_cut_cut` | 33324 | 33324.00000000001 | 1 | 4 |
| `kit_boss_cut` | `boss_cut` | 34080 | 34080.00000000001 | 1 | 2 |
| `kit_boss_cut_cut` | `boss_cut_cut` | 33580 | 33580.00000000001 | 1 | 3 |
| `kit_boss_blind` | `boss1_front_rect_blind` | 18000 | 18000.0 | 1 | 1 |
| `kit_circle_boss` | `circle_boss` | 5541.769440932396 | 5541.769440932395 | 1 | 1 |
| `kit_boss_midplane` | `boss1_front_rect_blind` | 17280 | 17279.999999999996 | 1 | 1 |
| `kit_boss_reversed` | `boss1_front_rect_blind` | 11264 | 11264.0 | 1 | 1 |
| `kit_boss_right_plane` | `boss_right_plane` | 5544 | 5544.0 | 1 | 1 |
| `kit_boss_top_plane` | `boss_top_plane` | 10296 | 10295.999999999998 | 1 | 1 |
| `kit_boss_boss` | `boss2_front_rect_blind` | 28800 | **32000.0** | **2** | 2 |

`kit_boss_boss` is the merge-result case and is the one entry that is wrong: the target's second
boss is concentric with and overlaps the first, so SOLIDWORKS should fuse them into one 28800 mm³
body, and instead it keeps two bodies totalling 32000 mm³. See §6.

Records: `.rescratch/sw/out/measure_nboss.json`, `measure_nboss56.json`, `measure_merge.json`.

## 6. Merge-result: what the measurements say, and why it is not a single flag

The donor family that backs an *n*-boss target is `boss1..boss8_front_rect_blind`, whose bosses
are **disjoint** tiles along X. Those parts were authored through
`FeatureManager.FeatureExtrusion3` with `Merge = True` (`.rescratch/corpus/scripts/swcom.py`), and
they still save as *n* separate bodies, because merging only happens where the solids actually
touch. `boss_face`, authored the same way with a second boss that *does* overlap the first,
saves with `body_count = 1` (`.rescratch/donors/manifest.json`).

So the two authored parts differ in body count while both were authored with merge enabled. What
the second feature's records carry is therefore not merely a merge boolean but the resolved
feature scope — which existing body the extrusion was combined into. Patching the donor's sketch
corners so the two rectangles overlap does not rewrite that scope, so the target keeps the
donor's "new body" outcome.

That also means a merged 2-boss donor cannot simply be added to the library: `select_donor` keys
on `(operation, profile, support, end condition)` per feature, which is identical for the disjoint
and the overlapping stack, so a merged donor would replace `boss2_front_rect_blind` for every
2-boss target and would break the disjoint cases that §5 measures as correct. Cracking
merge-result needs an overlap dimension in the donor key as well as the field itself, and neither
is measured here. `kit_boss_boss` is reported wrong rather than claimed fixed.

## 5. Files

New in this directory: `multitrace.py` (multi-span trace driver), `blocks.py` (insertion-run
diff), `nodediff.py` (aligned per-node body-length table), `bodydump.py` (hex of chosen node
bodies), `growstream.py` (count-field relocation across a growth plan), `spans.py`, `ids.py`,
`libcheck.py`. `tracelog.py` gained the span field; `segment.py` and `model.py` gained a stream
argument and span filtering, with the previous defaults unchanged — the nine parts of
`REPORT.md` still segment and re-emit byte-identically through the modified code.

Logs: `out/cdb_multi_<label>.log`. Machine-readable: `out/multitrace.json`,
`out/blocks_*.json`, `out/nodediff_*.json`.
