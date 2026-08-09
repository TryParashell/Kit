<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# `Contents/Config-0-ResolvedFeatures` — serialization grammar

SOLIDWORKS 2025 (`18000`), corpus `.rescratch/corpus/parts` (31 parts) + `.rescratch/corpus2/parts`
(20 parts) + `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024` (57 parts).
Tools in `.rescratch/grammar/`. Nothing under `src/` or `tests/` was modified.

This builds on `.rescratch/corpus/REPORT.md` (report 1) and `.rescratch/corpus2/REPORT.md`
(report 2) and does not restate what they established. It resolves four things they left open,
adds the record class that controls the feature tree, and states precisely what still blocks
authoring an arbitrary tree.

Every claim marked CONFIRMED was verified across the whole corpus by script, or measured in
SOLIDWORKS. Claims marked PARTIAL or OPAQUE are called out as such.

---

## 0. Summary of what is new here

| finding                                                                                                          | status                                      |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `moCompFeature_c` is the feature tree: a fixed-stride array, one entry per tree node, carrying the `KeyWords` id | **CONFIRMED**, 51/51 corpus files           |
| The `xx aa 70 6a` / `xx af 70 6a` "object-index noise" of report 2 §11 is a `u32` Unix `time_t`                  | **CONFIRMED**                               |
| `ff ff 01 00` is `wNewClassTag` (`0xFFFF`) + `u16` schema; schema is 1 for every class in every corpus file      | **CONFIRMED**                               |
| The reader is not MFC's `CArchive`; it is SOLIDWORKS' own `su_CArchive`, exported by name from `swccu.dll`       | **CONFIRMED** (see `WINDBG.md`)             |
| `swXmlContents/KeyWords` starts with a `0x86` tag byte and uses CRLF, not a UTF-8 BOM                            | **CONFIRMED**, and a BOM crashes SOLIDWORKS |
| boss ↔ cut is **not** selected by the tree flags word — it is opaque                                             | measured, corrects report 2 §7.2            |
| end condition (blind ↔ MidPlane) and direction are writable in place for any feature                             | measured, exact                             |
| the sketch support plane is writable in place                                                                    | measured, exact, verified by centre of mass |
| tree order is taken from the `moCompFeature_c` array order                                                       | measured, exact                             |
| the five derived depth copies and the bbox cache must be left stale, not written wrong                           | measured                                    |
| `moCompFeature_c` entry count is the one thing that changes stream length structurally per feature               | **CONFIRMED**                               |

---

## 1. Container framing (context, unchanged)

The `.SLDPRT` is a SOLIDWORKS-proprietary archive of raw-deflate streams with a nibble-swapped
name encoding. `src/convert/adapters/solidworks/container.py` reads and writes it;
`build_sldprt(streams, template=<donor bytes>)` must be given a template because the
`(file_id, local/central/end signature)` triplet has not been inverted. A wrong triplet
hard-crashes SOLIDWORKS.

`Contents/Config-0-Partition` (the Parasolid body cache) can be dropped entirely; SOLIDWORKS
rebuilds the identical solid from `Contents/Config-0-ResolvedFeatures` plus
`swXmlContents/KeyWords`. Every measurement in `results.md` was taken with the Partition dropped,
so every volume quoted is a genuine rebuild from the feature stream.

---

## 2. The archive layer: `su_CArchive`

### 2.1 Tag grammar — CONFIRMED

The stream is a byte-compatible clone of MFC `CArchive` object serialization. Runtime
confirmation is in `WINDBG.md`; the tags are:

| bytes                                                 | meaning                                                                                                    |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `00 00`                                               | `wNullTag` — a null object pointer                                                                         |
| `ff ff` `<u16 schema>` `<u16 nameLen>` `<ascii name>` | `wNewClassTag`: a class _definition_. `CRuntimeClass::Store` writes schema then name length then the name. |
| `<u16 t>` with `t & 0x8000`, `t != 0xffff`            | class _reference_: class map index `t & 0x7fff`                                                            |
| `<u16 t>` with `t & 0x8000 == 0`, `t != 0`            | object _reference_: object map index `t`                                                                   |
| `7f ff` then `<u32>`                                  | `wBigObjectTag` escape for indices ≥ 0x7fff (not seen in this corpus)                                      |

So the constant `CLASS_MARKER = ff ff 01 00` in `src/convert/adapters/solidworks/format.py` is
really `wNewClassTag` followed by **schema 1**. `probe_tags.py` scanned for `ff ff <any schema>`
across seven representative files and found schema 1 for all 41–48 classes in each — so the
existing 4-byte constant is safe for this SOLIDWORKS version, but it is a schema filter, not
part of the marker.

A class definition is emitted the first time an object of that class is written. Later objects of
the same class carry only the 2-byte reference. **This is why features 2+ have no
`ff ff 01 00`, and it is also why a marker walk is not an object segmentation.**

### 2.2 Strings — CONFIRMED

`ff fe ff` is MFC's `_AfxWriteStringLength` Unicode tag (`BYTE 0xff` then `WORD 0xfffe`),
followed by the length and then UTF-16LE characters:

```
ff fe ff <u8 units>                       units <  255
ff fe ff ff <u16 units>                   255 <= units < 0xfffe
```

Only the `u8` form occurs in this corpus.

### 2.3 The map counter — the renumbering constraint

`su_CArchive` keeps one counter (`getMapCount`) that is incremented for **every** class
definition and **every** object, in stream order, starting at 1. A class reference `0x8000|i`
therefore encodes a position in that combined sequence. Consequence, and this is the central
constraint on authoring:

> Inserting or deleting any object anywhere in the stream shifts the map index of every class
> defined after the insertion point, so every class-reference token that targets one of those
> classes has to be renumbered.

`probe_tags.py` shows this directly: the class-reference token inside `moCompFeature_c` is
`0x8076` in a 1-feature file, `0x8077` in a 2-feature file and `0x8078` in a 3-feature file —
the same class, three different indices, because more objects precede its definition.

Renumbering is mechanical _if_ you can enumerate the tokens, and enumerating them needs the
object segmentation, which needs per-class `Serialize` layouts. That is the remaining blocker
(§8). `WINDBG.md` describes the runtime route that lifts it.

---

## 3. `moCompFeature_c` — the feature tree — CONFIRMED

This is the record that decides how many features the part has, in what order, and which
`KeyWords` id each one carries. Report 1 saw only that it grows by 238 bytes per feature.
It is a fixed-stride array.

```
moCompFeature_c record data
  entry 0                      93 bytes
  entry 1 .. entry n-1        119 bytes each
```

so `record_length == 93 + 119 * (n - 1)` where `n` is the number of tree nodes it holds.
`n == 2 * feature_count`: one entry per sketch and one per extrusion, interleaved
`sketch1, feature1, sketch2, feature2, …`. That is **2 entries per feature, not one per tree
node**: the 20-node single-feature baseline carries exactly two entries, for node ids 26 and 32,
and the folders, the three planes and the Origin get no entry at all
(`../records/RESOLVEDFEATURES.md` §5).

Verified by `probe_entries.py` on all 51 corpus files: the length equation holds in every file,
and the id sequence read out of the array equals the `feature_id` field of the corresponding
tree-node name records (and therefore the `id` attribute in `swXmlContents/KeyWords`) in
**51/51** files.

### 3.1 Entry layout

Each entry ends with, relative to the entry end:

| offset     | width | field                                                        | authored or derived                      |
| ---------- | ----- | ------------------------------------------------------------ | ---------------------------------------- |
| `end - 8`  | `u32` | tree-node id, the same value as `KeyWords` `id`              | **AUTHORED**                             |
| `end - 4`  | `u32` | Unix `time_t` of when the node was last touched              | **AUTHORED** (any plausible value works) |
| `end - 12` | `u32` | constant `0x00004650` (18000 = the SOLIDWORKS version stamp) | constant                                 |

The 119-byte entry begins with the 26-byte inter-entry block

```
<u16 class-ref>  00 00  01 00 00 00  00 00 00 40  ff ff ff ff  00 00 00 00  ff fe ff 00  <u16 class-ref>
```

`00 00 00 40` is the generic tree-node flag word `0x40000000`; `ff fe ff 00` is an empty
UTF-16 string; the two class-reference tokens are the ones that renumber with feature count
(§2.3). The remaining 93 bytes are the entry body, identical in every entry of every file
except for the two `u32` fields above:

```
2b 80                       class reference -> moUnitComponent_c (external, index 43)
02 00                       object reference -> the shared component object
00 x 41
ff x 16                     four u32 = -1 (null ids)
00 x 20
50 46 00 00                 u32 = 18000
<u32 node id>
<u32 time_t>
```

The `02 00 00 00` this table used to read as a `u32` = 2 is **not** a scalar. `02 00` is an
object-reference tag and the next two bytes are the first two of the 41-byte zero run, confirmed by
the segmenter at `classref external#43 5673..5675`, `objectref external#2 5675..5766`. The
decomposition is `2 + 2 + 89 = 93`, and the 89 is the `runs_by_version["0"]["18000"]` the layout
table already records for `moCompFeature_c`. The 26-byte inter-entry block is
`classref + u16 0 + u32 1 + u32 0x40000000 + i32 -1 + u32 0 + empty string + classref`, so its
non-tag part is 22 bytes.

### 3.2 Measured behaviour

- Swapping two 119-byte entry pairs reorders the tree. SOLIDWORKS opened the result with the
  tree in the swapped order, one body, and the volume unchanged (`E9`, `results.md`) — so
  **rebuild order comes from this array**, not from stream order.
- Deleting the last entry pair is a 238-byte length change and therefore a map-index change
  (§2.3). Result in `results.md` (`E10`).

---

## 4. Tree-node name records — CONFIRMED (extends report 2 §6.1)

Every tree node is serialized as

```
<u16 class-ref>  ff fe ff  <u8 units>  <utf16le name>  00 00 00 00  <u32 flags>  <u32 node id>
```

`resolvedlib.name_records` / `tree_nodes` find these without needing class markers, which is how
unmarked features 2+ are reachable.

### 4.1 Flag words

Mask `0x7FFFFFFF`; bit `0x80000000` is the tree-expanded UI state and carries no geometry
meaning. Values enumerated across the V8 production corpus (`.rescratch/v8/flagmap.json`) and
the two authored corpora:

| flags                      | node kind                                   | name stems seen                                     |
| -------------------------- | ------------------------------------------- | --------------------------------------------------- |
| `0x40000000`               | folder, sketch, plane data, fillet, pattern | `Comments`, `Sketch*`, `Fillet*`, `*Pattern*`       |
| `0xC0000000`               | reference plane / origin                    | `Front Plane`, `Top Plane`, `Right Plane`, `Origin` |
| `0x40000140`, `0x40000040` | extruded **boss**                           | `Boss-Extrude*`                                     |
| `0x400201CA`               | extruded **cut**                            | `Cut-Extrude*`                                      |
| `0x40000001`               | chamfer                                     | `Chamfer*`                                          |
| `0x40004003`, `0x40004002` | sweep                                       | `Sweep*`                                            |
| `0x40004404`               | loft                                        | `Loft*`                                             |

`flags` at `name_text_end + 4` is **AUTHORED**, and it is the only place a boss is _distinguishable_
from a cut in this stream — there is no `moCut_c` class. But it is **not** what _selects_ the
operation. Measured (`results.md` §1, E1/E2 and A3): flipping cut → boss or boss → cut on a
2-feature donor kills the SOLIDWORKS process, and writing cut flags onto a boss skeleton is
silently ignored and rebuilds a boss. The flags word is a tree annotation that has to agree with
the operation; the operation itself lives in the `moExtrusion_c` / `moICE_c` body and is
**OPAQUE**. This corrects the natural reading of report 2 §7.2.

`node id` at `name_text_end + 8` is **AUTHORED** and must match `moCompFeature_c` and
`swXmlContents/KeyWords`.

The feature _name_ string is a label. It is variable-length, so changing it moves every
subsequent offset; `serialize.py` deliberately keeps the skeleton's name and makes `KeyWords`
agree with it rather than the other way round.

---

## 5. Per-feature geometry

### 5.1 Sketch coordinates — CONFIRMED

Every 2-D sketch coordinate is wrapped in a fixed 18-byte prefix and a 4-byte suffix:

```
00 00 00 00 00 00 f0 3f   (double 1.0)
00 00 00 00 00 00 00 00   (double 0.0)
1e 00                     (u16 30)
<double x>  <double y>    METRES
<u8 role> 00 <u8 class> 00
```

`role` 0 = free point, 2 = point constrained on a curve. `class` 2 = point.
`resolvedlib.sketch_coordinates` enumerates them; assigning each to the last `Sketch*` name
record before it partitions them per sketch exactly (report 2 §6.4, re-verified here).

- **Rectangle**: four free points, corner order `(min,min) (max,max) (min,max) (max,min)`,
  strides `178, 162, 162` — the first gap is 16 bytes longer than the other two, so the uniform
  162-byte stride this section used to claim is right for the last two gaps and wrong for the
  first (`../records/RESOLVEDFEATURES.md` §5). **AUTHORED**.
- **Circle**: one free point (the centre) plus one on-curve point at exactly **17°**. There is
  no radius field; radius is `hypot(dx, dy)`. **AUTHORED** as
  `centre + r·(cos 17°, sin 17°)`.

### 5.2 Depth — CONFIRMED

A dimension-scalar record: a name record whose name is `D1` followed immediately by
`DIMENSION_SCALAR_HEADERS[0]`
(`0000000000000040 ffffffff 00000000 fffeff 000000`), then the value as a `float64` in metres.
Locate by ordinal among dimension-scalar records, not by class marker.

Six copies at scalar `+{0, +72, +398, +422, +560, +584}` with signs `(+,+,−,−,+,+)`.
Copy `+0` is the authored parameter; the other five are the annotation's derived geometry. For a
plane-supported feature `+72` equals the depth; for a feature sketched on a face at height `h`
it equals `h + depth`. `serialize.py` writes all six with the plane-supported convention.

A **ThroughAll** feature has **no** dimension-scalar record at all, and its `<Extrusion>` element
in `KeyWords` has no `<Dimension>` child.

### 5.3 Direction and end condition — CONFIRMED

Anchored on the feature's own depth scalar:

| field                       | feature 1      | features 2+    |
| --------------------------- | -------------- | -------------- |
| direction reverse, 1 byte   | `scalar − 824` | `scalar − 721` |
| `swEndConditions_e`, 1 byte | `scalar − 818` | `scalar − 715` |

Feature 1 additionally mirrors the direction flag at `moFromEndSpec_c + 29`.
Codes exercised and measured: `0` Blind, `1` ThroughAll, `6` MidPlane. Both bytes are
**AUTHORED**. The true field width is still undetermined — the neighbouring bytes are zero, so
1, 2 and 4 byte fields all fit.

`0` and `6` are writable in place on a blind donor. `1` (ThroughAll) is writable on a blind donor
too — see `E3` in `results.md`, which is the result report 2 §5.5 predicted would be impossible.

### 5.4 Sketch support plane — CONFIRMED

Inside `moSketchChain_c`: a `u32` plane object id (2 = Front, 3 = Top, 4 = Right) with the
`u32` axis code `5 − id` exactly 10 bytes later. The pair must be located by that relation,
not at a fixed offset (marker+209 in the rectangle layout, marker+197 in the circle layout).

A 9-double row-major orthonormal basis follows at `moSketchChain_c + 224` for Top and Right and
is **omitted entirely for Front** (Front is the identity). Both are **AUTHORED**.

Writing the id/axis pair alone re-plants the sketch: `E6` moved a Front-plane pad to the Right
plane and SOLIDWORKS rebuilt it with the centre of mass at `(5, 0, 0)` mm. See `results.md` for
the Top-plane case.

### 5.5 Face-supported sketches — PARTIAL

A sketch supported by a planar face adds `moEdgeRef_c`, `moFaceRefPlnData_c`, `moCompFace_c`
and a zlib-compressed Parasolid transmit blob (`78 01` → `PS\0\0\0` + `3: TRANSMIT FILE …`)
inside the stream. The blob is a **DERIVED CACHE**: it may be left describing the old face
position and SOLIDWORKS re-resolves the reference (report 2 §3, §7 case C/D). It cannot be
deleted the way the Partition can.

The face reference itself is OPAQUE to this work: a writer cannot choose _which_ face supports
a sketch, only inherit the choice from a skeleton.

---

## 6. Derived caches — what may be left stale

All of these follow from the sketch and the depth. None is an authored parameter, and all four
prior round-trip proofs left them stale and still got exact volumes.

| record                                          | fields                                                                                            | rule                                    |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------- |
| `moBBoxCenterData_c`                            | `+28/+36/+44` body bbox centre `(x, y, z)` m, `+52` bounding-sphere diameter                      | `diameter = 2·√(hx²+hy²+hz²)`           |
| `moRefPlane_c`, `moDefaultRefPlnData_c`         | three display rectangles, one per principal plane                                                 | half-extent × 1.1 about the bbox centre |
| `moLengthParameter_c` (and its unmarked copies) | annotation witness points at scalar `+32/+40/+56/+64/+229/+245`, and scalar `+318 = (extent/2)/5` | derived from the profile's max corner   |
| the embedded Parasolid                          | the supporting face surface                                                                       | re-resolved on rebuild                  |

`serialize.py` leaves all of these stale by default. That is not laziness — it is a measured
requirement. Writing the six depth copies with the blind-forward sign pattern
`(+,+,−,−,+,+)` onto a reversed or MidPlane feature produced 0 bodies, a crash on open, and one
silently wrong volume (`results.md` §2.2). The sign of scalar `+72` depends on the end condition
(`+depth` blind-forward, `−depth` reversed, `+depth/2` MidPlane) and `+398/+422` flip with
direction, so the copies can only be written once that rule is fully implemented.

**A stale derived cache is safe; a wrong one is not.** `Part.write_depth_copies` and
`Part.write_bbox_cache` exist and default to `False`.

Two scratch doubles remain **OPAQUE**: `moExtrusion_c + 114` and `moFromEndSpec_c + 140` /
`moICE_c + 106/+108`, which hold `0.0` or `0.016` m with no correlation to anything authored
across all 51 files.

---

## 7. The XML side streams — fully AUTHORED

Both are plain XML and `serialize.py` emits them from scratch.

### `swXmlContents/KeyWords`

The stream begins with **one `0x86` tag byte** — not a UTF-8 BOM — then
`<?xml version="1.0" encoding="UTF-8"?>` `\r\n`, then
`<Keywords id="<time_t>" Name="<session doc name>">`, and ends with a trailing `\r\n`. All line
endings are CRLF. Writing a BOM instead of `0x86` makes SOLIDWORKS crash on open
(measured — `results.md` §2.3). The body contains, in this order:

1. one `<Configuration id="0" Name="Default" Type="ConfigurationManager" Material="…"/>`
2. one `<Extrusion>` per feature, ascending id.
   Feature 1 carries `Type="Boss-Extrude"`; features 2+ carry
   `Dissectable="true" DissectableChildren="<its sketch id>" DissectableRoot="true"` and **no**
   `Type`. A blind or MidPlane feature has a `<Dimension Name="D1">depth_mm</Dimension>` child;
   a ThroughAll feature has none.
3. 23 boilerplate `<Feature>` elements (the folders, the three planes, the lights) — a fixed
   table, reproduced verbatim in `serialize.py::_BOILERPLATE_FEATURES`
4. one `<Sketch id=… Name="Sketch<n>" Dissectable="true"/>` per feature
5. `<Sketch id="5" Name="Origin" Type="Origin"/>`

Boss versus cut is visible in `KeyWords` **only** through the `Name` string, so the name written
here must be the same string the resolved stream carries.

### `swXmlContents/Features`

A three-object header naming the document, its configuration and its path. No prefix byte, CRLF
line endings, trailing CRLF. `swVersion="18000"`, `swConfigurationFlags="-2143288960"`,
`swLastModifiedStamp` is a monotonic counter that does not need to be accurate.

### Ids

The corpus convention is sketch 26 → feature 32 → sketch 33 → feature 40 → sketch 41 →
feature 47. `serialize.py` can author that sequence (`Part(author_ids=True)`) but defaults to
**inheriting** the skeleton's ids, because other inherited streams (`Contents/Config-0`,
`Contents/CnfgObjs`, `Contents/DisplayLists`) also reference them and were not audited. Ids are
understood; renumbering them is not proven safe.

---

## 8. What still blocks an arbitrary feature tree

1. **Object segmentation.** Per-class `Serialize` layouts are unknown for ~45 classes, so the
   byte span of each object cannot be computed statically. Everything below follows from this.
2. **Map-index renumbering** (§2.3). Adding or removing a feature changes the object count and
   therefore the class-reference tokens. Without segmentation the tokens cannot be enumerated,
   so they cannot be renumbered.
3. **Feature count** is therefore bounded by the available skeletons. `serialize.py` covers
   1, 2 and 3 features and _refuses_ a 4-feature request with an explicit error rather than
   emitting something that would crash SOLIDWORKS.
4. **Profile type beyond rectangle and circle.** Polygon, slot and spline profiles use `sg*`
   classes not present in either authored corpus. The V8 production corpus contains them
   (`.rescratch/v8/vocabulary.txt`, 185 classes) but they were not decoded.
5. **Sketch support choice.** A writer can pick Front/Top/Right; it cannot pick a face or a user
   reference plane, because that changes the class set and adds the Parasolid blob.
6. **Boss versus cut.** The tree flags word is an annotation, not the selector (§4.1). The
   operation must be inherited from a skeleton until the `moExtrusion_c` / `moICE_c` body is
   decoded — which needs the same object segmentation as item 1.
7. **Every non-extrude operation.** `moRevolution_c`, `moBlend_c`, `moSweep_c`, `moHoleWzd_c`,
   `moLPattern_c`, `moCirPattern_c`, `moMirrorPattern_c`, `moShell_c`, `moChamfer`, `moHelix_c`
   are present in the V8 corpus and have known tree flag words, but no field layout was derived
   for any of them here.
8. **End conditions 2, 3, 4, 5, 7, 9, 10, 11** (ThroughNext, UpToVertex, UpToSurface,
   OffsetFromSurface, UpToBody, ThroughAllBoth, UpToSelection, UpToNext). `T1 = 5` raises an
   internal application error in COM authoring without a pre-selected surface, so no donor
   exists to diff. UpToSurface/UpToBody additionally need a reference to the target entity,
   which is the same opaque face-reference problem as §5.5.
   Note that blind → ThroughAll is **not** a byte flip: E3 in `results.md` crashes, because
   ThroughAll deletes the whole dimension object.
9. **The container signature triplet.** `build_sldprt` still needs a donor template.

Item 1 is the keystone. `WINDBG.md` sets out the runtime route to it and how far it got.

---

## 9. Scripts

```
.rescratch/grammar/
  GRAMMAR.md              this document
  WINDBG.md               runtime instrumentation
  results.md              every SOLIDWORKS measurement, including failures
  carchive.py             su_CArchive tag scanner: class definitions, references, strings
  streamlib.py            donor load / container rebuild / moCompFeature_c parsing
  serialize.py            the from-scratch writer
  build_skeletons.py      validates and registers the topology skeletons
  author_parts.py         emits the from-scratch parts
  experiments.py          the byte-level capability experiments
  build_experiments.py    builds them
  measure.py              one fresh SOLIDWORKS subprocess per file
  measure_one.py          the subprocess: open, rebuild, GetMassProperties
  probe_tags.py           schema survey, class-reference histogram, timestamp identification
  probe_compfeature.py    moCompFeature_c self-similarity and hex dump
  probe_entries.py        moCompFeature_c entry ids vs tree nodes, all 51 files
  probe_xml.py            KeyWords / Features dumps
  probe_exports.py        PE export table reader
  probe_su_archive.py     locates su_CArchive across the SOLIDWORKS install
  probe_modules.py        confirms which MFC runtime SOLIDWORKS loads
  diagnose_a1.py          isolates a single write by building four one-boss variants
  cdb_*.txt               the cdb scripts, verbatim
  diagnose/               the isolation artefacts
  skeletons/manifest.json the accepted skeletons
  out/                    all machine-readable output
  parts/                  the capability-experiment artefacts
  authored/               the from-scratch artefacts
```
