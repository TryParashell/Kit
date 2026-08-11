<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

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
plain diff: two parts of the _same_ family differ only by the repeated unit.

`tiles` means the segmentation covers the stream with zero gaps, zero overlaps and zero trailing
bytes. `mismatches` is the number of objects where the modelled map counter disagrees with the
counter cdb logged at that object. `re-emit` is `model.parse` followed by `Model.emit`, which
recomputes every class and object token from scratch.

| part                       | stream                 | bytes | objects             | base | tiles | mismatches | re-emit   |
| -------------------------- | ---------------------- | ----- | ------------------- | ---- | ----- | ---------- | --------- |
| `boss1_front_rect_blind`   | `ResolvedFeatures`     | 11073 | 321                 | 109  | yes   | 0          | identical |
|                            | `CMgr`                 | 1957  | 28                  | 3    | yes   | 0          | identical |
|                            | `Config-0-ModelHeader` | 2315  | 67                  | 3    | yes   | 0          | identical |
|                            | `Config-0`             | 25212 | 123                 | 4    | yes   | 0          | identical |
| `boss2_front_rect_blind`   | `ResolvedFeatures`     | 16174 | 500                 | 110  | yes   | 0          | identical |
|                            | `CMgr`                 | 2019  | 29                  | 3    | yes   | 0          | identical |
|                            | `Config-0-ModelHeader` | 2471  | 72                  | 3    | yes   | 0          | identical |
|                            | `Config-0`             | 25316 | 126                 | 4    | yes   | 0          | identical |
| `boss3_front_rect_blind`   | `ResolvedFeatures`     | 21205 | 679                 | 111  | yes   | 0          | identical |
|                            | `CMgr`                 | 2081  | 30                  | 3    | yes   | 0          | identical |
|                            | `Config-0-ModelHeader` | 2627  | 77                  | 3    | yes   | 0          | identical |
|                            | `Config-0`             | 25420 | 129                 | 4    | yes   | 0          | identical |
| `boss4_front_rect_blind`   | `ResolvedFeatures`     | 26236 | 858                 | 112  | yes   | 0          | identical |
|                            | `CMgr`                 | 2143  | 31                  | 3    | yes   | 0          | identical |
|                            | `Config-0-ModelHeader` | 2783  | 82                  | 3    | yes   | 0          | identical |
|                            | `Config-0`             | 25524 | 132                 | 4    | yes   | 0          | identical |
| `boss_face`                | `ResolvedFeatures`     | 19281 | 391                 | 110  | yes   | 0          | identical |
|                            | `CMgr`                 | 2059  | 33                  | 3    | yes   | 0          | identical |
|                            | `Config-0-ModelHeader` | 2471  | 72                  | 3    | yes   | 0          | identical |
|                            | `Config-0`             | 25300 | 126                 | 4    | yes   | 0          | identical |
| `BASELINE_40x20x10`        | all four               |       | 321 / 28 / 67 / 123 |      | yes   | 0          | identical |
| `TWOPAD_d5`                | all four               |       | 400 / 33 / 72 / 126 |      | yes   | 0          | identical |
| `THREEFEATURE_pad_cut_pad` | all four               |       | 615 / 40 / 77 / 129 |      | yes   | 0          | identical |

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
is _inserted_ per feature from a node whose _body grows_ per feature.

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

- node 10 holds `u32 count` followed by `count` entries of `(u32 atom id, u32 0)`; the ids run
  101, 102, 103, … (`0x65`, `0x66`, `0x67`). +8 bytes.
- nodes 12..14 are a singly linked list of `moLinkedAtomIdNode_c`. Every node but the last has a
  32-byte body ending in the _next_ id; the last has a 56-byte body. Growth inserts one 32-byte
  link, so the per-feature block is one object, 34 bytes on the wire. +34 bytes.
- node 22 holds `u32 0, u32 0xffffffff, u32 count`, then `count` entries of
  `(u32 atom id, u32 0)` in **reverse** id order, then a fixed 24-byte trailer. +8 bytes.
- node 28 holds `u16 0, u32 count`, then `count` entries of `(u32 feature id, u64 stamp)`; the
  feature ids are the tree ids of the extrusions (40, 47, 32 on `boss3`). +12 bytes.

8 + 34 + 8 + 12 = **62**, which is exactly the measured stream growth
(1957 → 2019 → 2081 → 2143 → 2205 → … on `boss1..boss8`, constant +62).

The `u16` at `CMgr` byte 1414 that `REPORT.md` §4 found equal to _n_ is the `u32 count` of node 10
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

### Terminal modifiers also require the model-header spatial frame and creation pair

The SOLIDWORKS-authored rectangular boss plus one edge fillet has a 2371-byte
`Contents/Config-0-ModelHeader`. The 69-object cdb trace in
`.rescratch/trace/out/segments_bossfillet_header.json` tiles the stream with no gaps, overlaps,
counter mismatches or trailing bytes. Its final `suObList` object begins at 2195 and is 176 bytes.

The final object body has this version-18000 shape:

```
classref suObList
10 zero bytes
u32 spatial-frame-present
if present: 10 doubles
10 bytes of 0xff
empty class declaration
40 zero bytes
u32 1
16 zero bytes
u32 1
```

The ten doubles are `(cx, cy, cz, maxx, maxy, maxz, minx, miny, minz, radius)` in metres. The
first three values are the bounding-box centre, the following six are the maximum and minimum
corners, and `radius = sqrt(hx² + hy² + hz²)` is the bounding sphere radius. The 40 × 20 × 10 mm
boss therefore writes `(0, 0, .005, .02, .01, .01, -.02, -.01, 0, .0229128784747792)`.
Radius-two and radius-three fillets have the same frame because the selected edge treatment does
not change the body's extents.

The oracle matrix isolates two independent requirements:

| candidate header change                                         | opens |         volume mm³ |
| --------------------------------------------------------------- | ----: | -----------------: |
| no frame and unrelated creation pair                            | crash |                  — |
| typed frame only                                                |   yes |  8000.000000000001 |
| first archived creation field only                              |   yes |  8000.000000000001 |
| second archived creation field only                             |   yes |  8000.000000000001 |
| both archived creation fields set to the generation predecessor |   yes | 7991.4159265358985 |

Changing the seven system-folder action stamps alone still leaves the boss unfilleted. The two
creation fields in the `moExtObject_c` tail must both equal the action stamp immediately preceding
the fillet generation; neither field works alone. The production writer derives that value as the
first recovered feature action stamp minus one and calculates the spatial frame from the source
dimensions. No header bytes are copied.

The fully generated `sw_boss_fillet.firstprinciples.v6.sldprt` opens with one body and the live
tree `Sketch1 → Boss-Extrude1 → Fillet1` at 7991.4159265358985 mm³. Driving
`D1@Fillet1` from 2 mm to 3 mm rebuilds successfully and changes the measured volume to
7980.6858347057705 mm³, exactly matching the independently authored radius-three control. Raw
records are `.rescratch/sw/out/measure_bossfillet_header_matrix.json` and
`.rescratch/sw/out/measure_bossfillet_creation_fields.json`.

### Edge chamfer is fully typed and independently parameter-checked

The controlled `PartDesign::Chamfer` source is a 40 × 20 × 10 mm boss with an equal-distance
2 mm treatment on `Pad.Edge5`. Its SOLIDWORKS control uses `Chamfer_c`, preserves the selection as
`(Boss-Extrude1, Edge3)`, and has the native tree
`Sketch1 → Boss-Extrude1 → Chamfer1`.

The multi-stream trace characterises every load-bearing stream without retaining any control
bytes:

| stream                               |  bytes | objects | result                                                |
| ------------------------------------ | -----: | ------: | ----------------------------------------------------- |
| `Contents/Config-0-ResolvedFeatures` | 15,811 |     468 | exact, zero unparsed spans                            |
| `Contents/CMgr`                      |  1,973 |      28 | exact                                                 |
| `Contents/Config-0-ModelHeader`      |  2,373 |      69 | exact                                                 |
| `Contents/Config-0`                  | 25,470 |     128 | exact                                                 |
| `ThirdPtyStore/VisualStates`         |  1,593 |       — | intentionally omitted; independently proved droppable |

`resolved_bosschamfer_program.py` emits the resolved-feature stream from 3,722 typed primitive
operations owned by 515 traced objects. The generated 15,811-byte stream has SHA-256
`d8b6f859a0e60e5e6307833ce502723123663bc9e25ca2b46e74f608dd5b9450`. The last previously
unknown 24-byte region is the `Chamfer_c` direct surface-selection array: a tag, a `long`, a
`u16` count, and six direct `i32` surface identifiers. The generator now recognises and emits
that grammar; it does not contain an opaque span, encoded block, or donor-file read.

The writer computes the same model-header spatial frame described above and derives both
creation fields from the recovered feature action stamp. It patches the equal-distance value in
all six typed dimension locations, the two positive spatial records, and their two signed
counterparts. No field is supplied by a CAD application at conversion time.

The fully generated `sw_boss_chamfer.firstprinciples.v1.sldprt` opens without load errors or
warnings, rebuilds, reports one body, and exposes a live unsuppressed `Chamfer1`. At 2 mm its
volume is 7980.000000000002 mm³ and surface area is 2784.284271247462 mm². Driving
`D1@Chamfer1` to 3 mm rebuilds the same file to 7955.000000000001 mm³ and
2773.4264068711927 mm², exactly matching a separately authored 3 mm control. This proves native
parameter ownership, feature-history ownership, and regenerated B-rep ownership together.

### Inward shell is fully typed and independently parameter-checked

The controlled `PartDesign::Thickness` source is a 40 × 20 × 10 mm boss with `Pad.Face6`
removed and a 2 mm inward wall. Its SOLIDWORKS control uses `moShell_c`, preserves the resolved
face witnesses as `(Boss-Extrude1, Face1)` and `(Boss-Extrude1, Face4)`, and has the native tree
`Sketch1 → Boss-Extrude1 → Shell1`.

The multi-stream trace covers every load-bearing byte without retaining any control bytes:

| stream                               |  bytes | objects | result                                                |
| ------------------------------------ | -----: | ------: | ----------------------------------------------------- |
| `Contents/Config-0-ResolvedFeatures` | 13,868 |     422 | exact, zero unparsed spans                            |
| `Contents/CMgr`                      |  1,973 |      28 | exact                                                 |
| `Contents/Config-0-ModelHeader`      |  2,369 |      69 | exact                                                 |
| `Contents/Config-0`                  | 25,212 |     123 | exact                                                 |
| `ThirdPtyStore/VisualStates`         |  1,593 |       — | intentionally omitted; independently proved droppable |

`resolved_bossshell_program.py` emits the resolved-feature stream from 3,326 typed primitive
operations owned by 497 traced serializer callsites. Its 13,868-byte default has SHA-256
`19572f2d262a02c450ac66315089598074f506880ac0df03f8a74670ffac0191`. The program contains no
opaque span, encoded block, donor-file read, or CAD application call.

The writer proves the selected FreeCAD subelement from the pad's first-principles OpenCascade
B-rep: it must be the same-sense planar face at the pad depth with a positive Z normal. It then
maps the inward thickness into all six recovered native dimension fields and updates the inner
wall witness, outer X witnesses, pad depth, model-header bounds, action stamps, and the
shell-specific one-atom configuration graph. The last item matters: the shell's `CMgr` atom
links to tree 32, while its single-view `Config-0` keeps only tree 34. Treating it like either a
generic two-feature history or the two-view fillet/chamfer envelope makes SOLIDWORKS terminate
during open.

The fully generated `sw_boss_shell.firstprinciples.v2.sldprt` opens in SOLIDWORKS 2025 SP5.0
with no load errors or warnings, rebuilds, reports one body, and exposes live unsuppressed
`Boss-Extrude1` and `Shell1` features. At 2 mm it measures 3392.0000000000014 mm³ and
3632.0000000000005 mm². Driving only `D1@Shell1` to 3 mm rebuilds to
4668.000000000002 mm³ and 3472.0 mm², matching the independently authored 3 mm control within
floating-point precision. Conversion and native stream generation use only Python; SOLIDWORKS
was used solely for the isolated oracle check.

### Sketch-normal linear pattern is typed, direction-correct, and parameter-checked

The controlled `PartDesign::LinearPattern` source repeats a 10 × 10 × 5 mm pad three times at a
5 mm pitch along the sketch `N_Axis`. Its SOLIDWORKS counterpart uses `moLPattern_c`, retains the
seed and direction selections as `(Boss-Extrude1, Edge4)` and `(Boss-Extrude1, Edge3)`, and has
the native tree `Sketch1 → Boss-Extrude1 → LPattern1`.

`resolved_bosslinearpattern_program.py` emits the 22,264-byte resolved-feature stream from 5,161
typed operations owned by 598 traced serializers. Its default SHA-256 is
`fa69899e0a0d5f3271f2e1a9fff8e8eae396c7492f8910ef3ba470b3f53bb370`; there are no unknown
spans or copied vendor blocks. The recovered `Config-0` pattern annotation manager contributes
another 104 typed operations and no opaque bytes. The writer maps occurrence count to `D1`,
pitch to `D3`, and emits the positive sketch-normal direction through the native flip byte at
resolved offset 18,577 together with its signed pitch, unit-vector, and transform witnesses.

Direction was checked independently because matching volume alone cannot distinguish +Z from
-Z. The generated part opens in SOLIDWORKS 2025 SP5.0 with no errors or warnings, rebuilds to one
body, and measures 1,500 mm³, 800 mm², with centre of mass at +7.5 mm Z. Driving only `D3` from
5 mm to 4 mm gives 1,300 mm³, 720 mm², and +6.5 mm Z; driving only `D1` from three to four
instances gives 2,000 mm³, 1,000 mm², and +10 mm Z. Driving the seed depth from 5 mm to 6 mm
gives 1,600 mm³, 840 mm², and +8 mm Z. All conversion-time emission remains Python-only;
SOLIDWORKS was used solely as the isolated oracle.

### Sketch-normal circular pattern is fully typed, partial-angle capable, and parameter-checked

The controlled `PartDesign::PolarPattern` source rotates a 10 × 5 × 5 mm pad about the sketch
`N_Axis`. Its SOLIDWORKS counterpart uses `moCirPattern_c`, retains the seed and axis witnesses
as `(Boss-Extrude1, Edge4)` and `(Boss-Extrude1, Edge1)`, and has the native tree
`Sketch1 → Boss-Extrude1 → CirPattern1`.

The recovered stream set is complete and independently re-emittable:

| stream                               |  bytes | objects | result                     |
| ------------------------------------ | -----: | ------: | -------------------------- |
| `Contents/Config-0-ResolvedFeatures` | 19,603 |     553 | exact, zero unparsed spans |
| `Contents/CMgr`                      |  2,059 |      33 | exact                      |
| `Contents/Config-0-ModelHeader`      |  2,379 |      69 | exact                      |
| `Contents/Config-0`                  | 25,520 |     131 | exact                      |

`resolved_bosscircularpattern_program.py` emits the resolved-feature stream from 4,578 typed
operations owned by 600 recovered serializer callsites. Its default SHA-256 is
`ced6aec7dd5b4bc323416dfd89afe75d684aa8ad9010b54438ec516798f91be3`; there are no opaque
spans, encoded blocks, donor bytes, or conversion-time CAD calls. Occurrence count is stored in
one integer and two double fields, angular span in three radian fields, and the FreeCAD-positive
axis maps to the recovered native flip byte at resolved offset 17,876. The circular and linear
controls independently prove that their 512-byte `Config-0` pattern annotation managers are
byte-identical, so both use the same typed 104-operation manager.

The generated full-circle part opens in SOLIDWORKS 2025 SP5.0 with no errors or warnings,
rebuilds to one body, and measures 1,000 mm³, 800 mm², with centre of mass at Z = 2.5 mm.
Driving only `D3@CirPattern1` from 360° to 180° gives 891.7468245269455 mm³,
751.7949192431123 mm², and centre `(-1.0192586265744237, 2.2255661537030473, 2.5)` mm,
matching the independently authored FreeCAD 180° source. Driving only `D1@CirPattern1` from
four to five gives 1,148.462594927217 mm³ and 912.3372979119898 mm², matching a separately
authored five-instance FreeCAD source. Driving the seed depth from 5 mm to 6 mm updates the
dependent pattern to 1,200 mm³, 880 mm², and Z centre 3 mm.

That five-instance source also exposed tolerance-equivalent but separately numbered vertices in
FreeCAD's Boolean B-rep. The CAD-free OpenCascade reader now canonicalises only coordinate keys
that agree to fifteen significant digits and are within the larger recorded vertex tolerance;
each bucket is capped at 64 candidates. This retains strict topology validation without accepting
an unbounded or merely bounding-box-level proof. SOLIDWORKS and FreeCAD were used only as
isolated oracles; production conversion and native stream emission remain Python-only.

## 4. Which streams are load-critical

Measured through `.rescratch/sw/measure.py`, control before and after, one fresh subprocess per
candidate, absolute paths, dialog dismisser running. Every batch reported `control healthy: True`
with the control at 8000.000000000001 mm³ on both sides.

The current emitted container holds 27 streams. Reading it back with `SldprtArchive` and the
stream-specific decoders shows which records are load-critical and how each is now emitted:

| stream                                              | in the emitted container     | status         | evidence                                                                                                                                      |
| --------------------------------------------------- | ---------------------------- | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `Contents/Config-0-ResolvedFeatures`                | typed feature-family program | load-critical  | the tree, sketches, selections and editable dimensions live here; every generated program has zero opaque spans                               |
| `Contents/CMgr`                                     | typed archive grammar        | load-critical  | every one of its 1,957 reference-body bytes is declared; the 96-byte display cache is a validated zero field, not injectable data             |
| `Contents/Config-0-ModelHeader` + `Header2`         | typed archive grammar        | load-critical  | tree logs, creation pairs and the spatial frame are calculated from source history and geometry                                               |
| `Contents/Config-0`                                 | typed field program          | load-critical  | view, annotation and pattern managers are selected from explicit source semantics; zero opaque bytes remain                                   |
| `Contents/Definition`                               | typed primitive fields       | load-critical  | all 3,618 reference-body bytes are accounted for and arbitrary residual injection is rejected                                                 |
| `Contents/Config-0-Partition`                       | Kit-synthesised blank        | **droppable**  | every §5 volume is a genuine rebuild from the records, not a cached body                                                                      |
| `Contents/Config-0-LWDATA`, `Contents/DisplayLists` | Kit-synthesised              | **stale-safe** | present but never feature-count-shaped; 17 correct volumes across 1 to 6 features, plus `cvB` / `cvC` in `.rescratch/sw/out/measure_cv1.json` |
| `_MO_VERSION_18000/Biography`                       | Kit-synthesised              | **stale-safe** | same: one fixed shape, 1 to 6 features all build correctly                                                                                    |
| `ThirdPtyStore/VisualStates`                        | **absent**                   | **droppable**  | the writer never emits it and every measured write opens and rebuilds                                                                         |

`VisualStates` is omitted because the application-oracle matrix proves it is not required for
load, rebuild, native-tree editing, or body regeneration. `Biography`, `DisplayLists`, `LWDATA`
and `Partition` are deterministic typed or calculated streams and do not carry source-feature
bytes. No production path reads an oracle file or retains an unexplained vendor span.

## 5. Measured results

The first fifteen rows below are the historical oracle matrix that established the stream
grammar. The final row is the current typed boss-to-boss program rechecked after the donor-era
implementation was removed. `nbossN` is a FreeCAD-format document of _N_ disjoint blind
rectangular pads on the front plane; `kit_*` are authored FreeCAD sources. The control is
`BASELINE_40x20x10` at 8000.000000000001 mm³ before and after every batch.

| candidate              | oracle family or typed program    | expected mm³      | measured mm³           | bodies | solid features built |
| ---------------------- | --------------------------------- | ----------------- | ---------------------- | ------ | -------------------- |
| `nboss1`               | `boss1_front_rect_blind`          | 1476              | 1476.0000000000002     | 1      | 1                    |
| `nboss2`               | `boss2_front_rect_blind`          | 4066              | 4065.9999999999995     | 2      | 2                    |
| `nboss3`               | `boss3_front_rect_blind`          | 11954             | 11954.0                | 3      | 3                    |
| `nboss4`               | `boss4_front_rect_blind`          | 33896             | 33895.999999999985     | 4      | **4**                |
| `nboss5`               | `boss5_front_rect_blind`          | 57546             | 57545.999999999985     | 5      | **5**                |
| `nboss6`               | `boss6_front_rect_blind`          | 80610             | 80609.99999999996      | 6      | **6**                |
| `kit_boss_cut_cut_cut` | `boss_cut_cut_cut`                | 33324             | 33324.00000000001      | 1      | 4                    |
| `kit_boss_cut`         | `boss_cut`                        | 34080             | 34080.00000000001      | 1      | 2                    |
| `kit_boss_cut_cut`     | `boss_cut_cut`                    | 33580             | 33580.00000000001      | 1      | 3                    |
| `kit_boss_blind`       | `boss1_front_rect_blind`          | 18000             | 18000.0                | 1      | 1                    |
| `kit_circle_boss`      | `circle_boss`                     | 5541.769440932396 | 5541.769440932395      | 1      | 1                    |
| `kit_boss_midplane`    | `boss1_front_rect_blind`          | 17280             | 17279.999999999996     | 1      | 1                    |
| `kit_boss_reversed`    | `boss1_front_rect_blind`          | 11264             | 11264.0                | 1      | 1                    |
| `kit_boss_right_plane` | `boss_right_plane`                | 5544              | 5544.0                 | 1      | 1                    |
| `kit_boss_top_plane`   | `boss_top_plane`                  | 10296             | 10295.999999999998     | 1      | 1                    |
| `kit_boss_boss`        | typed `resolved_bossboss_program` | 28800             | **28799.999999999996** | **1**  | 2                    |

`kit_boss_boss` now opens without errors or warnings, rebuilds, and exposes
`Sketch1 → Boss-Extrude1 → Sketch2 → Boss-Extrude2` as a single fused body. See §6.

Records: `.rescratch/sw/out/measure_nboss.json`, `measure_nboss56.json`, `measure_merge.json`.

## 6. Merge-result closure

The historical experiment correctly showed that merge was not a standalone boolean: the native
records also own the resolved feature scope. That gap is now closed by a first-principles typed
program, not by selecting or patching a source part. `resolved_bossboss_program.py` emits 16,474
bytes with SHA-256
`9292aa8eb59293e1983cdde1cda36aeba60c1b5e6b55ebf036bdac91519047a9`, while the writer derives
both sketches, depths, source links, merge scope, model-header bounds, atom graph and Parasolid
body from the FreeCAD document.

The current `kit_boss_boss.current.sldprt` opens in SOLIDWORKS 2025 SP5.0 with zero errors or
warnings, rebuilds to one body, and initially measures 28,799.999999999996 mm³, 7,880 mm², with
Z centre 7.083333333333331 mm. Driving only `D1@Boss-Extrude2` from 25 mm to 30 mm rebuilds the
same native feature to 30,400.000000000004 mm³ and 8,240 mm², with Z centre
8.157894736842108 mm. The successful dependent-body change proves that the fused result is owned
by the editable SOLIDWORKS history rather than a cached or flattened body.

## 7. Files

New in this directory: `multitrace.py` (multi-span trace driver), `blocks.py` (insertion-run
diff), `nodediff.py` (aligned per-node body-length table), `bodydump.py` (hex of chosen node
bodies), `growstream.py` (count-field relocation across a growth plan), `spans.py`, `ids.py`,
`libcheck.py`. `tracelog.py` gained the span field; `segment.py` and `model.py` gained a stream
argument and span filtering, with the previous defaults unchanged — the nine parts of
`REPORT.md` still segment and re-emit byte-identically through the modified code.

Logs: `out/cdb_multi_<label>.log`. Machine-readable: `out/multitrace.json`,
`out/blocks_*.json`, `out/nodediff_*.json`.
